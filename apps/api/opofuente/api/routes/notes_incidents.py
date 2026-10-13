"""La bandeja del motor: las incidencias que deja la comprobación de los apuntes (F18, §4.1).

La otra mitad de la bandeja del propietario. La del alumno (`notes_reports`) es lo que marca quien
estudia; esta es lo que **el propio sistema no ha podido resolver solo**: una norma que cambió, una
clave que los apuntes contradicen, un hueco sin material, una pregunta que no se puede juzgar. Hasta
ahora eso solo se veía abriendo la API.

Lo que esta ruta garantiza:

- la incidencia **no se queda dentro de la aplicación**: sale con su categoría, su motivo, la frase
  verificada cuando la hay, el tema y el apartado del que habla, y el enunciado de la pregunta que
  la
  provoca;
- **se puede ir a mirarla**: el apartado viaja con su ancla (la misma que usan los apuntes) y la
  pregunta con su identificador, así que el enlace lleva al punto del texto y a la pregunta sin
  buscarlos a mano;
- el **despacho es auditado**: `PATCH /notes-incidents/{id}` escribe el estado, la nota y su evento
en
  la misma transacción, y el actor viaja en el cuerpo o en la cabecera `X-OpoFuente-Actor` como en
  el
  resto de escrituras del panel;
- las **cuatro cifras de las categorías** salen de la base, no de la página: son las que deciden qué
  se trabaja primero.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Header, Path, Query

from opofuente.api.deps import NotesIncidentsServiceDep
from opofuente.api.error_responses import RESOURCE_ERRORS, WRITE_ERRORS
from opofuente.api.notes_incident_schemas import (
    IncidentCategoryName,
    IncidentStatusName,
    NotesIncidentListSchema,
    NotesIncidentSchema,
    NotesIncidentUpdateSchema,
)
from opofuente.application.notes_report_service import ACTOR_PROPIETARIO
from opofuente.domain.notes_incidents import IncidentStatus, NotesIncident
from opofuente.domain.topic_notes import (
    TEXTO_DE_CATEGORIA,
    TEXTO_SIN_MATERIA,
    CategoriaIncidencia,
    Motivo,
)

router = APIRouter(tags=["panel"])

#: La cabecera con la que el panel dice quién escribe, igual que en la clasificación.
ACTOR_HEADER = "X-OpoFuente-Actor"


def _por_que(incidencia: NotesIncident) -> str:
    """Por qué el motor señaló esta incidencia, en las palabras del dominio.

    Es el texto que el propietario lee para saber qué se le está pidiendo, y se calcula **aquí** y
    no
    en la pantalla para que haya una sola versión. La pregunta que no se pudo situar en ninguna
    materia tiene su propio texto: su categoría es «pregunta ambigua», pero lo que le pasa no es que
    le falte la clave, y decirle eso sería mentirle sobre el trabajo que tiene delante.
    """
    if incidencia.reason is Motivo.SIN_MATERIA_EN_EL_INDICE:
        return TEXTO_SIN_MATERIA
    return TEXTO_DE_CATEGORIA[incidencia.category]


def _incidencia(incidencia: NotesIncident) -> NotesIncidentSchema:
    return NotesIncidentSchema(
        id=incidencia.id,
        topic_code=incidencia.topic_code,
        topic_title=incidencia.topic_title,
        category=incidencia.category.value,
        category_help=_por_que(incidencia),
        reason=incidencia.reason.value,
        coverage=incidencia.coverage.value,
        detail=incidencia.detail,
        phrase=incidencia.phrase,
        attempts=incidencia.attempts,
        anchor=incidencia.anchor,
        section_title=incidencia.section_title,
        question_version_id=incidencia.question_version_id,
        stem=incidencia.stem,
        set_title=incidencia.set_title,
        source_document_id=incidencia.source_document_id,
        source_document_title=incidencia.source_document_title,
        source_document_type=incidencia.source_document_type,
        source_version_status=incidencia.source_version_status,
        source_version_label=incidencia.source_version_label,
        status=incidencia.status.value,
        created_at=incidencia.created_at,
        reviewed_at=incidencia.reviewed_at,
        resolution_note=incidencia.resolution_note,
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
    "/notes-incidents",
    response_model=NotesIncidentListSchema,
    responses=RESOURCE_ERRORS,
    summary="Las incidencias del motor, para la bandeja del propietario",
)
def list_notes_incidents(
    service: NotesIncidentsServiceDep,
    category: Annotated[
        IncidentCategoryName | None,
        Query(description="Filtra por categoría; sin ella salen todas."),
    ] = None,
    status: Annotated[
        IncidentStatusName | None,
        Query(description="Filtra por estado; sin él salen todas."),
    ] = None,
    topic: Annotated[
        str | None,
        Query(description="Código legible del tema, como `I.2`, para ver solo las de un tema."),
    ] = None,
    q: Annotated[
        str | None,
        Query(
            max_length=200,
            description="Busca en el enunciado de la pregunta, el motivo, la frase y el apartado.",
        ),
    ] = None,
    limit: Annotated[
        int,
        Query(ge=1, le=1000, description="Cuántas incidencias se devuelven como mucho."),
    ] = 200,
) -> NotesIncidentListSchema:
    """Las incidencias, de la más nueva a la más vieja.

    `pending` cuenta las que están **sin despachar** (`open`) sin mirar el filtro: es el número que
    el propietario necesita ver aunque esté mirando las de una sola categoría. `totals_by_category`
    cuenta las cuatro categorías **en la base entera**, con un `GROUP BY`: es la cifra de cada
    clase,
    medida y no heredada. El `total`, en cambio, es el del filtro.
    """
    categoria = None if category is None else CategoriaIncidencia(category)
    estado = None if status is None else IncidentStatus(status)
    incidencias = service.list_incidents(
        category=categoria, status=estado, topic_code=topic, q=q, limit=limit
    )
    contados = service.status_counts()
    return NotesIncidentListSchema(
        pending=contados[IncidentStatus.OPEN],
        in_progress=contados[IncidentStatus.IN_PROGRESS],
        reviewed=contados[IncidentStatus.REVIEWED],
        dismissed=contados[IncidentStatus.DISMISSED],
        total=service.total(category=categoria, status=estado, topic_code=topic, q=q),
        totals_by_category={
            cual.value: cuantas for cual, cuantas in service.category_counts().items()
        },
        incidents=[_incidencia(incidencia) for incidencia in incidencias],
    )


@router.patch(
    "/notes-incidents/{incident_id}",
    response_model=NotesIncidentSchema,
    responses=WRITE_ERRORS,
    summary="Despacha una incidencia: en curso, resuelta o descartada, con la nota de lo decidido",
)
def update_notes_incident(
    service: NotesIncidentsServiceDep,
    body: NotesIncidentUpdateSchema,
    incident_id: str = Path(
        description="Identificador de la incidencia, tal como lo devuelve la bandeja."
    ),
    actor: Annotated[str | None, Header(alias=ACTOR_HEADER)] = None,
) -> NotesIncidentSchema:
    """Cambia el estado de una incidencia y, si se escribe, deja la nota de lo que se ha decidido.

    No hay ruta para borrar una incidencia: lo que señaló el motor no se tira, se despacha. Una
    incidencia que no existe es un 404 con su identificador, y una nota de más de una línea se
    recorta antes de guardarse.
    """
    incidencia = service.update_incident(
        incident_id,
        status=IncidentStatus(body.status),
        note=body.note,
        actor=_actor(declared=body.actor, header=actor),
    )
    return _incidencia(incidencia)
