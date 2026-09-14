"""Ajustes del esquema OpenAPI que FastAPI no permite expresar por ruta.

FastAPI documenta el modelo de una respuesta adicional bajo el media type de la ruta
(`application/json`). En OpoFuente **todas** las respuestas de error se sirven como
`application/problem+json` (RFC 9457) desde `api/errors.py`, así que el esquema documentado
se mueve al media type real.

El `$ref` se reutiliza tal y como lo generó FastAPI: aquí no se escriben a mano nombres de
componente, de modo que renombrar un modelo no rompe esta transformación (la prueba de
contrato comprueba la cadena completa).
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

PROBLEM_MEDIA_TYPE = "application/problem+json"
JSON_MEDIA_TYPE = "application/json"


def apply_problem_media_type(schema: dict[str, Any]) -> dict[str, Any]:
    """Mueve el esquema documentado de cada respuesta de error a `application/problem+json`.

    Idempotente: aplicarla dos veces produce el mismo resultado.
    """
    for operation in _iter_operations(schema):
        responses = operation.get("responses")
        if not isinstance(responses, dict):
            continue
        for status, response in responses.items():
            if not isinstance(response, dict) or not _is_error_status(status):
                continue
            content = response.get("content")
            if not isinstance(content, dict):
                continue
            documented = content.pop(JSON_MEDIA_TYPE, None)
            if documented and PROBLEM_MEDIA_TYPE not in content:
                content[PROBLEM_MEDIA_TYPE] = documented
    return schema


def _iter_operations(schema: dict[str, Any]) -> Iterator[dict[str, Any]]:
    paths = schema.get("paths")
    if not isinstance(paths, dict):
        return
    for path_item in paths.values():
        if not isinstance(path_item, dict):
            continue
        for operation in path_item.values():
            if isinstance(operation, dict) and "responses" in operation:
                yield operation


def _is_error_status(status: str) -> bool:
    return status.isdigit() and status[0] in {"4", "5"}
