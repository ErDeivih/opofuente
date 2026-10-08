"""Lecturas del clasificador de preguntas (F4): qué bancos hay y qué pregunta cada uno.

Es un repositorio **de lectura** y existe aparte del banco de preguntas por una razón: lo que el
clasificador necesita saber no es «dame preguntas», es «dame las que **no tienen tema** agrupadas
por su conjunto de origen y en un orden que no cambie entre pasadas». Mezclarlo con las consultas
del banco (que sirven preguntas con su clave y su auditoría) habría dejado dos intenciones en el
mismo sitio.

Tres decisiones que se ven en el SQL:

1. **«sin tema» es «sin ningún mapeo»**, no «sin mapeo aceptado». Una pregunta con una propuesta
   provisional ya está en la cola del propietario: volver a proponerla en la pasada siguiente sería
   llenar la cola de lo mismo.
2. **Las ya declaradas fuera de temario tampoco entran**: ya están decididas, y volver a preguntarle
   al modelo por ellas sería pagar dos veces por la misma respuesta.
3. **El orden es determinista y estable**: por número de preguntas pendientes de mayor a menor —que
   es lo que permite cortar tras los dos primeros bancos con sentido— y, a igualdad, por título e
   identificador. Sin ese desempate, dos pasadas podrían coger bancos distintos y el informe no
   cuadraría con el anterior.
"""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from opofuente.application.topic_classification_models import BankToClassify
from opofuente.domain.topic_classification import ClassifiableQuestion
from opofuente.infrastructure.db_models import (
    CurriculumMappingRecord,
    OptionVersionRecord,
    QuestionCurriculumExclusionRecord,
    QuestionSetRecord,
    QuestionVersionRecord,
)

#: Estados del conjunto que no se clasifican: un conjunto archivado es material retirado.
_NO_ARCHIVADOS = QuestionSetRecord.status != "archived"

#: Una versión `superseded` no es una pregunta del banco: ya no se practica (DEBT-025).
_NO_SUSTITUIDAS = QuestionVersionRecord.status != "superseded"


class SqlAlchemyTopicClassificationRepository:
    """Los bancos con preguntas sin tema y las preguntas de cada banco, para clasificarlas."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def banks(self, opposition_id: str, *, limit: int | None = None) -> tuple[BankToClassify, ...]:
        """Bancos con preguntas sin tema, de mayor a menor, con lo que les falta por clasificar.

        Se cuentan en SQL y no en memoria: el banco del propietario tiene 17.000 preguntas y
        traerlas todas para contarlas en Python sería pagar en cada arranque lo que se paga una vez.
        """
        sin_tema = (
            ~select(CurriculumMappingRecord.id)
            .where(
                CurriculumMappingRecord.subject_type == "question_version",
                CurriculumMappingRecord.subject_id == QuestionVersionRecord.id,
            )
            .exists()
        )
        excluidas = (
            ~select(QuestionCurriculumExclusionRecord.question_version_id)
            .where(
                QuestionCurriculumExclusionRecord.question_version_id == QuestionVersionRecord.id
            )
            .exists()
        )
        consulta = (
            select(
                QuestionSetRecord.id,
                QuestionSetRecord.title,
                func.count(QuestionVersionRecord.id),
            )
            .join(
                QuestionVersionRecord,
                QuestionVersionRecord.question_set_id == QuestionSetRecord.id,
            )
            .where(
                QuestionSetRecord.opposition_id == opposition_id,
                _NO_ARCHIVADOS,
                _NO_SUSTITUIDAS,
                sin_tema,
                excluidas,
            )
            .group_by(QuestionSetRecord.id, QuestionSetRecord.title)
            .order_by(
                func.count(QuestionVersionRecord.id).desc(),
                QuestionSetRecord.title,
                QuestionSetRecord.id,
            )
        )
        if limit is not None:
            consulta = consulta.limit(limit)
        with self._session_factory() as session:
            filas = session.execute(consulta).all()
            return tuple(
                BankToClassify(set_id=str(fila[0]), title=str(fila[1]), pending=int(fila[2]))
                for fila in filas
            )

    def pending_questions(
        self, set_id: str, *, limit: int | None = None
    ) -> tuple[ClassifiableQuestion, ...]:
        """Las preguntas sin tema del banco, en el orden del documento, con sus opciones.

        El orden es el de la publicación (posición y clave estable): una pregunta sin número —las
        que se importaron de un texto sin numerar— cae al final, ordenada por su clave, que es
        determinista.
        """
        sin_tema = (
            ~select(CurriculumMappingRecord.id)
            .where(
                CurriculumMappingRecord.subject_type == "question_version",
                CurriculumMappingRecord.subject_id == QuestionVersionRecord.id,
            )
            .exists()
        )
        consulta = (
            select(QuestionVersionRecord.id)
            .where(
                QuestionVersionRecord.question_set_id == set_id,
                _NO_SUSTITUIDAS,
                sin_tema,
            )
            .order_by(
                QuestionVersionRecord.position,
                QuestionVersionRecord.stable_key,
                QuestionVersionRecord.id,
            )
        )
        if limit is not None:
            consulta = consulta.limit(limit)
        with self._session_factory() as session:
            identificadores = [str(fila) for fila in session.execute(consulta).scalars()]
            if not identificadores:
                return ()
            opciones: dict[str, list[tuple[str, str]]] = {clave: [] for clave in identificadores}
            filas = session.execute(
                select(
                    OptionVersionRecord.question_version_id,
                    OptionVersionRecord.stable_key,
                    OptionVersionRecord.text,
                )
                .where(OptionVersionRecord.question_version_id.in_(identificadores))
                .order_by(
                    OptionVersionRecord.question_version_id,
                    OptionVersionRecord.position,
                )
            ).all()
            for pregunta_id, clave, texto in filas:
                opciones[str(pregunta_id)].append((str(clave), str(texto)))
            enunciados: dict[str, str] = {
                str(pregunta_id): str(enunciado)
                for pregunta_id, enunciado in session.execute(
                    select(QuestionVersionRecord.id, QuestionVersionRecord.stem).where(
                        QuestionVersionRecord.id.in_(identificadores)
                    )
                ).all()
            }
            return tuple(
                ClassifiableQuestion(
                    question_version_id=clave,
                    stem=str(enunciados.get(clave, "")),
                    options=tuple(opciones[clave]),
                )
                for clave in identificadores
            )


__all__ = ["SqlAlchemyTopicClassificationRepository"]
