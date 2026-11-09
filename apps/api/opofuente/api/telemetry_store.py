"""Contador en memoria de la telemetría propia (sin tabla, sin migración, sin servicio externo).

Es deliberadamente efímero: guarda lo justo para saber si la demo se usa y qué errores ve el
navegador, y lo pierde al reiniciar. El acceso va bajo un `threading.Lock` porque FastAPI puede
ejecutar los endpoints síncronos en varios hilos a la vez y un contador sin protección perdería
incrementos.

No guarda IP, `User-Agent`, cookies, URL, contenido de documentos ni nada del mensaje de error más
allá del texto ya saneado que le pasa la ruta. Aquí no hay E/S: todo son enteros y, como mucho,
20 errores en un `deque` acotado.
"""

from __future__ import annotations

import threading
from collections import Counter, deque
from datetime import UTC, datetime

from opofuente.api.telemetry_schemas import (
    TelemetryEventType,
    TelemetryRecentErrorSchema,
    TelemetryScreen,
    TelemetrySummarySchema,
)

#: Cuántos errores recientes se conservan como máximo. El resumen nunca crece por encima de esto.
MAX_RECENT_ERRORS = 20


class TelemetryStore:
    """Contadores por tipo y por pantalla, más una ventana corta de errores recientes."""

    def __init__(self, *, max_recent_errors: int = MAX_RECENT_ERRORS) -> None:
        self._lock = threading.Lock()
        self._total = 0
        self._by_type: Counter[TelemetryEventType] = Counter()
        self._by_screen: Counter[TelemetryScreen] = Counter()
        self._recent_errors: deque[TelemetryRecentErrorSchema] = deque(maxlen=max_recent_errors)

    def record(
        self,
        event_type: TelemetryEventType,
        screen: TelemetryScreen,
        message: str | None = None,
        *,
        at: datetime | None = None,
    ) -> None:
        """Suma un evento. `message` solo se conserva para los errores ya saneados."""
        with self._lock:
            self._total += 1
            self._by_type[event_type] += 1
            self._by_screen[screen] += 1
            if event_type is TelemetryEventType.ERROR:
                self._recent_errors.append(
                    TelemetryRecentErrorSchema(
                        screen=screen,
                        message=message,
                        at=at if at is not None else datetime.now(UTC),
                    )
                )

    def summary(self) -> TelemetrySummarySchema:
        """Copia consistente de los contadores; se toma el candado una sola vez."""
        with self._lock:
            return TelemetrySummarySchema(
                total=self._total,
                by_type={tipo: self._by_type[tipo] for tipo in TelemetryEventType},
                by_screen={pantalla: self._by_screen[pantalla] for pantalla in TelemetryScreen},
                recent_errors=list(self._recent_errors),
            )


__all__ = ["MAX_RECENT_ERRORS", "TelemetryStore"]
