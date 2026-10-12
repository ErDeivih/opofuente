"""La bandeja del propietario: los avisos del alumno sobre los apuntes (F13 y F16, decisión D2).

El aviso lo escribe el alumno desde su zona (`POST /student/topics/{codigo}/reports`); aquí el
propietario lo **lee** y lo **despacha**. Las dos mitades están en este fichero porque son la misma
bandeja: una ruta de lectura sin ruta de escritura dejaba al propietario mirando lo que el alumno
marca sin poder decir qué ha hecho con ello, que es lo que le pasa hoy.

Lo que esta ruta garantiza:

- el aviso **no se queda dentro de la aplicación**: sale con su tema, su apartado, su motivo y su
  fecha;
- el **despacho es auditado**: `PATCH /notes-reports/{id}` escribe el estado, la nota y su evento en
  la misma transacción, y el actor viaja en el cuerpo o en la cabecera `X-OpoFuente-Actor` como en
  el resto de escrituras del panel;
- el **apartado exacto** viaja con el aviso (`section_key` y `anchor`), que es lo que permite abrir
  los apuntes en el punto del que habla en lugar de buscarlo a mano.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Header, Path, Query

from opofuente.api.deps import NotesReportsServiceDep
from opofuente.api.error_responses import RESOURCE_ERRORS, WRITE_ERRORS
from opofuente.api.notes_report_schemas import (
    NoteReportListSchema,
    NoteReportSchema,
    NoteReportStatusName,
    NoteReportUpdateSchema,
)
from opofuente.application.notes_report_service import ACTOR_PROPIETARIO
from opofuente.domain.notes_reports import NoteReport, NoteReportStatus

router = APIRouter(tags=["panel"])

#: La cabecera con la que el panel dice quién escribe, igual que en la clasificación.
ACTOR_HEADER = "X-OpoFuente-Actor"


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
        resolution_note=aviso.resolution_note,
    )


def _actor(*, declared: str | None, header: str | None) -> str:
    """Quién despacha: lo que dice el cuerpo, si no la cabecera y, si no, la persona local.

    Un actor en blanco se ignora: en la auditoría es peor un actor vacío que el de por defecto.
    """
    for candidato in (declared, header):
        if candidato is not None and candidato.strip() != "":
            return candidato.strip()
    return ACTOR_PROPIETARIO


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
    q: Annotated[
        str | None,
        Query(
            max_length=200,
            description="Busca en el motivo del alumno y en el título del apartado.",
        ),
    ] = None,
    limit: Annotated[
        int,
        Query(ge=1, le=1000, description="Cuántos avisos se devuelven como mucho."),
    ] = 200,
) -> NoteReportListSchema:
    """Los avisos, del más nuevo al más viejo.

    `pending` cuenta los que están **sin despachar** (`open`) sin mirar el filtro: es el número que
    el propietario necesita ver aunque esté mirando los de un solo tema. Los otros tres recuentos y
    el `total` del filtro salen de la base, no de la página que se devuelve.
    """
    estado = None if status is None else NoteReportStatus(status)
    avisos = service.list_reports(status=estado, topic_code=topic, q=q, limit=limit)
    contados = service.status_counts()
    return NoteReportListSchema(
        pending=contados[NoteReportStatus.OPEN],
        in_progress=contados[NoteReportStatus.IN_PROGRESS],
        reviewed=contados[NoteReportStatus.REVIEWED],
        dismissed=contados[NoteReportStatus.DISMISSED],
        total=service.total(status=estado, topic_code=topic, q=q),
        reports=[_aviso(aviso) for aviso in avisos],
    )


@router.patch(
    "/notes-reports/{report_id}",
    response_model=NoteReportSchema,
    responses=WRITE_ERRORS,
    summary="Despacha un aviso: en curso, resuelto o descartado, con la nota de lo que se ha hecho",
)
def update_note_report(
    service: NotesReportsServiceDep,
    body: NoteReportUpdateSchema,
    report_id: str = Path(description="Identificador del aviso, tal como lo devuelve la bandeja."),
    actor: Annotated[str | None, Header(alias=ACTOR_HEADER)] = None,
) -> NoteReportSchema:
    """Cambia el estado de un aviso y, si se escribe, deja la nota de lo que se ha hecho.

    No hay ruta para borrar un aviso: lo que el alumno marcó como mal no se tira, se despacha. Un
    aviso que no existe es un 404 con su identificador, y una nota de más de una línea se recorta
    antes de guardarse.
    """
    aviso = service.update_report(
        report_id,
        status=NoteReportStatus(body.status),
        note=body.note,
        actor=_actor(declared=body.actor, header=actor),
    )
    return _aviso(aviso)
