"""Migración 0033: los avisos del alumno sobre los apuntes («esto está mal», D2).

Lo que se prueba, y es lo que la decisión pide:

- el aviso **entra** con su apartado, su anclaje y su motivo, y nace `open` (lo que espera al
  propietario);
- un aviso **sin motivo** no entra: la bandeja no puede tener filas que nadie sabe qué arreglar;
- un estado que no es ninguno de los tres (`open`, `reviewed`, `dismissed`) tampoco;
- la vuelta atrás se lleva la tabla y no toca ninguna otra.
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

DESDE = "0032_huella_del_texto_comprobado"

_INSERT = (
    "INSERT INTO notes_reports "
    "(id, curriculum_node_id, owner_id, section_key, anchor, reason, status, created_at) "
    "VALUES (:id, 'nodo-1', 'local', 'udp', 'udp', :motivo, :estado, '2026-10-11')"
)


def _settings(tmp_path: Path) -> Settings:
    return Settings(data_dir=tmp_path / "datos", _env_file=None)


def _insertar(settings: Settings, *, identificador: str, motivo: str, estado: str = "open") -> None:
    """Inserta un aviso de prueba: lo que se comprueba aquí son los `CHECK` de la tabla.

    Las claves foráneas se apagan para que lo que se pruebe sea la restricción y no la referencia:
    aquí no hay nodos del programa de verdad.
    """
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.begin() as conexion:
            conexion.execute(text("PRAGMA foreign_keys=OFF"))
            conexion.execute(
                text(_INSERT),
                {"id": identificador, "motivo": motivo, "estado": estado},
            )
    finally:
        engine.dispose()


def _insertar_malo(
    settings: Settings, *, identificador: str, motivo: str, estado: str = "open"
) -> None:
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.begin() as conexion:
            conexion.execute(text("PRAGMA foreign_keys=OFF"))
            with pytest.raises(IntegrityError):
                conexion.execute(
                    text(_INSERT),
                    {"id": identificador, "motivo": motivo, "estado": estado},
                )
    finally:
        engine.dispose()


def _filas(settings: Settings, sentencia: str, parametros: dict[str, object]) -> list[object]:
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.connect() as conexion:
            return list(conexion.execute(text(sentencia), parametros).all())
    finally:
        engine.dispose()


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


def test_un_aviso_entra_con_su_apartado_y_nace_pendiente(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    run_migrations(settings, revision="head")

    _insertar(settings, identificador="aviso-1", motivo="El puerto de LDAPS no es 389.")

    filas = _filas(
        settings,
        "SELECT section_key, anchor, reason, status, owner_id FROM notes_reports WHERE id = :id",
        {"id": "aviso-1"},
    )
    assert filas == [("udp", "udp", "El puerto de LDAPS no es 389.", "open", "local")], (
        "el aviso guarda dónde, qué y en qué estado"
    )


def test_un_aviso_sin_motivo_no_entra(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    run_migrations(settings, revision="head")

    _insertar_malo(settings, identificador="aviso-2", motivo="   ")


def test_un_estado_que_nadie_sabe_despachar_no_entra(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    run_migrations(settings, revision="head")

    _insertar_malo(
        settings, identificador="aviso-3", motivo="Falta el puerto de SNMP.", estado="lo_que_sea"
    )


def test_la_vuelta_atras_se_lleva_la_tabla_y_solo_esa(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    run_migrations(settings, revision="head")
    assert "notes_reports" in _tablas(settings)

    command.downgrade(alembic_config(settings), DESDE)

    assert "notes_reports" not in _tablas(settings)
    assert "notes_incidents" in _tablas(settings), "la bandeja del motor no se toca al bajar"

    # Y subir otra vez la recrea: bajar no deja el esquema en un estado del que no se pueda salir.
    run_migrations(settings, revision="head")
    assert "notes_reports" in _tablas(settings)
    _insertar(settings, identificador="aviso-4", motivo="La máscara /26 no deja 62 hosts.")
    assert _filas(
        settings, "SELECT status FROM notes_reports WHERE id = :id", {"id": "aviso-4"}
    ) == [("open",)]
