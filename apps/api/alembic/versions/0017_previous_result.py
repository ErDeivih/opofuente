"""Recalcular conserva el resultado anterior (S08).

Revision ID: 0017_previous_result
Revises: 0016_study_sessions
Create Date: 2026-09-17

Dos columnas en `study_sessions`, y el porqué:

1. **`previous_result_json`**: recalcular con una clave nueva (S08) no puede borrar lo que se dijo
   antes. La puntuación anterior se guarda para que la interfaz pueda explicar «tu puntuación cambió
   de X a Y por la plantilla oficial v2» en lugar de cambiar la cifra en silencio.
2. **`recalculated_at`**: cuándo se recalculó, para poder fechar el cambio.

Las evaluaciones anteriores **no** se tocan: la tabla `attempt_evaluations` ya guarda una fila por
clave con `supersedes_id`, así que la corrección de la clave v1 sigue siendo legible después de
añadir la de la v2 (invariante 7).
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0017_previous_result"
down_revision = "0016_study_sessions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("study_sessions") as batch:
        batch.add_column(sa.Column("previous_result_json", sa.Text(), nullable=True))
        batch.add_column(sa.Column("recalculated_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("study_sessions") as batch:
        batch.drop_column("recalculated_at")
        batch.drop_column("previous_result_json")
