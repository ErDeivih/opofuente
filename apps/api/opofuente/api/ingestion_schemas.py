"""DTO de ingestión y trabajos (08_API-CONTRACT §4 y §5).

La ruta real de la carpeta de origen (`source_root`) **no** se publica nunca: la API devuelve
`source_path_display`, que es la versión abreviada. Los contadores viajan como diccionarios porque
cada tipo de lote tiene los suyos y el contrato los documenta por separado.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from opofuente.domain.ingestion import BatchStatus, ItemStatus


class EntrySchema(BaseModel):
    id: str
    relative_path: str
    original_name: str
    size_bytes: int
    media_type: str | None = None
    status: ItemStatus
    detail: str | None = None
    artifact_sha256: str | None = None


class IssueSchema(BaseModel):
    code: str
    severity: Literal["info", "warning", "error"]
    safe_message: str
    relative_path: str | None = None
    details: dict[str, object] = Field(default_factory=dict)


class BatchSchema(BaseModel):
    id: str
    kind: Literal["inventory", "import"]
    mode: Literal["read_only", "copy"]
    status: BatchStatus
    source_path_display: str
    counters: dict[str, int]
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    job_id: str | None = None
    inventory_batch_id: str | None = None
    manifest_hash: str | None = None
    error_summary: str | None = None
    formats: dict[str, int] = Field(default_factory=dict)
    issue_counts: dict[str, int] = Field(default_factory=dict)
    total_items: int = 0


class InventorySchema(BaseModel):
    """Respuesta de un inventario: qué hay y qué se omite, sin haber copiado nada."""

    batch: BatchSchema
    sample: list[EntrySchema]
    issues: list[IssueSchema]
    copied_anything: Literal[False] = False
    note: str = (
        "OpoFuente ha leído la carpeta sin modificarla. No se ha copiado ni movido nada todavía."
    )


class CreateInventoryRequest(BaseModel):
    source_path: str = Field(min_length=1, max_length=4096)


class BatchDetailSchema(BaseModel):
    batch: BatchSchema
    entries: list[EntrySchema]
    issues: list[IssueSchema]
    report: ImportReportSchema


class ImportReportSchema(BaseModel):
    """Informe del lote. Los contadores deben cuadrar (total = copiadas + fallidas + omitidas)."""

    batch_id: str
    kind: Literal["inventory", "import"]
    status: BatchStatus
    counters: dict[str, int]
    issue_counts: dict[str, int]
    balanced: bool
    artifacts_total: int
    generated_at: datetime


class EntryPageSchema(BaseModel):
    entries: list[EntrySchema]
    total: int
    limit: int
    offset: int


class IssuePageSchema(BaseModel):
    issues: list[IssueSchema]
    total: int
    limit: int
    offset: int


class JobSchema(BaseModel):
    id: str
    job_type: str
    status: str
    progress: float
    attempts: int
    max_attempts: int
    created_at: datetime
    updated_at: datetime
    step: str | None = None
    error_code: str | None = None
    error_message: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    cancel_requested: bool = False


BatchDetailSchema.model_rebuild()
