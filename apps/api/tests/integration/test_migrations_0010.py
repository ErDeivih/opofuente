"""Reproduce la regresión de la 0009 sobre procedencia **válida** y comprueba la reparación.

Escenario del propietario: una base en `0008` con dos entradas del **mismo artefacto** cuyos tipos
de origen son correctos y distintos (`file` y `paste`). Al actualizar a la cabeza, esos tipos tienen
que sobrevivir: la 0009 borraba el tipo de todas las entradas de un artefacto con varios orígenes,
sin distinguir lo inventado de lo que consta. La 0010 los recupera por coincidencia exacta entre la
procedencia visible de la entrada y la del origen del artefacto.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import text

from opofuente.config import Settings
from opofuente.infrastructure.db import build_engine
from opofuente.infrastructure.migrations import run_migrations

AHORA = datetime(2026, 9, 16, 12, 0, tzinfo=UTC)


def _settings(tmp_path: Path) -> Settings:
    return Settings(data_dir=tmp_path / "datos", _env_file=None)


def _crear_base_0008_con_procedencia_valida(settings: Settings) -> None:
    """Base en 0008 con un artefacto que entró como fichero **y** como texto pegado.

    Los dos orígenes existen de verdad y cada entrada tiene el suyo, que es lo que el código nuevo
    escribe: `origin_display` casa con el `display_location` de su origen.
    """
    run_migrations(settings, revision="0008_item_representations")
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.begin() as conexion:
            conexion.execute(
                text(
                    "INSERT INTO source_artifacts (id, sha256, size_bytes, media_type, "
                    "storage_key, first_seen_at) VALUES "
                    "('art-1', :sha, 100, 'text/plain', 'sha256/aa/bb/' || :sha, :ahora)"
                ),
                {"sha": "b" * 64, "ahora": AHORA},
            )
            for identificador, tipo, donde in (
                ("org-file", "file", "material/tema-01.txt"),
                ("org-paste", "paste", "Apunte pegado del tema 1"),
            ):
                conexion.execute(
                    text(
                        "INSERT INTO artifact_origins (id, artifact_id, origin_type, "
                        "display_location, accessed_at) VALUES "
                        "(:id, 'art-1', :tipo, :donde, :ahora)"
                    ),
                    {"id": identificador, "tipo": tipo, "donde": donde, "ahora": AHORA},
                )
            conexion.execute(
                text(
                    "INSERT INTO ingestion_batches (id, kind, mode, status, source_path_display, "
                    "counters_json, created_at) VALUES "
                    "('batch-1', 'import', 'copy', 'succeeded', 'prueba', '{}', :ahora)"
                ),
                {"ahora": AHORA},
            )
            for identificador, ruta, tipo, visible in (
                ("item-file", "material/tema-01.txt", "file", "material/tema-01.txt"),
                ("item-paste", "Apunte pegado del tema 1", "paste", "Apunte pegado del tema 1"),
            ):
                conexion.execute(
                    text(
                        "INSERT INTO ingestion_items (id, batch_id, relative_path, original_name, "
                        "size_bytes, media_type, artifact_id, status, position, container_depth, "
                        "origin_type, origin_display) VALUES "
                        "(:id, 'batch-1', :ruta, :ruta, 100, 'text/plain', 'art-1', 'hashed', "
                        ":pos, 0, :tipo, :visible)"
                    ),
                    {
                        "id": identificador,
                        "ruta": ruta,
                        "tipo": tipo,
                        "visible": visible,
                        "pos": 1 if tipo == "file" else 2,
                    },
                )
    finally:
        engine.dispose()


def _tipo(settings: Settings, item_id: str) -> object:
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.connect() as conexion:
            return conexion.execute(
                text("SELECT origin_type FROM ingestion_items WHERE id = :id"), {"id": item_id}
            ).one()[0]
    finally:
        engine.dispose()


def test_la_procedencia_valida_sobrevive_al_actualizar_a_la_cabeza(tmp_path: Path) -> None:
    """Dos entradas del mismo artefacto con tipos distintos y **correctos** no se tocan.

    Regresión encontrada tras la 0009: al limpiar lo inventado borraba el tipo de **todas** las
    entradas de un artefacto con varios orígenes, así que una entrada de fichero y otra de texto
    pegado del mismo contenido (que sí constan) se quedaban sin procedencia.
    """
    settings = _settings(tmp_path)
    _crear_base_0008_con_procedencia_valida(settings)

    run_migrations(settings, revision="head")

    assert _tipo(settings, "item-file") == "file"
    assert _tipo(settings, "item-paste") == "paste"


def test_la_0010_recupera_el_tipo_que_la_0009_habia_borrado(tmp_path: Path) -> None:
    """En una base que ya ejecutó la 0009, la 0010 devuelve el tipo que consta.

    La reparación no adivina: solo escribe cuando la procedencia visible de la entrada coincide
    exactamente con la de un origen del artefacto.
    """
    settings = _settings(tmp_path)
    _crear_base_0008_con_procedencia_valida(settings)
    run_migrations(settings, revision="0009_repair_item_origin")
    assert _tipo(settings, "item-file") is None, "estado de partida: la 0009 borró lo válido"

    run_migrations(settings, revision="head")

    assert _tipo(settings, "item-file") == "file"
    assert _tipo(settings, "item-paste") == "paste"


def test_la_0010_no_inventa_cuando_la_procedencia_visible_no_coincide(tmp_path: Path) -> None:
    """Si la procedencia visible no casa con ningún origen, el tipo se queda «no consta»."""
    settings = _settings(tmp_path)
    _crear_base_0008_con_procedencia_valida(settings)
    run_migrations(settings, revision="0009_repair_item_origin")
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.begin() as conexion:
            # Una entrada antigua cuyo `origin_display` se rellenó con su ruta relativa y no casa
            # con ningún origen del artefacto: no hay nada que afirmar.
            conexion.execute(
                text(
                    "INSERT INTO ingestion_items (id, batch_id, relative_path, original_name, "
                    "size_bytes, media_type, artifact_id, status, position, container_depth, "
                    "origin_type, origin_display) VALUES "
                    "('item-antiguo', 'batch-1', 'copia-antigua.txt', 'copia-antigua.txt', 100, "
                    "'text/plain', 'art-1', 'hashed', 3, 0, NULL, 'copia-antigua.txt')"
                )
            )
    finally:
        engine.dispose()

    run_migrations(settings, revision="head")

    assert _tipo(settings, "item-antiguo") is None
    # Y no estropea las que sí constan.
    assert _tipo(settings, "item-file") == "file"
