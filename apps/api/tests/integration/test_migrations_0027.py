"""Migración 0027: `owner_id` en las tablas donde vive el progreso.

Lo que se prueba, y es lo que la fase pide («preparado para cuentas, sin cuentas todavía»):

- la columna existe en `study_sessions` y en lo que cuelga de ella, es `NOT NULL` y tiene valor por
  defecto en el servidor: una fila escrita **sin** la columna —como la escribe cualquier código que
  no sepa de dueños— queda en `'local'`, que es lo que impide que el historial viejo se quede sin
  dueño;
- las filas que ya existían antes de migrar también quedan en `'local'`, que es el caso que de
  verdad importa: migrar la base del propietario no puede dejar su progreso huérfano;
- el índice del listado por dueño se crea y se retira con la vuelta atrás.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import text

from alembic import command
from opofuente.config import Settings
from opofuente.infrastructure.db import build_engine
from opofuente.infrastructure.migrations import alembic_config, run_migrations

AHORA = datetime(2026, 10, 7, 9, 0, tzinfo=UTC)
DESDE = "0026_examenes_oficiales_publicos"

#: Las tablas del progreso de una persona, de la sesión hacia abajo.
TABLAS: tuple[str, ...] = (
    "study_sessions",
    "session_questions",
    "attempts",
    "attempt_evaluations",
    "learning_errors",
)

INDICE = "ix_study_sessions_owner"


def _settings(tmp_path: Path) -> Settings:
    return Settings(data_dir=tmp_path / "datos", _env_file=None)


def _columnas(settings: Settings, tabla: str) -> dict[str, tuple[object, object, object]]:
    """(tipo, no_nula, valor_por_defecto) de cada columna de la tabla, leído con SQLite a pelo."""
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.connect() as conexion:
            filas = conexion.execute(text(f"PRAGMA table_info({tabla})")).all()
    finally:
        engine.dispose()
    return {str(fila[1]): (fila[2], fila[3], fila[4]) for fila in filas}


def _indices(settings: Settings, tabla: str) -> set[str]:
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.connect() as conexion:
            filas = conexion.execute(text(f"PRAGMA index_list({tabla})")).all()
    finally:
        engine.dispose()
    return {str(fila[1]) for fila in filas}


def _ejecutar(settings: Settings, sentencia: str, parametros: dict[str, object]) -> None:
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.begin() as conexion:
            conexion.execute(text(sentencia), parametros)
    finally:
        engine.dispose()


def _sembrar_sesion_sin_dueno(settings: Settings) -> None:
    """Una sesión escrita **antes** de la migración: sin columna de dueño, porque no existía."""
    _ejecutar(
        settings,
        "INSERT INTO oppositions (id, code, name, active, created_at, updated_at) VALUES "
        "('op-1', 'tai-age', 'TAI', 0, :ahora, :ahora)",
        {"ahora": AHORA},
    )
    _ejecutar(
        settings,
        "INSERT INTO study_sessions (id, opposition_id, mode, status, feedback, "
        "configuration_json, total_questions, created_at) VALUES "
        "('sesion-1', 'op-1', 'practice', 'draft', 'immediate', '{}', 0, :ahora)",
        {"ahora": AHORA},
    )


def test_la_columna_existe_en_todo_el_arbol_del_progreso(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    run_migrations(settings, revision="head")

    for tabla in TABLAS:
        columna = _columnas(settings, tabla)["owner_id"]
        tipo, no_nula, por_defecto = columna
        assert tipo == "VARCHAR(64)", f"{tabla}.owner_id es {tipo}"
        assert no_nula == 1, f"{tabla}.owner_id admite nulos"
        assert por_defecto == "'local'", f"{tabla}.owner_id no tiene 'local' por defecto"
    assert INDICE in _indices(settings, "study_sessions")


def test_lo_que_ya_existia_queda_en_local(tmp_path: Path) -> None:
    """El caso que importa: migrar la base del propietario no deja su progreso sin dueño."""
    settings = _settings(tmp_path)
    run_migrations(settings, revision=DESDE)
    _sembrar_sesion_sin_dueno(settings)

    run_migrations(settings, revision="head")

    engine = build_engine(settings.data_paths.database)
    try:
        with engine.connect() as conexion:
            dueno = conexion.execute(
                text("SELECT owner_id FROM study_sessions WHERE id = 'sesion-1'")
            ).scalar_one()
    finally:
        engine.dispose()
    assert dueno == "local"


def test_una_fila_nueva_sin_dueno_queda_en_local(tmp_path: Path) -> None:
    """El valor por defecto del **servidor**: es lo que cubre al código que no sepa de dueños."""
    settings = _settings(tmp_path)
    run_migrations(settings, revision="head")
    _sembrar_sesion_sin_dueno(settings)

    engine = build_engine(settings.data_paths.database)
    try:
        with engine.connect() as conexion:
            dueno = conexion.execute(
                text("SELECT owner_id FROM study_sessions WHERE id = 'sesion-1'")
            ).scalar_one()
    finally:
        engine.dispose()
    assert dueno == "local"


def test_la_vuelta_atras_retira_la_columna_y_el_indice(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    run_migrations(settings, revision="head")

    command.downgrade(alembic_config(settings), DESDE)

    for tabla in TABLAS:
        assert "owner_id" not in _columnas(settings, tabla)
    assert INDICE not in _indices(settings, "study_sessions")
