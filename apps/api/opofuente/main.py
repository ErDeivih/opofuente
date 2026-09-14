"""Arranque de la aplicación FastAPI.

Composición explícita: se construyen motor, sondas y proveedores de capacidades y se
inyectan en `app.state`, de modo que una prueba puede crear una aplicación completa
apuntando a un directorio temporal (nunca al directorio de datos real).
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from opofuente import __version__
from opofuente.api import api_router
from opofuente.api.errors import register_exception_handlers
from opofuente.api.middleware import (
    CorrelationIdMiddleware,
    OriginCheckMiddleware,
    SecurityHeadersMiddleware,
)
from opofuente.application.system_service import SystemService
from opofuente.config import Settings, get_settings
from opofuente.infrastructure.capabilities import (
    ConfigurationCapabilityProvider,
    PlannedCapabilityProvider,
    SqliteCapabilityProvider,
)
from opofuente.infrastructure.db import build_engine, build_session_factory
from opofuente.infrastructure.migrations import script_head
from opofuente.infrastructure.observability import setup_logging
from opofuente.infrastructure.probes import DatabaseProbe, DataDirectoryProbe

logger = logging.getLogger(__name__)

API_PREFIX = "/api/v1"

DESCRIPTION = (
    "API local de OpoFuente. Escucha solo en loopback y no tiene autenticación: es una "
    "aplicación de un único usuario. Ninguna respuesta contiene claves ni contenido privado "
    "en logs. Especificación en docs/product-spec."
)


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved = settings or get_settings()
    paths = resolved.data_paths
    engine = build_engine(paths.database)
    session_factory = build_session_factory(engine)

    system_service = SystemService(
        version=__version__,
        probes=(
            DatabaseProbe(session_factory, expected_revision=script_head(resolved)),
            DataDirectoryProbe(paths),
        ),
        capability_providers=(
            ConfigurationCapabilityProvider(resolved),
            SqliteCapabilityProvider(engine),
            PlannedCapabilityProvider(),
        ),
    )

    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
        paths.ensure_directories()
        setup_logging(resolved)
        logger.info(
            "opofuente.startup host=%s port=%s log_level=%s",
            resolved.host,
            resolved.port,
            resolved.log_level,
            extra={"event": "startup"},
        )
        try:
            yield
        finally:
            engine.dispose()
            logger.info("opofuente.shutdown", extra={"event": "shutdown"})

    app = FastAPI(
        title="OpoFuente API",
        version=__version__,
        description=DESCRIPTION,
        openapi_url=f"{API_PREFIX}/openapi.json",
        docs_url=f"{API_PREFIX}/docs",
        redoc_url=None,
        lifespan=lifespan,
    )

    app.state.settings = resolved
    app.state.engine = engine
    app.state.session_factory = session_factory
    app.state.system_service = system_service

    # El orden importa: el último añadido es el más externo, así que el identificador de
    # correlación envuelve también los rechazos por Origin.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(resolved.cors_origins),
        allow_credentials=False,
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Idempotency-Key", "X-Correlation-ID"],
        expose_headers=["X-Correlation-ID"],
    )
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(OriginCheckMiddleware, allowed_origins=resolved.cors_origins)
    app.add_middleware(CorrelationIdMiddleware)

    app.include_router(api_router, prefix=API_PREFIX)
    register_exception_handlers(app)
    return app


app = create_app()


def main() -> None:
    """Arranque por consola: `python -m opofuente.main` o el script `opofuente`."""
    import uvicorn

    settings = get_settings()
    settings.data_paths.ensure_directories()
    uvicorn.run(
        "opofuente.main:app",
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
