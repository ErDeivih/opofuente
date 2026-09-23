"""DTO de oposiciones, convocatorias, programa y reglas de examen (08_API-CONTRACT §3).

Todos los datos que se publican vienen de los fixtures construidos desde fuentes oficiales
(ver `fixtures/profiles/manifest.json`). Lo que la convocatoria no publica se devuelve como
`null` y la interfaz debe mostrarlo como «no consta», no como un valor supuesto.
"""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel

from opofuente.domain.profiles import ConvocationStatus, NodeType, PartFormat, PartKind, RuleKind


class ConvocationReferenceSchema(BaseModel):
    id: str
    code: str
    title: str
    official_url: str
    published_at: date
    exam_date: date | None = None
    status: ConvocationStatus


class ActiveConvocationSchema(BaseModel):
    """Convocatoria activa de una oposición, en la forma mínima que necesita el selector."""

    id: str
    code: str
    published_at: date
    status: ConvocationStatus


class OppositionSchema(BaseModel):
    id: str
    code: str
    name: str
    description: str | None = None
    active: bool
    active_convocation: ActiveConvocationSchema | None = None


class OppositionDetailSchema(BaseModel):
    opposition: OppositionSchema
    convocations: list[ConvocationReferenceSchema]


class ExamPartSchema(BaseModel):
    code: str
    name: str
    kind: PartKind
    format: PartFormat | None = None
    position: int
    parent_code: str | None = None
    ordinary_items: int | None = None
    reserve_items: int | None = None
    options_per_question: int | None = None
    score_min: float | None = None
    score_max: float | None = None
    pass_score: float | None = None
    wrong_penalty_fraction: float | None = None
    fail_if_errors_gte: int | None = None
    time_minutes: int | None = None
    structure_note: str | None = None
    notes: str | None = None
    evidence_quote: str


class ExamRuleSchema(BaseModel):
    code: str
    kind: RuleKind
    value_text: str
    description: str
    evidence_quote: str


class ConvocationDetailSchema(BaseModel):
    id: str
    code: str
    title: str
    official_url: str
    published_at: date
    exam_date: date | None = None
    #: Por qué la fecha de ejercicio es esa, o por qué no hay ninguna (S12.2).
    exam_date_note: str | None = None
    status: ConvocationStatus
    source_reference: str | None = None
    opposition_id: str
    opposition_code: str
    opposition_name: str
    parts: list[ExamPartSchema]
    rules: list[ExamRuleSchema]


class CurriculumNodeSchema(BaseModel):
    id: str
    node_type: NodeType
    official_code: str
    title: str
    description: str | None = None
    position: int
    path: str
    depth: int
    children: list[CurriculumNodeSchema]


class CurriculumSchema(BaseModel):
    convocation_id: str
    convocation_code: str
    opposition_code: str
    counts: dict[str, int]
    nodes: list[CurriculumNodeSchema]


class CurriculumNodeDetailSchema(BaseModel):
    node: CurriculumNodeSchema
    convocation_id: str
    convocation_code: str
    convocation_title: str
    official_url: str
    published_at: date
    opposition_code: str
    opposition_name: str
    source_reference: str | None = None
    ancestors: list[CurriculumNodeSchema]
    coverage: None = None
    """La cobertura documental llega con la biblioteca (S05). Se declara nula a propósito: un
    cero haría creer que no hay material cuando lo que no existe todavía es el cálculo."""
