"""Las tarjetas de repaso y su estado de SM-2 (M3 de la fase 3).

**Que guarda, y por que en una sola tabla:**

- **la tarjeta**: anverso, reverso y **la cita del parrafo del que sale**;
- **de donde sale**: `topic_fact_id`, el hecho que la sostiene. **Sin el no se puede adelantar la
  tarjeta al fallar la pregunta de ese hecho**, que es el punto 4 de la especificacion;
- **como se hizo**: `origin` dice si salio de una plantilla (`structural`) o de un modelo
  (`generated`). **La cifra del 0,1 % solo se sostiene si se distinguen**;
- **su estado de SM-2**: en la misma fila, no en otra tabla. **Una tarjeta sin su estado de repaso
  no existe**, y un `join` por cada vuelta a la cola no se paga.

**`due_at` va indexado a proposito**: la cola pregunta «que vence hoy», y es la unica
consulta de cada pantalla de repaso.

Revision ID: 0042_tarjetas
Revises: 0041_explicaciones_cita_ancla
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0042_tarjetas"
down_revision = "0041_explicaciones_cita_ancla"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "cards",
        sa.Column("id", sa.String(36), primary_key=True),
        # **El hecho del que sale.** Sin el no se puede adelantar al fallar (punto 4).
        sa.Column("topic_fact_id", sa.String(36), nullable=True),
        sa.Column("front", sa.Text(), nullable=False),
        sa.Column("back", sa.Text(), nullable=False),
        # **La cita**: el párrafo del que sale. Una tarjeta sin cita no se puede comprobar.
        sa.Column("citation", sa.Text(), nullable=True),
        # `structural` (de plantilla, sin modelo) o `generated` (reformulada por el modelo).
        sa.Column("origin", sa.String(16), nullable=False, server_default="structural"),
        sa.Column("status", sa.String(16), nullable=False, server_default="active"),
        # **SM-2 en la misma fila**: una tarjeta sin su estado de repaso no existe.
        sa.Column("ease", sa.Float(), nullable=False, server_default="2.5"),
        sa.Column("interval_days", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("repetitions", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    # La consulta de cada pantalla de repaso: «qué vence hoy».
    op.create_index("ix_cards_due_at", "cards", ["due_at"])
    # Y la de «la tarjeta de este hecho», para adelantarla al fallar un test.
    op.create_index("ix_cards_topic_fact_id", "cards", ["topic_fact_id"])
    # El anverso es unico: dos tarjetas del mismo par duplican el repaso del alumno.
    op.create_index("ix_cards_front", "cards", ["front"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_cards_front", table_name="cards")
    op.drop_index("ix_cards_topic_fact_id", table_name="cards")
    op.drop_index("ix_cards_due_at", table_name="cards")
    op.drop_table("cards")
