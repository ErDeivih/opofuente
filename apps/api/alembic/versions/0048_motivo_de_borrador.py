"""Por qué una tarjeta se queda en borrador (fase «lo que ve el alumno», punto 1).

**Qué es**: una columna en `cards` que dice **por qué** una tarjeta generada **no** ha pasado a
`active`. **Sin ella, el panel enseña «5.274 en borrador» y no puede decir una sola razón**: y una
tarjeta que no se sirve sin decir por qué es una tarjeta que nadie va a arreglar.

**Qué motivos escribe**: los del punto 1 —la respuesta no está literalmente en el hecho, tiene más de
25 palabras, la pregunta la contiene, o hay otra tarjeta igual en el tema—. **Y se queda vacío en las
que sí pasan**, que es lo que las hace distinguibles.

**Por qué una columna y no una tabla aparte**: **el motivo es de la tarjeta y se lee con ella**; una
tabla de motivos habría que unirla en cada consulta para responder «¿por qué esta no?».

Revision ID: 0048_motivo_de_borrador
Revises: 0047_explicaciones_archivadas
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0048_motivo_de_borrador"
down_revision = "0047_explicaciones_archivadas"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("cards", sa.Column("draft_reason", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("cards", "draft_reason")
