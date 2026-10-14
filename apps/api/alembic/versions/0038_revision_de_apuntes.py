"""La revisión de los apuntes por el propietario: qué decidió y con qué motivo (F24, §4.3).

Revision ID: 0038_revision_de_apuntes
Revises: 0037_origin_scope
Create Date: 2026-10-14

**Para qué sirve.** El objetivo (§4.3) pide leer un borrador **dentro del panel** y decidirlo
(«Marcar revisado»), y hasta hoy la decisión no tenía dónde escribirse: el estado de los apuntes se
deducía del par (¿hay apartados escritos?, ¿hay versión archivada?) y no había ninguna fila que
dijera «esto lo he mirado yo el 14 de octubre y por esto». La consecuencia práctica es que un tema
en borrador se quedaba en borrador sin que nadie hubiera dicho nada de él: no se distinguía «nadie
lo ha revisado» de «lo he revisado y no lo apruebo».

**Qué guarda, y qué no.** Una fila **por tema** (`uq_topic_notes_review_node`) con la decisión
(`approved` / `rejected`), la nota de lo decidido, la fecha y el actor. No guarda las cifras del
motivo: esas se **leen de donde ya están** —las comprobaciones guardadas del motor, la bandeja de
incidencias y el propio texto— porque una copia dentro de la fila sería una segunda versión de lo
mismo, y la que se queda vieja es siempre la copia. `rejected` exige nota
(`ck_topic_notes_review_note`): un rechazo sin motivo deja el borrador igual de parado y encima sin
saber por qué.

**Vuelta atrás.** Se lleva la tabla entera y con ella las decisiones. El esquema vuelve al de
`0037`; los apuntes, sus comprobaciones y sus bandejas siguen exactamente donde estaban, y el
estado de cada tema vuelve a deducirse del par de siempre.
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0038_revision_de_apuntes"
down_revision = "0037_origin_scope"
branch_labels = None
depends_on = None

#: El vocabulario cerrado de la decisión, con el mismo orden que el `StrEnum` del dominio.
_DECISIONES = "decision IN ('approved', 'rejected')"

#: Un rechazo sin motivo no se puede arreglar: lo dice la base y no solo la ruta.
_NOTA_OBLIGATORIA = "decision <> 'rejected' OR (note IS NOT NULL AND length(trim(note)) > 0)"


def upgrade() -> None:
    op.create_table(
        "topic_notes_reviews",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "curriculum_node_id",
            sa.String(36),
            sa.ForeignKey("curriculum_nodes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("decision", sa.String(16), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("actor", sa.String(120), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(_DECISIONES, name="ck_topic_notes_review_decision"),
        sa.CheckConstraint(_NOTA_OBLIGATORIA, name="ck_topic_notes_review_note"),
        # Una decisión por tema: la segunda pasada **actualiza** la primera en vez de apilar otra,
        # que es lo que hace que la tabla pueda decir «qué he decidido de este tema» sin ambigüedad.
        sa.UniqueConstraint("curriculum_node_id", name="uq_topic_notes_review_node"),
    )
    # El contador del menú pregunta «¿cuántos borradores esperan tu decisión?» en cada pantalla del
    # panel: sin índice, eso es un recorrido de la tabla con su `JOIN` por cada carga.
    op.create_index("ix_topic_notes_reviews_decision", "topic_notes_reviews", ["decision"])


def downgrade() -> None:
    op.drop_index("ix_topic_notes_reviews_decision", table_name="topic_notes_reviews")
    op.drop_table("topic_notes_reviews")
