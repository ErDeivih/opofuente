"""Errores de dominio. Sin dependencias de framework."""

from __future__ import annotations


class OpoFuenteError(Exception):
    """Base de todos los errores propios de la aplicación."""


class ConfigurationError(OpoFuenteError):
    """La configuración viola un invariante duro (por ejemplo, host no loopback)."""


class InvariantViolationError(OpoFuenteError):
    """Una regla de dominio se ha roto. Nunca debe silenciarse."""
