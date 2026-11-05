"""Marca de estudio por nodo del temario común.

Revision ID: 0022_study_marks
Revises: 0021_temario_comun_y_referencias
Create Date: 2026-11-05

Una fila por nodo que la persona marca como estudiado, con la fecha. Es el dato que alimenta el
avance por bloque y total (MAPA de objetivos, bloque 3) sin guardar porcentajes: el porcentaje se
calcula al leerlo, igual que la cobertura.

`ON DELETE CASCADE` a propósito: la marca no tiene sentido sin el nodo, y no es contenido que haya
que conservar como evidencia (a diferencia de los mapeos, que son `RESTRICT`). Borrar el nodo
solo es posible si no tiene material asignado (ADR-007), así que la marca nunca se lleva por
delante nada más.

`down_revision` es `0021`; el `downgrade` retira la tabla.
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0022_study_marks"
down_revision = "0021_temario_comun_y_referencias"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "curriculum_study_marks",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "curriculum_node_id",
            sa.String(length=36),
            sa.ForeignKey("curriculum_nodes.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("marked_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("curriculum_study_marks")
