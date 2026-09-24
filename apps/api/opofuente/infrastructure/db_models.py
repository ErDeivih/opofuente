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
    Index,
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
            "status IN ('draft', 'active', 'available', 'superseded', 'archived')",
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
    # Por qué la fecha de ejercicio es la que es, o por qué no hay ninguna: distingue «no lo sé» de
    # «lo dirá otra resolución» (S12.2).
    exam_date_note: Mapped[str | None] = mapped_column(Text, nullable=True)
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
        # Un origen se identifica por su ubicación **y su canal**: el mismo contenido puede entrar
        # como fichero y como texto pegado con la misma etiqueta (`tema.txt` los dos) y son dos
        # orígenes distintos. Volver a importar la misma carpeta no duplica orígenes, pero un
        # fichero modificado produce otro artefacto (y por tanto otro origen).
        UniqueConstraint(
            "artifact_id", "origin_type", "display_location", name="uq_artifact_origin"
        ),
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
            "'cancelled', 'paused')",
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
    #: Niveles de contenedor recorridos hasta esta entrada. Un ZIP de primer nivel deja a sus
    #: miembros en 1; un ZIP que venía dentro de otro llega con 1 y expandirlo daría 2. El límite de
    #: anidamiento se comprueba con este número, no con el nombre del fichero.
    container_depth: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    #: De dónde salió **esta** entrada (`file`, `paste`, `url`), no de dónde salió su artefacto: el
    #: mismo contenido puede entrar por tres vías distintas y cada entrada tiene la suya.
    origin_type: Mapped[str | None] = mapped_column(String(16), nullable=True)
    #: Cómo se muestra ese origen. Nunca lleva cadena de consulta: una URL con token se guarda sin
    #: ella, porque este valor viaja a la API y a la interfaz.
    origin_display: Mapped[str | None] = mapped_column(Text, nullable=True)

    batch: Mapped[IngestionBatchRecord] = relationship(back_populates="items")
    #: Representaciones que salieron de esta entrada: pueden ser varias (texto nativo **y** OCR, y
    #: una por versión de extractor), así que la relación es de muchos a muchos.
    representations: Mapped[list[ExtractedRepresentationRecord]] = relationship(
        secondary="item_representations", viewonly=True
    )


class ItemRepresentationRecord(Base):
    """Qué representaciones salieron de qué entrada (relación de muchos a muchos).

    Tabla explícita en lugar de una clave ajena singular: una entrada puede tener su texto nativo,
    su OCR y las versiones de extractor que hagan falta, y un mismo texto (el fichero y su copia)
    puede estar producido por varias entradas. La unicidad es por pareja.
    """

    __tablename__ = "item_representations"
    __table_args__ = (
        UniqueConstraint("item_id", "representation_id", name="uq_item_representation"),
    )

    item_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("ingestion_items.id", ondelete="CASCADE"), primary_key=True
    )
    representation_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("extracted_representations.id", ondelete="CASCADE"),
        primary_key=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


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
            "'cancel_requested', 'cancelled', 'paused')",
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


# ----------------------------------------- S04: clasificación, cobertura, duplicados y auditoría


