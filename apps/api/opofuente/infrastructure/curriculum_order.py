"""El orden del programa: por el número del bloque y el del tema, no por el texto de la ruta.

`path` es un identificador jerárquico con puntos («IV.10», «1.1.10») y ordenarlo **como texto** pone
`IV.10` justo detrás de `IV.1` y `1.1.10` detrás de `1.1.1`: sale el orden en el que el documento
listó los temas, no el orden en el que se estudian. Aquí cada segmento se traduce a su número
—romano o arábigo— y se ordena por (bloque, tema, epígrafe), que es el orden oficial del temario
y el mismo para cualquier programa futuro.

Dos decisiones que se ven en el código:

1. **La clave se construye en SQL**, no en Python. Así la consulta del programa, la de cobertura y
   la de los listados del panel ordenan igual sin que nadie tenga que acordarse de reordenar
   después; no hay dos órdenes que puedan divergir. Y el orden sigue valiendo cuando el programa
   real no tiene `position` coherente con la numeración oficial.
2. **Una ruta corta va antes que sus hijas** (`I` antes de `I.1`) y un segmento que no es número se
   va al final, desempatado alfabéticamente: un temario con un bloque «PARTE GENERAL» sigue saliendo
   en un orden estable y predecible en lugar de mezclarse con los numerados.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import Integer, case, cast, func

from opofuente.domain.profiles import MAX_DEPTH

#: Una columna o expresión SQL. Es `Any` a propósito: la columna de un modelo es un
#: `InstrumentedAttribute`, que se comporta como una expresión en toda consulta pero que mypy
#: no considera un `ColumnElement`. Anotar la clase concreta obligaría a un `cast` en cada llamada.
Expresion = Any

#: Números romanos que puede llevar un bloque del programa. Se cubren de sobra los que usan las
#: convocatorias reales (I a XV) para no tener que tocar esto cuando entre un temario más largo.
ROMANOS: dict[str, int] = {
    "I": 1,
    "II": 2,
    "III": 3,
    "IV": 4,
    "V": 5,
    "VI": 6,
    "VII": 7,
    "VIII": 8,
    "IX": 9,
    "X": 10,
    "XI": 11,
    "XII": 12,
    "XIII": 13,
    "XIV": 14,
    "XV": 15,
}

#: Un segmento que ni es número ni es romano («PARTE GENERAL») se ordena **después** de todos los
#: numerados y se desempata por su texto.
NO_NUMERICO = 1_000_000

#: Segmentos que tiene una ruta como mucho: la raíz y un nivel por cada `MAX_DEPTH`.
SEGMENTOS = MAX_DEPTH + 1


def _tras_saltar(expresion: Expresion, saltos: int) -> Expresion:
    """La parte de la ruta que queda tras `saltos` puntos (con 0 saltos, la ruta entera)."""
    resto = expresion
    for _ in range(saltos):
        punto = func.instr(resto, ".")
        resto = case((punto == 0, ""), else_=func.substr(resto, punto + 1))
    return resto


def _segmento(expresion: Expresion, indice: int) -> Expresion:
    """El segmento `indice` (0 = primero) de una ruta con puntos, o cadena vacía si no lo tiene."""
    resto = _tras_saltar(expresion, indice)
    punto = func.instr(resto, ".")
    return case((punto == 0, resto), else_=func.substr(resto, 1, punto - 1))


def _clave_de_segmento(expresion: Expresion, indice: int) -> tuple[Expresion, Expresion]:
    """(valor, texto) de un segmento: el valor numérico manda y el texto solo desempata."""
    segmento = _segmento(expresion, indice)
    numero = cast(segmento, Integer)
    romano = case(*[(func.upper(segmento) == nombre, valor) for nombre, valor in ROMANOS.items()])
    return (
        case(
            (segmento == "", 0),
            (numero > 0, numero),
            (romano.is_not(None), romano),
            else_=NO_NUMERICO,
        ),
        segmento,
    )


def curriculum_order(path: Expresion) -> tuple[Expresion, ...]:
    """Las expresiones de `ORDER BY` que ponen el programa en orden numérico.

    Se usa tal cual en la consulta (`order_by(*curriculum_order(CurriculumNodeRecord.path))`) y su
    resultado es un orden **total** —cada segmento y la ruta entera como último desempate—, de modo
    que dos bases con los mismos datos devuelven siempre la misma lista.
    """
    claves: list[Expresion] = []
    for indice in range(SEGMENTOS):
        claves.extend(_clave_de_segmento(path, indice))
    claves.append(path)
    return tuple(claves)
