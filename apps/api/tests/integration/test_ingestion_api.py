"""Pruebas de integración de la API de ingestión y trabajos (S02)."""

from __future__ import annotations

import time
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from opofuente.api.errors import PROBLEM_MEDIA_TYPE
from opofuente.config import Settings
from opofuente.domain.ingestion import ItemStatus
from opofuente.domain.jobs import JobStatus
from opofuente.infrastructure.db import build_engine, build_session_factory
from opofuente.infrastructure.db_models import JobRecord
from opofuente.infrastructure.job_repository import SqlAlchemyJobRepository
from opofuente.main import create_app

ALLOWED_ORIGIN = {"Origin": "http://127.0.0.1:5173"}
FOREIGN_ORIGIN = {"Origin": "http://malicioso.example"}


@pytest.fixture
def material(tmp_path: Path) -> Path:
    root = tmp_path / "material"
    (root / "apuntes").mkdir(parents=True)
    (root / "apuntes" / "ley.md").write_text("ley 39/2015", encoding="utf-8")
    (root / "apuntes" / "ley-copia.md").write_text("ley 39/2015", encoding="utf-8")
    (root / ".oculto.txt").write_text("no", encoding="utf-8")
    return root


def inventariar(client: TestClient, root: Path) -> dict:
    response = client.post("/api/v1/inventories", json={"source_path": str(root)})
    assert response.status_code == 200, response.text
    return response.json()


def test_inventario_en_lectura_no_copia_y_da_vista_previa(
    api_only_client: TestClient, material: Path
) -> None:
    before = snapshot(material)
    body = inventariar(api_only_client, material)

    assert body["batch"]["kind"] == "inventory"
    assert body["batch"]["mode"] == "read_only"
    assert body["batch"]["status"] == "succeeded"
    assert body["copied_anything"] is False
    assert "sin modificarla" in body["note"]
    assert body["batch"]["counters"]["inventoried"] == 2
    assert body["batch"]["counters"]["omitted_hidden"] == 1
    assert body["batch"]["formats"][".md"] == 2
    assert [entry["relative_path"] for entry in body["sample"]] == [
        "apuntes/ley-copia.md",
        "apuntes/ley.md",
    ]
    # La ruta absoluta del usuario no se publica: solo la versión abreviada.
    assert "source_path_display" in body["batch"]
    assert str(material) not in body["batch"]["source_path_display"]
    # Omitir algo sin decir qué: la incidencia lleva la ruta relativa del elemento afectado.
    assert [(issue["code"], issue["relative_path"]) for issue in body["issues"]] == [
        ("omitted_hidden", ".oculto.txt")
    ]
    assert snapshot(material) == before


def test_las_incidencias_de_directorio_conservan_su_ruta(
    api_only_client: TestClient, tmp_path: Path
) -> None:
    """Un directorio omitido no tiene entrada propia: su ruta debe persistirse en la incidencia."""
    root = tmp_path / "con-carpetas"
    (root / "node_modules").mkdir(parents=True)
    (root / "node_modules" / "basura.js").write_text("no", encoding="utf-8")
    (root / "ok.txt").write_text("contenido", encoding="utf-8")

    body = inventariar(api_only_client, root)
    batch_id = body["batch"]["id"]
    assert {issue["code"]: issue["relative_path"] for issue in body["issues"]} == {
        "omitted_directory": "node_modules"
    }

    # Y sigue ahí al leerla de la base de datos, no solo en la respuesta inmediata.
    listado = api_only_client.get(f"/api/v1/ingestion-batches/{batch_id}/issues").json()
    assert {issue["code"]: issue["relative_path"] for issue in listado["issues"]} == {
        "omitted_directory": "node_modules"
    }


