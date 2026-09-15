"""Descarga segura por URL (09_SECURITY §4, DEBT-004).

Reglas que aplica, todas comprobadas en las pruebas negativas:

1. **solo `http` y `https`**;
2. **resolución DNS y bloqueo de destinos internos**: loopback, privadas (RFC 1918), link-local
   (incluida la de metadatos `169.254.169.254`), multicast, reservadas, no especificadas y sus
   equivalentes IPv6 (incluidas las IPv4 embebidas y las mapeadas);
3. **cada redirección se vuelve a validar** desde cero, incluida su resolución DNS;
4. **tiempo, tamaño y número de redirecciones limitados**, leyendo por trozos y cortando en cuanto
   se pasa del tope;
5. **conexión fijada a la IP validada**: se abre el socket contra la dirección que se comprobó, no
   contra el nombre, así que un DNS que cambie de respuesta entre la comprobación y la conexión
   (rebinding) no puede colar una IP interna. El TLS sigue validando el nombre del certificado;
6. **User-Agent identificable** y **sin cookies ni autenticación automática**.

No se elude ninguna condición de uso: si un sitio responde 401/403/404, eso es el resultado.
"""

from __future__ import annotations

import http.client
import ipaddress
import socket
import ssl
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urljoin, urlsplit

from opofuente.domain.errors import UrlRejectedError

USER_AGENT = "OpoFuente/0.0 (biblioteca personal local; +https://localhost)"

