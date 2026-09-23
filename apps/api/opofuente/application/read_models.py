"""Modelos de lectura que la API devuelve.

No son entidades de dominio ni tablas: son la forma en que la aplicación entrega los datos ya
combinados (por ejemplo, una convocatoria con sus partes y reglas) evitando que la capa API
consulte la base de datos.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime

from opofuente.domain.jobs import Job
from opofuente.domain.profiles import (
    ConvocationStatus,
    ExamPart,
    ExamRule,
    NodeType,
    PartFormat,
    PartKind,
    RuleKind,
)


@dataclass(frozen=True, slots=True)
class OppositionSummary:
    id: str
    code: str
    name: str
    description: str | None
    active: bool
    convocation_id: str | None
    convocation_code: str | None
    convocation_status: ConvocationStatus | None
    convocation_published_at: date | None


@dataclass(frozen=True, slots=True)
class ConvocationSummary:
    id: str
    opposition_id: str
    code: str
    title: str
    official_url: str
    published_at: date
    exam_date: date | None
    status: ConvocationStatus


@dataclass(frozen=True, slots=True)
class OppositionDetail:
    opposition: OppositionSummary
    convocations: tuple[ConvocationSummary, ...]


@dataclass(frozen=True, slots=True)
class ConvocationDetail:
    summary: ConvocationSummary
    opposition_code: str
    opposition_name: str
    source_reference: str | None
    #: Por qué la fecha de ejercicio es la que es, o por qué no hay ninguna: distingue «no lo sé» de
    #: «lo dirá otra resolución», y por eso la interfaz puede enseñarlo (S12.2).
    exam_date_note: str | None
    parts: tuple[ExamPart, ...]
    rules: tuple[ExamRule, ...]


@dataclass(frozen=True, slots=True)
class NodeView:
    id: str
    node_type: NodeType
    official_code: str
    title: str
    description: str | None
    position: int
    path: str
    depth: int
    children: tuple[NodeView, ...] = ()


@dataclass(frozen=True, slots=True)
class CurriculumView:
    convocation_id: str
    convocation_code: str
    opposition_code: str
    counts: dict[str, int]
    nodes: tuple[NodeView, ...]


@dataclass(frozen=True, slots=True)
class NodeDetail:
    node: NodeView
    convocation_id: str
    convocation_code: str
    convocation_title: str
    official_url: str
    published_at: date
    opposition_code: str
    opposition_name: str
    source_reference: str | None
    ancestors: tuple[NodeView, ...] = ()


@dataclass(frozen=True, slots=True)
class EntityOutcome:
    """Qué ha pasado con una entidad al sembrar: creada, actualizada, sin cambios o bloqueada.

    `blocked` es un conflicto, no un «sin cambios»: la siembra **quería** retirar la entidad (un
    nodo del programa que ya no está en el fixture) y no ha podido porque tiene material asignado.
    Se informa en lugar de borrarse en silencio (DEBT-005, ADR-007).
    """

    code: str
    created: bool
    updated: bool
    blocked: bool = False

    @property
    def unchanged(self) -> bool:
        return not self.created and not self.updated and not self.blocked


@dataclass(frozen=True, slots=True)
class SeedOutcome:
    profile_code: str
    entities: tuple[EntityOutcome, ...] = ()

    @property
    def created(self) -> int:
        return sum(1 for entity in self.entities if entity.created)

    @property
    def updated(self) -> int:
        return sum(1 for entity in self.entities if entity.updated)

    @property
    def unchanged(self) -> int:
        return sum(1 for entity in self.entities if entity.unchanged)

    @property
    def blocked(self) -> int:
        return sum(1 for entity in self.entities if entity.blocked)

    @property
    def changed(self) -> bool:
        return self.created > 0 or self.updated > 0 or self.blocked > 0


@dataclass(frozen=True, slots=True)
class SeedReport:
    profiles: tuple[SeedOutcome, ...] = ()

    @property
    def created(self) -> int:
        return sum(profile.created for profile in self.profiles)

    @property
    def updated(self) -> int:
        return sum(profile.updated for profile in self.profiles)

    @property
    def unchanged(self) -> int:
        return sum(profile.unchanged for profile in self.profiles)

    @property
    def blocked(self) -> int:
        return sum(profile.blocked for profile in self.profiles)

    @property
    def changed(self) -> bool:
        return any(profile.changed for profile in self.profiles)

    def summary(self) -> str:
        texto = (
            f"{len(self.profiles)} perfiles: {self.created} entidades nuevas, "
            f"{self.updated} actualizadas, {self.unchanged} sin cambios"
        )
        if self.blocked:
            texto += (
                f", {self.blocked} sin retirar (nodos del programa con material asignado; "
                "ver ADR-007)"
            )
        return texto


# ------------------------------------------------------------------ S02: ingesta y trabajos


@dataclass(frozen=True, slots=True)
class EntryView:
    """Una entrada del inventario o del lote, tal y como se muestra."""

    id: str
    relative_path: str
    original_name: str
    size_bytes: int
    media_type: str | None
    status: str
    detail: str | None = None
    artifact_sha256: str | None = None
    #: Fecha de modificación vista en el inventario. Viaja al lote de importación para poder
    #: detectar que el fichero cambió antes de copiarlo (no solo por tamaño).
    mtime: datetime | None = None
    #: Niveles de contenedor recorridos hasta esta entrada (0 = tal cual del origen, 1 = dentro
    #: de un ZIP). El límite de anidamiento se decide con este dato persistido, no con el nombre.
    container_depth: int = 0
    #: De dónde salió esta entrada en concreto: `file`, `paste` o `url`.
    origin_type: str | None = None
    #: Cómo se muestra ese origen, ya saneado (las URL, sin cadena de consulta).
    origin_display: str | None = None


@dataclass(frozen=True, slots=True)
class IssueView:
    code: str
    severity: str
    safe_message: str
    relative_path: str | None = None
    details: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class BatchView:
    id: str
    kind: str
    mode: str
    status: str
    source_path_display: str
    counters: dict[str, int]
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    job_id: str | None = None
    inventory_batch_id: str | None = None
    manifest_hash: str | None = None
    error_summary: str | None = None
    formats: dict[str, int] = field(default_factory=dict)
    issue_counts: dict[str, int] = field(default_factory=dict)
    total_items: int = 0


@dataclass(frozen=True, slots=True)
class BatchDetail:
    batch: BatchView
    entries: tuple[EntryView, ...]
    issues: tuple[IssueView, ...]
    artifacts_total: int = 0


@dataclass(frozen=True, slots=True)
class EntryPage:
    entries: tuple[EntryView, ...]
    total: int
    limit: int
    offset: int


@dataclass(frozen=True, slots=True)
class IssuePage:
    issues: tuple[IssueView, ...]
    total: int
    limit: int
    offset: int


@dataclass(frozen=True, slots=True)
class RepresentationSource:
    """Una entrada de la que sale el texto de una representación, con **su** origen.

    Se toma de la entrada, no del artefacto: el mismo contenido puede haber entrado como fichero,
    como texto pegado y como URL, y cada entrada sabe de dónde vino. Deducirlo del artefacto daba
    tipos de origen equivocados.

    `location` es la procedencia **mostrable** de esa entrada: la ruta relativa de un fichero, el
    título de un texto pegado o la URL descargada (ya sin cadena de consulta). No es la clave
    interna del artefacto.
    """

    location: str
    origin_type: str | None = None
    depth: int = 0


@dataclass(frozen=True, slots=True)
class RepresentationView:
    """Una representación extraída, tal y como se muestra. El texto se lee aparte."""

    id: str
    artifact_id: str
    kind: str
    status: str
    quality: str
    extractor_name: str
    extractor_version: str
    char_count: int
    ocr_candidate: bool
    warnings: tuple[str, ...]
    created_at: datetime
    language: str | None = None
    page_count: int | None = None
    has_text: bool = False
    storage_key: str | None = None
    format_version: int = 1
    #: Entradas de las que sale este texto, en orden de entrada. Un mismo contenido copiado dos
    #: veces comparte representación: sin esto, quien lee no sabe de qué fichero es el texto.
    sources: tuple[RepresentationSource, ...] = ()

    @property
    def source_locations(self) -> tuple[str, ...]:
        return tuple(source.location for source in self.sources)


@dataclass(frozen=True, slots=True)
class JobView:
    id: str
    job_type: str
    status: str
    progress: float
    attempts: int
    max_attempts: int
    created_at: datetime
    updated_at: datetime
    step: str | None = None
    error_code: str | None = None
    error_message: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    cancel_requested: bool = False


def job_to_view(job: Job) -> JobView:
    """Traduce el trabajo de dominio a la vista que devuelve la API."""
    return JobView(
        id=job.id,
        job_type=job.job_type.value,
        status=job.status.value,
        progress=job.progress,
        attempts=job.attempts,
        max_attempts=job.max_attempts,
        created_at=job.created_at,
        updated_at=job.updated_at,
        step=job.step,
        error_code=job.error_code,
        error_message=job.error_message,
        started_at=job.started_at,
        finished_at=job.finished_at,
        cancel_requested=job.cancellation_requested,
    )


# ------------------------------------------- S04: clasificación, revisión, cobertura y duplicados


@dataclass(frozen=True, slots=True)
class AlternativeView:
    """Alternativa que un motor barajó para el mismo eje, con su confianza."""

    value: str
    confidence: float


@dataclass(frozen=True, slots=True)
class ProposalView:
    """Propuesta tal como la sirve la API: con su banda, si es crítica y con qué se sostiene."""

    id: str
    subject_type: str
    subject_id: str
    subject_label: str | None
    axis: str
    proposed_value: str
    value_label: str | None
    confidence: float
    band: str
    is_critical: bool
    status: str
    engine_name: str
    engine_version: str
    alternatives: tuple[AlternativeView, ...] = ()
    evidence: tuple[str, ...] = ()
    created_at: datetime | None = None
    decided_at: datetime | None = None
    decision_note: str | None = None


@dataclass(frozen=True, slots=True)
class ProposalPage:
    proposals: tuple[ProposalView, ...]
    total: int
    limit: int
    offset: int


@dataclass(frozen=True, slots=True)
class ReviewGroupView:
    """Grupo de revisión: propuestas pendientes que comparten sujeto, eje y valor propuesto."""

    key: str
    subject_type: str
    axis: str
    proposed_value: str
    label: str
    proposal_ids: tuple[str, ...] = ()
    min_confidence: float = 0.0
    max_confidence: float = 0.0
    is_critical: bool = False

    @property
    def size(self) -> int:
        return len(self.proposal_ids)


@dataclass(frozen=True, slots=True)
class MappingView:
    """Material asignado a un nodo del programa."""

    id: str
    node_id: str
    node_path: str
    node_title: str
    node_depth: int
    subject_type: str
    subject_id: str
    subject_label: str | None
    coverage_type: str
    depth: int
    confidence: float
    status: str
    source_proposal_id: str | None = None
    approved_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class CoverageNodeView:
    """Cobertura de un nodo: provisional (sin confirmar) y aceptada (confirmada y utilizable)."""

    node_id: str
    path: str
    title: str
    depth: int
    provisional: int = 0
    accepted: int = 0
    materials: tuple[str, ...] = ()

    @property
    def total(self) -> int:
        return self.provisional + self.accepted


@dataclass(frozen=True, slots=True)
class CoverageView:
    """Cobertura de un programa. `unclassified` es el material del que aún no se sabe nada."""

    convocation_code: str
    nodes: tuple[CoverageNodeView, ...] = ()
    provisional_total: int = 0
    accepted_total: int = 0
    classified_subjects: int = 0
    unclassified_subjects: int = 0
    materials_total: int = 0


@dataclass(frozen=True, slots=True)
class NodeCoverageView:
    """Cobertura de un nodo concreto y de todo su subárbol, sin mezclar provisional y aceptada."""

    node_id: str
    path: str
    title: str
    depth: int
    provisional: int = 0
    accepted: int = 0
    unclassified_subjects: int = 0
    materials_total: int = 0
    subtree: tuple[CoverageNodeView, ...] = ()


@dataclass(frozen=True, slots=True)
class DecisionOutcome:
    """Resultado de decidir una propuesta. Cada ítem es transaccional: o se aplica, o se explica."""

    proposal_id: str
    status: str
    applied: bool
    mapping_id: str | None = None
    audit_event_id: str | None = None
    reason: str | None = None


@dataclass(frozen=True, slots=True)
class BulkDecisionResult:
    """Decisión en lote: nunca es todo-o-nada, y las excepciones viajan aparte."""

    outcomes: tuple[DecisionOutcome, ...] = ()
    excluded: tuple[str, ...] = ()

    @property
    def applied(self) -> int:
        return sum(1 for outcome in self.outcomes if outcome.applied)

    @property
    def conflicts(self) -> int:
        return sum(1 for outcome in self.outcomes if not outcome.applied)

    @property
    def requested(self) -> int:
        return len(self.outcomes) + len(self.excluded)


@dataclass(frozen=True, slots=True)
class DuplicateMemberView:
    subject_type: str
    subject_id: str
    subject_label: str | None
    similarity: float
    is_representative: bool = False


@dataclass(frozen=True, slots=True)
class DuplicateClusterDraft:
    """Cluster detectado por un motor de duplicados, antes de guardarlo."""

    kind: str
    relation: str
    signature: str
    members: tuple[DuplicateMemberView, ...] = ()


@dataclass(frozen=True, slots=True)
class AuditEventView:
    """Acción auditada: quién, qué, sobre qué y el antes/después sanitizado."""

    id: str
    actor: str
    action: str
    object_type: str
    object_id: str
    created_at: datetime
    before: dict[str, object] = field(default_factory=dict)
    after: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class DuplicateClusterView:
    """Grupo de material con el mismo texto o muy parecido. Nunca borra nada por sí solo."""

    id: str
    kind: str
    relation: str
    signature: str
    status: str
    members: tuple[DuplicateMemberView, ...] = ()
    created_at: datetime | None = None
    resolved_at: datetime | None = None
    resolution_note: str | None = None


@dataclass(frozen=True, slots=True)
class AcceptedValueView:
    """Lo que consta de un eje para un material: lo aceptado o lo aplicado provisionalmente."""

    axis: str
    value: str
    value_label: str | None
    status: str
    confidence: float
    is_critical: bool = False
    decided_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class AcceptedClassificationView:
    """Clasificación vigente de un material, eje por eje.

    Es lo que hace que aceptar una propuesta **se note** en el producto: hasta ahora el valor
    aceptado solo se podía reconstruir consultando la lista de propuestas, así que en cuatro de los
    cinco ejes la revisión no tenía efecto visible.
    """

    subject_type: str
    subject_id: str
    subject_label: str | None
    values: tuple[AcceptedValueView, ...] = ()

    @property
    def pending_review(self) -> bool:
        """¿Queda algo aplicado provisionalmente, es decir, revisable?"""
        return any(valor.status == "auto_applied_provisional" for valor in self.values)


@dataclass(frozen=True, slots=True)
class ClassificationRunReport:
    """Qué ha dejado una pasada: propuestas nuevas, repetidas y sujetos sin señales."""

    subjects: int = 0
    proposals_created: int = 0
    proposals_unchanged: int = 0
    subjects_without_signals: int = 0
    auto_applied: int = 0
    duplicates_found: int = 0

    def summary(self) -> str:
        return (
            f"{self.subjects} sujetos: {self.proposals_created} propuestas nuevas, "
            f"{self.proposals_unchanged} ya existentes, "
            f"{self.subjects_without_signals} sin señales, "
            f"{self.auto_applied} aplicadas provisionalmente, "
            f"{self.duplicates_found} grupos de duplicados"
        )


__all__ = [
    "AcceptedClassificationView",
    "AcceptedValueView",
    "AlternativeView",
    "AuditEventView",
    "BulkDecisionResult",
    "ClassificationRunReport",
    "ConvocationDetail",
    "ConvocationSummary",
    "CoverageNodeView",
    "CoverageView",
    "CurriculumView",
    "DecisionOutcome",
    "DuplicateClusterDraft",
    "DuplicateClusterView",
    "DuplicateMemberView",
    "EntityOutcome",
    "MappingView",
    "NodeCoverageView",
    "NodeDetail",
    "NodeView",
    "OppositionDetail",
    "OppositionSummary",
    "PartFormat",
    "PartKind",
    "ProposalPage",
    "ProposalView",
    "ReviewGroupView",
    "RuleKind",
    "SeedOutcome",
    "SeedReport",
    "field",
]
