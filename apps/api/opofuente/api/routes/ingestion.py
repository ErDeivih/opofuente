"""Rutas de ingestión, extracción y trabajos (08_API-CONTRACT §4 y §5).

Implementado hasta S03:

- inventario en lectura de una carpeta local y su confirmación para importar una copia;
- las otras tres entradas del MVP: ficheros, texto pegado y URL descargada (con guarda SSRF);
- consulta de lotes, entradas, incidencias e informe;
- texto extraído: representaciones por artefacto, con su calidad y sus avisos, y lectura por trozos;
- consulta de trabajos y cancelación.

`GET /events` (SSE) sigue sin existir: el contrato lo marca como mejora P1 con polling obligatorio
como respaldo, y aquí se usa polling. Devolver un 501 sería un botón falso.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, File, Query, UploadFile

from opofuente.api.deps import (
    ExtractionServiceDep,
    IngestionServiceDep,
    IntakeServiceDep,
    JobServiceDep,
)
from opofuente.api.error_responses import (
    INGESTION_WRITE_ERRORS,
    RESOURCE_ERRORS,
    RETRY_ERRORS,
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
    PasteRequest,
    RepresentationSchema,
    RepresentationSourceSchema,
    RepresentationTextSchema,
    UrlRequest,
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
    RepresentationView,
)
from opofuente.domain.ingestion import ItemStatus, balanced_counters
from opofuente.domain.jobs import JobStatus
from opofuente.infrastructure.representation_store import TextSlice

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


def _representation(view: RepresentationView) -> RepresentationSchema:
    return RepresentationSchema(
        id=view.id,
        artifact_id=view.artifact_id,
        kind=view.kind,
        status=view.status,
        quality=view.quality,
        extractor=f"{view.extractor_name}@{view.extractor_version}",
        char_count=view.char_count,
        page_count=view.page_count,
        language=view.language,
        ocr_candidate=view.ocr_candidate,
        warnings=list(view.warnings),
        has_text=view.has_text,
        created_at=view.created_at,
        sources=[
            RepresentationSourceSchema(
                location=source.location, origin_type=source.origin_type, depth=source.depth
            )
            for source in view.sources
        ],
    )


def _representation_text(view: RepresentationView, trozo: TextSlice) -> RepresentationTextSchema:
    """El lector devuelve el texto **con sus avisos**: quien lee sabe si el OCR no se ejecutó."""
    return RepresentationTextSchema(
        representation_id=view.id,
        text=trozo.text,
        offset=trozo.offset,
        limit=trozo.limit,
        total_chars=trozo.total_chars,
        truncated=trozo.truncated,
        quality=view.quality,
        warnings=list(view.warnings),
    )


def _inventory(result: InventoryResult) -> InventorySchema:
    return InventorySchema(
        batch=_batch(result.batch),
        sample=[_entry(entry) for entry in result.sample],
        issues=[_issue(issue) for issue in result.issues],
    )


@router.post(
    "/ingestion-batches/files",
    response_model=BatchSchema,
    responses=INGESTION_WRITE_ERRORS,
    summary="Copia los ficheros que el usuario selecciona o suelta (S03)",
)
def ingest_files(
    intake: IntakeServiceDep,
    files: Annotated[list[UploadFile], File(description="Uno o más ficheros")],
) -> BatchSchema:
    """Subida de ficheros: cada uno se copia al almacén y sigue el pipeline.

    Un ZIP se copia aquí y se expande en la extracción, con los límites de seguridad del módulo de
    ZIP (traversal, bombas y enlaces se rechazan).
    """
    temporales = intake.stage_uploads(
        [(file.filename or "sin-nombre", file.file) for file in files]
    )
    return _batch(intake.ingest_files(temporales))


@router.post(
    "/ingestion-batches/paste",
    response_model=BatchSchema,
    responses=INGESTION_WRITE_ERRORS,
    summary="Guarda el texto pegado como material propio (S03)",
)
def ingest_paste(request: PasteRequest, intake: IntakeServiceDep) -> BatchSchema:
    return _batch(intake.ingest_paste(request.text, title=request.title))


@router.post(
    "/ingestion-batches/url",
    response_model=BatchSchema,
    responses=INGESTION_WRITE_ERRORS,
    summary="Descarga una URL con la guarda de red y la guarda como material (S03)",
)
def ingest_url(request: UrlRequest, intake: IntakeServiceDep) -> BatchSchema:
    return _batch(intake.ingest_url(request.url))


@router.get(
    "/ingestion-batches/{batch_id}/representations",
    response_model=list[RepresentationSchema],
    responses=RESOURCE_ERRORS,
    summary="Texto extraído de las entradas del lote, con su calidad y sus avisos",
)
def list_representations(
    batch_id: str, service: ExtractionServiceDep
) -> list[RepresentationSchema]:
    return [_representation(view) for view in service.representations_for_batch(batch_id)]


@router.get(
    "/representations/{representation_id}",
    response_model=RepresentationSchema,
    responses=RESOURCE_ERRORS,
    summary="Una representación: extractor, calidad, páginas y avisos",
)
def get_representation(
    representation_id: str, service: ExtractionServiceDep
) -> RepresentationSchema:
    return _representation(service.get_representation(representation_id))


@router.get(
    "/representations/{representation_id}/text",
    response_model=RepresentationTextSchema,
    responses=RESOURCE_ERRORS,
    summary="Texto extraído, por trozos, con sus avisos a la vista",
)
def get_representation_text(
    representation_id: str,
    service: ExtractionServiceDep,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=200_000)] = 20_000,
) -> RepresentationTextSchema:
    view = service.get_representation(representation_id)
    trozo = service.read_text(representation_id, offset=offset, limit=limit)
    return _representation_text(view, trozo)


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
    responses=WRITE_ERRORS,
    summary="Pide cancelar el lote (el worker se detiene entre ficheros)",
)
def cancel_batch(batch_id: str, service: IngestionServiceDep) -> BatchSchema:
    return _batch(service.cancel_batch(batch_id))


@router.post(
    "/ingestion-batches/{batch_id}/pause",
    response_model=BatchSchema,
    responses=RETRY_ERRORS,
    summary="Pausa el lote: deja de avanzar sin perder lo hecho; 409 si ya terminó",
)
def pause_batch(batch_id: str, service: IngestionServiceDep) -> BatchSchema:
    """Pausar no es cancelar: lo copiado sigue copiado y el lote se reanuda (DEBT-027 §4)."""
    return _batch(service.pause_batch(batch_id))


@router.post(
    "/ingestion-batches/{batch_id}/resume",
    response_model=BatchSchema,
    responses=RETRY_ERRORS,
    summary="Reanuda un lote en pausa y lo devuelve a la cola; 409 si no está en pausa",
)
def resume_batch(batch_id: str, service: IngestionServiceDep) -> BatchSchema:
    return _batch(service.resume_batch(batch_id))


@router.post(
    "/ingestion-batches/{batch_id}/retry",
    response_model=BatchSchema,
    responses=RETRY_ERRORS,
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
