"""El repositorio del supuesto: guardarlo con sus preguntas (M5).

**Que hace y que no**: guarda un supuesto **aceptado** con sus preguntas en
orden, y dice cuantos hay por bloque. **No valida**: cuando algo llega
aqui, ya paso las tres comprobaciones. **No decide**: el orden de las
preguntas lo trae el supuesto.

**Una transaccion para el supuesto y sus veinticinco preguntas**: un
supuesto sin ellas no es nada, y guardarlo a medias dejaria casos vacios
que el simulacro elegiria.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from opofuente.domain.practical_case import SupuestoPropuesto
from opofuente.infrastructure.db_models import (
    PracticalCaseQuestionRecord,
    PracticalCaseRecord,
    QuestionVersionRecord,
)


@dataclass(frozen=True, slots=True)
class SupuestoGuardado:
    """Un supuesto en la base, con el numero de preguntas que tiene."""

    id: str
    block: str
    statement: str
    origin: str
    preguntas: int


class SqlAlchemyPracticalCaseRepository:
    """Los supuestos y sus preguntas."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def contar(self, *, block: str, origin: str = "generated") -> int:
        """**Cuantos hay de un bloque y un origen**: es la cifra del hito."""
        with self._session_factory() as session:
            return int(
                session.execute(
                    select(func.count())
                    .select_from(PracticalCaseRecord)
                    .where(PracticalCaseRecord.block == block)
                    .where(PracticalCaseRecord.origin == origin)
                ).scalar_one()
            )

    def guardar(
        self,
        *,
        case_id: str,
        supuesto: SupuestoPropuesto,
        origin: str,
        pregunta_ids: tuple[str, ...],
        source_document: str | None = None,
    ) -> SupuestoGuardado | None:
        """Guarda el supuesto y sus preguntas, **o `None` si alguna no existe**.

        **Las preguntas tienen que existir como versiones de pregunta**: un
        supuesto apunta a preguntas del banco, no a texto suelto. **Si
        falta una, no se guarda nada**: un supuesto al que le falta una
        pregunta es una serie con un hueco, y el alumno la contestaria sin
        saber que falta.
        """
        with self._session_factory() as session:
            existentes = set(
                session.execute(
                    select(QuestionVersionRecord.id).where(
                        QuestionVersionRecord.id.in_(pregunta_ids)
                    )
                ).scalars()
            )
            if any(ident not in existentes for ident in pregunta_ids):
                return None
            ahora = datetime.now(UTC)
            session.add(
                PracticalCaseRecord(
                    id=case_id,
                    block=supuesto.block,
                    statement=supuesto.statement,
                    origin=origin,
                    source_document=source_document,
                    created_at=ahora,
                )
            )
            for posicion, pregunta_id in enumerate(pregunta_ids, start=1):
                session.add(
                    PracticalCaseQuestionRecord(
                        # **Un id propio y no `case_id` con la posicion**: 36 mas 3
                        # caracteres se pasa de lo que mide la columna, y la base lo rechaza.
                        id=str(uuid.uuid4()),
                        practical_case_id=case_id,
                        question_version_id=pregunta_id,
                        position=posicion,
                    )
                )
            session.commit()
        return SupuestoGuardado(
            id=case_id,
            block=supuesto.block,
            statement=supuesto.statement,
            origin=origin,
            preguntas=len(pregunta_ids),
        )
