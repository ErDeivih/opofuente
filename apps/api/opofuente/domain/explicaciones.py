"""Las cuatro comprobaciones mecánicas de una explicación (M1 de la fase 3).

Una explicación que no pase estas cuatro no se guarda: la escribe un modelo, y lo que un modelo
dice **se comprueba**, no se cree. Ninguna es opinable y ninguna necesita el modelo para decidirse.

1. **La cita existe literalmente en el apartado.** No vale parafrasear: si la explicación dice «el
   artículo 18 dice que…», esa frase tiene que estar en el texto del apartado al que se ancla. Se
   comparan los espacios colapsados, porque el texto de los apuntes trae saltos de línea y sangrías
   que no cambian lo que dice.
2. **La letra que justifica la explicación es la que corrige.** Si la explicación delata que la
   respuesta es la «c» y la clave servible dice «b», la explicación es de otra pregunta o de otra
   versión: no entra.
3. **Ninguna frase sobre exámenes ni frecuencias.** El material no promete que algo
   caiga: prometerlo sería una afirmación sobre el examen futuro que nadie puede sostener.
4. **De dos a cinco frases.** Una frase sola no explica; seis son un párrafo que el alumno no lee.
"""

from __future__ import annotations

import re
from collections.abc import Sequence

#: Cuántas frases tiene una explicación que se pueda leer.
MIN_FRASES = 2
MAX_FRASES = 5

#: Lo que no puede aparecer en una explicación: promesas sobre el examen.
_LO_QUE_NO_SE_PROMETE = re.compile(
    r"\b(en (el|los) ex[áa]menes?|suele[sn]? (caer|aparecer|preguntar)|"
    r"cae (siempre|mucho|frecuentemente)|pregunta (t[íi]pica|habitual)|"
    r"es (muy )?frecuente (que|en)|probabilidad de (caer|aparecer)|"
    r"aparece en (el|los) ex[áa]menes?)\b",
    re.IGNORECASE,
)

#: Los cortes de frase: punto, interrogación o exclamación seguidos de espacio o final.
_FIN_DE_FRASE = re.compile(r"[.!?…]+(?:\s+|$)")


def _colapsa(texto: str) -> str:
    """El texto con los espacios colapsados, para comparar citas sin que estorbe el formato."""
    return " ".join(texto.split())


def frases(texto: str) -> tuple[str, ...]:
    """Las frases de la explicación, sin las que quedan vacías."""
    return tuple(trozo.strip() for trozo in _FIN_DE_FRASE.split(texto) if trozo.strip())


def cita_literal(cita: str, apartado: str) -> bool:
    """¿Está la cita, tal cual, dentro del texto del apartado?"""
    buscada = _colapsa(cita)
    return bool(buscada) and buscada in _colapsa(apartado)


def habla_del_examen(texto: str) -> tuple[str, ...]:
    """Las frases que prometen algo sobre el examen, que son las que no pueden estar."""
    return tuple(f for f in frases(texto) if _LO_QUE_NO_SE_PROMETE.search(f))


def problemas(
    texto: str,
    *,
    cita: str,
    apartado: str,
    letra: str,
    clave: Sequence[str],
) -> tuple[str, ...]:
    """Las cuatro comprobaciones, y devuelve **qué falla**, no un sí o un no.

    El motivo importa: la bandeja del propietario enseña por qué una explicación no entró, y un
    «rechazada» sin motivo obliga a mirarla otra vez para saber lo mismo.
    """
    fallos: list[str] = []
    if not cita_literal(cita, apartado):
        fallos.append("la cita no está literalmente en el apartado")
    if letra.strip().lower() not in {clave_letra.strip().lower() for clave_letra in clave}:
        fallos.append(f"la explicación justifica la letra «{letra}», que no es la que corrige")
    promesas = habla_del_examen(texto)
    if promesas:
        fallos.append(f"promete algo sobre el examen: «{promesas[0]}»")
    cuantas = len(frases(texto))
    if cuantas < MIN_FRASES or cuantas > MAX_FRASES:
        fallos.append(f"tiene {cuantas} frases y tiene que tener de {MIN_FRASES} a {MAX_FRASES}")
    return tuple(fallos)
