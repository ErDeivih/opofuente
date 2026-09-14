"""DTO de la API. Traducen objetos de dominio a JSON del contrato."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from opofuente.domain.system import CapabilityStatus


class LiveSchema(BaseModel):
    status: Literal["alive"] = "alive"
    version: str


class CheckSchema(BaseModel):
    name: str
    status: Literal["ok", "failed"]
    detail: str


class ReadinessSchema(BaseModel):
    status: Literal["ready", "degraded"]
    checks: list[CheckSchema]


class CapabilitySchema(BaseModel):
    id: str
    label: str
    status: CapabilityStatus
    detail: str
    planned_slice: str | None = None


class DegradationSchema(BaseModel):
    code: str
    message: str


class CapabilitiesSchema(BaseModel):
    version: str
    capabilities: list[CapabilitySchema]
    degradations: list[DegradationSchema]


class LlmSettingsSchema(BaseModel):
    provider: str
    model: str | None = None
    base_url_configured: bool
    api_key_configured: bool
    sends_data_off_device: bool


class EmbeddingSettingsSchema(BaseModel):
    provider: str
    model: str | None = None


class OcrSettingsSchema(BaseModel):
    tesseract_configured: bool
    tesseract_available: bool


class SettingsSchema(BaseModel):
    """Configuración efectiva sanitizada. Nunca incluye secretos."""

    version: str
    host: str
    port: int
    log_level: str
    data_dir: str
    database_file: str
    disk_total_bytes: int
    disk_free_bytes: int
    cors_origins: list[str]
    llm: LlmSettingsSchema
    embeddings: EmbeddingSettingsSchema
    ocr: OcrSettingsSchema
    editable: bool
    """False mientras no exista almacén de ajustes persistido (slice posterior)."""
