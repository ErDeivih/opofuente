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
    AuditEventView,
    BatchDetail,
    BatchView,
    ConvocationDetail,
    ConvocationSummary,
    CoverageView,
    CurriculumView,
    DecisionOutcome,
    DossierVersionView,
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
from opofuente.application.topic_notes_models import NotesNode
from opofuente.domain.artifacts import OriginType, Sha256, StoredArtifact
from opofuente.domain.classification import (
    ClassificationSubject,
    CoverageType,
    Proposal,
    ProposalStatus,
)
from opofuente.domain.dossier import PassageFacts, TopicDossier
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
from opofuente.domain.topic_classification import (
    ClassifiableQuestion,
    ProposalBatch,
    Syllabus,
)
from opofuente.domain.topic_notes import (
    ComprobacionBatch,
    Hecho,
    HechosBatch,
    IncidenciaDeApuntes,
    MaterialPassage,
    NotesCheck,
    NoteSection,
    QuestionGroup,
    RedaccionBatch,
    TopicNotes,
)


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

    def activate_convocation(
        self, convocation_id: str, *, now: datetime
    ) -> ConvocationSummary | None:
        """Hace vigente una convocatoria y deja disponible la que lo era."""
        ...

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

    def request_pause(self, batch_id: str) -> bool:
        """Marca el lote en pausa: deja de avanzar sin perder lo hecho (DEBT-027 §4)."""
        ...

    def clear_pause(self, batch_id: str) -> bool:
        """Quita la pausa de un lote y lo devuelve a la cola."""
        ...

    def is_paused(self, batch_id: str) -> bool: ...

    def start_running(self, batch_id: str, *, now: datetime) -> bool:
        """Pasa el lote a `running` si no está en pausa. `False` si la pausa llegó antes."""
        ...

    def confirm_pause(self, batch_id: str, counters: CountersLike, *, now: datetime) -> bool:
        """Deja la pausa confirmada con los contadores al día, si el lote sigue en pausa."""
        ...

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

    def pause(self, job_id: str, *, now: datetime) -> bool:
        """Detiene un trabajo que aún no ha empezado (uno en marcha lo para su manejador)."""
        ...

    def acknowledge_pause(self, job_id: str, *, owner: str, now: datetime) -> None:
        """El manejador ha parado por la pausa de su lote: queda detenido, no terminado."""
        ...

    def resume(self, job_id: str, *, now: datetime) -> bool:
        """Devuelve a la cola un trabajo en pausa."""
        ...

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
class DossierRepository(Protocol):
    """De dónde salen los tramos de un tema y dónde se guardan sus versiones (S13).

    Un solo puerto para las dos cosas porque las dos son «el dossier en la base de datos»: el corpus
    (evidencias y mapeos) y el archivo de lo que se leyó. La primera no filtra nada: decide el
    dominio.
    """

    def node(self, node_id: str) -> tuple[str, str, int] | None:
        """`(path, title, depth)` del nodo, o `None` si no existe."""
        ...

    def passages_for_node(self, node_id: str) -> tuple[PassageFacts, ...]:
        """Los tramos citables que le llegan al tema y a su subárbol, con sus mapeos."""
        ...

    def mappings_for_node(self, node_id: str) -> tuple[str, ...]:
        """Estados de los mapeos vivos (no rechazados) que llegan al tema y a su subárbol."""
        ...

    def save_snapshot(
        self, *, node_id: str, dossier: TopicDossier, payload: str, now: datetime
    ) -> tuple[str, bool]:
        """Guarda una versión del dossier. Devuelve `(id, creada)`; repetir no duplica."""
        ...

    def latest_snapshot_id(self, node_id: str) -> str | None:
        """La última versión guardada, o `None` si el tema no tiene ninguna."""
        ...

    def snapshot(self, node_id: str, version_id: str) -> tuple[str, datetime, str] | None:
        """`(payload, built_at, content_hash)` de una versión guardada, si es de ese tema."""
        ...

    def snapshots(self, node_id: str) -> tuple[DossierVersionView, ...]:
        """Las versiones guardadas, de la más nueva a la más antigua, sin su contenido."""
        ...

    def retire_snapshot(self, node_id: str, *, reason: str, now: datetime) -> bool:
        """Retira la última versión del tema y lo deja auditado.

        Es lo contrario de `save_snapshot`, y existe porque un tema que no pasa la puerta de
        cobertura **no puede quedar publicado**: se va la lectura guardada, no el contenido.
        """
        ...


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


