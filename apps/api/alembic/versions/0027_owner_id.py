"""De quién es el progreso: `owner_id` en las tablas de estudio (F2).

Revision ID: 0027_owner_id
Revises: 0026_examenes_oficiales_publicos
Create Date: 2026-10-07

La aplicación sigue siendo local y de un solo usuario: **no** hay cuentas, ni login, ni token. Lo
que esta migración compra es que el progreso ya sepa **de quién es** el día que las haya, sin
rehacer los datos de nadie: cada fila que hoy existe queda en `'local'`, el único propietario que
hay.

Se añade a `study_sessions` y a lo que cuelga de ella —la composición congelada, los intentos, sus
evaluaciones y los errores declarados—, que es donde vive el progreso de una persona. Tres
decisiones que se ven en el código:

1. **`NOT NULL` con valor por defecto en el servidor**, no una columna anulable: una fila sin dueño
   no es una fila «sin decidir», es una fila que el día de mañana nadie podría reclamar. El valor
   por defecto la contesta sola y las filas que ya estaban no se quedan a medias.
2. **Se copia el dueño hacia abajo** aunque el padre ya lo diga. Es redundancia a propósito: el
   listado de sesiones filtra por `study_sessions.owner_id`, y las consultas de progreso del alumno
   filtran por el de los intentos sin atravesar tres uniones para saber de quién son. El precio es
   que un cambio de dueño hay que hacerlo en la fila y en lo que cuelga de ella, y por eso el dueño
   **no** se puede cambiar desde ninguna ruta todavía.
3. **`downgrade` retira las columnas y el índice**: bajar de revisión devuelve la base al estado en
   el que el progreso no declaraba de quién era, que es exactamente lo que había.

Las tablas de repaso (`review_items`, `review_events`) se quedan **fuera** a propósito: su estado se
identifica por pregunta (índice único sobre `question_version_id`) y ensancharlo a
`(owner_id, question_version_id)` es la mitad del trabajo de las cuentas, no de esta fase. Se anota
aquí para que no se olvide, en lugar de dejar una columna que no filtra nada.
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0027_owner_id"
down_revision = "0026_examenes_oficiales_publicos"
branch_labels = None
depends_on = None

#: Las tablas donde vive el progreso de una persona, de la sesión hacia abajo. El orden es el de la
#: cadena de claves foráneas: la sesión primero, lo que cuelga de ella después.
TABLAS: tuple[str, ...] = (
    "study_sessions",
    "session_questions",
    "attempts",
    "attempt_evaluations",
    "learning_errors",
)

#: El dueño que se le pone a todo lo que ya existe: el único que hay hoy.
PROPIETARIO_POR_DEFECTO = "local"

#: El índice que sostiene el listado de sesiones de una persona, que es la consulta que se filtra.
INDICE = "ix_study_sessions_owner"


def upgrade() -> None:
    # `ALTER TABLE ... ADD COLUMN` nativo: SQLite lo admite desde siempre y no hace falta recrear la
    # tabla (a diferencia de 0025, que añadía también un `CHECK`).
    for tabla in TABLAS:
        op.add_column(
            tabla,
            sa.Column(
                "owner_id",
                sa.String(64),
                nullable=False,
                server_default=sa.text(f"'{PROPIETARIO_POR_DEFECTO}'"),
            ),
        )
    op.create_index(INDICE, "study_sessions", ["owner_id", "status"], unique=False)


def downgrade() -> None:
    op.drop_index(INDICE, table_name="study_sessions")
    for tabla in reversed(TABLAS):
        op.drop_column(tabla, "owner_id")
