"""La bandeja de explicaciones generadas: qué entra y qué no (M1).

Siembra por la API lo que la API puede sembrar y por SQL lo que la API nunca escribe: las
explicaciones `generated`. Comprueba el filtro, el orden y el tope.

**`seeded_client: Any` a propósito**: `mypy` ve esa fixture como un `Callable` que devuelve un
`Awaitable` (es asíncrona) y no le encuentra `.app`. Anotarla `Any` es lo que deja pasar el resto.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any, cast

from fastapi.testclient import TestClient

from opofuente.infrastructure.db import build_engine
from opofuente_testing.db import ejecutar, filas

ALLOWED_ORIGIN = {"Origin": "http://127.0.0.1:5173"}

TEXTO = """1. Pregunta una:
   a) uno
   b) dos
   Respuesta correcta: b
2. Pregunta dos:
   a) tres
   b) cuatro
   Respuesta correcta: a
"""

_SQL_IDS = (
    "SELECT id FROM question_versions WHERE question_set_id = :conjunto ORDER BY rowid DESC LIMIT 2"
)

_SQL_INSERT = (
    "INSERT INTO question_explanations "
    "(id, question_version_id, option_stable_key, origin, status, model_name, "
    "prompt_template_version, created_at, text) "
    "VALUES (:id, :pregunta, :opcion, :origin, 'draft', :modelo, NULL, :cuando, :texto)"
)


def _conjunto(client: TestClient) -> dict[str, Any]:
    """Un conjunto sobre la oposición activa de la siembra de las pruebas."""
    oposiciones = client.get("/api/v1/oppositions").json()
    activa = next(oposicion for oposicion in oposiciones if oposicion["active"])
    respuesta = client.post(
        "/api/v1/question-sets",
        json={
            "title": "Examen de prueba",
            "opposition_id": activa["id"],
            "set_type": "private_bank",
        },
        headers=ALLOWED_ORIGIN,
    )
    assert respuesta.status_code == 201, respuesta.text
    creado: dict[str, Any] = respuesta.json()
    return creado


def _dos_preguntas(client: TestClient) -> tuple[str, str]:
    """Importa el texto y devuelve las dos versiones, de la más nueva a la más vieja."""
    conjunto = _conjunto(client)
    respuesta = client.post(
        f"/api/v1/question-sets/{conjunto['id']}/parse",
        json={"kind": "questions", "text": TEXTO},
        headers=ALLOWED_ORIGIN,
    )
    assert respuesta.status_code == 200, respuesta.text
    motor = build_engine(cast(Any, client.app).state.settings.data_paths.database)
    try:
        with motor.connect() as conexion:
            leidas = filas(conexion, _SQL_IDS, {"conjunto": conjunto["id"]})
            ids = [str(fila[0]) for fila in leidas]
    finally:
        motor.dispose()
    assert len(ids) == 2, f"se esperaban dos preguntas y hay {len(ids)}"
    return ids[0], ids[1]


def _explicacion(
    client: TestClient,
    *,
    question_version_id: str,
    origin: str,
    texto: str,
    cuando: datetime,
    option_stable_key: str | None = None,
) -> None:
    """Siembra una explicación por SQL: la API no escribe `generated` a propósito."""
    motor = build_engine(cast(Any, client.app).state.settings.data_paths.database)
    try:
        with motor.begin() as conexion:
            ejecutar(
                conexion,
                _SQL_INSERT,
                {
                    "id": str(uuid.uuid4()),
                    "pregunta": question_version_id,
                    "opcion": option_stable_key,
                    "origin": origin,
                    "modelo": "deepseek-chat" if origin == "generated" else None,
                    "cuando": cuando.isoformat(),
                    "texto": texto,
                },
            )
    finally:
        motor.dispose()


def test_la_bandeja_ensena_lo_generado_y_no_lo_privado(seeded_client: Any) -> None:
    cliente: TestClient = seeded_client
    nueva, vieja = _dos_preguntas(cliente)
    ahora = datetime.now(UTC)
    _explicacion(
        cliente,
        question_version_id=vieja,
        origin="generated",
        texto="La primera, que lleva más tiempo esperando.",
        cuando=ahora - timedelta(hours=2),
    )
    _explicacion(
        cliente,
        question_version_id=nueva,
        origin="generated",
        texto="La segunda, más reciente.",
        cuando=ahora - timedelta(hours=1),
    )
    _explicacion(
        cliente,
        question_version_id=nueva,
        origin="private",
        texto="Una explicación escrita por una persona: no hay nada que aprobar.",
        cuando=ahora,
        option_stable_key="a",
    )

    respuesta = cliente.get("/api/v1/explanations/pending")
    assert respuesta.status_code == 200, respuesta.text
    bandeja = respuesta.json()
    assert len(bandeja) == 2, "la privada no entra en la bandeja"
    primera = bandeja[0]["explanation"]["question_version_id"]
    assert primera == vieja, "la más antigua va primero"
    assert all(fila["stem"] for fila in bandeja), "cada fila trae su enunciado"

    una = cliente.get("/api/v1/explanations/pending?limit=1")
    assert una.status_code == 200, una.text
    assert len(una.json()) == 1, "el tope se respeta"
