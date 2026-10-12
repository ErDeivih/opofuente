"""Migración 0034: despachar un aviso — «en curso» y la nota de lo que se ha hecho (F16).

Lo que se prueba, y es lo que el bloque C pide del modelo:

- el **estado nuevo** (`in_progress`) entra, y los cuatro estados del vocabulario son los únicos que
  entran: uno que nadie sabe despachar sigue rechazándose;
- la **nota** entra, y en blanco no: una nota que no dice nada es peor que no tenerla;
- **lo que ya estaba sigue en pie**: las restricciones de `0033` (motivo, apartado y anclaje no
  vacíos) sobreviven a la recreación de la tabla que SQLite exige para ensanchar un `CHECK`, y los
  dos índices siguen ahí;
- la **vuelta atrás** devuelve el vocabulario de tres estados, se lleva la columna y deja los avisos
  que estaban «en curso» otra vez pendientes —que es lo que eran—.
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

DESDE = "0033_avisos_del_alumno"

_INSERT = (
    "INSERT INTO notes_reports "
    "(id, curriculum_node_id, owner_id, section_key, anchor, reason, status, created_at, "
    "resolution_note) "
    "VALUES (:id, 'nodo-1', 'local', :seccion, 'ancla', :motivo, :estado, '2026-10-11', :nota)"
)

#: La misma inserción contra el esquema **anterior** a esta migración, que no tiene la nota: es la
#: que se usa para comprobar que, tras bajar, el vocabulario vuelve a tener tres estados.
_INSERT_SIN_NOTA = (
    "INSERT INTO notes_reports "
    "(id, curriculum_node_id, owner_id, section_key, anchor, reason, status, created_at) "
    "VALUES (:id, 'nodo-1', 'local', :seccion, 'ancla', :motivo, :estado, '2026-10-11')"
)


def _settings(tmp_path: Path) -> Settings:
    return Settings(data_dir=tmp_path / "datos", _env_file=None)


def _insertar(
    settings: Settings,
    *,
    identificador: str,
    motivo: str = "El puerto de LDAPS no es 389.",
    estado: str = "open",
    nota: str | None = None,
    seccion: str = "udp",
) -> None:
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
                {
                    "id": identificador,
                    "motivo": motivo,
                    "estado": estado,
                    "nota": nota,
                    "seccion": seccion,
                },
            )
    finally:
        engine.dispose()


def _insertar_malo(
    settings: Settings, *, identificador: str, con_nota: bool = True, **campos: object
) -> None:
    """Inserta un aviso que **no** puede entrar: lo que se prueba es la restricción."""
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.begin() as conexion:
            conexion.execute(text("PRAGMA foreign_keys=OFF"))
            with pytest.raises(IntegrityError):
                conexion.execute(
                    text(_INSERT if con_nota else _INSERT_SIN_NOTA),
                    {
                        "id": identificador,
                        "motivo": "El puerto de LDAPS no es 389.",
                        "nota": None,
                        "seccion": "udp",
                        "estado": "open",
                    }
                    | campos,
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


def test_el_estado_en_curso_y_la_nota_entran_y_los_demas_estados_no(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    run_migrations(settings, revision="head")

    _insertar(
        settings,
        identificador="aviso-1",
        estado="in_progress",
        nota="Mirando el apartado de puertos.",
    )

    assert _filas(
        settings,
        "SELECT status, resolution_note FROM notes_reports WHERE id = :id",
        {"id": "aviso-1"},
    ) == [("in_progress", "Mirando el apartado de puertos.")]

    for estado in ("reviewed", "dismissed", "open"):
        _insertar(settings, identificador=f"aviso-{estado}", estado=estado)

    assert _filas(settings, "SELECT count(*) FROM notes_reports", {}) == [(4,)], (
        "los cuatro estados del vocabulario entran"
    )

    _insertar_malo(
        settings,
        identificador="aviso-malo",
        estado="mirando",
    )


def test_una_nota_en_blanco_no_entra(tmp_path: Path) -> None:
    """Una nota que no dice nada es peor que no tenerla: se rechaza, no se guarda vacía."""
    settings = _settings(tmp_path)
    run_migrations(settings, revision="head")

    _insertar_malo(settings, identificador="aviso-2", nota="   ")


def test_las_restricciones_y_los_indices_de_0033_siguen_en_pie(tmp_path: Path) -> None:
    """Ensanchar el `CHECK` recrea la tabla: lo que había dentro tiene que sobrevivir."""
    settings = _settings(tmp_path)
    run_migrations(settings, revision="head")

    _insertar_malo(settings, identificador="aviso-3", motivo="   ")
    _insertar_malo(settings, identificador="aviso-4", seccion="   ")

    indices = _indices(settings, "notes_reports")
    assert "ix_notes_reports_status_created" in indices
    assert "ix_notes_reports_node_status" in indices


def test_la_vuelta_atras_devuelve_los_tres_estados_y_se_lleva_la_nota(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    run_migrations(settings, revision="head")
    _insertar(settings, identificador="aviso-5", estado="in_progress", nota="En ello.")

    command.downgrade(alembic_config(settings), DESDE)

    assert "resolution_note" not in _columnas(settings, "notes_reports")
    assert _filas(
        settings, "SELECT status FROM notes_reports WHERE id = :id", {"id": "aviso-5"}
    ) == [("open",)], "lo que estaba en curso vuelve a esperar, que es lo que era"
    _insertar_malo(settings, identificador="aviso-6", estado="in_progress", con_nota=False)

    # Y subir otra vez devuelve el vocabulario entero: bajar no deja el esquema en un callejón.
    run_migrations(settings, revision="head")
    _insertar(settings, identificador="aviso-7", estado="in_progress", nota="Otra vez en ello.")
    assert _filas(
        settings,
        "SELECT status, resolution_note FROM notes_reports WHERE id = :id",
        {"id": "aviso-7"},
    ) == [("in_progress", "Otra vez en ello.")]
