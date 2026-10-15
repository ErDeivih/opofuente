"""Errores HTTP en formato RFC 9457 (`application/problem+json`).

Contrato (08_API-CONTRACT §1): `type`, `title`, `status`, `detail`, `instance`, `code`,
`correlation_id` y `field_errors` opcional. Los mensajes nunca exponen rutas completas,
contenido importado, prompts ni claves.
"""

from __future__ import annotations

import logging
from collections.abc import Sequence

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from starlette.exceptions import HTTPException as StarletteHTTPException

from opofuente.domain.errors import (
    AccountsDisabledError,
    AttemptFrozenError,
    ClassificationConflictError,
    ConsentRequiredError,
    InvalidAccountInputError,
    InvalidAnswerError,
    InvalidBatchStateError,
    InvalidCredentialsError,
    InvalidReviewError,
    InvalidSourceError,
    InvalidStateError,
    LegalDisabledError,
    MappingMismatchError,
    NotFoundError,
    OpoFuenteError,
    SessionStateError,
    TooManyAttemptsError,
    UnsafeContentError,
    UnsupportedError,
    UrlRejectedError,
)
from opofuente.infrastructure.correlation import get_correlation_id

logger = logging.getLogger(__name__)

PROBLEM_MEDIA_TYPE = "application/problem+json"

_ERROR_CODES: dict[int, str] = {
    400: "bad_request",
    401: "unauthorized",
    403: "forbidden",
    404: "not_found",
    405: "method_not_allowed",
    408: "timeout",
    409: "conflict",
    422: "validation_error",
    429: "too_many_requests",
    500: "internal_error",
    503: "not_ready",
}

_ERROR_TITLES: dict[int, str] = {
    400: "Bad Request",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not Found",
    405: "Method Not Allowed",
    408: "Request Timeout",
    409: "Conflict",
    422: "Unprocessable Entity",
    429: "Too Many Requests",
    500: "Internal Server Error",
    503: "Service Unavailable",
}


class FieldError(BaseModel):
    field: str
    message: str


class ProblemDetail(BaseModel):
    """Cuerpo de error del contrato."""

    type: str = "about:blank"
    title: str
    status: int = Field(ge=100, le=599)
    detail: str
    instance: str
    code: str
    correlation_id: str
    field_errors: list[FieldError] | None = None


def problem_response(
    *,
    status_code: int,
    detail: str,
    instance: str,
    code: str | None = None,
    title: str | None = None,
    field_errors: Sequence[FieldError] | None = None,
) -> JSONResponse:
    """Construye la respuesta de error del contrato."""
    problem = ProblemDetail(
        title=title or _ERROR_TITLES.get(status_code, "Error"),
        status=status_code,
        detail=detail,
        instance=instance,
        code=code or _ERROR_CODES.get(status_code, "error"),
        correlation_id=get_correlation_id() or "",
        field_errors=list(field_errors) if field_errors else None,
    )
    return problem_response_from(problem)


