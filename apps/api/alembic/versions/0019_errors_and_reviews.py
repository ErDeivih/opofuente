"""Errores, repaso y su historial (S10).

Revision ID: 0019_errors_and_reviews
Revises: 0018_search_and_rag
Create Date: 2026-09-18

Tres tablas, y cada una existe por una razón distinta:

1. **`learning_errors`**: lo que la persona **declara** de un fallo (causa, concepto y nota propia).
   No se crea sola: un fallo sin causa declarada es un fallo sin causa, no un fallo «de
   conocimiento» (`06_QUESTIONS` §8).
2. **`review_items`**: el estado de repaso de una pregunta (cuándo toca, intervalo, repeticiones y
   cuántos fallos ha tenido). Se crea **automáticamente** cuando un intento sale mal: §8 pide que un
   fallo entre en el repaso sin pedir nada a cambio.
3. **`review_events`**: el historial, que **no se sobrescribe**. Cada cambio de fecha guarda de
   dónde a dónde, con qué resultado, con qué confianza y por qué: sin eso, la cola de repaso sería
   una lista de fechas que nadie puede explicar.

Sobre los borrados: un elemento de repaso cuelga de la versión de pregunta (si la pregunta deja de
existir, su repaso tampoco tiene sentido), un error cuelga del intento que lo provocó, y el vínculo
con el programa (`curriculum_node_id`) va con `RESTRICT` por la misma razón que en ADR-007: el nodo
es lo que agrupa el error, y borrarlo en silencio reagruparía los fallos de otro tema como si fueran
del mismo.
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0019_errors_and_reviews"
down_revision = "0018_search_and_rag"
branch_labels = None
depends_on = None

_CAUSAS = (
    "knowledge",
    "confusion",
    "reading",
    "time",
    "calculation",
    "ambiguous",
    "other",
)
_ESTADOS_ERROR = ("open", "resolved")
_TIPOS_EVENTO = ("created", "attempt", "reviewed", "snoozed")
_DESENLACES = ("correct", "wrong")
_CONFIANZAS = ("low", "medium", "high")


def _lista(valores: tuple[str, ...]) -> str:
    return ", ".join(repr(valor) for valor in valores)


def upgrade() -> None:
    op.create_table(
        "learning_errors",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "attempt_id",
            sa.String(length=36),
            sa.ForeignKey("attempts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "curriculum_node_id",
            sa.String(length=36),
            sa.ForeignKey("curriculum_nodes.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column("concept_label", sa.Text(), nullable=True),
        sa.Column("cause", sa.String(length=16), nullable=False),
        sa.Column("user_note", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="open"),
        #: Recurrencia: cuántas veces ha fallado esta pregunta desde que el error está abierto.
        sa.Column("occurrences", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(f"cause IN ({_lista(_CAUSAS)})", name="ck_error_cause"),
        sa.CheckConstraint(f"status IN ({_lista(_ESTADOS_ERROR)})", name="ck_error_status"),
        sa.CheckConstraint("occurrences >= 1", name="ck_error_occurrences"),
        sa.CheckConstraint(
            "concept_label IS NULL OR length(trim(concept_label)) > 0", name="ck_error_concept"
        ),
        #: Un error «resuelto» tiene fecha de resolución, y uno abierto no la tiene.
        sa.CheckConstraint(
            "(status = 'resolved' AND resolved_at IS NOT NULL) OR "
            "(status = 'open' AND resolved_at IS NULL)",
            name="ck_error_resolution",
        ),
    )
    op.create_index("ix_learning_errors_attempt", "learning_errors", ["attempt_id"])
    op.create_index("ix_learning_errors_status", "learning_errors", ["status", "last_seen_at"])
    op.create_index("ix_learning_errors_node", "learning_errors", ["curriculum_node_id"])

    op.create_table(
        "review_items",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "question_version_id",
            sa.String(length=36),
            sa.ForeignKey("question_versions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "opposition_id",
            sa.String(length=36),
            sa.ForeignKey("oppositions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "learning_error_id",
            sa.String(length=36),
            sa.ForeignKey("learning_errors.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("interval_days", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("repetitions", sa.Integer(), nullable=False, server_default="0"),
        #: Fallos acumulados: es lo que distingue «se me olvidó una vez» de «no hay manera».
        sa.Column("lapses", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_reviewed_at", sa.DateTime(timezone=True), nullable=True),
        #: Motivo del último cambio de fecha, tal cual se le enseñó a la persona en la cola.
        sa.Column("last_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("interval_days >= 0", name="ck_review_interval"),
        sa.CheckConstraint("repetitions >= 0", name="ck_review_repetitions"),
        sa.CheckConstraint("lapses >= 0", name="ck_review_lapses"),
        #: Una pregunta tiene **un** repaso: dos colas para lo mismo es una cola que miente.
        sa.UniqueConstraint("question_version_id", name="uq_review_per_question"),
    )
    op.create_index("ix_review_items_due", "review_items", ["due_at"])
    op.create_index("ix_review_items_opposition", "review_items", ["opposition_id", "due_at"])

    op.create_table(
        "review_events",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "review_item_id",
            sa.String(length=36),
            sa.ForeignKey("review_items.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("kind", sa.String(length=16), nullable=False),
        sa.Column("outcome", sa.String(length=16), nullable=True),
        sa.Column("confidence", sa.String(length=16), nullable=True),
        sa.Column("cause", sa.String(length=16), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("previous_due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("previous_interval_days", sa.Integer(), nullable=True),
        sa.Column("interval_days", sa.Integer(), nullable=False),
        sa.Column("repetitions", sa.Integer(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(f"kind IN ({_lista(_TIPOS_EVENTO)})", name="ck_review_event_kind"),
        sa.CheckConstraint(
            f"outcome IS NULL OR outcome IN ({_lista(_DESENLACES)})", name="ck_review_event_outcome"
        ),
        sa.CheckConstraint(
            f"confidence IS NULL OR confidence IN ({_lista(_CONFIANZAS)})",
            name="ck_review_event_confidence",
        ),
        sa.CheckConstraint(
            f"cause IS NULL OR cause IN ({_lista(_CAUSAS)})", name="ck_review_event_cause"
        ),
        #: Un evento con desenlace lo tiene porque hubo un intento o un repaso; un aplazamiento no
        #: dice nada del saber y por eso no lo lleva.
        sa.CheckConstraint(
            "(kind IN ('created', 'attempt', 'reviewed') AND outcome IS NOT NULL) OR "
            "(kind = 'snoozed' AND outcome IS NULL)",
            name="ck_review_event_outcome_required",
        ),
    )
    op.create_index("ix_review_events_item", "review_events", ["review_item_id", "occurred_at"])


def downgrade() -> None:
    op.drop_index("ix_review_events_item", table_name="review_events")
    op.drop_table("review_events")
    op.drop_index("ix_review_items_opposition", table_name="review_items")
    op.drop_index("ix_review_items_due", table_name="review_items")
    op.drop_table("review_items")
    op.drop_index("ix_learning_errors_node", table_name="learning_errors")
    op.drop_index("ix_learning_errors_status", table_name="learning_errors")
    op.drop_index("ix_learning_errors_attempt", table_name="learning_errors")
    op.drop_table("learning_errors")
