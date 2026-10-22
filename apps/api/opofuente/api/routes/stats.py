"""La ruta de las estadisticas del alumno (M6).

**Una ruta de lectura**: la nota con su intervalo, los temas flojos, el
tiempo y la evolucion. **No escribe nada** y **no acepta nada**: **una
estadistica que se puede cambiar no mide, se negocia.**

**Y responde vacia si no hay datos**: **`200` con las listas vacias y la
nota a `null`**, **no un `404`**: **un alumno nuevo tiene derecho a que la
pantalla le diga «aun no hay nada que medir»**, **y eso es un estado, no un
error.**
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from opofuente.api.deps import StatsServiceDep
from opofuente.application.stats_service import Resumen

router = APIRouter(tags=["estadisticas"])


class TemaFlojoSchema(BaseModel):
    codigo: str
    titulo: str
    intentos: int
    acierto: float
    frase: str


class SemanaSchema(BaseModel):
    empieza: str
    intentos: int
    acierto: float


class NotaSchema(BaseModel):
    """La nota **con su intervalo**, y el intervalo puede no estar."""

    nota: float
    minimo: float | None = None
    maximo: float | None = None
    intentos: int
    frase: str


class StatsSchema(BaseModel):
    nota: NotaSchema | None = None
    flojos: list[TemaFlojoSchema]
    semanas: list[SemanaSchema]
    segundos_por_pregunta: float | None = None
    #: La comparacion del tiempo ya escrita, **o `null` si no hay tiempo**.
    comparacion_del_tiempo: str | None = None


def _stats(resumen: Resumen) -> StatsSchema:
    nota = resumen.nota
    return StatsSchema(
        nota=(
            None
            if nota is None
            else NotaSchema(
                nota=nota.nota,
                minimo=nota.minimo,
                maximo=nota.maximo,
                intentos=nota.intentos,
                frase=nota.frase,
            )
        ),
        flojos=[
            TemaFlojoSchema(
                codigo=tema.codigo,
                titulo=tema.titulo,
                intentos=tema.intentos,
                acierto=tema.acierto,
                frase=tema.frase,
            )
            for tema in resumen.flojos
        ],
        semanas=[
            SemanaSchema(
                empieza=semana.empieza,
                intentos=semana.intentos,
                acierto=semana.acierto,
            )
            for semana in resumen.estadisticas.semanas
        ],
        segundos_por_pregunta=resumen.estadisticas.segundos_por_pregunta,
        comparacion_del_tiempo=resumen.estadisticas.comparacion_del_tiempo,
    )


@router.get(
    "/stats",
    response_model=StatsSchema,
    summary="Que estudiar, con la cifra: nota, flojos, tiempo y semanas (M6)",
)
def get_stats(service: StatsServiceDep) -> StatsSchema:
    """**Nada de frases sin cifra**: todo lo que sale de aqui lleva su número.

    **Y si no hay intentos**, la nota es `null` y las listas van vacías:
    **la pantalla lo dice con palabras**, no con ceros.
    """
    return _stats(service.resumen())
