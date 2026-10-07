"""Quién puede ver un conjunto de preguntas: `personal` o `public` (F2).

Revision ID: 0025_question_set_distribution
Revises: 0024_dossier_snapshots
Create Date: 2026-10-07

El corpus del propietario mezcla dos cosas que hasta ahora eran la misma fila: los **exámenes
oficiales** que publica una administración (el INAP publica sus cuestionarios) y el **material
privado** que él ha ido reuniendo (227 bancos, con su ruta de Windows en el título). La zona del
alumno solo puede servir lo primero, y esa decisión tiene que estar en el dato, no en una lista de
títulos escrita en la pantalla: una lista así se queda vieja en cuanto entra un examen nuevo.

De ahí una columna y no una tabla nueva:

1. **`personal` por defecto**, para que nada de lo que ya existe cambie de visibilidad al migrar. Lo
   que era privado sigue siéndolo salvo que alguien lo diga expresamente.
2. **`NOT NULL` con valor por defecto en el servidor**: una fila sin distribución no es una fila
   «sin decidir», es una fila que la aplicación no sabría si enseñar. El valor por defecto la
   contesta sola y el `CHECK` cierra el vocabulario.
3. **La vuelta atrás retira la columna** y con ella la decisión: bajar de revisión devuelve la base
   al estado en el que ningún conjunto tenía visibilidad declarada, que es lo que había.
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0025_question_set_distribution"
down_revision = "0024_dossier_snapshots"
branch_labels = None
depends_on = None

_DISTRIBUCIONES = "distribution IN ('personal', 'public')"


def upgrade() -> None:
    # En SQLite el `batch` recrea la tabla (no se puede añadir un `CHECK` a una existente); el
    # `server_default` es lo que hace que las filas que ya están no queden sin valor.
    with op.batch_alter_table("question_sets") as batch:
        batch.add_column(
            sa.Column(
                "distribution",
                sa.String(16),
                nullable=False,
                server_default=sa.text("'personal'"),
            )
        )
        batch.create_check_constraint("ck_question_set_distribution", _DISTRIBUCIONES)


def downgrade() -> None:
    with op.batch_alter_table("question_sets") as batch:
        batch.drop_constraint("ck_question_set_distribution", type_="check")
        batch.drop_column("distribution")
