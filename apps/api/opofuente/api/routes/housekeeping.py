"""Rutas de higiene del almacén y reindexación (07_UI-UX §11, DEBT-007 y DEBT-015).

Dos reglas que se ven en las rutas y no son casualidad:

1. **medir y retirar son rutas distintas**. `GET /housekeeping` no escribe nunca; cada retirada
   (`POST /housekeeping/…`) lleva su confirmación explícita en el cuerpo. Un «limpiar todo» sin foto
   previa es lo que el contrato prohíbe, y una acción destructiva sin confirmación es lo que haría
   que nadie se atreviera a tocar nada;
2. **rehacer el índice no es una acción global peligrosa**: `texto` es la verdad y `evidence_fts` es
   derivado, así que rehacerlo no puede perder nada. Aun así dice cuántos fragmentos ha indexado y
   cuánto ha tardado, que es lo que pide DEBT-015.
"""

from __future__ import annotations

from fastapi import APIRouter

from opofuente.api.deps import HousekeepingServiceDep, SearchServiceDep
from opofuente.api.error_responses import INGESTION_WRITE_ERRORS, RESOURCE_ERRORS
from opofuente.api.housekeeping_schemas import (
    AreaUsageSchema,
    HousekeepingCandidateSchema,
    HousekeepingReportSchema,
    IndexHealthSchema,
    PurgeRequestSchema,
    PurgeResultSchema,
    ReindexSchema,
)
from opofuente.application.housekeeping_service import (
    HousekeepingService,
    PurgeResult,
)
from opofuente.domain.errors import InvalidStateError
from opofuente.domain.housekeeping import HousekeepingAction

router = APIRouter(tags=["almacén"])

#: Acciones de retirada admitidas, con la ruta que las invoca: una acción que no esté aquí no
#: existe, y añadir una nueva obliga a pasar por este mapa.
_PURGE_ACTIONS: dict[str, HousekeepingAction] = {
    "temps": HousekeepingAction.STALE_TEMP,
    "orphan-artifacts": HousekeepingAction.ORPHAN_ARTIFACT,
    "old-jobs": HousekeepingAction.OLD_JOB,
}


def _report(servicio: HousekeepingService) -> HousekeepingReportSchema:
    informe = servicio.report()
    return HousekeepingReportSchema(
        usage=[
            AreaUsageSchema(
                area=area.area,
                path_display=area.path_display,
                size_bytes=area.size_bytes,
                file_count=area.file_count,
                readable=area.readable,
                note=area.note,
            )
            for area in informe.usage
        ],
        candidates=[
            HousekeepingCandidateSchema(
                action=candidato.action.value,
                reference=candidato.reference,
                detail=candidato.detail,
                size_bytes=candidato.size_bytes,
                display=candidato.display,
            )
            for candidato in informe.candidates
        ],
        retention_days=informe.retention_days,
        total_bytes=informe.total_bytes,
        reclaimable_bytes=informe.reclaimable_bytes,
    )


def _resultado(resultado: PurgeResult) -> PurgeResultSchema:
    return PurgeResultSchema(
        action=resultado.action.value,
        removed=resultado.removed,
        freed_bytes=resultado.freed_bytes,
        skipped=list(resultado.skipped),
        detail=resultado.detail,
    )


def _purge(
    servicio: HousekeepingService,
    accion: HousekeepingAction,
    request: PurgeRequestSchema,
) -> PurgeResultSchema:
    if not request.confirm:
        raise InvalidStateError(
            "retirar material exige confirmación explícita: revisa la lista y vuelve a pedirlo"
        )
    referencias = None if request.references is None else tuple(request.references)
    if accion is HousekeepingAction.STALE_TEMP:
        return _resultado(servicio.purge_temps(references=referencias))
    if accion is HousekeepingAction.ORPHAN_ARTIFACT:
        return _resultado(servicio.purge_orphan_artifacts(identifiers=referencias))
    return _resultado(servicio.purge_old_jobs(identifiers=referencias))


@router.get(
    "/housekeeping",
    response_model=HousekeepingReportSchema,
    responses=RESOURCE_ERRORS,
    summary="Qué ocupa el almacén y qué se puede retirar (no escribe nada)",
)
def housekeeping_report(service: HousekeepingServiceDep) -> HousekeepingReportSchema:
    return _report(service)


@router.post(
    "/housekeeping/temps",
    response_model=PurgeResultSchema,
    responses=INGESTION_WRITE_ERRORS,
    summary="Retira temporales de operaciones interrumpidas",
)
def purge_temps(request: PurgeRequestSchema, service: HousekeepingServiceDep) -> PurgeResultSchema:
    return _purge(service, HousekeepingAction.STALE_TEMP, request)


@router.post(
    "/housekeeping/orphan-artifacts",
    response_model=PurgeResultSchema,
    responses=INGESTION_WRITE_ERRORS,
    summary="Retira artefactos sin origen ni documento que los use",
)
def purge_orphan_artifacts(
    request: PurgeRequestSchema, service: HousekeepingServiceDep
) -> PurgeResultSchema:
    return _purge(service, HousekeepingAction.ORPHAN_ARTIFACT, request)


@router.post(
    "/housekeeping/old-jobs",
    response_model=PurgeResultSchema,
    responses=INGESTION_WRITE_ERRORS,
    summary="Retira del historial los trabajos terminados y antiguos",
)
def purge_old_jobs(
    request: PurgeRequestSchema, service: HousekeepingServiceDep
) -> PurgeResultSchema:
    return _purge(service, HousekeepingAction.OLD_JOB, request)


@router.get(
    "/search/index",
    response_model=IndexHealthSchema,
    responses=RESOURCE_ERRORS,
    summary="Estado del índice léxico: completo o con fragmentos por indexar",
)
def index_health(service: SearchServiceDep) -> IndexHealthSchema:
    sano, detalle, faltan = service.index_health()
    return IndexHealthSchema(healthy=sano, detail=detalle, missing_entries=faltan)


@router.post(
    "/search/reindex",
    response_model=ReindexSchema,
    responses=INGESTION_WRITE_ERRORS,
    summary="Rehace el índice léxico desde el texto de las evidencias (DEBT-015)",
)
def reindex(service: SearchServiceDep) -> ReindexSchema:
    informe = service.reindex()
    return ReindexSchema(
        indexed=informe.indexed,
        before=informe.before,
        after=informe.after,
        took_seconds=informe.took_seconds,
        detail=informe.detail,
    )
