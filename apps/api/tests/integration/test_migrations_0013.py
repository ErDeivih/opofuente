"""Migración 0013: documentos, versiones, derechos y lo que la base garantiza (S05).

Aquí no se prueba que las tablas existan (eso lo dice la migración), sino **lo que la base impide**,
que es lo que sostiene los criterios de aceptación del slice:

1. el mismo artefacto no puede ser dos versiones del mismo documento (una fuente compartida se
   **una vez** y se asigna a varias oposiciones con mapeos distintos);
2. un artefacto con versión **no se puede borrar** (`ON DELETE RESTRICT`): la biblioteca no pierde
   material;
3. una versión aceptada tiene que llevar fecha de aprobación, y no puede sustituirse a sí misma;
4. los derechos nacen **desconocidos** (restringidos), no como permiso;
5. el vocabulario de los mapeos admite ya `document_version` (la ampliación que anunció la
   0012), y sigue rechazando lo que no existe.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from opofuente.config import Settings
from opofuente.infrastructure.db import build_engine
from opofuente.infrastructure.migrations import run_migrations

AHORA = datetime(2026, 9, 16, 12, 0, tzinfo=UTC)
SHA_A = "a" * 64


def _settings(tmp_path: Path) -> Settings:
    return Settings(data_dir=tmp_path / "datos", _env_file=None)


def _sembrar(settings: Settings, *, documentos: int = 1, versiones: int = 1) -> None:
    """Crea un artefacto, un documento lógico y sus versiones con SQL directo."""
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.begin() as conexion:
            conexion.execute(
                text(
                    "INSERT INTO source_artifacts (id, sha256, size_bytes, media_type, "
                    "storage_key, first_seen_at) VALUES ('art-1', :sha, 100, 'application/pdf', "
                    "'sha256/aa', :ahora)"
                ),
                {"sha": SHA_A, "ahora": AHORA},
            )
            conexion.execute(
                text(
                    "INSERT INTO rights_statuses (id, code, review_status, commercial_reuse, "
                    "sharing, created_at, updated_at) VALUES "
                    "('rights-unknown', 'unknown', 'unknown', 0, 0, :ahora, :ahora)"
                ),
                {"ahora": AHORA},
            )
            for indice in range(1, documentos + 1):
                conexion.execute(
                    text(
                        "INSERT INTO logical_documents (id, canonical_title, document_type, "
                        "owner_scope, created_at, updated_at) VALUES "
                        "(:id, 'Temario de prueba', 'curriculum', 'private_user', :ahora, :ahora)"
                    ),
                    {"id": f"doc-{indice}", "ahora": AHORA},
                )
            for indice in range(1, versiones + 1):
                conexion.execute(
                    text(
                        "INSERT INTO document_versions (id, logical_document_id, artifact_id, "
                        "version_label, status, rights_status_id, created_at) VALUES "
                        "(:id, 'doc-1', 'art-1', :etiqueta, 'candidate', 'rights-unknown', :ahora)"
                    ),
                    {"id": f"ver-{indice}", "etiqueta": f"v{indice}", "ahora": AHORA},
                )
    finally:
        engine.dispose()


def _ejecutar(settings: Settings, sql: str, **parametros: object) -> None:
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.begin() as conexion:
            conexion.execute(text(sql), parametros)
    finally:
        engine.dispose()


def _contar(settings: Settings, sql: str) -> int:
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.connect() as conexion:
            return int(conexion.execute(text(sql)).scalar_one())
    finally:
        engine.dispose()


def test_el_mismo_artefacto_no_es_dos_versiones_del_mismo_documento(tmp_path: Path) -> None:
    """Una fuente compartida se guarda **una vez**: el mismo artefacto no se duplica."""
    settings = _settings(tmp_path)
    run_migrations(settings, revision="head")
    _sembrar(settings, versiones=1)

    with pytest.raises(IntegrityError):
        _ejecutar(
            settings,
            "INSERT INTO document_versions (id, logical_document_id, artifact_id, version_label, "
            "status, created_at) VALUES ('ver-2', 'doc-1', 'art-1', 'v2', 'candidate', :ahora)",
            ahora=AHORA,
        )

    assert _contar(settings, "SELECT COUNT(*) FROM document_versions") == 1


def test_un_artefacto_con_version_no_se_puede_borrar(tmp_path: Path) -> None:
    """La biblioteca no puede perder el material del que sale una versión."""
    settings = _settings(tmp_path)
    run_migrations(settings, revision="head")
    _sembrar(settings)

    with pytest.raises(IntegrityError):
        _ejecutar(settings, "DELETE FROM source_artifacts WHERE id = 'art-1'")

    assert _contar(settings, "SELECT COUNT(*) FROM source_artifacts") == 1
    assert _contar(settings, "SELECT COUNT(*) FROM document_versions") == 1


def test_una_version_aceptada_necesita_fecha_de_aprobacion(tmp_path: Path) -> None:
    """Aceptar es una promoción crítica: sin fecha de aprobación no hay aceptación que valga."""
    settings = _settings(tmp_path)
    run_migrations(settings, revision="head")
    _sembrar(settings)

    with pytest.raises(IntegrityError):
        _ejecutar(settings, "UPDATE document_versions SET status = 'accepted' WHERE id = 'ver-1'")

    _ejecutar(
        settings,
        "UPDATE document_versions SET status = 'accepted', approved_at = :ahora, "
        "approved_by = 'local' WHERE id = 'ver-1'",
        ahora=AHORA,
    )
    assert _contar(settings, "SELECT COUNT(*) FROM document_versions") == 1


def test_una_version_no_puede_sustituirse_a_si_misma(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    run_migrations(settings, revision="head")
    _sembrar(settings)

    with pytest.raises(IntegrityError):
        _ejecutar(
            settings,
            "UPDATE document_versions SET supersedes_id = 'ver-1' WHERE id = 'ver-1'",
        )


def test_los_derechos_nacen_desconocidos_y_restringidos(tmp_path: Path) -> None:
    """09_SECURITY §8: sin revisar, los derechos no son un permiso."""
    settings = _settings(tmp_path)
    run_migrations(settings, revision="head")

    _ejecutar(
        settings,
        "INSERT INTO rights_statuses (id, code, created_at, updated_at) VALUES "
        "('rights-nuevo', 'nuevo', :ahora, :ahora)",
        ahora=AHORA,
    )

    engine = build_engine(settings.data_paths.database)
    try:
        with engine.connect() as conexion:
            revision = conexion.execute(
                text("SELECT review_status, sharing FROM rights_statuses WHERE id = 'rights-nuevo'")
            ).one()
    finally:
        engine.dispose()

    assert revision[0] == "unknown"
    assert bool(revision[1]) is False

    with pytest.raises(IntegrityError):
        _ejecutar(
            settings,
            "INSERT INTO rights_statuses (id, code, review_status, created_at, updated_at) "
            "VALUES ('rights-malo', 'malo', 'inventado', :ahora, :ahora)",
            ahora=AHORA,
        )


def test_los_mapeos_de_programa_admiten_documentos_y_rechazan_lo_que_no_existe(
    tmp_path: Path,
) -> None:
    """La ampliación que anunció la 0012: un documento se puede mapear a un nodo del programa."""
    settings = _settings(tmp_path)
    run_migrations(settings, revision="head")
    _sembrar(settings)
    _ejecutar(
        settings,
        "INSERT INTO oppositions (id, code, name, active, created_at, updated_at) "
        "VALUES ('op-1', 'tai', 'TAI', 1, :ahora, :ahora)",
        ahora=AHORA,
    )
    _ejecutar(
        settings,
        "INSERT INTO convocation_versions (id, opposition_id, code, title, official_url, "
        "published_at, status, created_at, updated_at) VALUES ('conv-1', 'op-1', 'conv-2026', "
        "'Convocatoria', 'https://example.invalid/c', '2026-01-15', 'active', :ahora, :ahora)",
        ahora=AHORA,
    )
    _ejecutar(
        settings,
        "INSERT INTO curriculum_nodes (id, convocation_version_id, node_type, official_code, "
        "title, position, path, depth) VALUES ('node-1', 'conv-1', 'topic', '1', 'Tema 1', 1, "
        "'tema-1', 0)",
    )

    _ejecutar(
        settings,
        "INSERT INTO curriculum_mappings (id, curriculum_node_id, subject_type, subject_id, "
        "coverage_type, depth, confidence, status, created_at, approved_at) VALUES "
        "('map-1', 'node-1', 'document_version', 'ver-1', 'partial', 0, 0.9, 'accepted', "
        ":ahora, :ahora)",
        ahora=AHORA,
    )
    assert _contar(settings, "SELECT COUNT(*) FROM curriculum_mappings") == 1

    with pytest.raises(IntegrityError):
        _ejecutar(
            settings,
            "INSERT INTO curriculum_mappings (id, curriculum_node_id, subject_type, subject_id, "
            "coverage_type, depth, confidence, status, created_at) VALUES "
            "('map-2','node-1','opinion_personal', 'x', 'partial', 0, 0.5, 'provisional', :ahora)",
            ahora=AHORA,
        )


def test_la_evidencia_guarda_donde_esta(tmp_path: Path) -> None:
    """Una cita tiene que poder abrir la sección y la página: sin offsets, no hay cita."""
    settings = _settings(tmp_path)
    run_migrations(settings, revision="head")
    _sembrar(settings)
    _ejecutar(
        settings,
        "INSERT INTO document_sections (id, document_version_id, section_type, title, position, "
        "char_start, char_end, ordinal) VALUES ('sec-1', 'ver-1', 'topic', 'Tema 1', 1, 0, 120, 1)",
    )
    _ejecutar(
        settings,
        "INSERT INTO evidence_spans (id, document_version_id, section_id, ordinal, text, "
        "normalized_text, char_start, char_end, page, citation_label, created_at) VALUES "
        "('ev-1', 'ver-1', 'sec-1', 1, 'El plazo es de diez días.', 'el plazo es de diez dias.', "
        "0, 25, 3, 'Tema 1, pág. 3', :ahora)",
        ahora=AHORA,
    )

    engine = build_engine(settings.data_paths.database)
    try:
        with engine.connect() as conexion:
            fila = conexion.execute(
                text(
                    "SELECT s.page_start IS NULL, e.page, e.citation_label FROM evidence_spans e "
                    "JOIN document_sections s ON s.id = e.section_id WHERE e.id = 'ev-1'"
                )
            ).one()
    finally:
        engine.dispose()

    assert fila[1] == 3
    assert fila[2] == "Tema 1, pág. 3"

    with pytest.raises(IntegrityError):
        _ejecutar(
            settings,
            "INSERT INTO evidence_spans (id, document_version_id, ordinal, text, normalized_text, "
            "char_start, char_end, created_at) VALUES ('ev-2','ver-1',2,'x','x',10,5, :ahora)",
            ahora=AHORA,
        )
