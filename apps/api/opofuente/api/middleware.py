"""Middlewares ASGI propios.

- `CorrelationIdMiddleware`: asigna y devuelve un identificador por petición.
- `OriginCheckMiddleware`: rechaza escrituras con `Origin` no autorizado. La aplicación no
  tiene login en el MVP, así que la comprobación de Origin es la defensa CSRF disponible
  (08_API-CONTRACT §12, 09_SECURITY-PRIVACY-AND-RIGHTS §2).
- `SecurityHeadersMiddleware`: cabeceras de endurecimiento en las respuestas de la API.

Son ASGI puros (no `BaseHTTPMiddleware`) para no interferir con SSE en slices posteriores.
"""

from __future__ import annotations

from uuid import uuid4

from starlette.datastructures import Headers, MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from opofuente.api.errors import problem_response
from opofuente.infrastructure.correlation import reset_correlation_id, set_correlation_id

CORRELATION_HEADER = "x-correlation-id"
SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})
_MAX_CORRELATION_ID_LENGTH = 64

SECURITY_HEADERS: dict[str, str] = {
    "content-security-policy": (
        "default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'"
    ),
    "cross-origin-resource-policy": "same-origin",
    "referrer-policy": "no-referrer",
    "x-content-type-options": "nosniff",
    "x-frame-options": "DENY",
}


class CorrelationIdMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        incoming = Headers(scope=scope).get(CORRELATION_HEADER)
        correlation_id = (incoming or "").strip()[:_MAX_CORRELATION_ID_LENGTH] or str(uuid4())
        token = set_correlation_id(correlation_id)

        async def send_with_correlation_id(message: Message) -> None:
            if message["type"] == "http.response.start":
                MutableHeaders(scope=message).append(CORRELATION_HEADER, correlation_id)
            await send(message)

        try:
            await self.app(scope, receive, send_with_correlation_id)
        finally:
            reset_correlation_id(token)


class OriginCheckMiddleware:
    def __init__(self, app: ASGIApp, *, allowed_origins: tuple[str, ...]) -> None:
        self.app = app
        self._allowed_origins = frozenset(allowed_origins)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or scope["method"] in SAFE_METHODS:
            await self.app(scope, receive, send)
            return

        origin = Headers(scope=scope).get("origin")
        if origin is None or origin in self._allowed_origins:
            # Sin cabecera Origin (peticiones locales de herramientas) o origen autorizado.
            await self.app(scope, receive, send)
            return

        response = problem_response(
            status_code=403,
            detail="Origen no autorizado para modificar datos.",
            instance=str(scope.get("path", "")),
            code="forbidden_origin",
        )
        await response(scope, receive, send)


class SecurityHeadersMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_with_security_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                for name, value in SECURITY_HEADERS.items():
                    headers.setdefault(name, value)
            await send(message)

        await self.app(scope, receive, send_with_security_headers)
