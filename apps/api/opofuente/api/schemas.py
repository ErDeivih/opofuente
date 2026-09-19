"""DTO de la API. Traducen objetos de dominio a JSON del contrato."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from opofuente.api.errors import ProblemDetail
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


class ReadinessProblem(ProblemDetail):
    """Cuerpo del 503 de `/health/ready`.

    Es un problema RFC 9457 al que se añade el detalle de cada comprobación, de modo que la
    interfaz pueda explicar **por qué** la aplicación no está lista sin abrir otra petición.
    Se declara como esquema propio para que `application/problem+json` esté descrito de verdad
    en OpenAPI y el frontend use el tipo generado (no una conversión escrita a mano).
    """

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
    #: Destino real del proveedor, calculado sobre el endpoint efectivo (DEBT-001): `disabled`,
    #: `local`, `remote` o `unknown`. El booleano de arriba se mantiene porque el contrato lo
    #: publica, pero deja de ser la única respuesta: `unknown` cuenta como que sí sale.
    destination: Literal["disabled", "local", "remote", "unknown"]
    destination_reason: str


class EmbeddingSettingsSchema(BaseModel):
    provider: str
    model: str | None = None
    #: El proveedor de embeddings tiene **su** clasificación: antes se informaba dentro del bloque
    #: de LLM, que es exactamente el defecto que registró DEBT-001.
    base_url_configured: bool = False
    destination: Literal["disabled", "local", "remote", "unknown"] = "disabled"
    destination_reason: str = "sin proveedor de embeddings configurado"


class OcrSettingsSchema(BaseModel):
    tesseract_configured: bool
    tesseract_available: bool


class LimitsSchema(BaseModel):
    """Límites efectivos de la configuración (07_UI-UX §11: «límites» en Ajustes).

    Se publican para que la pantalla pueda decir con qué topes trabaja el programa sin que nadie
    tenga que leer el código, y para que un fallo por tamaño tenga una cifra que enseñar.
    """

    max_file_bytes: int
    max_batch_entries: int
    max_url_bytes: int
    max_url_redirects: int
    max_paste_bytes: int
    max_zip_entries: int
    max_zip_uncompressed_bytes: int
    max_zip_ratio: int
    max_zip_depth: int
    max_pdf_pages: int
    max_representation_chars: int
    worker_poll_seconds: float
    job_lease_seconds: int


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
    limits: LimitsSchema
    editable: bool
    """False mientras no exista almacén de ajustes persistido (slice posterior)."""


class DiagnosticSchema(BaseModel):
    """Diagnóstico sanitizado (09_SECURITY §12): sin secretos, sin contenido y sin rutas completas.

    Es lo que se puede pegar en una incidencia. Lleva **lo que hace falta para juzgar el estado** y
    nada de lo que el usuario tiene dentro: ni una ruta absoluta, ni un enunciado, ni una clave.
    """

    generated_at: str
    version: str
    schema_revision: str
    python_version: str
    platform: str
    host: str
    port: int
    log_level: str
    data_dir_display: str
    database_file_display: str
    disk_total_bytes: int
    disk_free_bytes: int
    counts: dict[str, int]
    capabilities: list[CapabilitySchema]
    degradations: list[DegradationSchema]
    checks: list[CheckSchema]
    limits: LimitsSchema
    log_tail: list[str]
    note: str
