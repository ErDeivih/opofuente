"""Las rutas del plan de estudio y de «Hoy» (M4, O4).

**Cuatro rutas de lectura y una de escritura**: leer lo guardado, leer el
calendario derivado, ponerlo, y leer lo de hoy o el progreso. **La de hoy y
la del calendario son vistas del plan, no datos aparte**: se calculan con la
misma funcion, para que no puedan decir cosas distintas. **La pantalla `/plan`
solo lee**: editar sigue siendo el `PUT` de siempre.
"""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter
from pydantic import BaseModel, Field

from opofuente.api.deps import PlanServiceDep
from opofuente.api.error_responses import RESOURCE_ERRORS
from opofuente.domain.errors import NotFoundError
from opofuente.domain.study_plan import Plan, Semana, Tarea, TemaDelPlan

router = APIRouter(tags=["plan"])


class TareaSchema(BaseModel):
    """Una tarea con su boton: el tipo dice a que pantalla lleva."""

    tipo: str
    codigo: str | None = None
    titulo: str
    minutos: int
    bloque_codigo: str | None = None
    bloque_titulo: str | None = None


class SemanaSchema(BaseModel):
    numero: int
    empieza: date
    tareas: list[TareaSchema]
    #: `lectura` o `fase-2`.
    fase: str = "lectura"
    #: Lo que no se pudo programar o no cabe en las horas, y por que.
    recortes: list[str] = Field(default_factory=list)


class TemaFueraSchema(BaseModel):
    """Un tema que no entra, **con nombre**: un codigo solo no dice nada."""

    codigo: str
    titulo: str
    bloque_codigo: str = ""
    bloque_titulo: str = ""


class PlanSchema(BaseModel):
    """El plan entero, **con lo que no cabe dicho**."""

    semanas: list[SemanaSchema]
    fuera: list[str] = Field(description="Los temas que no entran antes del examen")
    dentro: list[str]
    cabe_todo: bool
    fuera_temas: list[TemaFueraSchema] = Field(default_factory=list)
    #: `extensivo` o `intensivo`, derivado de temas y semanas.
    modo: str = "extensivo"
    temas_por_semana: int = 1
    planificable: bool = True
    motivo: str | None = None
    total_semanas: int = 0
    semanas_de_lectura: int = 0
    fase_2_desde: int | None = None


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
    #: El ritmo derivado, para no recalcularlo en el navegador.
    modo: str | None = None
    planificable: bool = True
    motivo: str | None = None
    fuera_temas: list[TemaFueraSchema] = Field(default_factory=list)


class ProgresoDeBloqueSchema(BaseModel):
    """El avance de un bloque, **con el umbral decidido en el servidor**."""

    codigo: str
    titulo: str
    leidos: int
    practicados: int
    esperados: int
    total: int
    vas_bien: bool
    frase: str


class ProgresoSchema(BaseModel):
    """Como va el alumno respecto al plan, con la frase ya compuesta."""

    leidos: int
    practicados: int
    esperados: int
    total: int
    vas_bien: bool
    frase: str
    bloques: list[ProgresoDeBloqueSchema] = Field(default_factory=list)


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
        bloque_codigo=tarea.bloque_codigo,
        bloque_titulo=tarea.bloque_titulo,
    )


def _semana(semana: Semana) -> SemanaSchema:
    return SemanaSchema(
        numero=semana.numero,
        empieza=semana.empieza,
        tareas=[_tarea(tarea) for tarea in semana.tareas],
        fase=semana.fase,
        recortes=list(semana.recortes),
    )


def _tema_fuera(tema: TemaDelPlan) -> TemaFueraSchema:
    return TemaFueraSchema(
        codigo=tema.codigo,
        titulo=tema.titulo,
        bloque_codigo=tema.bloque_codigo,
        bloque_titulo=tema.bloque_titulo,
    )


def _plan(plan: Plan) -> PlanSchema:
    return PlanSchema(
        semanas=[_semana(semana) for semana in plan.semanas],
        fuera=list(plan.fuera),
        dentro=list(plan.dentro),
        cabe_todo=plan.cabe_todo,
        fuera_temas=[_tema_fuera(tema) for tema in plan.fuera_detalle],
        modo=plan.modo.value,
        temas_por_semana=plan.temas_por_semana,
        planificable=plan.planificable,
        motivo=plan.motivo,
        total_semanas=plan.total_semanas,
        semanas_de_lectura=plan.semanas_de_lectura,
        fase_2_desde=plan.fase_2_desde,
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


@router.get(
    "/plan/calendario",
    response_model=PlanSchema,
    responses=RESOURCE_ERRORS,
    summary="El calendario derivado, en solo lectura (O4)",
)
def leer_calendario(service: PlanServiceDep) -> PlanSchema:
    """El plan calculado con lo guardado, **sin escribir nada**.

    Existe para que `/plan` pueda enseñar el calendario al volver a entrar:
    **la pantalla no inventa ni guarda una derivacion**, la pide. Editar sigue
    siendo el `PUT /plan` de siempre.
    """
    plan = service.plan()
    if plan is None:
        raise NotFoundError("plan", "calendario")
    return _plan(plan)


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
        bloques=[
            ProgresoDeBloqueSchema(
                codigo=bloque.codigo,
                titulo=bloque.titulo,
                leidos=bloque.leidos,
                practicados=bloque.practicados,
                esperados=bloque.esperados,
                total=bloque.total,
                vas_bien=bloque.vas_bien,
                frase=bloque.frase,
            )
            for bloque in avance.bloques
        ],
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
    lo_de_hoy = service.hoy()
    return HoySchema(
        semana=None if lo_de_hoy.semana is None else _semana(lo_de_hoy.semana),
        motivos=list(lo_de_hoy.motivos),
        modo=None if lo_de_hoy.modo is None else lo_de_hoy.modo.value,
        planificable=lo_de_hoy.planificable,
        motivo=lo_de_hoy.motivo,
        fuera_temas=[_tema_fuera(tema) for tema in lo_de_hoy.fuera_detalle],
    )
