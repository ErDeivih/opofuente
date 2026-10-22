"""El repositorio del plan: los temas con su peso y su carencia (M4).

**Dos cosas y ninguna mas**: los temas que el planificador necesita,
con su enunciado, sus preguntas y sus secciones; y la fila del plan, que
guarda lo que decide el alumno.

**La carencia se mide aqui y no en el dominio**: `secciones` y
`preguntas` son dos `count` sobre la base, y el dominio no habla SQL.
**Lo que el dominio decide es el orden**, y para eso le basta un
booleano.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime

from sqlalchemy import select, text
from sqlalchemy.orm import Session, sessionmaker

from opofuente.domain.study_plan import TemaDelPlan
from opofuente.infrastructure.db_models import StudyPlanRecord


@dataclass(frozen=True, slots=True)
class PlanGuardado:
    """Lo que el alumno decidio: el examen, las horas y los descansos."""

    exam_date: date
    hours_per_week: int
    rest_days: frozenset[int]


class SqlAlchemyPlanRepository:
    """Los temas que se reparten y la fila del plan."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def temas(self) -> tuple[TemaDelPlan, ...]:
        """Los temas del programa activo, **con su peso y su carencia**.

        **La carencia es `secciones / preguntas`, y se compara con la
        mediana**: un tema esta flojo si tiene menos apuntes por pregunta
        que la mitad de los temas. **No se compara con un numero fijo**
        porque el programa entero puede tener pocos o muchos apuntes, y
        el umbral tiene que moverse con el.

        **Los temas sin preguntas no entran**: no se pueden practicar, y
        meterlos en el plan seria mandar a leer algo que nadie evalua.
        """
        with self._session_factory() as session:
            filas = session.execute(
                text(
                    """
                    select n.official_code,
                           n.title,
                           count(distinct a.question_version_id) as preguntas,
                           count(distinct s.id) as secciones
                    from curriculum_nodes n
                    left join question_note_anchors a
                           on a.curriculum_node_id = n.id
                    left join topic_note_sections s
                           on s.curriculum_node_id = n.id
                    where n.node_type = 'topic'
                    group by n.official_code, n.title
                    having count(distinct a.question_version_id) > 0
                    order by n.official_code
                    """
                )
            ).all()
        if not filas:
            return ()
        proporciones = sorted((fila[3] / fila[2]) for fila in filas if int(fila[2]) > 0)
        mediana = proporciones[len(proporciones) // 2]
        return tuple(
            TemaDelPlan(
                codigo=str(fila[0]),
                titulo=str(fila[1]),
                preguntas=int(fila[2]),
                flojo=(fila[3] / fila[2]) <= mediana,
            )
            for fila in filas
        )

    def guardado(self) -> PlanGuardado | None:
        """El plan que hay, **o `None` si nadie ha puesto la fecha**."""
        with self._session_factory() as session:
            fila = session.execute(select(StudyPlanRecord)).scalars().first()
            if fila is None:
                return None
            return PlanGuardado(
                exam_date=fila.exam_date,
                hours_per_week=int(fila.hours_per_week),
                rest_days=frozenset(
                    int(valor)
                    for valor in str(fila.rest_days).split(",")
                    if valor.strip().isdigit()
                ),
            )

    def guardar(
        self, *, exam_date: date, hours_per_week: int, rest_days: frozenset[int]
    ) -> PlanGuardado:
        """Escribe el plan del alumno. **Uno solo**: el plan es suyo y no hay historial."""
        ahora = datetime.now(UTC)
        with self._session_factory() as session:
            fila = session.execute(select(StudyPlanRecord)).scalars().first()
            texto = ",".join(str(dia) for dia in sorted(rest_days))
            if fila is None:
                session.add(
                    StudyPlanRecord(
                        id=str(__import__("uuid").uuid4()),
                        exam_date=exam_date,
                        hours_per_week=hours_per_week,
                        rest_days=texto,
                        created_at=ahora,
                    )
                )
            else:
                fila.exam_date = exam_date
                fila.hours_per_week = hours_per_week
                fila.rest_days = texto
                fila.updated_at = ahora
            session.commit()
        return PlanGuardado(exam_date=exam_date, hours_per_week=hours_per_week, rest_days=rest_days)
