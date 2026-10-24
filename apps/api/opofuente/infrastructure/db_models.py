"""Modelos de infraestructura.

Aquí viven las tablas de S01: oposiciones, convocatorias, programa y reglas de examen
(ver ADR-005), además del registro de metadatos de la instancia local que permite a
`/health/ready` comprobar que la migración inicial se aplicó de verdad.

Las entidades de dominio equivalentes, sin SQLAlchemy, están en `opofuente.domain.profiles`.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from typing import Any

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
from sqlalchemy.engine import Dialect
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import TypeDecorator

from opofuente.domain.study import OWNER_ID_LOCAL
from opofuente.infrastructure.db import Base

CONVOCATION_STATUSES = ("draft", "active", "superseded", "archived")
NODE_TYPES = ("block", "topic", "epigraph")
PART_KINDS = ("group", "test")
PART_FORMATS = ("single_choice", "multi_mark_error", "psychotechnical")
RULE_KINDS = ("boolean", "integer", "fraction", "text")


class UtcDateTime(TypeDecorator[datetime]):
    """Fecha que se guarda en UTC y se **lee con zona**: lo que la API sirve lleva siempre `+00:00`.

    Por qué existe: SQLite no guarda la zona horaria. Se escribía un `datetime` *aware* y se leía
    *naive*, así que la API servía «2026-10-05T10:43:52.793645» sin zona y el navegador lo
    interpretaba como hora local de Madrid: el cronómetro de una práctica empezaba en `2:00:03` y un
    examen oficial de 120 minutos **nacía con el tiempo agotado** (5 de octubre de 2026).

    Al escribir se normaliza a UTC y se guarda sin zona, para no cambiar el formato de lo que ya
    hay; al leer se le vuelve a poner UTC, que es la zona que la aplicación usa en todas sus fechas
    internas (01_PRODUCT-SPEC §7).
    """

    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, value: datetime | None, dialect: Dialect) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            # Un dato heredado sin zona ya está en UTC: es como se ha guardado siempre.
            return value
        return value.astimezone(UTC).replace(tzinfo=None)

    def process_result_value(self, value: datetime | None, dialect: Dialect) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)

    def process_literal_param(self, value: Any, dialect: Dialect) -> str:
        raise NotImplementedError("UtcDateTime no se usa en literales de SQL")


class AppMetadataRecord(Base):
    __tablename__ = "app_metadata"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)


class OppositionRecord(Base):
    __tablename__ = "oppositions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("0"), default=False
    )
    created_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)

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
    created_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)

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
    first_seen_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)
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
    accessed_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)
    size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    mtime: Mapped[datetime | None] = mapped_column(UtcDateTime(), nullable=True)

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
    created_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(UtcDateTime(), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(UtcDateTime(), nullable=True)
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
    mtime: Mapped[datetime | None] = mapped_column(UtcDateTime(), nullable=True)
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
    created_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)


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
    created_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)
    resolved_at: Mapped[datetime | None] = mapped_column(UtcDateTime(), nullable=True)
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
    lease_expires_at: Mapped[datetime | None] = mapped_column(UtcDateTime(), nullable=True)
    #: Antes de esta fecha el trabajo no se puede reclamar: es la espera entre reintentos. Sin
    #: ella, un `retry_delay_seconds` escrito en el mensaje no aplazaría nada de verdad.
    not_before: Mapped[datetime | None] = mapped_column(UtcDateTime(), nullable=True)
    cancel_requested_at: Mapped[datetime | None] = mapped_column(UtcDateTime(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(UtcDateTime(), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(UtcDateTime(), nullable=True)


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
    created_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)

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
    created_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)
    decided_at: Mapped[datetime | None] = mapped_column(UtcDateTime(), nullable=True)
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
    created_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)
    approved_at: Mapped[datetime | None] = mapped_column(UtcDateTime(), nullable=True)

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
    built_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)
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
    created_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)
    resolved_at: Mapped[datetime | None] = mapped_column(UtcDateTime(), nullable=True)
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
    created_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)


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
    created_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)


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
    created_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)

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
    retrieved_at: Mapped[datetime | None] = mapped_column(UtcDateTime(), nullable=True)
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
    approved_at: Mapped[datetime | None] = mapped_column(UtcDateTime(), nullable=True)
    approved_by: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)

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
    created_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_text: Mapped[str] = mapped_column(Text, nullable=False)


class CollectionRecord(Base):
    """Coleccion personal: agrupa material sin duplicar bytes."""

    __tablename__ = "collections"
    __table_args__ = (CheckConstraint("length(trim(name)) > 0", name="ck_collection_name"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)


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
    added_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)


# ----------------------------------------- S06: preguntas, claves, evidencias y explicaciones


class QuestionSetRecord(Base):
    """Un conjunto de preguntas: examen oficial, banco privado, practica o lote generado.

    El **modelo** (A/B) es del conjunto, no de cada pregunta: un examen modelo A es un conjunto con
    su propia plantilla, y por eso `answer_key_versions` no necesita repetir el modelo.

    `distribution` dice **quién puede ver el conjunto**: `personal` (material del propietario, valor
    por defecto para no cambiar la visibilidad de lo que ya existe) o `public` (publicable, como los
    exámenes oficiales que publica la administración). Es del conjunto y no de la pregunta: un
    cuestionario oficial se publica entero.

    `origin_scope` dice **de qué administración sale** (`0037`): `age` (Administración General del
    Estado), `otra_administracion` (lo que queda fuera de un simulacro) o `desconocida` (el valor
    por defecto: material cuya procedencia no se puede afirmar). También es del conjunto.
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
        CheckConstraint(
            "distribution IN ('personal', 'public')", name="ck_question_set_distribution"
        ),
        CheckConstraint(
            "origin_scope IN ('age', 'otra_administracion', 'desconocida')",
            name="ck_question_set_origin_scope",
        ),
        CheckConstraint(
            "key_reliability IN ('fiable', 'dudosa', 'no_fiable')",
            name="ck_question_set_key_reliability",
        ),
        CheckConstraint(
            "key_checked_count >= 0 AND key_discrepant_count >= 0",
            name="ck_question_set_key_counts",
        ),
        CheckConstraint(
            "key_discrepant_count <= key_checked_count",
            name="ck_question_set_key_discrepant",
        ),
        Index("ix_question_sets_key_reliability", "key_reliability"),
        Index("ix_question_sets_origin_scope", "origin_scope"),
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
    distribution: Mapped[str] = mapped_column(
        String(16), nullable=False, server_default=text("'personal'"), default="personal"
    )
    #: De qué administración sale el material (`0037`, D10). Es del **conjunto** como
    #: `distribution`: un cuestionario oficial se publica entero y su procedencia es la del
    #: documento. `desconocida` por defecto y no `age`: decir «es de la AGE» de un material que
    #: nadie ha comprobado sería afirmar lo que no se sabe, y ese valor sí excluye de un simulacro.
    origin_scope: Mapped[str] = mapped_column(
        String(24), nullable=False, server_default=text("'desconocida'"), default="desconocida"
    )
    #: Si la clave de este conjunto se puede fiar (`0036`, §1 del objetivo). Es del
    #: **conjunto** y no de la pregunta porque la clave se extrajo del material de un conjunto
    #: entero: si la extracción salió desplazada, salió desplazada para todas sus preguntas.
    #: `fiable` por defecto: un conjunto que nadie ha medido no es un conjunto en cuarentena.
    key_reliability: Mapped[str] = mapped_column(
        String(16), nullable=False, server_default=text("'fiable'"), default="fiable"
    )
    #: Preguntas con letra y clave que se compararon al medir, y cuántas de ellas no coincidían. Los
    #: dos números se guardan con el veredicto para que la cifra se pueda auditar sin volver a
    #: medirla.
    key_checked_count: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0"), default=0
    )
    key_discrepant_count: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0"), default=0
    )
    key_measured_at: Mapped[datetime | None] = mapped_column(DateTime(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)


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
    created_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)
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
    approved_at: Mapped[datetime | None] = mapped_column(UtcDateTime(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)


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
    created_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)


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
            "status IN ('draft', 'reviewed', 'rejected', 'archived')",
            name="ck_explanation_status",
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
            # **Una sola explicación viva por versión**: la archivada convive con la que la
            # sustituyó, y por eso queda fuera del único (remate, punto 1).
            sqlite_where=text("option_stable_key IS NULL AND status <> 'archived'"),
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
    created_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    #: La frase LITERAL de los apuntes que sostiene la explicación (§3 de la fase 3).
    citation: Mapped[str | None] = mapped_column(Text, nullable=True)
    #: El apartado de los apuntes al que pertenece esa cita: la explicación se ancla, no se inventa.
    note_anchor_id: Mapped[str | None] = mapped_column(String(36), nullable=True)


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
    created_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)
    reviewed_at: Mapped[datetime | None] = mapped_column(UtcDateTime(), nullable=True)


