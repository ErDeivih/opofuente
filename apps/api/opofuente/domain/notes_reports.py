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

Y una tercera, que llegó con el bloque C (la bandeja del propietario, F16): **qué cuenta como
despachado lo decide el dominio**, no la pantalla. `reviewed_at` se escribe cuando el aviso se
cierra (`reviewed` o `dismissed`) y se deja vacío cuando vuelve a estar abierto o en curso; si lo
decidiera la interfaz, la bandeja podría enseñar «resuelto el 12-oct» con el aviso pendiente.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum

#: Un aviso es una línea. Más de esto no lo lee nadie en una bandeja.
MAX_REASON_CHARS = 300


class NoteReportStatus(StrEnum):
    """En qué punto está un aviso.

    `open` es lo que espera al propietario; `in_progress` es «lo he visto y estoy en ello»; y
    `reviewed` y `dismissed` son las dos salidas posibles, que no se escriben desde la zona del
    alumno. `in_progress` se añadió en la migración `0034` porque sin él un aviso está pendiente o
    está cerrado: no había forma de dejar constancia de estar mirándolo sin cerrarlo.
    """

    OPEN = "open"
    IN_PROGRESS = "in_progress"
    REVIEWED = "reviewed"
    DISMISSED = "dismissed"


#: Los estados con los que un aviso está **cerrado**: nadie tiene que volver a mirarlo.
CLOSED_STATUSES: frozenset[NoteReportStatus] = frozenset(
    {NoteReportStatus.REVIEWED, NoteReportStatus.DISMISSED}
)


def reviewed_at_for(status: NoteReportStatus, now: datetime) -> datetime | None:
    """Cuándo se despachó un aviso que pasa a `status`.

    Cerrarlo deja la fecha; reabrirlo (o ponerlo en curso) la **borra**, porque la columna dice
    cuándo se despachó y un aviso abierto con fecha de revisión es una traza que miente.
    """
    return now if status in CLOSED_STATUSES else None


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
    #: Qué se ha hecho con el aviso, en una línea. `None` mientras nadie lo haya escrito.
    resolution_note: str | None = None
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


def normalise_note(texto: str | None) -> str | None:
    """La nota de lo que se ha hecho, recortada y en una línea. Vacía es «no hay nota».

    La nota **no** es como el motivo: el motivo es obligatorio porque un aviso sin él no se puede
    arreglar, y la nota es potestativa porque el propietario puede cerrar un aviso que se arregla
    solo (una errata que ya no está). Lo que sí se comprueba es su forma: una línea, y de `None`
    (o en blanco) a `None`, para que la columna no guarde cadenas vacías que luego haya que
    distinguir de «sin nota».
    """
    if texto is None:
        return None
    limpio = " ".join(texto.split())
    if not limpio:
        return None
    if len(limpio) > MAX_REASON_CHARS:
        raise ValueError(f"la nota de un aviso no pasa de {MAX_REASON_CHARS} caracteres")
    return limpio


@dataclass(frozen=True, slots=True)
class NoteReportFilter:
    """Lo que se puede pedir al listar la bandeja: por estado y por tema.

    `q` busca en lo que escribió el alumno y en el título de su apartado: es lo que hace falta para
    encontrar un aviso concreto entre cientos sin recorrerlos. Un tema y un estado se combinan con
    la búsqueda, no se excluyen.
    """

    status: NoteReportStatus | None = None
    topic_code: str | None = None
    q: str | None = None
    limit: int = field(default=200)


__all__ = [
    "CLOSED_STATUSES",
    "MAX_REASON_CHARS",
    "NoteReport",
    "NoteReportFilter",
    "NoteReportStatus",
    "normalise_note",
    "normalise_reason",
    "reviewed_at_for",
]