# ------------------------------------------------------------------- F4: clasificar por tema


@runtime_checkable
class TopicProposer(Protocol):
    """Un motor que propone tema y epígrafe para un lote de preguntas (F4).

    Propone, no decide: devuelve lo que contestó con su confianza, y los umbrales y la escritura son
    del servicio. Por eso el clasificador se puede probar entero con un doble que no llama a nadie.
    """

    name: str

    @property
    def version(self) -> str:
        """La versión del motor: dos modelos distintos proponen cosas distintas."""
        ...

    def propose(
        self, questions: Sequence[ClassifiableQuestion], *, syllabus: Syllabus
    ) -> ProposalBatch:
        """Las propuestas del lote y lo que costó pedirlas."""
        ...


# ------------------------------------------- apuntes guiados por preguntas (pasos B-E del plan)


@runtime_checkable
class TopicNotesReader(Protocol):
    """Los apuntes redactados de un tema, leídos para meterlos en su dossier.

    Es un puerto aparte del repositorio entero a propósito: quien solo monta el dossier de un tema
    (la
    API, al abrir un tema) no necesita saber escribir hechos ni apartados.
    """

    def notes_for_node(self, node_id: str) -> TopicNotes | None:
        """Los apuntes del tema tal como están hoy, o `None` si todavía no se han escrito."""
        ...


@runtime_checkable
class TopicNotesRepository(TopicNotesReader, Protocol):
    """Lo que los apuntes necesitan de la base: las preguntas del tema y lo que se va escribiendo.

    Todas las escrituras son idempotentes por su clave natural (tema + hecho, tema + apartado,
    pregunta + tema), porque una corrida de apuntes se reanuda: lo que ya está escrito no se repite
    y
    lo que falta se escribe. Es lo que permite parar y volver a empezar sin pagar dos veces.
    """

    def node_id(self, code: str) -> str | None:
        """El nodo del tema por su código legible (`IV.7`). `None` si no existe."""
        ...

    def node(self, node_id: str) -> NotesNode | None:
        """El tema con sus epígrafes oficiales, en orden. `None` si el nodo no es un tema."""
        ...

    def question_groups(self, node_id: str) -> tuple[QuestionGroup, ...]:
        """Los grupos de preguntas del tema (y de sus epígrafes), con su clave y su estado."""
        ...

    def facts(self, node_id: str) -> tuple[Hecho, ...]:
        """Los hechos guardados del tema, en orden de creación."""
        ...

    def save_facts(
        self, node_id: str, hechos: Sequence[Hecho], *, now: datetime
    ) -> tuple[Hecho, ...]:
        """Guarda los hechos nuevos (los que ya estaban no se duplican).

        Devuelve los hechos guardados **en el mismo orden** que llegaron y con su identificador: es
        lo
        que permite repartirlos por apartados después, y sin el identificador no se pueden ni
        asignar
        ni volver a leer.
        """
        ...

    def sections(self, node_id: str) -> tuple[NoteSection, ...]:
        """Los apartados del tema, en orden, con sus hechos y su texto."""
        ...

    def save_sections(
        self, node_id: str, sections: Sequence[NoteSection], *, now: datetime
    ) -> tuple[NoteSection, ...]:
        """Crea o actualiza los apartados del esquema y reparte los hechos. Devuelve los
        guardados."""
        ...

    def save_section_body(
        self,
        section: NoteSection,
        *,
        title: str | None,
        body: str,
        needs_review_reason: str | None,
        model: str | None,
        now: datetime,
        append: bool = False,
    ) -> NoteSection:
        """Escribe el texto de un apartado (o le añade un párrafo, con `append=True`).

        `model` es el modelo que lo escribió: va con el apartado para que la versión del tema pueda
        decir con qué se redactó, que es lo que permite comparar dos corridas.
        """
        ...

    def checks(self, node_id: str) -> tuple[NotesCheck, ...]:
        """Los resultados de comprobación guardados del tema, para reanudar sin repetir llamadas."""
        ...

    def forget_sections(self, node_id: str) -> int:
        """Tira los apartados del tema y sus enlaces, y deja los hechos sin repartir.

        Se usa cuando el esquema se mueve: los apartados que había ya no corresponden a ningún
        subapartado del plan nuevo, y su texto y sus comprobaciones se vuelven a calcular. Los
        **hechos se conservan**: son el trabajo caro y siguen siendo verdad.
        """
        ...

    def save_checks(self, node_id: str, results: Sequence[NotesCheck], *, now: datetime) -> int:
        """Guarda el resultado de comprobar unas preguntas. Cada pregunta tiene un solo
        resultado."""
        ...

    def save_incidents(
        self, node_id: str, incidents: Sequence[IncidenciaDeApuntes], *, now: datetime
    ) -> int:
        """Deja en la bandeja del propietario las preguntas que los apuntes no cubren (§2.1.4).

        Una fila por pregunta y tema: lo que ya está cubierto sale de la bandeja, y volver a
        comprobar el tema actualiza la incidencia en vez de añadir otra copia.
        """
        ...

    def incidents(self, node_id: str) -> tuple[IncidenciaDeApuntes, ...]:
        """La bandeja del tema: las incidencias con su categoría, para el panel."""
        ...

    def forget_facts(
        self,
        node_id: str,
        fact_ids: Sequence[str],
        *,
        actor: str,
        reason: str,
        now: datetime,
    ) -> int:
        """Tira unos hechos del tema y lo deja auditado. Devuelve cuántos ha tirado.

        Es para lo que se va del tema: los hechos de una pregunta **mal clasificada**, que se lleva
        la cola de clasificación. Dejarlos aquí sería sostener un apartado del que ya no son, y el
        propietario lo pidió así: «sus datos se van con ellas». Se borran uno a uno (no por lote a
        ciegas) y queda el evento con quién lo hizo y por qué.
        """
        ...