class QuestionCurriculumExclusionRecord(Base):
    """Una pregunta declarada **fuera del temario** del programa vigente (F4).

    No es un mapeo y no apunta a ningún nodo: es la marca de que esta pregunta no pertenece a ningún
    tema de esta convocatoria, con el motivo de por qué. Así es imposible confundirla con un tema
    —no tiene código oficial ni posición— y las consultas que componen simulacros y exámenes
    oficiales pueden dejarla fuera mirando la pregunta, no un nodo.

    La clave primaria es la pregunta: una pregunta está fuera de temario o no lo está, y decir dos
    veces lo mismo no son dos hechos (la segunda escritura no crea nada y no deja evento).
    """

    __tablename__ = "question_curriculum_exclusions"
    __table_args__ = (
        CheckConstraint(
            "reason IN ('otra_administracion', 'enunciado_roto')",
            name="ck_question_exclusion_reason",
        ),
        CheckConstraint("length(trim(actor)) > 0", name="ck_question_exclusion_actor"),
        Index("ix_question_exclusions_reason", "reason"),
    )

    question_version_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("question_versions.id", ondelete="CASCADE"), primary_key=True
    )
    reason: Mapped[str] = mapped_column(String(32), nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    actor: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)


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
        # El listado de sesiones de una persona se filtra por `owner_id` (F2): sin este índice, la
        # consulta que la zona del alumno hace en cada carga recorre la tabla entera.
        Index("ix_study_sessions_owner", "owner_id", "status"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    #: De quién es esta sesión. `NOT NULL` y con valor por defecto en el servidor: hoy siempre
    #: `'local'`, y el día que haya cuentas el historial ya está repartido (0027).
    owner_id: Mapped[str] = mapped_column(
        String(64), nullable=False, server_default=text("'local'"), default=OWNER_ID_LOCAL
    )
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
    recalculated_at: Mapped[datetime | None] = mapped_column(UtcDateTime(), nullable=True)
    time_limit_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_questions: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0"), default=0
    )
    started_at: Mapped[datetime | None] = mapped_column(UtcDateTime(), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(UtcDateTime(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)


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
    #: El dueño de la sesión, copiado (0027): las consultas de progreso del alumno filtran por aquí
    #: sin atravesar la sesión.
    owner_id: Mapped[str] = mapped_column(
        String(64), nullable=False, server_default=text("'local'"), default=OWNER_ID_LOCAL
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
    owner_id: Mapped[str] = mapped_column(
        String(64), nullable=False, server_default=text("'local'"), default=OWNER_ID_LOCAL
    )
    chosen_option_keys_json: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("'[]'"), default="[]"
    )
    elapsed_ms: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0"), default=0
    )
    confidence: Mapped[str | None] = mapped_column(String(16), nullable=True)
    client_sequence: Mapped[int | None] = mapped_column(Integer, nullable=True)
    answered_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)


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
    owner_id: Mapped[str] = mapped_column(
        String(64), nullable=False, server_default=text("'local'"), default=OWNER_ID_LOCAL
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
    evaluated_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)


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
    created_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)


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
    created_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)


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
    created_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)


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
    owner_id: Mapped[str] = mapped_column(
        String(64), nullable=False, server_default=text("'local'"), default=OWNER_ID_LOCAL
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
    first_seen_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)
    resolved_at: Mapped[datetime | None] = mapped_column(UtcDateTime(), nullable=True)


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
    due_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)
    interval_days: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0"), default=0
    )
    repetitions: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0"), default=0
    )
    lapses: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0"), default=0
    )
    last_reviewed_at: Mapped[datetime | None] = mapped_column(UtcDateTime(), nullable=True)
    last_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)


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
    previous_due_at: Mapped[datetime | None] = mapped_column(UtcDateTime(), nullable=True)
    due_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)
    previous_interval_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    interval_days: Mapped[int] = mapped_column(Integer, nullable=False)
    repetitions: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)


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
    needs_review_at: Mapped[datetime | None] = mapped_column(UtcDateTime(), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(UtcDateTime(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)


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
    created_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)


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
    created_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)
    confirmed_at: Mapped[datetime | None] = mapped_column(UtcDateTime(), nullable=True)
    discarded_at: Mapped[datetime | None] = mapped_column(UtcDateTime(), nullable=True)
    reviewed_by: Mapped[str | None] = mapped_column(String(64), nullable=True)


