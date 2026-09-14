"""Value objects de estado del sistema (health y capacidades).

Puros: sin pydantic, sin FastAPI y sin acceso a disco. La API traduce estos objetos a DTO.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class CheckStatus(StrEnum):
    OK = "ok"
    FAILED = "failed"


class CapabilityStatus(StrEnum):
    """Estado real de una capacidad. Nada se declara operativo sin comprobarlo."""

    ENABLED = "enabled"
    """Comprobado y utilizable en este proceso."""

    DISABLED = "disabled"
    """No configurado. La aplicación funciona sin ello."""

    UNAVAILABLE = "unavailable"
    """Configurado o previsto, pero no utilizable ahora mismo."""

    CONFIGURED_UNVERIFIED = "configured_unverified"
    """Configurado, sin verificación real todavía. No equivale a funcionar."""

    PLANNED = "planned"
    """Corresponde a un slice posterior. No existe todavía."""


@dataclass(frozen=True, slots=True)
class CheckResult:
    name: str
    status: CheckStatus
    detail: str

    @property
    def ok(self) -> bool:
        return self.status is CheckStatus.OK


@dataclass(frozen=True, slots=True)
class ReadinessReport:
    checks: tuple[CheckResult, ...]

    @property
    def ready(self) -> bool:
        return all(check.ok for check in self.checks)


@dataclass(frozen=True, slots=True)
class Capability:
    id: str
    label: str
    status: CapabilityStatus
    detail: str
    planned_slice: str | None = None


@dataclass(frozen=True, slots=True)
class Degradation:
    code: str
    message: str


@dataclass(frozen=True, slots=True)
class CapabilitiesReport:
    version: str
    capabilities: tuple[Capability, ...]
    degradations: tuple[Degradation, ...]

    @property
    def by_id(self) -> dict[str, Capability]:
        return {capability.id: capability for capability in self.capabilities}
