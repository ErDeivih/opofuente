"""DTO de la ficha de pregunta (F20, §4.2 del objetivo).

Tres decisiones que se ven en los esquemas y no son formato:

1. **la fiabilidad de la clave viaja con su fuente**: `key_reliability` (de la columna del §1) y
   `reliability_source` (de dónde se ha leído) van juntos. Un veredicto sin decir de dónde sale no
se
   puede distinguir de un cálculo hecho por la pantalla, y el §1 es el único que lo mantiene;
2. **lo que no se puede hacer se dice con el motivo**: `protection.reason` y `repair.por_que_no` son
   nulos solo cuando la acción **sí** es posible. La pantalla no tiene que adivinar por qué un botón
   está apagado;
3. **marcar la correcta exige las letras y admite el motivo**: `correct_option_keys` no tiene valor
por
   defecto —cambiar una respuesta correcta es un acto deliberado— y `note` es opcional porque el
   histórico ya guarda el antes y el después.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

#: El vocabulario de las letras que pueden venir como respuesta correcta. La base admite hasta ocho
#: opciones (`a`-`h`) y la validación de que existan en la pregunta la hace el dominio, que es
#: único que tiene delante las opciones.
OptionKeyName = Literal["a", "b", "c", "d", "e", "f", "g", "h"]


class QuestionFileOptionSchema(BaseModel):
    stable_key: str
    position: int
    text: str
    label: str | None


class QuestionFileKeySchema(BaseModel):
    """La respuesta correcta que manda hoy y **de dónde sale**."""

    answer_key_version_id: str
    version_no: int
    status: Literal["draft", "active", "superseded", "rejected"]
    outcome: Literal["keyed", "annulled", "unanswered", "conflicting"]
    correct_option_keys: list[str]
    approved_at: datetime | None
    published_at: date | None
    source_document_id: str | None
    source_document_title: str | None
    source_document_type: str | None
    source_version_label: str | None
    source_version_status: str | None
    notes: str | None


class QuestionFileNotesSchema(BaseModel):
    """Lo que contestan los apuntes, con el apartado y la frase verificada."""

    answer_letter: str | None
    expected_letters: list[str]
    result: Literal["covered", "gap", "doubtful", "conflict"] | None
    phrase: str | None
    anchor: str
    section_title: str | None
    topic_code: str
    topic_title: str
    key_status: Literal["active", "draft", "ninguna"]
    checked_at: datetime | None
    coincides: bool


class QuestionFileIncidentSchema(BaseModel):
    id: str
    category: Literal[
        "hueco_sin_material",
        "clave_sospechosa",
        "pregunta_ambigua",
        "norma_cambiada",
        "pregunta_mal_importada",
        "clave_no_fiable",
    ]
    reason: str
    status: Literal["open", "in_progress", "reviewed", "dismissed"]
    coverage: Literal["doubtful", "conflict"]
    detail: str
    phrase: str | None
    topic_code: str
    topic_title: str
    resolution_note: str | None
    reviewed_at: datetime | None


class QuestionFileExclusionSchema(BaseModel):
    reason: Literal["otra_administracion", "enunciado_roto"]
    note: str | None
    actor: str
    created_at: datetime


class QuestionFileVersionSchema(BaseModel):
    id: str
    version_no: int
    status: Literal["incomplete", "complete", "verified", "conflicting", "annulled", "superseded"]
    stem: str
    note: str | None
    created_at: datetime | None
    option_count: int
    correct_option_keys: list[str]


class QuestionFileKeyVersionSchema(BaseModel):
    id: str
    version_no: int
    status: Literal["draft", "active", "superseded", "rejected"]
    approved_at: datetime | None
    created_at: datetime | None
    source_document_title: str | None
    correct_option_keys: list[str]


class QuestionFileProtectedSetSchema(BaseModel):
    id: str
    title: str
    set_type: str
    source_document_title: str | None
    reason: str


class QuestionFileProtectionSchema(BaseModel):
    protected: bool
    reason: str | None
    sets: list[QuestionFileProtectedSetSchema]


class QuestionFileRepairSchema(BaseModel):
    reglas: list[str]
    titulos: list[str]
    detalle: str
    stem: str | None
    opciones: list[str] | None
    por_que_no: str | None


class QuestionFileSchema(BaseModel):
    """La ficha entera de una pregunta."""

    question_version_id: str
    question_set_id: str
    set_title: str
    set_type: Literal["official_exam", "private_bank", "practice", "generated_batch"]
    set_distribution: Literal["personal", "public"]
    stable_key: str
    version_no: int
    position: int
    question_type: Literal["single_choice", "multi_mark_error", "true_false", "free_text_reference"]
    status: Literal["incomplete", "complete", "verified", "conflicting", "annulled", "superseded"]
    origin_type: Literal["official", "private", "generated"]
    is_reserve: bool
    reserve_order: int | None
    created_at: datetime | None
    note: str | None
    stem: str
    options: list[QuestionFileOptionSchema]
    key: QuestionFileKeySchema | None
    key_reliability: Literal["fiable", "dudosa", "no_fiable"] | None
    reliability_source: str
    notes: list[QuestionFileNotesSchema]
    incidents: list[QuestionFileIncidentSchema]
    exclusion: QuestionFileExclusionSchema | None
    protection: QuestionFileProtectionSchema
    repair: QuestionFileRepairSchema
    versions: list[QuestionFileVersionSchema]
    keys: list[QuestionFileKeyVersionSchema]
    superseded_by: str | None


class MarkCorrectOptionSchema(BaseModel):
    """Marca la respuesta correcta de esta pregunta.

    `correct_option_keys` es **obligatorio y sin valor por defecto**: cambiar lo que se da por bueno
    es un acto deliberado, y admitir el cuerpo vacío dejaría la puerta abierta a una llamada que no
    dice qué quiere.
    """

    model_config = ConfigDict(extra="forbid")

    correct_option_keys: list[OptionKeyName] = Field(min_length=1)
    note: str | None = Field(default=None, max_length=500)
    actor: str | None = Field(default=None, max_length=64)


class MarkCorrectResultSchema(BaseModel):
    """Lo que devuelve marcar la correcta: la ficha al día y las dos plantillas.

    `superseded_key_version_id` viaja porque el hecho que hay que poder comprobar es que la anterior
    **no se ha pisado**: queda `superseded` y se puede leer.
    """

    file: QuestionFileSchema
    key_version_id: str
    superseded_key_version_id: str | None
    previous_option_keys: list[str]
    correct_option_keys: list[str]
    actor: str


class RepairQuestionSchema(BaseModel):
    """Repara lo que una regla mecánica pueda reparar de esta pregunta.

    No se manda texto: lo que se escribe lo decide una regla del dominio sobre el enunciado y las
    opciones que ya hay. `reglas` solo puede **restringir** lo que el dominio ofrece.
    """

    model_config = ConfigDict(extra="forbid")

    note: str = Field(min_length=1, max_length=500)
    reglas: list[str] | None = None
    actor: str | None = Field(default=None, max_length=64)


class RepairResultSchema(BaseModel):
    file: QuestionFileSchema
    new_question_version_id: str
    superseded_question_version_id: str
    reglas: list[str]
    key_version_id: str | None
    moved_topics: int
    moved_anchors: int
    moved_exclusion: bool
    dispatched_incidents: int
    actor: str


__all__ = [
    "MarkCorrectOptionSchema",
    "MarkCorrectResultSchema",
    "OptionKeyName",
    "QuestionFileExclusionSchema",
    "QuestionFileIncidentSchema",
    "QuestionFileKeySchema",
    "QuestionFileKeyVersionSchema",
    "QuestionFileNotesSchema",
    "QuestionFileOptionSchema",
    "QuestionFileProtectedSetSchema",
    "QuestionFileProtectionSchema",
    "QuestionFileRepairSchema",
    "QuestionFileSchema",
    "QuestionFileVersionSchema",
    "RepairQuestionSchema",
    "RepairResultSchema",
]
