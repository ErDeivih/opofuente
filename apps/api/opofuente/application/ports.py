"""Puertos consumidos por la capa de aplicación.

Toda integración (base de datos, OCR, almacén, proveedores IA) se declara aquí como
Protocol y se implementa en `opofuente.infrastructure`, de modo que el dominio no
conozca ninguna tecnología (02_ARCHITECTURE §7).
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from datetime import datetime
from pathlib import Path
from typing import Protocol, runtime_checkable

from opofuente.application.read_models import (
    BatchDetail,
    BatchView,
    ConvocationDetail,
    ConvocationSummary,
    CurriculumView,
    EntryPage,
    EntryView,
    IssuePage,
    NodeDetail,
    OppositionDetail,
    OppositionSummary,
    SeedOutcome,
)
from opofuente.domain.artifacts import OriginType, Sha256, StoredArtifact
from opofuente.domain.ingestion import (
    BatchKind,
    BatchMode,
    BatchStatus,
    CountersLike,
    DiscoveredEntry,
    ImportCounters,
    ImportIssue,
    ItemStatus,
    ScanResult,
)
from opofuente.domain.jobs import Job, JobStatus, JobType
from opofuente.domain.profiles import Profile
from opofuente.domain.system import Capability, CheckResult


@runtime_checkable
class HealthProbe(Protocol):
    """Comprobación real de una dependencia para /health/ready."""

    name: str

    def check(self) -> CheckResult:
        """Devuelve el resultado de la comprobación. No debe lanzar excepciones."""
        ...


@runtime_checkable
class CapabilityProvider(Protocol):
    """Declara qué capacidades opcionales están disponibles en este proceso."""

    def provide(self) -> tuple[Capability, ...]: ...


@runtime_checkable
class Clock(Protocol):
    """Fuente de tiempo. Inyectable para poder probar sin depender del reloj real."""

    def now(self) -> datetime: ...


@runtime_checkable
class ProfileRepository(Protocol):
    """Acceso a oposiciones, convocatorias, programa y reglas de examen."""

    def list_oppositions(self) -> Sequence[OppositionSummary]: ...

    def get_opposition(self, opposition_id: str) -> OppositionDetail | None: ...

    def activate_opposition(self, opposition_id: str, *, now: datetime) -> OppositionSummary | None:
        """Marca una oposición como activa y desactiva el resto."""
        ...

    def list_convocations(self, opposition_id: str) -> Sequence[ConvocationSummary]: ...

    def get_convocation(self, convocation_id: str) -> ConvocationDetail | None: ...

    def get_curriculum(self, convocation_id: str) -> CurriculumView | None: ...

    def get_node(self, node_id: str) -> NodeDetail | None: ...

    def upsert_profile(self, profile: Profile, *, now: datetime) -> SeedOutcome:
        """Siembra idempotente: repetirla no duplica ni deja datos a medias."""
        ...


@runtime_checkable
class ArtifactStorePort(Protocol):
    """Almacén de originales por contenido."""

    def store_file(
        self, source: Path, *, on_chunk: Callable[[], None] | None = None
    ) -> StoredArtifact:
        """Copia el fichero al almacén. `on_chunk` permite renovar el lease durante la copia."""
        ...

    def path_for(self, digest: Sha256) -> Path: ...

    def exists(self, digest: Sha256) -> bool: ...


@runtime_checkable
class InventoryScanner(Protocol):
    """Recorrido en lectura de una carpeta. No copia, no mueve y no borra."""

    def scan(self, root: Path) -> ScanResult: ...


@runtime_checkable
class IngestionRepository(Protocol):
    """Persistencia de lotes, entradas, incidencias y artefactos."""

    def create_batch(
        self,
        *,
        kind: BatchKind,
        mode: BatchMode,
        source_path_display: str,
        now: datetime,
        status: BatchStatus,
        manifest_hash: str | None = ...,
        inventory_batch_id: str | None = ...,
        job_id: str | None = ...,
        source_root: str | None = ...,
    ) -> str: ...

    def add_entries(
        self,
        batch_id: str,
        entries: Iterable[DiscoveredEntry],
        *,
        status: ItemStatus | None = ...,
    ) -> int: ...

    def add_issues(self, batch_id: str, issues: Iterable[ImportIssue], *, now: datetime) -> int: ...

    def set_counters(
        self, batch_id: str, counters: CountersLike, *, manifest_hash: str | None = ...
    ) -> None: ...

    def set_status(
        self,
        batch_id: str,
        status: BatchStatus,
        *,
        now: datetime,
        error_summary: str | None = ...,
    ) -> None: ...

    def set_job(self, batch_id: str, job_id: str) -> None: ...

    def request_cancel(self, batch_id: str) -> bool: ...

    def get_batch(self, batch_id: str) -> BatchView | None: ...

    def list_batches(self, *, limit: int, offset: int) -> tuple[BatchView, ...]: ...

    def get_batch_detail(
        self, batch_id: str, *, entry_limit: int, issue_limit: int
    ) -> BatchDetail | None: ...

    def list_entries(
        self,
        batch_id: str,
        *,
        limit: int,
        offset: int,
        status: ItemStatus | None = ...,
    ) -> EntryPage: ...

    def list_issues(self, batch_id: str, *, limit: int, offset: int) -> IssuePage: ...

    def pending_entries(self, batch_id: str) -> Sequence[EntryView]: ...

    def find_import_for(self, inventory_batch_id: str) -> BatchView | None: ...

    def source_root_of(self, batch_id: str) -> str | None: ...

    def summarize_import(self, batch_id: str) -> ImportCounters: ...

    def count_batch_artifacts(self, batch_id: str) -> int: ...

    def reset_items_for_retry(self, batch_id: str) -> int:
        """Devuelve a `inventoried` las entradas canceladas o fallidas del lote."""
        ...

    def issue_exists(self, batch_id: str, code: str, relative_path: str | None) -> bool:
        """¿Ya está anotada esa incidencia en el lote?"""
        ...

    def pending_extraction_count(self, batch_id: str) -> int:
        """Entradas copiadas y todavía sin extraer."""
        ...

    def count_items_in_status(self, batch_id: str, status: ItemStatus) -> int:
        """Cuántas entradas del lote están en ese estado (lo usa el reintento por fases)."""
        ...

    def item_id_for(self, batch_id: str, relative_path: str) -> str | None:
        """Identificador de una entrada del lote por su ruta relativa."""
        ...

    def mark_item(
        self,
        item_id: str,
        status: ItemStatus,
        *,
        artifact_id: str | None = ...,
        detail: str | None = ...,
        representation_id: str | None = ...,
    ) -> None: ...

    def register_artifact(
        self,
        *,
        digest: Sha256,
        size_bytes: int,
        media_type: str,
        storage_key: str,
        origin_type: OriginType,
        display_location: str,
        original_name: str | None,
        source_path_display: str | None,
        file_mtime: datetime | None,
        now: datetime,
    ) -> tuple[str, bool]: ...


@runtime_checkable
class JobQueue(Protocol):
    """Cola persistida de trabajos, con lease y cancelación (02_ARCHITECTURE §6)."""

    def enqueue(
        self,
        *,
        job_type: JobType,
        payload: dict[str, object],
        now: datetime,
        idempotency_key: str | None = ...,
        max_attempts: int = ...,
    ) -> tuple[Job, bool]: ...

    def get(self, job_id: str) -> Job | None: ...

    def list(self, *, limit: int, statuses: tuple[JobStatus, ...] = ...) -> tuple[Job, ...]: ...

    def claim_next(self, *, owner: str, now: datetime, lease_seconds: int) -> Job | None: ...

    def mark_running(self, job_id: str, *, owner: str, now: datetime) -> None: ...

    def renew_lease(
        self, job_id: str, *, owner: str, now: datetime, lease_seconds: int
    ) -> bool: ...

    def report_progress(
        self, job_id: str, *, progress: float, step: str | None, now: datetime
    ) -> None: ...

    def cancellation_requested(self, job_id: str) -> bool: ...

    def request_cancel(self, job_id: str, *, now: datetime) -> bool: ...

    def finish(self, job_id: str, *, owner: str, now: datetime) -> None: ...

    def acknowledge_cancel(self, job_id: str, *, owner: str, now: datetime) -> None: ...

    def fail(
        self,
        job_id: str,
        *,
        error_code: str,
        error_message: str,
        now: datetime,
        retry_at: datetime | None = ...,
    ) -> JobStatus: ...

    def requeue_expired_leases(self, *, now: datetime) -> tuple[Job, ...]:
        """Trabajos cuyo lease venció, con su estado nuevo (para avisar de los que se pierden)."""
        ...