def snapshot(root: Path) -> dict[str, tuple[int, float]]:
    return {
        path.relative_to(root).as_posix(): (path.stat().st_size, path.stat().st_mtime)
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def test_inventario_con_ruta_invalida_devuelve_400(api_only_client: TestClient) -> None:
    # El cuerpo vacío incumple el contrato (min_length=1): 422 con el detalle del campo.
    vacio = api_only_client.post("/api/v1/inventories", json={"source_path": ""})
    assert vacio.status_code == 422
    assert vacio.headers["content-type"].startswith(PROBLEM_MEDIA_TYPE)
    assert vacio.json()["field_errors"]

    # Rutas que existen como cadena pero no como carpeta utilizable: 400 con motivo.
    for ruta in ("   ", "ruta/relativa", "F:\\no-existe-de-verdad-1234"):
        response = api_only_client.post("/api/v1/inventories", json={"source_path": ruta})
        assert response.status_code == 400, ruta
        assert response.headers["content-type"].startswith(PROBLEM_MEDIA_TYPE)
        assert response.json()["code"] == "invalid_source"


def test_inventario_del_directorio_de_datos_se_rechaza(
    api_only_client: TestClient, migrated_settings: Settings
) -> None:
    response = api_only_client.post(
        "/api/v1/inventories", json={"source_path": str(migrated_settings.data_dir)}
    )
    assert response.status_code == 400
    assert "datos de OpoFuente" in response.json()["detail"]


def test_inventario_de_una_carpeta_inexistente_devuelve_404_al_consultarlo(
    api_only_client: TestClient,
) -> None:
    response = api_only_client.get("/api/v1/inventories/no-existe")
    assert response.status_code == 404
    assert response.json()["code"] == "not_found"


def test_escritura_desde_origen_ajeno_se_rechaza(
    api_only_client: TestClient, material: Path
) -> None:
    response = api_only_client.post(
        "/api/v1/inventories", json={"source_path": str(material)}, headers=FOREIGN_ORIGIN
    )
    assert response.status_code == 403
    assert response.json()["code"] == "forbidden_origin"


def test_confirmar_importacion_crea_lote_y_trabajo_en_cola(
    api_only_client: TestClient, material: Path
) -> None:
    inventario = inventariar(api_only_client, material)
    response = api_only_client.post(
        f"/api/v1/inventories/{inventario['batch']['id']}/confirm-import", headers=ALLOWED_ORIGIN
    )
    assert response.status_code == 200
    batch = response.json()
    assert batch["kind"] == "import"
    assert batch["mode"] == "copy"
    assert batch["status"] == "queued"
    assert batch["job_id"]
    assert batch["inventory_batch_id"] == inventario["batch"]["id"]

    job = api_only_client.get(f"/api/v1/jobs/{batch['job_id']}").json()
    assert job["job_type"] == "ingest_batch"
    assert job["status"] == "queued"

    # Confirmar otra vez no crea otro lote ni otro trabajo.
    repetido = api_only_client.post(
        f"/api/v1/inventories/{inventario['batch']['id']}/confirm-import", headers=ALLOWED_ORIGIN
    )
    assert repetido.json()["id"] == batch["id"]
    assert len(api_only_client.get("/api/v1/jobs").json()) == 1


def test_lote_inexistente_devuelve_404(api_only_client: TestClient) -> None:
    for ruta in (
        "/api/v1/ingestion-batches/no-existe",
        "/api/v1/ingestion-batches/no-existe/items",
        "/api/v1/ingestion-batches/no-existe/issues",
        "/api/v1/ingestion-batches/no-existe/report",
        "/api/v1/jobs/no-existe",
    ):
        response = api_only_client.get(ruta)
        assert response.status_code == 404, ruta


def test_cancelar_un_lote_y_un_trabajo(api_only_client: TestClient, material: Path) -> None:
    inventario = inventariar(api_only_client, material)
    batch = api_only_client.post(
        f"/api/v1/inventories/{inventario['batch']['id']}/confirm-import", headers=ALLOWED_ORIGIN
    ).json()

    cancela = api_only_client.post(
        f"/api/v1/ingestion-batches/{batch['id']}/cancel", headers=ALLOWED_ORIGIN
    )
    assert cancela.status_code == 200
    assert cancela.json()["status"] == "cancel_requested"

    job = api_only_client.post(f"/api/v1/jobs/{batch['job_id']}/cancel", headers=ALLOWED_ORIGIN)
    assert job.status_code == 200
    assert job.json()["cancel_requested"] is True


def test_cancelar_un_lote_que_no_ha_empezado_lo_cierra_el_worker(
    seeded_settings: Settings, material: Path
) -> None:
    """Regresión: un lote cancelado antes de arrancar se quedaba en `cancel_requested` para siempre.

    El trabajo se marcaba `cancel_requested` y `claim_next` solo reclamaba los `queued`, así que
    nadie lo ejecutaba nunca: el lote quedaba sin contadores y con el informe descuadrado. Ahora el
    worker reclama también los trabajos cancelados para cerrarlos en `cancelled`.
    """
    settings = Settings(
        data_dir=seeded_settings.data_dir,
        worker_enabled=True,
        worker_poll_seconds=0.1,
        _env_file=None,
    )
    with TestClient(create_app(settings)) as client:
        inventario = inventariar(client, material)
        batch = client.post(
            f"/api/v1/inventories/{inventario['batch']['id']}/confirm-import",
            headers=ALLOWED_ORIGIN,
        ).json()

        cancelado = client.post(
            f"/api/v1/ingestion-batches/{batch['id']}/cancel", headers=ALLOWED_ORIGIN
        )
        assert cancelado.json()["status"] == "cancel_requested"

        deadline = time.monotonic() + 20
        detalle = client.get(f"/api/v1/ingestion-batches/{batch['id']}").json()
        while detalle["batch"]["status"] != "cancelled" and time.monotonic() < deadline:
            time.sleep(0.2)
            detalle = client.get(f"/api/v1/ingestion-batches/{batch['id']}").json()

        assert detalle["batch"]["status"] == "cancelled"
        # El informe de un lote cancelado cuadra: las entradas que no se copiaron quedan canceladas.
        assert detalle["batch"]["counters"]["total"] == 2
        assert detalle["batch"]["counters"]["cancelled"] == 2
        assert detalle["report"]["balanced"] is True

        trabajo = client.get(f"/api/v1/jobs/{batch['job_id']}").json()
        assert trabajo["status"] == "cancelled"
        # Y el material del usuario sigue intacto.
        assert snapshot(material)


def test_reintentar_un_lote_en_cola_lo_deja_encolado(
    api_only_client: TestClient, material: Path
) -> None:
    inventario = inventariar(api_only_client, material)
    batch = api_only_client.post(
        f"/api/v1/inventories/{inventario['batch']['id']}/confirm-import", headers=ALLOWED_ORIGIN
    ).json()
    response = api_only_client.post(
        f"/api/v1/ingestion-batches/{batch['id']}/retry", headers=ALLOWED_ORIGIN
    )
    assert response.status_code == 200
    assert response.json()["status"] == "queued"


def test_el_ciclo_completo_lo_ejecuta_el_worker(seeded_settings: Settings, material: Path) -> None:
    """Con el worker en marcha, confirmar la importación termina en un lote copiado."""
    settings = Settings(
        data_dir=seeded_settings.data_dir,
        worker_enabled=True,
        worker_poll_seconds=0.1,
        _env_file=None,
    )
    app = create_app(settings)
    with TestClient(app) as client:
        inventario = inventariar(client, material)
        batch = client.post(
            f"/api/v1/inventories/{inventario['batch']['id']}/confirm-import",
            headers=ALLOWED_ORIGIN,
        ).json()

        finished = None
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            detalle = client.get(f"/api/v1/ingestion-batches/{batch['id']}").json()
            if detalle["batch"]["status"] in {"succeeded", "failed", "cancelled"}:
                finished = detalle
                break
            time.sleep(0.1)

        assert finished is not None, "el worker no terminó el lote a tiempo"
        assert finished["batch"]["status"] == "succeeded"
        assert finished["report"]["counters"]["copied"] == 2
        assert finished["report"]["balanced"] is True
        assert finished["report"]["artifacts_total"] == 1
        # El trabajo queda terminado y con progreso completo.
        job = client.get(f"/api/v1/jobs/{batch['job_id']}").json()
        assert job["status"] == JobStatus.SUCCEEDED.value
        assert job["progress"] == 1.0

        entradas = client.get(f"/api/v1/ingestion-batches/{batch['id']}/items").json()
        assert entradas["total"] == 2
        assert {entry["status"] for entry in entradas["entries"]} == {ItemStatus.HASHED.value}


def test_un_reinicio_recupera_el_trabajo_interrumpido(
    api_only_client: TestClient, material: Path, migrated_settings: Settings
) -> None:
    """Un lease vencido vuelve a la cola: ni se pierde el trabajo ni se duplica."""
    inventario = inventariar(api_only_client, material)
    batch = api_only_client.post(
        f"/api/v1/inventories/{inventario['batch']['id']}/confirm-import", headers=ALLOWED_ORIGIN
    ).json()

    engine = build_engine(migrated_settings.data_paths.database)
    try:
        repository = SqlAlchemyJobRepository(build_session_factory(engine))
        now = datetime.now(UTC)
        claimed = repository.claim_next(owner="worker-caido", now=now, lease_seconds=5)
        assert claimed is not None and claimed.id == batch["job_id"]
        repository.mark_running(claimed.id, owner="worker-caido", now=now)

        # El worker anterior murió: su lease caduca y el trabajo vuelve a la cola.
        with build_session_factory(engine)() as session:
            record = session.execute(
                select(JobRecord).where(JobRecord.id == claimed.id)
            ).scalar_one()
            record.lease_expires_at = now - timedelta(seconds=1)
            session.commit()

        assert repository.requeue_expired_leases(now=now) == 1
        recuperado = repository.get(claimed.id)
        assert recuperado is not None
        assert recuperado.status is JobStatus.QUEUED
        assert recuperado.attempts == 1
    finally:
        engine.dispose()


def test_listado_de_lotes_y_entradas_paginado(api_only_client: TestClient, material: Path) -> None:
    inventario = inventariar(api_only_client, material)
    batch_id = inventario["batch"]["id"]

    lotes = api_only_client.get("/api/v1/ingestion-batches").json()
    assert len(lotes) == 1
    assert lotes[0]["id"] == batch_id

    entradas = api_only_client.get(f"/api/v1/ingestion-batches/{batch_id}/items?limit=1").json()
    assert entradas["total"] == 3
    assert len(entradas["entries"]) == 1
    assert entradas["limit"] == 1

    incidencias = api_only_client.get(f"/api/v1/ingestion-batches/{batch_id}/issues").json()
    assert incidencias["total"] == 1
    assert incidencias["issues"][0]["code"] == "omitted_hidden"
    assert incidencias["issues"][0]["relative_path"] == ".oculto.txt"

    informe = api_only_client.get(f"/api/v1/ingestion-batches/{batch_id}/report").json()
    assert informe["kind"] == "inventory"
    assert informe["counters"]["inventoried"] == 2
    assert informe["balanced"] is True
