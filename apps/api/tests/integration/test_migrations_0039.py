"""Migración 0039: la clave derivada y el motivo por el que una pregunta sigue fuera (F29).

Lo que se prueba, y es todo lo que la migración promete:

- las dos tablas entran **vacías**, así que ninguna fila existente cambia de significado;
- el **vocabulario está cerrado** donde se puede cerrar: una clave derivada **no** se puede guardar
  como `active` (el `CHECK` solo admite `derived`) y el motivo de fuera solo admite los tres del
  encargo;
- las dos fuentes tienen que **coincidir en la propia fila**: una fila con dos letras distintas no
  entra, y eso es la definición de la clave derivada impuesta donde no se puede saltar;
- la **vuelta atrás** se lleva las dos tablas y su índice, y volver a subir las devuelve.
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

DESDE = "0038_revision_de_apuntes"

#: La fila mínima de una clave derivada. Se apagan las claves foráneas: aquí no hay pregunta de
#: verdad (haría falta un conjunto, una oposición y un ancla), y lo que se prueba son los `CHECK` de
#: la tabla, que es lo que la migración añade.
_INSERT_CLAVE = (
    "INSERT INTO question_derived_keys "
    "(question_version_id, question_set_id, correct_option_keys_json, key_state, notes_letter, "
    "notes_quote, notes_anchor_id, notes_key_status, model_letter, model_name, model_version, "
    "prompt_version, actor, created_at) "
    "VALUES (:id, 'set-1', '[\"b\"]', :estado, :letra_apuntes, 'La cita que la sostiene', "
    "'ancla-1', 'active', :letra_modelo, 'deepseek-flash', 'flash', 'clave-derivada-1', 'prueba', "
    "'2026-10-15')"
)

#: Y la del motivo de fuera.
_INSERT_MOTIVO = (
    "INSERT INTO question_key_gaps "
    "(question_version_id, question_set_id, reason, actor, created_at) "
    "VALUES (:id, 'set-1', :motivo, 'prueba', '2026-10-15')"
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


def _rechaza(settings: Settings, sentencia: str, parametros: dict[str, object]) -> str:
    """Ejecuta una fila que **tiene** que ser rechazada y devuelve el mensaje del fallo."""
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.begin() as conexion:
            conexion.execute(text("PRAGMA foreign_keys=OFF"))
            with pytest.raises(IntegrityError) as fallo:
                conexion.execute(text(sentencia), parametros)
            return str(fallo.value)
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
                ).all()
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


def _parametros(**campos: object) -> dict[str, object]:
    """Los valores de la fila de prueba: por defecto, una clave derivada que **sí** es válida."""
    return {
        "id": campos.get("identificador", "q-1"),
        "estado": campos.get("estado", "derived"),
        "letra_apuntes": campos.get("letra_apuntes", "b"),
        "letra_modelo": campos.get("letra_modelo", "b"),
    }


def test_la_clave_derivada_no_se_puede_guardar_como_active(tmp_path: Path) -> None:
    """`derived` es el único estado que cabe: guardarla como `active` falla en la base."""
    settings = _settings(tmp_path)
    run_migrations(settings, revision="head")
    _ejecutar(settings, _INSERT_CLAVE, _parametros(identificador="q-bien"))

    mensaje = _rechaza(settings, _INSERT_CLAVE, _parametros(identificador="q-mal", estado="active"))

    assert "ck_derived_key_state" in mensaje, mensaje


def test_las_dos_fuentes_tienen_que_decir_la_misma_letra(tmp_path: Path) -> None:
    """La coincidencia no es una regla del código: una fila con dos letras distintas no entra."""
    settings = _settings(tmp_path)
    run_migrations(settings, revision="head")

    mensaje = _rechaza(
        settings,
        _INSERT_CLAVE,
        _parametros(identificador="q-discorde", letra_modelo="c"),
    )

    assert "ck_derived_key_fuentes" in mensaje, mensaje


def test_el_motivo_de_fuera_solo_admite_los_tres_del_encargo(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    run_migrations(settings, revision="head")

    for motivo in ("sin_material", "sin_cita", "sin_coincidencia"):
        _ejecutar(settings, _INSERT_MOTIVO, {"id": f"q-{motivo}", "motivo": motivo})

    mensaje = _rechaza(settings, _INSERT_MOTIVO, {"id": "q-malo", "motivo": "porque_si"})

    assert "ck_key_gap_reason" in mensaje, mensaje


def test_las_dos_tablas_nacen_vacias_y_la_clave_activa_no_se_toca(tmp_path: Path) -> None:
    """Migrar **no** deriva nada: añade dos tablas vacías y no toca ni una clave existente."""
    settings = _settings(tmp_path)
    run_migrations(settings, revision=DESDE)
    _ejecutar(
        settings,
        "INSERT INTO question_sets (id, title, opposition_id, set_type, status, distribution, "
        "origin_scope, key_reliability, created_at, updated_at) VALUES ('set-1', 'Banco', 'op-1', "
        "'private_bank', 'draft', 'personal', 'desconocida', 'no_fiable', '2026-10-15', "
        "'2026-10-15')",
        {},
    )

    run_migrations(settings, revision="head")

    engine = build_engine(settings.data_paths.database)
    try:
        with engine.connect() as conexion:
            derivadas = conexion.execute(
                text("SELECT count(*) FROM question_derived_keys")
            ).scalar()
            motivos = conexion.execute(text("SELECT count(*) FROM question_key_gaps")).scalar()
            veredicto = conexion.execute(
                text("SELECT key_reliability FROM question_sets WHERE id = 'set-1'")
            ).scalar()
    finally:
        engine.dispose()
    assert derivadas == 0, "la tabla nace vacía: la migración no deriva nada"
    assert motivos == 0
    assert veredicto == "no_fiable", "el veredicto del conjunto se queda como estaba"


def test_la_vuelta_atras_se_lleva_las_dos_tablas_y_volver_a_subir_las_devuelve(
    tmp_path: Path,
) -> None:
    settings = _settings(tmp_path)
    run_migrations(settings, revision="head")
    assert {"question_derived_keys", "question_key_gaps"} <= _tablas(settings)
    assert "ix_derived_keys_set" in _indices(settings, "question_derived_keys")

    command.downgrade(alembic_config(settings), DESDE)
    assert not ({"question_derived_keys", "question_key_gaps"} & _tablas(settings))

    command.upgrade(alembic_config(settings), "head")
    assert {"question_derived_keys", "question_key_gaps"} <= _tablas(settings)
    assert "ix_key_gaps_set" in _indices(settings, "question_key_gaps")
