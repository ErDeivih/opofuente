"""Las preguntas que los apuntes no cubren, en la bandeja del propietario con su categoría.

Revision ID: 0031_incidencias_apuntes
Revises: 0030_ancla_en_conflicto
Create Date: 2026-10-10

El §2.1.4 del objetivo pide que, antes de cerrar un tema, se intente rellenar los huecos de los
apuntes y que **lo que siga sin resolver vaya a la bandeja del propietario con el motivo**. Hasta
ahora ese resto solo se contaba en el informe de la corrida: se perdía al cerrar la terminal.

La categoría es un vocabulario cerrado de cuatro valores, y cada uno nombra **quién lo arregla**: al
hueco se le escribe más material, a la clave sospechosa se le revisa la clave, a la pregunta ambigua
se le reescribe el enunciado y a la norma cambiada se le comprueba qué dice hoy la norma. Sin la
categoría, la bandeja sería una lista de preguntas sin saber qué hacer con ellas.

Es una tabla **nueva**: no se toca ninguna fila de las que ya están. La vuelta atrás la borra, y lo
único que se pierde es lo que la bandeja enseñaba, no un dato de los apuntes ni de las preguntas.
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0031_incidencias_apuntes"
down_revision = "0030_ancla_en_conflicto"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "notes_incidents",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "curriculum_node_id",
            sa.String(36),
            sa.ForeignKey("curriculum_nodes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "question_version_id",
            sa.String(36),
            sa.ForeignKey("question_versions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("group_signature", sa.String(64), nullable=False),
        sa.Column("category", sa.String(24), nullable=False),
        sa.Column("coverage", sa.String(16), nullable=False),
        sa.Column("reason", sa.String(48), nullable=False),
        sa.Column("section_key", sa.Text(), nullable=True),
        sa.Column("anchor", sa.Text(), nullable=True),
        sa.Column("phrase", sa.Text(), nullable=True),
        sa.Column("detail", sa.Text(), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default=sa.text("1"), default=1),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "category IN ('hueco_sin_material', 'clave_sospechosa', 'pregunta_ambigua', "
            "'norma_cambiada')",
            name="ck_notes_incident_category",
        ),
        sa.CheckConstraint(
            "coverage IN ('doubtful', 'conflict')", name="ck_notes_incident_coverage"
        ),
        sa.CheckConstraint("length(trim(detail)) > 0", name="ck_notes_incident_detail"),
        sa.CheckConstraint("attempts >= 1", name="ck_notes_incident_attempts"),
        # Una pregunta está una vez en la bandeja de un tema: volver a comprobar el tema no puede
        # llenar la bandeja de copias de la misma incidencia.
        sa.UniqueConstraint(
            "question_version_id", "curriculum_node_id", name="uq_notes_incident_question_node"
        ),
    )
    op.create_index(
        "ix_notes_incidents_node_category", "notes_incidents", ["curriculum_node_id", "category"]
    )


def downgrade() -> None:
    op.drop_index("ix_notes_incidents_node_category", table_name="notes_incidents")
    op.drop_table("notes_incidents")
