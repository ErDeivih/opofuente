"""Migración 0037: de qué administración sale cada conjunto (`origin_scope`, D10).

Lo que se prueba:

- la columna entra con sus **tres valores** y con el valor por defecto `desconocida`: ninguna fila
  existente cambia de significado al migrar, y el valor por defecto **no excluye de nada**;
- un vocabulario que nadie sabe leer (`estatal`, `AGE`, vacío) no entra: lo rechaza la base;
- lo que ya estaba sigue en pie: las restricciones de `0014`, `0025` y `0036` sobre `question_sets`
  sobreviven a la recreación de la tabla que SQLite exige para añadir un `CHECK`;
- la **vuelta atrás** se lleva la columna, su `CHECK` y su índice, y volver a subir la devuelve.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from alembic import command
from opofuente.config import Settings
from opofuente.infrastructure.db import build_engine
from opofuente.infrastructure.migrations import alembic_config, run_migrations

DESDE = "0036_claves_no_fiables"

#: La inserción mínima de un conjunto, con la columna nueva. Se apagan las claves foráneas porque
#: aquí no hay oposición de verdad: lo que se prueba son los `CHECK` de la tabla.
_INSERT = (
    "INSERT INTO question_sets "
    "(id, title, opposition_id, set_type, status, distribution, origin_scope, created_at, "
    "updated_at) "
    "VALUES (:id, :titulo, 'op-1', 'private_bank', 'draft', 'personal', :ambito, "
    "'2026-10-13', '2026-10-13')"
)

#: La misma inserción contra el esquema anterior, que no tiene la columna nueva.
_INSERT_ANTIGUO = (
    "INSERT INTO question_sets "
    "(id, title, opposition_id, set_type, status, distribution, created_at, updated_at) "
    "VALUES (:id, :titulo, 'op-1', 'private_bank', 'draft', 'personal', "
    "'2026-10-13', '2026-10-13')"
)


def _settings(tmp_path: Path) -> Settings:
    return Settings(data_dir=tmp_path / "datos", _env_file=None)


def _ejecutar(settings: Settings, sentencia: str, parametros: dict[str, object]) -> None:
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.begin() as conexion:
            conexion.execute(text("PRAGMA foreign_keys=OFF"))
            conexion.execute(text(sentencia), parametros)
    finally:
        engine.dispose()


def _insertar(settings: Settings, **campos: object) -> None:
    base: dict[str, object] = {"titulo": "Banco de prueba", "ambito": "desconocida"}
    _ejecutar(settings, _INSERT, base | campos)


def _insertar_malo(settings: Settings, **campos: object) -> None:
    base: dict[str, object] = {"titulo": "Banco de prueba", "ambito": "desconocida"}
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.begin() as conexion:
            conexion.execute(text("PRAGMA foreign_keys=OFF"))
            with pytest.raises(IntegrityError):
                conexion.execute(text(_INSERT), base | campos)
    finally:
        engine.dispose()


def _columnas(settings: Settings, tabla: str) -> set[str]:
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.connect() as conexion:
            return {
                str(fila[1])
                for fila in conexion.execute(text(f"PRAGMA table_info('{tabla}')")).all()
            }
    finally:
        engine.dispose()


def _indices(settings: Settings, tabla: str) -> set[str]:
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.connect() as conexion:
            return {
                str(fila[1])
                for fila in conexion.execute(text(f"PRAGMA index_list('{tabla}')")).all()
            }
    finally:
        engine.dispose()


def _filas(settings: Settings, sentencia: str, parametros: dict[str, object]) -> list[object]:
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.connect() as conexion:
            return list(conexion.execute(text(sentencia), parametros).all())
    finally:
        engine.dispose()


def test_los_tres_ambitos_entran_y_el_que_nadie_sabe_leer_no(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    run_migrations(settings, revision="head")

    for ambito in ("age", "otra_administracion", "desconocida"):
        _insertar(settings, id=f"set-{ambito}", ambito=ambito)

    assert _filas(settings, "SELECT count(*) FROM question_sets", {}) == [(3,)]

    for malo in ("estatal", "AGE", "", "age "):
        _insertar_malo(settings, id="set-malo", ambito=malo)


def test_el_valor_por_defecto_es_desconocida_y_no_excluye_de_nada(tmp_path: Path) -> None:
    """Migrar **no** afirma de dónde sale un material: lo que ya estaba queda `desconocida`."""
    settings = _settings(tmp_path)
    run_migrations(settings, revision=DESDE)
    _ejecutar(settings, _INSERT_ANTIGUO, {"id": "set-viejo", "titulo": "Banco de antes"})

    run_migrations(settings, revision="head")

    filas = _filas(settings, "SELECT origin_scope FROM question_sets", {})
    assert filas == [("desconocida",)]


def test_las_restricciones_de_antes_sobreviven_a_la_migracion(tmp_path: Path) -> None:
    """Añadir un `CHECK` recrea la tabla en SQLite: los `CHECK` anteriores siguen ahí."""
    settings = _settings(tmp_path)
    run_migrations(settings, revision="head")

    # El tipo (`0014`) y la visibilidad (`0025`) siguen rechazando lo que no es su vocabulario.
    for sentencia, parametros in (
        (
            "INSERT INTO question_sets (id, title, opposition_id, set_type, status, distribution, "
            "origin_scope, created_at, updated_at) VALUES ('set-tipo', 'Banco', 'op-1', 'examen', "
            "'draft', 'personal', 'age', '2026-10-13', '2026-10-13')",
            {},
        ),
        (
            "INSERT INTO question_sets (id, title, opposition_id, set_type, status, distribution, "
            "origin_scope, created_at, updated_at) VALUES ('set-dist', 'Banco', 'op-1', "
            "'private_bank', 'draft', 'PUBLICO', 'age', '2026-10-13', '2026-10-13')",
            {},
        ),
    ):
        engine = build_engine(settings.data_paths.database)
        try:
            with engine.begin() as conexion:
                conexion.execute(text("PRAGMA foreign_keys=OFF"))
                with pytest.raises(IntegrityError):
                    conexion.execute(text(sentencia), parametros)
        finally:
            engine.dispose()

    assert "origin_scope" in _columnas(settings, "question_sets")
    assert "ix_question_sets_origin_scope" in _indices(settings, "question_sets")
    assert "ix_question_sets_key_reliability" in _indices(settings, "question_sets")


def test_la_vuelta_atras_se_lleva_la_columna_y_volver_a_subir_la_devuelve(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    run_migrations(settings, revision="head")
    assert "origin_scope" in _columnas(settings, "question_sets")

    command.downgrade(alembic_config(settings), DESDE)
    assert "origin_scope" not in _columnas(settings, "question_sets")
    assert "ix_question_sets_origin_scope" not in _indices(settings, "question_sets")

    # Y se puede volver a subir: bajar no deja el esquema en un callejón.
    command.upgrade(alembic_config(settings), "head")
    assert "origin_scope" in _columnas(settings, "question_sets")
