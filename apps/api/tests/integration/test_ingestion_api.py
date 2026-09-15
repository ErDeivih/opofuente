"""Pruebas de integración de la API de ingestión y trabajos (S02)."""

from __future__ import annotations

import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from opofuente.api.errors import PROBLEM_MEDIA_TYPE
from opofuente.config import Settings
from opofuente.domain.ingestion import ItemStatus
from opofuente.domain.jobs import JobStatus, JobType
from opofuente.infrastructure.db import build_engine, build_session_factory
from opofuente.infrastructure.db_models import JobRecord
from opofuente.infrastructure.job_repository import SqlAlchemyJobRepository
from opofuente.main import create_app
from opofuente_testing.jobs import failed_extraction, jobs_for_batch, run_one_job
from opofuente_testing.synthetic_documents import build_bomb_docx

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


def test_un_lote_recien_confirmado_declara_sus_pendientes(
    api_only_client: TestClient, material: Path
) -> None:
    """Regresión: entre la confirmación y el worker, el informe decía «0 de 0» y no cuadraba.

    Con el worker apagado no hay nadie que recalcule nada después, así que los contadores tienen que
    estar bien desde el momento en que se crean las entradas: `total = pending`.
    """
    inventario = inventariar(api_only_client, material)
    batch = api_only_client.post(
        f"/api/v1/inventories/{inventario['batch']['id']}/confirm-import", headers=ALLOWED_ORIGIN
    ).json()

    assert batch["status"] == "queued"
    counters = batch["counters"]
    assert counters["total"] == 2
    assert counters["pending"] == 2
    assert counters["copied"] == 0
    assert _suma_cuadra(counters)

    informe = api_only_client.get(f"/api/v1/ingestion-batches/{batch['id']}/report").json()
    assert informe["balanced"] is True
    assert informe["counters"]["pending"] == 2


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

        run_one_job(client)

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


def test_reintentar_un_lote_en_cola_devuelve_409(
    api_only_client: TestClient, material: Path
) -> None:
    """Reintentar solo vale para un lote parado: en cola o trabajando responde 409.

    Devolver entradas a `inventoried` mientras el worker sigue trabajando descuadraría los
    contadores y podría copiar dos veces lo mismo, así que la API lo rechaza con el 409 documentado.
    """
    inventario = inventariar(api_only_client, material)
    batch = api_only_client.post(
        f"/api/v1/inventories/{inventario['batch']['id']}/confirm-import", headers=ALLOWED_ORIGIN
    ).json()
    assert batch["status"] == "queued"

    response = api_only_client.post(
        f"/api/v1/ingestion-batches/{batch['id']}/retry", headers=ALLOWED_ORIGIN
    )

    assert response.status_code == 409
    assert response.headers["content-type"].startswith(PROBLEM_MEDIA_TYPE)
    body = response.json()
    assert body["code"] == "invalid_state"
    assert "failed" in body["detail"] and "cancelled" in body["detail"]
    assert body["correlation_id"]
    # Y nada ha cambiado: el lote sigue en cola con su trabajo.
    assert (
        api_only_client.get(f"/api/v1/ingestion-batches/{batch['id']}").json()["batch"]["status"]
        == "queued"
    )


