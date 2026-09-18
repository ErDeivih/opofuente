"""Pruebas de integración: salud, migración desde base vacía y configuración expuesta."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from opofuente import __version__
from opofuente.api.errors import PROBLEM_MEDIA_TYPE
from opofuente.application.system_service import SystemService
from opofuente.config import Settings
from opofuente.infrastructure.db import build_engine
from opofuente.infrastructure.migrations import database_revision, run_migrations, script_head
from opofuente.infrastructure.probes import DatabaseProbe
from opofuente.main import create_app


def test_live_responde_y_versiona(client: TestClient) -> None:
    response = client.get("/api/v1/health/live")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "alive"
    assert body["version"]


def test_ready_comprueba_base_de_datos_migrada(client: TestClient) -> None:
    response = client.get("/api/v1/health/ready")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ready"
    checks = {check["name"]: check for check in body["checks"]}
    assert checks["database"]["status"] == "ok"
    assert "foreign_keys=ON" in checks["database"]["detail"]
    assert "journal_mode=wal" in checks["database"]["detail"]
    assert checks["data_dir"]["status"] == "ok"
    assert checks["data_dir"]["detail"] == "directorio de datos escribible"


def test_ready_falla_si_la_base_de_datos_esta_vacia(unmigrated_client: TestClient) -> None:
    response = unmigrated_client.get("/api/v1/health/ready")
    assert response.status_code == 503
    assert response.headers["content-type"].startswith(PROBLEM_MEDIA_TYPE)
    body = response.json()
    assert body["code"] == "not_ready"
    assert body["correlation_id"]
    checks = {check["name"]: check for check in body["checks"]}
    assert checks["database"]["status"] == "failed"
    assert checks["data_dir"]["status"] == "ok"


def test_ready_falla_si_la_revision_no_coincide(migrated_settings: Settings) -> None:
    app = create_app(migrated_settings)
    # Una base migrada a un esquema anterior no debe darse por buena. Se reemplaza el servicio
    # por el punto de composición documentado (app.state), sin tocar la base de datos.
    app.state.system_service = SystemService(
        version=__version__,
        probes=(DatabaseProbe(app.state.session_factory, expected_revision="9999_inexistente"),),
        capability_providers=(),
    )
    with TestClient(app) as client:
        response = client.get("/api/v1/health/ready")
    assert response.status_code == 503
    checks = {check["name"]: check for check in response.json()["checks"]}
    assert "!= esperada 9999_inexistente" in checks["database"]["detail"]


def test_migracion_desde_base_vacia(settings: Settings) -> None:
    settings.data_paths.ensure_directories()
    assert not settings.data_paths.database.exists()
    run_migrations(settings)
    assert settings.data_paths.database.is_file()

    engine = build_engine(settings.data_paths.database)
    try:
        assert database_revision(engine) == script_head(settings)
    finally:
        engine.dispose()

    # Repetir la migración no cambia la revisión ni duplica metadatos.
    run_migrations(settings)
    engine = build_engine(settings.data_paths.database)
    try:
        assert database_revision(engine) == script_head(settings)
    finally:
        engine.dispose()


def test_arbol_de_datos_creado_al_arrancar(client: TestClient, migrated_settings: Settings) -> None:
    paths = migrated_settings.data_paths
    for directory in (
        paths.root,
        paths.artifacts,
        paths.extracted,
        paths.qdrant,
        paths.exports,
        paths.backups,
        paths.logs,
        paths.tmp,
    ):
        assert directory.is_dir(), directory
    assert (paths.logs / "opofuente.log").is_file()


def test_capabilities_no_declara_operativo_lo_que_no_existe(client: TestClient) -> None:
    response = client.get("/api/v1/capabilities")
    assert response.status_code == 200
    body = response.json()
    capabilities = {item["id"]: item for item in body["capabilities"]}
    assert capabilities["ocr"]["status"] == "disabled"
    assert capabilities["llm"]["status"] == "disabled"
    # S02 existe y se comprueba de verdad: almacén escribible y worker corriendo en este proceso.
    assert capabilities["artifact_store"]["status"] == "enabled"
    assert capabilities["worker"]["status"] == "enabled"
    # S09 construyó la búsqueda literal y **no** el índice vectorial: sin embeddings no hay vectores
    # que indexar, así que no se promete un slice futuro.
    assert capabilities["vector_index"]["status"] == "unavailable"
    assert capabilities["vector_index"]["planned_slice"] is None
    # El SQLite de este equipo se comprueba de verdad: FTS5 disponible **y** índice creado en esta
    # base (migración 0018 aplicada, que es lo que comprueba la sonda de arranque).
    assert capabilities["fts5"]["status"] == "enabled"
    # Nada se declara operativo sin comprobarlo: lo ausente genera su degradación explícita.
    assert any(
        degradation["code"] == "vector_index.unavailable" for degradation in body["degradations"]
    )
    assert all(degradation["code"] for degradation in body["degradations"])


def test_settings_no_expone_la_clave(tmp_path: Path) -> None:
    settings = Settings(
        data_dir=tmp_path / "data",
        llm_provider="openai_compatible",
        llm_base_url="http://127.0.0.1:11434/v1",
        llm_model="modelo-local",
        llm_api_key="clave-secreta-de-prueba",
        _env_file=None,
    )
    settings.data_paths.ensure_directories()
    run_migrations(settings)
    with TestClient(create_app(settings)) as client:
        response = client.get("/api/v1/settings")
    assert response.status_code == 200
    body = response.json()
    assert body["llm"]["api_key_configured"] is True
    assert body["llm"]["provider"] == "openai_compatible"
    assert body["llm"]["sends_data_off_device"] is True
    assert body["editable"] is False
    assert "clave-secreta-de-prueba" not in json.dumps(body)
    assert body["disk_total_bytes"] > 0


def test_openapi_y_docs_disponibles(client: TestClient) -> None:
    assert client.get("/api/v1/openapi.json").status_code == 200
    assert client.get("/api/v1/docs").status_code == 200
