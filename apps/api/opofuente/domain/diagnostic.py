"""Diagnóstico y simulacro: la muestra, el intervalo y lo que se puede decir con ella.

Dos modos de 06_QUESTIONS §5 que S07 declaró y no construyó (DEBT-012), y que tienen en común una
idea: **decir solo lo que la muestra sostiene**.

1. **El simulacro** (`mock_exam`) es el perfil exacto del examen —las mismas preguntas por parte y
las
   mismas reservas— pero **no se llama oficial**, y evita las preguntas que se han visto hace poco
   si
   hay banco suficiente. Aquí vive lo segundo: qué preguntas cuentan como «vistas hace poco» y cómo
   se
   ordena el banco para preferir las que no lo están.
2. **El diagnóstico** (`diagnostic`) es una muestra **pequeña y estratificada** por tema, y su
lectura
   es una estimación por tema **con su intervalo**, nunca un porcentaje de dominio calculado con dos
   preguntas. Aquí vive la muestra y el intervalo; el servicio solo aporta los datos.

Todo es dominio puro: ni base de datos, ni reloj, ni azar. La muestra se elige **por orden**
(primero
las preguntas con menos intentos), no al azar: un diagnóstico que cambia de preguntas en cada
pulsación
no se puede comparar consigo mismo, y el orden se puede explicar.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from math import sqrt

from opofuente.domain.numeros import nota

# --- simulacro ------------------------------------------------------------------------------------

#: Días en los que una pregunta cuenta como «vista hace poco». Es la misma ventana que usa la
#: estimación de dominio (`domain/review.py`), y por la misma razón: lo de hace meses no dice cómo
#: se
#: está ahora.
DIAS_VISTA_HACE_POCO = 60


def order_for_mock(
    questions: Sequence[str],
    *,
    recently_seen: frozenset[str],
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Separa las preguntas en (no vistas hace poco, vistas hace poco), sin perder ninguna.

    Devuelve las dos listas en vez de una sola: quien compone tiene que poder decir **cuántas** ha
    tenido que repetir, y una lista ya filtrada no lo dice.
    """
    frescas = tuple(pregunta for pregunta in questions if pregunta not in recently_seen)
    repetidas = tuple(pregunta for pregunta in questions if pregunta in recently_seen)
    return (frescas, repetidas)


# --- diagnóstico ----------------------------------------------------------------------------------

#: Preguntas por tema en la muestra. La muestra es **pequeña** a propósito: el diagnóstico no busca
#: una nota, busca saber por dónde está el hueco con pocas preguntas y con la incertidumbre a la
#: vista.
PREGUNTAS_POR_TEMA = 2

#: Tope de la muestra entera, para que un temario de sesenta temas no se convierta en un examen.
MAXIMO_MUESTRA_DIAGNOSTICO = 20

#: Temas mínimos para que la muestra sea «estratificada». Con menos temas no se reparte nada: se
#: dice
#: que el banco no permite un diagnóstico en lugar de enseñar una muestra que no estratifica.
MINIMO_TEMAS_DIAGNOSTICO = 3

#: Nivel de confianza del intervalo (95 %), con su valor z de la normal estándar.
Z_CONFIANZA = 1.96


@dataclass(frozen=True, slots=True)
class DiagnosticTopic:
    """Un tema del programa con sus preguntas candidatas, en el orden en que se eligen."""

    node_id: str
    title: str
    #: Preguntas del tema, ya ordenadas: primero las que menos se han intentado.
    question_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class DiagnosticSample:
    """La muestra elegida y lo que se ha quedado fuera, dicho con números."""

    question_ids: tuple[str, ...]
    topics: tuple[str, ...]
    #: Preguntas del banco sin tema asignado: no pueden estratificar, así que no entran.
    without_topic: int
    #: Temas con preguntas que se han quedado sin representación por el tope de la muestra.
    uncovered_topics: tuple[str, ...]
    detail: str


