"""Representaciones extraídas y estados de entrada de S03.

Revision ID: 0006_extracted_representations
Revises: 0005_job_not_before
Create Date: 2026-09-15

Dos cambios:

1. **`extracted_representations`** (03_DATA-MODEL §3): una fila por intento de extracción de un
   artefacto, con su extractor y su versión, el tipo, el estado, la calidad, la clave del texto
   guardado, el número de páginas, la estructura, los avisos y si es candidata a OCR. La unicidad
   `(artifact_id, extractor_name, extractor_version, kind)` hace que volver a ejecutar el mismo
   extractor sobre el mismo artefacto no duplique nada; **otra versión del extractor sí crea otra
   representación**, que es lo que pide la especificación.

2. **Estados nuevos de entrada**: `extracted` (copiada y con texto extraído) y
   `unsupported_preserved` (copiada y conservada sin extraer, DEBT-008). La restricción `CHECK` de
   `ingestion_items.status` se recrea con los estados nuevos; en SQLite eso obliga a reconstruir la
   tabla, así que se hace con `batch_alter_table`.

`downgrade` completo: quita la tabla y devuelve el `CHECK` anterior.
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0006_extracted_representations"
down_revision = "0005_job_not_before"
branch_labels = None
depends_on = None

_OLD_ITEM_STATUSES = (
    "discovered",
    "inventoried",
    "omitted",
    "copied",
    "hashed",
    "failed",
    "cancelled",
)
_ITEM_STATUSES = (
    *_OLD_ITEM_STATUSES,
    "extracted",
    "unsupported_preserved",
    "expanded",
    "ocr_pending",
)

_REPRESENTATION_KINDS = (
    "native_text",
    "ocr",
    "plain_text",
    "html_text",
    "csv_preview",
    "json_preview",
    "image_metadata",
)
_REPRESENTATION_STATUSES = ("extracted", "pending", "empty", "failed")
_QUALITIES = ("good", "usable_with_warnings", "ocr_unreviewed", "poor", "failed")


def _status_check(values: tuple[str, ...], name: str) -> sa.CheckConstraint:
    quoted = ", ".join(f"'{value}'" for value in values)
    return sa.CheckConstraint(f"status IN ({quoted})", name=name)


def upgrade() -> None:
    op.create_table(
        "extracted_representations",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "artifact_id",
            sa.String(length=36),
            sa.ForeignKey("source_artifacts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("extractor_name", sa.String(length=64), nullable=False),
        sa.Column("extractor_version", sa.String(length=32), nullable=False),
        sa.Column("kind", sa.String(length=24), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("quality", sa.String(length=24), nullable=False),
        sa.Column("language", sa.String(length=16), nullable=True),
        sa.Column("text_storage_key", sa.Text(), nullable=True),
        sa.Column("char_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("page_count", sa.Integer(), nullable=True),
        sa.Column("ocr_candidate", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("sections_json", sa.Text(), nullable=True),
        sa.Column("warnings_json", sa.Text(), nullable=True),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        sa.Column("format_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            f"kind IN ({', '.join(repr(value) for value in _REPRESENTATION_KINDS)})",
            name="ck_representation_kind",
        ),
        sa.CheckConstraint(
            f"status IN ({', '.join(repr(value) for value in _REPRESENTATION_STATUSES)})",
            name="ck_representation_status",
        ),
        sa.CheckConstraint(
            f"quality IN ({', '.join(repr(value) for value in _QUALITIES)})",
            name="ck_representation_quality",
        ),
        sa.CheckConstraint("char_count >= 0", name="ck_representation_chars"),
        sa.UniqueConstraint(
            "artifact_id",
            "extractor_name",
            "extractor_version",
            "kind",
            name="uq_representation_extractor",
        ),
    )
    op.create_index("ix_representations_artifact", "extracted_representations", ["artifact_id"])
    op.create_index(
        "ix_representations_ocr_candidate",
        "extracted_representations",
        ["ocr_candidate"],
        sqlite_where=sa.text("ocr_candidate = 1"),
    )

    # Los estados nuevos de entrada obligan a recrear el CHECK de `ingestion_items`.
    with op.batch_alter_table("ingestion_items", recreate="always") as batch:
        batch.drop_constraint("ck_item_status", type_="check")
        new_check = ", ".join(f"'{value}'" for value in _ITEM_STATUSES)
        batch.create_check_constraint("ck_item_status", f"status IN ({new_check})")


def downgrade() -> None:
    with op.batch_alter_table("ingestion_items", recreate="always") as batch:
        batch.drop_constraint("ck_item_status", type_="check")
        old_check = ", ".join(f"'{value}'" for value in _OLD_ITEM_STATUSES)
        batch.create_check_constraint("ck_item_status", f"status IN ({old_check})")

    op.drop_index("ix_representations_ocr_candidate", table_name="extracted_representations")
    op.drop_index("ix_representations_artifact", table_name="extracted_representations")
    op.drop_table("extracted_representations")
