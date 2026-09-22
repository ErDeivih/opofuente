"""Recuentos de preparación sobre SQLite (S12.6).

Todo son consultas agregadas: `COUNT` y `EXISTS` resueltos en la base. La alternativa (traerse los
documentos, las preguntas y las claves y contarlos en memoria) aguanta con el corpus del propietario
y deja de aguantar con el doble, sin que nadie se entere hasta que la pantalla de Inicio tarda.

Dos criterios que se aplican en **todas** las consultas y conviene no perder de vista:

- el material que cuenta como material es el **aceptado** (una versión en estado `candidate` está
  importada, no aceptada, y se declara aparte en la lista de pendientes);
- una pregunta cuenta como pregunta del conjunto si su versión no está sustituida (DEBT-025).
"""

from __future__ import annotations

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.sql.elements import ColumnElement

from opofuente.application.readiness_models import (
    MaterialSummary,
    OppositionRef,
    PendingCounts,
    QuestionSummary,
)
from opofuente.infrastructure.db_models import (
    AnswerKeyVersionRecord,
    ChangeSetRecord,
    ClassificationProposalRecord,
    ConvocationVersionRecord,
    CurriculumMappingRecord,
    CurriculumNodeRecord,
    DocumentVersionRecord,
    ImportIssueRecord,
    LogicalDocumentRecord,
    OppositionRecord,
    QuestionSetRecord,
    QuestionVersionRecord,
)

#: Estados de la propuesta de clasificación que siguen esperando a una persona.
_PENDING_PROPOSAL = "pending"

#: Estados de un mapeo que cuentan como asignación: lo provisional no es una decisión.
_ACCEPTED_MAPPING = "accepted"

#: Estados de conjunto que se estudian: un conjunto archivado no cuenta para la preparación.
_ARCHIVED_SET = "archived"

#: Estados de la versión de documento que cuentan como material: la aceptada está dentro; la
#: candidata, la sustituida, la retirada y la rechazada, no.
_ACCEPTED_VERSION = "accepted"
_CANDIDATE_VERSION = "candidate"


def _no_sustituidas() -> ColumnElement[bool]:
    """Filtro compartido: la versión sustituida de una pregunta no es una pregunta (DEBT-025)."""
    return QuestionVersionRecord.status != "superseded"


