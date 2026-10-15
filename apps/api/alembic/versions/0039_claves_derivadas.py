"""La clave **derivada** de una pregunta, y por que una pregunta sigue fuera (§1 del encargo).

Revision ID: 0039_claves_derivadas
Revises: 0038_revision_de_apuntes
Create Date: 2026-10-15

**Dos tablas y ninguna mas, con un significado cada una.**

1. **`question_derived_keys`** — la clave derivada de **una pregunta**, con las dos fuentes que la
   sostienen (la letra de los apuntes con su cita verificada, y la letra que el modelo contesto a la
   pregunta sola). Es de la **pregunta** y no del conjunto a proposito: la clave extraida del
   material se estropea para un conjunto entero —por eso el §1 puso la fiabilidad en
   `question_sets`—, pero lo que se deriva es letra a letra: hay preguntas de un mismo conjunto con
   derivacion y sin ella.
   - La letra derivada **nunca** es la clave del conjunto: por eso vive aqui y no en
     `answer_key_versions`, y `key_state` lleva `CHECK (key_state = 'derived')`. Guardar una clave
     derivada como `active` es **imposible en la base**, no una regla de estilo que alguien pueda
     olvidar. La clave oficial del conjunto no se toca ni se copia.
   - El `CHECK` de las dos fuentes obliga a que la letra de los apuntes y la del modelo **coincidan
     en la propia fila**: una fila que no coincida no entra, y eso es la definicion de la clave
     derivada, impuesta donde no se puede saltar.
2. **`question_key_gaps`** — por que una pregunta de un conjunto en cuarentena **sigue fuera**:
   `sin_material`, `sin_cita` o `sin_coincidencia`. Es el dato que el §2 necesita para agrupar la
   bandeja **por conjunto**, y el que hace verdad «las que no tengan clave fiable siguen fuera de
   ese conjunto»: una pregunta con motivo escrito no vuelve aunque el conjunto vuelva.
   Se escribe **solo** para preguntas de conjuntos que la corrida ha procesado (los que estan en
   cuarentena), asi que ningun conjunto sano cambia de comportamiento.

**Ninguna fila existente cambia.** Las dos tablas nacen vacias; la clave activa de cada conjunto,
sus entradas y sus anclas se quedan exactamente donde estaban. Es aditivo, y la vuelta atras borra
las dos tablas: el esquema vuelve al de `0038` sin tocar ni una pregunta.
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0039_claves_derivadas"
down_revision = "0038_revision_de_apuntes"
branch_labels = None
depends_on = None

#: El vocabulario cerrado de la clave derivada, con el mismo orden que el `StrEnum` del dominio.
_ESTADOS = "key_state IN ('derived')"

#: Y el de los motivos por los que una pregunta sigue fuera.
_MOTIVOS = "reason IN ('sin_material', 'sin_cita', 'sin_coincidencia')"

#: Las dos fuentes tienen que decir la misma letra. Se compara en minuscula y sin espacios de sobra
#: porque es como se comparan en todo el motor de claves.
_FUENTES = (
    "length(trim(notes_letter)) > 0 AND length(trim(model_letter)) > 0 "
    "AND lower(trim(notes_letter)) = lower(trim(model_letter))"
)


def upgrade() -> None:
    op.create_table(
        "question_derived_keys",
        sa.Column("question_version_id", sa.String(36), primary_key=True),
        sa.Column(
            "question_set_id",
            sa.String(36),
            sa.ForeignKey("question_sets.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("correct_option_keys_json", sa.Text(), nullable=False),
        sa.Column("key_state", sa.String(16), nullable=False, server_default=sa.text("'derived'")),
        sa.Column("notes_letter", sa.String(4), nullable=False),
        sa.Column("notes_quote", sa.Text(), nullable=False),
        sa.Column(
            "notes_anchor_id",
            sa.String(36),
            sa.ForeignKey("question_note_anchors.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("notes_key_status", sa.String(16), nullable=False),
        sa.Column("model_letter", sa.String(4), nullable=False),
        sa.Column("model_name", sa.String(64), nullable=False),
        sa.Column("model_version", sa.String(64), nullable=False),
        sa.Column("prompt_version", sa.String(64), nullable=False),
        sa.Column("actor", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["question_version_id"],
            ["question_versions.id"],
            ondelete="CASCADE",
            name="fk_derived_key_question",
        ),
        sa.CheckConstraint(_ESTADOS, name="ck_derived_key_state"),
        sa.CheckConstraint(_FUENTES, name="ck_derived_key_fuentes"),
        sa.CheckConstraint("correct_option_keys_json <> '[]'", name="ck_derived_key_has_key"),
    )
    # La cuenta por conjunto (la decision del ≥ 90 %) y la lectura de la bandeja van por aqui.
    op.create_index("ix_derived_keys_set", "question_derived_keys", ["question_set_id"])

    op.create_table(
        "question_key_gaps",
        sa.Column("question_version_id", sa.String(36), primary_key=True),
        sa.Column(
            "question_set_id",
            sa.String(36),
            sa.ForeignKey("question_sets.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("reason", sa.String(24), nullable=False),
        sa.Column("actor", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["question_version_id"],
            ["question_versions.id"],
            ondelete="CASCADE",
            name="fk_key_gap_question",
        ),
        sa.CheckConstraint(_MOTIVOS, name="ck_key_gap_reason"),
    )
    op.create_index("ix_key_gaps_set", "question_key_gaps", ["question_set_id"])


def downgrade() -> None:
    op.drop_index("ix_key_gaps_set", table_name="question_key_gaps")
    op.drop_table("question_key_gaps")
    op.drop_index("ix_derived_keys_set", table_name="question_derived_keys")
    op.drop_table("question_derived_keys")
