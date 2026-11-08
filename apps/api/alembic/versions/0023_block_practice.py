"""Modo de sesión `block_practice` (B-017).

Revision ID: 0023_block_practice
Revises: 0022_study_marks
Create Date: 2026-11-08

La práctica libre por bloque es una sesión más, con su composición congelada como las demás; lo
único que cambia es el vocabulario del modo. Se amplía el `CHECK` de `study_sessions.mode` sin tocar
columnas ni datos.

`downgrade` se niega si ya hay sesiones de ese modo: convertirlas a otro modo falsearía lo que se
estudió, igual que la bajada de 0021 con el temario común (B-010).
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0023_block_practice"
down_revision = "0022_study_marks"
branch_labels = None
depends_on = None

_MODO_ANTERIOR = "mode IN ('practice', 'error_review', 'official_exam', 'mock_exam', 'diagnostic')"
_MODO_NUEVO = (
    "mode IN ('practice', 'error_review', 'official_exam', 'mock_exam', 'diagnostic', "
    "'block_practice')"
)


def upgrade() -> None:
    with op.batch_alter_table("study_sessions") as batch:
        batch.drop_constraint("ck_session_mode", type_="check")
        batch.create_check_constraint("ck_session_mode", _MODO_NUEVO)


def downgrade() -> None:
    conexion = op.get_bind()
    cuantas = conexion.execute(
        sa.text("SELECT count(*) FROM study_sessions WHERE mode = 'block_practice'")
    ).scalar_one()
    if cuantas:
        raise RuntimeError(
            "0023 (downgrade): hay "
            f"{cuantas} sesión(es) de práctica por bloque; no se bajan de modo a la fuerza "
            "(decisión B-017). Archívalas o expórtalas antes de bajar."
        )
    with op.batch_alter_table("study_sessions") as batch:
        batch.drop_constraint("ck_session_mode", type_="check")
        batch.create_check_constraint("ck_session_mode", _MODO_ANTERIOR)
