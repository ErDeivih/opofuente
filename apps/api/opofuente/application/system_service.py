"""Caso de uso: informar del estado del sistema y de sus capacidades reales.

Regla: nunca se declara operativa una capacidad que no se haya comprobado. Una capacidad
ausente se comunica como degradación explícita, no como error silencioso
(16_TRACEABILITY-AND-DEFINITION-OF-DONE §4).
"""

from __future__ import annotations

import logging
from collections.abc import Sequence

from opofuente.application.ports import CapabilityProvider, HealthProbe
from opofuente.domain.system import (
    CapabilitiesReport,
    Capability,
    CapabilityStatus,
    CheckResult,
    CheckStatus,
    Degradation,
    ReadinessReport,
)

logger = logging.getLogger(__name__)

_DEGRADATION_PREFIX: dict[CapabilityStatus, str] = {
    CapabilityStatus.DISABLED: "no configurado",
    CapabilityStatus.UNAVAILABLE: "no disponible",
    CapabilityStatus.CONFIGURED_UNVERIFIED: "configurado sin verificar",
    CapabilityStatus.PLANNED: "todavía no implementado",
}


class SystemService:
    """Compone sondas de salud y proveedores de capacidades."""

    def __init__(
        self,
        *,
        version: str,
        probes: Sequence[HealthProbe],
        capability_providers: Sequence[CapabilityProvider],
    ) -> None:
        self._version = version
        self._probes = tuple(probes)
        self._capability_providers = tuple(capability_providers)

    def readiness(self) -> ReadinessReport:
        """Ejecuta todas las sondas. Una sonda que falla no aborta el informe."""
        checks: list[CheckResult] = []
        for probe in self._probes:
            checks.append(self._run_probe(probe))
        return ReadinessReport(checks=tuple(checks))

    def capabilities(self) -> CapabilitiesReport:
        capabilities = tuple(
            capability
            for provider in self._capability_providers
            for capability in provider.provide()
        )
        degradations = tuple(
            _to_degradation(capability)
            for capability in capabilities
            if capability.status is not CapabilityStatus.ENABLED
        )
        return CapabilitiesReport(
            version=self._version,
            capabilities=capabilities,
            degradations=degradations,
        )

    @staticmethod
    def _run_probe(probe: HealthProbe) -> CheckResult:
        try:
            return probe.check()
        # Se captura Exception a propósito: una sonda rota debe degradar el informe,
        # nunca tumbar /health/ready ni filtrar la traza al cliente.
        except Exception as exc:
            logger.warning(
                "probe.crashed",
                extra={"probe": probe.name, "error_type": type(exc).__name__},
            )
            return CheckResult(
                name=probe.name,
                status=CheckStatus.FAILED,
                detail=f"comprobación interrumpida ({type(exc).__name__})",
            )


def _to_degradation(capability: Capability) -> Degradation:
    prefix = _DEGRADATION_PREFIX.get(capability.status, "degradado")
    if capability.status is CapabilityStatus.PLANNED and capability.planned_slice:
        message = f"{capability.label}: {prefix} (previsto en {capability.planned_slice})."
    else:
        message = f"{capability.label}: {prefix}. {capability.detail}".strip()
    return Degradation(code=f"{capability.id}.{capability.status.value}", message=message)
