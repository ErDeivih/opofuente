"""Despachar una incidencia del motor: su estado y la nota de lo que se ha hecho (F18, bloque C).

Revision ID: 0035_incidencias_despachables
Revises: 0034_avisos_en_curso_y_nota
Create Date: 2026-10-13

La migración `0031` creó `notes_incidents` —la bandeja del motor— con la categoría, el motivo, la
frase verificada y el apartado, y nada más. Estaba bien para lo que era entonces: un resto que la
corrida de apuntes contaba al terminar. Pero el §4.1 del objetivo pide una bandeja que **se
despache**, y al construirla se midió lo que faltaba de verdad en el modelo:

1. **No había estado.** Una incidencia está en la bandeja o no está: se borra cuando el motor deja
   de señalarla, y su `save_incidents` no guarda ninguna decisión. Sin estado, el propietario solo
   puede mirar y callarse, que es exactamente el hueco que esta tanda viene a cerrar. Se añaden los
   **cuatro estados que esta aplicación ya usa para despachar una bandeja** —los mismos de
   `notes_reports` (`0033`/`0034`): `open`, `in_progress`, `reviewed`, `dismissed`— y ni uno más:
   un vocabulario nuevo para el mismo trabajo sería inventar un flujo, y `dismissed` hace falta de
   verdad, porque el motor **se equivoca** (una clave que contradice la norma puede estar bien y
   ser los apuntes los que sobra) y sin él esa incidencia no se podría cerrar nunca.

2. **No había dónde escribir qué se ha hecho**, ni cuándo se cerró. Se añaden `resolution_note` —una
   línea, opcional, como la del aviso del alumno— y `reviewed_at`, que solo tiene fecha mientras la
   incidencia esté cerrada: la columna dice cuándo se despachó y una incidencia abierta con fecha de
   revisión es una traza que miente. Eso lo decide el dominio, no la pantalla.

Lo que **no** cambia: el motor. `save_incidents` sigue ignorando estas columnas, así que una
decisión
del propietario sobrevive a una corrida que vuelve a señalar lo mismo. Lo que sí queda dicho: si el
motor deja de señalar una incidencia, la borra (es su comportamiento desde `0031`) y con la fila se
va la nota; lo que se decidió sigue en `audit_events`, que es donde esta aplicación conserva lo que
el dato pierde.

La vuelta atrás borra las tres columnas y el índice. **Las decisiones y sus notas se pierden**: solo
viven aquí, y por eso lo dice. Los estados no hay que recolocarlos —la columna se va entera—, pero
las filas que estaban despachadas vuelven a aparecer como pendientes en cuanto el motor las señale
otra vez, que es lo que eran antes de esta migración.
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0035_incidencias_despachables"
down_revision = "0034_avisos_en_curso_y_nota"
branch_labels = None
depends_on = None

#: El vocabulario del estado: el mismo de la bandeja del alumno, que es el que ya existe.
_ESTADOS = "status IN ('open', 'in_progress', 'reviewed', 'dismissed')"

#: La nota: nula o con algo dentro. En blanco no: una nota que no dice nada es peor que no tenerla.
_NOTA = "resolution_note IS NULL OR length(trim(resolution_note)) > 0"


def upgrade() -> None:
    with op.batch_alter_table("notes_incidents") as batch:
        # Las 453 incidencias que ya hay entran como `open`: nadie ha decidido nada sobre ellas
        # todavía, y ese es justo el punto de partida de la bandeja.
        batch.add_column(
            sa.Column(
                "status",
                sa.String(16),
                nullable=False,
                server_default=sa.text("'open'"),
            )
        )
        batch.add_column(sa.Column("resolution_note", sa.Text(), nullable=True))
        batch.add_column(sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True))
        batch.create_check_constraint("ck_notes_incident_status", _ESTADOS)
        batch.create_check_constraint("ck_notes_incident_note", _NOTA)
    # El índice del filtro de la bandeja: «las pendientes de esta categoría» es la consulta que la
    # pantalla hace cada vez que se enciende.
    op.create_index("ix_notes_incidents_status_category", "notes_incidents", ["status", "category"])


def downgrade() -> None:
    op.drop_index("ix_notes_incidents_status_category", table_name="notes_incidents")
    with op.batch_alter_table("notes_incidents") as batch:
        batch.drop_constraint("ck_notes_incident_note", type_="check")
        batch.drop_constraint("ck_notes_incident_status", type_="check")
        batch.drop_column("reviewed_at")
        batch.drop_column("resolution_note")
        batch.drop_column("status")