class TopicFactRecord(Base):
    """Un hecho de los apuntes de un tema, con las preguntas de las que salió (paso B).

    `text_hash` es la huella normalizada del texto y hay un índice único por tema: volver a pasar
    por
    el mismo lote no duplica los hechos, que es lo que hace que una corrida se pueda reanudar.
    """

    __tablename__ = "topic_facts"
    __table_args__ = (
        CheckConstraint("kind IN ('normativo', 'tecnico')", name="ck_topic_fact_kind"),
        CheckConstraint("length(trim(text)) > 0", name="ck_topic_fact_text"),
        CheckConstraint("length(text_hash) = 64", name="ck_topic_fact_hash"),
        UniqueConstraint("curriculum_node_id", "text_hash", name="uq_topic_fact_text"),
        Index("ix_topic_facts_node", "curriculum_node_id"),
        Index("ix_topic_facts_subsection", "curriculum_node_id", "subsection_key"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    curriculum_node_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("curriculum_nodes.id", ondelete="CASCADE"), nullable=False
    )
    epigraph_code: Mapped[str] = mapped_column(Text, nullable=False)
    subsection_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    #: Va **antes** de `text` a propósito: la columna `text` tapa el `text()` de SQLAlchemy dentro
    #: del cuerpo de la clase, y el `server_default` de aquí dejaría de ser una llamada.
    doubtful: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("0"), default=False
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    text_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    kind: Mapped[str] = mapped_column(String(16), nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_group_ids: Mapped[str] = mapped_column(Text, nullable=False)
    source_question_ids: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)


class TopicNoteSectionRecord(Base):
    """Un apartado de los apuntes de un tema: su texto, su anclaje y sus hechos (paso C y D)."""

    __tablename__ = "topic_note_sections"
    __table_args__ = (
        CheckConstraint("status IN ('pending', 'reviewed')", name="ck_note_section_status"),
        CheckConstraint("position >= 1", name="ck_note_section_position"),
        CheckConstraint("length(trim(subsection_key)) > 0", name="ck_note_section_key"),
        CheckConstraint("length(trim(anchor)) > 0", name="ck_note_section_anchor"),
        UniqueConstraint("curriculum_node_id", "subsection_key", name="uq_note_section_key"),
        Index("ix_note_sections_node_position", "curriculum_node_id", "position"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    curriculum_node_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("curriculum_nodes.id", ondelete="CASCADE"), nullable=False
    )
    subsection_key: Mapped[str] = mapped_column(Text, nullable=False)
    epigraph_code: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    anchor: Mapped[str] = mapped_column(Text, nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    body_markdown: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("''"), default=""
    )
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, server_default=text("'pending'"), default="pending"
    )
    needs_review_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    model: Mapped[str | None] = mapped_column(Text, nullable=True)
    prompt_template_version: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)


