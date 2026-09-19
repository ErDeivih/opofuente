"""Rutas de copia, verificación y restauración (08_API-CONTRACT §11).

El contrato fija cinco rutas y una regla: «restaurar exige seleccionar backup validado,
previsualización y creación automática de backup previo». Aquí están las cinco y la regla se cumple
**de verdad**:

- `POST /restore/validate` es la previsualización: valida sin escribir;
- `POST /restore/execute` no acepta un backup sin validar: comprueba la copia entera antes de tocar
  nada y hace la copia previa automática (eso ocurre dentro del servicio, no en la ruta, porque es
  una regla de negocio y no una comprobación de entrada).
"""

from __future__ import annotations

from fastapi import APIRouter

from opofuente.api.backup_schemas import (
    BackupListSchema,
    BackupSchema,
    CreateBackupSchema,
    RestorePreviewSchema,
    RestoreRequestSchema,
    RestoreResultSchema,
    VerificationSchema,
)
from opofuente.api.deps import BackupServiceDep
from opofuente.api.error_responses import INGESTION_WRITE_ERRORS, RESOURCE_ERRORS
from opofuente.application.backup_service import (
    BackupView,
    RestorePreview,
    RestoreResult,
    VerificationView,
)
from opofuente.domain.backup import BackupError
from opofuente.domain.errors import InvalidStateError, NotFoundError

router = APIRouter(tags=["copias"])


def _backup(view: BackupView) -> BackupSchema:
    return BackupSchema(
        id=view.id,
        created_at=view.created_at,
        app_version=view.app_version,
        schema_revision=view.schema_revision,
        scope=list(view.scope),
        size_bytes=view.size_bytes,
        file_count=view.file_count,
        note=view.note,
        restorable=view.restorable,
        restorable_reason=view.restorable_reason,
    )


def _verification(view: VerificationView) -> VerificationSchema:
    return VerificationSchema(
        backup=_backup(view.backup), verified=view.verified, problems=list(view.problems)
    )


def _preview(view: RestorePreview) -> RestorePreviewSchema:
    return RestorePreviewSchema(
        backup=_backup(view.backup),
        can_restore=view.can_restore,
        blockers=list(view.blockers),
        missing_scope=list(view.missing_scope),
        free_bytes=view.free_bytes,
        needed_bytes=view.needed_bytes,
        targets=list(view.targets),
        previous_backup_note=view.previous_backup_note,
    )


def _result(view: RestoreResult) -> RestoreResultSchema:
    return RestoreResultSchema(
        backup_id=view.backup_id,
        previous_backup_id=view.previous_backup_id,
        restored=list(view.restored),
        rollback_paths=list(view.rollback_paths),
        schema_revision=view.schema_revision,
        health_ok=view.health_ok,
        health_detail=view.health_detail,
    )


@router.get(
    "/backups",
    response_model=BackupListSchema,
    responses=RESOURCE_ERRORS,
    summary="Copia de seguridad: listado, alta e identidad de cada copia",
)
def list_backups(service: BackupServiceDep) -> BackupListSchema:
    return BackupListSchema(backups=[_backup(copia) for copia in service.list()])


@router.post(
    "/backups",
    response_model=BackupSchema,
    status_code=201,
    responses=INGESTION_WRITE_ERRORS,
    summary="Hace una copia de seguridad del árbol de datos",
)
def create_backup(request: CreateBackupSchema, service: BackupServiceDep) -> BackupSchema:
    """Copia consistente de DB, artefactos, representaciones y fixtures, con manifiesto y hashes."""
    try:
        return _backup(service.create(note=request.note))
    except BackupError as error:
        raise InvalidStateError(str(error)) from error


@router.post(
    "/backups/{backup_id}/verify",
    response_model=VerificationSchema,
    responses=RESOURCE_ERRORS,
    summary="Verifica una copia entrada por entrada, sin escribir nada",
)
def verify_backup(backup_id: str, service: BackupServiceDep) -> VerificationSchema:
    informe = service.verify(backup_id)
    if informe is None:
        raise NotFoundError("copia de seguridad", backup_id)
    return _verification(informe)


@router.post(
    "/restore/validate",
    response_model=RestorePreviewSchema,
    responses=RESOURCE_ERRORS,
    summary="Previsualiza una restauración: valida, comprueba espacio y versión, y no escribe",
)
def validate_restore(
    request: RestoreRequestSchema, service: BackupServiceDep
) -> RestorePreviewSchema:
    vista = service.preview(request.backup_id)
    if vista is None:
        raise NotFoundError("copia de seguridad", request.backup_id)
    return _preview(vista)


@router.post(
    "/restore/execute",
    response_model=RestoreResultSchema,
    responses=INGESTION_WRITE_ERRORS,
    summary="Restaura una copia validada, con copia previa automática y deshacer si falla",
)
def execute_restore(
    request: RestoreRequestSchema, service: BackupServiceDep
) -> RestoreResultSchema:
    try:
        return _result(service.restore(request.backup_id, keep_rollback=request.keep_rollback))
    except BackupError as error:
        raise InvalidStateError(str(error)) from error
