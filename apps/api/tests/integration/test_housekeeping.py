"""Pruebas de higiene del almacén, diagnóstico y reindexación (S12: DEBT-007 y DEBT-015).

Lo que se comprueba, y por qué cada cosa importa:

1. **la foto no borra nada**: `report()` dice qué sobra sin tocar un byte;
2. **lo referenciado no se propone**: un artefacto con origen no aparece como candidato, y si
   se pide retirarlo por identificador, se salta;
3. **retirar exige confirmación** (el contrato pide que sea una decisión, no un accidente);
4. **un temporal fuera del árbol de datos no se toca**, aunque aparezca en la carpeta;
5. **ningún secreto ni ruta completa en el diagnóstico**: la clave de un proveedor no sale y las
   rutas van abreviadas, que es el criterio del slice.
"""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from opofuente.application.housekeeping_service import HousekeepingService
from opofuente.config import Settings
from opofuente.domain.housekeeping import HousekeepingAction, human_bytes
from opofuente.infrastructure.artifact_store import ArtifactStore
from opofuente.infrastructure.housekeeping_repository import SqlAlchemyHousekeepingRepository
from opofuente.infrastructure.migrations import run_migrations

AHORA = datetime(2026, 9, 19, 12, 0, tzinfo=UTC)
ALLOWED_ORIGIN = {"Origin": "http://127.0.0.1:5173"}


class _Reloj:
    def __init__(self, ahora: datetime = AHORA) -> None:
        self._ahora = ahora

    def now(self) -> datetime:
        return self._ahora


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    resolved = Settings(data_dir=tmp_path / "datos", _env_file=None)
    resolved.data_paths.ensure_directories()
    run_migrations(resolved, revision="head")
    return resolved


def _servicio(settings: Settings, *, ahora: datetime = AHORA) -> HousekeepingService:
    from opofuente.infrastructure.db import build_engine, build_session_factory

    engine = build_engine(settings.data_paths.database)
    return HousekeepingService(
        paths=settings.data_paths,
        artifacts=ArtifactStore(settings.data_paths),
        repository=SqlAlchemyHousekeepingRepository(build_session_factory(engine)),
        clock=_Reloj(ahora).now,
        retention_days=30,
    )


def _artefacto(settings: Settings, *, sha: str, con_origen: bool) -> str:
    """Un artefacto en el almacén, con o sin origen. Devuelve su identificador."""
    from opofuente.infrastructure.db import build_engine

    identificador = f"art-{sha[:6]}"
    almacen = ArtifactStore(settings.data_paths)
    ruta = settings.data_paths.artifacts / "sha256" / sha[:2] / sha[2:4] / sha
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_bytes(f"contenido {sha}".encode())
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.begin() as conexion:
            conexion.exec_driver_sql(
                "INSERT INTO source_artifacts (id, sha256, size_bytes, media_type, storage_key, "
                "first_seen_at) VALUES (?, ?, ?, 'text/plain', ?, ?)",
                (
                    identificador,
                    sha,
                    ruta.stat().st_size,
                    f"sha256/{sha[:2]}/{sha[2:4]}/{sha}",
                    AHORA.isoformat(),
                ),
            )
            if con_origen:
                conexion.exec_driver_sql(
                    "INSERT INTO artifact_origins (id, artifact_id, origin_type, display_location, "
                    "accessed_at) VALUES (?, ?, 'file', ?, ?)",
                    (f"orig-{sha[:6]}", identificador, f"carpeta/{sha[:6]}.txt", AHORA.isoformat()),
                )
    finally:
        engine.dispose()
    assert almacen.path_for_key(f"sha256/{sha[:2]}/{sha[2:4]}/{sha}").exists()
    return identificador


# --- la foto ------------------------------------------------------------------------------------


def test_la_foto_mide_el_almacen_y_dice_lo_que_no_puede_medir(settings: Settings) -> None:
    servicio = _servicio(settings)
    (settings.data_paths.artifacts / "suelto.bin").write_bytes(b"x" * 2048)

    informe = servicio.report()

    material = next(area for area in informe.usage if area.area == "artifacts")
    assert material.size_bytes == 2048
    assert material.file_count == 1
    assert material.readable is True
    # Un área que no existe se declara «no existe todavía», no como cero sin explicación.
    copias = next(area for area in informe.usage if area.area == "backups")
    assert copias.size_bytes == 0
    assert copias.note is not None


def test_la_foto_no_borra_nada(settings: Settings) -> None:
    """Medir no es retirar: `report()` es de solo lectura y esto lo fija."""
    servicio = _servicio(settings)
    sha = "a" * 64
    _artefacto(settings, sha=sha, con_origen=False)
    antes = sorted(ruta.name for ruta in settings.data_paths.artifacts.rglob("*") if ruta.is_file())

    informe = servicio.report()

    assert informe.candidates, "el artefacto sin origen se propone"
    despues = sorted(
        ruta.name for ruta in settings.data_paths.artifacts.rglob("*") if ruta.is_file()
    )
    assert despues == antes


