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
    """Qué ha pasado con una entidad al sembrar: creada, actualizada o sin cambios."""

    code: str
    created: bool
    updated: bool

    @property
    def unchanged(self) -> bool:
        return not self.created and not self.updated


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
    def changed(self) -> bool:
        return self.created > 0 or self.updated > 0


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
    def changed(self) -> bool:
        return any(profile.changed for profile in self.profiles)

    def summary(self) -> str:
        return (
            f"{len(self.profiles)} perfiles: {self.created} entidades nuevas, "
            f"{self.updated} actualizadas, {self.unchanged} sin cambios"
        )


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


__all__ = [
    "ConvocationDetail",
    "ConvocationSummary",
    "CurriculumView",
    "EntityOutcome",
    "NodeDetail",
    "NodeView",
    "OppositionDetail",
    "OppositionSummary",
    "PartFormat",
    "PartKind",
    "RuleKind",
    "SeedOutcome",
    "SeedReport",
    "field",
]
