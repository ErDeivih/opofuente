"""Migración 0025: quién puede ver un conjunto de preguntas (`distribution`).

Lo que se prueba es la promesa de la columna, no solo su nombre: **nada de lo que ya estaba cambia
de visibilidad** al migrar (una fila que existía antes de la columna queda en `personal`), la
columna **no admite nulos ni un valor inventado** (un conjunto sin distribución sería un conjunto
del que la aplicación no sabría si enseñarlo) y bajar de revisión la retira sin llevarse la tabla
por delante.

La primera prueba migra hasta 0024 **antes** de insertar: así la fila se escribe sin la columna y es
la migración la que tiene que rellenarla, que es exactamente lo que pasará en la base real.
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

AHORA = datetime(2026, 10, 7, 9, 0, tzinfo=UTC)
ANTES = "0024_dossier_snapshots"

#: Cómo se insertaba un conjunto **antes** de esta migración: sin columna de distribución.
_INSERT_SIN_DISTRIBUCION = (
    "INSERT INTO question_sets (id, title, opposition_id, set_type, created_at, updated_at) "
    "VALUES (:id, :titulo, 'op-1', 'private_bank', :ahora, :ahora)"
)

_INSERT_CON_DISTRIBUCION = (
    "INSERT INTO question_sets (id, title, opposition_id, set_type, created_at, updated_at, "
    "distribution) VALUES (:id, :titulo, 'op-1', 'private_bank', :ahora, :ahora, :distribution)"
)


def _settings(tmp_path: Path) -> Settings:
    return Settings(data_dir=tmp_path / "datos", _env_file=None)


def _ejecutar(
    settings: Settings, sentencia: str, parametros: dict[str, object] | None = None
) -> None:
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.begin() as conexion:
            conexion.execute(text(sentencia), parametros or {})
    finally:
        engine.dispose()


def _consultar(settings: Settings, sentencia: str) -> list[tuple[object, ...]]:
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.connect() as conexion:
            return list(conexion.execute(text(sentencia)).all())
    finally:
        engine.dispose()


def _columnas_de_question_sets(settings: Settings) -> set[str]:
    return {str(fila[1]) for fila in _consultar(settings, "PRAGMA table_info(question_sets)")}


def _oposicion(settings: Settings) -> None:
    _ejecutar(
        settings,
        "INSERT INTO oppositions (id, code, name, active, created_at, updated_at) VALUES "
        "('op-1', 'tai', 'TAI', 0, :ahora, :ahora)",
        {"ahora": AHORA},
    )


def _conjunto_sin_distribucion(settings: Settings, *, id_: str) -> None:
    _ejecutar(
        settings,
        _INSERT_SIN_DISTRIBUCION,
        {"id": id_, "titulo": f"Conjunto {id_}", "ahora": AHORA},
    )


def _conjunto(settings: Settings, *, id_: str, distribution: str | None) -> None:
    _ejecutar(
        settings,
        _INSERT_CON_DISTRIBUCION,
        {
            "id": id_,
            "titulo": f"Conjunto {id_}",
            "ahora": AHORA,
            "distribution": distribution,
        },
    )


def test_lo_que_ya_existia_se_queda_en_personal(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    run_migrations(settings, revision=ANTES)
    _oposicion(settings)
    _conjunto_sin_distribucion(settings, id_="set-1")

    run_migrations(settings, revision="head")

    assert _consultar(settings, "SELECT distribution FROM question_sets") == [("personal",)]


def test_una_distribucion_que_no_existe_no_entra(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    run_migrations(settings, revision="head")
    _oposicion(settings)

    with pytest.raises(IntegrityError):
        _conjunto(settings, id_="set-malo", distribution="publico")

    _conjunto(settings, id_="set-bueno", distribution="public")
    assert _consultar(settings, "SELECT distribution FROM question_sets") == [("public",)]


def test_un_conjunto_sin_distribucion_no_entra(tmp_path: Path) -> None:
    """`NULL` no es «sin decidir»: es una fila que la aplicación no sabría si enseñar."""
    settings = _settings(tmp_path)
    run_migrations(settings, revision="head")
    _oposicion(settings)

    with pytest.raises(IntegrityError):
        _conjunto(settings, id_="set-nulo", distribution=None)


def test_al_bajar_de_revision_la_columna_desaparece_y_la_tabla_se_queda(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    run_migrations(settings, revision="head")
    _oposicion(settings)
    _conjunto(settings, id_="set-1", distribution="public")

    command.downgrade(alembic_config(settings), ANTES)

    assert "distribution" not in _columnas_de_question_sets(settings)
    assert "question_sets" in {
        str(fila[0]) for fila in _consultar(settings, "SELECT name FROM sqlite_master")
    }
    assert _consultar(settings, "SELECT COUNT(*) FROM question_sets") == [(1,)]