class ClassificationProposalRecord(Base):
    """Lo que un motor **propone** sobre un artefacto o una representación.

    No es un hecho: hasta que se acepta no cambia nada del material. La identidad incluye el motor
    y su versión, así que volver a clasificar con el mismo motor no duplica propuestas y un motor
    nuevo sí puede proponer otra cosa sobre el mismo eje.
    """

    __tablename__ = "classification_proposals"
    __table_args__ = (
        CheckConstraint(
            "subject_type IN ('artifact', 'representation')", name="ck_proposal_subject"
        ),
        CheckConstraint(
            "axis IN ('document_type', 'opposition', 'topic', 'authority', 'rights')",
            name="ck_proposal_axis",
        ),
        CheckConstraint(
            "status IN ('pending', 'accepted', 'rejected', 'superseded', "
            "'auto_applied_provisional')",
            name="ck_proposal_status",
        ),
        CheckConstraint("confidence >= 0 AND confidence <= 1", name="ck_proposal_confidence"),
        # Sin fecha de decisión no hay decisión, y sin decisión no hay nada que deshacer.
        CheckConstraint(
            "(status = 'pending' AND decided_at IS NULL) "
            "OR (status <> 'pending' AND decided_at IS NOT NULL)",
            name="ck_proposal_decision",
        ),
        UniqueConstraint(
            "subject_type",
            "subject_id",
            "axis",
            "engine_name",
            "engine_version",
            "proposed_value",
            name="uq_proposal_identity",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    subject_type: Mapped[str] = mapped_column(String(24), nullable=False)
    subject_id: Mapped[str] = mapped_column(String(36), nullable=False)
    axis: Mapped[str] = mapped_column(String(24), nullable=False)
    proposed_value: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    alternatives_json: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("'[]'")
    )
    evidence_json: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'[]'"))
    engine_name: Mapped[str] = mapped_column(String(64), nullable=False)
    engine_version: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    decision_note: Mapped[str | None] = mapped_column(Text, nullable=True)


class CurriculumMappingRecord(Base):
    """Material asignado a un nodo del programa: la base de la cobertura.

    `curriculum_node_id` es `ON DELETE RESTRICT` a propósito (DEBT-005 y ADR-007): un nodo con
    material asignado no se puede borrar, ni desde la siembra ni desde SQL directo.
    """

    __tablename__ = "curriculum_mappings"
    __table_args__ = (
        # 0013 amplía el vocabulario: un mapeo puede apuntar también a una versión de documento, a
        # una sección o a una cita textual. El modelo refleja el esquema migrado, no el de 0012.
        CheckConstraint(
            "subject_type IN ('artifact', 'representation', 'document_version', "
            "'section', 'evidence', 'question_version')",
            name="ck_mapping_subject",
        ),
        CheckConstraint(
            "coverage_type IN ('mention', 'partial', 'complete')", name="ck_mapping_coverage"
        ),
        CheckConstraint(
            "status IN ('provisional', 'accepted', 'rejected')", name="ck_mapping_status"
        ),
        CheckConstraint("depth >= 0", name="ck_mapping_depth"),
        CheckConstraint("confidence >= 0 AND confidence <= 1", name="ck_mapping_confidence"),
        CheckConstraint(
            "status <> 'accepted' OR approved_at IS NOT NULL", name="ck_mapping_approved"
        ),
        UniqueConstraint(
            "curriculum_node_id", "subject_type", "subject_id", name="uq_mapping_identity"
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    curriculum_node_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("curriculum_nodes.id", ondelete="RESTRICT"), nullable=False
    )
    subject_type: Mapped[str] = mapped_column(String(24), nullable=False)
    subject_id: Mapped[str] = mapped_column(String(36), nullable=False)
    coverage_type: Mapped[str] = mapped_column(String(16), nullable=False)
    depth: Mapped[int] = mapped_column(Integer, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    source_proposal_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("classification_proposals.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    node: Mapped[CurriculumNodeRecord] = relationship()


class DossierSnapshotRecord(Base):
    """Una versión guardada del dossier de un tema (S13).

    El dossier **no vive aquí**: se calcula desde el corpus (evidencias y mapeos) cada vez que se
    pide,
    porque la verdad está en las fuentes. Esta tabla guarda lo que se leyó en un momento dado, para
    poder compararlo con lo que se lee ahora; `payload_json` lleva el dossier entero, no una
    referencia,
    porque una versión anterior tiene que poder leerse **como se leyó**.
    """

    __tablename__ = "dossier_snapshots"
    __table_args__ = (
        CheckConstraint("length(content_hash) = 64", name="ck_dossier_hash"),
        CheckConstraint("sources_count >= 0 AND passages_count >= 0", name="ck_dossier_counts"),
        UniqueConstraint("curriculum_node_id", "content_hash", name="uq_dossier_snapshot_hash"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    curriculum_node_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("curriculum_nodes.id", ondelete="CASCADE"), nullable=False
    )
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    built_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    sources_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    passages_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    payload_json: Mapped[str] = mapped_column(Text, nullable=False)


class DuplicateClusterRecord(Base):
    """Grupo de material con el mismo texto o muy parecido.
    Los duplicados **exactos** de bytes no llegan aquí: ya son un artefacto con varios orígenes.
    Aquí viven el mismo texto con otra codificación o maquetación (`same_text`) y los casi
    duplicados.
    """

    __tablename__ = "duplicate_clusters"
    __table_args__ = (
        CheckConstraint("kind IN ('same_text', 'near_duplicate')", name="ck_cluster_kind"),
        CheckConstraint(
            "relation IN ('revision_candidate', 'subset', 'superset', 'similar')",
            name="ck_cluster_relation",
        ),
        CheckConstraint("status IN ('open', 'resolved', 'dismissed')", name="ck_cluster_status"),
        CheckConstraint("status = 'open' OR resolved_at IS NOT NULL", name="ck_cluster_resolved"),
        UniqueConstraint("kind", "signature", name="uq_cluster_signature"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    kind: Mapped[str] = mapped_column(String(24), nullable=False)
    relation: Mapped[str] = mapped_column(String(24), nullable=False)
    signature: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolution_note: Mapped[str | None] = mapped_column(Text, nullable=True)


class DuplicateClusterMemberRecord(Base):
    """Miembro de un cluster: artefacto o representación, con su similitud respecto al grupo."""

    __tablename__ = "duplicate_cluster_members"
    __table_args__ = (
        CheckConstraint("subject_type IN ('artifact', 'representation')", name="ck_member_subject"),
        CheckConstraint("similarity >= 0 AND similarity <= 1", name="ck_member_similarity"),
        UniqueConstraint("cluster_id", "subject_type", "subject_id", name="uq_cluster_member"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    cluster_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("duplicate_clusters.id", ondelete="CASCADE"), nullable=False
    )
    subject_type: Mapped[str] = mapped_column(String(24), nullable=False)
    subject_id: Mapped[str] = mapped_column(String(36), nullable=False)
    similarity: Mapped[float] = mapped_column(Float, nullable=False)
    is_representative: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("0"), default=False
    )

    cluster: Mapped[DuplicateClusterRecord] = relationship()


class AuditEventRecord(Base):
    """Acción que altera autoridad, clasificación, respuesta o versión.

    Guarda el antes/después **sanitizado** (estados, identificadores y valores de clasificación),
    nunca el contenido del material: es la traza que hace verificable el «deshacer».
    """

    __tablename__ = "audit_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    actor: Mapped[str] = mapped_column(String(32), nullable=False)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    object_type: Mapped[str] = mapped_column(String(32), nullable=False)
    object_id: Mapped[str] = mapped_column(String(36), nullable=False)
    before_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    after_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    correlation_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


# ------------------------------------------------- S05: documentos, versiones y derechos


class RightsStatusRecord(Base):
    """Condiciones de uso de una fuente. `unknown` significa restringido, no permiso."""

    __tablename__ = "rights_statuses"
    __table_args__ = (
        CheckConstraint(
            "review_status IN ('unknown', 'reviewed', 'restricted')", name="ck_rights_review"
        ),
        UniqueConstraint("code", name="uq_rights_code"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    code: Mapped[str] = mapped_column(String(48), nullable=False)
    license_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    license_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    attribution: Mapped[str | None] = mapped_column(Text, nullable=True)
    commercial_reuse: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("0"), default=False
    )
    sharing: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("0"), default=False
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    review_status: Mapped[str] = mapped_column(
        String(16), nullable=False, server_default=text("'unknown'"), default="unknown"
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class LogicalDocumentRecord(Base):
    """La obra: titulo canonico, tipo documental y a quien pertenece."""

    __tablename__ = "logical_documents"
    __table_args__ = (
        CheckConstraint(
            "document_type IN ('convocation', 'curriculum', 'law_or_regulation', "
            "'official_technical', 'private_syllabus', 'personal_notes', 'official_exam', "
            "'answer_key', 'private_question_bank', 'practical_case', 'flashcards', "
            "'community_material', 'unknown')",
            name="ck_document_type",
        ),
        CheckConstraint(
            "owner_scope IN ('public', 'private_user', 'generated')", name="ck_document_scope"
        ),
        CheckConstraint("length(trim(canonical_title)) > 0", name="ck_document_title"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    canonical_title: Mapped[str] = mapped_column(Text, nullable=False)
    document_type: Mapped[str] = mapped_column(String(32), nullable=False)
    authority_tier: Mapped[str | None] = mapped_column(String(8), nullable=True)
    owner_scope: Mapped[str] = mapped_column(
        String(16), nullable=False, server_default=text("'private_user'"), default="private_user"
    )
    canonical_identifier: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    versions: Mapped[list[DocumentVersionRecord]] = relationship(
        back_populates="document", cascade="all, delete-orphan", passive_deletes=True
    )


class DocumentVersionRecord(Base):
    """Un fichero concreto que representa la obra, con su vigencia y sus derechos."""

    __tablename__ = "document_versions"
    __table_args__ = (
        CheckConstraint(
            "status IN ('candidate', 'accepted', 'outdated', 'superseded', "
            "'withdrawn', 'rejected')",
            name="ck_version_status",
        ),
        CheckConstraint(
            "status <> 'accepted' OR approved_at IS NOT NULL", name="ck_version_approved"
        ),
        CheckConstraint(
            "valid_from IS NULL OR valid_to IS NULL OR valid_to >= valid_from",
            name="ck_version_validity",
        ),
        CheckConstraint("supersedes_id IS NULL OR supersedes_id <> id", name="ck_version_not_self"),
        UniqueConstraint("logical_document_id", "artifact_id", name="uq_version_artifact"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    logical_document_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("logical_documents.id", ondelete="CASCADE"), nullable=False
    )
    artifact_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("source_artifacts.id", ondelete="RESTRICT"), nullable=False
    )
    representation_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("extracted_representations.id", ondelete="SET NULL"),
        nullable=True,
    )
    version_label: Mapped[str | None] = mapped_column(Text, nullable=True)
    published_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    valid_from: Mapped[date | None] = mapped_column(Date, nullable=True)
    valid_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    retrieved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    language: Mapped[str | None] = mapped_column(String(16), nullable=True)
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, server_default=text("'candidate'"), default="candidate"
    )
    supersedes_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("document_versions.id", ondelete="SET NULL"), nullable=True
    )
    rights_status_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("rights_statuses.id", ondelete="SET NULL"), nullable=True
    )
    official_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    approved_by: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    document: Mapped[LogicalDocumentRecord] = relationship(back_populates="versions")
    rights: Mapped[RightsStatusRecord | None] = relationship()
    sections: Mapped[list[DocumentSectionRecord]] = relationship(
        back_populates="version", cascade="all, delete-orphan", passive_deletes=True
    )


class DocumentSectionRecord(Base):
    """Estructura del documento: donde empieza y acaba cada parte, con su pagina."""

    __tablename__ = "document_sections"
    __table_args__ = (
        CheckConstraint(
            "section_type IN ('page', 'title', 'chapter', 'article', 'provision', "
            "'technical', 'topic')",
            name="ck_section_type",
        ),
        CheckConstraint("position >= 1", name="ck_section_position"),
        CheckConstraint("char_start >= 0 AND char_end >= char_start", name="ck_section_offsets"),
        CheckConstraint(
            "page_start IS NULL OR page_end IS NULL OR page_end >= page_start",
            name="ck_section_pages",
        ),
        UniqueConstraint("document_version_id", "ordinal", name="uq_section_ordinal"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    document_version_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("document_versions.id", ondelete="CASCADE"), nullable=False
    )
    parent_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("document_sections.id", ondelete="CASCADE"), nullable=True
    )
    section_type: Mapped[str] = mapped_column(String(16), nullable=False)
    label: Mapped[str | None] = mapped_column(Text, nullable=True)
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    position: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("1"))
    page_start: Mapped[int | None] = mapped_column(Integer, nullable=True)
    page_end: Mapped[int | None] = mapped_column(Integer, nullable=True)
    char_start: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    char_end: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    ordinal: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("1"))

    version: Mapped[DocumentVersionRecord] = relationship(back_populates="sections")


class EvidenceSpanRecord(Base):
    """Unidad citable: el texto exacto con su seccion, su pagina y su etiqueta de cita."""

    __tablename__ = "evidence_spans"
    __table_args__ = (
        CheckConstraint(
            "index_status IN ('pending', 'indexed', 'failed', 'stale')", name="ck_evidence_index"
        ),
        CheckConstraint("char_start >= 0 AND char_end >= char_start", name="ck_evidence_offsets"),
        CheckConstraint("ordinal >= 1", name="ck_evidence_ordinal"),
        UniqueConstraint("document_version_id", "ordinal", name="uq_evidence_ordinal"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    document_version_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("document_versions.id", ondelete="CASCADE"), nullable=False
    )
    section_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("document_sections.id", ondelete="SET NULL"), nullable=True
    )
    ordinal: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("1"))
    char_start: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    char_end: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    page: Mapped[int | None] = mapped_column(Integer, nullable=True)
    citation_label: Mapped[str | None] = mapped_column(Text, nullable=True)
    quality: Mapped[str | None] = mapped_column(String(24), nullable=True)
    index_status: Mapped[str] = mapped_column(
        String(16), nullable=False, server_default=text("'pending'"), default="pending"
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_text: Mapped[str] = mapped_column(Text, nullable=False)


class CollectionRecord(Base):
    """Coleccion personal: agrupa material sin duplicar bytes."""

    __tablename__ = "collections"
    __table_args__ = (CheckConstraint("length(trim(name)) > 0", name="ck_collection_name"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class CollectionItemRecord(Base):
    """Membresia de un sujeto en una coleccion, con su posicion."""

    __tablename__ = "collection_items"
    __table_args__ = (
        CheckConstraint(
            "subject_type IN ('artifact', 'representation', 'document_version', "
            "'section', 'evidence', 'question_version')",
            name="ck_collection_subject",
        ),
        UniqueConstraint("collection_id", "subject_type", "subject_id", name="uq_collection_item"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    collection_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("collections.id", ondelete="CASCADE"), nullable=False
    )
    subject_type: Mapped[str] = mapped_column(String(24), nullable=False)
    subject_id: Mapped[str] = mapped_column(String(36), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("1"))
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


# ----------------------------------------- S06: preguntas, claves, evidencias y explicaciones


class QuestionSetRecord(Base):
    """Un conjunto de preguntas: examen oficial, banco privado, practica o lote generado.

    El **modelo** (A/B) es del conjunto, no de cada pregunta: un examen modelo A es un conjunto con
    su propia plantilla, y por eso `answer_key_versions` no necesita repetir el modelo.
    """

    __tablename__ = "question_sets"
    __table_args__ = (
        CheckConstraint(
            "set_type IN ('official_exam', 'private_bank', 'practice', 'generated_batch')",
            name="ck_question_set_type",
        ),
        CheckConstraint(
            "status IN ('draft', 'confirmed', 'archived')", name="ck_question_set_status"
        ),
        CheckConstraint("length(trim(title)) > 0", name="ck_question_set_title"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    opposition_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("oppositions.id", ondelete="RESTRICT"), nullable=False
    )
    convocation_version_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("convocation_versions.id", ondelete="SET NULL"),
        nullable=True,
    )
    set_type: Mapped[str] = mapped_column(String(24), nullable=False)
    model_code: Mapped[str | None] = mapped_column(String(8), nullable=True)
    held_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    source_document_version_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("document_versions.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, server_default=text("'draft'"), default="draft"
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class QuestionVersionRecord(Base):
    """Una version concreta de una pregunta, con su cita y su procedencia.

    `stable_key` es la identidad de la pregunta entre versiones y `version_no` distingue las
    correcciones: corregir una pregunta **no** borra la anterior, la sustituye.
    """

    __tablename__ = "question_versions"
    __table_args__ = (
        CheckConstraint(
            "question_type IN ('single_choice', 'multi_mark_error', 'true_false', "
            "'free_text_reference')",
            name="ck_question_type",
        ),
        CheckConstraint(
            "status IN ('incomplete', 'complete', 'verified', 'conflicting', 'annulled', "
            "'superseded')",
            name="ck_question_status",
        ),
        CheckConstraint(
            "origin_type IN ('official', 'private', 'generated')", name="ck_question_origin"
        ),
        CheckConstraint("length(trim(stem)) > 0", name="ck_question_stem"),
        CheckConstraint("version_no >= 1", name="ck_question_version_no"),
        CheckConstraint("position >= 1", name="ck_question_position"),
        CheckConstraint(
            "reserve_order IS NULL OR reserve_order >= 1", name="ck_question_reserve_order"
        ),
        CheckConstraint("is_reserve OR reserve_order IS NULL", name="ck_question_reserve_flag"),
        CheckConstraint(
            "supersedes_id IS NULL OR supersedes_id <> id", name="ck_question_not_self"
        ),
        UniqueConstraint("question_set_id", "stable_key", "version_no", name="uq_question_version"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    question_set_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("question_sets.id", ondelete="CASCADE"), nullable=False
    )
    stable_key: Mapped[str] = mapped_column(String(64), nullable=False)
    version_no: Mapped[int] = mapped_column(Integer, nullable=False)
    stem: Mapped[str] = mapped_column(Text, nullable=False)
    question_type: Mapped[str] = mapped_column(String(24), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    is_reserve: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("0"), default=False
    )
    reserve_order: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, server_default=text("'incomplete'"), default="incomplete"
    )
    origin_type: Mapped[str] = mapped_column(String(16), nullable=False)
    source_section_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("document_sections.id", ondelete="SET NULL"), nullable=True
    )
    supersedes_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("question_versions.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    #: Motivo de una corrección local: quien lea la pregunta después tiene que ver por qué cambió.
    note: Mapped[str | None] = mapped_column(Text, nullable=True)


class OptionVersionRecord(Base):
    """Una opcion de una version de pregunta.

    La clave estable y la posicion son distintas a proposito: el mismo conjunto de opciones
    reordenado en el modelo B tiene las mismas claves y otras posiciones.
    """

    __tablename__ = "option_versions"
    __table_args__ = (
        CheckConstraint("position >= 1", name="ck_option_position"),
        CheckConstraint("length(trim(text)) > 0", name="ck_option_text"),
        UniqueConstraint("question_version_id", "stable_key", name="uq_option_key"),
        UniqueConstraint("question_version_id", "position", name="uq_option_position"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    question_version_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("question_versions.id", ondelete="CASCADE"), nullable=False
    )
    stable_key: Mapped[str] = mapped_column(String(16), nullable=False)
    label: Mapped[str | None] = mapped_column(String(16), nullable=True)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)


class AnswerKeyVersionRecord(Base):
    """Una version de la plantilla de un conjunto, con su aprobacion.

    Una clave activa esta aprobada, y solo puede haber **una activa por conjunto** (invariante 5):
    el indice unico parcial lo impone en la base, no solo en el codigo. Que una clave **oficial**
    tenga ademas plantilla oficial enlazada depende del tipo del conjunto y se comprueba en el
    servicio.
    """

    __tablename__ = "answer_key_versions"
    __table_args__ = (
        CheckConstraint(
            "status IN ('draft', 'active', 'superseded', 'rejected')", name="ck_key_status"
        ),
        CheckConstraint("version_no >= 1", name="ck_key_version_no"),
        CheckConstraint("status <> 'active' OR approved_at IS NOT NULL", name="ck_key_approved"),
        CheckConstraint("supersedes_id IS NULL OR supersedes_id <> id", name="ck_key_not_self"),
        UniqueConstraint("question_set_id", "version_no", name="uq_key_version"),
        Index(
            "uq_answer_key_active",
            "question_set_id",
            unique=True,
            sqlite_where=text("status = 'active'"),
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    question_set_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("question_sets.id", ondelete="CASCADE"), nullable=False
    )
    source_document_version_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("document_versions.id", ondelete="SET NULL"), nullable=True
    )
    version_no: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, server_default=text("'draft'"), default="draft"
    )
    supersedes_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("answer_key_versions.id", ondelete="SET NULL"), nullable=True
    )
    published_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class AnswerKeyEntryRecord(Base):
    """Que le pasa a una pregunta en una plantilla: con clave, anulada, sin responder o en
    conflicto."""

    __tablename__ = "answer_key_entries"
    __table_args__ = (
        CheckConstraint(
            "outcome IN ('keyed', 'annulled', 'unanswered', 'conflicting')",
            name="ck_key_entry_outcome",
        ),
        CheckConstraint(
            "outcome <> 'keyed' OR (correct_option_keys_json IS NOT NULL "
            "AND correct_option_keys_json <> '[]')",
            name="ck_key_entry_has_key",
        ),
    )

    answer_key_version_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("answer_key_versions.id", ondelete="CASCADE"), primary_key=True
    )
    question_version_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("question_versions.id", ondelete="CASCADE"), primary_key=True
    )
    outcome: Mapped[str] = mapped_column(String(16), nullable=False)
    correct_option_keys_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class QuestionEvidenceRecord(Base):
    """Que evidencia sostiene que parte de una pregunta, con su claim y su estado de revision."""

    __tablename__ = "question_evidence"
    __table_args__ = (
        CheckConstraint(
            "role IN ('stem', 'correct', 'distractor', 'explanation')",
            name="ck_question_evidence_role",
        ),
        CheckConstraint(
            "status IN ('proposed', 'accepted', 'rejected')", name="ck_question_evidence_status"
        ),
    )

    question_version_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("question_versions.id", ondelete="CASCADE"), primary_key=True
    )
    # La cita de una pregunta no se queda sin su span: el material citado no se borra por debajo.
    evidence_span_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("evidence_spans.id", ondelete="RESTRICT"), primary_key=True
    )
    role: Mapped[str] = mapped_column(String(16), primary_key=True)
    claim: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, server_default=text("'proposed'"), default="proposed"
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class QuestionExplanationRecord(Base):
    """Explicacion de la pregunta entera (`option_stable_key` nulo) o de una opcion.

    Si la escribio un modelo, se guarda **cual** y con que version de plantilla: una explicacion
    generada sin eso no es trazable, y la base lo exige.
    """

    __tablename__ = "question_explanations"
    __table_args__ = (
        CheckConstraint(
            "origin IN ('official', 'private', 'generated')", name="ck_explanation_origin"
        ),
        CheckConstraint(
            "status IN ('draft', 'reviewed', 'rejected')", name="ck_explanation_status"
        ),
        CheckConstraint("length(trim(text)) > 0", name="ck_explanation_text"),
        CheckConstraint(
            "origin <> 'generated' OR model_name IS NOT NULL", name="ck_explanation_generated"
        ),
        UniqueConstraint("question_version_id", "option_stable_key", name="uq_explanation_option"),
        Index(
            "uq_explanation_question",
            "question_version_id",
            unique=True,
            sqlite_where=text("option_stable_key IS NULL"),
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    question_version_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("question_versions.id", ondelete="CASCADE"), nullable=False
    )
    option_stable_key: Mapped[str | None] = mapped_column(String(16), nullable=True)
    origin: Mapped[str] = mapped_column(String(16), nullable=False)
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, server_default=text("'draft'"), default="draft"
    )
    model_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    prompt_template_version: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)


class QuestionIssueReportRecord(Base):
    """Lo que reporta quien estudia sobre una pregunta: ambigua, mal keyada, con errata…"""

    __tablename__ = "question_issue_reports"
    __table_args__ = (
        CheckConstraint(
            "kind IN ('ambiguous', 'wrong_key', 'typo', 'outdated', 'other')", name="ck_issue_kind"
        ),
        CheckConstraint("status IN ('open', 'reviewed', 'dismissed')", name="ck_issue_status"),
        CheckConstraint("length(trim(detail)) > 0", name="ck_issue_detail"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    question_version_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("question_versions.id", ondelete="CASCADE"), nullable=False
    )
    kind: Mapped[str] = mapped_column(String(16), nullable=False)
    detail: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, server_default=text("'open'"), default="open"
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


# ---------------------------------------------------------------------------- S07: estudio


class StudySessionRecord(Base):
    """Una sesión de estudio con su configuración congelada (03_DATA-MODEL §7).

    `answer_key_version_id` es **la clave con la que se corrige**: se fija al iniciar y no cambia
    aunque después se active otra (invariante 7). `result_json` guarda el cálculo agregado tal como
    se hizo, con la composición efectiva que se usó.
    """

    __tablename__ = "study_sessions"
    __table_args__ = (
        CheckConstraint(
            "mode IN ('practice', 'error_review', 'official_exam', 'mock_exam', 'diagnostic')",
            name="ck_session_mode",
        ),
        CheckConstraint(
            "status IN ('draft', 'running', 'finished', 'abandoned')", name="ck_session_status"
        ),
        CheckConstraint("feedback IN ('immediate', 'at_end')", name="ck_session_feedback"),
        CheckConstraint("total_questions >= 0", name="ck_session_total"),
        CheckConstraint(
            "status <> 'running' OR started_at IS NOT NULL", name="ck_session_running_started"
        ),
        CheckConstraint(
            "status <> 'finished' OR finished_at IS NOT NULL", name="ck_session_finished_at"
        ),
        Index("ix_study_sessions_opposition", "opposition_id", "status"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    opposition_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("oppositions.id", ondelete="RESTRICT"), nullable=False
    )
    convocation_version_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("convocation_versions.id", ondelete="RESTRICT"), nullable=True
    )
    question_set_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("question_sets.id", ondelete="RESTRICT"), nullable=True
    )
    answer_key_version_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("answer_key_versions.id", ondelete="RESTRICT"), nullable=True
    )
    mode: Mapped[str] = mapped_column(String(16), nullable=False)
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, server_default=text("'draft'"), default="draft"
    )
    feedback: Mapped[str] = mapped_column(String(16), nullable=False)
    configuration_json: Mapped[str] = mapped_column(Text, nullable=False)
    result_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    #: El resultado que había antes de recalcular con una clave nueva (S08): sirve para explicar el
    #: cambio en lugar de que la puntuación cambie sola.
    previous_result_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    recalculated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    time_limit_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_questions: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0"), default=0
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class SessionQuestionRecord(Base):
    """Una pregunta tal como se presentó, con la clave **congelada** en ese momento.

    Congelar la clave es lo que hace que activar una plantilla nueva no cambie lo que alguien ya
    vio: la reevaluación (S08) es una evaluación nueva, no un cambio de esta foto.
    """

    __tablename__ = "session_questions"
    __table_args__ = (
        CheckConstraint("position > 0", name="ck_session_question_position"),
        CheckConstraint(
            "key_outcome IS NULL OR key_outcome IN "
            "('keyed', 'annulled', 'unanswered', 'conflicting')",
            name="ck_session_question_key_outcome",
        ),
        CheckConstraint(
            "is_reserve = 0 OR reserve_order IS NOT NULL",
            name="ck_session_question_reserve_order",
        ),
        UniqueConstraint("session_id", "position", name="uq_session_question_position"),
        UniqueConstraint("session_id", "question_version_id", name="uq_session_question_version"),
        Index("ix_session_questions_session", "session_id", "position"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("study_sessions.id", ondelete="CASCADE"), nullable=False
    )
    question_version_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("question_versions.id", ondelete="RESTRICT"), nullable=False
    )
    stable_key: Mapped[str] = mapped_column(String(64), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    part_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_reserve: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("0"), default=False
    )
    reserve_order: Mapped[int | None] = mapped_column(Integer, nullable=True)
    key_outcome: Mapped[str | None] = mapped_column(String(16), nullable=True)
    correct_option_keys_json: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("'[]'"), default="[]"
    )