class QuestionNoteAnchorRecord(Base):
    """El enlace de una pregunta con el párrafo de los apuntes que la contesta (paso E).

    Una fila por pregunta y tema. `quoted_sentence` es la frase que se verificó **contra el texto**
    de
    los apuntes: es lo que permite abrir el párrafo exacto desde la pregunta.

    `text_sha256` es la huella de **ese** texto. Sin ella, volver a ejecutar el tema reutilizaba la
    comprobación aunque el apartado se hubiera reescrito, y la cita guardada dejaba de estar en los
    apuntes: la bandeja del propietario enseñaba frases que ya no existen en el texto. Con la
    huella,
    una comprobación se reutiliza solo si el texto que el modelo leyó es el de hoy.
    """

    __tablename__ = "question_note_anchors"
    __table_args__ = (
        CheckConstraint(
            "key_status IN ('active', 'draft', 'ninguna')", name="ck_anchor_key_status"
        ),
        CheckConstraint(
            "result IN ('covered', 'gap', 'doubtful', 'conflict')", name="ck_anchor_result"
        ),
        CheckConstraint("attempts >= 1", name="ck_anchor_attempts"),
        UniqueConstraint(
            "question_version_id", "curriculum_node_id", name="uq_anchor_question_node"
        ),
        Index("ix_anchors_node_result", "curriculum_node_id", "result"),
        Index("ix_anchors_section", "section_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    question_version_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("question_versions.id", ondelete="CASCADE"), nullable=False
    )
    curriculum_node_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("curriculum_nodes.id", ondelete="CASCADE"), nullable=False
    )
    section_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("topic_note_sections.id", ondelete="CASCADE"),
        nullable=True,
    )
    anchor: Mapped[str] = mapped_column(Text, nullable=False)
    group_signature: Mapped[str] = mapped_column(String(64), nullable=False)
    quoted_sentence: Mapped[str | None] = mapped_column(Text, nullable=True)
    answer_letter: Mapped[str | None] = mapped_column(String(4), nullable=True)
    expected_letters: Mapped[str | None] = mapped_column(Text, nullable=True)
    key_status: Mapped[str] = mapped_column(String(16), nullable=False)
    result: Mapped[str] = mapped_column(String(16), nullable=False)
    note: Mapped[str | None] = mapped_column(String(48), nullable=True)
    attempts: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("1"), default=1
    )
    #: La huella del texto contra el que se verificó la cita. Nula en las filas escritas antes de
    #: que existiera: esas se vuelven a comprobar, que es lo correcto con una comprobación de la que
    #: no se sabe a qué texto corresponde.
    text_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    checked_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)


class NotesIncidentRecord(Base):
    """Una pregunta que los apuntes no cubren, en la bandeja del propietario (§2.1.4).

    La bandeja es lo que queda **después** de intentar rellenar el hueco: las dudosas y los
    conflictos de letra, cada uno con su categoría (a quién le toca arreglarlo), su motivo y la
    frase verificada que lo prueba cuando la hay.

    Una fila por pregunta y tema (`uq_notes_incident_question_node`): volver a comprobar el tema
    actualiza la incidencia en vez de añadir otra copia, que es lo que hace que la bandeja se pueda
    vaciar de verdad.

    `status` es lo que la convierte en una bandeja que **se despacha** (migración `0035`): el motor
    deja la incidencia `open` y el propietario la pone «en curso» mientras la mira y la cierra con
    `reviewed` (ha hecho lo que su categoría pide) o con `dismissed` (ha decidido que el motor se
    equivoca, que también pasa). `resolution_note` es lo que escribe de lo que ha hecho —una línea,
    opcional— y `reviewed_at` solo tiene fecha mientras esté cerrada. Ninguna de las tres la toca el
    motor: su `save_incidents` actualiza la categoría, el motivo y la frase, y **no** pisa la
    decisión de nadie.
    """

    __tablename__ = "notes_incidents"
    __table_args__ = (
        CheckConstraint(
            "category IN ('hueco_sin_material', 'clave_sospechosa', 'pregunta_ambigua', "
            "'norma_cambiada', 'pregunta_mal_importada', 'clave_no_fiable')",
            name="ck_notes_incident_category",
        ),
        CheckConstraint("coverage IN ('doubtful', 'conflict')", name="ck_notes_incident_coverage"),
        CheckConstraint("length(trim(detail)) > 0", name="ck_notes_incident_detail"),
        CheckConstraint("attempts >= 1", name="ck_notes_incident_attempts"),
        CheckConstraint(
            "status IN ('open', 'in_progress', 'reviewed', 'dismissed', 'propuesta_lista', "
            "'no_son_preguntas')",
            name="ck_notes_incident_status",
        ),
        CheckConstraint(
            "resolution_note IS NULL OR length(trim(resolution_note)) > 0",
            name="ck_notes_incident_note",
        ),
        UniqueConstraint(
            "question_version_id", "curriculum_node_id", name="uq_notes_incident_question_node"
        ),
        Index("ix_notes_incidents_node_category", "curriculum_node_id", "category"),
        Index("ix_notes_incidents_status_category", "status", "category"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    curriculum_node_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("curriculum_nodes.id", ondelete="CASCADE"), nullable=False
    )
    question_version_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("question_versions.id", ondelete="CASCADE"), nullable=False
    )
    group_signature: Mapped[str] = mapped_column(String(64), nullable=False)
    category: Mapped[str] = mapped_column(String(24), nullable=False)
    coverage: Mapped[str] = mapped_column(String(16), nullable=False)
    reason: Mapped[str] = mapped_column(String(48), nullable=False)
    section_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    anchor: Mapped[str | None] = mapped_column(Text, nullable=True)
    phrase: Mapped[str | None] = mapped_column(Text, nullable=True)
    detail: Mapped[str] = mapped_column(Text, nullable=False)
    attempts: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("1"), default=1
    )
    created_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)
    #: Desde la migración `0035`: en qué punto está la incidencia para el propietario.
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, server_default=text("'open'"), default="open"
    )
    #: Lo que escribió de lo que ha hecho, en una línea. Nula mientras no haya escrito nada.
    resolution_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    #: Cuándo la cerró. Nula mientras esté abierta o en curso: lo decide el dominio, no la pantalla.
    reviewed_at: Mapped[datetime | None] = mapped_column(UtcDateTime(), nullable=True)


