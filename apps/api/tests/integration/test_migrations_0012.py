"""Migración 0012: propuestas, mapeos de programa, duplicados y auditoría (S04).

Comprueba tres cosas que no se ven leyendo el fichero de la migración:

1. el esquema queda creado al llegar a la cabeza, con la revisión marcada;
2. la clave foránea de `curriculum_mappings` hacia `curriculum_nodes` es **RESTRICT** de verdad: un
   nodo con material asignado no se puede borrar (DEBT-005, ADR-007). Es la red de seguridad para
   cualquier camino que no pase por la guarda de la siembra;
3. la vuelta atrás se ejecuta de verdad (`run_migrations` solo sube, así que la bajada se pide a
   Alembic) y deja el esquema como estaba en 0011.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from alembic import command
from opofuente.config import Settings
from opofuente.infrastructure.db import build_engine
from opofuente.infrastructure.migrations import alembic_config, run_migrations

AHORA = datetime(2026, 9, 16, 12, 0, tzinfo=UTC)

TABLAS_DE_S04 = (
    "classification_proposals",
    "curriculum_mappings",
    "duplicate_clusters",
    "duplicate_cluster_members",
    "audit_events",
)


def _settings(tmp_path: Path) -> Settings:
    return Settings(data_dir=tmp_path / "datos", _env_file=None)


def _bajar_a(settings: Settings, revision: str) -> None:
    """Baja de revisión de verdad: `run_migrations` solo sube."""
    command.downgrade(alembic_config(settings), revision)


def _tablas(settings: Settings) -> set[str]:
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.connect() as conexion:
            return {
                str(fila[0])
                for fila in conexion.execute(
                    text("SELECT name FROM sqlite_master WHERE type = 'table'")
                )
            }
    finally:
        engine.dispose()


def _revision(settings: Settings) -> str:
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.connect() as conexion:
            return str(conexion.execute(text("SELECT version_num FROM alembic_version")).scalar())
    finally:
        engine.dispose()


def _sembrar_nodo_con_material(settings: Settings, *, con_material: bool) -> str:
    """Crea convocatoria, nodo y (opcionalmente) un mapeo, y devuelve el id del nodo."""
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.begin() as conexion:
            conexion.execute(
                text(
                    "INSERT INTO oppositions (id, code, name, active, created_at, updated_at) "
                    "VALUES ('op-1', 'prueba', 'Prueba', 1, :ahora, :ahora)"
                ),
                {"ahora": AHORA},
            )
            conexion.execute(
                text(
                    "INSERT INTO convocation_versions (id, opposition_id, code, title, "
                    "official_url, published_at, exam_date, status, created_at, updated_at) "
                    "VALUES ('conv-1', 'op-1', 'conv-2026', 'Convocatoria de prueba', "
                    "'https://example.invalid/convocatoria', '2026-01-15', NULL, 'active', "
                    ":ahora, :ahora)"
                ),
                {"ahora": AHORA},
            )
            conexion.execute(
                text(
                    "INSERT INTO curriculum_nodes (id, convocation_version_id, parent_id, "
                    "node_type, official_code, title, position, path, depth) VALUES "
                    "('node-1', 'conv-1', NULL, 'topic', '1', 'Tema 1', 1, 'tema-1', 0)"
                )
            )
            if con_material:
                conexion.execute(
                    text(
                        "INSERT INTO curriculum_mappings (id, curriculum_node_id, subject_type, "
                        "subject_id, coverage_type, depth, confidence, status, created_at, "
                        "approved_at) VALUES ('map-1', 'node-1', 'artifact', 'art-1', 'partial', "
                        "0, 0.8, 'accepted', :ahora, :ahora)"
                    ),
                    {"ahora": AHORA},
                )
    finally:
        engine.dispose()
    return "node-1"


def test_el_esquema_de_clasificacion_queda_creado(tmp_path: Path) -> None:
    """Al llegar a la cabeza están las cinco tablas de S04 y la revisión lo dice."""
    settings = _settings(tmp_path)
    run_migrations(settings, revision="head")

    tablas = _tablas(settings)

    assert _revision(settings) == "0012_classification_and_review"
    for tabla in TABLAS_DE_S04:
        assert tabla in tablas, f"falta la tabla {tabla}"


def test_un_nodo_con_material_asignado_no_se_puede_borrar(tmp_path: Path) -> None:
    """`ON DELETE RESTRICT` de verdad: el borrado del nodo falla aunque no pase por la siembra.

    Es la mitad del cierre de DEBT-005 que no depende del código de la aplicación: si alguien borra
    el nodo con SQL directo, la base lo rechaza.
    """
    settings = _settings(tmp_path)
    run_migrations(settings, revision="head")
    _sembrar_nodo_con_material(settings, con_material=True)

    engine = build_engine(settings.data_paths.database)
    try:
        with pytest.raises(IntegrityError), engine.begin() as conexion:
            conexion.execute(text("DELETE FROM curriculum_nodes WHERE id = 'node-1'"))
    finally:
        engine.dispose()

    # Y el nodo sigue ahí: no se ha borrado «a medias».
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.connect() as conexion:
            vivos = conexion.execute(text("SELECT COUNT(*) FROM curriculum_nodes")).scalar()
            mapeos = conexion.execute(text("SELECT COUNT(*) FROM curriculum_mappings")).scalar()
        assert vivos == 1
        assert mapeos == 1
    finally:
        engine.dispose()


def test_un_nodo_sin_material_si_se_puede_borrar(tmp_path: Path) -> None:
    """La restricción no bloquea lo que no tiene referencias: sin mapeo, el nodo se retira."""
    settings = _settings(tmp_path)
    run_migrations(settings, revision="head")
    _sembrar_nodo_con_material(settings, con_material=False)

    engine = build_engine(settings.data_paths.database)
    try:
        with engine.begin() as conexion:
            conexion.execute(text("DELETE FROM curriculum_nodes WHERE id = 'node-1'"))
            vivos = conexion.execute(text("SELECT COUNT(*) FROM curriculum_nodes")).scalar()
        assert vivos == 0
    finally:
        engine.dispose()


def test_la_migracion_se_puede_revertir(tmp_path: Path) -> None:
    """Bajar a 0011 retira las tablas de S04; volver a subir las recrea."""
    settings = _settings(tmp_path)
    run_migrations(settings, revision="head")

    _bajar_a(settings, "0011_origin_identity_by_channel")

    assert _revision(settings) == "0011_origin_identity_by_channel"
    tablas = _tablas(settings)
    for tabla in TABLAS_DE_S04:
        assert tabla not in tablas, f"{tabla} sigue ahí tras bajar"

    run_migrations(settings, revision="head")

    assert _revision(settings) == "0012_classification_and_review"
    tablas = _tablas(settings)
    for tabla in TABLAS_DE_S04:
        assert tabla in tablas
