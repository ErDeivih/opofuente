"""Dependencias de FastAPI.

El estado vive en `app.state` (no en un singleton global) para que las pruebas puedan
construir aplicaciones con configuración temporal sin tocar el directorio de datos real.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Request

from opofuente.application.auto_study_service import AutoStudyService
from opofuente.application.backup_service import BackupService
from opofuente.application.change_service import ChangeService
from opofuente.application.classification_service import ClassificationService
from opofuente.application.diagnostic_service import DiagnosticService
from opofuente.application.dossier_service import DossierService
from opofuente.application.export_service import ExportService
from opofuente.application.extraction_service import ExtractionService
from opofuente.application.housekeeping_service import HousekeepingService
from opofuente.application.ingestion_service import IngestionService
from opofuente.application.intake_service import IntakeService
from opofuente.application.job_service import JobService
from opofuente.application.library_service import LibraryService
from opofuente.application.notes_report_service import NotesReportsService
from opofuente.application.profiles_service import ProfilesService
from opofuente.application.question_service import QuestionService
from opofuente.application.readiness_service import ReadinessService
from opofuente.application.review_service import ReviewService
from opofuente.application.search_service import SearchService
from opofuente.application.student_service import StudentService
from opofuente.application.study_service import StudyService
from opofuente.application.system_service import SystemService
from opofuente.config import Settings
from opofuente.infrastructure.artifact_store import ArtifactStore


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


def get_extraction_service(request: Request) -> ExtractionService:
    service: ExtractionService = request.app.state.extraction_service
    return service


def get_intake_service(request: Request) -> IntakeService:
    service: IntakeService = request.app.state.intake_service
    return service


def get_job_service(request: Request) -> JobService:
    service: JobService = request.app.state.job_service
    return service


def get_classification_service(request: Request) -> ClassificationService:
    service: ClassificationService = request.app.state.classification_service
    return service


def get_library_service(request: Request) -> LibraryService:
    service: LibraryService = request.app.state.library_service
    return service


def get_artifact_store(request: Request) -> ArtifactStore:
    store: ArtifactStore = request.app.state.artifact_store
    return store


def get_question_service(request: Request) -> QuestionService:
    service: QuestionService = request.app.state.question_service
    return service


def get_auto_study_service(request: Request) -> AutoStudyService:
    service: AutoStudyService = request.app.state.auto_study_service
    return service


def get_study_service(request: Request) -> StudyService:
    service: StudyService = request.app.state.study_service
    return service


def get_search_service(request: Request) -> SearchService:
    service: SearchService = request.app.state.search_service
    return service


def get_review_service(request: Request) -> ReviewService:
    service: ReviewService = request.app.state.review_service
    return service


def get_change_service(request: Request) -> ChangeService:
    service: ChangeService = request.app.state.change_service
    return service


def get_export_service(request: Request) -> ExportService:
    service: ExportService = request.app.state.export_service
    return service


def get_backup_service(request: Request) -> BackupService:
    service: BackupService = request.app.state.backup_service
    return service


def get_housekeeping_service(request: Request) -> HousekeepingService:
    service: HousekeepingService = request.app.state.housekeeping_service
    return service


def get_diagnostic_service(request: Request) -> DiagnosticService:
    service: DiagnosticService = request.app.state.diagnostic_service
    return service


def get_readiness_service(request: Request) -> ReadinessService:
    service: ReadinessService = request.app.state.readiness_service
    return service


def get_dossier_service(request: Request) -> DossierService:
    service: DossierService = request.app.state.dossier_service
    return service


def get_student_service(request: Request) -> StudentService:
    service: StudentService = request.app.state.student_service
    return service


def get_notes_reports_service(request: Request) -> NotesReportsService:
    """La bandeja de avisos del alumno, que es del propietario: la lee el panel."""
    service: NotesReportsService = request.app.state.notes_reports_service
    return service


#: Dependencias anotadas (estilo moderno de FastAPI: sin llamadas en valores por defecto).
AppSettingsDep = Annotated[Settings, Depends(get_app_settings)]
SystemServiceDep = Annotated[SystemService, Depends(get_system_service)]
ProfilesServiceDep = Annotated[ProfilesService, Depends(get_profiles_service)]
IngestionServiceDep = Annotated[IngestionService, Depends(get_ingestion_service)]
ExtractionServiceDep = Annotated[ExtractionService, Depends(get_extraction_service)]
IntakeServiceDep = Annotated[IntakeService, Depends(get_intake_service)]
JobServiceDep = Annotated[JobService, Depends(get_job_service)]
ClassificationServiceDep = Annotated[ClassificationService, Depends(get_classification_service)]
LibraryServiceDep = Annotated[LibraryService, Depends(get_library_service)]
ArtifactStoreDep = Annotated[ArtifactStore, Depends(get_artifact_store)]
QuestionServiceDep = Annotated[QuestionService, Depends(get_question_service)]
AutoStudyServiceDep = Annotated[AutoStudyService, Depends(get_auto_study_service)]
StudyServiceDep = Annotated[StudyService, Depends(get_study_service)]
SearchServiceDep = Annotated[SearchService, Depends(get_search_service)]
ReviewServiceDep = Annotated[ReviewService, Depends(get_review_service)]
ExportServiceDep = Annotated[ExportService, Depends(get_export_service)]
ChangeServiceDep = Annotated[ChangeService, Depends(get_change_service)]
DossierServiceDep = Annotated[DossierService, Depends(get_dossier_service)]
BackupServiceDep = Annotated[BackupService, Depends(get_backup_service)]
HousekeepingServiceDep = Annotated[HousekeepingService, Depends(get_housekeeping_service)]
DiagnosticServiceDep = Annotated[DiagnosticService, Depends(get_diagnostic_service)]
ReadinessServiceDep = Annotated[ReadinessService, Depends(get_readiness_service)]
StudentServiceDep = Annotated[StudentService, Depends(get_student_service)]
NotesReportsServiceDep = Annotated[NotesReportsService, Depends(get_notes_reports_service)]
