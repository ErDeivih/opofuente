"""La bandeja del motor: lo que el sistema no pudo resolver, listo para que alguien decida (F18).

El servicio hace dos cosas y las dos son delgadas a propósito: **leer** la bandeja con sus filtros y
sus cifras, y **despachar** una incidencia. Lo que decide es:

- qué filtros se pueden pedir (categoría, estado, tema y búsqueda) y que el `total` que viaja con la
  lista sea el del filtro, contado en la base y no el de la página;
- que las cuatro cifras de las categorías y las cuatro de los estados sean **de la bandeja entera**,
  no del filtro: son los números de los botones, y un botón que dice cuántos hay «de esta categoría»
  después de haber filtrado por otra cosa diría un número que nadie entiende;
- que despachar una incidencia que no existe sea un 404 y no una escritura silenciosa.

La nota se normaliza **antes** de tocar la base, con la misma regla que la del aviso del alumno
(`normalise_note`): una nota kilométrica se rechaza sin haber escrito nada, y una nota en blanco no
es un error —significa «no hay nota»—.
"""

from __future__ import annotations

from opofuente.application.notes_report_service import ACTOR_PROPIETARIO
from opofuente.domain.errors import NotFoundError
from opofuente.domain.notes_incidents import (
    IncidentFilter,
    IncidentStatus,
    NotesIncident,
    normalise_note,
)
from opofuente.domain.topic_notes import CategoriaIncidencia
from opofuente.infrastructure.clock import SystemClock
from opofuente.infrastructure.notes_incident_repository import (
    SqlAlchemyNotesIncidentRepository,
)


class NotesIncidentsService:
    """Lee la bandeja del motor y despacha las incidencias que el propietario ya ha decidido."""

    def __init__(
        self, incidents: SqlAlchemyNotesIncidentRepository, clock: SystemClock | None = None
    ) -> None:
        self._incidents = incidents
        self._clock = clock if clock is not None else SystemClock()

    def list_incidents(
        self,
        *,
        category: CategoriaIncidencia | None = None,
        status: IncidentStatus | None = None,
        topic_code: str | None = None,
        q: str | None = None,
        limit: int = 200,
    ) -> tuple[NotesIncident, ...]:
        """Las incidencias, de la más nueva a la más vieja, con lo que las provoca resuelto."""
        return self._incidents.list_incidents(
            IncidentFilter(
                category=category, status=status, topic_code=topic_code, q=q, limit=limit
            )
        )

    def total(
        self,
        *,
        category: CategoriaIncidencia | None = None,
        status: IncidentStatus | None = None,
        topic_code: str | None = None,
        q: str | None = None,
    ) -> int:
        """Cuántas incidencias hay con ese filtro, contadas en la base."""
        return self._incidents.count(category=category, status=status, topic_code=topic_code, q=q)

    def status_counts(self) -> dict[IncidentStatus, int]:
        """Cuántas hay en cada estado: los números de los filtros de estado de la bandeja."""
        return self._incidents.counts_by_status()

    def category_counts(self) -> dict[CategoriaIncidencia, int]:
        """Cuántas hay de cada categoría: **las cuatro cifras** de la bandeja, contadas en la
        base."""
        return self._incidents.counts_by_category()

    def count_open(self) -> int:
        """Cuántas incidencias siguen esperando a que alguien las mire. Es el número del menú."""
        return self._incidents.count_open()

    def update_incident(
        self,
        incident_id: str,
        *,
        status: IncidentStatus,
        note: str | None = None,
        actor: str = ACTOR_PROPIETARIO,
    ) -> NotesIncident:
        """Despacha una incidencia: en curso, resuelta o descartada, con la nota de lo decidido.

        Es la ruta **auditada** del bloque C: el cambio de estado, la nota y su evento entran en
        una sola transacción (lo hace el repositorio). Una incidencia que no existe es un 404: la
        bandeja se lee con identificadores de verdad, y escribir «en curso» sobre algo que no está
        sería dejar un evento que miente.
        """
        incidencia = self._incidents.update(
            incident_id=incident_id,
            status=status,
            note=normalise_note(note),
            actor=actor,
            now=self._clock.now(),
        )
        if incidencia is None:
            raise NotFoundError("incidencia del motor", incident_id)
        return incidencia


__all__ = ["NotesIncidentsService"]
