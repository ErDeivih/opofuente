"""DTO de higiene del almacén, diagnóstico y reindexación (07_UI-UX §11, DEBT-007 y DEBT-015)."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class AreaUsageSchema(BaseModel):
    """Lo que ocupa un área del árbol de datos. `readable=False` significa «no se ha podido medir»,
    que no es lo mismo que cero."""

    area: str
    path_display: str
    size_bytes: int
    file_count: int
    readable: bool
    note: str | None = None


class HousekeepingCandidateSchema(BaseModel):
    """Algo que se puede retirar, con su motivo y su tamaño. La pantalla lo enseña **antes**."""

    action: str
    reference: str
    detail: str
    size_bytes: int
    display: str


class HousekeepingReportSchema(BaseModel):
    usage: list[AreaUsageSchema]
    candidates: list[HousekeepingCandidateSchema]
    retention_days: int
    total_bytes: int
    reclaimable_bytes: int


class PurgeRequestSchema(BaseModel):
    """Qué retirar y con qué confirmación.

    `confirm` es obligatorio y tiene que ser `true`: retirar material es una decisión, y el contrato
    pide que no pueda ocurrir por accidente. Se exige en el **mismo** cuerpo que las referencias,
    no en un segundo parámetro, para que no haya dos formas de pedir lo mismo.
    """

    model_config = ConfigDict(extra="forbid")

    #: Qué retirar. Sin lista, todo lo que la foto propone para esa acción (nunca más que eso).
    references: list[str] | None = None
    confirm: bool = Field(description="debe ser `true`: retirar material no se hace por accidente")


class PurgeResultSchema(BaseModel):
    action: str
    removed: int
    freed_bytes: int
    skipped: list[str]
    detail: str


class HousekeepingStatusSchema(BaseModel):
    """Estado del almacén y de la cola: lo que Ajustes enseña sin tener que mirar el disco."""

    schema_revision: str
    database_size_bytes: int
    artifacts: int
    jobs_pending: int
    evidence_spans: int
    questions: int
    study_sessions: int
    rag_queries: int
    learning_errors: int
    change_sets: int
    fts_indexed: int
    fts_ready: bool
    fts_detail: str
    missing_index_entries: int


class IndexHealthSchema(BaseModel):
    """Si el índice léxico está completo. Cuando faltan fragmentos, se dice cuántos."""

    healthy: bool
    detail: str
    missing_entries: int


class ReindexSchema(BaseModel):
    """Resultado de rehacer el índice léxico (DEBT-015)."""

    indexed: int
    before: int
    after: int
    took_seconds: float
    detail: str


__all__ = [
    "AreaUsageSchema",
    "HousekeepingCandidateSchema",
    "HousekeepingReportSchema",
    "HousekeepingStatusSchema",
    "IndexHealthSchema",
    "PurgeRequestSchema",
    "PurgeResultSchema",
    "ReindexSchema",
]
