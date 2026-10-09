"""Migración 0030: una letra distinta de la clave es un conflicto, no una cobertura.

Lo que se prueba, y es lo que la decisión pide:

- el resultado `conflict` **entra** en la base (el dominio lo produce desde la revisión del
  propietario: 96 preguntas de los tres pilotos se contaban como cubiertas diciendo otra letra);
- un resultado que no es ninguno de los cuatro **no entra**: el vocabulario sigue siendo cerrado y
  una marca que nadie sabe revisar no puede aparecer;
- la vuelta atrás devuelve los conflictos a `doubtful` —que es lo que eran antes: una duda para
  revisar— y **estrecha** la restricción: bajar no deja filas que el esquema viejo rechace.
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

DESDE = "0029_apuntes_por_preguntas"


def _settings(tmp_path: Path) -> Settings:
    return Settings(data_dir=tmp_path / "datos", _env_file=None)


def _filas(settings: Settings, sentencia: str, parametros: dict[str, object]) -> list[object]:
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.connect() as conexion:
            return list(conexion.execute(text(sentencia), parametros).all())
    finally:
        engine.dispose()


_INSERT = (
    "INSERT INTO question_note_anchors "
    "(id, question_version_id, curriculum_node_id, anchor, group_signature, key_status, "
    "result, attempts, checked_at) "
    "VALUES (:id, :pregunta, 'nodo-1', 'iv-7-2-1', 'firma', 'draft', :resultado, 2, '2026-10-09')"
)


def _insertar(settings: Settings, *, resultado: str, pregunta: str) -> None:
    """Inserta un ancla de prueba: lo que se comprueba aquí es el `CHECK` del resultado."""
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.begin() as conexion:
            # Las claves foráneas se apagan para que lo que se pruebe sea el `CHECK`, no la
            # referencia: aquí no hay preguntas ni nodos de verdad.
            conexion.execute(text("PRAGMA foreign_keys=OFF"))
            conexion.execute(
                text(_INSERT),
                {"id": pregunta, "pregunta": f"q-{pregunta}", "resultado": resultado},
            )
    finally:
        engine.dispose()


def _insertar_malo(settings: Settings) -> None:
    """El mismo `INSERT` con un resultado que no existe: tiene que rechazarlo la base."""
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.begin() as conexion:
            conexion.execute(text("PRAGMA foreign_keys=OFF"))
            with pytest.raises(IntegrityError):
                conexion.execute(
                    text(_INSERT), {"id": "p-2", "pregunta": "q-p-2", "resultado": "lo_que_sea"}
                )
    finally:
        engine.dispose()


def test_el_conflicto_entra_en_la_base(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    run_migrations(settings, revision="head")

    _insertar(settings, resultado="conflict", pregunta="p-1")

    filas = _filas(
        settings,
        "SELECT result FROM question_note_anchors WHERE question_version_id = :pregunta",
        {"pregunta": "q-p-1"},
    )
    assert [str(fila[0]) for fila in filas] == ["conflict"]


def test_un_resultado_que_nadie_sabe_revisar_no_entra(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    run_migrations(settings, revision="head")

    _insertar_malo(settings)


def test_la_vuelta_atras_devuelve_los_conflictos_a_dudas(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    run_migrations(settings, revision="head")
    _insertar(settings, resultado="conflict", pregunta="p-3")

    command.downgrade(alembic_config(settings), DESDE)

    filas = _filas(
        settings,
        "SELECT result, note FROM question_note_anchors WHERE question_version_id = :pregunta",
        {"pregunta": "q-p-3"},
    )
    assert [str(fila[0]) for fila in filas] == ["doubtful"], "lo que era antes: una duda por mirar"

    # Y subir otra vez la ensancha sin dejar el esquema inservible.
    run_migrations(settings, revision="head")
    _insertar(settings, resultado="conflict", pregunta="p-4")
    assert _filas(
        settings,
        "SELECT result FROM question_note_anchors WHERE question_version_id = :pregunta",
        {"pregunta": "q-p-4"},
    )
