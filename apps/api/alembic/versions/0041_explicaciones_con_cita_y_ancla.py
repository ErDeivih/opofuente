"""La explicación se ancla al párrafo: cita literal y apartado (M1 de la fase 3).

Revision ID: 0041_explicaciones_cita_ancla
Revises: 0040_cuentas_y_consentimiento
Create Date: 2026-10-20

**Para qué sirve.** El §3 de la fase 3 pide que la explicación de una pregunta se apoye en
**el apartado de los apuntes que ya contiene la respuesta** y que la comprobación sea mecánica:
**la cita existe literalmente en los apuntes**. La tabla `question_explanations` ya tenía `origin`,
`status`, `model_name` y `text`; lo que faltaba era **de dónde sale** lo que dice.

**Nacen nulas** y no rompen nada: las 11.315 explicaciones privadas que ya están siguen sin cita y
sin ancla, y solo las nuevas (`origin = 'generated'`) las llevan. **El código que las exige es quien
decide**: una explicación generada sin cita no pasa las comprobaciones y va a la bandeja como
`sin_material`.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0041_explicaciones_cita_ancla"
down_revision: str | None = "0040_cuentas_y_consentimiento"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("question_explanations") as batch:
        batch.add_column(sa.Column("citation", sa.Text(), nullable=True))
        batch.add_column(sa.Column("note_anchor_id", sa.String(length=36), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("question_explanations") as batch:
        batch.drop_column("note_anchor_id")
        batch.drop_column("citation")
