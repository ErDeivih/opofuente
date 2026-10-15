"""Esquemas de las cuentas (§8 del objetivo vivo).

**Lo que no aparece aquí, y es lo importante.** No hay ningún campo para la contraseña en ninguna
respuesta: el resumen no viaja, y el tipo del que sale (`AccountWithSecret`) no es el que se sirve.
Tampoco viaja el `owner_id` —es una costura interna del progreso, no un dato del alumno— ni el
testigo
de sesión: ese sale una sola vez y por una cookie `HttpOnly`, no por el cuerpo de una respuesta que
acabe en el registro de nadie.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from opofuente.application.account_models import Account, AccountAuditEntry, SessionView


class EmailPasswordSchema(BaseModel):
    """Cuerpo común del alta y del acceso.

    Las longitudes son las del contrato: una dirección de más de 254 caracteres no es una dirección,
    y
    una contraseña de más de 256 no se admite porque el coste de derivarla crece con ella. Que el
    mínimo tenga que ser doce lo decide el dominio, no el esquema: así el mensaje de error dice
    **por
    qué** no vale, y no un «valor inválido» genérico.
    """

    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=256)


class PasswordResetRequestSchema(BaseModel):
    email: str = Field(min_length=3, max_length=254)


class PasswordResetConfirmSchema(BaseModel):
    token: str = Field(min_length=1, max_length=256)
    password: str = Field(min_length=1, max_length=256)


class AccountAcceptedSchema(BaseModel):
    """Respuesta **uniforme** del alta y de la petición de recuperación.

    Es la misma si la dirección era nueva o no, y por eso no tiene ningún campo que lo diga. El
    mensaje explica lo que hay que hacer a continuación sin informar de si la cuenta existía.
    """

    status: Literal["accepted"] = "accepted"
    message: str


class AccountSchema(BaseModel):
    """La cuenta tal como se enseña: su dirección y sus fechas. Nada más."""

    id: str
    email: str
    created_at: datetime
    password_changed_at: datetime


class AccountEventSchema(BaseModel):
    """Un movimiento auditado de la cuenta, con lo que se puede contar de él."""

    kind: str
    occurred_at: datetime
    detail: dict[str, object]


class AccountMeSchema(BaseModel):
    """Quién soy, hasta cuándo dura esta sesión y qué ha pasado con mi cuenta."""

    account: AccountSchema
    session_expires_at: datetime
    events: list[AccountEventSchema]


class AccountSessionSchema(BaseModel):
    """Una sesión abierta. `current` marca la que se está usando."""

    id: str
    created_at: datetime
    last_seen_at: datetime
    expires_at: datetime
    current: bool


class AccountSessionsSchema(BaseModel):
    sessions: list[AccountSessionSchema]


class AccountClosedSchema(BaseModel):
    """Lo que se ha borrado al cerrar la cuenta, contado. Un «hecho» sin cifra no dice nada."""

    status: Literal["closed"] = "closed"
    sessions: int
    study_rows: int
    audit_events: int


class AccountsAvailableSchema(BaseModel):
    """Si esta instalación tiene cuentas, y qué implica tenerlas o no.

    La interfaz lo necesita para no ofrecer un acceso que no existe. Lo que **no** dice es si la
    sesión actual es válida: eso lo contesta `GET /accounts/me` con un 200 o un 401, que es la única
    respuesta que no se puede fingir desde la pantalla.
    """

    enabled: bool
    anonymous_study: bool
    session_cookie_name: str
    session_days: int
    delivery_channel: str


def account(view: Account) -> AccountSchema:
    return AccountSchema(
        id=view.id,
        email=view.email,
        created_at=view.created_at,
        password_changed_at=view.password_changed_at,
    )


def event(entry: AccountAuditEntry) -> AccountEventSchema:
    return AccountEventSchema(kind=entry.kind, occurred_at=entry.occurred_at, detail=entry.detail)


def account_session(view: SessionView) -> AccountSessionSchema:
    return AccountSessionSchema(
        id=view.id,
        created_at=view.created_at,
        last_seen_at=view.last_seen_at,
        expires_at=view.expires_at,
        current=view.current,
    )


__all__ = [
    "AccountAcceptedSchema",
    "AccountClosedSchema",
    "AccountEventSchema",
    "AccountMeSchema",
    "AccountSchema",
    "AccountSessionSchema",
    "AccountSessionsSchema",
    "AccountsAvailableSchema",
    "EmailPasswordSchema",
    "PasswordResetConfirmSchema",
    "PasswordResetRequestSchema",
    "account",
    "account_session",
    "event",
]
