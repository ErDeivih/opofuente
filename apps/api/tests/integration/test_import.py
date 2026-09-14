"""Pruebas de integración de la importación: copia por hash, idempotencia y cancelación.

Se comprueban los criterios de aceptación de S02:

- los originales mantienen hash y fecha;
- dos archivos idénticos producen **un** artefacto y **dos** orígenes;
- una caída o un reinicio no duplican nada;
- la cancelación deja un informe cuadrado.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
from sqlalchemy import func, select

from opofuente.application.ingestion_service import IngestionService
from opofuente.application.job_service import JobExecution
from opofuente.config import DataPaths, Settings
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
    assert detalle.batch.status == BatchStatus.SUCCEEDED.value
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
    """Simula un proceso que muere a mitad: el trabajo vuelve a la cola y continúa sin duplicar."""
    inventario = service.create_inventory(str(material))
    batch_id = import_all(service, inventario.batch.id, cancel_after=1)

    # Tras la cancelación quedan entradas sin copiar; se devuelven a la cola como haría un reinicio.
    with session_factory() as session:
        session.execute(
            IngestionItemRecord.__table__.update()
            .where(IngestionItemRecord.status == ItemStatus.CANCELLED.value)
            .values(status=ItemStatus.INVENTORIED.value)
        )
        session.commit()

    batch = service.retry_batch(batch_id)
    job = _job_for(service, batch.id)
    service.run_import_job(FakeExecution(job))

    detalle = service.get_batch(batch_id)
    assert detalle.batch.counters["copied"] == 3
    with session_factory() as session:
        assert (
            session.execute(select(func.count()).select_from(SourceArtifactRecord)).scalar_one()
            == 2
        )


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
    assert detalle.batch.status == BatchStatus.SUCCEEDED.value


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
