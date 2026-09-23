"""Vistas de errores, repaso y dominio (S10): lo que la API devuelve y la interfaz enseña.

Son dataclasses **de lectura**: la comprobación de qué se puede decir de un fallo o de un tema vive
en el dominio y en el servicio. Aquí solo se describe lo que viaja.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from opofuente.domain.review import ErrorCause, Mastery, ReviewOutcome


@dataclass(frozen=True, slots=True)
class ReviewItemView:
    """El estado de repaso de una pregunta: cuándo toca y con qué intervalo."""

    id: str
    question_version_id: str
    opposition_id: str
    learning_error_id: str | None
    due_at: datetime
    interval_days: int
    repetitions: int
    lapses: int
    last_reviewed_at: datetime | None
    last_reason: str | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class ReviewEventView:
    """Un paso del historial: qué pasó, de qué fecha a qué fecha y por qué."""

    id: str
    kind: str
    outcome: ReviewOutcome | None
    confidence: str | None
    cause: ErrorCause | None
    note: str | None
    previous_due_at: datetime | None
    due_at: datetime
    previous_interval_days: int | None
    interval_days: int
    repetitions: int
    reason: str
    occurred_at: datetime


@dataclass(frozen=True, slots=True)
class DueItemView:
    """Lo que toca repasar, con la pregunta y el motivo de estar en la cola."""

    item: ReviewItemView
    question_version_id: str
    question_set_id: str
    stable_key: str
    stem: str
    #: La parte del examen de la sesión en la que se falló. Es `None` si aquella sesión no la
    #: registró: sin parte no se puede montar el repaso, y se dice en lugar de inventarla.
    part_code: str | None
    is_reserve: bool
    origin_type: str
    overdue_days: int
    explanation: str
    options: tuple[tuple[str, str], ...]
    session_id: str


@dataclass(frozen=True, slots=True)
class ReviewStatsView:
    """Cuánto queda por repasar, sin adornos: activos, vencidos y fallos acumulados."""

    active: int
    due: int
    next_due_at: datetime | None
    lapses: int


@dataclass(frozen=True, slots=True)
class ErrorView:
    """Un fallo con la causa que ha declarado la persona (o la que declaró y luego corrigió)."""

    id: str
    attempt_id: str
    question_version_id: str | None
    stable_key: str | None
    stem: str | None
    session_id: str | None
    part_code: str | None
    curriculum_node_id: str | None
    node_title: str | None
    concept_label: str | None
    cause: ErrorCause
    user_note: str | None
    status: str
    occurrences: int
    first_seen_at: datetime
    last_seen_at: datetime
    resolved_at: datetime | None


@dataclass(frozen=True, slots=True)
class ErrorDetailView:
    """Un error con su intento, su repaso y el historial completo de ese repaso."""

    error: ErrorView
    chosen_option_keys: tuple[str, ...]
    confidence: str | None
    answered_at: datetime | None
    review: ReviewItemView | None
    events: tuple[ReviewEventView, ...]


@dataclass(frozen=True, slots=True)
class ConceptSummaryView:
    """Un concepto: los fallos que se agrupan bajo él, con lo que hay que saber para priorizar."""

    key: str
    label: str
    errors: tuple[ErrorView, ...]
    open_count: int
    resolved_count: int
    occurrences: int
    last_seen_at: datetime
    node_id: str | None


@dataclass(frozen=True, slots=True)
class ConceptGroupView:
    """La vista `Conceptos`: los grupos y sus totales."""

    groups: tuple[ConceptSummaryView, ...]
    total_errors: int
    open_errors: int


@dataclass(frozen=True, slots=True)
class ReviewQueueView:
    """La vista `Hoy`: la cola ordenada, sus cifras y los conceptos con los que se relaciona."""

    items: tuple[DueItemView, ...]
    stats: ReviewStatsView
    concepts: tuple[ConceptSummaryView, ...]
    #: Lo que la cola **no** puede decir todavía (por ejemplo, que no hay preguntas asignadas a un
    #: tema): se declara en lugar de dejar la pantalla muda.
    notes: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class NodeMasteryView:
    """El dominio estimado de un nodo del programa, con sus recuentos y su explicación."""

    curriculum_node_id: str
    mastery: Mastery


@dataclass(frozen=True, slots=True)
class NodeStudyState:
    """El estado de estudio de un nodo: qué preguntas tiene y cuándo toca repasarlas.

    Es la otra mitad de la pregunta que contesta el dominio: un tema con dominio alto y sin ninguna
    pregunta asignada que se pueda practicar no es lo mismo que un tema con preguntas y buen
    dominio, y la pantalla de Programa tiene que poder decirlo.
    """

    curriculum_node_id: str
    #: Cuántas preguntas (versiones vigentes con mapeo **aceptado** a este nodo) hay de cada estado.
    questions_by_status: tuple[tuple[str, int], ...] = ()
    #: Las mismas preguntas por **origen** (oficial, privada, generada): 07_UI-UX §5 pide ver las
    #: oficiales separadas del resto, y eso no se puede deducir del estado.
    questions_by_origin: tuple[tuple[str, int], ...] = ()
    #: Repasos ya vencidos del nodo (los que tocan ahora).
    reviews_due: int = 0
    #: Cuándo toca el siguiente repaso **programado** (el que aún no ha vencido). Los vencidos van
    #: en `reviews_due`: una fecha pasada aquí confundiría «toca ahora» con «toca el día 25».
    next_review_at: datetime | None = None

    @property
    def questions_total(self) -> int:
        return sum(cantidad for _, cantidad in self.questions_by_status)


@dataclass(frozen=True, slots=True)
class ExportView:
    """El resultado de una exportación: el fichero escrito y lo que hay que saber de él."""

    path: str
    filename: str
    format: str
    bytes: int
    item_count: int
    documents: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    provenance: dict[str, Any] = field(default_factory=dict)
