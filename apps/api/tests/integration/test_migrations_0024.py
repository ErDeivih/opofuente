"""Migración 0024: las versiones del dossier de un tema (S13, parte 1).

Lo que se prueba es la forma de la tabla que sostiene la promesa «la versión anterior queda guardada
y
consultable»: la huella **no se repite por nodo** (pedir el mismo dossier dos veces no crea dos
versiones), el contenido se guarda entero, borrar el nodo se lleva sus instantáneas y bajar de
revisión
retira la tabla. Que `payload_json` sea obligatorio también se comprueba: una versión sin contenido
no
sería una versión, sería una fila que promete algo que no puede leer.
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

AHORA = datetime(2026, 9, 24, 9, 0, tzinfo=UTC)
ANTES = "0023_pause_batch"


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


def _nodo(settings: Settings) -> None:
    _ejecutar(
        settings,
        "INSERT INTO oppositions (id, code, name, active, created_at, updated_at) VALUES "
        "('op-1', 'tai', 'TAI', 0, :ahora, :ahora)",
        {"ahora": AHORA},
    )
    _ejecutar(
        settings,
        "INSERT INTO convocation_versions (id, opposition_id, code, title, official_url, "
        "published_at, status, created_at, updated_at) VALUES ('conv-1', 'op-1', 'tai-2026', "
        "'TAI', 'https://boe.es/x', '2026-01-01', 'available', :ahora, :ahora)",
        {"ahora": AHORA},
    )
    _ejecutar(
        settings,
        "INSERT INTO curriculum_nodes (id, convocation_version_id, node_type, official_code, "
        "title, position, path, depth) VALUES ('nodo-1', 'conv-1', 'topic', '1', 'Tema 1', 1, "
        "'I.1', 1)",
    )


def _instantanea(settings: Settings, *, id_: str, hash_: str, payload: str = "{}") -> None:
    _ejecutar(
        settings,
        "INSERT INTO dossier_snapshots (id, curriculum_node_id, content_hash, built_at, "
        "created_at, sources_count, passages_count, payload_json) VALUES (:id, 'nodo-1', :hash, "
        ":ahora, :ahora, 1, 2, :payload)",
        {"id": id_, "hash": hash_, "ahora": AHORA, "payload": payload},
    )


def test_la_tabla_guarda_la_huella_y_la_huella_no_se_repite_por_nodo(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    run_migrations(settings, revision="head")
    _nodo(settings)

    _instantanea(settings, id_="ver-1", hash_="a" * 64)

    with pytest.raises(IntegrityError):
        _instantanea(settings, id_="ver-2", hash_="a" * 64)

    # Otra huella sí entra: es una lectura distinta del mismo tema.
    _instantanea(settings, id_="ver-2", hash_="b" * 64)
    assert _consultar(settings, "SELECT COUNT(*) FROM dossier_snapshots") == [(2,)]


def test_la_huella_tiene_que_ser_una_huella(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    run_migrations(settings, revision="head")
    _nodo(settings)

    with pytest.raises(IntegrityError):
        _instantanea(settings, id_="ver-corta", hash_="a" * 10)


def test_una_version_sin_contenido_no_entra(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    run_migrations(settings, revision="head")
    _nodo(settings)

    with pytest.raises(IntegrityError):
        _ejecutar(
            settings,
            "INSERT INTO dossier_snapshots (id, curriculum_node_id, content_hash, built_at, "
            "created_at, payload_json) VALUES ('ver-3', 'nodo-1', :hash, :ahora, :ahora, NULL)",
            {"hash": "c" * 64, "ahora": AHORA},
        )


def test_borrar_el_nodo_se_lleva_sus_instantaneas(tmp_path: Path) -> None:
    """Una instantánea de un nodo que ya no existe no es historia: es basura."""
    settings = _settings(tmp_path)
    run_migrations(settings, revision="head")
    _nodo(settings)
    _instantanea(settings, id_="ver-1", hash_="a" * 64)

    _ejecutar(settings, "DELETE FROM curriculum_nodes WHERE id = 'nodo-1'")

    assert _consultar(settings, "SELECT COUNT(*) FROM dossier_snapshots") == [(0,)]


def test_al_bajar_de_revision_la_tabla_desaparece(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    run_migrations(settings, revision="head")
    _nodo(settings)
    _instantanea(settings, id_="ver-1", hash_="a" * 64)

    command.downgrade(alembic_config(settings), ANTES)

    tablas = {str(fila[0]) for fila in _consultar(settings, "SELECT name FROM sqlite_master")}
    assert "dossier_snapshots" not in tablas
    assert "curriculum_nodes" in tablas, "bajar de revisión no toca lo que no es suyo"
