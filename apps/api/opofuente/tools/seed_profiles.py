"""Siembra los perfiles oficiales y el temario común desde los fixtures versionados.

Es idempotente: ejecutarlo dos veces deja el mismo estado y el informe dice cuántas entidades se
crearon, cuántas se actualizaron y cuántas no cambiaron. El temario común se siembra en su edición y
solo se publica cuando el recuento cuadra con el contrato (5 bloques / 40 temas / 45 nodos); sus
referencias (`primary` del TAI 2025) se crean o se confirman con su cita.

Uso:
    uv run python -m opofuente.tools.seed_profiles
    uv run python -m opofuente.tools.seed_profiles --check   # falla si hubo que escribir algo
"""

from __future__ import annotations

import sys
from collections.abc import Sequence

from opofuente.application.curriculum_service import CurriculaService
from opofuente.application.profiles_service import ProfilesService
from opofuente.config import get_settings, project_root
from opofuente.infrastructure.clock import SystemClock
from opofuente.infrastructure.curriculum_fixture_loader import (
    COMMON_CURRICULUM_FIXTURE,
    load_common_curriculum,
)
from opofuente.infrastructure.curriculum_repository import SqlAlchemyCurriculumRepository
from opofuente.infrastructure.db import build_engine, build_session_factory
from opofuente.infrastructure.fixture_loader import load_profiles
from opofuente.infrastructure.profile_repository import SqlAlchemyProfileRepository


def main(argv: Sequence[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    check_only = "--check" in args
    settings = get_settings()
    settings.data_paths.ensure_directories()

    engine = build_engine(settings.data_paths.database)
    try:
        sesiones = build_session_factory(engine)
        perfiles = ProfilesService(SqlAlchemyProfileRepository(sesiones), SystemClock())
        report = perfiles.seed(load_profiles(project_root() / "fixtures" / "profiles"))

        curricula = CurriculaService(SqlAlchemyCurriculumRepository(sesiones), SystemClock())
        curriculum = curricula.seed(
            load_common_curriculum(project_root() / COMMON_CURRICULUM_FIXTURE)
        )
    finally:
        engine.dispose()

    for outcome in report.profiles:
        linea = (
            f"  {outcome.profile_code}: {outcome.created} nuevas, "
            f"{outcome.updated} actualizadas, {outcome.unchanged} sin cambios"
        )
        if outcome.blocked:
            linea += f", {outcome.blocked} nodos sin retirar (tienen material asignado)"
        print(linea)
    print(report.summary())
    print(f"  {curriculum.summary()}")

    if check_only and (report.changed or curriculum.changed):
        print(
            "Los datos sembrados no coinciden con los fixtures: había cambios pendientes.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
