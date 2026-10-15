"""Cuentas, sesiones, recuperación, freno de intentos, consentimiento y contadores (S28).

Revision ID: 0040_cuentas_y_consentimiento
Revises: 0039_claves_derivadas
Create Date: 2026-10-15

**Para qué sirve.** El §8 del objetivo vivo pide cuentas con sesión propia y rutas auditadas, el §9
pide consentimiento de verdad y un inventario de datos que se pueda comprobar, y el §10 pide
contadores que no lleven identificadores. Las seis tablas de esta migración son eso, y las seis
nacen**vacías y sin uso**: con `OPOFUENTE_ACCOUNTS_ENABLED=0`, `OPOFUENTE_LEGAL_ENABLED=0`,
`OPOFUENTE_ANALYTICS_ENABLED=0` y `OPOFUENTE_PAYMENTS_ENABLED=0` —que es como nacen— nada escribe en
ellas y la aplicación se comporta como antes para quien estudia sin cuenta. Ese es el motivo de que
sean tablas nuevas y no columnas nuevas: una columna nueva en una tabla que ya se usa se paga en
cadaconsulta aunque nadie encienda la función.

**Lo que este esquema hace imposible, que es lo que de verdad importa:**

- **Ninguna contraseña en claro.** `accounts.password_hash` guarda un resumen argon2id y
  `password_algo` dice con qué derivador se escribió, para poder cambiarlo sin invalidar lo
  anterior.- **Ningún dato de red.** No hay columna de dirección, de puerto ni de navegador en
  ninguna de las
  seis tablas. El freno de intentos se identifica por el resumen del correo, no por la dirección
  desde la que se insiste; el inventario de datos lo declara y la prueba de integración lo comprueba
  contra este esquema, así que la promesa no puede envejecer sola.
- **Ningún contador con sujeto.** `analytics_events` tiene día, tipo y etiqueta: no hay dónde
  escribir una cuenta, una sesión ni un texto libre.
- **Ningún consentimiento con nombre.** `consent_records` no guarda quién decidió: la decisión que
hay que recordar por persona vive en su navegador, en una cookie propia.

**Lo que no se toca.** Ni una columna de las tablas del estudio. El progreso ya se firma con
`owner_id` desde la migración `0027`, y el dueño de una cuenta es `acct:<id>`: separar el progreso
dedos cuentas no exige migrar el modelo del estudio, solo escribir dueños distintos.

**Vuelta atrás.** Se llevan las seis tablas y con ellas las cuentas. Ninguna otra tabla las
referencia(`account_sessions` y `password_resets` sí, con `ON DELETE CASCADE`, y se van con ellas),
así que el
esquema vuelve exactamente al de `0038` y los datos del estudio quedan donde estaban. El progreso
quehubiera quedado firmado como `acct:<id>` no se borra al volver atrás: se queda sin cuenta que lo
reclame, y eso se dice en `PARA-EL-PROPIETARIO.md` en lugar de borrarlo por sorpresa.
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0040_cuentas_y_consentimiento"
down_revision = "0039_claves_derivadas"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "accounts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("email", sa.Text(), nullable=False),
        sa.Column("email_normalized", sa.Text(), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column(
            "password_algo",
            sa.String(16),
            nullable=False,
            server_default=sa.text("'argon2id'"),
        ),
        sa.Column("owner_id", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("password_changed_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("length(trim(email)) > 0", name="ck_account_email"),
        sa.CheckConstraint(
            "length(trim(email_normalized)) > 0", name="ck_account_email_normalized"
        ),
        sa.CheckConstraint("length(trim(password_hash)) > 0", name="ck_account_password_hash"),
        sa.CheckConstraint("password_algo IN ('argon2id')", name="ck_account_password_algo"),
        # Dos cuentas con el mismo correo son la misma cuenta: lo impone la base, no solo la ruta.
        sa.UniqueConstraint("email_normalized", name="uq_account_email_normalized"),
    )

    op.create_table(
        "account_sessions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "account_id",
            sa.String(36),
            sa.ForeignKey("accounts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("owner_id", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("expires_at > created_at", name="ck_account_session_expiry"),
        sa.UniqueConstraint("token_hash", name="uq_account_session_token"),
        sa.Index("ix_account_sessions_account", "account_id", "expires_at"),
    )

    op.create_table(
        "password_resets",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "account_id",
            sa.String(36),
            sa.ForeignKey("accounts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("expires_at > created_at", name="ck_password_reset_expiry"),
        sa.UniqueConstraint("token_hash", name="uq_password_reset_token"),
        sa.Index("ix_password_resets_account", "account_id", "expires_at"),
    )

    op.create_table(
        "login_throttles",
        sa.Column("key_hash", sa.String(64), primary_key=True),
        sa.Column("failures", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("window_started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("failures >= 0", name="ck_login_throttle_failures"),
        sa.CheckConstraint(
            "locked_until IS NULL OR locked_until > window_started_at",
            name="ck_login_throttle_lock",
        ),
    )

    op.create_table(
        "consent_records",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("policy_version", sa.Integer(), nullable=False),
        sa.Column("analytics", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("preferences", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.CheckConstraint("policy_version >= 1", name="ck_consent_policy_version"),
        sa.CheckConstraint("analytics IN (0, 1)", name="ck_consent_analytics"),
        sa.CheckConstraint("preferences IN (0, 1)", name="ck_consent_preferences"),
        sa.Index("ix_consent_records_decided", "decided_at"),
    )

    op.create_table(
        "analytics_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("occurred_on", sa.String(10), nullable=False),
        sa.Column("name", sa.String(16), nullable=False),
        sa.Column("label", sa.String(48), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("name IN ('page_view', 'action')", name="ck_analytics_name"),
        sa.CheckConstraint("length(trim(label)) > 0", name="ck_analytics_label"),
        sa.CheckConstraint("length(occurred_on) = 10", name="ck_analytics_day"),
        sa.Index("ix_analytics_events_day_label", "occurred_on", "name", "label"),
    )


def downgrade() -> None:
    # El orden es el inverso al de las dependencias: las hijas primero.
    op.drop_table("analytics_events")
    op.drop_table("consent_records")
    op.drop_table("login_throttles")
    op.drop_table("password_resets")
    op.drop_table("account_sessions")
    op.drop_table("accounts")
