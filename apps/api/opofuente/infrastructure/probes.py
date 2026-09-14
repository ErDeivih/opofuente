"""Sondas reales de salud para /health/ready.

Ninguna sonda simula nada: comprueban la base de datos migrada (incluida la conexión,
el modo WAL y `foreign_keys=ON`) y la escritura real en el directorio de datos.
Los mensajes de fallo no incluyen rutas absolutas.
"""

from __future__ import annotations

import os
from uuid import uuid4

from sqlalchemy import func, select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from opofuente.config import DataPaths
from opofuente.domain.system import CheckResult, CheckStatus
from opofuente.infrastructure.db_models import AppMetadataRecord


class DatabaseProbe:
    """Comprueba que SQLite responde y que el esquema está en la revisión esperada."""

    name = "database"

    def __init__(
        self,
        session_factory: sessionmaker[Session],
        expected_revision: str | None,
    ) -> None:
        self._session_factory = session_factory
        self._expected_revision = expected_revision

    def check(self) -> CheckResult:
        try:
            with self._session_factory() as session:
                session.execute(text("SELECT 1"))
                revision = session.execute(
                    text("SELECT version_num FROM alembic_version")
                ).scalar_one_or_none()
                metadata_rows = session.execute(
                    select(func.count()).select_from(AppMetadataRecord)
                ).scalar_one()
                foreign_keys = session.execute(text("PRAGMA foreign_keys")).scalar_one()
                journal_mode = session.execute(text("PRAGMA journal_mode")).scalar_one()
        except SQLAlchemyError as exc:
            return CheckResult(
                name=self.name,
                status=CheckStatus.FAILED,
                detail=f"sqlite inaccesible o esquema sin migrar ({type(exc).__name__})",
            )

        problems: list[str] = []
        if self._expected_revision is None:
            problems.append("no hay scripts de migración disponibles")
        elif revision != self._expected_revision:
            problems.append(
                f"revisión de esquema {revision or 'ninguna'} != esperada {self._expected_revision}"
            )
        if int(foreign_keys or 0) != 1:
            problems.append("PRAGMA foreign_keys no está activo")
        if str(journal_mode).lower() != "wal":
            problems.append(f"journal_mode={journal_mode} (se esperaba wal)")
        if int(metadata_rows or 0) < 1:
            problems.append("tabla app_metadata vacía")

        if problems:
            return CheckResult(self.name, CheckStatus.FAILED, "; ".join(problems))
        return CheckResult(
            name=self.name,
            status=CheckStatus.OK,
            detail=(
                f"sqlite ok (revisión {revision}, foreign_keys=ON, journal_mode=wal, "
                f"app_metadata={metadata_rows})"
            ),
        )


class DataDirectoryProbe:
    """Comprueba que el directorio de datos existe y admite escritura real."""

    name = "data_dir"

    def __init__(self, paths: DataPaths) -> None:
        self._paths = paths

    def check(self) -> CheckResult:
        try:
            self._paths.ensure_directories()
            probe_file = self._paths.tmp / f"write-probe-{os.getpid()}-{uuid4().hex}"
            probe_file.write_text("ok", encoding="utf-8")
            probe_file.unlink()
        except OSError as exc:
            return CheckResult(
                name=self.name,
                status=CheckStatus.FAILED,
                detail=f"directorio de datos no escribible ({type(exc).__name__})",
            )
        return CheckResult(
            name=self.name,
            status=CheckStatus.OK,
            detail="directorio de datos escribible",
        )
