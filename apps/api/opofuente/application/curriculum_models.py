"""Modelos de lectura del temario común (B-004 y B-005).

No son tablas: son la forma en que la aplicación entrega el temario para que la capa API no consulte
la base a mano. El avance se calcula al leer (nunca se guarda un porcentaje) y siempre sobre los
nodos del temario común, que es el que estudia el alumno.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

from opofuente.application.read_models import NodeView


@dataclass(frozen=True, slots=True)
class CurriculumVersionView:
    code: str
    version_no: int
    title: str
    status: str


@dataclass(frozen=True, slots=True)
class CurriculumSummaryView:
    code: str
    name: str
    kind: str
    group_code: str | None
    family: str | None
    versions: tuple[CurriculumVersionView, ...]
    active_version: CurriculumVersionView | None


@dataclass(frozen=True, slots=True)
class BlockProgressView:
    block_id: str
    path: str
    title: str
    position: int
    topics_total: int
    topics_studied: int
    topics_with_activity: int
    percent: float


@dataclass(frozen=True, slots=True)
class ProgressView:
    curriculum_code: str
    version_code: str
    blocks: tuple[BlockProgressView, ...]
    topics_total: int
    topics_studied: int
    topics_with_activity: int
    percent: float


@dataclass(frozen=True, slots=True)
class CurriculumDetailView:
    code: str
    name: str
    kind: str
    group_code: str | None
    family: str | None
    versions: tuple[CurriculumVersionView, ...]
    active_version: CurriculumVersionView | None
    counts: dict[str, int]
    nodes: tuple[NodeView, ...]
    progress: ProgressView | None


@dataclass(frozen=True, slots=True)
class AdjustmentView:
    kind: str
    weight: float | None
    official_code_override: str | None
    title_override: str | None
    evidence_quote: str


@dataclass(frozen=True, slots=True)
class AppearanceView:
    """Una convocatoria en la que aparece un tema del común, con sus particularidades."""

    convocation_id: str
    convocation_code: str
    convocation_title: str
    convocation_status: str
    role: str
    source_reference: str | None
    omitted: bool
    adjustments: tuple[AdjustmentView, ...]


@dataclass(frozen=True, slots=True)
class CurriculumIdentityView:
    code: str
    name: str
    kind: str
    version_code: str
    version_title: str


@dataclass(frozen=True, slots=True)
class ConvocationIdentityView:
    id: str
    code: str
    title: str
    official_url: str
    published_at: date
    opposition_code: str
    opposition_name: str
    source_reference: str | None


@dataclass(frozen=True, slots=True)
class ReferenceView:
    role: str
    curriculum_code: str
    curriculum_name: str
    curriculum_kind: str
    version_code: str
    version_no: int
    version_title: str
    source_reference: str | None


@dataclass(frozen=True, slots=True)
class TemarioView:
    """Temario efectivo de una convocatoria: la versión referenciada con sus particularidades."""

    convocation: ConvocationIdentityView
    curriculum: CurriculumIdentityView
    version: CurriculumVersionView
    counts: dict[str, int]
    nodes: tuple[NodeView, ...]
    omitted_topics: int


@dataclass(frozen=True, slots=True)
class CurriculumNodeDetailView:
    node: NodeView
    curriculum: CurriculumIdentityView
    convocation: ConvocationIdentityView | None
    appears_in: tuple[AppearanceView, ...]
    particularities: tuple[AdjustmentView, ...]
    studied_at: datetime | None
    ancestors: tuple[NodeView, ...]


@dataclass(frozen=True, slots=True)
class StudyMarkView:
    node_id: str
    studied_at: datetime


@dataclass(frozen=True, slots=True)
class NodeQuestionView:
    """Pregunta del banco catalogada en el tema, en la versión que se mapeó."""

    id: str
    question_set_id: str
    set_title: str
    stable_key: str
    stem: str
    question_type: str
    origin_type: str
    position: int
    is_reserve: bool


@dataclass(frozen=True, slots=True)
class NodeQuestionPage:
    node_id: str
    total: int
    limit: int
    offset: int
    questions: tuple[NodeQuestionView, ...]


@dataclass(frozen=True, slots=True)
class NodeMaterialView:
    """Material de la biblioteca catalogado en el tema: documento, sección o cita."""

    subject_type: str
    subject_id: str
    document_id: str | None
    document_version_id: str | None
    title: str
    section_title: str | None
    page: int | None
    citation_label: str | None
    excerpt: str | None
    coverage_type: str


@dataclass(frozen=True, slots=True)
class NodeMaterialPage:
    node_id: str
    total: int
    materials: tuple[NodeMaterialView, ...]


def percent(studied: int, total: int) -> float:
    """Porcentaje con un decimal; cero cuando todavía no hay temas."""
    if total <= 0:
        return 0.0
    return round(studied * 100.0 / total, 1)
