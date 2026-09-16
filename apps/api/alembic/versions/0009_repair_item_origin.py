"""Repara las bases que ya ejecutaron la versión antigua de 0007.

Revision ID: 0009_repair_item_origin
Revises: 0008_item_representations
Create Date: 2026-09-16

La migración `0007` se corrigió para no inventar procedencia histórica, pero esa migración **ya se
había aplicado** en instalaciones anteriores: Alembic no vuelve a ejecutarla, así que una base
marcada como `0007_item_depth_and_origin` (o actualizada después a `0008`) conservaba los
`origin_type` falsos que escribió la versión antigua: `paste` o `url` para todas las entradas de un
artefacto que en realidad tenía varios orígenes. Corregir el fichero de una migración ya aplicada no
arregla las bases que la ejecutaron: hace falta una migración **posterior**, y esta lo es.

Qué hace, en dos pasos y en este orden:

1. **limpia lo inventado**: si el artefacto de la entrada tiene **varios** orígenes, no se puede
   saber cuál era el suyo, así que el tipo vuelve a `NULL` («no consta»);
2. **recupera lo inequívoco**: si el artefacto tiene **un único** origen registrado, ese es el suyo
   y se escribe (también para las filas que quedaron en `NULL` con la versión nueva de `0007`).

`origin_display` no se toca: siempre fue un dato que ya estaba en la fila (su ruta relativa), no
una afirmación.

`downgrade`: no hace nada, y es deliberado. Esta migración **corrige datos**; reconstruir el valor
inventado exigiría volver a afirmar algo que no consta. Se deja documentado en lugar de escribir un
`downgrade` que mienta.
"""

from __future__ import annotations

from alembic import op

revision = "0009_repair_item_origin"
down_revision = "0008_item_representations"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Ambiguo: el artefacto tiene más de un origen → el tipo inventado vuelve a «no consta».
    op.execute(
        "UPDATE ingestion_items SET origin_type = NULL WHERE artifact_id IN ("
        "SELECT artifact_id FROM artifact_origins GROUP BY artifact_id HAVING COUNT(*) > 1)"
    )
    # 2. Inequívoco: un solo origen → ese es el tipo de la entrada (también si estaba en NULL).
    op.execute(
        "UPDATE ingestion_items SET origin_type = ("
        "SELECT o.origin_type FROM artifact_origins o "
        "WHERE o.artifact_id = ingestion_items.artifact_id) "
        "WHERE artifact_id IN ("
        "SELECT artifact_id FROM artifact_origins GROUP BY artifact_id HAVING COUNT(*) = 1)"
    )


def downgrade() -> None:
    """Sin vuelta atrás: corregir un dato inventado no se deshace volviendo a inventarlo."""
