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


class InvalidSourceError(OpoFuenteError):
    """La carpeta señalada no se puede inventariar. La API lo traduce a 400."""


class JobCancelledError(OpoFuenteError):
    """El trabajo se detuvo porque se pidió cancelarlo. No es un fallo."""


class InvalidBatchStateError(OpoFuenteError):
    """La operación no tiene sentido en el estado actual del lote. La API lo traduce a 409.

    Ejemplo: reintentar un lote que ya terminó bien, o que todavía se está copiando. Reintentar
    devolvería entradas a la cola mientras el worker trabaja sobre ellas.
    """

    def __init__(self, current: str, allowed: tuple[str, ...]) -> None:
        allowed_text = " o ".join(allowed)
        super().__init__(
            f"el lote está en estado «{current}»: solo se puede reintentar si está {allowed_text}"
        )
        self.current = current
        self.allowed = allowed
