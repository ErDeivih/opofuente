"""Carga del fixture de convocatorias C1 que referencian el temario común.

El fixture se genera desde las fuentes verificadas (`build_c1_convocatorias_fixtures.py`); aquí se
valida la forma (pydantic) y la coherencia (dominio) antes de sembrarlo. No decide qué convocatorias
entran: eso ya está escrito en el fixture, con las filas descartadas y su motivo.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from opofuente.domain.convocatorias_c1 import (
    C1Convocatoria,
    C1ConvocatoriasFixture,
    C1Source,
    DiscardedRow,
    validate_c1_convocatorias,
)
from opofuente.domain.errors import InvariantViolationError

C1_CONVOCATORIAS_FIXTURE = Path("fixtures") / "curricula" / "convocatorias-c1.json"


class _OppositionFixture(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    name: str
    description: str


class _SourceFixture(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    document: str
    sha256: str
    observed_at: str


class _GeneratedFromFixture(BaseModel):
    model_config = ConfigDict(extra="forbid")

    criteria: list[str]
    sources: list[_SourceFixture]


class _ConvocatoriaFixture(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    title: str
    administration: str | None = None
    territory: str | None = None
    group_code: str
    official_url: str
    published_at: date
    published_at_note: str | None = None
    status: str
    source_reference: str
    source_id: str


class _DiscardedFixture(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_id: str
    row: int
    title: str
    reason: str


class C1ConvocatoriasFile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    opposition: _OppositionFixture
    generated_from: _GeneratedFromFixture
    convocatorias: list[_ConvocatoriaFixture] = Field(default_factory=list)
    discarded: list[_DiscardedFixture] = Field(default_factory=list)


def load_c1_convocatorias(path: Path | None = None) -> C1ConvocatoriasFixture:
    """Lee y valida el fixture de convocatorias C1."""
    ruta = path or C1_CONVOCATORIAS_FIXTURE
    try:
        data: Any = json.loads(ruta.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise InvariantViolationError(f"falta el fixture de convocatorias C1: {ruta}") from error
    except json.JSONDecodeError as error:
        raise InvariantViolationError(f"{ruta.name} no es JSON válido: {error}") from error

    try:
        fixture = C1ConvocatoriasFile.model_validate(data)
    except ValidationError as error:
        raise InvariantViolationError(
            f"{ruta.name} no cumple el formato de convocatorias C1: {error}"
        ) from error

    dominio = C1ConvocatoriasFixture(
        opposition_code=fixture.opposition.code,
        opposition_name=fixture.opposition.name,
        opposition_description=fixture.opposition.description,
        convocatorias=tuple(
            C1Convocatoria(
                code=item.code,
                title=item.title,
                administration=item.administration,
                territory=item.territory,
                official_url=item.official_url,
                published_at=item.published_at,
                published_at_note=item.published_at_note,
                status=item.status,
                source_reference=item.source_reference,
                source_id=item.source_id,
            )
            for item in fixture.convocatorias
        ),
        sources=tuple(
            C1Source(
                id=item.id,
                document=item.document,
                sha256=item.sha256,
                observed_at=item.observed_at,
            )
            for item in fixture.generated_from.sources
        ),
        discarded=tuple(
            DiscardedRow(
                source_id=item.source_id,
                row=item.row,
                title=item.title,
                reason=item.reason,
            )
            for item in fixture.discarded
        ),
    )
    validate_c1_convocatorias(dominio)
    return dominio
