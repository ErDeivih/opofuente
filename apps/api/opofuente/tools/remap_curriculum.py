"""Re-atribuye el banco del programa publicado al temario común, con informe por fila e inverso.

Es la tarea B-003: una vez que el temario común existe (B-002) y el programa del TAI está guardado
como evidencia, las preguntas y los fallos que colgaban de los 33 temas publicados tienen que poder
verse bajo el tema común. Lo hace con las equivalencias curadas:

Uso:
    uv run python -m opofuente.tools.remap_curriculum --check
    uv run python -m opofuente.tools.remap_curriculum --apply
    uv run python -m opofuente.tools.remap_curriculum --inverse <ruta del informe>

`--check` calcula el plan sin escribir nada. `--apply` **hace una copia previa** de la base
(fichero, `-wal` y `-shm`) y escribe el informe junto a la copia: una fila por equivalencia y una
entrada por cada mapeo o fallo movido, para poder revisarlo y deshacerlo. `--inverse` devuelve el
material a su nodo publicado usando ese informe y retira las equivalencias que creó.

Lo dudoso no se toca: las equivalencias `proposed` se guardan para revisión pero su material se
queda en el programa publicado, y los choques de unicidad se informan como conflicto en vez de
forzarse. Re-ejecutar la misma operación no duplica ni cambia nada.
"""

from __future__ import annotations

import json
import shutil
import sys
from collections.abc import Sequence
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from opofuente.application.remap_models import RemapPlan
from opofuente.config import Settings, get_settings, project_root
from opofuente.domain.errors import InvariantViolationError
from opofuente.infrastructure.db import build_engine, build_session_factory
from opofuente.infrastructure.equivalence_fixture_loader import (
    TAI_EQUIVALENCES_FIXTURE,
    load_equivalences,
)
from opofuente.infrastructure.remap_repository import SqlAlchemyRemapRepository


def backup_database(settings: Settings) -> Path:
    """Copia la base (y sus `-wal`/`-shm`) antes de escribir. Devuelve el directorio de la copia."""
    base = settings.data_paths.database
    if not base.is_file():
        raise InvariantViolationError(f"no existe la base de datos que hay que migrar: {base}")
    marca = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    destino = settings.data_paths.backups / f"remap-curriculum-{marca}"
    if destino.exists():  # pragma: no cover - dos ejecuciones en el mismo segundo
        destino = settings.data_paths.backups / f"remap-curriculum-{marca}-{base.stat().st_size}"
    destino.mkdir(parents=True)
    for sufijo in ("", "-wal", "-shm"):
        origen = Path(f"{base}{sufijo}")
        if origen.is_file():
            shutil.copy2(origen, destino / f"{base.name}{sufijo}")
    copia = destino / base.name
    if not copia.is_file() or copia.stat().st_size != base.stat().st_size:
        raise InvariantViolationError(
            f"la copia previa de la base no se ha podido verificar en {destino}"
        )
    return destino


def _relative(settings: Settings, path: Path) -> str:
    try:
        return str(path.relative_to(settings.data_dir))
    except ValueError:  # pragma: no cover - la copia siempre vive dentro del árbol de datos
        return path.name


def _plan_report(
    plan: RemapPlan, *, settings: Settings, backup: Path | None, operation: str
) -> dict[str, Any]:
    cambios = [
        asdict(cambio) for fila in plan.rows for cambio in (*fila.mappings, *fila.learning_errors)
    ]
    return {
        "operation": operation,
        "generated_at": datetime.now(UTC).isoformat(),
        "database": settings.data_paths.database.name,
        "backup": _relative(settings, backup) if backup is not None else None,
        "source_curriculum_version": plan.source_version_code,
        "target_curriculum_version": plan.target_version_code,
        "summary": plan.summary(),
        "counts": {
            "equivalences_created": plan.equivalences_created,
            "equivalences_updated": plan.equivalences_updated,
            "equivalences_unchanged": plan.equivalences_unchanged,
            "mappings_examined": plan.mappings_examined,
            "mappings_moved": plan.mappings_moved,
            "mappings_conflicts": plan.mappings_conflicts,
            "errors_examined": plan.errors_examined,
            "errors_moved": plan.errors_moved,
        },
        "created_equivalence_ids": list(plan.created_equivalence_ids),
        "changes": cambios,
        "rows": [asdict(fila) for fila in plan.rows],
    }


