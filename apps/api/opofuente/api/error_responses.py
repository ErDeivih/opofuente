"""Fragmentos de respuestas de error reutilizables por los routers.

En OpoFuente **todas** las respuestas de error son RFC 9457 servidas como
`application/problem+json` (api/errors.py) y `api/openapi.py` mueve el esquema documentado al
media type real. Aquí se declaran una sola vez para que el contrato no diverja entre rutas.

Declarar el 422 explícitamente no es cosmético: si no se hace, FastAPI documenta su propio
`HTTPValidationError` (con `detail: [...]`), que **no** es el cuerpo que devuelve esta aplicación
(que usa `ProblemDetail` con `field_errors`). Ver DEBT-002.
"""

from __future__ import annotations

from typing import Any

from opofuente.api.errors import ProblemDetail

_INTERNAL: dict[int | str, dict[str, Any]] = {
    500: {
        "model": ProblemDetail,
        "description": "Error interno inesperado (RFC 9457).",
    }
}

_NOT_FOUND: dict[int | str, dict[str, Any]] = {
    404: {
        "model": ProblemDetail,
        "description": "El recurso no existe.",
    }
}

_VALIDATION: dict[int | str, dict[str, Any]] = {
    422: {
        "model": ProblemDetail,
        "description": (
            "Parámetros inválidos. Cuerpo RFC 9457 (`ProblemDetail`) con `field_errors`."
        ),
    }
}

_FORBIDDEN_ORIGIN: dict[int | str, dict[str, Any]] = {
    403: {
        "model": ProblemDetail,
        "description": (
            "Origen no autorizado para modificar datos (`forbidden_origin`). Lo produce el "
            "middleware de comprobación de Origin en métodos de escritura."
        ),
    }
}

_INVALID_SOURCE: dict[int | str, dict[str, Any]] = {
    400: {
        "model": ProblemDetail,
        "description": (
            "La carpeta indicada no se puede usar (`invalid_source`): no existe, no es una "
            "carpeta, es relativa, es el directorio de datos de OpoFuente o no se puede leer."
        ),
    }
}

_INVALID_STATE: dict[int | str, dict[str, Any]] = {
    409: {
        "model": ProblemDetail,
        "description": (
            "La operación no vale para el estado actual del recurso (`invalid_state`). "
            "Por ejemplo, reintentar un lote que no está fallido ni cancelado."
        ),
    }
}

#: Errores que puede devolver cualquier ruta.
BASE_ERRORS: dict[int | str, dict[str, Any]] = {**_INTERNAL}

#: Errores de una ruta que busca un recurso por identificador.
RESOURCE_ERRORS: dict[int | str, dict[str, Any]] = {**_INTERNAL, **_NOT_FOUND, **_VALIDATION}

#: Errores de una ruta de escritura con identificador: añade el rechazo por Origin.
WRITE_ERRORS: dict[int | str, dict[str, Any]] = {
    **_INTERNAL,
    **_NOT_FOUND,
    **_VALIDATION,
    **_FORBIDDEN_ORIGIN,
}

#: Errores de las rutas de ingestión que reciben una carpeta del usuario.
INGESTION_WRITE_ERRORS: dict[int | str, dict[str, Any]] = {
    **WRITE_ERRORS,
    **_INVALID_SOURCE,
}

#: Errores **solo** de `POST /retry`, que es la única ruta que rechaza por estado del lote.
#: Cancelar no produce 409: sobre un lote ya terminado es una operación sin efecto que devuelve el
#: estado actual, así que documentarlo ahí sería documentar algo que no ocurre.
RETRY_ERRORS: dict[int | str, dict[str, Any]] = {
    **WRITE_ERRORS,
    **_INVALID_STATE,
}
