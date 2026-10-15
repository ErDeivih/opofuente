"""La puerta de las rutas cuando hay cuentas (§8): sin sesión, no se pasa.

**Cómo decide, y por qué así.** Con `OPOFUENTE_ACCOUNTS_ENABLED=1` la puerta **cierra por defecto**:
todo lo que no esté en la lista de lo público exige una sesión viva. Se hace al revés que casi todo
el
mundo —lista de lo prohibido— por dos motivos que se apoyan en hechos de este repositorio:

1. Las rutas del taller **no comparten prefijo**: son `/backups`, `/questions`, `/curriculum-nodes`,
   `/notes-review`, `/question-files`… Una lista de lo prohibido hay que escribirla entera y
   mantenerla, y el día que se añada una ruta de administración nueva y a nadie se le ocurra
   añadirla
   a la lista, la puerta queda abierta **en silencio**. Eso ya pasaría una vez; con el cierre por
   defecto no puede pasar.
2. Lo que tiene que seguir abierto es **corto y estable**: la salud, el alta y el acceso, los textos
   legales, el consentimiento, los contadores y **toda la zona de estudio**. Son seis prefijos y una
   prueba que los recorre.

**La zona de estudio queda abierta a propósito, con cuentas o sin ellas.** Es la regla que manda en
todo el bloque (§B del objetivo vivo): quien ya estudiaba sin cuenta tiene que seguir estudiando
igual. Si la puerta cerrara `/student/*`, encender las cuentas dejaría fuera exactamente a quien el
propietario no quiere dejar fuera.

**Con la bandera apagada la puerta no existe**: no se ejecuta ninguna comprobación, así que el
comportamiento es byte a byte el de antes. Una prueba lo comprueba.
"""

from __future__ import annotations

from collections.abc import Callable
from http.cookies import CookieError, SimpleCookie

from starlette.datastructures import Headers
from starlette.types import ASGIApp, Receive, Scope, Send

from opofuente.api.errors import problem_response
from opofuente.domain.accounts import SESSION_COOKIE_NAME

#: Rutas que se sirven **sin** sesión aunque las cuentas estén encendidas.
#:
#: Cada una está por un motivo, y conviene no añadir ninguna sin uno:
#: - la salud: la sonda de arranque no puede necesitar cuenta;
#: - el alta, el acceso y la recuperación: son la puerta de entrada, no pueden exigir haber entrado;
#: - los textos legales y el consentimiento (§9): hay que poder leerlos y decidir **antes** de tener
#:   cuenta, y desde luego antes de que se ponga ninguna cookie que no sea necesaria;
#: - los contadores (§10): el permiso ya se comprueba con la cookie de consentimiento, que es más
#:   estricto que una sesión para este caso concreto —un contador sin sujeto—;
#: - **la zona de estudio entera**: la regla que manda en el bloque.
PUBLIC_PREFIXES: tuple[str, ...] = (
    "/api/v1/health/",
    "/api/v1/accounts/register",
    "/api/v1/accounts/login",
    "/api/v1/accounts/password-resets",
    "/api/v1/platform/policy",
    "/api/v1/legal/",
    "/api/v1/analytics/events",
    "/api/v1/student/",
)

#: #: Y estas dos, exactas: el catálogo de capacidades y los ajustes los lee la pantalla de estado
#: antes
#: de que nadie entre. Ninguna de las dos enseña un dato de nadie.
PUBLIC_EXACT: tuple[str, ...] = ("/api/v1/capabilities", "/api/v1/settings")


def is_public_path(path: str) -> bool:
    """¿Esta ruta se sirve sin sesión?"""
    if path in PUBLIC_EXACT:
        return True
    return any(path.startswith(prefijo) for prefijo in PUBLIC_PREFIXES)


class SessionGateMiddleware:
    """Exige una sesión viva para todo lo que no sea público, cuando hay cuentas.

    `is_live` se inyecta en vez de construir el servicio aquí: el middleware es ASGI puro y no sabe
    de
    servicios; lo que sabe es que hay una cookie y que alguien puede decir si vale.
    """

    def __init__(
        self,
        app: ASGIApp,
        *,
        enabled: Callable[[], bool],
        is_live: Callable[[str | None], bool],
        cookie_name: str = SESSION_COOKIE_NAME,
    ) -> None:
        self.app = app
        self._enabled = enabled
        self._is_live = is_live
        self._cookie_name = cookie_name

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or not self._enabled():
            await self.app(scope, receive, send)
            return

        path = str(scope.get("path", ""))
        if not path.startswith("/api/v1") or is_public_path(path):
            await self.app(scope, receive, send)
            return

        if self._is_live(self._token_from(scope)):
            await self.app(scope, receive, send)
            return

        response = problem_response(
            status_code=401,
            detail=(
                "Esta operación necesita una sesión abierta. Entra con tu cuenta o, si esta "
                "instalación no tiene cuentas, no deberías estar viendo este mensaje."
            ),
            instance=path,
            code="session_required",
        )
        await response(scope, receive, send)

    def _token_from(self, scope: Scope) -> str | None:
        """El testigo de la cookie de sesión, leído con el analizador de cookies de la biblioteca.

        Se lee a mano y no con `request.cookies` porque aquí todavía no hay `Request`: esto es ASGI.
        `SimpleCookie` es el mismo analizador que usa Starlette por dentro, así que una cookie con
        formato raro se descarta igual en los dos sitios.
        """
        crudo = Headers(scope=scope).get("cookie")
        if not crudo:
            return None
        jarra: SimpleCookie = SimpleCookie()
        try:
            jarra.load(crudo)
        except CookieError:
            # Una cookie con formato ilegible es una cookie que no vale: se trata como si no
            # estuviera, que es lo que hará también la ruta que la lea.
            return None
        galleta = jarra.get(self._cookie_name)
        return None if galleta is None else galleta.value


def session_token_from_cookie(
    cookie_header: str | None, *, name: str = SESSION_COOKIE_NAME
) -> str | None:
    """El testigo de sesión de una cabecera `Cookie`, para las rutas que sí tienen `Request`.

    Se comparte con el middleware para que los dos lean la cookie **igual**: dos lecturas distintas
    de
    la misma cookie es la forma clásica de que una puerta y una ruta no coincidan.
    """
    if not cookie_header:
        return None
    jarra: SimpleCookie = SimpleCookie()
    try:
        jarra.load(cookie_header)
    except CookieError:
        return None
    galleta = jarra.get(name)
    return None if galleta is None else galleta.value


__all__ = [
    "PUBLIC_EXACT",
    "PUBLIC_PREFIXES",
    "SessionGateMiddleware",
    "is_public_path",
    "session_token_from_cookie",
]
