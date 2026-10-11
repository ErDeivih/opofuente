"""La bandeja del propietario para lo que avisa el alumno (decisión D2).

Es un servicio de lectura y corto a propósito: el alumno escribe el aviso por la zona del alumno
(`StudentService.report`), y aquí solo se **lee** lo que espera una persona. Lo que sí decide es el
filtro: el panel necesita poder pedir «solo los pendientes» y «solo los de este tema», y esa
decisión vive aquí y no en la ruta para que el contrato no tenga que interpretar nada.
"""

from __future__ import annotations

from opofuente.domain.notes_reports import NoteReport, NoteReportFilter, NoteReportStatus
from opofuente.infrastructure.notes_report_repository import SqlAlchemyNotesReportRepository


class NotesReportsService:
    """Lee los avisos del alumno sobre los apuntes, con su estado y su tema."""

    def __init__(self, reports: SqlAlchemyNotesReportRepository) -> None:
        self._reports = reports

    def list_reports(
        self,
        *,
        status: NoteReportStatus | None = None,
        topic_code: str | None = None,
        limit: int = 200,
    ) -> tuple[NoteReport, ...]:
        """Los avisos, del más nuevo al más viejo, con el tema y el apartado resueltos."""
        return self._reports.list_reports(
            NoteReportFilter(status=status, topic_code=topic_code, limit=limit)
        )

    def count_open(self) -> int:
        """Cuántos avisos siguen esperando a que alguien los lea."""
        return self._reports.count_open()


__all__ = ["NotesReportsService"]
