"""Modelos de lectura de la biblioteca (S05): documentos, versiones, secciones y colecciones."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime


@dataclass(frozen=True, slots=True)
class RightsView:
    """Condiciones de uso de una fuente, con lo que falta para poder atribuirla."""

    code: str
    review_status: str
    license_name: str | None = None
    license_url: str | None = None
    attribution: str | None = None
    commercial_reuse: bool = False
    sharing: bool = False
    notes: str | None = None

    @property
    def is_restricted(self) -> bool:
        """Desconocido se trata como restringido: no es un permiso, es una ausencia de dato."""
        return self.review_status != "reviewed"


@dataclass(frozen=True, slots=True)
class VersionView:
    """Una versión concreta de un documento, con su vigencia y su procedencia."""

    id: str
    logical_document_id: str
    version_label: str | None
    status: str
    artifact_id: str
    representation_id: str | None = None
    published_at: date | None = None
    valid_from: date | None = None
    valid_to: date | None = None
    retrieved_at: datetime | None = None
    language: str | None = None
    supersedes_id: str | None = None
    rights: RightsView | None = None
    official_url: str | None = None
    content_hash: str | None = None
    approved_at: datetime | None = None
    approved_by: str | None = None
    section_count: int = 0
    evidence_count: int = 0

    @property
    def is_accepted(self) -> bool:
        return self.status == "accepted"


@dataclass(frozen=True, slots=True)
class DocumentView:
    """La obra con su versión activa: lo que la biblioteca muestra en la lista y en la cabecera."""

    id: str
    canonical_title: str
    document_type: str
    owner_scope: str
    authority_tier: str | None = None
    canonical_identifier: str | None = None
    active_version: VersionView | None = None
    version_count: int = 0
    mapping_count: int = 0
    created_at: datetime | None = None

    @property
    def is_public(self) -> bool:
        return self.owner_scope == "public"


@dataclass(frozen=True, slots=True)
class DocumentDetail:
    """Documento con todas sus versiones: es lo que alimenta la ficha y las pestañas."""

    document: DocumentView
    versions: tuple[VersionView, ...] = ()


@dataclass(frozen=True, slots=True)
class DocumentPage:
    documents: tuple[DocumentView, ...]
    total: int
    limit: int
    offset: int


@dataclass(frozen=True, slots=True)
class SectionView:
    """Una sección del documento, con dónde empieza y acaba: es lo que hace citable una cita."""

    id: str
    document_version_id: str
    section_type: str
    title: str | None
    label: str | None
    position: int
    ordinal: int
    parent_id: str | None = None
    page_start: int | None = None
    page_end: int | None = None
    char_start: int = 0
    char_end: int = 0


@dataclass(frozen=True, slots=True)
class EvidenceView:
    """Una unidad citable: el texto exacto con su sección, su página y su etiqueta de cita."""

    id: str
    document_version_id: str
    text: str
    normalized_text: str
    ordinal: int
    section_id: str | None = None
    page: int | None = None
    citation_label: str | None = None
    quality: str | None = None
    index_status: str = "pending"
    char_start: int = 0
    char_end: int = 0


@dataclass(frozen=True, slots=True)
class SectionDiff:
    """Diferencia de una sección entre dos versiones: añadida, quitada, cambiada o igual."""

    label: str
    kind: str
    left: str | None = None
    right: str | None = None


@dataclass(frozen=True, slots=True)
class VersionDiff:
    """Comparación determinista entre dos versiones, sección a sección. No fusiona nada."""

    document_id: str
    from_version_id: str
    to_version_id: str
    sections: tuple[SectionDiff, ...] = ()
    added: int = 0
    removed: int = 0
    changed: int = 0
    unchanged: int = 0

    @property
    def has_changes(self) -> bool:
        """¿Hay algo que revisar? Igual que en el dominio: lo que solo cambió de sitio no cuenta.

        Se calcula a partir de los recuentos y no se guarda: así no puede decir una cosa mientras
        los recuentos dicen otra.
        """
        return self.added + self.removed + self.changed > 0


@dataclass(frozen=True, slots=True)
class ArtifactFile:
    """El fichero original de una versión, tal y como entró: es lo que sirve `/original`."""

    storage_key: str
    media_type: str
    size_bytes: int
    sha256: str
    original_name: str | None = None
    quarantine_status: str = "none"

    @property
    def is_quarantined(self) -> bool:
        """En cuarentena no se sirve: el contenido está retenido a propósito, no es un fallo."""
        return self.quarantine_status != "none"


@dataclass(frozen=True, slots=True)
class VersionDetail:
    """Una versión con su documento: lo que responde `GET /document-versions/{id}`."""

    document_id: str
    document_title: str
    document_type: str
    owner_scope: str
    version: VersionView
    mapping_count: int = 0


@dataclass(frozen=True, slots=True)
class VersionText:
    """Trozo del texto extraído de una versión, con la calidad de la extracción a la vista."""

    document_version_id: str
    text: str
    offset: int
    limit: int
    total_chars: int
    truncated: bool
    representation_id: str | None = None
    quality: str | None = None
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class DocumentUpdateOutcome:
    """Resultado de editar un documento: el documento actualizado, o por qué no se pudo."""

    document: DocumentView | None
    reason: str | None = None

    @property
    def applied(self) -> bool:
        return self.reason is None


@dataclass(frozen=True, slots=True)
class CollectionView:
    """Colección personal con sus miembros."""

    id: str
    name: str
    description: str | None = None
    item_count: int = 0
    items: tuple[str, ...] = field(default_factory=tuple)
    created_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class PromotionOutcome:
    """Resultado de promocionar: qué documento y qué versión, o por qué no se pudo."""

    document_id: str | None
    version_id: str | None
    created_document: bool
    created_version: bool
    reason: str | None = None

    @property
    def applied(self) -> bool:
        return self.reason is None


__all__ = [
    "ArtifactFile",
    "CollectionView",
    "DocumentDetail",
    "DocumentPage",
    "DocumentUpdateOutcome",
    "DocumentView",
    "EvidenceView",
    "PromotionOutcome",
    "RightsView",
    "SectionDiff",
    "SectionView",
    "VersionDetail",
    "VersionDiff",
    "VersionText",
    "VersionView",
]
