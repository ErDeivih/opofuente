"""Carga del registro de convocatorias publicado por los boletines.

La validación de forma la hace pydantic (`extra="forbid"`: un campo desconocido es un error, no una
nota al margen) y la de coherencia, el dominio. Se separa del dominio por la misma razón que los
perfiles: el dominio no sabe leer ficheros.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from opofuente.domain.classification import AuthorityTier, RightsStatus
from opofuente.domain.convocation_registry import (
    ConvocatoriaRegistrada,
    FuenteOficial,
    Grupo,
    Procedencia,
    RegistroDeConvocatorias,
    SistemaAcceso,
    validate_registry,
)
from opofuente.domain.errors import InvariantViolationError

REGISTRY_NAME = "convocation-registry.json"


class SourceFixture(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    title: str
    publisher: str
    identifier: str
    canonical_url: str
    retrieved_url: str | None = None
    published_at: date | None = None
    authority_tier: AuthorityTier
    rights_status: RightsStatus
    rights_source_url: str | None = None


class ProcedenciaFixture(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_id: str
    quote: str


class RegisteredConvocationFixture(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    cuerpo: str
    grupo: Grupo
    administracion: str
    sistemas: list[SistemaAcceso] = Field(min_length=1)
    plazas_libres: int
    plazas_promocion_interna: int | None = None
    plazo_dias_habiles: int
    enlace_oficial: str
    published_at: date | None = None
    procedencia: ProcedenciaFixture


class RegistryFixture(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1]
    note: str
    retrieved_at: date
    sources: list[SourceFixture]
    convocations: list[RegisteredConvocationFixture]


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise InvariantViolationError(f"falta el registro {path.name}") from error
    except json.JSONDecodeError as error:
        raise InvariantViolationError(f"{path.name} no es JSON válido: {error}") from error


def default_registry_path() -> Path:
    """Ruta del registro versionado dentro del paquete.

    No vive en `fixtures/` porque la política de escritura del workspace bloquea esa carpeta; el
    registro es dato de producto (lo lee la API), no un fixture de pruebas.
    """
    return Path(__file__).resolve().parent.parent / "resources" / REGISTRY_NAME


def load_registry(path: Path | None = None) -> RegistroDeConvocatorias:
    """Carga y valida el registro completo. Cualquier incoherencia aborta la carga entera."""
    registry_path = path or default_registry_path()
    try:
        fixture = RegistryFixture.model_validate(_read_json(registry_path))
    except ValidationError as error:
        raise InvariantViolationError(
            f"{registry_path.name} no cumple el formato: {error}"
        ) from error

    fuentes = tuple(
        FuenteOficial(
            id=item.id,
            title=item.title,
            publisher=item.publisher,
            identifier=item.identifier,
            canonical_url=item.canonical_url,
            authority_tier=item.authority_tier,
            rights_status=item.rights_status,
            published_at=item.published_at,
        )
        for item in fixture.sources
    )
    convocatorias = tuple(
        ConvocatoriaRegistrada(
            code=item.code,
            cuerpo=item.cuerpo,
            grupo=item.grupo,
            administracion=item.administracion,
            sistemas=tuple(item.sistemas),
            plazas_libres=item.plazas_libres,
            plazas_promocion_interna=item.plazas_promocion_interna,
            plazo_dias_habiles=item.plazo_dias_habiles,
            enlace_oficial=item.enlace_oficial,
            published_at=item.published_at,
            procedencia=Procedencia(
                source_id=item.procedencia.source_id,
                quote=item.procedencia.quote,
            ),
        )
        for item in fixture.convocations
    )

    validate_registry(convocatorias, fuentes)
    return RegistroDeConvocatorias(fuentes=fuentes, convocatorias=convocatorias)
