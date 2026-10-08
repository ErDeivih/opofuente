"""Migración 0028: dónde vive el «fuera de temario» (F4).

Lo que se prueba, y es lo que la decisión pide:

- la tabla existe, con la **pregunta** como clave primaria (una pregunta está fuera de temario o no
  lo está, y decir dos veces lo mismo no son dos hechos);
- el motivo es un vocabulario **cerrado**: un motivo que no sea uno de los dos no entra, y eso es lo
  que impide que mañana aparezca una marca que nadie sabe revisar;
- la marca cuelga de la pregunta con `ON DELETE CASCADE`: una marca huérfana no significa nada;
- la vuelta atrás retira el índice y la tabla.
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

TABLA = "question_curriculum_exclusions"
INDICE = "ix_question_exclusions_reason"
DESDE = "0027_owner_id"


def _settings(tmp_path: Path) -> Settings:
    return Settings(data_dir=tmp_path / "datos", _env_file=None)


def _filas(settings: Settings, sentencia: str, parametros: dict[str, object]) -> list[object]:
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.connect() as conexion:
            return list(conexion.execute(text(sentencia), parametros).all())
    finally:
        engine.dispose()


def test_la_tabla_existe_con_la_pregunta_como_clave(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    run_migrations(settings, revision="head")

    columnas = {
        str(fila[1]): (str(fila[2]), int(fila[3]), int(fila[5]))
        for fila in _filas(settings, f"PRAGMA table_info({TABLA})", {})
    }

    assert set(columnas) == {"question_version_id", "reason", "note", "actor", "created_at"}
    tipo, no_nula, clave = columnas["question_version_id"]
    assert tipo == "VARCHAR(36)"
    assert no_nula == 1
    assert clave == 1, "la clave primaria tiene que ser la pregunta"
    assert columnas["reason"][1] == 1 and columnas["actor"][1] == 1
    assert columnas["note"][1] == 0, "el motivo en palabras es opcional"


def test_la_marca_cuelga_de_la_pregunta_y_se_va_con_ella(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    run_migrations(settings, revision="head")

    claves = _filas(settings, f"PRAGMA foreign_key_list({TABLA})", {})
    assert len(claves) == 1
    assert str(claves[0][2]) == "question_versions", "la marca apunta a la pregunta"
    assert str(claves[0][6]).upper() == "CASCADE", "sin la pregunta, la marca no significa nada"


def test_el_motivo_es_un_vocabulario_cerrado(tmp_path: Path) -> None:
    """Un motivo que no se sabe revisar no entra: la base lo rechaza, no el código."""
    settings = _settings(tmp_path)
    run_migrations(settings, revision="head")
    # El nombre de la tabla va escrito a mano en el SQL (y no interpolado) para no construir
    # sentencias con texto: son dos inserciones fijas de una prueba.
    bueno = text(
        "INSERT INTO question_curriculum_exclusions "
        "(question_version_id, reason, actor, created_at) "
        "VALUES ('pregunta-1', 'otra_administracion', 'llm:deepseek-flash', '2026-10-08')"
    )
    malo = text(
        "INSERT INTO question_curriculum_exclusions "
        "(question_version_id, reason, actor, created_at) "
        "VALUES ('pregunta-2', 'lo_que_sea', 'llm:deepseek-flash', '2026-10-08')"
    )
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.begin() as conexion:
            # La clave foránea se apaga para que lo que se pruebe sea el `CHECK`, no la referencia.
            conexion.execute(text("PRAGMA foreign_keys=OFF"))
            conexion.execute(bueno)
            with pytest.raises(IntegrityError):
                conexion.execute(malo)
    finally:
        engine.dispose()


def test_el_listado_por_motivo_tiene_su_indice(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    run_migrations(settings, revision="head")

    indices = {str(fila[1]) for fila in _filas(settings, f"PRAGMA index_list({TABLA})", {})}

    assert INDICE in indices


def test_la_vuelta_atras_retira_la_tabla_y_el_indice(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    run_migrations(settings, revision="head")

    command.downgrade(alembic_config(settings), DESDE)

    tablas = {
        str(fila[0])
        for fila in _filas(settings, "SELECT name FROM sqlite_master WHERE type = 'table'", {})
    }
    assert TABLA not in tablas

    run_migrations(settings, revision="head")
    tablas = {
        str(fila[0])
        for fila in _filas(settings, "SELECT name FROM sqlite_master WHERE type = 'table'", {})
    }
    assert TABLA in tablas, "subir otra vez la recrea: bajar no deja el esquema inservible"
