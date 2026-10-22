"""Las rutas del plan de estudio y de «Hoy» (M4).

**Tres rutas**: leer el plan, ponerlo y leer lo de hoy. **La de hoy es una
vista del plan, no un dato aparte**: se calcula con la misma llamada y se
recorta a la semana en curso, para que no puedan decir cosas distintas.
"""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter
from pydantic import BaseModel, Field

from opofuente.api.deps import PlanServiceDep
from opofuente.api.error_responses import RESOURCE_ERRORS
from opofuente.application.plan_service import LoDeHoy
from opofuente.domain.errors import NotFoundError
from opofuente.domain.study_plan import Plan, Semana, Tarea

router = APIRouter(tags=["plan"])


class TareaSchema(BaseModel):
    """Una tarea con su boton: el tipo dice a que pantalla lleva."""

    tipo: str
    codigo: str | None = None
    titulo: str
    minutos: int


class SemanaSchema(BaseModel):
    numero: int
    empieza: date
    tareas: list[TareaSchema]


class PlanSchema(BaseModel):
    """El plan entero, **con lo que no cabe dicho**."""

    semanas: list[SemanaSchema]
    fuera: list[str] = Field(description="Los temas que no entran antes del examen")
    dentro: list[str]
    cabe_todo: bool


class GuardarPlanSchema(BaseModel):
    """Lo que decide el alumno: la fecha, las horas y los descansos."""

    exam_date: date
    hours_per_week: int = Field(ge=1, le=80)
    #: Los dias de descanso, de 0 (lunes) a 6 (domingo).
    rest_days: list[int] = Field(default_factory=lambda: [6])


class HoySchema(BaseModel):
    """La semana en curso, **o el motivo de que no haya nada**."""

    semana: SemanaSchema | None = None
    motivos: list[str]


class ProgresoSchema(BaseModel):
    """Como va el alumno respecto al plan, con la frase ya compuesta."""

    leidos: int
    practicados: int
    esperados: int
    total: int
    vas_bien: bool
    frase: str


class PlanGuardadoSchema(BaseModel):
    """Lo que hay guardado, o `null` si nadie ha puesto la fecha."""

    exam_date: date | None = None
    hours_per_week: int | None = None
    rest_days: list[int] = Field(default_factory=list)


def _tarea(tarea: Tarea) -> TareaSchema:
    return TareaSchema(
        tipo=tarea.tipo.value,
        codigo=tarea.codigo,
        titulo=tarea.titulo,
        minutos=tarea.minutos,
    )


def _semana(semana: Semana) -> SemanaSchema:
    return SemanaSchema(
        numero=semana.numero,
        empieza=semana.empieza,
        tareas=[_tarea(tarea) for tarea in semana.tareas],
    )


def _plan(plan: Plan) -> PlanSchema:
    return PlanSchema(
        semanas=[_semana(semana) for semana in plan.semanas],
        fuera=list(plan.fuera),
        dentro=list(plan.dentro),
        cabe_todo=plan.cabe_todo,
    )


@router.get(
    "/plan",
    response_model=PlanGuardadoSchema,
    summary="Lo que hay guardado del plan (M4)",
)
def leer_guardado(service: PlanServiceDep) -> PlanGuardadoSchema:
    """La fecha y las horas, **o `null` si no hay plan**. No calcula nada."""
    guardado = service.guardado()
    if guardado is None:
        return PlanGuardadoSchema()
    return PlanGuardadoSchema(
        exam_date=guardado.exam_date,
        hours_per_week=guardado.hours_per_week,
        rest_days=sorted(guardado.rest_days),
    )


@router.put(
    "/plan",
    response_model=PlanSchema,
    responses=RESOURCE_ERRORS,
    summary="Pone la fecha del examen y devuelve el plan (M4)",
)
def guardar_plan(cuerpo: GuardarPlanSchema, service: PlanServiceDep) -> PlanSchema:
    """Guarda la fecha y **devuelve el plan calculado**, que es lo que la
    pantalla necesita para pintarlo sin pedirlo otra vez.

    **404 si no hay temas que repartir**: un plan vacio no es un plan.
    """
    service.guardar(
        exam_date=cuerpo.exam_date,
        hours_per_week=cuerpo.hours_per_week,
        rest_days=frozenset(cuerpo.rest_days),
    )
    plan = service.plan()
    if plan is None:
        raise NotFoundError("temas que repartir", "plan")
    return _plan(plan)


@router.get(
    "/plan/progreso",
    response_model=ProgresoSchema,
    responses=RESOURCE_ERRORS,
    summary="Vas bien o vas retrasado, con la cifra (M4)",
)
def progreso(service: PlanServiceDep) -> ProgresoSchema:
    """Los temas leidos y practicados **frente a los que el plan pedia**.

    **404 si no hay plan**: sin fecha no hay con que comparar, y decir «vas
    bien» sin plan seria mentir.
    """
    avance = service.progreso()
    if avance is None:
        raise NotFoundError("plan", "progreso")
    return ProgresoSchema(
        leidos=avance.leidos,
        practicados=avance.practicados,
        esperados=avance.esperados,
        total=avance.total,
        vas_bien=avance.vas_bien,
        frase=avance.frase,
    )


@router.get(
    "/plan/hoy",
    response_model=HoySchema,
    summary="Lo que toca hoy, recortado de la semana en curso (M4)",
)
def plan_de_hoy(service: PlanServiceDep) -> HoySchema:
    """Las tareas de esta semana, **o el motivo de que no haya ninguna**."""
    if service.guardado() is None:
        return HoySchema(semana=None, motivos=["pon la fecha del examen para tener un plan"])
    plan = service.plan()
    if plan is None:
        return HoySchema(semana=None, motivos=["no hay temas con preguntas que repartir"])
    lo_de_hoy = _recortar(plan, service)
    return HoySchema(
        semana=None if lo_de_hoy.semana is None else _semana(lo_de_hoy.semana),
        motivos=list(lo_de_hoy.motivos),
    )


def _recortar(plan: Plan, service: PlanServiceDep) -> LoDeHoy:
    """El recorte del dia, **con el mismo criterio que el servicio**."""
    return service.hoy()
