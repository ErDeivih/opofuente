"""Pruebas de integración de las rutas de estudio (08_API-CONTRACT §10) por la API real.

Además del recorrido completo, aquí vive la prueba que sostiene el criterio de aceptación más
delicado del slice: **el payload de una sesión sin corregir no contiene la solución**. No se
comprueba solo que el campo venga vacío, sino que la respuesta entera —el JSON tal cual se sirve— no
lleve la clave por ninguna parte mientras no se pueda enseñar.
"""

from __future__ import annotations

import json
from typing import Any

from fastapi.testclient import TestClient

from opofuente.config import Settings

ALLOWED_ORIGIN = {"Origin": "http://127.0.0.1:5173"}


def _texto(preguntas: int, *, reservas: int = 0) -> str:
    """Un cuestionario con preguntas **distintas** y la misma respuesta correcta.

    El enunciado lleva un caso propio («caso A», «caso B»…) porque la normalización quita la
    numeración: un texto cuyas preguntas solo se diferenciaran en el número sería, con razón, la
    misma pregunta repetida, y la importación las contaría como «ya estaba».
    """
    lineas: list[str] = []
    for numero in range(1, preguntas + reservas + 1):
        marca = "[R] " if numero > preguntas else ""
        caso = chr(ord("A") + (numero - 1) % 26)
        lineas.append(
            f"{numero}. {marca}El plazo del procedimiento del caso {caso} es de diez dias habiles:"
        )
        for indice in range(4):
            lineas.append(f"{chr(ord('a') + indice)}) Opcion {chr(ord('A') + indice)}")
        lineas.append("Respuesta correcta: a")
        lineas.append("")
    return "\n".join(lineas)


def _conjunto(
    client: TestClient, *, preguntas: int, reservas: int = 0, activar: bool = True
) -> str:
    oposiciones = client.get("/api/v1/oppositions").json()
    activa = next(oposicion for oposicion in oposiciones if oposicion["active"])
    creado = client.post(
        "/api/v1/question-sets",
        json={
            "title": "Examen de prueba",
            "opposition_id": activa["id"],
            "set_type": "private_bank",
            "convocation_version_id": activa["active_convocation"]["id"],
        },
        headers=ALLOWED_ORIGIN,
    )
    assert creado.status_code == 201, creado.text
    conjunto = creado.json()
    importado = client.post(
        f"/api/v1/question-sets/{conjunto['id']}/parse",
        json={"kind": "questions", "text": _texto(preguntas, reservas=reservas)},
        headers=ALLOWED_ORIGIN,
    )
    assert importado.status_code == 200, importado.text
    if activar:
        claves = client.get(f"/api/v1/question-sets/{conjunto['id']}/answer-keys").json()
        activada = client.post(
            f"/api/v1/question-sets/{conjunto['id']}/answer-keys/{claves[0]['id']}/activate",
            headers=ALLOWED_ORIGIN,
        )
        assert activada.status_code == 200, activada.text
    return str(conjunto["id"])


def _crear_sesion(
    client: TestClient,
    set_id: str,
    *,
    cantidad: int = 4,
    feedback: str | None = "immediate",
) -> dict[str, Any]:
    oposiciones = client.get("/api/v1/oppositions").json()
    activa = next(oposicion for oposicion in oposiciones if oposicion["active"])
    cuerpo: dict[str, Any] = {
        "opposition_id": activa["id"],
        "mode": "practice",
        "sources": [
            {
                "question_set_id": set_id,
                "part_code": "primera_parte",
                "count": cantidad,
                "include_reserves": False,
            }
        ],
        "convocation_version_id": activa["active_convocation"]["id"],
    }
    if feedback is not None:
        cuerpo["feedback"] = feedback
    creada = client.post("/api/v1/study-sessions", json=cuerpo, headers=ALLOWED_ORIGIN)
    assert creada.status_code == 201, creada.text
    return creada.json()


def _arrancar(client: TestClient, session_id: str) -> dict[str, Any]:
    respuesta = client.post(f"/api/v1/study-sessions/{session_id}/start", headers=ALLOWED_ORIGIN)
    assert respuesta.status_code == 200, respuesta.text
    return respuesta.json()