class NotesReportRecord(Base):
    """Un aviso del alumno sobre un apartado de los apuntes («esto está mal», decisión D2).

    No es una comprobación del motor —eso es `notes_incidents`—: es una persona leyendo que dice
    «aquí hay un error» y escribe el motivo en una línea. Por eso no tiene categoría ni frase
    verificada: tiene el texto de quien lo reporta, la dirección del párrafo (`section_key` y
    `anchor`) y el estado con el que el propietario lo despachará.

    `status` cambia cuando el propietario lo despacha desde el panel: `in_progress` mientras lo
    tiene en la mano, `reviewed` cuando lo ha arreglado y `dismissed` cuando decide que no era un
    error (migración `0034`). Hasta entonces el aviso está `open`. `resolution_note` es lo que el
    propietario escribe de lo que ha hecho: opcional, en una línea, y nula mientras no haya escrito
    nada. No hay índice único: dos avisos sobre el mismo apartado son dos avisos, y borrarlos porque
    se parecen sería perder lo que dijo el segundo.
    """

    __tablename__ = "notes_reports"
    __table_args__ = (
        CheckConstraint(
            "status IN ('open', 'in_progress', 'reviewed', 'dismissed')",
            name="ck_note_report_status",
        ),
        CheckConstraint(
            "resolution_note IS NULL OR length(trim(resolution_note)) > 0",
            name="ck_note_report_note",
        ),
        CheckConstraint("length(trim(reason)) > 0", name="ck_note_report_reason"),
        CheckConstraint("length(trim(section_key)) > 0", name="ck_note_report_section"),
        CheckConstraint("length(trim(anchor)) > 0", name="ck_note_report_anchor"),
        Index("ix_notes_reports_status_created", "status", "created_at"),
        Index("ix_notes_reports_node_status", "curriculum_node_id", "status"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    curriculum_node_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("curriculum_nodes.id", ondelete="CASCADE"), nullable=False
    )
    #: Quién estudia y lo reporta. Hoy es `local`; está puesto para que el aviso no sea anónimo el
    #: día que haya cuentas, y para poder filtrar por persona sin migrar la tabla.
    owner_id: Mapped[str] = mapped_column(String(64), nullable=False)
    section_key: Mapped[str] = mapped_column(Text, nullable=False)
    anchor: Mapped[str] = mapped_column(Text, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, server_default=text("'open'"), default="open"
    )
    created_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)
    reviewed_at: Mapped[datetime | None] = mapped_column(UtcDateTime(), nullable=True)
    #: Qué se ha hecho con el aviso, en una línea, escrito por el propietario al despacharlo.
    resolution_note: Mapped[str | None] = mapped_column(Text, nullable=True)


class TopicNotesReviewRecord(Base):
    """La decisión del propietario sobre los apuntes de un tema (F24, §4.3 del objetivo).

    La pieza que faltaba para que la revisión de apuntes **se pueda hacer desde el panel**: hasta la
    migración `0038` un tema en borrador no se distinguía de un tema que nadie había mirado, porque
    el estado se deducía del par (¿hay apartados escritos?, ¿hay versión archivada?) y no había
    ninguna fila donde quedara escrita la decisión.

    Una fila por tema (`uq_topic_notes_review_node`): la segunda revisión **actualiza** la primera,
    y con ella viaja siempre el mismo evento de auditoría con su antes y su después. Las cifras del
    motivo **no** se copian aquí: se leen de donde ya están —las comprobaciones del motor, la
    bandeja de incidencias y el texto—, porque una copia dentro de la fila acabaría diciendo algo
    distinto de lo que dice el tema.

    `rejected` exige nota (`ck_topic_notes_review_note`): un rechazo sin motivo deja el borrador
    donde estaba y sin saber por qué. Aprobar **no** publica por sí solo: publicar es archivar la
    versión, y eso sigue pasando por las dos puertas del §2.3.
    """

    __tablename__ = "topic_notes_reviews"
    __table_args__ = (
        CheckConstraint(
            "decision IN ('approved', 'rejected')", name="ck_topic_notes_review_decision"
        ),
        CheckConstraint(
            "decision <> 'rejected' OR (note IS NOT NULL AND length(trim(note)) > 0)",
            name="ck_topic_notes_review_note",
        ),
        UniqueConstraint("curriculum_node_id", name="uq_topic_notes_review_node"),
        Index("ix_topic_notes_reviews_decision", "decision"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    curriculum_node_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("curriculum_nodes.id", ondelete="CASCADE"), nullable=False
    )
    decision: Mapped[str] = mapped_column(String(16), nullable=False)
    #: La nota de lo decidido, en una línea. Opcional al aprobar y **obligatoria** al rechazar.
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    #: Quién lo revisó. Hoy la persona local; está puesto para que la decisión no sea anónima el día
    #: que haya cuentas.
    actor: Mapped[str] = mapped_column(String(120), nullable=False)
    reviewed_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)


