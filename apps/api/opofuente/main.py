"""Arranque de la aplicación FastAPI.

Composición explícita: se construyen motor, sondas y proveedores de capacidades y se
inyectan en `app.state`, de modo que una prueba puede crear una aplicación completa
apuntando a un directorio temporal (nunca al directorio de datos real).
"""

from __future__ import annotations

import asyncio
import logging
import os
import shutil
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, suppress
from datetime import UTC, datetime
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import Engine

from opofuente import __version__
from opofuente.api import api_router
from opofuente.api.errors import register_exception_handlers
from opofuente.api.middleware import (
    CorrelationIdMiddleware,
    OriginCheckMiddleware,
    ProblemErrorMiddleware,
    SecurityHeadersMiddleware,
)
from opofuente.api.openapi import apply_problem_media_type
from opofuente.api.session_gate import SessionGateMiddleware
from opofuente.application.accounts_service import AccountsService
from opofuente.application.analytics_service import AnalyticsService
from opofuente.application.auto_study_service import AutoStudyService
from opofuente.application.backup_service import BackupService
from opofuente.application.card_service import CardService
from opofuente.application.change_service import ChangeService
from opofuente.application.classification_service import ClassificationService
from opofuente.application.diagnostic_service import DiagnosticService
from opofuente.application.dossier_service import DossierService
from opofuente.application.explicaciones import ExplanationProposer
from opofuente.application.export_service import ExportService
from opofuente.application.extraction_service import ExtractionService
from opofuente.application.housekeeping_service import HousekeepingService
from opofuente.application.ingestion_service import IngestionService
from opofuente.application.intake_service import IntakeService
from opofuente.application.job_service import JobService
from opofuente.application.legal_service import LegalService
from opofuente.application.library_service import LibraryService
from opofuente.application.notes_incident_service import NotesIncidentsService
from opofuente.application.notes_report_service import NotesReportsService
from opofuente.application.notes_review_service import MedidaSinModelo, NotesReviewService
from opofuente.application.plan_service import PlanService
from opofuente.application.profiles_service import ProfilesService
from opofuente.application.question_file_service import QuestionFileService
from opofuente.application.question_service import QuestionService
from opofuente.application.readiness_service import ReadinessService
from opofuente.application.review_service import ReviewService
from opofuente.application.search_service import SearchService
from opofuente.application.student_service import StudentService
from opofuente.application.study_service import StudyService
from opofuente.application.system_service import SystemService
from opofuente.application.topic_notes_service import TopicNotesService
from opofuente.config import Settings, get_settings, resolve_tmp_directory
from opofuente.domain.errors import ConfigurationError
from opofuente.domain.jobs import JobType
from opofuente.infrastructure.account_repository import SqlAlchemyAccountRepository
from opofuente.infrastructure.analytics_repository import SqlAlchemyAnalyticsRepository
from opofuente.infrastructure.artifact_store import ArtifactStore
from opofuente.infrastructure.capabilities import (
    ConfigurationCapabilityProvider,
    IngestionCapabilityProvider,
    SqliteCapabilityProvider,
    VectorIndexCapabilityProvider,
)
from opofuente.infrastructure.card_repository import SqlAlchemyCardRepository
from opofuente.infrastructure.change_repository import SqlAlchemyChangeRepository
from opofuente.infrastructure.classification_repository import SqlAlchemyClassificationRepository
from opofuente.infrastructure.classifiers import DeterministicClassifier
from opofuente.infrastructure.classifiers.topic_fragments import FragmentTopicClassifier
from opofuente.infrastructure.clock import SystemClock
from opofuente.infrastructure.db import build_engine, build_session_factory
from opofuente.infrastructure.document_repository import SqlAlchemyDocumentRepository
from opofuente.infrastructure.dossier_repository import SqlAlchemyDossierRepository
from opofuente.infrastructure.explanation_client import DeepSeekExplanationProposer
from opofuente.infrastructure.extraction_repository import SqlAlchemyExtractionRepository
from opofuente.infrastructure.extractors import ExtractorRegistry
from opofuente.infrastructure.filesystem_inventory import FilesystemInventory
from opofuente.infrastructure.housekeeping_repository import SqlAlchemyHousekeepingRepository
from opofuente.infrastructure.ingestion_repository import SqlAlchemyIngestionRepository
from opofuente.infrastructure.job_repository import SqlAlchemyJobRepository
from opofuente.infrastructure.key_reliability_repository import (
    SqlAlchemyKeyReliabilityRepository,
)
from opofuente.infrastructure.migrations import database_revision, run_migrations, script_head
from opofuente.infrastructure.notes_incident_repository import (
    SqlAlchemyNotesIncidentRepository,
)
from opofuente.infrastructure.notes_report_repository import SqlAlchemyNotesReportRepository
from opofuente.infrastructure.notes_review_repository import SqlAlchemyNotesReviewRepository
from opofuente.infrastructure.observability import setup_logging
from opofuente.infrastructure.ocr import tesseract_from_settings
from opofuente.infrastructure.password_hashing import Argon2PasswordHasher
from opofuente.infrastructure.plan_repository import SqlAlchemyPlanRepository
from opofuente.infrastructure.probes import DatabaseProbe, DataDirectoryProbe
from opofuente.infrastructure.profile_repository import SqlAlchemyProfileRepository
from opofuente.infrastructure.question_file_repository import SqlAlchemyQuestionFileRepository
from opofuente.infrastructure.question_repository import SqlAlchemyQuestionRepository
from opofuente.infrastructure.readiness_repository import SqlAlchemyReadinessRepository
from opofuente.infrastructure.representation_store import RepresentationStore
from opofuente.infrastructure.review_repository import SqlAlchemyReviewRepository
from opofuente.infrastructure.search_repository import SqlAlchemySearchRepository
from opofuente.infrastructure.student_repository import SqlAlchemyStudentRepository
from opofuente.infrastructure.study_repository import SqlAlchemyStudyRepository
from opofuente.infrastructure.topic_notes_repository import SqlAlchemyTopicNotesRepository
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


