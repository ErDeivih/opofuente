"""El repositorio de las tarjetas de repaso (M3 de la fase 3).

Guarda tarjetas, dice cuales vencen y adelanta la de un hecho cuando su pregunta se falla.
**No sabe de SM-2**: la formula vive en `domain/repaso.py`. **Tampoco las genera**: eso es del
servicio.

**Una tabla y no dos**: la tarjeta sin su estado de repaso no existe, asi que el estado va en la
misma fila. La cola pregunta que vence hoy en cada pantalla, y un join por vuelta no se paga.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from opofuente.infrastructure.db_models import CardRecord


@dataclass(frozen=True, slots=True)
class CardView:
    """Una tarjeta tal como la lee la pantalla de repaso."""

    id: str
    topic_fact_id: str | None
    front: str
    back: str
    citation: str | None
    origin: str
    status: str
    ease: float
    interval_days: int
    repetitions: int
    due_at: datetime


def _view(fila: CardRecord) -> CardView:
    return CardView(
        id=str(fila.id),
        topic_fact_id=None if fila.topic_fact_id is None else str(fila.topic_fact_id),
        front=str(fila.front),
        back=str(fila.back),
        citation=None if fila.citation is None else str(fila.citation),
        origin=str(fila.origin),
        status=str(fila.status),
        ease=float(fila.ease),
        interval_days=int(fila.interval_days),
        repetitions=int(fila.repetitions),
        due_at=fila.due_at,
    )


class SqlAlchemyCardRepository:
    """Las tarjetas en la base, con el mínimo que necesita la cola del día."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def add(
        self,
        *,
        card_id: str,
        topic_fact_id: str | None,
        front: str,
        back: str,
        citation: str | None,
        origin: str,
        now: datetime,
    ) -> CardView | None:
        """Guarda una tarjeta nueva, **o devuelve la que ya existía con ese anverso**.

        **El anverso es único**: dos tarjetas del mismo par duplicarían el repaso y el trabajo del
        alumno. **Devolver la existente en vez de fallar** es lo que hace idempotente al generador:
        pasar dos veces por los mismos hechos no crea el doble de tarjetas.
        """
        with self._session_factory() as session:
            existente = session.execute(
                select(CardRecord).where(CardRecord.front == front)
            ).scalar_one_or_none()
            if existente is not None:
                return _view(existente)
            fila = CardRecord(
                id=card_id,
                topic_fact_id=topic_fact_id,
                front=front,
                back=back,
                citation=citation,
                origin=origin,
                status="active",
                ease=2.5,
                interval_days=0,
                repetitions=0,
                # **Nace vencida**: una tarjeta nueva se repasa hoy, no mañana.
                due_at=now,
                created_at=now,
            )
            session.add(fila)
            session.commit()
            return _view(fila)

    def due(self, *, dia: datetime, limit: int) -> tuple[CardView, ...]:
        """Las tarjetas que vencen en el día, **primero las más atrasadas**.

        `limit` tiene tope de 200: una pantalla de repaso con más no se hace, y **la cola ya recorta
        con su propio tope diario**.
        """
        if limit <= 0:
            raise ValueError("el límite de la cola tiene que ser mayor que cero")
        with self._session_factory() as session:
            filas = (
                session.execute(
                    select(CardRecord)
                    .where(CardRecord.status == "active")
                    .where(CardRecord.due_at <= dia)
                    .order_by(CardRecord.due_at, CardRecord.id)
                    .limit(min(limit, 200))
                )
                .scalars()
                .all()
            )
        return tuple(_view(fila) for fila in filas)

    def pending(self, *, dia: datetime) -> int:
        """**Cuántas vencen**, sin traerlas: la cola enseña el número antes de empezar."""
        with self._session_factory() as session:
            return int(
                session.execute(
                    select(func.count())
                    .select_from(CardRecord)
                    .where(CardRecord.status == "active")
                    .where(CardRecord.due_at <= dia)
                ).scalar_one()
            )

    def of_fact(self, topic_fact_id: str) -> tuple[CardView, ...]:
        """Las tarjetas de un hecho: es lo que se adelanta cuando su pregunta se falla."""
        with self._session_factory() as session:
            filas = (
                session.execute(
                    select(CardRecord)
                    .where(CardRecord.topic_fact_id == topic_fact_id)
                    .where(CardRecord.status == "active")
                )
                .scalars()
                .all()
            )
        return tuple(_view(fila) for fila in filas)

    def reschedule(
        self,
        *,
        card_id: str,
        ease: float,
        interval_days: int,
        repetitions: int,
        due_at: datetime,
        now: datetime,
    ) -> bool:
        """Escribe el resultado de SM-2 que le da el dominio.

        **`False` si la tarjeta no existe.**
        """
        with self._session_factory() as session:
            fila = session.get(CardRecord, card_id)
            if fila is None:
                return False
            fila.ease = ease
            fila.interval_days = interval_days
            fila.repetitions = repetitions
            fila.due_at = due_at
            fila.updated_at = now
            session.commit()
            return True
