"""La forma de lo que crea `0039` y su vuelta atrás, medidas en la base (S28).

El método del proyecto es «escrito no es hecho; ejecutado es hecho», y una migración que declara
columnas no está probada hasta que se mira la tabla que dejó. Aquí se comprueba lo que el §8 al §11
necesita que sea verdad **en el esquema**, y no en un comentario:

1. las seis tablas existen al llegar a la cabeza;
2. las restricciones que hacen imposible guardar lo que no se puede guardar **rechazan de verdad**
   (`password_algo` que no sea argon2id, un suceso de analítica con un tipo inventado, un fin de
   consentimiento que no sea 0 o 1, un bloqueo que empieza antes de su ventana);
3. la clave única de la dirección normalizada impide dos cuentas con el mismo correo;
4. la vuelta atrás **se lleva las seis tablas**;
5. y —lo que sostiene el inventario de datos del §9— **no hay ninguna columna de dirección de red ni
   de navegador** en ninguna de las seis.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from alembic import command
from opofuente.config import Settings
from opofuente.infrastructure.db import build_engine
from opofuente.infrastructure.migrations import alembic_config, run_migrations, script_head

TABLAS: tuple[str, ...] = (
    "accounts",
    "account_sessions",
    "password_resets",
    "login_throttles",
    "consent_records",
    "analytics_events",
)

#: Fragmentos que **no** pueden aparecer en el nombre de ninguna columna de estas tablas. Es la
#: mitad del §9 que casi nunca se escribe: lo que **no** se recoge, comprobado contra el esquema.
PROHIBIDOS: tuple[str, ...] = (
    "ip",
    "remote_addr",
    "client_address",
    "user_agent",
    "browser",
    "platform",
    "visitor_id",
    "third_party",
    "ga_id",
    "cookie_id",
)


def _settings(tmp_path: Path) -> Settings:
    return Settings(data_dir=tmp_path / "datos", _env_file=None)


def _columnas(settings: Settings, tabla: str) -> list[str]:
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.connect() as conexion:
            return [str(fila[1]) for fila in conexion.execute(text(f"PRAGMA table_info({tabla})"))]
    finally:
        engine.dispose()


def _ejecutar(settings: Settings, sentencia: str) -> None:
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.begin() as conexion:
            conexion.execute(text(sentencia))
    finally:
        engine.dispose()


def _tablas(settings: Settings) -> set[str]:
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.connect() as conexion:
            return {
                str(fila[0])
                for fila in conexion.execute(
                    text("SELECT name FROM sqlite_master WHERE type = 'table'")
                )
            }
    finally:
        engine.dispose()


@pytest.fixture
def migrada(tmp_path: Path) -> Settings:
    settings = _settings(tmp_path)
    run_migrations(settings, revision="head")
    return settings


def test_la_cabeza_es_la_migracion_de_la_plataforma(migrada: Settings) -> None:
    assert script_head(migrada) == "0039_cuentas_y_consentimiento"


def test_las_seis_tablas_estan_y_no_tienen_donde_guardar_una_persona(migrada: Settings) -> None:
    """Lo que el inventario del §9 declara: estas columnas existen, y estas otras no."""
    presentes = _tablas(migrada)
    for tabla in TABLAS:
        assert tabla in presentes, tabla
        columnas = [columna.lower() for columna in _columnas(migrada, tabla)]
        assert columnas, f"{tabla} no tiene columnas"
        for prohibido in PROHIBIDOS:
            for columna in columnas:
                assert prohibido not in columna, f"{tabla}.{columna} no debería existir"

    # Y la contraseña se guarda en un resumen, con su algoritmo declarado al lado.
    columnas_cuenta = _columnas(migrada, "accounts")
    assert "password_hash" in columnas_cuenta
    assert "password_algo" in columnas_cuenta
    assert "password" not in columnas_cuenta, "no puede haber una columna de contraseña en claro"


def test_el_algoritmo_de_la_contrasena_esta_acotado(migrada: Settings) -> None:
    """Un algoritmo que no sea argon2id no entra: lo impide la base, no solo el código."""
    with pytest.raises(IntegrityError):
        _ejecutar(
            migrada,
            "INSERT INTO accounts (id, email, email_normalized, password_hash, password_algo, "
            "owner_id, created_at, updated_at, password_changed_at) VALUES "
            "('a', 'a@b.es', 'a@b.es', 'x', 'sha256', 'acct:x', '2026-10-15', '2026-10-15', "
            "'2026-10-15')",
        )


def test_no_hay_dos_cuentas_con_la_misma_direccion(migrada: Settings) -> None:
    sentencia = (
        "INSERT INTO accounts (id, email, email_normalized, password_hash, password_algo, "
        "owner_id, created_at, updated_at, password_changed_at) VALUES "
        "('{id}', '{email}', 'ana@ejemplo.es', 'x', 'argon2id', 'acct:{id}', '2026-10-15', "
        "'2026-10-15', '2026-10-15')"
    )
    _ejecutar(migrada, sentencia.format(id="cuenta-1", email="ana@ejemplo.es"))
    with pytest.raises(IntegrityError):
        _ejecutar(migrada, sentencia.format(id="cuenta-2", email="ana@ejemplo.es"))


def test_los_contadores_solo_admiten_su_vocabulario(migrada: Settings) -> None:
    """Un suceso de analítica con un tipo inventado no se guarda: el vocabulario es cerrado."""
    _ejecutar(
        migrada,
        "INSERT INTO analytics_events (id, occurred_on, name, label, recorded_at) VALUES "
        "('e1', '2026-10-15', 'page_view', 'inicio', '2026-10-15')",
    )
    with pytest.raises(IntegrityError):
        _ejecutar(
            migrada,
            "INSERT INTO analytics_events (id, occurred_on, name, label, recorded_at) VALUES "
            "('e2', '2026-10-15', 'click', 'inicio', '2026-10-15')",
        )


def test_el_consentimiento_solo_admite_dos_valores(migrada: Settings) -> None:
    with pytest.raises(IntegrityError):
        _ejecutar(
            migrada,
            "INSERT INTO consent_records (id, decided_at, policy_version, analytics, preferences) "
            "VALUES ('c1', '2026-10-15', 1, 2, 0)",
        )


def test_un_bloqueo_no_puede_empezar_antes_de_su_ventana(migrada: Settings) -> None:
    with pytest.raises(IntegrityError):
        _ejecutar(
            migrada,
            "INSERT INTO login_throttles (key_hash, failures, window_started_at, locked_until) "
            "VALUES ('k', 5, '2026-10-15 12:00:00', '2026-10-15 11:00:00')",
        )


def test_la_vuelta_atras_se_lleva_las_seis_tablas(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    run_migrations(settings, revision="head")
    assert set(TABLAS) <= _tablas(settings)

    command.downgrade(alembic_config(settings), "0038_revision_de_apuntes")

    presentes = _tablas(settings)
    for tabla in TABLAS:
        assert tabla not in presentes, f"{tabla} sigue ahí tras bajar a 0038"

    # Y volver a subir las recrea: bajar no deja el esquema en un estado del que no se pueda salir.
    run_migrations(settings, revision="head")
    presentes = _tablas(settings)
    for tabla in TABLAS:
        assert tabla in presentes, f"{tabla} no se ha recreado al volver a subir"
