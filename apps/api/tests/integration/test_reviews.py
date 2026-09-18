"""Pruebas de integración de errores, repaso y dominio (08_API-CONTRACT §10 y §11) por la API real.

Recorren el criterio de aceptación del slice entero:

1. **un fallo crea repaso** y un acierto lo reprograma subiendo el intervalo;
2. **el historial no se sobrescribe**: cada cambio de fecha queda con sus dos fechas y su motivo;
3. **el repaso se puede hacer de verdad** (sesión `error_review` compuesta por la cola) y también
   declararse desde la cola, diciendo que el desenlace es declarado;
4. **el dominio con pocos datos es «evidencia insuficiente»**, nunca un porcentaje.
"""

from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient

from opofuente.config import Settings

ALLOWED_ORIGIN = {"Origin": "http://127.0.0.1:5173"}


def _texto(preguntas: int) -> str:
    lineas: list[str] = []
    for numero in range(1, preguntas + 1):
        caso = chr(ord("A") + (numero - 1) % 26)
        lineas.append(f"{numero}. El plazo del procedimiento del caso {caso} es de diez dias:")
        for indice in range(4):
            lineas.append(f"{chr(ord('a') + indice)}) Opcion {chr(ord('A') + indice)}")
        lineas.append("Respuesta correcta: a")
        lineas.append("")
    return "\n".join(lineas)


def _oposicion_activa(client: TestClient) -> dict[str, Any]:
    oposiciones = client.get("/api/v1/oppositions").json()
    return next(oposicion for oposicion in oposiciones if oposicion["active"])


def _conjunto(client: TestClient, *, preguntas: int, titulo: str = "Banco de repaso") -> str:
    activa = _oposicion_activa(client)
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
        json={"kind": "questions", "text": _texto(preguntas)},
        headers=ALLOWED_ORIGIN,
    )
    assert importado.status_code == 200, importado.text
    claves = client.get(f"/api/v1/question-sets/{conjunto['id']}/answer-keys").json()
    activada = client.post(
        f"/api/v1/question-sets/{conjunto['id']}/answer-keys/{claves[0]['id']}/activate",
        headers=ALLOWED_ORIGIN,
    )
    assert activada.status_code == 200, activada.text
    return str(conjunto["id"])


def _sesion(client: TestClient, set_id: str, *, cantidad: int, part_code: str = "primera_parte"):
    activa = _oposicion_activa(client)
    creada = client.post(
        "/api/v1/study-sessions",
        json={
            "opposition_id": activa["id"],
            "mode": "practice",
            "sources": [
                {
                    "question_set_id": set_id,
                    "part_code": part_code,
                    "count": cantidad,
                    "include_reserves": False,
                }
            ],
            "convocation_version_id": activa["active_convocation"]["id"],
            "feedback": "immediate",
        },
        headers=ALLOWED_ORIGIN,
    )
    assert creada.status_code == 201, creada.text
    return creada.json()


def _responder(client: TestClient, session_id: str, *, correcta: bool) -> dict[str, Any]:
    """Responde a la pregunta actual. La clave correcta del material sintético es la opción `a`."""
    actual = client.get(f"/api/v1/study-sessions/{session_id}/current-question").json()
    pregunta = actual["question"]
    respuesta = client.post(
        f"/api/v1/study-sessions/{session_id}/answers",
        json={
            "question_version_id": pregunta["question_version_id"],
            "chosen_option_keys": ["a" if correcta else "b"],
            "elapsed_ms": 1500,
            "confidence": "high",
        },
        headers=ALLOWED_ORIGIN,
    )
    assert respuesta.status_code == 201, respuesta.text
    return respuesta.json()


def _fallar_una(client: TestClient, *, preguntas: int = 3) -> tuple[str, str]:
    """Crea un conjunto, una sesión y falla la primera pregunta. Devuelve (set, attempt_id)."""
    set_id = _conjunto(client, preguntas=preguntas)
    sesion = _sesion(client, set_id, cantidad=preguntas)
    client.post(f"/api/v1/study-sessions/{sesion['id']}/start", headers=ALLOWED_ORIGIN)
    resultado = _responder(client, sesion["id"], correcta=False)
    assert resultado["correction"]["outcome"] == "wrong"
    return set_id, str(resultado["attempt"]["id"])


# --- el fallo crea repaso -----------------------------------------------------------------------


