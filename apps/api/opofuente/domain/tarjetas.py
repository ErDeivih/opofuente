"""De un hecho de los apuntes a una tarjeta, **sin modelo y sin inventar** (M3 de la fase 3).

La regla del hito es estricta: **una tarjeta mal formada es peor que un hueco**, porque el
alumno memoriza una pregunta que no era. Por eso aquí **no se reformula nada**: se reconocen
**formas regulares** —«el puerto 137 corresponde al servicio X», «X utiliza el puerto N»— y
**lo que no encaja devuelve `None`**, que el llamante cuenta y dice. **Lo que no encaja no se
convierte en tarjeta a la fuerza.**
Esto es la mitad barata del paso 1 de M3: la que no necesita el modelo.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

#: «el puerto 137 corresponde al servicio NetBIOS Name Service».
_PUERTO_A_SERVICIO = re.compile(
    r"el\s+puerto\s+(?P<puerto>\d{1,5})\s+corresponde\s+al\s+servicio\s+"
    r"(?P<servicio>[A-Za-z0-9 ._/-]+)",
    re.IGNORECASE,
)

#: «El protocolo NTP utiliza el puerto 123».
_SERVICIO_A_PUERTO = re.compile(
    r"(?P<servicio>[A-Za-z][A-Za-z0-9 ._/-]{1,40}?)\s+(?:utiliza|usa|emplea)\s+el\s+puerto\s+"
    r"(?P<puerto>\d{1,5})",
    re.IGNORECASE,
)


@dataclass(frozen=True, slots=True)
class Tarjeta:
    """Una tarjeta corta: lo que se pregunta, lo que se responde, y de qué hecho sale."""

    anverso: str
    reverso: str
    #: El texto del hecho del que sale: es el enlace con los apuntes y lo que permite comprobarla.
    hecho: str


def _limpia(texto: str) -> str:
    """El texto sin espacios de sobra y **cortado donde empieza otro dato**.

    «NetBIOS Name Service y el 139 a NetBIOS Session Service» no es un reverso: son dos. El
    corte en « y el », la coma, el punto y coma o el punto deja el primero, que es el que la
    frase estaba afirmando.
    """
    corto = re.split(r"\s+y\s+el\s+|,|;|\.\s", texto)[0]
    return " ".join(corto.split()).strip(" .,;:")


def tarjeta_estructural(texto: str) -> Tarjeta | None:
    """La tarjeta que sale de una forma regular, o `None` si el hecho no encaja en ninguna."""
    if not texto.strip():
        return None
    encontrado = _PUERTO_A_SERVICIO.search(texto)
    if encontrado:
        puerto = encontrado.group("puerto")
        servicio = _limpia(encontrado.group("servicio"))
        if servicio:
            return Tarjeta(
                anverso=f"¿Qué servicio corresponde al puerto {puerto}?",
                reverso=servicio,
                hecho=texto,
            )
    encontrado = _SERVICIO_A_PUERTO.search(texto)
    if encontrado:
        servicio = _limpia(encontrado.group("servicio"))
        puerto = encontrado.group("puerto")
        if servicio:
            return Tarjeta(
                anverso=f"¿Qué puerto utiliza {servicio}?",
                reverso=puerto,
                hecho=texto,
            )
    return None
