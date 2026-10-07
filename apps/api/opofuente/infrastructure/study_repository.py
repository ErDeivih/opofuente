"""Repositorio de sesiones de estudio (S07): sesiones, composición, intentos y evaluaciones.

Dos cosas que este repositorio hace de una manera concreta y conviene saber por qué:

1. **La composición se congela al crearla**: `create_session` inserta la sesión y sus preguntas
   en la misma transacción, con la clave de cada pregunta copiada tal como estaba. No hay ninguna
   ruta que modifique `session_questions`: lo que se presentó no se reescribe.
2. **Guardar una evaluación es idempotente por (intento, clave)**: si ya existe la evaluación de ese
   intento con esa clave, no se duplica. Recalcular con otra clave (S08) añade una fila nueva que
   sustituye a la anterior, porque la anterior sigue siendo lo que se dijo entonces.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import replace
from datetime import datetime
from fractions import Fraction
from uuid import uuid4

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session, sessionmaker

from opofuente.application.question_models import OptionView
from opofuente.application.study_models import (
    AttemptView,
    PartScoreView,
    RecalculationView,
    ScoreView,
    SessionPage,
    SessionQuestionView,
    SessionResultView,
    SessionView,
    SubstitutionView,
)
from opofuente.domain.errors import InvariantViolationError
from opofuente.domain.study import (
    OWNER_ID_LOCAL,
    Confidence,
    Feedback,
    FrozenQuestion,
    SessionConfiguration,
    SessionMode,
    SessionStatus,
)
from opofuente.infrastructure.db_models import (
    AttemptEvaluationRecord,
    AttemptRecord,
    AuditEventRecord,
    OptionVersionRecord,
    QuestionVersionRecord,
    SessionQuestionRecord,
    StudySessionRecord,
)


def _new_id() -> str:
    return str(uuid4())


def _score(numerador: int, denominador: int) -> ScoreView:
    return ScoreView(Fraction(numerador, denominador))


class SqlAlchemyStudyRepository:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    # ------------------------------------------------------------------ sesiones

    def create_session(
        self,
        *,
        opposition_id: str,
        configuration: SessionConfiguration,
        questions: Sequence[FrozenQuestion],
        now: datetime,
        convocation_version_id: str | None = None,
        question_set_id: str | None = None,
        answer_key_version_id: str | None = None,
        time_limit_minutes: int | None = None,
        key_label: str | None = None,
        actor: str = "local",
    ) -> SessionView:
        """Crea la sesión con su composición **congelada** en la misma transacción."""
        if not questions:
            raise InvariantViolationError("una sesión sin preguntas no se puede crear")
        with self._session_factory() as session:
            identificador = _new_id()
            fila = StudySessionRecord(
                id=identificador,
                owner_id=OWNER_ID_LOCAL,
                opposition_id=opposition_id,
                convocation_version_id=convocation_version_id,
                question_set_id=question_set_id,
                answer_key_version_id=answer_key_version_id,
                mode=configuration.mode.value,
                status=SessionStatus.DRAFT.value,
                feedback=configuration.feedback.value,
                configuration_json=json.dumps(
                    self._configuration_json(configuration, key_label), ensure_ascii=False
                ),
                result_json=None,
                time_limit_minutes=time_limit_minutes,
                total_questions=len(questions),
                started_at=None,
                finished_at=None,
                created_at=now,
            )
            session.add(fila)
            # La sesión se confirma **antes** de su composición: sin relaciones declaradas,
            # SQLAlchemy no sabe que la pregunta de la sesión depende de ella y podría invertir el
            # orden (lo cazó la clave foránea, igual que pasó con las opciones en S06).
            session.flush()
            for pregunta in questions:
                session.add(
                    SessionQuestionRecord(
                        id=_new_id(),
                        session_id=identificador,
                        question_version_id=pregunta.question_version_id,
                        stable_key=pregunta.stable_key,
                        position=pregunta.position,
                        part_code=pregunta.part_code,
                        is_reserve=pregunta.is_reserve,
                        reserve_order=pregunta.reserve_order,
                        key_outcome=pregunta.key_outcome,
                        correct_option_keys_json=json.dumps(
                            list(pregunta.correct_option_keys), ensure_ascii=False
                        ),
                    )
                )
            self._audit(
                session,
                actor=actor,
                action="study_session.created",
                object_type="study_session",
                object_id=identificador,
                before={},
                after={
                    "mode": configuration.mode.value,
                    "feedback": configuration.feedback.value,
                    "questions": len(questions),
                    "answer_key_version_id": answer_key_version_id,
                },
                now=now,
            )
            session.commit()
            return self._session_view(session, fila)

    def get_session(self, session_id: str) -> SessionView | None:
        with self._session_factory() as session:
            fila = session.get(StudySessionRecord, session_id)
            return None if fila is None else self._session_view(session, fila)

    def discard_session(
        self, session_id: str, *, now: datetime, actor: str = "local"
    ) -> str | None:
        """Descarta una sesión: la **borra** si no tiene respuestas y la **abandona** si las tiene.

        Una sesión sin respuestas es una preparación que no llegó a nada (una prueba, un clic de
        más): borrarla no pierde historia. En cuanto hay un intento, algo se aprendió y el historial
        no se toca: se marca `abandoned`, que es el estado que la aplicación ya tiene para eso.

        Devuelve qué se hizo (`"deleted"` o `"abandoned"`), o `None` si la sesión no existe.
        """
        with self._session_factory() as session:
            fila = session.get(StudySessionRecord, session_id)
            if fila is None:
                return None
            intentos = int(
                session.execute(
                    select(func.count())
                    .select_from(AttemptRecord)
                    .join(
                        SessionQuestionRecord,
                        SessionQuestionRecord.id == AttemptRecord.session_question_id,
                    )
                    .where(SessionQuestionRecord.session_id == session_id)
                ).scalar_one()
            )
            if intentos:
                antes = {"status": fila.status, "attempts": intentos}
                fila.status = "abandoned"
                self._audit(
                    session,
                    actor=actor,
                    action="study_session.abandoned",
                    object_type="study_session",
                    object_id=session_id,
                    before=antes,
                    after={"status": "abandoned"},
                    now=now,
                )
                session.commit()
                return "abandoned"

            self._audit(
                session,
                actor=actor,
                action="study_session.discarded",
                object_type="study_session",
                object_id=session_id,
                before={"status": fila.status, "questions": fila.total_questions},
                after={},
                now=now,
            )
            # Las preguntas congeladas cuelgan de la sesión (ON DELETE CASCADE en el modelo, pero se
            # borran aquí también porque SQLite no impone las claves foráneas por defecto).
            session.execute(
                delete(SessionQuestionRecord).where(SessionQuestionRecord.session_id == session_id)
            )
            session.delete(fila)
            session.commit()
            return "deleted"

    def list_sessions(
        self,
        *,
        opposition_id: str | None = None,
        status: str | None = None,
        owner_id: str = OWNER_ID_LOCAL,
        limit: int = 50,
        offset: int = 0,
    ) -> SessionPage:
        """Las sesiones **de esta persona**, filtradas por `owner_id` (F2).

        El filtro no está de adorno aunque hoy el valor sea único: es la consulta que leerá la zona
        del alumno, y el día que haya cuentas el historial de dos personas no puede salir mezclado
        porque nadie se acordó de añadir el `WHERE`. Sin `owner_id` explícito se listan las del
        dueño local, que es el único que existe.
        """
        with self._session_factory() as session:
            condiciones = [StudySessionRecord.owner_id == owner_id]
            if opposition_id is not None:
                condiciones.append(StudySessionRecord.opposition_id == opposition_id)
            if status is not None:
                condiciones.append(StudySessionRecord.status == status)
            total = session.execute(
                select(func.count()).select_from(StudySessionRecord).where(*condiciones)
            ).scalar_one()
            filas = (
                session.execute(
                    select(StudySessionRecord)
                    .where(*condiciones)
                    .order_by(StudySessionRecord.created_at.desc(), StudySessionRecord.id)
                    .limit(limit)
                    .offset(offset)
                )
                .scalars()
                .all()
            )
            return SessionPage(
                sessions=tuple(self._session_view(session, fila) for fila in filas),
                total=int(total),
                limit=limit,
                offset=offset,
            )

    def finished_sessions_of_set(self, question_set_id: str) -> tuple[str, ...]:
        """Sesiones **terminadas** que se corrigieron con un conjunto de preguntas (DEBT-013).

        Es lo que hace falta para recalcular en bloque tras corregir una clave: no todas las
        sesiones del conjunto son candidatas (las que siguen en marcha se corrigen al terminar),
        pero las que ya terminaron y usaron este conjunto son exactamente las que quedan con la
        puntuación vieja.
        """
        with self._session_factory() as session:
            filas = session.execute(
                select(StudySessionRecord.id).where(
                    StudySessionRecord.status == SessionStatus.FINISHED.value,
                    StudySessionRecord.question_set_id == question_set_id,
                )
            ).scalars()
            return tuple(str(fila) for fila in filas)

    def session_key_state_of_set(
        self, question_set_id: str, key_version_id: str
    ) -> tuple[tuple[str, ...], tuple[str, ...]]:
        """(desactualizadas, sin ninguna corrección) entre las sesiones terminadas del conjunto.

        «Desactualizada» es una definición concreta, no una impresión: la sesión tiene correcciones
        guardadas y **alguna** de las vigentes no la hizo esa clave. Se mira la evaluación
        **vigente** de cada intento (la última por fecha), que es la que manda para leer el
        resultado de hoy: las anteriores siguen en la base y no cuentan (invariante 7). Así, tras
        recalcular con la clave activa, la sesión deja de estar desactualizada sin que nadie marque
        nada a mano.

        Las sesiones terminadas **sin ninguna corrección guardada** se devuelven aparte y no como
        desactualizadas: no hay nada que comparar, y contarlas como pendientes dejaría un número que
        no bajaría nunca por mucho que se recalcule.
        """
        with self._session_factory() as session:
            sesiones = tuple(
                str(fila)
                for fila in session.execute(
                    select(StudySessionRecord.id)
                    .where(
                        StudySessionRecord.status == SessionStatus.FINISHED.value,
                        StudySessionRecord.question_set_id == question_set_id,
                    )
                    .order_by(StudySessionRecord.created_at, StudySessionRecord.id)
                ).scalars()
            )
            if not sesiones:
                return ((), ())
            # Un intento cuelga de la pregunta de la sesión, no de la sesión: el vínculo se hace por
            # `session_question_id` y el join es obligatorio, no una comodidad.
            intentos = session.execute(
                select(AttemptRecord.id, SessionQuestionRecord.session_id)
                .join(
                    SessionQuestionRecord,
                    AttemptRecord.session_question_id == SessionQuestionRecord.id,
                )
                .where(SessionQuestionRecord.session_id.in_(list(sesiones)))
            ).all()
            vigentes = self._latest_evaluations(session, [str(fila.id) for fila in intentos])
            por_sesion: dict[str, list[AttemptEvaluationRecord]] = {}
            for fila in intentos:
                evaluacion = vigentes.get(str(fila.id))
                if evaluacion is not None:
                    por_sesion.setdefault(str(fila.session_id), []).append(evaluacion)

            desactualizadas: list[str] = []
            sin_correccion: list[str] = []
            for sesion_id in sesiones:
                evaluaciones = por_sesion.get(sesion_id, [])
                if not evaluaciones:
                    sin_correccion.append(sesion_id)
                elif any(
                    evaluacion.answer_key_version_id != key_version_id
                    for evaluacion in evaluaciones
                ):
                    desactualizadas.append(sesion_id)
            return (tuple(desactualizadas), tuple(sin_correccion))

    def recently_attempted_question_ids(
        self, opposition_id: str, *, since: datetime
    ) -> frozenset[str]:
        """Preguntas que se han intentado desde `since` (DEBT-012: lo que un simulacro evita).

        Se mira la **oposición** entera y no un conjunto: una pregunta vista en cualquier sesión
        cuenta
        como vista, y el simulacro existe para no repetir lo reciente con el banco que haya.
        """
        with self._session_factory() as session:
            filas = session.execute(
                select(SessionQuestionRecord.question_version_id)
                .join(AttemptRecord, AttemptRecord.session_question_id == SessionQuestionRecord.id)
                .join(StudySessionRecord, StudySessionRecord.id == SessionQuestionRecord.session_id)
                .where(
                    StudySessionRecord.opposition_id == opposition_id,
                    AttemptRecord.answered_at >= since,
                )
            ).scalars()
            return frozenset(str(fila) for fila in filas)

    def attempt_counts(self, opposition_id: str) -> Mapping[str, int]:
        """Cuántas veces se ha intentado cada pregunta de la oposición (DEBT-012).

        Lo usa la muestra del diagnóstico para empezar por los temas y las preguntas **menos
        vistos**:
        preguntar siempre lo mismo mediría la memoria de la última sesión, no el temario.
        """
        with self._session_factory() as session:
            filas = session.execute(
                select(
                    SessionQuestionRecord.question_version_id,
                    func.count(AttemptRecord.id),
                )
                .join(AttemptRecord, AttemptRecord.session_question_id == SessionQuestionRecord.id)
                .join(StudySessionRecord, StudySessionRecord.id == SessionQuestionRecord.session_id)
                .where(StudySessionRecord.opposition_id == opposition_id)
                .group_by(SessionQuestionRecord.question_version_id)
            ).all()
        return {str(pregunta): int(total) for pregunta, total in filas}

    def start(self, session_id: str, *, now: datetime, actor: str = "local") -> SessionView | None:
        """Pone la sesión en marcha. Arrancar una que ya corre no cambia nada (es reintentable)."""
        with self._session_factory() as session:
            fila = session.get(StudySessionRecord, session_id)
            if fila is None:
                return None
            if fila.status == SessionStatus.DRAFT.value:
                fila.status = SessionStatus.RUNNING.value
                fila.started_at = now
                self._audit(
                    session,
                    actor=actor,
                    action="study_session.started",
                    object_type="study_session",
                    object_id=session_id,
                    before={"status": "draft"},
                    after={"status": "running", "questions": fila.total_questions},
                    now=now,
                )
                session.commit()
            return self._session_view(session, fila)

    def finish(
        self,
        session_id: str,
        *,
        result_json: str,
        now: datetime,
        actor: str = "local",
    ) -> SessionView | None:
        """Cierra la sesión con el resultado calculado. Terminar dos veces no lo recalcula."""
        with self._session_factory() as session:
            fila = session.get(StudySessionRecord, session_id)
            if fila is None:
                return None
            if fila.status != SessionStatus.FINISHED.value:
                anterior = fila.status
                fila.status = SessionStatus.FINISHED.value
                fila.finished_at = now
                fila.result_json = result_json
                self._audit(
                    session,
                    actor=actor,
                    action="study_session.finished",
                    object_type="study_session",
                    object_id=session_id,
                    before={"status": anterior},
                    after={"status": "finished", "result": json.loads(result_json)},
                    now=now,
                )
                session.commit()
            return self._session_view(session, fila)

    def result_json(self, session_id: str) -> str | None:
        """El resultado guardado, como texto: es lo que el recálculo conserva como anterior."""
        with self._session_factory() as session:
            fila = session.get(StudySessionRecord, session_id)
            return None if fila is None else fila.result_json

    def store_result(
        self,
        session_id: str,
        *,
        result_json: str,
        now: datetime,
        previous_result_json: str | None = None,
    ) -> None:
        """Guarda el resultado sin cambiar el estado: se usa al recalcular (S08).

        `previous_result_json` es el resultado que había: se conserva para poder explicar qué cambió
        en lugar de que la cifra cambie sola.
        """
        with self._session_factory() as session:
            fila = session.get(StudySessionRecord, session_id)
            if fila is None:
                return
            fila.previous_result_json = previous_result_json
            fila.result_json = result_json
            fila.recalculated_at = now if previous_result_json is not None else fila.recalculated_at
            session.commit()

    # ------------------------------------------------------------------ composición

    def session_questions(self, session_id: str) -> tuple[SessionQuestionView, ...]:
        """Las preguntas de la sesión con su contenido, **sin** la solución.

        La clave congelada viaja en el modelo (hace falta para corregir) pero no se serializa: el
        contrato no la expone en la pregunta de una sesión sin corregir.
        """
        with self._session_factory() as session:
            filas = (
                session.execute(
                    select(SessionQuestionRecord)
                    .where(SessionQuestionRecord.session_id == session_id)
                    .order_by(SessionQuestionRecord.position)
                )
                .scalars()
                .all()
            )
            if not filas:
                return ()
            versiones = {
                version.id: version
                for version in session.execute(
                    select(QuestionVersionRecord).where(
                        QuestionVersionRecord.id.in_([fila.question_version_id for fila in filas])
                    )
                )
                .scalars()
                .all()
            }
            opciones: dict[str, list[OptionVersionRecord]] = {}
            for opcion in (
                session.execute(
                    select(OptionVersionRecord)
                    .where(OptionVersionRecord.question_version_id.in_(list(versiones)))
                    .order_by(OptionVersionRecord.question_version_id, OptionVersionRecord.position)
                )
                .scalars()
                .all()
            ):
                opciones.setdefault(opcion.question_version_id, []).append(opcion)

            vistas: list[SessionQuestionView] = []
            for fila in filas:
                version = versiones.get(fila.question_version_id)
                vistas.append(
                    SessionQuestionView(
                        session_question_id=fila.id,
                        question_version_id=fila.question_version_id,
                        stable_key=fila.stable_key,
                        position=fila.position,
                        part_code=fila.part_code,
                        is_reserve=bool(fila.is_reserve),
                        reserve_order=fila.reserve_order,
                        stem=version.stem if version is not None else "",
                        question_type=version.question_type if version is not None else "",
                        origin_type=version.origin_type if version is not None else "",
                        options=tuple(
                            OptionView(
                                id=opcion.id,
                                stable_key=opcion.stable_key,
                                text=opcion.text,
                                position=opcion.position,
                                label=opcion.label,
                            )
                            for opcion in opciones.get(fila.question_version_id, [])
                        ),
                        frozen_outcome=fila.key_outcome,
                        frozen_correct_keys=tuple(
                            str(clave)
                            for clave in json.loads(fila.correct_option_keys_json or "[]")
                        ),
                    )
                )
            return tuple(vistas)

    # ------------------------------------------------------------------ intentos

    def attempts(self, session_id: str) -> tuple[AttemptView, ...]:
        """Los intentos de la sesión, con la evaluación **vigente** de cada uno."""
        with self._session_factory() as session:
            filas = session.execute(
                select(AttemptRecord, SessionQuestionRecord)
                .join(
                    SessionQuestionRecord,
                    AttemptRecord.session_question_id == SessionQuestionRecord.id,
                )
                .where(SessionQuestionRecord.session_id == session_id)
                .order_by(SessionQuestionRecord.position)
            ).all()
            if not filas:
                return ()
            evaluaciones = self._latest_evaluations(session, [fila.id for fila, _ in filas])
            return tuple(
                self._attempt_view(
                    fila,
                    evaluaciones.get(fila.id),
                    question_version_id=pregunta.question_version_id,
                )
                for fila, pregunta in filas
            )

    def attempt_for_question(self, session_question_id: str) -> AttemptView | None:
        with self._session_factory() as session:
            fila = session.execute(
                select(AttemptRecord).where(
                    AttemptRecord.session_question_id == session_question_id
                )
            ).scalar_one_or_none()
            if fila is None:
                return None
            pregunta = session.get(SessionQuestionRecord, session_question_id)
            evaluaciones = self._latest_evaluations(session, [fila.id])
            return self._attempt_view(
                fila,
                evaluaciones.get(fila.id),
                question_version_id=(pregunta.question_version_id if pregunta is not None else ""),
            )

    def save_attempt(
        self,
        *,
        session_question_id: str,
        chosen_option_keys: Sequence[str],
        elapsed_ms: int,
        now: datetime,
        confidence: Confidence | None = None,
        client_sequence: int | None = None,
        actor: str = "local",
    ) -> AttemptView:
        """Guarda el intento de una pregunta. El intento se congela: no se reescribe.

        El dueño **se copia de la sesión**, no se pone a `'local'` por comodidad: el intento cuelga
        de una pregunta congelada que cuelga de una sesión, y el dueño de la sesión es el que manda.
        Escribir el valor por defecto aquí sería crear progreso huérfano el día que haya cuentas.
        """
        with self._session_factory() as session:
            fila = AttemptRecord(
                id=_new_id(),
                session_question_id=session_question_id,
                owner_id=self._owner_of_session_question(session, session_question_id),
                chosen_option_keys_json=json.dumps(list(chosen_option_keys), ensure_ascii=False),
                elapsed_ms=max(0, elapsed_ms),
                confidence=confidence.value if confidence is not None else None,
                client_sequence=client_sequence,
                answered_at=now,
            )
            session.add(fila)
            self._audit(
                session,
                actor=actor,
                action="attempt.recorded",
                object_type="attempt",
                object_id=fila.id,
                before={},
                after={
                    "session_question_id": session_question_id,
                    "chosen": list(chosen_option_keys),
                    "elapsed_ms": fila.elapsed_ms,
                },
                now=now,
            )
            session.commit()
            return self._attempt_view(fila, None, question_version_id="")

    def save_evaluation(
        self,
        *,
        attempt_id: str,
        outcome: str,
        score: Fraction,
        now: datetime,
        answer_key_version_id: str | None = None,
        reason: str | None = None,
        supersedes_id: str | None = None,
        actor: str = "local",
    ) -> AttemptView | None:
        """Guarda la evaluación de un intento. Si ya existe para esa clave, no la duplica."""
        with self._session_factory() as session:
            intento = session.get(AttemptRecord, attempt_id)
            if intento is None:
                return None
            existente = session.execute(
                select(AttemptEvaluationRecord).where(
                    AttemptEvaluationRecord.attempt_id == attempt_id,
                    AttemptEvaluationRecord.answer_key_version_id == answer_key_version_id,
                )
            ).scalar_one_or_none()
            if existente is None:
                session.add(
                    AttemptEvaluationRecord(
                        id=_new_id(),
                        attempt_id=attempt_id,
                        # El dueño es el del intento que se corrige (0027): la evaluación es una
                        # lectura del mismo progreso, no una fila nueva de nadie.
                        owner_id=str(intento.owner_id),
                        answer_key_version_id=answer_key_version_id,
                        outcome=outcome,
                        score_numerator=score.numerator,
                        score_denominator=score.denominator,
                        reason=reason,
                        supersedes_id=supersedes_id,
                        evaluated_at=now,
                    )
                )
                self._audit(
                    session,
                    actor=actor,
                    action="attempt.evaluated",
                    object_type="attempt",
                    object_id=attempt_id,
                    before={},
                    after={
                        "outcome": outcome,
                        "score": f"{score.numerator}/{score.denominator}",
                        "answer_key_version_id": answer_key_version_id,
                    },
                    now=now,
                )
                session.commit()
            vigentes = self._latest_evaluations(session, [attempt_id])
            return self._attempt_view(
                intento,
                vigentes.get(attempt_id, existente),
                question_version_id=self._question_version_of(session, attempt_id),
            )

    # ------------------------------------------------------------------ ayudas

    @staticmethod
    def _owner_of_session_question(session: Session, session_question_id: str) -> str:
        """El dueño de la sesión de una pregunta congelada (0027).

        Si la pregunta no existe se devuelve el dueño local: el llamante va a fallar igualmente al
        insertar (la clave foránea no la deja), y aquí no se inventa un error distinto.
        """
        propietario = session.execute(
            select(StudySessionRecord.owner_id)
            .join(SessionQuestionRecord, SessionQuestionRecord.session_id == StudySessionRecord.id)
            .where(SessionQuestionRecord.id == session_question_id)
        ).scalar_one_or_none()
        return str(propietario) if propietario is not None else OWNER_ID_LOCAL

    @staticmethod
    def _question_version_of(session: Session, attempt_id: str) -> str:
        """La versión de pregunta de un intento: la que se congeló en la sesión."""
        version = session.execute(
            select(SessionQuestionRecord.question_version_id)
            .join(AttemptRecord, AttemptRecord.session_question_id == SessionQuestionRecord.id)
            .where(AttemptRecord.id == attempt_id)
        ).scalar_one_or_none()
        return str(version) if version is not None else ""

    @staticmethod
    def _latest_evaluations(
        session: Session, attempt_ids: Sequence[str]
    ) -> dict[str, AttemptEvaluationRecord]:
        """La evaluación vigente de cada intento: la última por fecha y, a igualdad, por id.

        La de una clave nueva que sustituye a la anterior es la que manda para leer el resultado de
        hoy; las anteriores siguen en la base (invariante 7).
        """
        if not attempt_ids:
            return {}
        filas = (
            session.execute(
                select(AttemptEvaluationRecord)
                .where(AttemptEvaluationRecord.attempt_id.in_(list(attempt_ids)))
                .order_by(
                    AttemptEvaluationRecord.attempt_id,
                    AttemptEvaluationRecord.evaluated_at,
                    AttemptEvaluationRecord.id,
                )
            )
            .scalars()
            .all()
        )
        vigentes: dict[str, AttemptEvaluationRecord] = {}
        for fila in filas:
            vigentes[fila.attempt_id] = fila
        return vigentes

    @staticmethod
    def _attempt_view(
        fila: AttemptRecord,
        evaluacion: AttemptEvaluationRecord | None,
        *,
        question_version_id: str,
    ) -> AttemptView:
        return AttemptView(
            id=fila.id,
            session_question_id=fila.session_question_id,
            question_version_id=question_version_id,
            chosen_option_keys=tuple(
                str(clave) for clave in json.loads(fila.chosen_option_keys_json or "[]")
            ),
            elapsed_ms=fila.elapsed_ms,
            confidence=Confidence(fila.confidence) if fila.confidence else None,
            client_sequence=fila.client_sequence,
            answered_at=fila.answered_at,
            outcome=evaluacion.outcome if evaluacion is not None else None,
            score=(
                _score(evaluacion.score_numerator, evaluacion.score_denominator)
                if evaluacion is not None
                else None
            ),
            reason=evaluacion.reason if evaluacion is not None else None,
        )

    def _session_view(self, session: Session, fila: StudySessionRecord) -> SessionView:
        configuracion_cruda = json.loads(fila.configuration_json or "{}")
        respondidas = session.execute(
            select(func.count())
            .select_from(AttemptRecord)
            .join(
                SessionQuestionRecord,
                AttemptRecord.session_question_id == SessionQuestionRecord.id,
            )
            .where(SessionQuestionRecord.session_id == fila.id)
        ).scalar_one()
        return SessionView(
            id=fila.id,
            mode=SessionMode(fila.mode),
            status=SessionStatus(fila.status),
            feedback=Feedback(fila.feedback),
            opposition_id=fila.opposition_id,
            convocation_version_id=fila.convocation_version_id,
            question_set_id=fila.question_set_id,
            answer_key_version_id=fila.answer_key_version_id,
            key_label=configuracion_cruda.get("key_label"),
            configuration=self._configuration_from_json(configuracion_cruda),
            time_limit_minutes=fila.time_limit_minutes,
            total_questions=fila.total_questions,
            answered_questions=int(respondidas),
            started_at=fila.started_at,
            finished_at=fila.finished_at,
            created_at=fila.created_at,
            result=(
                self._result_from_json(
                    fila.result_json,
                    fila.finished_at,
                    previous_json=fila.previous_result_json,
                    recalculated_at=fila.recalculated_at,
                )
                if fila.result_json
                else None
            ),
        )

    @staticmethod
    def _result_from_json(
        datos_json: str,
        terminada: datetime | None,
        *,
        previous_json: str | None = None,
        recalculated_at: datetime | None = None,
    ) -> SessionResultView:
        """El resultado guardado, tal como se calculó: no se recalcula al leerlo.

        Se guarda en el cierre para que lo que se enseña sea **la composición efectiva del cálculo**
        (06_QUESTIONS §7), y no una cifra recalculada con las claves de hoy. Si la sesión se
        recalculó con una clave nueva, el resultado anterior viaja con él para explicar el cambio.
        """
        resultado = SqlAlchemyStudyRepository._resultado_desde_json(datos_json, terminada)
        if previous_json is None:
            return resultado
        anterior = SqlAlchemyStudyRepository._resultado_desde_json(previous_json, recalculated_at)
        cambio = anterior.total.score.value != resultado.total.score.value
        return replace(
            resultado,
            recalculation=RecalculationView(
                previous_total=anterior.total.score,
                previous_parts=anterior.parts,
                previous_key_label=anterior.key_label,
                recalculated_at=recalculated_at,
                changed=cambio,
                note=(
                    f"La puntuación cambió de {anterior.total.score.fraction} a "
                    f"{resultado.total.score.fraction} al recalcular con "
                    f"«{resultado.key_label or 'la clave nueva'}»."
                    if cambio
                    else (
                        "Se recalculó con la clave nueva y la puntuación no cambió: la corrección "
                        "es la misma."
                    )
                ),
            ),
        )

    @staticmethod
    def _resultado_desde_json(datos_json: str, terminada: datetime | None) -> SessionResultView:
        """Un resultado guardado, campo a campo, sin interpretar nada de más."""
        datos = json.loads(datos_json)

        def score(crudo: Mapping[str, object]) -> ScoreView:
            return _score(int(str(crudo["numerator"])), int(str(crudo["denominator"])))

        def parte(cruda: Mapping[str, object]) -> PartScoreView:
            penalizacion = cruda.get("penalty")
            return PartScoreView(
                part_code=(None if cruda.get("part_code") is None else str(cruda["part_code"])),
                part_name=(None if cruda.get("part_name") is None else str(cruda["part_name"])),
                ordinary_items=(
                    int(str(cruda["ordinary_items"]))
                    if cruda.get("ordinary_items") is not None
                    else None
                ),
                score_min=(
                    float(str(cruda["score_min"])) if cruda.get("score_min") is not None else None
                ),
                score_max=(
                    float(str(cruda["score_max"])) if cruda.get("score_max") is not None else None
                ),
                pass_score=(
                    float(str(cruda["pass_score"])) if cruda.get("pass_score") is not None else None
                ),
                penalty=(
                    ScoreView(Fraction(str(penalizacion))) if penalizacion is not None else None
                ),
                kind=str(cruda.get("kind", "direct")),
                correct=int(str(cruda["correct"])),
                wrong=int(str(cruda["wrong"])),
                blank=int(str(cruda["blank"])),
                annulled=int(str(cruda["annulled"])),
                excluded=int(str(cruda["excluded"])),
                conflicting=int(str(cruda["conflicting"])),
                reserves_used=int(str(cruda["reserves_used"])),
                unused_reserves=int(str(cruda["unused_reserves"])),
                score=score(cruda["score"]),  # type: ignore[arg-type]
                passed=(None if cruda.get("passed") is None else bool(cruda.get("passed"))),
                verdict_note=(
                    None if cruda.get("verdict_note") is None else str(cruda["verdict_note"])
                ),
                official_available=bool(cruda.get("official_available", False)),
            )

        return SessionResultView(
            session_id=str(datos["session_id"]),
            mode=SessionMode(str(datos["mode"])),
            answer_key_version_id=(
                str(datos["answer_key_version_id"])
                if datos.get("answer_key_version_id") is not None
                else None
            ),
            key_label=str(datos["key_label"]) if datos.get("key_label") is not None else None,
            parts=tuple(parte(cruda) for cruda in datos.get("parts") or []),
            total=parte(datos["total"]),
            substitutions=tuple(
                SubstitutionView(
                    annulled_question_version_id=str(cruda["annulled_question_version_id"]),
                    reserve_question_version_id=(
                        str(cruda["reserve_question_version_id"])
                        if cruda.get("reserve_question_version_id") is not None
                        else None
                    ),
                )
                for cruda in datos.get("substitutions") or []
            ),
            unfinished=int(str(datos.get("unfinished", 0))),
            official_available=bool(datos.get("official_available", False)),
            official_note=(
                str(datos["official_note"]) if datos.get("official_note") is not None else None
            ),
            calculated_at=terminada,
        )

    @staticmethod
    def _configuration_json(
        configuration: SessionConfiguration, key_label: str | None
    ) -> Mapping[str, object]:
        return {
            "mode": configuration.mode.value,
            "feedback": configuration.feedback.value,
            "time_limit_minutes": configuration.time_limit_minutes,
            "shuffle": configuration.shuffle,
            "key_label": key_label,
            # La nota de la composición se congela con ella: por qué se eligieron estas preguntas
            # (un
            # simulacro que repitió, de qué temas salió una muestra) no puede cambiar después.
            "note": configuration.note,
            # De qué es la sesión, en palabras: es lo que hace que la lista diga «TAI libre 2025 ·
            # modelo A» en vez de cinco filas iguales.
            "context_label": configuration.context_label,
            "sources": [
                {
                    "question_set_id": fuente.question_set_id,
                    "part_code": fuente.part_code,
                    "count": fuente.count,
                    "include_reserves": fuente.include_reserves,
                }
                for fuente in configuration.sources
            ],
        }

    @staticmethod
    def _configuration_from_json(datos: Mapping[str, object]) -> SessionConfiguration:
        from opofuente.domain.study import SessionSource

        crudas = datos.get("sources")
        fuentes: Sequence[Mapping[str, object]] = (
            [fuente for fuente in crudas if isinstance(fuente, Mapping)]
            if isinstance(crudas, list)
            else []
        )
        return SessionConfiguration(
            mode=SessionMode(str(datos.get("mode", SessionMode.PRACTICE.value))),
            feedback=Feedback(str(datos.get("feedback", Feedback.AT_END.value))),
            sources=tuple(
                SessionSource(
                    question_set_id=str(fuente.get("question_set_id", "")),
                    part_code=(
                        str(fuente["part_code"]) if fuente.get("part_code") is not None else None
                    ),
                    count=(int(str(fuente["count"])) if fuente.get("count") is not None else None),
                    include_reserves=bool(fuente.get("include_reserves", True)),
                )
                for fuente in fuentes
            ),
            time_limit_minutes=(
                int(str(datos["time_limit_minutes"]))
                if datos.get("time_limit_minutes") is not None
                else None
            ),
            shuffle=bool(datos.get("shuffle", False)),
            note=(str(datos["note"]) if datos.get("note") is not None else None),
            context_label=(
                str(datos["context_label"]) if datos.get("context_label") is not None else None
            ),
        )

    @staticmethod
    def _audit(
        session: Session,
        *,
        actor: str,
        action: str,
        object_type: str,
        object_id: str,
        before: Mapping[str, object],
        after: Mapping[str, object],
        now: datetime,
    ) -> str:
        evento = AuditEventRecord(
            id=_new_id(),
            actor=actor,
            action=action,
            object_type=object_type,
            object_id=object_id,
            before_json=json.dumps(before, ensure_ascii=False),
            after_json=json.dumps(after, ensure_ascii=False),
            correlation_id=None,
            created_at=now,
        )
        session.add(evento)
        return evento.id


__all__ = ["SqlAlchemyStudyRepository"]