#: Cabeceras que se envían siempre. Nada de cookies ni de cabeceras del navegador.
BASE_HEADERS: dict[str, str] = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/pdf,text/plain,*/*;q=0.8",
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.5",
}

#: Puertos que se aceptan si la URL no los dice. Cualquier otro puerto explícito se admite, pero el
#: destino tiene que pasar la comprobación de direcciones.
ALLOWED_SCHEMES = frozenset({"http", "https"})

#: Rangos de IPv4/IPv6 que nunca se descargan.
BLOCKED_NETWORKS: tuple[ipaddress.IPv4Network | ipaddress.IPv6Network, ...] = (
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("100.64.0.0/10"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.0.0.0/24"),
    ipaddress.ip_network("192.0.2.0/24"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("198.18.0.0/15"),
    ipaddress.ip_network("198.51.100.0/24"),
    ipaddress.ip_network("203.0.113.0/24"),
    ipaddress.ip_network("224.0.0.0/4"),
    ipaddress.ip_network("240.0.0.0/4"),
    ipaddress.ip_network("::/128"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
    ipaddress.ip_network("ff00::/8"),
    ipaddress.ip_network("2001:db8::/32"),
)

Resolver = Callable[[str], Iterable[str]]


def default_resolver(host: str) -> tuple[str, ...]:
    """Resuelve un nombre a todas sus direcciones (IPv4 e IPv6)."""
    try:
        infos = socket.getaddrinfo(host, None, proto=socket.IPPROTO_TCP)
    except socket.gaierror as error:
        raise UrlRejectedError("el nombre del destino no se pudo resolver") from error
    addresses: list[str] = []
    for info in infos:
        address = str(info[4][0])
        if address not in addresses:
            addresses.append(address)
    if not addresses:
        raise UrlRejectedError("el nombre del destino no tiene direcciones")
    return tuple(addresses)


@dataclass(frozen=True, slots=True)
class UrlLimits:
    """Límites de descarga. Salen de la configuración."""

    timeout_seconds: float
    max_bytes: int
    max_redirects: int


@dataclass(frozen=True, slots=True)
class ValidatedUrl:
    """URL comprobada: esquema, destino y direcciones permitidas."""

    url: str
    host: str
    port: int
    scheme: str
    addresses: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class FetchResult:
    """Resultado de una descarga segura, ya guardada en un fichero temporal."""

    initial_url: str
    final_url: str
    redirects: tuple[str, ...]
    status: int
    content_type: str | None
    size_bytes: int
    path: Path
    headers: dict[str, str] = field(default_factory=dict)


def is_blocked_address(address: str) -> bool:
    """¿La dirección está en un rango que no se descarga nunca?"""
    try:
        ip = ipaddress.ip_address(address)
    except ValueError:
        return True
    if ip.is_loopback or ip.is_private or ip.is_link_local or ip.is_multicast or ip.is_reserved:
        return True
    if ip.is_unspecified:
        return True
    if isinstance(ip, ipaddress.IPv6Address):
        # Direcciones IPv4 embebidas (`::ffff:10.0.0.1`) y `6to4`: se comprueba la IPv4 de dentro.
        if ip.ipv4_mapped is not None:
            return is_blocked_address(str(ip.ipv4_mapped))
        if ip.sixtofour is not None:
            return is_blocked_address(str(ip.sixtofour))
    return any(ip in network for network in BLOCKED_NETWORKS)


def validate_url(url: str, *, resolver: Resolver = default_resolver) -> ValidatedUrl:
    """Comprueba esquema, puerto y direcciones. Lanza `UrlRejectedError` si algo no vale."""
    candidate = url.strip()
    if not candidate:
        raise UrlRejectedError("indica una URL")
    parts = urlsplit(candidate)
    if parts.scheme.lower() not in ALLOWED_SCHEMES:
        raise UrlRejectedError("solo se admiten direcciones http o https")
    host = parts.hostname
    if not host:
        raise UrlRejectedError("la URL no dice a qué servidor hay que ir")
    if parts.username or parts.password:
        raise UrlRejectedError("no se admiten credenciales dentro de la URL")
    try:
        port = parts.port or (443 if parts.scheme.lower() == "https" else 80)
    except ValueError as error:
        raise UrlRejectedError("el puerto de la URL no es válido") from error

    addresses = tuple(resolver(host))
    if not addresses:
        raise UrlRejectedError("el nombre del destino no tiene direcciones")
    for address in addresses:
        if is_blocked_address(address):
            raise UrlRejectedError("el destino está en una red interna o reservada: no se descarga")
    return ValidatedUrl(
        url=candidate, host=host, port=port, scheme=parts.scheme.lower(), addresses=addresses
    )


class _PinnedConnection(http.client.HTTPConnection):
    """Conexión HTTP que se abre contra la IP ya validada, no contra el nombre.

    Así un cambio de DNS entre la comprobación y la conexión (rebinding) no puede llevar la petición
    a una dirección interna. Para https, el socket se envuelve con TLS usando el **nombre** como
    `server_hostname`, de modo que el certificado se sigue validando contra el nombre real.
    """

    def __init__(
        self,
        host: str,
        port: int,
        *,
        pinned_ip: str,
        timeout: float,
        context: ssl.SSLContext | None = None,
    ) -> None:
        super().__init__(host, port, timeout=timeout)
        self._pinned_ip = pinned_ip
        self._context = context

    def connect(self) -> None:
        self.sock = socket.create_connection((self._pinned_ip, self.port), self.timeout)
        if self._context is not None:
            self.sock = self._context.wrap_socket(self.sock, server_hostname=self.host)


class _HttpsPinnedConnection(_PinnedConnection, http.client.HTTPSConnection):
    """Variante https: misma fijación de IP y además TLS con contexto por defecto."""


def fetch_url(
    url: str,
    *,
    destination: Path,
    limits: UrlLimits,
    resolver: Resolver = default_resolver,
    chunk_bytes: int = 64 * 1024,
) -> FetchResult:
    """Descarga una URL siguiendo redirecciones, validando cada salto y con topes de tamaño.

    El contenido se escribe en `destination` (fichero temporal del llamante) y **no** se interpreta:
    guardar bytes no ejecuta nada.
    """
    initial = url
    current = url
    redirects: list[str] = []
    for _ in range(limits.max_redirects + 1):
        target = validate_url(current, resolver=resolver)
        status, headers, body_path, size = _fetch_once(
            target, destination=destination, limits=limits, chunk_bytes=chunk_bytes
        )
        location = headers.get("location")
        if status in {301, 302, 303, 307, 308}:
            if not location:
                raise UrlRejectedError("el destino redirige sin decir a dónde")
            if len(redirects) >= limits.max_redirects:
                raise UrlRejectedError("demasiadas redirecciones")
            current = urljoin(current, location)
            redirects.append(current)
            continue
        if status >= 400:
            raise UrlRejectedError(f"el destino respondió {status}")
        return FetchResult(
            initial_url=initial,
            final_url=target.url,
            redirects=tuple(redirects),
            status=status,
            content_type=headers.get("content-type"),
            size_bytes=size,
            path=body_path,
            headers=headers,
        )
    raise UrlRejectedError("demasiadas redirecciones")


def _fetch_once(
    target: ValidatedUrl,
    *,
    destination: Path,
    limits: UrlLimits,
    chunk_bytes: int,
) -> tuple[int, dict[str, str], Path, int]:
    """Una petición, con la IP fijada y el cuerpo limitado por tamaño."""
    context = ssl.create_default_context() if target.scheme == "https" else None
    connection: http.client.HTTPConnection
    if target.scheme == "https":
        connection = _HttpsPinnedConnection(
            target.host,
            target.port,
            pinned_ip=target.addresses[0],
            timeout=limits.timeout_seconds,
            context=context,
        )
    else:
        connection = _PinnedConnection(
            target.host,
            target.port,
            pinned_ip=target.addresses[0],
            timeout=limits.timeout_seconds,
        )
    path = urlsplit(target.url).path or "/"
    query = urlsplit(target.url).query
    request_path = f"{path}?{query}" if query else path

    destination.parent.mkdir(parents=True, exist_ok=True)
    size = 0
    try:
        connection.request("GET", request_path, headers=BASE_HEADERS)
        response = connection.getresponse()
        headers = {key.lower(): value for key, value in response.getheaders()}
        with destination.open("wb") as sink:
            while True:
                chunk = response.read(chunk_bytes)
                if not chunk:
                    break
                size += len(chunk)
                if size > limits.max_bytes:
                    sink.close()
                    destination.unlink(missing_ok=True)
                    raise UrlRejectedError(
                        f"la respuesta supera el límite de {limits.max_bytes} bytes"
                    )
                sink.write(chunk)
    except (http.client.HTTPException, OSError, ssl.SSLError) as error:
        destination.unlink(missing_ok=True)
        raise UrlRejectedError(f"la descarga falló ({type(error).__name__})") from error
    finally:
        connection.close()
    return response.status, headers, destination, size


def url_limits_from_settings(
    *, timeout_seconds: float, max_bytes: int, max_redirects: int
) -> UrlLimits:
    """Construye los límites desde la configuración validada."""
    return UrlLimits(
        timeout_seconds=timeout_seconds, max_bytes=max_bytes, max_redirects=max_redirects
    )
