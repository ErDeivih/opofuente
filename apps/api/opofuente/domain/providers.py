"""Clasificación del destino real de cada proveedor (DEBT-001, 09_SECURITY §3).

El problema que resuelve este módulo es de **información al usuario**, no de seguridad: el booleano
`sends_data_off_device` decía «sale del equipo» a un proveedor que apunta a `127.0.0.1` y no decía
nada del proveedor de embeddings. La pantalla de Ajustes tiene que poder contestar dos preguntas
distintas:

1. ¿este proveedor está configurado? (`disabled`)
2. si lo está, ¿el contenido sale de este equipo? (`local` / `remote` / `unknown`)

La clasificación se calcula sobre el **endpoint efectivo**, no sobre el nombre del proveedor:
`ollama` apuntando a una IP pública es remoto, y `openai_compatible` apuntando a `127.0.0.1` no
sale del equipo. Cuando no se puede determinar, la respuesta es `unknown` y **nunca** se presenta
como `local`: decir «no sale de tu equipo» sin poder comprobarlo sería la peor respuesta posible.
"""

from __future__ import annotations

import ipaddress
from dataclasses import dataclass
from enum import StrEnum
from urllib.parse import urlsplit


class DataDestination(StrEnum):
    """Dónde acaba el contenido que se manda a un proveedor."""

    DISABLED = "disabled"
    LOCAL = "local"
    REMOTE = "remote"
    UNKNOWN = "unknown"


#: Nombres que en una red local significan «este equipo» sin resolverlos por DNS.
_LOOPBACK_NAMES = frozenset({"localhost", "127.0.0.1", "::1"})


@dataclass(frozen=True, slots=True)
class DestinationReason:
    """El destino y **por qué**, que es lo que la pantalla enseña junto al estado."""

    destination: DataDestination
    reason: str
    endpoint: str | None = None


def _is_private_address(address: str) -> bool:
    try:
        ip = ipaddress.ip_address(address)
    except ValueError:
        return False
    if isinstance(ip, ipaddress.IPv6Address):
        if ip.ipv4_mapped is not None:
            return _is_private_address(str(ip.ipv4_mapped))
        if ip.sixtofour is not None:
            return _is_private_address(str(ip.sixtofour))
    return ip.is_loopback or ip.is_private or ip.is_link_local


def classify_endpoint(url: str | None) -> DestinationReason:
    """Clasifica un endpoint por su URL **resuelta**, sin hacer ninguna conexión.

    `local` significa: la dirección del endpoint es este equipo o la red privada declarada como
    propia (loopback, 10/8, 172.16/12, 192.168/16, link-local). Cualquier otra dirección es
    `remote`. Un endpoint que no es una URL con host es `unknown`: no se adivina.
    """
    if url is None or not url.strip():
        return DestinationReason(DataDestination.DISABLED, "sin endpoint configurado")
    partes = urlsplit(url.strip())
    if partes.scheme.lower() not in {"http", "https"} or not partes.hostname:
        return DestinationReason(
            DataDestination.UNKNOWN,
            "el endpoint no es una dirección http(s) con servidor: no se puede saber el destino",
            endpoint=url,
        )
    host = partes.hostname.strip().lower()
    if host in _LOOPBACK_NAMES:
        return DestinationReason(
            DataDestination.LOCAL,
            "el endpoint apunta a este equipo (loopback): el contenido no sale de aquí",
            endpoint=host,
        )
    if _is_private_address(host):
        return DestinationReason(
            DataDestination.LOCAL,
            "el endpoint apunta a una dirección de red privada: el contenido no sale a internet",
            endpoint=host,
        )
    return DestinationReason(
        DataDestination.REMOTE,
        "el endpoint apunta a un servidor fuera de este equipo: el contenido se envía a un tercero",
        endpoint=host,
    )


def classify_provider(
    *,
    name: str,
    provider: str,
    endpoint: str | None,
    needs_endpoint: bool = True,
) -> DestinationReason:
    """Clasifica un proveedor según su configuración.

    `disabled` no es un destino: es «no hay proveedor», y se dice así para no confundirlo con
    «no sale del equipo». Un proveedor activo **sin** endpoint es `unknown`: está configurado y no
    se puede saber a dónde iría.
    """
    if provider == "disabled":
        return DestinationReason(
            DataDestination.DISABLED, f"{name} no está configurado: no se envía nada"
        )
    if needs_endpoint and (endpoint is None or not endpoint.strip()):
        return DestinationReason(
            DataDestination.UNKNOWN,
            f"{name} está configurado ({provider}) pero no declara endpoint: "
            "no se puede determinar el destino",
        )
    return classify_endpoint(endpoint)


def sends_content_off_device(reason: DestinationReason) -> bool:
    """¿Esta clasificación implica que el contenido puede salir del equipo?

    `unknown` cuenta como que sí: es la respuesta conservadora cuando no se puede comprobar.
    """
    return reason.destination in (DataDestination.REMOTE, DataDestination.UNKNOWN)


__all__ = [
    "DataDestination",
    "DestinationReason",
    "classify_endpoint",
    "classify_provider",
    "sends_content_off_device",
]