def test_reintentar_un_lote_cancelado_cuadra_el_informe(
    migrated_settings: Settings, material: Path
) -> None:
    """Reintentar un lote cancelado: el informe cuadra **en el momento**, con las pendientes.

    Regresión: al reintentar, las entradas recuperadas volvían a `inventoried`, que no aparecía en
    ninguna parte del informe, así que la API devolvía `balanced: false` (total=3, copiada=1) aunque
    la documentación dijera que el informe cuadra. Ahora el informe declara `pending`.
    """
    settings = Settings(data_dir=migrated_settings.data_dir, worker_enabled=False, _env_file=None)
    with TestClient(create_app(settings)) as client:
        inventario = inventariar(client, material)
        batch = client.post(
            f"/api/v1/inventories/{inventario['batch']['id']}/confirm-import",
            headers=ALLOWED_ORIGIN,
        ).json()
        client.post(f"/api/v1/ingestion-batches/{batch['id']}/cancel", headers=ALLOWED_ORIGIN)
        run_one_job(client)  # el worker reclama el trabajo cancelado y cierra el lote

        cancelado = client.get(f"/api/v1/ingestion-batches/{batch['id']}").json()
        assert cancelado["batch"]["status"] == "cancelled"
        assert cancelado["report"]["balanced"] is True
        assert cancelado["batch"]["counters"]["pending"] == 0

        reintento = client.post(
            f"/api/v1/ingestion-batches/{batch['id']}/retry", headers=ALLOWED_ORIGIN
        )
        assert reintento.status_code == 200
        assert reintento.json()["status"] == "queued"

        # Lo importante: ya cuadra, y las pendientes están declaradas.
        en_curso = client.get(f"/api/v1/ingestion-batches/{batch['id']}").json()
        counters = en_curso["batch"]["counters"]
        assert counters["pending"] == 2
        assert counters["cancelled"] == 0
        assert en_curso["report"]["balanced"] is True
        assert _suma_cuadra(counters)

        run_one_job(client)  # la copia del reintento
        copiado = client.get(f"/api/v1/ingestion-batches/{batch['id']}").json()
        assert copiado["batch"]["counters"]["copied"] == 2
        assert copiado["batch"]["status"] == "queued", "queda la extracción"
        run_one_job(client)  # la extracción, que cierra el lote

        final = client.get(f"/api/v1/ingestion-batches/{batch['id']}").json()
        assert final["batch"]["status"] == "succeeded"
        assert final["batch"]["counters"]["copied"] == 2
        assert final["batch"]["counters"]["pending"] == 0
        assert final["report"]["balanced"] is True


def _suma_cuadra(counters: dict[str, int]) -> bool:
    """`total = copied + pending + failed + cancelled + source_changed`."""
    return counters["total"] == (
        counters["copied"]
        + counters["pending"]
        + counters["failed"]
        + counters["cancelled"]
        + counters["source_changed"]
    )


def _trabajos_de(migrated_settings: Settings, batch_id: str, job_type: JobType) -> list[Any]:
    """Trabajos de ese tipo encolados para el lote, leídos de la cola real."""
    engine = build_engine(migrated_settings.data_paths.database)
    try:
        cola = SqlAlchemyJobRepository(build_session_factory(engine))
        return jobs_for_batch(cola, batch_id, job_type)
    finally:
        engine.dispose()


