"""El planificador del estudio: reparte los temas antes del examen (M4).

**Es determinista a proposito**: **el plan se ve en una pantalla y se compara con el de la semana
pasada**, asi que dos ejecuciones con los mismos datos dan lo mismo. **Nada de aleatorio, nada de
`now()` por dentro**: la fecha de hoy entra por parametro.

**Lo que reparte**: los temas, por su peso (preguntas de cada uno) y por lo flojo que va.
**Lo que reserva**: **las DOS ULTIMAS semanas son para simulacros**, no para leer temas nuevos.
**Lo que dice cuando no cabe**: si el examen esta mas cerca que el trabajo, **no inventa un reparto
imposible: deja temas fuera y los nombra.**

**No usa el modelo**: este fichero no llama a nadie. Los minutos por tarea son una
estimacion declarada, no una medida del alumno, y se dice.
(`MINUTOS_POR_TEMA`), no una medida del alumno, y se dice.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from enum import StrEnum


class TipoDeTarea(StrEnum):
    """Que se hace en una tarea. **El tipo decide a que pantalla lleva el boton.**"""

    LEER = "leer"
    TEST = "test"
    REPASO = "repaso"
    SIMULACRO = "simulacro"


#: Los minutos que se suponen a un tema leido entero. **Declarado, no medido.**
MINUTOS_POR_TEMA = 150


@dataclass(frozen=True, slots=True)
class TemaDelPlan:
    """Un tema con lo que el planificador necesita saber de el, y nada mas."""

    codigo: str
    titulo: str
    #: Cuantas preguntas tiene: el peso con el que se reparte.
    preguntas: int
    #: Si el alumno va flojo en el. **Lo decide quien llama**, con su criterio.
    flojo: bool = False


@dataclass(frozen=True, slots=True)
class Tarea:
    """Una cosa concreta que hacer, con su tipo y lo que cuesta."""

    tipo: TipoDeTarea
    #: El tema al que pertenece, o `None` en un simulacro.
    codigo: str | None
    titulo: str
    minutos: int


@dataclass(frozen=True, slots=True)
class Semana:
    """Una semana del plan: su numero y sus tareas."""

    numero: int
    #: El lunes de esa semana.
    empieza: date
    tareas: tuple[Tarea, ...]

    @property
    def minutos(self) -> int:
        return sum(tarea.minutos for tarea in self.tareas)


@dataclass(frozen=True, slots=True)
class Plan:
    """El plan entero, **con lo que no cabe dicho en voz alta**."""

    semanas: tuple[Semana, ...]
    #: Los temas que no entran antes del examen, **por su codigo**. Vacio si caben todos.
    fuera: tuple[str, ...]
    #: Los temas que se quedan hasta la ultima semana de lectura.
    dentro: tuple[str, ...]

    @property
    def cabe_todo(self) -> bool:
        return not self.fuera


def _semanas_de_lectura(dias: int) -> int:
    """Cuantas semanas quedan para leer, **quitando las dos de simulacros**."""
    return max((dias // 7) - 2, 0)


def _dias_de_estudio(dias_semana: int, descanso: frozenset[int]) -> int:
    """Los dias que se estudia en una semana, quitando los de descanso."""
    return max(len([dia for dia in range(7) if dia not in descanso]), 1)


def planificar(
    temas: tuple[TemaDelPlan, ...],
    *,
    hoy: date,
    fecha_examen: date,
    horas_por_semana: int,
    dias_de_descanso: frozenset[int] = frozenset({6}),
) -> Plan:
    """Reparte los temas y devuelve el plan, **o el plan con lo que no cabe**.

    **El orden decide quien se queda fuera**: primero los flojos, luego los de mas
    preguntas, y despues el resto por codigo. **Un tema flojo y con peso alto va antes
    sabe**: el examen pesa lo que pesa, y lo que se falla cuenta doble.

    **`semanas_de_lectura` no incluye las dos ultimas**: esas son de simulacros, y
    si no queda ninguna, el plan solo tiene simulacros y lo dice.
    el plan solo tiene simulacros y lo dice.
    """
    if fecha_examen <= hoy:
        return Plan(semanas=(), fuera=tuple(tema.codigo for tema in temas), dentro=())

    dias = (fecha_examen - hoy).days
    semanas_lectura = _semanas_de_lectura(dias)
    dias_por_semana = _dias_de_estudio(7, dias_de_descanso)
    minutos_por_semana = horas_por_semana * 60

    # Cuantos temas caben: uno por dia de estudio de las semanas de lectura.
    capacidad = semanas_lectura * dias_por_semana
    ordenados = sorted(temas, key=lambda tema: (not tema.flojo, -tema.preguntas, tema.codigo))
    dentro = ordenados[:capacidad]
    fuera = tuple(tema.codigo for tema in ordenados[capacidad:])

    semanas: list[Semana] = []
    lunes = hoy - timedelta(days=hoy.weekday())
    indice = 0
    for numero in range(1, semanas_lectura + 1):
        tareas: list[Tarea] = []
        for dia in range(7):
            if dia in dias_de_descanso or indice >= len(dentro):
                continue
            tema = dentro[indice]
            indice += 1
            tareas.append(
                Tarea(
                    tipo=TipoDeTarea.LEER,
                    codigo=tema.codigo,
                    titulo=f"Lee {tema.codigo}: {tema.titulo}",
                    minutos=MINUTOS_POR_TEMA,
                )
            )
        if tareas:
            # **Un test por semana del tema mas flojo de los leidos**: leer sin
            # contestar no fija nada.
            flojo = next((t for t in dentro if t.flojo), dentro[0] if dentro else None)
            if flojo is not None:
                tareas.append(
                    Tarea(
                        tipo=TipoDeTarea.TEST,
                        codigo=flojo.codigo,
                        titulo=f"Test de {min(20, max(flojo.preguntas, 5))} de {flojo.codigo}",
                        minutos=20,
                    )
                )
            semanas.append(Semana(numero=numero, empieza=lunes, tareas=tuple(tareas)))
        lunes += timedelta(days=7)

    # **Las dos ultimas, a simulacros**, aunque el alumno vaya sobrado.
    for extra in (1, 2):
        semanas.append(
            Semana(
                numero=semanas_lectura + extra,
                empieza=lunes,
                tareas=(
                    Tarea(
                        tipo=TipoDeTarea.SIMULACRO,
                        codigo=None,
                        titulo="Simulacro corto" if extra == 1 else "Simulacro completo",
                        minutos=min(60 * extra, minutos_por_semana),
                    ),
                ),
            )
        )
        lunes += timedelta(days=7)

    return Plan(
        semanas=tuple(semanas),
        fuera=fuera,
        dentro=tuple(tema.codigo for tema in dentro),
    )
