"""Migración 0038: la decisión del propietario sobre los apuntes de un tema (F24, §4.3).

Lo que se prueba:

- la tabla entra con sus **dos** decisiones y con la nota **obligatoria al rechazar**;
- un rechazo **sin nota no entra**: lo impide la base y no solo la ruta (una decisión que se colara
  por otro camino dejaría el borrador igual de parado y sin saber por qué);
- **una fila por tema**: la segunda revisión actualiza la primera en vez de apilar otra copia;
- los índices están y la tabla se lleva por delante lo suyo;
- la **vuelta atrás** se lleva la tabla entera, y volver a subir la devuelve.
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

DESDE = "0037_origin_scope"

#: La inserción mínima de una decisión. El nodo se apunta a mano porque aquí no se siembra el
#: programa: lo que se prueban son las restricciones de la tabla.
_INSERT = (
    "INSERT INTO topic_notes_reviews "
    "(id, curriculum_node_id, decision, note, actor, reviewed_at, created_at, updated_at) "
    "VALUES (:id, :nodo, :decision, :nota, 'local', '2026-10-14 08:00:00', "
    "'2026-10-14 08:00:00', '2026-10-14 08:00:00')"
)


def _settings(tmp_path: Path) -> Settings:
    return Settings(data_dir=tmp_path / "datos", _env_file=None)


def _ejecutar(
    settings: Settings,
    sentencia: str,
    parametros: dict[str, object],
    *,
    claves_foraneas: bool = True,
) -> None:
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.begin() as conexion:
            if not claves_foraneas:
                conexion.execute(text("PRAGMA foreign_keys=OFF"))
            conexion.execute(text(sentencia), parametros)
    finally:
        engine.dispose()


def _insertar_malo(settings: Settings, sentencia: str, parametros: dict[str, object]) -> None:
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.begin() as conexion:
            conexion.execute(text("PRAGMA foreign_keys=OFF"))
            with pytest.raises(IntegrityError):
                conexion.execute(text(sentencia), parametros)
    finally:
        engine.dispose()


def _tablas(settings: Settings) -> set[str]:
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.connect() as conexion:
            return {
                str(fila[0])
                for fila in conexion.execute(
                    text("SELECT name FROM sqlite_master WHERE type='table'")
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
                for fila in conexion.execute(text("PRAGMA index_list('topic_notes_reviews')")).all()
            }
    finally:
        engine.dispose()


def _filas(settings: Settings) -> list[tuple[object, ...]]:
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.connect() as conexion:
            return list(
                conexion.execute(
                    text(
                        "SELECT decision, note, actor FROM topic_notes_reviews ORDER BY created_at"
                    )
                ).all()
            )
    finally:
        engine.dispose()


def test_las_dos_decisiones_entran_y_la_que_nadie_sabe_leer_no(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    run_migrations(settings, revision="head")

    _ejecutar(
        settings,
        _INSERT,
        {"id": "r-1", "nodo": "nodo-1", "decision": "approved", "nota": None},
        claves_foraneas=False,
    )
    _ejecutar(
        settings,
        _INSERT,
        {"id": "r-2", "nodo": "nodo-2", "decision": "rejected", "nota": "faltan 43 preguntas"},
        claves_foraneas=False,
    )

    assert len(_filas(settings)) == 2

    for decision in ("aprobado", "APPROVED", "", "pending"):
        _insertar_malo(
            settings,
            _INSERT,
            {"id": "r-malo", "nodo": "nodo-malo", "decision": decision, "nota": "cualquiera"},
        )


def test_un_rechazo_sin_motivo_no_entra_en_la_base(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    run_migrations(settings, revision="head")

    for nota in (None, "", "   "):
        _insertar_malo(
            settings,
            _INSERT,
            {"id": "r-sin-nota", "nodo": "nodo-sin-nota", "decision": "rejected", "nota": nota},
        )

    # Y aprobar sin nota sí entra: la nota es potestativa al aprobar.
    _ejecutar(
        settings,
        _INSERT,
        {
            "id": "r-aprobado-sin-nota",
            "nodo": "nodo-aprobado",
            "decision": "approved",
            "nota": None,
        },
        claves_foraneas=False,
    )
    assert _filas(settings) == [("approved", None, "local")]


def test_una_decision_por_tema(tmp_path: Path) -> None:
    """La segunda revisión actualiza la primera: la tabla dice «qué he decidido de este tema»."""
    settings = _settings(tmp_path)
    run_migrations(settings, revision="head")
    _ejecutar(
        settings,
        _INSERT,
        {"id": "r-1", "nodo": "nodo-1", "decision": "approved", "nota": "primera"},
        claves_foraneas=False,
    )

    _insertar_malo(
        settings,
        _INSERT,
        {"id": "r-2", "nodo": "nodo-1", "decision": "rejected", "nota": "segunda"},
    )

    assert len(_filas(settings)) == 1


def test_los_indices_de_la_tabla_estan(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    run_migrations(settings, revision="head")

    assert "ix_topic_notes_reviews_decision" in _indices(settings)


def test_la_vuelta_atras_se_lleva_la_tabla_y_volver_a_subir_la_devuelve(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    run_migrations(settings, revision="head")
    assert "topic_notes_reviews" in _tablas(settings)

    command.downgrade(alembic_config(settings), DESDE)
    assert "topic_notes_reviews" not in _tablas(settings)
    # Y lo que había antes sigue donde estaba: bajar no toca los apuntes ni sus comprobaciones.
    assert {"topic_note_sections", "question_note_anchors", "question_sets"} <= _tablas(settings)

    command.upgrade(alembic_config(settings), "head")
    assert "topic_notes_reviews" in _tablas(settings)
