"""La bandeja del propietario: los avisos del alumno sobre los apuntes (F13, decisión D2).

Una sola ruta de lectura y ninguna de escritura: el aviso lo escribe el alumno desde su zona
(`POST /student/topics/{codigo}/reports`) y aquí se lee. Despacharlos —marcarlos revisados o
descartarlos— es el panel de administración (bloque C), y esa ruta llegará con su pantalla: dejar
hoy un `PATCH` sin pantalla que lo use sería contrato muerto.

Lo que esta ruta garantiza es que el aviso **no se queda dentro de la aplicación**: el propietario
puede leer hoy lo que el alumno ha marcado, con su tema, su apartado y su motivo.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query

from opofuente.api.deps import NotesReportsServiceDep
from opofuente.api.error_responses import RESOURCE_ERRORS
from opofuente.api.notes_report_schemas import (
    NoteReportListSchema,
    NoteReportSchema,
    NoteReportStatusName,
)
from opofuente.domain.notes_reports import NoteReport, NoteReportStatus

router = APIRouter(tags=["panel"])


def _aviso(aviso: NoteReport) -> NoteReportSchema:
    return NoteReportSchema(
        id=aviso.id,
        topic_code=aviso.topic_code,
        topic_title=aviso.topic_title,
        section_key=aviso.section_key,
        section_title=aviso.section_title,
        anchor=aviso.anchor,
        reason=aviso.reason,
        status=aviso.status.value,
        created_at=aviso.created_at,
        reviewed_at=aviso.reviewed_at,
    )


@router.get(
    "/notes-reports",
    response_model=NoteReportListSchema,
    responses=RESOURCE_ERRORS,
    summary="Los avisos del alumno sobre los apuntes, para la bandeja del propietario",
)
def list_note_reports(
    service: NotesReportsServiceDep,
    status: Annotated[
        NoteReportStatusName | None,
        Query(description="Filtra por estado; sin él salen todos."),
    ] = None,
    topic: Annotated[
        str | None,
        Query(description="Código legible del tema, como `IV.7`, para ver solo los de un tema."),
    ] = None,
    limit: Annotated[
        int,
        Query(ge=1, le=1000, description="Cuántos avisos se devuelven como mucho."),
    ] = 200,
) -> NoteReportListSchema:
    """Los avisos, del más nuevo al más viejo.

    `pending` cuenta los que están sin despachar **sin mirar el filtro**: es el número que el
    propietario necesita ver aunque esté mirando los de un solo tema.
    """
    avisos = service.list_reports(
        status=None if status is None else NoteReportStatus(status),
        topic_code=topic,
        limit=limit,
    )
    return NoteReportListSchema(
        pending=service.count_open(),
        reports=[_aviso(aviso) for aviso in avisos],
    )