class AttemptRecord(Base):
    """Lo que hizo una persona: su respuesta, su tiempo y su confianza.

    El acierto **no** se guarda aquí: se deduce de la evaluación, y así no hay dos verdades que
    puedan separarse. Un intento por pregunta: el intento se congela al registrarlo.
    """

    __tablename__ = "attempts"
    __table_args__ = (
        CheckConstraint("elapsed_ms >= 0", name="ck_attempt_elapsed"),
        CheckConstraint(
            "confidence IS NULL OR confidence IN ('low', 'medium', 'high')",
            name="ck_attempt_confidence",
        ),
        UniqueConstraint("session_question_id", name="uq_attempt_per_question"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    session_question_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("session_questions.id", ondelete="CASCADE"), nullable=False
    )
    chosen_option_keys_json: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("'[]'"), default="[]"
    )
    elapsed_ms: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0"), default=0
    )
    confidence: Mapped[str | None] = mapped_column(String(16), nullable=True)
    client_sequence: Mapped[int | None] = mapped_column(Integer, nullable=True)
    answered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class AttemptEvaluationRecord(Base):
    """La corrección de un intento con una clave concreta, con su puntuación **exacta**.

    Un tercio no es un decimal: se guarda como numerador y denominador (DEBT-006, ADR-010).
    Recalcular con otra clave añade una evaluación nueva que sustituye a la anterior, en lugar de
    borrar la que había (invariante 7).
    """

    __tablename__ = "attempt_evaluations"
    __table_args__ = (
        CheckConstraint(
            "outcome IN ('correct', 'wrong', 'blank', 'annulled', 'excluded', 'conflicting', "
            "'unused_reserve')",
            name="ck_evaluation_outcome",
        ),
        CheckConstraint("score_denominator > 0", name="ck_evaluation_denominator"),
        UniqueConstraint("attempt_id", "answer_key_version_id", name="uq_evaluation_per_key"),
        Index("ix_evaluations_attempt", "attempt_id", "evaluated_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    attempt_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("attempts.id", ondelete="CASCADE"), nullable=False
    )
    answer_key_version_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("answer_key_versions.id", ondelete="RESTRICT"), nullable=True
    )
    outcome: Mapped[str] = mapped_column(String(16), nullable=False)
    score_numerator: Mapped[int] = mapped_column(Integer, nullable=False)
    score_denominator: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("1"), default=1
    )
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    supersedes_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("attempt_evaluations.id", ondelete="SET NULL"), nullable=True
    )
    evaluated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


