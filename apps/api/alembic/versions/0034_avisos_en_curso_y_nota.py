"""Despachar un aviso del alumno: «en curso» y la nota de lo que se ha hecho (F16, bloque C).

Revision ID: 0034_avisos_en_curso_y_nota
Revises: 0033_avisos_del_alumno
Create Date: 2026-10-11

La migración `0033` dejó los avisos del alumno guardándose con tres estados —`open`, `reviewed`,
`dismissed`— y la ruta de lectura para que el propietario los viera. Lo que faltaba era **actuar**
sobre ellos, y al construir la bandeja se midió lo que faltaba de verdad en el modelo:

1. **No había forma de decir «lo he visto y estoy en ello».** Con tres estados, un aviso está
   pendiente o está cerrado, y el propietario que empieza a mirar uno no puede dejar constancia de
   que lo tiene en la mano sin cerrarlo. Se añade **`in_progress`** y nada más: «visto» sin «en
   curso» sería el mismo estado que `open` con otro nombre, y eso sí sería inventar flujo. Los tres
   que ya había **no cambian de significado** (`open` = espera, `reviewed` = resuelto, `dismissed` =
   no era un error).

2. **No había dónde escribir qué se ha hecho.** El propietario necesita decir «arreglado en la
   versión del 12-oct» y que eso se lea la próxima vez que abra el aviso, sin volver a deducirlo. Se
   añade **`resolution_note`**, opcional (nullable) y de una línea, con el mismo tope que el motivo
   del alumno: una nota vacía no vale, y una nota que no esté puesta no se inventa.

En SQLite, ensanchar un `CHECK` obliga a **recrear la tabla**, así que la migración va por lotes
(como la `0025`): la columna, la restricción del estado con los cuatro valores y la de la nota
—`NULL` o con algo dentro, nunca en blanco— entran en la misma recreación. Las demás restricciones y
los dos índices de `0033` siguen ahí: lo comprueba su prueba.

La vuelta atrás quita la columna y vuelve a dejar los tres estados de `0033`. **Antes de bajar hay
que decidir qué pasa con los avisos que estén en `in_progress`**: su `downgrade` los devuelve a
`open` (siguen esperando, que es lo que eran antes de que existiera el estado), y eso se hace en la
misma transacción que la recreación de la tabla, no después. Las notas se pierden: son texto de una
persona y solo viven en esta columna, así que bajar de revisión las tira, y por eso lo dice aquí.
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0034_avisos_en_curso_y_nota"
down_revision = "0033_avisos_del_alumno"
branch_labels = None
depends_on = None

#: El vocabulario del estado, con el que ya había y el que faltaba.
_ESTADOS = "status IN ('open', 'in_progress', 'reviewed', 'dismissed')"

#: La nota: nula o con algo dentro. En blanco no: una nota que no dice nada es peor que no tenerla.
_NOTA = "resolution_note IS NULL OR length(trim(resolution_note)) > 0"


def upgrade() -> None:
    with op.batch_alter_table("notes_reports") as batch:
        batch.add_column(sa.Column("resolution_note", sa.Text(), nullable=True))
        batch.drop_constraint("ck_note_report_status", type_="check")
        batch.create_check_constraint("ck_note_report_status", _ESTADOS)
        batch.create_check_constraint("ck_note_report_note", _NOTA)


def downgrade() -> None:
    # Lo que esté «en curso» vuelve a esperar: es el estado que tenía antes de que este vocabulario
    # existiera, y dejarlo apuntando a un valor que el `CHECK` viejo no admite haría fallar la
    # recreación de la tabla a mitad.
    op.execute("UPDATE notes_reports SET status = 'open' WHERE status = 'in_progress'")
    with op.batch_alter_table("notes_reports") as batch:
        batch.drop_constraint("ck_note_report_note", type_="check")
        batch.drop_constraint("ck_note_report_status", type_="check")
        batch.create_check_constraint(
            "ck_note_report_status", "status IN ('open', 'reviewed', 'dismissed')"
        )
        batch.drop_column("resolution_note")
