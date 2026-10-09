"""Una letra distinta de la clave es un conflicto, no una cobertura (revisión de los apuntes).

Revision ID: 0030_ancla_en_conflicto
Revises: 0029_apuntes_por_preguntas
Create Date: 2026-10-09

La revisión del propietario midió que **96 preguntas** de los tres pilotos contaban como cubiertas
cuando los apuntes daban una letra distinta de la de su plantilla (clave en borrador). El criterio
estaba mal en el dominio: con clave en borrador decidía solo la frase copiada, y una letra distinta
de la clave no es «cubierta», es un **conflicto** (o la clave está mal, o los apuntes) que va a la
cola de revisión.

La migración solo ensancha la restricción `ck_anchor_result` para que el resultado nuevo se pueda
guardar; **ninguna fila cambia de estado**. Las que ya estaban guardadas se vuelven a evaluar cuando
el tema se compruebe otra vez, y la vuelta atrás devuelve los conflictos a `doubtful`, que es lo que
eran antes (una duda para revisar). En SQLite el `batch_alter_table` recrea la tabla, así que la
restricción vieja se sustituye por la nueva con el mismo nombre.
"""

from __future__ import annotations

from alembic import op

revision = "0030_ancla_en_conflicto"
down_revision = "0029_apuntes_por_preguntas"
branch_labels = None
depends_on = None

_RESULTADOS_CON_CONFLICTO = "result IN ('covered', 'gap', 'doubtful', 'conflict')"
_RESULTADOS_SIN_CONFLICTO = "result IN ('covered', 'gap', 'doubtful')"


def upgrade() -> None:
    with op.batch_alter_table("question_note_anchors") as batch:
        batch.drop_constraint("ck_anchor_result", type_="check")
        batch.create_check_constraint("ck_anchor_result", _RESULTADOS_CON_CONFLICTO)


def downgrade() -> None:
    # Los conflictos vuelven a ser dudas **antes** de estrechar la restricción: al revés, el `batch`
    # recrearía la tabla con filas que la restricción nueva rechaza. El motivo no se toca: sigue
    # siendo el mismo (`letra_no_coincide`), y la pregunta sigue en la cola de revisión.
    op.execute("UPDATE question_note_anchors SET result = 'doubtful' WHERE result = 'conflict'")
    with op.batch_alter_table("question_note_anchors") as batch:
        batch.drop_constraint("ck_anchor_result", type_="check")
        batch.create_check_constraint("ck_anchor_result", _RESULTADOS_SIN_CONFLICTO)
