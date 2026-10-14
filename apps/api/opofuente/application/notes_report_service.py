"""La bandeja del propietario para lo que avisa el alumno (decisiones D2 y F16).

El alumno escribe el aviso por la zona del alumno (`StudentService.report`) y aquí el propietario
hace las dos cosas que necesita: **leerlo** y **despacharlo**. Lo que decide el servicio es el
filtro —el panel necesita poder pedir «solo los pendientes», «solo los de este tema» y «los que
digan *puerto*», y esa decisión vive aquí y no en la ruta para que el contrato no tenga que
interpretar nada— y qué pasa cuando el aviso que se quiere despachar no existe.
"""

from __future__ import annotations

from opofuente.domain.errors import NotFoundError
from opofuente.domain.notes_reports import (
    NoteReport,
    NoteReportFilter,
    NoteReportStatus,
    normalise_note,
)
from opofuente.infrastructure.clock import SystemClock
from opofuente.infrastructure.notes_report_repository import SqlAlchemyNotesReportRepository

#: Quién firma el despacho cuando la pantalla no dice otra cosa: la persona en esta máquina.
ACTOR_PROPIETARIO = "local"


class NotesReportsService:
    """Lee los avisos del alumno y despacha los que el propietario ya ha mirado."""

    def __init__(
        self, reports: SqlAlchemyNotesReportRepository, clock: SystemClock | None = None
    ) -> None:
        self._reports = reports
        self._clock = clock if clock is not None else SystemClock()

    def list_reports(
        self,
        *,
        status: NoteReportStatus | None = None,
        topic_code: str | None = None,
        q: str | None = None,
        limit: int = 200,
    ) -> tuple[NoteReport, ...]:
        """Los avisos, del más nuevo al más viejo, con el tema y el apartado resueltos."""
        return self._reports.list_reports(
            NoteReportFilter(status=status, topic_code=topic_code, q=q, limit=limit)
        )

    def total(
        self,
        *,
        status: NoteReportStatus | None = None,
        topic_code: str | None = None,
        q: str | None = None,
    ) -> int:
        """Cuántos avisos hay con ese filtro, sin traerse las filas para contarlas."""
        return self._reports.count(status=status, topic_code=topic_code, q=q)

    def status_counts(self) -> dict[NoteReportStatus, int]:
        """Cuántos avisos hay en cada estado: los números que llevan los filtros de la bandeja."""
        return self._reports.counts()

    def count_open(self) -> int:
        """Cuántos avisos siguen esperando a que alguien los lea."""
        return self._reports.count_open()

    def update_report(
        self,
        report_id: str,
        *,
        status: NoteReportStatus,
        note: str | None = None,
        actor: str = ACTOR_PROPIETARIO,
    ) -> NoteReport:
        """Despacha un aviso: en curso, resuelto o descartado, con la nota de lo que se ha hecho.

        Es la ruta **auditada** del bloque C: el cambio de estado, la nota y su evento entran en una
        sola transacción (lo hace el repositorio). Un aviso que no existe es un 404 y no una
        escritura silenciosa: la bandeja del propietario se lee con identificadores de verdad.

        La nota se normaliza aquí **antes** de tocar la base, para que una nota kilométrica se
        rechace sin haber escrito nada. Que venga vacía no es un error: significa «no hay nota».
        """
        aviso = self._reports.update(
            report_id=report_id,
            status=status,
            note=normalise_note(note),
            actor=actor,
            now=self._clock.now(),
        )
        if aviso is None:
            raise NotFoundError("aviso del alumno", report_id)
        return aviso


__all__ = ["ACTOR_PROPIETARIO", "NotesReportsService"]
