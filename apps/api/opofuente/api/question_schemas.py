"""DTO del banco de preguntas (08_API-CONTRACT §9).

Dos cosas que se ven en los esquemas y son decisiones, no formato:

1. **La clave no viaja salvo que se pida.** `QuestionSchema.correct_option_keys` viene vacía en las
   respuestas que no la piden a propósito, y el contrato lo exige para las sesiones no corregidas.
2. **Una corrección local lleva motivo obligatorio.** `LocalCorrectionSchema.note` no tiene valor
   por defecto: si alguien cambia una transcripción oficial, tiene que decir por qué.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class QuestionSetSchema(BaseModel):
    id: str
    title: str
    set_type: Literal["official_exam", "private_bank", "practice", "generated_batch"]
    status: Literal["draft", "confirmed", "archived"]
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
    is_official: bool = False


class QuestionSetPageSchema(BaseModel):
    sets: list[QuestionSetSchema]
    total: int
    limit: int
    offset: int


class CreateQuestionSetSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=300)
    opposition_id: str = Field(min_length=1)
    set_type: Literal["official_exam", "private_bank", "practice", "generated_batch"]
    convocation_version_id: str | None = None
    model_code: str | None = Field(default=None, max_length=8)
    held_at: date | None = None
    source_document_version_id: str | None = None


class OptionSchema(BaseModel):
    id: str
    stable_key: str
    label: str | None = None
    text: str
    position: int


class QuestionSchema(BaseModel):
    id: str
    question_set_id: str
    stable_key: str
    version_no: int
    stem: str
    question_type: Literal["single_choice", "multi_mark_error", "true_false", "free_text_reference"]
    position: int
    status: Literal["incomplete", "complete", "verified", "conflicting", "annulled", "superseded"]
    origin_type: Literal["official", "private", "generated"]
    is_reserve: bool = False
    reserve_order: int | None = None
    source_section_id: str | None = None
    supersedes_id: str | None = None
    created_at: datetime | None = None
    #: Motivo de la corrección local: quien lee la pregunta tiene que ver por qué cambió.
    note: str | None = None
    #: Las listas son **obligatorias** aunque puedan estar vacías: el servidor siempre las calcula,
    #: y declararlas opcionales obligaría a cada cliente a defenderse de un caso que no ocurre.
    options: list[OptionSchema]
    correct_option_keys: list[str]
    key_outcome: Literal["keyed", "annulled", "unanswered", "conflicting"] | None = None
    explanation_count: int = 0


class QuestionPageSchema(BaseModel):
    questions: list[QuestionSchema]
    total: int
    limit: int
    offset: int


class PatchQuestionSchema(BaseModel):
    """Cambia lo que se puede cambiar sin tocar el texto importado: una corrección es otra cosa."""

    model_config = ConfigDict(extra="forbid")

    stem: str | None = Field(default=None, min_length=1)
    question_type: (
        Literal["single_choice", "multi_mark_error", "true_false", "free_text_reference"] | None
    ) = None
    position: int | None = Field(default=None, ge=1)
    is_reserve: bool | None = None
    reserve_order: int | None = Field(default=None, ge=1)


class LocalCorrectionSchema(BaseModel):
    """Corrección local de una transcripción: **con motivo** y sin tocar el original importado."""

    model_config = ConfigDict(extra="forbid")

    note: str = Field(min_length=3, max_length=1000)
    stem: str | None = Field(default=None, min_length=1)
    options: list[str] | None = None


class CsvMappingSchema(BaseModel):
    stem: str = "stem"
    options: list[str] = Field(
        default_factory=lambda: ["option_a", "option_b", "option_c", "option_d"]
    )
    correct: str | None = "correct"
    explanation: str | None = "explanation"
    topic: str | None = "topic"
    source: str | None = "source"
    tags: str | None = "tags"
    position: str | None = None
    reserve: str | None = None


class ParseQuestionSetSchema(BaseModel):
    """Lo que se pide al importar: preguntas de un texto, un CSV, un JSON o una plantilla suelta."""

    model_config = ConfigDict(extra="forbid")

    kind: Literal["questions", "answer_key", "csv", "json"] = "questions"
    text: str = Field(min_length=1)
    mapping: CsvMappingSchema | None = None
    source_document_version_id: str | None = None


class RejectedRowSchema(BaseModel):
    row_number: int
    cause: str
    detail: str


class ParseIssueSchema(BaseModel):
    line: int
    code: str
    detail: str


class DuplicateGroupSchema(BaseModel):
    kind: Literal["same_question", "reordered_options", "similar"]
    members: list[str]
    conflicting_keys: bool = False
    keys_seen: list[str]
    can_merge: bool = False


class QuestionImportReportSchema(BaseModel):
    """Lo que ha pasado al importar: ni una fila se pierde, ni un conflicto se esconde.

    Se llama `QuestionImportReport` y no `ImportReport` porque la ingestión ya tiene su propio
    `ImportReportSchema` (el cuadre del lote): dos modelos con el mismo nombre obligan a FastAPI a
    inventar nombres cualificados en el OpenAPI y rompen los tipos derivados del contrato.
    """

    set_id: str
    created: int = 0
    existing: int = 0
    incomplete: int = 0
    with_key: int = 0
    key_entries: int = 0
    keys_in_conflict: int = 0
    #: Preguntas que quedaron **catalogadas por bloque y tema** al heredar el programa del documento
    #: del que salen (S12.6). Sin ese mapeo, el diagnóstico por temas no las vería.
    mapped_to_topics: int = 0
    #: Listas obligatorias: «sin filas rechazadas» se dice con una lista vacía, no con un ausente.
    rejected: list[RejectedRowSchema]
    issues: list[ParseIssueSchema]
    duplicates: list[DuplicateGroupSchema]
    missing_columns: list[str]
    ignored_columns: list[str]
    unmatched_positions: list[int]
    model_code_detected: str | None = None
    key_id: str | None = None
    #: Rótulos de parte vistos en el material. Se declaran y **no** se guardan por pregunta
    #: (ADR-014): lo que no se hace es perderlos en silencio (DEBT-010, criterio 3).
    parts_detected: list[str] = Field(default_factory=list)
    #: Citas creadas al importar desde un documento: el enlace pregunta↔fragmento (DEBT-010).
    evidence_links: int = 0
    #: Explicaciones **por opción** guardadas al importar (S12.7): el material las traía y se dice.
    option_explanations: int = 0


class ImportQuestionsFromDocumentSchema(BaseModel):
    """Importar las preguntas de una **versión de documento** (DEBT-010)."""

    model_config = ConfigDict(extra="forbid")

    document_version_id: str = Field(min_length=1)


class KeyEntrySchema(BaseModel):
    question_version_id: str
    outcome: Literal["keyed", "annulled", "unanswered", "conflicting"]
    correct_option_keys: list[str] = Field(default_factory=list)
    notes: str | None = None


class AnswerKeySchema(BaseModel):
    id: str
    question_set_id: str
    version_no: int
    status: Literal["draft", "active", "superseded", "rejected"]
    source_document_version_id: str | None = None
    supersedes_id: str | None = None
    published_at: date | None = None
    approved_at: datetime | None = None
    created_at: datetime | None = None
    entries: list[KeyEntrySchema]


class MarkKeySupersedesRequestSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    superseded_id: str = Field(min_length=1)


class IssueReportRequestSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: Literal["ambiguous", "wrong_key", "typo", "outdated", "other"]
    detail: str = Field(min_length=3, max_length=2000)


class IssueReportSchema(BaseModel):
    id: str
    question_version_id: str
    kind: Literal["ambiguous", "wrong_key", "typo", "outdated", "other"]
    detail: str
    status: Literal["open", "reviewed", "dismissed"]
    created_at: datetime | None = None


class ExplanationSchema(BaseModel):
    """Explicación de una pregunta entera o de una de sus opciones (07_UI-UX §7, S12.7).

    `option_stable_key` nulo es «la pregunta entera»; con valor, es la explicación de esa opción
    («por qué la b no vale»). El origen y el estado no son adorno: una explicación generada por un
    modelo queda en borrador y se dice con qué modelo se escribió.
    """

    id: str
    question_version_id: str
    option_stable_key: str | None = None
    text: str
    origin: Literal["official", "private", "generated"]
    status: Literal["draft", "reviewed", "rejected"]
    model_name: str | None = None
    created_at: datetime | None = None


class SetExplanationRequestSchema(BaseModel):
    """Escribir (o sustituir) la explicación de una pregunta o de una de sus opciones."""

    model_config = ConfigDict(extra="forbid")

    text: str = Field(min_length=1, max_length=4000)
    option_stable_key: str | None = Field(default=None, max_length=16)


class QuestionEvidenceSchema(BaseModel):
    span_id: str
    role: Literal["stem", "correct", "distractor", "explanation"]
    claim: str | None = None
    status: Literal["proposed", "accepted", "rejected"]
    text: str
    page: int | None = None
    citation_label: str | None = None
    document_version_id: str
    section_id: str | None = None


class CorrectionOutcomeSchema(BaseModel):
    """La versión corregida y, si la tenía, la plantilla nueva que apunta a ella."""

    question: QuestionSchema
    key_id: str | None = None
