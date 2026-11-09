"""Telemetría propia del despliegue de demo: qué pantallas se usan y qué errores ve el navegador.

**Qué NO se guarda aquí, nunca** (no forma parte del esquema, así que no puede colarse por un
campo de más):

- la IP ni ningún dato derivado de la conexión;
- el `User-Agent`, cookies, `Referer` ni el resto de cabeceras;
- el contenido de documentos, preguntas, respuestas o texto pegado;
- la URL: solo el **nombre estable de la pantalla**, validado contra una lista blanca;
- rutas absolutas del disco en el mensaje: se sustituyen por `[ruta]` antes de contar;
- cualquier otro campo del cuerpo: Pydantic lo ignora, no hay `dict` libre en el modelo.

**Qué sí se guarda y dónde:** unos contadores en memoria del proceso (total, por tipo, por pantalla
y hasta 20 errores recientes con mensaje corto y hora), protegidos por un `threading.Lock`. No hay
tabla, migración, base de datos ni servicio externo. **Al reiniciar el proceso se pierde todo**: es
observabilidad de demo, no analítica histórica.

Límites: cuerpo de como mucho 4096 bytes (413 si lo supera) y mensaje recortado a 200 caracteres.
Los eventos aceptados responden **202**.
"""

from __future__ import annotations

import re
from typing import Any

from fastapi import APIRouter, Request, Response
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

from opofuente.api.deps import TelemetryStoreDep
from opofuente.api.error_responses import BASE_ERRORS, WRITE_WITHOUT_RESOURCE_ERRORS
from opofuente.api.errors import ProblemDetail, problem_response
from opofuente.api.telemetry_schemas import (
    TelemetryEventSchema,
    TelemetrySummarySchema,
)

router = APIRouter(prefix="/telemetry", tags=["telemetría"])

#: Tope del cuerpo de un evento. Un evento legítimo ocupa unos pocos cientos de bytes.
MAX_EVENT_BYTES = 4096

#: Tope del mensaje de error que se conserva (el resto se descarta, no se rechaza).
MAX_MESSAGE_CHARS = 200

_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b-\x1f\x7f]")
_WHITESPACE = re.compile(r"\s+")
#: Ruta absoluta de Windows (`C:\...`), recurso de red (`\\servidor\...`) y ruta POSIX (`/...`).
_WINDOWS_PATH = re.compile(r"(?i)\b[a-z]:[\\/][^\s\"'<>|]*")
_UNC_PATH = re.compile(r"\\\\[^\s\"'<>|]+")
_POSIX_PATH = re.compile(r"(?<![\w.:/])/(?:[^\s/\"'<>|]+/)*[^\s/\"'<>|]*")
_REDACTED_PATH = "[ruta]"

_EVENT_RESPONSES: dict[int | str, dict[str, Any]] = {
    **WRITE_WITHOUT_RESOURCE_ERRORS,
    413: {
        "model": ProblemDetail,
        "description": (
            f"El cuerpo supera el límite de {MAX_EVENT_BYTES} bytes y se rechaza sin contar "
            "(`payload_too_large`)."
        ),
    },
}


@router.post(
    "/events",
    status_code=202,
    response_class=Response,
    responses=_EVENT_RESPONSES,
    summary="Acepta un evento de telemetría (pantalla vista o error)",
)
async def record_event(request: Request, store: TelemetryStoreDep) -> Response:
    """Cuenta un `page_view` o un `error`.

    `screen` tiene que estar en la lista blanca (`TelemetryScreen`): una pantalla desconocida se
    rechaza con 422 y no crea ninguna entrada nueva. El mensaje de un error se sanea (sin rutas
    absolutas) y se recorta a 200 caracteres antes de guardarse; el cuerpo de la petición está
    acotado a 4096 bytes.

    Responder 202 significa «aceptado y contado», no «guardado»: no hay persistencia.
    """
    raw = await _read_limited_body(request)
    if raw is None:
        return problem_response(
            status_code=413,
            title="Content Too Large",
            detail=(
                "El evento de telemetría supera el límite de "
                f"{MAX_EVENT_BYTES} bytes y no se ha contado."
            ),
            instance=request.url.path,
            code="payload_too_large",
        )

    try:
        payload = TelemetryEventSchema.model_validate_json(raw)
    except ValidationError as error:
        # Se reutiliza el manejador de validación de la aplicación para que el 422 sea el mismo
        # `ProblemDetail` con `field_errors` que documenta el contrato.
        raise RequestValidationError(error.errors()) from error

    store.record(payload.type, payload.screen, _sanitize_message(payload.message))
    return Response(status_code=202)


@router.get(
    "/summary",
    response_model=TelemetrySummarySchema,
    responses=BASE_ERRORS,
    summary="Resumen de la telemetría en memoria (se pierde al reiniciar)",
)
def read_summary(store: TelemetryStoreDep) -> TelemetrySummarySchema:
    """Totales por tipo y por pantalla, y hasta 20 errores recientes ya saneados.

    Es una foto del proceso actual: arranca a cero en cada reinicio. No incluye IP, `User-Agent`,
    URL, contenido ni nada que no sea pantalla, mensaje corto y hora.
    """
    return store.summary()


async def _read_limited_body(request: Request) -> bytes | None:
    """Lee el cuerpo sin pasar de `MAX_EVENT_BYTES`; devuelve `None` si lo supera.

    Se comprueba primero `Content-Length` (rechazo barato) y después el tamaño real mientras se lee,
    para que un cuerpo sin longitud declarada (chunked) tampoco pueda crecer sin límite.
    """
    declared = request.headers.get("content-length")
    if declared is not None:
        try:
            if int(declared) > MAX_EVENT_BYTES:
                return None
        except ValueError:
            return None

    chunks: list[bytes] = []
    total = 0
    async for chunk in request.stream():
        total += len(chunk)
        if total > MAX_EVENT_BYTES:
            return None
        chunks.append(chunk)
    return b"".join(chunks)


def _sanitize_message(message: str | None) -> str | None:
    """Deja un mensaje corto, en una línea y sin rutas absolutas (ni de Windows ni POSIX)."""
    if message is None:
        return None
    text = _CONTROL_CHARS.sub(" ", message)
    text = _WHITESPACE.sub(" ", text).strip()
    text = _WINDOWS_PATH.sub(_REDACTED_PATH, text)
    text = _UNC_PATH.sub(_REDACTED_PATH, text)
    text = _POSIX_PATH.sub(_REDACTED_PATH, text)
    return text[:MAX_MESSAGE_CHARS]


__all__ = ["MAX_EVENT_BYTES", "MAX_MESSAGE_CHARS", "router"]
