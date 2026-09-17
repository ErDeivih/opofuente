"""Errores de dominio. Sin dependencias de framework."""

from __future__ import annotations


class OpoFuenteError(Exception):
    """Base de todos los errores propios de la aplicación."""


class ConfigurationError(OpoFuenteError):
    """La configuración viola un invariante duro (por ejemplo, host no loopback)."""


class InvariantViolationError(OpoFuenteError):
    """Una regla de dominio se ha roto. Nunca debe silenciarse."""


class MappingMismatchError(InvariantViolationError):
    """El mapeo pedido no encaja con el fichero que se ha subido. La API lo traduce a 422.

    No es un fallo interno: quien importa ha elegido unas columnas que el fichero no trae, así que
    se dice **antes** de tocar la base y con el campo que hay que corregir (`field_errors`), en
    lugar de devolver un 500 por una regla que en realidad rompió la entrada.
    """

    def __init__(self, reason: str, *, field: str, code: str = "mapping_mismatch") -> None:
        super().__init__(reason)
        self.reason = reason
        self.field = field
        self.code = code


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


class ClassificationConflictError(OpoFuenteError):
    """La decisión no se puede aplicar en el estado actual de la propuesta. La API lo traduce a 409.

    Casos: aceptar algo ya rechazado, aceptar una propuesta de tema cuyo nodo no está en el programa
    sembrado, o deshacer una decisión que no existe. Nunca se aplica «a medias»: o se aplica, o se
    explica por qué no.
    """


class UnsafeContentError(OpoFuenteError):
    """El contenido se rechaza por seguridad. La API lo traduce a 400 `unsafe_content`.

    Casos: ZIP con rutas que escapan, ZIP bomba, anidamiento excesivo, XML con entidades externas o
    estructura que excede los límites del parser (DEBT-004).
    """

    def __init__(self, reason: str, *, code: str = "unsafe_content") -> None:
        super().__init__(reason)
        self.reason = reason
        self.code = code


class UrlRejectedError(OpoFuenteError):
    """La URL no se puede descargar con seguridad. La API lo traduce a 400 `url_rejected`.

    Casos: esquema que no es http/https, destino en red privada o loopback, redirección a un destino
    bloqueado, demasiadas redirecciones o respuesta por encima del límite.
    """

    def __init__(self, reason: str, *, code: str = "url_rejected") -> None:
        super().__init__(reason)
        self.reason = reason
        self.code = code
