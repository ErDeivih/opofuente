"""Motor y sesiones SQLAlchemy 2 sobre SQLite.

Invariantes exigidos por 02_ARCHITECTURE §5:
- ``PRAGMA foreign_keys=ON`` en toda conexión;
- WAL para lectura concurrente;
- transacciones cortas;
- todo cambio de esquema pasa por Alembic.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.engine import URL
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    """Metadatos declarativos compartidos con Alembic."""


def as_utc(value: datetime | None) -> datetime | None:
    """Fecha leída de la base como UTC explícito.

    SQLite guarda `DateTime(timezone=True)` sin desplazamiento, así que al leerlo vuelve
    **ingenuo**: compararlo con un instante absoluto (`stat().st_mtime`) o con otro instante
    consciente de la zona da una diferencia de horas o un `TypeError`. Todo lo que escribe OpoFuente
    está en UTC, así que aquí se dice explícitamente al leer.
    """
    if value is None:
        return None
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def sqlite_url(database_path: Path) -> str:
    """URL de SQLAlchemy para una ruta local, sin problemas de escapado en Windows."""
    return str(URL.create("sqlite+pysqlite", database=str(database_path)))


def build_engine(database_path: Path) -> Engine:
    """Crea el motor. No abre el fichero hasta la primera conexión."""
    database_path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(
        URL.create("sqlite+pysqlite", database=str(database_path)),
        future=True,
        connect_args={"check_same_thread": False},
    )

    @event.listens_for(engine, "connect")
    def _apply_pragmas(dbapi_connection: Any, _connection_record: Any) -> None:
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.execute("PRAGMA busy_timeout=5000")
        finally:
            cursor.close()

    return engine


def build_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, expire_on_commit=False, class_=Session)
