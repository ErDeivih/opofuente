"""El origen se identifica por artefacto, **canal** y etiqueta.

Revision ID: 0011_origin_identity_by_channel
Revises: 0010_recover_item_origin
Create Date: 2026-09-16

La tabla `artifact_origins` identificaba un origen por `(artifact_id, display_location)`, sin el
canal. Consecuencia real: el mismo contenido que entra como **fichero** y como **texto pegado**
con la misma etiqueta (`tema.txt` los dos) no podía tener dos orígenes; el segundo reutilizaba la
fila del primero y su canal se perdía. La identidad correcta es
`(artifact_id, origin_type, display_location)`.

Y de ahí se sigue la segunda parte: con varias entradas históricas que comparten artefacto y
etiqueta, la etiqueta **no** permite saber qué entrada vino por qué canal (la restricción vieja
tampoco dejaba guardar los dos canales, así que uno se perdió en el registro). La reparación de
datos vuelve a decidir caso por caso y, en ese caso, deja `NULL` («no consta») en lugar de elegir
uno: la 0010 resolvía la coincidencia con una subconsulta escalar que, con varias filas, se quedaba
con la primera, es decir, inventaba.

Qué hace esta migración:

1. sustituye la restricción única por la que incluye el canal;
2. deja sin tipo de origen las entradas que comparten artefacto y etiqueta con **otra** entrada (el
   canal se perdió: no se puede saber cuál era el de cada una);
3. recupera el tipo cuando hay **una sola** entrada con esa etiqueta y **un solo** origen con esa
   etiqueta (el dato consta).

`downgrade`: la vuelta atrás no puede existir tal cual: con la restricción vieja, dos orígenes del
mismo artefacto y la misma etiqueta no caben, así que se conserva uno de cada pareja —el de `id`
menor en orden binario, criterio determinista porque la tabla **no** guarda la fecha de creación del
origen— y se documenta. Ni el `id` ni `accessed_at` dicen cuándo apareció un origen, así que aquí no
se afirma nada sobre antigüedad. Se vuelve a la restricción `(artifact_id, display_location)` y las
entradas cuyo canal ya no existe vuelven a «no consta».
"""

from __future__ import annotations

from alembic import op

revision = "0011_origin_identity_by_channel"
down_revision = "0010_recover_item_origin"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("artifact_origins") as batch:
        batch.drop_constraint("uq_artifact_origin", type_="unique")
        batch.create_unique_constraint(
            "uq_artifact_origin", ["artifact_id", "origin_type", "display_location"]
        )

    # 1. Varias entradas del mismo artefacto con la **misma** etiqueta: el canal se perdió (la
    #    restricción vieja no dejaba guardar dos orígenes con la misma etiqueta), así que
    #    no se puede saber cuál vino por qué canal y no se afirma ninguno.
    op.execute(
        "UPDATE ingestion_items SET origin_type = NULL WHERE artifact_id IS NOT NULL AND ("
        "SELECT COUNT(*) FROM ingestion_items otra "
        "WHERE otra.artifact_id = ingestion_items.artifact_id "
        "AND otra.origin_display = ingestion_items.origin_display) > 1"
    )
    # 2. Una sola entrada con esa etiqueta y un único origen con esa etiqueta: el dato consta.
    op.execute(
        "UPDATE ingestion_items SET origin_type = ("
        "SELECT o.origin_type FROM artifact_origins o "
        "WHERE o.artifact_id = ingestion_items.artifact_id "
        "AND o.display_location = ingestion_items.origin_display) "
        "WHERE artifact_id IS NOT NULL AND ("
        "SELECT COUNT(*) FROM ingestion_items otra "
        "WHERE otra.artifact_id = ingestion_items.artifact_id "
        "AND otra.origin_display = ingestion_items.origin_display) = 1 AND ("
        "SELECT COUNT(*) FROM artifact_origins o "
        "WHERE o.artifact_id = ingestion_items.artifact_id "
        "AND o.display_location = ingestion_items.origin_display) = 1"
    )


def downgrade() -> None:
    """Vuelve a la restricción sin canal, conservando un origen por pareja.

    El criterio es **determinista y no temporal**: la tabla no guarda cuándo se registró cada origen
    (`accessed_at` es la última vez que se usó, y se reescribe), así que no se puede afirmar cuál es
    «el más antiguo». Se conserva el de `id` menor en orden binario —reproducible y sin depender de
    ninguna fecha— y los demás se retiran. Es una pérdida deliberada, no un descuido: con la
    restricción vieja esa información no cabe.

    Y ninguna entrada conserva un canal que acaba de desaparecer: su procedencia se mantiene solo
    si existe el origen que la respalda (mismo artefacto, etiqueta y canal); si no, vuelve a «no
    consta».
    """
    op.execute(
        "DELETE FROM artifact_origins WHERE id NOT IN ("
        "SELECT MIN(id) FROM artifact_origins GROUP BY artifact_id, display_location)"
    )
    with op.batch_alter_table("artifact_origins") as batch:
        batch.drop_constraint("uq_artifact_origin", type_="unique")
        batch.create_unique_constraint("uq_artifact_origin", ["artifact_id", "display_location"])
    op.execute(
        "UPDATE ingestion_items SET origin_type = NULL "
        "WHERE origin_type IS NOT NULL AND NOT EXISTS ("
        "SELECT 1 FROM artifact_origins o "
        "WHERE o.artifact_id = ingestion_items.artifact_id "
        "AND o.display_location = ingestion_items.origin_display "
        "AND o.origin_type = ingestion_items.origin_type)"
    )