def test_lo_referenciado_no_se_propone_retirar(settings: Settings) -> None:
    """La consulta comprueba las referencias: un artefacto con origen no es basura."""
    servicio = _servicio(settings)
    _artefacto(settings, sha="b" * 64, con_origen=True)
    _artefacto(settings, sha="c" * 64, con_origen=False)

    informe = servicio.report()

    referencias = {c.reference for c in informe.candidates}
    assert "art-bbbbbb" not in referencias, "tiene origen: no se propone retirar"
    assert "art-cccccc" in referencias


def test_los_temporales_de_una_operacion_interrumpida_se_proponen(settings: Settings) -> None:
    servicio = _servicio(settings)
    (settings.data_paths.tmp / "descarga.part").write_bytes(b"x" * 4096)
    (settings.data_paths.tmp / "restore-viejo").mkdir()
    (settings.data_paths.tmp / "restore-viejo" / "dato.bin").write_bytes(b"y" * 1024)

    informe = servicio.report()

    temporales = informe.by_action(HousekeepingAction.STALE_TEMP)
    referencias = {c.reference for c in temporales}
    assert "descarga.part" in referencias
    assert "restore-viejo" in referencias
    assert informe.reclaimable_bytes >= 5120


def test_los_trabajos_antiguos_se_proponen_solo_pasada_la_retencion(settings: Settings) -> None:
    from opofuente.infrastructure.db import build_engine

    engine = build_engine(settings.data_paths.database)
    try:
        with engine.begin() as conexion:
            for identificador, hace_dias, estado in (
                ("job-viejo", 45, "succeeded"),
                ("job-reciente", 1, "succeeded"),
                ("job-vivo", 45, "queued"),
            ):
                momento = AHORA - timedelta(days=hace_dias)
                conexion.exec_driver_sql(
                    "INSERT INTO jobs (id, job_type, status, payload_json, progress, "
                    "attempts, max_attempts, created_at, updated_at) VALUES "
                    "(?, 'ingest_batch', ?, '{}', 0, 0, 3, ?, ?)",
                    (identificador, estado, momento.isoformat(), momento.isoformat()),
                )
    finally:
        engine.dispose()

    # El reloj del servicio es «ahora»: 45 días atrás está fuera de la retención de 30.
    informe = _servicio(settings).report()

    referencias = {c.reference for c in informe.by_action(HousekeepingAction.OLD_JOB)}
    assert "job-viejo" in referencias
    assert "job-reciente" not in referencias, "todavía puede interesar verlo"
    assert "job-vivo" not in referencias, "un trabajo en cola no se retira nunca"


# --- retirada -----------------------------------------------------------------------------------


def test_retirar_artefactos_sin_uso_borra_fichero_y_fila(settings: Settings) -> None:
    servicio = _servicio(settings)
    _artefacto(settings, sha="d" * 64, con_origen=False)
    ruta = settings.data_paths.artifacts / "sha256" / "dd" / "dd" / ("d" * 64)

    resultado = servicio.purge_orphan_artifacts()

    assert resultado.removed == 1
    assert resultado.freed_bytes > 0
    assert not ruta.exists()
    assert servicio.report().by_action(HousekeepingAction.ORPHAN_ARTIFACT) == ()


def test_retirar_lo_referenciado_se_salta_y_se_dice(settings: Settings) -> None:
    """Pedir retirar un artefacto que tiene origen: no se toca y se informa del salto."""
    servicio = _servicio(settings)
    identificador = _artefacto(settings, sha="e" * 64, con_origen=True)
    ruta = settings.data_paths.artifacts / "sha256" / "ee" / "ee" / ("e" * 64)

    resultado = servicio.purge_orphan_artifacts(identifiers=(identificador,))

    assert resultado.removed == 0
    assert ruta.exists(), "el fichero sigue donde estaba"
    assert _artefacto_existe(settings, identificador), "la fila sigue donde estaba"


def test_retirar_temporales_respeta_los_que_estan_fuera_del_arbol(settings: Settings) -> None:
    """La guarda `is_within`: un temporal fuera del árbol de datos no se toca ni se propone."""
    servicio = _servicio(settings)
    dentro = settings.data_paths.tmp / "dentro.part"
    dentro.write_bytes(b"x")
    fuera = settings.data_paths.root.parent / "fuera.part"
    fuera.write_bytes(b"no me toques")

    informe = servicio.report()
    referencias = {c.reference for c in informe.by_action(HousekeepingAction.STALE_TEMP)}
    assert "dentro.part" in referencias
    assert "fuera.part" not in referencias

    resultado = servicio.purge_temps()
    assert resultado.removed == 1
    assert fuera.exists(), "lo que está fuera del árbol de datos sigue intacto"


