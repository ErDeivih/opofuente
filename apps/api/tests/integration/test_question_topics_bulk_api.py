"""La asignación de temas por lotes, y el fuera de temario (F4).

La ruta por lotes existe para que la clasificación de un banco entero no sean 17.000 peticiones. Lo
que estas pruebas defienden es que **no es un segundo camino de escritura**:

- el mapeo y el evento de auditoría de una fila del lote son **los mismos** que los de la ruta
  individual: se comparan de verdad, fila a fila y campo a campo, contra la base;
- repetir el lote no duplica ni el mapeo ni el evento (se reintenta);
- una fila mala **no** tumba el lote: se dice cuál falló y por qué, y las demás se aplican;
- el «fuera de temario» se declara con su motivo, se puede consultar y **no** es un mapeo: no tiene
  nodo ni código, así que no se puede confundir con un tema;
- asignar un tema a una pregunta marcada levanta la marca: no puede ser de un tema y no ser del
  temario a la vez.
"""

from __future__ import annotations

from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import bindparam, text

from opofuente.config import Settings
from opofuente.infrastructure.db import build_engine

ALLOWED_ORIGIN = {"Origin": "http://127.0.0.1:5173"}

#: Cabecera con la que la clasificación automática se identifica sin repetir el actor en cada
#: cuerpo.
ACTOR_HEADER = "X-OpoFuente-Actor"

#: El actor de la clasificación automática: miles de asignaciones tienen que poder auditarse como
#: suyas, y se distingue de `local` (una persona).
ACTOR_LLM = "llm:deepseek-flash"

TEXTO = (
    "1. La Constitucion espanola se aprobo en:\n"
    "a) 1976\n"
    "b) 1978\n"
    "Respuesta correcta: b\n"
    "2. El plazo de alegaciones es de diez dias habiles.\n"
    "a) Verdadero\n"
    "b) Falso\n"
    "Respuesta correcta: a\n"
    "3. La ley de procedimiento comun se publico en:\n"
    "a) 2015\n"
    "b) 2016\n"
    "Respuesta correcta: a\n"
)


def _aplanar(nodos: list[dict[str, Any]]) -> list[dict[str, Any]]:
    planos: list[dict[str, Any]] = []
    for nodo in nodos:
        planos.append(nodo)
        planos.extend(_aplanar(nodo.get("children", [])))
    return planos


def _nodos(client: TestClient, tipo: str) -> list[dict[str, Any]]:
    """Todos los nodos del programa sembrado de ese tipo, en orden."""
    oposiciones = client.get("/api/v1/oppositions").json()
    convocatoria = next(item["active_convocation"]["id"] for item in oposiciones if item["active"])
    programa = client.get(f"/api/v1/convocations/{convocatoria}/curriculum").json()
    return [nodo for nodo in _aplanar(programa["nodes"]) if nodo["node_type"] == tipo]


def _nodo(client: TestClient, tipo: str) -> dict[str, Any]:
    return _nodos(client, tipo)[0]


def _conjunto(client: TestClient) -> dict[str, Any]:
    oposiciones = client.get("/api/v1/oppositions").json()
    activa = next(oposicion for oposicion in oposiciones if oposicion["active"])
    respuesta = client.post(
        "/api/v1/question-sets",
        json={
            "title": "Banco para clasificar por lotes",
            "opposition_id": activa["id"],
            "set_type": "private_bank",
        },
        headers=ALLOWED_ORIGIN,
    )
    assert respuesta.status_code == 201, respuesta.text
    return dict(respuesta.json())


def _preguntas(client: TestClient, set_id: str) -> list[dict[str, Any]]:
    respuesta = client.post(
        f"/api/v1/question-sets/{set_id}/parse",
        json={"kind": "questions", "text": TEXTO},
        headers=ALLOWED_ORIGIN,
    )
    assert respuesta.status_code == 200, respuesta.text
    assert respuesta.json()["created"] == 3, respuesta.text
    return list(client.get("/api/v1/questions", params={"set_id": set_id}).json()["questions"])


def _individual(
    client: TestClient,
    pregunta_id: str,
    node_id: str,
    *,
    actor: str = "local",
    confidence: float = 1.0,
    reason: str | None = None,
    epigraph_node_id: str | None = None,
) -> Any:
    cuerpo: dict[str, Any] = {"curriculum_node_id": node_id}
    if actor:
        cuerpo["actor"] = actor
    if confidence != 1.0:
        cuerpo["confidence"] = confidence
    if reason is not None:
        cuerpo["reason"] = reason
    if epigraph_node_id is not None:
        cuerpo["epigraph_node_id"] = epigraph_node_id
    return client.post(
        f"/api/v1/questions/{pregunta_id}/topics", json=cuerpo, headers=ALLOWED_ORIGIN
    )


