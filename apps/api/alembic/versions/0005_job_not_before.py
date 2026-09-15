"""Espera real entre reintentos de un trabajo.

Revision ID: 0005_job_not_before
Revises: 0004_issue_relative_path
Create Date: 2026-09-14

`jobs.fail()` escribía «reintento en 2s» en el paso del trabajo, pero **no** aplazaba nada: el
trabajo quedaba inmediatamente disponible y el worker lo volvía a reclamar en la siguiente vuelta.
Esta revisión añade `not_before`, la fecha a partir de la cual el trabajo se puede reclamar, y
`claim_next` deja de tomarlo antes de tiempo.

`downgrade` elimina la columna; el aplazamiento es una comodidad de ejecución, no un dato que haya
que conservar.
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0005_job_not_before"
down_revision = "0004_issue_relative_path"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("jobs", sa.Column("not_before", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("jobs", "not_before")
