"""Contenido de la ficha de tema: preguntas del banco y material de la biblioteca (B-007).

La ficha no examina: devuelve las preguntas **sin clave** y solo las catalogadas como aceptadas.
El material sale de la biblioteca (documento, sección o cita) y también solo si el mapeo está
aceptado: lo provisional o rechazado no se enseña como si fuera apunte del tema.
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

AHORA = datetime(2026, 11, 6, 9, 0, tzinfo=UTC)


def _node_id(settings: Settings) -> str:
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.connect() as conexion:
            return str(
                conexion.execute(
                    text(
                        "SELECT n.id FROM curriculum_nodes n "
                        "JOIN curriculum_versions v ON v.id = n.curriculum_version_id "
                        "WHERE v.code = 'informatica-c1-v1' AND n.path = 'I.1'"
                    )
                ).scalar_one()
            )
    finally:
        engine.dispose()


def _sembrar_contenido(settings: Settings, node_id: str) -> None:
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.begin() as conexion:
            oposicion = conexion.execute(
                text("SELECT id FROM oppositions WHERE code = 'tai-age'")
            ).scalar_one()
            conexion.execute(
                text(
                    "INSERT INTO question_sets (id, title, opposition_id, set_type, status, "
                    "created_at, updated_at) VALUES ('set-1', 'Banco de prueba', :oposicion, "
                    "'private_bank', 'confirmed', :ahora, :ahora)"
                ),
                {"oposicion": oposicion, "ahora": AHORA},
            )
            for identificador, posicion, estado in (
                ("preg-1", 1, "complete"),
                ("preg-2", 2, "complete"),
                ("preg-vieja", 3, "superseded"),
            ):
                conexion.execute(
                    text(
                        "INSERT INTO question_versions (id, question_set_id, stable_key, "
                        "version_no, stem, question_type, position, is_reserve, status, "
                        "origin_type, created_at) VALUES (:id, 'set-1', :stable, 1, :stem, "
                        "'single_choice', :posicion, 0, :estado, 'official', :ahora)"
                    ),
                    {
                        "id": identificador,
                        "stable": identificador,
                        "stem": f"Enunciado de {identificador}",
                        "posicion": posicion,
                        "estado": estado,
                        "ahora": AHORA,
                    },
                )
            for sujeto, tipo, estado, aprobado in (
                ("preg-1", "question_version", "accepted", True),
                ("preg-2", "question_version", "rejected", False),
                ("preg-vieja", "question_version", "accepted", True),
            ):
                conexion.execute(
                    text(
                        "INSERT INTO curriculum_mappings (id, curriculum_node_id, subject_type, "
                        "subject_id, coverage_type, depth, confidence, status, created_at, "
                        "approved_at) VALUES (:id, :nodo, :tipo, :sujeto, 'complete', 0, 1.0, "
                        ":estado, :ahora, :aprobado)"
                    ),
                    {
                        "id": f"map-{sujeto}",
                        "nodo": node_id,
                        "tipo": tipo,
                        "sujeto": sujeto,
                        "estado": estado,
                        "ahora": AHORA,
                        "aprobado": AHORA if aprobado else None,
                    },
                )

            # Biblioteca mínima: una obra, su versión, una sección y una cita.
            conexion.execute(
                text(
                    "INSERT INTO source_artifacts (id, sha256, size_bytes, media_type, "
                    "storage_key, first_seen_at) VALUES ('art-1', :sha, 100, 'text/plain', 'k', "
                    ":ahora)"
                ),
                {"sha": "a" * 64, "ahora": AHORA},
            )
            conexion.execute(
                text(
                    "INSERT INTO logical_documents (id, canonical_title, document_type, "
                    "authority_tier, owner_scope, created_at, updated_at) VALUES ('doc-1', "
                    "'Apuntes de prueba', 'private_syllabus', 'A', 'public', :ahora, :ahora)"
                ),
                {"ahora": AHORA},
            )
            conexion.execute(
                text(
                    "INSERT INTO document_versions (id, logical_document_id, artifact_id, status, "
                    "created_at) VALUES ('doc-ver-1', 'doc-1', 'art-1', 'candidate', :ahora)"
                ),
                {"ahora": AHORA},
            )
            conexion.execute(
                text(
                    "INSERT INTO document_sections (id, document_version_id, section_type, label, "
                    "title, position, page_start, page_end, char_start, char_end, ordinal) VALUES "
                    "('sec-1', 'doc-ver-1', 'chapter', 'Tema 1', 'Tema 1: la Constitución', 1, 1, "
                    "1, 0, 10, 1)"
                )
            )
            conexion.execute(
                text(
                    "INSERT INTO evidence_spans (id, document_version_id, section_id, ordinal, "
                    "citation_label, quality, index_status, text, normalized_text, created_at) "
                    "VALUES ('span-1', 'doc-ver-1', 'sec-1', 1, 'pág. 1', 'good', 'indexed', "
                    "'La Constitución Española de 1978.', 'la constitucion espanola de 1978.', "
                    ":ahora)"
                ),
                {"ahora": AHORA},
            )
            for sujeto, tipo, estado, aprobado in (
                ("doc-ver-1", "document_version", "accepted", True),
                ("sec-1", "section", "accepted", True),
                ("span-1", "evidence", "accepted", True),
            ):
                estado_sujeto = sujeto if tipo != "document_version" else f"{sujeto}-{estado}"
                conexion.execute(
                    text(
                        "INSERT INTO curriculum_mappings (id, curriculum_node_id, subject_type, "
                        "subject_id, coverage_type, depth, confidence, status, created_at, "
                        "approved_at) VALUES (:id, :nodo, :tipo, :sujeto, 'complete', 0, 0.9, "
                        ":estado, :ahora, :aprobado)"
                    ),
                    {
                        "id": f"map-mat-{estado_sujeto}",
                        "nodo": node_id,
                        "tipo": tipo,
                        "sujeto": sujeto,
                        "estado": estado,
                        "ahora": AHORA,
                        "aprobado": AHORA if aprobado else None,
                    },
                )
    finally:
        engine.dispose()


@pytest.fixture
def cliente(seeded_settings: Settings) -> TestClient:
    seed_common_curriculum(seeded_settings)
    node_id = _node_id(seeded_settings)
    _sembrar_contenido(seeded_settings, node_id)
    app = create_app(seeded_settings)
    with TestClient(app) as test_client:
        yield test_client


def test_la_ficha_devuelve_las_preguntas_aceptadas_sin_clave(cliente: TestClient) -> None:
    node_id = _node_id_for_client(cliente)
    respuesta = cliente.get(f"/api/v1/curriculum-nodes/{node_id}/questions")
    assert respuesta.status_code == 200
    pagina = respuesta.json()

    assert pagina["total"] == 1, "solo cuenta la aceptada y no sustituida"
    assert [pregunta["stem"] for pregunta in pagina["questions"]] == ["Enunciado de preg-1"]
    assert pagina["questions"][0]["set_title"] == "Banco de prueba"
    # La clave no viaja a la ficha: aquí se estudia, no se corrige.
    assert "correct_option_keys" not in pagina["questions"][0]
    assert "options" not in pagina["questions"][0]


def test_la_ficha_devuelve_el_material_aceptado_con_su_cita(cliente: TestClient) -> None:
    node_id = _node_id_for_client(cliente)
    respuesta = cliente.get(f"/api/v1/curriculum-nodes/{node_id}/materials")
    assert respuesta.status_code == 200
    pagina = respuesta.json()

    assert pagina["total"] == 3, "documento, sección y cita aceptados"
    tipos = {material["subject_type"] for material in pagina["materials"]}
    assert tipos == {"document_version", "section", "evidence"}
    assert all(material["title"] == "Apuntes de prueba" for material in pagina["materials"])
    seccion = next(
        material for material in pagina["materials"] if material["subject_type"] == "section"
    )
    assert seccion["section_title"] == "Tema 1: la Constitución"
    assert seccion["page"] == 1
    cita = next(
        material for material in pagina["materials"] if material["subject_type"] == "evidence"
    )
    assert cita["citation_label"] == "pág. 1"
    assert cita["excerpt"] == "La Constitución Española de 1978."


def test_el_contenido_de_un_nodo_inexistente_da_404(cliente: TestClient) -> None:
    assert cliente.get("/api/v1/curriculum-nodes/no-existe/questions").status_code == 404
    assert cliente.get("/api/v1/curriculum-nodes/no-existe/materials").status_code == 404


def _node_id_for_client(cliente: TestClient) -> str:
    """El nodo se resuelve por la API para no atar la prueba a un `id` concreto."""
    datos = cliente.get("/api/v1/curricula/informatica-c1").json()
    return str(datos["nodes"][0]["children"][0]["id"])
