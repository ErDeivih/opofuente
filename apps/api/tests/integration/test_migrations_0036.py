"""Migración 0036: la fiabilidad de la clave de un conjunto (`key_reliability`, §1 del objetivo).

Lo que se prueba:

- la columna entra con sus **tres valores** y con el valor por defecto `fiable`: ninguna fila
  existente cambia de significado al migrar;
- los dos contadores entran con sus restricciones: no pueden ser negativos y **el numerador no
  puede pasar del denominador** (una cifra imposible se rechaza en la base, no en el informe);
- un vocabulario que nadie sabe leer (`regular`, `mala`) no entra;
- lo que ya estaba sigue en pie: las restricciones de `0014` y `0025` sobre `question_sets`
  sobreviven a la recreación de la tabla que SQLite exige para añadir un `CHECK`;
- la **vuelta atrás** se lleva las cuatro columnas y deja el esquema como estaba, y volver a subir
  las devuelve: bajar no deja el esquema en un callejón.
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

DESDE = "0034_avisos_en_curso_y_nota"

#: La inserción mínima de un conjunto. Se apagan las claves foráneas porque aquí no hay oposición de
#: verdad: lo que se prueba son los `CHECK` de la tabla.
_INSERT = (
    "INSERT INTO question_sets "
    "(id, title, opposition_id, set_type, status, distribution, created_at, updated_at, "
    "key_reliability, key_checked_count, key_discrepant_count) "
    "VALUES (:id, :titulo, 'op-1', 'private_bank', 'draft', 'personal', "
    "'2026-10-13', '2026-10-13', :veredicto, :comprobadas, :discrepantes)"
)

#: La misma inserción contra el esquema anterior, que no tiene las columnas nuevas.
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
    base: dict[str, object] = {
        "titulo": "Banco de prueba",
        "veredicto": "fiable",
        "comprobadas": 0,
        "discrepantes": 0,
    }
    _ejecutar(settings, _INSERT, base | campos)


def _insertar_malo(settings: Settings, **campos: object) -> None:
    base: dict[str, object] = {
        "titulo": "Banco de prueba",
        "veredicto": "fiable",
        "comprobadas": 0,
        "discrepantes": 0,
    }
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


def test_los_tres_veredictos_entran_y_el_que_nadie_sabe_leer_no(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    run_migrations(settings, revision="head")

    for veredicto in ("fiable", "dudosa", "no_fiable"):
        _insertar(settings, id=f"set-{veredicto}", veredicto=veredicto)

    assert _filas(settings, "SELECT count(*) FROM question_sets", {}) == [(3,)]

    for malo in ("regular", "mala", "", "FIABLE"):
        _insertar_malo(settings, id=f"set-{malo}", veredicto=malo)


def test_el_valor_por_defecto_es_fiable_y_lo_que_ya_estaba_no_cambia(tmp_path: Path) -> None:
    """Migrar **no** pone en cuarentena nada: lo que nadie ha medido sigue siendo fiable."""
    settings = _settings(tmp_path)
    run_migrations(settings, revision=DESDE)
    _ejecutar(
        settings,
        _INSERT_ANTIGUO,
        {"id": "set-viejo", "titulo": "Banco de antes de la migración"},
    )

    run_migrations(settings, revision="head")

    assert _filas(
        settings,
        "SELECT key_reliability, key_checked_count, key_discrepant_count, key_measured_at "
        "FROM question_sets WHERE id = :id",
        {"id": "set-viejo"},
    ) == [("fiable", 0, 0, None)]


def test_los_dos_contadores_entran_y_el_numerador_no_puede_pasar_del_denominador(
    tmp_path: Path,
) -> None:
    settings = _settings(tmp_path)
    run_migrations(settings, revision="head")

    _insertar(settings, id="set-bien", comprobadas=18, discrepantes=16, veredicto="no_fiable")
    assert _filas(
        settings,
        "SELECT key_checked_count, key_discrepant_count FROM question_sets WHERE id = :id",
        {"id": "set-bien"},
    ) == [(18, 16)]

    _insertar_malo(settings, id="set-imposible", comprobadas=10, discrepantes=11)
    _insertar_malo(settings, id="set-negativo", comprobadas=-1, discrepantes=0)
    _insertar_malo(settings, id="set-negativo-2", comprobadas=1, discrepantes=-1)


def test_las_restricciones_de_los_conjuntos_siguen_en_pie(tmp_path: Path) -> None:
    """Añadir un `CHECK` recrea la tabla en SQLite: lo que había dentro tiene que sobrevivir."""
    settings = _settings(tmp_path)
    run_migrations(settings, revision="head")

    _insertar_malo(settings, id="set-sin-titulo", titulo="   ")
    _insertar_malo(settings, id="set-malo", veredicto="a_medias")
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.begin() as conexion:
            conexion.execute(text("PRAGMA foreign_keys=OFF"))
            with pytest.raises(IntegrityError):
                conexion.execute(
                    text(
                        "INSERT INTO question_sets "
                        "(id, title, opposition_id, set_type, status, distribution, created_at, "
                        "updated_at) VALUES ('set-tipo', 'X', 'op-1', 'cualquiera', 'draft', "
                        "'personal', '2026-10-13', '2026-10-13')"
                    )
                )
    finally:
        engine.dispose()

    assert "ix_question_sets_key_reliability" in _indices(settings, "question_sets")


def test_la_vuelta_atras_se_lleva_las_cuatro_columnas_y_subir_las_devuelve(
    tmp_path: Path,
) -> None:
    settings = _settings(tmp_path)
    run_migrations(settings, revision="head")
    _insertar(settings, id="set-1", comprobadas=18, discrepantes=16, veredicto="no_fiable")

    command.downgrade(alembic_config(settings), DESDE)

    columnas = _columnas(settings, "question_sets")
    for columna in (
        "key_reliability",
        "key_checked_count",
        "key_discrepant_count",
        "key_measured_at",
    ):
        assert columna not in columnas, f"«{columna}» sigue ahí tras bajar"
    # El conjunto sigue existiendo: bajar pierde la **medida**, no el material.
    assert _filas(settings, "SELECT count(*) FROM question_sets", {}) == [(1,)]

    run_migrations(settings, revision="head")
    assert "key_reliability" in _columnas(settings, "question_sets")
    assert _filas(
        settings,
        "SELECT key_reliability FROM question_sets WHERE id = :id",
        {"id": "set-1"},
    ) == [("fiable",)], "al volver a subir, el veredicto se pierde: vuelve al valor por defecto"