# ---------------------------------------------------------------------------- S09: búsqueda y RAG
#
# El índice léxico (`evidence_fts`, FTS5 con contenido externo) **no** se mapea aquí a propósito: es
# una tabla virtual que se consulta con SQL propio, con sus disparadores y su `rebuild`, y
# meterla en el ORM no aportaría nada (no tiene columnas que el dominio use).


class RagQueryRecord(Base):
    """Una consulta de búsqueda o de RAG, con los filtros y la revisión del corpus que usó.

    Guardar la revisión del corpus (`corpus_revision`) es lo que permite decir «esta respuesta
    se dio con este material»: si el corpus cambia, la respuesta no se reutiliza como si fuera
    de hoy.
    """

    __tablename__ = "rag_queries"
    __table_args__ = (
        CheckConstraint("strategy IN ('lexical', 'hybrid')", name="ck_rag_strategy"),
        CheckConstraint(
            "version_mode IN ('current', 'explicit_historical')", name="ck_rag_version_mode"
        ),
        CheckConstraint("length(trim(question)) > 0", name="ck_rag_question"),
        Index("ix_rag_queries_created", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    opposition_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("oppositions.id", ondelete="RESTRICT"), nullable=True
    )
    convocation_version_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("convocation_versions.id", ondelete="RESTRICT"), nullable=True
    )
    question: Mapped[str] = mapped_column(Text, nullable=False)
    filters_json: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'{}'"))
    strategy: Mapped[str] = mapped_column(
        String(16), nullable=False, server_default=text("'lexical'")
    )
    version_mode: Mapped[str] = mapped_column(
        String(24), nullable=False, server_default=text("'current'")
    )
    corpus_revision: Mapped[str] = mapped_column(String(64), nullable=False)
    provider: Mapped[str] = mapped_column(
        String(32), nullable=False, server_default=text("'extractive'")
    )
    model: Mapped[str | None] = mapped_column(Text, nullable=True)
    prompt_template_version: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class RetrievalHitRecord(Base):
    """Un fragmento recuperado en una consulta, con su posición y si llegó a usarse.

    Se guardan **todos** los recuperados, no solo los usados (`05_RAG §5`, paso 9): poder ver lo que
    se descartó es la mitad de auditar una respuesta.
    """

    __tablename__ = "retrieval_hits"
    __table_args__ = (
        CheckConstraint("rank > 0", name="ck_hit_rank"),
        CheckConstraint("strategy IN ('lexical', 'hybrid')", name="ck_hit_strategy"),
        UniqueConstraint("query_id", "span_id", name="uq_hit_span"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    query_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("rag_queries.id", ondelete="CASCADE"), nullable=False
    )
    span_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("evidence_spans.id", ondelete="RESTRICT"), nullable=False
    )
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False, server_default=text("0"))
    strategy: Mapped[str] = mapped_column(
        String(16), nullable=False, server_default=text("'lexical'")
    )
    used: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("0"), default=False
    )


