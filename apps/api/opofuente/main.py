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
from opofuente.application.classification_service import ClassificationService
from opofuente.application.export_service import ExportService
from opofuente.application.extraction_service import ExtractionService
from opofuente.application.ingestion_service import IngestionService
from opofuente.application.intake_service import IntakeService
from opofuente.application.job_service import JobService
from opofuente.application.library_service import LibraryService
from opofuente.application.profiles_service import ProfilesService
from opofuente.application.question_service import QuestionService
from opofuente.application.review_service import ReviewService
from opofuente.application.search_service import SearchService
from opofuente.application.study_service import StudyService
from opofuente.application.system_service import SystemService
from opofuente.config import Settings, get_settings
from opofuente.domain.jobs import JobType
from opofuente.infrastructure.artifact_store import ArtifactStore
from opofuente.infrastructure.capabilities import (
    ConfigurationCapabilityProvider,
    IngestionCapabilityProvider,
    SqliteCapabilityProvider,
    VectorIndexCapabilityProvider,
)
from opofuente.infrastructure.classification_repository import SqlAlchemyClassificationRepository
from opofuente.infrastructure.classifiers import DeterministicClassifier
from opofuente.infrastructure.clock import SystemClock
from opofuente.infrastructure.db import build_engine, build_session_factory
from opofuente.infrastructure.document_repository import SqlAlchemyDocumentRepository
from opofuente.infrastructure.extraction_repository import SqlAlchemyExtractionRepository
from opofuente.infrastructure.extractors import ExtractorRegistry
from opofuente.infrastructure.filesystem_inventory import FilesystemInventory
from opofuente.infrastructure.ingestion_repository import SqlAlchemyIngestionRepository
from opofuente.infrastructure.job_repository import SqlAlchemyJobRepository
from opofuente.infrastructure.migrations import database_revision, script_head
from opofuente.infrastructure.observability import setup_logging
from opofuente.infrastructure.probes import DatabaseProbe, DataDirectoryProbe
from opofuente.infrastructure.profile_repository import SqlAlchemyProfileRepository
from opofuente.infrastructure.question_repository import SqlAlchemyQuestionRepository
from opofuente.infrastructure.representation_store import RepresentationStore
from opofuente.infrastructure.review_repository import SqlAlchemyReviewRepository
from opofuente.infrastructure.search_repository import SqlAlchemySearchRepository
from opofuente.infrastructure.study_repository import SqlAlchemyStudyRepository
from opofuente.infrastructure.url_guard import url_limits_from_settings
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
            VectorIndexCapabilityProvider(),
        ),
    )
    clock = SystemClock()
    profiles_service = ProfilesService(
        SqlAlchemyProfileRepository(session_factory),
        clock,
    )
    job_queue = SqlAlchemyJobRepository(session_factory)
    ingestion_repository = SqlAlchemyIngestionRepository(session_factory)
    artifact_store = ArtifactStore(paths)
    ingestion_service = IngestionService(
        repository=ingestion_repository,
        jobs=job_queue,
        store=artifact_store,
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
    extraction_service = ExtractionService(
        repository=SqlAlchemyExtractionRepository(session_factory),
        ingestions=ingestion_repository,
        store=artifact_store,
        representations=RepresentationStore(paths),
        registry=ExtractorRegistry(resolved),
        jobs=job_queue,
        clock=clock,
        data_root=paths.root,
        max_member_bytes=resolved.max_file_bytes,
    )
    intake_service = IntakeService(
        repository=ingestion_repository,
        jobs=job_queue,
        store=artifact_store,
        clock=clock,
        data_root=paths.root,
        max_file_bytes=resolved.max_file_bytes,
        max_paste_bytes=resolved.max_paste_bytes,
        url_limits=url_limits_from_settings(
            timeout_seconds=resolved.url_timeout_seconds,
            max_bytes=resolved.max_url_bytes,
            max_redirects=resolved.max_url_redirects,
        ),
    )
    job_service = JobService(job_queue, clock)
    representations = RepresentationStore(paths)
    classification_repository = SqlAlchemyClassificationRepository(session_factory, representations)
    classification_service = ClassificationService(
        repository=classification_repository,
        engines=(DeterministicClassifier(),),
        clock=clock,
    )
    library_service = LibraryService(
        documents=SqlAlchemyDocumentRepository(session_factory, representations),
        classifications=classification_repository,
        clock=clock,
    )
    question_service = QuestionService(
        questions=SqlAlchemyQuestionRepository(session_factory),
        clock=clock,
    )
    search_service = SearchService(
        search=SqlAlchemySearchRepository(session_factory),
        clock=clock,
    )
    review_service = ReviewService(
        reviews=SqlAlchemyReviewRepository(session_factory),
        clock=clock,
    )
    export_service = ExportService(
        questions=SqlAlchemyQuestionRepository(session_factory),
        documents=SqlAlchemyDocumentRepository(session_factory, representations),
        profiles=SqlAlchemyProfileRepository(session_factory),
        exports_dir=paths.exports,
        clock=clock,
        version=__version__,
    )
    study_service = StudyService(
        study=SqlAlchemyStudyRepository(session_factory),
        questions=SqlAlchemyQuestionRepository(session_factory),
        profiles=SqlAlchemyProfileRepository(session_factory),
        clock=clock,
        review=review_service,
    )
    worker = JobWorker(
        queue=job_queue,
        handlers={
            JobType.INGEST_BATCH: ingestion_service.run_import_job,
            JobType.EXTRACT_ARTIFACT: extraction_service.run_extraction_job,
            JobType.CLASSIFY_DOCUMENT: classification_service.run_classification_job,
        },
        # Un trabajo que se queda `failed` sin más reintentos tiene que cerrar el lote: si no, el
        # lote seguiría diciendo que trabaja mientras su trabajo ya no va a ejecutarse.
        on_failed={
            JobType.INGEST_BATCH: ingestion_service.on_job_failed,
            JobType.EXTRACT_ARTIFACT: ingestion_service.on_job_failed,
        },
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
    app.state.extraction_service = extraction_service
    app.state.intake_service = intake_service
    app.state.job_service = job_service
    app.state.classification_service = classification_service
    app.state.library_service = library_service
    app.state.artifact_store = artifact_store
    app.state.question_service = question_service
    app.state.study_service = study_service
    app.state.search_service = search_service
    app.state.review_service = review_service
    app.state.export_service = export_service

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
