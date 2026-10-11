"""Consultas del progreso del alumno (F2).

Es un repositorio **de lectura** y tiene las consultas agregadas que la zona del alumno necesita más
una de estado (qué temas tienen sus apuntes publicados). Todas las del progreso comparten tres
filtros, y los tres son la razón de que este fichero exista:

1. **la oposición**, siempre: el progreso de otro cuerpo no aparece por aquí ni en forma de cuenta
   (es el requisito de aislamiento de la fase);
2. **el dueño del progreso** (`owner_id`), siempre: hoy es `'local'`, y el filtro ya está para que
el
   día que haya cuentas nadie tenga que acordarse;
3. **`public` cuando el modo público está activo**: con la zona abierta, un banco privado del
   propietario no puede contar ni en un recuento.

Las cifras se calculan **en SQL** y no en Python a propósito: la zona del alumno pide el programa
entero (4 bloques, 33 temas) en cada carga, y traer todas las filas para contarlas aquí haría que la
pantalla tardara más cuanta más gente estudiara.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from typing import Any

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session, sessionmaker

from opofuente.domain.topic_notes import NotesState
from opofuente.infrastructure.db_models import (
    AttemptEvaluationRecord,
    AttemptRecord,
    CurriculumMappingRecord,
    DossierSnapshotRecord,
    QuestionSetRecord,
    QuestionVersionRecord,
    ReviewItemRecord,
    SessionQuestionRecord,
    StudySessionRecord,
    TopicNoteSectionRecord,
)

#: Los desenlaces que cuentan para el porcentaje de acierto: los tres que puntúan, con el blanco
#: dentro. Un blanco no es un acierto, y dejarlo fuera subiría el porcentaje sin haber acertado
#: nada.
OUTCOMES_QUE_CUENTAN: tuple[str, ...] = ("correct", "wrong", "blank")


def _solo_publicos[Fila: tuple[Any, ...]](
    consulta: Select[Fila], public_only: bool
) -> Select[Fila]:
    """Añade el filtro de visibilidad pública cuando la zona del alumno está abierta.

    La consulta que llega tiene que traer ya `question_sets` unido: el filtro es del conjunto,
    que es donde vive `distribution`, no de la pregunta.
    """
    if not public_only:
        return consulta
    return consulta.where(QuestionSetRecord.distribution == "public")


class SqlAlchemyStudentRepository:
    """Las consultas del progreso del alumno, y nada más."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    # ------------------------------------------------------------------ recuentos

    def question_counts(self, opposition_id: str, *, public_only: bool) -> Mapping[str, int]:
        """Preguntas **disponibles** por nodo del programa: catalogadas y vigentes.

        Es la misma regla que la cifra «preguntas: N» del Programa —mapeo aceptado— más los dos
        filtros de esta capa (la oposición del alumno y, en modo público, solo conjuntos públicos).
        Una versión sustituida no cuenta: ya no se practica.
        """
        consulta = (
            select(
                CurriculumMappingRecord.curriculum_node_id,
                func.count(func.distinct(QuestionVersionRecord.id)),
            )
            .join(
                QuestionVersionRecord,
                QuestionVersionRecord.id == CurriculumMappingRecord.subject_id,
            )
            .join(QuestionSetRecord, QuestionSetRecord.id == QuestionVersionRecord.question_set_id)
            .where(
                CurriculumMappingRecord.subject_type == "question_version",
                CurriculumMappingRecord.status == "accepted",
                QuestionVersionRecord.status != "superseded",
                QuestionSetRecord.status != "archived",
                QuestionSetRecord.opposition_id == opposition_id,
            )
            .group_by(CurriculumMappingRecord.curriculum_node_id)
        )
        with self._session_factory() as session:
            filas = session.execute(_solo_publicos(consulta, public_only)).all()
        return {str(nodo): int(total) for nodo, total in filas}

    def answered_counts(
        self, opposition_id: str, owner_id: str, *, public_only: bool
    ) -> Mapping[str, int]:
        """Preguntas **vistas** por nodo: intentos registrados, se hayan corregido o no.

        El intento cuenta aunque la sesión no se haya cerrado y la corrección no se pueda enseñar:
        «vistas» es lo que el alumno ha hecho, no lo que ya sabe.
        """
        consulta = (
            select(
                CurriculumMappingRecord.curriculum_node_id,
                func.count(func.distinct(AttemptRecord.id)),
            )
            .select_from(AttemptRecord)
            .join(
                SessionQuestionRecord,
                SessionQuestionRecord.id == AttemptRecord.session_question_id,
            )
            .join(StudySessionRecord, StudySessionRecord.id == SessionQuestionRecord.session_id)
            .join(
                QuestionVersionRecord,
                QuestionVersionRecord.id == SessionQuestionRecord.question_version_id,
            )
            .join(QuestionSetRecord, QuestionSetRecord.id == QuestionVersionRecord.question_set_id)
            .join(
                CurriculumMappingRecord,
                (CurriculumMappingRecord.subject_id == SessionQuestionRecord.question_version_id)
                & (CurriculumMappingRecord.subject_type == "question_version")
                & (CurriculumMappingRecord.status == "accepted"),
            )
            .where(
                StudySessionRecord.opposition_id == opposition_id,
                StudySessionRecord.owner_id == owner_id,
                QuestionSetRecord.opposition_id == opposition_id,
            )
            .group_by(CurriculumMappingRecord.curriculum_node_id)
        )
        with self._session_factory() as session:
            filas = session.execute(_solo_publicos(consulta, public_only)).all()
        return {str(nodo): int(total) for nodo, total in filas}

    def outcome_counts(
        self, opposition_id: str, owner_id: str, *, public_only: bool
    ) -> Mapping[str, Mapping[str, int]]:
        """Desenlaces por nodo, con la evaluación **vigente** de cada intento.

        Recalcular con una clave nueva crea una evaluación nueva y no borra la anterior (invariante
        7): sumar todas contaría dos veces el mismo intento. La vigente es la última por fecha y, a
        igualdad, por identificador — el mismo desempate que usa el repositorio de estudio.
        """
        vigente = (
            select(AttemptEvaluationRecord.id)
            .where(AttemptEvaluationRecord.attempt_id == AttemptRecord.id)
            .order_by(
                AttemptEvaluationRecord.evaluated_at.desc(),
                AttemptEvaluationRecord.id.desc(),
            )
            .limit(1)
            # `correlate` explícito: la consulta de fuera también trae `attempt_evaluations`, así
            # que sin esto SQLAlchemy autocorrelaciona **la propia tabla de dentro** y la
            # subconsulta se queda sin `FROM` («returned no FROM clauses due to auto-correlation»).
            # Solo se correlaciona el intento, que es lo único que viene de fuera.
            .correlate(AttemptRecord)
            .scalar_subquery()
        )
        consulta = (
            select(
                CurriculumMappingRecord.curriculum_node_id,
                AttemptEvaluationRecord.outcome,
                func.count(func.distinct(AttemptEvaluationRecord.id)),
            )
            .select_from(AttemptEvaluationRecord)
            .join(AttemptRecord, AttemptRecord.id == AttemptEvaluationRecord.attempt_id)
            .join(
                SessionQuestionRecord,
                SessionQuestionRecord.id == AttemptRecord.session_question_id,
            )
            .join(StudySessionRecord, StudySessionRecord.id == SessionQuestionRecord.session_id)
            .join(
                QuestionVersionRecord,
                QuestionVersionRecord.id == SessionQuestionRecord.question_version_id,
            )
            .join(QuestionSetRecord, QuestionSetRecord.id == QuestionVersionRecord.question_set_id)
            .join(
                CurriculumMappingRecord,
                (CurriculumMappingRecord.subject_id == SessionQuestionRecord.question_version_id)
                & (CurriculumMappingRecord.subject_type == "question_version")
                & (CurriculumMappingRecord.status == "accepted"),
            )
            .where(
                StudySessionRecord.opposition_id == opposition_id,
                StudySessionRecord.owner_id == owner_id,
                QuestionSetRecord.opposition_id == opposition_id,
                AttemptEvaluationRecord.outcome.in_(OUTCOMES_QUE_CUENTAN),
                AttemptEvaluationRecord.id == vigente,
            )
            .group_by(CurriculumMappingRecord.curriculum_node_id, AttemptEvaluationRecord.outcome)
        )
        with self._session_factory() as session:
            filas = session.execute(_solo_publicos(consulta, public_only)).all()
        recuentos: dict[str, dict[str, int]] = {}
        for nodo, desenlace, total in filas:
            recuentos.setdefault(str(nodo), {})[str(desenlace)] = int(total)
        return recuentos

    def public_set_ids(self, opposition_id: str) -> frozenset[str]:
        """Los conjuntos **publicables** de esta oposición: con ellos se decide qué sesión se sirve.

        Es la consulta que hace que el modo público no sea solo un filtro de recuentos: en modo
        público, un test cuyas preguntas salen de un banco privado del propietario no se enseña ni
        en el historial, porque su nota y sus aciertos son información de ese banco.
        """
        with self._session_factory() as session:
            filas = session.execute(
                select(QuestionSetRecord.id).where(
                    QuestionSetRecord.opposition_id == opposition_id,
                    QuestionSetRecord.distribution == "public",
                    QuestionSetRecord.status != "archived",
                )
            ).scalars()
            return frozenset(str(fila) for fila in filas)

    def due_counts(
        self,
        opposition_id: str,
        owner_id: str,
        *,
        now: datetime,
        public_only: bool,
    ) -> tuple[int, Mapping[str, int]]:
        """Fallos vencidos: el total y su reparto por tema `(total, {nodo: cuántos})`.

        Un fallo vencido es una pregunta de repaso cuya fecha ya pasó **y** que esta persona falló
        de
        verdad: la cola de repaso se llena sola al responder, así que sin el `EXISTS` sobre los
        intentos del dueño se contarían repasos de sesiones que no son suyos.

        El total **no** exige que la pregunta esté catalogada en un tema: una pregunta sin tema
        también se repasa, y el total tiene que cuadrar con la lista que la pantalla enseña.
        """
        del_dueno = (
            select(func.count())
            .select_from(AttemptRecord)
            .join(
                SessionQuestionRecord,
                SessionQuestionRecord.id == AttemptRecord.session_question_id,
            )
            .join(StudySessionRecord, StudySessionRecord.id == SessionQuestionRecord.session_id)
            .where(
                SessionQuestionRecord.question_version_id == ReviewItemRecord.question_version_id,
                StudySessionRecord.owner_id == owner_id,
                StudySessionRecord.opposition_id == opposition_id,
            )
            .exists()
        )
        base = (
            select(ReviewItemRecord.id, ReviewItemRecord.question_version_id)
            .join(
                QuestionVersionRecord,
                QuestionVersionRecord.id == ReviewItemRecord.question_version_id,
            )
            .join(QuestionSetRecord, QuestionSetRecord.id == QuestionVersionRecord.question_set_id)
            .where(
                ReviewItemRecord.opposition_id == opposition_id,
                ReviewItemRecord.due_at <= now,
                QuestionSetRecord.opposition_id == opposition_id,
                del_dueno,
            )
        )
        with self._session_factory() as session:
            vencidos = session.execute(_solo_publicos(base, public_only)).all()
            if not vencidos:
                return 0, {}
            por_pregunta = {str(pregunta) for _, pregunta in vencidos}
            mapeos = session.execute(
                select(
                    CurriculumMappingRecord.curriculum_node_id,
                    CurriculumMappingRecord.subject_id,
                ).where(
                    CurriculumMappingRecord.subject_type == "question_version",
                    CurriculumMappingRecord.status == "accepted",
                    CurriculumMappingRecord.subject_id.in_(por_pregunta),
                )
            ).all()
        por_nodo: dict[str, int] = {}
        for nodo, _pregunta in mapeos:
            por_nodo[str(nodo)] = por_nodo.get(str(nodo), 0) + 1
        return len(vencidos), por_nodo

    def notes_states(self) -> Mapping[str, NotesState]:
        """El estado de los apuntes de cada tema que **tiene apartados escritos**.

        Un tema que no aparece aquí no tiene apuntes (`NotesState.NONE`), y quien pregunta lo dice
        con su valor por defecto: devolver una fila «sin apuntes» por cada nodo del programa sería
        escribir 33 ceros para contar tres temas.

        Lo que separa el borrador del publicado no es el texto —los tres temas redactados lo
        tienen—, sino la **versión archivada**: el tema que pasa las dos puertas del §2.3 archiva su
        versión y es lo que la marca «Versión generada · en revisión» señala al alumno. Un tema con
        texto y sin versión se lee igual, y la pantalla dice que está en borrador.
        """
        with self._session_factory() as session:
            con_apartados = set(
                session.execute(
                    select(TopicNoteSectionRecord.curriculum_node_id).distinct()
                ).scalars()
            )
            publicados = set(
                session.execute(
                    select(DossierSnapshotRecord.curriculum_node_id).distinct()
                ).scalars()
            )
        return {
            str(nodo): (NotesState.PUBLISHED if str(nodo) in publicados else NotesState.DRAFT)
            for nodo in con_apartados
        }
