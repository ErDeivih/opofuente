"""Los avisos del alumno sobre los apuntes («esto está mal», decisión D2 del objetivo).

Esto **no** es la comprobación del motor. `notes_incidents` (migración 0031) guarda lo que queda
cuando los apuntes se comprueban con las preguntas: un hueco, una letra que no cuadra, una norma que
cambió. Aquí es otra cosa: una persona leyendo el tema que dice «en este apartado hay un error» y
escribe el motivo en **una línea**. Por eso el vocabulario es distinto y más pobre a propósito: no
hay categoría (no hay que clasificar el aviso, hay que leerlo) y no hay frase verificada (nadie la
ha verificado).

Las dos reglas que sí son del dominio y por eso viven aquí, y no en la ruta:

1. **el motivo es obligatorio y es una línea**: se recorta, no puede quedar vacío y no puede ser un
   párrafo entero. Un aviso sin motivo no se puede arreglar —nadie sabe qué está mal— y uno de
   quinientos caracteres deja de ser un aviso;
2. **la dirección del párrafo es la del apartado** (`section_key`, el `subsection_key` del esquema,
   y su `anchor` estable), no la de la pantalla: así el aviso sigue apuntando al mismo sitio aunque
   el orden de lectura cambie.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum

#: Un aviso es una línea. Más de esto no lo lee nadie en una bandeja.
MAX_REASON_CHARS = 300


class NoteReportStatus(StrEnum):
    """En qué punto está un aviso.

    `open` es lo que espera al propietario; `reviewed` y `dismissed` son las dos salidas posibles, y
    ninguna de las dos se escribe desde la zona del alumno.
    """

    OPEN = "open"
    REVIEWED = "reviewed"
    DISMISSED = "dismissed"


@dataclass(frozen=True, slots=True)
class NoteReport:
    """Un aviso del alumno, tal como se guarda y tal como se lee en la bandeja.

    `topic_code`, `topic_title` y `section_title` los resuelve quien lee (la bandeja): no se guardan
    para no tener dos copias que puedan decir cosas distintas del mismo apartado. `section_title`
    queda en `None` cuando el apartado ya no existe —los apuntes se reescriben—, y eso es
    precisamente lo que el propietario tiene que ver: un aviso que apuntaba a un texto que ya no
    está.
    """

    id: str
    node_id: str
    owner_id: str
    section_key: str
    anchor: str
    reason: str
    status: NoteReportStatus
    created_at: datetime
    reviewed_at: datetime | None = None
    topic_code: str = ""
    topic_title: str = ""
    section_title: str | None = None


def normalise_reason(texto: str) -> str:
    """El motivo del aviso, recortado y en una línea. Vacío no vale; kilométrico tampoco.

    No se colapsan los espacios interiores a propósito: si alguien escribe dos espacios, es su
    texto. Lo que se quita son los saltos de línea, porque una bandeja que enseña tres líneas por
    aviso deja de poder recorrerse de un vistazo.
    """
    limpio = " ".join(texto.split())
    if not limpio:
        raise ValueError("un aviso sin motivo no se puede arreglar")
    if len(limpio) > MAX_REASON_CHARS:
        raise ValueError(f"el motivo de un aviso no pasa de {MAX_REASON_CHARS} caracteres")
    return limpio


@dataclass(frozen=True, slots=True)
class NoteReportFilter:
    """Lo que se puede pedir al listar la bandeja: por estado y por tema."""

    status: NoteReportStatus | None = None
    topic_code: str | None = None
    limit: int = field(default=200)


__all__ = [
    "MAX_REASON_CHARS",
    "NoteReport",
    "NoteReportFilter",
    "NoteReportStatus",
    "normalise_reason",
]
