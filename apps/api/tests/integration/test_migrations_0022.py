"""Migración 0022: marca de estudio por nodo del temario común.

Comprueba lo que no se ve en el fichero: la tabla existe al llegar a la cabeza, una marca por nodo
(restricción real), la marca **no impide** borrar un nodo sin material y se va con él (`CASCADE`), y
la bajada retira la tabla.
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
from opofuente.infrastructure.migrations import alembic_config, run_migrations, script_head

AHORA = datetime(2026, 11, 5, 10, 0, tzinfo=UTC)


def _settings(tmp_path: Path) -> Settings:
    return Settings(data_dir=tmp_path / "datos", _env_file=None)


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


def _sembrar_nodo(settings: Settings) -> str:
    """Inserta un tema bajo la versión común que ya crea la migración 0021."""
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
            version = conexion.execute(
                text("SELECT id FROM curriculum_versions WHERE code = 'informatica-c1-v1'")
            ).scalar_one()
            conexion.execute(
                text(
                    "INSERT INTO curriculum_nodes (id, curriculum_version_id, parent_id, "
                    "node_type, official_code, title, position, path, depth) VALUES "
                    "('nodo-1', :version, NULL, 'topic', '1', 'Tema 1', 1, '1', 0)"
                ),
                {"version": version},
            )
    finally:
        engine.dispose()
    return "nodo-1"


def test_la_tabla_de_marcas_queda_creada_en_la_cabeza(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    run_migrations(settings, revision="head")

    assert _revision(settings) == script_head(settings)
    assert "curriculum_study_marks" in _tablas(settings)


def test_una_marca_por_nodo_y_se_va_con_el_nodo_sin_material(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    run_migrations(settings, revision="head")
    nodo = _sembrar_nodo(settings)

    engine = build_engine(settings.data_paths.database)
    try:
        with engine.begin() as conexion:
            conexion.execute(
                text(
                    "INSERT INTO curriculum_study_marks (id, curriculum_node_id, marked_at) "
                    "VALUES ('marca-1', :nodo, :ahora)"
                ),
                {"nodo": nodo, "ahora": AHORA},
            )
        with pytest.raises(IntegrityError), engine.begin() as conexion:
            conexion.execute(
                text(
                    "INSERT INTO curriculum_study_marks (id, curriculum_node_id, marked_at) "
                    "VALUES ('marca-2', :nodo, :ahora)"
                ),
                {"nodo": nodo, "ahora": AHORA},
            )
        # El nodo no tiene material (ni mapeos ni fallos): se puede borrar y la marca se va con él.
        with engine.begin() as conexion:
            conexion.execute(text("DELETE FROM curriculum_nodes WHERE id = :nodo"), {"nodo": nodo})
        with engine.connect() as conexion:
            marcas = conexion.execute(
                text("SELECT COUNT(*) FROM curriculum_study_marks")
            ).scalar_one()
    finally:
        engine.dispose()

    assert marcas == 0


def test_la_bajada_retira_la_tabla(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    run_migrations(settings, revision="head")

    command.downgrade(alembic_config(settings), "0021_temario_comun_y_referencias")

    assert _revision(settings) == "0021_temario_comun_y_referencias"
    assert "curriculum_study_marks" not in _tablas(settings)
    run_migrations(settings, revision="head")
    assert "curriculum_study_marks" in _tablas(settings)
