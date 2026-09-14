"""Puertos consumidos por la capa de aplicación.

Toda integración (base de datos, OCR, almacén, proveedores IA) se declara aquí como
Protocol y se implementa en `opofuente.infrastructure`, de modo que el dominio no
conozca ninguna tecnología (02_ARCHITECTURE §7).
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from typing import Protocol, runtime_checkable

from opofuente.application.read_models import (
    ConvocationDetail,
    ConvocationSummary,
    CurriculumView,
    NodeDetail,
    OppositionDetail,
    OppositionSummary,
    SeedOutcome,
)
from opofuente.domain.profiles import Profile
from opofuente.domain.system import Capability, CheckResult


@runtime_checkable
class HealthProbe(Protocol):
    """Comprobación real de una dependencia para /health/ready."""

    name: str

    def check(self) -> CheckResult:
        """Devuelve el resultado de la comprobación. No debe lanzar excepciones."""
        ...


@runtime_checkable
class CapabilityProvider(Protocol):
    """Declara qué capacidades opcionales están disponibles en este proceso."""

    def provide(self) -> tuple[Capability, ...]: ...


@runtime_checkable
class Clock(Protocol):
    """Fuente de tiempo. Inyectable para poder probar sin depender del reloj real."""

    def now(self) -> datetime: ...


@runtime_checkable
class ProfileRepository(Protocol):
    """Acceso a oposiciones, convocatorias, programa y reglas de examen."""

    def list_oppositions(self) -> Sequence[OppositionSummary]: ...

    def get_opposition(self, opposition_id: str) -> OppositionDetail | None: ...

    def activate_opposition(self, opposition_id: str, *, now: datetime) -> OppositionSummary | None:
        """Marca una oposición como activa y desactiva el resto."""
        ...

    def list_convocations(self, opposition_id: str) -> Sequence[ConvocationSummary]: ...

    def get_convocation(self, convocation_id: str) -> ConvocationDetail | None: ...

    def get_curriculum(self, convocation_id: str) -> CurriculumView | None: ...

    def get_node(self, node_id: str) -> NodeDetail | None: ...

    def upsert_profile(self, profile: Profile, *, now: datetime) -> SeedOutcome:
        """Siembra idempotente: repetirla no duplica ni deja datos a medias."""
        ...