def _texto_de(payload: object) -> str:
    """El payload servido, como texto: así se busca la solución en todo lo que viaja."""
    return json.dumps(payload, ensure_ascii=False)


# --- crear y leer -------------------------------------------------------------------------------


def test_crear_arrancar_y_leer_una_sesion(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    set_id = _conjunto(seeded_client, preguntas=6)

    creada = _crear_sesion(seeded_client, set_id, cantidad=4)
    assert creada["status"] == "draft"
    assert creada["total_questions"] == 4
    assert creada["key_label"] is not None
    assert creada["configuration"]["feedback"] == "immediate"

    arrancada = _arrancar(seeded_client, creada["id"])
    assert arrancada["status"] == "running"
    assert arrancada["started_at"] is not None

    detalle = seeded_client.get(f"/api/v1/study-sessions/{creada['id']}")
    assert detalle.status_code == 200
    assert detalle.json()["id"] == creada["id"]
    assert seeded_client.get("/api/v1/study-sessions/no-existe").status_code == 404

    listado = seeded_client.get("/api/v1/study-sessions").json()
    assert listado["total"] == 1
    assert listado["sessions"][0]["id"] == creada["id"]


def test_sin_clave_activa_la_sesion_no_se_crea(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    set_id = _conjunto(seeded_client, preguntas=4, activar=False)

    respuesta = seeded_client.post(
        "/api/v1/study-sessions",
        json={
            "opposition_id": seeded_client.get("/api/v1/oppositions").json()[0]["id"],
            "mode": "practice",
            "sources": [{"question_set_id": set_id, "part_code": "primera_parte", "count": 2}],
        },
        headers=ALLOWED_ORIGIN,
    )

    assert respuesta.status_code == 409, respuesta.text
    assert respuesta.json()["code"] == "classification_conflict"
    assert "clave activa" in respuesta.json()["detail"]


def test_un_modo_que_no_existe_no_entra_por_el_contrato(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """El contrato solo declara los modos que el slice implementa: lo demás es 422 del esquema."""
    respuesta = seeded_client.post(
        "/api/v1/study-sessions",
        json={
            "opposition_id": "op-1",
            "mode": "mock_exam",
            "sources": [{"question_set_id": "x", "part_code": "primera_parte"}],
        },
        headers=ALLOWED_ORIGIN,
    )

    assert respuesta.status_code == 422
    assert respuesta.json()["code"] == "validation_error"


# --- la solución no se filtra -------------------------------------------------------------------


def test_la_pregunta_de_una_sesion_sin_corregir_no_lleva_la_solucion(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """Criterio de aceptación de S07: ni la clave ni la explicación antes de responder."""
    set_id = _conjunto(seeded_client, preguntas=4)
    sesion = _arrancar(seeded_client, _crear_sesion(seeded_client, set_id)["id"])

    actual = seeded_client.get(f"/api/v1/study-sessions/{sesion['id']}/current-question")

    assert actual.status_code == 200
    cuerpo = actual.json()
    assert cuerpo["question"]["correction"] is None
    # La opción correcta es la «a»: no puede aparecer como solución en ningún sitio del payload.
    texto = _texto_de(cuerpo)
    assert "correct_option_keys" not in texto
    assert "outcome" not in texto
    # Y el esquema de la pregunta no tiene dónde ponerla.
    assert set(cuerpo["question"]) == {
        "session_question_id",
        "question_version_id",
        "stable_key",
        "position",
        "part_code",
        "is_reserve",
        "reserve_order",
        "stem",
        "question_type",
        "origin_type",
        "options",
        "answered",
        "chosen_option_keys",
        "elapsed_ms",
        "confidence",
        "correction",
    }


def test_con_correccion_al_final_la_sesion_no_lleva_la_solucion_hasta_terminar(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    set_id = _conjunto(seeded_client, preguntas=3)
    sesion = _arrancar(
        seeded_client, _crear_sesion(seeded_client, set_id, cantidad=3, feedback="at_end")["id"]
    )
    actual = seeded_client.get(f"/api/v1/study-sessions/{sesion['id']}/current-question").json()
    pregunta = actual["question"]["question_version_id"]

    respondida = seeded_client.post(
        f"/api/v1/study-sessions/{sesion['id']}/answers",
        json={"question_version_id": pregunta, "chosen_option_keys": ["a"], "elapsed_ms": 1000},
        headers=ALLOWED_ORIGIN,
    )

    assert respondida.status_code == 201, respondida.text
    assert respondida.json()["correction"] is None
    assert "correct_option_keys" not in _texto_de(respondida.json())

    revision = seeded_client.get(f"/api/v1/study-sessions/{sesion['id']}/review").json()
    assert revision["pending"] == 1
    assert "correct_option_keys" not in _texto_de(revision)

    terminada = seeded_client.post(
        f"/api/v1/study-sessions/{sesion['id']}/finish", headers=ALLOWED_ORIGIN
    )
    assert terminada.status_code == 200
    revision_final = seeded_client.get(f"/api/v1/study-sessions/{sesion['id']}/review").json()
    corregidas = [entrada for entrada in revision_final["entries"] if entrada["answered"]]
    assert corregidas[0]["correction"]["correct_option_keys"] == ["a"]


# --- responder ----------------------------------------------------------------------------------


def test_responder_dos_veces_lo_mismo_no_crea_otro_intento(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    set_id = _conjunto(seeded_client, preguntas=4)
    sesion = _arrancar(seeded_client, _crear_sesion(seeded_client, set_id)["id"])
    actual = seeded_client.get(f"/api/v1/study-sessions/{sesion['id']}/current-question").json()
    pregunta = actual["question"]["question_version_id"]
    cuerpo = {"question_version_id": pregunta, "chosen_option_keys": ["b"], "elapsed_ms": 2000}

    primera = seeded_client.post(
        f"/api/v1/study-sessions/{sesion['id']}/answers", json=cuerpo, headers=ALLOWED_ORIGIN
    )
    segunda = seeded_client.post(
        f"/api/v1/study-sessions/{sesion['id']}/answers",
        json=dict(cuerpo, elapsed_ms=9999),
        headers=ALLOWED_ORIGIN,
    )

    assert primera.status_code == 201 and primera.json()["saved"] is True
    assert segunda.status_code == 201 and segunda.json()["saved"] is False
    assert segunda.json()["already_answered"] is True
    assert primera.json()["attempt"]["id"] == segunda.json()["attempt"]["id"]
    # La penalización viaja exacta: un tercio, no un decimal.
    assert primera.json()["correction"]["score"]["fraction"] == "-1/3"
    assert primera.json()["correction"]["score"]["decimal"] == "-0.3333"

    cambiada = seeded_client.post(
        f"/api/v1/study-sessions/{sesion['id']}/answers",
        json=dict(cuerpo, chosen_option_keys=["a"]),
        headers=ALLOWED_ORIGIN,
    )
    assert cambiada.status_code == 409
    assert cambiada.json()["code"] == "attempt_frozen"


def test_una_respuesta_invalida_es_un_422_con_su_campo(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    set_id = _conjunto(seeded_client, preguntas=4)
    sesion = _arrancar(seeded_client, _crear_sesion(seeded_client, set_id)["id"])
    actual = seeded_client.get(f"/api/v1/study-sessions/{sesion['id']}/current-question").json()
    pregunta = actual["question"]["question_version_id"]

    respuesta = seeded_client.post(
        f"/api/v1/study-sessions/{sesion['id']}/answers",
        json={"question_version_id": pregunta, "chosen_option_keys": ["z"], "elapsed_ms": 10},
        headers=ALLOWED_ORIGIN,
    )

    assert respuesta.status_code == 422
    problema = respuesta.json()
    assert problema["code"] == "invalid_answer"
    assert problema["field_errors"][0]["field"] == "chosen_option_keys"


def test_responder_en_una_sesion_sin_arrancar_es_un_conflicto_de_estado(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    set_id = _conjunto(seeded_client, preguntas=4)
    sesion = _crear_sesion(seeded_client, set_id, cantidad=2)

    # La pregunta se puede leer, pero no responder: la sesión no está en marcha.
    actual = seeded_client.get(f"/api/v1/study-sessions/{sesion['id']}/current-question").json()
    respuesta = seeded_client.post(
        f"/api/v1/study-sessions/{sesion['id']}/answers",
        json={
            "question_version_id": actual["question"]["question_version_id"],
            "chosen_option_keys": ["a"],
            "elapsed_ms": 10,
        },
        headers=ALLOWED_ORIGIN,
    )

    assert respuesta.status_code == 409
    assert respuesta.json()["code"] == "invalid_session_state"


# --- navegar, terminar y revisar ----------------------------------------------------------------


def test_navegar_recorre_la_sesion(seeded_settings: Settings, seeded_client: TestClient) -> None:
    set_id = _conjunto(seeded_client, preguntas=6)
    sesion = _arrancar(seeded_client, _crear_sesion(seeded_client, set_id, cantidad=3)["id"])

    siguiente = seeded_client.post(
        f"/api/v1/study-sessions/{sesion['id']}/navigate",
        json={"direction": "next"},
        headers=ALLOWED_ORIGIN,
    )
    tercera = seeded_client.post(
        f"/api/v1/study-sessions/{sesion['id']}/navigate",
        json={"position": 3},
        headers=ALLOWED_ORIGIN,
    )

    assert siguiente.json()["question"]["position"] == 2
    assert tercera.json()["question"]["position"] == 3
    assert tercera.json()["pending"] == 3
    fuera = seeded_client.post(
        f"/api/v1/study-sessions/{sesion['id']}/navigate",
        json={"position": 9},
        headers=ALLOWED_ORIGIN,
    )
    assert fuera.status_code == 404


def test_terminar_da_el_resultado_por_partes_y_sin_calificacion_oficial(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """Caso calculado a mano por la API: 2 aciertos, 1 fallo y 1 blanco, con tercio de castigo."""
    set_id = _conjunto(seeded_client, preguntas=4)
    sesion = _arrancar(seeded_client, _crear_sesion(seeded_client, set_id)["id"])

    for posicion, claves in ((1, []), (2, ["b"]), (3, ["a"]), (4, ["a"])):
        actual = seeded_client.post(
            f"/api/v1/study-sessions/{sesion['id']}/navigate",
            json={"position": posicion},
            headers=ALLOWED_ORIGIN,
        ).json()
        respondida = seeded_client.post(
            f"/api/v1/study-sessions/{sesion['id']}/answers",
            json={
                "question_version_id": actual["question"]["question_version_id"],
                "chosen_option_keys": claves,
                "elapsed_ms": 1500,
            },
            headers=ALLOWED_ORIGIN,
        )
        assert respondida.status_code == 201, respondida.text

    resultado = seeded_client.post(
        f"/api/v1/study-sessions/{sesion['id']}/finish", headers=ALLOWED_ORIGIN
    )

    assert resultado.status_code == 200, resultado.text
    cuerpo = resultado.json()
    assert cuerpo["total"]["correct"] == 2
    assert cuerpo["total"]["wrong"] == 1
    assert cuerpo["total"]["blank"] == 1
    assert cuerpo["total"]["score"]["fraction"] == "5/3"
    assert cuerpo["total"]["score"]["decimal"] == "1.6667"
    assert cuerpo["parts"][0]["part_code"] == "primera_parte"
    assert cuerpo["parts"][0]["pass_score"] == 25.0
    assert cuerpo["official_available"] is False
    assert "no se declara aprobado ni suspenso" in cuerpo["official_note"]
    assert cuerpo["calculated_at"] is not None

    guardado = seeded_client.get(f"/api/v1/study-sessions/{sesion['id']}/result")
    assert guardado.status_code == 200
    assert guardado.json()["total"] == cuerpo["total"]

    otra_vez = seeded_client.post(
        f"/api/v1/study-sessions/{sesion['id']}/finish", headers=ALLOWED_ORIGIN
    )
    assert otra_vez.status_code == 200
    assert otra_vez.json()["total"] == cuerpo["total"]


def test_una_sesion_sin_terminar_no_da_resultado(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    set_id = _conjunto(seeded_client, preguntas=4)
    sesion = _arrancar(seeded_client, _crear_sesion(seeded_client, set_id, cantidad=2)["id"])

    respuesta = seeded_client.get(f"/api/v1/study-sessions/{sesion['id']}/result")

    assert respuesta.status_code == 409
    assert respuesta.json()["code"] == "invalid_session_state"


def test_la_revision_sin_responder_dice_que_falta_por_contestar(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    set_id = _conjunto(seeded_client, preguntas=3)
    sesion = _arrancar(seeded_client, _crear_sesion(seeded_client, set_id, cantidad=3)["id"])

    revision = seeded_client.get(f"/api/v1/study-sessions/{sesion['id']}/review").json()

    assert revision["partial"] is True
    assert revision["pending"] == 0
    assert revision["unanswered"] == 3
    assert len(revision["entries"]) == 3
    assert all(entrada["correction"] is None for entrada in revision["entries"])


def test_recalcular_con_una_clave_nueva_por_la_api(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """La ruta del recálculo (añadida a §10): puntuación exacta y comparación antes/después."""
    set_id = _conjunto(seeded_client, preguntas=3)
    sesion = _arrancar(seeded_client, _crear_sesion(seeded_client, set_id, cantidad=3)["id"])
    for posicion in (1, 2, 3):
        actual = seeded_client.post(
            f"/api/v1/study-sessions/{sesion['id']}/navigate",
            json={"position": posicion},
            headers=ALLOWED_ORIGIN,
        ).json()
        seeded_client.post(
            f"/api/v1/study-sessions/{sesion['id']}/answers",
            json={
                "question_version_id": actual["question"]["question_version_id"],
                "chosen_option_keys": ["a"],
                "elapsed_ms": 500,
            },
            headers=ALLOWED_ORIGIN,
        )
    antes = seeded_client.post(
        f"/api/v1/study-sessions/{sesion['id']}/finish", headers=ALLOWED_ORIGIN
    ).json()
    assert antes["total"]["correct"] == 3
    assert antes["recalculation"] is None

    # Una plantilla nueva corrige la clave: la buena pasa a ser la «b».
    plantilla = seeded_client.post(
        f"/api/v1/question-sets/{set_id}/parse",
        json={"kind": "answer_key", "text": "1. b\n2. b\n3. b\n"},
        headers=ALLOWED_ORIGIN,
    )
    assert plantilla.status_code == 200, plantilla.text
    claves = seeded_client.get(f"/api/v1/question-sets/{set_id}/answer-keys").json()
    activada = seeded_client.post(
        f"/api/v1/question-sets/{set_id}/answer-keys/{claves[-1]['id']}/activate",
        headers=ALLOWED_ORIGIN,
    )
    assert activada.status_code == 200, activada.text

    despues = seeded_client.post(
        f"/api/v1/study-sessions/{sesion['id']}/recalculate", headers=ALLOWED_ORIGIN
    )

    assert despues.status_code == 200, despues.text
    cuerpo = despues.json()
    assert cuerpo["total"]["correct"] == 0
    assert cuerpo["total"]["wrong"] == 3
    assert cuerpo["total"]["score"]["fraction"] == "-1", "tres errores con un tercio de castigo"
    comparacion = cuerpo["recalculation"]
    assert comparacion["changed"] is True
    assert comparacion["previous_total"]["fraction"] == "3"
    assert "plantilla v2" in (cuerpo["key_label"] or "")
    assert comparacion["previous_parts"][0]["correct"] == 3

    # Y la comparación sobrevive a una recarga: viaja con el resultado guardado.
    releído = seeded_client.get(f"/api/v1/study-sessions/{sesion['id']}/result").json()
    assert releído["recalculation"]["previous_total"]["fraction"] == "3"


def test_recalcular_una_sesion_que_no_ha_terminado_es_un_conflicto(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    set_id = _conjunto(seeded_client, preguntas=3)
    sesion = _arrancar(seeded_client, _crear_sesion(seeded_client, set_id, cantidad=2)["id"])

    respuesta = seeded_client.post(
        f"/api/v1/study-sessions/{sesion['id']}/recalculate", headers=ALLOWED_ORIGIN
    )

    assert respuesta.status_code == 409
    assert respuesta.json()["code"] == "invalid_session_state"
