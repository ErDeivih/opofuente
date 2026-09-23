"""Migración 0021: una convocatoria publicada puede no ser la vigente (S12.2).

Lo que se prueba no es que el estado nuevo exista en un enumerado, sino **lo que la base garantiza**
después de ensanchar una restricción `CHECK` en SQLite, que obliga a recrear la tabla:

1. antes de 0021 un estado `available` no entraba, y después entra;
2. la recreación de la tabla **no se lleva por delante** el índice único parcial que garantiza una
   sola convocatoria vigente por oposición. Es el riesgo real de este cambio: el índice se creó con
   `CREATE UNIQUE INDEX ... WHERE status = 'active'`, y si la tabla se recreara sin él, la
   aplicación podría quedar con dos convocatorias vigentes a la vez sin que nada lo impidiera;
3. las claves foráneas que apuntan a `convocation_versions` siguen apuntando a ella;
4. el `downgrade` devuelve las convocatorias «disponibles» a «superadas» antes de estrechar la
   restricción, así que bajar no deja filas que la restricción antigua rechace.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from alembic import command
from opofuente.config import Settings
from opofuente.infrastructure.db import build_engine
from opofuente.infrastructure.migrations import alembic_config, run_migrations

AHORA = datetime(2026, 9, 23, 12, 0, tzinfo=UTC)
ANTES = "0020_changes_and_derivatives"
DESPUES = "0021_convocation_available"


def _settings(tmp_path: Path) -> Settings:
    return Settings(data_dir=tmp_path / "datos", _env_file=None)


def _ejecutar(settings: Settings, sentencia: str, parametros: dict[str, object]) -> None:
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.begin() as conexion:
            conexion.execute(text(sentencia), parametros)
    finally:
        engine.dispose()


def _consultar(settings: Settings, sentencia: str) -> list[tuple[object, ...]]:
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.connect() as conexion:
            return list(conexion.execute(text(sentencia)).all())
    finally:
        engine.dispose()


def _oposicion(settings: Settings, identificador: str) -> None:
    _ejecutar(
        settings,
        "INSERT INTO oppositions (id, code, name, description, active, created_at, updated_at) "
        "VALUES (:id, :code, 'Celador/a', 'd', 0, :ahora, :ahora)",
        {"id": identificador, "code": f"code-{identificador}", "ahora": AHORA},
    )


def _convocatoria(
    settings: Settings,
    identificador: str,
    oposicion: str,
    estado: str,
    publicada: str = "2022-12-28",
) -> None:
    _ejecutar(
        settings,
        "INSERT INTO convocation_versions (id, opposition_id, code, title, official_url, "
        "published_at, exam_date, status, source_reference, supersedes_id, created_at, updated_at) "
        "VALUES (:id, :oposicion, :code, 'ORDEN', 'https://bocyl.jcyl.es/', :publicada, NULL, "
        ":estado, NULL, NULL, :ahora, :ahora)",
        {
            "id": identificador,
            "oposicion": oposicion,
            "code": f"conv-{identificador}",
            "publicada": publicada,
            "estado": estado,
            "ahora": AHORA,
        },
    )


def test_available_no_entraba_antes_y_entra_despues(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    run_migrations(settings, revision=ANTES)
    _oposicion(settings, "op-1")
    with pytest.raises(IntegrityError):
        _convocatoria(settings, "conv-1", "op-1", "available")

    run_migrations(settings, revision="head")
    _convocatoria(settings, "conv-2", "op-1", "available")
    assert _consultar(settings, "SELECT status FROM convocation_versions WHERE id = 'conv-2'") == [
        ("available",)
    ]


def test_la_migracion_conserva_el_indice_de_una_sola_vigente(tmp_path: Path) -> None:
    """El índice único parcial sobrevive a la recreación de la tabla.

    Sin él, la aplicación podría quedar con dos convocatorias vigentes de la misma oposición: la
    pantalla de Programa elegiría una de las dos sin decir nada.
    """
    settings = _settings(tmp_path)
    run_migrations(settings, revision="head")
    indices = {
        str(fila[0])
        for fila in _consultar(
            settings,
            "SELECT name FROM sqlite_master WHERE type = 'index' AND tbl_name = "
            "'convocation_versions'",
        )
    }
    assert "uq_convocation_single_active" in indices
    definicion = _consultar(
        settings,
        "SELECT sql FROM sqlite_master WHERE name = 'uq_convocation_single_active'",
    )
    assert definicion and "WHERE status = 'active'" in str(definicion[0][0])

    _oposicion(settings, "op-1")
    _convocatoria(settings, "conv-1", "op-1", "active")
    with pytest.raises(IntegrityError):
        _convocatoria(settings, "conv-2", "op-1", "active")
    # Y una disponible convive con la vigente sin problema: es justo el caso de Celador.
    _convocatoria(settings, "conv-3", "op-1", "available")
    assert _consultar(
        settings, "SELECT count(*) FROM convocation_versions WHERE opposition_id = 'op-1'"
    ) == [(2,)]


def test_las_claves_foraneas_siguen_apuntando_a_la_tabla_recreada(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    run_migrations(settings, revision="head")
    _oposicion(settings, "op-1")
    _convocatoria(settings, "conv-1", "op-1", "active")

    engine = build_engine(settings.data_paths.database)
    try:
        with engine.connect() as conexion:
            apuntan = [
                (fila[3], fila[2])
                for tabla in ("curriculum_nodes", "exam_parts", "exam_rules", "question_sets")
                for fila in conexion.execute(text(f"PRAGMA foreign_key_list({tabla})")).all()
                if fila[2] == "convocation_versions"
            ]
            assert len(apuntan) == 4, apuntan
            # Una convocatoria que no existe no se puede referenciar: la clave foránea sigue viva.
            with pytest.raises(IntegrityError):
                conexion.execute(
                    text(
                        "INSERT INTO exam_parts (id, convocation_version_id, code, name, kind, "
                        "position) VALUES ('p-1', 'no-existe', 'e', 'n', 'test', 1)"
                    )
                )
    finally:
        engine.dispose()


def test_el_downgrade_devuelve_las_disponibles_a_superadas(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    run_migrations(settings, revision="head")
    _oposicion(settings, "op-1")
    _convocatoria(settings, "conv-1", "op-1", "available")

    command.downgrade(alembic_config(settings), ANTES)

    assert _consultar(settings, "SELECT status FROM convocation_versions WHERE id = 'conv-1'") == [
        ("superseded",)
    ]
    with pytest.raises(IntegrityError):
        _convocatoria(settings, "conv-2", "op-1", "available")
