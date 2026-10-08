"""La cola de revisión del propietario (F5): una tarjeta por pregunta, y decidirla en lote.

Lo que defienden estas pruebas es lo que hace utilizable la cola con cientos de propuestas dentro:

- **una pregunta, una tarjeta**: una pregunta con dos propuestas distintas —pasó en la corrida real,
  porque dos procesos se pisaron— sale una sola vez, con los dos candidatos dentro. Si saliera dos
  veces, aceptar una dejaría la otra puesta y la pregunta volvería a la cola;
- **decidir retira lo demás**: aceptar un tema confirma su mapeo y **retira** (no borra) las otras
  propuestas de esa pregunta, con su evento. Borrarlas las devolvería a la siguiente pasada del
  clasificador: la cola se llenaría de trabajo ya hecho;
- **lo aceptado manda**: una pregunta que ya tiene tema aceptado no ofrece candidatos: lo que tiene
  son propuestas que sobran, y se retiran;
- **decidir es un lote**: aceptar, corregir el tema y declarar fuera de temario caben en la
  **misma** llamada (`POST /questions/topics/bulk`), que es lo que permite despachar cientos sin
  una petición por pregunta.
"""

from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy import text

from opofuente.config import Settings
from opofuente.infrastructure.db import build_engine

ALLOWED_ORIGIN = {"Origin": "http://127.0.0.1:5173"}

TEXTO = (
    "1. La Constitucion espanola se aprobo en:\n"
    "a) 1976\n"
    "b) 1978\n"
    "Respuesta correcta: b\n"
    "2. El plazo de alegaciones es de diez dias habiles.\n"
    "a) Verdadero\n"
    "b) Falso\n"
    "Respuesta correcta: a\n"
    "3. El regimen local de Aragon se regula en:\n"
    "a) su ley de administracion local\n"
    "b) la Constitucion\n"
    "Respuesta correcta: a\n"
)


def _aplanar(nodos: list[dict[str, Any]]) -> list[dict[str, Any]]:
    planos: list[dict[str, Any]] = []
    for nodo in nodos:
        planos.append(nodo)
        planos.extend(_aplanar(nodo.get("children", [])))
    return planos


def _temas_del_programa(client: TestClient) -> dict[str, dict[str, Any]]:
    """Los nodos del programa **sembrado** por su ruta («I.1», «I.1.1»), leídos por la API real."""
    oposiciones = client.get("/api/v1/oppositions").json()
    convocatoria = next(item["active_convocation"]["id"] for item in oposiciones if item["active"])
    programa = client.get(f"/api/v1/convocations/{convocatoria}/curriculum").json()
    return {str(nodo["path"]): nodo for nodo in _aplanar(programa["nodes"])}


