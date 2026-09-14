"""Errores de dominio. Sin dependencias de framework."""

from __future__ import annotations


class OpoFuenteError(Exception):
    """Base de todos los errores propios de la aplicación."""


class ConfigurationError(OpoFuenteError):
    """La configuración viola un invariante duro (por ejemplo, host no loopback)."""


class InvariantViolationError(OpoFuenteError):
    """Una regla de dominio se ha roto. Nunca debe silenciarse."""


class NotFoundError(OpoFuenteError):
    """Se ha pedido algo que no existe. La API lo traduce a 404."""

    def __init__(self, resource: str, identifier: str) -> None:
        super().__init__(f"no existe {resource} con identificador {identifier}")
        self.resource = resource
        self.identifier = identifier
