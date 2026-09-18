"""Rutas de búsqueda y RAG (08_API-CONTRACT §8).

Cinco rutas, y una regla que las atraviesa: **buscar no responde**. `POST /search` devuelve
fragmentos; para obtener una respuesta con citas hay que pedirla con `POST /rag/queries`, y esa
respuesta puede ser `insufficient`. Mezclarlas ahorraría una llamada y le quitaría a quien pregunta
la posibilidad de mirar la evidencia antes de creerse una frase.
"""

from __future__ import annotations

from fastapi import APIRouter

from opofuente.api.deps import SearchServiceDep
from opofuente.api.error_responses import INGESTION_WRITE_ERRORS, RESOURCE_ERRORS
from opofuente.api.search_schemas import (
    AnswerSchema,
    AskRequestSchema,
    ClaimSchema,
    EvidenceSpanSchema,
    RagQuerySchema,
    RetrievalHitSchema,
    RetrievalSchema,
    SearchHitSchema,
    SearchRequestSchema,
    SearchResultSchema,
)
from opofuente.application.search_models import (
    AnswerView,
    RagQueryView,
    RetrievalView,
    SearchHitView,
    SearchOutcome,
    SpanView,
)
from opofuente.application.search_service import AskRequest, SearchRequest
from opofuente.domain.rag import AnswerStyle, SearchFilters, SearchStrategy, VersionMode

router = APIRouter(tags=["búsqueda"])


def _filters(request: SearchRequestSchema) -> SearchFilters:
    return SearchFilters(
        opposition_id=request.opposition_id,
        convocation_id=request.convocation_id,
        curriculum_node_ids=tuple(request.curriculum_node_ids),
        document_ids=tuple(request.document_ids),
        authority_tier=request.authority_tier,
        reference_date=request.reference_date,
        version_mode=VersionMode(request.version_mode),
        languages=tuple(request.languages),
        limit=request.limit,
    )


def _span(view: SpanView) -> EvidenceSpanSchema:
    return EvidenceSpanSchema(
        id=view.id,
        document_id=view.document_id,
        document_version_id=view.document_version_id,
        document_title=view.document_title,
        document_type=view.document_type,
        authority_tier=view.authority_tier,
        version_status=view.version_status,
        section_id=view.section_id,
        section_title=view.section_title,
        citation_label=view.citation_label,
        page=view.page,
        page_start=view.page_start,
        page_end=view.page_end,
        ordinal=view.ordinal,
        text=view.text,
    )


def _hit(view: SearchHitView) -> SearchHitSchema:
    return SearchHitSchema(
        span=_span(view.span),
        rank=view.rank,
        score=view.score,
        strategy=view.strategy.value,
        matched_terms=list(view.matched_terms),
    )


def _search_result(view: SearchOutcome) -> SearchResultSchema:
    return SearchResultSchema(
        hits=[_hit(hit) for hit in view.hits],
        total=view.total,
        strategy=view.strategy.value,
        strategies=[estrategia.value for estrategia in view.strategies],
        corpus_revision=view.corpus_revision,
        version_mode=view.version_mode.value,
        degradations=list(view.degradations),
        excluded=list(view.excluded),
    )


def _answer(view: AnswerView) -> AnswerSchema:
    return AnswerSchema(
        id=view.id,
        query_id=view.query_id,
        status=view.status.value,
        short_answer=view.short_answer,
        explanation=view.explanation,
        claims=[
            ClaimSchema(
                text=claim.text,
                support=claim.support.value,
                evidence=[_span(evidencia) for evidencia in claim.evidence],
            )
            for claim in view.claims
        ],
        uncertainties=list(view.uncertainties),
        suggested_followups=list(view.suggested_followups),
        provider=view.provider,
        model=view.model,
        prompt_template_version=view.prompt_template_version,
        created_at=view.created_at,
    )


def _query(view: RagQueryView) -> RagQuerySchema:
    return RagQuerySchema(
        id=view.id,
        question=view.question,
        strategy=view.strategy.value,
        version_mode=view.version_mode.value,
        corpus_revision=view.corpus_revision,
        provider=view.provider,
        model=view.model,
        prompt_template_version=view.prompt_template_version,
        created_at=view.created_at,
        answer=None if view.answer is None else _answer(view.answer),
    )


def _retrieval(view: RetrievalView) -> RetrievalSchema:
    return RetrievalSchema(
        query_id=view.query_id,
        corpus_revision=view.corpus_revision,
        hits=[
            RetrievalHitSchema(
                span=_span(hit.span),
                rank=hit.rank,
                score=hit.score,
                strategy=hit.strategy.value,
                used=hit.used,
            )
            for hit in view.hits
        ],
        used_ids=list(view.used_ids),
    )


@router.post(
    "/search",
    response_model=SearchResultSchema,
    responses=INGESTION_WRITE_ERRORS,
    summary="Busca en el corpus publicado (sin generar respuesta)",
)
def search(request: SearchRequestSchema, service: SearchServiceDep) -> SearchResultSchema:
    return _search_result(
        service.search_only(
            SearchRequest(
                query=request.query,
                filters=_filters(request),
                strategy=SearchStrategy(request.strategy),
            )
        )
    )


@router.post(
    "/rag/queries",
    response_model=RagQuerySchema,
    status_code=201,
    responses=INGESTION_WRITE_ERRORS,
    summary="Pregunta al corpus y devuelve una respuesta con citas",
)
def ask(request: AskRequestSchema, service: SearchServiceDep) -> RagQuerySchema:
    """La respuesta puede ser `insufficient`: es un resultado, no un error."""
    return _query(
        service.ask(
            AskRequest(
                query=request.query,
                filters=_filters(request),
                style=AnswerStyle(request.style),
                allow_private_sources=request.allow_private_sources,
            )
        )
    )


@router.get(
    "/rag/queries/{query_id}",
    response_model=RagQuerySchema,
    responses=RESOURCE_ERRORS,
    summary="Una consulta guardada con su respuesta",
)
def get_rag_query(query_id: str, service: SearchServiceDep) -> RagQuerySchema:
    return _query(service.query(query_id))


@router.get(
    "/rag/queries/{query_id}/retrieval",
    response_model=RetrievalSchema,
    responses=RESOURCE_ERRORS,
    summary="Todo lo que se recuperó en una consulta, se usara o no",
)
def get_rag_retrieval(query_id: str, service: SearchServiceDep) -> RetrievalSchema:
    return _retrieval(service.retrieval(query_id))


@router.get(
    "/evidence-spans/{span_id}",
    response_model=EvidenceSpanSchema,
    responses=RESOURCE_ERRORS,
    summary="Un fragmento de evidencia con lo necesario para abrirlo",
)
def get_evidence_span(span_id: str, service: SearchServiceDep) -> EvidenceSpanSchema:
    return _span(service.span(span_id))