def _lote(
    client: TestClient,
    filas: list[dict[str, Any]],
    *,
    actor: str | None = None,
    cabecera: str | None = None,
) -> Any:
    cuerpo: dict[str, Any] = {"assignments": filas}
    if actor is not None:
        cuerpo["actor"] = actor
    cabeceras = dict(ALLOWED_ORIGIN)
    if cabecera is not None:
        cabeceras[ACTOR_HEADER] = cabecera
    return client.post("/api/v1/questions/topics/bulk", json=cuerpo, headers=cabeceras)


def _mapeo(settings: Settings, mapping_id: str) -> dict[str, Any]:
    """La fila del mapeo tal como quedó en la base, sin pasar por la API."""
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.connect() as conexion:
            fila = conexion.execute(
                text(
                    "SELECT curriculum_node_id, subject_type, subject_id, coverage_type, depth, "
                    "confidence, status, approved_at IS NOT NULL "
                    "FROM curriculum_mappings WHERE id = :id"
                ),
                {"id": mapping_id},
            ).one()
    finally:
        engine.dispose()
    return {
        "curriculum_node_id": str(fila[0]),
        "subject_type": str(fila[1]),
        "subject_id": str(fila[2]),
        "coverage_type": str(fila[3]),
        "depth": int(fila[4]),
        "confidence": float(fila[5]),
        "status": str(fila[6]),
        "aprobado": bool(fila[7]),
    }


def _eventos(settings: Settings, *, acciones: tuple[str, ...]) -> list[dict[str, Any]]:
    consulta = text(
        "SELECT action, actor, object_id, before_json, after_json FROM audit_events "
        "WHERE action IN :acciones ORDER BY created_at, id"
    ).bindparams(bindparam("acciones", expanding=True))
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.connect() as conexion:
            filas = conexion.execute(consulta, {"acciones": list(acciones)}).all()
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


def _normalizar(evento: dict[str, Any], *, pregunta: str, mapeo: str) -> dict[str, Any]:
    """Un evento comparable: los identificadores propios se sustituyen por marcadores.

    Es lo que permite comparar el evento de la ruta individual con el de una fila del lote sin que
    la diferencia de identificadores (que es inevitable) tape las diferencias de contenido (que
    serían un fallo).
    """
    return {
        "action": evento["action"],
        "actor": evento["actor"],
        "object_id": "<mapeo>" if evento["object_id"] == mapeo else evento["object_id"],
        "before": evento["before"].replace(pregunta, "<pregunta>").replace(mapeo, "<mapeo>"),
        "after": evento["after"].replace(pregunta, "<pregunta>").replace(mapeo, "<mapeo>"),
    }


