"""Esquemas de cambios, dependencias y derivados (S11).

Lo que estos esquemas no hacen: no aceptan un cambio sin decir qué se tocó, no dejan revisar un
derivado que no está pendiente y **no** interpretan el efecto jurídico de nada. El aviso de lo que
la aplicación no decide viaja en cada cambio (`effect_note`).
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, Field

ChangeStatusName = Literal["proposed", "confirmed", "discarded"]
SectionChangeKindName = Literal["added", "removed", "changed", "unchanged"]
ArtifactKindName = Literal["summary"]
ArtifactReviewName = Literal["pending", "reviewed", "discarded"]
DependentKindName = Literal["derived_artifact", "question_version", "rag_answer"]

TitleText = Annotated[str, Field(min_length=1, max_length=200)]


class SectionChangeSchema(BaseModel):
    """Una sección del diff: qué le pasó y, si se puede, sus dos textos."""

    label: str
    kind: SectionChangeKindName
    left: str | None = None
    right: str | None = None


class AffectedSchema(BaseModel):
    """Un dependiente afectado por el cambio, con su motivo."""

    kind: DependentKindName
    id: str
    title: str
    sections: list[str]
    reason: str
    reviewable: bool


class ChangeSetSchema(BaseModel):
    """Una propuesta de cambio, con lo que se invalidaría al confirmarla."""

    id: str
    document_id: str
    document_title: str
    previous_version_id: str
    previous_version_label: str | None = None
    new_version_id: str
    new_version_label: str | None = None
    status: ChangeStatusName
    created_at: datetime
    confirmed_at: datetime | None = None
    discarded_at: datetime | None = None
    reviewed_by: str | None = None
    sections: list[SectionChangeSchema]
    affected: list[AffectedSchema]
    sections_changed: int
    sections_added: int
    sections_removed: int
    sections_unchanged: int
    effect_note: str
    notes: list[str]


class ChangeOutcomeSchema(BaseModel):
    """El resultado de confirmar o descartar: qué se ha hecho exactamente."""

    change: ChangeSetSchema
    applied: bool
    reason: str | None = None
    marked: list[str]
    superseded_version_id: str | None = None


class DerivedArtifactSchema(BaseModel):
    """Un derivado del material (hoy, un resumen extractivo), con su procedencia y su estado."""

    id: str
    kind: ArtifactKindName
    title: str
    content: str
    document_version_id: str
    document_id: str
    document_title: str
    generator: str
    prompt_template_version: str | None = None
    model: str | None = None
    review_status: ArtifactReviewName
    needs_review: bool
    needs_review_reason: str | None = None
    needs_review_at: datetime | None = None
    reviewed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    sections: list[str]


class CreateSummarySchema(BaseModel):
    """Lo que se manda para resumir unas secciones de una versión."""

    document_version_id: str
    section_ids: list[str] = Field(min_length=1)
    title: TitleText | None = None


class ReviewArtifactSchema(BaseModel):
    """Cerrar la revisión de un derivado: sigue valiendo o se aparta."""

    resolution: Literal["reviewed", "discarded"]
