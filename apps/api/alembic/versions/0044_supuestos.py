"""Los supuestos prácticos y sus preguntas (M5).

**Que guarda, y por que en dos tablas:**

- **el supuesto**: su enunciado, su bloque (III o IV) y de donde salio
  (`official` de un examen del INAP, o `generated` del modelo). **El
  enunciado es lo que el alumno lee antes de las preguntas**, y sin el no
  hay supuesto: solo hay veinte preguntas sueltas;
- **sus preguntas**: que version de pregunta va en que supuesto y en que
  orden. **Una pregunta puede estar en un supuesto y en su banco a la
  vez**, asi que esto es una tabla de union y no una columna.

**Por que el orden importa**: un supuesto es **una serie** —«con los datos
del caso, conteste»—, y las preguntas se numeran del 1 al 25. **Guardarlas
sin orden las baraja**, y una serie barajada se contesta peor.

**`origin` distingue lo oficial de lo generado**, y no es cosmetico: **el
hito exige que el simulacro prefiera un oficial**, y para eso hay que
saber cual lo es.

Revision ID: 0044_supuestos
Revises: 0043_plan_de_estudio
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0044_supuestos"
down_revision = "0043_plan_de_estudio"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "practical_cases",
        sa.Column("id", sa.String(36), primary_key=True),
        #: El bloque del examen al que pertenece: III o IV.
        sa.Column("block", sa.String(4), nullable=False),
        #: **El enunciado del caso**: lo que se lee antes de las preguntas.
        sa.Column("statement", sa.Text(), nullable=False),
        #: `official` (de un examen del INAP) o `generated` (del modelo).
        sa.Column("origin", sa.String(16), nullable=False),
        #: La fuente oficial, si la hay: de que documento y que examen.
        sa.Column("source_document", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "practical_case_questions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "practical_case_id",
            sa.String(36),
            sa.ForeignKey("practical_cases.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "question_version_id",
            sa.String(36),
            sa.ForeignKey("question_versions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        #: **El orden dentro del supuesto**: del 1 al 25, sin huecos.
        sa.Column("position", sa.Integer(), nullable=False),
    )
    op.create_index(
        "ix_practical_cases_block",
        "practical_cases",
        ["block", "origin"],
    )
    op.create_index(
        "ix_practical_case_questions_case",
        "practical_case_questions",
        ["practical_case_id", "position"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_practical_case_questions_case",
        table_name="practical_case_questions",
    )
    op.drop_index("ix_practical_cases_block", table_name="practical_cases")
    op.drop_table("practical_case_questions")
    op.drop_table("practical_cases")
