"""Arranque de la aplicación FastAPI.

Composición explícita: se construyen motor, sondas y proveedores de capacidades y se
inyectan en `app.state`, de modo que una prueba puede crear una aplicación completa
apuntando a un directorio temporal (nunca al directorio de datos real).
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import Engine

from opofuente import __version__
from opofuente.api import api_router
from opofuente.api.errors import register_exception_handlers
from opofuente.api.middleware import (
    CorrelationIdMiddleware,
    OriginCheckMiddleware,
    SecurityHeadersMiddleware,
)
from opofuente.api.openapi import apply_problem_media_type
from opofuente.application.ingestion_service import IngestionService
from opofuente.application.job_service import JobService
from opofuente.application.profiles_service import ProfilesService
from opofuente.application.system_service import SystemService
from opofuente.config import Settings, get_settings
from opofuente.domain.jobs import JobType
from opofuente.infrastructure.artifact_store import ArtifactStore
from opofuente.infrastructure.capabilities import (
    ConfigurationCapabilityProvider,
    IngestionCapabilityProvider,
    PlannedCapabilityProvider,
    SqliteCapabilityProvider,
)
from opofuente.infrastructure.clock import SystemClock
from opofuente.infrastructure.db import build_engine, build_session_factory
from opofuente.infrastructure.filesystem_inventory import FilesystemInventory
from opofuente.infrastructure.ingestion_repository import SqlAlchemyIngestionRepository
from opofuente.infrastructure.job_repository import SqlAlchemyJobRepository
from opofuente.infrastructure.migrations import database_revision, script_head
from opofuente.infrastructure.observability import setup_logging
from opofuente.infrastructure.probes import DatabaseProbe, DataDirectoryProbe
from opofuente.infrastructure.profile_repository import SqlAlchemyProfileRepository
from opofuente.infrastructure.worker_liveness import WorkerLiveness
from opofuente.workers.job_worker import JobWorker

logger = logging.getLogger(__name__)

API_PREFIX = "/api/v1"

DESCRIPTION = (
    "API local de OpoFuente. Escucha solo en loopback y no tiene autenticación: es una "
    "aplicación de un único usuario. Ninguna respuesta contiene claves ni contenido privado "
    "en logs. Especificación en docs/product-spec."
)


def _database_is_migrated(engine: Engine, settings: Settings) -> bool:
    """¿Está la base de datos en la revisión de cabeza? Si no, el worker no arranca."""
    expected = script_head(settings)
    return expected is not None and database_revision(engine) == expected


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved = settings or get_settings()
    paths = resolved.data_paths
    engine = build_engine(paths.database)
    session_factory = build_session_factory(engine)

    worker_liveness = WorkerLiveness()
    system_service = SystemService(
        version=__version__,
        probes=(
            DatabaseProbe(session_factory, expected_revision=script_head(resolved)),
            DataDirectoryProbe(paths),
        ),
        capability_providers=(
            ConfigurationCapabilityProvider(resolved),
            SqliteCapabilityProvider(engine),
            IngestionCapabilityProvider(
                paths=paths,
                settings=resolved,
                liveness=worker_liveness,
            ),
            PlannedCapabilityProvider(),
        ),
    )
    clock = SystemClock()
    profiles_service = ProfilesService(
        SqlAlchemyProfileRepository(session_factory),
        clock,
    )
    job_queue = SqlAlchemyJobRepository(session_factory)
    ingestion_repository = SqlAlchemyIngestionRepository(session_factory)
    ingestion_service = IngestionService(
        repository=ingestion_repository,
        jobs=job_queue,
        store=ArtifactStore(paths),
        scanner=FilesystemInventory(
            max_file_bytes=resolved.max_file_bytes,
            max_entries=resolved.max_batch_entries,
            forbidden_roots=(paths.root,),
        ),
        clock=clock,
        data_root=paths.root,
        max_entries=resolved.max_batch_entries,
        # El lease se renueva a un tercio de su vida: margen de sobra para un fichero lento.
        heartbeat_seconds=max(resolved.job_lease_seconds / 3, 2.0),
    )
    job_service = JobService(job_queue, clock)
    worker = JobWorker(
        queue=job_queue,
        handlers={JobType.INGEST_BATCH: ingestion_service.run_import_job},
        # Un trabajo que se queda `failed` sin más reintentos tiene que cerrar el lote: si no, el
        # lote seguiría diciendo que trabaja mientras su trabajo ya no va a ejecutarse.
        on_failed={JobType.INGEST_BATCH: ingestion_service.on_job_failed},
        clock=clock,
        lease_seconds=resolved.job_lease_seconds,
        poll_seconds=resolved.worker_poll_seconds,
        liveness=worker_liveness,
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
        worker_task: asyncio.Task[None] | None = None
        if resolved.worker_enabled and _database_is_migrated(engine, resolved):
            # Un reinicio recupera los trabajos interrumpidos antes de aceptar trabajo nuevo.
            worker_task = asyncio.create_task(worker.run_forever(), name="opofuente-worker")
            # No se atiende ninguna petición hasta que el worker ha arrancado de verdad: así
            # /capabilities no declara operativa una cola que todavía nadie está trabajando.
            await worker.wait_started()
        elif resolved.worker_enabled:
            logger.warning(
                "opofuente.worker_skipped reinicia después de migrar la base de datos",
                extra={"event": "worker_skipped"},
            )
        try:
            yield
        finally:
            if worker_task is not None:
                worker.stop()
                with suppress(asyncio.CancelledError, TimeoutError):
                    await asyncio.wait_for(worker_task, timeout=5)
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
    app.state.profiles_service = profiles_service
    app.state.ingestion_service = ingestion_service
    app.state.job_service = job_service

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
    # El esquema se genera una vez y se ajusta: los errores se sirven como
    # application/problem+json, no como application/json (api/openapi.py).
    app.openapi_schema = apply_problem_media_type(app.openapi())
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
