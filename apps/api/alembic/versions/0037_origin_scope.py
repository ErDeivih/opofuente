"""De dónde sale cada conjunto: `origin_scope` (D10, §1 de los ajustes y DECISIONES §1).

Revision ID: 0037_origin_scope
Revises: 0036_claves_no_fiables
Create Date: 2026-10-13

**Para qué sirve, que es lo que decide su vocabulario.** El objetivo pide poder distinguir **de
dónde sale cada conjunto** para dos cosas concretas y ninguna más:

1. que el alumno sepa **qué está practicando** (la lista de exámenes oficiales lo enseña);
2. que los **simulacros y los exámenes** se parezcan al examen real: la normativa y la organización
   propias de **otra administración** no caen en el examen de TAI, así que no entran en una
   composición `exam_like` (`CompositionSpec.exam_like`). En un test por tema y en los apuntes
   **sí cuentan**: son material para estudiar (DECISIONES-Y-SIGUIENTE-TANDA §1).

Por eso el vocabulario es el de **la administración de la que sale el material**, y no el del tipo
de documento (eso ya lo dice `set_type`) ni el de la visibilidad (eso ya lo dice `distribution`):

- `age` — de la **Administración General del Estado**: los exámenes oficiales del INAP y de la
  Guardia Civil, que es lo que la oposición del propietario mide;
- `otra_administracion` — de otra administración (autonómica, local o institucional): es lo que
  queda **fuera** de un simulacro;
- `desconocida` — el valor por defecto, y no es un cajón de sastre: es la respuesta honesta para el
  material del propietario reunido de internet, cuya administración de origen no se puede afirmar.
  Un valor por defecto con más significado («age», por ejemplo) diría algo que nadie ha comprobado.

**Ninguna fila cambia de significado al migrar**: todas nacen `desconocida`, que no excluye de
nada. El relleno hacia atrás de los conjuntos que ya están —los cuatro del INAP de 2025 y los dos
de la Guardia Civil son `age`; los exámenes de otras administraciones, `otra_administracion`— va
por la **ruta auditada** (`PATCH /api/v1/question-sets/{id}` y su método de repositorio), no por
`UPDATE` dentro de esta migración: cada cambio de procedencia deja su evento de auditoría, que es
lo que permite revisar después por qué un conjunto quedó fuera de un simulacro.

**Vuelta atrás.** Quita la columna, su `CHECK` y su índice. Bajar **pierde la procedencia** y el
esquema vuelve al de `0036`; las preguntas, sus claves y sus conjuntos siguen exactamente donde
estaban.
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0037_origin_scope"
down_revision = "0036_claves_no_fiables"
branch_labels = None
depends_on = None

#: El vocabulario cerrado, con el mismo orden que el `StrEnum` del dominio.
_AMBITOS = "origin_scope IN ('age', 'otra_administracion', 'desconocida')"


def upgrade() -> None:
    with op.batch_alter_table("question_sets") as batch:
        batch.add_column(
            sa.Column(
                "origin_scope",
                sa.String(24),
                nullable=False,
                server_default=sa.text("'desconocida'"),
            )
        )
        batch.create_check_constraint("ck_question_set_origin_scope", _AMBITOS)
        # El motor de tests pregunta «¿qué conjuntos son de otra administración?» en cada
        # composición que se parece a un examen: sin índice, eso es un recorrido de la tabla.
        batch.create_index("ix_question_sets_origin_scope", ["origin_scope"])


def downgrade() -> None:
    with op.batch_alter_table("question_sets") as batch:
        batch.drop_index("ix_question_sets_origin_scope")
        batch.drop_constraint("ck_question_set_origin_scope", type_="check")
        batch.drop_column("origin_scope")
