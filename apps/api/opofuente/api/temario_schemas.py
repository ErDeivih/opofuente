"""DTO del temario común, sus referencias, particularidades y avance (B-004).

El alumno ve el temario: la respuesta no expone cómo se calcula el avance, solo los recuentos que
necesita para decidir qué estudiar (DOCTRINA-CALIDAD §8). `coverage` se declara nulo a propósito,
como en el programa: un cero haría creer que no hay material cuando lo que no existe es el cálculo.
"""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field

from opofuente.api.profile_schemas import CurriculumNodeSchema
from opofuente.domain.profiles import NodeType


class CurriculumVersionSchema(BaseModel):
    code: str
    version_no: int
    title: str
    status: str


class CurriculumSummarySchema(BaseModel):
    code: str
    name: str
    kind: str
    group_code: str | None = None
    family: str | None = None
    versions: list[CurriculumVersionSchema]
    active_version: CurriculumVersionSchema | None = None


class BlockProgressSchema(BaseModel):
    block_id: str
    path: str
    title: str
    position: int
    topics_total: int
    topics_studied: int
    topics_with_activity: int
    percent: float


class ProgressSchema(BaseModel):
    curriculum_code: str
    version_code: str
    blocks: list[BlockProgressSchema]
    topics_total: int
    topics_studied: int
    topics_with_activity: int
    percent: float


class CurriculumDetailSchema(BaseModel):
    code: str
    name: str
    kind: str
    group_code: str | None = None
    family: str | None = None
    versions: list[CurriculumVersionSchema]
    active_version: CurriculumVersionSchema | None = None
    counts: dict[str, int]
    nodes: list[CurriculumNodeSchema]
    progress: ProgressSchema | None = None


class AdjustmentSchema(BaseModel):
    kind: str
    weight: float | None = None
    official_code_override: str | None = None
    title_override: str | None = None
    evidence_quote: str


class AppearanceSchema(BaseModel):
    convocation_id: str
    convocation_code: str
    convocation_title: str
    role: str
    source_reference: str | None = None
    omitted: bool
    adjustments: list[AdjustmentSchema]


class CurriculumIdentitySchema(BaseModel):
    code: str
    name: str
    kind: str
    version_code: str
    version_title: str


class ConvocationIdentitySchema(BaseModel):
    id: str
    code: str
    title: str
    official_url: str
    published_at: date
    opposition_code: str
    opposition_name: str
    source_reference: str | None = None


class CurriculumNodeDetailSchema(BaseModel):
    node: CurriculumNodeSchema
    curriculum: CurriculumIdentitySchema
    convocation: ConvocationIdentitySchema | None = None
    appears_in: list[AppearanceSchema] = Field(default_factory=list)
    particularities: list[AdjustmentSchema] = Field(default_factory=list)
    studied_at: datetime | None = None
    ancestors: list[CurriculumNodeSchema] = Field(default_factory=list)
    coverage: None = None
    """La cobertura documental llega con la biblioteca (S05); se declara nula a propósito."""


class TemarioSchema(BaseModel):
    convocation: ConvocationIdentitySchema
    curriculum: CurriculumIdentitySchema
    version: CurriculumVersionSchema
    counts: dict[str, int]
    nodes: list[CurriculumNodeSchema]
    omitted_topics: int


class CurriculumReferenceSchema(BaseModel):
    role: str
    curriculum_code: str
    curriculum_name: str
    curriculum_kind: str
    version_code: str
    version_no: int
    version_title: str
    source_reference: str | None = None


class StudyMarkSchema(BaseModel):
    node_id: str
    studied_at: datetime


#: Re-exporta el tipo de nodo para que el esquema OpenAPI lo documente junto al temario.
__all__ = ["CurriculumNodeSchema", "NodeType"]