class DerivedKeyRecord(Base):
    """La clave **derivada** de una pregunta (migración `0039`, §1 del encargo).

    Nace de dos fuentes **independientes** que dicen la misma letra: la de los apuntes, con la cita
    verificada, y la que el modelo contesta a la pregunta **sola** (enunciado y opciones, sin
    apuntes). La clave extraída del material **no** participa en la decisión, que es lo que hace que
    la letra derivada se pueda fiar aunque la del conjunto esté mal.

    Es de la **pregunta**, no del conjunto: la clave extraída se estropea para un conjunto entero
    —por eso el §1 puso la fiabilidad en `question_sets`—, pero lo que se deriva es letra a letra.

    **`key_state` vale `derived` y solo `derived`**, y lo impone un `CHECK`: guardar una clave
    derivada como `active` es imposible en la base, no una regla de estilo. La clave del conjunto no
    se toca, no se copia y no se sustituye.
    """

    __tablename__ = "question_derived_keys"
    __table_args__ = (
        CheckConstraint("key_state IN ('derived')", name="ck_derived_key_state"),
        CheckConstraint(
            "length(trim(notes_letter)) > 0 AND length(trim(model_letter)) > 0 "
            "AND lower(trim(notes_letter)) = lower(trim(model_letter))",
            name="ck_derived_key_fuentes",
        ),
        CheckConstraint("correct_option_keys_json <> '[]'", name="ck_derived_key_has_key"),
        Index("ix_derived_keys_set", "question_set_id"),
    )

    question_version_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("question_versions.id", ondelete="CASCADE", name="fk_derived_key_question"),
        primary_key=True,
    )
    question_set_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("question_sets.id", ondelete="CASCADE"), nullable=False
    )
    correct_option_keys_json: Mapped[str] = mapped_column(Text, nullable=False)
    key_state: Mapped[str] = mapped_column(
        String(16), nullable=False, server_default=text("'derived'"), default="derived"
    )
    #: La letra que dan los apuntes y la **cita verificada** que la sostiene: la primera fuente.
    notes_letter: Mapped[str] = mapped_column(String(4), nullable=False)
    notes_quote: Mapped[str] = mapped_column(Text, nullable=False)
    notes_anchor_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("question_note_anchors.id", ondelete="CASCADE"),
        nullable=False,
    )
    #: Contra qué clave comprobó el motor de apuntes esa letra (`active` · `draft` · `ninguna`). No
    #: decide la derivación —la letra vale por su cita— pero viaja con la evidencia: de ahí sale
    #: que la letra corrobore o contradiga la clave del conjunto.
    notes_key_status: Mapped[str] = mapped_column(String(16), nullable=False)
    #: La segunda fuente: la letra que contestó el modelo a la pregunta sola, y con qué motor.
    model_letter: Mapped[str] = mapped_column(String(4), nullable=False)
    model_name: Mapped[str] = mapped_column(String(64), nullable=False)
    model_version: Mapped[str] = mapped_column(String(64), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(64), nullable=False)
    actor: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)


class KeyGapRecord(Base):
    """Por qué una pregunta de un conjunto en cuarentena **sigue fuera** (migración `0039`).

    Tres motivos y ninguno más (`sin_material` · `sin_cita` · `sin_coincidencia`), que son los del
    informe del encargo. Es el dato que el §2 necesita para agrupar la bandeja **por conjunto**
    que hace verdad «las que no tengan clave fiable siguen fuera de ese conjunto»: una pregunta con
    motivo escrito no vuelve a los tests aunque su conjunto vuelva.

    Se escribe **solo** para preguntas de conjuntos que la corrida ha procesado (los que están en
    cuarentena), así que ningún conjunto sano cambia de comportamiento por tener esta tabla.
    """

    __tablename__ = "question_key_gaps"
    __table_args__ = (
        CheckConstraint(
            "reason IN ('sin_material', 'sin_cita', 'sin_coincidencia')",
            name="ck_key_gap_reason",
        ),
        Index("ix_key_gaps_set", "question_set_id"),
    )

    question_version_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("question_versions.id", ondelete="CASCADE", name="fk_key_gap_question"),
        primary_key=True,
    )
    question_set_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("question_sets.id", ondelete="CASCADE"), nullable=False
    )
    reason: Mapped[str] = mapped_column(String(24), nullable=False)
    actor: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)


# --------------------------------------------------------------------------- S28: cuentas (§8)


