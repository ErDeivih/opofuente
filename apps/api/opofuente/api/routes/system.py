"""Rutas de sistema: salud, capacidades y configuración sanitizada.

No contienen reglas de negocio (02_ARCHITECTURE §3: la capa API no decide).
"""

from __future__ import annotations

import shutil

from fastapi import APIRouter, Response
from fastapi.responses import JSONResponse, PlainTextResponse

from opofuente import __version__
from opofuente.api.deps import AppSettingsDep, DiagnosticServiceDep, SystemServiceDep
from opofuente.api.error_responses import BASE_ERRORS
from opofuente.api.errors import problem_response_from
from opofuente.api.schemas import (
    CapabilitiesSchema,
    CapabilitySchema,
    CheckSchema,
    DegradationSchema,
    DiagnosticSchema,
    EmbeddingSettingsSchema,
    LimitsSchema,
    LiveSchema,
    LlmSettingsSchema,
    OcrSettingsSchema,
    ReadinessProblem,
    ReadinessSchema,
    SettingsSchema,
)
from opofuente.config import Settings as AppSettings
from opofuente.config import project_root
from opofuente.domain.providers import classify_provider, sends_content_off_device

router = APIRouter()

INTERNAL_ERROR_RESPONSE = BASE_ERRORS


@router.get(
    "/health/live",
    response_model=LiveSchema,
    responses=INTERNAL_ERROR_RESPONSE,
    summary="Proceso vivo",
)
def live() -> LiveSchema:
    """No comprueba dependencias: solo que el proceso responde."""
    return LiveSchema(version=__version__)


@router.get(
    "/health/ready",
    response_model=ReadinessSchema,
    responses={
        **INTERNAL_ERROR_RESPONSE,
        503: {
            # El esquema se documenta bajo application/problem+json (api/openapi.py).
            "model": ReadinessProblem,
            "description": (
                "Alguna dependencia no está lista. Cuerpo RFC 9457 (`ReadinessProblem`) con "
                "`checks`: el detalle de cada comprobación."
            ),
        },
    },
    summary="Listo para servir (comprueba la base de datos)",
)
def ready(service: SystemServiceDep) -> Response:
    report = service.readiness()
    checks = [
        CheckSchema(name=check.name, status=check.status.value, detail=check.detail)
        for check in report.checks
    ]
    if report.ready:
        payload = ReadinessSchema(status="ready", checks=checks)
        return JSONResponse(status_code=200, content=payload.model_dump(mode="json"))
    return problem_response_from(
        ReadinessProblem(
            title="Service Unavailable",
            status=503,
            detail="La aplicación no está lista.",
            instance="/api/v1/health/ready",
            code="not_ready",
            correlation_id="",
            checks=checks,
        )
    )


@router.get(
    "/capabilities",
    response_model=CapabilitiesSchema,
    responses=INTERNAL_ERROR_RESPONSE,
    summary="Capacidades reales y degradaciones",
)
def capabilities(service: SystemServiceDep) -> CapabilitiesSchema:
    report = service.capabilities()
    return CapabilitiesSchema(
        version=report.version,
        capabilities=[
            CapabilitySchema(
                id=capability.id,
                label=capability.label,
                status=capability.status,
                detail=capability.detail,
                planned_slice=capability.planned_slice,
            )
            for capability in report.capabilities
        ],
        degradations=[
            DegradationSchema(code=degradation.code, message=degradation.message)
            for degradation in report.degradations
        ],
    )


