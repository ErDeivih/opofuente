"""Los contadores de uso sobre SQLite (S28, §10 del objetivo vivo).

Dos operaciones y ninguna más: **sumar uno** y **contar**. No hay lectura por fila porque no hay
nada que leer por fila: no se guarda quién, ni cuándo exactamente, ni desde dónde. Se guarda el día,
si era una pantalla o una acción, y la etiqueta de una lista cerrada.

La agrupación se hace en la base (`GROUP BY`) y no en memoria: con un año de contadores, traerse las
filas para contarlas es la diferencia entre una consulta y un problema.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session, sessionmaker

from opofuente.application.account_models import CountByLabel
from opofuente.domain.analytics import AnalyticsEvent
from opofuente.infrastructure.db_models import AnalyticsEventRecord
from opofuente.infrastructure.sql_counts import affected_rows


class SqlAlchemyAnalyticsRepository:
    """Suma y cuenta contadores. Nada más, y a propósito."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def record(self, event: AnalyticsEvent, *, now: datetime) -> str:
        with self._session_factory() as session:
            fila = AnalyticsEventRecord(
                id=str(uuid4()),
                occurred_on=event.day,
                name=event.name,
                label=event.label,
                recorded_at=now,
            )
            session.add(fila)
            session.commit()
            return fila.id

    def summary(self, *, days: int) -> list[CountByLabel]:
        """Los contadores de los últimos `days` días, de mayor a menor.

        `days <= 0` cuenta todo lo que haya: es lo que se usa cuando alguien pregunta «¿qué se ha
        contado desde el principio?» en la pantalla del propietario.
        """
        consulta = (
            select(
                AnalyticsEventRecord.name,
                AnalyticsEventRecord.label,
                func.count().label("total"),
            )
            .group_by(AnalyticsEventRecord.name, AnalyticsEventRecord.label)
            .order_by(func.count().desc())
        )
        if days > 0:
            consulta = consulta.where(AnalyticsEventRecord.occurred_on >= self._first_day(days))
        with self._session_factory() as session:
            filas = session.execute(consulta).all()
        return [
            CountByLabel(name=str(nombre), label=str(etiqueta), total=int(total))
            for nombre, etiqueta, total in filas
        ]

    def totals_by_day(self, *, days: int) -> list[tuple[str, int]]:
        consulta = (
            select(AnalyticsEventRecord.occurred_on, func.count())
            .group_by(AnalyticsEventRecord.occurred_on)
            .order_by(AnalyticsEventRecord.occurred_on.desc())
        )
        if days > 0:
            consulta = consulta.where(AnalyticsEventRecord.occurred_on >= self._first_day(days))
        with self._session_factory() as session:
            filas = session.execute(consulta).all()
        return [(str(dia), int(total)) for dia, total in filas]

    def purge_older_than(self, *, day: str) -> int:
        """Borra lo anterior a un día. Es el «doce meses» del inventario, y se puede ejecutar."""
        with self._session_factory() as session:
            borrados = affected_rows(
                session.execute(
                    delete(AnalyticsEventRecord).where(AnalyticsEventRecord.occurred_on < day)
                )
            )
            session.commit()
        return borrados

    @staticmethod
    def _first_day(days: int) -> str:
        return (datetime.now(UTC) - timedelta(days=days)).date().isoformat()


__all__ = ["CountByLabel", "SqlAlchemyAnalyticsRepository"]
