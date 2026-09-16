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


class PasteRequest(BaseModel):
    """Texto pegado por el usuario (04_INGESTION §2)."""

    text: str = Field(min_length=1, max_length=2_000_000)
    title: str | None = Field(default=None, max_length=200)


class UrlRequest(BaseModel):
    """URL que se descargará con la guarda de red (09_SECURITY §4)."""

    url: str = Field(min_length=1, max_length=2048)


class RepresentationSourceSchema(BaseModel):
    """De qué entrada sale el texto, con **su** origen y su profundidad de contenedor.

    El origen se toma de la entrada, no del artefacto: unos mismos bytes pueden haber entrado como
    fichero, como texto pegado y como URL, y unirlos por artefacto atribuía a una entrada el origen
    de otra.
    """

    location: str
    """Procedencia mostrable: la ruta relativa del fichero, el título del texto pegado o la URL
    descargada **sin** cadena de consulta."""
    origin_type: str | None = None
    """`file`, `paste` o `url`. `null` en entradas anteriores a la corrección de S03."""
    depth: int = 0
    """Niveles de contenedor recorridos: 0 si vino del origen tal cual, 1 si salió de un ZIP."""


class RepresentationSchema(BaseModel):
    """Texto extraído de un artefacto, con quién lo extrajo, su calidad y sus avisos.

    El texto **no** viaja aquí: se lee por trozos en `/representations/{id}/text`, para que un
    documento largo no bloquee la interfaz.
    """

    id: str
    artifact_id: str
    kind: str
    status: str
    quality: str
    extractor: str
    char_count: int
    page_count: int | None = None
    language: str | None = None
    ocr_candidate: bool = False
    warnings: list[str] = Field(default_factory=list)
    has_text: bool = False
    created_at: datetime
    #: Entradas de las que sale este texto, en orden de entrada y sin repetir. Un mismo contenido
    #: copiado dos veces comparte representación y aparece aquí con sus dos procedencias.
    sources: list[RepresentationSourceSchema] = Field(default_factory=list)


class RepresentationTextSchema(BaseModel):
    """Trozo de texto pedido, con lo necesario para seguir leyendo y los avisos a la vista."""

    representation_id: str
    text: str
    offset: int
    limit: int
    total_chars: int
    truncated: bool
    quality: str
    warnings: list[str] = Field(default_factory=list)


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
