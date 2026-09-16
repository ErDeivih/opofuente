"""Propuestas de clasificación, mapeos de programa, duplicados y auditoría (S04).

Revision ID: 0012_classification_and_review
Revises: 0011_origin_identity_by_channel
Create Date: 2026-09-16

Qué añade S04 al esquema:

1. `classification_proposals`: lo que el motor determinista (o, más adelante, un clasificador LLM
   opcional) **propone** sobre un artefacto o una representación: tipo documental, oposición, tema,
   autoridad y derechos. Una propuesta no es un hecho: tiene estado, motor, versión y confianza, y
   hasta que alguien la acepta no cambia nada del material.
2. `curriculum_mappings`: la asignación de material a un nodo del programa, que es lo que hace
   calculable la cobertura. La clave foránea al nodo es `ON DELETE RESTRICT` **a propósito**: es el
   cierre de DEBT-005 (ver `docs/decisions/ADR-007-nodos-con-material-asignado.md`). Un nodo con
   material asignado no puede desaparecer, ni por la siembra ni por un `DELETE` directo.
3. `duplicate_clusters` y `duplicate_cluster_members`: la deduplicación de **texto** (mismo
   contenido con otra codificación o maquetación) y los casi duplicados. Los duplicados exactos de
   bytes no necesitan tabla: ya son un artefacto con varios orígenes (`artifact_origins`).
4. `audit_events`: acciones que alteran autoridad, clasificación, respuesta o versión. Es lo que
   hace verificable el «deshacer» de una decisión en lote, y guarda el antes/después
   **sanitizado**, nunca el contenido completo del material.

Vocabulario que la especificación no fija (`coverage_type`, `depth`) y cómo se ha decidido:

- `coverage_type`: `mention` < `partial` < `complete`, el grado con el que el material cubre el
  nodo;
- `depth`: profundidad del nodo de programa en el árbol **en el momento de aceptar el mapeo**, para
  que la cobertura se pueda leer igual aunque el fixture reorganice el temario después.

Ambas quedan documentadas en `docs/slices/S04.md`; ampliar sus valores exige una migración, igual
que el `CHECK` de estados de `ingestion_items` en la 0006.
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0012_classification_and_review"
down_revision = "0011_origin_identity_by_channel"
branch_labels = None
depends_on = None

_SUBJECT_TYPES = ("artifact", "representation")
_AXES = ("document_type", "opposition", "topic", "authority", "rights")
_PROPOSAL_STATUSES = (
    "pending",
    "accepted",
    "rejected",
    "superseded",
    "auto_applied_provisional",
)
_COVERAGE_TYPES = ("mention", "partial", "complete")
_MAPPING_STATUSES = ("provisional", "accepted", "rejected")
_CLUSTER_KINDS = ("same_text", "near_duplicate")
_CLUSTER_RELATIONS = ("revision_candidate", "subset", "superset", "similar")
_CLUSTER_STATUSES = ("open", "resolved", "dismissed")


def _in(values: tuple[str, ...]) -> str:
    return ", ".join(repr(value) for value in values)


def upgrade() -> None:
    op.create_table(
        "classification_proposals",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("subject_type", sa.String(length=24), nullable=False),
        sa.Column("subject_id", sa.String(length=36), nullable=False),
        sa.Column("axis", sa.String(length=24), nullable=False),
        sa.Column("proposed_value", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("alternatives_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("evidence_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("engine_name", sa.String(length=64), nullable=False),
        sa.Column("engine_version", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("decision_note", sa.Text(), nullable=True),
        sa.CheckConstraint(f"subject_type IN ({_in(_SUBJECT_TYPES)})", name="ck_proposal_subject"),
        sa.CheckConstraint(f"axis IN ({_in(_AXES)})", name="ck_proposal_axis"),
        sa.CheckConstraint(f"status IN ({_in(_PROPOSAL_STATUSES)})", name="ck_proposal_status"),
        sa.CheckConstraint("confidence >= 0 AND confidence <= 1", name="ck_proposal_confidence"),
        # Una propuesta en estado `pending` no está decidida; cualquier otra sí. Sin esto se puede
        # aceptar algo sin fecha de decisión, y el «deshacer» no tendría de qué fiarse.
        sa.CheckConstraint(
            "(status = 'pending' AND decided_at IS NULL) "
            "OR (status <> 'pending' AND decided_at IS NOT NULL)",
            name="ck_proposal_decision",
        ),
        # Volver a clasificar el mismo material con el mismo motor no duplica propuestas: la
        # identidad incluye motor y versión, así que un motor nuevo sí puede proponer otra cosa.
        sa.UniqueConstraint(
            "subject_type",
            "subject_id",
            "axis",
            "engine_name",
            "engine_version",
            "proposed_value",
            name="uq_proposal_identity",
        ),
    )
    op.create_index(
        "ix_proposal_subject", "classification_proposals", ["subject_type", "subject_id", "axis"]
    )
    op.create_index("ix_proposal_status", "classification_proposals", ["status"])

    op.create_table(
        "curriculum_mappings",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "curriculum_node_id",
            sa.String(length=36),
            # DEBT-005 / ADR-007: un nodo con material asignado no se puede borrar.
            sa.ForeignKey("curriculum_nodes.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("subject_type", sa.String(length=24), nullable=False),
        sa.Column("subject_id", sa.String(length=36), nullable=False),
        sa.Column("coverage_type", sa.String(length=16), nullable=False),
        sa.Column("depth", sa.Integer(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column(
            "source_proposal_id",
            sa.String(length=36),
            sa.ForeignKey("classification_proposals.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(f"subject_type IN ({_in(_SUBJECT_TYPES)})", name="ck_mapping_subject"),
        sa.CheckConstraint(
            f"coverage_type IN ({_in(_COVERAGE_TYPES)})", name="ck_mapping_coverage"
        ),
        sa.CheckConstraint(f"status IN ({_in(_MAPPING_STATUSES)})", name="ck_mapping_status"),
        sa.CheckConstraint("depth >= 0", name="ck_mapping_depth"),
        sa.CheckConstraint("confidence >= 0 AND confidence <= 1", name="ck_mapping_confidence"),
        sa.CheckConstraint(
            "status <> 'accepted' OR approved_at IS NOT NULL", name="ck_mapping_approved"
        ),
        # Un mismo material no se mapea dos veces al mismo nodo; sí puede estar en varios nodos.
        sa.UniqueConstraint(
            "curriculum_node_id", "subject_type", "subject_id", name="uq_mapping_identity"
        ),
    )
    op.create_index("ix_mapping_subject", "curriculum_mappings", ["subject_type", "subject_id"])
    op.create_index("ix_mapping_node", "curriculum_mappings", ["curriculum_node_id"])

    op.create_table(
        "duplicate_clusters",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("kind", sa.String(length=24), nullable=False),
        sa.Column("relation", sa.String(length=24), nullable=False),
        sa.Column("signature", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolution_note", sa.Text(), nullable=True),
        sa.CheckConstraint(f"kind IN ({_in(_CLUSTER_KINDS)})", name="ck_cluster_kind"),
        sa.CheckConstraint(f"relation IN ({_in(_CLUSTER_RELATIONS)})", name="ck_cluster_relation"),
        sa.CheckConstraint(f"status IN ({_in(_CLUSTER_STATUSES)})", name="ck_cluster_status"),
        sa.CheckConstraint(
            "status = 'open' OR resolved_at IS NOT NULL", name="ck_cluster_resolved"
        ),
        # La firma es la huella del texto normalizado (o de la similitud): recalcularla no crea un
        # cluster nuevo, lo reutiliza.
        sa.UniqueConstraint("kind", "signature", name="uq_cluster_signature"),
    )
    op.create_index("ix_cluster_status", "duplicate_clusters", ["status"])

    op.create_table(
        "duplicate_cluster_members",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "cluster_id",
            sa.String(length=36),
            sa.ForeignKey("duplicate_clusters.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("subject_type", sa.String(length=24), nullable=False),
        sa.Column("subject_id", sa.String(length=36), nullable=False),
        sa.Column("similarity", sa.Float(), nullable=False),
        sa.Column("is_representative", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.CheckConstraint(f"subject_type IN ({_in(_SUBJECT_TYPES)})", name="ck_member_subject"),
        sa.CheckConstraint("similarity >= 0 AND similarity <= 1", name="ck_member_similarity"),
        sa.UniqueConstraint("cluster_id", "subject_type", "subject_id", name="uq_cluster_member"),
    )
    op.create_index(
        "ix_member_subject", "duplicate_cluster_members", ["subject_type", "subject_id"]
    )

    op.create_table(
        "audit_events",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("actor", sa.String(length=32), nullable=False),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("object_type", sa.String(length=32), nullable=False),
        sa.Column("object_id", sa.String(length=36), nullable=False),
        sa.Column("before_json", sa.Text(), nullable=True),
        sa.Column("after_json", sa.Text(), nullable=True),
        sa.Column("correlation_id", sa.String(length=36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_audit_object", "audit_events", ["object_type", "object_id"])
    op.create_index("ix_audit_created", "audit_events", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_audit_created", table_name="audit_events")
    op.drop_index("ix_audit_object", table_name="audit_events")
    op.drop_table("audit_events")

    op.drop_index("ix_member_subject", table_name="duplicate_cluster_members")
    op.drop_table("duplicate_cluster_members")

    op.drop_index("ix_cluster_status", table_name="duplicate_clusters")
    op.drop_table("duplicate_clusters")

    op.drop_index("ix_mapping_node", table_name="curriculum_mappings")
    op.drop_index("ix_mapping_subject", table_name="curriculum_mappings")
    op.drop_table("curriculum_mappings")

    op.drop_index("ix_proposal_status", table_name="classification_proposals")
    op.drop_index("ix_proposal_subject", table_name="classification_proposals")
    op.drop_table("classification_proposals")
