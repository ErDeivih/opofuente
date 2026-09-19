"""Vistas de cambios, dependencias y derivados (S11): lo que la API devuelve.

Son dataclasses de lectura: la decisión de qué queda afectado vive en el dominio (`assess_change`) y
el recorrido de dependencias, en el repositorio. Aquí solo se describe lo que viaja.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True, slots=True)
class DerivedArtifactView:
    """Un derivado del material (hoy, un resumen extractivo) con su procedencia y su estado."""

    id: str
    kind: str
    title: str
    content: str
    document_version_id: str
    document_id: str
    document_title: str
    generator: str
    prompt_template_version: str | None
    model: str | None
    review_status: str
    needs_review: bool
    needs_review_reason: str | None
    needs_review_at: datetime | None
    reviewed_at: datetime | None
    created_at: datetime
    updated_at: datetime
    #: Las secciones de las que depende, para poder decir de dónde sale y qué lo invalidaría.
    sections: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class SectionChangeView:
    """Una sección del diff: su etiqueta, qué le pasó y los dos textos (recortados si toca)."""

    label: str
    kind: str
    left: str | None = None
    right: str | None = None


@dataclass(frozen=True, slots=True)
class AffectedView:
    """Un dependiente afectado por el cambio, con su motivo."""

    kind: str
    id: str
    title: str
    sections: tuple[str, ...]
    reason: str
    reviewable: bool


@dataclass(frozen=True, slots=True)
class ChangeSetView:
    """Una propuesta de cambio: qué se tocó, qué queda por revisar y en qué estado está."""

    id: str
    document_id: str
    document_title: str
    previous_version_id: str
    previous_version_label: str | None
    new_version_id: str
    new_version_label: str | None
    status: str
    created_at: datetime
    confirmed_at: datetime | None
    discarded_at: datetime | None
    reviewed_by: str | None
    sections: tuple[SectionChangeView, ...]
    affected: tuple[AffectedView, ...]
    sections_changed: int
    sections_added: int
    sections_removed: int
    sections_unchanged: int
    #: Lo que la aplicación **no** interpreta. Va con cada cambio, no en un pie de página.
    effect_note: str
    notes: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ChangeOutcome:
    """El resultado de confirmar o descartar un cambio, con lo que se ha hecho exactamente."""

    change: ChangeSetView
    applied: bool
    reason: str | None = None
    #: Los derivados que han quedado pendientes de revisar por este cambio.
    marked: tuple[str, ...] = field(default_factory=tuple)
    superseded_version_id: str | None = None
