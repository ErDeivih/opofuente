"""DTO de clasificación, revisión, cobertura y duplicados (contrato §3, §6 y §7).

La API no decide: sirve lo que el servicio decidió. Los valores viajan con su etiqueta legible
(`value_label`) y con la banda de confianza calculada, para que la interfaz no tenga que interpretar
vocabularios ni umbrales por su cuenta.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class AlternativeSchema(BaseModel):
    value: str
    confidence: float


class ProposalSchema(BaseModel):
    id: str
    subject_type: Literal["artifact", "representation"]
    subject_id: str
    subject_label: str | None = None
    axis: Literal["document_type", "opposition", "topic", "authority", "rights"]
    proposed_value: str
    value_label: str | None = None
    confidence: float
    band: Literal["high", "medium", "low"]
    is_critical: bool
    status: Literal["pending", "accepted", "rejected", "superseded", "auto_applied_provisional"]
    engine_name: str
    engine_version: str
    alternatives: list[AlternativeSchema] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    created_at: datetime | None = None
    decided_at: datetime | None = None
    decision_note: str | None = None


class ProposalPageSchema(BaseModel):
    proposals: list[ProposalSchema]
    total: int
    limit: int
    offset: int


class ReviewGroupSchema(BaseModel):
    key: str
    subject_type: str
    axis: str
    proposed_value: str
    label: str
    proposal_ids: list[str]
    size: int
    min_confidence: float
    max_confidence: float
    is_critical: bool


class DecisionRequestSchema(BaseModel):
    """Decisión explícita sobre una propuesta. `override_value` corrige el valor propuesto."""

    note: str | None = None
    override_value: str | None = None
    coverage_type: Literal["mention", "partial", "complete"] = "partial"


class BulkDecisionRequestSchema(BaseModel):
    """Decisión en lote con excepciones explícitas (11_IMPLEMENTATION-SLICES S04)."""

    proposal_ids: list[str] = Field(min_length=1)
    decision: Literal["accepted", "rejected"]
    note: str | None = None
    overrides: dict[str, str] = Field(default_factory=dict)
    excluded: list[str] = Field(default_factory=list)


class DecisionOutcomeSchema(BaseModel):
    proposal_id: str
    status: str
    applied: bool
    mapping_id: str | None = None
    audit_event_id: str | None = None
    reason: str | None = None


class BulkDecisionResponseSchema(BaseModel):
    outcomes: list[DecisionOutcomeSchema]
    applied: int
    conflicts: int
    requested: int
    excluded: list[str] = Field(default_factory=list)


class MappingSchema(BaseModel):
    id: str
    node_id: str
    node_path: str
    node_title: str
    node_depth: int
    subject_type: str
    subject_id: str
    subject_label: str | None = None
    coverage_type: Literal["mention", "partial", "complete"]
    depth: int
    confidence: float
    status: Literal["provisional", "accepted", "rejected"]
    source_proposal_id: str | None = None
    approved_at: datetime | None = None


class CoverageNodeSchema(BaseModel):
    node_id: str
    path: str
    title: str
    depth: int
    provisional: int
    accepted: int
    materials: list[str] = Field(default_factory=list)


class CoverageSchema(BaseModel):
    """Cobertura de un nodo y de su subárbol: provisional y aceptada, nunca mezcladas."""

    node_id: str
    path: str
    title: str
    provisional: int
    accepted: int
    unclassified_subjects: int
    materials_total: int
    subtree: list[CoverageNodeSchema] = Field(default_factory=list)


class DuplicateMemberSchema(BaseModel):
    subject_type: str
    subject_id: str
    subject_label: str | None = None
    similarity: float
    is_representative: bool


class DuplicateClusterSchema(BaseModel):
    id: str
    kind: Literal["same_text", "near_duplicate"]
    relation: Literal["revision_candidate", "subset", "superset", "similar"]
    signature: str
    status: Literal["open", "resolved", "dismissed"]
    members: list[DuplicateMemberSchema] = Field(default_factory=list)
    created_at: datetime | None = None
    resolved_at: datetime | None = None
    resolution_note: str | None = None


class ResolveDuplicateRequestSchema(BaseModel):
    relation: Literal["revision_candidate", "subset", "superset", "similar"]
    note: str | None = None


class AcceptedValueSchema(BaseModel):
    """Un eje de la clasificación vigente de un material, con su etiqueta legible."""

    axis: str
    value: str
    value_label: str | None = None
    status: Literal["accepted", "auto_applied_provisional"]
    confidence: float
    is_critical: bool
    decided_at: datetime | None = None


class AcceptedClassificationSchema(BaseModel):
    """Lo que consta de un material: lo aceptado y lo que quedó provisional (revisable)."""

    subject_type: str
    subject_id: str
    subject_label: str | None = None
    pending_review: bool
    values: list[AcceptedValueSchema] = Field(default_factory=list)


class ClassificationReportSchema(BaseModel):
    """Qué dejó la última pasada de clasificación: se sirve tal cual, sin redondear nada."""

    subjects: int
    proposals_created: int
    proposals_unchanged: int
    subjects_without_signals: int
    auto_applied: int
    duplicates_found: int
    summary: str
