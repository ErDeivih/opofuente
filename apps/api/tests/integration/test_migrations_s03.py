"""Pruebas de las migraciones de S03: datos reales creados bajo una revisión y migrados.

Las migraciones se ejecutan de verdad (Alembic sobre una base temporal), con **datos creados en la
revisión anterior**: así se comprueba qué pasa con el material que ya existía, no solo con una base
vacía. Es donde se demuestra que una migración no inventa información: lo que no se puede saber se
queda `NULL`, nunca adivinado.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import text

from opofuente.config import Settings
from opofuente.infrastructure.db import build_engine
from opofuente.infrastructure.migrations import run_migrations

AHORA = datetime(2026, 9, 15, 12, 0, tzinfo=UTC)


def _settings(tmp_path: Path) -> Settings:
    return Settings(data_dir=tmp_path / "datos", _env_file=None)


def _crear_datos_ambiguos(settings: Settings, *, origenes: tuple[str, ...]) -> None:
    """Crea una base en la revisión 0006 con un artefacto con varios orígenes y su entrada."""
    run_migrations(settings, revision="0006_extracted_representations")
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.begin() as conexion:
            conexion.execute(
                text(
                    "INSERT INTO source_artifacts (id, sha256, size_bytes, media_type, "
                    "storage_key, first_seen_at) VALUES "
                    "('art-1', :sha, 100, 'text/plain', 'sha256/aa/bb/' || :sha, :ahora)"
                ),
                {"sha": "a" * 64, "ahora": AHORA},
            )
            for origen in origenes:
                conexion.execute(
                    text(
                        "INSERT INTO artifact_origins (id, artifact_id, origin_type, "
                        "display_location, accessed_at) VALUES "
                        "(:id, 'art-1', :tipo, :donde, :ahora)"
                    ),
                    {
                        "id": f"org-{origen}",
                        "tipo": origen,
                        "donde": f"origen-{origen}",
                        "ahora": AHORA,
                    },
                )
            conexion.execute(
                text(
                    "INSERT INTO ingestion_batches (id, kind, mode, status, source_path_display, "
                    "counters_json, created_at) VALUES "
                    "('batch-1', 'import', 'copy', 'succeeded', 'prueba', '{}', :ahora)"
                ),
                {"ahora": AHORA},
            )
            conexion.execute(
                text(
                    "INSERT INTO ingestion_items (id, batch_id, relative_path, original_name, "
                    "size_bytes, media_type, artifact_id, status, position) VALUES "
                    "('item-1', 'batch-1', 'notas.txt', 'notas.txt', 100, 'text/plain', "
                    "'art-1', 'hashed', 1)"
                )
            )
    finally:
        engine.dispose()


#: Consultas fijas de la entrada de prueba: una por columna que interesa, escritas enteras para que
#: no haya SQL construido con texto variable.
_CONSULTAS = {
    "origin_type": text("SELECT origin_type FROM ingestion_items WHERE id = 'item-1'"),
    "origin_display": text("SELECT origin_display FROM ingestion_items WHERE id = 'item-1'"),
    "container_depth": text("SELECT container_depth FROM ingestion_items WHERE id = 'item-1'"),
}


def _leer_entrada(settings: Settings, columna: str) -> object:
    """Lee una columna concreta de la entrada de prueba, de las declaradas arriba."""
    consulta = _CONSULTAS[columna]
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.connect() as conexion:
            return conexion.execute(consulta).one()[0]
    finally:
        engine.dispose()


def test_la_migracion_no_inventa_el_origen_cuando_es_ambiguo(tmp_path: Path) -> None:
    """Con tres orígenes distintos no se puede saber cuál era el de la entrada: queda «no consta».

    La migración anterior asignaba `paste` a todas las entradas cuyo artefacto tuviera **algún**
    origen pegado, así que unos bytes que entraron como fichero, como texto pegado y como URL
    aparecían como «pegados» aunque no lo fueran. Inventar procedencia es peor que no afirmar nada.
    """
    settings = _settings(tmp_path)
    _crear_datos_ambiguos(settings, origenes=("file", "paste", "url"))

    run_migrations(settings, revision="head")

    assert _leer_entrada(settings, "origin_type") is None, (
        "la procedencia ambigua queda sin afirmar"
    )
    assert _leer_entrada(settings, "origin_display") == "notas.txt", "lo que sí se sabe se conserva"
    assert _leer_entrada(settings, "container_depth") == 0


def test_la_migracion_conserva_el_origen_cuando_no_hay_duda(tmp_path: Path) -> None:
    """Con un único origen registrado, ese es el de la entrada: el dato no es ambiguo."""
    settings = _settings(tmp_path)
    _crear_datos_ambiguos(settings, origenes=("url",))

    run_migrations(settings, revision="head")

    assert _leer_entrada(settings, "origin_type") == "url"


def test_la_migracion_crea_la_relacion_entrada_representacion(tmp_path: Path) -> None:
    """0008 sustituye la clave ajena singular por la tabla de asociación, sin perder enlaces.

    Se crea una representación enlazada bajo 0007 (cuando el enlace era una columna) y se comprueba
    que después de migrar sigue existiendo como fila de `item_representations`.
    """
    settings = _settings(tmp_path)
    _crear_datos_ambiguos(settings, origenes=("file",))
    run_migrations(settings, revision="0007_item_depth_and_origin")
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.begin() as conexion:
            conexion.execute(
                text(
                    "INSERT INTO extracted_representations (id, artifact_id, extractor_name, "
                    "extractor_version, kind, status, quality, char_count, ocr_candidate, "
                    "sections_json, warnings_json, metadata_json, format_version, created_at) "
                    "VALUES ('rep-1', 'art-1', 'plain_text', '1', 'native_text', 'extracted', "
                    "'good', 10, 0, '[]', '[]', '{}', 1, :ahora)"
                ),
                {"ahora": AHORA},
            )
            conexion.execute(
                text("UPDATE ingestion_items SET representation_id = 'rep-1' WHERE id = 'item-1'")
            )
    finally:
        engine.dispose()

    run_migrations(settings, revision="head")

    engine = build_engine(settings.data_paths.database)
    try:
        with engine.connect() as conexion:
            filas = conexion.execute(
                text("SELECT item_id, representation_id FROM item_representations")
            ).all()
            columnas = {
                fila[1]
                for fila in conexion.execute(text("PRAGMA table_info(ingestion_items)")).all()
            }
        assert [tuple(fila) for fila in filas] == [("item-1", "rep-1")]
    finally:
        engine.dispose()
    assert "representation_id" not in columnas, "la columna singular ya no existe"
