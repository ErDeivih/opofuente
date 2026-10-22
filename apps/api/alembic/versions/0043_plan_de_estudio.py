"""El plan de estudio: la fecha del examen y las horas por semana (M4).

**Una fila por plan y no una por semana**: el plan se calcula, no se
guarda. Lo que se guarda es **lo que el alumno decide** —cuando es el
examen, cuanto tiempo le echa y que dias descansa—, y el reparto sale de
ahi cada vez. **Guardar el reparto seria guardar una derivacion**: en
cuanto cambie un tema o una fecha, el reparto guardado mentiria.

**`rest_days` es una cadena y no una lista JSON**: son siete valores
posibles y se guardan como `"6"` o `"0,6"`, que se lee de un vistazo en
la base. Una lista JSON en una columna de texto se lee peor y no da nada.

Revision ID: 0043_plan_de_estudio
Revises: 0042_tarjetas
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0043_plan_de_estudio"
down_revision = "0042_tarjetas"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "study_plans",
        sa.Column("id", sa.String(36), primary_key=True),
        #: El dia del examen. **Sin esto no hay plan**: es lo que decide
        #: cuanto tiempo queda.
        sa.Column("exam_date", sa.Date(), nullable=False),
        sa.Column("hours_per_week", sa.Integer(), nullable=False),
        #: Los dias de descanso, como `"6"` o `"0,6"`: cero es lunes.
        sa.Column("rest_days", sa.String(16), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("study_plans")
