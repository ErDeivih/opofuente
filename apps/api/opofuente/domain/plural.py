"""Un número con su palabra **en su forma**: «1 pregunta», «3 preguntas».

Existe porque el panel enseñaba «1 pregunta(s) 1 preguntas no tienen…» y «10 fila con 3
celda(s)»: el defecto no es cosmético —el propietario lo lee en cada fila— y tampoco se
arregla con una regla que añada una «s» al final: en español el plural no es eso («la pregunta
que no se puede juzgar» → «las preguntas que no se pueden juzgar»), y una regla a medias
escribiría «1 preguntas».

Por eso el singular y el plural se escriben **los dos**, en la llamada, y nunca se derivan el
uno del otro. Es la misma regla que el módulo de la pantalla (`apps/web/src/lib/plural.ts`), que
se llama igual: un solo sitio por lado y ninguna forma inventada.

Dos funciones, y la segunda existe por la primera: `forma` elige la palabra y la devuelve sola —lo
necesita el resumen de la bandeja, que pone la cifra por su cuenta—, y `con_numero` la compone con
su cifra, que es lo que hace falta el resto de las veces.
"""

from __future__ import annotations

__all__ = ["con_numero", "forma"]


def forma(cantidad: int, singular: str, plural: str) -> str:
    """La palabra en su forma, sin la cifra: «aviso» para uno y «avisos» para tres."""
    return singular if cantidad == 1 else plural


def con_numero(cantidad: int, singular: str, plural: str) -> str:
    """«1 aviso», «3 avisos». La cifra delante y la palabra en su forma."""
    return f"{cantidad} {forma(cantidad, singular, plural)}"
