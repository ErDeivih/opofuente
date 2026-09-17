"""DTO de la biblioteca: documentos, versiones, derechos, secciones, evidencias y colecciones.

La API sirve lo que el servicio ya decidió. Dos cosas que el contrato dice explícitamente y no
se dejan a la interpretación de quien consuma:

- **`rights.is_restricted`**: los derechos sin revisar viajan marcados como restringidos, no como un
  permiso implícito (09_SECURITY §8);
- **`active_version`** puede ser una versión **candidata**, y entonces `is_accepted` es falso: una
  candidata es una propuesta de cambio, no la versión buena.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field


class RightsSchema(BaseModel):
    code: str
    review_status: Literal["unknown", "reviewed", "restricted"]
    license_name: str | None = None
    license_url: str | None = None
    attribution: str | None = None
    commercial_reuse: bool = False
    sharing: bool = False
    notes: str | None = None
    is_restricted: bool


class VersionSchema(BaseModel):
    id: str
    logical_document_id: str
    version_label: str | None = None
    status: Literal["candidate", "accepted", "outdated", "superseded", "withdrawn", "rejected"]
    is_accepted: bool
    artifact_id: str
    representation_id: str | None = None
    published_at: date | None = None
    valid_from: date | None = None
    valid_to: date | None = None
    retrieved_at: datetime | None = None
    language: str | None = None
    supersedes_id: str | None = None
    rights: RightsSchema | None = None
    official_url: str | None = None
    content_hash: str | None = None
    approved_at: datetime | None = None
    approved_by: str | None = None
    section_count: int = 0
    evidence_count: int = 0


class DocumentSchema(BaseModel):
    id: str
    canonical_title: str
    document_type: str
    owner_scope: Literal["public", "private_user", "generated"]
    is_public: bool
    authority_tier: str | None = None
    canonical_identifier: str | None = None
    active_version: VersionSchema | None = None
    version_count: int = 0
    mapping_count: int = 0
    created_at: datetime | None = None


class DocumentDetailSchema(BaseModel):
    document: DocumentSchema
    versions: list[VersionSchema] = Field(default_factory=list)


class DocumentPageSchema(BaseModel):
    documents: list[DocumentSchema]
    total: int
    limit: int
    offset: int


class SectionSchema(BaseModel):
    id: str
    document_version_id: str
    section_type: str
    title: str | None = None
    label: str | None = None
    position: int
    ordinal: int
    parent_id: str | None = None
    page_start: int | None = None
    page_end: int | None = None
    char_start: int = 0
    char_end: int = 0


class EvidenceSchema(BaseModel):
    """Unidad citable: es lo que permite abrir el documento en el sitio exacto."""

    id: str
    document_version_id: str
    text: str
    normalized_text: str
    ordinal: int
    section_id: str | None = None
    page: int | None = None
    citation_label: str | None = None
    quality: str | None = None
    index_status: Literal["pending", "indexed", "failed", "stale"] = "pending"
    char_start: int = 0
    char_end: int = 0


class PromoteRequestSchema(BaseModel):
    """Promociona un artefacto. `document_id` añade una versión a un documento que ya existe."""

    artifact_id: str = Field(min_length=1)
    document_id: str | None = None
    title: str | None = Field(default=None, max_length=500)
    document_type: str = "unknown"
    authority_tier: str | None = Field(default=None, max_length=8)
    version_label: str | None = Field(default=None, max_length=120)
    rights_code: str | None = Field(default=None, max_length=48)
    official_url: str | None = Field(default=None, max_length=2048)


class PromotionOutcomeSchema(BaseModel):
    document_id: str | None = None
    version_id: str | None = None
    created_document: bool
    created_version: bool
    applied: bool
    reason: str | None = None


class MarkSupersedesRequestSchema(BaseModel):
    superseded_id: str = Field(min_length=1)


class CollectionSchema(BaseModel):
    id: str
    name: str
    description: str | None = None
    item_count: int = 0
    items: list[str] = Field(default_factory=list)
    created_at: datetime | None = None


class CreateCollectionRequestSchema(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)


class CollectionItemRequestSchema(BaseModel):
    subject_type: Literal["artifact", "representation", "document_version", "section", "evidence"]
    subject_id: str = Field(min_length=1)


class MappingRequestSchema(BaseModel):
    """Alta de un mapeo: qué nodo del programa cubre esta versión de documento (contrato §7).

    No se acepta `confidence` desde fuera: un mapeo que pide una persona es una afirmación, no una
    estimación, y fingir una probabilidad inventada sería peor que no tenerla.
    """

    curriculum_node_id: str = Field(min_length=1)
    coverage_type: Literal["mention", "partial", "complete"] = "partial"


class DocumentMappingSchema(BaseModel):
    """Un mapeo creado desde la biblioteca.

    Se llama `DocumentMapping` y no `Mapping` a propósito: la clasificación ya tiene su propio
    `MappingSchema` (el del material) y dos modelos con el mismo nombre obligan a FastAPI a inventar
    nombres cualificados en el OpenAPI, lo que rompe los tipos derivados del contrato.
    """

    id: str
    document_version_id: str
    curriculum_node_id: str
    coverage_type: Literal["mention", "partial", "complete"]
    status: Literal["provisional", "accepted", "rejected"]


class SectionDiffSchema(BaseModel):
    label: str
    kind: Literal["added", "removed", "changed", "unchanged"]
    left: str | None = None
    right: str | None = None


class VersionDiffSchema(BaseModel):
    """Comparación de dos versiones: informa de los cambios y no fusiona nada."""

    document_id: str
    from_version_id: str
    to_version_id: str
    sections: list[SectionDiffSchema] = Field(default_factory=list)
    added: int = 0
    removed: int = 0
    changed: int = 0
    unchanged: int = 0
    has_changes: bool = False
