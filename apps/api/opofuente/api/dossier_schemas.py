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


class DossierNoteSectionSchema(BaseModel):
    """Un apartado de los apuntes redactados, con el rastro de las preguntas que cubre.

    `question_ids` son identificadores de pregunta, y eso es deliberado: esta pantalla es la del
    **propietario** (la ficha del tema en el programa), no la del alumno, y poder cruzar un apartado
    con sus preguntas es justo lo que hace falta para revisarlos. La zona del alumno tiene su propia
    ruta y su propio contrato, sin identificadores.
    """

    key: str
    epigraph_code: str
    title: str
    anchor: str = Field(
        description="Anclaje estable del apartado, para enlazar desde una pregunta."
    )
    body_markdown: str
    facts_total: int = Field(ge=0)
    needs_review_reason: str | None = None
    covered: int = Field(ge=0)
    gaps: int = Field(ge=0)
    doubtful: int = Field(ge=0)
    conflicts: int = Field(
        ge=0,
        description=(
            "Preguntas que este apartado contesta con una letra distinta de su clave: van a "
            "revisión, no cuentan como cubiertas."
        ),
    )
    question_ids: list[str]
    gap_question_ids: list[str]
    doubtful_question_ids: list[str]
    conflict_question_ids: list[str]


class DossierNotesSchema(BaseModel):
    """Los apuntes de un tema: los que se escriben a partir de sus preguntas y se comprueban con
    ellas.

    Van dentro del dossier porque el tema es una unidad de lectura y de versionado: al guardar una
    versión se guarda el tema entero, citas **y** apuntes, y una versión antigua se lee como se
    leyó.
    """

    generated_at: datetime | None = None
    model: str | None = None
    prompt_template_version: str
    sections_total: int = Field(ge=0)
    questions_total: int = Field(ge=0)
    covered: int = Field(ge=0)
    gaps: int = Field(ge=0)
    doubtful: int = Field(ge=0)
    conflicts: int = Field(
        ge=0,
        description=(
            "Preguntas cuya letra según los apuntes no coincide con la clave. No son cobertura: "
            "son la cola de revisión de la comprobación (paso E)."
        ),
    )
    sections: list[DossierNoteSectionSchema]

    @model_validator(mode="after")
    def _coherente(self) -> DossierNotesSchema:
        """Los totales se comprueban contra lo servido: un total que no cuadra es un dato falso."""
        if self.sections_total != len(self.sections):
            raise ValueError("sections_total no cuadra con los apartados servidos")
        if self.covered != sum(apartado.covered for apartado in self.sections):
            raise ValueError("covered no cuadra con los apartados servidos")
        if self.conflicts != sum(apartado.conflicts for apartado in self.sections):
            raise ValueError("conflicts no cuadra con los apartados servidos")
        if self.questions_total != sum(
            apartado.covered + apartado.gaps + apartado.doubtful + apartado.conflicts
            for apartado in self.sections
        ):
            raise ValueError("questions_total no cuadra con las preguntas comprobadas")
        return self


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
    #: Los apuntes redactados del tema, si los tiene: `null` es «este tema todavía no tiene apuntes
    #: escritos», que no es lo mismo que unos apuntes vacíos.
    notes: DossierNotesSchema | None = None

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
