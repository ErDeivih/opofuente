"""B-012: el `path` de un tema se resuelve dentro de una versión, no a ciegas (S04/S13).

Con el temario común y los programas publicados conviviendo, el mismo `path` (por ejemplo `I.1`)
existe en más de una versión. Aceptar una propuesta de tema no puede coger «la primera fila» que
devuelva SQLite: este test fija las tres salidas posibles:

1. si se indica la versión, se usa esa (aunque haya otra con el mismo path);
2. si no se indica, se prefiere el **temario común activo** (el que estudia el alumno);
3. si no hay común y hay varias versiones con ese path, se responde 409 y se pide el ámbito.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from opofuente.config import Settings
from opofuente.infrastructure.db import build_engine
from opofuente.main import create_app
from tests.conftest import seed_common_curriculum

ALLOWED_ORIGIN = {"Origin": "http://127.0.0.1:5173"}
AHORA = datetime(2026, 11, 7, 12, 0, tzinfo=UTC)


def _db(settings: Settings):
    return build_engine(settings.data_paths.database)


def _versions(settings: Settings) -> dict[str, str]:
    engine = _db(settings)
    try:
        with engine.connect() as conexion:
            filas = conexion.execute(
                text(
                    "SELECT v.code, v.id FROM curriculum_versions v "
                    "WHERE v.code IN ('informatica-c1-v1', 'tai-age-2025-programa-v1', "
                    "'gc-cabos-guardias-2026-programa-v1')"
                )
            ).all()
    finally:
        engine.dispose()
    return {str(codigo): str(identificador) for codigo, identificador in filas}


def _crear_propuesta(settings: Settings, proposal_id: str, valor: str) -> None:
    engine = _db(settings)
    try:
        with engine.begin() as conexion:
            conexion.execute(
                text(
                    "INSERT INTO classification_proposals (id, subject_type, subject_id, axis, "
                    "proposed_value, confidence, alternatives_json, evidence_json, engine_name, "
                    "engine_version, status, created_at, decided_at, decision_note) VALUES "
                    "(:id, 'artifact', :sujeto, 'topic', :valor, 0.9, '[]', '[]', 'motor', '1', "
                    "'pending', :ahora, NULL, NULL)"
                ),
                {
                    "id": proposal_id,
                    "sujeto": f"art-{proposal_id}",
                    "valor": valor,
                    "ahora": AHORA,
                },
            )
    finally:
        engine.dispose()


def _version_del_mapeo(settings: Settings, proposal_id: str) -> str:
    engine = _db(settings)
    try:
        with engine.connect() as conexion:
            return str(
                conexion.execute(
                    text(
                        "SELECT n.curriculum_version_id FROM curriculum_mappings m "
                        "JOIN curriculum_nodes n ON n.id = m.curriculum_node_id "
                        "WHERE m.source_proposal_id = :proposal"
                    ),
                    {"proposal": proposal_id},
                ).scalar_one()
            )
    finally:
        engine.dispose()


@pytest.fixture
def cliente_con_comun(seeded_settings: Settings):
    seed_common_curriculum(seeded_settings)
    app = create_app(seeded_settings)
    with TestClient(app) as cliente:
        yield cliente, seeded_settings


@pytest.fixture
def cliente_sin_comun(seeded_settings: Settings):
    app = create_app(seeded_settings)
    with TestClient(app) as cliente:
        yield cliente, seeded_settings


def test_sin_ambito_se_prefiere_el_temario_comun_activo(cliente_con_comun) -> None:
    cliente, settings = cliente_con_comun
    versiones = _versions(settings)
    _crear_propuesta(settings, "prop-comun", "I.1")

    respuesta = cliente.post(
        "/api/v1/classification-proposals/prop-comun/accept",
        json={},
        headers=ALLOWED_ORIGIN,
    )

    assert respuesta.status_code == 200, respuesta.text
    assert _version_del_mapeo(settings, "prop-comun") == versiones["informatica-c1-v1"]


def test_el_ambito_explicito_elige_el_programa_publicado(cliente_con_comun) -> None:
    cliente, settings = cliente_con_comun
    versiones = _versions(settings)
    _crear_propuesta(settings, "prop-publicado", "I.1")

    respuesta = cliente.post(
        "/api/v1/classification-proposals/prop-publicado/accept",
        json={"curriculum_version_id": versiones["tai-age-2025-programa-v1"]},
        headers=ALLOWED_ORIGIN,
    )

    assert respuesta.status_code == 200, respuesta.text
    assert _version_del_mapeo(settings, "prop-publicado") == versiones["tai-age-2025-programa-v1"]


def test_sin_comun_y_con_dos_versiones_se_pide_el_ambito(cliente_sin_comun) -> None:
    cliente, settings = cliente_sin_comun
    versiones = _versions(settings)
    # GC y Celador publican el tema «1» en sus programas: sin ámbito no se puede elegir uno.
    _crear_propuesta(settings, "prop-ambigua", "1")

    respuesta = cliente.post(
        "/api/v1/classification-proposals/prop-ambigua/accept",
        json={},
        headers=ALLOWED_ORIGIN,
    )

    assert respuesta.status_code == 409, respuesta.text
    assert respuesta.json()["code"] == "classification_conflict"
    sigue = cliente.get("/api/v1/classification-proposals/prop-ambigua").json()
    assert sigue["status"] == "pending", "un conflicto no cambia la propuesta"

    con_ambito = cliente.post(
        "/api/v1/classification-proposals/prop-ambigua/accept",
        json={"curriculum_version_id": versiones["gc-cabos-guardias-2026-programa-v1"]},
        headers=ALLOWED_ORIGIN,
    )

    assert con_ambito.status_code == 200, con_ambito.text
    assert (
        _version_del_mapeo(settings, "prop-ambigua")
        == versiones["gc-cabos-guardias-2026-programa-v1"]
    )
