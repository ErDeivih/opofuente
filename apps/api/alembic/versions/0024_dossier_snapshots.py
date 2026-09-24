"""Las versiones del dossier de un tema (S13, parte 1).

Revision ID: 0024_dossier_snapshots
Revises: 0023_pause_batch
Create Date: 2026-09-24

El dossier de un tema se **calcula** desde el corpus cada vez que se pide: la verdad está en las
evidencias y en los mapeos, no en una copia. Esta tabla guarda *instantáneas* de lo que se leyó,
para
poder decir «esto es lo que sabía del tema antes y esto lo que sé ahora» cuando entra material
nuevo.

Tres decisiones que se ven en el esquema:

1. **`payload_json` guarda el dossier entero**, no una referencia: una versión anterior tiene que
   poder leerse **como se leyó**, aunque los mapeos o las versiones de los documentos hayan cambiado
   después. Un puntero a las fuentes de hoy contaría otra cosa.
2. **`uq_dossier_snapshot_hash` por nodo y huella de contenido**: pedir el mismo dossier dos veces
no
   crea dos versiones. La huella se calcula sobre lo que el usuario lee (fuentes, citas y huecos) y
   no
   sobre la fecha, así que releer no ensucia el historial.
3. **`ON DELETE CASCADE` desde el nodo**: una instantánea de un nodo que ya no existe no es
historia,
   es basura. El nodo del programa no se borra en el uso normal (se archiva), así que esto solo
   actúa
   en una limpieza deliberada.
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0024_dossier_snapshots"
down_revision = "0023_pause_batch"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "dossier_snapshots",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "curriculum_node_id",
            sa.String(36),
            sa.ForeignKey("curriculum_nodes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("built_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("sources_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("passages_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("payload_json", sa.Text(), nullable=False),
        sa.CheckConstraint("length(content_hash) = 64", name="ck_dossier_hash"),
        sa.CheckConstraint("sources_count >= 0 AND passages_count >= 0", name="ck_dossier_counts"),
        sa.UniqueConstraint("curriculum_node_id", "content_hash", name="uq_dossier_snapshot_hash"),
    )
    op.create_index(
        "ix_dossier_snapshots_node_built",
        "dossier_snapshots",
        ["curriculum_node_id", "built_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_dossier_snapshots_node_built", table_name="dossier_snapshots")
    op.drop_table("dossier_snapshots")
