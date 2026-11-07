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

from opofuente.application.curriculum_models import (
    CurriculumDetailView,
    CurriculumNodeDetailView,
    CurriculumSummaryView,
    CurriculumVersionView,
    NodeMaterialPage,
    NodeQuestionPage,
    ProgressView,
    ReferenceView,
    StudyMarkView,
    TemarioView,
)
from opofuente.application.read_models import (
    AuditEventView,
    BatchDetail,
    BatchView,
    ConvocationDetail,
    ConvocationSummary,
    ConvocatoriasSeedReport,
    CoverageView,
    CurriculumSeedReport,
    CurriculumView,
    DecisionOutcome,
    DuplicateClusterDraft,
    DuplicateClusterView,
    EntryPage,
    EntryView,
    IssuePage,
    MappingView,
    NodeCoverageView,
    NodeDetail,
    OppositionDetail,
    OppositionSummary,
    ProposalPage,
    ProposalView,
    ReviewGroupView,
    SeedOutcome,
)
from opofuente.application.readiness_models import (
    MaterialSummary,
    OppositionRef,
    PendingCounts,
    QuestionSummary,
)
from opofuente.domain.artifacts import OriginType, Sha256, StoredArtifact
from opofuente.domain.classification import (
    ClassificationSubject,
    CoverageType,
    Proposal,
    ProposalStatus,
)
from opofuente.domain.convocatorias_c1 import C1ConvocatoriasFixture
from opofuente.domain.curricula import CommonCurriculum
from opofuente.domain.duplicates import TextDocument
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
from opofuente.domain.rag import CandidateSpan
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
class CurriculumRepository(Protocol):
    """Persistencia del temario común y de las referencias de las convocatorias."""

    def upsert_common_curriculum(
        self, curriculum: CommonCurriculum, *, now: datetime
    ) -> CurriculumSeedReport:
        """Siembra idempotente: repetirla no duplica ni deja el temario a medias."""
        ...


@runtime_checkable
class ConvocatoriasRepository(Protocol):
    """Siembra de convocatorias C1 que referencian el temario común (B-006)."""

    def upsert_c1_convocatorias(
        self, fixture: C1ConvocatoriasFixture, *, now: datetime
    ) -> ConvocatoriasSeedReport:
        """Importa o actualiza; repetirla no duplica ni deja referencias a medias."""
        ...


@runtime_checkable
class CurriculumReadRepository(Protocol):
    """Lecturas del temario común, sus referencias, particularidades y avance."""

    def list_curricula(self, *, kind: str | None) -> tuple[CurriculumSummaryView, ...]: ...

    def get_curriculum(self, code: str) -> CurriculumDetailView | None: ...

    def list_versions(self, code: str) -> tuple[CurriculumVersionView, ...] | None: ...

    def get_progress(self, code: str) -> ProgressView | None: ...

    def list_references(self, convocation_id: str) -> tuple[ReferenceView, ...] | None: ...

    def get_temario(self, convocation_id: str) -> TemarioView | None: ...

    def get_node(
        self, node_id: str, *, convocation_id: str | None = ...
    ) -> CurriculumNodeDetailView | None: ...

    def mark_studied(self, node_id: str, *, now: datetime) -> StudyMarkView | None: ...

    def unmark_studied(self, node_id: str) -> bool | None: ...

    def node_questions(
        self, node_id: str, *, limit: int, offset: int
    ) -> NodeQuestionPage | None: ...

    def node_materials(self, node_id: str, *, limit: int) -> NodeMaterialPage | None: ...


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
    ) -> None: ...

    def link_representation(self, item_id: str, representation_id: str, *, now: datetime) -> None:
        """Asocia una representación con la entrada de la que salió (idempotente por pareja)."""
        ...

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


# ------------------------------------------------------------------- S04: clasificación y revisión


@runtime_checkable
class ClassifierPort(Protocol):
    """Motor de clasificación: **propone**, no decide.

    Un motor recibe un `ClassificationSubject` (texto acotado, nombre, procedencia y los nodos del
    programa) y devuelve propuestas con su confianza, sus alternativas y su evidencia. No escribe
    nada: guardar y decidir es del servicio. Así el motor determinista de hoy y un clasificador LLM
    opcional de S09 son intercambiables, y el que no haya LLM configurado no cambia nada.
    """

    name: str
    version: str

    def propose(self, subject: ClassificationSubject) -> Sequence[Proposal]:
        """Propuestas sostenidas por la evidencia. Sin señales, una tupla vacía."""
        ...


