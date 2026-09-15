"""Rutas de ingestión y trabajos (08_API-CONTRACT §4 y §5).

Solo se implementa lo que S02 puede sostener:

- inventario en lectura de una carpeta local y su confirmación para importar una copia;
- consulta de lotes, entradas, incidencias e informe;
- consulta de trabajos y cancelación.

`POST /ingestion-batches/files` (multipart), `/paste` y `/url` **no** existen todavía: necesitan
extractores (S03) y protección SSRF, y devolver un 501 sería un botón falso. La pantalla de Bandeja
lo declara. `GET /events` (SSE) tampoco: el contrato lo marca como mejora P1 con polling
obligatorio como respaldo, y S02 usa polling.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query

from opofuente.api.deps import IngestionServiceDep, JobServiceDep
from opofuente.api.error_responses import (
    BATCH_STATE_ERRORS,
    INGESTION_WRITE_ERRORS,
    RESOURCE_ERRORS,
    WRITE_ERRORS,
)
from opofuente.api.ingestion_schemas import (
    BatchDetailSchema,
    BatchSchema,
    CreateInventoryRequest,
    EntryPageSchema,
    EntrySchema,
    ImportReportSchema,
    InventorySchema,
    IssuePageSchema,
    IssueSchema,
    JobSchema,
)
from opofuente.application.ingestion_service import InventoryResult
from opofuente.application.read_models import (
    BatchDetail,
    BatchView,
    EntryPage,
    EntryView,
    IssuePage,
    IssueView,
    JobView,
)
from opofuente.domain.ingestion import ItemStatus, balanced_counters
from opofuente.domain.jobs import JobStatus

router = APIRouter()


def _entry(entry: EntryView) -> EntrySchema:
    return EntrySchema(
        id=entry.id,
        relative_path=entry.relative_path,
        original_name=entry.original_name,
        size_bytes=entry.size_bytes,
        media_type=entry.media_type,
        status=ItemStatus(entry.status),
        detail=entry.detail,
        artifact_sha256=entry.artifact_sha256,
    )


def _issue(issue: IssueView) -> IssueSchema:
    return IssueSchema(
        code=issue.code,
        severity=issue.severity,  # type: ignore[arg-type]
        safe_message=issue.safe_message,
        relative_path=issue.relative_path,
        details=issue.details,
    )


def _batch(batch: BatchView) -> BatchSchema:
    return BatchSchema(
        id=batch.id,
        kind=batch.kind,  # type: ignore[arg-type]
        mode=batch.mode,  # type: ignore[arg-type]
        status=batch.status,  # type: ignore[arg-type]
        source_path_display=batch.source_path_display,
        counters=batch.counters,
        created_at=batch.created_at,
        started_at=batch.started_at,
        finished_at=batch.finished_at,
        job_id=batch.job_id,
        inventory_batch_id=batch.inventory_batch_id,
        manifest_hash=batch.manifest_hash,
        error_summary=batch.error_summary,
        formats=batch.formats,
        issue_counts=batch.issue_counts,
        total_items=batch.total_items,
    )


def _report(detail: BatchDetail) -> ImportReportSchema:
    counters = detail.batch.counters
    # La regla del cuadre vive en el dominio (una sola vez); el inventario no tiene ecuación porque
    # no copia nada.
    balanced = detail.batch.kind == "inventory" or balanced_counters(counters)
    return ImportReportSchema(
        batch_id=detail.batch.id,
        kind=detail.batch.kind,  # type: ignore[arg-type]
        status=detail.batch.status,  # type: ignore[arg-type]
        counters=counters,
        issue_counts=detail.batch.issue_counts,
        balanced=balanced,
        artifacts_total=detail.artifacts_total,
        generated_at=detail.batch.finished_at or detail.batch.created_at,
    )


def _inventory(result: InventoryResult) -> InventorySchema:
    return InventorySchema(
        batch=_batch(result.batch),
        sample=[_entry(entry) for entry in result.sample],
        issues=[_issue(issue) for issue in result.issues],
    )


@router.post(
    "/inventories",
    response_model=InventorySchema,
    responses=INGESTION_WRITE_ERRORS,
    summary="Inventaría una carpeta en modo lectura (no copia nada)",
)
def create_inventory(
    request: CreateInventoryRequest, service: IngestionServiceDep
) -> InventorySchema:
    return _inventory(service.create_inventory(request.source_path))


@router.get(
    "/inventories/{inventory_id}",
    response_model=InventorySchema,
    responses=RESOURCE_ERRORS,
    summary="Inventario ya realizado",
)
def get_inventory(inventory_id: str, service: IngestionServiceDep) -> InventorySchema:
    return _inventory(service.get_inventory(inventory_id))


@router.post(
    "/inventories/{inventory_id}/confirm-import",
    response_model=BatchSchema,
    responses=INGESTION_WRITE_ERRORS,
    summary="Confirma la importación de una copia del inventario",
)
def confirm_import(inventory_id: str, service: IngestionServiceDep) -> BatchSchema:
    return _batch(service.confirm_import(inventory_id))


@router.get(
    "/ingestion-batches",
    response_model=list[BatchSchema],
    responses=RESOURCE_ERRORS,
    summary="Lotes de inventario e importación",
)
def list_batches(
    service: IngestionServiceDep,
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[BatchSchema]:
    return [_batch(batch) for batch in service.list_batches(limit=limit, offset=offset)]


@router.get(
    "/ingestion-batches/{batch_id}",
    response_model=BatchDetailSchema,
    responses=RESOURCE_ERRORS,
    summary="Lote con sus entradas, incidencias e informe",
)
def get_batch(batch_id: str, service: IngestionServiceDep) -> BatchDetailSchema:
    detail = service.get_batch(batch_id)
    return BatchDetailSchema(
        batch=_batch(detail.batch),
        entries=[_entry(entry) for entry in detail.entries],
        issues=[_issue(issue) for issue in detail.issues],
        report=_report(detail),
    )


@router.post(
    "/ingestion-batches/{batch_id}/cancel",
    response_model=BatchSchema,
    responses=BATCH_STATE_ERRORS,
    summary="Pide cancelar el lote (el worker se detiene entre ficheros)",
)
def cancel_batch(batch_id: str, service: IngestionServiceDep) -> BatchSchema:
    return _batch(service.cancel_batch(batch_id))


@router.post(
    "/ingestion-batches/{batch_id}/retry",
    response_model=BatchSchema,
    responses=BATCH_STATE_ERRORS,
    summary="Reintenta un lote fallido o cancelado (409 si está en otro estado)",
)
def retry_batch(batch_id: str, service: IngestionServiceDep) -> BatchSchema:
    return _batch(service.retry_batch(batch_id))


@router.get(
    "/ingestion-batches/{batch_id}/items",
    response_model=EntryPageSchema,
    responses=RESOURCE_ERRORS,
    summary="Entradas del lote",
)
def list_items(
    batch_id: str,
    service: IngestionServiceDep,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    status: Annotated[ItemStatus | None, Query()] = None,
) -> EntryPageSchema:
    page: EntryPage = service.list_entries(batch_id, limit=limit, offset=offset, status=status)
    return EntryPageSchema(
        entries=[_entry(entry) for entry in page.entries],
        total=page.total,
        limit=page.limit,
        offset=page.offset,
    )


@router.get(
    "/ingestion-batches/{batch_id}/issues",
    response_model=IssuePageSchema,
    responses=RESOURCE_ERRORS,
    summary="Incidencias del lote",
)
def list_issues(
    batch_id: str,
    service: IngestionServiceDep,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> IssuePageSchema:
    page: IssuePage = service.list_issues(batch_id, limit=limit, offset=offset)
    return IssuePageSchema(
        issues=[_issue(issue) for issue in page.issues],
        total=page.total,
        limit=page.limit,
        offset=page.offset,
    )


@router.get(
    "/ingestion-batches/{batch_id}/report",
    response_model=ImportReportSchema,
    responses=RESOURCE_ERRORS,
    summary="Informe del lote",
)
def get_report(batch_id: str, service: IngestionServiceDep) -> ImportReportSchema:
    return _report(service.get_batch(batch_id))


@router.get(
    "/jobs",
    response_model=list[JobSchema],
    responses=RESOURCE_ERRORS,
    summary="Trabajos (polling con backoff desde la interfaz)",
)
def list_jobs(
    service: JobServiceDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 25,
    status: Annotated[list[JobStatus] | None, Query()] = None,
) -> list[JobSchema]:
    jobs = service.list_jobs(limit=limit, statuses=tuple(status or ()))
    return [_job(job) for job in jobs]


@router.get(
    "/jobs/{job_id}",
    response_model=JobSchema,
    responses=RESOURCE_ERRORS,
    summary="Estado de un trabajo",
)
def get_job(job_id: str, service: JobServiceDep) -> JobSchema:
    return _job(service.get_job(job_id))


@router.post(
    "/jobs/{job_id}/cancel",
    response_model=JobSchema,
    responses=WRITE_ERRORS,
    summary="Pide cancelar un trabajo",
)
def cancel_job(job_id: str, service: JobServiceDep) -> JobSchema:
    return _job(service.cancel_job(job_id))


def _job(job: JobView) -> JobSchema:
    return JobSchema(
        id=job.id,
        job_type=job.job_type,
        status=job.status,
        progress=job.progress,
        attempts=job.attempts,
        max_attempts=job.max_attempts,
        created_at=job.created_at,
        updated_at=job.updated_at,
        step=job.step,
        error_code=job.error_code,
        error_message=job.error_message,
        started_at=job.started_at,
        finished_at=job.finished_at,
        cancel_requested=job.cancel_requested,
    )
