"""Sesiones de estudio, intentos y puntuación directa (03_DATA-MODEL §7 y 06_QUESTIONS §5-§7).

Tres reglas gobiernan todo lo de aquí, y las tres vienen de un criterio de aceptación del slice:

1. **El intento conserva lo que se presentó** (invariante 6): la composición, la versión de cada
   pregunta y la clave con la que se corrige se **congelan** al iniciar. Activar después una clave
   nueva no reescribe lo pasado: crea una evaluación nueva (invariante 7), y eso es S08.
2. **La aritmética es exacta o no es**: la penalización de un tercio no se representa en coma
   flotante. Aquí se calcula con `Fraction` y se guarda como numerador y denominador; el decimal
   solo se usa para enseñarlo (DEBT-006, ADR-010).
3. **La aplicación calcula la puntuación directa, no la oficial**: la convocatoria transforma la
   puntuación directa con unos baremos que publica la Comisión, y hasta que ese criterio no esté
   importado la calificación oficial 0-50 **no está disponible** y se dice, en lugar de inventarla.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal
from enum import StrEnum
from fractions import Fraction

from opofuente.domain.errors import InvariantViolationError, SessionStateError

# --- vocabularios (los mismos que la migración 0016) --------------------------------------------


class SessionMode(StrEnum):
    """Modos de sesión de 06_QUESTIONS §5, los cinco que la spec define y el producto ofrece.

    S07 implementó `practice` y `official_exam`; S10 añadió `error_review`, que compone la sesión
    con
    lo que la cola de repaso tiene vencido; y `mock_exam` y `diagnostic` llegaron al cerrar la deuda
    DEBT-012: el simulacro monta el perfil exacto del examen (sin llamarse oficial y evitando lo
    visto
    hace poco) y el diagnóstico compone una muestra pequeña estratificada por tema y la lee con su
    intervalo (`domain/diagnostic.py`).
    """

    PRACTICE = "practice"
    ERROR_REVIEW = "error_review"
    OFFICIAL_EXAM = "official_exam"
    MOCK_EXAM = "mock_exam"
    DIAGNOSTIC = "diagnostic"


#: Modos que este slice sabe construir y corregir de verdad.
SUPPORTED_MODES: tuple[SessionMode, ...] = (
    SessionMode.PRACTICE,
    SessionMode.ERROR_REVIEW,
    SessionMode.OFFICIAL_EXAM,
    SessionMode.MOCK_EXAM,
    SessionMode.DIAGNOSTIC,
)


class SessionStatus(StrEnum):
    """`draft` es una sesión creada y sin congelar; `running`, ya iniciada y cronometrada."""

    DRAFT = "draft"
    RUNNING = "running"
    FINISHED = "finished"
    ABANDONED = "abandoned"


class Feedback(StrEnum):
    """Cuándo se puede ver la corrección: es lo que impide filtrar la solución."""

    IMMEDIATE = "immediate"
    AT_END = "at_end"


class Confidence(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ScoringKind(StrEnum):
    """Cómo se corrige una parte, según lo que publica su convocatoria.

    No es una preferencia de la aplicación: TAI publica la penalización de un tercio y deja la
    calificación a unos baremos que fija la Comisión; Guardia Civil publica la fórmula completa
    `Px = (Y/T)·(A - E/(N-1))`; y sus pruebas de ortografía y gramática se evalúan como apto o no
    apto por número de errores. Las tres formas se corrigen aquí tal como están publicadas.
    """

    DIRECT = "direct"
    SCALED = "scaled"
    #: La parte se evalúa como apto o no apto por número de errores. El valor del vocabulario es el
    #: que se guarda y se sirve; no hay ninguna credencial aquí (`S105` lo lee por el nombre).
    PASS_FAIL = "pass_fail"  # noqa: S105

    @property
    def numeric(self) -> bool:
        """¿Da esta forma de corregir una puntuación numérica que se suma al total?"""
        return self in (ScoringKind.DIRECT, ScoringKind.SCALED)


class AttemptOutcome(StrEnum):
    """Qué ha pasado con un intento, con el vocabulario de la clave.

    `annulled`, `excluded` y `conflicting` **no** son fallos: son preguntas que no se corrigen (la
    clave las anuló, no hay entrada para ellas o dos claves se contradicen) y por eso quedan fuera
    del cálculo con su motivo, en lugar de contarse como erróneas.
    """

    CORRECT = "correct"
    WRONG = "wrong"
    BLANK = "blank"
    ANNULLED = "annulled"
    EXCLUDED = "excluded"
    CONFLICTING = "conflicting"
    UNUSED_RESERVE = "unused_reserve"

    @property
    def counts_in_score(self) -> bool:
        """¿Esta pregunta entra en la puntuación? Las cuatro últimas no, y se informan aparte."""
        return self in (AttemptOutcome.CORRECT, AttemptOutcome.WRONG, AttemptOutcome.BLANK)


# --- aritmética exacta (DEBT-006 / ADR-010) ------------------------------------------------------

#: Tolerancia con la que un decimal almacenado se acepta como la fracción publicada: media unidad de
#: su última cifra. La convocatoria dice «un tercio» y en la base hay `0.3333333333`, que difiere de
#: `1/3` en 3,3·10⁻¹¹.
TOLERANCIA_FRACCION = Fraction(1, 2 * 10**10)

#: Denominador máximo que se admite al recuperar la fracción exacta de un decimal almacenado. Una
#: penalización publicada es siempre una fracción sencilla (1/2, 1/3, 1/4, 2/3…): si el decimal
#: guardado no corresponde a ninguna de ellas, el cálculo se detiene en lugar de inventar una
#: aproximación que nadie ha publicado.
MAX_DENOMINADOR = 100


def exact_fraction(stored: float) -> Fraction:
    """Fracción exacta que representa un decimal almacenado.

    El `float` de la base es **información** (qué dice la convocatoria), no autoridad de cálculo: se
    lee su valor decimal tal cual está escrito y se busca la fracción más simple que coincide con él
    dentro de `TOLERANCIA_FRACCION`. Así `0.3333333333` es `1/3` y tres errores descuentan
    exactamente un punto, sin residuo binario.

    Si el decimal no corresponde a ninguna fracción sencilla, esto **falla** en lugar de inventar
    una aproximación: una penalización que nadie ha publicado no se puede aplicar en silencio.
    """
    if stored < 0:
        raise InvariantViolationError(f"una penalización no puede ser negativa: {stored!r}")
    aproximada = Fraction(str(stored))
    simple = aproximada.limit_denominator(MAX_DENOMINADOR)
    if abs(simple - aproximada) > TOLERANCIA_FRACCION:
        raise InvariantViolationError(
            f"la penalización almacenada {stored!r} no corresponde a ninguna fracción sencilla "
            f"(denominador ≤ {MAX_DENOMINADOR})"
        )
    return simple


def exact_score(correct: int, wrong: int, penalty: Fraction) -> Fraction:
    """Puntuación directa: cada acierto vale uno y cada error descuenta la penalización.

    Las preguntas en blanco valen cero (regla `blank_answer_penalty` de la convocatoria) y las que
    no se corrigen ni suman ni restan: quien decide qué entra es `AttemptOutcome.counts_in_score`.
    """
    if penalty < 0:
        raise InvariantViolationError("la penalización no puede ser negativa")
    return Fraction(correct) - Fraction(wrong) * penalty


def decimal_text(valor: Fraction, *, decimales: int = 4) -> str:
    """Representación decimal de una puntuación exacta, para enseñarla.

    Se redondea **solo aquí**, al mostrarla, con `ROUND_HALF_UP` (la regla que espera cualquiera que
    lea una nota) y sin recortar ceros: `0,6667` en lugar de `0,66666…`. El valor exacto viaja
    aparte como numerador y denominador, así que redondear no pierde nada.
    """
    exponente = Decimal(1).scaleb(-decimales)
    exacto = Decimal(valor.numerator) / Decimal(valor.denominator)
    return str(exacto.quantize(exponente, rounding=ROUND_HALF_UP))


# --- composición congelada ------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class SessionSource:
    """De dónde salen las preguntas de la sesión y qué parte del examen representan.

    `part_code` es la declaración de la persona (o del perfil, en un examen oficial): la pregunta no
    sabe a qué parte pertenece todavía (DEBT-010), así que la sesión lo dice y lo congela, en lugar
    de deducirlo de un número que nadie ha guardado.
    """

    question_set_id: str
    part_code: str | None = None
    count: int | None = None
    include_reserves: bool = True


@dataclass(frozen=True, slots=True)
class FrozenQuestion:
    """Una pregunta tal como se presentó: su versión, su parte, su reserva y la clave congelada."""

    question_version_id: str
    stable_key: str
    position: int
    part_code: str | None
    is_reserve: bool
    reserve_order: int | None
    key_outcome: str | None
    correct_option_keys: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class SessionConfiguration:
    """Configuración congelada al iniciar (03_DATA-MODEL §7)."""

    mode: SessionMode
    feedback: Feedback
    sources: tuple[SessionSource, ...]
    time_limit_minutes: int | None = None
    shuffle: bool = False
    #: Lo que la composición quiere decir de sí misma y no cabe en ningún otro campo: cuántas
    #: preguntas del simulacro se habían visto hace poco, de qué temas salió la muestra del
    #: diagnóstico. Se guarda con la sesión porque se congela con ella: la explicación de una
    #: composición no puede cambiar después (DEBT-012).
    note: str | None = None
    #: De qué es esta sesión, en palabras: «TAI libre 2025 · modelo A», «I.7 · Protección de datos»,
    #: «Repaso de tus fallos». Se congela con la sesión porque la lista tiene que poder decir de
    #: qué es cada una sin adivinar: antes solo llevaba el identificador del conjunto y la etiqueta
    #: de la clave (que llega a listar 21 plantillas), así que cinco sesiones de examen oficial se
    #: veían como cinco filas idénticas (5 de octubre de 2026).
    context_label: str | None = None

    def __post_init__(self) -> None:
        if self.mode in (SessionMode.OFFICIAL_EXAM, SessionMode.MOCK_EXAM) and (
            self.feedback is not Feedback.AT_END
        ):
            raise InvariantViolationError(
                "un examen no puede dar la corrección antes de terminar: se filtraría la solución"
            )
        if self.mode is SessionMode.OFFICIAL_EXAM and self.shuffle:
            raise InvariantViolationError(
                "un examen oficial se presenta en el orden de su publicación, no barajado"
            )


@dataclass(frozen=True, slots=True)
class SessionPlan:
    """La composición efectiva de una sesión, con las reservas ya repartidas.

    Se calcula antes de guardar nada: si no hay preguntas suficientes o falta la clave, la sesión no
    se crea y se dice por qué.
    """

    questions: tuple[FrozenQuestion, ...]

    @property
    def ordinary(self) -> tuple[FrozenQuestion, ...]:
        return tuple(pregunta for pregunta in self.questions if not pregunta.is_reserve)

    @property
    def reserves(self) -> tuple[FrozenQuestion, ...]:
        return tuple(pregunta for pregunta in self.questions if pregunta.is_reserve)


def assign_positions(
    questions: Sequence[FrozenQuestion], *, shuffle: bool
) -> tuple[FrozenQuestion, ...]:
    """Numera las preguntas en el orden en que se van a presentar.

    En un examen oficial el orden es el de la publicación; en práctica se puede barajar, y cuando se
    baraja se dice: el orden queda congelado en la sesión, no se recalcula en cada lectura.
    """
    ordenadas = list(questions)
    if shuffle:
        # Barajado determinista por clave estable: la misma sesión conserva su orden entre lecturas
        # y reintentos, sin depender de `random` ni de la hora.
        ordenadas.sort(key=lambda pregunta: (pregunta.stable_key, pregunta.question_version_id))
    return tuple(
        FrozenQuestion(
            question_version_id=pregunta.question_version_id,
            stable_key=pregunta.stable_key,
            position=indice,
            part_code=pregunta.part_code,
            is_reserve=pregunta.is_reserve,
            reserve_order=pregunta.reserve_order,
            key_outcome=pregunta.key_outcome,
            correct_option_keys=pregunta.correct_option_keys,
        )
        for indice, pregunta in enumerate(ordenadas, start=1)
    )


def reserves_in_order(questions: Sequence[FrozenQuestion]) -> tuple[FrozenQuestion, ...]:
    """Reservas ordenadas por su orden declarado y, si no lo tienen, por su posición."""
    return tuple(
        sorted(
            (pregunta for pregunta in questions if pregunta.is_reserve),
            key=lambda pregunta: (
                pregunta.reserve_order if pregunta.reserve_order is not None else 10**6,
                pregunta.position,
            ),
        )
    )


# --- corrección -----------------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Answer:
    """Lo que hizo una persona: qué marcó, cuánto tardó y con qué confianza."""

    chosen_option_keys: tuple[str, ...]
    elapsed_ms: int
    confidence: Confidence | None = None
    client_sequence: int | None = None


@dataclass(frozen=True, slots=True)
class GradedAttempt:
    """Un intento corregido: su desenlace y su puntuación **exacta**.

    `score` es una fracción, no un decimal: un tercio de punto no se pierde por el camino. El
    decimal, cuando se enseña, se calcula a partir de ella.
    """

    outcome: AttemptOutcome
    score: Fraction
    reason: str | None = None

    @property
    def counts_in_score(self) -> bool:
        return self.outcome.counts_in_score


def grade_attempt(
    *,
    chosen_option_keys: Sequence[str],
    frozen_outcome: str | None,
    frozen_correct_keys: Sequence[str],
    penalty: Fraction,
) -> GradedAttempt:
    """Corrige un intento con la clave **congelada** de la sesión.

    Lo que decide el desenlace es el estado de la clave en el momento de congelar, no el de ahora:
    activar una plantilla nueva más tarde crea una evaluación nueva (S08), no cambia esta.

    - `keyed`: acierto si marcó exactamente las opciones correctas; error si marcó otra cosa; en
      blanco si no marcó nada;
    - `annulled` y `unanswered`: la pregunta no se corrige y **no penaliza**; se informa con su
      motivo;
    - `conflicting`: dos claves se contradicen, así que la aplicación no elige: queda fuera del
      cálculo hasta que alguien lo decida.
    """
    marcadas = tuple(clave.strip().lower() for clave in chosen_option_keys if clave.strip() != "")

    if frozen_outcome is None or frozen_outcome == "unanswered":
        return GradedAttempt(
            AttemptOutcome.EXCLUDED,
            Fraction(0),
            "la clave no tiene entrada para esta pregunta",
        )
    if frozen_outcome == "annulled":
        return GradedAttempt(AttemptOutcome.ANNULLED, Fraction(0), "la clave anuló la pregunta")
    if frozen_outcome == "conflicting":
        return GradedAttempt(
            AttemptOutcome.CONFLICTING,
            Fraction(0),
            "dos claves se contradicen: no se corrige hasta decidir cuál vale",
        )
    if frozen_outcome != "keyed":
        raise InvariantViolationError(f"desenlace de clave desconocido: {frozen_outcome!r}")

    correctas = tuple(clave.strip().lower() for clave in frozen_correct_keys)
    if not correctas:
        return GradedAttempt(
            AttemptOutcome.EXCLUDED,
            Fraction(0),
            "la clave dice que la pregunta tiene respuesta, pero no cuál",
        )
    if not marcadas:
        return GradedAttempt(AttemptOutcome.BLANK, Fraction(0))
    if set(marcadas) == set(correctas):
        return GradedAttempt(AttemptOutcome.CORRECT, Fraction(1))
    return GradedAttempt(AttemptOutcome.WRONG, -penalty)


# --- resultado ------------------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Substitution:
    """Una pregunta anulada y la reserva que la sustituye (06_QUESTIONS §7).

    Si no queda reserva, `reserve` es `None` y la pregunta se queda fuera del cálculo: el número de
    preguntas que cuentan baja, y eso se ve en el resultado en lugar de taparse.
    """

    annulled_question_version_id: str
    reserve_question_version_id: str | None


@dataclass(frozen=True, slots=True)
class EffectiveItem:
    """Una pregunta con el intento que la corrige (o `None` si no se respondió)."""

    question: FrozenQuestion
    attempt: GradedAttempt | None


@dataclass(frozen=True, slots=True)
class PartScore:
    """Puntuación directa de una parte, con lo que hace falta para leerla sin engañarse.

    `score_max` y `pass_score` son de la **calificación oficial** (0-50), no de la puntuación
    directa: por eso viajan como umbral declarado y `official_available` dice si se pueden aplicar.
    Comparar una puntuación directa con el mínimo oficial sería inventar un aprobado.
    """

    part_code: str | None
    part_name: str | None
    ordinary_items: int | None
    score_min: float | None
    score_max: float | None
    pass_score: float | None
    #: La penalización de la parte. Es `None` en las partes que no se puntúan con penalización
    #: (apto/no apto) y en el total cuando las partes no comparten una.
    penalty: Fraction | None
    #: Cómo se corrigió esta parte: directa, escalada con la fórmula publicada o apto/no apto.
    kind: ScoringKind
    correct: int
    wrong: int
    blank: int
    annulled: int
    excluded: int
    conflicting: int
    reserves_used: int
    unused_reserves: int
    score: Fraction
    #: Veredicto publicado: `True`/`False` si la convocatoria lo dice, `None` si no se puede.
    passed: bool | None = None
    verdict_note: str | None = None
    official_available: bool = False

    @property
    def score_decimal(self) -> str:
        return decimal_text(self.score)

    @property
    def graded(self) -> int:
        return self.correct + self.wrong + self.blank


@dataclass(frozen=True, slots=True)
class SessionResult:
    """Resultado agregado de una sesión, con la composición efectiva del cálculo (§7 de 06)."""

    session_id: str
    mode: SessionMode
    answer_key_version_id: str | None
    parts: tuple[PartScore, ...]
    total: PartScore
    substitutions: tuple[Substitution, ...]
    unfinished: int
    official_available: bool
    official_note: str | None

    @property
    def score_decimal(self) -> str:
        return decimal_text(self.total.score)


def effective_composition(
    questions: Sequence[FrozenQuestion],
    attempts: Mapping[str, GradedAttempt | None],
) -> tuple[tuple[EffectiveItem, ...], tuple[Substitution, ...]]:
    """Aplica la sustitución de reservas y devuelve la composición efectiva del cálculo.

    La convocatoria dice que las reservas «serán valoradas, por su orden, en el caso de que se anule
    alguna» de las ordinarias. Eso se traduce aquí en tres cosas, y ninguna se improvisa:

    1. una ordinaria **anulada por la clave** se sustituye por la primera reserva no usada;
    2. una reserva que se contestó pero no hizo falta **no entra** en la puntuación (se informa como
       reserva sin usar, porque contarla inflaría el resultado);
    3. si se anulan más ordinarias que reservas hay, las que sobran quedan fuera y el número de
       preguntas que cuentan baja: la puntuación directa no cambia por eso, pero el resultado lo
       dice.
    """
    ordinarias = [pregunta for pregunta in questions if not pregunta.is_reserve]
    reservas = list(reserves_in_order(questions))

    anuladas = [
        pregunta
        for pregunta in ordinarias
        if (intento := attempts.get(pregunta.question_version_id)) is not None
        and intento.outcome is AttemptOutcome.ANNULLED
    ]

    sustituciones: list[Substitution] = []
    usadas: set[str] = set()
    for anulada in anuladas:
        reserva = reservas.pop(0) if reservas else None
        if reserva is not None:
            usadas.add(reserva.question_version_id)
        sustituciones.append(
            Substitution(
                annulled_question_version_id=anulada.question_version_id,
                reserve_question_version_id=(
                    reserva.question_version_id if reserva is not None else None
                ),
            )
        )

    efectivas: list[EffectiveItem] = []
    for pregunta in ordinarias:
        intento = attempts.get(pregunta.question_version_id)
        if intento is not None and intento.outcome is AttemptOutcome.ANNULLED:
            continue
        efectivas.append(EffectiveItem(pregunta, intento))

    for pregunta in reserves_in_order(questions):
        intento = attempts.get(pregunta.question_version_id)
        if pregunta.question_version_id in usadas:
            efectivas.append(EffectiveItem(pregunta, intento))
            continue
        # Contestada o no, una reserva que no sustituye a nadie no entra en el cálculo.
        efectivas.append(
            EffectiveItem(
                pregunta,
                GradedAttempt(
                    AttemptOutcome.UNUSED_RESERVE,
                    Fraction(0),
                    "reserva no usada: no se anuló ninguna pregunta ordinaria",
                ),
            )
        )

    # Las anuladas que no se pudieron sustituir se informan igual, fuera del cálculo.
    for anulada in anuladas:
        if not any(
            sustitucion.annulled_question_version_id == anulada.question_version_id
            and sustitucion.reserve_question_version_id is not None
            for sustitucion in sustituciones
        ):
            efectivas.append(
                EffectiveItem(
                    anulada,
                    GradedAttempt(
                        AttemptOutcome.ANNULLED,
                        Fraction(0),
                        "anulada sin reserva disponible: queda fuera del cálculo",
                    ),
                )
            )

    return tuple(efectivas), tuple(sustituciones)


@dataclass(frozen=True, slots=True)
class PartRule:
    """Lo que la convocatoria dice de una parte: cómo se corrige, su tamaño y sus umbrales.

    `kind` decide la corrección, y las tres formas son las que publican las dos convocatorias:

    - `direct`: la convocatoria publica la penalización pero **no** la transformación a la escala
      oficial (TAI: se calcula `A - E·p` y la calificación 0-50 queda declarada como no disponible);
    - `scaled`: la convocatoria publica la fórmula completa `Px = (Y/T)·(A - E/(N-1))` (Guardia
      Civil), así que la puntuación de la prueba **es** la publicada y su umbral se puede aplicar;
    - `pass_fail`: la parte se evalúa como apto o no apto por el número de errores (ortografía y
      gramática), sin puntuación numérica.

    `penalty` viaja con la parte porque dos partes del mismo examen pueden penalizar distinto;
    `score_max` es la `Y` de la fórmula, `ordinary_items` la `T` y `options_per_question` la `N`.
    """

    code: str | None
    name: str | None = None
    ordinary_items: int | None = None
    score_min: float | None = None
    score_max: float | None = None
    pass_score: float | None = None
    penalty: Fraction = Fraction(0)
    kind: ScoringKind = ScoringKind.DIRECT
    options_per_question: int | None = None
    fail_if_errors_gte: int | None = None
    format: str | None = None
    #: Nota de la parte que explica cómo se corrigió aquí (por ejemplo, una práctica parcial de una
    #: prueba cuya fórmula se aplica al cuestionario completo).
    note: str | None = None

    def __post_init__(self) -> None:
        if self.kind is ScoringKind.SCALED:
            if self.score_max is None or not self.ordinary_items:
                raise InvariantViolationError(
                    f"la parte «{self.code}» se puntúa con la fórmula publicada y necesita su "
                    "puntuación máxima y su número de preguntas"
                )
            if self.options_per_question is None or self.options_per_question < 2:
                raise InvariantViolationError(
                    f"la parte «{self.code}» necesita el número de alternativas por pregunta: sin "
                    "él no se puede descontar `E/(N-1)`"
                )
        if self.kind is ScoringKind.PASS_FAIL and self.fail_if_errors_gte is None:
            raise InvariantViolationError(
                f"la parte «{self.code}» se evalúa como apto o no apto y necesita su número de "
                "errores a partir del cual no se supera"
            )

    @property
    def numeric(self) -> bool:
        """¿Esta parte da una puntuación numérica que se suma al total?"""
        return self.kind.numeric


def score_part(rule: PartRule, *, correct: int, wrong: int) -> Fraction:
    """Puntuación **exacta** de una parte según lo que publica su convocatoria.

    - `direct`: `A - E·p`, con la penalización exacta de la parte;
    - `scaled`: `(Y/T)·(A - E/(N-1))`, la fórmula oficial de Guardia Civil;
    - `pass_fail`: cero, porque una parte que se evalúa como apto o no apto no da puntos (y quien
      decide si se supera es `passed_part`).
    """
    if rule.kind is ScoringKind.PASS_FAIL:
        return Fraction(0)
    if rule.kind is ScoringKind.DIRECT:
        return exact_score(correct, wrong, rule.penalty)

    # `scaled`: `PartRule` ya ha comprobado que están Y, T y N.
    assert rule.score_max is not None  # noqa: S101 - lo garantiza PartRule.__post_init__
    assert rule.ordinary_items  # noqa: S101
    assert rule.options_per_question is not None  # noqa: S101
    bruto = Fraction(correct) - Fraction(wrong, rule.options_per_question - 1)
    return Fraction(str(rule.score_max)) * bruto / Fraction(rule.ordinary_items)


@dataclass(frozen=True, slots=True)
class PartVerdict:
    """El veredicto de una parte cuando la convocatoria lo publica.

    `passed` es `None` cuando la parte no declara umbral (una parte de TAI, cuyo 0-50 depende de
    unos baremos que no están): ahí no se puede decir si se supera, y no se dice.
    """

    passed: bool | None
    reason: str | None = None


def verdict_for(rule: PartRule, score: Fraction, *, wrong: int) -> PartVerdict:
    """¿Se supera esta parte? Solo se responde si la convocatoria lo dice."""
    if rule.note is not None:
        # La parte trae su propia explicación (una práctica parcial, por ejemplo): manda esa.
        return PartVerdict(passed=None, reason=rule.note)
    if rule.kind is ScoringKind.PASS_FAIL:
        assert rule.fail_if_errors_gte is not None  # noqa: S101 - lo garantiza PartRule
        superada = wrong < rule.fail_if_errors_gte
        return PartVerdict(
            passed=superada,
            reason=(
                f"«{rule.name or rule.code}» se evalúa como apto o no apto: "
                f"{wrong} respuestas erróneas frente al límite de {rule.fail_if_errors_gte}"
            ),
        )
    if rule.pass_score is None:
        return PartVerdict(
            passed=None,
            reason=(
                f"la convocatoria no publica el umbral de «{rule.name or rule.code}»: "
                "no se declara superada ni no superada"
            ),
        )
    if rule.kind is ScoringKind.SCALED:
        return PartVerdict(
            passed=score >= Fraction(str(rule.pass_score)),
            reason=(
                f"la puntuación de la prueba se calcula con la fórmula publicada y su mínimo es "
                f"{rule.pass_score}"
            ),
        )
    # `direct`: el umbral publicado es de la calificación oficial, no de la puntuación directa.
    return PartVerdict(
        passed=None,
        reason=(
            f"el mínimo de {rule.pass_score} es de la calificación oficial, que necesita los "
            "baremos de la convocatoria: no se aplica a la puntuación directa"
        ),
    )


def aggregate(
    *,
    session_id: str,
    mode: SessionMode,
    answer_key_version_id: str | None,
    items: Sequence[EffectiveItem],
    substitutions: Sequence[Substitution],
    part_rules: Mapping[str | None, PartRule],
) -> SessionResult:
    """Agrupa los intentos por parte y suma la puntuación directa, con aritmética exacta.

    Los intentos sin responder no entran en el cálculo —la sesión puede estar a medias— y se
    informan como pendientes. Lo que decide si una pregunta cuenta es
    `AttemptOutcome.counts_in_score`, no un recuento a mano.

    La puntuación **total es la suma de las partes numéricas**, no un recálculo con los totales: si
    dos partes penalizan distinto (o una se escala con la fórmula de Guardia Civil y otra no),
    `aciertos - errores·p` con una sola `p` daría otra cosa. Las partes de apto/no apto y las que no
    se evalúan quedan fuera de la suma y se informan aparte.
    """
    partes: dict[str | None, list[EffectiveItem]] = {}
    for item in items:
        partes.setdefault(item.question.part_code, []).append(item)

    def suma(clave: str | None, entradas: Sequence[EffectiveItem]) -> PartScore:
        regla = part_rules.get(clave, PartRule(code=clave))
        aciertos = errores = blancos = anuladas = excluidas = conflictivas = 0
        reservas = sin_usar = 0
        for item in entradas:
            intento = item.attempt
            if intento is None:
                continue
            if item.question.is_reserve:
                if intento.outcome is AttemptOutcome.UNUSED_RESERVE:
                    sin_usar += 1
                else:
                    reservas += 1
            if intento.outcome is AttemptOutcome.CORRECT:
                aciertos += 1
            elif intento.outcome is AttemptOutcome.WRONG:
                errores += 1
            elif intento.outcome is AttemptOutcome.BLANK:
                blancos += 1
            elif intento.outcome is AttemptOutcome.ANNULLED:
                anuladas += 1
            elif intento.outcome is AttemptOutcome.CONFLICTING:
                conflictivas += 1
            elif intento.outcome is AttemptOutcome.EXCLUDED:
                excluidas += 1
        puntuacion = score_part(regla, correct=aciertos, wrong=errores)
        veredicto = verdict_for(regla, puntuacion, wrong=errores)
        return PartScore(
            part_code=clave,
            part_name=regla.name,
            ordinary_items=regla.ordinary_items,
            score_min=regla.score_min,
            score_max=regla.score_max,
            pass_score=regla.pass_score,
            penalty=regla.penalty if regla.kind.numeric else None,
            kind=regla.kind,
            correct=aciertos,
            wrong=errores,
            blank=blancos,
            annulled=anuladas,
            excluded=excluidas,
            conflicting=conflictivas,
            reserves_used=reservas,
            unused_reserves=sin_usar,
            score=puntuacion,
            passed=veredicto.passed,
            verdict_note=veredicto.reason,
        )

    detalle = tuple(suma(clave, entradas) for clave, entradas in partes.items())
    numericas = tuple(parte for parte in detalle if parte.kind.numeric)
    penalizaciones = {parte.penalty for parte in numericas}
    penalizacion = penalizaciones.pop() if len(penalizaciones) == 1 else None

    total = PartScore(
        part_code=None,
        part_name=None,
        ordinary_items=None,
        score_min=None,
        score_max=None,
        pass_score=None,
        penalty=penalizacion,
        kind=ScoringKind.DIRECT if numericas else ScoringKind.PASS_FAIL,
        correct=sum(parte.correct for parte in detalle),
        wrong=sum(parte.wrong for parte in detalle),
        blank=sum(parte.blank for parte in detalle),
        annulled=sum(parte.annulled for parte in detalle),
        excluded=sum(parte.excluded for parte in detalle),
        conflicting=sum(parte.conflicting for parte in detalle),
        reserves_used=sum(parte.reserves_used for parte in detalle),
        unused_reserves=sum(parte.unused_reserves for parte in detalle),
        # La suma de las partes **numéricas**: es exacta por definición y no depende de que
        # compartan penalización ni forma de cálculo.
        score=sum((parte.score for parte in numericas), Fraction(0)),
        passed=None,
    )

    return SessionResult(
        session_id=session_id,
        mode=mode,
        answer_key_version_id=answer_key_version_id,
        parts=detalle,
        total=total,
        substitutions=tuple(substitutions),
        unfinished=sum(1 for item in items if item.attempt is None),
        official_available=False,
        official_note=unavailable_note(mode),
    )


#: Lo que se dice cuando no hay criterio oficial importado (criterio de aceptación de S07): la
#: puntuación directa es real, la calificación 0-50 y el «apto» no se pueden calcular.
OFFICIAL_UNAVAILABLE_NOTE = (
    "La calificación oficial 0-50 resulta de transformar la puntuación directa con los baremos "
    "que fija la Comisión de Selección, y esa tabla no está importada: se muestra la puntuación "
    "directa y no se declara aprobado ni suspenso."
)

#: Lo que se añade al anterior en un **simulacro** (06_QUESTIONS §5: «no se denomina oficial»).
MOCK_EXAM_NOTE = (
    "Es un simulacro: el perfil es el del examen —mismas preguntas por parte y mismas reservas—, "
    "pero no es un examen oficial."
)

#: Lo que se añade en un **diagnóstico**: su puntuación no es una nota, es el recuento de una
#: muestra.
DIAGNOSTIC_NOTE = (
    "Es un diagnóstico: una muestra pequeña repartida por temas. La puntuación directa es el "
    "recuento de esa muestra, no una nota; la estimación por tema, con su intervalo, se lee aparte."
)


def unavailable_note(mode: SessionMode) -> str:
    """La explicación de la puntuación según el modo: un simulacro no es un examen, y se dice."""
    if mode is SessionMode.MOCK_EXAM:
        return f"{MOCK_EXAM_NOTE} {OFFICIAL_UNAVAILABLE_NOTE}"
    if mode is SessionMode.DIAGNOSTIC:
        return f"{DIAGNOSTIC_NOTE} {OFFICIAL_UNAVAILABLE_NOTE}"
    return OFFICIAL_UNAVAILABLE_NOTE


# --- estados de la sesión -------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class SessionState:
    """Instantánea de una sesión para decidir qué se puede hacer con ella."""

    session_id: str
    mode: SessionMode
    status: SessionStatus
    feedback: Feedback
    answer_key_version_id: str | None
    total_questions: int
    answered_questions: int
    started_at: datetime | None
    finished_at: datetime | None
    time_limit_minutes: int | None
    extra: dict[str, object] = field(default_factory=dict)

    @property
    def finished(self) -> bool:
        return self.status is SessionStatus.FINISHED


def can_show_correction(state: SessionState, *, question_answered: bool) -> bool:
    """¿Se puede enseñar la corrección de una pregunta?

    La regla que impide filtrar la solución: con corrección inmediata, solo de lo ya respondido; con
    corrección al final, solo cuando la sesión ha terminado. Ni un caso más.
    """
    if state.feedback is Feedback.IMMEDIATE:
        return question_answered
    return state.finished


def assert_can_answer(state: SessionState) -> None:
    """Solo se responde en una sesión en marcha."""
    if state.status is not SessionStatus.RUNNING:
        raise SessionStateError(
            f"la sesión está en estado «{state.status.value}»: no admite respuestas"
        )


def assert_can_finish(state: SessionState) -> None:
    """Terminar es un acto de una sesión en marcha.

    Terminar una sesión ya terminada **no** es un error: devolver el resultado que ya está
    calculado es lo correcto (recargar y volver a pulsar no puede fallar), y el servicio lo hace
    así. Lo que no se puede es terminar lo que nunca se inició.
    """
    if state.status is SessionStatus.DRAFT:
        raise SessionStateError("la sesión no se ha iniciado: no hay nada que terminar")


def can_start(status: SessionStatus) -> bool:
    return status is SessionStatus.DRAFT
