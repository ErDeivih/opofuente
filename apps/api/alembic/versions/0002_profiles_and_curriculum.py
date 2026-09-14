"""Oposiciones, convocatorias, programa y reglas de examen.

Revision ID: 0002_profiles_and_curriculum
Revises: 0001_app_metadata
Create Date: 2026-09-14

Crea las tablas de S01 (ver ADR-005). Incluye dos índices únicos **parciales** que son la
restricción real que exige el slice: no puede haber más de una convocatoria activa por
oposición ni más de una oposición activa. La validación no depende del código de la aplicación.

"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0002_profiles_and_curriculum"
down_revision = "0001_app_metadata"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "oppositions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("code", sa.String(length=64), nullable=False, unique=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    # Solo una oposición activa (la que la interfaz muestra como seleccionada).
    op.execute(
        "CREATE UNIQUE INDEX uq_opposition_single_active ON oppositions(active) WHERE active = 1"
    )

    op.create_table(
        "convocation_versions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "opposition_id",
            sa.String(length=36),
            sa.ForeignKey("oppositions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("code", sa.String(length=64), nullable=False, unique=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("official_url", sa.Text(), nullable=False),
        sa.Column("published_at", sa.Date(), nullable=False),
        sa.Column("exam_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("source_reference", sa.Text(), nullable=True),
        sa.Column(
            "supersedes_id",
            sa.String(length=36),
            sa.ForeignKey("convocation_versions.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "status IN ('draft', 'active', 'superseded', 'archived')",
            name="ck_convocation_status",
        ),
    )
    op.create_index(
        "ix_convocation_opposition", "convocation_versions", ["opposition_id"], unique=False
    )
    # Restricción real de S01: una sola convocatoria activa por oposición.
    op.execute(
        "CREATE UNIQUE INDEX uq_convocation_single_active "
        "ON convocation_versions(opposition_id) WHERE status = 'active'"
    )

    op.create_table(
        "curriculum_nodes",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "convocation_version_id",
            sa.String(length=36),
            sa.ForeignKey("convocation_versions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "parent_id",
            sa.String(length=36),
            sa.ForeignKey("curriculum_nodes.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("node_type", sa.String(length=16), nullable=False),
        sa.Column("official_code", sa.String(length=32), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("path", sa.String(length=128), nullable=False),
        sa.Column("depth", sa.Integer(), nullable=False),
        sa.CheckConstraint("node_type IN ('block', 'topic', 'epigraph')", name="ck_node_type"),
        sa.CheckConstraint("depth >= 0", name="ck_node_depth"),
        sa.CheckConstraint("position >= 1", name="ck_node_position"),
        sa.UniqueConstraint("convocation_version_id", "path", name="uq_curriculum_path"),
    )
    op.create_index(
        "ix_curriculum_convocation", "curriculum_nodes", ["convocation_version_id"], unique=False
    )
    op.create_index("ix_curriculum_parent", "curriculum_nodes", ["parent_id"], unique=False)

    op.create_table(
        "exam_parts",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "convocation_version_id",
            sa.String(length=36),
            sa.ForeignKey("convocation_versions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "parent_id",
            sa.String(length=36),
            sa.ForeignKey("exam_parts.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("kind", sa.String(length=16), nullable=False),
        sa.Column("format", sa.String(length=32), nullable=True),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("ordinary_items", sa.Integer(), nullable=True),
        sa.Column("reserve_items", sa.Integer(), nullable=True),
        sa.Column("options_per_question", sa.Integer(), nullable=True),
        sa.Column("score_min", sa.Float(), nullable=True),
        sa.Column("score_max", sa.Float(), nullable=True),
        sa.Column("pass_score", sa.Float(), nullable=True),
        sa.Column("wrong_penalty_fraction", sa.Float(), nullable=True),
        sa.Column("fail_if_errors_gte", sa.Integer(), nullable=True),
        sa.Column("time_minutes", sa.Integer(), nullable=True),
        sa.Column("structure_note", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("evidence_quote", sa.Text(), nullable=False),
        sa.CheckConstraint("kind IN ('group', 'test')", name="ck_part_kind"),
        sa.CheckConstraint(
            "format IS NULL OR format IN ('single_choice', 'multi_mark_error', 'psychotechnical')",
            name="ck_part_format",
        ),
        sa.UniqueConstraint("convocation_version_id", "code", name="uq_exam_part_code"),
    )
    op.create_index("ix_exam_parts_convocation", "exam_parts", ["convocation_version_id"])

    op.create_table(
        "exam_rules",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "convocation_version_id",
            sa.String(length=36),
            sa.ForeignKey("convocation_versions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("kind", sa.String(length=16), nullable=False),
        sa.Column("value_text", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("evidence_quote", sa.Text(), nullable=False),
        sa.CheckConstraint(
            "kind IN ('boolean', 'integer', 'fraction', 'text')", name="ck_rule_kind"
        ),
        sa.UniqueConstraint("convocation_version_id", "code", name="uq_exam_rule_code"),
    )
    op.create_index("ix_exam_rules_convocation", "exam_rules", ["convocation_version_id"])


def downgrade() -> None:
    op.drop_index("ix_exam_rules_convocation", table_name="exam_rules")
    op.drop_table("exam_rules")
    op.drop_index("ix_exam_parts_convocation", table_name="exam_parts")
    op.drop_table("exam_parts")
    op.drop_index("ix_curriculum_parent", table_name="curriculum_nodes")
    op.drop_index("ix_curriculum_convocation", table_name="curriculum_nodes")
    op.drop_table("curriculum_nodes")
    op.drop_index("uq_convocation_single_active", table_name="convocation_versions")
    op.drop_index("ix_convocation_opposition", table_name="convocation_versions")
    op.drop_table("convocation_versions")
    op.drop_index("uq_opposition_single_active", table_name="oppositions")
    op.drop_table("oppositions")