def test_el_lote_deja_el_mismo_mapeo_y_el_mismo_evento_que_la_ruta_individual(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """La comparación de verdad: la misma asignación por las dos rutas, campo a campo."""
    conjunto = _conjunto(seeded_client)
    individual, lote = _preguntas(seeded_client, conjunto["id"])[:2]
    tema = _nodo(seeded_client, "topic")

    de_una = _individual(
        seeded_client,
        individual["id"],
        tema["id"],
        actor=ACTOR_LLM,
        confidence=0.9,
        reason="la Constitución es el tema I.1",
    )
    de_lote = _lote(
        seeded_client,
        [
            {
                "question_version_id": lote["id"],
                "curriculum_node_id": tema["id"],
                "confidence": 0.9,
                "reason": "la Constitución es el tema I.1",
            }
        ],
        actor=ACTOR_LLM,
    )

    assert de_una.status_code == 200, de_una.text
    assert de_lote.status_code == 200, de_lote.text
    fila = de_lote.json()["results"][0]
    assert fila["outcome"] == "created"
    assert fila["assignment"]["created"] is True

    un_mapeo = _mapeo(seeded_settings, de_una.json()["mapping_id"])
    otro_mapeo = _mapeo(seeded_settings, fila["assignment"]["mapping_id"])
    un_mapeo.pop("subject_id"), otro_mapeo.pop("subject_id")
    assert un_mapeo == otro_mapeo, "el lote no escribe un mapeo distinto"

    eventos = _eventos(seeded_settings, acciones=("question.mapped",))
    assert len(eventos) == 2
    uno = _normalizar(eventos[0], pregunta=individual["id"], mapeo=de_una.json()["mapping_id"])
    dos = _normalizar(eventos[1], pregunta=lote["id"], mapeo=fila["assignment"]["mapping_id"])
    assert uno == dos, "el evento del lote tiene que ser el mismo que el de la ruta individual"
    assert uno["actor"] == ACTOR_LLM
    assert '"confidence": 0.9' in uno["after"]
    assert "la Constitución es el tema I.1" in uno["after"], "el motivo queda en la auditoría"


def test_repetir_el_lote_no_duplica_ni_los_mapeos_ni_los_eventos(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """Un lote de clasificación se reintenta: la segunda pasada no puede ensuciar nada."""
    conjunto = _conjunto(seeded_client)
    pregunta = _preguntas(seeded_client, conjunto["id"])[0]
    tema = _nodo(seeded_client, "topic")
    fila = {"question_version_id": pregunta["id"], "curriculum_node_id": tema["id"]}

    primera = _lote(seeded_client, [fila], actor=ACTOR_LLM)
    segunda = _lote(seeded_client, [fila], actor=ACTOR_LLM)

    assert primera.json()["created"] == 1
    assert segunda.json()["results"][0]["outcome"] == "existing"
    assert segunda.json()["existing"] == 1
    assert segunda.json()["results"][0]["assignment"]["created"] is False
    assert len(seeded_client.get(f"/api/v1/questions/{pregunta['id']}/topics").json()) == 1
    assert len(_eventos(seeded_settings, acciones=("question.mapped",))) == 1


def test_una_fila_mala_no_tumba_el_lote(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """Abortar 200 asignaciones porque una pregunta se retiró obligaría a repetir las 199 buenas."""
    conjunto = _conjunto(seeded_client)
    primera, segunda, _ = _preguntas(seeded_client, conjunto["id"])
    tema = _nodo(seeded_client, "topic")
    bloque = _nodo(seeded_client, "block")

    respuesta = _lote(
        seeded_client,
        [
            {"question_version_id": primera["id"], "curriculum_node_id": tema["id"]},
            {"question_version_id": segunda["id"], "curriculum_node_id": bloque["id"]},
            {"question_version_id": "pregunta-que-no-existe", "curriculum_node_id": tema["id"]},
            {"question_version_id": segunda["id"]},
            {
                "question_version_id": segunda["id"],
                "curriculum_node_id": tema["id"],
                "exclusion_reason": "enunciado_roto",
            },
        ],
        actor=ACTOR_LLM,
    )

    assert respuesta.status_code == 200, respuesta.text
    cuerpo = respuesta.json()
    desenlaces = [fila["outcome"] for fila in cuerpo["results"]]
    assert desenlaces == ["created", "error", "error", "error", "error"]
    assert cuerpo["created"] == 1
    assert cuerpo["errors"] == 4
    assert "bloque" in cuerpo["results"][1]["detail"]
    assert "no existe" in cuerpo["results"][2]["detail"]
    assert "tema o un motivo" in cuerpo["results"][3]["detail"]
    assert "no las dos cosas" in cuerpo["results"][4]["detail"]

    # La buena sí se ha escrito: el lote no se queda a medias por culpa de las malas.
    assert len(seeded_client.get(f"/api/v1/questions/{primera['id']}/topics").json()) == 1
    assert len(_eventos(seeded_settings, acciones=("question.mapped",))) == 1


def test_el_lote_declara_fuera_de_temario_con_su_motivo_y_se_puede_consultar(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """Fuera de temario no es un tema: no hay nodo, así que no se puede confundir con uno."""
    conjunto = _conjunto(seeded_client)
    pregunta = _preguntas(seeded_client, conjunto["id"])[0]

    respuesta = _lote(
        seeded_client,
        [
            {
                "question_version_id": pregunta["id"],
                "exclusion_reason": "otra_administracion",
                "reason": "ley autonómica de Aragón",
            }
        ],
        actor=ACTOR_LLM,
    )

    assert respuesta.status_code == 200, respuesta.text
    fila = respuesta.json()["results"][0]
    assert fila["outcome"] == "excluded"
    assert fila["exclusion"]["reason"] == "otra_administracion"
    assert fila["assignment"] is None, "fuera de temario no escribe ningún mapeo"
    assert seeded_client.get(f"/api/v1/questions/{pregunta['id']}/topics").json() == []

    consulta = seeded_client.get("/api/v1/question-exclusions").json()
    assert consulta["total"] == 1
    assert consulta["exclusions"][0]["question_version_id"] == pregunta["id"]
    assert consulta["exclusions"][0]["actor"] == ACTOR_LLM
    assert consulta["exclusions"][0]["note"] == "ley autonómica de Aragón"

    por_motivo = seeded_client.get(
        "/api/v1/question-exclusions", params={"reason": "enunciado_roto"}
    ).json()
    assert por_motivo["total"] == 0, "el filtro por motivo filtra de verdad"
    assert por_motivo["totals_by_reason"] == {"otra_administracion": 1}, (
        "los recuentos por motivo no dependen del filtro de la petición"
    )

    # Repetirlo no duplica la marca ni el evento: la pregunta ya está declarada.
    repetida = _lote(
        seeded_client,
        [{"question_version_id": pregunta["id"], "exclusion_reason": "otra_administracion"}],
        actor=ACTOR_LLM,
    )
    assert repetida.json()["results"][0]["outcome"] == "already_excluded"
    assert seeded_client.get("/api/v1/question-exclusions").json()["total"] == 1
    assert len(_eventos(seeded_settings, acciones=("question.out_of_syllabus",))) == 1


def test_asignar_un_tema_levanta_la_marca_de_fuera_de_temario(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """No puede ser de un tema y no ser del temario a la vez: la marca se retira, y se audita."""
    conjunto = _conjunto(seeded_client)
    pregunta = _preguntas(seeded_client, conjunto["id"])[0]
    tema = _nodo(seeded_client, "topic")
    _lote(
        seeded_client,
        [{"question_version_id": pregunta["id"], "exclusion_reason": "enunciado_roto"}],
        actor=ACTOR_LLM,
    )

    asignada = _individual(seeded_client, pregunta["id"], tema["id"], actor="local")

    assert asignada.status_code == 200, asignada.text
    assert seeded_client.get("/api/v1/question-exclusions").json()["total"] == 0
    acciones = [
        evento["action"]
        for evento in _eventos(
            seeded_settings, acciones=("question.out_of_syllabus", "question.in_syllabus")
        )
    ]
    assert acciones == ["question.out_of_syllabus", "question.in_syllabus"]


def test_asignar_un_epigrafe_escribe_tambien_su_tema(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """Un epígrafe no sustituye a su tema: la pregunta cuelga de los dos, y las dos se auditan."""
    conjunto = _conjunto(seeded_client)
    pregunta = _preguntas(seeded_client, conjunto["id"])[0]
    tema = next(nodo for nodo in _nodos(seeded_client, "topic") if nodo["children"])
    epigrafe = tema["children"][0]

    respuesta = _individual(
        seeded_client,
        pregunta["id"],
        tema["id"],
        actor=ACTOR_LLM,
        epigraph_node_id=epigrafe["id"],
    )

    assert respuesta.status_code == 200, respuesta.text
    cuerpo = respuesta.json()
    assert cuerpo["curriculum_node_id"] == tema["id"]
    assert cuerpo["epigraph"] is not None
    assert cuerpo["epigraph"]["curriculum_node_id"] == epigrafe["id"]
    assert cuerpo["epigraph"]["created"] is True

    mapeos = seeded_client.get(f"/api/v1/questions/{pregunta['id']}/topics").json()
    assert {mapeo["curriculum_node_id"] for mapeo in mapeos} == {tema["id"], epigrafe["id"]}
    assert len(_eventos(seeded_settings, acciones=("question.mapped",))) == 2


def test_un_epigrafe_de_otro_tema_se_rechaza_sin_escribir_nada(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """Un epígrafe ajeno no es «casi» lo mismo: es un error de quien lo manda."""
    conjunto = _conjunto(seeded_client)
    pregunta = _preguntas(seeded_client, conjunto["id"])[0]
    con_hijos = [nodo for nodo in _nodos(seeded_client, "topic") if nodo["children"]]
    tema = con_hijos[0]
    ajeno = next(nodo for nodo in con_hijos[1:] if nodo["children"])

    respuesta = _individual(
        seeded_client,
        pregunta["id"],
        tema["id"],
        epigraph_node_id=ajeno["children"][0]["id"],
    )

    assert respuesta.status_code == 409, respuesta.text
    assert "no es del tema" in respuesta.json()["detail"]
    assert seeded_client.get(f"/api/v1/questions/{pregunta['id']}/topics").json() == []
    assert _eventos(seeded_settings, acciones=("question.mapped",)) == []


def test_la_fila_con_epigrafe_ajeno_es_un_error_de_esa_fila_y_las_demas_siguen(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    conjunto = _conjunto(seeded_client)
    primera, segunda, _ = _preguntas(seeded_client, conjunto["id"])
    con_hijos = [nodo for nodo in _nodos(seeded_client, "topic") if nodo["children"]]
    tema = con_hijos[0]
    ajeno = next(nodo for nodo in con_hijos[1:] if nodo["children"])

    respuesta = _lote(
        seeded_client,
        [
            {
                "question_version_id": primera["id"],
                "curriculum_node_id": tema["id"],
                "epigraph_node_id": ajeno["children"][0]["id"],
            },
            {
                "question_version_id": segunda["id"],
                "curriculum_node_id": tema["id"],
                "epigraph_node_id": tema["children"][0]["id"],
            },
        ],
        actor=ACTOR_LLM,
    )

    cuerpo = respuesta.json()
    assert [fila["outcome"] for fila in cuerpo["results"]] == ["error", "created"]
    assert cuerpo["results"][1]["assignment"]["epigraph"] is not None
    assert seeded_client.get(f"/api/v1/questions/{primera['id']}/topics").json() == []


def test_el_actor_del_lote_viaja_a_la_auditoria_por_el_cuerpo_o_por_la_cabecera(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    conjunto = _conjunto(seeded_client)
    primera, segunda, _ = _preguntas(seeded_client, conjunto["id"])
    tema = _nodo(seeded_client, "topic")

    por_cuerpo = _lote(
        seeded_client,
        [{"question_version_id": primera["id"], "curriculum_node_id": tema["id"]}],
        actor=ACTOR_LLM,
    )
    por_cabecera = _lote(
        seeded_client,
        [{"question_version_id": segunda["id"], "curriculum_node_id": tema["id"]}],
        cabecera="revision:humano",
    )

    assert por_cuerpo.json()["created"] == por_cabecera.json()["created"] == 1
    actores = {
        evento["object_id"]: evento["actor"]
        for evento in _eventos(seeded_settings, acciones=("question.mapped",))
    }
    assert actores[por_cuerpo.json()["results"][0]["assignment"]["mapping_id"]] == ACTOR_LLM
    assert actores[por_cabecera.json()["results"][0]["assignment"]["mapping_id"]] == (
        "revision:humano"
    )


@pytest.mark.parametrize(
    "cuerpo",
    [
        {"assignments": []},
        {"assignments": [{"question_version_id": "p"}] * 201},
    ],
)
def test_un_lote_vacio_o_demasiado_largo_se_rechaza_entero(
    seeded_client: TestClient, cuerpo: dict[str, Any]
) -> None:
    """El tope de 200 es del contrato: un lote sin filas o de 201 no se acepta a medias."""
    respuesta = seeded_client.post(
        "/api/v1/questions/topics/bulk", json=cuerpo, headers=ALLOWED_ORIGIN
    )

    assert respuesta.status_code == 422, respuesta.text


def test_los_enunciados_fuera_de_temario_se_pueden_buscar_y_contar_por_motivo(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """La sección «No son preguntas» (D6) se lee buscando: con cientos de marcas, a ojo no."""
    conjunto = _conjunto(seeded_client)
    primera, segunda, tercera = _preguntas(seeded_client, conjunto["id"])

    _lote(
        seeded_client,
        [
            {
                "question_version_id": primera["id"],
                "exclusion_reason": "enunciado_roto",
                "reason": "el enunciado es un trozo de norma",
            },
            {
                "question_version_id": segunda["id"],
                "exclusion_reason": "enunciado_roto",
                "reason": "el enunciado es un trozo de norma",
            },
            {
                "question_version_id": tercera["id"],
                "exclusion_reason": "otra_administracion",
                "reason": "ley autonómica",
            },
        ],
        actor=ACTOR_LLM,
    )

    todas = seeded_client.get("/api/v1/question-exclusions").json()
    assert todas["total"] == 3
    assert todas["totals_by_reason"] == {"enunciado_roto": 2, "otra_administracion": 1}

    # La búsqueda va por el enunciado, y se combina con el motivo en lugar de sustituirlo.
    palabra = "Constitucion"
    encontrados = seeded_client.get(
        "/api/v1/question-exclusions",
        params={"reason": "enunciado_roto", "q": palabra},
    ).json()
    assert encontrados["total"] >= 1
    assert all(palabra.lower() in str(fila["stem"]).lower() for fila in encontrados["exclusions"])
    assert all(fila["reason"] == "enunciado_roto" for fila in encontrados["exclusions"])

    assert (
        seeded_client.get(
            "/api/v1/question-exclusions", params={"q": "una-frase-que-no-esta-en-ningun-enunciado"}
        ).json()["total"]
        == 0
    )
