"""Metadatos de la instancia local.

Revision ID: 0001_app_metadata
Revises:
Create Date: 2026-09-14

S00 no introduce entidades de negocio. Esta primera migración crea la tabla de metadatos
de la instancia, que permite a /health/ready comprobar que el esquema se aplicó de verdad
y no solo que el fichero SQLite existe.

"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import sqlalchemy as sa

from alembic import op

revision = "0001_app_metadata"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "app_metadata",
        sa.Column("key", sa.String(length=64), primary_key=True),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    now = datetime.now(UTC)
    metadata_table = sa.table(
        "app_metadata",
        sa.column("key", sa.String),
        sa.column("value", sa.Text),
        sa.column("updated_at", sa.DateTime(timezone=True)),
    )
    op.bulk_insert(
        metadata_table,
        [
            {"key": "schema_initialized_at", "value": now.isoformat(), "updated_at": now},
            {"key": "instance_id", "value": str(uuid4()), "updated_at": now},
            {"key": "schema_origin", "value": "S00", "updated_at": now},
        ],
    )


def downgrade() -> None:
    op.drop_table("app_metadata")
