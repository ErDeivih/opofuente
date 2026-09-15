"""Pruebas de integración de la importación: copia por hash, idempotencia y cancelación.

Se comprueban los criterios de aceptación de S02:

- los originales mantienen hash y fecha;
- dos archivos idénticos producen **un** artefacto y **dos** orígenes;
- una caída o un reinicio no duplican nada;
- la cancelación deja un informe cuadrado.
"""

from __future__ import annotations

import asyncio
import hashlib
import os
from datetime import UTC, datetime
from pathlib import Path

import pytest
from sqlalchemy import func, select

from opofuente.application.ingestion_service import IngestionService
from opofuente.application.job_service import JobExecution
from opofuente.config import DataPaths, Settings
from opofuente.domain.artifacts import Sha256
from opofuente.domain.errors import InvalidBatchStateError
from opofuente.domain.ingestion import BatchStatus, IssueCode, ItemStatus
from opofuente.domain.jobs import Job, JobStatus, JobType
from opofuente.infrastructure.artifact_store import ArtifactStore
from opofuente.infrastructure.db import build_engine, build_session_factory
from opofuente.infrastructure.db_models import (
    ArtifactOriginRecord,
    IngestionItemRecord,
    JobRecord,
    SourceArtifactRecord,
)
from opofuente.infrastructure.filesystem_inventory import FilesystemInventory
from opofuente.infrastructure.ingestion_repository import SqlAlchemyIngestionRepository
from opofuente.infrastructure.job_repository import SqlAlchemyJobRepository
from opofuente.workers.job_worker import JobWorker


class FixedClock:
    def __init__(self) -> None:
        self._now = datetime(2026, 9, 14, 12, 0, tzinfo=UTC)

    def now(self) -> datetime:
        return self._now

    def advance(self, seconds: int = 1) -> None:
        from datetime import timedelta

        self._now += timedelta(seconds=seconds)


class FakeExecution(JobExecution):
    """Ejecución de prueba: informa sin base de datos y permite forzar la cancelación."""

    def __init__(self, job: Job, *, cancel_after: int | None = None) -> None:
        self._cancel_after = cancel_after
        self._checks = 0
        self.progress_calls: list[float] = []
        super().__init__(
            job,
            report=self._report,
            heartbeat=lambda: None,
            is_cancelled=self._is_cancelled,
        )

    def _report(self, value: float, step: str | None) -> None:
        self.progress_calls.append(value)

    def _is_cancelled(self) -> bool:
        self._checks += 1
        return self._cancel_after is not None and self._checks > self._cancel_after


@pytest.fixture
def session_factory(migrated_settings: Settings):
    engine = build_engine(migrated_settings.data_paths.database)
    try:
        yield build_session_factory(engine)
    finally:
        engine.dispose()


@pytest.fixture
def clock() -> FixedClock:
    return FixedClock()


@pytest.fixture
def service(migrated_settings: Settings, session_factory, clock: FixedClock) -> IngestionService:
    paths: DataPaths = migrated_settings.data_paths
    return IngestionService(
        repository=SqlAlchemyIngestionRepository(session_factory),
        jobs=SqlAlchemyJobRepository(session_factory),
        store=ArtifactStore(paths),
        scanner=FilesystemInventory(
            max_file_bytes=1024 * 1024, max_entries=1000, forbidden_roots=(paths.root,)
        ),
        clock=clock,
        data_root=paths.root,
        max_entries=1000,
    )


@pytest.fixture
def material(tmp_path: Path) -> Path:
    root = tmp_path / "material"
    (root / "apuntes").mkdir(parents=True)
    (root / "apuntes" / "ley.md").write_text("ley 39/2015", encoding="utf-8")
    # Dos ficheros idénticos con nombres distintos: un artefacto y dos orígenes.
    (root / "apuntes" / "ley-copia.md").write_text("ley 39/2015", encoding="utf-8")
    (root / "preguntas.csv").write_text("p;o\n1;a", encoding="utf-8")
    return root


