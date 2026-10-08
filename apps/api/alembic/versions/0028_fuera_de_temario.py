"""Fuera de temario: dónde vive lo que no es materia del programa (F4).

Revision ID: 0028_fuera_de_temario
Revises: 0027_owner_id
Create Date: 2026-10-08

El propietario decidió que las preguntas de **otras administraciones** (Zaragoza, Murcia,
Pontevedra, Barcelona, Asturias…) no se tiren en bloque: mucha de su informática es exactamente la
de los bloques II a IV de TAI. Se clasifican por contenido y, cuando son **normativa u
organización propias de otra administración**, se declaran fuera de temario con su motivo.

Ese «fuera de temario» necesitaba un sitio, y se descartaron dos que parecían naturales:

1. **un nodo del programa** (`curriculum_nodes`): un nodo de tipo tema entraría en los recuentos del
   temario (4 bloques / 33 temas / 134 epígrafes) y en el diagnóstico por temas, y uno de otro tipo
   exigiría tocar el vocabulario de `node_type` —que es lo que declara el contrato— para decir algo
   que no es del programa;
2. **un estado del mapeo**: un mapeo necesita un nodo al que apuntar, así que volvía al problema
   anterior; y `rejected` ya significa otra cosa (una propuesta que se descartó, no una pregunta que
   no es de este examen).

Lo que sí es: **una marca en la pregunta**. Esta tabla. No tiene código oficial, ni posición, ni
título, así que **no se puede confundir con un tema**: es imposible que aparezca en el temario, y la
consulta que compone simulacros la mira por identificador de pregunta, no por nodo.

Por qué una tabla y no una columna en `question_versions`:

- el motivo es un vocabulario cerrado que en SQLite exige recrear la tabla si se añade un `CHECK`
  (como en 0025), mientras que una tabla nueva se crea tal cual;
- la marca tiene **autor y fecha** propios, y eso es lo que la hace revisable (quién la puso, cuándo
  y por qué), sin ensanchar la fila de la pregunta con metadatos de una decisión que puede cambiar;
- `ON DELETE CASCADE`: si algún día se retira una pregunta, su marca se va con ella; una marca
  huérfana no significa nada.

`downgrade` retira el índice y la tabla: bajar de revisión devuelve la base al estado en el que
«fuera de temario» no existía, que es exactamente lo que había.
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0028_fuera_de_temario"
down_revision = "0027_owner_id"
branch_labels = None
depends_on = None

TABLA = "question_curriculum_exclusions"
INDICE = "ix_question_exclusions_reason"

#: Los motivos, en el orden en que los lee quien revisa. Es el mismo vocabulario que
#: `domain.topic_classification.OutOfSyllabus`: una marca que dijera otra cosa no se sabría revisar.
MOTIVOS = ("otra_administracion", "enunciado_roto")


def _in(values: tuple[str, ...]) -> str:
    return ", ".join(repr(value) for value in values)


def upgrade() -> None:
    op.create_table(
        TABLA,
        sa.Column(
            "question_version_id",
            sa.String(36),
            sa.ForeignKey("question_versions.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("reason", sa.String(32), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("actor", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(f"reason IN ({_in(MOTIVOS)})", name="ck_question_exclusion_reason"),
        sa.CheckConstraint("length(trim(actor)) > 0", name="ck_question_exclusion_actor"),
    )
    # El listado de la cola de revisión va por motivo: sin este índice recorre la tabla entera cada
    # vez que el propietario abre la pantalla.
    op.create_index(INDICE, TABLA, ["reason"], unique=False)


def downgrade() -> None:
    op.drop_index(INDICE, table_name=TABLA)
    op.drop_table(TABLA)