class AccountRecord(Base):
    """Una cuenta: una dirección de correo y el resumen de su contraseña (S28, §8 del objetivo).

    **Lo que no guarda es tan importante como lo que guarda.** No hay ninguna columna para la
    contraseña en claro, ni para la dirección de red desde la que se entra, ni para el navegador. La
    contraseña vive como resumen argon2id (`password_hash`) y el algoritmo se declara en
    `password_algo`, para que el día que se cambie de derivador las contraseñas viejas se puedan
    seguir comprobando y volver a escribir con el nuevo.

    `email_normalized` es la que decide si dos cuentas son la misma —minúsculas y sin acentos— y es
    única; `email` conserva lo que se escribió, para poder enseñarlo tal cual en «mi cuenta».
    """

    __tablename__ = "accounts"
    __table_args__ = (
        CheckConstraint("length(trim(email)) > 0", name="ck_account_email"),
        CheckConstraint("length(trim(email_normalized)) > 0", name="ck_account_email_normalized"),
        CheckConstraint("length(trim(password_hash)) > 0", name="ck_account_password_hash"),
        CheckConstraint("password_algo IN ('argon2id')", name="ck_account_password_algo"),
        UniqueConstraint("email_normalized", name="uq_account_email_normalized"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    #: La dirección tal y como la escribió su dueño, sin espacios alrededor.
    email: Mapped[str] = mapped_column(Text, nullable=False)
    #: La dirección en su forma canónica: es la que identifica la cuenta.
    email_normalized: Mapped[str] = mapped_column(Text, nullable=False)
    #: El resumen de la contraseña. Nunca sale de esta tabla hacia ninguna respuesta.
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    password_algo: Mapped[str] = mapped_column(
        String(16), nullable=False, server_default=text("'argon2id'"), default="argon2id"
    )
    #: El `owner_id` con el que se firma su progreso (`acct:<id>`). Se copia aquí y no se deduce en
    #: cada consulta para que cambiar la forma del dueño sea una migración y no una aritmética
    #: repartida por el código.
    owner_id: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)
    #: Cuándo se cambió la contraseña por última vez. Sirve para poder decir «tu contraseña es de
    #: hace un año» sin guardar el historial de contraseñas, que es justo lo que no hay que guardar.
    password_changed_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)


class AccountSessionRecord(Base):
    """Una sesión abierta: el **resumen** de su testigo y sus fechas (S28).

    El testigo que viaja al navegador no está aquí: se guarda su SHA-256. Quien lea la base no puede
    suplantar a nadie con lo que hay dentro. `owner_id` se copia para que el progreso de la sesión y
    el de la cuenta no puedan discrepar.
    """

    __tablename__ = "account_sessions"
    __table_args__ = (
        UniqueConstraint("token_hash", name="uq_account_session_token"),
        CheckConstraint("expires_at > created_at", name="ck_account_session_expiry"),
        Index("ix_account_sessions_account", "account_id", "expires_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    account_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False
    )
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    owner_id: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)
    #: Cuando se cierra sesión, la fila se marca en vez de borrarse: así un testigo robado que se
    #: intente usar después de cerrar sesión se distingue de un testigo que nunca existió.
    revoked_at: Mapped[datetime | None] = mapped_column(UtcDateTime(), nullable=True)


class PasswordResetRecord(Base):
    """Un enlace de recuperación: el resumen de su testigo y cuándo caduca (S28).

    Los enlaces se piden sin decir si la dirección tiene cuenta y se consumen una sola vez
    (`used_at`). El que no se usa caduca en una hora.
    """

    __tablename__ = "password_resets"
    __table_args__ = (
        UniqueConstraint("token_hash", name="uq_password_reset_token"),
        CheckConstraint("expires_at > created_at", name="ck_password_reset_expiry"),
        Index("ix_password_resets_account", "account_id", "expires_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    account_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False
    )
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(UtcDateTime(), nullable=True)


class LoginThrottleRecord(Base):
    """El freno de los intentos fallidos, por cuenta (S28).

    La fila se identifica por el **resumen** de la dirección normalizada, no por la dirección: el
    freno tiene que poder contar sin construir un registro de quién lo intenta. No guarda qué
    contraseña se probó, ni desde dónde, ni en qué orden.

    Se borra en cuanto se acierta (`register_success`): quien se equivoca una vez y luego entra bien
    no arrastra nada. Lo que quede sin resolverse —una cuenta que nadie vuelve a tocar— se limpia
    con `purge_stale`, que el servicio llama antes de contar un fallo.
    """

    __tablename__ = "login_throttles"
    __table_args__ = (
        CheckConstraint("failures >= 0", name="ck_login_throttle_failures"),
        CheckConstraint(
            "locked_until IS NULL OR locked_until > window_started_at",
            name="ck_login_throttle_lock",
        ),
    )

    key_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    failures: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0"), default=0
    )
    window_started_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)
    locked_until: Mapped[datetime | None] = mapped_column(UtcDateTime(), nullable=True)


class ConsentRecordRecord(Base):
    """Una decisión sobre las cookies, **sin sujeto** (S28, §9 del objetivo).

    No hay ninguna columna para saber quién la tomó: no hay cuenta, no hay sesión, no hay dirección
    de red. Es lo que permite poder demostrar que se preguntó y que hubo respuestas sin construir un
    fichero de quién aceptó qué. La decisión que **sí** hay que recordar por persona vive en su
    navegador, en una cookie, y no sube aquí.
    """

    __tablename__ = "consent_records"
    __table_args__ = (
        CheckConstraint("policy_version >= 1", name="ck_consent_policy_version"),
        CheckConstraint("analytics IN (0, 1)", name="ck_consent_analytics"),
        CheckConstraint("preferences IN (0, 1)", name="ck_consent_preferences"),
        Index("ix_consent_records_decided", "decided_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    decided_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)
    policy_version: Mapped[int] = mapped_column(Integer, nullable=False)
    analytics: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("0"), default=False
    )
    preferences: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("0"), default=False
    )


