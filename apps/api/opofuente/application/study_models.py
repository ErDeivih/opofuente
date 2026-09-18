"""Modelos de lectura de las sesiones de estudio (S07).

Dos reglas de este fichero, y las dos son criterios de aceptación del slice:

1. **La solución no viaja por defecto.** `SessionQuestionView` lleva el enunciado y las opciones, y
   la corrección solo existe dentro de `CorrectionView`, que el servicio construye **únicamente**
   cuando se puede enseñar (corrección inmediata de una pregunta ya respondida, o sesión terminada).
   Una pregunta sin corregir no tiene forma de llevar la clave: el campo no está.
2. **La puntuación viaja exacta y decimal.** Toda puntuación se enseña como fracción (`1/3`) y como
   decimal redondeado (`0.3333`), y el valor exacto es el primero: el decimal es para leerlo
   (DEBT-006, ADR-010).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from fractions import Fraction

from opofuente.application.question_models import OptionView, QuestionEvidenceView
from opofuente.domain.study import (
    AttemptOutcome,
    Confidence,
    Feedback,
    SessionConfiguration,
    SessionMode,
    SessionStatus,
)


@dataclass(frozen=True, slots=True)
class ScoreView:
    """Una puntuación, exacta y legible. El decimal nunca sustituye a la fracción."""

    value: Fraction

    @property
    def fraction(self) -> str:
        return (
            str(self.value.numerator)
            if self.value.denominator == 1
            else f"{self.value.numerator}/{self.value.denominator}"
        )

    @property
    def decimal(self) -> str:
        from opofuente.domain.study import decimal_text

        return decimal_text(self.value)

    @property
    def numerator(self) -> int:
        return self.value.numerator

    @property
    def denominator(self) -> int:
        return self.value.denominator


@dataclass(frozen=True, slots=True)
class CorrectionView:
    """Lo que se puede enseñar de una pregunta **después** de corregirla.

    Existe solo cuando el servicio decide que se puede ver: es la pieza que impide que la solución
    se filtre en el payload de una sesión sin corregir.
    """

    outcome: str
    correct_option_keys: tuple[str, ...]
    score: ScoreView
    reason: str | None = None
    explanation: str | None = None
    evidence: tuple[QuestionEvidenceView, ...] = ()

    @property
    def is_correct(self) -> bool:
        return self.outcome == AttemptOutcome.CORRECT.value


@dataclass(frozen=True, slots=True)
class SessionQuestionView:
    """Una pregunta tal como se presenta: sin solución, con lo que marcó quien estudia."""

    session_question_id: str
    question_version_id: str
    stable_key: str
    position: int
    part_code: str | None
    is_reserve: bool
    reserve_order: int | None
    stem: str
    question_type: str
    origin_type: str
    options: tuple[OptionView, ...] = ()
    answered: bool = False
    chosen_option_keys: tuple[str, ...] = ()
    elapsed_ms: int | None = None
    confidence: Confidence | None = None
    correction: CorrectionView | None = None
    #: Desenlace **congelado** de la clave. No se serializa: solo decide si la corrección se puede
    #: calcular, y el contrato no lo expone en la pregunta de una sesión.
    frozen_outcome: str | None = None
    frozen_correct_keys: tuple[str, ...] = ()
    attempts_count: int = 0


@dataclass(frozen=True, slots=True)
class SessionView:
    """Una sesión con su configuración congelada y su progreso."""

    id: str
    mode: SessionMode
    status: SessionStatus
    feedback: Feedback
    opposition_id: str
    convocation_version_id: str | None
    question_set_id: str | None
    answer_key_version_id: str | None
    key_label: str | None
    configuration: SessionConfiguration
    time_limit_minutes: int | None
    total_questions: int
    answered_questions: int
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime
    result: SessionResultView | None = None

    @property
    def is_finished(self) -> bool:
        return self.status is SessionStatus.FINISHED

    @property
    def next_position(self) -> int | None:
        return (
            self.answered_questions + 1 if self.answered_questions < self.total_questions else None
        )


@dataclass(frozen=True, slots=True)
class SessionPage:
    sessions: tuple[SessionView, ...]
    total: int
    limit: int
    offset: int


@dataclass(frozen=True, slots=True)
class AttemptView:
    """Lo que se registró de una pregunta, con su evaluación si la tiene."""

    id: str
    session_question_id: str
    question_version_id: str
    chosen_option_keys: tuple[str, ...]
    elapsed_ms: int
    confidence: Confidence | None
    client_sequence: int | None
    answered_at: datetime
    outcome: str | None = None
    score: ScoreView | None = None
    reason: str | None = None


@dataclass(frozen=True, slots=True)
class AnswerOutcomeView:
    """Resultado de registrar una respuesta: si se guardó, si ya estaba y qué se puede enseñar.

    Incluye la **pregunta respondida** con su corrección (cuando se puede ver) porque la pantalla
    tiene que enseñar el resultado de lo que se acaba de contestar antes de pasar a la siguiente: el
    ciclo de 06_QUESTIONS §6 es responder, corregir y ver el resultado, no saltar de pregunta.
    """

    saved: bool
    already_answered: bool
    attempt: AttemptView
    session: SessionView
    question: SessionQuestionView
    correction: CorrectionView | None = None


@dataclass(frozen=True, slots=True)
class PartScoreView:
    """Puntuación directa de una parte, con los umbrales oficiales como datos declarados."""

    part_code: str | None
    part_name: str | None
    ordinary_items: int | None
    score_min: float | None
    score_max: float | None
    pass_score: float | None
    #: `None` solo en el total, cuando las partes no comparten penalización: no hay una sola que lo
    #: describa, y decir una sería inventarla.
    penalty: ScoreView | None
    correct: int
    wrong: int
    blank: int
    annulled: int
    excluded: int
    conflicting: int
    reserves_used: int
    unused_reserves: int
    score: ScoreView
    official_available: bool = False

    @property
    def graded(self) -> int:
        return self.correct + self.wrong + self.blank


@dataclass(frozen=True, slots=True)
class SubstitutionView:
    """Una pregunta anulada y la reserva que la sustituyó (o nada, si no había)."""

    annulled_question_version_id: str
    reserve_question_version_id: str | None


@dataclass(frozen=True, slots=True)
class SessionResultView:
    """Resultado agregado, tal como se calculó y se guardó: la composición efectiva incluida."""

    session_id: str
    mode: SessionMode
    answer_key_version_id: str | None
    key_label: str | None
    parts: tuple[PartScoreView, ...]
    total: PartScoreView
    substitutions: tuple[SubstitutionView, ...]
    unfinished: int
    official_available: bool
    official_note: str | None
    calculated_at: datetime | None = None

    @property
    def score(self) -> ScoreView:
        return self.total.score


@dataclass(frozen=True, slots=True)
class ReviewView:
    """La revisión de una sesión: cada pregunta con lo que se marcó y su corrección.

    `pending` cuenta las preguntas **respondidas** cuya corrección todavía no se puede ver (con
    corrección al final, hasta que la sesión termine); `unanswered`, las que no se respondieron. Son
    dos cosas distintas y se informan por separado: una espera corrección, la otra espera respuesta.
    """

    session: SessionView
    entries: tuple[SessionQuestionView, ...]
    partial: bool = False
    note: str | None = None
    pending: int = 0
    unanswered: int = 0
    extra: dict[str, object] = field(default_factory=dict)
