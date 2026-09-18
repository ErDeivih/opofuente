"""Repositorio de búsqueda y RAG (S09): índice léxico, consultas guardadas y respuestas citadas.

Tres cosas que hace de una manera concreta:

1. **la consulta va al índice FTS5 con el filtro del corpus en SQL**, no filtrando después:
   recuperar lo que no se puede citar y descartarlo luego sería más lento y, peor, dejaría la
   sensación de que el material está y no sale por casualidad;
2. **la elegibilidad se comprueba también en el dominio** (`corpus_eligible`) y su motivo se
   devuelve: si algo no aparece, se puede decir por qué;
3. **todo lo recuperado se guarda**, con `used` para los que llegaron al redactor: una respuesta se
   audita después («¿por qué dijiste esto?» → estos fragmentos, estos descartados).
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from datetime import datetime
from uuid import uuid4

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session, sessionmaker

from opofuente.application.search_models import (
    AnswerView,
    ClaimView,
    RagQueryView,
    RetrievalHitDetail,
    RetrievalView,
    SearchHitView,
    SearchOutcome,
    SpanView,
)
from opofuente.domain.rag import (
    AnswerStatus,
    CandidateSpan,
    ClaimSupport,
    RagDraft,
    SearchFilters,
    SearchStrategy,
    VersionMode,
    corpus_eligible,
    significant_terms,
)
from opofuente.infrastructure.db_models import (
    AnswerClaimEvidenceRecord,
    AnswerClaimRecord,
    DocumentSectionRecord,
    DocumentVersionRecord,
    EvidenceSpanRecord,
    GeneratedAnswerRecord,
    LogicalDocumentRecord,
    RagQueryRecord,
    RetrievalHitRecord,
)


def _new_id() -> str:
    return str(uuid4())


class SqlAlchemySearchRepository:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    # ------------------------------------------------------------------ índice

    def rebuild_index(self) -> int:
        """Rehace el índice léxico desde SQLite y devuelve cuántos fragmentos ha indexado (§4)."""
        with self._session_factory() as session:
            session.execute(text("INSERT INTO evidence_fts(evidence_fts) VALUES('rebuild')"))
            total = session.execute(
                select(func.count()).select_from(EvidenceSpanRecord)
            ).scalar_one()
            session.commit()
            return int(total)

    def corpus_revision(self) -> str:
        """Identificador de la revisión del corpus, **derivado** de los fragmentos que hay.

        No es un contador que alguien tenga que acordarse de subir: cambia exactamente cuando cambia
        el material indexable (se promociona o se retira algo), que es lo que `05_RAG §4` pide para
        invalidar cachés y para saber con qué corpus se respondió.
        """
        with self._session_factory() as session:
            fila = session.execute(
                select(
                    func.count(),
                    func.max(EvidenceSpanRecord.created_at),
                    func.max(EvidenceSpanRecord.ordinal),
                ).select_from(EvidenceSpanRecord)
            ).one()
        total, ultimo, ultimo_ordinal = fila
        return f"{int(total)}-{ultimo or 'sin-fecha'}-{int(ultimo_ordinal or 0)}"

    # ------------------------------------------------------------------ búsqueda

    def search(
        self,
        expression: str,
        filters: SearchFilters,
        *,
        limit: int,
    ) -> tuple[tuple[CandidateSpan, ...], tuple[str, ...]]:
        """Busca en el índice léxico con los filtros del corpus y devuelve también lo excluido.

        La consulta SQL filtra por lo que se puede decidir en la base (estado, tipo documental,
        documentos, idioma) y devuelve además lo necesario para que el dominio compruebe la vigencia
        y la calidad con su propio criterio: así no hay dos verdades sobre qué es elegible.
        """
        terminos = tuple(significant_terms(expression.replace('"', " ").replace("*", " ")))
        with self._session_factory() as session:
            filas = session.execute(
                text(
                    """
                    SELECT s.id AS span_id,
                           s.document_version_id AS document_version_id,
                           s.section_id AS section_id,
                           s.page AS page,
                           s.citation_label AS citation_label,
                           s.text AS text,
                           s.ordinal AS ordinal,
                           sec.title AS section_title,
                           sec.page_start AS section_page_start,
                           v.status AS version_status,
                           v.valid_from AS valid_from,
                           v.valid_to AS valid_to,
                           v.language AS language,
                           r.quality AS representation_quality,
                           d.id AS document_id,
                           d.canonical_title AS document_title,
                           d.document_type AS document_type,
                           d.authority_tier AS authority_tier,
                           bm25(evidence_fts) AS score
                    FROM evidence_fts
                    JOIN evidence_spans s ON s.rowid = evidence_fts.rowid
                    JOIN document_versions v ON v.id = s.document_version_id
                    JOIN logical_documents d ON d.id = v.logical_document_id
                    LEFT JOIN document_sections sec ON sec.id = s.section_id
                    LEFT JOIN extracted_representations r ON r.id = v.representation_id
                    WHERE evidence_fts MATCH :expresion
                      AND (:solo_publico = 0 OR d.owner_scope <> 'private_user')
                    ORDER BY score
                    LIMIT :limite
                    """
                ),
                {
                    "expresion": expression,
                    "limite": max(1, limit * 4),
                    "solo_publico": 0 if filters.include_private else 1,
                },
            ).mappings()

            candidatos: list[CandidateSpan] = []
            excluidos: list[str] = []
            for fila in filas:
                decision = corpus_eligible(
                    version_status=str(fila["version_status"]),
                    representation_quality=(
                        None
                        if fila["representation_quality"] is None
                        else str(fila["representation_quality"])
                    ),
                    valid_from=fila["valid_from"],
                    valid_to=fila["valid_to"],
                    reference_date=filters.reference_date,
                    version_mode=filters.version_mode,
                )
                if not decision.eligible:
                    motivo = f"«{fila['document_title']}»: {decision.reason}"
                    if motivo not in excluidos:
                        excluidos.append(motivo)
                    continue
                if filters.document_ids and str(fila["document_id"]) not in filters.document_ids:
                    continue
                if filters.languages and (
                    fila["language"] is not None and str(fila["language"]) not in filters.languages
                ):
                    continue
                if filters.authority_tier is not None and (
                    fila["authority_tier"] is None
                    or str(fila["authority_tier"]) != filters.authority_tier
                ):
                    continue
                normalizado = " ".join(str(fila["text"]).lower().split())
                candidatos.append(
                    CandidateSpan(
                        span_id=str(fila["span_id"]),
                        document_version_id=str(fila["document_version_id"]),
                        document_id=str(fila["document_id"]),
                        document_title=str(fila["document_title"]),
                        document_type=str(fila["document_type"]),
                        authority_tier=(
                            None if fila["authority_tier"] is None else str(fila["authority_tier"])
                        ),
                        version_status=str(fila["version_status"]),
                        citation_label=(
                            None if fila["citation_label"] is None else str(fila["citation_label"])
                        ),
                        page=fila["page"],
                        section_id=None if fila["section_id"] is None else str(fila["section_id"]),
                        section_title=(
                            None if fila["section_title"] is None else str(fila["section_title"])
                        ),
                        text=str(fila["text"]),
                        score=-float(fila["score"] or 0.0),
                        strategy=SearchStrategy.LEXICAL,
                        matched_terms=tuple(
                            termino for termino in terminos if termino in normalizado
                        ),
                        valid_from=fila["valid_from"],
                        valid_to=fila["valid_to"],
                    )
                )
                if len(candidatos) >= limit * 2:
                    break
            return tuple(candidatos), tuple(excluidos)

    # ------------------------------------------------------------------ guardar la consulta

    def save_query(
        self,
        *,
        question: str,
        filters: SearchFilters,
        strategy: SearchStrategy,
        version_mode: VersionMode,
        corpus_revision: str,
        provider: str = "extractive",
        model: str | None = None,
        prompt_template_version: str | None = None,
        now: datetime,
    ) -> str:
        with self._session_factory() as session:
            identificador = _new_id()
            session.add(
                RagQueryRecord(
                    id=identificador,
                    opposition_id=filters.opposition_id,
                    convocation_version_id=filters.convocation_id,
                    question=question,
                    filters_json=json.dumps(
                        {
                            "curriculum_node_ids": list(filters.curriculum_node_ids),
                            "document_ids": list(filters.document_ids),
                            "authority_tier": filters.authority_tier,
                            "reference_date": (
                                None
                                if filters.reference_date is None
                                else filters.reference_date.isoformat()
                            ),
                            "languages": list(filters.languages),
                            "limit": filters.limit,
                        },
                        ensure_ascii=False,
                    ),
                    strategy=strategy.value,
                    version_mode=version_mode.value,
                    corpus_revision=corpus_revision,
                    provider=provider,
                    model=model,
                    prompt_template_version=prompt_template_version,
                    created_at=now,
                )
            )
            session.commit()
            return identificador

    def save_hits(
        self,
        query_id: str,
        hits: Sequence[SearchHitView],
        *,
        used_ids: Sequence[str] = (),
    ) -> None:
        """Guarda **todos** los fragmentos recuperados y cuáles se usaron."""
        usados = set(used_ids)
        with self._session_factory() as session:
            for posicion, hit in enumerate(hits, start=1):
                session.add(
                    RetrievalHitRecord(
                        id=_new_id(),
                        query_id=query_id,
                        span_id=hit.span.id,
                        rank=posicion,
                        score=float(hit.score),
                        strategy=hit.strategy.value,
                        used=hit.span.id in usados,
                    )
                )
            session.commit()

    def save_answer(
        self,
        query_id: str,
        draft: RagDraft,
        *,
        now: datetime,
        provider: str = "extractive",
        model: str | None = None,
        prompt_template_version: str | None = "extractive-v1",
    ) -> str:
        """Guarda la respuesta con sus afirmaciones y la evidencia de cada una."""
        with self._session_factory() as session:
            respuesta_id = _new_id()
            session.add(
                GeneratedAnswerRecord(
                    id=respuesta_id,
                    query_id=query_id,
                    status=draft.status.value,
                    short_answer=draft.short_answer,
                    explanation=draft.explanation,
                    uncertainties_json=json.dumps(list(draft.uncertainties), ensure_ascii=False),
                    suggested_followups_json=json.dumps(
                        list(draft.suggested_followups), ensure_ascii=False
                    ),
                    provider=provider,
                    model=model,
                    prompt_template_version=prompt_template_version,
                    created_at=now,
                )
            )
            # La afirmación se confirma antes que su evidencia: sin relaciones declaradas,
            # SQLAlchemy no sabe que depende de ella (el mismo tropiezo que en S06 y S07).
            session.flush()
            for posicion, claim in enumerate(draft.claims, start=1):
                claim_id = _new_id()
                session.add(
                    AnswerClaimRecord(
                        id=claim_id,
                        answer_id=respuesta_id,
                        position=posicion,
                        text=claim.text,
                        support=claim.support.value,
                        created_at=now,
                    )
                )
                session.flush()
                for span_id in claim.evidence_ids:
                    session.add(AnswerClaimEvidenceRecord(claim_id=claim_id, span_id=span_id))
            session.commit()
            return respuesta_id

    # ------------------------------------------------------------------ leer lo guardado

    def query(self, query_id: str) -> RagQueryView | None:
        with self._session_factory() as session:
            fila = session.get(RagQueryRecord, query_id)
            if fila is None:
                return None
            respuesta = session.execute(
                select(GeneratedAnswerRecord).where(GeneratedAnswerRecord.query_id == query_id)
            ).scalar_one_or_none()
            return RagQueryView(
                id=fila.id,
                question=fila.question,
                strategy=SearchStrategy(fila.strategy),
                version_mode=VersionMode(fila.version_mode),
                corpus_revision=fila.corpus_revision,
                provider=fila.provider,
                model=fila.model,
                prompt_template_version=fila.prompt_template_version,
                created_at=fila.created_at,
                answer=None if respuesta is None else self._answer_view(session, respuesta),
            )

    def retrieval(self, query_id: str) -> RetrievalView | None:
        with self._session_factory() as session:
            consulta = session.get(RagQueryRecord, query_id)
            if consulta is None:
                return None
            filas = (
                session.execute(
                    select(RetrievalHitRecord)
                    .where(RetrievalHitRecord.query_id == query_id)
                    .order_by(RetrievalHitRecord.rank)
                )
                .scalars()
                .all()
            )
            detalles = tuple(
                RetrievalHitDetail(
                    span=self._span_view(session, fila.span_id),
                    rank=fila.rank,
                    score=fila.score,
                    strategy=SearchStrategy(fila.strategy),
                    used=bool(fila.used),
                )
                for fila in filas
                if session.get(EvidenceSpanRecord, fila.span_id) is not None
            )
            return RetrievalView(
                query_id=query_id,
                corpus_revision=consulta.corpus_revision,
                hits=detalles,
                used_ids=tuple(detalle.span.id for detalle in detalles if detalle.used),
            )

    def span(self, span_id: str) -> SpanView | None:
        with self._session_factory() as session:
            if session.get(EvidenceSpanRecord, span_id) is None:
                return None
            return self._span_view(session, span_id)

    # ------------------------------------------------------------------ vistas

    def _span_view(self, session: Session, span_id: str) -> SpanView:
        fila = session.execute(
            select(
                EvidenceSpanRecord,
                DocumentVersionRecord,
                LogicalDocumentRecord,
                DocumentSectionRecord,
            )
            .join(
                DocumentVersionRecord,
                DocumentVersionRecord.id == EvidenceSpanRecord.document_version_id,
            )
            .join(
                LogicalDocumentRecord,
                LogicalDocumentRecord.id == DocumentVersionRecord.logical_document_id,
            )
            .outerjoin(
                DocumentSectionRecord, DocumentSectionRecord.id == EvidenceSpanRecord.section_id
            )
            .where(EvidenceSpanRecord.id == span_id)
        ).one()
        span, version, documento, seccion = fila
        return SpanView(
            id=span.id,
            document_version_id=span.document_version_id,
            document_id=documento.id,
            document_title=documento.canonical_title,
            document_type=documento.document_type,
            authority_tier=documento.authority_tier,
            version_status=version.status,
            section_id=span.section_id,
            section_title=None if seccion is None else seccion.title,
            citation_label=span.citation_label,
            page=span.page,
            text=span.text,
            ordinal=span.ordinal,
            page_start=None if seccion is None else seccion.page_start,
            page_end=None if seccion is None else seccion.page_end,
        )

    def _answer_view(self, session: Session, fila: GeneratedAnswerRecord) -> AnswerView:
        claims = (
            session.execute(
                select(AnswerClaimRecord)
                .where(AnswerClaimRecord.answer_id == fila.id)
                .order_by(AnswerClaimRecord.position)
            )
            .scalars()
            .all()
        )
        vistas: list[ClaimView] = []
        for claim in claims:
            evidencias = (
                session.execute(
                    select(AnswerClaimEvidenceRecord.span_id).where(
                        AnswerClaimEvidenceRecord.claim_id == claim.id
                    )
                )
                .scalars()
                .all()
            )
            vistas.append(
                ClaimView(
                    text=claim.text,
                    support=ClaimSupport(claim.support),
                    evidence=tuple(
                        self._span_view(session, span_id)
                        for span_id in evidencias
                        if session.get(EvidenceSpanRecord, span_id) is not None
                    ),
                )
            )
        return AnswerView(
            id=fila.id,
            query_id=fila.query_id,
            status=AnswerStatus(fila.status),
            short_answer=fila.short_answer,
            explanation=fila.explanation,
            claims=tuple(vistas),
            uncertainties=tuple(
                str(valor) for valor in json.loads(fila.uncertainties_json or "[]")
            ),
            suggested_followups=tuple(
                str(valor) for valor in json.loads(fila.suggested_followups_json or "[]")
            ),
            provider=fila.provider,
            model=fila.model,
            prompt_template_version=fila.prompt_template_version,
            created_at=fila.created_at,
        )


__all__ = ["SearchOutcome", "SqlAlchemySearchRepository"]
