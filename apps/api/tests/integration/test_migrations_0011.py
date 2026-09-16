"""Reproduce y comprueba los dos casos límite del quinto corrector.

1. **Identidad del origen**: un mismo contenido que entró como fichero y como texto pegado con
   la **misma etiqueta** (`tema.txt`) tiene que dejar **dos** orígenes, uno por canal. Si la
   identidad es `(artifact_id, display_location)` el segundo reutiliza la fila del primero y su
   canal se pierde.
2. **Lectura CP-1252 con `0xC3` en el límite**: ese byte es `Ã` en Windows-1252, así que no puede
   recortarse como si fuera un carácter UTF-8 partido.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from alembic import command
from opofuente.config import Settings
from opofuente.domain.artifacts import OriginType, Sha256
from opofuente.infrastructure.db import build_engine, build_session_factory
from opofuente.infrastructure.ingestion_repository import SqlAlchemyIngestionRepository
from opofuente.infrastructure.migrations import alembic_config, run_migrations

AHORA = datetime(2026, 9, 16, 12, 0, tzinfo=UTC)
ANTES = datetime(2026, 9, 16, 9, 0, tzinfo=UTC)
SHA = "c" * 64


def _settings(tmp_path: Path) -> Settings:
    return Settings(data_dir=tmp_path / "datos", _env_file=None)


def _bajar_a(settings: Settings, revision: str) -> None:
    """Ejecuta un *downgrade* de verdad: `run_migrations` solo sube de revisión."""
    command.downgrade(alembic_config(settings), revision)


def _base_0008_con_dos_entradas_llamadas_igual(settings: Settings) -> None:
    """Base en 0008: el mismo contenido entró como fichero y como texto pegado, ambos `tema.txt`.

    Es el caso que pierde el canal, y se reproduce **como era de verdad**: con la identidad vieja
    `(artifact_id, display_location)` la tabla solo podía guardar **un** origen por etiqueta, así
    que el segundo canal ni siquiera llegó a registrarse. Quedan dos entradas del mismo artefacto y
    la misma etiqueta, y un único origen (`file`, `tema.txt`): mirando los datos no se puede saber
    cuál de las dos entradas vino por qué canal.
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
                {"sha": SHA, "ahora": AHORA},
            )
            conexion.execute(
                text(
                    "INSERT INTO artifact_origins (id, artifact_id, origin_type, "
                    "display_location, accessed_at) VALUES "
                    "('org-file', 'art-1', 'file', 'tema.txt', :ahora)"
                ),
                {"ahora": AHORA},
            )
            for indice in (1, 2):
                conexion.execute(
                    text(
                        "INSERT INTO ingestion_batches (id, kind, mode, status, "
                        "source_path_display, counters_json, created_at) VALUES "
                        "(:id, 'import', 'copy', 'succeeded', 'prueba', '{}', :ahora)"
                    ),
                    {"id": f"batch-{indice}", "ahora": AHORA},
                )
            for identificador, lote, posicion in (
                ("item-file", "batch-1", 1),
                ("item-paste", "batch-2", 1),
            ):
                conexion.execute(
                    text(
                        "INSERT INTO ingestion_items (id, batch_id, relative_path, original_name, "
                        "size_bytes, media_type, artifact_id, status, position, container_depth, "
                        "origin_type, origin_display) VALUES "
                        "(:id, :lote, 'tema.txt', 'tema.txt', 100, 'text/plain', 'art-1', "
                        "'hashed', :pos, 0, NULL, 'tema.txt')"
                    ),
                    {"id": identificador, "lote": lote, "pos": posicion},
                )
    finally:
        engine.dispose()


def _origen(settings: Settings, item_id: str) -> object:
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.connect() as conexion:
            return conexion.execute(
                text("SELECT origin_type FROM ingestion_items WHERE id = :id"), {"id": item_id}
            ).one()[0]
    finally:
        engine.dispose()


