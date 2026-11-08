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

#: Modos que el contrato acepta: los cinco que la aplicación **sabe construir y corregir** de
#: verdad (06_QUESTIONS §5). El vocabulario del modelo y el del contrato vuelven a coincidir al
#: cerrar
#: DEBT-012: `mock_exam` monta el perfil exacto sin llamarse oficial y `diagnostic` compone una
#: muestra estratificada por tema y la lee con su intervalo.
SessionModeName = Literal[
    "practice", "error_review", "official_exam", "mock_exam", "diagnostic", "block_practice"
]
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
    #: En el repaso de errores la composición la pone la cola de repaso (S10), así que no se eligen
    #: conjuntos a mano: por eso la lista puede ir vacía.
    sources: list[SessionSourceSchema] = Field(default_factory=list)
    convocation_version_id: str | None = None
    feedback: FeedbackName | None = None
    shuffle: bool = False
    time_limit_minutes: int | None = Field(default=None, ge=1)
    review_limit: int | None = Field(
        default=None,
        ge=1,
        le=50,
        description="Solo en `error_review`: cuántas preguntas vencidas entran como mucho.",
    )
    block_node_id: str | None = Field(
        default=None,
        description=(
            "Solo en `block_practice`: bloque del temario común del que salen las preguntas "
            "aceptadas de sus temas."
        ),
    )
    block_limit: int | None = Field(
        default=None,
        ge=1,
        le=200,
        description=(
            "Solo en `block_practice`: cuántas preguntas entran como mucho. Sin valor, todas las "
            "aceptadas del bloque."
        ),
    )


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
    #: Lo que la composición dice de sí misma: cuántas preguntas de un simulacro se habían visto
    #: hace poco, de qué temas salió la muestra de un diagnóstico (DEBT-012).
    note: str | None = None


class IntervalSchema(BaseModel):
    """Un intervalo de confianza sobre una muestra pequeña, con su nivel declarado."""

    low: float
    high: float
    confidence: float
    width: float


class DiagnosticTopicSchema(BaseModel):
    """Lo que se contestó de un tema en la muestra, con su intervalo y su aviso."""

    node_id: str
    title: str
    answered: int
    correct: int
    interval: IntervalSchema | None = None
    note: str


class DiagnosticReadingSchema(BaseModel):
    """La lectura de un diagnóstico: por tema y con el tamaño de la muestra delante.

    Los intervalos viajan **con** sus recuentos porque sin ellos no se pueden leer: un intervalo
    ancho
    sobre dos preguntas y uno estrecho sobre veinte no dicen lo mismo.
    """

    session_id: str
    mode: SessionModeName
    sample_size: int
    answered: int
    topics: list[DiagnosticTopicSchema]
    detail: str


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


class SessionRecalculationSchema(BaseModel):
    """Lo que cambió en una sesión al recalcularla en bloque (DEBT-013)."""

    session_id: str
    previous_total: str
    new_total: str
    previous_key_label: str
    new_key_label: str
    changed: bool


class BulkRecalculationSchema(BaseModel):
    """Recálculo en bloque: qué plantilla se usó, sesión por sesión, y cuántas cambiaron."""

    question_set_id: str
    key_version: int
    changed: int
    detail: str
    sessions: list[SessionRecalculationSchema]


class OutdatedSessionsSchema(BaseModel):
    """Sesiones terminadas del conjunto que no están corregidas con su plantilla activa (DEBT-013).

    Los tres recuentos —al día, desactualizadas y sin corrección guardada— suman las terminadas: si
    se solaparan, el número que la pantalla enseña no se podría comprobar.
    """

    question_set_id: str
    key_version: int
    key_id: str
    finished: int
    up_to_date: int
    outdated: int
    without_evaluation: int
    outdated_session_ids: list[str]
    detail: str


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
