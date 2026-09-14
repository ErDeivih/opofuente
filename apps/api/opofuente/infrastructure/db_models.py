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
