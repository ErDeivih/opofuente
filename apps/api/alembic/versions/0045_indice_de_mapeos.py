"""Un indice para los mapeos, que es lo que hacia lenta la pantalla de progreso (M7).

**Que problema resuelve**: la consulta del progreso agrupa por nodo y une
contra `curriculum_mappings` por `(subject_type, subject_id, status)`. **El
plan de SQLite elegia `ix_mapping_node`** —el indice por nodo— y **recorria
los 47.113 mapeos** en vez de buscar los 119 intentos.

**Por que este indice y no otro**: **el `join` filtra por `subject_type` y
`subject_id`, y el `group by` pide `curriculum_node_id`**. **Un indice que
lleve las cuatro columnas en ese orden** deja resolver las dos cosas sin
tocar la tabla. **`ix_mapping_subject` ya existe con las dos primeras**, y
no basta: el motor sigue prefiriendo recorrer por nodo.

**Y lo que este cambio NO hace**: **no cambia ninguna cifra.** **Un indice
cambia como se busca, no que se encuentra**, **y eso es exactamente lo que
hay que exigirle a un arreglo de rendimiento.**

Revision ID: 0045_indice_de_mapeos
Revises: 0044_supuestos
"""

from __future__ import annotations

from alembic import op

revision = "0045_indice_de_mapeos"
down_revision = "0044_supuestos"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # El orden importa: primero lo que filtra el join, y al final lo que
    # agrupa, para que el `group by` no necesite una tabla temporal.
    op.create_index(
        "ix_mapping_subject_node",
        "curriculum_mappings",
        ["subject_type", "subject_id", "status", "curriculum_node_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_mapping_subject_node", table_name="curriculum_mappings")
