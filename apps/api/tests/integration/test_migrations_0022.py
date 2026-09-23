"""Migración 0022: la nota de la fecha del ejercicio se guarda y se sirve (S12.2).

Lo que se prueba es que la nota **deja de vivir solo en el fixture**: la columna admite el texto y
desaparece al bajar de revisión, que es lo que hace que `downgrade` no mienta sobre el esquema. Que
la columna se llame así y esté en el detalle de la convocatoria es lo que permite a la interfaz
distinguir «no consta el dato» de «lo dirá otra resolución».
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import text

from alembic import command
from opofuente.config import Settings
from opofuente.infrastructure.db import build_engine
from opofuente.infrastructure.migrations import alembic_config, run_migrations

AHORA = datetime(2026, 9, 23, 12, 0, tzinfo=UTC)
ANTES = "0021_convocation_available"


def _settings(tmp_path: Path) -> Settings:
    return Settings(data_dir=tmp_path / "datos", _env_file=None)


def _ejecutar(settings: Settings, sentencia: str, parametros: dict[str, object]) -> None:
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.begin() as conexion:
            conexion.execute(text(sentencia), parametros)
    finally:
        engine.dispose()


def _consultar(settings: Settings, sentencia: str) -> list[tuple[object, ...]]:
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.connect() as conexion:
            return list(conexion.execute(text(sentencia)).all())
    finally:
        engine.dispose()


def _convocatoria(settings: Settings) -> None:
    _ejecutar(
        settings,
        "INSERT INTO oppositions (id, code, name, description, active, created_at, updated_at) "
        "VALUES ('op-1', 'celador-sacyl', 'Celador/a', 'd', 0, :ahora, :ahora)",
        {"ahora": AHORA},
    )
    _ejecutar(
        settings,
        "INSERT INTO convocation_versions (id, opposition_id, code, title, official_url, "
        "published_at, exam_date, status, source_reference, supersedes_id, created_at, updated_at) "
        "VALUES ('conv-1', 'op-1', 'celador-sacyl-estabilizacion-2022', 'ORDEN', "
        "'https://bocyl.jcyl.es/', '2022-12-28', NULL, 'available', NULL, NULL, :ahora, :ahora)",
        {"ahora": AHORA},
    )


def test_la_nota_se_guarda_y_se_puede_leer(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    run_migrations(settings, revision="head")
    _convocatoria(settings)

    _ejecutar(
        settings,
        "UPDATE convocation_versions SET exam_date_note = :nota WHERE id = 'conv-1'",
        {"nota": "El plazo de solicitudes cerró en enero de 2023."},
    )

    assert _consultar(
        settings, "SELECT exam_date_note FROM convocation_versions WHERE id = 'conv-1'"
    ) == [("El plazo de solicitudes cerró en enero de 2023.",)]


def test_en_0021_la_columna_no_existia(tmp_path: Path) -> None:
    """La columna es de esta migración, no de la anterior: bajar la retira."""
    settings = _settings(tmp_path)
    run_migrations(settings, revision="head")
    _convocatoria(settings)

    command.downgrade(alembic_config(settings), ANTES)

    columnas = {
        str(fila[1]) for fila in _consultar(settings, "PRAGMA table_info(convocation_versions)")
    }
    assert "exam_date_note" not in columnas
