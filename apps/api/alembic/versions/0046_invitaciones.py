"""Las invitaciones de la beta cerrada (M8).

**Que es**: **un enlace de un solo uso con caducidad**, **que es lo que hace
que «beta por invitacion» signifique algo**. **Hoy hay cuentas y hay
administrador, y quien quiera entrar tiene que pedir que se la creen a mano:
eso no es una beta cerrada, es una beta de uno.**

**Las tres columnas que importan, y por que cada una:**

1. **`token_hash` y no el token**: **el enlace se enseña una vez y no se
   guarda**, **igual que una contrasena**. **Quien lea la base no puede
   invitar a nadie**;
2. **`expires_at`**: **una invitacion sin caducidad es una puerta abierta con
   un cartel de «solo invitados»**;
3. **`used_at`**: **un solo uso**. **Y se guarda cuando se usa en vez de
   borrar la fila**, **porque un enlace usado hay que poder explicarlo**.

**Y el correo va en la invitacion**: **el enlace vale para esa direccion y no
para otra**, **que es lo que impide que un enlace reenviado sirva a quien no
se invitó.**

Revision ID: 0046_invitaciones
Revises: 0045_indice_de_mapeos
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0046_invitaciones"
down_revision = "0045_indice_de_mapeos"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "account_invitations",
        sa.Column("id", sa.String(36), primary_key=True),
        # **El hash del token, no el token.** El enlace se enseña una vez.
        sa.Column("token_hash", sa.String(128), nullable=False),
        # **A quien se invita**: el enlace vale para esta direccion y no otra.
        sa.Column("email", sa.Text(), nullable=False),
        sa.Column("email_normalized", sa.Text(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        # Nulo mientras no se haya usado.
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("length(trim(token_hash)) > 0", name="ck_invitation_token"),
        sa.CheckConstraint("length(trim(email_normalized)) > 0", name="ck_invitation_email"),
    )
    # **Un indice unico por token**: dos invitaciones con el mismo hash serian
    # la misma, y buscarla por el token es lo que se hace en cada canje.
    op.create_index("ix_invitation_token", "account_invitations", ["token_hash"], unique=True)
    op.create_index("ix_invitation_email", "account_invitations", ["email_normalized"])


def downgrade() -> None:
    op.drop_index("ix_invitation_email", table_name="account_invitations")
    op.drop_index("ix_invitation_token", table_name="account_invitations")
    op.drop_table("account_invitations")
