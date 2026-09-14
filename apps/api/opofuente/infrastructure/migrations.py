"""Ejecución y comprobación de migraciones Alembic.

La URL de la base de datos se resuelve desde `Settings` (`OPOFUENTE_DATA_DIR`), nunca
desde alembic.ini, para que las pruebas puedan apuntar a un directorio temporal.
"""

from __future__ import annotations

from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import Engine, text
from sqlalchemy.exc import SQLAlchemyError

from alembic import command
from opofuente.config import Settings, get_settings, project_root
from opofuente.infrastructure.db import sqlite_url

SCRIPT_LOCATION = ("apps", "api", "alembic")


def alembic_config(settings: Settings) -> Config:
    config = Config()
    config.set_main_option("script_location", str(project_root().joinpath(*SCRIPT_LOCATION)))
    config.set_main_option("sqlalchemy.url", sqlite_url(settings.data_paths.database))
    return config


def script_head(settings: Settings) -> str | None:
    """Revisión de cabeza declarada por los scripts de migración."""
    script = ScriptDirectory.from_config(alembic_config(settings))
    return script.get_current_head()


def run_migrations(settings: Settings, revision: str = "head") -> None:
    """Aplica migraciones hasta `revision`. Usado por scripts, pruebas y desarrollo."""
    settings.data_paths.ensure_directories()
    command.upgrade(alembic_config(settings), revision)


def database_revision(engine: Engine) -> str | None:
    """Revisión aplicada en la base de datos, o None si no hay tabla de Alembic."""
    try:
        with engine.connect() as connection:
            row = connection.execute(text("SELECT version_num FROM alembic_version")).scalar()
    except SQLAlchemyError:
        return None
    return str(row) if row is not None else None


def default_head() -> str | None:
    return script_head(get_settings())
