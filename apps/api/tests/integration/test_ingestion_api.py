"""Pruebas de integración de la API de ingestión y trabajos (S02)."""

from __future__ import annotations

import asyncio
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from opofuente.api.errors import PROBLEM_MEDIA_TYPE
from opofuente.config import Settings
from opofuente.domain.ingestion import ItemStatus
from opofuente.domain.jobs import JobStatus, JobType
from opofuente.infrastructure.clock import SystemClock
from opofuente.infrastructure.db import build_engine, build_session_factory
from opofuente.infrastructure.db_models import JobRecord
from opofuente.infrastructure.job_repository import SqlAlchemyJobRepository
from opofuente.main import create_app
from opofuente.workers.job_worker import JobWorker

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


def test_un_lote_cancelado_antes_de_arrancar_lo_cierra_el_worker(
    migrated_settings: Settings, material: Path
) -> None:
    """Regresión: un lote cancelado antes de arrancar se quedaba en `cancel_requested` para siempre.

    El trabajo se marcaba `cancel_requested` y `claim_next` solo reclamaba los `queued`, así que
    nadie lo ejecutaba nunca: el lote quedaba sin contadores, con el informe descuadrado y el
    trabajo esperando para siempre.

    La prueba es determinista a propósito: el worker de la aplicación **está apagado** cuando se
    pide la cancelación, así que el estado no depende de quién llegue antes; después se arranca un
    worker de verdad (el mismo repositorio y los mismos manejadores de la aplicación) y se comprueba
    que reclama el trabajo cancelado y cierra el lote.
    """
    settings = Settings(
        data_dir=migrated_settings.data_dir,
        worker_enabled=False,
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
        # Nadie ha ejecutado nada todavía: el lote sigue exactamente ahí.
        assert client.get(f"/api/v1/jobs/{batch['job_id']}").json()["status"] == "cancel_requested"

        _run_one_job(client)

        detalle = client.get(f"/api/v1/ingestion-batches/{batch['id']}").json()
        assert detalle["batch"]["status"] == "cancelled"
        counters = detalle["batch"]["counters"]
        # El material tiene dos ficheros inventariados y uno oculto (que no entra en el lote).
        assert counters["total"] == 2
        assert counters["cancelled"] == 2
        assert counters["copied"] == 0
        assert detalle["report"]["balanced"] is True

        trabajo = client.get(f"/api/v1/jobs/{batch['job_id']}").json()
        assert trabajo["status"] == "cancelled"
        # Y el material del usuario sigue intacto.
        assert snapshot(material)


def _run_one_job(client: TestClient, *, attempts: int = 1) -> None:
    """Ejecuta el worker real de la aplicación sobre los servicios de la app de prueba."""
    service = client.app.state.ingestion_service
    worker = JobWorker(
        queue=service.jobs,
        handlers={JobType.INGEST_BATCH: service.run_import_job},
        on_failed={JobType.INGEST_BATCH: service.on_job_failed},
        clock=SystemClock(),
        lease_seconds=60,
        poll_seconds=0.05,
        owner="worker-de-prueba",
    )
    for _ in range(attempts):
        asyncio.run(worker.run_once())


def test_un_lote_cancelado_termina_siempre_en_un_estado_cerrado(
    seeded_settings: Settings, tmp_path: Path
) -> None:
    """Invariante de cara al usuario: de `cancel_requested` se sale, tarde lo que tarde la copia.

    Con el worker en marcha, quién gana la carrera (la cancelación o la copia) depende de la
    máquina: lo que **no** puede pasar es que el lote se quede en `cancel_requested` sin contadores.
    Se acepta cualquiera de los dos finales coherentes y se comprueba que el informe cuadra en
    ambos.
    """
    lento = tmp_path / "material-lento"
    lento.mkdir()
    for index in range(400):
        (lento / f"tema-{index:04d}.txt").write_bytes(b"x" * 65536)

    settings = Settings(
        data_dir=seeded_settings.data_dir,
        worker_enabled=True,
        worker_poll_seconds=0.1,
        _env_file=None,
    )
    with TestClient(create_app(settings)) as client:
        inventario = inventariar(client, lento)
        batch = client.post(
            f"/api/v1/inventories/{inventario['batch']['id']}/confirm-import",
            headers=ALLOWED_ORIGIN,
        ).json()
        client.post(f"/api/v1/ingestion-batches/{batch['id']}/cancel", headers=ALLOWED_ORIGIN)

        deadline = time.monotonic() + 60
        detalle = client.get(f"/api/v1/ingestion-batches/{batch['id']}").json()
        while (
            detalle["batch"]["status"] in {"queued", "running", "cancel_requested"}
            and time.monotonic() < deadline
        ):
            time.sleep(0.2)
            detalle = client.get(f"/api/v1/ingestion-batches/{batch['id']}").json()

        estado = detalle["batch"]["status"]
        counters = detalle["batch"]["counters"]
        assert estado in {"cancelled", "succeeded"}, estado
        assert detalle["report"]["balanced"] is True
        assert counters["total"] == 400
        assert counters["copied"] + counters["cancelled"] == 400
        if estado == "cancelled":
            assert counters["cancelled"] > 0
        # El trabajo acompaña al lote: nunca estados cruzados.
        trabajo = client.get(f"/api/v1/jobs/{batch['job_id']}").json()
        assert trabajo["status"] == estado
        assert len(list(lento.iterdir())) == 400


def test_una_cancelacion_que_llega_tarde_no_reescribe_el_lote_terminado(
    seeded_settings: Settings, material: Path
) -> None:
    """Si el lote ya había terminado, gana el trabajo hecho: ni `cancelled` ni estados cruzados.

    El trabajo y el lote acaban en el mismo estado (`succeeded`): el trabajo no puede quedar
    `cancelled` con un lote ya copiado, y la petición de cancelación queda registrada en el trabajo
    sin mentir sobre lo que pasó.
    """
    settings = Settings(
        data_dir=seeded_settings.data_dir,
        worker_enabled=True,
        worker_poll_seconds=0.06,
        _env_file=None,
    )
    with TestClient(create_app(settings)) as client:
        inventario = inventariar(client, material)
        batch = client.post(
            f"/api/v1/inventories/{inventario['batch']['id']}/confirm-import",
            headers=ALLOWED_ORIGIN,
        ).json()

        # Se espera a que el lote termine de verdad y solo entonces se pide cancelar.
        deadline = time.monotonic() + 30
        detalle = client.get(f"/api/v1/ingestion-batches/{batch['id']}").json()
        while (
            detalle["batch"]["status"] not in {"succeeded", "failed"}
            and time.monotonic() < deadline
        ):
            time.sleep(0.1)
            detalle = client.get(f"/api/v1/ingestion-batches/{batch['id']}").json()
        assert detalle["batch"]["status"] == "succeeded"

        respuesta = client.post(
            f"/api/v1/ingestion-batches/{batch['id']}/cancel", headers=ALLOWED_ORIGIN
        )
        assert respuesta.status_code == 200

        detalle = client.get(f"/api/v1/ingestion-batches/{batch['id']}").json()
        assert detalle["batch"]["status"] == "succeeded"
        trabajo = client.get(f"/api/v1/jobs/{batch['job_id']}").json()
        assert trabajo["status"] == "succeeded"


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

        recuperados = repository.requeue_expired_leases(now=now)
        assert [job.id for job in recuperados] == [claimed.id]
        assert recuperados[0].status is JobStatus.QUEUED
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
