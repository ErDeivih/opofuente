"""DTO del dossier del tema (S13, parte 1).

La forma es **la misma** que la del documento que se archiva al guardar una versión
(`domain.dossier.dossier_document`): una sola forma para lo que se guarda y lo que se sirve, y una
prueba que lo comprueba. Así una versión antigua se lee con el mismo lector que la actual.

`holes` son **códigos**, no frases: la interfaz los traduce, igual que los avisos de extracción. Un
tema sin material no devuelve un cero: devuelve su hueco.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from opofuente.domain.dossier import HoleCode, TopicDossier, dossier_document

HoleCodeSchema = Literal[
    "sin_material",
    "sin_texto",
    "no_citable",
    "sin_version_aceptada",
    "mapeo_provisional",
    "repetido_en_otra_fuente",
]


class DossierHoleSchema(BaseModel):
    code: HoleCodeSchema
    count: int = Field(ge=0)
    reason: str | None = None


class DossierPassageSchema(BaseModel):
    evidence_id: str
    text: str = Field(description="Texto literal del tramo: la cita, tal cual se guardó.")
    citation_label: str | None = None
    page: int | None = None
    section_title: str | None = None
    ordinal: int
    quality: str | None = None
    #: Obligatorio aunque pueda estar vacío: el servidor manda siempre la lista, y declararla
    #: opcional obligaría a cada cliente a defenderse de un `undefined` que no ocurre.
    repeated_in: list[str]


class DossierSourceSchema(BaseModel):
    document_id: str
    document_title: str
    document_type: str
    authority_tier: str | None = None
    version_id: str
    version_label: str | None = None
    version_status: str
    quality: str | None = None
    mappings: list[str]
    provisional: bool
    passages_total: int = Field(ge=0)
    passages: list[DossierPassageSchema]


class DossierSchema(BaseModel):
    """El dossier de un tema: sus fuentes citadas, sus huecos y con qué se construyó."""

    format_version: int
    node_id: str
    path: str
    title: str
    depth: int
    generated_at: datetime
    content_hash: str
    version_id: str | None = None
    previous_version_id: str | None = None
    sources_total: int = Field(ge=0)
    passages_total: int = Field(ge=0)
    accepted_sources: int = Field(ge=0)
    provisional_sources: int = Field(ge=0)
    provisional: bool
    empty: bool
    sources: list[DossierSourceSchema]
    holes: list[DossierHoleSchema]

    @model_validator(mode="after")
    def _coherente(self) -> DossierSchema:
        """Los totales se comprueban contra lo servido: un total que no cuadra es un dato falso."""
        if self.sources_total != len(self.sources):
            raise ValueError("sources_total no cuadra con las fuentes servidas")
        if self.passages_total != sum(fuente.passages_total for fuente in self.sources):
            raise ValueError("passages_total no cuadra con los pasajes servidos")
        for fuente in self.sources:
            if fuente.passages_total != len(fuente.passages):
                raise ValueError("passages_total de una fuente no cuadra con sus pasajes")
        return self


class DossierVersionSchema(BaseModel):
    """Una versión guardada del dossier: lo justo para listarla y elegir con cuál comparar."""

    id: str
    content_hash: str
    built_at: datetime
    sources_count: int = Field(ge=0)
    passages_count: int = Field(ge=0)


class DossierArchiveSchema(BaseModel):
    """Resultado de archivar: el dossier archivado y si esa lectura ya estaba guardada."""

    created: bool
    version_id: str
    dossier: DossierSchema


def hole_codes() -> tuple[str, ...]:
    """Los códigos de hueco del dominio, para que esquema y dominio no se separen en silencio."""
    return tuple(codigo.value for codigo in HoleCode)


def dossier_schema(dossier: TopicDossier) -> DossierSchema:
    """Valida el documento del dominio contra este contrato antes de servirlo.

    Se sirve el mismo documento que se archiva: si algún día el dominio devuelve algo que el
    contrato no admite, falla aquí (y en la prueba), no en la interfaz del usuario.
    """
    return DossierSchema.model_validate(dossier_document(dossier))
