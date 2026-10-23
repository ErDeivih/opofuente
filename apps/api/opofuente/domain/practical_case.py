"""El supuesto practico: sus reglas, sin modelo y sin red (M5).

**Lo que este fichero decide, y es lo unico que decide**: si un supuesto
propuesto **se puede aceptar**. El modelo escribe; aqui se comprueba.

**Las tres comprobaciones, y por que cada una:**

1. **veinticinco preguntas, cuatro opciones cada una**: un supuesto es una
   serie de 20 + 5 reservas, y una serie corta no es un supuesto;
2. **cada pregunta cita un parrafo de los apuntes**: sin cita no se puede
   comprobar, y un supuesto que no se puede comprobar es peor que ninguno;
3. **un segundo modelo las responde a ciegas y coincide en el 90 %**: es la
   unica forma de saber que el supuesto **tiene una respuesta defendible**.
   **Si el segundo modelo no coincide, el supuesto se descarta**, no se
   arregla: dos modelos que discrepan en una de cada cinco preguntas no
   estan midiendo el temario, estan adivinando.

**Y una que NO se hace**: **no se compara el enunciado con nada**. Un caso
practico se inventa sobre el temario, y no hay original contra el que
medirlo. **Se comprueba lo que se puede: las preguntas.**
"""

from __future__ import annotations

from dataclasses import dataclass, field

#: Las preguntas que tiene un supuesto oficial: 20 mas 5 de reserva.
PREGUNTAS_DEL_SUPUESTO = 25

#: La coincidencia minima del segundo modelo. Por debajo, el supuesto se
#: descarta. **No es un umbral de calidad: es el punto en que dos modelos
#: independientes dejan de estar de acuerdo sobre lo que dice el temario.**
COINCIDENCIA_MINIMA = 0.9


@dataclass(frozen=True, slots=True)
class PreguntaPropuesta:
    """Una pregunta del supuesto, con su clave y su cita."""

    enunciado: str
    #: Las cuatro opciones, por su letra.
    opciones: tuple[tuple[str, str], ...]
    #: La letra que corrige.
    clave: str
    #: **La frase literal de los apuntes** que la sostiene.
    cita: str


@dataclass(frozen=True, slots=True)
class SupuestoPropuesto:
    """Lo que devuelve el modelo para un bloque, y lo que hay que comprobar."""

    block: str
    statement: str
    preguntas: tuple[PreguntaPropuesta, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class Veredicto:
    """Si el supuesto se acepta, **y si no, por que**."""

    aceptado: bool
    #: Las razones del rechazo, **todas**, no la primera.
    problemas: tuple[str, ...]


def recortar_al_numero(supuesto: SupuestoPropuesto) -> SupuestoPropuesto:
    """Deja el supuesto en ``PREGUNTAS_DEL_SUPUESTO``, **quitando las sobrantes por el final**.

    **Por que no se descarta** (fase 3, §2.4): **pedir veinticinco y tirar el supuesto entero
    porque vinieron veintiseis es tirar un supuesto bueno por un error de contar**. Se quitan
    las de mas, que es lo que el documento manda.

    **Por el final y no por el principio**: el modelo anade lo que le sobra al final, y las
    primeras veinticinco son las que siguen el orden del apartado.

    **Si vienen de menos no se inventa nada**: se deja como esta y ``validar_forma`` lo dice.
    """
    if len(supuesto.preguntas) <= PREGUNTAS_DEL_SUPUESTO:
        return supuesto
    return SupuestoPropuesto(
        block=supuesto.block,
        statement=supuesto.statement,
        preguntas=supuesto.preguntas[:PREGUNTAS_DEL_SUPUESTO],
    )


def validar_forma(supuesto: SupuestoPropuesto) -> Veredicto:
    """Las dos comprobaciones que no necesitan al segundo modelo.

    **Se hacen antes de gastar la segunda llamada**: un supuesto con doce
    preguntas no merece que nadie lo responda.
    """
    problemas: list[str] = []
    if supuesto.block not in {"III", "IV"}:
        problemas.append(f"«{supuesto.block}» no es un bloque de supuesto: es III o IV")
    if not supuesto.statement.strip():
        problemas.append("el enunciado del caso esta vacio")
    if len(supuesto.preguntas) != PREGUNTAS_DEL_SUPUESTO:
        problemas.append(
            f"trae {len(supuesto.preguntas)} preguntas y un supuesto tiene {PREGUNTAS_DEL_SUPUESTO}"
        )
    for numero, pregunta in enumerate(supuesto.preguntas, start=1):
        if len(pregunta.opciones) != 4:
            problemas.append(
                f"la pregunta {numero} trae {len(pregunta.opciones)} opciones, no cuatro"
            )
        if pregunta.clave not in {letra for letra, _ in pregunta.opciones}:
            problemas.append(
                f"la clave de la pregunta {numero} («{pregunta.clave}») no es una de sus opciones"
            )
        if not pregunta.cita.strip():
            problemas.append(f"la pregunta {numero} no cita ningun parrafo")
    return Veredicto(aceptado=not problemas, problemas=tuple(problemas))


def validar_con_respuestas(
    supuesto: SupuestoPropuesto,
    *,
    respuestas: tuple[str, ...],
) -> Veredicto:
    """La tercera comprobacion: **el segundo modelo responde sin ver la clave**.

    **El orden importa**: `respuestas[i]` es lo que contesto a la pregunta
    `i`. **Se compara letra a letra**, y si el segundo modelo devuelve menos
    respuestas que preguntas, **ese hueco cuenta como fallo**: no se rellena
    a favor.
    """
    problemas = list(validar_forma(supuesto).problemas)
    total = len(supuesto.preguntas)
    aciertos = sum(
        1
        for indice, pregunta in enumerate(supuesto.preguntas)
        if indice < len(respuestas) and respuestas[indice] == pregunta.clave
    )
    coincidencia = aciertos / total if total > 0 else 0.0
    if coincidencia < COINCIDENCIA_MINIMA:
        problemas.append(
            f"el segundo modelo coincide en {aciertos} de {total} "
            f"({coincidencia:.0%}) y hace falta el "
            f"{COINCIDENCIA_MINIMA:.0%}"
        )
    return Veredicto(aceptado=not problemas, problemas=tuple(problemas))
