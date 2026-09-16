"""Profundidad de contenedor, origen propio y representación enlazada de cada entrada.

Revision ID: 0007_item_depth_and_origin
Revises: 0006_extracted_representations
Create Date: 2026-09-15

Tres columnas nuevas en `ingestion_items`, cada una cierra un agujero real de S03:

1. **`container_depth`**: hasta qué nivel de contenedores ha bajado esta entrada. Un ZIP expandido
   deja sus miembros con profundidad 1, y un ZIP que viaja **dentro** de otro llega con profundidad
   1, así que expandirlo daría 2. El límite se comprueba con este número, no con el nombre: antes se
   contaban los segmentos terminados en `.zip`, así que un `outer.zip/inner.bin` (reconocido como
   contenedor por su contenido) se expandía otra vez y la bomba anidada se colaba.

2. **`origin_type` y `origin_display`**: de dónde salió **esta** entrada (fichero, texto pegado,
   URL) y con qué nombre se muestra. La procedencia de una representación se calculaba uniendo la
   entrada con todos los orígenes del artefacto, así que unos mismos bytes que hubieran entrado como
   fichero, como texto pegado y como URL podían aparecer con el tipo equivocado.

3. **`representation_id`**: qué representación salió de **esta** entrada. El texto extraído se
   buscaba uniendo la entrada con el artefacto, y un artefacto puede tener varias representaciones
   (el mismo contenido entrado como fichero deja `native_text` y entrado como texto pegado deja
   `plain_text`): la lista de un lote enseñaba representaciones producidas en otro lote.

Las entradas anteriores a esta migración quedan con `container_depth = 0` (todos los contenedores
ya expandidos son de primer nivel), con `origin_display` igual a su ruta relativa y con su
`origin_type` **solo cuando no hay ambigüedad**: se toma del artefacto únicamente si ese artefacto
tiene un único origen registrado. Cuando tiene varios (los mismos bytes entraron como fichero, como
texto pegado y como URL) no hay información para saber cuál correspondía a cada entrada, así que se
queda `NULL` («no consta») en lugar de inventarse uno. El `representation_id` se enlaza **solo**
cuando ese artefacto tiene una única representación: cuando hay varias no se puede saber cuál era la
de cada entrada, y adivinar sería peor que dejar el enlace vacío.

`downgrade` completo: quita las cuatro columnas.
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0007_item_depth_and_origin"
down_revision = "0006_extracted_representations"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("ingestion_items") as batch:
        batch.add_column(
            sa.Column(
                "container_depth",
                sa.Integer(),
                nullable=False,
                server_default=sa.text("0"),
            )
        )
        batch.add_column(sa.Column("origin_type", sa.String(16), nullable=True))
        batch.add_column(sa.Column("origin_display", sa.Text(), nullable=True))
        batch.add_column(
            sa.Column(
                "representation_id",
                sa.String(36),
                # Con nombre: la recreación de la tabla en SQLite (batch_alter_table) exige que las
                # restricciones estén nombradas.
                sa.ForeignKey(
                    "extracted_representations.id",
                    ondelete="SET NULL",
                    name="fk_item_representation",
                ),
                nullable=True,
            )
        )

    # `origin_display` se rellena con la ruta relativa: es un dato que ya está en la fila, no una
    # afirmación nueva. `origin_type` **no** se inventa: solo se rellena cuando no hay ambigüedad.
    op.execute(
        "UPDATE ingestion_items SET origin_display = relative_path WHERE origin_display IS NULL"
    )
    # El tipo de origen histórico solo se rellena cuando **no hay ambigüedad**: si el artefacto de
    # esa entrada tiene un único origen registrado, ese es el suyo. Con varios orígenes (los mismos
    # bytes entraron como fichero, como texto pegado y como URL) no hay información para saber cuál
    # correspondía a cada entrada, así que se queda en `NULL` («no consta») en lugar de inventarse
    # uno: decir `paste` para todas cuando una pudo venir de una URL es peor que no afirmar nada.
    op.execute(
        "UPDATE ingestion_items SET origin_type = ("
        "SELECT o.origin_type FROM artifact_origins o "
        "WHERE o.artifact_id = ingestion_items.artifact_id "
        "GROUP BY o.artifact_id HAVING COUNT(*) = 1) "
        "WHERE artifact_id IN ("
        "SELECT artifact_id FROM artifact_origins GROUP BY artifact_id HAVING COUNT(*) = 1)"
    )
    # Enlace a la representación solo cuando el artefacto tiene exactamente una.
    op.execute(
        "UPDATE ingestion_items SET representation_id = ("
        "SELECT r.id FROM extracted_representations r "
        "WHERE r.artifact_id = ingestion_items.artifact_id "
        "GROUP BY r.artifact_id HAVING COUNT(*) = 1) "
        "WHERE artifact_id IS NOT NULL"
    )


def downgrade() -> None:
    with op.batch_alter_table("ingestion_items") as batch:
        batch.drop_column("representation_id")
        batch.drop_column("origin_display")
        batch.drop_column("origin_type")
        batch.drop_column("container_depth")
