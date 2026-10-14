"""Contrato de la bandeja de avisos del alumno (F13 y F16, decisiones D2 y del bloque C).

Es la mitad **del propietario**: aquí sí viaja el identificador del aviso (lo necesita para
despacharlo), el código del tema y el título del apartado. La mitad del alumno
(`student_schemas.StudentReportSchema`) no los tiene, y esa asimetría es la regla de las dos zonas:
el mismo hecho se sirve distinto según quién mira, con esquemas propios y no filtrando al final.

Desde F16 esta mitad también **escribe**, y solo una cosa: el estado del aviso y la nota de lo que
se ha hecho. No hay ruta para editar el motivo del alumno ni el apartado al que apunta: eso es lo
que dijo quien lo reportó, y corregirlo sería reescribir su aviso.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from opofuente.domain.notes_reports import MAX_REASON_CHARS

#: En qué punto está un aviso. Es el vocabulario del dominio, no uno nuevo.
NoteReportStatusName = Literal["open", "in_progress", "reviewed", "dismissed"]


class NoteReportSchema(BaseModel):
    """Un aviso del alumno: qué apartado, qué dice, cuándo llegó y cómo acabó.

    `section_title` es `None` cuando el apartado ya no existe —los apuntes se reescriben—: el aviso
    se sigue enseñando, y ese hueco es justo lo que hay que mirar. `resolution_note` es lo que el
    propietario escribió de lo que hizo, y `reviewed_at` cuándo lo cerró (vuelve a estar vacío si lo
    reabre).
    """

    id: str
    topic_code: str
    topic_title: str
    section_key: str
    section_title: str | None = None
    anchor: str
    reason: str
    status: NoteReportStatusName
    created_at: datetime
    reviewed_at: datetime | None = None
    resolution_note: str | None = None


class NoteReportListSchema(BaseModel):
    """Los avisos, cuántos siguen sin despachar y cuántos hay en cada estado.

    Los recuentos van aparte de la lista aunque se puedan contar de ella: la lista viene filtrada y
    limitada (por estado, por tema y por búsqueda), y los números que el propietario necesita ver
    son los de la bandeja entera, no los de la página que está mirando. `pending` es solo `open`:
    un aviso «en curso» ya no espera a nadie, y por eso no cuenta ahí.
    """

    pending: int = Field(ge=0, description="Avisos en estado `open`, con independencia del filtro.")
    in_progress: int = Field(ge=0, description="Avisos que el propietario tiene en la mano.")
    reviewed: int = Field(ge=0, description="Avisos resueltos.")
    dismissed: int = Field(ge=0, description="Avisos descartados: no eran un error.")
    total: int = Field(ge=0, description="Avisos que devuelve el filtro, contados en la base.")
    reports: list[NoteReportSchema]


class NoteReportUpdateSchema(BaseModel):
    """Lo único que se puede cambiar de un aviso: en qué punto está y qué se ha hecho.

    `note` es potestativa a propósito. El motivo del alumno es obligatorio porque un aviso sin él no
    se puede arreglar; la nota del propietario no, porque hay avisos que se cierran sin nada que
    escribir. Cuando viene, es **una línea** (el servidor la recorta) y sustituye a la que hubiera;
    cuando no viene, la que hubiera se queda.
    """

    model_config = ConfigDict(extra="forbid")

    status: NoteReportStatusName
    note: str | None = Field(default=None, max_length=MAX_REASON_CHARS)
    actor: str | None = Field(default=None, min_length=1, max_length=64)

    @field_validator("note")
    @classmethod
    def _una_linea(cls, valor: str | None) -> str | None:
        """La nota viaja en una línea: los saltos se quitan aquí, no en la pantalla."""
        return None if valor is None else " ".join(valor.split())