def _print_plan(plan: RemapPlan) -> None:
    for fila in plan.rows:
        estado = "aplicada" if fila.applied else "se queda (revisar)"
        detalle = (
            f"mapeos movidos {len(fila.mappings)}, conflictos {len(fila.conflicts)}, "
            f"fallos movidos {len(fila.learning_errors)}, "
            f"material que se queda {fila.kept_mappings + fila.kept_learning_errors}"
        )
        print(
            f"  {fila.source_path:>6} -> {fila.target_path:<6} [{fila.relation}/{estado}] {detalle}"
        )
        for conflicto in fila.conflicts:
            print(f"    ! {conflicto}")
    print(f"  {plan.summary()}")


def _repository(settings: Settings) -> tuple[SqlAlchemyRemapRepository, Any]:
    engine = build_engine(settings.data_paths.database)
    return SqlAlchemyRemapRepository(build_session_factory(engine)), engine


def _run(args: list[str]) -> int:
    check_only = "--check" in args
    apply = "--apply" in args
    inverse_path: Path | None = None
    if "--inverse" in args:
        indice = args.index("--inverse")
        try:
            inverse_path = Path(args[indice + 1])
        except IndexError as error:
            raise InvariantViolationError("--inverse necesita la ruta del informe") from error
    if sum([check_only, apply, inverse_path is not None]) != 1:
        raise InvariantViolationError("usa uno de --check, --apply o --inverse <informe>")

    fixture_path = TAI_EQUIVALENCES_FIXTURE
    if "--fixture" in args:
        indice = args.index("--fixture")
        try:
            fixture_path = Path(args[indice + 1])
        except IndexError as error:
            raise InvariantViolationError("--fixture necesita una ruta") from error

    settings = get_settings()
    settings.data_paths.ensure_directories()
    repository, engine = _repository(settings)
    try:
        if inverse_path is not None:
            if not inverse_path.is_file():
                raise InvariantViolationError(f"no existe el informe: {inverse_path}")
            informe = json.loads(inverse_path.read_text(encoding="utf-8"))
            backup = backup_database(settings)
            resultado = repository.inverse(informe)
            destino = backup / "informe-inverso.json"
            destino.write_text(
                json.dumps(
                    {
                        "operation": "inverse",
                        "generated_at": datetime.now(UTC).isoformat(),
                        "backup": _relative(settings, backup),
                        "source_report": inverse_path.name,
                        "result": asdict(resultado),
                        "summary": resultado.summary(),
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
                newline="\n",
            )
            print(f"  {resultado.summary()}")
            print(f"  copia previa: {_relative(settings, backup)}")
            print(f"  informe del inverso: {_relative(settings, destino)}")
            return 0

        fixture = load_equivalences(project_root() / fixture_path)
        if check_only:
            plan = repository.plan(fixture)
            _print_plan(plan)
            if not plan.changed:
                print(
                    "  No hay cambios pendientes: el banco ya está re-atribuido con este fixture."
                )
            else:
                print("  Plan calculado sin escribir nada (dry-run).")
            return 0

        backup = backup_database(settings)
        plan = repository.apply(fixture, now=datetime.now(UTC))
        informe = _plan_report(plan, settings=settings, backup=backup, operation="apply")
        destino = backup / "informe.json"
        destino.write_text(
            json.dumps(informe, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        _print_plan(plan)
        print(f"  copia previa: {_relative(settings, backup)}")
        print(f"  informe por fila: {_relative(settings, destino)}")
        return 0
    finally:
        engine.dispose()


def main(argv: Sequence[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    try:
        return _run(args)
    except InvariantViolationError as error:
        print(error, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