def problem_response_from(problem: ProblemDetail) -> JSONResponse:
    """Serializa un problema ya construido, incluidas las extensiones de sus subclases.

    Permite que el cuerpo servido sea exactamente el esquema documentado (por ejemplo
    `ReadinessProblem` con `checks`), en lugar de añadir campos sueltos por fuera del modelo.
    Si el problema no trae identificador de correlación, se toma el de la petición.
    """
    resolved = (
        problem
        if problem.correlation_id
        else problem.model_copy(update={"correlation_id": get_correlation_id() or ""})
    )
    return JSONResponse(
        status_code=resolved.status,
        content=resolved.model_dump(exclude_none=True),
        media_type=PROBLEM_MEDIA_TYPE,
    )


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(StarletteHTTPException)
    async def _http_exception_handler(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        detail = (
            exc.detail
            if isinstance(exc.detail, str)
            else _ERROR_TITLES.get(exc.status_code, "Error")
        )
        return problem_response(
            status_code=exc.status_code,
            detail=detail,
            instance=request.url.path,
        )

    @app.exception_handler(RequestValidationError)
    async def _validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        field_errors = [
            FieldError(
                field=".".join(str(part) for part in error.get("loc", ())),
                message=str(error.get("msg", "valor inválido")),
            )
            for error in exc.errors()
        ]
        return problem_response(
            status_code=422,
            detail="La petición no cumple el contrato.",
            instance=request.url.path,
            field_errors=field_errors,
        )

    @app.exception_handler(OpoFuenteError)
    async def _domain_exception_handler(request: Request, exc: OpoFuenteError) -> JSONResponse:
        if isinstance(exc, NotFoundError):
            return problem_response(
                status_code=404,
                detail=f"No existe {exc.resource} con ese identificador.",
                instance=request.url.path,
                code="not_found",
            )
        if isinstance(exc, AttemptFrozenError):
            # El intento ya está registrado: el contrato lo dice con su propio código, porque no es
            # lo mismo que un conflicto de clasificación y la pantalla reacciona distinto.
            return problem_response(
                status_code=409,
                detail=str(exc),
                instance=request.url.path,
                code="attempt_frozen",
            )
        if isinstance(exc, SessionStateError):
            return problem_response(
                status_code=409,
                detail=str(exc),
                instance=request.url.path,
                code="invalid_session_state",
            )
        if isinstance(exc, UnsupportedError):
            return problem_response(
                status_code=409,
                detail=str(exc),
                instance=request.url.path,
                code="unsupported",
            )
        if isinstance(exc, InvalidAnswerError):
            return problem_response(
                status_code=422,
                detail=str(exc),
                instance=request.url.path,
                code=exc.code,
                field_errors=[FieldError(field=exc.field, message=exc.reason)],
            )
        if isinstance(exc, InvalidReviewError):
            # Rechazar los apuntes de un tema sin motivo, o decidir sobre un tema sin texto: es la
            # misma familia que una respuesta inválida —entrada que no vale, con su campo— y se
            # contesta igual, con `field_errors`, para que la pantalla sepa qué señalar.
            return problem_response(
                status_code=422,
                detail=str(exc),
                instance=request.url.path,
                code=exc.code,
                field_errors=[FieldError(field=exc.field, message=exc.reason)],
            )
        if isinstance(exc, InvalidAccountInputError):
            # §8: un correo sin forma de correo o una contraseña demasiado corta son entrada
            # inválida, con su campo, y se contestan como cualquier otra (422 con `field_errors`)
            # en lugar de con un 500 por una regla que rompió quien escribía.
            return problem_response(
                status_code=422,
                detail=str(exc),
                instance=request.url.path,
                code=exc.code,
                field_errors=[FieldError(field=exc.field, message=exc.reason)],
            )
        if isinstance(exc, ConsentRequiredError):
            return problem_response(
                status_code=403,
                detail=str(exc),
                instance=request.url.path,
                code="consent_required",
            )
        if isinstance(exc, LegalDisabledError):
            return problem_response(
                status_code=404,
                detail="Esta instalación no sirve los textos legales ni el aviso de cookies.",
                instance=request.url.path,
                code="not_found",
            )
        if isinstance(exc, AccountsDisabledError):
            # Con la bandera apagada la función **no existe**: no hay cuentas, ni rutas vivas, ni
            # nada que alcanzar de otra forma. Se contesta 404 y no 403 por eso mismo.
            return problem_response(
                status_code=404,
                detail="Esta instalación no tiene cuentas activadas.",
                instance=request.url.path,
                code="not_found",
            )
        if isinstance(exc, InvalidCredentialsError):
            # Un solo texto para «ese correo no está» y «esa contraseña no es»: distinguirlos sería
            # decir quién tiene cuenta aquí (ver el docstring del error).
            return problem_response(
                status_code=401,
                detail=str(exc),
                instance=request.url.path,
                code="invalid_credentials",
            )
        if isinstance(exc, TooManyAttemptsError):
            # El 429 lleva `Retry-After`: un «demasiados intentos» sin decir cuándo se puede volver
            # deja sin salida a quien de verdad se equivocó de contraseña.
            respuesta = problem_response(
                status_code=429,
                detail=str(exc),
                instance=request.url.path,
                code="too_many_attempts",
            )
            respuesta.headers["Retry-After"] = str(exc.retry_after_seconds)
            return respuesta
        if isinstance(exc, MappingMismatchError):
            # El 422 de esta aplicación siempre lleva `field_errors`, así que el mapeo que hay que
            # corregir se dice igual que el de una validación de esquema. Va antes que el resto de
            # invariantes porque sí es culpa de la entrada, no del programa.
            return problem_response(
                status_code=422,
                detail=str(exc),
                instance=request.url.path,
                code=exc.code,
                field_errors=[FieldError(field=exc.field, message=exc.reason)],
            )
        if isinstance(exc, InvalidSourceError):
            return problem_response(
                status_code=400,
                detail=str(exc),
                instance=request.url.path,
                code="invalid_source",
            )
        if isinstance(exc, InvalidBatchStateError):
            return problem_response(
                status_code=409,
                detail=str(exc),
                instance=request.url.path,
                code="invalid_state",
            )
        if isinstance(exc, InvalidStateError):
            return problem_response(
                status_code=409,
                detail=str(exc),
                instance=request.url.path,
                code="invalid_state",
            )
        if isinstance(exc, ClassificationConflictError):
            return problem_response(
                status_code=409,
                detail=str(exc),
                instance=request.url.path,
                code="classification_conflict",
            )
        if isinstance(exc, UnsafeContentError):
            return problem_response(
                status_code=400,
                detail=str(exc),
                instance=request.url.path,
                code=exc.code,
            )
        if isinstance(exc, UrlRejectedError):
            return problem_response(
                status_code=400,
                detail=str(exc),
                instance=request.url.path,
                code=exc.code,
            )
        logger.error(
            "request.domain_error",
            extra={"error_type": type(exc).__name__, "path": request.url.path},
        )
        return problem_response(
            status_code=500,
            detail="Error interno de la aplicación.",
            instance=request.url.path,
        )

    @app.exception_handler(Exception)
    async def _unexpected_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.error(
            "request.unhandled_error",
            extra={"error_type": type(exc).__name__, "path": request.url.path},
        )
        return problem_response(
            status_code=500,
            detail="Error interno de la aplicación.",
            instance=request.url.path,
        )
