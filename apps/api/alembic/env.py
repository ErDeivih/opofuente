"""Entorno de Alembic.

La URL de la base de datos se toma de `OPOFUENTE_DATA_DIR` (a través de `Settings`) o de
la opción `sqlalchemy.url` inyectada programáticamente por
`opofuente.infrastructure.migrations`. Nunca hay credenciales en `alembic.ini`.
"""

from __future__ import annotations

from logging.config import fileConfig

from sqlalchemy import create_engine, pool

import opofuente.infrastructure.db_models  # noqa: F401 - registra las tablas en Base.metadata
from alembic import context
from opofuente.config import get_settings
from opofuente.infrastructure.db import Base, sqlite_url

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name, disable_existing_loggers=False)

target_metadata = Base.metadata


def _database_url() -> str:
    configured = config.get_main_option("sqlalchemy.url")
    if configured:
        return configured
    settings = get_settings()
    settings.data_paths.ensure_directories()
    return sqlite_url(settings.data_paths.database)


def run_migrations_offline() -> None:
    context.configure(
        url=_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        render_as_batch=True,
        compare_type=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = create_engine(_database_url(), poolclass=pool.NullPool, future=True)
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()
    connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
