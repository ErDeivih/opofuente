"""Migración 0035: despachar una incidencia del motor (F18, bloque C).

Lo que se prueba, y es lo que este bloque pide del modelo:

- **las 453 incidencias que ya había siguen ahí y entran como pendientes**: la migración añade
  columnas, no toca filas. Se comprueba de verdad —se baja a `0031`, se escribe una incidencia con
  la
  forma vieja y se vuelve a subir—, porque «añadir una columna» en SQLite recrea la tabla y una
  recreación mal hecha se lleva por delante datos que nadie mira hasta que faltan;
- el **estado** que faltaba entra, y los cuatro del vocabulario son los únicos que entran: uno que
  nadie sabe despachar sigue rechazándose;
- la **nota** entra, y en blanco no: una nota que no dice nada es peor que no tenerla;
- **lo que ya estaba sigue en pie**: las restricciones de `0031` (categoría, cobertura, detalle y
  vueltas) y su índice sobreviven a la recreación de la tabla;
- la **vuelta atrás** se lleva las tres columnas y el índice, y subir otra vez devuelve el
  vocabulario entero: bajar no deja el esquema en un callejón.
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

DESDE = "0031_incidencias_apuntes"

#: La forma **vieja** de una incidencia: la que tenía la tabla antes de esta migración.
_INSERT_VIEJO = (
    "INSERT INTO notes_incidents "
    "(id, curriculum_node_id, question_version_id, group_signature, category, coverage, reason, "
    "section_key, anchor, phrase, detail, attempts, created_at) "
    "VALUES (:id, 'nodo-1', :pregunta, 'firma-1', :categoria, :cobertura, :motivo, :seccion, "
    ":ancla, :frase, :detalle, :vueltas, '2026-10-12')"
)

#: La forma de después: con el estado, la nota y la fecha de revisión.
_INSERT_NUEVO = (
    "INSERT INTO notes_incidents "
    "(id, curriculum_node_id, question_version_id, group_signature, category, coverage, reason, "
    "section_key, anchor, phrase, detail, attempts, created_at, status, resolution_note, "
    "reviewed_at) "
    "VALUES (:id, 'nodo-1', :pregunta, 'firma-1', :categoria, :cobertura, :motivo, :seccion, "
    ":ancla, :frase, :detalle, :vueltas, '2026-10-12', :estado, :nota, :revisado)"
)


def _settings(tmp_path: Path) -> Settings:
    return Settings(data_dir=tmp_path / "datos", _env_file=None)


def _insertar(
    settings: Settings,
    *,
    identificador: str,
    pregunta: str = "pregunta-1",
    estado: str = "open",
    nota: str | None = None,
    revisado: str | None = None,
    viejo: bool = False,
    **campos: object,
) -> None:
    """Inserta una incidencia de prueba.

    Las claves foráneas se apagan para que lo que se pruebe sea la restricción y no la referencia:
    aquí no hay nodos del programa ni preguntas de verdad.
    """
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.begin() as conexion:
            conexion.execute(text("PRAGMA foreign_keys=OFF"))
            conexion.execute(
                text(_INSERT_VIEJO if viejo else _INSERT_NUEVO),
                {
                    "id": identificador,
                    "pregunta": pregunta,
                    "categoria": "clave_sospechosa",
                    "cobertura": "conflict",
                    "motivo": "letra_no_coincide",
                    "seccion": "udp",
                    "ancla": "puertos-familias",
                    "frase": "los apuntes dicen que el puerto es 636",
                    "detalle": "la clave contradice los apuntes",
                    "vueltas": 1,
                    "estado": estado,
                    "nota": nota,
                    "revisado": revisado,
                }
                | campos,
            )
    finally:
        engine.dispose()


def _insertar_malo(
    settings: Settings, *, identificador: str, viejo: bool = False, **campos: object
) -> None:
    """Inserta una incidencia que **no** puede entrar: lo que se prueba es la restricción."""
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.begin() as conexion:
            conexion.execute(text("PRAGMA foreign_keys=OFF"))
            with pytest.raises(IntegrityError):
                conexion.execute(
                    text(_INSERT_VIEJO if viejo else _INSERT_NUEVO),
                    {
                        "id": identificador,
                        "pregunta": f"pregunta-{identificador}",
                        "categoria": "hueco_sin_material",
                        "cobertura": "doubtful",
                        "motivo": "sin_frase_en_los_apuntes",
                        "seccion": "udp",
                        "ancla": None,
                        "frase": None,
                        "detalle": "los apuntes no contienen el dato",
                        "vueltas": 1,
                        "estado": "open",
                        "nota": None,
                        "revisado": None,
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


def test_lo_que_ya_estaba_entra_como_pendiente_al_subir(tmp_path: Path) -> None:
    """La incidencia escrita con la forma vieja sigue ahí, y en `open`: nadie la ha mirado aún."""
    settings = _settings(tmp_path)
    run_migrations(settings, revision=DESDE)
    _insertar(settings, identificador="incidencia-vieja", viejo=True)

    run_migrations(settings, revision="head")

    assert _filas(
        settings,
        "SELECT status, resolution_note, reviewed_at FROM notes_incidents WHERE id = :id",
        {"id": "incidencia-vieja"},
    ) == [("open", None, None)], "las filas de antes entran pendientes, que es lo que eran"


def test_el_estado_entra_y_los_que_nadie_sabe_despachar_no(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    run_migrations(settings, revision="head")

    _insertar(
        settings,
        identificador="incidencia-1",
        estado="in_progress",
        nota="Mirando la clave en el banco.",
        revisado=None,
    )
    assert _filas(
        settings,
        "SELECT status, resolution_note, reviewed_at FROM notes_incidents WHERE id = :id",
        {"id": "incidencia-1"},
    ) == [("in_progress", "Mirando la clave en el banco.", None)]

    for estado in ("reviewed", "dismissed", "open"):
        _insertar(
            settings,
            identificador=f"incidencia-{estado}",
            pregunta=f"pregunta-{estado}",
            estado=estado,
            revisado="2026-10-13 10:00:00" if estado != "open" else None,
        )

    assert _filas(settings, "SELECT count(*) FROM notes_incidents", {}) == [(4,)], (
        "los cuatro estados del vocabulario entran"
    )

    _insertar_malo(settings, identificador="incidencia-mala", estado="mirando")


def test_una_nota_en_blanco_no_entra(tmp_path: Path) -> None:
    """Una nota que no dice nada es peor que no tenerla: se rechaza, no se guarda vacía."""
    settings = _settings(tmp_path)
    run_migrations(settings, revision="head")

    _insertar_malo(settings, identificador="incidencia-2", nota="   ")


def test_las_restricciones_y_el_indice_de_0031_siguen_en_pie(tmp_path: Path) -> None:
    """Recrear la tabla para añadir el estado no puede llevarse por delante lo que ya había."""
    settings = _settings(tmp_path)
    run_migrations(settings, revision="head")

    _insertar_malo(settings, identificador="incidencia-3", categoria="inventada")
    _insertar_malo(settings, identificador="incidencia-4", cobertura="covered")
    _insertar_malo(settings, identificador="incidencia-5", detalle="   ")

    indices = _indices(settings, "notes_incidents")
    assert "ix_notes_incidents_node_category" in indices, "el índice de 0031 sobrevive"
    assert "ix_notes_incidents_status_category" in indices, "y el nuevo está"


def test_la_vuelta_atras_se_lleva_las_tres_columnas_y_el_indice(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    run_migrations(settings, revision="head")
    _insertar(
        settings,
        identificador="incidencia-6",
        estado="reviewed",
        nota="La clave estaba mal; corregida.",
        revisado="2026-10-13 10:00:00",
    )

    command.downgrade(alembic_config(settings), DESDE)

    columnas = _columnas(settings, "notes_incidents")
    assert "status" not in columnas
    assert "resolution_note" not in columnas
    assert "reviewed_at" not in columnas
    assert "ix_notes_incidents_status_category" not in _indices(settings, "notes_incidents")
    assert _filas(settings, "SELECT count(*) FROM notes_incidents", {}) == [(1,)], (
        "la fila sigue ahí: lo que se pierde es la decisión, no la incidencia"
    )

    # Y subir otra vez devuelve el vocabulario entero: bajar no deja el esquema en un callejón.
    run_migrations(settings, revision="head")
    assert _filas(
        settings, "SELECT status FROM notes_incidents WHERE id = :id", {"id": "incidencia-6"}
    ) == [("open",)], "lo que estaba resuelto vuelve a esperar, que es lo que era sin la columna"
    _insertar(
        settings,
        identificador="incidencia-7",
        pregunta="pregunta-7",
        estado="dismissed",
        nota="El motor se equivocaba: la clave es correcta.",
    )
    assert _filas(
        settings,
        "SELECT status, resolution_note FROM notes_incidents WHERE id = :id",
        {"id": "incidencia-7"},
    ) == [("dismissed", "El motor se equivocaba: la clave es correcta.")]
