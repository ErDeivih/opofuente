"""Contrato de la bandeja de avisos del alumno (F13, decisión D2).

Es la mitad **del propietario**: aquí sí viaja el identificador del aviso (lo necesita para
despacharlo), el código del tema y el título del apartado. La mitad del alumno
(`student_schemas.StudentReportSchema`) no los tiene, y esa asimetría es la regla de las dos zonas:
el mismo hecho se sirve distinto según quién mira, con esquemas propios y no filtrando al final.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

#: En qué punto está un aviso. Es el vocabulario del dominio, no uno nuevo.
NoteReportStatusName = Literal["open", "reviewed", "dismissed"]


class NoteReportSchema(BaseModel):
    """Un aviso del alumno: qué apartado, qué dice y cuándo llegó.

    `section_title` es `None` cuando el apartado ya no existe —los apuntes se reescriben—: el aviso
    se sigue enseñando, y ese hueco es justo lo que hay que mirar.
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


class NoteReportListSchema(BaseModel):
    """Los avisos y cuántos siguen sin despachar.

    El recuento va aparte de la lista aunque se pueda contar de ella: la lista viene filtrada y
    limitada (por estado y por tema), y el número que el propietario necesita ver es el de
    pendientes de verdad, no el de la página que está mirando.
    """

    pending: int = Field(ge=0, description="Avisos en estado `open`, con independencia del filtro.")
    reports: list[NoteReportSchema]
