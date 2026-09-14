"""Rutas de sistema: salud, capacidades y configuración sanitizada.

No contienen reglas de negocio (02_ARCHITECTURE §3: la capa API no decide).
"""

from __future__ import annotations

import shutil

from fastapi import APIRouter, Response
from fastapi.responses import JSONResponse

from opofuente import __version__
from opofuente.api.deps import AppSettingsDep, SystemServiceDep
from opofuente.api.errors import PROBLEM_MEDIA_TYPE, ProblemDetail, problem_response
from opofuente.api.schemas import (
    CapabilitiesSchema,
    CapabilitySchema,
    CheckSchema,
    DegradationSchema,
    EmbeddingSettingsSchema,
    LiveSchema,
    LlmSettingsSchema,
    OcrSettingsSchema,
    ReadinessSchema,
    SettingsSchema,
)
from opofuente.config import project_root

router = APIRouter()


@router.get("/health/live", response_model=LiveSchema, summary="Proceso vivo")
def live() -> LiveSchema:
    """No comprueba dependencias: solo que el proceso responde."""
    return LiveSchema(version=__version__)


@router.get(
    "/health/ready",
    response_model=ReadinessSchema,
    responses={
        503: {
            "model": ProblemDetail,
            "description": "Alguna dependencia no está lista; incluye `checks` como extensión.",
            "content": {PROBLEM_MEDIA_TYPE: {}},
        }
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
    return problem_response(
        status_code=503,
        detail="La aplicación no está lista.",
        instance="/api/v1/health/ready",
        code="not_ready",
        extra_body={"checks": [check.model_dump(mode="json") for check in checks]},
    )


@router.get(
    "/capabilities",
    response_model=CapabilitiesSchema,
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
    summary="Configuración efectiva sanitizada (sin secretos)",
)
def read_settings(settings: AppSettingsDep) -> SettingsSchema:
    paths = settings.data_paths
    base = paths.root if paths.root.exists() else project_root()
    usage = shutil.disk_usage(base)
    tesseract_path = settings.tesseract_path
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
            sends_data_off_device=settings.sends_data_off_device,
        ),
        embeddings=EmbeddingSettingsSchema(
            provider=settings.embedding_provider,
            model=settings.embedding_model,
        ),
        ocr=OcrSettingsSchema(
            tesseract_configured=tesseract_path is not None,
            tesseract_available=tesseract_path is not None and tesseract_path.is_file(),
        ),
        editable=False,
    )
