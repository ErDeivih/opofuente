"""Esquemas de búsqueda y RAG (08_API-CONTRACT §8).

Dos cosas que el contrato tiene que dejar claras y que estos esquemas declaran:

1. **una cita es abrible**: cada fragmento viaja con documento, versión, sección, página y etiqueta,
   no solo con su texto. Una cita sin sitio no se puede comprobar;
2. **una respuesta dice con qué se hizo**: estado (`supported`/`partial`/`insufficient`), proveedor,
   modelo, revisión del corpus y las incertidumbres. Nada de eso es decorativo: es lo que permite
   auditar por qué la aplicación dijo lo que dijo.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field

AnswerStatusName = Literal["supported", "partial", "insufficient"]
StrategyName = Literal["lexical", "hybrid"]
VersionModeName = Literal["current", "explicit_historical"]
StyleName = Literal["brief", "teach", "compare"]
SupportName = Literal["direct", "inferred"]


class SearchRequestSchema(BaseModel):
    """Lo que se manda para buscar (o para preguntar)."""

    query: str = Field(min_length=1)
    opposition_id: str | None = None
    convocation_id: str | None = None
    curriculum_node_ids: list[str] = Field(default_factory=list)
    document_ids: list[str] = Field(default_factory=list)
    authority_tier: str | None = None
    reference_date: date | None = None
    version_mode: VersionModeName = "current"
    languages: list[str] = Field(default_factory=list)
    strategy: StrategyName = "lexical"
    limit: int = Field(default=10, ge=1, le=50)


class AskRequestSchema(SearchRequestSchema):
    """La consulta de RAG añade el estilo y si se admite material privado."""

    style: StyleName = "brief"
    allow_private_sources: bool = True


class EvidenceSpanSchema(BaseModel):
    """Un fragmento de evidencia con lo necesario para abrirlo."""

    id: str
    document_id: str
    document_version_id: str
    document_title: str
    document_type: str
    authority_tier: str | None = None
    version_status: str
    section_id: str | None = None
    section_title: str | None = None
    citation_label: str | None = None
    page: int | None = None
    page_start: int | None = None
    page_end: int | None = None
    ordinal: int
    text: str


class SearchHitSchema(BaseModel):
    span: EvidenceSpanSchema
    rank: int
    score: float
    strategy: StrategyName
    matched_terms: list[str]


class SearchResultSchema(BaseModel):
    """Lo que devuelve una búsqueda: resultados, estrategia y lo que no se pudo hacer."""

    hits: list[SearchHitSchema]
    total: int
    strategy: StrategyName
    strategies: list[StrategyName]
    corpus_revision: str
    version_mode: VersionModeName
    degradations: list[str]
    excluded: list[str]


class ClaimSchema(BaseModel):
    """Una afirmación con las citas que la sostienen."""

    text: str
    support: SupportName
    evidence: list[EvidenceSpanSchema]


class AnswerSchema(BaseModel):
    """La respuesta con sus afirmaciones citadas y sus incertidumbres."""

    id: str
    query_id: str
    status: AnswerStatusName
    short_answer: str
    explanation: str
    claims: list[ClaimSchema]
    uncertainties: list[str]
    suggested_followups: list[str]
    provider: str
    model: str | None = None
    prompt_template_version: str | None = None
    created_at: datetime | None = None


class RagQuerySchema(BaseModel):
    """Una consulta de RAG guardada, con su respuesta y la revisión del corpus que usó."""

    id: str
    question: str
    strategy: StrategyName
    version_mode: VersionModeName
    corpus_revision: str
    provider: str
    model: str | None = None
    prompt_template_version: str | None = None
    created_at: datetime | None = None
    answer: AnswerSchema | None = None


class RetrievalHitSchema(BaseModel):
    span: EvidenceSpanSchema
    rank: int
    score: float
    strategy: StrategyName
    used: bool


class RetrievalSchema(BaseModel):
    """La recuperación completa: todo lo que se encontró, se usara o no (§5, paso 9)."""

    query_id: str
    corpus_revision: str
    hits: list[RetrievalHitSchema]
    used_ids: list[str]
