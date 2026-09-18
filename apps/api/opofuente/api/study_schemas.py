"""Esquemas de las rutas de estudio (08_API-CONTRACT §10).

Lo que estos esquemas **no** tienen es tan importante como lo que tienen: la pregunta de una sesión
no declara ningún campo de solución. La clave solo puede aparecer dentro de `CorrectionSchema`, y el
servicio solo construye una corrección cuando se puede enseñar (corrección inmediata de algo ya
respondido, o sesión terminada). Así el contrato hace imposible filtrar la respuesta sin querer:
no hay campo donde ponerla.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from opofuente.api.question_schemas import OptionSchema, QuestionEvidenceSchema

SessionModeName = Literal["practice", "official_exam"]
SessionStatusName = Literal["draft", "running", "finished", "abandoned"]
FeedbackName = Literal["immediate", "at_end"]
ConfidenceName = Literal["low", "medium", "high"]
AttemptOutcomeName = Literal[
    "correct",
    "wrong",
    "blank",
    "annulled",
    "excluded",
    "conflicting",
    "unused_reserve",
]


class SessionSourceSchema(BaseModel):
    """De dónde salen las preguntas y qué parte del examen representan."""

    question_set_id: str
    part_code: str = Field(
        min_length=1,
        description=(
            "Parte de la convocatoria con la que se corrige. Es obligatoria: la penalización y los "
            "umbrales los publica la convocatoria, no el cliente."
        ),
    )
    count: int | None = Field(
        default=None,
        ge=1,
        description="Cuántas preguntas ordinarias se quieren (solo en práctica).",
    )
    include_reserves: bool = True


class CreateSessionSchema(BaseModel):
    """Lo que se manda para montar una sesión."""

    opposition_id: str
    mode: SessionModeName
    sources: list[SessionSourceSchema] = Field(min_length=1)
    convocation_version_id: str | None = None
    feedback: FeedbackName | None = None
    shuffle: bool = False
    time_limit_minutes: int | None = Field(default=None, ge=1)


class ScoreSchema(BaseModel):
    """Una puntuación: la fracción exacta y su decimal, que es solo para leerla."""

    numerator: int
    denominator: int = Field(gt=0)
    fraction: str
    decimal: str


class CorrectionSchema(BaseModel):
    """La corrección de una pregunta. **Aquí y solo aquí** viaja la solución."""

    outcome: AttemptOutcomeName
    correct_option_keys: list[str]
    score: ScoreSchema
    reason: str | None = None
    explanation: str | None = None
    evidence: list[QuestionEvidenceSchema]


class SessionQuestionSchema(BaseModel):
    """Una pregunta de la sesión, sin solución: enunciado, opciones y lo que se marcó."""

    session_question_id: str
    question_version_id: str
    stable_key: str
    position: int
    part_code: str | None = None
    is_reserve: bool
    reserve_order: int | None = None
    stem: str
    question_type: str
    origin_type: str
    options: list[OptionSchema]
    answered: bool
    chosen_option_keys: list[str]
    elapsed_ms: int | None = None
    confidence: ConfidenceName | None = None
    correction: CorrectionSchema | None = None


class SessionConfigurationSchema(BaseModel):
    """La configuración congelada al crear la sesión."""

    mode: SessionModeName
    feedback: FeedbackName
    time_limit_minutes: int | None = None
    shuffle: bool
    sources: list[SessionSourceSchema]


class PartScoreSchema(BaseModel):
    """Puntuación de una parte, con su forma de cálculo y los umbrales como datos declarados."""

    part_code: str | None = None
    part_name: str | None = None
    ordinary_items: int | None = None
    score_min: float | None = None
    score_max: float | None = None
    pass_score: float | None = None
    penalty: ScoreSchema | None = None
    kind: Literal["direct", "scaled", "pass_fail"]
    correct: int
    wrong: int
    blank: int
    annulled: int
    excluded: int
    conflicting: int
    reserves_used: int
    unused_reserves: int
    score: ScoreSchema
    passed: bool | None = None
    verdict_note: str | None = None
    official_available: bool


class SubstitutionSchema(BaseModel):
    """Una pregunta anulada y la reserva que la sustituyó."""

    annulled_question_version_id: str
    reserve_question_version_id: str | None = None


class RecalculationSchema(BaseModel):
    """Qué se dijo antes de recalcular con una clave nueva, y qué cambió (S08).

    Recalcular no borra el resultado anterior: la interfaz puede explicar «tu puntuación cambió de X
    a Y por la plantilla oficial v2» en lugar de que la cifra cambie sola.
    """

    previous_total: ScoreSchema
    previous_parts: list[PartScoreSchema]
    previous_key_label: str | None = None
    recalculated_at: datetime | None = None
    changed: bool
    note: str


class SessionResultSchema(BaseModel):
    """El resultado de una sesión, tal como se calculó y se guardó."""

    session_id: str
    mode: SessionModeName
    answer_key_version_id: str | None = None
    key_label: str | None = None
    parts: list[PartScoreSchema]
    total: PartScoreSchema
    substitutions: list[SubstitutionSchema]
    unfinished: int
    official_available: bool
    official_note: str | None = None
    calculated_at: datetime | None = None
    recalculation: RecalculationSchema | None = None


class SessionSchema(BaseModel):
    """Una sesión con su configuración congelada y su progreso."""

    id: str
    mode: SessionModeName
    status: SessionStatusName
    feedback: FeedbackName
    opposition_id: str
    convocation_version_id: str | None = None
    question_set_id: str | None = None
    answer_key_version_id: str | None = None
    key_label: str | None = None
    configuration: SessionConfigurationSchema
    time_limit_minutes: int | None = None
    total_questions: int
    answered_questions: int
    started_at: datetime | None = None
    finished_at: datetime | None = None
    created_at: datetime
    result: SessionResultSchema | None = None


class SessionPageSchema(BaseModel):
    sessions: list[SessionSchema]
    total: int
    limit: int
    offset: int


class CurrentQuestionSchema(BaseModel):
    """Qué pregunta toca y cómo va la sesión."""

    session: SessionSchema
    question: SessionQuestionSchema | None = None
    answered: int
    total: int
    pending: int
    finished: bool


class AnswerRequestSchema(BaseModel):
    """La respuesta a una pregunta: qué se marcó, cuánto se tardó y con qué confianza."""

    question_version_id: str
    chosen_option_keys: list[str] = Field(default_factory=list)
    elapsed_ms: int = Field(default=0, ge=0)
    confidence: ConfidenceName | None = None
    client_sequence: int | None = Field(default=None, ge=0)


class AttemptSchema(BaseModel):
    """Un intento: lo que se marcó y, si ya se corrigió, su desenlace."""

    id: str
    session_question_id: str
    question_version_id: str
    chosen_option_keys: list[str]
    elapsed_ms: int
    confidence: ConfidenceName | None = None
    client_sequence: int | None = None
    answered_at: datetime
    outcome: AttemptOutcomeName | None = None
    score: ScoreSchema | None = None
    reason: str | None = None


class AnswerOutcomeSchema(BaseModel):
    """Qué ha pasado al registrar una respuesta, con la corrección si se puede enseñar.

    Lleva la **pregunta respondida**: la pantalla enseña el resultado de lo que se acaba de
    contestar antes de pasar a la siguiente, y esa pregunta es la que trae su corrección.
    """

    saved: bool
    already_answered: bool
    attempt: AttemptSchema
    session: SessionSchema
    question: SessionQuestionSchema
    correction: CorrectionSchema | None = None


class NavigateRequestSchema(BaseModel):
    """A dónde se navega: a una posición o al siguiente/anterior."""

    position: int | None = Field(default=None, ge=1)
    direction: Literal["next", "previous"] | None = None


class ReviewSchema(BaseModel):
    """La revisión: cada pregunta con lo que se marcó y su corrección cuando se puede ver."""

    session: SessionSchema
    entries: list[SessionQuestionSchema]
    partial: bool
    note: str | None = None
    pending: int
    unanswered: int
