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
from datetime import datetime, timedelta
from fractions import Fraction

from opofuente.application.ports import Clock
from opofuente.application.question_models import AnswerKeyView, KeyEntryView, QuestionView
from opofuente.application.read_models import ConvocationDetail, OppositionDetail
from opofuente.application.review_service import ReviewService
from opofuente.application.study_models import (
    AnswerOutcomeView,
    AttemptView,
    BulkRecalculationView,
    CorrectionView,
    OutdatedSessionsView,
    PartScoreView,
    ReviewView,
    ScoreView,
    SessionPage,
    SessionQuestionView,
    SessionRecalculationView,
    SessionResultView,
    SessionView,
    SubstitutionView,
)
from opofuente.domain.diagnostic import (
    DIAS_VISTA_HACE_POCO,
    MINIMO_TEMAS_DIAGNOSTICO,
    DiagnosticReading,
    DiagnosticTopic,
    order_for_mock,
    read_diagnostic,
    stratified_sample,
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
    AttemptOutcome,
    Confidence,
    Feedback,
    FrozenQuestion,
    GradedAttempt,
    PartRule,
    PartScore,
    ScoringKind,
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

#: Formatos de parte que este slice corrige. Son las tres formas que publican las convocatorias
#: sembradas: respuesta única (TAI y GC), marcar errores (ortografía y gramática de GC) y
#: psicotécnicas (aptitudes intelectuales de GC), cada una con la regla de su parte.
_SUPPORTED_PART_FORMATS = (None, "single_choice", "multi_mark_error", "psychotechnical")

#: Tipos de pregunta que este slice corrige. Una pregunta de otro tipo no entra en la composición.
_SUPPORTED_QUESTION_TYPES = ("single_choice", "true_false", "multi_mark_error")

#: Preguntas que entran por defecto en una sesión de repaso, y su tope. Una sesión de repaso es lo
#: que toca hoy: con doscientos elementos vencidos, lo honesto es empezar por veinte y volver
#: mañana, no montar un examen de doscientos.
REVIEW_SESSION_LIMIT = 20
MAX_REVIEW_SESSION_LIMIT = 50


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
    #: Solo para el repaso de errores: cuántas preguntas vencidas entran como mucho (el material lo
    #: pone la cola de repaso, no quien pide la sesión).
    review_limit: int | None = None


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
        review: ReviewService | None = None,
    ) -> None:
        self._study = study
        self._questions = questions
        self._profiles = profiles
        self._clock = clock
        #: El repaso es opcional para que las pruebas de sesiones sigan siendo de sesiones: si no
        #: está, no se registra ningún repaso, pero nada de lo demás cambia.
        self._review = review

    # ------------------------------------------------------------------ crear y leer

    def create_session(self, request: CreateSessionInput) -> SessionView:
        """Monta la composición, la congela y crea la sesión: nada se crea si falta material."""
        if request.mode not in SUPPORTED_MODES:
            raise UnsupportedError(
                f"el modo «{request.mode.value}» todavía no está implementado: "
                "este slice construye práctica, repaso de errores, examen oficial, simulacro y "
                "diagnóstico"
            )
        oposicion: OppositionDetail | None = self._profiles.get_opposition(request.opposition_id)
        if oposicion is None:
            raise NotFoundError("oposición", request.opposition_id)
        convocatoria = self._convocatoria(request, oposicion.opposition.convocation_id)
        if request.mode is SessionMode.ERROR_REVIEW:
            return self._create_review_session(request, convocatoria)
        if request.mode is SessionMode.DIAGNOSTIC:
            return self._create_diagnostic_session(request, convocatoria)
        if not request.sources:
            raise UnsupportedError("una sesión necesita al menos un conjunto de preguntas")

        #: Las partes que la sesión usa: se resuelven una vez y viajan con la composición.
        contexto: dict[str, _PartContext] = {}
        congeladas: list[FrozenQuestion] = []
        claves: set[str] = set()
        etiquetas: list[str] = []
        limite_tiempo: int | None = None
        conjunto_unico: str | None = request.sources[0].question_set_id
        #: Preguntas del simulacro que ya se habían visto hace poco. Se cuentan para poder decirlo:
        #: un
        #: simulacro que repite sin avisar mide memoria de la última sesión (DEBT-012).
        repetidas = 0

        #: Preguntas que ya se habían visto hace poco: solo el simulacro las evita (DEBT-012).
        vistas_hace_poco: frozenset[str] = (
            self._vistas_hace_poco(request.opposition_id)
            if request.mode is SessionMode.MOCK_EXAM
            else frozenset()
        )

        for fuente in request.sources:
            parte = self._parte(convocatoria, fuente.part_code)
            contexto[parte.code] = parte
            clave = self._clave_activa(fuente.question_set_id)
            claves.add(clave.id)
            etiquetas.append(f"{parte.name}: plantilla v{clave.version_no}")
            preguntas = self._preguntas(fuente, parte, request.mode, recently_seen=vistas_hace_poco)
            if request.mode is SessionMode.MOCK_EXAM:
                # Cuántas de las elegidas se habían visto hace poco: el orden de `_preguntas`
                # prefiere
                # las frescas, y lo que no se puede evitar se dice en la nota de la sesión.
                repetidas += sum(1 for pregunta in preguntas if pregunta.id in vistas_hace_poco)
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

        # Un examen y un simulacro corrigen al terminar: enseñar la corrección mientras se contesta
        # filtraría la solución, y el simulacro se parece al examen a propósito
        # (`SessionConfiguration`
        # lo exige también desde el dominio, no solo aquí).
        feedback = (
            Feedback.AT_END
            if request.mode in (SessionMode.OFFICIAL_EXAM, SessionMode.MOCK_EXAM)
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
            note=(
                None
                if request.mode is not SessionMode.MOCK_EXAM
                else self._nota_del_simulacro(repetidas, total=len(congeladas))
            ),
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

    def _create_review_session(
        self, request: CreateSessionInput, convocatoria: ConvocationDetail
    ) -> SessionView:
        """Monta una sesión con lo que la cola de repaso tiene vencido (06 §5, modo repaso).

        La composición **no** la elige quien estudia: la pone la cola, que es la que sabe qué está
        vencido y por qué. Si no hay nada vencido, no se crea una sesión vacía: se dice con un 409 y
        el motivo, porque una sesión de repaso sin repasos no es un repaso.
        """
        if request.sources:
            raise UnsupportedError(
                "una sesión de repaso la compone la cola de repaso: no se elige el conjunto a mano"
            )
        if self._review is None:
            raise UnsupportedError("este proceso no tiene el repaso de errores disponible")
        limite = request.review_limit or REVIEW_SESSION_LIMIT
        vencidas = self._review.due_for_session(
            opposition_id=request.opposition_id, limit=min(limite, MAX_REVIEW_SESSION_LIMIT)
        )
        if not vencidas:
            raise UnsupportedError(
                "no hay nada vencido que repasar: la cola de repaso está vacía "
                "(los repasos se crean al fallar una pregunta en una sesión)"
            )

        congeladas: list[FrozenQuestion] = []
        contexto: dict[str, _PartContext] = {}
        claves: set[str] = set()
        etiquetas: list[str] = []
        conjuntos: set[str] = set()
        limite_tiempo: int | None = None
        for posicion, vencida in enumerate(vencidas, start=1):
            if vencida.part_code is None:
                raise UnsupportedError(
                    f"el repaso de «{vencida.stable_key}» no sabe a qué parte del examen "
                    "pertenece: la sesión en la que se falló no lo registró, así que no se puede "
                    "componer la sesión de repaso"
                )
            parte = self._parte(convocatoria, vencida.part_code)
            contexto[parte.code] = parte
            clave = self._clave_activa(vencida.question_set_id)
            claves.add(clave.id)
            conjuntos.add(vencida.question_set_id)
            etiqueta = f"{parte.name}: plantilla v{clave.version_no}"
            if etiqueta not in etiquetas:
                etiquetas.append(etiqueta)
            entrada = next(
                (
                    candidata
                    for candidata in clave.entries
                    if candidata.question_version_id == vencida.question_version_id
                ),
                None,
            )
            congeladas.append(
                FrozenQuestion(
                    question_version_id=vencida.question_version_id,
                    stable_key=vencida.stable_key,
                    position=posicion,
                    part_code=parte.code,
                    is_reserve=False,
                    reserve_order=None,
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

        configuracion = SessionConfiguration(
            mode=request.mode,
            # El repaso corrije al momento: §5 dice que no se enseña la respuesta **antes** del
            # intento, y después sí, que es justo lo que se viene a hacer aquí.
            feedback=request.feedback or Feedback.IMMEDIATE,
            sources=(),
            time_limit_minutes=limite_tiempo,
            shuffle=request.shuffle,
        )
        return self._study.create_session(
            opposition_id=request.opposition_id,
            configuration=configuracion,
            questions=assign_positions(congeladas, shuffle=request.shuffle),
            now=self._clock.now(),
            convocation_version_id=convocatoria.summary.id,
            question_set_id=next(iter(conjuntos)) if len(conjuntos) == 1 else None,
            answer_key_version_id=next(iter(claves)) if len(claves) == 1 else None,
            time_limit_minutes=limite_tiempo,
            key_label=" · ".join(etiquetas),
        )

    def _vistas_hace_poco(self, opposition_id: str) -> frozenset[str]:
        """Las preguntas intentadas en la ventana reciente de la oposición (DEBT-012)."""
        ahora = self._clock.now()
        return self._study.recently_attempted_question_ids(
            opposition_id, since=ahora - timedelta(days=DIAS_VISTA_HACE_POCO)
        )

    @staticmethod
    def _nota_del_simulacro(repetidas: int, *, total: int) -> str:
        """Lo que un simulacro dice de su propia composición: cuánto ha tenido que repetir.

        No se calla: un simulacro que repite preguntas de ayer mide memoria, no temario, y quien lo
        hace tiene que poder saber cuánto de lo que acaba de ver ya lo había visto.
        """
        if repetidas == 0:
            return (
                "simulacro con el perfil exacto del examen: ninguna de sus preguntas se había "
                "intentado en los últimos días"
            )
        return (
            f"simulacro con el perfil exacto del examen: {repetidas} de {total} pregunta(s) ya se "
            "habían intentado en los últimos días, porque el banco no daba para más sin repetir"
        )

    def _create_diagnostic_session(
        self, request: CreateSessionInput, convocatoria: ConvocationDetail
    ) -> SessionView:
        """Monta la muestra estratificada por tema de un diagnóstico (06_QUESTIONS §5).

        La composición **no** la elige quien estudia: la elige la muestra, que es la que sabe qué
        temas
        hay y cuánto se ha visto cada pregunta. Una muestra pequeña y repartida sirve para saber por
        dónde está el hueco; un cuestionario largo con cuatro preguntas de un tema mediría el azar
        de
        esas cuatro.

        Lo que **no** hace: inventarse temas. Una pregunta sin nodo del programa aceptado no puede
        estratificar, así que se queda fuera de la muestra y se cuenta.
        """
        if request.sources:
            raise UnsupportedError(
                "una sesión de diagnóstico la compone la muestra por temas: no se "
                "elige el conjunto a mano"
            )
        ahora = self._clock.now()
        intentos_previos = self._study.attempt_counts(request.opposition_id)
        conjuntos = self._questions.list_sets(opposition_id=request.opposition_id, limit=200).sets
        con_clave = [conjunto for conjunto in conjuntos if conjunto.active_key_id is not None]
        if not con_clave:
            raise UnsupportedError(
                "ningún conjunto de esta oposición tiene plantilla activa: sin clave no se puede "
                "corregir un diagnóstico"
            )

        # Los temas se juntan entre conjuntos: el tema es del programa, no del conjunto del que
        # salió
        # la pregunta, así que dos temarios del mismo tema son el mismo tema.
        candidatas: dict[str, list[QuestionView]] = {}
        titulos: dict[str, str] = {}
        sin_tema = 0
        for conjunto in con_clave:
            temas_del_conjunto = self._questions.node_titles_of_set(conjunto.id)
            for pregunta in self._questions.all_questions(conjunto.id):
                if pregunta.question_type not in _SUPPORTED_QUESTION_TYPES or pregunta.is_reserve:
                    continue
                suyos = temas_del_conjunto.get(pregunta.id, ())
                if not suyos:
                    sin_tema += 1
                    continue
                # El **primer** tema de la pregunta (el de ruta anterior) es el que la estratifica:
                # una
                # pregunta asignada a dos temas no puede contar dos veces en la misma muestra.
                node_id, titulo = suyos[0]
                titulos[node_id] = titulo
                candidatas.setdefault(node_id, []).append(pregunta)

        temas_del_banco = tuple(
            DiagnosticTopic(
                node_id=node_id,
                title=titulos[node_id],
                # Primero las preguntas menos intentadas: preguntar siempre las mismas mediría la
                # memoria de la última sesión. El orden es estable, no aleatorio.
                question_ids=tuple(
                    pregunta.id
                    for pregunta in sorted(
                        preguntas,
                        key=lambda pregunta: (
                            intentos_previos.get(pregunta.id, 0),
                            pregunta.position,
                            pregunta.id,
                        ),
                    )
                ),
            )
            for node_id, preguntas in sorted(candidatas.items(), key=lambda par: titulos[par[0]])
        )
        if len(temas_del_banco) < MINIMO_TEMAS_DIAGNOSTICO:
            raise UnsupportedError(
                f"el banco solo tiene preguntas de {len(temas_del_banco)} tema(s) y un "
                f"diagnóstico necesita al menos {MINIMO_TEMAS_DIAGNOSTICO} para repartir "
                "la muestra: asigna las preguntas a sus temas (o pide una práctica)"
            )

        muestra = stratified_sample(temas_del_banco, without_topic=sin_tema)
        if not muestra.question_ids:
            raise UnsupportedError("la muestra del diagnóstico ha salido vacía: revisa el banco")

        # La parte de una pregunta del banco no está declarada: el diagnóstico no es un examen, así
        # que
        # sus preguntas se congelan **sin parte** y se corrigen en directo, sin la penalización que
        # la
        # convocatoria fija para un examen. Inventar a qué parte pertenece cada pregunta sería peor.
        por_id = {
            pregunta.id: pregunta for preguntas in candidatas.values() for pregunta in preguntas
        }
        claves: dict[str, str] = {}
        etiquetas: list[str] = []
        congeladas: list[FrozenQuestion] = []
        for posicion, question_id in enumerate(muestra.question_ids, start=1):
            pregunta = por_id[question_id]
            clave = self._clave_activa(pregunta.question_set_id)
            claves[pregunta.question_set_id] = clave.id
            etiqueta = f"plantilla v{clave.version_no}"
            if etiqueta not in etiquetas:
                etiquetas.append(etiqueta)
            entrada = next(
                (
                    candidata
                    for candidata in clave.entries
                    if candidata.question_version_id == pregunta.id
                ),
                None,
            )
            congeladas.append(
                FrozenQuestion(
                    question_version_id=pregunta.id,
                    stable_key=pregunta.stable_key,
                    position=posicion,
                    part_code=None,
                    is_reserve=False,
                    reserve_order=None,
                    key_outcome=entrada.outcome if entrada is not None else None,
                    correct_option_keys=(
                        entrada.correct_option_keys if entrada is not None else ()
                    ),
                )
            )

        configuracion = SessionConfiguration(
            mode=request.mode,
            feedback=request.feedback or Feedback.IMMEDIATE,
            sources=(),
            time_limit_minutes=None,
            shuffle=request.shuffle,
            note=muestra.detail,
        )
        return self._study.create_session(
            opposition_id=request.opposition_id,
            configuration=configuracion,
            questions=assign_positions(congeladas, shuffle=request.shuffle),
            now=ahora,
            convocation_version_id=convocatoria.summary.id,
            question_set_id=next(iter(claves)) if len(claves) == 1 else None,
            answer_key_version_id=next(iter(claves.values())) if len(claves) == 1 else None,
            time_limit_minutes=None,
            key_label=" · ".join(etiquetas),
        )

    def diagnostic_reading(self, session_id: str) -> DiagnosticReading:
        """Lee una sesión de diagnóstico: por tema, con su intervalo y el tamaño de la muestra.

        Solo tiene sentido en un diagnóstico, y se dice con un 409 en cualquier otro modo: la
        lectura
        de una muestra pequeña **no** es la nota de un examen, y presentarla al lado de la
        puntuación
        de una práctica invitaría a leerla como si lo fuera.
        """
        session = self._session_or_404(session_id)
        if session.mode is not SessionMode.DIAGNOSTIC:
            raise UnsupportedError(
                f"la lectura por temas es del diagnóstico, y esta sesión es de "
                f"«{session.mode.value}»: una muestra pequeña no se lee igual que un examen"
            )
        congeladas = self._study.session_questions(session_id)
        intentos = self._indice_intentos(session_id)
        temas_por_pregunta = self._questions.node_titles_of_questions(
            [congelada.question_version_id for congelada in congeladas]
        )
        acumulado: dict[str, tuple[str, int, int]] = {}
        for congelada in congeladas:
            suyos = temas_por_pregunta.get(congelada.question_version_id, ())
            # Sin tema, la pregunta no se puede leer por tema: se agrupa aparte y se dice, en lugar
            # de
            # repartirla a un tema que no le corresponde.
            node_id, titulo = suyos[0] if suyos else ("sin-tema", "sin tema asignado")
            intento = intentos.get(congelada.question_version_id)
            respondidas = 0
            acertadas = 0
            if intento is not None:
                respondidas = 1
                calificado = self._calificar(session, congelada, intento.chosen_option_keys)
                acertadas = 1 if calificado.outcome is AttemptOutcome.CORRECT else 0
            previo = acumulado.get(node_id, (titulo, 0, 0))
            acumulado[node_id] = (titulo, previo[1] + respondidas, previo[2] + acertadas)
        return read_diagnostic(acumulado, sample_size=len(congeladas))

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
                question=self._componer(
                    session, [pregunta], {pregunta.question_version_id: existente}
                )[0],
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
        self._registrar_repaso(session, pregunta, intento.id, calificado.outcome, entrada, ahora)
        return AnswerOutcomeView(
            saved=True,
            already_answered=False,
            attempt=evaluado or intento,
            session=session,
            question=self._componer(
                session, [pregunta], {pregunta.question_version_id: evaluado or intento}
            )[0],
            correction=self._correccion(session, pregunta, evaluado or intento),
        )

    # ------------------------------------------------------------------ cerrar y leer el resultado

    def _registrar_repaso(
        self,
        session: SessionView,
        pregunta: SessionQuestionView,
        attempt_id: str,
        outcome: AttemptOutcome,
        entrada: AnswerInput,
        now: datetime,
    ) -> None:
        """Un fallo entra en el repaso solo, y un acierto lo reprograma (06_QUESTIONS §8).

        Si el repaso no está disponible en este proceso (pruebas de sesiones), no se hace nada: la
        corrección de la sesión no depende de él.
        """
        if self._review is None:
            return
        self._review.record_attempt(
            attempt_id=attempt_id,
            question_version_id=pregunta.question_version_id,
            opposition_id=session.opposition_id,
            outcome=outcome,
            confidence=entrada.confidence,
            now=now,
        )

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

    def recalculate(self, session_id: str) -> SessionResultView:
        """Recalcula una sesión terminada con la clave **que esté activa ahora**.

        Es lo que hace S08 con una clave corregida: la sesión no se reescribe —lo que se presentó y
        lo que se contestó siguen donde estaban— pero sus intentos se corrigen otra vez con la
        plantilla nueva, y esa corrección es una **evaluación nueva** que sustituye a la anterior
        (invariante 7). El resultado de antes se conserva para poder explicar el cambio.

        Si la clave activa no dice nada de una pregunta (la plantilla nueva no la cubre), esa
        pregunta queda fuera del cálculo con su motivo: no se hereda la corrección anterior como si
        la clave nueva la respaldara.
        """
        session = self._session_or_404(session_id)
        if not session.is_finished:
            raise SessionStateError(
                "solo se recalcula una sesión terminada: su resultado se calcula al terminarla"
            )
        ahora = self._clock.now()
        entradas: dict[str, tuple[str | None, KeyEntryView]] = {}
        etiquetas: list[str] = []
        claves: set[str] = set()
        for fuente in session.configuration.sources:
            clave = self._clave_activa(fuente.question_set_id)
            claves.add(clave.id)
            etiquetas.append(f"{fuente.part_code}: plantilla v{clave.version_no}")
            for entrada_clave in clave.entries:
                entradas[entrada_clave.question_version_id] = (clave.id, entrada_clave)

        preguntas = self._study.session_questions(session_id)
        intentos = self._indice_intentos(session_id)
        overrides: dict[str, GradedAttempt] = {}
        for vista in preguntas:
            intento = intentos.get(vista.question_version_id)
            if intento is None:
                continue
            encontrada = entradas.get(vista.question_version_id)
            clave_id = None if encontrada is None else encontrada[0]
            entrada = None if encontrada is None else encontrada[1]
            calificado = grade_attempt(
                chosen_option_keys=intento.chosen_option_keys,
                frozen_outcome=entrada.outcome if entrada is not None else None,
                frozen_correct_keys=(entrada.correct_option_keys if entrada is not None else ()),
                penalty=self._penalizacion(session, vista),
            )
            overrides[vista.question_version_id] = calificado
            self._study.save_evaluation(
                attempt_id=intento.id,
                outcome=calificado.outcome.value,
                score=calificado.score,
                reason=calificado.reason,
                answer_key_version_id=clave_id,
                supersedes_id=intento.evaluation_id,
                now=ahora,
            )

        anterior = self._study.result_json(session_id)
        resultado = self._calcular(
            session_id,
            session,
            overrides=overrides,
            key_version_id=next(iter(claves)) if len(claves) == 1 else None,
            key_label=" · ".join(etiquetas),
        )
        self._study.store_result(
            session_id,
            result_json=self._resultado_json(resultado),
            previous_result_json=anterior,
            now=ahora,
        )
        return self.result(session_id)

    def recalculate_set(self, question_set_id: str) -> BulkRecalculationView:
        """Recalcula **todas** las sesiones terminadas del conjunto con la clave activa (DEBT-013).

        El problema que resuelve: una clave mal importada se corrige después de veinte sesiones, y
        hasta ahora había que recalcularlas una por una —y las que nadie recordara se quedaban con
        la puntuación vieja—. Aquí se hace de una vez, y el informe dice **sesión por sesión** qué
        cambió y cuánto, porque un «hecho» sin números no permite comprobar nada.

        Lo que **no** hace: inventar una puntuación nueva donde no la hay. Una sesión que la clave
        activa no cubre se recalcula igual (es lo que hace `recalculate`) y su resultado lo dirá. Y
        las sesiones que siguen en marcha no entran: se corrigen al terminar.
        """
        if self._questions.get_set(question_set_id) is None:
            raise NotFoundError("conjunto de preguntas", question_set_id)
        # La clave activa es la que corrige; sin ella no hay con qué recalcular, y se dice con el
        # mismo error que usa el resto del servicio para ese caso.
        activa = self._clave_activa(question_set_id)

        anteriores: dict[str, tuple[Fraction, str, str]] = {}
        for session_id in self._study.finished_sessions_of_set(question_set_id):
            antes = self._study.get_session(session_id)
            if antes is not None and antes.result is not None:
                anteriores[session_id] = (
                    antes.result.total.score.value,
                    antes.result.total.score.fraction,
                    antes.result.key_label or "",
                )

        cambios: list[SessionRecalculationView] = []
        for session_id, (antes_total, antes_fraccion, antes_etiqueta) in anteriores.items():
            # `recalculate` devuelve el resultado **nuevo** (no la sesión), así que lo que compara
            # es ese resultado con la foto tomada antes de recalcular.
            resultado = self.recalculate(session_id)
            nueva_total = resultado.total.score.value
            nueva_etiqueta = resultado.key_label or ""
            cambios.append(
                SessionRecalculationView(
                    session_id=session_id,
                    previous_total=antes_fraccion,
                    new_total=resultado.total.score.fraction,
                    previous_key_label=antes_etiqueta,
                    new_key_label=nueva_etiqueta,
                    changed=nueva_total != antes_total or nueva_etiqueta != antes_etiqueta,
                )
            )

        cambiadas = sum(1 for cambio in cambios if cambio.changed)
        return BulkRecalculationView(
            question_set_id=question_set_id,
            key_version=activa.version_no,
            sessions=tuple(cambios),
            changed=cambiadas,
            detail=(
                f"{len(cambios)} sesión(es) recalculadas con la plantilla v{activa.version_no}: "
                f"{cambiadas} cambiaron de puntuación o de plantilla"
                if cambios
                else (
                    "no hay sesiones terminadas de este conjunto: no hay nada que recalcular "
                    "(las que estén en marcha se corrigen al terminar)"
                )
            ),
        )

    def outdated_sessions(self, question_set_id: str) -> OutdatedSessionsView:
        """Cuántas sesiones terminadas quedan sin corregir con la clave **activa** (DEBT-013).

        Es la mitad que faltaba del recálculo en bloque: `recalculate_set` dice cuántas cambiaron
        **después** de recalcular, y esta dice cuántas lo necesitan **antes**. Sin ella, activar una
        plantilla corregida y no recalcular no se notaba en ninguna parte.

        Lo que no hace: llamar «desactualizada» a una sesión sin ninguna corrección guardada. Esas
        se cuentan aparte, porque no hay nada que comparar y presentarlas como pendientes dejaría
        un número que no bajaría nunca.
        """
        conjunto = self._questions.get_set(question_set_id)
        if conjunto is None:
            raise NotFoundError("conjunto de preguntas", question_set_id)
        activa = self._clave_activa(question_set_id)
        terminadas = self._study.finished_sessions_of_set(question_set_id)
        desactualizadas, sin_correccion = self._study.session_key_state_of_set(
            question_set_id, activa.id
        )
        al_dia = len(terminadas) - len(desactualizadas) - len(sin_correccion)
        return OutdatedSessionsView(
            question_set_id=question_set_id,
            key_version=activa.version_no,
            key_id=activa.id,
            finished=len(terminadas),
            up_to_date=al_dia,
            outdated=len(desactualizadas),
            without_evaluation=len(sin_correccion),
            outdated_session_ids=desactualizadas,
            detail=(
                "no hay sesiones terminadas de este conjunto: no hay nada que comparar"
                if not terminadas
                else (
                    f"de {len(terminadas)} sesión(es) terminadas, {len(desactualizadas)} no están "
                    f"corregidas con la plantilla v{activa.version_no} activa"
                    + (
                        f"; {len(sin_correccion)} no tienen ninguna corrección guardada, así que "
                        "no se pueden comparar"
                        if sin_correccion
                        else ""
                    )
                )
            ),
        )

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
                f"la parte «{parte.code}» se corrige como «{parte.format}», que no es una forma "
                "conocida: este slice corrige respuesta única, marcar errores y psicotécnicas"
            )
        return _PartContext(
            code=parte.code,
            name=parte.name,
            rule=StudyService._regla(parte),
            ordinary_items=parte.ordinary_items,
            reserve_items=parte.reserve_items,
            # El tiempo es de la parte y, si ella no lo dice, del grupo que la contiene: en TAI el
            # límite de 120 minutos está en el ejercicio único, no en cada parte.
            time_minutes=StudyService._tiempo(convocatoria, parte),
            format=parte.format,
        )

    @staticmethod
    def _regla(parte: ExamPart) -> PartRule:
        """Con qué regla se corrige una parte, según **lo que su convocatoria publica**.

        Tres formas, y ninguna se elige por gusto (ADR-011):

        1. la parte se evalúa como apto o no apto por número de errores (`fail_if_errors_gte`);
        2. la convocatoria publica la fórmula completa —`Y`, `T` y `N`— y entonces la puntuación de
           la prueba **es** la publicada (`Px = (Y/T)·(A - E/(N-1))`, Guardia Civil);
        3. la convocatoria solo publica la penalización (TAI): se calcula la puntuación directa y su
           calificación oficial queda declarada como no disponible.

        Si una parte no publica ni umbral de errores ni penalización ni la fórmula completa, no hay
        forma de corregirla y se dice, en lugar de calcular con un valor inventado.
        """
        if parte.fail_if_errors_gte is not None:
            return PartRule(
                code=parte.code,
                name=parte.name,
                ordinary_items=parte.ordinary_items,
                score_min=parte.score_min,
                score_max=parte.score_max,
                pass_score=parte.pass_score,
                kind=ScoringKind.PASS_FAIL,
                fail_if_errors_gte=parte.fail_if_errors_gte,
                format=parte.format,
            )
        if (
            parte.options_per_question is not None
            and parte.score_max is not None
            and parte.ordinary_items
        ):
            return PartRule(
                code=parte.code,
                name=parte.name,
                ordinary_items=parte.ordinary_items,
                score_min=parte.score_min,
                score_max=parte.score_max,
                pass_score=parte.pass_score,
                kind=ScoringKind.SCALED,
                options_per_question=parte.options_per_question,
                penalty=(
                    exact_fraction(parte.wrong_penalty_fraction)
                    if parte.wrong_penalty_fraction is not None
                    else Fraction(1, parte.options_per_question - 1)
                ),
                format=parte.format,
            )
        if parte.wrong_penalty_fraction is None:
            raise UnsupportedError(
                f"la convocatoria no publica cómo se corrige la parte «{parte.code}»: ni su umbral "
                "de errores, ni su fórmula, ni su penalización"
            )
        return PartRule(
            code=parte.code,
            name=parte.name,
            ordinary_items=parte.ordinary_items,
            score_min=parte.score_min,
            score_max=parte.score_max,
            pass_score=parte.pass_score,
            penalty=exact_fraction(parte.wrong_penalty_fraction),
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
        self,
        fuente: SourceInput,
        parte: _PartContext,
        modo: SessionMode,
        *,
        recently_seen: frozenset[str] = frozenset(),
    ) -> tuple[QuestionView, ...]:
        """Las preguntas de una fuente: ordinarias primero y reservas después, sin inventar.

        En un **simulacro** el banco se ordena antes de elegir: primero las preguntas que no se han
        visto hace poco y después las demás, para que las que entran sean las frescas (DEBT-012). El
        examen oficial **no** reordena: se presenta en el orden de su publicación.
        """
        conjunto = self._questions.get_set(fuente.question_set_id)
        if conjunto is None:
            raise NotFoundError("conjunto de preguntas", fuente.question_set_id)
        todas = self._questions.all_questions(fuente.question_set_id)
        validas = [
            pregunta for pregunta in todas if pregunta.question_type in _SUPPORTED_QUESTION_TYPES
        ]
        ordinarias = [pregunta for pregunta in validas if not pregunta.is_reserve]
        reservas = [pregunta for pregunta in validas if pregunta.is_reserve]

        if modo is SessionMode.MOCK_EXAM and recently_seen:
            por_id = {pregunta.id: pregunta for pregunta in ordinarias}
            frescas, vistas = order_for_mock(
                [pregunta.id for pregunta in ordinarias], recently_seen=recently_seen
            )
            ordinarias = [por_id[identificador] for identificador in (*frescas, *vistas)]

        if modo in (SessionMode.OFFICIAL_EXAM, SessionMode.MOCK_EXAM):
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
        """La penalización con la que se corrige una pregunta.

        Una pregunta **sin parte declarada** se corrige sin penalización: es el caso de un
        diagnóstico,
        cuya muestra sale del banco y no de una parte del examen. Aplicarle la penalización de una
        parte
        inventada sería peor que corregir en directo, y el resultado ya lo dice (`part_code` nulo y
        forma de cálculo directa).
        """
        if pregunta.part_code is None:
            return Fraction(0)
        return self._parte_de(session, pregunta.part_code).rule.penalty

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

    def _calcular(
        self,
        session_id: str,
        session: SessionView,
        *,
        overrides: Mapping[str, GradedAttempt] | None = None,
        key_version_id: str | None = None,
        key_label: str | None = None,
    ) -> SessionResultView:
        """El cálculo del resultado: composición efectiva, partes y total, con aritmética exacta.

        `overrides` es lo que usa el recálculo: los intentos ya corregidos con la clave **nueva**,
        que sustituyen a los de la clave congelada sin tocar lo que se presentó.
        """
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
            if overrides is not None and vista.question_version_id in overrides:
                calificados[vista.question_version_id] = overrides[vista.question_version_id]
                continue
            calificados[vista.question_version_id] = self._calificar(
                session, vista, intento.chosen_option_keys
            )

        items, sustituciones = effective_composition(congeladas, calificados)
        reglas = self._reglas_de_partes(session, congeladas)
        resultado = aggregate(
            session_id=session_id,
            mode=session.mode,
            answer_key_version_id=(
                session.answer_key_version_id if key_version_id is None else key_version_id
            ),
            items=items,
            substitutions=sustituciones,
            part_rules=reglas,
        )
        return SessionResultView(
            session_id=resultado.session_id,
            mode=resultado.mode,
            answer_key_version_id=resultado.answer_key_version_id,
            key_label=session.key_label if key_label is None else key_label,
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
        """La regla con la que se corrige cada parte de esta sesión.

        Una parte que se puntúa con la fórmula publicada (`Px = (Y/T)·(A - E/(N-1))`) solo se puede
        escalar cuando la sesión lleva **el cuestionario completo**: `T` es el número de preguntas
        de la prueba. Si se practica con una parte de ellas, se muestra la puntuación directa y se
        dice, porque escalar cuatro preguntas a la puntuación máxima de cien sería inventar una
        nota.
        """
        convocatoria = self._profiles.get_convocation(session.convocation_version_id or "")
        if convocatoria is None:
            raise NotFoundError("convocatoria", session.convocation_version_id or "")
        reglas: dict[str | None, PartRule] = {}
        for codigo in {pregunta.part_code for pregunta in preguntas}:
            if codigo is None:
                continue
            regla = self._parte(convocatoria, codigo).rule
            presentadas = sum(
                1
                for pregunta in preguntas
                if pregunta.part_code == codigo and not pregunta.is_reserve
            )
            if (
                regla.kind is ScoringKind.SCALED
                and regla.ordinary_items is not None
                and presentadas < regla.ordinary_items
            ):
                regla = replace(
                    regla,
                    kind=ScoringKind.DIRECT,
                    # Sin la `N` publicada no habría penalización: se usa la de la fórmula, que es
                    # `1/(N-1)`, y con ella la puntuación directa es la misma que la del bruto.
                    penalty=Fraction(1, (regla.options_per_question or 4) - 1),
                    note=(
                        f"Práctica parcial de «{regla.name}»: la fórmula de la convocatoria "
                        f"({regla.ordinary_items} preguntas) se aplica al cuestionario "
                        "completo, así que aquí se muestra la puntuación directa y no se "
                        "declara superada."
                    ),
                )
            reglas[codigo] = regla
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
            kind=parte.kind.value,
            correct=parte.correct,
            wrong=parte.wrong,
            blank=parte.blank,
            annulled=parte.annulled,
            excluded=parte.excluded,
            conflicting=parte.conflicting,
            reserves_used=parte.reserves_used,
            unused_reserves=parte.unused_reserves,
            score=ScoreView(parte.score),
            passed=parte.passed,
            verdict_note=parte.verdict_note,
            official_available=parte.official_available,
        )

    @staticmethod
    def _parte_json(parte: PartScoreView) -> dict[str, object]:
        """Una parte del resultado: recuentos, forma de cálculo y puntuación exacta."""
        return {
            "part_code": parte.part_code,
            "part_name": parte.part_name,
            "ordinary_items": parte.ordinary_items,
            "score_min": parte.score_min,
            "score_max": parte.score_max,
            "pass_score": parte.pass_score,
            "penalty": parte.penalty.fraction if parte.penalty is not None else None,
            "kind": parte.kind,
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
            "passed": parte.passed,
            "verdict_note": parte.verdict_note,
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