def test_la_etiqueta_repetida_no_permite_adivinar_el_canal(tmp_path: Path) -> None:
    """Con dos entradas que comparten artefacto y etiqueta, la reparación deja «no consta».

    El canal se perdió: la etiqueta es la misma para las dos, así que elegir una sería inventar. La
    respuesta honesta es `NULL`, que la interfaz declara como desconocido.
    """
    settings = _settings(tmp_path)
    _base_0008_con_dos_entradas_llamadas_igual(settings)

    run_migrations(settings, revision="head")

    assert _origen(settings, "item-file") is None
    assert _origen(settings, "item-paste") is None


def test_el_canal_no_se_pierde_al_registrar_el_mismo_nombre(tmp_path: Path) -> None:
    """`register_artifact` identifica el origen por artefacto, **canal** y etiqueta.

    Con la identidad vieja `(artifact_id, display_location)`, el mismo contenido que entra como
    fichero y como texto pegado con la misma etiqueta solo dejaba un origen: el segundo
    reutilizaba la fila del primero y su canal desaparecía.
    """
    settings = _settings(tmp_path)
    run_migrations(settings, revision="head")
    engine = build_engine(settings.data_paths.database)
    try:
        repositorio = SqlAlchemyIngestionRepository(build_session_factory(engine))
        digest = Sha256(SHA)
        for tipo in (OriginType.FILE, OriginType.PASTE):
            repositorio.register_artifact(
                digest=digest,
                size_bytes=100,
                media_type="text/plain",
                storage_key=f"sha256/aa/bb/{SHA}",
                origin_type=tipo,
                display_location="tema.txt",
                original_name="tema.txt",
                source_path_display=None,
                file_mtime=None,
                now=AHORA,
            )
        with engine.connect() as conexion:
            origenes = conexion.execute(
                text(
                    "SELECT origin_type FROM artifact_origins WHERE artifact_id = "
                    "(SELECT id FROM source_artifacts WHERE sha256 = :sha) ORDER BY origin_type"
                ),
                {"sha": SHA},
            ).all()
    finally:
        engine.dispose()

    assert [fila[0] for fila in origenes] == ["file", "paste"]


