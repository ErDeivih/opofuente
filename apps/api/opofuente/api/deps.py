"""Dependencias de FastAPI.

El estado vive en `app.state` (no en un singleton global) para que las pruebas puedan
construir aplicaciones con configuración temporal sin tocar el directorio de datos real.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Request

from opofuente.application.ingestion_service import IngestionService
from opofuente.application.job_service import JobService
from opofuente.application.profiles_service import ProfilesService
from opofuente.application.system_service import SystemService
from opofuente.config import Settings


def get_app_settings(request: Request) -> Settings:
    settings: Settings = request.app.state.settings
    return settings


def get_system_service(request: Request) -> SystemService:
    service: SystemService = request.app.state.system_service
    return service


def get_profiles_service(request: Request) -> ProfilesService:
    service: ProfilesService = request.app.state.profiles_service
    return service


def get_ingestion_service(request: Request) -> IngestionService:
    service: IngestionService = request.app.state.ingestion_service
    return service


def get_job_service(request: Request) -> JobService:
    service: JobService = request.app.state.job_service
    return service


#: Dependencias anotadas (estilo moderno de FastAPI: sin llamadas en valores por defecto).
AppSettingsDep = Annotated[Settings, Depends(get_app_settings)]
SystemServiceDep = Annotated[SystemService, Depends(get_system_service)]
ProfilesServiceDep = Annotated[ProfilesService, Depends(get_profiles_service)]
IngestionServiceDep = Annotated[IngestionService, Depends(get_ingestion_service)]
JobServiceDep = Annotated[JobService, Depends(get_job_service)]
