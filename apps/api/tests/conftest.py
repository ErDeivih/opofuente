"""Fixtures de las pruebas de backend.

Regla dura (10_TEST-PLAN §4): ninguna prueba toca la carpeta real del usuario. Todo
directorio de datos se crea bajo `tmp_path` y las variables `OPOFUENTE_*` del entorno del
desarrollador se neutralizan para que el resultado no dependa de la máquina.
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from opofuente.application.convocatorias_service import ConvocatoriasService
from opofuente.application.curriculum_service import CurriculaService
from opofuente.application.profiles_service import ProfilesService
from opofuente.application.read_models import (
    ConvocatoriasSeedReport,
    CurriculumSeedReport,
    SeedReport,
)
from opofuente.config import Settings, project_root
from opofuente.infrastructure.clock import SystemClock
from opofuente.infrastructure.convocatorias_fixture_loader import (
    C1_CONVOCATORIAS_FIXTURE,
    load_c1_convocatorias,
)
from opofuente.infrastructure.convocatorias_repository import (
    SqlAlchemyConvocatoriasRepository,
)
from opofuente.infrastructure.curriculum_fixture_loader import (
    COMMON_CURRICULUM_FIXTURE,
    load_common_curriculum,
)
from opofuente.infrastructure.curriculum_repository import SqlAlchemyCurriculumRepository
from opofuente.infrastructure.db import build_engine, build_session_factory
from opofuente.infrastructure.fixture_loader import load_profiles
from opofuente.infrastructure.migrations import run_migrations
from opofuente.infrastructure.profile_repository import SqlAlchemyProfileRepository
from opofuente.main import create_app


@pytest.fixture(autouse=True, scope="session")
def _hermetic_environment() -> Iterator[None]:
    saved = {
        key: value for key, value in os.environ.items() if key.startswith(("OPOFUENTE_", "VITE_"))
    }
    for key in saved:
        del os.environ[key]
    yield
    os.environ.update(saved)


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    """Configuración aislada; ignora el `.env` del repositorio."""
    return Settings(data_dir=tmp_path / "data", _env_file=None)


@pytest.fixture
def migrated_settings(settings: Settings) -> Settings:
    settings.data_paths.ensure_directories()
    run_migrations(settings)
    return settings


@pytest.fixture
def client(migrated_settings: Settings) -> Iterator[TestClient]:
    app = create_app(migrated_settings)
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def unmigrated_client(settings: Settings) -> Iterator[TestClient]:
    """Aplicación con base de datos vacía: sirve para comprobar el estado no listo."""
    settings.data_paths.ensure_directories()
    app = create_app(settings)
    with TestClient(app) as test_client:
        yield test_client


def seed_official_profiles(settings: Settings) -> SeedReport:
    """Siembra los perfiles oficiales en el directorio de datos de la prueba."""
    engine = build_engine(settings.data_paths.database)
    try:
        repository = SqlAlchemyProfileRepository(build_session_factory(engine))
        service = ProfilesService(repository, SystemClock())
        return service.seed(load_profiles(project_root() / "fixtures" / "profiles"))
    finally:
        engine.dispose()


def seed_common_curriculum(settings: Settings) -> CurriculumSeedReport:
    """Siembra el temario común v1 y sus referencias en el directorio de datos de la prueba."""
    engine = build_engine(settings.data_paths.database)
    try:
        sesiones = build_session_factory(engine)
        servicio = CurriculaService(SqlAlchemyCurriculumRepository(sesiones), SystemClock())
        return servicio.seed(load_common_curriculum(project_root() / COMMON_CURRICULUM_FIXTURE))
    finally:
        engine.dispose()


def seed_c1_convocatorias(settings: Settings) -> ConvocatoriasSeedReport:
    """Siembra las convocatorias C1 que referencian el temario común (B-006)."""
    engine = build_engine(settings.data_paths.database)
    try:
        sesiones = build_session_factory(engine)
        servicio = ConvocatoriasService(SqlAlchemyConvocatoriasRepository(sesiones), SystemClock())
        return servicio.seed(load_c1_convocatorias(project_root() / C1_CONVOCATORIAS_FIXTURE))
    finally:
        engine.dispose()


@pytest.fixture
def seeded_settings(migrated_settings: Settings) -> Settings:
    seed_official_profiles(migrated_settings)
    return migrated_settings


@pytest.fixture
def seeded_client(seeded_settings: Settings) -> Iterator[TestClient]:
    app = create_app(seeded_settings)
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def api_only_client(migrated_settings: Settings) -> Iterator[TestClient]:
    """Aplicación migrada **sin worker**: los trabajos quedan en cola y los controla la prueba."""
    settings = Settings(data_dir=migrated_settings.data_dir, worker_enabled=False, _env_file=None)
    app = create_app(settings)
    with TestClient(app) as test_client:
        yield test_client
