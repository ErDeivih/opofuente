"""Logs JSON rotativos, sin contenido de documentos ni secretos.

Reglas (02_ARCHITECTURE §9 y 09_SECURITY-PRIVACY-AND-RIGHTS §9):
- nunca se registra el texto importado, preguntas privadas, prompts completos, respuestas
  personales, rutas absolutas ni claves;
- el formateador solo copia un conjunto blanco de campos extra, así que un `extra` con
  contenido sensible se descarta en lugar de filtrarse;
- de una excepción se registra el tipo, nunca la traza (puede contener rutas o contenido).
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import UTC, datetime
from logging.handlers import RotatingFileHandler
from typing import Any

from opofuente.config import Settings
from opofuente.infrastructure.correlation import get_correlation_id

#: Campos extra que sí se registran. Cualquier otro se ignora deliberadamente.
SAFE_EXTRA_KEYS: frozenset[str] = frozenset(
    {
        "capability",
        "check",
        "duration_ms",
        "error_type",
        "event",
        "job_id",
        "method",
        "path",
        "probe",
        "revision",
        "status_code",
    }
)

_HANDLER_MARK = "opofuente-json"
_MAX_BYTES = 2_000_000
_BACKUP_COUNT = 5


class JsonFormatter(logging.Formatter):
    """Serializa cada registro como una línea JSON sanitizada."""

    def __init__(self, *, service: str, version: str) -> None:
        super().__init__()
        self._service = service
        self._version = version

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "service": self._service,
            "version": self._version,
        }
        correlation_id = get_correlation_id()
        if correlation_id:
            payload["correlation_id"] = correlation_id
        for key in sorted(SAFE_EXTRA_KEYS):
            value = record.__dict__.get(key)
            if value is not None:
                payload[key] = value
        if record.exc_info and record.exc_info[0] is not None:
            payload["exception"] = record.exc_info[0].__name__
        return json.dumps(payload, ensure_ascii=False)


def setup_logging(settings: Settings) -> None:
    """Configura logs JSON a stderr y a un fichero rotativo dentro de `data/logs`."""
    paths = settings.data_paths
    paths.ensure_directories()
    formatter = JsonFormatter(service="opofuente", version=_version())

    root = logging.getLogger()
    root.setLevel(settings.log_level)
    # Solo se retiran los handlers propios: no se toca lo que haya puesto otro
    # (por ejemplo, el capturador de logs de pytest).
    for handler in [h for h in root.handlers if h.get_name() == _HANDLER_MARK]:
        root.removeHandler(handler)
        handler.close()

    stream_handler = logging.StreamHandler(sys.stderr)
    stream_handler.set_name(_HANDLER_MARK)
    stream_handler.setFormatter(formatter)

    file_handler = RotatingFileHandler(
        paths.logs / "opofuente.log",
        maxBytes=_MAX_BYTES,
        backupCount=_BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.set_name(_HANDLER_MARK)
    file_handler.setFormatter(formatter)

    root.addHandler(stream_handler)
    root.addHandler(file_handler)

    # El servidor ya registra cada petición con su correlation ID.
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


def _version() -> str:
    from opofuente import __version__

    return __version__
