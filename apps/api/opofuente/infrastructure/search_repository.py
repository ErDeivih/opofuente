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

from sqlalchemy import bindparam, func, select, text
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
from opofuente.infrastructure.curriculum_lookup import (
    official_version_id,
    version_ids_of_opposition,
)
from opofuente.infrastructure.db_models import (
    AnswerClaimEvidenceRecord,
    AnswerClaimRecord,
    CurriculumNodeRecord,
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


#: Consulta de búsqueda léxica, **constante**: los valores viajan siempre como parámetros ligados.
#:
#: Tres decisiones que se leen en el SQL y no en Python:
#:
#: 1. el ámbito de programa se abre con una CTE recursiva, así que pedir un bloque incluye sus
#:    temas y epígrafes (igual que la cobertura): una versión cuenta para el ámbito si algún
#:    **mapeo** suyo —de la versión, del artefacto, de la representación, de una sección o de un
#:    fragmento— cae dentro, y los mapeos rechazados no cuentan;
#: 2. los cuatro filtros explícitos viajan al `WHERE`, de modo que la ventana de `bm25` ya está
#:    acotada por ellos (filtrar después del `LIMIT` esconde material que sí respondía);
#: 3. lo que **no** se decide aquí es la elegibilidad (vigencia, estado y calidad): eso es criterio
#:    del dominio, en `corpus_eligible`, para que no haya dos verdades sobre qué se puede citar.
SQL_BUSQUEDA = """
WITH RECURSIVE ambito(node_id) AS (
    SELECT id FROM curriculum_nodes WHERE id IN :nodos
    UNION
    SELECT hijo.id FROM curriculum_nodes hijo
    JOIN ambito ON hijo.parent_id = ambito.node_id
)
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
  AND (:sin_documentos = 1 OR d.id IN :documentos)
  AND (:sin_idiomas = 1 OR v.language IS NULL OR v.language IN :idiomas)
  AND (:sin_autoridad = 1 OR d.authority_tier = :autoridad)
  AND (
    :sin_ambito = 1
    OR EXISTS (
      SELECT 1 FROM curriculum_mappings m
      WHERE m.status <> 'rejected'
        AND m.curriculum_node_id IN (SELECT node_id FROM ambito)
        AND (
          (m.subject_type = 'document_version' AND m.subject_id = v.id)
          OR (m.subject_type = 'artifact' AND m.subject_id = v.artifact_id)
          OR (m.subject_type = 'representation' AND m.subject_id = v.representation_id)
          OR (m.subject_type = 'section'
              AND m.subject_id IN (
                SELECT sec2.id FROM document_sections sec2
                WHERE sec2.document_version_id = v.id
              ))
          OR (m.subject_type = 'evidence' AND m.subject_id = s.id)
        )
    )
  )
ORDER BY score
LIMIT :limite
"""


class SqlAlchemySearchRepository:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def _scope_nodes(self, filters: SearchFilters) -> tuple[str, ...]:
        """Nodos raíz del ámbito pedido: los del filtro, o los de la convocatoria/oposición.

        El ámbito no se limita al nodo exacto: incluye su **subárbol**, igual que la cobertura, para
        que preguntar por un bloque no deje fuera lo asignado a sus temas.
        """
        if filters.curriculum_node_ids:
            return tuple(filters.curriculum_node_ids)
        if filters.convocation_id is None and filters.opposition_id is None:
            return ()
        with self._session_factory() as session:
            consulta = select(CurriculumNodeRecord.id).where(
                CurriculumNodeRecord.parent_id.is_(None)
            )
            if filters.convocation_id is not None:
                version_id = official_version_id(session, filters.convocation_id)
                if version_id is None:
                    # La convocatoria no publica programa: su ámbito no tiene nodos.
                    return ()
                consulta = consulta.where(CurriculumNodeRecord.curriculum_version_id == version_id)
            else:
                consulta = consulta.where(
                    CurriculumNodeRecord.curriculum_version_id.in_(
                        version_ids_of_opposition(filters.opposition_id or "")
                    )
                )
            return tuple(str(nodo) for nodo in session.execute(consulta).scalars())

    # ------------------------------------------------------------------ índice

    def rebuild_index(self) -> int:
        """Rehace el índice léxico completamente y devuelve cuántos fragmentos ha indexado.

        `REBUILD` reconstruye la tabla externa leyendo `evidence_spans`: es la operación honesta
        cuando el índice y los datos se han separado (un borrado a mano, una restauración, un
        `UPDATE` en crudo). Si el índice estaba bien, el resultado es el mismo y no se pierde nada.
        """
        with self._session_factory() as session:
            session.execute(text("INSERT INTO evidence_fts(evidence_fts) VALUES('rebuild')"))
            total = session.execute(
                select(func.count()).select_from(EvidenceSpanRecord)
            ).scalar_one()
            session.commit()
            return int(total)

    def indexed_count(self) -> int:
        """Cuántos fragmentos hay **en el índice** ahora mismo, no cuántos debería haber.

        La diferencia con el recuento de `evidence_spans` es la comprobación que Ajustes
        necesita: si
        el índice perdió entradas (un borrado a mano, una restauración), los dos números no
        coinciden y
        eso se puede decir. No se puede saber de forma barata cuáles faltan, pero saber **si**
        faltan
        es suficiente para ofrecer la reparación.
        """
        with self._session_factory() as session:
            filas = session.execute(text("SELECT COUNT(*) FROM evidence_fts")).scalar_one()
            return int(filas)

    def indexed_spans(self) -> int:
        """Fragmentos que deberían estar en el índice: la verdad está en `evidence_spans`."""
        with self._session_factory() as session:
            return int(
                session.execute(select(func.count()).select_from(EvidenceSpanRecord)).scalar_one()
            )

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

        Dos reglas que se aplican **en la consulta** y no después, porque un `LIMIT` antes del
        filtro esconde material que sí respondía:

        1. los filtros explícitos (documentos, idioma, autoridad y el ámbito de programa) viajan
           al `WHERE`, así que la ventana de `bm25` ya está acotada;
        2. el ámbito de programa (`opposition_id`, `convocation_id`, `curriculum_node_ids`) se
           resuelve por los **mapeos** de la versión del documento —con el subárbol del nodo
           incluido, igual que la cobertura—: una versión sin mapeo no está probada como material de
           esa oposición, y sin prueba no entra en su ámbito.

        Lo que sí se decide en el dominio es la **elegibilidad** (vigencia, estado y calidad): así
        no hay dos verdades sobre qué se puede citar, y lo descartado se informa con su motivo.
        """
        terminos = tuple(significant_terms(expression.replace('"', " ").replace("*", " ")))
        # Una sola resolución del ámbito: la consulta la usa dos veces (indicador y nodos raíz).
        nodos_ambito = self._scope_nodes(filters)
        # Las listas de un `IN` viajan como parámetros **expansibles** de SQLAlchemy: la consulta es
        # una cadena constante (nada se interpola) y los valores siguen siendo parámetros ligados.
        parametros: dict[str, object] = {
            "expresion": expression,
            "limite": max(1, limit * 4),
            "solo_publico": 0 if filters.include_private else 1,
            "documentos": list(filters.document_ids) or [""],
            "sin_documentos": 0 if filters.document_ids else 1,
            "idiomas": list(filters.languages) or [""],
            "sin_idiomas": 0 if filters.languages else 1,
            "sin_autoridad": 0 if filters.authority_tier is not None else 1,
            "autoridad": filters.authority_tier or "",
            "nodos": list(nodos_ambito) or [""],
            "sin_ambito": 0 if nodos_ambito else 1,
        }
        consulta = text(SQL_BUSQUEDA).bindparams(
            bindparam("documentos", expanding=True),
            bindparam("idiomas", expanding=True),
            bindparam("nodos", expanding=True),
        )
        with self._session_factory() as session:
            filas = session.execute(consulta, parametros).mappings()

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
                # Los filtros explícitos (documentos, idioma, autoridad y ámbito de programa) ya los
                # aplica la consulta antes del `LIMIT`: aquí solo queda la elegibilidad del dominio.
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