def test_retirar_trabajos_antiguos_no_toca_los_que_estan_en_cola(settings: Settings) -> None:
    from opofuente.infrastructure.db import build_engine

    engine = build_engine(settings.data_paths.database)
    try:
        with engine.begin() as conexion:
            for identificador, estado in (("job-a", "succeeded"), ("job-b", "queued")):
                momento = AHORA - timedelta(days=90)
                conexion.exec_driver_sql(
                    "INSERT INTO jobs (id, job_type, status, payload_json, progress, "
                    "attempts, max_attempts, created_at, updated_at) VALUES "
                    "(?, 'ingest_batch', ?, '{}', 0, 0, 3, ?, ?)",
                    (identificador, estado, momento.isoformat(), momento.isoformat()),
                )
    finally:
        engine.dispose()

    resultado = _servicio(settings).purge_old_jobs()

    assert resultado.removed == 1
    assert _trabajo_existe(settings, "job-b"), "el que estaba en cola no se retira"


# --- API ----------------------------------------------------------------------------------------


def _cliente(settings: Settings) -> TestClient:
    from opofuente.main import create_app

    return TestClient(create_app(settings))


def test_la_api_ensena_la_foto_y_exige_confirmacion_para_retirar(settings: Settings) -> None:
    from opofuente.infrastructure.db import build_engine

    engine = build_engine(settings.data_paths.database)
    try:
        with engine.begin() as conexion:
            conexion.exec_driver_sql(
                "INSERT INTO source_artifacts (id, sha256, size_bytes, media_type, storage_key, "
                "first_seen_at) VALUES ('art-huerfano', ?, 10, 'text/plain', 'sha256/ff/ff/x', ?)",
                ("f" * 64, AHORA.isoformat()),
            )
    finally:
        engine.dispose()

    with _cliente(settings) as client:
        foto = client.get("/api/v1/housekeeping")
        assert foto.status_code == 200, foto.text
        cuerpo = foto.json()
        assert any(c["action"] == "orphan_artifact" for c in cuerpo["candidates"])
        assert cuerpo["reclaimable_bytes"] >= 0

        sin_confirmar = client.post(
            "/api/v1/housekeeping/orphan-artifacts",
            json={"references": None, "confirm": False},
            headers=ALLOWED_ORIGIN,
        )
        assert sin_confirmar.status_code == 409, sin_confirmar.text
        assert "confirmación" in sin_confirmar.json()["detail"]

        confirmado = client.post(
            "/api/v1/housekeeping/orphan-artifacts",
            json={"references": None, "confirm": True},
            headers=ALLOWED_ORIGIN,
        )
        assert confirmado.status_code == 200, confirmado.text
        assert confirmado.json()["removed"] == 1


def test_el_diagnostico_no_lleva_secretos_ni_rutas_completas(tmp_path: Path) -> None:
    """Criterio del slice: ningún secreto ni contenido privado en logs ni en el diagnóstico."""
    from opofuente.main import create_app

    settings = Settings(
        data_dir=tmp_path / "datos",
        llm_provider="openai_compatible",
        llm_base_url="http://127.0.0.1:11434/v1",
        llm_model="modelo-local",
        llm_api_key="clave-secreta-de-prueba-1234",
        _env_file=None,
    )
    settings.data_paths.ensure_directories()
    run_migrations(settings, revision="head")
    # Un registro con una clave y una ruta absoluta dentro, como podría escribir una biblioteca.
    (settings.data_paths.logs / "opofuente.log").write_text(
        '{"message": "arranque con api_key=clave-secreta-de-prueba-1234 en '
        'C:\\\\Users\\\\David\\\\datos\\\\opofuente.sqlite3"}',
        encoding="utf-8",
    )

    with TestClient(create_app(settings)) as client:
        respuesta = client.get("/api/v1/diagnostics")
        texto = client.get("/api/v1/diagnostics/text")

    assert respuesta.status_code == 200, respuesta.text
    cuerpo = respuesta.json()
    serializado = str(cuerpo)
    assert "clave-secreta-de-prueba-1234" not in serializado
    assert "David" not in serializado
    assert cuerpo["data_dir_display"].startswith("…")
    assert cuerpo["counts"]["artifacts"] == 0
    assert cuerpo["limits"]["max_file_bytes"] > 0
    assert any("[redactado]" in linea for linea in cuerpo["log_tail"])
    # El texto plano es el mismo diagnóstico: nada de dos versiones con datos distintos.
    assert texto.status_code == 200
    assert "clave-secreta-de-prueba-1234" not in texto.text
    assert "diagnóstico sanitizado" in texto.text


