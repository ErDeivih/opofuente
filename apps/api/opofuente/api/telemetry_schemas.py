"""Esquemas de la telemetría propia del despliegue de demo.

La lista blanca de pantallas (`TelemetryScreen`) es la misma que usa la web en
`apps/web/src/telemetry.ts`. Si una ruta nueva no se añade en **los dos** sitios, la API rechaza el
nombre con 422 en lugar de aceptar etiquetas inventadas y hacer crecer el resumen sin límite.

Un evento solo lleva tres datos: qué tipo de evento es, el nombre estable de la pantalla y, como
mucho, un mensaje de error corto que el servidor vuelve a sanear y truncar. No hay IP, ni
`User-Agent`, ni URL, ni contenido de documentos: nada de eso forma parte del esquema, así que no
puede llegar por descuido al contador.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class TelemetryEventType(StrEnum):
    """Tipos de evento admitidos. Añadir uno obliga a decidir qué cuenta el resumen."""

    PAGE_VIEW = "page_view"
    ERROR = "error"


class TelemetryScreen(StrEnum):
    """Nombre estable de cada pantalla de la web (nunca la URL con identificadores)."""

    INICIO = "inicio"
    BANDEJA = "bandeja"
    TEMARIO = "temario"
    TEMA = "tema"
    PRACTICA = "practica"
    PROGRAMA = "programa"
    BIBLIOTECA = "biblioteca"
    PREGUNTAS = "preguntas"
    ESTUDIAR = "estudiar"
    ERRORES = "errores"
    CAMBIOS = "cambios"
    AJUSTES = "ajustes"
    REVISION = "revision"
    BUSCAR = "buscar"
    NO_ENCONTRADA = "no_encontrada"


class TelemetryEventSchema(BaseModel):
    """Evento que envía la web. `message` solo tiene sentido en los errores."""

    type: TelemetryEventType = Field(description="`page_view` o `error`.")
    screen: TelemetryScreen = Field(
        description="Pantalla de la lista blanca; una desconocida se rechaza con 422."
    )
    message: str | None = Field(
        default=None,
        description=(
            "Mensaje corto del error. El servidor lo sanea (sin rutas absolutas) y lo trunca a "
            "200 caracteres antes de contarlo. En `page_view` se ignora."
        ),
    )


class TelemetryRecentErrorSchema(BaseModel):
    """Un error reciente, ya saneado y sin contenido: solo pantalla, mensaje corto y hora."""

    screen: TelemetryScreen
    message: str | None
    at: datetime = Field(description="Instante en que se recibió el evento (UTC).")


class TelemetrySummarySchema(BaseModel):
    """Foto de los contadores en memoria del proceso en este instante."""

    total: int = Field(description="Eventos aceptados desde que arrancó el proceso.")
    by_type: dict[TelemetryEventType, int] = Field(
        description="Conteo por tipo de evento; los dos tipos aparecen siempre."
    )
    by_screen: dict[TelemetryScreen, int] = Field(
        description="Conteo por pantalla de la lista blanca (todas, también las que están a 0)."
    )
    recent_errors: list[TelemetryRecentErrorSchema] = Field(
        description="Como mucho 20 errores, del más antiguo al más reciente. No se guarda nada más."
    )


__all__ = [
    "TelemetryEventSchema",
    "TelemetryEventType",
    "TelemetryRecentErrorSchema",
    "TelemetryScreen",
    "TelemetrySummarySchema",
]