@router.get(
    "/settings",
    response_model=SettingsSchema,
    responses=INTERNAL_ERROR_RESPONSE,
    summary="Configuración efectiva sanitizada (sin secretos)",
)
def read_settings(settings: AppSettingsDep) -> SettingsSchema:
    """Configuración efectiva, **con el destino real de cada proveedor** (DEBT-001).

    Cada proveedor se clasifica por separado sobre su endpoint efectivo: antes el proveedor de
    embeddings se informaba dentro del bloque de LLM, y un endpoint local contaba como que salía del
    equipo. Un destino `unknown` viaja como tal y cuenta como que sí sale.
    """
    paths = settings.data_paths
    base = paths.root if paths.root.exists() else project_root()
    usage = shutil.disk_usage(base)
    tesseract_path = settings.tesseract_path
    llm_destino = classify_provider(
        name="el modelo de lenguaje",
        provider=settings.llm_provider,
        endpoint=settings.llm_base_url,
    )
    embeddings_destino = classify_provider(
        name="el proveedor de embeddings",
        provider=settings.embedding_provider,
        endpoint=settings.embedding_base_url,
    )
    return SettingsSchema(
        version=__version__,
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level,
        # La pantalla de Ajustes debe mostrar la ruta de datos (07_UI-UX §11).
        data_dir=str(paths.root),
        database_file=str(paths.database),
        disk_total_bytes=usage.total,
        disk_free_bytes=usage.free,
        cors_origins=list(settings.cors_origins),
        llm=LlmSettingsSchema(
            provider=settings.llm_provider,
            model=settings.llm_model,
            base_url_configured=bool(settings.llm_base_url),
            api_key_configured=settings.llm_api_key_configured,
            sends_data_off_device=sends_content_off_device(llm_destino),
            destination=llm_destino.destination.value,
            destination_reason=llm_destino.reason,
        ),
        embeddings=EmbeddingSettingsSchema(
            provider=settings.embedding_provider,
            model=settings.embedding_model,
            base_url_configured=bool(settings.embedding_base_url),
            destination=embeddings_destino.destination.value,
            destination_reason=embeddings_destino.reason,
        ),
        ocr=OcrSettingsSchema(
            tesseract_configured=tesseract_path is not None,
            tesseract_available=tesseract_path is not None and tesseract_path.is_file(),
        ),
        limits=_limits(settings),
        editable=False,
    )


@router.get(
    "/diagnostics",
    response_model=DiagnosticSchema,
    responses=INTERNAL_ERROR_RESPONSE,
    summary="Diagnóstico sanitizado para pegar en una incidencia (sin secretos ni contenido)",
)
def diagnostics(service: DiagnosticServiceDep, settings: AppSettingsDep) -> DiagnosticSchema:
    """Versiones, capacidades, salud, recuentos, límites y el final del registro, todo saneado.

    No es un volcado: es lo que hace falta para juzgar el estado sin publicar nada del usuario. Las
    rutas van abreviadas y cada línea del registro pasa por el saneado de secretos y rutas.
    """
    informe = service.report()
    return DiagnosticSchema(
        generated_at=informe.generated_at,
        version=informe.version,
        schema_revision=informe.schema_revision,
        python_version=informe.python_version,
        platform=informe.platform,
        host=informe.host,
        port=informe.port,
        log_level=informe.log_level,
        data_dir_display=informe.data_dir_display,
        database_file_display=informe.database_file_display,
        disk_total_bytes=informe.disk_total_bytes,
        disk_free_bytes=informe.disk_free_bytes,
        counts=informe.counts,
        capabilities=[
            CapabilitySchema(
                id=capability.id,
                label=capability.label,
                status=capability.status,
                detail=capability.detail,
                planned_slice=capability.planned_slice,
            )
            for capability in informe.capabilities.capabilities
        ],
        degradations=[
            DegradationSchema(code=degradation.code, message=degradation.message)
            for degradation in informe.capabilities.degradations
        ],
        checks=[
            CheckSchema(name=check.name, status=check.status.value, detail=check.detail)
            for check in informe.readiness.checks
        ],
        limits=_limits(settings),
        log_tail=list(informe.log_tail),
        note=informe.note,
    )


def _limits(settings: AppSettings) -> LimitsSchema:
    """Límites efectivos. Una sola función para `/settings` y `/diagnostics`: los mismos números."""
    return LimitsSchema(
        max_file_bytes=settings.max_file_bytes,
        max_batch_entries=settings.max_batch_entries,
        max_url_bytes=settings.max_url_bytes,
        max_url_redirects=settings.max_url_redirects,
        max_paste_bytes=settings.max_paste_bytes,
        max_zip_entries=settings.max_zip_entries,
        max_zip_uncompressed_bytes=settings.max_zip_uncompressed_bytes,
        max_zip_ratio=settings.max_zip_ratio,
        max_zip_depth=settings.max_zip_depth,
        max_pdf_pages=settings.max_pdf_pages,
        max_representation_chars=settings.max_representation_chars,
        worker_poll_seconds=settings.worker_poll_seconds,
        job_lease_seconds=settings.job_lease_seconds,
    )


@router.get(
    "/diagnostics/text",
    response_class=PlainTextResponse,
    responses=INTERNAL_ERROR_RESPONSE,
    summary="El mismo diagnóstico en texto plano, para copiar y pegar",
)
def diagnostics_text(service: DiagnosticServiceDep) -> PlainTextResponse:
    return PlainTextResponse(service.as_text(), media_type="text/plain; charset=utf-8")
