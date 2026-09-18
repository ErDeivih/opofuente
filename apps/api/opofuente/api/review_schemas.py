"""Esquemas de errores, repaso y dominio (S10).

Tres cosas que estos esquemas **no** hacen: no aceptan la causa de un fallo como texto libre (el
vocabulario es cerrado), no dejan declarar el resultado de un repaso sin decir cuál fue, y no
esconden el recuento de intentos: la estimación de dominio viaja siempre con sus números.
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, Field

ErrorCauseName = Literal[
    "knowledge", "confusion", "reading", "time", "calculation", "ambiguous", "other"
]
ErrorStatusName = Literal["open", "resolved"]
ReviewOutcomeName = Literal["correct", "wrong"]
ReviewEventKindName = Literal["created", "attempt", "reviewed", "snoozed"]
ConfidenceName = Literal["low", "medium", "high"]
MasteryLevelName = Literal["no_data", "insufficient_evidence", "low", "medium", "high"]

NoteText = Annotated[str, Field(max_length=2000)]


class ReviewItemSchema(BaseModel):
    """El estado de repaso de una pregunta."""

    id: str
    question_version_id: str
    opposition_id: str
    learning_error_id: str | None = None
    due_at: datetime
    interval_days: int
    repetitions: int
    lapses: int
    last_reviewed_at: datetime | None = None
    last_reason: str | None = None
    created_at: datetime
    updated_at: datetime


class ReviewEventSchema(BaseModel):
    """Un paso del historial: de qué fecha a qué fecha, con qué resultado y por qué."""

    id: str
    kind: ReviewEventKindName
    outcome: ReviewOutcomeName | None = None
    confidence: ConfidenceName | None = None
    cause: ErrorCauseName | None = None
    note: str | None = None
    previous_due_at: datetime | None = None
    due_at: datetime
    previous_interval_days: int | None = None
    interval_days: int
    repetitions: int
    reason: str
    occurred_at: datetime


class DueItemSchema(BaseModel):
    """Una pregunta vencida, con su motivo y sus opciones para poder repasarla."""

    review: ReviewItemSchema
    question_version_id: str
    question_set_id: str
    stable_key: str
    stem: str
    part_code: str | None = None
    is_reserve: bool
    origin_type: str
    overdue_days: int
    explanation: str
    options: list[DueOptionSchema]
    session_id: str


class DueOptionSchema(BaseModel):
    """Una opción de la pregunta que toca repasar (sin decir cuál es la correcta)."""

    stable_key: str
    text: str


class ReviewStatsSchema(BaseModel):
    """Cuánto queda por repasar."""

    active: int
    due: int
    next_due_at: datetime | None = None
    lapses: int


class ErrorSchema(BaseModel):
    """Un fallo con la causa declarada y su procedencia (pregunta, sesión y parte)."""

    id: str
    attempt_id: str
    question_version_id: str | None = None
    stable_key: str | None = None
    stem: str | None = None
    session_id: str | None = None
    part_code: str | None = None
    curriculum_node_id: str | None = None
    node_title: str | None = None
    concept_label: str | None = None
    cause: ErrorCauseName
    user_note: str | None = None
    status: ErrorStatusName
    occurrences: int
    first_seen_at: datetime
    last_seen_at: datetime
    resolved_at: datetime | None = None


class ErrorDetailSchema(BaseModel):
    """Un error con su intento, su repaso y el historial de ese repaso."""

    error: ErrorSchema
    chosen_option_keys: list[str]
    confidence: ConfidenceName | None = None
    answered_at: datetime | None = None
    review: ReviewItemSchema | None = None
    events: list[ReviewEventSchema]


class ConceptSchema(BaseModel):
    """Un concepto con los fallos que agrupa."""

    key: str
    label: str
    node_id: str | None = None
    open_count: int
    resolved_count: int
    occurrences: int
    last_seen_at: datetime
    errors: list[ErrorSchema]


class ConceptGroupSchema(BaseModel):
    """La vista `Conceptos`: los grupos y sus totales."""

    groups: list[ConceptSchema]
    total_errors: int
    open_errors: int


class ReviewQueueSchema(BaseModel):
    """La vista `Hoy`: la cola ordenada, sus cifras, los conceptos y lo que no se puede decir."""

    items: list[DueItemSchema]
    stats: ReviewStatsSchema
    concepts: list[ConceptSchema]
    notes: list[str]


class ErrorClassificationSchema(BaseModel):
    """Lo que se declara de un fallo: por qué, sobre qué concepto y con qué nota."""

    cause: ErrorCauseName
    concept_label: str | None = Field(default=None, max_length=200)
    curriculum_node_id: str | None = None
    note: NoteText | None = None


class CompleteReviewSchema(BaseModel):
    """El resultado **declarado** de un repaso hecho fuera de una sesión."""

    outcome: ReviewOutcomeName
    confidence: ConfidenceName | None = None
    cause: ErrorCauseName | None = None
    note: NoteText | None = None


class SnoozeReviewSchema(BaseModel):
    """Aplazar un repaso sin contarlo como repasado."""

    days: int = Field(ge=1, le=90)


class MasterySchema(BaseModel):
    """El dominio estimado de un nodo, con sus recuentos y su explicación."""

    level: MasteryLevelName
    attempts: int
    correct: int
    recent_attempts: int
    accuracy: float | None = None
    explanation: str
    has_estimate: bool


class ResolveErrorSchema(BaseModel):
    """Resolver un error: `resolved` o volver a abrirlo, con la nota de por qué."""

    resolved: bool = True
    note: NoteText | None = None


DueItemSchema.model_rebuild()
