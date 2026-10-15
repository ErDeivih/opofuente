"""Modelos de lectura y escritura de las cuentas (§8 del objetivo vivo).

Son datos planos, sin SQLAlchemy y sin FastAPI, para que las reglas y las rutas compartan una sola
forma de «esto es una cuenta» y no haya dos versiones del mismo objeto (una del repositorio y otra
dela respuesta). Ninguno de estos modelos tiene un campo para la contraseña ni para su resumen: lo
que
viaja hacia fuera no puede llevar lo que no está en el modelo.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal


@dataclass(frozen=True, slots=True)
class Account:
    """Una cuenta, tal como la ven las capas de arriba. **Sin** el resumen de la contraseña."""

    id: str
    email: str
    #: La dirección en su forma canónica. Viaja en el modelo porque hay dos sitios que la necesitan
    #: sin volver a la base: el nombre del fichero del enlace de recuperación y la comprobación de
    #: que la contraseña no es la propia dirección.
    email_normalized: str
    owner_id: str
    created_at: datetime
    password_changed_at: datetime


@dataclass(frozen=True, slots=True)
class AccountWithSecret:
    """Una cuenta **con** el resumen de su contraseña. Solo la usa la comprobación del acceso.

    Existe para que el resumen no se pueda colar por descuido en una respuesta: el tipo que devuelve
    «busca esta cuenta» es distinto del tipo que devuelve «esta es tu cuenta», así que para servir
    el resumen habría que escribirlo a propósito.
    """

    account: Account
    password_hash: str
    password_algo: str


@dataclass(frozen=True, slots=True)
class SessionView:
    """Una sesión abierta, tal como se enseña en «mi cuenta»."""

    id: str
    created_at: datetime
    last_seen_at: datetime
    expires_at: datetime
    current: bool


@dataclass(frozen=True, slots=True)
class SessionUser:
    """Quién está al otro lado: su cuenta, la sesión por la que entró y su dueño de progreso.

    `owner_id` viaja aquí y no se deduce en cada sitio porque es **lo que firma el progreso**: si
    dos partes del código lo dedujeran por su cuenta, un día discreparían y el progreso de una
    persona
    aparecería en la pantalla de otra.
    """

    account: Account
    session_id: str
    owner_id: str


@dataclass(frozen=True, slots=True)
class SessionCookie:
    """Cómo se pone la cookie de sesión. La decide el servidor; la ruta solo la aplica.

    Va en un modelo y no en tres constantes sueltas por la ruta porque las tres propiedades se
    declaran juntas o no se declaran: una cookie de sesión sin `HttpOnly` es una cookie que lee
    cualquier script de la página, y separar los campos invita a escribir dos y olvidar el tercero.
    """

    name: str
    max_age: int
    same_site: Literal["lax", "strict", "none"]
    secure: bool
    path: str = "/"


@dataclass(frozen=True, slots=True)
class RegisterOutcome:
    """Lo que se contesta al dar de alta, sea la dirección nueva o no.

    `created` **no** viaja en la respuesta: existe para la auditoría y las pruebas. Lo que se
    contesta es siempre lo mismo, porque decir «esa dirección ya está» es decir quién tiene cuenta
    aquí.
    """

    created: bool
    account: Account | None


@dataclass(frozen=True, slots=True)
class LoginOutcome:
    """El resultado de un acceso: la cuenta, el testigo de sesión y cuándo caduca.

    El testigo se devuelve **una sola vez** —aquí, para ponerlo en la cookie— y lo que se guarda es
    su resumen. Ni el modelo de la respuesta ni el de la base lo llevan.
    """

    account: Account
    session_token: str
    expires_at: datetime


@dataclass(frozen=True, slots=True)
class ResetRequestOutcome:
    """Lo que se sabe al pedir un enlace de recuperación.

    `token` es `None` cuando la dirección no tiene cuenta. La respuesta de la API es la misma en los
    dos casos; esto es lo que la prueba mira.
    """

    token: str | None
    account: Account | None
    expires_at: datetime | None


@dataclass(frozen=True, slots=True)
class ConsentSummary:
    """Cuántas decisiones se han tomado, contadas por desenlace. Sin ningún dato de quién."""

    total: int
    with_analytics: int
    with_preferences: int
    policy_version: int
    since: datetime | None


@dataclass(frozen=True, slots=True)
class AccountAuditEntry:
    """Una línea de la auditoría de la cuenta, ya legible para la pantalla."""

    kind: str
    occurred_at: datetime
    detail: dict[str, object]


@dataclass(frozen=True, slots=True)
class CountByLabel:
    """Un renglón del resumen de contadores: el tipo, la etiqueta y cuántas veces."""

    name: str
    label: str
    total: int


__all__ = [
    "Account",
    "AccountAuditEntry",
    "AccountWithSecret",
    "ConsentSummary",
    "CountByLabel",
    "LoginOutcome",
    "RegisterOutcome",
    "ResetRequestOutcome",
    "SessionCookie",
    "SessionUser",
    "SessionView",
]
