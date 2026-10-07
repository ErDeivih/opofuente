"""Repositorio de errores, repaso y dominio (S10): estado, cola e historial.

Tres cosas que hace de una manera concreta:

1. **el historial se escribe, no se actualiza**: cada cambio de fecha de un repaso deja un evento
   con el intervalo anterior, el nuevo y su motivo. La fila del elemento dice dónde está; el
   historial, cómo llegó ahí;
2. **un solo repaso por pregunta** (índice único): si ya existe, un fallo nuevo lo reprograma en
   lugar de crear una cola paralela para la misma pregunta;
3. **la cola se ordena por lo vencido**: lo más atrasado primero y, a igualdad, lo que lleva más
   tiempo esperando. El orden no se deja al azar de la base.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from datetime import datetime
from uuid import uuid4

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session, sessionmaker

from opofuente.application.review_models import (
    ConceptGroupView,
    ConceptSummaryView,
    DueItemView,
    ErrorDetailView,
    ErrorView,
    NodeStudyState,
    ReviewEventView,
    ReviewItemView,
    ReviewStatsView,
)
from opofuente.domain.review import (
    ErrorCause,
    ErrorStatus,
    ReviewEventKind,
    ReviewOutcome,
    concept_key,
)
from opofuente.infrastructure.db import as_utc
from opofuente.infrastructure.db_models import (
    AttemptEvaluationRecord,
    AttemptRecord,
    CurriculumMappingRecord,
    CurriculumNodeRecord,
    LearningErrorRecord,
    OptionVersionRecord,
    QuestionVersionRecord,
    ReviewEventRecord,
    ReviewItemRecord,
    SessionQuestionRecord,
    StudySessionRecord,
)

#: Cuántos elementos devuelve la cola como mucho. Una cola de repaso no es un listado: es lo que
#: toca hoy, y con doscientos elementos lo que se hace es empezar por el primero.
DEFAULT_QUEUE_LIMIT = 50


def _new_id() -> str:
    return str(uuid4())


def _opciones(json_texto: str) -> tuple[str, ...]:
    try:
        datos = json.loads(json_texto)
    except json.JSONDecodeError:
        return ()
    if not isinstance(datos, list):
        return ()
    return tuple(str(valor) for valor in datos)


class SqlAlchemyReviewRepository:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    # ------------------------------------------------------------------ repaso: estado

    def active_item(self, question_version_id: str) -> ReviewItemView | None:
        with self._session_factory() as session:
            fila = session.execute(
                select(ReviewItemRecord).where(
                    ReviewItemRecord.question_version_id == question_version_id
                )
            ).scalar_one_or_none()
            return None if fila is None else self._item_view(fila)

    def item(self, review_id: str) -> ReviewItemView | None:
        with self._session_factory() as session:
            fila = session.get(ReviewItemRecord, review_id)
            return None if fila is None else self._item_view(fila)

    def save_item(
        self,
        *,
        review_id: str | None,
        question_version_id: str,
        opposition_id: str,
        learning_error_id: str | None,
        due_at: datetime,
        interval_days: int,
        repetitions: int,
        lapses: int,
        reason: str,
        reviewed_at: datetime | None,
        now: datetime,
    ) -> ReviewItemView:
        """Crea o actualiza el elemento de repaso. Devuelve cómo ha quedado."""
        with self._session_factory() as session:
            fila = None if review_id is None else session.get(ReviewItemRecord, review_id)
            if fila is None:
                fila = ReviewItemRecord(
                    id=review_id or _new_id(),
                    question_version_id=question_version_id,
                    opposition_id=opposition_id,
                    learning_error_id=learning_error_id,
                    due_at=due_at,
                    interval_days=interval_days,
                    repetitions=repetitions,
                    lapses=lapses,
                    last_reviewed_at=reviewed_at,
                    last_reason=reason,
                    created_at=now,
                    updated_at=now,
                )
                session.add(fila)
            else:
                fila.due_at = due_at
                fila.interval_days = interval_days
                fila.repetitions = repetitions
                fila.lapses = lapses
                fila.last_reason = reason
                fila.updated_at = now
                if reviewed_at is not None:
                    fila.last_reviewed_at = reviewed_at
                if learning_error_id is not None:
                    fila.learning_error_id = learning_error_id
            session.commit()
            return self._item_view(fila)

    def record_event(
        self,
        *,
        review_item_id: str,
        kind: ReviewEventKind,
        outcome: str | None,
        confidence: str | None,
        cause: str | None,
        note: str | None,
        previous_due_at: datetime | None,
        due_at: datetime,
        previous_interval_days: int | None,
        interval_days: int,
        repetitions: int,
        reason: str,
        now: datetime,
    ) -> None:
        with self._session_factory() as session:
            session.add(
                ReviewEventRecord(
                    id=_new_id(),
                    review_item_id=review_item_id,
                    kind=kind.value,
                    outcome=outcome,
                    confidence=confidence,
                    cause=cause,
                    note=note,
                    previous_due_at=previous_due_at,
                    due_at=due_at,
                    previous_interval_days=previous_interval_days,
                    interval_days=interval_days,
                    repetitions=repetitions,
                    reason=reason,
                    occurred_at=now,
                )
            )
            session.commit()

    def events(self, review_item_id: str, *, limit: int = 50) -> tuple[ReviewEventView, ...]:
        with self._session_factory() as session:
            filas = session.execute(
                select(ReviewEventRecord)
                .where(ReviewEventRecord.review_item_id == review_item_id)
                .order_by(ReviewEventRecord.occurred_at.desc())
                .limit(limit)
            ).scalars()
            return tuple(self._event_view(fila) for fila in filas)

    # ------------------------------------------------------------------ la cola de hoy

    def due(
        self,
        *,
        opposition_id: str | None,
        now: datetime,
        limit: int = DEFAULT_QUEUE_LIMIT,
        include_future: bool = False,
    ) -> tuple[DueItemView, ...]:
        """Lo que toca hoy, con la explicación de por qué está en la cola."""
        with self._session_factory() as session:
            consulta = (
                select(
                    ReviewItemRecord,
                    QuestionVersionRecord,
                    SessionQuestionRecord,
                    StudySessionRecord,
                )
                .join(
                    QuestionVersionRecord,
                    QuestionVersionRecord.id == ReviewItemRecord.question_version_id,
                )
                .join(
                    SessionQuestionRecord,
                    SessionQuestionRecord.question_version_id == QuestionVersionRecord.id,
                )
                .join(
                    StudySessionRecord,
                    StudySessionRecord.id == SessionQuestionRecord.session_id,
                )
                .order_by(ReviewItemRecord.due_at.asc(), ReviewItemRecord.created_at.asc())
                .limit(limit)
            )
            if opposition_id is not None:
                consulta = consulta.where(ReviewItemRecord.opposition_id == opposition_id)
            if not include_future:
                consulta = consulta.where(ReviewItemRecord.due_at <= now)
            vistas: list[DueItemView] = []
            vistos: set[str] = set()
            for item, pregunta, pregunta_sesion, sesion in session.execute(consulta).all():
                # La pregunta puede estar en varias sesiones: se enseña una vez, la última.
                if item.question_version_id in vistos:
                    continue
                vistos.add(item.question_version_id)
                vistas.append(
                    DueItemView(
                        item=self._item_view(item),
                        question_version_id=pregunta.id,
                        question_set_id=pregunta.question_set_id,
                        stable_key=pregunta.stable_key,
                        stem=pregunta.stem,
                        part_code=pregunta_sesion.part_code,
                        is_reserve=bool(pregunta.is_reserve),
                        origin_type=pregunta.origin_type,
                        overdue_days=max(0, (now - (as_utc(item.due_at) or now)).days),
                        explanation=item.last_reason
                        or "está en la cola porque se falló y todavía no se ha repasado",
                        options=self._options_of(session, pregunta.id),
                        session_id=sesion.id,
                    )
                )
            return tuple(vistas)

    @staticmethod
    def _options_of(session: Session, question_version_id: str) -> tuple[tuple[str, str], ...]:
        filas = session.execute(
            select(OptionVersionRecord)
            .where(OptionVersionRecord.question_version_id == question_version_id)
            .order_by(OptionVersionRecord.position)
        ).scalars()
        return tuple((fila.stable_key, fila.text) for fila in filas)

    def stats(self, *, opposition_id: str | None, now: datetime) -> ReviewStatsView:
        with self._session_factory() as session:
            filtros = []
            if opposition_id is not None:
                filtros.append(ReviewItemRecord.opposition_id == opposition_id)
            filas = session.execute(
                select(
                    func.count(),
                    func.sum(case((ReviewItemRecord.due_at <= now, 1), else_=0)),
                    func.min(ReviewItemRecord.due_at),
                    func.sum(ReviewItemRecord.lapses),
                )
                .select_from(ReviewItemRecord)
                .where(*filtros)
            ).one()
            total, vencidos, proximo, fallos = filas
            return ReviewStatsView(
                active=int(total or 0),
                due=int(vencidos or 0),
                next_due_at=proximo,
                lapses=int(fallos or 0),
            )

    # ------------------------------------------------------------------ errores declarados

    def save_error(
        self,
        *,
        attempt_id: str,
        cause: str,
        concept_label: str | None,
        curriculum_node_id: str | None,
        note: str | None,
        now: datetime,
    ) -> ErrorView | None:
        """Declara la causa de un fallo. Si ya estaba declarada, se **corrige**, no se duplica."""
        with self._session_factory() as session:
            intento = session.get(AttemptRecord, attempt_id)
            if intento is None:
                return None
            existente = session.execute(
                select(LearningErrorRecord).where(LearningErrorRecord.attempt_id == attempt_id)
            ).scalar_one_or_none()
            if existente is None:
                fila = LearningErrorRecord(
                    id=_new_id(),
                    attempt_id=attempt_id,
                    # El dueño es el del intento: un fallo no es de quien lo declara, es de quien
                    # falló, y el intento ya lo dice (0027).
                    owner_id=str(intento.owner_id),
                    curriculum_node_id=curriculum_node_id,
                    concept_label=concept_label,
                    cause=cause,
                    user_note=note,
                    status=ErrorStatus.OPEN.value,
                    occurrences=1,
                    first_seen_at=now,
                    last_seen_at=now,
                    resolved_at=None,
                )
                session.add(fila)
            else:
                fila = existente
                fila.cause = cause
                fila.curriculum_node_id = curriculum_node_id
                fila.concept_label = concept_label
                fila.user_note = note
                fila.last_seen_at = now
            session.commit()
            return self._error_view(session, fila)

    def error_for_attempt(self, attempt_id: str) -> ErrorView | None:
        with self._session_factory() as session:
            fila = session.execute(
                select(LearningErrorRecord).where(LearningErrorRecord.attempt_id == attempt_id)
            ).scalar_one_or_none()
            return None if fila is None else self._error_view(session, fila)

    def error(self, error_id: str) -> ErrorDetailView | None:
        with self._session_factory() as session:
            fila = session.get(LearningErrorRecord, error_id)
            if fila is None:
                return None
            base = self._error_view(session, fila)
            intento = session.get(AttemptRecord, fila.attempt_id)
            item = session.execute(
                select(ReviewItemRecord).where(
                    ReviewItemRecord.question_version_id == base.question_version_id
                )
            ).scalar_one_or_none()
            eventos = (
                ()
                if item is None
                else tuple(
                    self._event_view(evento)
                    for evento in session.execute(
                        select(ReviewEventRecord)
                        .where(ReviewEventRecord.review_item_id == item.id)
                        .order_by(ReviewEventRecord.occurred_at.desc())
                    ).scalars()
                )
            )
            return ErrorDetailView(
                error=base,
                chosen_option_keys=()
                if intento is None
                else _opciones(intento.chosen_option_keys_json),
                confidence=None if intento is None else intento.confidence,
                answered_at=None if intento is None else intento.answered_at,
                review=None if item is None else self._item_view(item),
                events=eventos,
            )

    def resolve_error(self, error_id: str, *, note: str | None, now: datetime) -> ErrorView | None:
        with self._session_factory() as session:
            fila = session.get(LearningErrorRecord, error_id)
            if fila is None:
                return None
            fila.status = ErrorStatus.RESOLVED.value
            fila.resolved_at = now
            fila.last_seen_at = now
            if note is not None:
                fila.user_note = note
            session.commit()
            return self._error_view(session, fila)

    def reopen_error(self, error_id: str, *, now: datetime) -> ErrorView | None:
        with self._session_factory() as session:
            fila = session.get(LearningErrorRecord, error_id)
            if fila is None:
                return None
            fila.status = ErrorStatus.OPEN.value
            fila.resolved_at = None
            fila.last_seen_at = now
            session.commit()
            return self._error_view(session, fila)

    def errors(
        self,
        *,
        opposition_id: str | None,
        status: str | None,
        cause: str | None,
        limit: int = 200,
    ) -> tuple[ErrorView, ...]:
        with self._session_factory() as session:
            consulta = (
                select(LearningErrorRecord)
                .order_by(LearningErrorRecord.last_seen_at.desc())
                .limit(limit)
            )
            if status is not None:
                consulta = consulta.where(LearningErrorRecord.status == status)
            if cause is not None:
                consulta = consulta.where(LearningErrorRecord.cause == cause)
            if opposition_id is not None:
                consulta = consulta.where(
                    LearningErrorRecord.attempt_id.in_(
                        select(AttemptRecord.id)
                        .join(
                            SessionQuestionRecord,
                            SessionQuestionRecord.id == AttemptRecord.session_question_id,
                        )
                        .join(
                            StudySessionRecord,
                            StudySessionRecord.id == SessionQuestionRecord.session_id,
                        )
                        .where(StudySessionRecord.opposition_id == opposition_id)
                    )
                )
            return tuple(
                self._error_view(session, fila) for fila in session.execute(consulta).scalars()
            )

    def concepts(
        self, *, opposition_id: str | None, now: datetime
    ) -> tuple[ConceptSummaryView, ...]:
        """Agrupa los errores por concepto, con lo que hay que saber de cada grupo.

        La agrupación la decide el dominio (`concept_key`): el nodo del programa cuando existe y, si
        no, la etiqueta normalizada. Se hace en memoria porque el número de errores de una persona
        es pequeño y así una sola regla (la del dominio) vale para todas las vistas.
        """
        errores = self.errors(opposition_id=opposition_id, status=None, cause=None, limit=500)
        grupos: dict[str, list[ErrorView]] = {}
        etiquetas: dict[str, tuple[datetime, str]] = {}
        for error in errores:
            clave = concept_key(error.concept_label, curriculum_node_id=error.curriculum_node_id)
            grupos.setdefault(clave, []).append(error)
            # La etiqueta del grupo es la del **primer** error que lo abrió: si se tomara la del
            # último, el mismo concepto cambiaría de nombre cada vez que se vuelve a fallar.
            candidata = error.node_title or error.concept_label or "sin concepto declarado"
            anterior = etiquetas.get(clave)
            if anterior is None or error.first_seen_at < anterior[0]:
                etiquetas[clave] = (error.first_seen_at, candidata)
        resumen: list[ConceptSummaryView] = []
        for clave, entradas in grupos.items():
            abiertos = sum(1 for entrada in entradas if entrada.status == ErrorStatus.OPEN.value)
            resumen.append(
                ConceptSummaryView(
                    key=clave,
                    label=etiquetas[clave][1],
                    errors=tuple(sorted(entradas, key=lambda e: e.last_seen_at, reverse=True)),
                    open_count=abiertos,
                    resolved_count=len(entradas) - abiertos,
                    occurrences=sum(entrada.occurrences for entrada in entradas),
                    last_seen_at=max(entrada.last_seen_at for entrada in entradas),
                    node_id=entradas[0].curriculum_node_id,
                )
            )
        resumen.sort(key=lambda grupo: (grupo.open_count == 0, -grupo.occurrences, grupo.label))
        return tuple(resumen)

    # ------------------------------------------------------------------ dominio por nodo

    def node_attempts(
        self, node_ids: Sequence[str], *, now: datetime
    ) -> dict[str, tuple[tuple[bool, datetime], ...]]:
        """Los intentos de las preguntas asignadas a cada nodo, para estimar su dominio.

        Se usa la evaluación **vigente** de cada intento (la última de cada clave), que es la misma
        que enseña el resultado de una sesión: contar una evaluación sustituida haría que un
        recálculo cambiara el dominio sin que nadie hubiera estudiado nada más.
        """
        if not node_ids:
            return {}
        with self._session_factory() as session:
            filas = session.execute(
                select(
                    CurriculumMappingRecord.curriculum_node_id,
                    AttemptRecord.id,
                    AttemptEvaluationRecord.outcome,
                    AttemptRecord.answered_at,
                    AttemptEvaluationRecord.evaluated_at,
                )
                .select_from(CurriculumMappingRecord)
                .join(
                    SessionQuestionRecord,
                    SessionQuestionRecord.question_version_id == CurriculumMappingRecord.subject_id,
                )
                .join(
                    AttemptRecord,
                    AttemptRecord.session_question_id == SessionQuestionRecord.id,
                )
                .join(
                    AttemptEvaluationRecord,
                    AttemptEvaluationRecord.attempt_id == AttemptRecord.id,
                )
                .where(
                    CurriculumMappingRecord.subject_type == "question_version",
                    CurriculumMappingRecord.status == "accepted",
                    CurriculumMappingRecord.curriculum_node_id.in_(tuple(node_ids)),
                    AttemptEvaluationRecord.outcome.in_(("correct", "wrong", "blank")),
                )
            ).all()
        # Un intento puede tener varias evaluaciones (una por clave tras un recálculo): la vigente
        # es la última, y es la que cuenta para el dominio.
        vigentes: dict[tuple[str, str], tuple[bool, datetime, datetime]] = {}
        for node_id, attempt_id, outcome, answered_at, evaluated_at in filas:
            clave = (str(node_id), str(attempt_id))
            anterior = vigentes.get(clave)
            if anterior is None or evaluated_at >= anterior[2]:
                vigentes[clave] = (outcome == "correct", answered_at, evaluated_at)
        acumulado: dict[str, list[tuple[bool, datetime]]] = {}
        for (node_id, _), (correcto, answered_at, _) in vigentes.items():
            acumulado.setdefault(node_id, []).append((correcto, as_utc(answered_at) or answered_at))
        return {node_id: tuple(intentos) for node_id, intentos in acumulado.items()}

    def node_study_state(
        self, node_ids: Sequence[str], *, now: datetime
    ) -> dict[str, NodeStudyState]:
        """Qué preguntas tiene cada nodo y cuándo toca repasarlas (DEBT-027 §5).

        Dos consultas agregadas, no dos listados: el árbol del programa tiene decenas de nodos y
        traerse las preguntas de cada uno para contarlas en memoria es lo que este proyecto evita.

        Cuenta **versiones vigentes con mapeo aceptado**: la misma regla que usan el banco, la
        cobertura y la preparación. Si aquí contara otra cosa, la pantalla de Programa y la de
        Preguntas darían dos cifras distintas de lo mismo.

        El `JOIN` con `review_items` es por la versión de pregunta mapeada, así que un repaso cuenta
        para el nodo en el que está catalogada su pregunta.
        """
        if not node_ids:
            return {}
        nodos = tuple(node_ids)
        with self._session_factory() as session:
            # Una sola consulta agrupada por estado y origen: son los dos ejes que pide 07_UI-UX §5
            # («preguntas: oficiales/verificadas/dudosas») y así no se recorren las preguntas dos
            # veces.
            por_estado_y_origen = session.execute(
                select(
                    CurriculumMappingRecord.curriculum_node_id,
                    QuestionVersionRecord.status,
                    QuestionVersionRecord.origin_type,
                    func.count(QuestionVersionRecord.id),
                )
                .select_from(CurriculumMappingRecord)
                .join(
                    QuestionVersionRecord,
                    QuestionVersionRecord.id == CurriculumMappingRecord.subject_id,
                )
                .where(
                    CurriculumMappingRecord.subject_type == "question_version",
                    CurriculumMappingRecord.status == "accepted",
                    CurriculumMappingRecord.curriculum_node_id.in_(nodos),
                    QuestionVersionRecord.status != "superseded",
                )
                .group_by(
                    CurriculumMappingRecord.curriculum_node_id,
                    QuestionVersionRecord.status,
                    QuestionVersionRecord.origin_type,
                )
            ).all()
            repasos = session.execute(
                select(
                    CurriculumMappingRecord.curriculum_node_id,
                    func.count(ReviewItemRecord.id),
                    func.min(ReviewItemRecord.due_at),
                )
                .select_from(CurriculumMappingRecord)
                .join(
                    ReviewItemRecord,
                    ReviewItemRecord.question_version_id == CurriculumMappingRecord.subject_id,
                )
                .where(
                    CurriculumMappingRecord.subject_type == "question_version",
                    CurriculumMappingRecord.status == "accepted",
                    CurriculumMappingRecord.curriculum_node_id.in_(nodos),
                    # El siguiente repaso **programado** es el que aún no ha vencido: los vencidos
                    # se cuentan aparte (`reviews_due`), y dar aquí una fecha pasada confundiría
                    # «toca ahora» con «toca el día 25».
                    ReviewItemRecord.due_at > now,
                )
                .group_by(CurriculumMappingRecord.curriculum_node_id)
            ).all()
            vencidos = {
                str(nodo): int(cantidad)
                for nodo, cantidad in session.execute(
                    select(
                        CurriculumMappingRecord.curriculum_node_id,
                        func.count(ReviewItemRecord.id),
                    )
                    .select_from(CurriculumMappingRecord)
                    .join(
                        ReviewItemRecord,
                        ReviewItemRecord.question_version_id == CurriculumMappingRecord.subject_id,
                    )
                    .where(
                        CurriculumMappingRecord.subject_type == "question_version",
                        CurriculumMappingRecord.status == "accepted",
                        CurriculumMappingRecord.curriculum_node_id.in_(nodos),
                        ReviewItemRecord.due_at <= now,
                    )
                    .group_by(CurriculumMappingRecord.curriculum_node_id)
                ).all()
            }

        estados: dict[str, dict[str, int]] = {}
        origenes: dict[str, dict[str, int]] = {}
        for nodo, estado, origen, cantidad in por_estado_y_origen:
            estados.setdefault(str(nodo), {})[str(estado)] = estados.get(str(nodo), {}).get(
                str(estado), 0
            ) + int(cantidad)
            origenes.setdefault(str(nodo), {})[str(origen)] = origenes.get(str(nodo), {}).get(
                str(origen), 0
            ) + int(cantidad)
        siguientes = {
            str(nodo): as_utc(proximo) for nodo, _, proximo in repasos if proximo is not None
        }

        def _recuento(
            acumulado: dict[str, dict[str, int]], nodo: str
        ) -> tuple[tuple[str, int], ...]:
            return tuple(sorted(acumulado.get(nodo, {}).items()))

        return {
            nodo: NodeStudyState(
                curriculum_node_id=nodo,
                questions_by_status=_recuento(estados, nodo),
                questions_by_origin=_recuento(origenes, nodo),
                reviews_due=vencidos.get(nodo, 0),
                next_review_at=siguientes.get(nodo),
            )
            for nodo in nodos
        }

    # ------------------------------------------------------------------ vistas

    @staticmethod
    def _item_view(fila: ReviewItemRecord) -> ReviewItemView:
        return ReviewItemView(
            id=fila.id,
            question_version_id=fila.question_version_id,
            opposition_id=fila.opposition_id,
            learning_error_id=fila.learning_error_id,
            due_at=as_utc(fila.due_at) or fila.due_at,
            interval_days=fila.interval_days,
            repetitions=fila.repetitions,
            lapses=fila.lapses,
            last_reviewed_at=as_utc(fila.last_reviewed_at),
            last_reason=fila.last_reason,
            created_at=as_utc(fila.created_at) or fila.created_at,
            updated_at=as_utc(fila.updated_at) or fila.updated_at,
        )

    @staticmethod
    def _event_view(fila: ReviewEventRecord) -> ReviewEventView:
        return ReviewEventView(
            id=fila.id,
            kind=fila.kind,
            outcome=None if fila.outcome is None else ReviewOutcome(fila.outcome),
            confidence=fila.confidence,
            cause=None if fila.cause is None else ErrorCause(fila.cause),
            note=fila.note,
            previous_due_at=as_utc(fila.previous_due_at),
            due_at=as_utc(fila.due_at) or fila.due_at,
            previous_interval_days=fila.previous_interval_days,
            interval_days=fila.interval_days,
            repetitions=fila.repetitions,
            reason=fila.reason,
            occurred_at=as_utc(fila.occurred_at) or fila.occurred_at,
        )

    @staticmethod
    def _error_view(session: Session, fila: LearningErrorRecord) -> ErrorView:
        pregunta = session.execute(
            select(QuestionVersionRecord, SessionQuestionRecord, StudySessionRecord)
            .join(
                SessionQuestionRecord,
                SessionQuestionRecord.question_version_id == QuestionVersionRecord.id,
            )
            .join(AttemptRecord, AttemptRecord.session_question_id == SessionQuestionRecord.id)
            .join(
                StudySessionRecord,
                StudySessionRecord.id == SessionQuestionRecord.session_id,
            )
            .where(AttemptRecord.id == fila.attempt_id)
        ).first()
        nodo = (
            None
            if fila.curriculum_node_id is None
            else session.get(CurriculumNodeRecord, fila.curriculum_node_id)
        )
        return ErrorView(
            id=fila.id,
            attempt_id=fila.attempt_id,
            question_version_id=None if pregunta is None else pregunta[0].id,
            stable_key=None if pregunta is None else pregunta[0].stable_key,
            stem=None if pregunta is None else pregunta[0].stem,
            session_id=None if pregunta is None else pregunta[2].id,
            part_code=None if pregunta is None else pregunta[1].part_code,
            curriculum_node_id=fila.curriculum_node_id,
            node_title=None if nodo is None else nodo.title,
            concept_label=fila.concept_label,
            cause=ErrorCause(fila.cause),
            user_note=fila.user_note,
            status=fila.status,
            occurrences=fila.occurrences,
            first_seen_at=as_utc(fila.first_seen_at) or fila.first_seen_at,
            last_seen_at=as_utc(fila.last_seen_at) or fila.last_seen_at,
            resolved_at=as_utc(fila.resolved_at),
        )


def group_summary(groups: Sequence[ConceptSummaryView]) -> ConceptGroupView:
    """Resumen de los grupos de conceptos, para la cabecera de la vista."""
    return ConceptGroupView(
        groups=tuple(groups),
        total_errors=sum(len(grupo.errors) for grupo in groups),
        open_errors=sum(grupo.open_count for grupo in groups),
    )


__all__ = [
    "DEFAULT_QUEUE_LIMIT",
    "SqlAlchemyReviewRepository",
    "group_summary",
]
