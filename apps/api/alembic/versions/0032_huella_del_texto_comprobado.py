"""La huella del texto contra el que se verificó cada comprobación del paso E.

Revision ID: 0032_huella_del_texto_comprobado
Revises: 0031_incidencias_apuntes
Create Date: 2026-10-11

El paso E guarda, por pregunta, la frase de los apuntes que la contesta **verificada contra el
texto**. Hasta ahora, volver a ejecutar el tema reutilizaba esa comprobación sin mirar si el texto
seguía siendo el mismo: `_paso_comprobacion` compara por firma del grupo y da por buena la que ya
está. Cuando el esquema se mueve y un apartado se rehace, el texto cambia y la comprobación vieja
—con su cita— se queda: la bandeja del propietario acaba enseñando frases que **no están** en los
apuntes que va a leer.

Esta columna es la pieza que faltaba: la huella (`sha256`) del texto que el modelo leyó y contra el
que se verificó la cita. Un check se reutiliza solo si la huella es la de hoy; si no, se vuelve a
comprobar. Es una columna **nueva y anulable**: no toca ninguna fila (las que ya están se vuelven a
comprobar la próxima vez, que es justo lo que hay que hacer con ellas) y la vuelta atrás la retira.
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0032_huella_del_texto_comprobado"
down_revision = "0031_incidencias_apuntes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "question_note_anchors",
        sa.Column("text_sha256", sa.String(64), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("question_note_anchors", "text_sha256")
