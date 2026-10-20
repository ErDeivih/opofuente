"""Lo que hace falta para escribir una explicación: el lote, la propuesta y el puerto del modelo.

Una explicación se apoya en **el apartado de los apuntes que contiene la respuesta** (§3 de la fase
3): por eso lo que viaja al modelo es la pregunta, **su clave servible** y **el texto del
    apartado**,
y por eso lo que vuelve **tiene que traer la cita**: sin cita no hay nada que comprobar, y una
explicación que no se puede comprobar no entra.

El puerto se llama `ExplanationProposer` y devuelve **lo que el modelo contestó**, sin decidir nada:
los umbrales y las cuatro comprobaciones son del servicio. Gracias a eso **todo el servicio se
    prueba
con un doble, sin llamar a nadie y sin gastar** — que es la única forma de tener el ensayo a 0 $ que
pide el hito.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class PreguntaAExplicar:
    """Una pregunta que se puede explicar, con el material que la sostiene."""

    #: La versión de la pregunta: es a lo que se ancla la explicación en la base.
    question_version_id: str
    #: El enunciado, tal como lo lee el alumno.
    enunciado: str
    #: Las opciones, por su letra estable.
    opciones: tuple[tuple[str, str], ...]
    #: **La clave servible**: las letras que corrigen. Sin esto no se explica nada.
    clave: tuple[str, ...]
    #: El texto del apartado de los apuntes al que está anclada la pregunta.
    apartado: str
    #: De qué apartado es, para guardarlo en la explicación.
    note_anchor_id: str


@dataclass(frozen=True, slots=True)
class ExplicacionPropuesta:
    """Lo que devuelve el modelo para una pregunta, con lo que hace falta para comprobarla."""

    question_version_id: str
    #: De dos a cinco frases (lo comprueba el servicio, no se confía).
    texto: str
    #: La frase **literal** de los apuntes que sostiene la explicación.
    cita: str
    #: La letra que la explicación justifica como correcta.
    letra: str


class ExplanationProposer(Protocol):
    """El puerto: lo único que el servicio sabe del modelo."""

    name: str

    def propose(self, lote: Sequence[PreguntaAExplicar]) -> Sequence[ExplicacionPropuesta]:
        """Devuelve una propuesta por pregunta del lote. **No decide**: contesta."""
        ...