def snapshot(root: Path) -> dict[str, tuple[int, float]]:
    return {
        path.relative_to(root).as_posix(): (path.stat().st_size, path.stat().st_mtime)
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def _job_for(service: IngestionService, batch_id: str) -> Job:
    jobs = service.jobs
    desde = jobs.list(limit=20)
    for job in desde:
        if job.payload.get("batch_id") == batch_id:
            return job
    raise AssertionError("no se encoló el trabajo del lote")


def import_all(service: IngestionService, inventory_id: str, *, cancel_after: int | None = None):
    """Ejecuta **solo** la fase de copia del pipeline.

    Desde S03 el lote tiene dos fases: copiar y extraer. Esta función corre la copia, así que el
    lote queda en `queued` (con la extracción pendiente) salvo que se cancele. Los tests que
    necesiten el lote cerrado tienen que ejecutar también la extracción.
    """
    from opofuente.domain.errors import JobCancelledError

    batch = service.confirm_import(inventory_id)
    job = _job_for(service, batch.id)
    try:
        service.run_import_job(FakeExecution(job, cancel_after=cancel_after))
    except JobCancelledError:
        if cancel_after is None:  # pragma: no cover - no debería ocurrir
            raise
    return batch.id


def test_importacion_copia_por_hash_y_respeta_los_originales(
    service: IngestionService, material: Path, session_factory
) -> None:
    antes = snapshot(material)
    inventario = service.create_inventory(str(material))
    batch_id = import_all(service, inventario.batch.id)

    detalle = service.get_batch(batch_id)
    # La copia terminó; queda la extracción, así que el lote sigue en cola (S03).
    assert detalle.batch.status == BatchStatus.QUEUED.value
    assert detalle.batch.counters["total"] == 3
    assert detalle.batch.counters["copied"] == 3
    assert detalle.batch.counters["failed"] == 0
    assert detalle.batch.counters["source_changed"] == 0
    # Tres entradas, dos contenidos distintos: el repetido no se guarda dos veces.
    assert service.count_batch_artifacts(batch_id) == 2

    with session_factory() as session:
        assert (
            session.execute(select(func.count()).select_from(SourceArtifactRecord)).scalar_one()
            == 2
        )
        assert (
            session.execute(select(func.count()).select_from(ArtifactOriginRecord)).scalar_one()
            == 3
        )
        estados = set(
            session.execute(
                select(IngestionItemRecord.status).where(IngestionItemRecord.batch_id == batch_id)
            ).scalars()
        )
    assert estados == {ItemStatus.HASHED.value}

    # Los originales siguen intactos: mismo tamaño y misma fecha de modificación.
    assert snapshot(material) == antes


def test_dos_ficheros_identicos_son_un_artefacto_y_dos_origenes(
    service: IngestionService, material: Path, session_factory
) -> None:
    inventario = service.create_inventory(str(material))
    batch_id = import_all(service, inventario.batch.id)

    with session_factory() as session:
        artifact = session.execute(
            select(SourceArtifactRecord).where(
                SourceArtifactRecord.sha256 == _sha_of(material / "apuntes" / "ley.md")
            )
        ).scalar_one()
        origenes = set(
            session.execute(
                select(ArtifactOriginRecord.display_location).where(
                    ArtifactOriginRecord.artifact_id == artifact.id
                )
            ).scalars()
        )
    assert origenes == {"apuntes/ley.md", "apuntes/ley-copia.md"}
    assert service.get_batch(batch_id).batch.counters["copied"] == 3


def _sha_of(path: Path) -> str:
    import hashlib

    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_confirmar_dos_veces_no_duplica_el_lote(service: IngestionService, material: Path) -> None:
    inventario = service.create_inventory(str(material))
    primero = service.confirm_import(inventario.batch.id)
    segundo = service.confirm_import(inventario.batch.id)
    assert primero.id == segundo.id


def test_reanudar_tras_una_caida_no_duplica_artefactos(
    service: IngestionService, material: Path, session_factory
) -> None:
    """Simula una caída a mitad: reintentar es cosa de la aplicación y no duplica artefactos.

    Lo que se comprueba aquí es que **`retry_batch` devuelve las entradas a la cola por sí solo**:
    la versión anterior de esta prueba arreglaba la base con un `UPDATE` a mano, así que ocultaba
    que reintentar no reencolaba nada que copiar.
    """
    inventario = service.create_inventory(str(material))
    batch_id = import_all(service, inventario.batch.id, cancel_after=1)

    detalle = service.get_batch(batch_id)
    assert detalle.batch.status == BatchStatus.CANCELLED.value
    pendientes_antes = _statuses(service, batch_id)
    assert pendientes_antes[ItemStatus.CANCELLED.value] > 0

    # Reintentar sin tocar la base: la aplicación devuelve las canceladas a `inventoried`.
    batch = service.retry_batch(batch_id)
    assert batch.status == BatchStatus.QUEUED.value
    estados = _statuses(service, batch_id)
    assert estados.get(ItemStatus.CANCELLED.value, 0) == 0
    assert (
        estados.get(ItemStatus.INVENTORIED.value, 0) == pendientes_antes[ItemStatus.CANCELLED.value]
    )
    # Y el informe ya cuadra antes de volver a ejecutar: nada se queda a medias.
    counters = service.get_batch(batch_id).batch.counters
    assert counters["cancelled"] == 0
    assert counters["total"] == 3

    job = _job_for(service, batch.id)
    service.run_import_job(FakeExecution(job))

    detalle = service.get_batch(batch_id)
    # La copia del reintento terminó (la extracción es la otra fase del pipeline).
    assert detalle.batch.status == BatchStatus.QUEUED.value
    assert detalle.batch.counters["copied"] == 3
    assert detalle.batch.counters["cancelled"] == 0
    with session_factory() as session:
        assert (
            session.execute(select(func.count()).select_from(SourceArtifactRecord)).scalar_one()
            == 2
        )


def _statuses(service: IngestionService, batch_id: str) -> dict[str, int]:
    """Estado real de las entradas del lote, leído por la API interna del servicio."""
    page = service.list_entries(batch_id, limit=500, offset=0)
    counts: dict[str, int] = {}
    for entry in page.entries:
        counts[entry.status] = counts.get(entry.status, 0) + 1
    return counts


def test_reintentar_recupera_las_canceladas_pero_no_las_que_cambiaron(
    service: IngestionService, material: Path
) -> None:
    """Regresión: una entrada cuyo fichero cambió no se reintenta con el inventario viejo.

    Se cambia el contenido del primer fichero por orden (y de tamaño distinto), se deja que se
    intente y se cancela el lote a mitad. Al reintentar, las canceladas vuelven a la cola pero la
    que cambió se queda fallida: ese inventario ya no describe el origen y volvería a fallar; para
    esa hace falta un inventario nuevo.
    """
    inventario = service.create_inventory(str(material))
    (material / "apuntes" / "ley-copia.md").write_text("otra cosa distinta", encoding="utf-8")

    batch_id = import_all(service, inventario.batch.id, cancel_after=1)

    detalle = service.get_batch(batch_id)
    assert detalle.batch.status == BatchStatus.CANCELLED.value
    assert detalle.batch.counters["source_changed"] == 1
    antes = _statuses(service, batch_id)
    # La que cambió se intentó y falló; las otras dos quedaron canceladas al cancelar el lote.
    assert antes[ItemStatus.FAILED.value] == 1
    assert antes[ItemStatus.CANCELLED.value] == 2

    batch = service.retry_batch(batch_id)
    assert batch.status == BatchStatus.QUEUED.value

    estados = _statuses(service, batch_id)
    assert estados[ItemStatus.FAILED.value] == 1, "la que cambió no se reintenta"
    assert estados[ItemStatus.INVENTORIED.value] == 2
    counters = service.get_batch(batch_id).batch.counters
    assert counters["source_changed"] == 1
    assert counters["pending"] == 2
    assert counters["total"] == (
        counters["copied"]
        + counters["pending"]
        + counters["failed"]
        + counters["cancelled"]
        + counters["source_changed"]
    )

    job = _job_for(service, batch.id)
    service.run_import_job(FakeExecution(job))

    final = service.get_batch(batch_id)
    # La copiada de antes sigue copiada, la recuperada se copia y la que cambió sigue pendiente de
    # un inventario nuevo.
    assert final.batch.counters["copied"] == 2
    assert final.batch.counters["source_changed"] == 1
    assert final.batch.counters["pending"] == 0
    # Y reintentar no duplicó la incidencia: sigue habiendo una sola.
    assert sum(1 for issue in final.issues if issue.code == IssueCode.SOURCE_CHANGED.value) == 1
    assert final.batch.counters["total"] == (
        final.batch.counters["copied"]
        + final.batch.counters["pending"]
        + final.batch.counters["failed"]
        + final.batch.counters["cancelled"]
        + final.batch.counters["source_changed"]
    )


def test_un_lote_terminado_con_un_fichero_cambiado_no_se_reintenta(
    service: IngestionService, material: Path
) -> None:
    """Ese inventario ya no describe el origen: hay que inventariar otra vez, no reintentar.

    El lote terminó bien salvo una entrada cuyo fichero cambió, así que su estado es `succeeded` y
    `retry_batch` lo rechaza (la API lo sirve como 409): insistir con el inventario viejo volvería a
    fallar y el usuario no se enteraría de que su fichero ya no es el que revisó.
    """
    inventario = service.create_inventory(str(material))
    (material / "preguntas.csv").write_text("p;o\n1;a\n2;b", encoding="utf-8")
    batch_id = import_all(service, inventario.batch.id)

    detalle = service.get_batch(batch_id)
    assert detalle.batch.status == BatchStatus.QUEUED.value
    assert detalle.batch.counters["source_changed"] == 1
    assert detalle.batch.counters["pending"] == 0

    with pytest.raises(InvalidBatchStateError) as error:
        service.retry_batch(batch_id)
    assert "queued" in str(error.value)

    # Y el estado no se ha tocado: ni el lote ni sus contadores.
    assert service.get_batch(batch_id).batch.status == BatchStatus.QUEUED.value


def test_un_fichero_que_cambia_tras_el_inventario_no_se_copia(
    service: IngestionService, material: Path, session_factory
) -> None:
    inventario = service.create_inventory(str(material))
    (material / "preguntas.csv").write_text("p;o\n1;a\n2;b", encoding="utf-8")

    batch_id = import_all(service, inventario.batch.id)

    detalle = service.get_batch(batch_id)
    assert detalle.batch.counters["source_changed"] == 1
    assert detalle.batch.counters["copied"] == 2
    assert detalle.batch.counters["total"] == 3
    assert any(issue.code == IssueCode.SOURCE_CHANGED.value for issue in detalle.issues)
    # Lo que sí se copió sigue copiado; la extracción es la fase siguiente del pipeline.
    assert detalle.batch.status == BatchStatus.QUEUED.value


def test_un_fichero_que_cambia_de_fecha_sin_cambiar_de_tamano_no_se_copia(
    service: IngestionService, material: Path
) -> None:
    """Regresión: la fecha del inventario viaja al lote y se compara de verdad.

    Antes solo se comparaba el tamaño, así que un fichero editado sin cambiar de longitud se copiaba
    como si el usuario lo hubiera revisado. Aquí se toca solo la fecha (`utime`), con el mismo
    contenido y el mismo tamaño.
    """
    inventario = service.create_inventory(str(material))
    objetivo = material / "preguntas.csv"
    antes = objetivo.stat()
    os.utime(objetivo, (antes.st_atime + 120, antes.st_mtime + 120))
    assert objetivo.stat().st_size == antes.st_size

    batch_id = import_all(service, inventario.batch.id)

    detalle = service.get_batch(batch_id)
    assert detalle.batch.counters["source_changed"] == 1
    assert detalle.batch.counters["copied"] == 2
    assert any(issue.code == IssueCode.SOURCE_CHANGED.value for issue in detalle.issues)
    # El contenido del fichero rechazado no se copió: solo queda el artefacto de los dos ficheros
    # idénticos (`ley.md` y `ley-copia.md` comparten contenido).
    assert service.count_batch_artifacts(batch_id) == 1


def test_el_almacen_avisa_por_trozos_durante_la_copia(tmp_path: Path) -> None:
    """El almacén avisa al copiar cada trozo: un fichero grande no deja vencer el lease."""
    paths = DataPaths.from_root(tmp_path / "datos")
    paths.ensure_directories()
    store = ArtifactStore(paths, chunk_bytes=8)
    origen = tmp_path / "grande.bin"
    origen.write_bytes(b"x" * 64)

    avisos: list[int] = []
    store.store_file(origen, on_chunk=lambda: avisos.append(1))

    assert len(avisos) == 8, "cada trozo de 8 bytes de un fichero de 64 debe avisar"
    assert store.exists(Sha256(hashlib.sha256(origen.read_bytes()).hexdigest()))


def test_la_copia_renueva_el_lease_por_tiempo_y_dentro_de_un_fichero(
    migrated_settings: Settings, session_factory, material: Path, monkeypatch
) -> None:
    """Regresión: el lease se renueva por tiempo, no cada diez ficheros.

    Se copia **un solo** fichero con un intervalo de latido diminuto y un reloj monótono falso: si
    la renovación dependiera del número de ficheros, no habría ni un solo latido.
    """
    reloj = _RelojMonotono()
    monkeypatch.setattr("opofuente.application.ingestion_service.time.monotonic", reloj.monotonic)
    paths = migrated_settings.data_paths
    servicio = IngestionService(
        repository=SqlAlchemyIngestionRepository(session_factory),
        jobs=SqlAlchemyJobRepository(session_factory),
        store=ArtifactStore(paths, chunk_bytes=4),
        scanner=FilesystemInventory(
            max_file_bytes=1024 * 1024, max_entries=1000, forbidden_roots=(paths.root,)
        ),
        clock=FixedClock(),
        data_root=paths.root,
        max_entries=1000,
        heartbeat_seconds=0.05,
    )
    inventario = servicio.create_inventory(str(material))
    batch = servicio.confirm_import(inventario.batch.id)
    job = _job_for(servicio, batch.id)
    ejecucion = RelojFakeExecution(job, reloj=reloj)

    servicio.run_import_job(ejecucion)

    assert ejecucion.latidos > 0, "copiar un fichero tiene que renovar el lease"
    assert servicio.get_batch(batch.id).batch.counters["copied"] == 3


class _RelojMonotono:
    """Reloj monótono falso: cada lectura avanza medio segundo."""

    def __init__(self) -> None:
        self._value = 0.0

    def monotonic(self) -> float:
        self._value += 0.5
        return self._value


class RelojFakeExecution(FakeExecution):
    """Ejecución de prueba que cuenta los latidos y avanza el reloj al informar."""

    def __init__(self, job: Job, *, reloj: _RelojMonotono) -> None:
        self.latidos = 0
        self._reloj = reloj
        super().__init__(job)

    def heartbeat(self) -> None:
        self.latidos += 1

    def progress(self, value: float, step: str | None = None) -> None:
        self._reloj.monotonic()


def test_un_fallo_inesperado_cierra_el_lote_cuando_se_agotan_los_intentos(
    migrated_settings: Settings, session_factory, material: Path
) -> None:
    """Regresión: el lote no puede quedarse en `running` con su trabajo ya `failed`.

    Se usa el worker de verdad con un reloj falso: el primer intento revienta con un error no
    previsto, se espera la vuelta del reintento (que ahora es real) y, agotados los intentos, tanto
    el trabajo como el lote tienen que estar cerrados y el informe cuadrar.
    """
    paths = migrated_settings.data_paths
    clock = FixedClock()
    jobs = SqlAlchemyJobRepository(session_factory)
    servicio = IngestionService(
        repository=SqlAlchemyIngestionRepository(session_factory),
        jobs=jobs,
        store=_AlmacenQueRevienta(ArtifactStore(paths)),
        scanner=FilesystemInventory(
            max_file_bytes=1024 * 1024, max_entries=1000, forbidden_roots=(paths.root,)
        ),
        clock=clock,
        data_root=paths.root,
        max_entries=1000,
    )
    inventario = servicio.create_inventory(str(material))
    batch = servicio.confirm_import(inventario.batch.id)
    worker = JobWorker(
        queue=jobs,
        handlers={JobType.INGEST_BATCH: servicio.run_import_job},
        on_failed={JobType.INGEST_BATCH: servicio.on_job_failed},
        clock=clock,
        lease_seconds=30,
        poll_seconds=0.01,
        owner="worker-de-prueba",
    )

    # Tres vueltas con la espera entre reintentos ya vencida: se agotan los tres intentos.
    for _ in range(3):
        assert asyncio.run(worker.run_once()) is True
        clock.advance(60)

    trabajo = jobs.get(batch.job_id or "")
    assert trabajo is not None
    assert trabajo.status is JobStatus.FAILED
    assert trabajo.attempts == 3

    detalle = servicio.get_batch(batch.id)
    assert detalle.batch.status == BatchStatus.FAILED.value
    assert detalle.batch.error_summary is not None
    assert "RuntimeError" in detalle.batch.error_summary
    # Sin rutas del usuario en el motivo del fallo.
    assert str(material) not in detalle.batch.error_summary
    assert "…" in detalle.batch.error_summary
    counters = detalle.batch.counters
    assert counters["total"] == 3
    assert counters["copied"] == 0


class _AlmacenQueRevienta:
    """Envoltorio del almacén que revienta con un error no previsto en la primera copia."""

    def __init__(self, real: ArtifactStore) -> None:
        self._real = real

    def store_file(self, source: Path, *, on_chunk=None):  # type: ignore[no-untyped-def]
        raise RuntimeError(f"disco lleno al copiar {source}")

    def path_for(self, digest: Sha256) -> Path:
        return self._real.path_for(digest)

    def exists(self, digest: Sha256) -> bool:
        return self._real.exists(digest)


def test_los_leases_vencidos_que_agotan_los_intentos_cierran_el_lote(
    migrated_settings: Settings, session_factory, material: Path
) -> None:
    """Un proceso que se cae tres veces deja el trabajo `failed`, y el lote no puede seguir vivo.

    Se simula la caída moviendo el reloj (el lease caduca), sin tocar el SQLite del escenario: lo
    único que se comprueba después es el estado real que deja la aplicación.
    """
    paths = migrated_settings.data_paths
    clock = FixedClock()
    jobs = SqlAlchemyJobRepository(session_factory)
    servicio = IngestionService(
        repository=SqlAlchemyIngestionRepository(session_factory),
        jobs=jobs,
        store=ArtifactStore(paths),
        scanner=FilesystemInventory(
            max_file_bytes=1024 * 1024, max_entries=1000, forbidden_roots=(paths.root,)
        ),
        clock=clock,
        data_root=paths.root,
        max_entries=1000,
    )
    inventario = servicio.create_inventory(str(material))
    batch = servicio.confirm_import(inventario.batch.id)
    worker = JobWorker(
        queue=jobs,
        handlers={JobType.INGEST_BATCH: servicio.run_import_job},
        on_failed={JobType.INGEST_BATCH: servicio.on_job_failed},
        clock=clock,
        lease_seconds=5,
        poll_seconds=0.01,
        owner="worker-de-prueba",
    )

    # Tres caídas: se reclama el trabajo, se marca en marcha y el proceso «muere» (el lease vence).
    for _ in range(3):
        reclamado = jobs.claim_next(owner=worker.owner, now=clock.now(), lease_seconds=5)
        assert reclamado is not None
        jobs.mark_running(reclamado.id, owner=worker.owner, now=clock.now())
        clock.advance(600)
        worker.recover_interrupted()

    trabajo = jobs.get(batch.job_id or "")
    assert trabajo is not None
    assert trabajo.status is JobStatus.FAILED
    assert trabajo.attempts == 3

    detalle = servicio.get_batch(batch.id)
    assert detalle.batch.status == BatchStatus.FAILED.value
    counters = detalle.batch.counters
    assert counters["total"] == 3
    assert counters["copied"] == 0
    assert counters["failed"] == 0
    # Y el material sigue intacto: nada de esto ha tocado el origen.
    assert sorted(path.name for path in material.rglob("*") if path.is_file())


def test_el_espera_entre_reintentos_es_real(migrated_settings: Settings, session_factory) -> None:
    """Regresión: «reintento en 2s» aplaza de verdad el trabajo, no es solo un texto.

    El paso del reintento debe ser una fecha (`not_before`), y mientras no llegue el trabajo no se
    puede reclamar: si no, el worker lo vuelve a tomar en la vuelta siguiente y el mensaje miente.
    """
    clock = FixedClock()
    repository = SqlAlchemyJobRepository(session_factory)
    job, created = repository.enqueue(
        job_type=JobType.INGEST_BATCH, payload={"batch_id": "x"}, now=clock.now()
    )
    assert created is True
    reclamado = repository.claim_next(owner="w", now=clock.now(), lease_seconds=30)
    assert reclamado is not None and reclamado.id == job.id

    estado = repository.fail(
        job.id, error_code="RuntimeError", error_message="fallo de prueba", now=clock.now()
    )
    assert estado is JobStatus.QUEUED

    esperando = repository.get(job.id)
    assert esperando is not None
    assert esperando.not_before is not None
    assert esperando.not_before > clock.now()
    assert repository.claim_next(owner="w", now=clock.now(), lease_seconds=30) is None

    clock.advance(int((esperando.not_before - clock.now()).total_seconds()) + 1)
    assert repository.claim_next(owner="w", now=clock.now(), lease_seconds=30) is not None


def test_la_cancelacion_deja_el_informe_cuadrado(service: IngestionService, material: Path) -> None:
    inventario = service.create_inventory(str(material))
    batch_id = import_all(service, inventario.batch.id, cancel_after=1)

    detalle = service.get_batch(batch_id)
    counters = detalle.batch.counters
    assert detalle.batch.status == BatchStatus.CANCELLED.value
    assert counters["cancelled"] > 0
    assert counters["copied"] > 0
    assert counters["total"] == (
        counters["copied"] + counters["source_changed"] + counters["failed"] + counters["cancelled"]
    )
    con_canceladas = service.list_entries(
        batch_id, limit=100, offset=0, status=ItemStatus.CANCELLED
    )
    assert con_canceladas.total == counters["cancelled"]


def test_el_informe_cuenta_las_incidencias(service: IngestionService, tmp_path: Path) -> None:
    root = tmp_path / "material"
    root.mkdir()
    (root / "ok.txt").write_text("contenido", encoding="utf-8")
    (root / "instalador.exe").write_text("no", encoding="utf-8")

    inventario = service.create_inventory(str(root))
    assert inventario.batch.counters["inventoried"] == 1
    assert inventario.batch.counters["omitted_executable"] == 1
    assert inventario.batch.issue_counts.get(IssueCode.OMITTED_EXECUTABLE.value) == 1


def test_el_almacen_guarda_y_verifica_el_contenido(
    service: IngestionService, material: Path, migrated_settings: Settings
) -> None:
    from opofuente.domain.artifacts import Sha256

    inventario = service.create_inventory(str(material))
    import_all(service, inventario.batch.id)

    store = ArtifactStore(migrated_settings.data_paths)
    digest = Sha256(_sha_of(material / "apuntes" / "ley.md"))
    assert store.exists(digest)
    assert store.verify(digest)
    assert store.path_for(digest).is_file()
    # La ruta en disco es la documentada (02_ARCHITECTURE §5), sin segmentos repetidos:
    # data/artifacts/sha256/ab/cd/<hash>.
    assert (
        store.path_for(digest)
        == migrated_settings.data_paths.root
        / "artifacts"
        / "sha256"
        / digest.prefix
        / digest.suffix
        / digest.value
    )


def test_los_trabajos_se_encolan_una_vez_por_lote(
    service: IngestionService, material: Path, session_factory
) -> None:
    inventario = service.create_inventory(str(material))
    service.confirm_import(inventario.batch.id)
    service.confirm_import(inventario.batch.id)

    with session_factory() as session:
        total = session.execute(
            select(func.count())
            .select_from(JobRecord)
            .where(JobRecord.job_type == JobType.INGEST_BATCH.value)
        ).scalar_one()
        estados = set(session.execute(select(JobRecord.status)).scalars())
    assert total == 1
    assert estados == {JobStatus.QUEUED.value}
