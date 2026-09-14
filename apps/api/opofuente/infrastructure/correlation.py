"""Identificador de correlación por petición y por trabajo.

Vive en un ContextVar para que el formateador de logs lo incluya sin pasarlo a mano y
sin arriesgar contenido sensible.
"""

from __future__ import annotations

from contextvars import ContextVar, Token

_correlation_id: ContextVar[str | None] = ContextVar("opofuente_correlation_id", default=None)


def set_correlation_id(value: str) -> Token[str | None]:
    return _correlation_id.set(value)


def reset_correlation_id(token: Token[str | None]) -> None:
    _correlation_id.reset(token)


def get_correlation_id() -> str | None:
    return _correlation_id.get()
