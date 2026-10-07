"""Temas de una pregunta: asignar, listar y quitar, con su auditoría.

Hasta ahora el mapeo pregunta↔tema se escribía solo desde dentro (`map_question_to_node`, la
catalogación automática de S12.6) y no había ninguna forma de hacerlo por HTTP. Lo que defienden
estas pruebas es lo que hace falta para clasificar un banco de 7.677 preguntas y para administrarlo
a mano:

- asignar deja el mapeo **y** su evento (`question.mapped`), y repetirlo no duplica ni lo uno ni lo
  otro: un lote de clasificación se reintenta;
- el actor automático (`llm:…`) queda guardado en el evento, porque miles de asignaciones hechas por
  un proceso tienen que poder distinguirse de las de una persona;
- un nodo que no existe es un 404; un nodo que **no es un tema** es un 409 con el motivo (un bloque
  o un epígrafe agrupan temas, y una pregunta colgada de ellos quedaría fuera del diagnóstico por
  temas creyendo estar dentro);
- quitar deja la pregunta sin tema y auditado (`question.unmapped`), y quitar lo que no estaba es un
  404, no una retirada silenciosa de algo que nunca estuvo.
"""

from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy import text

from opofuente.config import Settings
from opofuente.infrastructure.db import build_engine

ALLOWED_ORIGIN = {"Origin": "http://127.0.0.1:5173"}

#: El evento del nodo que no vale se pide con cabecera, no con cuerpo: la clasificación automática
#: hace miles de llamadas y repetir el actor en cada cuerpo sería repetirlo mil veces.
ACTOR_HEADER = "X-OpoFuente-Actor"

TEXTO = (
    "1. La Constitucion espanola se aprobo en:\n"
    "a) 1976\n"
    "b) 1978\n"
    "Respuesta correcta: b\n"
    "2. El plazo de alegaciones es de diez dias habiles.\n"
    "a) Verdadero\n"
    "b) Falso\n"
    "Respuesta correcta: a\n"
)