def _disk_usage(root: Path) -> tuple[int, int]:
    """Espacio total y libre de la unidad donde vive el árbol de datos.

    Si el directorio no existe todavía se mide su ancestro más cercano: un cero porque «aún no hay
    carpeta» sería un dato falso sobre el disco.
    """
    candidato = root
    while not candidato.exists() and candidato.parent != candidato:
        candidato = candidato.parent
    uso = shutil.disk_usage(candidato)
    return uso.total, uso.free


def _restored_database_health(settings: Settings) -> tuple[bool, str]:
    """Comprobación posterior a una restauración: la base colocada está migrada y se puede abrir.

    No arranca la aplicación entera (sería construir otra vez el proceso desde dentro de una
    petición): comprueba lo que de verdad puede quedar mal después de un intercambio de ficheros,
    que es que la base restaurada no esté en la revisión del código o no se pueda leer.
    """
    engine = build_engine(settings.data_paths.database)
    try:
        esperada = script_head(settings)
        actual = database_revision(engine)
        if esperada is None:
            return False, "no se pudo determinar la revisión de cabeza del programa"
        if actual != esperada:
            return False, f"la base restaurada está en {actual} y el programa espera {esperada}"
        return True, f"la base restaurada se abre y está en la revisión {actual}"
    except Exception as error:
        # Se informa del fallo en lugar de propagarlo a media restauración.
        return False, f"la base restaurada no se pudo comprobar ({type(error).__name__})"
    finally:
        engine.dispose()


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved = settings or get_settings()
    # # El temporal se resuelve **antes** de construir nada: si `data/tmp` es un enlace a una unidad
    # que
    # # no está conectada, todo lo que pasa por ahí —importar un artefacto, la instantánea antes de
    # una
    # copia, la restauración— falla a media operación. Ver `config.resolve_tmp_directory`.
    tmp_decision = resolve_tmp_directory(resolved.data_paths)
    paths = tmp_decision.paths
    engine = build_engine(paths.database)
    session_factory = build_session_factory(engine)

    worker_liveness = WorkerLiveness()
    # Un solo adaptador de OCR por proceso: la sonda se ejecuta una vez y el informe de capacidades
    # dice lo mismo que el extractor hace (un binario, una versión, unos idiomas).
    ocr = tesseract_from_settings(resolved)
    system_service = SystemService(
        version=__version__,
        probes=(
            DatabaseProbe(session_factory, expected_revision=script_head(resolved)),
            DataDirectoryProbe(paths),
        ),
        capability_providers=(
            ConfigurationCapabilityProvider(resolved, ocr=ocr),
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
        registry=ExtractorRegistry(resolved, ocr=ocr),
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
        engines=(DeterministicClassifier(), FragmentTopicClassifier()),
        clock=clock,
        # Clasificar el corpus entero es un **trabajo**, no una petición: con el material del
        # propietario tarda casi un minuto y bloqueaba la pantalla (DEBT-024).
        jobs=job_queue,
    )
    change_service = ChangeService(
        changes=SqlAlchemyChangeRepository(session_factory),
        documents=SqlAlchemyDocumentRepository(session_factory, representations),
        clock=clock,
    )
    library_service = LibraryService(
        documents=SqlAlchemyDocumentRepository(session_factory, representations),
        classifications=classification_repository,
        clock=clock,
        # La biblioteca avisa de una versión nueva; el cambio lo propone el servicio de cambios.
        changes=change_service,
    )
    question_service = QuestionService(
        questions=SqlAlchemyQuestionRepository(session_factory),
        clock=clock,
        # Importar preguntas **desde un documento** necesita leer sus secciones y fragmentos: la
        # cita de una pregunta sale de ahí (DEBT-010).
        documents=SqlAlchemyDocumentRepository(session_factory, representations),
    )
    # F20: la ficha de pregunta. Reutiliza el servicio del banco para leer la pregunta y sus
    # plantillas, y añade lo que solo la ficha necesita (de dónde salió la clave, qué contestaron
    # los apuntes, las incidencias y el veredicto de fiabilidad del §1) y las dos escrituras
    # auditadas: marcar la correcta y reparar con una regla.
    question_file_service = QuestionFileService(
        questions=question_service,
        files=SqlAlchemyQuestionFileRepository(session_factory),
        clock=clock,
    )
    search_service = SearchService(
        search=SqlAlchemySearchRepository(session_factory),
        clock=clock,
    )
    # Lo que la aplicación hace sola cuando una versión se acepta (S12.5, ADR-017): importar sin que
    # nadie pulse nada las preguntas que el material trae y la clasificación ya dice qué es.
    auto_study_service = AutoStudyService(
        questions=question_service,
        classifications=classification_service,
        library=library_service,
        profiles=profiles_service,
        documents=SqlAlchemyDocumentRepository(session_factory, representations),
        clock=clock,
    )
    review_service = ReviewService(
        reviews=SqlAlchemyReviewRepository(session_factory),
        clock=clock,
    )
    # S12.6: «¿ya puedo estudiar con lo que he soltado?». Cuenta lo que hay (material por papel,
    # preguntas por tema, claves activas) y lo que sigue esperando a una persona; no escribe nada.
    readiness_service = ReadinessService(
        repository=SqlAlchemyReadinessRepository(session_factory),
    )
    # S13: el dossier del tema. Se calcula desde el corpus cada vez que se pide y se archiva cuando
    # alguien lo pide: la verdad está en las fuentes, no en una copia. Los apuntes redactados (pasos
    # B-E) se leen de su tabla y viajan dentro del mismo documento, así que se versionan con él. El
    # repositorio de apuntes se comparte con la zona del alumno (F13), que lee los mismos apartados
    # para la pantalla de lectura: dos instancias serían dos formas de leer lo mismo.
    notes_repository = SqlAlchemyTopicNotesRepository(session_factory)
    dossier_service = DossierService(
        repository=SqlAlchemyDossierRepository(session_factory),
        clock=clock,
        notes=notes_repository,
    )
    # F13: los avisos del alumno sobre los apuntes. Se escriben desde su zona, auditados, y los lee
    # la bandeja del propietario (decisión D2 del objetivo). Desde F16 el propietario también los
    # despacha desde esa bandeja, con su evento y su nota (bloque C).
    notes_reports_repository = SqlAlchemyNotesReportRepository(session_factory)
    notes_reports_service = NotesReportsService(notes_reports_repository, clock=clock)
    # F18: la bandeja del motor. Escribe en `notes_incidents` el propio motor de apuntes (no se
    # toca)
    # y la lee y la despacha el propietario desde el panel, con su estado, su nota y su evento
    # (bloque C, §4.1 del objetivo).
    # F31: además se agrupa por conjunto y admite acciones en bloque. Las dos acciones que escriben
    # fuera de la bandeja van por las rutas auditadas que ya existían —el veredicto de fiabilidad
    # del §1 y la asignación de temario— en vez de por una escritura propia: un segundo camino para
    # el mismo cambio es como acabas con una clave cambiada sin su marca.
    notes_incidents_repository = SqlAlchemyNotesIncidentRepository(session_factory)
    notes_incidents_service = NotesIncidentsService(
        notes_incidents_repository,
        clock=clock,
        keys=SqlAlchemyKeyReliabilityRepository(session_factory),
        questions=question_service,
    )
    # F24: la revisión de los apuntes (§4.3 del objetivo). El propietario ve los temas con su motivo
    # medido, lee un borrador dentro del panel y lo aprueba o lo rechaza. El servicio de apuntes
    # entra **solo para medir** (lee lo guardado y no llama a nadie: le acompaña un motor que se
    # niega a usarse) y publicar sigue siendo `DossierService.archive`, el camino de siempre.
    notes_review_repository = SqlAlchemyNotesReviewRepository(session_factory)
    notes_review_service = NotesReviewService(
        profiles=SqlAlchemyProfileRepository(session_factory),
        reviews=notes_review_repository,
        notes=notes_repository,
        topic_notes=TopicNotesService(
            repository=notes_repository,
            dossier=SqlAlchemyDossierRepository(session_factory),
            model=MedidaSinModelo(),
            workers=1,
        ),
        dossier=dossier_service,
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
    # F2: la zona del alumno. Reutiliza el servicio de estudio para leer las sesiones (que ya
    # filtra por dueño) y añade lo suyo: el progreso por bloque y por tema, el temario, los fallos
    # vencidos y —desde F13— los apuntes del tema y el aviso «esto está mal». El filtro de oposición
    # sale de la configuración, no de la petición.
    student_service = StudentService(
        settings=resolved,
        profiles=SqlAlchemyProfileRepository(session_factory),
        student=SqlAlchemyStudentRepository(session_factory),
        study=study_service,
        clock=clock,
        notes=notes_repository,
        reports=notes_reports_repository,
    )
    # S28 (§8 a §11 del objetivo vivo): la plataforma desplegable. Los tres servicios se construyen
    # **siempre**, aunque sus banderas nazcan apagadas, porque las tres cosas comparten una misma
    # propiedad y no se puede depender de cuál está encendida:
    #
    # # - con las cuentas apagadas, sus rutas contestan 404 y no escriben ni una fila (hay una
    # prueba);
    # - el consentimiento (§9) existe **sin** cuentas: se puede leer la política y decidir sobre las
    #   cookies en una instalación de un solo usuario;
    # - la analítica (§10) comprueba en cada petición que está encendida **y** que hay permiso.
    #
    # # El derivador de contraseñas no calcula nada al construirse: el resumen de mentira que iguala
    # los
    # tiempos de un acceso fallido se calcula la primera vez que hace falta.
    account_repository = SqlAlchemyAccountRepository(session_factory)
    accounts_service = AccountsService(
        store=account_repository,
        hasher=Argon2PasswordHasher(
            time_cost=resolved.password_hash_time_cost,
            memory_cost_kib=resolved.password_hash_memory_cost_kib,
            parallelism=resolved.password_hash_parallelism,
        ),
        clock=clock,
        settings=resolved,
    )
    legal_service = LegalService(store=account_repository, clock=clock, settings=resolved)
    analytics_service = AnalyticsService(
        store=SqlAlchemyAnalyticsRepository(session_factory),
        clock=clock,
        settings=resolved,
    )
    # S12: copia, verificación y restauración. La migración y la comprobación van como funciones: al
    # restaurar hay que migrar la base recién colocada y comprobar que quedó sana.
    backup_service = BackupService(
        paths=paths,
        app_version=__version__,
        clock=lambda: datetime.now(UTC),
        schema_revision=lambda: script_head(resolved) or "desconocida",
        migrate=lambda: run_migrations(resolved, revision="head"),
        health=lambda: _restored_database_health(resolved),
    )
    # S12: higiene del almacén (DEBT-007) y diagnóstico sanitizado (09_SECURITY §12). El diagnóstico
    # se compone con lo que ya saben los demás servicios, no con una segunda versión de la verdad.
    housekeeping_repository = SqlAlchemyHousekeepingRepository(session_factory)
    housekeeping_service = HousekeepingService(
        paths=paths,
        artifacts=artifact_store,
        repository=housekeeping_repository,
        clock=lambda: datetime.now(UTC),
    )
    diagnostic_service = DiagnosticService(
        version=__version__,
        host=resolved.host,
        port=resolved.port,
        log_level=resolved.log_level,
        data_dir=paths.root,
        database_file=paths.database,
        disk_usage=lambda: _disk_usage(paths.root),
        schema_revision=lambda: script_head(resolved) or "desconocida",
        counts=housekeeping_repository.counts,
        capabilities=system_service.capabilities,
        readiness=system_service.readiness,
        clock=lambda: datetime.now(UTC),
        log_file=paths.logs / "opofuente.log",
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
        # Lo primero que se dice al arrancar es dónde ha quedado el temporal y por qué. Si no se
        # puede escribir en ninguno de los dos, **no se arranca a medias**: se explica la ruta
        # exacta, el disco que falta y qué hacer, y el proceso muere aquí en lugar de aceptar
        # peticiones que van a fallar a media operación.
        if tmp_decision.nothing_writable:
            logger.error(
                "opofuente.startup_failed %s. Comprueba que la unidad del temporal está conectada "
                "(en este equipo `datos\\tmp` apunta a otra unidad) o define el temporal en la "
                "misma unidad que la base; la aplicación no arranca sin un temporal escribible.",
                tmp_decision.detail,
                extra={"event": "startup_failed"},
            )
            raise ConfigurationError(f"no hay ningún temporal escribible: {tmp_decision.detail}")
        if tmp_decision.fallback_used:
            logger.warning(
                "opofuente.tmp_fallback %s",
                tmp_decision.detail,
                extra={"event": "tmp_fallback"},
            )
        else:
            logger.info("opofuente.tmp_ok %s", tmp_decision.detail, extra={"event": "tmp_ok"})
        logger.info(
            "opofuente.startup host=%s port=%s log_level=%s plataforma=%s",
            resolved.host,
            resolved.port,
            resolved.log_level,
            "encendida" if resolved.any_platform_feature_enabled else "apagada",
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

    # **El proposer del modelo, o None**: sin `DEEPSEEK_API_KEY` la aplicación arranca igual y solo
    # «regenerar» responde 503. **No lanzar aquí es a propósito**: una clave que falta no puede
    # impedir que se abra la aplicación.
    def _construir_proposer() -> ExplanationProposer | None:
        clave = os.environ.get("DEEPSEEK_API_KEY", "").strip()
        if not clave:
            return None
        return DeepSeekExplanationProposer(api_key=clave)

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
    app.state.card_service = CardService(SqlAlchemyCardRepository(session_factory))
    app.state.plan_service = PlanService(SqlAlchemyPlanRepository(session_factory))
    app.state.explanation_proposer = _construir_proposer()
    app.state.question_file_service = question_file_service
    app.state.auto_study_service = auto_study_service
    app.state.study_service = study_service
    app.state.student_service = student_service
    app.state.accounts_service = accounts_service
    app.state.legal_service = legal_service
    app.state.analytics_service = analytics_service
    app.state.tmp_decision = tmp_decision
    app.state.search_service = search_service
    app.state.review_service = review_service
    app.state.export_service = export_service
    app.state.change_service = change_service
    app.state.backup_service = backup_service
    app.state.housekeeping_service = housekeeping_service
    app.state.diagnostic_service = diagnostic_service
    app.state.readiness_service = readiness_service
    app.state.dossier_service = dossier_service
    app.state.notes_reports_service = notes_reports_service
    app.state.notes_incidents_service = notes_incidents_service
    app.state.notes_review_service = notes_review_service

    # El orden importa: el último añadido es el más externo, así que el identificador de
    # correlación envuelve también los rechazos por Origin.
    #
    # `allow_credentials` sigue a la bandera de las cuentas y no es un detalle: la cookie de sesión
    # viaja entre la web (otro puerto, mismo sitio) y esta API, y el navegador **descarta** una
    # # respuesta con credenciales si el servidor no las autoriza. Con las cuentas apagadas se queda
    # en
    # `False`, que es como estaba: ninguna petición de hoy cambia de comportamiento.
    # Un fallo inesperado tiene que salir **por dentro** del middleware de CORS: es la única forma
    # de
    # que su respuesta lleve `Access-Control-Allow-Origin`. `add_middleware` mete cada middleware
    # por
    # delante del anterior, así que este se añade **antes** que el de CORS a propósito: el primero
    # añadido es el más interno, y el de CORS tiene que envolverlo. Si se añadiera detrás, el 500
    # saldría por fuera de CORS —como salía— y el navegador lo leería como un error de CORS.
    app.add_middleware(ProblemErrorMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(resolved.cors_origins),
        allow_credentials=resolved.accounts_enabled,
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Idempotency-Key", "X-Correlation-ID"],
        expose_headers=["X-Correlation-ID"],
    )
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(OriginCheckMiddleware, allowed_origins=resolved.cors_origins)
    # La puerta de las sesiones (§8): con las cuentas apagadas no comprueba nada, así que el
    # comportamiento es el de siempre; encendidas, cierra por defecto todo lo que no sea público, y
    # deja abierta la zona de estudio.
    app.add_middleware(
        SessionGateMiddleware,
        enabled=lambda: resolved.accounts_enabled,
        is_live=accounts_service.is_live,
    )
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
