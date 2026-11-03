"""Cómo se reparte un tema de los apuntes en sus capítulos, en orden de lectura.

Vive fuera de `student_service` porque hay **dos** consumidores del mismo reparto: la pantalla de
lectura (`GET /student/topics/{codigo}/notes`, un capítulo cada vez) y la exportación a PDF
(`GET /student/topics/{codigo}/pdf`, el tema entero). Tenerlo dos veces sería tener dos órdenes que
pueden divergir: el PDF y la pantalla contarían el tema de forma distinta.

Los capítulos son los **epígrafes oficiales** del tema tal como están en el programa importado
(`tema.children`); los apartados vienen de los apuntes, cada uno en el epígrafe que tiene
guardado. El número de un apartado es su lugar en el tema entero (1..N) y no se reinicia en cada
capítulo: es el número con el que se cita y el que sale en el índice completo, igual en todas las
pantallas.
"""

from __future__ import annotations

from dataclasses import dataclass

from opofuente.application.read_models import NodeView
from opofuente.domain.profiles import NodeType
from opofuente.domain.topic_notes import SectionNotes


@dataclass(frozen=True, slots=True)
class ChapterSection:
    """Un apartado dentro de su capítulo: su número en el tema y su texto."""

    number: int
    notes: SectionNotes


@dataclass(frozen=True, slots=True)
class ChapterReading:
    """Un capítulo de los apuntes ya repartido: su identidad y los apartados que le tocan."""

    code: str
    title: str
    position: int
    sections: tuple[ChapterSection, ...]


def read_by_chapters(
    tema: NodeView, apartados: tuple[SectionNotes, ...]
) -> tuple[ChapterReading, ...]:
    """Reparte los apartados de un tema en sus **epígrafes oficiales**, en orden de lectura.

    Dos casos límite que no pueden perder texto:

    - un apartado cuyo epígrafe **no es** un epígrafe del programa (el programa se reorganizó y los
      apuntes se quedaron con el código viejo) abre su propio capítulo al final, titulado con su
      código. Es feo, pero perder el párrafo es peor;
    - un apartado **sin** código de epígrafe cae en un capítulo que es el tema, con su título.
      Hoy no hay ninguno de los dos casos (medido sobre los 29 temas con apuntes: 0 apartados fuera
      de su programa), y por eso el camino está escrito pero no probado con datos: se prueba con
      los suyos.
    """
    if not apartados:
        return ()

    numeros = {apartado.key: numero for numero, apartado in enumerate(apartados, start=1)}
    oficiales = [hijo for hijo in tema.children if hijo.node_type is NodeType.EPIGRAPH]
    titulos = {epigrafe.path: epigrafe.title for epigrafe in oficiales}
    orden = {epigrafe.path: posicion for posicion, epigrafe in enumerate(oficiales, start=1)}

    por_codigo: dict[str, list[SectionNotes]] = {}
    for apartado in apartados:
        por_codigo.setdefault(apartado.epigraph_code, []).append(apartado)

    # El orden es el del programa; lo que no está en el programa va detrás, por orden de aparición.
    codigos = [epigrafe.path for epigrafe in oficiales if epigrafe.path in por_codigo]
    codigos.extend(codigo for codigo in por_codigo if codigo not in orden)

    leidos: list[ChapterReading] = []
    for posicion, codigo in enumerate(codigos, start=1):
        leidos.append(
            ChapterReading(
                code=codigo,
                title=titulos.get(codigo) or codigo or tema.title,
                position=posicion,
                sections=tuple(
                    ChapterSection(number=numeros[apartado.key], notes=apartado)
                    for apartado in por_codigo[codigo]
                ),
            )
        )
    return tuple(leidos)