def stratified_sample(
    topics: Sequence[DiagnosticTopic],
    *,
    per_topic: int = PREGUNTAS_POR_TEMA,
    limit: int = MAXIMO_MUESTRA_DIAGNOSTICO,
    without_topic: int = 0,
) -> DiagnosticSample:
    """Reparte la muestra entre los temas: uno de cada uno antes de repetir en el mismo.

    El reparto es **round-robin** por temas, no por bloques: con el tope justo, un reparto por
    bloques
    dejaría los últimos temas sin ninguna pregunta, y un diagnóstico que no mira cuatro temas no
    puede
    decir nada de ellos.
    """
    disponibles = [tema for tema in topics if tema.question_ids]
    elegidas: list[str] = []
    usadas_por_tema: dict[str, int] = {tema.node_id: 0 for tema in disponibles}
    cubiertos: set[str] = set()
    for ronda in range(max(per_topic, 0)):
        for tema in disponibles:
            if len(elegidas) >= limit:
                break
            usadas = usadas_por_tema[tema.node_id]
            if usadas > ronda or usadas >= len(tema.question_ids):
                continue
            elegidas.append(tema.question_ids[usadas])
            usadas_por_tema[tema.node_id] = usadas + 1
            cubiertos.add(tema.node_id)
        if len(elegidas) >= limit:
            break

    sin_cubrir = tuple(tema.title for tema in disponibles if tema.node_id not in cubiertos)
    partes = [
        f"{len(elegidas)} preguntas en {len(cubiertos)} tema(s) de {len(disponibles)} con preguntas"
    ]
    if sin_cubrir:
        partes.append(
            f"el tope de la muestra dejó fuera {len(sin_cubrir)} tema(s): {', '.join(sin_cubrir)}"
        )
    if without_topic:
        partes.append(
            f"{without_topic} pregunta(s) del banco no tienen tema asignado y no entran "
            "en la muestra"
        )
    return DiagnosticSample(
        question_ids=tuple(elegidas),
        topics=tuple(tema.node_id for tema in disponibles if tema.node_id in cubiertos),
        without_topic=without_topic,
        uncovered_topics=sin_cubrir,
        detail=". ".join(partes) + ".",
    )


@dataclass(frozen=True, slots=True)
class Interval:
    """Un intervalo de confianza con cuatro decimales, para poder enseñarlo y compararlo.

    Se redondea al construirlo: dos intervalos del mismo cálculo tienen que poder compararse de un
    vistazo, y un `0.34119999999999997` en pantalla no ayuda a nadie.
    """

    low: float
    high: float
    confidence: float

    @property
    def width(self) -> float:
        return round(self.high - self.low, 4)


def wilson_interval(correct: int, total: int, *, z: float = Z_CONFIANZA) -> Interval | None:
    """Intervalo de Wilson para una proporción, o `None` si no hay ninguna respuesta.

    Se usa Wilson y no el intervalo normal porque con 2 aciertos de 2 el intervalo normal da (1, 1)
    —«dominio perfecto»— y Wilson da (0,34; 1,0), que es la verdad: con dos preguntas no se sabe
    casi
    nada. Es exactamente lo que §5 prohíbe enseñar como porcentaje de dominio.
    """
    if total <= 0:
        return None
    p = correct / total
    denominador = 1 + (z * z) / total
    centro = (p + (z * z) / (2 * total)) / denominador
    margen = z * sqrt((p * (1 - p) + (z * z) / (4 * total)) / total) / denominador
    return Interval(
        low=round(max(0.0, centro - margen), 4),
        high=round(min(1.0, centro + margen), 4),
        confidence=0.95,
    )


@dataclass(frozen=True, slots=True)
class TopicOutcome:
    """Lo que se contestó de un tema en la muestra: sin esto, la estimación no se puede leer."""

    node_id: str
    title: str
    answered: int
    correct: int
    interval: Interval | None
    note: str


@dataclass(frozen=True, slots=True)
class BlockTally:
    """Lo contestado de un bloque, ya agregado: cuántos temas suma y qué se acertó.

    El bloque no se contesta: se contesta por temas. Este recuento es lo que el servicio puede
    reunir de la muestra, y `topics` viaja para poder decir **a cuántos temas** se está agregando.
    """

    node_id: str
    title: str
    topics: int
    answered: int
    correct: int


@dataclass(frozen=True, slots=True)
class BlockOutcome:
    """La lectura por bloque: la misma muestra, agregada, y dicha como lo que es."""

    node_id: str
    title: str
    topics: int
    answered: int
    correct: int
    interval: Interval | None
    note: str


def read_blocks(
    tallies: Sequence[BlockTally],
    *,
    z: float = Z_CONFIANZA,
) -> tuple[BlockOutcome, ...]:
    """Agrega los temas por bloque, sin convertir la suma en una nota del bloque.

    Un bloque junta varios temas, así que su intervalo se estrecha aunque no se haya preguntado
    nada nuevo: eso **no** es más conocimiento, es más muestra. La nota de cada bloque lo dice
    (cuántos temas agrega) y no se calcula ningún umbral ni calificación: aquí solo se cuenta lo
    contestado y se da el intervalo de Wilson, igual que por tema.
    """
    fichas: list[BlockOutcome] = []
    for recuento in tallies:
        intervalo = wilson_interval(recuento.correct, recuento.answered, z=z)
        if recuento.answered == 0:
            frase = "no se contestó ninguna pregunta de este bloque en la muestra"
        else:
            bajo = nota(intervalo.low) if intervalo else nota(0)
            alto = nota(intervalo.high) if intervalo else nota(0)
            frase = (
                f"{recuento.correct} de {recuento.answered} en la muestra, con un intervalo del "
                f"95 % que va de {bajo} a {alto}"
            )
            if recuento.topics > 1:
                frase += (
                    f"; el bloque agrega {recuento.topics} temas en la muestra y no es una nota"
                )
            else:
                frase += "; el bloque no agrega temas en la muestra y no es una nota"
        fichas.append(
            BlockOutcome(
                node_id=recuento.node_id,
                title=recuento.title,
                topics=recuento.topics,
                answered=recuento.answered,
                correct=recuento.correct,
                interval=intervalo,
                note=frase,
            )
        )
    fichas.sort(key=lambda ficha: ficha.title)
    return tuple(fichas)


