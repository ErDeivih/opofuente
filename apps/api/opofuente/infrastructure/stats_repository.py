"""Las estadisticas del alumno: lo que dice que hacer (M6).

**Tres consultas y ninguna mas**, y las tres sobre lo que ya esta guardado:

1. **los cinco temas con menos acierto y mas intentos** —los flojos, con su
   boton de practicar—;
2. **el tiempo medio por pregunta**, frente a los 72 segundos del examen;
3. **la evolucion semanal**: el acierto de cada una de las ultimas semanas.

**El acierto es comparar dos JSON**: el que eligio el alumno
(`attempts.chosen_option_keys_json`) y el que corrige
(`answer_key_entries.correct_option_keys_json`). **`key_outcome` NO es el
acierto**: dice si la pregunta tiene clave (`keyed`) o si su clave se
contradice (`conflicting`), y leerlo como si fuera el resultado da un cero
en todos los temas.

**Y `attempts` es lo que se cuenta**: una pregunta contestada es una fila
ahi, con su tiempo. `session_questions` sin `attempt` es una pregunta que
se sirvio y no se contesto, y contarla como fallo seria mentir.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session, sessionmaker

from opofuente.infrastructure.db_models import (
    AttemptRecord,
)

#: Los segundos por pregunta que da el examen: 120 minutos para 100.
SEGUNDOS_POR_PREGUNTA_DEL_EXAMEN = 72


@dataclass(frozen=True, slots=True)
class TemaFlojo:
    """Un tema donde el alumno falla, **con su cifra**."""

    codigo: str
    titulo: str
    intentos: int
    acierto: float

    @property
    def frase(self) -> str:
        return f"{self.codigo}: aciertas el {self.acierto:.0%} en {self.intentos} intentos"


@dataclass(frozen=True, slots=True)
class SemanaDeAcierto:
    """El acierto de una semana, **y cuantos intentos lo sostienen**."""

    empieza: str
    intentos: int
    acierto: float


@dataclass(frozen=True, slots=True)
class Estadisticas:
    """Lo que la pantalla de progreso necesita para decir que hacer."""

    flojos: tuple[TemaFlojo, ...]
    segundos_por_pregunta: float | None
    semanas: tuple[SemanaDeAcierto, ...]

    @property
    def comparacion_del_tiempo(self) -> str | None:
        """El tiempo medio frente al del examen, **dicho como es**.

        **No es «vas mas rapido»**: el alumno practica en sesiones cortas y
        el examen es de cien preguntas. **Se dice el dato y se dice que son
        cosas distintas**, o no se dice.
        """
        if self.segundos_por_pregunta is None:
            return None
        return (
            f"Tus tests van a {self.segundos_por_pregunta:.1f} s por pregunta; "
            f"el examen da {SEGUNDOS_POR_PREGUNTA_DEL_EXAMEN} s. "
            "No es lo mismo: aquí practicas en tandas cortas."
        )


class SqlAlchemyStatsRepository:
    """Las tres consultas de M6, **y ninguna escritura**."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def flojos(self, *, limite: int = 5) -> tuple[TemaFlojo, ...]:
        """Los temas con menos acierto, **solo los que tienen intentos**.

        **Un tema sin intentos no es un tema flojo**: es un tema sin
        practicar, y eso se dice de otra manera.
        """
        with self._session_factory() as session:
            filas = session.execute(
                text(
                    """
                    select n.official_code,
                           n.title,
                           count(*) as intentos,
                           sum(case when t.chosen_option_keys_json =
                                         k.correct_option_keys_json
                                    then 1 else 0 end)
                               * 1.0 / count(*) as acierto
                    from attempts t
                    join session_questions q on q.id = t.session_question_id
                    join answer_key_entries k
                         on k.question_version_id = q.question_version_id
                    join question_note_anchors a
                         on a.question_version_id = q.question_version_id
                    join curriculum_nodes n on n.id = a.curriculum_node_id
                    where t.answered_at is not null
                    group by n.official_code, n.title
                    having count(*) >= 3
                    order by acierto asc, intentos desc
                    limit :limite
                    """
                ),
                {"limite": limite},
            ).all()
        return tuple(
            TemaFlojo(
                codigo=str(fila[0]),
                titulo=str(fila[1]),
                intentos=int(fila[2]),
                acierto=float(fila[3]),
            )
            for fila in filas
        )

    def tiempo_medio(self) -> float | None:
        """Los segundos por pregunta, **o `None` si no hay intentos con tiempo**."""
        with self._session_factory() as session:
            media = session.execute(
                select(func.avg(AttemptRecord.elapsed_ms)).where(
                    AttemptRecord.elapsed_ms.isnot(None)
                )
            ).scalar_one_or_none()
        if media is None:
            return None
        return float(media) / 1000.0

    def semanas(self, *, cuantas: int = 6) -> tuple[SemanaDeAcierto, ...]:
        """El acierto de las ultimas semanas, **de la mas vieja a la mas nueva**.

        **Se cuenta por semanas que empiezan en lunes**, y solo salen las
        que tienen intentos: **una semana vacia no es un cero por ciento**,
        es una semana sin datos.
        """
        desde = datetime.now(UTC) - timedelta(weeks=cuantas)
        with self._session_factory() as session:
            filas = session.execute(
                text(
                    """
                    select strftime('%Y-%m-%d', date(t.answered_at, 'weekday 0', '-6 days'))
                               as empieza,
                           count(*) as intentos,
                           sum(case when t.chosen_option_keys_json =
                                         k.correct_option_keys_json
                                    then 1 else 0 end)
                               * 1.0 / count(*) as acierto
                    from attempts t
                    join session_questions q on q.id = t.session_question_id
                    join answer_key_entries k
                         on k.question_version_id = q.question_version_id
                    where t.answered_at is not null
                      and t.answered_at >= :desde
                    group by empieza
                    order by empieza
                    """
                ),
                {"desde": desde.isoformat()},
            ).all()
        return tuple(
            SemanaDeAcierto(empieza=str(fila[0]), intentos=int(fila[1]), acierto=float(fila[2]))
            for fila in filas
        )
