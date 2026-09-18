"""Errores, repaso y dominio estimado (S10).

Tres cosas, y las tres con la misma regla: **no inventar datos**.

1. **La causa de un fallo la declara quien estudia** (`06_QUESTIONS` §8). La aplicación no deduce
   por qué te has equivocado: propone los epígrafes del mapeo de la pregunta —que ya existe, no se
   reclasifica nada— y la causa y la nota las escribe la persona. Un fallo sin causa declarada es un
   fallo sin causa, no un fallo «de conocimiento».
2. **Los intervalos son deterministas** (§8): fallo → 1 día; acierto con baja confianza → 2;
   acierto tras un fallo → 4; y a partir de ahí 8, 16 y 30 días. No es FSRS ni se le parece: §8 pide
   explícitamente **no copiar parcialmente** ese algoritmo, así que hay una escalera escrita, con su
   motivo, que se puede explicar y probar. Cada paso del historial guarda qué se hizo y por qué.
3. **El dominio no se estima con dos intentos** (§9): con pocos datos se dice «evidencia
   insuficiente» y se enseña el recuento, en lugar de un porcentaje que parezca una medición.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum

from opofuente.domain.study import AttemptOutcome, Confidence

# --- causas del fallo (§8 y 03_DATA-MODEL §7) ----------------------------------------------------


class ErrorCause(StrEnum):
    """Por qué se ha fallado, según quien estudia. El vocabulario es el del modelo de datos."""

    KNOWLEDGE = "knowledge"
    CONFUSION = "confusion"
    READING = "reading"
    TIME = "time"
    CALCULATION = "calculation"
    AMBIGUOUS = "ambiguous"
    OTHER = "other"


class ErrorStatus(StrEnum):
    """Un error se queda abierto hasta que quien estudia dice que ya no lo es."""

    OPEN = "open"
    RESOLVED = "resolved"


class ReviewOutcome(StrEnum):
    """Qué ha pasado al repasar una pregunta. Solo hay dos desenlaces: se ha sabido o no."""

    CORRECT = "correct"
    WRONG = "wrong"


class ReviewStatus(StrEnum):
    """Un elemento de repaso está vivo o apartado a mano (no se borra: se aparta)."""

    ACTIVE = "active"
    SUSPENDED = "suspended"


# --- la escalera de intervalos (§8) --------------------------------------------------------------

#: Intervalos publicados en §8, en días. La escalera se recorre hacia arriba y **solo** el final se
#: repite: 8 → 16 → 30 → 30…, porque el MVP no pretende estimar más allá de un mes.
INTERVALOS = (8, 16, 30)
INTERVALO_MAXIMO = 30
#: Un fallo vuelve a empezar: se repasa «hoy/mañana». Se elige mañana (1 día) y se dice.
INTERVALO_TRAS_FALLO = 1
#: Acierto con baja confianza: lo has acertado dudando.
INTERVALO_BAJA_CONFIANZA = 2
#: Acierto justo después de un fallo: ya no falla, pero todavía no está firme.
INTERVALO_TRAS_FALLO_SUPERADO = 4


@dataclass(frozen=True, slots=True)
class Schedule:
    """Cuándo vuelve a tocar y por qué. El motivo se guarda: una fecha sin motivo no se audita."""

    interval_days: int
    repetitions: int
    reason: str


def review_outcome_for(outcome: AttemptOutcome) -> ReviewOutcome | None:
    """Traduce el desenlace de un intento al de un repaso, o `None` si no dice nada del saber.

    Un acierto y un fallo son información. Un blanco **no** es un acierto: cuenta como fallo con su
    motivo, porque dejar una pregunta sin contestar no demuestra que se sepa. Las preguntas
    anuladas, excluidas o conflictivas no dicen nada de nadie y no entran en el repaso.
    """
    if outcome is AttemptOutcome.CORRECT:
        return ReviewOutcome.CORRECT
    if outcome is AttemptOutcome.WRONG:
        return ReviewOutcome.WRONG
    if outcome is AttemptOutcome.BLANK:
        return ReviewOutcome.WRONG
    return None


def schedule(
    *,
    outcome: ReviewOutcome,
    previous_interval_days: int,
    repetitions: int,
    confidence: Confidence | None = None,
) -> Schedule:
    """El intervalo siguiente y su motivo, sin mirar el reloj (eso lo pone el servicio).

    La escalera de §8, literal:

    - **fallo** → 1 día, y las repeticiones vuelven a cero (un fallo reduce el intervalo, aunque
      viniera de treinta días);
    - **acierto con baja confianza** → 2 días: lo has acertado dudando;
    - **acierto tras un fallo** → 4 días;
    - **acierto seguro repetido** → 8, 16 y 30 días.

    No declarar la confianza **no** es dudar: es no haberlo dicho, y se trata como acierto normal.
    """
    if outcome is ReviewOutcome.WRONG:
        motivo = (
            "un fallo vuelve a empezar: se repasa mañana"
            if previous_interval_days <= INTERVALO_TRAS_FALLO
            else (
                f"un fallo reduce el intervalo de {previous_interval_days} días a "
                f"{INTERVALO_TRAS_FALLO}"
            )
        )
        return Schedule(interval_days=INTERVALO_TRAS_FALLO, repetitions=0, reason=motivo)

    if confidence is Confidence.LOW:
        return Schedule(
            interval_days=INTERVALO_BAJA_CONFIANZA,
            repetitions=repetitions,
            reason="acertada con baja confianza: se repasa en dos días",
        )

    if previous_interval_days < INTERVALO_TRAS_FALLO_SUPERADO:
        return Schedule(
            interval_days=INTERVALO_TRAS_FALLO_SUPERADO,
            repetitions=repetitions + 1,
            reason="acertada después de un fallo: cuatro días",
        )

    siguiente = next(
        (intervalo for intervalo in INTERVALOS if intervalo > previous_interval_days),
        INTERVALO_MAXIMO,
    )
    return Schedule(
        interval_days=siguiente,
        repetitions=repetitions + 1,
        reason=(
            f"acertada y segura ({repetitions + 1}ª vez seguida): {siguiente} días"
            if siguiente > previous_interval_days
            else f"acertada y segura: se mantiene el máximo de {INTERVALO_MAXIMO} días"
        ),
    )


def next_due_at(now: datetime, interval_days: int) -> datetime:
    """Cuándo toca, contando días enteros desde ahora mismo (sin inventar horas del día)."""
    return now + timedelta(days=max(0, interval_days))


# --- conceptos (§9: agrupar fallos relacionados) --------------------------------------------------

_NO_ALFANUMERICO = re.compile(r"[^\w\s]")


def concept_key(label: str | None, *, curriculum_node_id: str | None) -> str:
    """La clave con la que se agrupan los fallos: el nodo del programa o la etiqueta escrita.

    Se normaliza la etiqueta (sin acentos, sin signos y en minúsculas) para que «Plazos» y «plazos»
    sean el mismo concepto: agrupar por la cadena exacta dejaría la vista de conceptos llena de
    duplicados que solo se diferencian en una mayúscula.
    """
    if curriculum_node_id:
        return f"node:{curriculum_node_id}"
    if label is None:
        return "sin-concepto"
    descompuesto = unicodedata.normalize("NFKD", label.lower())
    sin_acentos = "".join(c for c in descompuesto if not unicodedata.combining(c))
    limpio = " ".join(_NO_ALFANUMERICO.sub(" ", sin_acentos).split())
    return f"label:{limpio}" if limpio else "sin-concepto"


# --- dominio estimado (§9) ----------------------------------------------------------------------

#: Intentos mínimos para estimar algo. Con menos se dice «evidencia insuficiente»: §9 prohíbe
#: enseñar un porcentaje de dominio calculado con dos preguntas.
MIN_INTENTOS_DOMINIO = 5

#: Ventana de «intentos recientes». Fuera de ella, lo que se hizo hace meses no dice cómo se está
#: ahora, y por eso no se usa (se dice que no hay datos recientes en vez de reciclar los viejos).
DIAS_RECIENTES = 60

#: Umbrales de la estimación, **provisionales**: están escritos en un solo sitio, se declaran en el
#: resultado y hay que revisarlos con datos reales de estudio antes de darles valor diagnóstico.
UMBRAL_DOMINIO_ALTO = 0.8
UMBRAL_DOMINIO_MEDIO = 0.6


class MasteryLevel(StrEnum):
    """Lo que la aplicación puede decir del dominio de un nodo del programa."""

    NO_DATA = "no_data"
    INSUFFICIENT = "insufficient_evidence"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass(frozen=True, slots=True)
class AttemptStat:
    """Un intento ya corregido, reducido a lo que hace falta para estimar: acierto y cuándo."""

    correct: bool
    answered_at: datetime


@dataclass(frozen=True, slots=True)
class Mastery:
    """El dominio estimado de un nodo, con su recuento y su explicación.

    `level` nunca se deduce de un dato que no exista: sin intentos es `no_data`, y con menos de
    `MIN_INTENTOS_DOMINIO` intentos recientes es `insufficient_evidence`.
    """

    level: MasteryLevel
    attempts: int
    correct: int
    recent_attempts: int
    accuracy: float | None
    explanation: str

    @property
    def has_estimate(self) -> bool:
        return self.level in (MasteryLevel.LOW, MasteryLevel.MEDIUM, MasteryLevel.HIGH)


def mastery_from(
    attempts: Sequence[AttemptStat],
    *,
    now: datetime,
    recent_days: int = DIAS_RECIENTES,
    min_attempts: int = MIN_INTENTOS_DOMINIO,
) -> Mastery:
    """Estima el dominio de un tema con los intentos que hay, o dice que no se puede.

    La dificultad observada **no** entra en la estimación porque el modelo no la guarda todavía (la
    deuda queda registrada): inventarla sería dar por medido algo que nadie ha medido. Lo que sí
    entra es el acierto y la repetición en una ventana reciente.
    """
    total = len(attempts)
    if total == 0:
        return Mastery(
            level=MasteryLevel.NO_DATA,
            attempts=0,
            correct=0,
            recent_attempts=0,
            accuracy=None,
            explanation="Ningún intento en este tema: no hay nada que estimar.",
        )

    limite = now - timedelta(days=recent_days)
    recientes = [intento for intento in attempts if intento.answered_at >= limite]
    aciertos = sum(1 for intento in attempts if intento.correct)
    if len(recientes) < min_attempts:
        return Mastery(
            level=MasteryLevel.INSUFFICIENT,
            attempts=total,
            correct=aciertos,
            recent_attempts=len(recientes),
            accuracy=None,
            explanation=(
                f"Evidencia insuficiente: {len(recientes)} intento(s) en los últimos "
                f"{recent_days} días y hacen falta {min_attempts}. No se estima dominio con tan "
                f"pocos datos."
            ),
        )

    aciertos_recientes = sum(1 for intento in recientes if intento.correct)
    exactitud = aciertos_recientes / len(recientes)
    if exactitud >= UMBRAL_DOMINIO_ALTO:
        nivel = MasteryLevel.HIGH
    elif exactitud >= UMBRAL_DOMINIO_MEDIO:
        nivel = MasteryLevel.MEDIUM
    else:
        nivel = MasteryLevel.LOW
    return Mastery(
        level=nivel,
        attempts=total,
        correct=aciertos,
        recent_attempts=len(recientes),
        accuracy=round(exactitud, 4),
        explanation=(
            f"{aciertos_recientes} de {len(recientes)} aciertos en los últimos {recent_days} días "
            f"(umbrales provisionales: {UMBRAL_DOMINIO_MEDIO} y {UMBRAL_DOMINIO_ALTO}). La "
            f"dificultad observada no entra porque el modelo no la guarda."
        ),
    )
