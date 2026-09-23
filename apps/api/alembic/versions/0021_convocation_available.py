"""Una convocatoria publicada puede no ser la vigente (S12.2).

Revision ID: 0021_convocation_available
Revises: 0020_changes_and_derivatives
Create Date: 2026-09-23

El índice único parcial que ya existía garantiza **una sola** convocatoria activa por oposición, y
`active`, en este modelo, significa «la que la aplicación usa para trabajar». Con una segunda
convocatoria publicada y en curso —el proceso de estabilización de Celador/a (SACYL)— los cuatro
estados que había no la describían:

- `draft` sería mentir sobre un acto ya publicado;
- `active` no puede ser, porque la vigente es una sola;
- `superseded` diría que otra convocatoria la ha reemplazado, y nada la ha reemplazado: son dos
  procesos distintos que conviven;
- `archived` significa «no la uses», y esta se puede estudiar.

De ahí `available`: **publicada, utilizable y no vigente**. La migración solo ensancha la
restricción `ck_convocation_status`; ninguna fila cambia de estado. En SQLite el
`batch_alter_table` recrea la tabla, así que la restricción vieja se sustituye por la nueva con el
mismo nombre.
"""

from __future__ import annotations

from alembic import op

revision = "0021_convocation_available"
down_revision = "0020_changes_and_derivatives"
branch_labels = None
depends_on = None

_ESTADOS_CON_DISPONIBLE = "status IN ('draft', 'active', 'available', 'superseded', 'archived')"
_ESTADOS_SIN_DISPONIBLE = "status IN ('draft', 'active', 'superseded', 'archived')"


def upgrade() -> None:
    with op.batch_alter_table("convocation_versions") as batch:
        batch.drop_constraint("ck_convocation_status", type_="check")
        batch.create_check_constraint("ck_convocation_status", _ESTADOS_CON_DISPONIBLE)


def downgrade() -> None:
    # Las convocatorias «disponibles» vuelven a «superadas» antes de estrechar la restricción: al
    # revés, el `batch` recrearía la tabla con filas que la restricción nueva rechaza.
    op.execute("UPDATE convocation_versions SET status = 'superseded' WHERE status = 'available'")
    with op.batch_alter_table("convocation_versions") as batch:
        batch.drop_constraint("ck_convocation_status", type_="check")
        batch.create_check_constraint("ck_convocation_status", _ESTADOS_SIN_DISPONIBLE)