def test_reintentar_tras_un_fallo_de_extraccion_no_vuelve_a_copiar(
    api_only_client: TestClient, migrated_settings: Settings, tmp_path: Path
) -> None:
    """Con el artefacto ya copiado, el reintento vuelve a **extraer**, no a copiar.

    Antes toda entrada fallida volvía a `inventoried` y se encolaba `ingest_batch`: el contenido ya
    estaba en el almacén, así que se copiaba otra vez (o, en un lote sin carpeta de origen, el
    reintento terminaba con «el lote no conserva la carpeta de origen»).

    El DOCX bomba falla en la extracción de verdad (el contenedor se rechaza por tamaño), no por
    manipular la base.
    """
    bomba = build_bomb_docx(tmp_path / "trampa.docx")
    batch = api_only_client.post(
        "/api/v1/ingestion-batches/files",
        files=[("files", ("trampa.docx", bomba.read_bytes(), "application/vnd.openxmlformats"))],
        headers=ALLOWED_ORIGIN,
    ).json()

    run_one_job(api_only_client)

    fallado = api_only_client.get(f"/api/v1/ingestion-batches/{batch['id']}").json()
    assert fallado["batch"]["status"] == "failed"
    assert fallado["batch"]["counters"]["failed"] == 1
    assert fallado["entries"][0]["status"] == ItemStatus.FAILED.value

    respuesta = api_only_client.post(
        f"/api/v1/ingestion-batches/{batch['id']}/retry", headers=ALLOWED_ORIGIN
    )

    assert respuesta.status_code == 200, respuesta.text
    # Este lote entró subido: nunca hubo trabajo de copia, y el reintento no lo inventa.
    assert _trabajos_de(migrated_settings, batch["id"], JobType.INGEST_BATCH) == []
    assert len(_trabajos_de(migrated_settings, batch["id"], JobType.EXTRACT_ARTIFACT)) == 2

    # Y el lote apunta al trabajo del reintento.
    en_curso = api_only_client.get(f"/api/v1/ingestion-batches/{batch['id']}").json()
    assert en_curso["batch"]["status"] == "queued"
    assert en_curso["batch"]["job_id"]

    # El worker lo ejecuta sin quejarse de la carpeta de origen (que no existe) y cierra el lote.
    run_one_job(api_only_client)
    final = api_only_client.get(f"/api/v1/ingestion-batches/{batch['id']}").json()
    assert final["batch"]["status"] == "failed", "sigue fallando, pero por la extracción"
    # El artefacto ya estaba copiado y se reutiliza: no se copia una segunda vez.
    assert final["report"]["artifacts_total"] == 1
    # La entrada sigue contando como `failed` (la ecuación del informe admite un solo término por
    # entrada), pero lo que falló fue la lectura, no la copia: el artefacto está en el almacén.
    assert final["batch"]["counters"]["failed"] == 1
    assert final["entries"][0]["status"] == ItemStatus.FAILED.value
    assert final["entries"][0]["detail"] == "extracción fallida"


def test_reintentar_un_lote_de_texto_pegado_funciona_sin_carpeta_de_origen(
    api_only_client: TestClient,
    migrated_settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Un lote que entró pegado no tiene carpeta de origen: el reintento no puede necesitarla."""
    batch = api_only_client.post(
        "/api/v1/ingestion-batches/paste",
        json={"text": "Material sintetico pegado para probar el reintento."},
        headers=ALLOWED_ORIGIN,
    ).json()

    app: Any = api_only_client.app
    extraccion = app.state.extraction_service
    registro = extraccion._registry
    original = registro.extract
    monkeypatch.setattr(registro, "extract", lambda *args, **kwargs: failed_extraction())

    run_one_job(api_only_client)
    fallado = api_only_client.get(f"/api/v1/ingestion-batches/{batch['id']}").json()
    assert fallado["batch"]["status"] == "failed"

    monkeypatch.setattr(registro, "extract", original)
    respuesta = api_only_client.post(
        f"/api/v1/ingestion-batches/{batch['id']}/retry", headers=ALLOWED_ORIGIN
    )

    assert respuesta.status_code == 200, (
        f"el reintento de un lote pegado no puede pedir carpeta de origen: {respuesta.text}"
    )
    assert _trabajos_de(migrated_settings, batch["id"], JobType.INGEST_BATCH) == []
    assert len(_trabajos_de(migrated_settings, batch["id"], JobType.EXTRACT_ARTIFACT)) == 2

    run_one_job(api_only_client)
    final = api_only_client.get(f"/api/v1/ingestion-batches/{batch['id']}").json()
    assert final["batch"]["status"] == "succeeded"
    assert final["entries"][0]["status"] == ItemStatus.EXTRACTED.value


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

        # El pipeline completo: la importación copia y, al terminar, se encola la extracción. Se
        # espera a que el lote esté cerrado **y** sin entradas pendientes de extraer.
        finished = None
        deadline = time.monotonic() + 60
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

        entradas = client.get(f"/api/v1/ingestion-batches/{batch['id']}/items").json()
        assert entradas["total"] == 2
        # S03: lo copiado se extrae, así que las entradas ya no se quedan en `hashed`.
        assert {entry["status"] for entry in entradas["entries"]} == {ItemStatus.EXTRACTED.value}
        assert all(
            entry["detail"] and "native_text" in entry["detail"] for entry in entradas["entries"]
        )


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