def _aplanar(nodos: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """El árbol del programa, de arriba abajo: aquí solo se buscan nodos de un tipo concreto."""
    planos: list[dict[str, Any]] = []
    for nodo in nodos:
        planos.append(nodo)
        planos.extend(_aplanar(nodo.get("children", [])))
    return planos


def _nodo(client: TestClient, tipo: str) -> dict[str, Any]:
    """Primer nodo del programa **sembrado** con ese tipo, leído por la API real."""
    oposiciones = client.get("/api/v1/oppositions").json()
    convocatoria = next(item["active_convocation"]["id"] for item in oposiciones if item["active"])
    programa = client.get(f"/api/v1/convocations/{convocatoria}/curriculum").json()
    return next(nodo for nodo in _aplanar(programa["nodes"]) if nodo["node_type"] == tipo)


def _conjunto(client: TestClient) -> dict[str, Any]:
    """Un conjunto privado sobre la oposición que ya trae la siembra de las pruebas."""
    oposiciones = client.get("/api/v1/oppositions").json()
    activa = next(oposicion for oposicion in oposiciones if oposicion["active"])
    respuesta = client.post(
        "/api/v1/question-sets",
        json={
            "title": "Banco para clasificar",
            "opposition_id": activa["id"],
            "set_type": "private_bank",
        },
        headers=ALLOWED_ORIGIN,
    )
    assert respuesta.status_code == 201, respuesta.text
    return dict(respuesta.json())


def _preguntas(client: TestClient, set_id: str) -> list[dict[str, Any]]:
    """Las preguntas del conjunto importado, en el orden del documento."""
    respuesta = client.post(
        f"/api/v1/question-sets/{set_id}/parse",
        json={"kind": "questions", "text": TEXTO},
        headers=ALLOWED_ORIGIN,
    )
    assert respuesta.status_code == 200, respuesta.text
    assert respuesta.json()["created"] == 2, respuesta.text
    listado = client.get("/api/v1/questions", params={"set_id": set_id}).json()
    return list(listado["questions"])


def _asignar(
    client: TestClient,
    pregunta_id: str,
    node_id: str,
    *,
    actor: str | None = None,
    cabecera: str | None = None,
    confidence: float | None = None,
) -> Any:
    cuerpo: dict[str, Any] = {"curriculum_node_id": node_id}
    if actor is not None:
        cuerpo["actor"] = actor
    if confidence is not None:
        cuerpo["confidence"] = confidence
    cabeceras = dict(ALLOWED_ORIGIN)
    if cabecera is not None:
        cabeceras[ACTOR_HEADER] = cabecera
    return client.post(f"/api/v1/questions/{pregunta_id}/topics", json=cuerpo, headers=cabeceras)


def _temas(client: TestClient, pregunta_id: str) -> list[dict[str, Any]]:
    respuesta = client.get(f"/api/v1/questions/{pregunta_id}/topics")
    assert respuesta.status_code == 200, respuesta.text
    return list(respuesta.json())


def _eventos(settings: Settings) -> list[dict[str, Any]]:
    """Los eventos de esta funcionalidad, en orden.

    La API **no** publica la auditoría (es una traza interna), así que la prueba la lee de la base,
    como las demás pruebas que comprueban que algo quedó registrado.
    """
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.connect() as conexion:
            filas = conexion.execute(
                text(
                    "SELECT action, actor, object_id, before_json, after_json FROM audit_events "
                    "WHERE action IN ('question.mapped', 'question.unmapped') "
                    "ORDER BY created_at, id"
                )
            ).all()
    finally:
        engine.dispose()
    return [
        {
            "action": str(fila[0]),
            "actor": str(fila[1]),
            "object_id": str(fila[2]),
            "before": str(fila[3]),
            "after": str(fila[4]),
        }
        for fila in filas
    ]


def test_asignar_un_tema_deja_el_mapeo_y_su_evento_de_auditoria(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    conjunto = _conjunto(seeded_client)
    pregunta = _preguntas(seeded_client, conjunto["id"])[0]
    tema = _nodo(seeded_client, "topic")

    respuesta = _asignar(seeded_client, pregunta["id"], tema["id"])

    assert respuesta.status_code == 200, respuesta.text
    asignado = respuesta.json()
    assert asignado["created"] is True, "el mapeo no existía: esta llamada lo ha creado"
    assert asignado["curriculum_node_id"] == tema["id"]
    assert asignado["official_code"] == tema["official_code"]
    assert asignado["title"] == tema["title"]
    assert asignado["status"] == "accepted", "un tema asignado a propósito es un tema decidido"
    assert asignado["confidence"] == 1.0

    temas = _temas(seeded_client, pregunta["id"])
    assert [item["mapping_id"] for item in temas] == [asignado["mapping_id"]]

    eventos = _eventos(seeded_settings)
    assert [evento["action"] for evento in eventos] == ["question.mapped"]
    assert eventos[0]["actor"] == "local", "sin decir quién, el actor es la persona local"
    assert eventos[0]["object_id"] == asignado["mapping_id"]
    assert eventos[0]["before"] == "{}"
    assert tema["id"] in eventos[0]["after"]
    assert pregunta["id"] in eventos[0]["after"]


def test_repetir_la_asignacion_no_duplica_ni_el_mapeo_ni_el_evento(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """Reintentar un lote de clasificación no puede ensuciar la auditoría con la misma línea."""
    conjunto = _conjunto(seeded_client)
    pregunta = _preguntas(seeded_client, conjunto["id"])[0]
    tema = _nodo(seeded_client, "topic")

    primera = _asignar(seeded_client, pregunta["id"], tema["id"])
    segunda = _asignar(seeded_client, pregunta["id"], tema["id"])

    assert primera.status_code == segunda.status_code == 200
    assert primera.json()["created"] is True
    assert segunda.json()["created"] is False, "el mapeo ya estaba: no se ha creado otro"
    assert segunda.json()["mapping_id"] == primera.json()["mapping_id"]

    assert len(_temas(seeded_client, pregunta["id"])) == 1
    assert [evento["action"] for evento in _eventos(seeded_settings)] == ["question.mapped"]


def test_el_actor_automatico_queda_guardado_en_el_evento(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """La clasificación con un modelo se identifica: «lo hizo la máquina» tiene que poder auditarse.

    El actor viaja en el cuerpo o en la cabecera `X-OpoFuente-Actor`. Si vienen los dos, manda el
    cuerpo, que es lo explícito y lo que va en el contrato.
    """
    conjunto = _conjunto(seeded_client)
    primera, segunda = _preguntas(seeded_client, conjunto["id"])[:2]
    tema = _nodo(seeded_client, "topic")

    en_cuerpo = _asignar(
        seeded_client,
        primera["id"],
        tema["id"],
        actor="llm:deepseek-flash",
        cabecera="local",
        confidence=0.75,
    )
    en_cabecera = _asignar(seeded_client, segunda["id"], tema["id"], cabecera="llm:deepseek-flash")

    assert en_cuerpo.status_code == en_cabecera.status_code == 200, en_cabecera.text
    assert en_cuerpo.json()["confidence"] == 0.75, "la confianza que se manda es la que se guarda"

    actores = {evento["object_id"]: evento["actor"] for evento in _eventos(seeded_settings)}
    assert actores[en_cuerpo.json()["mapping_id"]] == "llm:deepseek-flash"
    assert actores[en_cabecera.json()["mapping_id"]] == "llm:deepseek-flash"


def test_un_nodo_que_no_existe_es_un_404_y_no_deja_rastro(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    conjunto = _conjunto(seeded_client)
    pregunta = _preguntas(seeded_client, conjunto["id"])[0]

    respuesta = _asignar(seeded_client, pregunta["id"], "nodo-que-no-existe")

    assert respuesta.status_code == 404, respuesta.text
    assert respuesta.json()["code"] == "not_found"
    assert _temas(seeded_client, pregunta["id"]) == []
    assert _eventos(seeded_settings) == [], "un destino que no existe no deja auditoría"


def test_una_pregunta_que_no_existe_es_un_404(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    tema = _nodo(seeded_client, "topic")

    respuesta = _asignar(seeded_client, "pregunta-que-no-existe", tema["id"])

    assert respuesta.status_code == 404, respuesta.text
    assert seeded_client.get("/api/v1/questions/no-existe/topics").status_code == 404
    assert _eventos(seeded_settings) == []


def test_un_nodo_que_no_es_un_tema_es_un_409_con_el_motivo(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """Un bloque agrupa temas: una pregunta colgada de él quedaría fuera del diagnóstico."""
    conjunto = _conjunto(seeded_client)
    pregunta = _preguntas(seeded_client, conjunto["id"])[0]
    bloque = _nodo(seeded_client, "block")

    respuesta = _asignar(seeded_client, pregunta["id"], bloque["id"])

    assert respuesta.status_code == 409, respuesta.text
    cuerpo = respuesta.json()
    assert cuerpo["code"] == "classification_conflict"
    assert "bloque" in cuerpo["detail"], cuerpo["detail"]
    assert "tema" in cuerpo["detail"], "el motivo tiene que decir a qué sí se puede asignar"
    assert _temas(seeded_client, pregunta["id"]) == [], "un destino que no vale no se guarda"
    assert _eventos(seeded_settings) == []


def test_quitar_un_tema_lo_deja_sin_tema_y_auditado(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    conjunto = _conjunto(seeded_client)
    pregunta = _preguntas(seeded_client, conjunto["id"])[0]
    tema = _nodo(seeded_client, "topic")
    mapeo = _asignar(seeded_client, pregunta["id"], tema["id"]).json()["mapping_id"]

    respuesta = seeded_client.delete(
        f"/api/v1/questions/{pregunta['id']}/topics/{tema['id']}", headers=ALLOWED_ORIGIN
    )

    assert respuesta.status_code == 204, respuesta.text
    assert _temas(seeded_client, pregunta["id"]) == []

    eventos = _eventos(seeded_settings)
    assert [evento["action"] for evento in eventos] == ["question.mapped", "question.unmapped"]
    retirada = eventos[1]
    assert retirada["object_id"] == mapeo, "la retirada se audita sobre el mapeo que se retiró"
    assert retirada["actor"] == "local"
    assert tema["id"] in retirada["before"], "queda dicho qué se quitó"
    assert pregunta["id"] in retirada["before"]
    assert retirada["after"] == "{}"


def test_quitar_un_tema_que_no_estaba_es_un_404(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    conjunto = _conjunto(seeded_client)
    pregunta = _preguntas(seeded_client, conjunto["id"])[0]
    tema = _nodo(seeded_client, "topic")

    respuesta = seeded_client.delete(
        f"/api/v1/questions/{pregunta['id']}/topics/{tema['id']}", headers=ALLOWED_ORIGIN
    )

    assert respuesta.status_code == 404, respuesta.text
    assert respuesta.json()["code"] == "not_found"
    assert _eventos(seeded_settings) == [], "no se audita una retirada que no ocurrió"


def test_el_actor_de_la_retirada_se_dice_por_cabecera(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """Quitar también tiene autor: deshacer la clasificación automática es una decisión."""
    conjunto = _conjunto(seeded_client)
    pregunta = _preguntas(seeded_client, conjunto["id"])[0]
    tema = _nodo(seeded_client, "topic")
    _asignar(seeded_client, pregunta["id"], tema["id"], actor="llm:deepseek-flash")

    respuesta = seeded_client.delete(
        f"/api/v1/questions/{pregunta['id']}/topics/{tema['id']}",
        headers={**ALLOWED_ORIGIN, ACTOR_HEADER: "revision:humano"},
    )

    assert respuesta.status_code == 204, respuesta.text
    assert _eventos(seeded_settings)[-1]["actor"] == "revision:humano"
