"""El servicio del plan: junta los temas con el planificador (M4).

**No decide nada**: **lee los temas, llama a `planificar`, y devuelve su
resultado**. La decision del reparto esta en el dominio y probada ahi; lo
que hace este servicio es darle los datos y **recortar la semana en
curso** para la pantalla «Hoy».

**Y una cosa que si decide, y es de producto**: **si nadie ha puesto la
fecha del examen, no hay plan**. **No se inventa una fecha a seis meses
por defecto aqui**: **la pantalla pide la fecha, y el boton de «poner a
seis meses» es de la pantalla, no del servidor.** **Un plan que aparece
solo porque el servidor supuso una fecha es un plan que el alumno no
acordó.**
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime

from opofuente.domain.study_plan import Plan, Semana, planificar
from opofuente.infrastructure.plan_repository import (
    PlanGuardado,
    SqlAlchemyPlanRepository,
)


@dataclass(frozen=True, slots=True)
class Progreso:
    """Como va el alumno respecto al plan, **con la cifra delante**.

    **«Vas bien» no es «has hecho mucho»**: es «llevas lo que el plan pedia
    para esta altura». Por eso se compara con los temas que ya deberian
    estar leidos, no con el total.
    """

    leidos: int
    practicados: int
    #: Los que el plan daba por leidos a estas alturas.
    esperados: int
    total: int

    @property
    def vas_bien(self) -> bool:
        """Si lleva al menos los que tocaban. **Empatar cuenta como ir bien.**"""
        return self.leidos >= self.esperados

    @property
    def frase(self) -> str:
        """La frase entera, compuesta aqui y no en la pantalla."""
        if self.vas_bien:
            return (
                f"Vas bien: {self.leidos} temas leidos y {self.practicados} "
                f"practicados, y el plan pedia {self.esperados} a estas alturas."
            )
        return (
            f"Vas {self.esperados - self.leidos} temas por detras: {self.leidos} "
            f"leidos de los {self.esperados} que pedia el plan. No pasa nada: "
            "el plan se recoloca."
        )


@dataclass(frozen=True, slots=True)
class LoDeHoy:
    """La semana en curso del plan, **o por que no hay nada que enseñar**."""

    semana: Semana | None
    #: Los temas de la semana, con su enunciado, para los botones.
    motivos: tuple[str, ...]


class PlanService:
    """El plan de estudio: calcularlo, guardarlo y recortar el dia."""

    def __init__(self, planes: SqlAlchemyPlanRepository) -> None:
        self._planes = planes

    def guardado(self) -> PlanGuardado | None:
        """La fecha y las horas que puso el alumno, o `None` si no hay."""
        return self._planes.guardado()

    def guardar(
        self, *, exam_date: date, hours_per_week: int, rest_days: frozenset[int]
    ) -> PlanGuardado:
        """Pone la fecha del examen. **Es lo unico que hace falta para que haya plan.**"""
        return self._planes.guardar(
            exam_date=exam_date, hours_per_week=hours_per_week, rest_days=rest_days
        )

    def progreso(self, *, hoy: date | None = None) -> Progreso | None:
        """Como va respecto al plan, **o `None` si no hay plan que comparar**.

        **Lo esperado se cuenta por semanas**: cada semana de lectura del
        plan da por leidos los temas que tiene como tareas de `leer`. **No
        es una prediccion: es lo que el propio plan prometio para hoy.**
        """
        dia = hoy or datetime.now(UTC).date()
        plan = self.plan(hoy=dia)
        if plan is None:
            return None
        leidos, practicados = self._planes.leido_y_practicado()
        esperados = 0
        for semana in plan.semanas:
            if semana.empieza > dia:
                break
            esperados += sum(1 for tarea in semana.tareas if tarea.tipo.value == "leer")
        return Progreso(
            leidos=leidos,
            practicados=practicados,
            esperados=esperados,
            total=len(plan.dentro),
        )

    def plan(self, *, hoy: date | None = None) -> Plan | None:
        """El plan entero, **o `None` si el alumno no ha puesto la fecha**.

        **Se recalcula en cada llamada**: guardarlo seria guardar una
        derivacion, y la derivacion miente en cuanto cambia un tema.
        """
        guardado = self._planes.guardado()
        if guardado is None:
            return None
        temas = self._planes.temas()
        if not temas:
            return None
        return planificar(
            temas,
            hoy=hoy or datetime.now(UTC).date(),
            fecha_examen=guardado.exam_date,
            horas_por_semana=guardado.hours_per_week,
            dias_de_descanso=guardado.rest_days,
        )

    def hoy(self, *, hoy: date | None = None) -> LoDeHoy:
        """Las tareas de la semana en curso, **que es lo que enseña «Hoy»**.

        **Si la semana no esta en el plan** —porque el examen ya paso o
        porque el plan empieza mas adelante—, **se devuelve vacio con su
        motivo**: una pantalla en blanco sin explicacion es peor que una
        frase.
        """
        dia = hoy or datetime.now(UTC).date()
        plan = self.plan(hoy=dia)
        if plan is None:
            return LoDeHoy(semana=None, motivos=("pon la fecha del examen para tener un plan",))
        actual = next(
            (
                semana
                for semana in plan.semanas
                if semana.empieza <= dia < _siguiente(semana.empieza)
            ),
            None,
        )
        if actual is None:
            if plan.fuera:
                return LoDeHoy(
                    semana=None,
                    motivos=(
                        "el examen esta demasiado cerca para cubrir todo: "
                        f"{len(plan.fuera)} temas se quedan fuera",
                    ),
                )
            return LoDeHoy(semana=None, motivos=("el plan no tiene tareas para hoy",))
        return LoDeHoy(semana=actual, motivos=())


def _siguiente(dia: date) -> date:
    """El dia siguiente, con `date` y sin `timedelta` a mano en cada uso."""
    from datetime import timedelta

    return dia + timedelta(days=7)
