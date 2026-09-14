"""Puertos consumidos por la capa de aplicación.

Toda integración (base de datos, OCR, almacén, proveedores IA) se declara aquí como
Protocol y se implementa en `opofuente.infrastructure`, de modo que el dominio no
conozca ninguna tecnología (02_ARCHITECTURE §7).
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

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