def _conjunto(client: TestClient, *, titulo: str) -> dict[str, Any]:
    oposiciones = client.get("/api/v1/oppositions").json()
    activa = next(oposicion for oposicion in oposiciones if oposicion["active"])
    respuesta = client.post(
        "/api/v1/question-sets",
        json={"title": titulo, "opposition_id": activa["id"], "set_type": "private_bank"},
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
    return list(client.get("/api/v1/questions", params={"set_id": set_id}).json()["questions"])


def _proponer(
    client: TestClient,
    *,
    question_version_id: str,
    node_id: str,
    confidence: float,
    reason: str,
    status: str | None = "provisional",
    epigraph_node_id: str | None = None,
) -> dict[str, Any]:
    """Escribe una propuesta por la ruta por lotes, que es la que usa el clasificador."""
    fila: dict[str, Any] = {
        "question_version_id": question_version_id,
        "curriculum_node_id": node_id,
        "confidence": confidence,
        "reason": reason,
    }
    if status is not None:
        fila["status"] = status
    if epigraph_node_id is not None:
        fila["epigraph_node_id"] = epigraph_node_id
    respuesta = client.post(
        "/api/v1/questions/topics/bulk",
        json={"assignments": [fila], "actor": "llm:deepseek-flash"},
        headers=ALLOWED_ORIGIN,
    )
    assert respuesta.status_code == 200, respuesta.text
    return dict(respuesta.json()["results"][0])


def _cola(client: TestClient, **parametros: Any) -> dict[str, Any]:
    respuesta = client.get("/api/v1/question-topic-proposals", params=parametros)
    assert respuesta.status_code == 200, respuesta.text
    return dict(respuesta.json())


def _conflictos(client: TestClient, **parametros: Any) -> dict[str, Any]:
    respuesta = client.get("/api/v1/question-topic-conflicts", params=parametros)
    assert respuesta.status_code == 200, respuesta.text
    return dict(respuesta.json())


def _retiradas(settings: Settings) -> list[dict[str, Any]]:
    """Las retiradas de mapeos, leídas de la auditoría (que la API no publica)."""
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.connect() as conexion:
            filas = conexion.execute(
                text(
                    "SELECT actor, object_id, before_json, after_json FROM audit_events "
                    "WHERE action = 'question.proposal_retired' ORDER BY created_at, id"
                )
            ).all()
    finally:
        engine.dispose()
    return [
        {
            "actor": str(fila[0]),
            "object_id": str(fila[1]),
            "before": str(fila[2]),
            "after": str(fila[3]),
        }
        for fila in filas
    ]


def _decisiones(client: TestClient, filas: list[dict[str, Any]]) -> dict[str, Any]:
    respuesta = client.post(
        "/api/v1/questions/topics/bulk",
        json={"assignments": filas},
        headers=ALLOWED_ORIGIN,
    )
    assert respuesta.status_code == 200, respuesta.text
    return dict(respuesta.json())


def test_la_cola_agrupa_por_pregunta_y_trae_el_enunciado_sus_opciones_y_el_motivo(
    seeded_client: TestClient,
) -> None:
    """Una tarjeta sin el enunciado delante no se puede juzgar: se lee entera, con el motivo."""
    conjunto = _conjunto(seeded_client, titulo="Banco de la cola")
    preguntas = _preguntas(seeded_client, conjunto["id"])
    temas = _temas_del_programa(seeded_client)
    _proponer(
        seeded_client,
        question_version_id=preguntas[0]["id"],
        node_id=temas["I.1"]["id"],
        confidence=0.6,
        reason="la duda era entre la Constitución y la ley ordinaria",
        epigraph_node_id=temas["I.1.1"]["id"],
    )

    cola = _cola(seeded_client)

    assert cola["total"] == 1, "una sola pregunta en la cola"
    tarjeta = cola["questions"][0]
    assert tarjeta["question_version_id"] == preguntas[0]["id"]
    assert tarjeta["stem"].startswith("La Constitucion espanola")
    assert [opcion["stable_key"] for opcion in tarjeta["options"]] == ["a", "b"]
    assert tarjeta["accepted"] is None
    assert len(tarjeta["proposals"]) == 1
    propuesta = tarjeta["proposals"][0]
    assert propuesta["topic"]["official_code"] == temas["I.1"]["official_code"]
    assert [epigrafe["official_code"] for epigrafe in propuesta["epigraphs"]] == [
        temas["I.1.1"]["official_code"]
    ]
    assert propuesta["confidence"] == 0.6
    assert propuesta["reason"] == "la duda era entre la Constitución y la ley ordinaria"
    # Nada de esto cuenta para el alumno: una propuesta sin confirmar no es una pregunta del tema.
    assert cola["questions"][0]["set_title"] == "Banco de la cola"


def test_una_pregunta_con_dos_propuestas_sale_una_sola_vez_y_al_aceptar_una_la_otra_se_retira(
    seeded_client: TestClient,
) -> None:
    """El caso real: dos corridas que se pisaron dejaron la misma pregunta con dos temas.

    El propietario tiene que verla **una vez**, con los dos candidatos dentro, y al elegir uno el
    otro no puede quedarse puesto: si quedara, la pregunta volvería a la cola y podría acabar con
    dos temas aceptados.
    """
    conjunto = _conjunto(seeded_client, titulo="Banco de las dos propuestas")
    pregunta = _preguntas(seeded_client, conjunto["id"])[0]
    temas = _temas_del_programa(seeded_client)
    _proponer(
        seeded_client,
        question_version_id=pregunta["id"],
        node_id=temas["I.1"]["id"],
        confidence=0.5,
        reason="de la primera corrida",
    )
    _proponer(
        seeded_client,
        question_version_id=pregunta["id"],
        node_id=temas["I.2"]["id"],
        confidence=0.62,
        reason="de la segunda corrida",
    )

    cola = _cola(seeded_client)

    assert cola["total"] == 1, "la pregunta sale una sola vez, no una por propuesta"
    assert [len(tarjeta["proposals"]) for tarjeta in cola["questions"]] == [2]
    candidatos = [
        propuesta["topic"]["official_code"] for propuesta in cola["questions"][0]["proposals"]
    ]
    assert len(set(candidatos)) == 2

    elegido = next(
        propuesta
        for propuesta in cola["questions"][0]["proposals"]
        if propuesta["topic"]["official_code"] == temas["I.2"]["official_code"]
    )
    resultado = _decisiones(
        seeded_client,
        [
            {
                "question_version_id": pregunta["id"],
                "curriculum_node_id": elegido["topic"]["node_id"],
                "status": "accepted",
                "reason": "elegido a mano en la revisión",
                "retire_others": True,
            }
        ],
    )

    assert resultado["promoted"] == 1, "el mapeo ya estaba como propuesta: se confirma"
    fila = resultado["results"][0]
    assert fila["outcome"] == "promoted"
    assert fila["assignment"]["status"] == "accepted"
    assert fila["assignment"]["retired"] == 1, "la otra propuesta se retira en la misma llamada"

    # La cola queda vacía y la pregunta tiene **un** tema aceptado, no dos. La propuesta retirada no
    # se borra: se queda marcada, y por eso se puede leer qué se propuso y qué se decidió.
    assert _cola(seeded_client)["total"] == 0
    mapeos = seeded_client.get(f"/api/v1/questions/{pregunta['id']}/topics").json()
    assert {(mapeo["title"], mapeo["status"]) for mapeo in mapeos} == {
        (temas["I.1"]["title"], "rejected"),
        (temas["I.2"]["title"], "accepted"),
    }


def test_una_pregunta_con_tema_aceptado_y_otra_propuesta_no_ofrece_candidatos(
    seeded_client: TestClient,
) -> None:
    """Lo aceptado manda: lo que queda son propuestas que sobran, y se retiran sin elegir nada."""
    conjunto = _conjunto(seeded_client, titulo="Banco de la aceptada y la propuesta")
    pregunta = _preguntas(seeded_client, conjunto["id"])[0]
    temas = _temas_del_programa(seeded_client)
    aceptada = _proponer(
        seeded_client,
        question_version_id=pregunta["id"],
        node_id=temas["I.1"]["id"],
        confidence=0.9,
        reason="clara",
        status="accepted",
    )
    _proponer(
        seeded_client,
        question_version_id=pregunta["id"],
        node_id=temas["I.3"]["id"],
        confidence=0.55,
        reason="de otra corrida",
    )

    cola = _cola(seeded_client)

    assert cola["total"] == 1
    tarjeta = cola["questions"][0]
    assert tarjeta["accepted"]["node_id"] == aceptada["assignment"]["curriculum_node_id"]
    assert [propuesta["topic"]["official_code"] for propuesta in tarjeta["proposals"]] == [
        temas["I.3"]["official_code"]
    ]

    # Retirar lo que sobra: se reescribe el tema aceptado (que ya está) y se retiran las demás.
    resultado = _decisiones(
        seeded_client,
        [
            {
                "question_version_id": pregunta["id"],
                "curriculum_node_id": tarjeta["accepted"]["node_id"],
                "status": "accepted",
                "retire_others": True,
                "reason": "ya tenía tema aceptado: sobran las demás propuestas",
            }
        ],
    )

    assert resultado["existing"] == 1
    assert resultado["results"][0]["assignment"]["retired"] == 1
    assert _cola(seeded_client)["total"] == 0


def test_fuera_de_temario_retira_las_propuestas_y_asignar_un_tema_levanta_la_marca(
    seeded_client: TestClient,
) -> None:
    """Una pregunta no puede estar fuera de temario y con una propuesta de tema a la vez."""
    conjunto = _conjunto(seeded_client, titulo="Banco del fuera de temario")
    pregunta = _preguntas(seeded_client, conjunto["id"])[0]
    temas = _temas_del_programa(seeded_client)
    _proponer(
        seeded_client,
        question_version_id=pregunta["id"],
        node_id=temas["I.1"]["id"],
        confidence=0.6,
        reason="dudosa",
    )

    resultado = _decisiones(
        seeded_client,
        [
            {
                "question_version_id": pregunta["id"],
                "exclusion_reason": "enunciado_roto",
                "reason": "las opciones están incompletas",
                "retire_others": True,
            }
        ],
    )

    assert resultado["excluded"] == 1
    assert _cola(seeded_client)["total"] == 0, "la propuesta se retira con la decisión"
    marcas = seeded_client.get("/api/v1/question-exclusions").json()["exclusions"]
    assert [marca["question_version_id"] for marca in marcas] == [pregunta["id"]]
    assert marcas[0]["note"] == "las opciones están incompletas"

    # Deshacer la exclusión es asignarle un tema: la marca se levanta con su evento. El mapeo no se
    # crea de cero —la propuesta retirada sigue en la tabla—, se **confirma**: es la misma fila que
    # vuelve a estar decidida, y así no se pierde lo que se propuso en su día.
    deshacer = _decisiones(
        seeded_client,
        [
            {
                "question_version_id": pregunta["id"],
                "curriculum_node_id": temas["I.1"]["id"],
                "status": "accepted",
                "reason": "sí es de este temario",
            }
        ],
    )
    assert deshacer["promoted"] == 1
    assert seeded_client.get("/api/v1/question-exclusions").json()["total"] == 0
    assert [
        mapeo["status"]
        for mapeo in seeded_client.get(f"/api/v1/questions/{pregunta['id']}/topics").json()
    ] == ["accepted"]


def test_la_cola_ordena_de_lo_mas_dudoso_a_lo_menos_y_pagina_por_preguntas(
    seeded_client: TestClient,
) -> None:
    """El propietario empieza por donde el modelo dudó más, y el total cuenta preguntas."""
    conjunto = _conjunto(seeded_client, titulo="Banco del orden")
    preguntas = _preguntas(seeded_client, conjunto["id"])
    temas = _temas_del_programa(seeded_client)
    for pregunta, confianza in zip(preguntas, (0.7, 0.5, 0.62), strict=True):
        _proponer(
            seeded_client,
            question_version_id=pregunta["id"],
            node_id=temas["I.1"]["id"],
            confidence=confianza,
            reason=f"confianza {confianza}",
        )

    cola = _cola(seeded_client)

    assert cola["total"] == 3
    assert [tarjeta["proposals"][0]["confidence"] for tarjeta in cola["questions"]] == [
        0.5,
        0.62,
        0.7,
    ]

    primera_pagina = _cola(seeded_client, limit=2, offset=0)
    segunda_pagina = _cola(seeded_client, limit=2, offset=2)
    assert [len(primera_pagina["questions"]), len(segunda_pagina["questions"])] == [2, 1]
    assert segunda_pagina["total"] == 3, "el total es el de la cola entera, no el de la página"
    assert segunda_pagina["questions"][0]["proposals"][0]["confidence"] == 0.7


def test_una_pregunta_con_dos_temas_sale_en_la_lista_con_su_actor_y_se_deja_con_uno(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """Lo que quedó torcido antes de esta tanda: una pregunta que cuenta en dos temas.

    Es lo que dejaron la catalogación heredada, las migraciones y las dos corridas que se pisaron.
    La lista tiene que enseñar **los dos temas con quién los decidió** —un tema de una migración y
    uno del modelo no se juzgan igual— y el propietario tiene que poder dejar uno solo; la
    aplicación no elige por su cuenta.
    """
    conjunto = _conjunto(seeded_client, titulo="Banco de los dos temas")
    pregunta = _preguntas(seeded_client, conjunto["id"])[0]
    temas = _temas_del_programa(seeded_client)
    primero = _proponer(
        seeded_client,
        question_version_id=pregunta["id"],
        node_id=temas["I.1"]["id"],
        confidence=1.0,
        reason="heredado del documento",
        status="accepted",
    )
    segundo = _proponer(
        seeded_client,
        question_version_id=pregunta["id"],
        node_id=temas["I.2"]["id"],
        confidence=0.8,
        reason="propuesta del modelo que se confirmó",
        status="accepted",
    )

    conflictos = _conflictos(seeded_client)

    assert conflictos["total"] == 1
    tarjeta = conflictos["questions"][0]
    assert tarjeta["question_version_id"] == pregunta["id"]
    assert tarjeta["stem"].startswith("La Constitucion")
    assert [tema["topic"]["path"] for tema in tarjeta["topics"]] == ["I.1", "I.2"]
    assert [tema["mapping_id"] for tema in tarjeta["topics"]] == [
        primero["assignment"]["mapping_id"],
        segundo["assignment"]["mapping_id"],
    ]
    # El actor sale de la auditoría: el primero lo firmó el lote (el modelo) y el segundo también,
    # pero con otra confianza, así que la lista permite distinguir qué pasó en cada uno.
    assert [tema["actor"] for tema in tarjeta["topics"]] == ["llm:deepseek-flash"] * 2

    # Y se resuelve eligiendo: se deja I.2 y se retira I.1, con su evento.
    elegido = next(tema for tema in tarjeta["topics"] if tema["topic"]["path"] == "I.2")
    resultado = _decisiones(
        seeded_client,
        [
            {
                "question_version_id": pregunta["id"],
                "curriculum_node_id": elegido["topic"]["node_id"],
                "status": "accepted",
                "retire_others": True,
                "reason": "se queda con I.2",
            }
        ],
    )

    assert resultado["results"][0]["assignment"]["retired"] == 1
    assert _conflictos(seeded_client)["total"] == 0, "ya no cuenta en dos temas"
    mapeos = seeded_client.get(f"/api/v1/questions/{pregunta['id']}/topics").json()
    assert {(mapeo["title"], mapeo["status"]) for mapeo in mapeos} == {
        (temas["I.1"]["title"], "rejected"),
        (temas["I.2"]["title"], "accepted"),
    }
    # Y queda auditado: quién lo retiró, de qué estado a cuál y con qué motivo.
    retiradas = _retiradas(seeded_settings)
    assert len(retiradas) == 1
    assert retiradas[0]["actor"] == "local", "lo decide el propietario, no la máquina"
    assert retiradas[0]["object_id"] == primero["assignment"]["mapping_id"]
    assert '"status": "accepted"' in retiradas[0]["before"]
    assert '"status": "rejected"' in retiradas[0]["after"]
    assert "se queda con I.2" in retiradas[0]["after"]

    # Nada se toca si nadie decide: la lista es de lectura.
    otra = _preguntas(seeded_client, _conjunto(seeded_client, titulo="Banco intacto")["id"])[0]
    for ruta in ("I.1", "I.2"):
        _proponer(
            seeded_client,
            question_version_id=otra["id"],
            node_id=temas[ruta]["id"],
            confidence=1.0,
            reason="heredado",
            status="accepted",
        )
    assert _conflictos(seeded_client)["total"] == 1
    assert len(seeded_client.get(f"/api/v1/questions/{otra['id']}/topics").json()) == 2