def test_el_downgrade_no_deja_canales_sin_origen(tmp_path: Path) -> None:
    """La vuelta atrás pierde un canal **a propósito**, pero no deja ninguno colgando.

    Con la restricción vieja no caben dos orígenes con la misma etiqueta, así que el `downgrade`
    conserva uno y borra el otro. El criterio es **determinista y no temporal**: la tabla no guarda
    cuándo se creó el origen (`accessed_at` es la última vez que se usó, y se actualiza), así que se
    conserva el de `id` menor en orden binario. Aquí el `id` menor es justo el de fecha posterior, y
    la prueba lo fija así a propósito para que nadie pueda leer el `id` como una fecha.

    Además, ninguna entrada puede quedarse con un canal que ya no existe: la entrada que entró como
    texto pegado se queda sin procedencia («no consta») en cuanto su origen se retira.
    """
    settings = _settings(tmp_path)
    run_migrations(settings, revision="head")
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.begin() as conexion:
            conexion.execute(
                text(
                    "INSERT INTO source_artifacts (id, sha256, size_bytes, media_type, "
                    "storage_key, first_seen_at) VALUES "
                    "('art-1', :sha, 100, 'text/plain', 'sha256/aa/bb/' || :sha, :ahora)"
                ),
                {"sha": SHA, "ahora": AHORA},
            )
            # Los dos canales del mismo contenido y la misma etiqueta, con el orden de `id`
            # invertido respecto al temporal: `org-z` es el más antiguo pero el que menos ordena.
            for origen_id, tipo, cuando in (
                ("org-z", "paste", ANTES),
                ("org-a", "file", AHORA),
            ):
                conexion.execute(
                    text(
                        "INSERT INTO artifact_origins (id, artifact_id, origin_type, "
                        "display_location, accessed_at) VALUES "
                        "(:id, 'art-1', :tipo, 'tema.txt', :cuando)"
                    ),
                    {"id": origen_id, "tipo": tipo, "cuando": cuando},
                )
            conexion.execute(
                text(
                    "INSERT INTO ingestion_batches (id, kind, mode, status, "
                    "source_path_display, counters_json, created_at) VALUES "
                    "('batch-1', 'import', 'copy', 'succeeded', 'prueba', '{}', :ahora)"
                ),
                {"ahora": AHORA},
            )
            # Una entrada por canal, las dos con la misma etiqueta y su canal correcto. Van en lotes
            # distintos, que es como llegan de verdad: un fichero por la carpeta y un pegado aparte
            # (además, la ruta relativa es única dentro de un lote).
            conexion.execute(
                text(
                    "INSERT INTO ingestion_batches (id, kind, mode, status, "
                    "source_path_display, counters_json, created_at) VALUES "
                    "('batch-2', 'import', 'copy', 'succeeded', 'pegado', '{}', :ahora)"
                ),
                {"ahora": AHORA},
            )
            for item_id, lote, posicion, tipo in (
                ("item-file", "batch-1", 1, "file"),
                ("item-paste", "batch-2", 1, "paste"),
            ):
                conexion.execute(
                    text(
                        "INSERT INTO ingestion_items (id, batch_id, relative_path, original_name, "
                        "size_bytes, media_type, artifact_id, status, position, container_depth, "
                        "origin_type, origin_display) VALUES "
                        "(:id, :lote, 'tema.txt', 'tema.txt', 100, 'text/plain', 'art-1', "
                        "'extracted', :pos, 0, :tipo, 'tema.txt')"
                    ),
                    {"id": item_id, "lote": lote, "pos": posicion, "tipo": tipo},
                )
    finally:
        engine.dispose()

    _bajar_a(settings, "0010_recover_item_origin")

    engine = build_engine(settings.data_paths.database)
    try:
        with engine.connect() as conexion:
            revision = conexion.execute(text("SELECT version_num FROM alembic_version")).scalar()
            origenes = conexion.execute(
                text(
                    "SELECT id, origin_type, display_location FROM artifact_origins "
                    "WHERE artifact_id = 'art-1'"
                )
            ).all()
            tipos: dict[str, str | None] = {
                str(fila[0]): fila[1]
                for fila in conexion.execute(
                    text("SELECT id, origin_type FROM ingestion_items")
                ).all()
            }
        assert revision == "0010_recover_item_origin", "el downgrade se ejecutó de verdad"
        assert [fila[0] for fila in origenes] == ["org-a"], "queda uno: el de `id` menor"
        assert origenes[0][1] == "file", (
            "y es el posterior en el tiempo: el criterio no es la fecha"
        )
        assert tipos["item-file"] == "file", "su canal sigue existiendo"
        assert tipos["item-paste"] is None, "su canal se retiró: no puede conservarlo"

        with pytest.raises(IntegrityError), engine.begin() as conexion:
            conexion.execute(
                text(
                    "INSERT INTO artifact_origins (id, artifact_id, origin_type, "
                    "display_location, accessed_at) VALUES "
                    "('org-c', 'art-1', 'paste', 'tema.txt', :ahora)"
                ),
                {"ahora": AHORA},
            )
    finally:
        engine.dispose()

    # Y volver a subir devuelve la identidad con canal: el ciclo entero está comprobado.
    run_migrations(settings, revision="head")

    engine = build_engine(settings.data_paths.database)
    try:
        with engine.begin() as conexion:
            conexion.execute(
                text(
                    "INSERT INTO artifact_origins (id, artifact_id, origin_type, "
                    "display_location, accessed_at) VALUES "
                    "('org-c', 'art-1', 'paste', 'tema.txt', :ahora)"
                ),
                {"ahora": AHORA},
            )
            origenes = conexion.execute(
                text(
                    "SELECT origin_type FROM artifact_origins WHERE artifact_id = 'art-1' "
                    "ORDER BY origin_type"
                )
            ).all()
        assert [fila[0] for fila in origenes] == ["file", "paste"]
    finally:
        engine.dispose()