@runtime_checkable
class ClassificationRepository(Protocol):
    """Persistencia de propuestas, mapeos, cobertura, duplicados y auditoría."""

    # --- insumos y propuestas

    def classification_targets(self, *, limit: int) -> tuple[ClassificationSubject, ...]:
        """Sujetos clasificables (artefactos y representaciones) con su extracto y los perfiles."""
        ...

    def save_proposals(self, proposals: Sequence[Proposal], *, now: datetime) -> tuple[int, int]:
        """Guarda propuestas nuevas y devuelve `(creadas, ya existentes)`, sin duplicar."""
        ...

    def text_documents(self, *, limit: int) -> tuple[TextDocument, ...]:
        """Textos de los sujetos comparables, para la detección de duplicados de texto."""
        ...

    def list_proposals(
        self,
        *,
        subject_type: str | None = ...,
        subject_id: str | None = ...,
        axis: str | None = ...,
        status: str | None = ...,
        limit: int = ...,
        offset: int = ...,
    ) -> ProposalPage: ...

    def get_proposal(self, proposal_id: str) -> ProposalView | None: ...

    def pending_groups(self) -> tuple[ReviewGroupView, ...]:
        """Propuestas pendientes agrupadas por sujeto, eje y valor: la unidad del lote."""
        ...

    # --- decisiones

    def decide(
        self,
        proposal_id: str,
        *,
        status: ProposalStatus,
        note: str | None,
        now: datetime,
        override_value: str | None = ...,
        coverage_type: CoverageType = ...,
        actor: str = ...,
        curriculum_version_id: str | None = ...,
    ) -> DecisionOutcome:
        """Aplica la decisión, su efecto (mapeo, cobertura) y la audita: un ítem por transacción."""
        ...

    def undo(self, proposal_id: str, *, now: datetime, actor: str = ...) -> DecisionOutcome:
        """Deshace la última decisión de una propuesta: vuelve a la cola y retira su mapeo."""
        ...

    def last_decision_event(self, proposal_id: str) -> AuditEventView | None:
        """Última decisión auditada de una propuesta, para poder deshacerla."""
        ...

    # --- mapeos y cobertura

    def list_mappings(
        self, *, subject_type: str | None = ..., subject_id: str | None = ...
    ) -> tuple[MappingView, ...]: ...

    def delete_mapping(self, mapping_id: str, *, now: datetime, actor: str = ...) -> bool: ...

    def coverage(self, *, convocation_code: str) -> CoverageView: ...

    def node_coverage(self, node_id: str) -> NodeCoverageView | None:
        """Cobertura de un nodo y de su subárbol."""
        ...

    # --- duplicados

    def record_text_duplicates(
        self, clusters: Sequence[DuplicateClusterDraft], *, now: datetime
    ) -> tuple[DuplicateClusterView, ...]: ...

    def list_duplicate_clusters(
        self, *, status: str | None = ...
    ) -> tuple[DuplicateClusterView, ...]: ...

    def resolve_duplicate_cluster(
        self, cluster_id: str, *, relation: str, note: str | None, now: datetime, actor: str = ...
    ) -> DuplicateClusterView | None: ...


@runtime_checkable
class VectorSearch(Protocol):
    """Búsqueda vectorial, opcional por diseño (`05_RAG §5`: FTS funciona sin ella).

    `available` y `reason` son parte del puerto a propósito: la aplicación tiene que poder decir «no
    hay proveedor de embeddings» en lugar de devolver cero resultados sin explicación. Un proveedor
    local o externo se enchufa aquí sin tocar el servicio.
    """

    @property
    def available(self) -> bool: ...

    @property
    def reason(self) -> str | None: ...

    @property
    def model(self) -> str | None: ...

    def search(self, question: str, *, limit: int) -> tuple[CandidateSpan, ...]: ...


@runtime_checkable
class ChangeRecorder(Protocol):
    """Quien se entera de que ha aparecido una versión nueva (S11).

    La biblioteca promociona —es su trabajo— y **avisa**; lo que se haga con el aviso (proponer un
    cambio, calcular el diff y los derivados afectados) no es cosa suya. Así una prueba de la
    biblioteca sigue pudiendo promocionar sin montar el servicio de cambios.
    """

    def record_version_change(self, *, document_id: str, new_version_id: str) -> object | None: ...


@runtime_checkable
class ReadinessRepository(Protocol):
    """Lo que hay que contar para decir si una oposición está lista para estudiar (S12.6).

    Son recuentos agregados, no listas: el resumen no enseña material ni preguntas, dice cuánto hay
    y qué falta. Por eso el puerto devuelve los modelos del resumen y no entidades, y cada cifra se
    resuelve en la base en lugar de traerse las filas para contarlas en memoria.
    """

    def opposition(self, opposition_id: str) -> OppositionRef | None: ...

    def material(self, *, opposition_id: str) -> MaterialSummary: ...

    def questions(self, *, opposition_id: str) -> QuestionSummary: ...

    def pending(self) -> PendingCounts: ...
