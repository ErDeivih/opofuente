"""Migración 0039: los dos estados que resuelve una regla en la bandeja del motor (F31, §2).

El fichero se llama `_bandeja` y no solo `0039` a propósito: la migración `0039_claves_derivadas`
—del bloque del §1, fusionada antes— ya tiene su `test_migrations_0039.py`, y los dos números
conviven porque el identificador de revisión es la cadena entera. Lo que **no** puede convivir es el
padre repetido: esta migración va **detrás** de aquella, y el último caso de esta prueba lo recorre.

Lo que se comprueba:

- los dos estados nuevos entran (`propuesta_lista` y `no_son_preguntas`) y uno que nadie sabe leer
  **no entra**: lo impide la base, no la ruta;
- el índice que pide la bandeja agrupada está;
- la **vuelta atrás** no borra ninguna fila: **recoloca** los dos estados nuevos en los que ya
  existían —una propuesta sin aprobar vuelve a «pendiente» y lo que se fue a «No son preguntas»
  vuelve a «descartada»—, y a partir de ahí el vocabulario viejo vuelve a mandar;
- y volver a subir devuelve la tabla a la cabeza, para que bajar no deje el esquema en un estado del
  que no se pueda salir.
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

#: El escalón de debajo: la migración del §1, que entró antes que esta.
DEBAJO = "0039_claves_derivadas"

#: La inserción mínima de una incidencia. El nodo y la pregunta se apuntan a mano —con las claves
#: foráneas apagadas— porque aquí no se siembra el programa: lo que se prueba es el vocabulario del
#: estado y su índice, no el motor de apuntes.
_INSERT = (
    "INSERT INTO notes_incidents "
    "(id, curriculum_node_id, question_version_id, group_signature, category, coverage, reason, "
    " detail, attempts, created_at, status, resolution_note, reviewed_at) "
    "VALUES (:id, :nodo, :pregunta, :firma, 'clave_sospechosa', 'conflict', 'letra_no_coincide', "
    " 'la clave contradice los apuntes', 1, '2026-10-15 08:00:00', :estado, NULL, NULL)"
)


def _settings(tmp_path: Path) -> Settings:
    return Settings(data_dir=tmp_path / "datos", _env_file=None)


def _ejecutar(settings: Settings, sentencia: str, parametros: dict[str, object]) -> None:
    """Ejecuta con las claves foráneas **apagadas**: aquí se mide el `CHECK`, no las referencias."""
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.begin() as conexion:
            conexion.execute(text("PRAGMA foreign_keys=OFF"))
            conexion.execute(text(sentencia), parametros)
    finally:
        engine.dispose()


def _rechaza(settings: Settings, sentencia: str, parametros: dict[str, object]) -> None:
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.begin() as conexion:
            conexion.execute(text("PRAGMA foreign_keys=OFF"))
            with pytest.raises(IntegrityError):
                conexion.execute(text(sentencia), parametros)
    finally:
        engine.dispose()


def _estados(settings: Settings) -> dict[str, str]:
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.connect() as conexion:
            return {
                str(identificador): str(estado)
                for identificador, estado in conexion.execute(
                    text("SELECT id, status FROM notes_incidents ORDER BY id")
                ).all()
            }
    finally:
        engine.dispose()


def _indices(settings: Settings) -> set[str]:
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.connect() as conexion:
            return {
                str(fila[1])
                for fila in conexion.execute(text("PRAGMA index_list('notes_incidents')")).all()
            }
    finally:
        engine.dispose()


def test_los_dos_estados_nuevos_entran_y_uno_que_nadie_sabe_leer_no(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    run_migrations(settings, revision="head")

    for nombre, estado in (
        ("a-propuesta", "propuesta_lista"),
        ("b-no-son", "no_son_preguntas"),
        ("c-pendiente", "open"),
    ):
        _ejecutar(
            settings,
            _INSERT,
            {
                "id": nombre,
                "nodo": f"nodo-{nombre}",
                "pregunta": f"p-{nombre}",
                "firma": nombre,
                "estado": estado,
            },
        )

    assert _estados(settings) == {
        "a-propuesta": "propuesta_lista",
        "b-no-son": "no_son_preguntas",
        "c-pendiente": "open",
    }

    # El vocabulario viejo sigue siendo el de siempre: los dos nombres que no existen no entran.
    for estado in ("propuesta", "PROPUESTA_LISTA", "", "sin_preguntas"):
        _rechaza(
            settings,
            _INSERT,
            {
                "id": "d-malo",
                "nodo": "nodo-malo",
                "pregunta": f"p-malo-{estado}",
                "firma": "mala",
                "estado": estado,
            },
        )


def test_el_indice_de_la_bandeja_agrupada_esta_y_se_va_al_bajar(tmp_path: Path) -> None:
    """El índice que pide la fila por conjunto: «lo que espera este conjunto» al desplegarla."""
    settings = _settings(tmp_path)
    run_migrations(settings, revision="head")

    assert "ix_notes_incidents_status_set" in _indices(settings)

    command.downgrade(alembic_config(settings), DEBAJO)
    assert "ix_notes_incidents_status_set" not in _indices(settings)


def test_la_vuelta_atras_recoloca_los_estados_y_no_borra_ninguna_fila(tmp_path: Path) -> None:
    """Bajar no tira lo que había: lo devuelve al vocabulario que entonces existía."""
    settings = _settings(tmp_path)
    run_migrations(settings, revision="head")

    for nombre, estado in (
        ("a-propuesta", "propuesta_lista"),
        ("b-no-son", "no_son_preguntas"),
        ("c-resuelta", "reviewed"),
    ):
        _ejecutar(
            settings,
            _INSERT,
            {
                "id": nombre,
                "nodo": f"nodo-{nombre}",
                "pregunta": f"p-{nombre}",
                "firma": nombre,
                "estado": estado,
            },
        )

    command.downgrade(alembic_config(settings), DEBAJO)

    # Las tres filas siguen ahí, con el estado que el vocabulario viejo sí sabe escribir: una
    # propuesta sin aprobar es algo pendiente, y lo que se fue a «No son preguntas» es algo que ya
    # no se toca.
    assert _estados(settings) == {
        "a-propuesta": "open",
        "b-no-son": "dismissed",
        "c-resuelta": "reviewed",
    }

    # Y con el `CHECK` viejo, los dos nombres nuevos ya no entran por ningún camino.
    for estado in ("propuesta_lista", "no_son_preguntas"):
        _rechaza(
            settings,
            _INSERT,
            {
                "id": f"e-{estado}",
                "nodo": f"nodo-{estado}",
                "pregunta": f"p-{estado}",
                "firma": estado,
                "estado": estado,
            },
        )

    # Volver a subir devuelve el vocabulario: bajar no deja el esquema sin salida.
    run_migrations(settings, revision="head")
    assert "ix_notes_incidents_status_set" in _indices(settings)
    _ejecutar(
        settings,
        _INSERT,
        {
            "id": "f-propuesta",
            "nodo": "nodo-f",
            "pregunta": "p-f",
            "firma": "f",
            "estado": "propuesta_lista",
        },
    )
    assert _estados(settings)["f-propuesta"] == "propuesta_lista"
