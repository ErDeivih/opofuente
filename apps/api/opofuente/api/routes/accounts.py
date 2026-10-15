"""Las rutas de las cuentas: alta, acceso, recuperación, sesiones y baja (§8).

**Lo que este módulo tiene que conseguir, y es lo único que hay que mirar al leerlo:** que la
respuesta del alta sea la misma exista o no la dirección, que la del acceso sea la misma falle por
contraseña o por dirección desconocida, y que el testigo de sesión salga **solo** por una cookie
`HttpOnly` y nunca por el cuerpo. Todo lo demás es fontanería.

**La cookie.** `HttpOnly` (el JavaScript de la página no la lee), `SameSite` configurable —`lax` por
defecto, que ya impide que la mande una petición que venga de otro sitio— y `Secure` también
configurable, apagado porque la aplicación escucha en `http://127.0.0.1`. Esos tres valores y su
porqué están en `PARA-EL-PROPIETARIO.md`, porque el día que esto se sirva por HTTPS hay que encender
el tercero.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, Response, status

from opofuente.api.account_schemas import (
    AccountAcceptedSchema,
    AccountClosedSchema,
    AccountEventSchema,
    AccountMeSchema,
    AccountsAvailableSchema,
    AccountSchema,
    AccountSessionsSchema,
    EmailPasswordSchema,
    PasswordResetConfirmSchema,
    PasswordResetRequestSchema,
    account,
    account_session,
    event,
)
from opofuente.api.deps import AccountsServiceDep
from opofuente.api.error_responses import BASE_ERRORS, WRITE_ERRORS
from opofuente.api.session_gate import session_token_from_cookie
from opofuente.application.account_models import SessionCookie
from opofuente.domain.accounts import SESSION_COOKIE_NAME
from opofuente.domain.errors import InvalidCredentialsError

router = APIRouter()

#: Lo que contesta el alta siempre, sea la dirección nueva o no, y por qué es así está en el
#: encabezado del servicio. La frase no dice si la cuenta existía; dice qué hacer.
REGISTER_MESSAGE = (
    "Si esa dirección puede registrarse, ya puedes entrar con ella desde la pantalla de acceso. "
    "No se manda ningún correo de confirmación."
)

RESET_MESSAGE = (
    "Si esa dirección tiene cuenta, se ha creado un enlace de recuperación que caduca en una hora. "
    "Esta instalación no tiene servicio de correo, así que el enlace queda en el equipo del "
    "titular: pídeselo."
)


def _cookie(request: Request) -> str | None:
    return session_token_from_cookie(request.headers.get("cookie"))


def _put_session_cookie(response: Response, cookie: SessionCookie, token: str) -> None:
    """Pone la cookie de sesión con los valores que decidió el servidor, no la ruta.

    `httponly=True` no es un detalle de estilo: es lo que impide que un script de la página —propio
    o
    inyectado— lea el testigo y se lo lleve.
    """
    response.set_cookie(
        key=cookie.name,
        value=token,
        max_age=cookie.max_age,
        httponly=True,
        secure=cookie.secure,
        samesite=cookie.same_site,
        path=cookie.path,
    )


def _clear_session_cookie(response: Response, cookie: SessionCookie) -> None:
    response.delete_cookie(
        key=cookie.name,
        path=cookie.path,
        httponly=True,
        secure=cookie.secure,
        samesite=cookie.same_site,
    )


@router.get(
    "/accounts/configuration",
    response_model=AccountsAvailableSchema,
    responses=BASE_ERRORS,
    summary="¿Esta instalación tiene cuentas, y se puede estudiar sin ellas?",
    tags=["cuentas"],
)
def configuration(service: AccountsServiceDep) -> AccountsAvailableSchema:
    """Lo que la interfaz necesita para no ofrecer un acceso que no existe.

    **Se contesta siempre, también con las cuentas apagadas**: es justo lo que hay que poder saber
    antes de decidir qué enseñar.
    """
    return AccountsAvailableSchema(
        enabled=service.enabled,
        anonymous_study=True,
        session_cookie_name=SESSION_COOKIE_NAME,
        session_days=service.session_cookie.max_age // 86400,
        delivery_channel=service.delivery_channel,
    )


@router.post(
    "/accounts/register",
    response_model=AccountAcceptedSchema,
    status_code=status.HTTP_202_ACCEPTED,
    responses=WRITE_ERRORS,
    summary="Darse de alta",
    tags=["cuentas"],
)
def register(payload: EmailPasswordSchema, service: AccountsServiceDep) -> AccountAcceptedSchema:
    """Da de alta una cuenta. **La respuesta no dice si la dirección ya estaba.**

    Se contesta 202 y no 201 a propósito: aceptado no es creado, y quien pregunta no tiene por qué
    saber cuál de las dos cosas ha pasado. La cuenta, si es nueva, queda lista para entrar sin
    confirmar el correo: sin servicio de correo contratado no hay forma de confirmarlo, y fingir que
    se ha mandado un mensaje dejaría a quien se registra esperando algo que no va a llegar.
    """
    service.require_enabled()
    service.register(email=payload.email, password=payload.password)
    return AccountAcceptedSchema(message=REGISTER_MESSAGE)


@router.post(
    "/accounts/login",
    response_model=AccountMeSchema,
    responses=WRITE_ERRORS,
    summary="Entrar",
    tags=["cuentas"],
)
def login(
    payload: EmailPasswordSchema, request: Request, response: Response, service: AccountsServiceDep
) -> AccountMeSchema:
    """Comprueba la contraseña y abre sesión. El testigo sale **solo** por la cookie."""
    service.require_enabled()
    resultado = service.login(email=payload.email, password=payload.password)
    _put_session_cookie(response, service.session_cookie, resultado.session_token)
    return AccountMeSchema(
        account=account(resultado.account),
        session_expires_at=resultado.expires_at,
        events=[event(entrada) for entrada in service.history(resultado.session_token)],
    )


@router.post(
    "/accounts/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=WRITE_ERRORS,
    summary="Cerrar la sesión de esta pestaña",
    tags=["cuentas"],
)
def logout(request: Request, response: Response, service: AccountsServiceDep) -> Response:
    """Cierra la sesión. Se contesta 204 aunque no hubiera nada que cerrar: es idempotente."""
    service.require_enabled()
    service.logout(_cookie(request))
    _clear_session_cookie(response, service.session_cookie)
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@router.get(
    "/accounts/me",
    response_model=AccountMeSchema,
    responses=BASE_ERRORS,
    summary="Quién soy, hasta cuándo dura esta sesión y qué ha pasado con mi cuenta",
    tags=["cuentas"],
)
def me(request: Request, service: AccountsServiceDep) -> AccountMeSchema:
    """La identidad de la sesión. **Sin sesión, 401**: es la respuesta que no se puede fingir."""
    service.require_enabled()
    usuario = service.resolve(_cookie(request))
    if usuario is None:
        raise InvalidCredentialsError("no hay ninguna sesión abierta")
    sesiones = service.sessions(_cookie(request))
    actual = next((vista for vista in sesiones if vista.current), None)
    if actual is None:
        raise InvalidCredentialsError("la sesión se ha cerrado mientras se leía")
    return AccountMeSchema(
        account=account(usuario.account),
        session_expires_at=actual.expires_at,
        events=[event(entrada) for entrada in service.history(_cookie(request))],
    )


@router.delete(
    "/accounts/me",
    response_model=AccountClosedSchema,
    responses=WRITE_ERRORS,
    summary="Cerrar la cuenta y borrar sus datos",
    tags=["cuentas"],
)
def close_account(
    request: Request, response: Response, service: AccountsServiceDep
) -> AccountClosedSchema:
    """Da de baja la cuenta: borra lo suyo y deja constancia.

    Se devuelve **cuánto** se ha borrado de cada cosa: un «hecho» sin cifra no dice nada, y quien
    ejerce el derecho de supresión tiene derecho a saber qué se ha ido.
    """
    service.require_enabled()
    borrado = service.close(_cookie(request))
    _clear_session_cookie(response, service.session_cookie)
    return AccountClosedSchema(
        sessions=borrado.get("sessions", 0),
        study_rows=borrado.get("study_rows", 0),
        audit_events=borrado.get("audit_events", 0),
    )


@router.get(
    "/accounts/sessions",
    response_model=AccountSessionsSchema,
    responses=BASE_ERRORS,
    summary="Mis sesiones abiertas",
    tags=["cuentas"],
)
def sessions(request: Request, service: AccountsServiceDep) -> AccountSessionsSchema:
    return AccountSessionsSchema(
        sessions=[account_session(v) for v in service.sessions(_cookie(request))]
    )


@router.delete(
    "/accounts/sessions/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=WRITE_ERRORS,
    summary="Cerrar otra sesión mía",
    tags=["cuentas"],
)
def revoke_session(
    session_id: str, request: Request, response: Response, service: AccountsServiceDep
) -> Response:
    """Cierra otra sesión. **Nunca la que se está usando**: eso dejaría fuera a quien lo pide."""
    service.require_enabled()
    if not service.revoke(_cookie(request), session_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Esa sesión no existe, ya estaba cerrada o es la que estás usando ahora mismo.",
        )
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@router.get(
    "/accounts/events",
    response_model=list[AccountEventSchema],
    responses=BASE_ERRORS,
    summary="Lo que ha pasado con mi cuenta, auditado",
    tags=["cuentas"],
)
def events(request: Request, service: AccountsServiceDep) -> list[AccountEventSchema]:
    """El alta, los accesos, los cierres de sesión y la baja, cada uno con su fecha."""
    return [event(entrada) for entrada in service.history(_cookie(request))]


@router.post(
    "/accounts/password-resets",
    response_model=AccountAcceptedSchema,
    status_code=status.HTTP_202_ACCEPTED,
    responses=WRITE_ERRORS,
    summary="Pedir un enlace para cambiar la contraseña",
    tags=["cuentas"],
)
def request_reset(
    payload: PasswordResetRequestSchema, service: AccountsServiceDep
) -> AccountAcceptedSchema:
    """Crea el enlace. **La respuesta no dice si la dirección tiene cuenta.**"""
    service.require_enabled()
    service.request_reset(email=payload.email)
    return AccountAcceptedSchema(message=RESET_MESSAGE)


@router.post(
    "/accounts/password-resets/confirm",
    response_model=AccountSchema,
    responses=WRITE_ERRORS,
    summary="Cambiar la contraseña con el enlace",
    tags=["cuentas"],
)
def confirm_reset(
    payload: PasswordResetConfirmSchema, service: AccountsServiceDep
) -> AccountSchema:
    """Cambia la contraseña y **cierra las demás sesiones**: si no, el cambio no echa a nadie."""
    service.require_enabled()
    return account(service.confirm_reset(token=payload.token, password=payload.password))


__all__ = ["router"]