class SqlAlchemyReadinessRepository:
    """Los recuentos del resumen de preparación, en consultas agregadas."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    # ------------------------------------------------------------------ referencias

    def opposition(self, opposition_id: str) -> OppositionRef | None:
        """La oposición con su convocatoria activa, si la tiene."""
        with self._session_factory() as session:
            fila = session.get(OppositionRecord, opposition_id)
            if fila is None:
                return None
            convocatoria = session.execute(
                select(ConvocationVersionRecord.code)
                .where(
                    ConvocationVersionRecord.opposition_id == opposition_id,
                    ConvocationVersionRecord.status == "active",
                )
                .order_by(ConvocationVersionRecord.published_at.desc())
                .limit(1)
            ).scalar_one_or_none()
        return OppositionRef(
            id=str(fila.id),
            name=str(fila.name),
            convocation_code=str(convocatoria) if convocatoria is not None else None,
        )

    # ------------------------------------------------------------------ material

    def material(self, *, opposition_id: str) -> MaterialSummary:
        """Material aceptado por papel documental, y cuánto no está asignado a este programa.

        Cuenta **documentos**, no versiones: dos versiones del mismo temario son un temario. El
        papel se cuenta para todo lo aceptado —un documento no deja de ser apuntes por no estar
        asignado—, y lo que sí se mira contra esta oposición es cuánto no dice todavía a qué parte
        de su programa pertenece, que es lo que la cobertura por temas no ve.
        """
        with self._session_factory() as session:
            por_papel = session.execute(
                select(
                    LogicalDocumentRecord.document_type,
                    func.count(func.distinct(LogicalDocumentRecord.id)),
                )
                .join(
                    DocumentVersionRecord,
                    DocumentVersionRecord.logical_document_id == LogicalDocumentRecord.id,
                )
                .where(DocumentVersionRecord.status == _ACCEPTED_VERSION)
                .group_by(LogicalDocumentRecord.document_type)
                .order_by(func.count(func.distinct(LogicalDocumentRecord.id)).desc())
            ).all()
            asignacion = (
                select(CurriculumMappingRecord.id)
                .where(
                    CurriculumMappingRecord.subject_type == "document_version",
                    CurriculumMappingRecord.subject_id == DocumentVersionRecord.id,
                    CurriculumMappingRecord.status == _ACCEPTED_MAPPING,
                    CurriculumMappingRecord.curriculum_node_id.in_(
                        _node_ids_of_opposition(opposition_id)
                    ),
                )
                .exists()
            )
            sin_asignar = int(
                session.execute(
                    select(func.count(func.distinct(LogicalDocumentRecord.id)))
                    .select_from(DocumentVersionRecord)
                    .join(
                        LogicalDocumentRecord,
                        LogicalDocumentRecord.id == DocumentVersionRecord.logical_document_id,
                    )
                    .where(
                        DocumentVersionRecord.status == _ACCEPTED_VERSION,
                        ~asignacion,
                    )
                ).scalar_one()
            )
        filas = tuple((str(papel), int(cantidad)) for papel, cantidad in por_papel)
        return MaterialSummary(
            by_role=filas,
            total=sum(cantidad for _, cantidad in filas),
            unassigned=sin_asignar,
        )

    # ------------------------------------------------------------------ preguntas y claves

    def questions(self, *, opposition_id: str) -> QuestionSummary:
        """Preguntas de la oposición, con tema, y cuántos conjuntos tienen clave activa."""
        with self._session_factory() as session:
            conjuntos = self._set_ids(session, opposition_id)
            if not conjuntos:
                return QuestionSummary(
                    sets_total=0,
                    sets_with_active_key=0,
                    questions=0,
                    questions_with_topic=0,
                )
            con_tema = (
                session.query(CurriculumMappingRecord.id)
                .filter(
                    CurriculumMappingRecord.subject_type == "question_version",
                    CurriculumMappingRecord.subject_id == QuestionVersionRecord.id,
                    CurriculumMappingRecord.status == _ACCEPTED_MAPPING,
                )
                .exists()
            )
            total = int(
                session.execute(
                    select(func.count())
                    .select_from(QuestionVersionRecord)
                    .where(
                        QuestionVersionRecord.question_set_id.in_(conjuntos),
                        _no_sustituidas(),
                    )
                ).scalar_one()
            )
            catalogadas = int(
                session.execute(
                    select(func.count())
                    .select_from(QuestionVersionRecord)
                    .where(
                        QuestionVersionRecord.question_set_id.in_(conjuntos),
                        _no_sustituidas(),
                        con_tema,
                    )
                ).scalar_one()
            )
            con_clave = int(
                session.execute(
                    select(func.count(func.distinct(QuestionSetRecord.id)))
                    .select_from(QuestionSetRecord)
                    .where(
                        QuestionSetRecord.id.in_(conjuntos),
                        session.query(AnswerKeyVersionRecord.id)
                        .filter(
                            AnswerKeyVersionRecord.question_set_id == QuestionSetRecord.id,
                            AnswerKeyVersionRecord.status == "active",
                        )
                        .exists(),
                    )
                ).scalar_one()
            )
        return QuestionSummary(
            sets_total=len(conjuntos),
            sets_with_active_key=con_clave,
            questions=total,
            questions_with_topic=catalogadas,
        )

    @staticmethod
    def _set_ids(session: Session, opposition_id: str) -> list[str]:
        """Conjuntos de la oposición que se pueden estudiar: los archivados quedan fuera."""
        filas = session.execute(
            select(QuestionSetRecord.id).where(
                QuestionSetRecord.opposition_id == opposition_id,
                QuestionSetRecord.status != _ARCHIVED_SET,
            )
        ).scalars()
        return [str(fila) for fila in filas.all()]

    # ------------------------------------------------------------------ pendientes

    def pending(self) -> PendingCounts:
        """Lo que espera a una persona: incidencias, propuestas, cambios y versiones sin aceptar."""
        with self._session_factory() as session:
            incidencias = int(
                session.execute(
                    select(func.count())
                    .select_from(ImportIssueRecord)
                    .where(
                        ImportIssueRecord.resolved_at.is_(None),
                        ImportIssueRecord.severity.in_(("warning", "error")),
                    )
                ).scalar_one()
            )
            propuestas = int(
                session.execute(
                    select(func.count())
                    .select_from(ClassificationProposalRecord)
                    .where(ClassificationProposalRecord.status == _PENDING_PROPOSAL)
                ).scalar_one()
            )
            cambios = int(
                session.execute(
                    select(func.count())
                    .select_from(ChangeSetRecord)
                    .where(ChangeSetRecord.status == "proposed")
                ).scalar_one()
            )
            versiones = int(
                session.execute(
                    select(func.count())
                    .select_from(DocumentVersionRecord)
                    .where(DocumentVersionRecord.status == _CANDIDATE_VERSION)
                ).scalar_one()
            )
        return PendingCounts(
            import_issues=incidencias,
            pending_proposals=propuestas,
            proposed_changes=cambios,
            unaccepted_versions=versiones,
        )


def _node_ids_of_opposition(opposition_id: str) -> Select[tuple[str]]:
    """Nodos del programa de una oposición, por su convocatoria."""
    return (
        select(CurriculumNodeRecord.id)
        .join(
            ConvocationVersionRecord,
            ConvocationVersionRecord.id == CurriculumNodeRecord.convocation_version_id,
        )
        .where(ConvocationVersionRecord.opposition_id == opposition_id)
    )


__all__ = ["SqlAlchemyReadinessRepository"]
