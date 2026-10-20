"""La bandeja de explicaciones generadas: qué entra y qué no (M1 de la fase 3).

La prueba siembra **por la API** lo que la API puede sembrar —un conjunto con dos preguntas— y
**por el `engine`** lo que la API no escribe nunca: las explicaciones `generated`, **a propósito**,
porque una explicación escrita por una persona no puede declararse generada por un modelo.

Lo que se comprueba, en una sola prueba: **el filtro** (la privada no entra), **el orden** (la más
antigua primero) y **el tope** (`limit`).
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy import text

from opofuente.infrastructure.db import build_engine

ALLOWED_ORIGIN = {"Origin": "http://127.0.0.1:5173"}

#: Dos preguntas: hacen falta dos versiones para poder sembrar tres explicaciones distintas.
#: Dos preguntas en el formato legible que entiende la importación (`kind="questions"`).
TEXTO = """1. Pregunta una:
   a) uno
   b) dos
   Respuesta correcta: b
2. Pregunta dos:
   a) tres
   b) cuatro
   Respuesta correcta: a
"""


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
    return respuesta.json()


def _dos_preguntas(client: TestClient) -> tuple[str, str]:
    """Importa el CSV y devuelve las dos versiones de pregunta, de la más nueva a la más vieja."""
    conjunto = _conjunto(client)
    respuesta = client.post(
        f"/api/v1/question-sets/{conjunto['id']}/parse",
        json={"kind": "questions", "text": TEXTO},
        headers=ALLOWED_ORIGIN,
    )
    assert respuesta.status_code == 200, respuesta.text
    engine = build_engine(client.app.state.settings.data_paths.database)
    try:
        with engine.connect() as conexion:
            ids = [
                str(fila[0])
                for fila in conexion.execute(
                    text(
                        "SELECT id FROM question_versions WHERE question_set_id = :conjunto "
                        "ORDER BY rowid DESC LIMIT 2"
                    ),
                    {"conjunto": conjunto["id"]},
                )
            ]
    finally:
        engine.dispose()
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
    """Siembra una explicación por el `engine`: la API no escribe `generated` a propósito."""
    engine = build_engine(client.app.state.settings.data_paths.database)
    try:
        with engine.begin() as conexion:
            conexion.execute(
                text(
                    "INSERT INTO question_explanations "
                    "(id, question_version_id, option_stable_key, origin, status, model_name, "
                    "prompt_template_version, created_at, text) "
                    "VALUES (:id, :pregunta, :opcion, :origin, 'draft', :modelo, NULL, :cuando, "
                    ":texto)"
                ),
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
        engine.dispose()


def test_la_bandeja_ensena_lo_generado_y_no_lo_privado(seeded_client: TestClient) -> None:
    # `seeded_client`: la bandeja necesita la oposición activa que deja la siembra de perfiles.
    client = seeded_client
    nueva, vieja = _dos_preguntas(client)
    ahora = datetime.now(UTC)
    # Dos generadas, la de `vieja` más antigua, y una privada que no puede aparecer nunca.
    _explicacion(
        client,
        question_version_id=vieja,
        origin="generated",
        texto="La primera, que lleva más tiempo esperando.",
        cuando=ahora - timedelta(hours=2),
    )
    _explicacion(
        client,
        question_version_id=nueva,
        origin="generated",
        texto="La segunda, más reciente.",
        cuando=ahora - timedelta(hours=1),
    )
    _explicacion(
        client,
        question_version_id=nueva,
        origin="private",
        texto="Una explicación escrita por una persona: no hay nada que aprobar.",
        cuando=ahora,
        option_stable_key="a",
    )

    respuesta = client.get("/api/v1/explanations/pending")
    assert respuesta.status_code == 200, respuesta.text
    filas = respuesta.json()
    assert len(filas) == 2, "la privada no entra en la bandeja"
    assert filas[0]["explanation"]["question_version_id"] == vieja, "la más antigua va primero"
    assert all(fila["stem"] for fila in filas), "cada fila trae su enunciado"

    una = client.get("/api/v1/explanations/pending?limit=1")
    assert una.status_code == 200, una.text
    assert len(una.json()) == 1, "el tope se respeta"