#: El actor con el que se firma lo que escribe la máquina en los apuntes.
ACTOR_APUNTES = "llm:deepseek-flash"


@runtime_checkable
class NotesModel(Protocol):
    """Un motor que saca hechos de las preguntas, redacta apartados y los comprueba (pasos B, D y
    E).

    No decide nada del producto: devuelve lo que contestó y el servicio aplica las reglas —qué se
    guarda, qué se da por cubierto y qué queda como incidencia—. Por eso los apuntes se pueden
    probar
    enteros con un doble que no llama a nadie (y sin gastar).

    Los cuatro métodos son las cuatro llamadas del plan: `hechos` (paso B), `redactar` (paso D),
    `comprobar` (paso E) y `anadir` (la vuelta de huecos del paso E).
    """

    name: str

    @property
    def version(self) -> str:
        """La versión del motor: dos modelos distintos escriben apuntes distintos."""
        ...

    def hechos(
        self,
        grupos: Sequence[QuestionGroup],
        *,
        topic_code: str,
        topic_title: str,
        epigraphs: Sequence[tuple[str, str]],
    ) -> HechosBatch:
        """Los hechos de un lote de grupos y lo que costó pedirlos."""
        ...

    def redactar(
        self,
        section: NoteSection,
        *,
        topic_code: str,
        topic_title: str,
        material: Sequence[MaterialPassage],
        es_tabla_de_puertos: bool = False,
    ) -> RedaccionBatch:
        """El texto de un apartado, con todos sus hechos dentro.

        `es_tabla_de_puertos` añade a las instrucciones la organización por familias y la regla de
        las notas (que explican el puerto, no lo que no es). Es un dato del apartado, no del tema, y
        el motor no tiene por qué saber de qué catálogo sale.
        """
        ...

    def comprobar(self, grupos: Sequence[QuestionGroup], *, apuntes: str) -> ComprobacionBatch:
        """Si los apuntes contestan a esas preguntas, con la frase exacta que lo justifica."""
        ...

    def anadir(
        self, section: NoteSection, grupos: Sequence[QuestionGroup], hechos: Sequence[Hecho]
    ) -> RedaccionBatch:
        """Lo que falta en un apartado para contestar las preguntas que no cubre.

        Los hechos son los del paso B para esas mismas preguntas: el añadido se apoya en ellos y no
        en
        lo que el modelo recuerde.
        """
        ...
