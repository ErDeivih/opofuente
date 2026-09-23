"""La nota de la fecha del ejercicio también se guarda y se sirve (S12.2).

Revision ID: 0022_convocation_exam_date_note
Revises: 0021_convocation_available
Create Date: 2026-09-23

La convocatoria del proceso de estabilización de Celador/a **no tiene fecha de ejercicio
publicada**: la fija la resolución de admitidos (base 8.3), y las listas provisionales se publicaron
en octubre de 2025. El fixture lo explicaba en `exam_date_note`, pero esa nota se quedaba en el
fichero: ni la base la guardaba ni la API la servía, así que la interfaz solo podía decir «no consta
en la convocatoria», que se lee igual cuando falta el dato que cuando la convocatoria lo deja para
más adelante.

Una columna nueva (`ADD COLUMN`, que en SQLite no recrea la tabla) y el campo en el detalle de la
convocatoria. No es decorativo: sin él, la aplicación no puede distinguir «no lo sé» de «lo dirá
otra resolución», y esa diferencia decide si tiene sentido estudiar para ese proceso.
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0022_convocation_exam_date_note"
down_revision = "0021_convocation_available"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("convocation_versions") as batch:
        batch.add_column(sa.Column("exam_date_note", sa.Text(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("convocation_versions") as batch:
        batch.drop_column("exam_date_note")