class AnalyticsEventRecord(Base):
    """Un contador de uso: día, tipo y etiqueta de una lista cerrada (S28, §10 del objetivo).

    **Este esquema no puede guardar datos personales.** No hay columna para la cuenta, para la
    sesión, para la dirección de red, para el navegador ni para ningún texto libre: lo único que se
    escribe son dos columnas con un vocabulario cerrado (`analytics.py`) y el día. Un contador sin
    sujeto no es un dato personal, y por eso no hay nada que anonimizar.
    """

    __tablename__ = "analytics_events"
    __table_args__ = (
        CheckConstraint("name IN ('page_view', 'action')", name="ck_analytics_name"),
        CheckConstraint("length(trim(label)) > 0", name="ck_analytics_label"),
        CheckConstraint("length(occurred_on) = 10", name="ck_analytics_day"),
        Index("ix_analytics_events_day_label", "occurred_on", "name", "label"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    #: El día, en `AAAA-MM-DD`. Se guarda el día y no la hora a propósito: la hora exacta de una
    #: visita, repetida, empieza a parecerse a un identificador.
    occurred_on: Mapped[str] = mapped_column(String(10), nullable=False)
    name: Mapped[str] = mapped_column(String(16), nullable=False)
    label: Mapped[str] = mapped_column(String(48), nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)


class CardRecord(Base):
    """Una tarjeta de repaso con su estado de SM-2 (M3).

    **La tarjeta y su estado en la misma fila**: una tarjeta sin él no existe, y la cola del día se
    pregunta en cada pantalla —un `join` por vuelta no se paga—.

    **`origin` distingue la plantilla del modelo.** Las dos son del alumno, pero **la cifra del
    0,1 % de la via sin modelo solo se sostiene si se separan**.
    """

    __tablename__ = "cards"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    #: El hecho de los apuntes del que sale. **Sin él no se puede adelantar al fallar.**
    topic_fact_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    front: Mapped[str] = mapped_column(Text, nullable=False)
    back: Mapped[str] = mapped_column(Text, nullable=False)
    #: **La cita**: sin ella la tarjeta no se puede comprobar.
    citation: Mapped[str | None] = mapped_column(Text, nullable=True)
    origin: Mapped[str] = mapped_column(String(16), nullable=False, default="structural")
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="active")
    ease: Mapped[float] = mapped_column(Float, nullable=False, default=2.5)
    interval_days: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    repetitions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class StudyPlanRecord(Base):
    """El plan de estudio: el examen, las horas y los descansos (M4).

    **Guarda lo que decide el alumno, no el reparto**: el reparto se
    calcula con `domain/study_plan.py` cada vez, porque guardarlo seria
    guardar una derivacion que miente en cuanto cambie un tema.
    """

    __tablename__ = "study_plans"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    #: El dia del examen: sin esto no hay plan.
    exam_date: Mapped[date] = mapped_column(Date, nullable=False)
    hours_per_week: Mapped[int] = mapped_column(Integer, nullable=False)
    #: Los dias de descanso, como `"6"` o `"0,6"`: cero es lunes.
    rest_days: Mapped[str] = mapped_column(String(16), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class PracticalCaseRecord(Base):
    """Un supuesto practico y su enunciado (M5).

    **El enunciado es lo que se lee antes de las preguntas**: sin el no hay
    supuesto, solo veinte preguntas sueltas. **`origin` dice si es oficial o
    generado**, y el hito exige que el simulacro prefiera uno oficial.
    """

    __tablename__ = "practical_cases"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    #: El bloque del examen: III o IV.
    block: Mapped[str] = mapped_column(String(4), nullable=False)
    statement: Mapped[str] = mapped_column(Text, nullable=False)
    #: `official` (del INAP) o `generated` (del modelo).
    origin: Mapped[str] = mapped_column(String(16), nullable=False)
    source_document: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class PracticalCaseQuestionRecord(Base):
    """Una pregunta dentro de un supuesto, **con su orden**.

    Un supuesto es una serie —«con los datos del caso, conteste»—, y las
    preguntas se numeran del 1 al 25: guardarlas sin orden las baraja.
    """

    __tablename__ = "practical_case_questions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    practical_case_id: Mapped[str] = mapped_column(String(36), nullable=False)
    question_version_id: Mapped[str] = mapped_column(String(36), nullable=False)
    #: Del 1 al 25, sin huecos.
    position: Mapped[int] = mapped_column(Integer, nullable=False)


class AccountInvitationRecord(Base):
    """Una invitacion de un solo uso (M8).

    **El token no se guarda**: se guarda su hash, **igual que una contrasena**.
    **Quien lea esta tabla no puede invitar a nadie**, **y por eso el enlace se
    enseña una sola vez y no se puede recuperar**.

    **`used_at` se escribe al canjear en vez de borrar la fila**: **una
    invitacion usada hay que poder explicarla**.
    """

    __tablename__ = "account_invitations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    #: El sha256 del token. **El token en claro no esta en ningun sitio.**
    token_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    email: Mapped[str] = mapped_column(Text, nullable=False)
    email_normalized: Mapped[str] = mapped_column(Text, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)
    #: Nulo mientras no se haya canjeado.
    used_at: Mapped[datetime | None] = mapped_column(UtcDateTime(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)
