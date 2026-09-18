"""Modelos de lectura de búsqueda y RAG (S09).

La cita de un fragmento lleva siempre lo que hace falta para **abrir el sitio correcto**: documento,
versión, sección, página y etiqueta. Una cita que no se puede abrir no sirve para comprobar nada, y
comprobar es justo lo que el producto promete.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from opofuente.domain.rag import AnswerStatus, ClaimSupport, SearchStrategy, VersionMode


@dataclass(frozen=True, slots=True)
class SpanView:
    """Un fragmento de evidencia, con su procedencia completa."""

    id: str
    document_version_id: str
    document_id: str
    document_title: str
    document_type: str
    authority_tier: str | None
    version_status: str
    section_id: str | None
    section_title: str | None
    citation_label: str | None
    page: int | None
    text: str
    ordinal: int
    page_start: int | None = None
    page_end: int | None = None


@dataclass(frozen=True, slots=True)
class SearchHitView:
    """Un resultado de búsqueda: el fragmento, su cita y por qué salió."""

    span: SpanView
    rank: int
    score: float
    strategy: SearchStrategy
    matched_terms: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class SearchOutcome:
    """Lo que devuelve una búsqueda: resultados, estrategia usada y lo que no se pudo hacer."""

    hits: tuple[SearchHitView, ...]
    strategy: SearchStrategy
    strategies: tuple[SearchStrategy, ...]
    corpus_revision: str
    version_mode: VersionMode
    degradations: tuple[str, ...] = ()
    excluded: tuple[str, ...] = ()
    total: int = 0

    @property
    def ids(self) -> tuple[str, ...]:
        return tuple(hit.span.id for hit in self.hits)


@dataclass(frozen=True, slots=True)
class ClaimView:
    """Una afirmación con las citas que la sostienen, ya resueltas a fragmentos abribles."""

    text: str
    support: ClaimSupport
    evidence: tuple[SpanView, ...]


@dataclass(frozen=True, slots=True)
class AnswerView:
    """La respuesta guardada, con sus afirmaciones citadas y sus incertidumbres."""

    id: str
    query_id: str
    status: AnswerStatus
    short_answer: str
    explanation: str
    claims: tuple[ClaimView, ...]
    uncertainties: tuple[str, ...]
    suggested_followups: tuple[str, ...]
    provider: str
    model: str | None
    prompt_template_version: str | None
    created_at: datetime | None = None

    @property
    def is_supported(self) -> bool:
        return self.status is AnswerStatus.SUPPORTED


@dataclass(frozen=True, slots=True)
class RagQueryView:
    """Una consulta guardada, con la revisión del corpus con la que se respondió."""

    id: str
    question: str
    strategy: SearchStrategy
    version_mode: VersionMode
    corpus_revision: str
    provider: str
    model: str | None
    prompt_template_version: str | None
    created_at: datetime | None = None
    answer: AnswerView | None = None


@dataclass(frozen=True, slots=True)
class RetrievalHitDetail:
    """Un fragmento recuperado: todos los que se guardaron, se usaran o no (§5 paso 9)."""

    span: SpanView
    rank: int
    score: float
    strategy: SearchStrategy
    used: bool


@dataclass(frozen=True, slots=True)
class RetrievalView:
    """La recuperación completa de una consulta."""

    query_id: str
    corpus_revision: str
    hits: tuple[RetrievalHitDetail, ...]
    used_ids: tuple[str, ...] = ()
    degradations: tuple[str, ...] = field(default_factory=tuple)
