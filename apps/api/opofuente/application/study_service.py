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
import random
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta
from fractions import Fraction
from typing import Literal

from opofuente.application.ports import Clock
from opofuente.application.question_models import (
    AnswerKeyView,
    KeyEntryView,
    QuestionSetView,
    QuestionView,
)
from opofuente.application.read_models import ConvocationDetail, NodeView, OppositionDetail
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
from opofuente.domain.questions import KeyOutcome
from opofuente.domain.study import (
    OWNER_ID_LOCAL,
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
from opofuente.domain.topic_notes import firma_de_grupo
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
    #: Solo en práctica: el tema cuyas preguntas catalogadas componen la sesión (S13).
    curriculum_node_id: str | None = None


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


#: Los filtros con los que se eligen las preguntas de una composición. `all` no filtra; los otros
#: tres miran lo que ya hizo quien estudia, que es lo que hace que «un test de lo que fallé» sea un
#: test de lo que falló y no de lo que le apetezca al orden del banco.
CompositionFilter = Literal["all", "unseen", "failed", "flagged"]


@dataclass(frozen=True, slots=True)
class PartSpec:
    """Una parte de una composición: de qué nodos del programa y cuántas preguntas.

    `node_ids` son nodos del temario: un tema trae sus preguntas y un bloque trae las de sus temas
    (se recorre su subárbol). `alternative_group` marca las partes **excluyentes entre sí** —el
    supuesto práctico de III o el de IV—: de un grupo se compone una, nunca las dos, y si llegan las
    dos se compone la primera y se dice.

    `weights` es el reparto por nodo (`{node_id: peso}`). Sin él el reparto es **proporcional a lo
    que hay** en cada nodo, que es lo que hace que un bloque con más preguntas pese más en el
    simulacro sin que nadie escriba una tabla a mano.
    """

    code: str
    node_ids: tuple[str, ...]
    count: int
    reserve: int = 0
    alternative_group: str | None = None
    weights: Mapping[str, float] | None = None


@dataclass(frozen=True, slots=True)
class CompositionSpec:
    """Cómo se monta una sesión, **declarado**: es la única forma de componer.

    De aquí salen todos los casos —el test de varios temas, el simulacro con su supuesto, el examen
    de un solo conjunto—, y por eso hay un solo sitio donde se decide qué clave se congela, cómo se
    numeran las reservas y con qué penalización se corrige. Un segundo camino de composición sería
    una segunda verdad sobre cómo se corrige una sesión.
    """

    parts: tuple[PartSpec, ...]
    mode: SessionMode = SessionMode.PRACTICE
    filter: CompositionFilter = "all"
    owner_id: str = OWNER_ID_LOCAL
    #: Se guarda con la sesión: la misma semilla elige las mismas preguntas, y una sesión que se
    #: quiere reproducir (una incidencia, una revisión) se puede volver a montar igual.
    seed: int | None = None
    #: Un simulacro o un examen: se parece al examen real, así que deja fuera las preguntas que no
    #: son de este temario (normativa y organización de otra administración).
    exam_like: bool = False
    #: En modo público solo entran preguntas de conjuntos publicables: enseñar la nota de un banco
    #: privado sería enseñar, en cifras, lo que pasa dentro de él.
    public_only: bool = False
    feedback: Feedback | None = None
    shuffle: bool = False
    #: El límite de tiempo, cuando la composición **no** es el perfil exacto del examen: una
    #: variante corta del simulacro tiene su propio tiempo y se dice. Si es `None`, manda el de la
    #: convocatoria (en TAI, los 120 minutos del ejercicio único).
    time_limit_minutes: int | None = None
    label: str | None = None
    note: str | None = None
    #: De dónde salió el supuesto práctico cuando no había preguntas de supuesto de verdad: se
    #: compone del bloque elegido y la sesión lo declara (`"bloque"`). No se inventa que es un
    #: supuesto si no lo es.
    practical_case_origin: str | None = None


@dataclass(frozen=True, slots=True)
class PartComposition:
    """Qué pidió una parte y qué se pudo montar: es lo que la respuesta dice cuando
    falta material."""

    code: str
    requested: int
    selected: int
    available: int
    reserves_requested: int = 0
    reserves_selected: int = 0


@dataclass(frozen=True, slots=True)
class CompositionResult:
    """La sesión montada y, por parte, lo que se pidió frente a lo que había."""

    session: SessionView
    parts: tuple[PartComposition, ...]

    @property
    def short(self) -> tuple[PartComposition, ...]:
        """Las partes a las que les faltó material: la respuesta lo dice, no falla por ello."""
        return tuple(parte for parte in self.parts if parte.selected < parte.requested)


@dataclass(frozen=True, slots=True)
class RunnerView:
    """La sesión como la lee la pantalla que la corre: la pregunta que toca y todas las demás.

    `current` es la primera sin responder (o `None` si ya están todas) y `questions` es la sesión
    entera, que es lo que necesita la hoja de respuestas para pintar sus filas.
    """

    session: SessionView
    current: SessionQuestionView | None
    questions: tuple[SessionQuestionView, ...]
    answered: int
    total: int
    pending: int
    finished: bool


@dataclass(frozen=True, slots=True)
class _Candidata:
    """Una pregunta que puede entrar en una composición, con lo que hace falta para congelarla.

    `signature` es la firma de «la misma pregunta» (enunciado y opciones normalizados) que usa el
    motor de apuntes: dos bancos pueden traer la misma pregunta y en una sesión no puede caer dos
    veces. `node_id` es el nodo del programa por el que entró: una pregunta catalogada en dos temas
    cuenta en el **primero** que la pidió, para que el reparto no la sume dos veces.

    `key_id` es `None` cuando la pregunta se corrige con su **clave derivada** (§1 del encargo F29):
    esa letra no vive en ninguna plantilla del conjunto: no hay identificador que
    apuntar, y la sesión no puede decir que se corrige con una.
    """

    question: QuestionView
    key_id: str | None
    entry: KeyEntryView
    signature: str
    node_id: str
    reserve_order: int | None = None


@dataclass(frozen=True, slots=True)
class _ClavesDelBanco:
    """Lo que la derivación (§1 del encargo F29) cambió en el banco, por pregunta.

    - **`derivadas`**: la letra de la clave derivada de cada pregunta. La pregunta se corrige con
      ella, tenga o no plantilla activa su conjunto, y su conjunto esté o no en cuarentena.
    - **`fuera`**: las preguntas con **motivo de fuera** escrito, que la derivación no pudo
      arreglar. Siguen fuera **aunque su conjunto vuelva** a los tests, que es la mitad del encargo
      que dice que las que no tienen clave fiable siguen fuera de ese conjunto.

    Se lee una vez por operación y se pasa a los sitios que eligen preguntas. Las dos tablas están
    vacías hasta que se corre la derivación, y entonces esto no cambia nada de lo de siempre.
    """

    derivadas: Mapping[str, tuple[str, ...]] = field(default_factory=dict)
    fuera: frozenset[str] = frozenset()
    conjuntos: frozenset[str] = frozenset()

    @property
    def vacio(self) -> bool:
        return not self.derivadas and not self.fuera

    def letras(self, question_version_id: str) -> tuple[str, ...] | None:
        """La letra derivada de esa pregunta, o `None` si no tiene."""
        return self.derivadas.get(question_version_id)

    def es_derivada(self, set_id: str) -> bool:
        """¿Este conjunto tiene alguna clave derivada? Lo pregunta el diagnóstico, que elige
        conjuntos enteros y no puede dejar fuera uno con letras derivadas dentro."""
        return set_id in self.conjuntos

    def entrada(self, question_version_id: str) -> KeyEntryView | None:
        """La entrada de clave de esa pregunta, si su clave es **derivada**."""
        letras = self.letras(question_version_id)
        if letras is None:
            return None
        return KeyEntryView(
            question_version_id=question_version_id,
            outcome=KeyOutcome.KEYED.value,
            correct_option_keys=letras,
            notes="clave derivada: los apuntes (con su cita) y el modelo sin apuntes coinciden",
        )

    def sigue_fuera(self, question_version_id: str) -> bool:
        """¿Esta pregunta tiene escrito su motivo de fuera?"""
        return question_version_id in self.fuera

    def con_letra_propia(self, question_ids: Sequence[str]) -> int:
        """Cuántas de esas preguntas traen su clave derivada."""
        return sum(1 for question_id in question_ids if self.letras(question_id) is not None)


@dataclass(frozen=True, slots=True)
class _Correccion:
    """Con qué se corrige un conjunto: su plantilla (o ninguna) y la entrada de cada pregunta.

    `key_id` es `None` cuando el conjunto **no tiene plantilla activa** y solo corrige por claves
    derivadas: la sesión no se corrige con una plantilla y no puede decir que sí.
    """

    key_id: str | None
    label: str
    entradas: Mapping[str, KeyEntryView]

    def entrada(self, question_version_id: str) -> KeyEntryView | None:
        return self.entradas.get(question_version_id)


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
        if request.mode is SessionMode.PRACTICE and request.curriculum_node_id is not None:
            # Práctica de un tema concreto (S13): la composición la pone la catalogación del tema,
            # así
            # que no se eligen conjuntos y la sesión no puede quedar vacía en silencio.
            return self._create_topic_session(request, convocatoria)
        if not request.sources:
            raise UnsupportedError("una sesión necesita al menos un conjunto de preguntas")

        #: Las partes que la sesión usa: se resuelven una vez y viajan con la composición.
        contexto: dict[str, _PartContext] = {}
        congeladas: list[FrozenQuestion] = []
        claves: set[str] = set()
        etiquetas: list[str] = []
        limite_tiempo: int | None = None
        banco = self._banco()
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
            conjunto_fuente = self._questions.get_set(fuente.question_set_id)
            preguntas = self._preguntas(
                fuente, parte, request.mode, recently_seen=vistas_hace_poco, banco=banco
            )
            correccion = (
                self._correccion_de(conjunto_fuente, preguntas, banco)
                if conjunto_fuente is not None
                else None
            )
            if correccion is not None and correccion.key_id is not None:
                claves.add(correccion.key_id)
            etiquetas.append(
                f"{parte.name}: {correccion.label if correccion is not None else 'sin plantilla'}"
            )
            if request.mode is SessionMode.MOCK_EXAM:
                # Cuántas de las elegidas se habían visto hace poco: el orden de `_preguntas`
                # prefiere
                # las frescas, y lo que no se puede evitar se dice en la nota de la sesión.
                repetidas += sum(1 for pregunta in preguntas if pregunta.id in vistas_hace_poco)
            # Las reservas se numeran al congelarlas: la convocatoria las valora **por su orden**, y
            # una reserva sin orden no se puede sustituir por la primera. Si el material ya traía un
            # orden, se respeta; si no, es el de presentación dentro de la parte.
            orden_reserva = 0
            for pregunta in preguntas:
                entrada = correccion.entrada(pregunta.id) if correccion is not None else None
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
            context_label=self._etiqueta_de_fuentes(request.sources),
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

    def _create_topic_session(
        self, request: CreateSessionInput, convocatoria: ConvocationDetail
    ) -> SessionView:
        """Monta una sesión con las preguntas catalogadas en un tema concreto (S13).

        Tres decisiones, y las tres se ven en el código:

        1. **la composición la pone la catalogación**, no quien estudia: se practica lo que está
           mapeado al tema con mapeo **aceptado**, que es exactamente lo que la cifra «preguntas: N»
           del Programa cuenta. Si aquí se pudiera elegir otra cosa, la pantalla y la sesión dirían
           números distintos del mismo tema;
        2. **el tema es el exacto**, no su subárbol: un bloque cuyas preguntas están catalogadas en
        sus
           temas no tiene preguntas propias, y eso se dice en lugar de mezclar temas que nadie ha
           pedido;
        3. **la parte no se declara**, igual que en el diagnóstico: la pregunta del banco no dice a
        qué
           parte del examen pertenece, e inventarla cambiaría la corrección (la penalización la fija
           la
           convocatoria por parte). Se corrige en directo y la sesión lo declara.
        """
        if request.sources:
            raise UnsupportedError(
                "una práctica por tema la compone la catalogación del tema: no se eligen los "
                "conjuntos a mano (usa la práctica normal si quieres elegir tú)"
            )
        if request.curriculum_node_id is None:  # pragma: no cover - lo garantiza el llamante
            raise UnsupportedError("una práctica por tema necesita el tema")
        candidatas = self._questions.question_ids_of_node(request.curriculum_node_id)
        if not candidatas:
            raise UnsupportedError(
                "este tema no tiene ninguna pregunta catalogada: se catalogan al importarlas o "
                "asignándolas en Revisión, y sin preguntas no hay sesión que montar"
            )

        ahora = self._clock.now()
        claves: dict[str, str] = {}
        etiquetas: list[str] = []
        congeladas: list[FrozenQuestion] = []
        sin_clave = 0
        sin_respuesta = 0
        no_practicables = 0
        en_cuarentena = 0
        derivadas = 0
        banco = self._banco()
        for question_id in candidatas:
            pregunta = self._questions.get_question(question_id)
            if pregunta is None or pregunta.question_type not in _SUPPORTED_QUESTION_TYPES:
                no_practicables += 1
                continue
            if pregunta.is_reserve:
                # Una reserva no se practica sola: entra en un examen para sustituir a otra.
                no_practicables += 1
                continue
            conjunto = self._questions.get_set(pregunta.question_set_id)
            propia = banco.entrada(pregunta.id)
            if propia is not None:
                # La clave derivada de la pregunta manda sobre la plantilla del conjunto y sobre su
                # cuarentena (§1 del encargo F29): es la letra que la devuelve al estudio.
                entrada: KeyEntryView | None = propia
                derivadas += 1
                if pregunta.question_set_id not in claves:
                    activa = self._clave_activa_o_none(pregunta.question_set_id)
                    if activa is not None:
                        claves[pregunta.question_set_id] = activa.id
                    etiqueta = (
                        f"{conjunto.title}: plantilla v{activa.version_no}"
                        if activa is not None and conjunto is not None
                        else f"{conjunto.title if conjunto else pregunta.question_set_id}: "
                        "claves derivadas"
                    )
                    if etiqueta not in etiquetas:
                        etiquetas.append(etiqueta)
            elif conjunto is None or conjunto.active_key_id is None:
                # Sin plantilla activa no hay con qué corregir: se queda fuera y se cuenta.
                sin_clave += 1
                continue
            elif conjunto.key_is_unreliable or banco.sigue_fuera(pregunta.id):
                # Cuarentena de clave (§1) o motivo de fuera escrito (§1 de F29): la práctica por
                # tema es uno de los sitios donde se eligen preguntas: se salta aquí también.
                # No es «no se puede corregir»: es que la clave no es de fiar y su letra no se pudo
                # derivar.
                en_cuarentena += 1
                continue
            else:
                clave = self._clave_activa(pregunta.question_set_id)
                claves[pregunta.question_set_id] = clave.id
                etiqueta = f"{conjunto.title}: plantilla v{clave.version_no}"
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
            if entrada is None or entrada.outcome != KeyOutcome.KEYED.value:
                # La plantilla activa no dice cuál es la buena (no tiene entrada, o la anula, o se
                # contradice): la pregunta no se puede corregir y responderla no contaría. Antes
                # entraba igual y se corregía como «excluida»; en una práctica, que elige las
                # preguntas, se deja fuera y se cuenta.
                sin_respuesta += 1
                continue
            congeladas.append(
                FrozenQuestion(
                    question_version_id=pregunta.id,
                    stable_key=pregunta.stable_key,
                    position=len(congeladas) + 1,
                    part_code=None,
                    is_reserve=False,
                    reserve_order=None,
                    key_outcome=entrada.outcome if entrada is not None else None,
                    correct_option_keys=(
                        entrada.correct_option_keys if entrada is not None else ()
                    ),
                )
            )

        if not congeladas:
            motivo = (
                f"{sin_clave} sin plantilla activa, {sin_respuesta} que la plantilla activa no "
                f"responde, {en_cuarentena} con la clave en cuarentena y {no_practicables} que "
                "no se practican solas (reservas o tipo no soportado)"
                if sin_clave or sin_respuesta or no_practicables or en_cuarentena
                else "ninguna con plantilla activa"
            )
            raise UnsupportedError(
                f"las preguntas de este tema no se pueden corregir todavía: {motivo}"
            )

        configuracion = SessionConfiguration(
            mode=SessionMode.PRACTICE,
            feedback=request.feedback or Feedback.IMMEDIATE,
            sources=(),
            time_limit_minutes=None,
            shuffle=request.shuffle,
            note=self._nota_del_tema(
                total=len(congeladas),
                sin_clave=sin_clave,
                sin_respuesta=sin_respuesta,
                no_practicables=no_practicables,
                en_cuarentena=en_cuarentena,
                derivadas=derivadas,
            ),
            context_label=self._etiqueta_del_tema(request.curriculum_node_id),
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

    # ------------------------------------------------------------------ componer (una sola forma)
    #
    # Todo lo que monta una sesión con preguntas elegidas pasa por `compose`: el test de varios
    # temas, el simulacro con su supuesto y el examen de un conjunto. Los caminos que ya existían
    # (por conjunto y por tema) siguen donde estaban porque tienen reglas propias —el examen toma la
    # parte entera de su conjunto, la práctica por tema la pone la catalogación—, pero **no** hay un
    # tercer sitio donde se congele una clave: `compose` usa `_clave_activa` y `FrozenQuestion`, los
    # mismos que ellos.

    def compose(self, spec: CompositionSpec, *, opposition_id: str) -> CompositionResult:
        """Monta una sesión a partir de una composición declarada (`CompositionSpec`).

        La oposición viaja aparte de la composición a propósito: **de qué** es una sesión (sus
        temas,
        sus partes, sus filtros) y **dónde** se estudia (la oposición, con su convocatoria y su
        forma de corregir) son dos cosas distintas, y mezclarlas en el mismo saco haría que una
        composición no se pudiera reutilizar.

        Nunca falla por falta de material: monta la sesión con lo que haya y **dice** lo que pidió y
        lo que había por parte (`CompositionResult.parts`). Un test de 50 con 30 preguntas
        disponibles es un test de 30 que lo dice, no un error que deja al alumno sin estudiar.
        """
        if not spec.parts:
            raise UnsupportedError("una composición sin partes no monta ninguna sesión")
        oposicion = self._profiles.get_opposition(opposition_id)
        if oposicion is None:
            raise NotFoundError("oposición", opposition_id)
        convocatoria = self._convocatoria_de(oposicion.opposition.convocation_id)

        vistas = self._estado_de_quien_estudia(spec, opposition_id)
        banco = self._banco()
        contexto: dict[str, _PartContext] = {}
        congeladas: list[FrozenQuestion] = []
        claves: set[str] = set()
        conjuntos: set[str] = set()
        etiquetas: list[str] = []
        partes: list[PartComposition] = []
        grupos_vistos: dict[str, PartSpec] = {}
        limite_tiempo: int | None = spec.time_limit_minutes
        firmas: set[str] = set()

        for parte in spec.parts:
            if parte.alternative_group is not None:
                if parte.alternative_group in grupos_vistos:
                    # Dos partes excluyentes a la vez (el supuesto de III **y** el de IV) no se
                    # montan: se compone la primera y se dice, en vez de duplicar el supuesto.
                    continue
                grupos_vistos[parte.alternative_group] = parte
            if parte.code in contexto:
                raise UnsupportedError(
                    f"la composición repite la parte «{parte.code}»: dos partes con el mismo "
                    "no se pueden corregir por separado"
                )
            if parte.code in {candidata.code for candidata in convocatoria.parts}:
                contexto_parte = self._parte(convocatoria, parte.code)
                contexto[contexto_parte.code] = contexto_parte
                if spec.time_limit_minutes is None and contexto_parte.time_minutes is not None:
                    limite_tiempo = (
                        contexto_parte.time_minutes
                        if limite_tiempo is None
                        else max(limite_tiempo, contexto_parte.time_minutes)
                    )
            # Una parte de la composición que **no** es una parte de la convocatoria (un test de
            # temas, por ejemplo) se congela **sin parte declarada**: no tiene regla publicada, y
            # aplicarle la de una parte que no es la suya sería corregir con un dato inventado. Se
            # corrige en directo, igual que una práctica por tema.
            codigo_congelado = (
                parte.code
                if parte.code in {candidata.code for candidata in convocatoria.parts}
                else None
            )

            candidatas, disponibles = self._candidatas(parte, spec, vistas, banco)
            elegidas = self._repartir(parte, candidatas, firmas)
            reservas = self._reservas(parte, candidatas, firmas, elegidas)
            for candidata in (*elegidas, *reservas):
                firmas.add(candidata.signature)
                if candidata.key_id is not None:
                    # Sin plantilla activa no hay identificador que apuntar: la pregunta se corrige
                    # con su clave derivada y la sesión no dice que se corrige con una plantilla.
                    claves.add(candidata.key_id)
                conjuntos.add(candidata.question.question_set_id)
                congeladas.append(
                    FrozenQuestion(
                        question_version_id=candidata.question.id,
                        stable_key=candidata.question.stable_key,
                        position=candidata.question.position,
                        part_code=codigo_congelado,
                        is_reserve=candidata.reserve_order is not None,
                        reserve_order=candidata.reserve_order,
                        key_outcome=candidata.entry.outcome,
                        correct_option_keys=candidata.entry.correct_option_keys,
                    )
                )
            partes.append(
                PartComposition(
                    code=parte.code,
                    requested=parte.count,
                    selected=len(elegidas),
                    available=disponibles,
                    reserves_requested=parte.reserve,
                    reserves_selected=len(reservas),
                )
            )

        if not congeladas:
            raise UnsupportedError(
                "no hay ninguna pregunta que se pueda poner: de los temas elegidos, ninguna tiene "
                "plantilla activa con su respuesta (y las que no la tienen no se pueden corregir)"
            )

        etiquetas = self._etiquetas_de_conjuntos(conjuntos)
        derivadas = banco.con_letra_propia(
            [congelada.question_version_id for congelada in congeladas]
        )
        if derivadas:
            # Se dice en la etiqueta de la clave de la sesión: una sesión corregida en parte con
            # claves derivadas no se corrige igual que una con la plantilla entera: el alumno tiene
            # que poder verlo después.
            etiquetas.append(f"{derivadas} clave(s) derivada(s)")

        # Un examen y un simulacro corrigen al terminar: enseñar la corrección mientras se contesta
        # filtraría la solución, y `SessionConfiguration` lo exige también desde el dominio.
        modo_examen = spec.mode in (SessionMode.OFFICIAL_EXAM, SessionMode.MOCK_EXAM)
        feedback = Feedback.AT_END if modo_examen else (spec.feedback or Feedback.IMMEDIATE)
        configuracion = SessionConfiguration(
            mode=spec.mode,
            feedback=feedback,
            sources=(),
            time_limit_minutes=limite_tiempo,
            shuffle=spec.shuffle,
            note=spec.note,
            context_label=spec.label,
            practical_case_origin=spec.practical_case_origin,
        )
        plan = assign_positions(congeladas, shuffle=spec.shuffle)
        sesion = self._study.create_session(
            opposition_id=opposition_id,
            configuration=configuracion,
            questions=plan,
            now=self._clock.now(),
            convocation_version_id=convocatoria.summary.id,
            question_set_id=next(iter(conjuntos)) if len(conjuntos) == 1 else None,
            answer_key_version_id=next(iter(claves)) if len(claves) == 1 else None,
            time_limit_minutes=limite_tiempo,
            key_label=" · ".join(etiquetas),
        )
        return CompositionResult(session=sesion, parts=tuple(partes))

    def _convocatoria_de(self, identificador: str | None) -> ConvocationDetail:
        """La convocatoria de la oposición, o el motivo por el que no se puede componer."""
        if identificador is None:
            raise UnsupportedError(
                "la oposición no tiene convocatoria: sin ella no se sabe cómo se corrige el examen"
            )
        convocatoria = self._profiles.get_convocation(identificador)
        if convocatoria is None:
            raise NotFoundError("convocatoria", identificador)
        return convocatoria

    def _estado_de_quien_estudia(
        self, spec: CompositionSpec, opposition_id: str
    ) -> Mapping[str, tuple[str | None, str | None]]:
        """Lo que ya hizo quien estudia, por pregunta: solo si la composición lo va a mirar.

        `all` no filtra, y entonces no se consulta nada: pedir el historial entero para no usarlo
        sería trabajo de la base a cambio de nada.
        """
        if spec.filter == "all":
            return {}
        return self._study.owner_last_state(opposition_id, spec.owner_id)

    def _candidatas(
        self,
        parte: PartSpec,
        spec: CompositionSpec,
        vistas: Mapping[str, tuple[str | None, str | None]],
        banco: _ClavesDelBanco,
    ) -> tuple[tuple[_Candidata, ...], int]:
        """Las preguntas que pueden entrar en una parte, en orden estable, y cuántas hay.

        Las reglas son las del contrato de la composición, y ninguna se improvisa aquí:

        - solo preguntas con **clave utilizable**: sin ella responder no cuenta;
        - **nunca dos de la misma pregunta**: dos bancos pueden traer el mismo enunciado, y
          repetirlo
          en un test de 25 sería medir dos veces lo mismo (se agrupa con la firma del motor de
          apuntes, que es la misma definición de «la misma pregunta» que usa el resto del sistema);
        - fuera las marcadas **fuera de temario** y los **enunciados rotos**: no son preguntas;
        - en modo público, solo conjuntos publicables;
        - y el filtro de lo ya hecho (`unseen`, `failed`, `flagged`) cuando se pide.

        **Y la clave, que es lo que cambió con la derivación (§1 de F29)**: una pregunta con
        clave derivada **entra** aunque su conjunto esté en cuarentena; una con motivo de fuera
        escrito **no entra**, aunque su conjunto no esté en cuarentena; y las demás entran con la
        plantilla de su conjunto, como siempre.
        """
        candidatas: list[_Candidata] = []
        vistas_del_tema: set[str] = set()
        for node_id in parte.node_ids:
            for pregunta_id in self._preguntas_del_nodo(node_id):
                if pregunta_id in vistas_del_tema:
                    continue
                vistas_del_tema.add(pregunta_id)
                pregunta = self._questions.get_question(pregunta_id)
                if pregunta is None or pregunta.question_type not in _SUPPORTED_QUESTION_TYPES:
                    continue
                conjunto = self._questions.get_set(pregunta.question_set_id)
                if conjunto is None:
                    continue
                propia = banco.entrada(pregunta.id)
                if propia is not None:
                    # La clave derivada manda sobre la plantilla del conjunto y sobre su cuarentena:
                    # es una letra con dos apoyos independientes y no depende de la extracción.
                    entrada: KeyEntryView | None = propia
                    clave_id: str | None = None
                elif conjunto.key_is_unreliable or banco.sigue_fuera(pregunta.id):
                    # Cuarentena de clave (§1) o motivo de fuera escrito (§1 de F29): la pregunta
                    # **no entra** en la parte. No se dice aquí porque el contrato de la composición
                    # ya enseña `available`, que es el número de preguntas que de verdad se pueden
                    # poner; lo que sí se hace es no contarla como disponible, que es lo que haría
                    # creer al alumno que tiene 80 preguntas cuando solo puede contestar 60.
                    continue
                elif conjunto.active_key_id is None:
                    continue
                else:
                    clave = self._clave_activa(pregunta.question_set_id)
                    entrada = next(
                        (
                            candidata
                            for candidata in clave.entries
                            if candidata.question_version_id == pregunta.id
                        ),
                        None,
                    )
                    clave_id = clave.id
                if entrada is None or entrada.outcome != KeyOutcome.KEYED.value:
                    continue
                if spec.public_only and conjunto.distribution != "public":
                    continue
                if spec.exam_like and conjunto.is_other_administration:
                    # Material de otra administración (`origin_scope`, D10): su normativa y su
                    # organización no caen en el examen de TAI, así que no entran en una composición
                    # que se parece al examen real. En un test por tema y en los apuntes **sí
                    # cuentan**: son material para estudiar, y por eso el filtro vive aquí (el
                    # embudo de examen y simulacro) y no en el recuento de preguntas.
                    continue
                if pregunta.id in self._excluidas(pregunta.question_set_id):
                    continue
                if not self._pasa_el_filtro(spec.filter, pregunta.id, vistas):
                    continue
                candidatas.append(
                    _Candidata(
                        question=pregunta,
                        key_id=clave_id,
                        entry=entrada,
                        signature=firma_de_grupo(
                            pregunta.stem,
                            tuple((opcion.stable_key, opcion.text) for opcion in pregunta.options),
                        ),
                        # El nodo por el que entró: como `vistas_del_tema` ya la ha marcado, es el
                        # **primero** de los nodos pedidos que la contiene.
                        node_id=node_id,
                    )
                )
        # Lo disponible para la parte son sus preguntas **ordinarias**: las reservas del banco no
        # cuentan para el tamaño del cuestionario, entran solo a sustituir a una anulada.
        disponibles = sum(1 for candidata in candidatas if not candidata.question.is_reserve)
        if spec.seed is not None:
            # La semilla baraja **una vez**, aquí: lo que se elige después ya es determinista, así
            # que la misma semilla monta la misma sesión y sin semilla el orden es el del programa.
            # `random` a propósito y no un generador criptográfico: esto es una semilla
            # reproducible para volver a montar la misma sesión, no un secreto.
            random.Random(spec.seed).shuffle(candidatas)  # noqa: S311
        return tuple(candidatas), disponibles

    def key_reliability_of(self, question_ids: Sequence[str]) -> dict[str, str]:
        """El veredicto de la clave del conjunto de cada pregunta (`fiable` · `dudosa` · `no`).

        Lo necesita la zona del alumno para **marcar** las preguntas de un conjunto dudoso con
        «clave en revisión» (§1). Vive aquí, y no en un servicio nuevo, porque el motor que elige
        las preguntas es el que sabe de qué conjunto salió cada una, y tener dos ideas de eso es
        como se acaba enseñando una marca que no corresponde.
        """
        return self._questions.key_reliability_by_question(question_ids)

    def derived_key_questions(self, question_ids: Sequence[str]) -> frozenset[str]:
        """Las preguntas de esa lista cuya clave es **derivada** (§1 del encargo F29).

        Son las que el alumno ve con la marca **«clave revisada automáticamente»**: su letra no sale
        de la plantilla del conjunto (que está en cuarentena o en borrador) sino de dos fuentes
        independientes que dicen lo mismo. Va aquí, con `key_reliability_of`, por el mismo motivo:
        quien sabe de la clave de una pregunta es el motor que la elige.
        """
        if not question_ids:
            return frozenset()
        derivadas = self._questions.derived_keys()
        return frozenset(question_id for question_id in question_ids if question_id in derivadas)

    def _preguntas_del_nodo(self, node_id: str) -> tuple[str, ...]:
        """Las preguntas de un nodo **y de sus descendientes**.

        Un tema trae las suyas; un bloque trae las de sus temas, que es lo que hace que «un test de
        todo el bloque IV» sea de todo el bloque y no de un bloque que no tiene preguntas propias.
        """
        nodo = self._profiles.get_node(node_id)
        if nodo is None:
            raise NotFoundError("nodo del programa", node_id)
        ids: list[str] = list(self._questions.question_ids_of_node(node_id))
        for hijo in self._descendientes(nodo.node):
            ids.extend(self._questions.question_ids_of_node(hijo))
        ordenadas: dict[str, None] = {}
        for identificador in ids:
            ordenadas.setdefault(identificador, None)
        return tuple(ordenadas)

    @staticmethod
    def _descendientes(nodo: NodeView) -> tuple[str, ...]:
        """Los identificadores de todo el subárbol de un nodo, en orden de lectura."""
        ids: list[str] = []
        for hijo in nodo.children:
            ids.append(hijo.id)
            ids.extend(StudyService._descendientes(hijo))
        return tuple(ids)

    def _excluidas(self, set_id: str) -> frozenset[str]:
        """Las preguntas del conjunto que no son preguntas: fuera de temario o enunciado roto."""
        return self._questions.excluded_question_ids(set_id)

    @staticmethod
    def _pasa_el_filtro(
        filtro: CompositionFilter,
        pregunta_id: str,
        vistas: Mapping[str, tuple[str | None, str | None]],
    ) -> bool:
        """¿Entra esta pregunta con el filtro pedido?

        `unseen` deja fuera lo ya intentado; `failed`, lo que no se falló la última vez; `flagged`,
        lo que no se marcó con poca confianza. Se mira el **último** intento: una pregunta fallada y
        después acertada no es una pregunta fallada.
        """
        if filtro == "all":
            return True
        ultimo = vistas.get(pregunta_id)
        if filtro == "unseen":
            return ultimo is None
        if ultimo is None:
            return False
        desenlace, confianza = ultimo
        if filtro == "failed":
            return desenlace == AttemptOutcome.WRONG.value
        return confianza == Confidence.LOW.value

    def _repartir(
        self, parte: PartSpec, candidatas: Sequence[_Candidata], firmas: set[str]
    ) -> tuple[_Candidata, ...]:
        """Elige las `count` preguntas ordinarias, repartidas por nodo y sin repetir ninguna.

        El reparto por nodo es proporcional a lo que hay (o a los pesos declarados), y lo que un
        nodo
        no puede dar pasa a los demás: es lo que evita que un tema con tres preguntas deje el test a
        medias teniendo el temario cientos.
        """
        if parte.count <= 0:
            return ()
        # Las reservas del banco no son preguntas ordinarias: entran por `_reservas`, a sustituir a
        # una anulada. Si se colaran aquí, una reserva ocuparía el sitio de una ordinaria y el
        # cuestionario tendría una pregunta menos de las que cuenta la parte.
        ordinarias = [candidata for candidata in candidatas if not candidata.question.is_reserve]
        por_nodo = self._por_nodo(parte, ordinarias)
        cupos = self._cupos(parte, por_nodo)
        elegidas: list[_Candidata] = []
        sobrantes: list[_Candidata] = []
        vistos: set[str] = set(firmas)
        for node_id in parte.node_ids:
            suyas = por_nodo.get(node_id, [])
            cupo = cupos.get(node_id, 0)
            tomadas = 0
            for candidata in suyas:
                if tomadas >= cupo:
                    sobrantes.append(candidata)
                    continue
                if candidata.signature in vistos:
                    continue
                vistos.add(candidata.signature)
                elegidas.append(candidata)
                tomadas += 1
        # Lo que no se pudo llenar con los cupos se completa con el resto, en el orden del programa.
        for candidata in sobrantes:
            if len(elegidas) >= parte.count:
                break
            if candidata.signature in vistos:
                continue
            vistos.add(candidata.signature)
            elegidas.append(candidata)
        return tuple(elegidas[: parte.count])

    @staticmethod
    def _por_nodo(parte: PartSpec, candidatas: Sequence[_Candidata]) -> dict[str, list[_Candidata]]:
        """Las candidatas agrupadas por el **primer** nodo de la parte al que pertenecen.

        Una pregunta puede estar catalogada en dos temas; para el reparto cuenta una vez, y en el
        primero de la lista, que es el orden en el que se pidieron: contarla en los dos haría que el
        total no cuadrara con lo que se selecciona. El nodo lo puso `_candidatas` al recogerla, así
        que aquí solo se agrupa.
        """
        por_nodo: dict[str, list[_Candidata]] = {node_id: [] for node_id in parte.node_ids}
        for candidata in candidatas:
            por_nodo.setdefault(candidata.node_id, []).append(candidata)
        return por_nodo

    @staticmethod
    def _cupos(parte: PartSpec, por_nodo: Mapping[str, Sequence[_Candidata]]) -> dict[str, int]:
        """Cuántas preguntas le tocan a cada nodo, proporcional a lo que hay o a sus pesos."""
        if parte.weights:
            pesos = {node_id: float(parte.weights.get(node_id, 0.0)) for node_id in parte.node_ids}
        else:
            pesos = {node_id: float(len(por_nodo.get(node_id, ()))) for node_id in parte.node_ids}
        total = sum(pesos.values())
        if total <= 0:
            return dict.fromkeys(parte.node_ids, 0)
        cupos = {node_id: int(parte.count * peso / total) for node_id, peso in pesos.items()}
        # Lo que el redondeo deja fuera se reparte entre los nodos que sí tienen preguntas, en el
        # orden en que se pidieron: así el total de cupos es el pedido y no uno menos por redondear.
        restante = parte.count - sum(cupos.values())
        ordenados = sorted(
            parte.node_ids,
            key=lambda node_id: (-(parte.count * pesos[node_id] / total - cupos[node_id]), node_id),
        )
        for node_id in ordenados:
            if restante <= 0:
                break
            if len(por_nodo.get(node_id, ())) > cupos[node_id]:
                cupos[node_id] += 1
                restante -= 1
        return cupos

    def _reservas(
        self,
        parte: PartSpec,
        candidatas: Sequence[_Candidata],
        firmas: set[str],
        elegidas: Sequence[_Candidata],
    ) -> tuple[_Candidata, ...]:
        """Las reservas de la parte: las que el banco marca como reserva, en su orden.

        La convocatoria las valora **por su orden** en el caso de que se anule una
        ordinaria, así que
        se numeran al congelarlas. Si el banco tiene menos de las que pide la parte, entran las que
        haya y la composición lo dice: no se inventan reservas de preguntas que no lo son.
        """
        if parte.reserve <= 0:
            return ()
        usadas = {candidata.question.id for candidata in elegidas}
        reservas = [
            candidata
            for candidata in candidatas
            if candidata.question.is_reserve
            and candidata.question.id not in usadas
            and candidata.signature not in firmas
        ]
        reservas.sort(
            key=lambda candidata: (
                candidata.question.reserve_order
                if candidata.question.reserve_order is not None
                else 10**6,
                candidata.question.position,
            )
        )
        return tuple(
            replace(candidata, reserve_order=indice)
            for indice, candidata in enumerate(reservas[: parte.reserve], start=1)
        )

    def _etiquetas_de_conjuntos(self, conjuntos: set[str]) -> list[str]:
        """De qué conjuntos salió la composición, para la etiqueta de la clave que se congeló.

        Un conjunto cuya única clave utilizable es una **derivada** (su plantilla está en borrador o
        en cuarentena) se etiqueta como tal: decir «plantilla vN» de un conjunto del que no se ha
        usado ninguna plantilla sería mentir sobre con qué se corrigió la sesión.
        """
        etiquetas: list[str] = []
        for set_id in sorted(conjuntos):
            conjunto = self._questions.get_set(set_id)
            if conjunto is None:
                continue
            activa = self._clave_activa_o_none(set_id)
            if activa is None:
                etiquetas.append(f"{conjunto.title}: claves derivadas")
                continue
            etiquetas.append(f"{conjunto.title}: plantilla v{activa.version_no}")
        return etiquetas

    def _etiqueta_de_fuentes(self, fuentes: Sequence[SourceInput]) -> str | None:
        """De qué es una sesión montada sobre conjuntos: sus títulos, que es lo que se lee.

        Antes la lista de sesiones solo tenía el identificador del conjunto, así que cinco exámenes
        oficiales distintos se veían como cinco filas iguales (5 de octubre de 2026).
        """
        return self._etiqueta_de_conjuntos([fuente.question_set_id for fuente in fuentes])

    def _etiqueta_de_conjuntos(self, ids: Sequence[str]) -> str | None:
        """El título de los conjuntos de una sesión, en una línea."""
        titulos: list[str] = []
        for identificador in ids:
            conjunto = self._questions.get_set(identificador)
            if conjunto is not None and conjunto.title not in titulos:
                titulos.append(conjunto.title)
        if not titulos:
            return None
        if len(titulos) == 1:
            return titulos[0]
        return f"{titulos[0]} y {len(titulos) - 1} conjunto(s) más"

    def _etiqueta_del_tema(self, node_id: str | None) -> str | None:
        """De qué es una práctica por tema: el código del tema y su título («I.7 · …»)."""
        if node_id is None:
            return None
        nodo = self._profiles.get_node(node_id)
        if nodo is None:
            return None
        titulo = nodo.node.title.strip()
        codigo = (nodo.node.path or "").strip()
        return f"{codigo} · {titulo}" if codigo else titulo

    @staticmethod
    def _nota_del_tema(
        *,
        total: int,
        sin_clave: int,
        no_practicables: int,
        sin_respuesta: int = 0,
        en_cuarentena: int = 0,
        derivadas: int = 0,
    ) -> str:
        """Lo que una práctica por tema deja fuera, dicho: si no, el número no cuadraría."""
        nota = (
            f"Práctica de un tema: {total} pregunta(s) catalogadas en él, sin parte declarada y "
            "corregidas en directo (la parte la fija la convocatoria para un examen)."
        )
        if derivadas:
            nota += (
                f" {derivadas} se corrigen con su **clave derivada** (los apuntes, con su "
                "modelo sin apuntes dicen la misma letra)."
            )
        if en_cuarentena:
            nota += (
                f" {en_cuarentena} se quedaron fuera con la clave en cuarentena (su conjunto "
                "discrepa de los apuntes en más del 30 % de las preguntas medidas)."
            )
        if sin_clave:
            nota += f" {sin_clave} se quedaron fuera por no tener plantilla activa."
        if sin_respuesta:
            nota += (
                f" {sin_respuesta} se quedaron fuera porque la plantilla activa no dice su "
                "respuesta (sin entrada, anulada o en conflicto)."
            )
        if no_practicables:
            nota += f" {no_practicables} no se practican solas (reservas o tipo no soportado)."
        return nota

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
        en_cuarentena = 0
        derivadas = 0
        banco = self._banco()
        for posicion, vencida in enumerate(vencidas, start=1):
            conjunto_vencido = self._questions.get_set(vencida.question_set_id)
            propia = banco.entrada(vencida.question_version_id)
            if propia is None and (
                (conjunto_vencido is not None and conjunto_vencido.key_is_unreliable)
                or banco.sigue_fuera(vencida.question_version_id)
            ):
                # Cuarentena de clave (§1) o motivo de fuera escrito (§1 de F29): el repaso es el
                # tercero de los sitios donde se eligen preguntas. Repreguntar lo que se falló
                # **con una clave que no es de fiar** es la peor forma de este defecto: se falló por
                # la clave, no por no saberlo. Una con clave derivada sí se repasa: su letra
                # tiene dos apoyos independientes.
                en_cuarentena += 1
                continue
            if vencida.part_code is None:
                raise UnsupportedError(
                    f"el repaso de «{vencida.stable_key}» no sabe a qué parte del examen "
                    "pertenece: la sesión en la que se falló no lo registró, así que no se puede "
                    "componer la sesión de repaso"
                )
            parte = self._parte(convocatoria, vencida.part_code)
            contexto[parte.code] = parte
            activa = self._clave_activa_o_none(vencida.question_set_id)
            if propia is not None:
                entrada: KeyEntryView | None = propia
                derivadas += 1
            else:
                if activa is None:
                    # Sin plantilla activa y sin clave derivada no hay con qué corregir: se queda
                    # fuera y se cuenta como si su clave no fuera de fiar (es la verdad: no la hay).
                    en_cuarentena += 1
                    continue
                entrada = next(
                    (
                        candidata
                        for candidata in activa.entries
                        if candidata.question_version_id == vencida.question_version_id
                    ),
                    None,
                )
            if activa is not None:
                claves.add(activa.id)
                etiqueta = f"{parte.name}: plantilla v{activa.version_no}"
            else:
                etiqueta = f"{parte.name}: claves derivadas"
            conjuntos.add(vencida.question_set_id)
            if etiqueta not in etiquetas:
                etiquetas.append(etiqueta)
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

        if not congeladas:
            # Todo lo vencido estaba en cuarentena: una sesión de repaso vacía no es un repaso, y
            # decir «no hay nada vencido» sería mentira (había, y no se puede preguntar).
            raise UnsupportedError(
                f"lo que te toca repasar ({en_cuarentena} pregunta(s)) es de conjuntos con la "
                "clave en cuarentena: no se te puede preguntar por una clave de la que no nos "
                "fiamos. Se arreglará la clave y volverán"
            )

        configuracion = SessionConfiguration(
            mode=request.mode,
            # El repaso corrije al momento: §5 dice que no se enseña la respuesta **antes** del
            # intento, y después sí, que es justo lo que se viene a hacer aquí.
            feedback=request.feedback or Feedback.IMMEDIATE,
            sources=(),
            time_limit_minutes=limite_tiempo,
            shuffle=request.shuffle,
            context_label="Repaso de tus fallos",
            note=(
                None
                if not en_cuarentena
                else f"{en_cuarentena} pregunta(s) de tu cola de repaso se han dejado fuera: su "
                "conjunto tiene la clave en cuarentena"
            ),
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
        hace tiene que poder saber cuánto de lo que acaba de ver ya lo había visto. La ventana se
        nombra con su número de días, no con un «hace poco» que cada uno leería a su manera.
        """
        if repetidas == 0:
            return (
                "simulacro con el perfil exacto del examen: ninguna de sus preguntas se había "
                f"intentado en los últimos {DIAS_VISTA_HACE_POCO} días"
            )
        return (
            f"simulacro con el perfil exacto del examen: {repetidas} de {total} pregunta(s) ya se "
            f"habían intentado en los últimos {DIAS_VISTA_HACE_POCO} días, porque el banco no daba "
            "para más sin repetir"
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
        banco = self._banco()
        conjuntos = self._questions.list_sets(opposition_id=request.opposition_id, limit=200).sets
        con_clave = [
            conjunto
            for conjunto in conjuntos
            if (conjunto.active_key_id is not None and not conjunto.key_is_unreliable)
            or banco.es_derivada(conjunto.id)
        ]
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
            # Solo cuenta lo que se puede corregir: lo que la plantilla activa responde **y** lo que
            # tiene clave derivada (§1 del encargo F29). Una pregunta sin respuesta se corregiría
            # como «excluida» y el diagnóstico mediría menos de lo que dice.
            activa = self._clave_activa_o_none(conjunto.id)
            corregibles = (
                {
                    entrada.question_version_id
                    for entrada in activa.entries
                    if entrada.outcome == KeyOutcome.KEYED.value
                }
                if activa is not None
                else set()
            )
            for pregunta in self._questions.all_questions(conjunto.id):
                if pregunta.question_type not in _SUPPORTED_QUESTION_TYPES or pregunta.is_reserve:
                    continue
                suyos = temas_del_conjunto.get(pregunta.id, ())
                if not suyos:
                    sin_tema += 1
                    continue
                if banco.sigue_fuera(pregunta.id) and banco.letras(pregunta.id) is None:
                    # Su motivo de fuera está escrito: sigue fuera aunque su conjunto entre.
                    continue
                if pregunta.id not in corregibles and banco.letras(pregunta.id) is None:
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
        # que sus preguntas se congelan **sin parte** y se corrigen en directo, sin la penalización
        # que la convocatoria fija para un examen. Inventar a qué parte pertenece cada pregunta
        # sería peor que corregirla sin penalización, y el resultado lo dice (parte nula, directo).
        por_id = {
            pregunta.id: pregunta for preguntas in candidatas.values() for pregunta in preguntas
        }
        titulos_por_conjunto = {conjunto.id: conjunto.title for conjunto in con_clave}
        claves: dict[str, str] = {}
        etiquetas: list[str] = []
        congeladas: list[FrozenQuestion] = []
        for posicion, question_id in enumerate(muestra.question_ids, start=1):
            pregunta = por_id[question_id]
            propia = banco.entrada(pregunta.id)
            activa = self._clave_activa_o_none(pregunta.question_set_id)
            if activa is not None:
                claves[pregunta.question_set_id] = activa.id
            if propia is not None:
                entrada: KeyEntryView | None = propia
            else:
                clave = self._clave_activa(pregunta.question_set_id)
                entrada = next(
                    (
                        candidata
                        for candidata in clave.entries
                        if candidata.question_version_id == pregunta.id
                    ),
                    None,
                )
            # La etiqueta lleva el conjunto: la muestra puede salir de varios, y dos plantillas «v1»
            # de conjuntos distintos no son la misma clave (decir «plantilla v1» a secas mentiría).
            etiqueta = f"{titulos_por_conjunto.get(pregunta.question_set_id, 'conjunto')}: " + (
                f"plantilla v{activa.version_no}" if activa is not None else "claves derivadas"
            )
            if etiqueta not in etiquetas:
                etiquetas.append(etiqueta)
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

        if request.feedback is not None and request.feedback is not Feedback.AT_END:
            raise UnsupportedError(
                "un diagnóstico corrige al terminar: es una muestra para estimar por dónde estás, "
                "y enseñar la respuesta a mitad mejoraría las siguientes preguntas del mismo tema, "
                "que es justo lo que se está midiendo"
            )
        configuracion = SessionConfiguration(
            mode=request.mode,
            # La corrección es **al terminar**, y no por copiar al examen: la muestra mide lo que
            # sabes ahora, y una corrección a mitad contamina el resto (la segunda pregunta del
            # mismo tema ya no sería independiente de la primera).
            feedback=Feedback.AT_END,
            sources=(),
            time_limit_minutes=None,
            shuffle=request.shuffle,
            note=muestra.detail,
            context_label="Diagnóstico por temas",
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
        lectura de una muestra pequeña **no** es la nota de un examen, y presentarla al lado de la
        puntuación de una práctica invitaría a leerla como si lo fuera.

        Los temas se leen del mapeo **aceptado** de cada pregunta al leer, con el mismo criterio con
        el que se compuso la muestra (el primer tema de la pregunta, por ruta). Lo que **no** viaja
        congelado con la sesión es el tema en sí —una pregunta puede pertenecer a varios—, así que
        si alguien reasigna una pregunta a otro tema, la lectura la agrupará donde diga el mapeo
        nuevo. Se dice aquí en lugar de dejar que parezca que el tema se congeló con la sesión.
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
        pagina = self._study.list_sessions(
            opposition_id=opposition_id, status=status, limit=limit, offset=offset
        )
        return replace(pagina, sessions=tuple(self._con_etiqueta(s) for s in pagina.sessions))

    def session(self, session_id: str) -> SessionView:
        return self._con_etiqueta(self._session_or_404(session_id))

    def _con_etiqueta(self, vista: SessionView) -> SessionView:
        """Pone nombre a una sesión creada antes de que se congelara su etiqueta.

        Las sesiones anteriores al 6 de octubre de 2026 no guardaron `context_label`, y la lista
        enseñaba el modo dos veces («examen oficial · examen oficial»). Lo que sí guardaron es de
        qué conjuntos salen sus preguntas: su título es el nombre que se lee.
        """
        if vista.configuration.context_label is not None:
            return vista
        ids = [fuente.question_set_id for fuente in vista.configuration.sources]
        if not ids and vista.question_set_id is not None:
            ids = [vista.question_set_id]
        etiqueta = self._etiqueta_de_conjuntos(ids)
        if etiqueta is None:
            return vista
        return replace(vista, configuration=replace(vista.configuration, context_label=etiqueta))

    def discard_session(self, session_id: str) -> str:
        """Descarta una sesión: borra la que no tiene respuestas y abandona la que las tiene.

        Es lo que hacía falta para no dejar el banco lleno de sesiones «sin empezar» de las pruebas
        (5 de octubre de 2026): cinco filas idénticas en Estudiar y un «Continuar estudiando» que
        apuntaba a una de ellas. Nunca se borra historial con respuestas.
        """
        self._session_or_404(session_id)
        hecho = self._study.discard_session(session_id, now=self._clock.now())
        if hecho is None:  # pragma: no cover - la sesión existe: se acaba de comprobar
            raise NotFoundError("sesión de estudio", session_id)
        return hecho

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

    def runner_view(self, session_id: str, *, position: int | None = None) -> RunnerView:
        """La sesión entera como la necesita la pantalla del test en curso, **sin evidencia**.

        Es la lectura de `current_question` más lo que la hoja de respuestas necesita de todas las
        preguntas (posición, si se contestó, qué se marcó y, cuando se puede enseñar, su
        corrección). No hay una segunda corrección: sale de `_componer`, que es la que ya existe,
        con la evidencia apagada.

        Con `position` se sirve **esa fila** de la hoja en lugar de la primera sin contestar: es lo
        que necesita la pantalla para volver a una pregunta ya contestada, que es el defecto 5 del
        recorrido (§3.2 del encargo F36). Sin `position` el comportamiento es el de siempre.
        """
        session = self._session_or_404(session_id)
        preguntas = self._study.session_questions(session_id)
        intentos = self._indice_intentos(session_id)
        vistas = self._componer(session, preguntas, intentos, with_evidence=False)
        vista = RunnerView(
            session=session,
            current=next((vista for vista in vistas if not vista.answered), None),
            questions=vistas,
            answered=sum(1 for vista in vistas if vista.answered),
            total=len(vistas),
            pending=sum(1 for vista in vistas if not vista.answered),
            finished=session.status is SessionStatus.FINISHED,
        )
        if position is None:
            return vista
        elegida = next((vista for vista in vistas if vista.position == position), None)
        if elegida is None:
            raise NotFoundError("pregunta del test", str(position))
        return replace(vista, current=elegida)

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
        """Registra una respuesta, la corrige con la clave congelada y dice qué se puede enseñar.

        Es **una sola máquina de estados** para el ciclo de contestar (§3.2 del encargo F36), y sus
        tres reglas son estas:

        1. **se contesta y se vuelve a contestar mientras la sesión está en marcha**. Cambiar de
        opción
           no es un error: se reescribe el intento, se rehace la corrección y el cambio queda en la
           auditoría. Antes devolvía un 409 («esa pregunta ya está respondida y el intento no se
           reescribe») y desde la pantalla el alumno pulsaba otra opción y no cambiaba nada;
        2. **reenviar lo mismo es idempotente**: se devuelve el intento que ya había, sin escribir
        nada.
           Es lo que hace que recargar y volver a enviar —o pulsar dos veces deprisa— no reviente;
        3. **un test terminado tiene las respuestas congeladas**: el intento no se reescribe y se
        dice
           con su código (`attempt_frozen`). El alumno ya vio la corrección y la nota está
           calculada.
        """
        session = self._session_or_404(session_id)
        estado = self._state(session)

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
            sin_cambios = tuple(existente.chosen_option_keys) == tuple(entrada.chosen_option_keys)
            if sin_cambios:
                # Nada que escribir: se contesta con lo que ya hay. La sesión tiene que estar en
                # marcha igualmente —un test cerrado no admite respuestas—, así que la comprobación
                # se hace aquí y no antes: así el reenvío tampoco se salta la máquina de estados.
                assert_can_answer(estado)
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
            if estado.status is not SessionStatus.RUNNING:
                raise AttemptFrozenError(
                    "el test ya no está en marcha: la respuesta que diste queda congelada y no se "
                    "reescribe; vuelve a montarlo para practicar esa pregunta otra vez"
                )
            return self._reescribir(session, pregunta, existente, entrada)

        assert_can_answer(estado)
        ahora = self._clock.now()
        intento, creado = self._study.save_attempt(
            session_question_id=pregunta.session_question_id,
            chosen_option_keys=entrada.chosen_option_keys,
            elapsed_ms=entrada.elapsed_ms,
            confidence=entrada.confidence,
            client_sequence=entrada.client_sequence,
            now=ahora,
        )
        if not creado:
            # Otra petición escribió el intento entre la lectura de arriba y esta escritura (el caso
            # de pulsar dos veces deprisa). No se ha escrito nada nuevo: se devuelve lo que hay.
            return AnswerOutcomeView(
                saved=False,
                already_answered=True,
                attempt=intento,
                session=session,
                question=self._componer(
                    session, [pregunta], {pregunta.question_version_id: intento}
                )[0],
                correction=self._correccion(session, pregunta, intento),
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

    def _reescribir(
        self,
        session: SessionView,
        pregunta: SessionQuestionView,
        existente: AttemptView,
        entrada: AnswerInput,
    ) -> AnswerOutcomeView:
        """Cambia la opción marcada de una pregunta y rehace su corrección (§3.2 del encargo)."""
        ahora = self._clock.now()
        intento = self._study.rewrite_attempt(
            attempt_id=existente.id,
            chosen_option_keys=entrada.chosen_option_keys,
            elapsed_ms=entrada.elapsed_ms,
            confidence=entrada.confidence,
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
            replace_existing=True,
        )
        # El repaso se vuelve a registrar con el desenlace nuevo: un fallo que pasa a acierto no
        # puede
        # quedarse en la cola de repaso, y al revés tampoco.
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
        activa = self._clave_activa_o_none(set_id)
        if activa is None:
            raise ClassificationConflictError(
                "el conjunto no tiene ninguna clave activa: activar una plantilla es lo que decide "
                "con qué se corrige el examen"
            )
        return activa

    def _clave_activa_o_none(self, set_id: str) -> AnswerKeyView | None:
        """La clave activa del conjunto, o `None` si no tiene ninguna.

        `_clave_activa` **revienta** cuando no la hay y eso es lo correcto donde la plantilla es
        obligatoria. Aquí no: un conjunto cuya clave está en cuarentena puede no tener plantilla
        activa —sus claves están en borrador— y aun así tener preguntas con **clave derivada** (§1
        del encargo F29). Esas preguntas se corrigen con su clave derivada y sin plantilla.
        """
        return next(
            (clave for clave in self._questions.list_keys(set_id) if clave.status == "active"), None
        )

    def _banco(self) -> _ClavesDelBanco:
        """Lo que la derivación cambió en el banco: **se lee una vez por operación**.

        Pregunta a pregunta serían miles de consultas en una composición de un tema con 600
        preguntas; las dos tablas son pequeñas por construcción (las derivadas son las de cita
        verificada y coinciden con el modelo; los motivos de fuera, las de los conjuntos en
        cuarentena).
        """
        return _ClavesDelBanco(
            derivadas=self._questions.derived_keys(),
            fuera=self._questions.questions_without_reliable_key(),
            conjuntos=self._questions.sets_with_derived_keys(),
        )

    def _correccion_de(
        self,
        conjunto: QuestionSetView,
        preguntas: Sequence[QuestionView],
        banco: _ClavesDelBanco,
    ) -> _Correccion:
        """Con qué se corrige cada pregunta: la plantilla del conjunto **con las derivadas encima**.

        Es el único sitio donde se junta lo uno con lo otro, y por eso está aquí y no repartido por
        los cinco sitios que eligen preguntas. Una pregunta con clave derivada se corrige **con su
        letra**, tenga o no plantilla activa su conjunto; las demás, con la plantilla de siempre.
        """
        activa = self._clave_activa_o_none(conjunto.id)
        entradas: dict[str, KeyEntryView] = (
            {entrada.question_version_id: entrada for entrada in activa.entries}
            if activa is not None
            else {}
        )
        derivadas = 0
        for pregunta in preguntas:
            propia = banco.entrada(pregunta.id)
            if propia is not None:
                entradas[pregunta.id] = propia
                derivadas += 1
        if activa is not None:
            etiqueta = f"plantilla v{activa.version_no}"
            identificador: str | None = activa.id
        else:
            # Sin plantilla activa, lo único que corrige son las claves derivadas. `None` y no un
            # identificador inventado: la sesión no se corrige con una plantilla y no puede decir
            # sí (la clave del conjunto es una clave foránea, y una inventada no existe).
            if not entradas:
                # Ni plantilla ni una sola clave derivada: esta sesión no se podría corregir, y
                # montarla sería enseñar preguntas que no cuentan. Se dice lo mismo que decía
                # `_clave_activa`, que es el error que el contrato de la sesión ya publica.
                raise ClassificationConflictError(
                    "el conjunto no tiene ninguna clave activa: activar una plantilla es lo que "
                    "decide con qué se corrige el examen"
                )
            etiqueta = "claves derivadas"
            identificador = None
        if derivadas:
            etiqueta += f" + {derivadas} derivada(s)"
        return _Correccion(key_id=identificador, label=etiqueta, entradas=entradas)

    def _preguntas(
        self,
        fuente: SourceInput,
        parte: _PartContext,
        modo: SessionMode,
        *,
        banco: _ClavesDelBanco,
        recently_seen: frozenset[str] = frozenset(),
    ) -> tuple[QuestionView, ...]:
        """Las preguntas de una fuente: ordinarias primero y reservas después, sin inventar.

        En un **simulacro** el banco se ordena antes de elegir: primero las preguntas que no se han
        visto hace poco y después las demás, para que las que entran sean las frescas (DEBT-012). El
        examen oficial **no** reordena: se presenta en el orden de su publicación.

        **Fuera del temario no entra en un examen** (F4): la normativa y la organización propias de
        otra administración no caen en el examen de TAI, y un simulacro que las metiera mediría
        otra cosa. En un test por tema y en los apuntes sí cuentan —son material para estudiar—, y
        por eso el filtro vive aquí y no en el recuento de preguntas.

        **Y la cuarentena ya no corta el conjunto entero** (§1 de F29): corta lo que no tiene
        clave de la que fiarse. Sus preguntas con **clave derivada** entran con su letra, y las que
        tienen el motivo de fuera escrito quedan fuera. Un conjunto en cuarentena sin ninguna
        derivada se corta entero, con su motivo y con sus dos números, como antes.
        """
        conjunto = self._questions.get_set(fuente.question_set_id)
        if conjunto is None:
            raise NotFoundError("conjunto de preguntas", fuente.question_set_id)
        todas = self._questions.all_questions(fuente.question_set_id)
        validas = [
            pregunta for pregunta in todas if pregunta.question_type in _SUPPORTED_QUESTION_TYPES
        ]
        if conjunto.key_is_unreliable or any(banco.sigue_fuera(p.id) for p in validas):
            # La cuarentena de clave (§1) o un motivo de fuera escrito (§1 de F29) dejan la pregunta
            # sin clave de la que fiarse: el alumno aprendería respuestas equivocadas. `_preguntas`
            # es el embudo de práctica por conjuntos, examen oficial y simulacro, así que se corta
            # aquí —pregunta a pregunta, no el conjunto entero— y se dice por qué con los números
            # delante, en lugar de montar una sesión con material en cuarentena.
            admitidas = [
                pregunta
                for pregunta in validas
                if banco.letras(pregunta.id) is not None
                or (not conjunto.key_is_unreliable and not banco.sigue_fuera(pregunta.id))
            ]
            if not admitidas:
                raise UnsupportedError(
                    f"la clave de «{conjunto.title}» está en cuarentena "
                    f"({conjunto.key_discrepant_count} de {conjunto.key_checked_count} preguntas "
                    f"medidas no coinciden con sus apuntes) y ninguna de sus {len(validas)} "
                    "pregunta(s) tiene clave derivada: sus preguntas no entran en tests, "
                    "simulacros ni repasos hasta que se arregle la clave"
                )
            validas = admitidas
        if modo in (SessionMode.OFFICIAL_EXAM, SessionMode.MOCK_EXAM):
            fuera_del_temario = self._questions.excluded_question_ids(fuente.question_set_id)
            validas = [pregunta for pregunta in validas if pregunta.id not in fuera_del_temario]
        ordinarias = [pregunta for pregunta in validas if not pregunta.is_reserve]
        reservas = [pregunta for pregunta in validas if pregunta.is_reserve]

        if modo is SessionMode.MOCK_EXAM and recently_seen:
            por_id = {pregunta.id: pregunta for pregunta in ordinarias}
            frescas, vistas = order_for_mock(
                [pregunta.id for pregunta in ordinarias], recently_seen=recently_seen
            )
            ordinarias = [por_id[identificador] for identificador in (*frescas, *vistas)]

        if modo in (SessionMode.OFFICIAL_EXAM, SessionMode.MOCK_EXAM):
            # El nombre del modo entra en los mensajes: decirle «examen oficial» a quien pidió un
            # simulacro es confundir dos cosas que la aplicación distingue a propósito.
            cual = "el examen oficial" if modo is SessionMode.OFFICIAL_EXAM else "el simulacro"
            if parte.ordinary_items is None:
                raise UnsupportedError(
                    f"la convocatoria no dice cuántas preguntas tiene la parte «{parte.code}»: "
                    f"sin ese dato no se puede montar {cual}"
                )
            if len(ordinarias) < parte.ordinary_items:
                raise UnsupportedError(
                    f"el conjunto «{conjunto.title}» tiene {len(ordinarias)} preguntas y la parte "
                    f"«{parte.code}» pide {parte.ordinary_items}: faltan preguntas para {cual}"
                )
            elegidas = ordinarias[: parte.ordinary_items]
            necesarias = parte.reserve_items or 0
            if len(reservas) < necesarias:
                raise UnsupportedError(
                    f"la parte «{parte.code}» pide {necesarias} reservas y el conjunto tiene "
                    f"{len(reservas)}: faltan reservas para {cual}"
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
        *,
        with_evidence: bool = True,
    ) -> tuple[SessionQuestionView, ...]:
        """Junta composición, intentos y correcciones: es lo que se enseña de una sesión.

        `with_evidence=False` deja fuera la evidencia documental: la zona del alumno no la tiene y
        pedirla sería trabajo de la base para tirarlo después (y una fuga que no debe existir ni en
        el camino). El panel sí la pide, porque el propietario revisa contra el material.
        """
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
                        self._correccion(session, pregunta, intento, with_evidence=with_evidence)
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
        *,
        with_evidence: bool = True,
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
            evidence=(
                self._questions.question_evidence(pregunta.question_version_id)
                if with_evidence
                else ()
            ),
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
            elif (
                regla.kind is ScoringKind.DIRECT
                and regla.ordinary_items is not None
                and regla.score_max is not None
                and presentadas >= regla.ordinary_items
            ):
                # El cuestionario **completo** de una parte que publica su banda (TAI: 80 preguntas
                # y 50 de máximo): la puntuación directa se puede escalar a esa banda, y esa es la
                # «nota estimada» por parte del simulacro. La penalización es la publicada, así que
                # no hace falta inventar el número de alternativas (`options_per_question` sigue
                # nulo en el perfil). Con la parte **incompleta** —una práctica de 20 de 80— no se
                # escala: se muestra la directa, porque escalar una muestra sería inventar una nota.
                regla = replace(regla, kind=ScoringKind.ESTIMATED)
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
