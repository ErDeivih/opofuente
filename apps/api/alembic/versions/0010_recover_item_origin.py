"""Recupera la procedencia válida que la 0009 borró de más.

Revision ID: 0010_recover_item_origin
Revises: 0009_repair_item_origin
Create Date: 2026-09-16

La 0009 limpiaba la procedencia inventada, pero lo hacía **de más**: borraba el tipo de origen de
**todas** las entradas de un artefacto con varios orígenes, sin distinguir lo que la 0007 antigua
había inventado de lo que consta de verdad. En una base con dos entradas del mismo artefacto —una
llegada como fichero y otra pegada como texto, cada una con su tipo correcto— las dos se quedaban
sin procedencia.

Corregir la 0009 no arreglaría las bases que ya la ejecutaron (Alembic no reejecuta migraciones
aplicadas: es la misma lección de la 0007), así que la reparación va en una migración **posterior**.

Cómo se recupera, sin inventar nada: cada entrada guarda `origin_display`, que es la procedencia
**visible** con la que entró (la ruta relativa del fichero, el título del texto pegado, la URL ya
sin cadena de consulta), y cada origen del artefacto guarda su `display_location`. Si coinciden
exactamente, ese origen es el de esa entrada: el dato consta y se escribe. Si no coincide ninguno,
la entrada se queda como está (`NULL` = «no consta»): no se adivina. La unicidad
`UNIQUE(artifact_id, display_location)` garantiza que la coincidencia no puede ser ambigua.

`downgrade`: no hace nada, y es deliberado. Esta migración **corrige datos**; volver atrás exigiría
borrar procedencia que consta.
"""

from __future__ import annotations

from alembic import op

revision = "0010_recover_item_origin"
down_revision = "0009_repair_item_origin"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Recupera el tipo de origen cuando la procedencia visible de la entrada coincide
    # **exactamente** con la de un origen del artefacto. Ni adivina ni toca lo que no coincide.
    op.execute(
        "UPDATE ingestion_items SET origin_type = ("
        "SELECT o.origin_type FROM artifact_origins o "
        "WHERE o.artifact_id = ingestion_items.artifact_id "
        "AND o.display_location = ingestion_items.origin_display) "
        "WHERE EXISTS ("
        "SELECT 1 FROM artifact_origins o "
        "WHERE o.artifact_id = ingestion_items.artifact_id "
        "AND o.display_location = ingestion_items.origin_display)"
    )


def downgrade() -> None:
    """Sin vuelta atrás: corregir datos no se deshace borrando lo que consta."""
