"""Rutas del dossier del tema (S13, parte 1).

El tema como unidad de lectura: `GET /curriculum-nodes/{id}/dossier` devuelve lo que el corpus dice
de
él, con cada frase citada y con lo que **no** tiene declarado como hueco.

Decisión de diseño que se ve en las rutas: **leer no archiva**. `GET` calcula el dossier de hoy y
dice
con qué versión se corresponde; archivar una versión es `POST .../dossier/versions`, explícito,
porque
un `GET` que escribe estado no se puede reintentar sin pensar. El archivo es idempotente por
contenido:
archivar dos veces la misma lectura devuelve la versión que ya estaba y `created: false`.
"""

from __future__ import annotations

from fastapi import APIRouter

from opofuente.api.deps import DossierServiceDep
from opofuente.api.dossier_schemas import (
    DossierArchiveSchema,
    DossierSchema,
    DossierVersionSchema,
    dossier_schema,
)
from opofuente.api.error_responses import INGESTION_WRITE_ERRORS, RESOURCE_ERRORS
from opofuente.domain.errors import NotFoundError

router = APIRouter(tags=["programa"])


@router.get(
    "/curriculum-nodes/{node_id}/dossier",
    response_model=DossierSchema,
    responses=RESOURCE_ERRORS,
    summary="Dossier del tema: los pasajes que lo sostienen, citados, y lo que falta",
)
def node_dossier(node_id: str, service: DossierServiceDep) -> DossierSchema:
    """Lo que el corpus dice hoy de este tema, con la procedencia de cada cita.

    Incluye los temas que cuelgan de él (el ámbito de un bloque es su subárbol) y **no** incluye
    nada
    que no se pueda citar: una versión sin aceptar o un texto pobre se declaran como huecos con su
    motivo, en lugar de aparecer como si fueran material bueno.
    """
    dossier = service.build(node_id)
    if dossier is None:
        raise NotFoundError("nodo del programa", node_id)
    return dossier_schema(dossier)


@router.post(
    "/curriculum-nodes/{node_id}/dossier/versions",
    response_model=DossierArchiveSchema,
    status_code=201,
    responses=INGESTION_WRITE_ERRORS,
    summary="Archiva la lectura actual del tema como una versión del dossier",
)
def archive_dossier(node_id: str, service: DossierServiceDep) -> DossierArchiveSchema:
    """Guarda lo que el tema dice hoy, para poder compararlo con lo que diga mañana.

    Si la lectura no ha cambiado desde la última versión guardada, no se crea otra: se devuelve la
    que
    ya estaba con `created: false`. Eso es lo que permite decir «esto es lo que sabía antes y esto
    lo
    que sé ahora» sin que el historial se llene de copias idénticas.
    """
    archivado = service.archive(node_id)
    if archivado is None:
        raise NotFoundError("nodo del programa", node_id)
    dossier, creada = archivado
    return DossierArchiveSchema(
        created=creada,
        version_id=dossier.version_id or "",
        dossier=dossier_schema(dossier),
    )


@router.get(
    "/curriculum-nodes/{node_id}/dossier/versions",
    response_model=list[DossierVersionSchema],
    responses=RESOURCE_ERRORS,
    summary="Versiones guardadas del dossier, de la más nueva a la más antigua",
)
def list_dossier_versions(node_id: str, service: DossierServiceDep) -> list[DossierVersionSchema]:
    versiones = service.versions(node_id)
    if versiones is None:
        raise NotFoundError("nodo del programa", node_id)
    return [
        DossierVersionSchema(
            id=version.id,
            content_hash=version.content_hash,
            built_at=version.built_at,
            sources_count=version.sources_count,
            passages_count=version.passages_count,
        )
        for version in versiones
    ]


@router.get(
    "/curriculum-nodes/{node_id}/dossier/versions/{version_id}",
    response_model=DossierSchema,
    responses=RESOURCE_ERRORS,
    summary="Una versión guardada del dossier, tal como se leyó entonces",
)
def get_dossier_version(node_id: str, version_id: str, service: DossierServiceDep) -> DossierSchema:
    dossier = service.version(node_id, version_id)
    if dossier is None:
        raise NotFoundError("versión del dossier", version_id)
    return dossier_schema(dossier)
