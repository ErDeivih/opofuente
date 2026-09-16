"""Relación entrada-representación como tabla de asociación (varias por entrada).

Revision ID: 0008_item_representations
Revises: 0007_item_depth_and_origin
Create Date: 2026-09-15

`ingestion_items.representation_id` era una clave ajena **singular**: una entrada solo podía apuntar
a una representación. Eso contradice la especificación de S03 (04_INGESTION §5): de un mismo
artefacto conviven el **texto nativo** y el **OCR** como representaciones distintas, y una versión
nueva de un extractor crea otra más. Con una sola columna, extraer el OCR habría pisado el enlace al
texto nativo y el lote habría dejado de mostrar una representación válida.

La relación correcta es de muchos a muchos: `item_representations` con **unicidad por pareja**
(`item_id`, `representation_id`). Un mismo texto compartido por dos entradas (el fichero y su copia)
sigue siendo una sola representación con dos entradas; y una entrada puede tener su texto nativo, su
OCR y las versiones que hagan falta.

Los enlaces que ya existían se copian a la tabla y la columna se elimina. `downgrade` completo:
vuelve a crear la columna, copia un enlace por entrada (el más antiguo, que es el que la columna
singular podía representar) y quita la tabla.
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0008_item_representations"
down_revision = "0007_item_depth_and_origin"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "item_representations",
        sa.Column(
            "item_id",
            sa.String(36),
            sa.ForeignKey("ingestion_items.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "representation_id",
            sa.String(36),
            sa.ForeignKey("extracted_representations.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("item_id", "representation_id", name="uq_item_representation"),
    )
    # Los enlaces que ya había se conservan: la columna singular pasa a ser una fila de la tabla.
    op.execute(
        "INSERT INTO item_representations (item_id, representation_id, created_at) "
        "SELECT id, representation_id, CURRENT_TIMESTAMP FROM ingestion_items "
        "WHERE representation_id IS NOT NULL"
    )
    with op.batch_alter_table("ingestion_items") as batch:
        batch.drop_column("representation_id")


def downgrade() -> None:
    with op.batch_alter_table("ingestion_items") as batch:
        batch.add_column(
            sa.Column(
                "representation_id",
                sa.String(36),
                sa.ForeignKey(
                    "extracted_representations.id",
                    ondelete="SET NULL",
                    name="fk_item_representation",
                ),
                nullable=True,
            )
        )
    # Con una sola columna no caben varias representaciones: se conserva la más antigua de cada
    # entrada y se dice en la documentación que el resto no se puede representar.
    op.execute(
        "UPDATE ingestion_items SET representation_id = ("
        "SELECT ir.representation_id FROM item_representations ir "
        "WHERE ir.item_id = ingestion_items.id "
        "ORDER BY ir.created_at LIMIT 1) "
        "WHERE EXISTS (SELECT 1 FROM item_representations ir WHERE ir.item_id = ingestion_items.id)"
    )
    op.drop_table("item_representations")
