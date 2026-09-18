"""Esquemas de exportación (08_API-CONTRACT §11).

El resultado lleva **el contenido y el fichero escrito**: lo primero para que la interfaz pueda
ofrecer la descarga sin pedir nada más, lo segundo para que el material quede en `<datos>/exports`
y se pueda abrir desde el explorador. Y lleva, sobre todo, lo que hay que leer antes de usar el
fichero: los avisos y la procedencia.
"""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, Field, model_validator

ExportFormatName = Literal["anki_csv", "markdown"]


class ExportRequestSchema(BaseModel):
    """Qué se exporta: un conjunto concreto, un tema, o todo lo de una oposición."""

    opposition_id: str | None = None
    question_set_id: str | None = None
    node_id: str | None = Field(
        default=None,
        description="Nodo del programa: solo las preguntas asignadas a ese tema.",
    )
    include_restricted: bool = Field(
        default=True,
        description=(
            "Si se incluye el material con derechos restringidos o sin determinar. Por defecto sí, "
            "con aviso: el material es del usuario y quien exporta decide."
        ),
    )
    title: Annotated[str | None, Field(default=None, max_length=120)] = None

    @model_validator(mode="after")
    def _necesita_alcance(self) -> ExportRequestSchema:
        if self.question_set_id is None and self.opposition_id is None:
            raise ValueError(
                "una exportación necesita un conjunto o una oposición: sin alcance se exportaría "
                "todo el banco sin decirlo"
            )
        return self


class ExportSchema(BaseModel):
    """El fichero exportado, con lo que hay que saber de él."""

    filename: str
    format: ExportFormatName
    path: str
    bytes: int
    item_count: int
    documents: list[str]
    warnings: list[str]
    provenance: dict[str, str]
    content: str