class GeneratedAnswerRecord(Base):
    """La respuesta de una consulta, con su estado y con qué proveedor se compuso."""

    __tablename__ = "generated_answers"
    __table_args__ = (
        CheckConstraint(
            "status IN ('supported', 'partial', 'insufficient')", name="ck_answer_status"
        ),
        UniqueConstraint("query_id", name="uq_answer_per_query"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    query_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("rag_queries.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    short_answer: Mapped[str] = mapped_column(Text, nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    uncertainties_json: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("'[]'")
    )
    suggested_followups_json: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("'[]'")
    )
    provider: Mapped[str] = mapped_column(
        String(32), nullable=False, server_default=text("'extractive'")
    )
    model: Mapped[str | None] = mapped_column(Text, nullable=True)
    prompt_template_version: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class AnswerClaimRecord(Base):
    """Una afirmación de una respuesta: sin evidencia no se guarda (lo comprueba el dominio)."""

    __tablename__ = "answer_claims"
    __table_args__ = (
        CheckConstraint("position > 0", name="ck_claim_position"),
        CheckConstraint("support IN ('direct', 'inferred')", name="ck_claim_support"),
        CheckConstraint("length(trim(text)) > 0", name="ck_claim_text"),
        UniqueConstraint("answer_id", "position", name="uq_claim_position"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    answer_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("generated_answers.id", ondelete="CASCADE"), nullable=False
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    # El nombre de la columna es `text`, así que aquí no se puede llamar a `text()`: el valor por
    # defecto va como cadena literal, que SQLAlchemy acepta igual.
    support: Mapped[str] = mapped_column(String(16), nullable=False, server_default="'direct'")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class AnswerClaimEvidenceRecord(Base):
    """La evidencia de una afirmación: `RESTRICT` para que la cita no se quede sin su texto."""

    __tablename__ = "answer_claim_evidence"

    claim_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("answer_claims.id", ondelete="CASCADE"), primary_key=True
    )
    span_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("evidence_spans.id", ondelete="RESTRICT"), primary_key=True
    )


class LearningErrorRecord(Base):
    """Lo que la persona **declara** de un fallo: su causa, su concepto y su nota.

    No se crea sola. Un fallo sin causa declarada no es un fallo «de conocimiento»: es un fallo del
    que todavía no se sabe por qué. El repaso, en cambio, sí nace solo (`ReviewItemRecord`).
    """

    __tablename__ = "learning_errors"
    __table_args__ = (
        CheckConstraint(
            "cause IN ('knowledge', 'confusion', 'reading', 'time', 'calculation', 'ambiguous', "
            "'other')",
            name="ck_error_cause",
        ),
        CheckConstraint("status IN ('open', 'resolved')", name="ck_error_status"),
        CheckConstraint("occurrences >= 1", name="ck_error_occurrences"),
        CheckConstraint(
            "concept_label IS NULL OR length(trim(concept_label)) > 0", name="ck_error_concept"
        ),
        CheckConstraint(
            "(status = 'resolved' AND resolved_at IS NOT NULL) OR "
            "(status = 'open' AND resolved_at IS NULL)",
            name="ck_error_resolution",
        ),
        Index("ix_learning_errors_attempt", "attempt_id"),
        Index("ix_learning_errors_status", "status", "last_seen_at"),
        Index("ix_learning_errors_node", "curriculum_node_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    attempt_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("attempts.id", ondelete="CASCADE"), nullable=False
    )
    curriculum_node_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("curriculum_nodes.id", ondelete="RESTRICT"), nullable=True
    )
    concept_label: Mapped[str | None] = mapped_column(Text, nullable=True)
    cause: Mapped[str] = mapped_column(String(16), nullable=False)
    user_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, server_default=text("'open'"), default="open"
    )
    occurrences: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("1"), default=1
    )
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ReviewItemRecord(Base):
    """El estado de repaso de una pregunta: cuándo toca, con qué intervalo y cuántos fallos lleva.

    Una fila por pregunta (índice único): dos repasos de lo mismo serían una cola que miente sobre
    lo que queda por hacer.
    """

    __tablename__ = "review_items"
    __table_args__ = (
        CheckConstraint("interval_days >= 0", name="ck_review_interval"),
        CheckConstraint("repetitions >= 0", name="ck_review_repetitions"),
        CheckConstraint("lapses >= 0", name="ck_review_lapses"),
        UniqueConstraint("question_version_id", name="uq_review_per_question"),
        Index("ix_review_items_due", "due_at"),
        Index("ix_review_items_opposition", "opposition_id", "due_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    question_version_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("question_versions.id", ondelete="CASCADE"), nullable=False
    )
    opposition_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("oppositions.id", ondelete="RESTRICT"), nullable=False
    )
    learning_error_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("learning_errors.id", ondelete="SET NULL"), nullable=True
    )
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    interval_days: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0"), default=0
    )
    repetitions: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0"), default=0
    )
    lapses: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0"), default=0
    )
    last_reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ReviewEventRecord(Base):
    """El historial de un repaso: no se sobrescribe, cada cambio de fecha queda con su motivo."""

    __tablename__ = "review_events"
    __table_args__ = (
        CheckConstraint(
            "kind IN ('created', 'attempt', 'reviewed', 'snoozed')",
            name="ck_review_event_kind",
        ),
        CheckConstraint(
            "outcome IS NULL OR outcome IN ('correct', 'wrong')", name="ck_review_event_outcome"
        ),
        CheckConstraint(
            "confidence IS NULL OR confidence IN ('low', 'medium', 'high')",
            name="ck_review_event_confidence",
        ),
        CheckConstraint(
            "cause IS NULL OR cause IN ('knowledge', 'confusion', 'reading', 'time', "
            "'calculation', 'ambiguous', 'other')",
            name="ck_review_event_cause",
        ),
        CheckConstraint(
            "(kind IN ('created', 'attempt', 'reviewed') AND outcome IS NOT NULL) OR "
            "(kind = 'snoozed' AND outcome IS NULL)",
            name="ck_review_event_outcome_required",
        ),
        Index("ix_review_events_item", "review_item_id", "occurred_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    review_item_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("review_items.id", ondelete="CASCADE"), nullable=False
    )
    kind: Mapped[str] = mapped_column(String(16), nullable=False)
    outcome: Mapped[str | None] = mapped_column(String(16), nullable=True)
    confidence: Mapped[str | None] = mapped_column(String(16), nullable=True)
    cause: Mapped[str | None] = mapped_column(String(16), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    previous_due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    previous_interval_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    interval_days: Mapped[int] = mapped_column(Integer, nullable=False)
    repetitions: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class DerivedArtifactRecord(Base):
    """Lo que se generó a partir del material (hoy, resúmenes extractivos) y si sigue valiendo.

    Guarda su generador y su plantilla porque un derivado sin procedencia no se puede reproducir ni
    comparar; y un derivado marcado para revisar **tiene** que decir por qué (lo comprueba un
    `CHECK`).
    """

    __tablename__ = "derived_artifacts"
    __table_args__ = (
        CheckConstraint("kind IN ('summary')", name="ck_artifact_kind"),
        CheckConstraint(
            "review_status IN ('pending', 'reviewed', 'discarded')", name="ck_artifact_review"
        ),
        CheckConstraint("length(trim(title)) > 0", name="ck_artifact_title"),
        CheckConstraint("length(trim(content)) > 0", name="ck_artifact_content"),
        CheckConstraint(
            "needs_review = 0 OR needs_review_reason IS NOT NULL", name="ck_artifact_reason"
        ),
        CheckConstraint(
            "needs_review_at IS NULL OR needs_review = 1", name="ck_artifact_reviewed_at"
        ),
        Index("ix_derived_artifacts_version", "document_version_id"),
        Index("ix_derived_artifacts_pending", "needs_review", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    kind: Mapped[str] = mapped_column(String(24), nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    document_version_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("document_versions.id", ondelete="RESTRICT"), nullable=False
    )
    generator: Mapped[str] = mapped_column(String(48), nullable=False)
    prompt_template_version: Mapped[str | None] = mapped_column(Text, nullable=True)
    model: Mapped[str | None] = mapped_column(Text, nullable=True)
    review_status: Mapped[str] = mapped_column(
        String(16), nullable=False, server_default=text("'pending'"), default="pending"
    )
    needs_review: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("0"), default=False
    )
    needs_review_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    needs_review_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class DependencyEdgeRecord(Base):
    """De qué depende cada cosa, escrita al crearla: permite invalidar solo lo afectado."""

    __tablename__ = "dependency_edges"
    __table_args__ = (
        CheckConstraint(
            "from_type IN ('document_version', 'document_section', 'evidence_span')",
            name="ck_edge_from",
        ),
        CheckConstraint(
            "to_type IN ('derived_artifact', 'question_version', 'rag_answer')", name="ck_edge_to"
        ),
        UniqueConstraint("from_type", "from_id", "to_type", "to_id", name="uq_edge"),
        Index("ix_dependency_edges_from", "from_type", "from_id"),
        Index("ix_dependency_edges_to", "to_type", "to_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    from_type: Mapped[str] = mapped_column(String(24), nullable=False)
    from_id: Mapped[str] = mapped_column(String(36), nullable=False)
    to_type: Mapped[str] = mapped_column(String(24), nullable=False)
    to_id: Mapped[str] = mapped_column(String(36), nullable=False)
    role: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ChangeSetRecord(Base):
    """La propuesta de cambio entre dos versiones: qué se tocó y qué queda por revisar.

    El diff y los derivados afectados se guardan **como se calcularon**: si el material cambia
    después, la propuesta sigue diciendo lo que decía cuando alguien la revisó.
    """

    __tablename__ = "change_sets"
    __table_args__ = (
        CheckConstraint(
            "status IN ('proposed', 'confirmed', 'discarded')", name="ck_change_status"
        ),
        CheckConstraint("previous_version_id <> new_version_id", name="ck_change_versions"),
        CheckConstraint(
            "(status = 'confirmed' AND confirmed_at IS NOT NULL AND discarded_at IS NULL) OR "
            "(status = 'discarded' AND discarded_at IS NOT NULL AND confirmed_at IS NULL) OR "
            "(status = 'proposed' AND confirmed_at IS NULL AND discarded_at IS NULL)",
            name="ck_change_timestamps",
        ),
        Index("ix_change_sets_document", "document_id", "created_at"),
        Index("ix_change_sets_status", "status", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    document_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("logical_documents.id", ondelete="RESTRICT"), nullable=False
    )
    previous_version_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("document_versions.id", ondelete="RESTRICT"), nullable=False
    )
    new_version_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("document_versions.id", ondelete="RESTRICT"), nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, server_default=text("'proposed'"), default="proposed"
    )
    sections_json: Mapped[str] = mapped_column(Text, nullable=False)
    affected_json: Mapped[str] = mapped_column(Text, nullable=False)
    sections_changed: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0"), default=0
    )
    sections_added: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0"), default=0
    )
    sections_removed: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0"), default=0
    )
    sections_unchanged: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0"), default=0
    )
    effect_note: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    discarded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reviewed_by: Mapped[str | None] = mapped_column(String(64), nullable=True)
