"""Carga del fixture de equivalencias entre el programa publicado del TAI y el temario común.

El fixture es curado a mano (B-003): cada fila lleva su relación, su confianza, su estado y el
motivo. El cargador valida la forma con pydantic y la coherencia con el dominio; la resolución de
nodos concretos —y la comprobación de que no falta ningún tema publicado— se hace contra la base al
calcular el plan, porque las rutas solo significan algo dentro de una versión.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from opofuente.domain.equivalences import (
    EquivalenceFixture,
    EquivalenceRow,
    validate_equivalences,
)
from opofuente.domain.errors import InvariantViolationError

TAI_EQUIVALENCES_FIXTURE = Path("fixtures") / "curricula" / "tai-age-2025.equivalences.json"


class _VersionRef(BaseModel):
    model_config = ConfigDict(extra="forbid")

    curriculum_version_code: str
    name: str


class _RowFixture(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_path: str
    target_path: str
    relation: str
    confidence: float
    status: str
    evidence_note: str


class EquivalenceFixtureFile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source: _VersionRef
    target: _VersionRef
    generated_by: str
    note: str
    equivalences: list[_RowFixture] = Field(default_factory=list)


def load_equivalences(path: Path | None = None) -> EquivalenceFixture:
    """Lee y valida el fixture de equivalencias."""
    ruta = path or TAI_EQUIVALENCES_FIXTURE
    try:
        data: Any = json.loads(ruta.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise InvariantViolationError(f"falta el fixture de equivalencias: {ruta}") from error
    except json.JSONDecodeError as error:
        raise InvariantViolationError(f"{ruta.name} no es JSON válido: {error}") from error

    try:
        fixture = EquivalenceFixtureFile.model_validate(data)
    except ValidationError as error:
        raise InvariantViolationError(
            f"{ruta.name} no cumple el formato de equivalencias: {error}"
        ) from error

    equivalencias = EquivalenceFixture(
        source_version_code=fixture.source.curriculum_version_code,
        target_version_code=fixture.target.curriculum_version_code,
        rows=tuple(
            EquivalenceRow(
                source_path=row.source_path,
                target_path=row.target_path,
                relation=row.relation,
                confidence=row.confidence,
                status=row.status,
                evidence_note=row.evidence_note,
            )
            for row in fixture.equivalences
        ),
    )
    validate_equivalences(equivalencias)
    return equivalencias
