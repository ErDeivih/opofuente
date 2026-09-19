"""Cambios, dependencias y derivados (S11).

Revision ID: 0020_changes_and_derivatives
Revises: 0019_errors_and_reviews
Create Date: 2026-09-18

Tres tablas, y cada una contesta una pregunta distinta de «¿qué pasa cuando cambia una fuente?»:

1. **`derived_artifacts`**: qué se generó a partir del material (hoy, resúmenes extractivos) y si
   sigue valiendo. Guarda su generador y su versión de plantilla, porque un derivado sin procedencia
   no se puede volver a producir ni comparar;
2. **`dependency_edges`**: de qué depende cada cosa, **escrito al crearla**. `03_DATA-MODEL` §8 lo
   dice expresamente («las aristas se crean durante generación/importación, no se infieren
   después»), y es lo que permite invalidar solo lo afectado en lugar de todo;
3. **`change_sets`**: la propuesta de cambio entre dos versiones, con su diff por sección, los
   derivados afectados y su estado. Nada se aplica hasta que una persona la confirma, y lo que la
   aplicación **no** dice (el efecto jurídico) también se guarda con ella.

Sobre los borrados: las aristas y los conjuntos de cambios cuelgan de un documento o una versión con
`RESTRICT`, por la misma razón que en ADR-007: si se borrara la versión, el cambio dejaría de poder
explicarse. Un derivado se puede descartar (`review_status`) pero no se borra: lo que se generó a
partir de una fuente que después cambió es justamente lo que hay que poder mirar.
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0020_changes_and_derivatives"
down_revision = "0019_errors_and_reviews"
branch_labels = None
depends_on = None

_TIPOS_ARTEFACTO = ("summary",)
_ESTADOS_REVISION = ("pending", "reviewed", "discarded")
_ORIGENES = ("document_version", "document_section", "evidence_span")
_DESTINOS = ("derived_artifact", "question_version", "rag_answer")
_ESTADOS_CAMBIO = ("proposed", "confirmed", "discarded")


def _lista(valores: tuple[str, ...]) -> str:
    return ", ".join(repr(valor) for valor in valores)


def upgrade() -> None:
    op.create_table(
        "derived_artifacts",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("kind", sa.String(length=24), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "document_version_id",
            sa.String(length=36),
            sa.ForeignKey("document_versions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        #: Procedencia del derivado: qué lo generó y con qué versión de plantilla. Sin esto no se
        #: puede reproducir ni comparar con el siguiente.
        sa.Column("generator", sa.String(length=48), nullable=False),
        sa.Column("prompt_template_version", sa.Text(), nullable=True),
        sa.Column("model", sa.Text(), nullable=True),
        sa.Column("review_status", sa.String(length=16), nullable=False, server_default="pending"),
        sa.Column("needs_review", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("needs_review_reason", sa.Text(), nullable=True),
        sa.Column("needs_review_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(f"kind IN ({_lista(_TIPOS_ARTEFACTO)})", name="ck_artifact_kind"),
        sa.CheckConstraint(
            f"review_status IN ({_lista(_ESTADOS_REVISION)})", name="ck_artifact_review"
        ),
        sa.CheckConstraint("length(trim(title)) > 0", name="ck_artifact_title"),
        sa.CheckConstraint("length(trim(content)) > 0", name="ck_artifact_content"),
        #: Marcar para revisar y decir por qué son la misma cosa: sin motivo, la marca no explica
        #: nada.
        sa.CheckConstraint(
            "needs_review = 0 OR needs_review_reason IS NOT NULL", name="ck_artifact_reason"
        ),
        sa.CheckConstraint(
            "needs_review_at IS NULL OR needs_review = 1", name="ck_artifact_reviewed_at"
        ),
    )
    op.create_index("ix_derived_artifacts_version", "derived_artifacts", ["document_version_id"])
    op.create_index(
        "ix_derived_artifacts_pending", "derived_artifacts", ["needs_review", "created_at"]
    )

    op.create_table(
        "dependency_edges",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("from_type", sa.String(length=24), nullable=False),
        sa.Column("from_id", sa.String(length=36), nullable=False),
        sa.Column("to_type", sa.String(length=24), nullable=False),
        sa.Column("to_id", sa.String(length=36), nullable=False),
        #: Para qué se usa la fuente (por ejemplo, el papel de la cita en la pregunta). Informativo.
        sa.Column("role", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(f"from_type IN ({_lista(_ORIGENES)})", name="ck_edge_from"),
        sa.CheckConstraint(f"to_type IN ({_lista(_DESTINOS)})", name="ck_edge_to"),
        #: Una arista repetida no aporta nada y sí infla el recorrido de dependencias.
        sa.UniqueConstraint("from_type", "from_id", "to_type", "to_id", name="uq_edge"),
    )
    op.create_index("ix_dependency_edges_from", "dependency_edges", ["from_type", "from_id"])
    op.create_index("ix_dependency_edges_to", "dependency_edges", ["to_type", "to_id"])

    op.create_table(
        "change_sets",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "document_id",
            sa.String(length=36),
            sa.ForeignKey("logical_documents.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "previous_version_id",
            sa.String(length=36),
            sa.ForeignKey("document_versions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "new_version_id",
            sa.String(length=36),
            sa.ForeignKey("document_versions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="proposed"),
        #: El diff y los derivados afectados, tal como se calcularon al proponerlo: si el material
        #: cambia después, la propuesta sigue diciendo lo que decía cuando se revisó.
        sa.Column("sections_json", sa.Text(), nullable=False),
        sa.Column("affected_json", sa.Text(), nullable=False),
        sa.Column("sections_changed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("sections_added", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("sections_removed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("sections_unchanged", sa.Integer(), nullable=False, server_default="0"),
        #: Lo que la aplicación **no** interpreta (el efecto jurídico). Viaja con el cambio.
        sa.Column("effect_note", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("discarded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reviewed_by", sa.String(length=64), nullable=True),
        sa.CheckConstraint(f"status IN ({_lista(_ESTADOS_CAMBIO)})", name="ck_change_status"),
        sa.CheckConstraint("previous_version_id <> new_version_id", name="ck_change_versions"),
        sa.CheckConstraint(
            "(status = 'confirmed' AND confirmed_at IS NOT NULL AND discarded_at IS NULL) OR "
            "(status = 'discarded' AND discarded_at IS NOT NULL AND confirmed_at IS NULL) OR "
            "(status = 'proposed' AND confirmed_at IS NULL AND discarded_at IS NULL)",
            name="ck_change_timestamps",
        ),
    )
    op.create_index("ix_change_sets_document", "change_sets", ["document_id", "created_at"])
    op.create_index("ix_change_sets_status", "change_sets", ["status", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_change_sets_status", table_name="change_sets")
    op.drop_index("ix_change_sets_document", table_name="change_sets")
    op.drop_table("change_sets")
    op.drop_index("ix_dependency_edges_to", table_name="dependency_edges")
    op.drop_index("ix_dependency_edges_from", table_name="dependency_edges")
    op.drop_table("dependency_edges")
    op.drop_index("ix_derived_artifacts_pending", table_name="derived_artifacts")
    op.drop_index("ix_derived_artifacts_version", table_name="derived_artifacts")
    op.drop_table("derived_artifacts")
