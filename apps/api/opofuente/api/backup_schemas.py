"""DTO de copia, verificación y restauración (08_API-CONTRACT §11)."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class BackupSchema(BaseModel):
    """Una copia tal como se enseña: identidad, tamaño y si se puede restaurar aquí y ahora."""

    id: str
    created_at: str
    app_version: str
    schema_revision: str
    scope: list[str]
    size_bytes: int
    file_count: int
    note: str | None = None
    #: Nunca se dice «restaurable» sin motivo: el motivo viaja siempre, también cuando es «sí».
    restorable: bool
    restorable_reason: str


class BackupListSchema(BaseModel):
    backups: list[BackupSchema]


class CreateBackupSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    note: str | None = Field(default=None, max_length=500)


class VerificationSchema(BaseModel):
    backup: BackupSchema
    verified: bool
    problems: list[str]


class RestorePreviewSchema(BaseModel):
    """Lo que una restauración haría **antes** de hacerlo: es el paso 1 y 2 del contrato."""

    backup: BackupSchema
    can_restore: bool
    blockers: list[str]
    missing_scope: list[str]
    free_bytes: int
    needed_bytes: int
    targets: list[str]
    previous_backup_note: str


class RestoreRequestSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    backup_id: str = Field(min_length=1, max_length=64)
    #: Pide dejar los puntos de retorno aunque la restauración termine bien. Sirve para inspeccionar
    #: el estado anterior después; por defecto se retiran, porque dejarlos ocupa el doble de disco.
    keep_rollback: bool = False


class RestoreResultSchema(BaseModel):
    backup_id: str
    previous_backup_id: str
    restored: list[str]
    rollback_paths: list[str]
    schema_revision: str
    health_ok: bool
    health_detail: str


__all__ = [
    "BackupListSchema",
    "BackupSchema",
    "CreateBackupSchema",
    "RestorePreviewSchema",
    "RestoreRequestSchema",
    "RestoreResultSchema",
    "VerificationSchema",
]
