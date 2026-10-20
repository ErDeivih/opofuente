"""Un doble del puerto de explicaciones: contesta lo que se le diga, sin llamar a nadie.

Es lo que permite probar el servicio entero —lotes, las cuatro comprobaciones, la bandeja y los
`sin_material`— **a coste cero**. El ensayo con el modelo de verdad se hace una vez, y con la cifra
delante.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from opofuente.application.explicaciones import ExplicacionPropuesta, PreguntaAExplicar


@dataclass
class FakeExplanationProposer:
    """Devuelve, por pregunta, la propuesta que se le haya dado; y si no hay, una de relleno."""

    name: str = "fake"
    #: Por `question_version_id`. Lo que no esté aquí recibe la de relleno.
    propuestas: dict[str, ExplicacionPropuesta] = field(default_factory=dict)
    #: Lo que se devuelve cuando no hay propuesta preparada: por defecto, **una que NO pasa** las
    #: comprobaciones, para que una prueba que olvide preparar su caso no salga verde por accidente.
    relleno: ExplicacionPropuesta | None = None
    #: Los lotes que se le han pedido, para poder afirmar cuántas llamadas se han hecho.
    lotes: list[tuple[str, ...]] = field(default_factory=list)

    def propose(self, lote: Sequence[PreguntaAExplicar]) -> Sequence[ExplicacionPropuesta]:
        self.lotes.append(tuple(p.question_version_id for p in lote))
        devueltas: list[ExplicacionPropuesta] = []
        for pregunta in lote:
            preparada = self.propuestas.get(pregunta.question_version_id)
            if preparada is not None:
                devueltas.append(preparada)
            elif self.relleno is not None:
                devueltas.append(
                    ExplicacionPropuesta(
                        question_version_id=pregunta.question_version_id,
                        texto=self.relleno.texto,
                        cita=self.relleno.cita,
                        letra=self.relleno.letra,
                    )
                )
        return tuple(devueltas)