def test_un_fallo_crea_un_repaso_para_hoy_con_su_motivo(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    _fallar_una(seeded_client)

    cola = seeded_client.get("/api/v1/reviews/due").json()
    assert len(cola["items"]) == 1
    item = cola["items"][0]
    assert item["review"]["interval_days"] == 0
    assert item["review"]["lapses"] == 1
    assert "hoy" in item["review"]["last_reason"]
    assert item["overdue_days"] == 0
    assert item["explanation"] == "un fallo entra en la cola de hoy mismo"
    # La pregunta llega con sus opciones y **sin** decir cuál es la correcta.
    assert item["options"], "la cola tiene que poder repasarse, no solo mirarse"
    assert "correct_option_keys" not in seeded_client.get("/api/v1/reviews/due").text


def test_un_acierto_en_el_repaso_sube_el_intervalo_y_guarda_el_historial(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    set_id, _ = _fallar_una(seeded_client)
    cola = seeded_client.get("/api/v1/reviews/due").json()
    review_id = cola["items"][0]["review"]["id"]

    primera = seeded_client.post(
        f"/api/v1/reviews/{review_id}/complete",
        json={"outcome": "correct", "confidence": "high"},
        headers=ALLOWED_ORIGIN,
    )
    assert primera.status_code == 200, primera.text
    assert primera.json()["interval_days"] == 4, "acierto tras un fallo: cuatro días"

    segunda = seeded_client.post(
        f"/api/v1/reviews/{review_id}/complete",
        json={"outcome": "correct", "confidence": "high"},
        headers=ALLOWED_ORIGIN,
    )
    assert segunda.json()["interval_days"] == 8

    # El historial conserva los tres pasos: el alta y los dos repasos, con sus dos fechas.
    detalle = seeded_client.get(f"/api/v1/reviews/{review_id}/history").json()
    assert [evento["kind"] for evento in detalle] == ["reviewed", "reviewed", "created"]
    assert [evento["interval_days"] for evento in detalle] == [8, 4, 0]
    assert detalle[0]["previous_interval_days"] == 4
    assert detalle[0]["previous_due_at"] is not None
    assert all(evento["reason"] for evento in detalle), "cada cambio de fecha lleva su motivo"

    # Y nada vencido: la cola de hoy queda vacía hasta que toque.
    assert seeded_client.get("/api/v1/reviews/due").json()["items"] == []
    assert set_id


def test_un_fallo_nuevo_reduce_el_intervalo_y_lo_dice(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    _, attempt_id = _fallar_una(seeded_client)
    cola = seeded_client.get("/api/v1/reviews/due").json()
    review_id = cola["items"][0]["review"]["id"]
    for _ in range(3):
        seeded_client.post(
            f"/api/v1/reviews/{review_id}/complete",
            json={"outcome": "correct", "confidence": "high"},
            headers=ALLOWED_ORIGIN,
        )
    subido = seeded_client.get(f"/api/v1/reviews/{review_id}").json()
    assert subido["interval_days"] == 16

    reducido = seeded_client.post(
        f"/api/v1/reviews/{review_id}/complete",
        json={"outcome": "wrong", "cause": "confusion"},
        headers=ALLOWED_ORIGIN,
    )
    assert reducido.json()["interval_days"] == 0, "un fallo devuelve el repaso a la cola de hoy"
    assert reducido.json()["lapses"] == 2
    assert attempt_id


def test_aplazar_un_repaso_no_lo_cuenta_como_repasado(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    _fallar_una(seeded_client)
    item = seeded_client.get("/api/v1/reviews/due").json()["items"][0]["review"]

    aplazado = seeded_client.post(
        f"/api/v1/reviews/{item['id']}/snooze", json={"days": 3}, headers=ALLOWED_ORIGIN
    )
    assert aplazado.status_code == 200, aplazado.text
    assert aplazado.json()["interval_days"] == item["interval_days"], "aplazar no es repasar"
    assert aplazado.json()["lapses"] == item["lapses"]
    assert "aplazado" in str(aplazado.json()["last_reason"])
    # Y deja de estar vencido: la cola se vacía.
    assert seeded_client.get("/api/v1/reviews/due").json()["items"] == []

    fuera = seeded_client.post(
        f"/api/v1/reviews/{item['id']}/snooze", json={"days": 400}, headers=ALLOWED_ORIGIN
    )
    assert fuera.status_code == 422, "un aplazamiento de un año no es un aplazamiento"


# --- la causa la declara la persona -------------------------------------------------------------


def test_el_error_necesita_causa_y_concepto_y_se_puede_corregir(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    _, attempt_id = _fallar_una(seeded_client)

    sin_concepto = seeded_client.post(
        f"/api/v1/attempts/{attempt_id}/error-classification",
        json={"cause": "knowledge"},
        headers=ALLOWED_ORIGIN,
    )
    assert sin_concepto.status_code == 422, sin_concepto.text
    assert sin_concepto.json()["field_errors"][0]["field"] == "concept_label"

    declarado = seeded_client.post(
        f"/api/v1/attempts/{attempt_id}/error-classification",
        json={
            "cause": "confusion",
            "concept_label": "Plazos",
            "note": "Confundí el plazo con el cómputo",
        },
        headers=ALLOWED_ORIGIN,
    )
    assert declarado.status_code == 200, declarado.text
    error = declarado.json()
    assert error["cause"] == "confusion"
    assert error["occurrences"] == 1
    assert error["status"] == "open"

    # Corregir la causa no duplica el error: se queda el mismo, con la causa nueva.
    corregido = seeded_client.post(
        f"/api/v1/attempts/{attempt_id}/error-classification",
        json={"cause": "reading", "concept_label": "Plazos"},
        headers=ALLOWED_ORIGIN,
    )
    assert corregido.json()["id"] == error["id"]
    assert corregido.json()["cause"] == "reading"

    detalle = seeded_client.get(f"/api/v1/learning-errors/{error['id']}").json()
    assert detalle["error"]["concept_label"] == "Plazos"
    assert detalle["chosen_option_keys"], "el detalle enseña qué se marcó"
    assert detalle["review"] is not None, "y el repaso que ese fallo creó"
    assert [evento["kind"] for evento in detalle["events"]] == ["created"]

    resuelto = seeded_client.post(
        f"/api/v1/learning-errors/{error['id']}/resolution",
        json={"resolved": True, "note": "Ya lo tengo"},
        headers=ALLOWED_ORIGIN,
    )
    assert resuelto.json()["status"] == "resolved"
    assert resuelto.json()["resolved_at"] is not None
    abierto = seeded_client.post(
        f"/api/v1/learning-errors/{error['id']}/resolution",
        json={"resolved": False},
        headers=ALLOWED_ORIGIN,
    )
    assert abierto.json()["status"] == "open"
    assert abierto.json()["resolved_at"] is None


def test_los_conceptos_agrupan_los_fallos_por_nodo_o_etiqueta(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    for _ in range(2):
        _, attempt_id = _fallar_una(seeded_client)
        seeded_client.post(
            f"/api/v1/attempts/{attempt_id}/error-classification",
            json={"cause": "knowledge", "concept_label": "plazos"},
            headers=ALLOWED_ORIGIN,
        )
    _, otro = _fallar_una(seeded_client)
    seeded_client.post(
        f"/api/v1/attempts/{otro}/error-classification",
        json={"cause": "time", "concept_label": "Plazos"},
        headers=ALLOWED_ORIGIN,
    )

    grupos = seeded_client.get("/api/v1/learning-errors").json()
    assert grupos["total_errors"] == 3
    assert len(grupos["groups"]) == 1, "«plazos» y «Plazos» son el mismo concepto"
    grupo = grupos["groups"][0]
    assert grupo["label"] == "plazos"
    assert grupo["occurrences"] == 3
    assert grupo["open_count"] == 3
    assert len(grupo["errors"]) == 3


# --- la sesión de repaso ------------------------------------------------------------------------


def test_la_sesion_de_repaso_se_compone_con_lo_vencido(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    _fallar_una(seeded_client, preguntas=3)
    activa = _oposicion_activa(seeded_client)

    creada = seeded_client.post(
        "/api/v1/study-sessions",
        json={
            "opposition_id": activa["id"],
            "mode": "error_review",
            "convocation_version_id": activa["active_convocation"]["id"],
        },
        headers=ALLOWED_ORIGIN,
    )
    assert creada.status_code == 201, creada.text
    sesion = creada.json()
    assert sesion["mode"] == "error_review"
    assert sesion["total_questions"] == 1, "solo entra lo que estaba vencido"

    seeded_client.post(f"/api/v1/study-sessions/{sesion['id']}/start", headers=ALLOWED_ORIGIN)
    # Acertarla en el repaso la reprograma: cuatro días, y sale de la cola de hoy.
    resultado = _responder(seeded_client, sesion["id"], correcta=True)
    assert resultado["correction"]["outcome"] == "correct"
    quedan = seeded_client.get("/api/v1/reviews/due").json()
    assert quedan["items"] == []
    assert quedan["stats"]["active"] == 1, "sigue habiendo un repaso, solo que no toca hoy"

    # Y sin nada vencido, una sesión de repaso no se inventa: 409 con el motivo.
    vacia = seeded_client.post(
        "/api/v1/study-sessions",
        json={
            "opposition_id": activa["id"],
            "mode": "error_review",
            "convocation_version_id": activa["active_convocation"]["id"],
        },
        headers=ALLOWED_ORIGIN,
    )
    assert vacia.status_code == 409, vacia.text
    assert "no hay nada vencido" in vacia.json()["detail"]


def test_una_sesion_de_repaso_no_acepta_conjuntos_elegidos_a_mano(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    set_id = _conjunto(seeded_client, preguntas=2)
    activa = _oposicion_activa(seeded_client)
    respuesta = seeded_client.post(
        "/api/v1/study-sessions",
        json={
            "opposition_id": activa["id"],
            "mode": "error_review",
            "sources": [{"question_set_id": set_id, "part_code": "primera_parte", "count": 1}],
            "convocation_version_id": activa["active_convocation"]["id"],
        },
        headers=ALLOWED_ORIGIN,
    )
    assert respuesta.status_code == 409, respuesta.text
    assert "cola de repaso" in respuesta.json()["detail"]


# --- lo que no entra en el repaso ---------------------------------------------------------------


def test_dejar_en_blanco_no_crea_repaso(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """Un blanco no demuestra que no se sepa: no entra solo, y se dice por qué."""
    set_id = _conjunto(seeded_client, preguntas=2)
    sesion = _sesion(seeded_client, set_id, cantidad=2)
    seeded_client.post(f"/api/v1/study-sessions/{sesion['id']}/start", headers=ALLOWED_ORIGIN)
    respuesta = seeded_client.post(
        f"/api/v1/study-sessions/{sesion['id']}/answers",
        json={"question_version_id": None, "chosen_option_keys": [], "elapsed_ms": 100},
        headers=ALLOWED_ORIGIN,
    )
    # Sin `question_version_id` no se sabe qué pregunta se deja en blanco: se rechaza.
    assert respuesta.status_code == 422, respuesta.text

    actual = seeded_client.get(f"/api/v1/study-sessions/{sesion['id']}/current-question").json()
    blanco = seeded_client.post(
        f"/api/v1/study-sessions/{sesion['id']}/answers",
        json={
            "question_version_id": actual["question"]["question_version_id"],
            "chosen_option_keys": [],
            "elapsed_ms": 100,
        },
        headers=ALLOWED_ORIGIN,
    )
    assert blanco.status_code == 201, blanco.text
    assert blanco.json()["correction"]["outcome"] == "blank"
    assert seeded_client.get("/api/v1/reviews/due").json()["items"] == []


# --- dominio ------------------------------------------------------------------------------------


def test_el_dominio_con_pocos_datos_es_evidencia_insuficiente(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """Criterio de aceptación de §9: con pocos datos, «insuficiente», no un porcentaje."""
    from datetime import UTC, datetime
    from uuid import uuid4

    from sqlalchemy import insert

    from opofuente.application.review_service import ReviewService
    from opofuente.domain.review import MasteryLevel
    from opofuente.infrastructure.clock import SystemClock
    from opofuente.infrastructure.db import build_engine, build_session_factory
    from opofuente.infrastructure.db_models import CurriculumMappingRecord
    from opofuente.infrastructure.review_repository import SqlAlchemyReviewRepository

    set_id, _ = _fallar_una(seeded_client, preguntas=3)
    nodo = _primer_tema(seeded_client)
    preguntas = seeded_client.get(f"/api/v1/question-sets/{set_id}/questions").json()
    primera = preguntas["questions"][0]

    # La asignación al tema se escribe con el mismo modelo que usa el resto de la aplicación: la API
    # todavía no expone esta asignación y aquí se prueba la estimación, no esa ruta.
    engine = build_engine(seeded_settings.data_paths.database)
    with build_session_factory(engine)() as session:
        session.execute(
            insert(CurriculumMappingRecord).values(
                id=str(uuid4()),
                curriculum_node_id=nodo["id"],
                subject_type="question_version",
                subject_id=primera["id"],
                coverage_type="partial",
                depth=int(nodo["depth"]),
                confidence=1.0,
                status="accepted",
                created_at=datetime.now(UTC),
                approved_at=datetime.now(UTC),
            )
        )
        session.commit()

    servicio = ReviewService(
        reviews=SqlAlchemyReviewRepository(build_session_factory(engine)),
        clock=SystemClock(),
    )
    estimacion = servicio.mastery([nodo["id"]])[nodo["id"]]
    assert estimacion.level is MasteryLevel.INSUFFICIENT
    assert estimacion.accuracy is None
    assert estimacion.recent_attempts == 1
    assert "Evidencia insuficiente" in estimacion.explanation

    # Y un nodo sin intentos no dice «0 %»: dice que no hay nada que estimar.
    sin_datos = servicio.mastery([nodo["id"], "nodo-sin-intentos"])["nodo-sin-intentos"]
    assert sin_datos.level is MasteryLevel.NO_DATA
    assert sin_datos.explanation == "Ningún intento en este tema: no hay nada que estimar."


def _primer_tema(client: TestClient) -> dict[str, Any]:
    activa = _oposicion_activa(client)
    curriculum = client.get(
        f"/api/v1/convocations/{activa['active_convocation']['id']}/curriculum"
    ).json()

    def aplanar(nodos: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [nodo for nodo in nodos for nodo in [nodo, *aplanar(nodo["children"])]]

    return next(nodo for nodo in aplanar(curriculum["nodes"]) if nodo["node_type"] == "topic")
