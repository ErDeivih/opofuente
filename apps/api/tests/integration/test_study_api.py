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


def _texto_largo(preguntas: int, *, reservas: int = 0) -> str:
    """Un cuestionario largo con preguntas **distintas de verdad**, para montar un examen.

    `_texto` repite el caso cada 26 preguntas (le basta para una práctica), así que con 80 preguntas
    el
    banco se queda en 26: la huella ve la misma pregunta repetida y la cuenta como «ya estaba». Aquí
    el
    supuesto lleva su número, que no se normaliza, y las 90 preguntas son 90.
    """
    lineas: list[str] = []
    for numero in range(1, preguntas + reservas + 1):
        marca = "[R] " if numero > preguntas else ""
        lineas.append(
            f"{numero}. {marca}El supuesto practico numero {numero} se resuelve en diez dias:"
        )
        for indice in range(4):
            lineas.append(f"{chr(ord('a') + indice)}) Opcion {chr(ord('A') + indice)}")
        lineas.append("Respuesta correcta: a")
        lineas.append("")
    return "\n".join(lineas)


def _conjunto(
    client: TestClient,
    *,
    preguntas: int,
    reservas: int = 0,
    activar: bool = True,
    texto: str | None = None,
    titulo: str = "Examen de prueba",
) -> str:
    oposiciones = client.get("/api/v1/oppositions").json()
    activa = next(oposicion for oposicion in oposiciones if oposicion["active"])
    creado = client.post(
        "/api/v1/question-sets",
        json={
            "title": titulo,
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
        json={
            "kind": "questions",
            "text": texto if texto is not None else _texto(preguntas, reservas=reservas),
        },
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
            # La oposición activa, por su nombre y no por su posición en la lista: con tres perfiles
            # sembrados, «la primera» ya no es TAI y la parte «primera_parte» es suya.
            "opposition_id": next(
                oposicion["id"]
                for oposicion in seeded_client.get("/api/v1/oppositions").json()
                if oposicion["code"] == "tai-age"
            ),
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
    """El contrato declara exactamente los cinco modos que la aplicación sabe construir (DEBT-012).

    Un modo que no está en el vocabulario no entra por el esquema (422), y los cinco que sí están se
    pueden pedir sin recibir un «no implementado»: lo comprueba el resto de pruebas del módulo.
    """
    respuesta = seeded_client.post(
        "/api/v1/study-sessions",
        json={
            "opposition_id": "op-1",
            "mode": "examen_sorpresa",
            "sources": [{"question_set_id": "x", "part_code": "primera_parte"}],
        },
        headers=ALLOWED_ORIGIN,
    )

    assert respuesta.status_code == 422
    assert respuesta.json()["code"] == "validation_error"


def test_los_cinco_modos_del_vocabulario_se_pueden_pedir(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """Ningún modo del contrato responde «no implementado»: era el criterio 3 de DEBT-012.

    Se piden los cinco con un conjunto preparado para el que más exige (práctica y examen oficial) y
    se
    comprueba que el que falla, si falla, falla por **falta de material** y no por no estar
    construido.
    """
    set_id = _conjunto(seeded_client, preguntas=80, reservas=5, texto=_texto_largo(80, reservas=5))
    oposicion = _oposicion_activa(seeded_client)
    modos = ["practice", "official_exam", "mock_exam", "diagnostic", "error_review"]

    for modo in modos:
        respuesta = seeded_client.post(
            "/api/v1/study-sessions",
            json={
                "opposition_id": oposicion["id"],
                "mode": modo,
                "sources": (
                    []
                    if modo in ("diagnostic", "error_review")
                    else [
                        {
                            "question_set_id": set_id,
                            "part_code": "primera_parte",
                            **({"count": 3} if modo == "practice" else {}),
                        }
                    ]
                ),
                **({"review_limit": 5} if modo == "error_review" else {}),
            },
            headers=ALLOWED_ORIGIN,
        )
        if modo == "diagnostic":
            # El banco de esta prueba no tiene temas: el diagnóstico se niega por eso, no por no
            # existir.
            assert respuesta.status_code == 409, respuesta.text
            assert "diagnóstico necesita al menos" in respuesta.json()["detail"]
            continue
        if modo == "error_review":
            # Y el repaso se niega porque no hay nada vencido: tampoco por no estar implementado.
            assert respuesta.status_code == 409, respuesta.text
            assert "no hay nada vencido" in respuesta.json()["detail"]
            continue
        assert respuesta.status_code == 201, f"{modo}: {respuesta.text}"
        assert respuesta.json()["mode"] == modo


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


def _terminar_sesion_con_todo_a(
    client: TestClient, set_id: str, *, cantidad: int
) -> dict[str, Any]:
    """Una sesión terminada con todas las respuestas en la opción A. Devuelve su resultado."""
    sesion = _arrancar(client, _crear_sesion(client, set_id, cantidad=cantidad)["id"])
    for posicion in range(1, cantidad + 1):
        actual = client.post(
            f"/api/v1/study-sessions/{sesion['id']}/navigate",
            json={"position": posicion},
            headers=ALLOWED_ORIGIN,
        ).json()
        client.post(
            f"/api/v1/study-sessions/{sesion['id']}/answers",
            json={
                "question_version_id": actual["question"]["question_version_id"],
                "chosen_option_keys": ["a"],
                "elapsed_ms": 500,
            },
            headers=ALLOWED_ORIGIN,
        )
    return client.post(
        f"/api/v1/study-sessions/{sesion['id']}/finish", headers=ALLOWED_ORIGIN
    ).json()


def _activar_clave_corregida(client: TestClient, set_id: str) -> None:
    """Corrige la clave del conjunto (la buena pasa a ser la B) y la activa."""
    plantilla = client.post(
        f"/api/v1/question-sets/{set_id}/parse",
        json={"kind": "answer_key", "text": "1. b\n2. b\n3. b\n4. b\n"},
        headers=ALLOWED_ORIGIN,
    )
    assert plantilla.status_code == 200, plantilla.text
    claves = client.get(f"/api/v1/question-sets/{set_id}/answer-keys").json()
    activada = client.post(
        f"/api/v1/question-sets/{set_id}/answer-keys/{claves[-1]['id']}/activate",
        headers=ALLOWED_ORIGIN,
    )
    assert activada.status_code == 200, activada.text


def test_recalcular_en_bloque_todas_las_sesiones_del_conjunto(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """DEBT-013: corregir una clave recalcula **de una vez** todas las sesiones afectadas.

    El problema que resuelve: sin esto había que recalcular sesión a sesión, y las que nadie
    recordara se quedaban con la puntuación vieja para siempre. Lo que se comprueba aquí es que se
    recorren todas, que el informe dice qué cambió en cada una y que las que **no** han terminado no
    se tocan (se corregirán al terminar).
    """
    set_id = _conjunto(seeded_client, preguntas=4)
    primera = _terminar_sesion_con_todo_a(seeded_client, set_id, cantidad=3)
    segunda = _terminar_sesion_con_todo_a(seeded_client, set_id, cantidad=2)
    assert primera["total"]["correct"] == 3, "con la clave original, la A es correcta"
    assert segunda["total"]["correct"] == 2

    # Y una tercera sesión que **no** ha terminado: no puede entrar en el recálculo.
    en_marcha = _arrancar(seeded_client, _crear_sesion(seeded_client, set_id, cantidad=2)["id"])

    _activar_clave_corregida(seeded_client, set_id)

    respuesta = seeded_client.post(
        f"/api/v1/question-sets/{set_id}/recalculate-sessions", headers=ALLOWED_ORIGIN
    )

    assert respuesta.status_code == 200, respuesta.text
    cuerpo = respuesta.json()
    assert cuerpo["question_set_id"] == set_id
    assert cuerpo["key_version"] == 2
    assert cuerpo["changed"] == 2, "las dos sesiones terminadas cambian de puntuación"
    identificadores = {cambio["session_id"] for cambio in cuerpo["sessions"]}
    assert en_marcha["id"] not in identificadores, "una sesión en marcha se corrige al terminar"
    assert len(cuerpo["sessions"]) == 2

    for cambio in cuerpo["sessions"]:
        assert cambio["changed"] is True, "todo lo que estaba en A pasa a estar mal"
        # Lo que importa es que la puntuación **cambia** y no se queda con la vieja; el valor
        # concreto lo calcula el dominio y tiene su propia prueba aritmética.
        assert cambio["new_total"] != cambio["previous_total"]
        assert cambio["new_total"].startswith("-"), "todo mal con castigo da puntuación negativa"
        assert "plantilla v1" in cambio["previous_key_label"]
        assert "plantilla v2" in cambio["new_key_label"]

    # Y las puntuaciones de antes se conservan: recalcular no borra lo que se dijo.
    primera_releida = seeded_client.get(
        f"/api/v1/study-sessions/{primera['session_id']}/result"
    ).json()
    assert primera_releida["recalculation"]["previous_total"]["fraction"] == "3"


def test_recalcular_en_bloque_sin_sesiones_terminadas_lo_dice(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """Sin sesiones terminadas no hay nada que recalcular, y se dice en lugar de dar un «hecho»."""
    set_id = _conjunto(seeded_client, preguntas=2)

    respuesta = seeded_client.post(
        f"/api/v1/question-sets/{set_id}/recalculate-sessions", headers=ALLOWED_ORIGIN
    )

    assert respuesta.status_code == 200, respuesta.text
    assert respuesta.json()["sessions"] == []
    assert respuesta.json()["changed"] == 0
    assert "no hay sesiones terminadas" in respuesta.json()["detail"]


def test_recalcular_en_bloque_sin_clave_activa_es_un_conflicto(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """Sin plantilla activa no hay con qué recalcular: se dice, no se inventa una puntuación.

    `_conjunto` activa la plantilla por defecto; aquí se crea el conjunto **sin activarla**, que es
    como nace de verdad (`activar=False`), y entonces recalcular no tiene con qué.
    """
    set_id = _conjunto(seeded_client, preguntas=2, activar=False)

    respuesta = seeded_client.post(
        f"/api/v1/question-sets/{set_id}/recalculate-sessions", headers=ALLOWED_ORIGIN
    )

    assert respuesta.status_code == 409, respuesta.text
    assert respuesta.json()["code"] == "classification_conflict"


def test_recalcular_en_bloque_un_conjunto_inexistente_es_un_404(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    respuesta = seeded_client.post(
        "/api/v1/question-sets/no-existe/recalculate-sessions", headers=ALLOWED_ORIGIN
    )

    assert respuesta.status_code == 404, respuesta.text


def test_decir_cuantas_sesiones_quedan_desactualizadas_tras_activar_una_clave(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """DEBT-013, criterio 3: la pantalla puede decir cuántas sesiones se quedan atrás.

    El recálculo en bloque dice qué cambió **después**; esto dice qué hace falta **antes**, que es
    lo que evita descubrir la clave corregida sesión a sesión. Se comprueba además que el número no
    es decorativo: baja a cero cuando se recalcula, así que mide lo que dice medir.
    """
    set_id = _conjunto(seeded_client, preguntas=4)
    terminadas = [
        _terminar_sesion_con_todo_a(seeded_client, set_id, cantidad=3),
        _terminar_sesion_con_todo_a(seeded_client, set_id, cantidad=2),
    ]
    # Una sesión en marcha **no** cuenta: se corrige al terminar, no ahora.
    _arrancar(seeded_client, _crear_sesion(seeded_client, set_id, cantidad=2)["id"])

    al_dia = seeded_client.get(f"/api/v1/question-sets/{set_id}/outdated-sessions")
    assert al_dia.status_code == 200, al_dia.text
    assert al_dia.json()["key_version"] == 1
    assert al_dia.json()["finished"] == 2, "las dos sesiones terminadas, y solo esas"
    assert al_dia.json()["up_to_date"] == 2
    assert al_dia.json()["outdated"] == 0, "todavía no se ha activado nada nuevo"

    _activar_clave_corregida(seeded_client, set_id)

    desactualizadas = seeded_client.get(f"/api/v1/question-sets/{set_id}/outdated-sessions").json()
    assert desactualizadas["key_version"] == 2
    assert desactualizadas["outdated"] == 2
    assert desactualizadas["up_to_date"] == 0
    assert desactualizadas["without_evaluation"] == 0
    # Los tres recuentos suman las terminadas: un número que no cuadra no se podría comprobar.
    assert (
        desactualizadas["up_to_date"]
        + desactualizadas["outdated"]
        + desactualizadas["without_evaluation"]
        == desactualizadas["finished"]
    )
    # Y se dice **cuáles**, no solo cuántas: con el mismo id que devuelve el recálculo.
    assert set(desactualizadas["outdated_session_ids"]) == {
        sesion["session_id"] for sesion in terminadas
    }

    # Después de recalcular, el número baja a cero: mide el estado real, no un «hubo cambios».
    rehecho = seeded_client.post(
        f"/api/v1/question-sets/{set_id}/recalculate-sessions", headers=ALLOWED_ORIGIN
    )
    assert rehecho.status_code == 200, rehecho.text
    assert rehecho.json()["changed"] == 2

    despues = seeded_client.get(f"/api/v1/question-sets/{set_id}/outdated-sessions").json()
    assert despues["outdated"] == 0
    assert despues["up_to_date"] == 2
    assert despues["outdated_session_ids"] == []


def test_una_sesion_terminada_sin_correcciones_no_se_cuenta_como_desactualizada(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """Una sesión terminada sin ninguna corrección guardada se cuenta aparte, no como pendiente.

    Contarla como desactualizada dejaría un número que no bajaría nunca: no hay nada que comparar
    con la clave, ni nada que recalcular.
    """
    set_id = _conjunto(seeded_client, preguntas=2)
    sesion = _arrancar(seeded_client, _crear_sesion(seeded_client, set_id, cantidad=2)["id"])
    terminada = seeded_client.post(
        f"/api/v1/study-sessions/{sesion['id']}/finish", headers=ALLOWED_ORIGIN
    )
    assert terminada.status_code == 200, terminada.text

    respuesta = seeded_client.get(f"/api/v1/question-sets/{set_id}/outdated-sessions")

    assert respuesta.status_code == 200, respuesta.text
    cuerpo = respuesta.json()
    assert cuerpo["finished"] == 1
    assert cuerpo["without_evaluation"] == 1
    assert cuerpo["outdated"] == 0
    assert cuerpo["up_to_date"] == 0
    assert "ninguna corrección guardada" in cuerpo["detail"]


def test_las_sesiones_desactualizadas_de_un_conjunto_inexistente_es_un_404(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    respuesta = seeded_client.get("/api/v1/question-sets/no-existe/outdated-sessions")

    assert respuesta.status_code == 404, respuesta.text


# --- simulacro y diagnóstico (DEBT-012) -----------------------------------------------------------


def _oposicion_activa(client: TestClient) -> dict[str, Any]:
    oposiciones = client.get("/api/v1/oppositions").json()
    return next(oposicion for oposicion in oposiciones if oposicion["active"])


def _csv_con_temas(preguntas: int) -> str:
    """Un CSV con la columna `topic`: es la vía documentada para asignar una pregunta a su tema.

    Los temas son rutas del programa sembrado (`I.1`, `I.2`, `I.3`), las mismas que ve la pantalla.
    """
    lineas = ["enunciado;op1;op2;clave;tema"]
    for numero in range(1, preguntas + 1):
        caso = chr(ord("A") + (numero - 1) % 26)
        tema = f"I.{((numero - 1) % 3) + 1}"
        lineas.append(f"Pregunta con tema del caso {caso} numero {numero};Verdadero;Falso;a;{tema}")
    return "\n".join(lineas)


def _activar_ultima_clave(client: TestClient, set_id: str) -> None:
    """Activa la plantilla más nueva del conjunto.

    Importar un CSV con la columna de la clave crea una plantilla **en borrador**: sin activarla,
    las
    preguntas importadas no tienen desenlace con el que corregirlas y contestarlas bien saldría mal.
    """
    claves = client.get(f"/api/v1/question-sets/{set_id}/answer-keys").json()
    activada = client.post(
        f"/api/v1/question-sets/{set_id}/answer-keys/{claves[-1]['id']}/activate",
        headers=ALLOWED_ORIGIN,
    )
    assert activada.status_code == 200, activada.text


def test_un_simulacro_monta_el_perfil_exacto_y_no_se_llama_oficial(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """`mock_exam`: mismo perfil que el examen, corrección al final y sin llamarse oficial."""
    set_id = _conjunto(seeded_client, preguntas=80, reservas=5, texto=_texto_largo(80, reservas=5))
    oposicion = _oposicion_activa(seeded_client)

    respuesta = seeded_client.post(
        "/api/v1/study-sessions",
        json={
            "opposition_id": oposicion["id"],
            "mode": "mock_exam",
            "sources": [{"question_set_id": set_id, "part_code": "primera_parte"}],
        },
        headers=ALLOWED_ORIGIN,
    )

    assert respuesta.status_code == 201, respuesta.text
    sesion = respuesta.json()
    assert sesion["mode"] == "mock_exam"
    assert sesion["total_questions"] == 85, "80 ordinarias y las 5 reservas de la convocatoria"
    assert sesion["time_limit_minutes"] == 120, "el simulacro usa el tiempo del perfil"
    assert sesion["configuration"]["feedback"] == "at_end", "no corrige mientras se contesta"
    # Lo que la composición dice de sí misma: sin nada visto antes, no repite nada.
    assert "ninguna de sus preguntas se había intentado" in sesion["configuration"]["note"]

    # Y al terminar, la puntuación se explica como la de un simulacro: **no** es un examen oficial.
    arrancada = _arrancar(seeded_client, sesion["id"])
    assert arrancada["status"] == "running"
    terminada = seeded_client.post(
        f"/api/v1/study-sessions/{sesion['id']}/finish", headers=ALLOWED_ORIGIN
    )
    assert terminada.status_code == 200, terminada.text
    nota = terminada.json()["official_note"]
    assert "simulacro" in nota
    assert "no es un examen oficial" in nota
    assert terminada.json()["official_available"] is False


def test_un_simulacro_evita_las_preguntas_vistas_hace_poco(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """Con banco de sobra, las preguntas recientes se quedan fuera y la nota lo dice."""
    set_id = _conjunto(seeded_client, preguntas=90, reservas=5, texto=_texto_largo(90, reservas=5))
    oposicion = _oposicion_activa(seeded_client)

    # Una práctica con las **cinco primeras** preguntas: son las que el banco ofrece primero, así
    # que
    # sin evitarlas serían también las cinco primeras del simulacro.
    practica = _arrancar(seeded_client, _crear_sesion(seeded_client, set_id, cantidad=5)["id"])
    vistas: set[str] = set()
    for posicion in range(1, 6):
        actual = seeded_client.post(
            f"/api/v1/study-sessions/{practica['id']}/navigate",
            json={"position": posicion},
            headers=ALLOWED_ORIGIN,
        ).json()
        vistas.add(actual["question"]["question_version_id"])
        seeded_client.post(
            f"/api/v1/study-sessions/{practica['id']}/answers",
            json={
                "question_version_id": actual["question"]["question_version_id"],
                "chosen_option_keys": ["a"],
                "elapsed_ms": 400,
            },
            headers=ALLOWED_ORIGIN,
        )
    seeded_client.post(f"/api/v1/study-sessions/{practica['id']}/finish", headers=ALLOWED_ORIGIN)
    assert len(vistas) == 5

    simulacro = seeded_client.post(
        "/api/v1/study-sessions",
        json={
            "opposition_id": oposicion["id"],
            "mode": "mock_exam",
            "sources": [{"question_set_id": set_id, "part_code": "primera_parte"}],
        },
        headers=ALLOWED_ORIGIN,
    )

    assert simulacro.status_code == 201, simulacro.text
    cuerpo = simulacro.json()
    assert "ninguna de sus preguntas se había intentado" in cuerpo["configuration"]["note"]

    # Y no es solo la nota: ninguna de las vistas entra en la composición, porque hay 85 sin ver.
    revision = seeded_client.get(f"/api/v1/study-sessions/{cuerpo['id']}/review")
    assert revision.status_code == 200, revision.text
    compuestas = {entrada["question_version_id"] for entrada in revision.json()["entries"]}
    assert compuestas & vistas == set(), "el simulacro ha repetido una pregunta vista hace poco"
    assert len(compuestas) == 85


def test_un_simulacro_sin_banco_suficiente_repite_y_lo_dice(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """Si no hay banco para no repetir, repite —y lo cuenta— en lugar de no montar el examen.

    El aviso es la diferencia entre un simulacro útil y uno que mide la memoria de ayer sin decirlo.
    """
    set_id = _conjunto(seeded_client, preguntas=80, reservas=5, texto=_texto_largo(80, reservas=5))
    oposicion = _oposicion_activa(seeded_client)

    practica = _arrancar(seeded_client, _crear_sesion(seeded_client, set_id, cantidad=5)["id"])
    for posicion in range(1, 6):
        actual = seeded_client.post(
            f"/api/v1/study-sessions/{practica['id']}/navigate",
            json={"position": posicion},
            headers=ALLOWED_ORIGIN,
        ).json()
        seeded_client.post(
            f"/api/v1/study-sessions/{practica['id']}/answers",
            json={
                "question_version_id": actual["question"]["question_version_id"],
                "chosen_option_keys": ["a"],
                "elapsed_ms": 400,
            },
            headers=ALLOWED_ORIGIN,
        )
    seeded_client.post(f"/api/v1/study-sessions/{practica['id']}/finish", headers=ALLOWED_ORIGIN)

    simulacro = seeded_client.post(
        "/api/v1/study-sessions",
        json={
            "opposition_id": oposicion["id"],
            "mode": "mock_exam",
            "sources": [{"question_set_id": set_id, "part_code": "primera_parte"}],
        },
        headers=ALLOWED_ORIGIN,
    )

    assert simulacro.status_code == 201, simulacro.text
    nota = simulacro.json()["configuration"]["note"]
    assert "5 de 85 pregunta(s) ya se habían intentado" in nota
    assert simulacro.json()["total_questions"] == 85, "el perfil se respeta aunque haya que repetir"


def test_un_diagnostico_compone_una_muestra_pequena_por_tema(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """`diagnostic`: la muestra la pone el servidor, se reparte por temas y se declara."""
    # Un conjunto con **una** pregunta sin tema: se queda fuera de la muestra y el informe lo
    # cuenta.
    set_id = _conjunto(seeded_client, preguntas=1)
    oposicion = _oposicion_activa(seeded_client)
    importado = seeded_client.post(
        f"/api/v1/question-sets/{set_id}/parse",
        json={
            "kind": "csv",
            "text": _csv_con_temas(6),
            "mapping": {
                "stem": "enunciado",
                "options": ["op1", "op2"],
                "correct": "clave",
                "topic": "tema",
            },
        },
        headers=ALLOWED_ORIGIN,
    )
    assert importado.status_code == 200, importado.text
    _activar_ultima_clave(seeded_client, set_id)

    respuesta = seeded_client.post(
        "/api/v1/study-sessions",
        json={"opposition_id": oposicion["id"], "mode": "diagnostic", "sources": []},
        headers=ALLOWED_ORIGIN,
    )

    assert respuesta.status_code == 201, respuesta.text
    sesion = respuesta.json()
    assert sesion["total_questions"] == 6, "dos preguntas por tema en la muestra"
    assert sesion["mode"] == "diagnostic"
    assert sesion["configuration"]["sources"] == []
    assert "6 preguntas en 3 tema(s) de 3 con preguntas" in sesion["configuration"]["note"]
    # La pregunta sin tema no entra en la muestra, y se dice que se ha quedado fuera.
    assert "1 pregunta(s) del banco no tienen tema asignado" in sesion["configuration"]["note"]

    # Y las preguntas de la muestra no llevan parte: un diagnóstico no es un examen de una parte.
    revision = seeded_client.get(f"/api/v1/study-sessions/{sesion['id']}/review").json()
    assert {entrada["part_code"] for entrada in revision["entries"]} == {None}


def test_la_lectura_del_diagnostico_da_por_tema_un_intervalo(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """La lectura por temas: lo contestado, su intervalo y el tamaño de la muestra delante."""
    set_id = _conjunto(seeded_client, preguntas=1)
    oposicion = _oposicion_activa(seeded_client)
    seeded_client.post(
        f"/api/v1/question-sets/{set_id}/parse",
        json={
            "kind": "csv",
            "text": _csv_con_temas(6),
            "mapping": {
                "stem": "enunciado",
                "options": ["op1", "op2"],
                "correct": "clave",
                "topic": "tema",
            },
        },
        headers=ALLOWED_ORIGIN,
    )
    _activar_ultima_clave(seeded_client, set_id)
    sesion = seeded_client.post(
        "/api/v1/study-sessions",
        json={"opposition_id": oposicion["id"], "mode": "diagnostic", "sources": []},
        headers=ALLOWED_ORIGIN,
    ).json()
    _arrancar(seeded_client, sesion["id"])

    # Se contestan las tres primeras de la muestra (una por tema, porque la muestra es round-robin).
    for posicion in range(1, 4):
        actual = seeded_client.post(
            f"/api/v1/study-sessions/{sesion['id']}/navigate",
            json={"position": posicion},
            headers=ALLOWED_ORIGIN,
        ).json()
        assert actual.get("question") is not None, actual
        seeded_client.post(
            f"/api/v1/study-sessions/{sesion['id']}/answers",
            json={
                "question_version_id": actual["question"]["question_version_id"],
                "chosen_option_keys": ["a"],
                "elapsed_ms": 300,
            },
            headers=ALLOWED_ORIGIN,
        )

    respuesta = seeded_client.get(f"/api/v1/study-sessions/{sesion['id']}/diagnostic")

    assert respuesta.status_code == 200, respuesta.text
    lectura = respuesta.json()
    assert lectura["session_id"] == sesion["id"]
    assert lectura["mode"] == "diagnostic"
    assert lectura["sample_size"] == 6
    assert lectura["answered"] == 3
    assert len(lectura["topics"]) == 3, "un tema por cada tema de la muestra"
    for ficha in lectura["topics"]:
        assert ficha["answered"] == 1
        assert ficha["correct"] == 1
        # Con una sola respuesta el intervalo es ancho, y la ficha lo dice: no es un dominio.
        assert ficha["interval"] is not None
        assert ficha["interval"]["low"] < 0.4
        assert ficha["interval"]["high"] == 1.0
        assert "el intervalo es ancho" in ficha["note"]
    assert "no son una nota ni un dominio del tema" in lectura["detail"]


def test_un_diagnostico_corrige_al_terminar_y_no_deja_elegirlo(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """La corrección de un diagnóstico es al terminar, y pedir otra cosa se dice con un 409.

    No es una manía: la muestra mide lo que sabes ahora, y ver la respuesta a mitad mejoraría las
    siguientes preguntas del mismo tema —que es justo lo que se está midiendo—.
    """
    set_id = _conjunto(seeded_client, preguntas=1)
    oposicion = _oposicion_activa(seeded_client)
    seeded_client.post(
        f"/api/v1/question-sets/{set_id}/parse",
        json={
            "kind": "csv",
            "text": _csv_con_temas(6),
            "mapping": {
                "stem": "enunciado",
                "options": ["op1", "op2"],
                "correct": "clave",
                "topic": "tema",
            },
        },
        headers=ALLOWED_ORIGIN,
    )
    _activar_ultima_clave(seeded_client, set_id)

    creado = seeded_client.post(
        "/api/v1/study-sessions",
        json={"opposition_id": oposicion["id"], "mode": "diagnostic", "sources": []},
        headers=ALLOWED_ORIGIN,
    )
    assert creado.status_code == 201, creado.text
    assert creado.json()["feedback"] == "at_end"

    rechazado = seeded_client.post(
        "/api/v1/study-sessions",
        json={
            "opposition_id": oposicion["id"],
            "mode": "diagnostic",
            "sources": [],
            "feedback": "immediate",
        },
        headers=ALLOWED_ORIGIN,
    )
    assert rechazado.status_code == 409, rechazado.text
    assert "corrige al terminar" in rechazado.json()["detail"]


def test_un_diagnostico_con_dos_conjuntos_dice_de_donde_sale_cada_plantilla(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """La muestra puede salir de **varios** conjuntos: la sesión dice cuál es cada plantilla.

    Es el caso que se rompía al decir solo «plantilla v1»: dos conjuntos distintos con su v1 son dos
    claves distintas, y una etiqueta que las junta miente sobre con qué se corrige.
    """
    primera = _conjunto(seeded_client, preguntas=1, titulo="Conjunto A")
    segunda = _conjunto(seeded_client, preguntas=1, titulo="Conjunto B")
    oposicion = _oposicion_activa(seeded_client)
    for set_id, sufijo in ((primera, "A"), (segunda, "B")):
        importado = seeded_client.post(
            f"/api/v1/question-sets/{set_id}/parse",
            json={
                "kind": "csv",
                "text": "\n".join(
                    [
                        "enunciado;op1;op2;clave;tema",
                        f"Pregunta uno del conjunto {sufijo};Verdadero;Falso;a;I.1",
                        f"Pregunta dos del conjunto {sufijo};Verdadero;Falso;a;I.2",
                        f"Pregunta tres del conjunto {sufijo};Verdadero;Falso;a;I.3",
                    ]
                ),
                "mapping": {
                    "stem": "enunciado",
                    "options": ["op1", "op2"],
                    "correct": "clave",
                    "topic": "tema",
                },
            },
            headers=ALLOWED_ORIGIN,
        )
        assert importado.status_code == 200, importado.text
        _activar_ultima_clave(seeded_client, set_id)

    respuesta = seeded_client.post(
        "/api/v1/study-sessions",
        json={"opposition_id": oposicion["id"], "mode": "diagnostic", "sources": []},
        headers=ALLOWED_ORIGIN,
    )

    assert respuesta.status_code == 201, respuesta.text
    sesion = respuesta.json()
    # Seis preguntas: dos por tema, y con tres temas la muestra entera cabe (dos de cada conjunto).
    assert sesion["total_questions"] == 6
    assert sesion["question_set_id"] is None, "la muestra sale de más de un conjunto"
    assert sesion["answer_key_version_id"] is None
    # Y la etiqueta nombra los dos conjuntos: no se funden en una sola «plantilla v1».
    assert "Conjunto A: plantilla v" in sesion["key_label"]
    assert "Conjunto B: plantilla v" in sesion["key_label"]


def test_la_lectura_por_temas_no_vale_para_una_practica(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """Se dice con un 409: una muestra pequeña no se lee igual que la nota de una práctica."""
    set_id = _conjunto(seeded_client, preguntas=4)
    practica = _crear_sesion(seeded_client, set_id, cantidad=2)

    respuesta = seeded_client.get(f"/api/v1/study-sessions/{practica['id']}/diagnostic")

    assert respuesta.status_code == 409, respuesta.text
    assert respuesta.json()["code"] == "unsupported"
    assert "es del diagnóstico" in respuesta.json()["detail"]


def test_un_diagnostico_sin_temas_suficientes_no_se_monta(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """Sin temas no hay muestra estratificada: se dice qué falta en lugar de sortear preguntas."""
    _conjunto(seeded_client, preguntas=6)
    oposicion = _oposicion_activa(seeded_client)

    respuesta = seeded_client.post(
        "/api/v1/study-sessions",
        json={"opposition_id": oposicion["id"], "mode": "diagnostic", "sources": []},
        headers=ALLOWED_ORIGIN,
    )

    assert respuesta.status_code == 409, respuesta.text
    assert respuesta.json()["code"] == "unsupported"
    assert "el banco solo tiene preguntas de 0 tema(s)" in respuesta.json()["detail"]
    assert "un diagnóstico necesita al menos 3" in respuesta.json()["detail"]


def _tema_con_preguntas(client: TestClient, *, ruta: str = "I.1") -> str:
    """El id del nodo del programa con esa ruta, en la convocatoria activa."""
    oposicion = _oposicion_activa(client)
    convocatoria = oposicion["active_convocation"]["id"]
    nodos = client.get(f"/api/v1/convocations/{convocatoria}/curriculum").json()["nodes"]

    def buscar(items: list[dict[str, Any]]) -> str | None:
        for nodo in items:
            if nodo["path"] == ruta:
                return str(nodo["id"])
            encontrado = buscar(nodo["children"])
            if encontrado is not None:
                return encontrado
        return None

    encontrado = buscar(nodos)
    assert encontrado is not None, f"el programa sembrado no tiene el nodo {ruta}"
    return encontrado


def test_una_practica_por_tema_la_compone_la_catalogacion_del_tema(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """`practice` con `curriculum_node_id`: las preguntas del tema, y ni una de otro (S13).

    La composición **no** la elige quien estudia: se practica lo que está catalogado en el tema con
    mapeo aceptado, que es lo que dice la cifra «preguntas: N» del Programa. Se comprueba en las dos
    direcciones: entran las del tema pedido y **no** entran las de los otros dos.
    """
    set_id = _conjunto(seeded_client, preguntas=1)
    oposicion = _oposicion_activa(seeded_client)
    # Seis preguntas repartidas entre I.1, I.2 e I.3 (dos de cada una).
    importado = seeded_client.post(
        f"/api/v1/question-sets/{set_id}/parse",
        json={
            "kind": "csv",
            "text": _csv_con_temas(6),
            "mapping": {
                "stem": "enunciado",
                "options": ["op1", "op2"],
                "correct": "clave",
                "topic": "tema",
            },
        },
        headers=ALLOWED_ORIGIN,
    )
    assert importado.status_code == 200, importado.text
    _activar_ultima_clave(seeded_client, set_id)
    nodo = _tema_con_preguntas(seeded_client, ruta="I.1")

    respuesta = seeded_client.post(
        "/api/v1/study-sessions",
        json={
            "opposition_id": oposicion["id"],
            "mode": "practice",
            "sources": [],
            "curriculum_node_id": nodo,
        },
        headers=ALLOWED_ORIGIN,
    )

    assert respuesta.status_code == 201, respuesta.text
    sesion = respuesta.json()
    assert sesion["mode"] == "practice"
    assert sesion["total_questions"] == 2, "las dos preguntas catalogadas en I.1"
    assert sesion["configuration"]["sources"] == [], "la composición no la elige quien estudia"
    assert "Práctica de un tema: 2 pregunta(s)" in sesion["configuration"]["note"]
    assert "sin parte declarada" in sesion["configuration"]["note"]

    revision = seeded_client.get(f"/api/v1/study-sessions/{sesion['id']}/review").json()
    assert {entrada["part_code"] for entrada in revision["entries"]} == {None}, (
        "la parte de una pregunta del banco no está declarada: no se inventa"
    )
    enunciados = {entrada["stem"] for entrada in revision["entries"]}
    assert all("tema del caso" in enunciado for enunciado in enunciados)


def test_una_practica_por_tema_no_se_monta_sin_preguntas_y_lo_dice(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """Un tema sin preguntas catalogadas no crea una sesión vacía: se dice qué falta."""
    oposicion = _oposicion_activa(seeded_client)
    nodo = _tema_con_preguntas(seeded_client, ruta="I.1")

    respuesta = seeded_client.post(
        "/api/v1/study-sessions",
        json={
            "opposition_id": oposicion["id"],
            "mode": "practice",
            "sources": [],
            "curriculum_node_id": nodo,
        },
        headers=ALLOWED_ORIGIN,
    )

    assert respuesta.status_code == 409, respuesta.text
    assert respuesta.json()["code"] == "unsupported"
    assert "no tiene ninguna pregunta catalogada" in respuesta.json()["detail"]
    assert "Revisión" in respuesta.json()["detail"], (
        "el motivo dice por dónde se arregla: asignarlas en Revisión"
    )


def test_una_practica_por_tema_no_admite_elegir_conjuntos(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """Elegir conjuntos y pedir un tema a la vez son dos composiciones distintas: se rechaza."""
    set_id = _conjunto(seeded_client, preguntas=2)
    oposicion = _oposicion_activa(seeded_client)
    nodo = _tema_con_preguntas(seeded_client, ruta="I.1")

    respuesta = seeded_client.post(
        "/api/v1/study-sessions",
        json={
            "opposition_id": oposicion["id"],
            "mode": "practice",
            "sources": [{"question_set_id": set_id, "part_code": "primera_parte"}],
            "curriculum_node_id": nodo,
        },
        headers=ALLOWED_ORIGIN,
    )

    assert respuesta.status_code == 409, respuesta.text
    assert "la compone la catalogación del tema" in respuesta.json()["detail"]


def test_una_practica_por_tema_deja_fuera_lo_que_la_plantilla_activa_no_responde(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """Una pregunta sin entrada en la clave activa no entra en la práctica, y se cuenta.

    Antes entraba igual y se corregía como «excluida»: quien estudia la contestaba para nada
    (informe de claves de octubre de 2026, `study_service.py:380`).
    """
    set_id = _conjunto(seeded_client, preguntas=1)
    oposicion = _oposicion_activa(seeded_client)
    # I.1 son las preguntas 1 y 4; la 4 llega sin clave, así que la plantilla no la responde.
    texto = _csv_con_temas(6).replace(
        "numero 4;Verdadero;Falso;a;I.1", "numero 4;Verdadero;Falso;;I.1"
    )
    assert "numero 4;Verdadero;Falso;;I.1" in texto
    importado = seeded_client.post(
        f"/api/v1/question-sets/{set_id}/parse",
        json={
            "kind": "csv",
            "text": texto,
            "mapping": {
                "stem": "enunciado",
                "options": ["op1", "op2"],
                "correct": "clave",
                "topic": "tema",
            },
        },
        headers=ALLOWED_ORIGIN,
    )
    assert importado.status_code == 200, importado.text
    _activar_ultima_clave(seeded_client, set_id)
    nodo = _tema_con_preguntas(seeded_client, ruta="I.1")

    respuesta = seeded_client.post(
        "/api/v1/study-sessions",
        json={
            "opposition_id": oposicion["id"],
            "mode": "practice",
            "sources": [],
            "curriculum_node_id": nodo,
        },
        headers=ALLOWED_ORIGIN,
    )

    assert respuesta.status_code == 201, respuesta.text
    sesion = respuesta.json()
    assert sesion["total_questions"] == 1, "solo la que la plantilla activa sabe corregir"
    assert (
        "1 se quedaron fuera porque la plantilla activa no dice su respuesta"
        in (sesion["configuration"]["note"])
    )
