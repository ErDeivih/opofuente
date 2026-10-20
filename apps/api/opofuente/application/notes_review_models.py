"""Lo que la revisión de apuntes le enseña al propietario (F24, §4.3 del objetivo).

Son cuatro vistas y todas salen de leer, no de decidir: la tabla de los temas con su estado y sus
cifras, el motivo de cada borrador **con su número**, la ficha de un tema apartado a apartado tal
como se leerá en la zona del alumno, y el resultado de aprobar o rechazar.

Dos decisiones que se ven en los campos:

1. **el motivo viaja como lista de razones**, no como una frase larga: un tema en borrador suele
   tener más de un motivo (II.4 tiene la cobertura por encima del listón y 30 respuestas correctas
   marcadas que no cuentan) y una frase sola obligaría a la pantalla a partirla, con lo que el
   orden —que es la decisión de qué se lee primero— se perdería por el camino;
2. **la ficha del tema trae los apartados con su texto**, y ese texto es **el mismo** que sirve la
   zona del alumno (`TopicNotesReader.notes_for_node`): la promesa de la pantalla es «léelo como lo
   leerá él», y cumplirla con una segunda lectura de la base sería prometerlo y no hacerlo.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from opofuente.domain.notes_review import Razon, ReviewDecision, TopicReview
from opofuente.domain.topic_notes import CategoriaIncidencia, NotesState
from opofuente.infrastructure.notes_review_repository import (
    ComprobacionesDelTema,
    ContadoresDeRevision,
)

#: Qué puerta del §2.3 impide publicar cuando el tema está aprobado y no se puede archivar.
ReviewBlockName = Literal["cobertura", "forma"]


@dataclass(frozen=True, slots=True)
class VersionDeTema:
    """La versión archivada de un tema: la que lo hace «publicado»."""

    id: str
    built_at: datetime


@dataclass(frozen=True, slots=True)
class SeccionDeRevision:
    """Un apartado de los apuntes, con su texto, su forma y lo que se ha comprobado en él.

    `peor` es la cifra que ordena la lista cuando el propietario pide «los peores primero»: lo que
    no está resuelto en ese apartado —en conflicto con la respuesta correcta, dudoso o sin frase—,
    que es exactamente lo que hay que leer antes para no releer sesenta páginas.
    """

    key: str
    title: str
    epigraph_code: str
    anchor: str
    position: int
    body_markdown: str
    facts_total: int
    words: int
    covered: int
    gaps: int
    doubtful: int
    conflicts: int
    needs_review_reason: str | None

    @property
    def peor(self) -> int:
        return self.conflicts + self.doubtful + self.gaps


@dataclass(frozen=True, slots=True)
class TemaEnRevision:
    """Una fila de la tabla del panel: el tema, su estado, sus cifras, su motivo y su decisión.

    `razones` va vacío en los temas que **no** se han medido en esta lectura y ya están publicados:
    su estado no necesita motivo (ya pasó las puertas) y medirlos todos costaría medir los 15
    publicados para no decir nada nuevo. La ficha del tema sí los mide siempre.
    """

    node_id: str
    code: str
    title: str
    block_code: str
    block_title: str
    state: NotesState
    sections_written: int
    facts: int
    checks: ComprobacionesDelTema
    incidents_open: int
    incidents_by_category: tuple[tuple[CategoriaIncidencia, int], ...]
    version: VersionDeTema | None
    review: TopicReview | None
    #: El motivo, con sus cifras. Vacío cuando el tema está publicado y no se ha medido.
    razones: tuple[Razon, ...] = ()
    #: Si esta lectura ha medido la cobertura (con `apuntes --medir`: sin modelo y sin coste).
    medida: bool = False
    #: La puerta de cobertura, medida: `(cubiertas, con clave utilizable)`. `None` sin medir.
    cobertura: tuple[int, int] | None = None
    #: La cobertura sobre **todas** las que tienen clave, que se enseña pero no decide.
    cobertura_todas_las_claves: tuple[int, int] | None = None


@dataclass(frozen=True, slots=True)
class RevisionDeApuntes:
    """La tabla entera: los contadores de la cabecera y las filas, en orden del programa."""

    counters: ContadoresDeRevision
    topics: tuple[TemaEnRevision, ...]


@dataclass(frozen=True, slots=True)
class FichaDeRevision:
    """Una **página** de la ficha de un tema: su fila de la tabla y los apartados de esa página.

    La ficha va paginada porque el tema entero no cabe de una vez: IV.7 tiene 25 apartados y
    sus cuerpos son **121 de los 131 KiB** de la respuesta, y el navegador los convierte a HTML
    uno a uno antes de que el propietario pueda leer el primero. Con la página de seis apartados
    la respuesta baja a unos 40 KiB y el primer párrafo se lee enseguida.

    `sections_total` viaja aparte de `sections` a propósito: es el número de apartados del tema —lo
    que se enseña en el título— y no el de la página, que cambia al pasar de hoja.
    """

    topic: TemaEnRevision
    sections: tuple[SeccionDeRevision, ...]
    sections_total: int = 0
    page: int = 1
    page_size: int = 6

    @property
    def pages(self) -> int:
        """Cuántas páginas tiene la ficha. Siempre al menos una, aunque no haya apartados."""
        if self.page_size <= 0:
            return 1
        return max(1, -(-self.sections_total // self.page_size))


@dataclass(frozen=True, slots=True)
class ResultadoDeDecision:
    """Lo que ha pasado al aprobar o rechazar: la decisión y **si eso ha publicado** el tema.

    `published` no es lo mismo que «aprobado»: aprobar un tema que no pasa las puertas del §2.3 lo
    deja aprobado y sin publicar, y `blocked_by` dice cuál de las dos puertas lo está frenando. El
    listón no se toca: lo que cambia con una aprobación es que alguien con criterio ha dicho que el
    texto está bien, y eso no convierte un 82 % en un 90 %.
    """

    topic: TemaEnRevision
    published: bool
    version_created: bool | None = None
    blocked_by: ReviewBlockName | None = None

    @property
    def decision(self) -> ReviewDecision | None:
        return None if self.topic.review is None else self.topic.review.decision


__all__ = [
    "FichaDeRevision",
    "ResultadoDeDecision",
    "ReviewBlockName",
    "RevisionDeApuntes",
    "SeccionDeRevision",
    "TemaEnRevision",
    "VersionDeTema",
]
