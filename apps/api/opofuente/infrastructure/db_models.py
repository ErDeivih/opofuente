"""Modelos de infraestructura.

Aquí viven las tablas de S01: oposiciones, convocatorias, programa y reglas de examen
(ver ADR-005), además del registro de metadatos de la instancia local que permite a
`/health/ready` comprobar que la migración inicial se aplicó de verdad.

Las entidades de dominio equivalentes, sin SQLAlchemy, están en `opofuente.domain.profiles`.
"""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from opofuente.infrastructure.db import Base

CONVOCATION_STATUSES = ("draft", "active", "superseded", "archived")
NODE_TYPES = ("block", "topic", "epigraph")
PART_KINDS = ("group", "test")
PART_FORMATS = ("single_choice", "multi_mark_error", "psychotechnical")
RULE_KINDS = ("boolean", "integer", "fraction", "text")


class AppMetadataRecord(Base):
    __tablename__ = "app_metadata"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class OppositionRecord(Base):
    __tablename__ = "oppositions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("0"), default=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    convocations: Mapped[list[ConvocationVersionRecord]] = relationship(
        back_populates="opposition",
        order_by="ConvocationVersionRecord.published_at",
    )


class ConvocationVersionRecord(Base):
    __tablename__ = "convocation_versions"
    __table_args__ = (
        CheckConstraint(
            "status IN ('draft', 'active', 'superseded', 'archived')",
            name="ck_convocation_status",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    opposition_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("oppositions.id", ondelete="RESTRICT"), nullable=False
    )
    code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    official_url: Mapped[str] = mapped_column(Text, nullable=False)
    published_at: Mapped[date] = mapped_column(Date, nullable=False)
    exam_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    # Procedencia: identificador del acto oficial y su ubicación dentro del documento.
    source_reference: Mapped[str | None] = mapped_column(Text, nullable=True)
    supersedes_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("convocation_versions.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    opposition: Mapped[OppositionRecord] = relationship(back_populates="convocations")
    # `passive_deletes=True`: SQLite ya aplica ON DELETE CASCADE, así que no hay que borrar los
    # hijos dos veces (la base de datos es la que garantiza la integridad).
    nodes: Mapped[list[CurriculumNodeRecord]] = relationship(
        back_populates="convocation", cascade="all, delete-orphan", passive_deletes=True
    )
    parts: Mapped[list[ExamPartRecord]] = relationship(
        back_populates="convocation", cascade="all, delete-orphan", passive_deletes=True
    )
    rules: Mapped[list[ExamRuleRecord]] = relationship(
        back_populates="convocation", cascade="all, delete-orphan", passive_deletes=True
    )


class CurriculumNodeRecord(Base):
    __tablename__ = "curriculum_nodes"
    __table_args__ = (
        # La identidad de un nodo es su ruta dentro de la convocatoria. `official_code` guarda la
        # numeración que publica la convocatoria y, donde no publica ninguna (los subniveles del
        # temario de Guardia Civil), la secuencia dentro del padre: por eso no puede ser única.
        UniqueConstraint("convocation_version_id", "path", name="uq_curriculum_path"),
        CheckConstraint("node_type IN ('block', 'topic', 'epigraph')", name="ck_node_type"),
        CheckConstraint("depth >= 0", name="ck_node_depth"),
        CheckConstraint("position >= 1", name="ck_node_position"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    convocation_version_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("convocation_versions.id", ondelete="CASCADE"), nullable=False
    )
    parent_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("curriculum_nodes.id", ondelete="CASCADE"), nullable=True
    )
    node_type: Mapped[str] = mapped_column(String(16), nullable=False)
    official_code: Mapped[str] = mapped_column(String(32), nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    path: Mapped[str] = mapped_column(String(128), nullable=False)
    depth: Mapped[int] = mapped_column(Integer, nullable=False)

    convocation: Mapped[ConvocationVersionRecord] = relationship(back_populates="nodes")


class ExamPartRecord(Base):
    __tablename__ = "exam_parts"
    __table_args__ = (
        UniqueConstraint("convocation_version_id", "code", name="uq_exam_part_code"),
        CheckConstraint("kind IN ('group', 'test')", name="ck_part_kind"),
        CheckConstraint(
            "format IS NULL OR format IN ('single_choice', 'multi_mark_error', 'psychotechnical')",
            name="ck_part_format",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    convocation_version_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("convocation_versions.id", ondelete="CASCADE"), nullable=False
    )
    parent_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("exam_parts.id", ondelete="CASCADE"), nullable=True
    )
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    kind: Mapped[str] = mapped_column(String(16), nullable=False)
    format: Mapped[str | None] = mapped_column(String(32), nullable=True)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    ordinary_items: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reserve_items: Mapped[int | None] = mapped_column(Integer, nullable=True)
    options_per_question: Mapped[int | None] = mapped_column(Integer, nullable=True)
    score_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    score_max: Mapped[float | None] = mapped_column(Float, nullable=True)
    pass_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    wrong_penalty_fraction: Mapped[float | None] = mapped_column(Float, nullable=True)
    fail_if_errors_gte: Mapped[int | None] = mapped_column(Integer, nullable=True)
    time_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    structure_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence_quote: Mapped[str] = mapped_column(Text, nullable=False)

    convocation: Mapped[ConvocationVersionRecord] = relationship(back_populates="parts")


class ExamRuleRecord(Base):
    __tablename__ = "exam_rules"
    __table_args__ = (
        UniqueConstraint("convocation_version_id", "code", name="uq_exam_rule_code"),
        CheckConstraint("kind IN ('boolean', 'integer', 'fraction', 'text')", name="ck_rule_kind"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    convocation_version_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("convocation_versions.id", ondelete="CASCADE"), nullable=False
    )
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    kind: Mapped[str] = mapped_column(String(16), nullable=False)
    value_text: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_quote: Mapped[str] = mapped_column(Text, nullable=False)

    convocation: Mapped[ConvocationVersionRecord] = relationship(back_populates="rules")


# ---------------------------------------------------------------------------- S02: ingesta


class SourceArtifactRecord(Base):
    """Un artefacto es un contenido: su identidad es el sha256 de sus bytes (03_DATA-MODEL §3)."""

    __tablename__ = "source_artifacts"
    __table_args__ = (
        CheckConstraint("size_bytes >= 0", name="ck_artifact_size"),
        CheckConstraint("length(sha256) = 64", name="ck_artifact_sha256_length"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    media_type: Mapped[str] = mapped_column(String(128), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(255), nullable=False)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    quarantine_status: Mapped[str] = mapped_column(
        String(16), nullable=False, server_default=text("'none'"), default="none"
    )

    origins: Mapped[list[ArtifactOriginRecord]] = relationship(
        back_populates="artifact", cascade="all, delete-orphan", passive_deletes=True
    )


class ArtifactOriginRecord(Base):
    """Dónde se ha visto ese contenido: el mismo artefacto puede llegar de varios sitios."""

    __tablename__ = "artifact_origins"
    __table_args__ = (
        CheckConstraint(
            "origin_type IN ('file', 'url', 'paste', 'generated')", name="ck_origin_type"
        ),
        # Un origen se identifica por su ubicación: volver a importar la misma carpeta no duplica
        # orígenes, pero un fichero modificado produce otro artefacto (y por tanto otro origen).
        UniqueConstraint("artifact_id", "display_location", name="uq_artifact_origin"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    artifact_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("source_artifacts.id", ondelete="RESTRICT"), nullable=False
    )
    origin_type: Mapped[str] = mapped_column(String(16), nullable=False)
    display_location: Mapped[str] = mapped_column(Text, nullable=False)
    source_path_display: Mapped[str | None] = mapped_column(Text, nullable=True)
    original_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    accessed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    mtime: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    artifact: Mapped[SourceArtifactRecord] = relationship(back_populates="origins")


class IngestionBatchRecord(Base):
    __tablename__ = "ingestion_batches"
    __table_args__ = (
        CheckConstraint("kind IN ('inventory', 'import')", name="ck_batch_kind"),
        CheckConstraint("mode IN ('read_only', 'copy')", name="ck_batch_mode"),
        CheckConstraint(
            "status IN ('queued', 'running', 'succeeded', 'failed', 'cancel_requested', "
            "'cancelled')",
            name="ck_batch_status",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    kind: Mapped[str] = mapped_column(String(16), nullable=False)
    mode: Mapped[str] = mapped_column(String(16), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    source_path_display: Mapped[str] = mapped_column(Text, nullable=False)
    # Ruta real de la carpeta señalada por el usuario: la importación necesita releer el origen,
    # pero **nunca** sale en la API ni en los logs (la interfaz recibe `source_path_display`).
    source_root: Mapped[str | None] = mapped_column(Text, nullable=True)
    counters_json: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("'{}'"), default="{}"
    )
    manifest_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    job_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    inventory_batch_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("ingestion_batches.id", ondelete="SET NULL"), nullable=True
    )

    items: Mapped[list[IngestionItemRecord]] = relationship(
        back_populates="batch", cascade="all, delete-orphan", passive_deletes=True
    )
    issues: Mapped[list[ImportIssueRecord]] = relationship(
        back_populates="batch", cascade="all, delete-orphan", passive_deletes=True
    )


class IngestionItemRecord(Base):
    __tablename__ = "ingestion_items"
    __table_args__ = (
        CheckConstraint(
            "status IN ('discovered', 'inventoried', 'omitted', 'copied', 'hashed', "
            "'extracted', 'unsupported_preserved', 'expanded', 'ocr_pending', "
            "'failed', 'cancelled')",
            name="ck_item_status",
        ),
        UniqueConstraint("batch_id", "relative_path", name="uq_item_path"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    batch_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("ingestion_batches.id", ondelete="CASCADE"), nullable=False
    )
    relative_path: Mapped[str] = mapped_column(Text, nullable=False)
    original_name: Mapped[str] = mapped_column(Text, nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    mtime: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    media_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    artifact_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("source_artifacts.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    position: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))

    batch: Mapped[IngestionBatchRecord] = relationship(back_populates="items")


class ImportIssueRecord(Base):
    __tablename__ = "import_issues"
    __table_args__ = (
        CheckConstraint("severity IN ('info', 'warning', 'error')", name="ck_issue_severity"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    batch_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("ingestion_batches.id", ondelete="CASCADE"), nullable=False
    )
    item_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("ingestion_items.id", ondelete="CASCADE"), nullable=True
    )
    code: Mapped[str] = mapped_column(String(48), nullable=False)
    severity: Mapped[str] = mapped_column(String(16), nullable=False)
    safe_message: Mapped[str] = mapped_column(Text, nullable=False)
    #: Ruta relativa del elemento afectado. Los directorios omitidos y los enlaces que salen de la
    #: carpeta no tienen entrada propia, así que la ruta no se puede recuperar por `item_id`.
    relative_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    details_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolution: Mapped[str | None] = mapped_column(Text, nullable=True)

    batch: Mapped[IngestionBatchRecord] = relationship(back_populates="issues")


class JobRecord(Base):
    """Cola persistida con lease. Sobrevive a un reinicio: los leases vencidos vuelven a la cola."""

    __tablename__ = "jobs"
    __table_args__ = (
        CheckConstraint(
            "status IN ('queued', 'leased', 'running', 'succeeded', 'failed', "
            "'cancel_requested', 'cancelled')",
            name="ck_job_status",
        ),
        CheckConstraint(
            "job_type IN ("
            "'inventory_source', 'ingest_batch', 'extract_artifact', 'classify_document', "
            "'parse_question_set', 'build_fts', 'embed_spans', 'diff_versions', "
            "'invalidate_derivatives', 'export_backup')",
            name="ck_job_type",
        ),
        CheckConstraint("progress >= 0 AND progress <= 1", name="ck_job_progress"),
        CheckConstraint("attempts >= 0", name="ck_job_attempts"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    job_type: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    payload_json: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("'{}'"), default="{}"
    )
    progress: Mapped[float] = mapped_column(Float, nullable=False, server_default=text("0"))
    step: Mapped[str | None] = mapped_column(Text, nullable=True)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    max_attempts: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("3"))
    error_code: Mapped[str | None] = mapped_column(String(48), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(128), nullable=True)
    lease_owner: Mapped[str | None] = mapped_column(String(64), nullable=True)
    lease_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    #: Antes de esta fecha el trabajo no se puede reclamar: es la espera entre reintentos. Sin
    #: ella, un `retry_delay_seconds` escrito en el mensaje no aplazaría nada de verdad.
    not_before: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancel_requested_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


# ------------------------------------------------------------------- S03: representaciones


class ExtractedRepresentationRecord(Base):
    """Texto extraído de un artefacto, con su extractor, su calidad y sus avisos.

    Una fila por `(artefacto, extractor, versión, tipo)`: volver a ejecutar el mismo extractor no
    duplica nada, y **otra versión crea otra representación** porque el texto puede ser distinto
    (03_DATA-MODEL §3). El texto en sí no vive aquí: se guarda en `data/extracted/…` y esta fila
    apunta a él con `text_storage_key`.
    """

    __tablename__ = "extracted_representations"
    __table_args__ = (
        CheckConstraint(
            "kind IN ('native_text', 'ocr', 'plain_text', 'html_text', 'csv_preview', "
            "'json_preview', 'image_metadata')",
            name="ck_representation_kind",
        ),
        CheckConstraint(
            "status IN ('extracted', 'pending', 'empty', 'failed')",
            name="ck_representation_status",
        ),
        CheckConstraint(
            "quality IN ('good', 'usable_with_warnings', 'ocr_unreviewed', 'poor', 'failed')",
            name="ck_representation_quality",
        ),
        CheckConstraint("char_count >= 0", name="ck_representation_chars"),
        UniqueConstraint(
            "artifact_id",
            "extractor_name",
            "extractor_version",
            "kind",
            name="uq_representation_extractor",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    artifact_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("source_artifacts.id", ondelete="CASCADE"), nullable=False
    )
    extractor_name: Mapped[str] = mapped_column(String(64), nullable=False)
    extractor_version: Mapped[str] = mapped_column(String(32), nullable=False)
    kind: Mapped[str] = mapped_column(String(24), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    quality: Mapped[str] = mapped_column(String(24), nullable=False)
    language: Mapped[str | None] = mapped_column(String(16), nullable=True)
    text_storage_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    char_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ocr_candidate: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("0"), default=False
    )
    sections_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    warnings_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    format_version: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("1"), default=1
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    artifact: Mapped[SourceArtifactRecord] = relationship()
