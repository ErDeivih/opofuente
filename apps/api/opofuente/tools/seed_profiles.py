"""Siembra los perfiles oficiales desde los fixtures versionados.

Es idempotente: ejecutarlo dos veces deja el mismo estado y el informe dice cuántas entidades se
crearon, cuántas se actualizaron y cuántas no cambiaron.

Uso:
    uv run python -m opofuente.tools.seed_profiles
    uv run python -m opofuente.tools.seed_profiles --check   # falla si hubo que escribir algo
"""

from __future__ import annotations

import sys
from collections.abc import Sequence

from opofuente.application.profiles_service import ProfilesService
from opofuente.config import get_settings, project_root
from opofuente.infrastructure.clock import SystemClock
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
        repository = SqlAlchemyProfileRepository(build_session_factory(engine))
        service = ProfilesService(repository, SystemClock())
        report = service.seed(load_profiles(project_root() / "fixtures" / "profiles"))
    finally:
        engine.dispose()

    for outcome in report.profiles:
        print(
            f"  {outcome.profile_code}: {outcome.created} nuevas, "
            f"{outcome.updated} actualizadas, {outcome.unchanged} sin cambios"
        )
    print(report.summary())

    if check_only and report.changed:
        print(
            "Los perfiles sembrados no coinciden con los fixtures: había cambios pendientes.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
