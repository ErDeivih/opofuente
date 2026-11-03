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

from opofuente.domain.study_plan import Plan, TemaDelPlan, planificar
from opofuente.infrastructure.db_models import StudyPlanRecord


@dataclass(frozen=True, slots=True)
class PlanGuardado:
    """Lo que el alumno decidio: el examen, las horas y los descansos."""

    exam_date: date
    hours_per_week: int
    rest_days: frozenset[int]


@dataclass(frozen=True, slots=True)
class AvanceDeBloque:
    """Lo leido y lo practicado de los temas de un bloque, **contados por bloque**."""

    codigo: str
    titulo: str
    leidos: int
    practicados: int
    total: int


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
                           count(distinct s.id) as secciones,
                           coalesce(p.official_code, '') as bloque_codigo,
                           coalesce(p.title, '') as bloque_titulo
                    from curriculum_nodes n
                    left join curriculum_nodes p on p.id = n.parent_id
                    left join question_note_anchors a
                           on a.curriculum_node_id = n.id
                    left join topic_note_sections s
                           on s.curriculum_node_id = n.id
                    where n.node_type = 'topic'
                    group by n.official_code, n.title, p.official_code, p.title
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
                bloque_codigo=str(fila[4]),
                bloque_titulo=str(fila[5]),
            )
            for fila in filas
        )

    def avance_por_bloque(self) -> tuple[AvanceDeBloque, ...]:
        """Lo leido y lo practicado de cada bloque, **en una sola consulta**.

        **La pantalla no vuelve a decidir el umbral**: compara `leidos` con los
        que el plan daba por hechos a estas alturas. Aqui solo se cuentan los
        temas y se agrupan por su bloque padre; un tema sin padre cae en
        `sin-bloque`, que se pinta como «Sin bloque».
        """
        with self._session_factory() as session:
            filas = session.execute(
                text(
                    """
                    select coalesce(p.official_code, 'sin-bloque') as codigo,
                           coalesce(p.title, 'Sin bloque') as titulo,
                           count(distinct n.id) as total,
                           count(distinct case when exists(
                               select 1 from topic_note_sections s
                               where s.curriculum_node_id = n.id
                           ) then n.id end) as leidos,
                           count(distinct case when exists(
                               select 1
                               from question_note_anchors a
                               join session_questions sq
                                    on sq.question_version_id = a.question_version_id
                               join attempts t on t.session_question_id = sq.id
                               where a.curriculum_node_id = n.id
                                 and t.answered_at is not null
                           ) then n.id end) as practicados
                    from curriculum_nodes n
                    left join curriculum_nodes p on p.id = n.parent_id
                    where n.node_type = 'topic'
                      and exists(
                          select 1 from question_note_anchors a
                          where a.curriculum_node_id = n.id
                      )
                    group by p.official_code, p.title
                    order by codigo
                    """
                )
            ).all()
        return tuple(
            AvanceDeBloque(
                codigo=str(fila[0]),
                titulo=str(fila[1]),
                total=int(fila[2]),
                leidos=int(fila[3]),
                practicados=int(fila[4]),
            )
            for fila in filas
        )

    def leido_y_practicado(self) -> tuple[int, int]:
        """Cuantos temas tienen apuntes y cuantos tienen alguna pregunta contestada.

        **«Leido» es tener texto** y no haberlo abierto: no hay registro de
        lectura, y suponerlo seria inventar. **«Practicado» es haber contestado
        al menos una pregunta de ese tema** en cualquier test. **Las dos cifras
        son de temas, no de preguntas**, porque el plan reparte temas.
        """
        with self._session_factory() as session:
            leidos = session.execute(
                text("select count(distinct curriculum_node_id) from topic_note_sections")
            ).scalar_one()
            practicados = session.execute(
                text(
                    """
                    select count(distinct a.curriculum_node_id)
                    from question_note_anchors a
                    join session_questions s
                         on s.question_version_id = a.question_version_id
                    join attempts t on t.session_question_id = s.id
                    where t.answered_at is not null
                    """
                )
            ).scalar_one()
        return int(leidos), int(practicados)

    def plan(self, *, hoy: date | None = None) -> Plan | None:
        """El plan entero, **o `None` si el alumno no ha puesto la fecha**.

        **Se recalcula en cada llamada**: guardarlo seria guardar una derivacion, y la derivacion
        miente en cuanto cambia un tema. **La fecha de hoy entra por parametro**, para que el plan
        sea determinista y se pueda comparar con el de la semana pasada.
        """
        guardado = self.guardado()
        if guardado is None:
            return None
        temas = self.temas()
        if not temas:
            return None
        return planificar(
            temas,
            hoy=hoy or datetime.now(UTC).date(),
            fecha_examen=guardado.exam_date,
            horas_por_semana=guardado.hours_per_week,
            dias_de_descanso=guardado.rest_days,
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
