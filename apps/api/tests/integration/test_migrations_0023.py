"""Migración 0023: pausar y reanudar un lote (DEBT-027 §4).

Lo que se prueba es **lo que la base garantiza** después de añadir dos estados, no que existan en un
enumerado:

1. `paused` entra en lotes y trabajos, y un estado inventado sigue sin entrar;
2. el índice único parcial de idempotencia se recrea con `paused` **dentro** de su predicado. Es la
   consecuencia que no se ve leyendo el estado: si `paused` quedara fuera, un trabajo pausado
   liberaría su clave y dos trabajos podrían avanzar el mismo lote a la vez;
3. las claves foráneas y el índice de estado siguen donde estaban tras recrear la tabla;
4. el `downgrade` devuelve lotes y trabajos en pausa a la cola antes de estrechar las restricciones.
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
ANTES = "0022_convocation_exam_date_note"


def _settings(tmp_path: Path) -> Settings:
    return Settings(data_dir=tmp_path / "datos", _env_file=None)


def _ejecutar(
    settings: Settings, sentencia: str, parametros: dict[str, object] | None = None
) -> None:
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.begin() as conexion:
            conexion.execute(text(sentencia), parametros or {})
    finally:
        engine.dispose()


def _consultar(settings: Settings, sentencia: str) -> list[tuple[object, ...]]:
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.connect() as conexion:
            return list(conexion.execute(text(sentencia)).all())
    finally:
        engine.dispose()


def _lote(settings: Settings, identificador: str = "lote-1", estado: str = "queued") -> None:
    _ejecutar(
        settings,
        "INSERT INTO ingestion_batches (id, kind, mode, status, source_path_display, "
        "counters_json, created_at) VALUES (:id, 'import', 'copy', :estado, 'C:/material', '{}', "
        "'2026-01-01')",
        {"id": identificador, "estado": estado},
    )


def _trabajo(
    settings: Settings, identificador: str, *, clave: str | None, estado: str = "queued"
) -> None:
    _ejecutar(
        settings,
        "INSERT INTO jobs (id, job_type, status, payload_json, progress, attempts, max_attempts, "
        "idempotency_key, created_at, updated_at) VALUES (:id, 'ingest_batch', :estado, '{}', 0, "
        "0, 3, :clave, '2026-01-01', '2026-01-01')",
        {"id": identificador, "estado": estado, "clave": clave},
    )


def test_los_lotes_y_los_trabajos_aceptan_pausa(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    run_migrations(settings, revision="head")

    _lote(settings, estado="paused")
    _trabajo(settings, "job-1", clave="ingest_batch:lote-1", estado="paused")
    assert _consultar(settings, "SELECT status FROM jobs WHERE id = 'job-1'") == [("paused",)]

    with pytest.raises(IntegrityError):
        _lote(settings, identificador="lote-2", estado="en-pausa-y-cansado")
    with pytest.raises(IntegrityError):
        _trabajo(settings, "job-2", clave=None, estado="en-pausa-y-cansado")


def test_un_trabajo_en_pausa_sigue_ocupando_su_clave_de_idempotencia(tmp_path: Path) -> None:
    """La consecuencia que no se ve: pausar no puede liberar la clave del trabajo del lote.

    Si la liberara, un segundo `ingest_batch` del mismo lote podría encolarse mientras el primero
    está en pausa y los dos avanzarían el mismo lote.
    """
    settings = _settings(tmp_path)
    run_migrations(settings, revision="head")
    _lote(settings)
    _trabajo(settings, "job-1", clave="ingest_batch:lote-1", estado="paused")

    with pytest.raises(IntegrityError):
        _trabajo(settings, "job-2", clave="ingest_batch:lote-1")

    definicion = _consultar(
        settings,
        "SELECT sql FROM sqlite_master WHERE name = 'uq_jobs_idempotency_alive'",
    )
    assert definicion and "'paused'" in str(definicion[0][0])


def test_la_recreacion_de_la_tabla_conserva_indices_y_claves_foraneas(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    run_migrations(settings, revision="head")
    indices = {
        str(fila[0])
        for fila in _consultar(
            settings,
            "SELECT name FROM sqlite_master WHERE type = 'index' AND tbl_name IN "
            "('jobs', 'ingestion_batches')",
        )
    }
    assert {"uq_jobs_idempotency_alive", "ix_jobs_status_created"} <= indices

    engine = build_engine(settings.data_paths.database)
    try:
        with engine.connect() as conexion:
            apuntan_batches = [
                (tabla, fila[2])
                for tabla in ("ingestion_items", "import_issues")
                for fila in conexion.execute(text(f"PRAGMA foreign_key_list({tabla})")).all()
                if fila[2] == "ingestion_batches"
            ]
            assert len(apuntan_batches) == 2, apuntan_batches
            assert conexion.execute(text("PRAGMA foreign_key_check")).all() == []
    finally:
        engine.dispose()


def test_el_downgrade_devuelve_la_pausa_a_la_cola(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    run_migrations(settings, revision="head")
    _lote(settings, estado="paused")
    _trabajo(settings, "job-1", clave="ingest_batch:lote-1", estado="paused")

    command.downgrade(alembic_config(settings), ANTES)

    assert _consultar(settings, "SELECT status FROM ingestion_batches WHERE id = 'lote-1'") == [
        ("queued",)
    ]
    assert _consultar(settings, "SELECT status FROM jobs WHERE id = 'job-1'") == [("queued",)]
    with pytest.raises(IntegrityError):
        _lote(settings, identificador="lote-2", estado="paused")
