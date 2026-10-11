"""Lo que el alumno marca como «esto está mal» en los apuntes, en la bandeja del propietario.

Revision ID: 0033_avisos_del_alumno
Revises: 0032_huella_del_texto_comprobado
Create Date: 2026-10-11

La decisión D2 del objetivo pide que el alumno lea los apuntes generados y **reporte** lo que ve
mal, y la D12 que ese botón exista por apartado. Lo que faltaba era el sitio donde guardarlo: hasta
ahora lo que el alumno reportaba no tenía tabla, así que el aviso se habría quedado en la pantalla.

La tabla es **de avisos**, no de comprobaciones: `notes_incidents` (migración 0031) es la bandeja
que el motor llena al comprobar las preguntas con los apuntes, con su categoría y su frase
verificada. Esto es lo contrario: una persona leyendo dice «aquí hay un error» y escribe el motivo
en una línea. Son dos cosas distintas y se arreglan de distinta manera, así que no comparten tabla
ni vocabulario.

`section_key` es la clave del apartado (el `subsection_key` de `topic_note_sections`) y `anchor` su
anclaje estable: juntos son la dirección del párrafo, y con ellos el propietario llega al sitio
exacto. `status` nace `open` y es lo único que cambiará cuando el panel empiece a despachar avisos.

Es una tabla **nueva**: no se toca ninguna fila de las que ya están. La vuelta atrás la borra, y lo
único que se pierde son los avisos pendientes, no un dato de los apuntes ni de las preguntas.
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0033_avisos_del_alumno"
down_revision = "0032_huella_del_texto_comprobado"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "notes_reports",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "curriculum_node_id",
            sa.String(36),
            sa.ForeignKey("curriculum_nodes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("owner_id", sa.String(64), nullable=False),
        sa.Column("section_key", sa.Text(), nullable=False),
        sa.Column("anchor", sa.Text(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column(
            "status",
            sa.String(16),
            nullable=False,
            server_default=sa.text("'open'"),
            default="open",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "status IN ('open', 'reviewed', 'dismissed')", name="ck_note_report_status"
        ),
        sa.CheckConstraint("length(trim(reason)) > 0", name="ck_note_report_reason"),
        sa.CheckConstraint("length(trim(section_key)) > 0", name="ck_note_report_section"),
        sa.CheckConstraint("length(trim(anchor)) > 0", name="ck_note_report_anchor"),
    )
    # La bandeja se lee por estado y por tema: sin este índice, listar los avisos pendientes recorre
    # la tabla entera cada vez que el propietario abre la bandeja.
    op.create_index("ix_notes_reports_status_created", "notes_reports", ["status", "created_at"])
    op.create_index(
        "ix_notes_reports_node_status", "notes_reports", ["curriculum_node_id", "status"]
    )


def downgrade() -> None:
    op.drop_index("ix_notes_reports_node_status", table_name="notes_reports")
    op.drop_index("ix_notes_reports_status_created", table_name="notes_reports")
    op.drop_table("notes_reports")
