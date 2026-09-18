"""Servicio de sesiones de estudio (S07): montar, corregir y cerrar una sesión.

Lo que vive aquí y no en el repositorio:

1. **Montar la composición**: elegir preguntas de los conjuntos, aplicar el tamaño y las reservas
   de la convocatoria (o del usuario, en práctica) y comprobar **antes de crear nada** que hay
   material y que hay clave activa. Un examen oficial que pida 80 preguntas y tenga 30 no se crea a
   medias: se dice cuántas faltan.
2. **Corregir con la clave congelada** y con la penalización **exacta** de la parte.
3. **Decidir qué se puede enseñar**: la corrección se construye solo cuando el modo y el estado lo
   permiten (`can_show_correction`), que es lo que impide filtrar la solución antes de responder.

Todo lo que la convocatoria no publica se rechaza en lugar de suponerse: una parte sin penalización
declarada o con un formato que este slice no corrige (S08) no entra en una sesión.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from fractions import Fraction

from opofuente.application.ports import Clock
from opofuente.application.question_models import AnswerKeyView, QuestionView
from opofuente.application.read_models import ConvocationDetail, OppositionDetail
from opofuente.application.study_models import (
    AnswerOutcomeView,
    AttemptView,
    CorrectionView,
    PartScoreView,
    ReviewView,
    ScoreView,
    SessionPage,
    SessionQuestionView,
    SessionResultView,
    SessionView,
    SubstitutionView,
)
from opofuente.domain.errors import (
    AttemptFrozenError,
    ClassificationConflictError,
    InvalidAnswerError,
    NotFoundError,
    SessionStateError,
    UnsupportedError,
)
from opofuente.domain.profiles import ExamPart
from opofuente.domain.study import (
    SUPPORTED_MODES,
    Confidence,
    Feedback,
    FrozenQuestion,
    GradedAttempt,
    PartRule,
    PartScore,
    SessionConfiguration,
    SessionMode,
    SessionSource,
    SessionState,
    SessionStatus,
    aggregate,
    assert_can_answer,
    assert_can_finish,
    assign_positions,
    can_show_correction,
    effective_composition,
    exact_fraction,
    grade_attempt,
)
from opofuente.infrastructure.profile_repository import SqlAlchemyProfileRepository
from opofuente.infrastructure.question_repository import SqlAlchemyQuestionRepository
from opofuente.infrastructure.study_repository import SqlAlchemyStudyRepository

#: Formatos de parte que este slice corrige. Los demás (`multi_mark_error`, psicotécnicos) se
#: rechazan diciendo que llegan en S08, en lugar de corregirlos como si fueran de respuesta única.
_SUPPORTED_PART_FORMATS = (None, "single_choice")

#: Tipos de pregunta que este slice corrige. Una pregunta de otro tipo no entra en la composición.
_SUPPORTED_QUESTION_TYPES = ("single_choice", "true_false")


@dataclass(frozen=True, slots=True)
class SourceInput:
    """De dónde salen las preguntas y qué parte del examen representan."""

    question_set_id: str
    part_code: str
    count: int | None = None
    include_reserves: bool = True


@dataclass(frozen=True, slots=True)
class CreateSessionInput:
    """Lo que pide quien crea una sesión (08_API-CONTRACT §10)."""

    opposition_id: str
    mode: SessionMode
    sources: tuple[SourceInput, ...]
    convocation_version_id: str | None = None
    feedback: Feedback | None = None
    shuffle: bool = False
    time_limit_minutes: int | None = None


@dataclass(frozen=True, slots=True)
class AnswerInput:
    """La respuesta a una pregunta, tal como la manda la interfaz."""

    question_version_id: str
    chosen_option_keys: tuple[str, ...]
    elapsed_ms: int
    confidence: Confidence | None = None
    client_sequence: int | None = None


@dataclass(frozen=True, slots=True)
class CurrentQuestionView:
    """Qué pregunta toca ahora, con el progreso de la sesión."""

    session: SessionView
    question: SessionQuestionView | None
    answered: int
    total: int
    pending: int
    finished: bool


@dataclass(frozen=True, slots=True)
class _PartContext:
    """La parte de la convocatoria con la que se corrige un bloque de preguntas."""

    code: str
    name: str
    rule: PartRule
    ordinary_items: int | None
    reserve_items: int | None
    time_minutes: int | None
    format: str | None


class StudyService:
    def __init__(
        self,
        *,
        study: SqlAlchemyStudyRepository,
        questions: SqlAlchemyQuestionRepository,
        profiles: SqlAlchemyProfileRepository,
        clock: Clock,
    ) -> None:
        self._study = study
        self._questions = questions
        self._profiles = profiles
        self._clock = clock

    # ------------------------------------------------------------------ crear y leer

    def create_session(self, request: CreateSessionInput) -> SessionView:
        """Monta la composición, la congela y crea la sesión: nada se crea si falta material."""
        if request.mode not in SUPPORTED_MODES:
            raise UnsupportedError(
                f"el modo «{request.mode.value}» todavía no está implementado: "
                "este slice construye práctica y examen oficial"
            )
        if not request.sources:
            raise UnsupportedError("una sesión necesita al menos un conjunto de preguntas")

        oposicion: OppositionDetail | None = self._profiles.get_opposition(request.opposition_id)
        if oposicion is None:
            raise NotFoundError("oposición", request.opposition_id)
        convocatoria = self._convocatoria(request, oposicion.opposition.convocation_id)

        #: Las partes que la sesión usa: se resuelven una vez y viajan con la composición.
        contexto: dict[str, _PartContext] = {}
        congeladas: list[FrozenQuestion] = []
        claves: set[str] = set()
        etiquetas: list[str] = []
        limite_tiempo: int | None = None
        conjunto_unico: str | None = request.sources[0].question_set_id

        for fuente in request.sources:
            parte = self._parte(convocatoria, fuente.part_code)
            contexto[parte.code] = parte
            clave = self._clave_activa(fuente.question_set_id)
            claves.add(clave.id)
            etiquetas.append(f"{parte.name}: plantilla v{clave.version_no}")
            preguntas = self._preguntas(fuente, parte, request.mode)
            entradas = {entrada.question_version_id: entrada for entrada in clave.entries}
            # Las reservas se numeran al congelarlas: la convocatoria las valora **por su orden**, y
            # una reserva sin orden no se puede sustituir por la primera. Si el material ya traía un
            # orden, se respeta; si no, es el de presentación dentro de la parte.
            orden_reserva = 0
            for pregunta in preguntas:
                entrada = entradas.get(pregunta.id)
                if pregunta.is_reserve:
                    orden_reserva += 1
                congeladas.append(
                    FrozenQuestion(
                        question_version_id=pregunta.id,
                        stable_key=pregunta.stable_key,
                        position=pregunta.position,
                        part_code=parte.code,
                        is_reserve=pregunta.is_reserve,
                        reserve_order=(
                            pregunta.reserve_order
                            if pregunta.is_reserve and pregunta.reserve_order is not None
                            else (orden_reserva if pregunta.is_reserve else None)
                        ),
                        key_outcome=entrada.outcome if entrada is not None else None,
                        correct_option_keys=(
                            entrada.correct_option_keys if entrada is not None else ()
                        ),
                    )
                )
            if parte.time_minutes is not None:
                limite_tiempo = (
                    parte.time_minutes
                    if limite_tiempo is None
                    else max(limite_tiempo, parte.time_minutes)
                )

        if request.mode is SessionMode.OFFICIAL_EXAM and request.time_limit_minutes is not None:
            raise UnsupportedError(
                "los parámetros de un examen oficial los fija la convocatoria: "
                "no se puede pedir otro límite de tiempo"
            )
        if len(request.sources) > 1:
            conjunto_unico = None

        feedback = (
            Feedback.AT_END
            if request.mode is SessionMode.OFFICIAL_EXAM
            else (request.feedback or Feedback.IMMEDIATE)
        )
        configuracion = SessionConfiguration(
            mode=request.mode,
            feedback=feedback,
            sources=tuple(
                SessionSource(
                    question_set_id=fuente.question_set_id,
                    part_code=fuente.part_code,
                    count=fuente.count,
                    include_reserves=fuente.include_reserves,
                )
                for fuente in request.sources
            ),
            time_limit_minutes=limite_tiempo,
            shuffle=request.shuffle,
        )
        plan = assign_positions(congeladas, shuffle=request.shuffle)
        return self._study.create_session(
            opposition_id=request.opposition_id,
            configuration=configuracion,
            questions=plan,
            now=self._clock.now(),
            convocation_version_id=convocatoria.summary.id,
            question_set_id=conjunto_unico,
            answer_key_version_id=next(iter(claves)) if len(claves) == 1 else None,
            time_limit_minutes=limite_tiempo,
            key_label=" · ".join(etiquetas),
        )

    def list_sessions(
        self,
        *,
        opposition_id: str | None = None,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> SessionPage:
        return self._study.list_sessions(
            opposition_id=opposition_id, status=status, limit=limit, offset=offset
        )

    def session(self, session_id: str) -> SessionView:
        return self._session_or_404(session_id)

    def start(self, session_id: str) -> SessionView:
        """Inicia la sesión. Arrancar una que ya corre devuelve la misma (es reintentable)."""
        session = self._study.get_session(session_id)
        if session is None:
            raise NotFoundError("sesión de estudio", session_id)
        if session.status is SessionStatus.FINISHED:
            raise SessionStateError("la sesión ya está terminada: no se puede volver a empezar")
        if session.status is SessionStatus.DRAFT:
            arrancada = self._study.start(session_id, now=self._clock.now())
            if arrancada is None:
                raise NotFoundError("sesión de estudio", session_id)
            return arrancada
        return session

    # ------------------------------------------------------------------ preguntas

    def current_question(self, session_id: str) -> CurrentQuestionView:
        """La primera pregunta sin responder, o el final de la sesión si no queda ninguna."""
        session = self._session_or_404(session_id)
        preguntas = self._study.session_questions(session_id)
        intentos = self._indice_intentos(session_id)
        vistas = self._componer(session, preguntas, intentos)

        pendiente = next((vista for vista in vistas if not vista.answered), None)
        return CurrentQuestionView(
            session=session,
            question=pendiente,
            answered=sum(1 for vista in vistas if vista.answered),
            total=len(vistas),
            pending=sum(1 for vista in vistas if not vista.answered),
            finished=session.status is SessionStatus.FINISHED,
        )

    def navigate(
        self, session_id: str, *, position: int | None = None, direction: str | None = None
    ) -> CurrentQuestionView:
        """Mueve el puntero de la sesión: a una posición concreta o al siguiente/anterior."""
        session = self._session_or_404(session_id)
        preguntas = self._study.session_questions(session_id)
        if not preguntas:
            return CurrentQuestionView(
                session=session,
                question=None,
                answered=0,
                total=0,
                pending=0,
                finished=session.is_finished,
            )
        intentos = self._indice_intentos(session_id)
        vistas = self._componer(session, preguntas, intentos)

        if direction == "next":
            actual = next((vista for vista in vistas if not vista.answered), vistas[0])
            objetivo = min(actual.position + 1, len(vistas))
        elif direction == "previous":
            actual = next((vista for vista in vistas if not vista.answered), vistas[0])
            objetivo = max(actual.position - 1, 1)
        elif position is not None:
            objetivo = position
        else:
            raise UnsupportedError("hay que decir a qué pregunta navegar: posición o dirección")

        elegida = next((vista for vista in vistas if vista.position == objetivo), None)
        if elegida is None:
            raise NotFoundError("posición de la sesión", str(objetivo))
        return CurrentQuestionView(
            session=session,
            question=elegida,
            answered=sum(1 for vista in vistas if vista.answered),
            total=len(vistas),
            pending=sum(1 for vista in vistas if not vista.answered),
            finished=session.is_finished,
        )

    def answer(self, session_id: str, entrada: AnswerInput) -> AnswerOutcomeView:
        """Registra una respuesta, la corrige con la clave congelada y dice qué se puede enseñar."""
        session = self._session_or_404(session_id)
        assert_can_answer(self._state(session))

        pregunta = next(
            (
                vista
                for vista in self._study.session_questions(session_id)
                if vista.question_version_id == entrada.question_version_id
            ),
            None,
        )
        if pregunta is None:
            raise NotFoundError("pregunta de la sesión", entrada.question_version_id)
        self._validar_respuesta(pregunta, entrada.chosen_option_keys)

        existente = self._study.attempt_for_question(pregunta.session_question_id)
        if existente is not None:
            if tuple(existente.chosen_option_keys) != tuple(entrada.chosen_option_keys):
                raise AttemptFrozenError(
                    "esa pregunta ya está respondida y el intento no se reescribe: "
                    "para cambiarla, empieza otra sesión"
                )
            return AnswerOutcomeView(
                saved=False,
                already_answered=True,
                attempt=existente,
                session=session,
                correction=self._correccion(session, pregunta, existente),
            )

        ahora = self._clock.now()
        intento = self._study.save_attempt(
            session_question_id=pregunta.session_question_id,
            chosen_option_keys=entrada.chosen_option_keys,
            elapsed_ms=entrada.elapsed_ms,
            confidence=entrada.confidence,
            client_sequence=entrada.client_sequence,
            now=ahora,
        )
        calificado = self._calificar(session, pregunta, entrada.chosen_option_keys)
        evaluado = self._study.save_evaluation(
            attempt_id=intento.id,
            outcome=calificado.outcome.value,
            score=calificado.score,
            reason=calificado.reason,
            answer_key_version_id=session.answer_key_version_id,
            now=ahora,
        )
        return AnswerOutcomeView(
            saved=True,
            already_answered=False,
            attempt=evaluado or intento,
            session=session,
            correction=self._correccion(session, pregunta, evaluado or intento),
        )

    # ------------------------------------------------------------------ cerrar y leer el resultado

    def finish(self, session_id: str) -> SessionResultView:
        """Cierra la sesión: corrige lo que falte, calcula el resultado y lo guarda."""
        session = self._session_or_404(session_id)
        if session.is_finished and session.result is not None:
            return session.result
        assert_can_finish(self._state(session))

        ahora = self._clock.now()
        preguntas = self._study.session_questions(session_id)
        intentos = self._indice_intentos(session_id)
        for vista in preguntas:
            intento = intentos.get(vista.question_version_id)
            if intento is None or intento.outcome is not None:
                continue
            calificado = self._calificar(session, vista, intento.chosen_option_keys)
            self._study.save_evaluation(
                attempt_id=intento.id,
                outcome=calificado.outcome.value,
                score=calificado.score,
                reason=calificado.reason,
                answer_key_version_id=session.answer_key_version_id,
                now=ahora,
            )

        resultado = self._calcular(session_id, session)
        cerrada = self._study.finish(
            session_id, result_json=self._resultado_json(resultado), now=ahora
        )
        if cerrada is None:
            raise NotFoundError("sesión de estudio", session_id)
        return replace(resultado, calculated_at=cerrada.finished_at)

    def result(self, session_id: str) -> SessionResultView:
        """El resultado guardado. Una sesión sin terminar no lo tiene: se dice, no se calcula."""
        session = self._session_or_404(session_id)
        if not session.is_finished:
            raise SessionStateError(
                "la sesión no está terminada: el resultado se calcula al terminarla"
            )
        if session.result is None:
            raise SessionStateError("la sesión terminó sin resultado guardado")
        return session.result

    def review(self, session_id: str) -> ReviewView:
        """La revisión: cada pregunta con lo que se marcó y, si se puede, su corrección.

        Con corrección inmediata se revisa lo ya respondido aunque la sesión siga en marcha; con
        corrección al final, solo cuando ha terminado. Las preguntas que aún no se pueden corregir
        se cuentan aparte en lugar de salir sin explicación.
        """
        session = self._session_or_404(session_id)
        intentos = self._indice_intentos(session_id)
        vistas = self._componer(session, self._study.session_questions(session_id), intentos)
        pendientes = sum(1 for vista in vistas if vista.answered and vista.correction is None)
        sin_responder = sum(1 for vista in vistas if not vista.answered)
        return ReviewView(
            session=session,
            entries=vistas,
            partial=not session.is_finished,
            note=(
                None
                if not pendientes
                else (
                    "Hay preguntas respondidas cuya corrección todavía no se puede ver: con "
                    "corrección al final se muestra al terminar la sesión."
                )
            ),
            pending=pendientes,
            unanswered=sin_responder,
        )

    # ------------------------------------------------------------------ composición

    def _convocatoria(
        self, request: CreateSessionInput, convocatoria_activa: str | None
    ) -> ConvocationDetail:
        identificador = request.convocation_version_id or convocatoria_activa
        if identificador is None:
            raise UnsupportedError(
                "la oposición no tiene convocatoria: sin ella no se sabe cómo se corrige el examen"
            )
        convocatoria = self._profiles.get_convocation(identificador)
        if convocatoria is None:
            raise NotFoundError("convocatoria", identificador)
        return convocatoria

    @staticmethod
    def _parte(convocatoria: ConvocationDetail, part_code: str) -> _PartContext:
        parte: ExamPart | None = next(
            (candidata for candidata in convocatoria.parts if candidata.code == part_code), None
        )
        if parte is None:
            raise NotFoundError("parte del examen", part_code)
        if parte.kind == "group":
            raise UnsupportedError(
                f"«{parte.code}» agrupa partes del examen: una sesión se monta sobre una parte con "
                "preguntas, no sobre el grupo"
            )
        if parte.format not in _SUPPORTED_PART_FORMATS:
            raise UnsupportedError(
                f"la parte «{parte.code}» se corrige como «{parte.format}», que llega en S08: "
                "este slice corrige partes de respuesta única"
            )
        if parte.wrong_penalty_fraction is None:
            raise UnsupportedError(
                f"la convocatoria no publica la penalización de la parte «{parte.code}»: "
                "sin ella no se puede calcular la puntuación directa"
            )
        return _PartContext(
            code=parte.code,
            name=parte.name,
            rule=PartRule(
                code=parte.code,
                name=parte.name,
                ordinary_items=parte.ordinary_items,
                score_min=parte.score_min,
                score_max=parte.score_max,
                pass_score=parte.pass_score,
                penalty=exact_fraction(parte.wrong_penalty_fraction),
            ),
            ordinary_items=parte.ordinary_items,
            reserve_items=parte.reserve_items,
            # El tiempo es de la parte y, si ella no lo dice, del grupo que la contiene: en TAI el
            # límite de 120 minutos está en el ejercicio único, no en cada parte.
            time_minutes=StudyService._tiempo(convocatoria, parte),
            format=parte.format,
        )

    @staticmethod
    def _tiempo(convocatoria: ConvocationDetail, parte: ExamPart) -> int | None:
        if parte.time_minutes is not None:
            return parte.time_minutes
        if parte.parent_code is None:
            return None
        padre = next(
            (candidata for candidata in convocatoria.parts if candidata.code == parte.parent_code),
            None,
        )
        return padre.time_minutes if padre is not None else None

    def _clave_activa(self, set_id: str) -> AnswerKeyView:
        """La clave **activa** del conjunto: es la que corrige. Una en borrador no corrige nada."""
        activa = next(
            (clave for clave in self._questions.list_keys(set_id) if clave.status == "active"), None
        )
        if activa is None:
            raise ClassificationConflictError(
                "el conjunto no tiene ninguna clave activa: activar una plantilla es lo que decide "
                "con qué se corrige el examen"
            )
        return activa

    def _preguntas(
        self, fuente: SourceInput, parte: _PartContext, modo: SessionMode
    ) -> tuple[QuestionView, ...]:
        """Las preguntas de una fuente: ordinarias primero y reservas después, sin inventar."""
        conjunto = self._questions.get_set(fuente.question_set_id)
        if conjunto is None:
            raise NotFoundError("conjunto de preguntas", fuente.question_set_id)
        todas = self._questions.all_questions(fuente.question_set_id)
        validas = [
            pregunta for pregunta in todas if pregunta.question_type in _SUPPORTED_QUESTION_TYPES
        ]
        ordinarias = [pregunta for pregunta in validas if not pregunta.is_reserve]
        reservas = [pregunta for pregunta in validas if pregunta.is_reserve]

        if modo is SessionMode.OFFICIAL_EXAM:
            if parte.ordinary_items is None:
                raise UnsupportedError(
                    f"la convocatoria no dice cuántas preguntas tiene la parte «{parte.code}»: "
                    "sin ese dato no se puede montar el examen oficial"
                )
            if len(ordinarias) < parte.ordinary_items:
                raise UnsupportedError(
                    f"el conjunto «{conjunto.title}» tiene {len(ordinarias)} preguntas y la parte "
                    f"«{parte.code}» pide {parte.ordinary_items}: faltan preguntas para el examen"
                )
            elegidas = ordinarias[: parte.ordinary_items]
            necesarias = parte.reserve_items or 0
            if len(reservas) < necesarias:
                raise UnsupportedError(
                    f"la parte «{parte.code}» pide {necesarias} reservas y el conjunto tiene "
                    f"{len(reservas)}: faltan reservas para el examen"
                )
            return (*elegidas, *reservas[:necesarias])

        cantidad = fuente.count if fuente.count is not None else len(ordinarias)
        if cantidad <= 0:
            raise UnsupportedError("una sesión de práctica con cero preguntas no tiene sentido")
        if len(ordinarias) < cantidad:
            raise UnsupportedError(
                f"el conjunto «{conjunto.title}» tiene {len(ordinarias)} preguntas y se han pedido "
                f"{cantidad}"
            )
        elegidas = ordinarias[:cantidad]
        return (*elegidas, *(reservas if fuente.include_reserves else ()))

    # ------------------------------------------------------------------ corrección

    @staticmethod
    def _state(session: SessionView) -> SessionState:
        return SessionState(
            session_id=session.id,
            mode=session.mode,
            status=session.status,
            feedback=session.feedback,
            answer_key_version_id=session.answer_key_version_id,
            total_questions=session.total_questions,
            answered_questions=session.answered_questions,
            started_at=session.started_at,
            finished_at=session.finished_at,
            time_limit_minutes=session.time_limit_minutes,
        )

    @staticmethod
    def _validar_respuesta(pregunta: SessionQuestionView, claves: Sequence[str]) -> None:
        """Una respuesta se valida contra las opciones de la pregunta que se presentó."""
        disponibles = {opcion.stable_key for opcion in pregunta.options}
        desconocidas = [clave for clave in claves if clave not in disponibles]
        if desconocidas:
            raise InvalidAnswerError(
                f"«{', '.join(desconocidas)}» no es una opción de esta pregunta",
                field="chosen_option_keys",
            )
        if pregunta.question_type in ("single_choice", "true_false") and len(set(claves)) > 1:
            raise InvalidAnswerError(
                "esta pregunta admite una sola respuesta",
                field="chosen_option_keys",
            )

    def _calificar(
        self, session: SessionView, pregunta: SessionQuestionView, claves: Sequence[str]
    ) -> GradedAttempt:
        return grade_attempt(
            chosen_option_keys=claves,
            frozen_outcome=pregunta.frozen_outcome,
            frozen_correct_keys=pregunta.frozen_correct_keys,
            penalty=self._penalizacion(session, pregunta),
        )

    def _penalizacion(self, session: SessionView, pregunta: SessionQuestionView) -> Fraction:
        parte = self._parte_de(session, pregunta.part_code)
        return parte.rule.penalty

    def _parte_de(self, session: SessionView, part_code: str | None) -> _PartContext:
        if part_code is None:
            raise UnsupportedError("la pregunta no declara su parte: no se sabe cómo se corrige")
        convocatoria = self._profiles.get_convocation(session.convocation_version_id or "")
        if convocatoria is None:
            raise NotFoundError("convocatoria", session.convocation_version_id or "")
        return self._parte(convocatoria, part_code)

    # ------------------------------------------------------------------ vistas

    def _session_or_404(self, session_id: str) -> SessionView:
        session = self._study.get_session(session_id)
        if session is None:
            raise NotFoundError("sesión de estudio", session_id)
        return session

    def _indice_intentos(self, session_id: str) -> dict[str, AttemptView]:
        return {
            intento.question_version_id: intento for intento in self._study.attempts(session_id)
        }

    def _componer(
        self,
        session: SessionView,
        preguntas: Sequence[SessionQuestionView],
        intentos: Mapping[str, AttemptView],
    ) -> tuple[SessionQuestionView, ...]:
        """Junta composición, intentos y correcciones: es lo que se enseña de una sesión."""
        vistas: list[SessionQuestionView] = []
        for pregunta in preguntas:
            intento = intentos.get(pregunta.question_version_id)
            vistas.append(
                SessionQuestionView(
                    session_question_id=pregunta.session_question_id,
                    question_version_id=pregunta.question_version_id,
                    stable_key=pregunta.stable_key,
                    position=pregunta.position,
                    part_code=pregunta.part_code,
                    is_reserve=pregunta.is_reserve,
                    reserve_order=pregunta.reserve_order,
                    stem=pregunta.stem,
                    question_type=pregunta.question_type,
                    origin_type=pregunta.origin_type,
                    options=pregunta.options,
                    answered=intento is not None,
                    chosen_option_keys=(intento.chosen_option_keys if intento is not None else ()),
                    elapsed_ms=intento.elapsed_ms if intento is not None else None,
                    confidence=intento.confidence if intento is not None else None,
                    correction=(
                        self._correccion(session, pregunta, intento)
                        if intento is not None
                        else None
                    ),
                    frozen_outcome=pregunta.frozen_outcome,
                    frozen_correct_keys=pregunta.frozen_correct_keys,
                )
            )
        return tuple(vistas)

    def _correccion(
        self,
        session: SessionView,
        pregunta: SessionQuestionView,
        intento: AttemptView,
    ) -> CorrectionView | None:
        """La corrección, **si se puede enseñar**: única puerta por la que sale la solución."""
        if not can_show_correction(self._state(session), question_answered=True):
            return None
        calificado = self._calificar(session, pregunta, intento.chosen_option_keys)
        return CorrectionView(
            outcome=calificado.outcome.value,
            correct_option_keys=tuple(pregunta.frozen_correct_keys),
            score=ScoreView(calificado.score),
            reason=calificado.reason,
            explanation=None,
            evidence=self._questions.question_evidence(pregunta.question_version_id),
        )

    def _calcular(self, session_id: str, session: SessionView) -> SessionResultView:
        """El cálculo del resultado: composición efectiva, partes y total, con aritmética exacta."""
        preguntas = self._study.session_questions(session_id)
        intentos = self._indice_intentos(session_id)
        congeladas = [
            FrozenQuestion(
                question_version_id=vista.question_version_id,
                stable_key=vista.stable_key,
                position=vista.position,
                part_code=vista.part_code,
                is_reserve=vista.is_reserve,
                reserve_order=vista.reserve_order,
                key_outcome=vista.frozen_outcome,
                correct_option_keys=vista.frozen_correct_keys,
            )
            for vista in preguntas
        ]
        calificados: dict[str, GradedAttempt | None] = {}
        for vista in preguntas:
            intento = intentos.get(vista.question_version_id)
            if intento is None:
                calificados[vista.question_version_id] = None
                continue
            calificados[vista.question_version_id] = self._calificar(
                session, vista, intento.chosen_option_keys
            )

        items, sustituciones = effective_composition(congeladas, calificados)
        reglas = self._reglas_de_partes(session, congeladas)
        resultado = aggregate(
            session_id=session_id,
            mode=session.mode,
            answer_key_version_id=session.answer_key_version_id,
            items=items,
            substitutions=sustituciones,
            part_rules=reglas,
        )
        return SessionResultView(
            session_id=resultado.session_id,
            mode=resultado.mode,
            answer_key_version_id=resultado.answer_key_version_id,
            key_label=session.key_label,
            parts=tuple(self._parte_view(parte) for parte in resultado.parts),
            total=self._parte_view(resultado.total),
            substitutions=tuple(
                SubstitutionView(
                    annulled_question_version_id=sustitucion.annulled_question_version_id,
                    reserve_question_version_id=sustitucion.reserve_question_version_id,
                )
                for sustitucion in resultado.substitutions
            ),
            unfinished=resultado.unfinished,
            official_available=resultado.official_available,
            official_note=resultado.official_note,
        )

    def _reglas_de_partes(
        self, session: SessionView, preguntas: Sequence[FrozenQuestion]
    ) -> dict[str | None, PartRule]:
        convocatoria = self._profiles.get_convocation(session.convocation_version_id or "")
        if convocatoria is None:
            raise NotFoundError("convocatoria", session.convocation_version_id or "")
        reglas: dict[str | None, PartRule] = {}
        for codigo in {pregunta.part_code for pregunta in preguntas}:
            if codigo is None:
                continue
            reglas[codigo] = self._parte(convocatoria, codigo).rule
        return reglas

    @staticmethod
    def _parte_view(parte: PartScore) -> PartScoreView:
        return PartScoreView(
            part_code=parte.part_code,
            part_name=parte.part_name,
            ordinary_items=parte.ordinary_items,
            score_min=parte.score_min,
            score_max=parte.score_max,
            pass_score=parte.pass_score,
            penalty=ScoreView(parte.penalty) if parte.penalty is not None else None,
            correct=parte.correct,
            wrong=parte.wrong,
            blank=parte.blank,
            annulled=parte.annulled,
            excluded=parte.excluded,
            conflicting=parte.conflicting,
            reserves_used=parte.reserves_used,
            unused_reserves=parte.unused_reserves,
            score=ScoreView(parte.score),
            official_available=parte.official_available,
        )

    @staticmethod
    def _parte_json(parte: PartScoreView) -> dict[str, object]:
        """Una parte del resultado, con sus recuentos y su puntuación exacta."""
        return {
            "part_code": parte.part_code,
            "part_name": parte.part_name,
            "ordinary_items": parte.ordinary_items,
            "score_min": parte.score_min,
            "score_max": parte.score_max,
            "pass_score": parte.pass_score,
            "penalty": parte.penalty.fraction if parte.penalty is not None else None,
            "correct": parte.correct,
            "wrong": parte.wrong,
            "blank": parte.blank,
            "annulled": parte.annulled,
            "excluded": parte.excluded,
            "conflicting": parte.conflicting,
            "reserves_used": parte.reserves_used,
            "unused_reserves": parte.unused_reserves,
            "score": {
                "numerator": parte.score.numerator,
                "denominator": parte.score.denominator,
            },
            "official_available": parte.official_available,
        }

    @staticmethod
    def _resultado_json(resultado: SessionResultView) -> str:
        """El resultado guardado, tal como se calculó: es la composición efectiva del cálculo."""
        return json.dumps(
            {
                "session_id": resultado.session_id,
                "mode": resultado.mode.value,
                "answer_key_version_id": resultado.answer_key_version_id,
                "key_label": resultado.key_label,
                "parts": [StudyService._parte_json(parte) for parte in resultado.parts],
                "total": StudyService._parte_json(resultado.total),
                "substitutions": [
                    {
                        "annulled_question_version_id": sustitucion.annulled_question_version_id,
                        "reserve_question_version_id": sustitucion.reserve_question_version_id,
                    }
                    for sustitucion in resultado.substitutions
                ],
                "unfinished": resultado.unfinished,
                "official_available": resultado.official_available,
                "official_note": resultado.official_note,
            },
            ensure_ascii=False,
        )


#: Reexportado para que el tipo de la opción viaje con las vistas de la sesión.
__all__ = [
    "AnswerInput",
    "CreateSessionInput",
    "CurrentQuestionView",
    "SourceInput",
    "StudyService",
]
