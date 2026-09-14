"""Ruta relativa en las incidencias del lote.

Revision ID: 0004_issue_relative_path
Revises: 0003_artifacts_ingestion_and_jobs
Create Date: 2026-09-14

`import_issues` solo guardaba `item_id`, y los directorios omitidos y los enlaces que salen de la
carpeta **no tienen entrada propia**: al leerlas de la base de datos se perdía a qué elemento se
referían («Omitido: directorio que no aporta material» sin decir cuál). Esta revisión añade la
columna con la ruta relativa, que es la que ya viaja en el objeto de dominio.

`downgrade` elimina la columna; no hay datos derivables que restaurar.
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0004_issue_relative_path"
down_revision = "0003_artifacts_ingestion_and_jobs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("import_issues", sa.Column("relative_path", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("import_issues", "relative_path")
