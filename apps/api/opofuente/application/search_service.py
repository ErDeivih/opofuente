"""Servicio de búsqueda y RAG (S09): recuperar con filtros y responder con citas.

Lo que vive aquí y no en el repositorio:

1. **la decisión de qué se puede responder**: se recupera, se fusiona, se diversifica y se
   compone la respuesta **extractiva**; el repositorio solo guarda y sirve datos.
2. **la degradación declarada**: sin proveedor de embeddings la búsqueda es léxica y el
   servicio lo dice en su respuesta, en lugar de devolver menos resultados en silencio
   (`05_RAG §5`).
3. **la invariante de citas**: antes de guardar una respuesta se comprueba que todas sus citas son
   fragmentos entregados (`assert_grounded`). Si no, no se guarda como respaldada.
4. **la trazabilidad**: se guardan la consulta, **todos** los fragmentos recuperados (marcando los
   usados) y la respuesta con la evidencia de cada afirmación, con la revisión del corpus con la que
   se respondió.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from opofuente.application.ports import Clock, VectorSearch
from opofuente.application.search_models import (
    AnswerView,
    RagQueryView,
    RetrievalView,
    SearchHitView,
    SearchOutcome,
    SpanView,
)
from opofuente.domain.errors import InvariantViolationError, NotFoundError
from opofuente.domain.rag import (
    CandidateSpan,
    SearchFilters,
    SearchStrategy,
    VersionMode,
    assert_grounded,
    compose_extractive_answer,
    fuse_candidates,
    match_expression,
    significant_terms,
)
from opofuente.infrastructure.search_repository import SqlAlchemySearchRepository

#: Cuántos fragmentos se recuperan por defecto y cuántos se entregan al redactor.
DEFAULT_LIMIT = 10
PACK_LIMIT = 6


class DisabledVectorSearch:
    """Sin proveedor de embeddings: la búsqueda vectorial no existe **y se dice**.

    Es la implementación por defecto y la única que hay hasta que se decida un modelo (el nombre se
    fija por ADR tras un benchmark en español, `05_RAG §4`): descargar un modelo al arrancar sin
    avisar está prohibido, y simular una búsqueda vectorial con ceros sería peor.
    """

    @property
    def available(self) -> bool:
        return False

    @property
    def reason(self) -> str | None:
        return (
            "sin proveedor de embeddings configurado: la búsqueda es solo léxica (FTS5). "
            "El índice vectorial local llega cuando se decida el modelo (DEBT-014)."
        )

    @property
    def model(self) -> str | None:
        return None

    def search(self, question: str, *, limit: int) -> tuple[CandidateSpan, ...]:
        return ()


@dataclass(frozen=True, slots=True)
class SearchRequest:
    """Lo que se pide en una búsqueda (08_API-CONTRACT §8)."""

    query: str
    #: `None` significa «los filtros por defecto»: un `SearchFilters()` mutable como valor por
    #: defecto se evalúa una sola vez y se comparte entre peticiones.
    filters: SearchFilters | None = None
    strategy: SearchStrategy = SearchStrategy.LEXICAL

    @property
    def effective_filters(self) -> SearchFilters:
        return self.filters if self.filters is not None else SearchFilters()


@dataclass(frozen=True, slots=True)
class AskRequest:
    """Lo que se pide en una consulta de RAG: la búsqueda más el estilo de respuesta."""

    query: str
    filters: SearchFilters | None = None
    style: str = "brief"
    allow_private_sources: bool = True

    @property
    def effective_filters(self) -> SearchFilters:
        return self.filters if self.filters is not None else SearchFilters()


class SearchService:
    def __init__(
        self,
        *,
        search: SqlAlchemySearchRepository,
        vector: VectorSearch | None = None,
        clock: Clock,
    ) -> None:
        self._search = search
        self._vector = vector if vector is not None else DisabledVectorSearch()
        self._clock = clock

    # ------------------------------------------------------------------ buscar

    def search_only(self, request: SearchRequest) -> SearchOutcome:
        """Busca y devuelve resultados **sin** generar respuesta (§5, último párrafo)."""
        expresion = match_expression(request.query)
        revision = self._search.corpus_revision()
        filtros = request.effective_filters
        candidatos, excluidos = self._search.search(expresion, filtros, limit=filtros.limit)

        vectoriales = self._vector_candidates(request, filtros)
        paquete = fuse_candidates(candidatos, vectoriales, limit=filtros.limit)

        hits = tuple(
            SearchHitView(
                span=self._span_view(span),
                rank=posicion,
                score=span.score,
                strategy=span.strategy,
                matched_terms=span.matched_terms,
            )
            for posicion, span in enumerate(paquete.hits, start=1)
        )
        return SearchOutcome(
            hits=hits,
            strategy=(
                SearchStrategy.HYBRID
                if SearchStrategy.HYBRID in paquete.strategies
                else SearchStrategy.LEXICAL
            ),
            strategies=paquete.strategies,
            corpus_revision=revision,
            version_mode=filtros.version_mode,
            degradations=paquete.degradations,
            excluded=excluidos,
            total=len(hits),
        )

    def ask(self, request: AskRequest) -> RagQueryView:
        """Responde con citas: recupera, compone y **guarda** la consulta, la recuperación y la
        respuesta.

        La respuesta puede ser `insufficient`: cuando el corpus no cubre la pregunta, eso es el
        resultado correcto, no un fallo, y se guarda como tal.
        """
        if not request.query.strip():
            raise InvariantViolationError("una consulta de RAG necesita una pregunta")
        ahora = self._clock.now()
        revision = self._search.corpus_revision()
        expresion = match_expression(request.query)
        filtros = request.effective_filters
        candidatos, _ = self._search.search(expresion, filtros, limit=filtros.limit)
        vectoriales = self._vector_candidates(request, filtros)
        paquete = fuse_candidates(candidatos, vectoriales, limit=PACK_LIMIT)

        entregados = paquete.hits
        borrador = compose_extractive_answer(request.query, entregados)
        assert_grounded(borrador, paquete.ids)

        query_id = self._search.save_query(
            question=request.query,
            filters=filtros,
            strategy=paquete.strategies[-1],
            version_mode=filtros.version_mode,
            corpus_revision=revision,
            provider="extractive",
            model=None,
            prompt_template_version="extractive-v1",
            now=ahora,
        )
        usados = set(borrador.evidence_ids)
        self._search.save_hits(
            query_id,
            tuple(
                SearchHitView(
                    span=self._span_view(span),
                    rank=posicion,
                    score=span.score,
                    strategy=span.strategy,
                    matched_terms=span.matched_terms,
                )
                for posicion, span in enumerate(entregados, start=1)
            ),
            used_ids=tuple(usados),
        )
        self._search.save_answer(query_id, borrador, now=ahora)
        consulta = self._search.query(query_id)
        if consulta is None:  # pragma: no cover - acaba de guardarse
            raise NotFoundError("consulta de RAG", query_id)
        return consulta

    # ------------------------------------------------------------------ leer

    def query(self, query_id: str) -> RagQueryView:
        consulta = self._search.query(query_id)
        if consulta is None:
            raise NotFoundError("consulta de RAG", query_id)
        return consulta

    def retrieval(self, query_id: str) -> RetrievalView:
        if self._search.query(query_id) is None:
            raise NotFoundError("consulta de RAG", query_id)
        recuperacion = self._search.retrieval(query_id)
        if recuperacion is None:  # pragma: no cover - la consulta existe
            raise NotFoundError("consulta de RAG", query_id)
        return recuperacion

    def span(self, span_id: str) -> SpanView:
        """El fragmento con lo que hace falta para abrirlo: documento, versión, sección y página."""
        fragmento = self._search.span(span_id)
        if fragmento is None:
            raise NotFoundError("fragmento de evidencia", span_id)
        return fragmento

    def rebuild(self) -> int:
        """Rehace el índice léxico desde SQLite (§4: los índices son reconstruibles)."""
        return self._search.rebuild_index()

    def capabilities(self) -> tuple[str, ...]:
        """Lo que la recuperación **no** puede hacer hoy, con su motivo, para declararlo."""
        motivos: list[str] = []
        if not self._vector.available:
            motivos.append(self._vector.reason or "búsqueda vectorial no disponible")
        return tuple(motivos)

    # ------------------------------------------------------------------ ayudas

    def _vector_candidates(
        self, request: SearchRequest | AskRequest, filtros: SearchFilters
    ) -> tuple[CandidateSpan, ...]:
        """Los candidatos vectoriales, si hay proveedor y si se pidió búsqueda híbrida."""
        pedida = getattr(request, "strategy", SearchStrategy.LEXICAL) is SearchStrategy.HYBRID
        if not pedida or not self._vector.available:
            return ()
        return self._vector.search(request.query, limit=filtros.limit)

    @staticmethod
    def _span_view(span: CandidateSpan) -> SpanView:
        return SpanView(
            id=span.span_id,
            document_version_id=span.document_version_id,
            document_id=span.document_id,
            document_title=span.document_title,
            document_type=span.document_type,
            authority_tier=span.authority_tier,
            version_status=span.version_status,
            section_id=span.section_id,
            section_title=span.section_title,
            citation_label=span.citation_label,
            page=span.page,
            text=span.text,
            ordinal=0,
            page_start=None,
            page_end=None,
        )


def answer_summary(answer: AnswerView | None) -> str:
    """Texto corto del estado de una respuesta, para la interfaz y para los informes."""
    if answer is None:
        return "sin respuesta"
    if answer.is_supported:
        return "respaldada por el corpus"
    return {
        "partial": "respaldada solo en parte",
        "insufficient": "evidencia insuficiente",
    }[answer.status.value]


def terms_of(question: str) -> Sequence[str]:
    """Los términos que la pregunta exige para considerarla respaldada."""
    return significant_terms(question)


#: Reexportado para que el vocabulario del filtro viaje con el servicio.
__all__ = [
    "AskRequest",
    "DisabledVectorSearch",
    "SearchRequest",
    "SearchService",
    "VersionMode",
    "answer_summary",
    "terms_of",
]
