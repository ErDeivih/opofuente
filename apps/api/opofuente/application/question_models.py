"""Modelos de lectura del banco de preguntas (S06): conjuntos, preguntas, opciones y claves.

La clave de una pregunta **no** viaja por defecto: `QuestionView.correct_option_keys` viene vacía
salvo que se pida explícitamente. El contrato §9 lo exige para las sesiones no corregidas («no
devolver claves ni explicaciones en el payload de pregunta de una sesión no corregida»), y la forma
más segura de cumplirlo es que el valor por defecto sea no llevarla: quien la necesite —el banco, el
editor— lo pide a propósito.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime


@dataclass(frozen=True, slots=True)
class OptionView:
    id: str
    stable_key: str
    text: str
    position: int
    label: str | None = None


@dataclass(frozen=True, slots=True)
class QuestionView:
    """Una pregunta con sus opciones y, si se ha pedido, su clave."""

    id: str
    question_set_id: str
    stable_key: str
    version_no: int
    stem: str
    question_type: str
    position: int
    status: str
    origin_type: str
    is_reserve: bool = False
    reserve_order: int | None = None
    source_section_id: str | None = None
    supersedes_id: str | None = None
    created_at: datetime | None = None
    options: tuple[OptionView, ...] = ()
    correct_option_keys: tuple[str, ...] = ()
    key_outcome: str | None = None
    explanation_count: int = 0

    @property
    def has_key(self) -> bool:
        return self.key_outcome is not None

    @property
    def option_count(self) -> int:
        return len(self.options)


@dataclass(frozen=True, slots=True)
class QuestionSetView:
    """Un conjunto con sus recuentos: es lo que se ve en el listado del banco."""

    id: str
    title: str
    set_type: str
    status: str
    opposition_id: str
    convocation_version_id: str | None = None
    model_code: str | None = None
    held_at: date | None = None
    source_document_version_id: str | None = None
    created_at: datetime | None = None
    question_count: int = 0
    reserve_count: int = 0
    incomplete_count: int = 0
    key_count: int = 0
    active_key_id: str | None = None

    @property
    def is_official(self) -> bool:
        return self.set_type == "official_exam"


@dataclass(frozen=True, slots=True)
class QuestionPage:
    questions: tuple[QuestionView, ...]
    total: int
    limit: int
    offset: int


@dataclass(frozen=True, slots=True)
class QuestionSetPage:
    sets: tuple[QuestionSetView, ...]
    total: int
    limit: int
    offset: int


@dataclass(frozen=True, slots=True)
class KeyEntryView:
    question_version_id: str
    outcome: str
    correct_option_keys: tuple[str, ...] = ()
    notes: str | None = None


@dataclass(frozen=True, slots=True)
class AnswerKeyView:
    id: str
    question_set_id: str
    version_no: int
    status: str
    source_document_version_id: str | None = None
    supersedes_id: str | None = None
    published_at: date | None = None
    approved_at: datetime | None = None
    created_at: datetime | None = None
    entries: tuple[KeyEntryView, ...] = ()

    @property
    def is_active(self) -> bool:
        return self.status == "active"

    @property
    def entry_count(self) -> int:
        return len(self.entries)


@dataclass(frozen=True, slots=True)
class SaveQuestionsOutcome:
    """Qué pasó al guardar un lote de preguntas: ni una se pierde en silencio."""

    created: int = 0
    existing: int = 0
    incomplete: int = 0
    question_ids: tuple[str, ...] = field(default_factory=tuple)

    @property
    def total(self) -> int:
        return self.created + self.existing


__all__ = [
    "AnswerKeyView",
    "KeyEntryView",
    "OptionView",
    "QuestionPage",
    "QuestionSetPage",
    "QuestionSetView",
    "QuestionView",
    "SaveQuestionsOutcome",
]