@dataclass(frozen=True, slots=True)
class DiagnosticReading:
    """La lectura de la muestra: por tema, con su intervalo, y el aviso de que es una muestra.

    `blocks` es el agregado por bloque del programa. Va **aparte** de `topics` y se calcula desde
    los mismos recuentos: no sustituye la lectura por tema ni se expone por HTTP todavía (el
    contrato de la ruta no tiene el campo y añadirlo exige regenerar OpenAPI con shell).
    """

    sample_size: int
    answered: int
    topics: tuple[TopicOutcome, ...]
    detail: str
    blocks: tuple[BlockOutcome, ...] = ()


def read_diagnostic(
    outcomes: Mapping[str, tuple[str, int, int]],
    *,
    sample_size: int,
    per_topic: int = PREGUNTAS_POR_TEMA,
    z: float = Z_CONFIANZA,
) -> DiagnosticReading:
    """Convierte lo contestado por tema en una lectura con intervalo, sin inventar precisión.

    `outcomes` es `{node_id: (título, respondidas, acertadas)}` de la muestra que se presentó. Un
    tema
    con menos respuestas que `per_topic` lo dice: su intervalo es ancho porque la muestra es corta,
    y
    eso es información, no un defecto que haya que esconder.
    """
    fichas: list[TopicOutcome] = []
    for node_id, (titulo, respondidas, acertadas) in outcomes.items():
        intervalo = wilson_interval(acertadas, respondidas, z=z)
        # La frase va en `frase` y no en `nota`: `nota` es la función que formatea la cifra (§2.2),
        # y una variable local con ese nombre la taparía dentro de esta función.
        if respondidas == 0:
            frase = "no se contestó ninguna pregunta de este tema en la muestra"
        elif respondidas < per_topic:
            frase = (
                f"la muestra solo trae {respondidas} pregunta(s) de este tema: el intervalo "
                "es ancho y no se puede leer como un dominio"
            )
        else:
            # Las dos cifras del intervalo, **en español** (§2.2): la columna de al lado la pinta la
            # pantalla con `Intl` (`0,34 - 1,00`), y esta frase es la nota de esa misma fila. Antes
            # decía `0.3424 a 1.0` —los flotantes crudos—, así que la misma fila llevaba los dos
            # formatos.
            bajo = nota(intervalo.low) if intervalo else nota(0)
            alto = nota(intervalo.high) if intervalo else nota(0)
            frase = (
                f"{acertadas} de {respondidas} en la muestra, con un intervalo del 95 % que va de "
                f"{bajo} a {alto}"
            )
        fichas.append(
            TopicOutcome(
                node_id=node_id,
                title=titulo,
                answered=respondidas,
                correct=acertadas,
                interval=intervalo,
                note=frase,
            )
        )
    fichas.sort(key=lambda ficha: ficha.title)
    total_respondidas = sum(ficha.answered for ficha in fichas)
    return DiagnosticReading(
        sample_size=sample_size,
        answered=total_respondidas,
        topics=tuple(fichas),
        detail=(
            f"muestra de {sample_size} pregunta(s), {total_respondidas} contestada(s): "
            "estos intervalos son del 95 % sobre esta muestra y no son una nota ni un "
            "dominio del tema"
        ),
    )


__all__ = [
    "DIAS_VISTA_HACE_POCO",
    "MAXIMO_MUESTRA_DIAGNOSTICO",
    "MINIMO_TEMAS_DIAGNOSTICO",
    "PREGUNTAS_POR_TEMA",
    "Z_CONFIANZA",
    "BlockOutcome",
    "BlockTally",
    "DiagnosticReading",
    "DiagnosticSample",
    "DiagnosticTopic",
    "Interval",
    "TopicOutcome",
    "order_for_mock",
    "read_blocks",
    "read_diagnostic",
    "stratified_sample",
    "wilson_interval",
]
