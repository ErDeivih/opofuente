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

from opofuente.domain.explicaciones import problemas


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


@dataclass(frozen=True, slots=True)
class LoteValidado:
    """Lo que sale de un lote: lo que entra, lo que se queda fuera y por qué.

    **Las tres listas son la salida del servicio**, y la bandeja del propietario se construye con la
    tercera: una explicación rechazada sin motivo obliga a mirarla otra vez para saber lo mismo.
    """

    #: Las que pasaron las cuatro comprobaciones, listas para guardarse.
    aceptadas: tuple[ExplicacionPropuesta, ...]
    #: Las que devolvió el modelo y no pasaron: su id y los motivos, tal cual.
    rechazadas: tuple[tuple[str, tuple[str, ...]], ...]
    #: Las preguntas que **no se pueden explicar** porque no tienen ancla o no tienen clave.
    sin_material: tuple[str, ...]


def _trozos(
    preguntas: Sequence[PreguntaAExplicar], tamano: int
) -> tuple[tuple[PreguntaAExplicar, ...], ...]:
    """El lote partido en tandas del tamaño pedido, sin perder ninguna y sin repetir."""
    if tamano <= 0:
        raise ValueError("el tamaño del lote tiene que ser mayor que cero")
    return tuple(tuple(preguntas[i : i + tamano]) for i in range(0, len(preguntas), tamano))


def validar_lote(
    preguntas: Sequence[PreguntaAExplicar],
    proposer: ExplanationProposer,
    *,
    tamano: int = 20,
) -> LoteValidado:
    """Pide las explicaciones por tandas y **comprueba cada una antes de darla por buena**.

    Las reglas, en el orden en que importan:

    1. **Sin apartado no hay explicación**: se va a `sin_material` **sin llamar al modelo** —gastar
       una llamada para que vuelva algo que no se puede comprobar es tirar el dinero—.
    2. **Sin clave servible tampoco**: no hay nada que justificar.
    3. **Lo que el modelo devuelve de más se ignora**: solo cuenta lo que corresponde a una pregunta
       del lote, porque un id inventado no puede acabar en la base.
    4. **Cada propuesta pasa las cuatro comprobaciones**; la que no, va a `rechazadas` **con sus
       motivos**, no con un «no».
    """
    con_material = tuple(p for p in preguntas if p.apartado.strip() and p.clave)
    sin_material = tuple(p.question_version_id for p in preguntas if p not in con_material)
    aceptadas: list[ExplicacionPropuesta] = []
    rechazadas: list[tuple[str, tuple[str, ...]]] = []
    for tanda in _trozos(con_material, tamano):
        por_id = {p.question_version_id: p for p in tanda}
        for propuesta in proposer.propose(tanda):
            pregunta = por_id.get(propuesta.question_version_id)
            if pregunta is None:
                continue
            motivos = problemas(
                propuesta.texto,
                cita=propuesta.cita,
                apartado=pregunta.apartado,
                letra=propuesta.letra,
                clave=pregunta.clave,
            )
            if motivos:
                rechazadas.append((propuesta.question_version_id, motivos))
            else:
                aceptadas.append(propuesta)
    return LoteValidado(
        aceptadas=tuple(aceptadas),
        rechazadas=tuple(rechazadas),
        sin_material=sin_material,
    )