def test_rehacer_el_indice_dice_lo_que_ha_hecho(settings: Settings) -> None:
    """DEBT-015: la acción existe, informa y no puede perder texto (el índice es derivado)."""
    from opofuente.infrastructure.db import build_engine
    from opofuente.main import create_app

    engine = build_engine(settings.data_paths.database)
    try:
        with engine.begin() as conexion:
            conexion.exec_driver_sql(
                "INSERT INTO source_artifacts (id, sha256, size_bytes, media_type, storage_key, "
                "first_seen_at) VALUES ('art-1', ?, 10, 'text/plain', 'k', ?)",
                ("1" * 64, AHORA.isoformat()),
            )
            conexion.exec_driver_sql(
                "INSERT INTO extracted_representations (id, artifact_id, extractor_name, "
                "extractor_version, kind, status, quality, char_count, created_at) VALUES "
                "('rep-1', 'art-1', 'text', '1', 'plain_text', 'extracted', 'good', 10, ?)",
                (AHORA.isoformat(),),
            )
            conexion.exec_driver_sql(
                "INSERT INTO logical_documents (id, canonical_title, document_type, "
                "authority_tier, owner_scope, created_at, updated_at) VALUES "
                "('doc-1', 'Temario', 'curriculum', 'A', "
                "'private_user', ?, ?)",
                (AHORA.isoformat(), AHORA.isoformat()),
            )
            conexion.exec_driver_sql(
                "INSERT INTO document_versions (id, logical_document_id, artifact_id, "
                "representation_id, status, approved_at, created_at) VALUES "
                "('ver-1', 'doc-1', 'art-1', 'rep-1', 'accepted', ?, ?)",
                (AHORA.isoformat(), AHORA.isoformat()),
            )
            conexion.exec_driver_sql(
                "INSERT INTO evidence_spans (id, document_version_id, ordinal, quality, "
                "index_status, text, normalized_text, created_at) VALUES "
                "('span-1', 'ver-1', 1, 'good', 'indexed', 'El plazo es de diez dias', "
                "'el plazo es de diez dias', ?)",
                (AHORA.isoformat(),),
            )
    finally:
        engine.dispose()
    # El índice ya está completo: los disparadores de 0018 indexan al insertar. No se puede «romper»
    # desde SQL sin tocar tablas internas de FTS5 (un `DELETE FROM evidence_fts` no cambia nada
    # en una tabla de contenido externo y `delete-all` tampoco: comprobado), así que lo que se
    # prueba aquí es
    # la acción —que existe, que informa y que no pierde texto— y el caso «faltan fragmentos» se
    # cubre en la prueba unitaria de `index_health`, donde el descuadre se puede simular de verdad.
    with TestClient(create_app(settings)) as client:
        sano = client.get("/api/v1/search/index")
        assert sano.status_code == 200, sano.text
        assert sano.json()["healthy"] is True
        assert sano.json()["missing_entries"] == 0
        assert "1 fragmentos" in sano.json()["detail"]

        rehecho = client.post("/api/v1/search/reindex", headers=ALLOWED_ORIGIN)

        assert rehecho.status_code == 200, rehecho.text
        cuerpo = rehecho.json()
        assert cuerpo["indexed"] == 1
        assert cuerpo["before"] == 1
        assert cuerpo["after"] == 1
        assert cuerpo["took_seconds"] >= 0
        assert "rehecho" in cuerpo["detail"]

        # Y la búsqueda vuelve a encontrar el fragmento: el índice es derivado, no se pierde texto.
        busqueda = client.post(
            "/api/v1/search",
            json={"query": "plazo", "limit": 5},
            headers=ALLOWED_ORIGIN,
        )
        assert busqueda.status_code == 200, busqueda.text
        assert busqueda.json()["hits"], "el índice rehecho encuentra lo que ya estaba"


def test_el_tamano_legible_no_miente() -> None:
    assert human_bytes(0) == "0 B"
    assert human_bytes(2048) == "2.0 KiB"
    assert human_bytes(-1) == "desconocido"


def _artefacto_existe(settings: Settings, identificador: str) -> bool:
    conexion = sqlite3.connect(settings.data_paths.database)
    try:
        return (
            conexion.execute(
                "SELECT COUNT(*) FROM source_artifacts WHERE id = ?", (identificador,)
            ).fetchone()[0]
            == 1
        )
    finally:
        conexion.close()


def _trabajo_existe(settings: Settings, identificador: str) -> bool:
    conexion = sqlite3.connect(settings.data_paths.database)
    try:
        return (
            conexion.execute("SELECT COUNT(*) FROM jobs WHERE id = ?", (identificador,)).fetchone()[
                0
            ]
            == 1
        )
    finally:
        conexion.close()
