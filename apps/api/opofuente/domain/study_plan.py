"""El planificador del estudio: reparte los temas antes del examen (M4, O4).

**Es determinista a proposito**: **el plan se ve en una pantalla y se compara con el de la semana
pasada**, asi que dos ejecuciones con los mismos datos dan lo mismo. **Nada de aleatorio, nada de
`now()` por dentro**: la fecha de hoy entra por parametro.

**Lo que reparte**: los temas, por su peso (preguntas de cada uno) y por lo flojo que va.
**El modo sale de los datos, no de una columna**: con un tema por semana el plan es `extensivo`; con
dos, `intensivo`; si ni con dos caben, el plan sigue existiendo pero se declara **no planificable** y
nombra los temas que se quedan fuera. No hay migracion ni campo que pueda contradecir al calculo.

**Lo que reserva**: **la fase 2 ocupa como mucho las CUATRO ultimas semanas** (supuesto practico
semanal y un simulacro completo en la ultima), pero **nunca se come el plan**: siempre quedan al
menos tres semanas de lectura mientras haya calendario para ellas, y con una semana o menos no se
programa simulacro (los temas se reparten igual). **Los repasos** caen a +1, +3 y +7 semanas **solo
si caben en las horas declaradas**; si no, se recortan y la semana lo dice. **El trabajo obligatorio
no se recorta en silencio**: leer dos temas o cerrar con supuesto y simulacro puede pedir mas minutos
de los declarados (el examen dura lo que dura), asi que la semana lo avisa en `recortes` en vez de
esconderlo o de acortar la tarea sin decirlo.

**No usa el modelo**: este fichero no llama a nadie. Los minutos por tarea son una estimacion
declarada, no una medida del alumno.
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
    SUPUESTO = "supuesto"
    SIMULACRO = "simulacro"


class ModoDeEstudio(StrEnum):
    """El ritmo que pide el calendario, **derivado de temas pendientes y semanas de lectura**."""

    EXTENSIVO = "extensivo"
    INTENSIVO = "intensivo"


#: Los minutos que se suponen a un tema leido entero. **Declarado, no medido.**
MINUTOS_POR_TEMA = 150
#: Un test semanal para no leer sin contestar.
MINUTOS_TEST = 20
#: Un repaso espaciado.
MINUTOS_REPASO = 30
#: Un supuesto practico de la fase 2.
MINUTOS_SUPUESTO = 90
#: El simulacro completo que cierra el plan.
MINUTOS_SIMULACRO = 120
#: A que semanas del tema leido se repasa.
INTERVALOS_REPASO = (1, 3, 7)
#: Cuantas semanas finales ocupa la fase 2 como maximo.
FASE_2_SEMANAS = 4
#: Las semanas de lectura que no se sacrifican a la fase 2 si el calendario las permite.
SEMANAS_DE_LECTURA_MINIMAS = 3


@dataclass(frozen=True, slots=True)
class TemaDelPlan:
    """Un tema con lo que el planificador necesita saber de el, y nada mas."""

    codigo: str
    titulo: str
    #: Cuantas preguntas tiene: el peso con el que se reparte.
    preguntas: int
    #: Si el alumno va flojo en el. **Lo decide quien llama**, con su criterio.
    flojo: bool = False
    #: El bloque del programa al que pertenece, para el progreso por bloque.
    bloque_codigo: str = ""
    bloque_titulo: str = ""


@dataclass(frozen=True, slots=True)
class Tarea:
    """Una cosa concreta que hacer, con su tipo y lo que cuesta."""

    tipo: TipoDeTarea
    #: El tema al que pertenece, o `None` en supuestos y simulacros.
    codigo: str | None
    titulo: str
    minutos: int
    bloque_codigo: str | None = None
    bloque_titulo: str | None = None


@dataclass(frozen=True, slots=True)
class Semana:
    """Una semana del plan: su numero, su fase y sus tareas."""

    numero: int
    #: El lunes de esa semana.
    empieza: date
    tareas: tuple[Tarea, ...]
    #: `lectura` o `fase-2`; la pantalla lo usa para agrupar sin recalcular.
    fase: str = "lectura"
    #: Lo que se ha quitado o lo que no cabe en las horas declaradas, dicho en palabras.
    recortes: tuple[str, ...] = ()

    @property
    def minutos(self) -> int:
        return sum(tarea.minutos for tarea in self.tareas)


@dataclass(frozen=True, slots=True)
class Derivacion:
    """El modo que sale de los numeros, y si con ese ritmo cabe todo."""

    modo: ModoDeEstudio
    temas_por_semana: int
    planificable: bool
    motivo: str | None = None


@dataclass(frozen=True, slots=True)
class Plan:
    """El plan entero, **con lo que no cabe dicho en voz alta**."""

    semanas: tuple[Semana, ...]
    #: Los temas que no entran antes del examen, **por su codigo**. Vacio si caben todos.
    fuera: tuple[str, ...]
    #: Los temas que se quedan hasta la ultima semana de lectura.
    dentro: tuple[str, ...]
    #: Los mismos temas de `fuera`, con titulo y bloque para poder nombrarlos.
    fuera_detalle: tuple[TemaDelPlan, ...] = ()
    modo: ModoDeEstudio = ModoDeEstudio.EXTENSIVO
    temas_por_semana: int = 1
    planificable: bool = True
    motivo: str | None = None
    total_semanas: int = 0
    semanas_de_lectura: int = 0
    fase_2_desde: int | None = None

    @property
    def cabe_todo(self) -> bool:
        return not self.fuera


def derivar_modo(temas_pendientes: int, semanas_de_lectura: int) -> Derivacion:
    """Deriva el ritmo y declara si es posible.

    **Un tema por semana es extensivo y dos es intensivo.** Si ni con dos caben, el plan no se
    rechaza: se marca `planificable=False` con un motivo, y los temas sobrantes se nombran en
    `fuera_detalle`. **Sin semanas de lectura no se puede prometer nada**, salvo que no queden temas.
    """
    if temas_pendientes <= 0:
        return Derivacion(ModoDeEstudio.EXTENSIVO, 1, True, None)
    if semanas_de_lectura <= 0:
        return Derivacion(
            ModoDeEstudio.INTENSIVO,
            2,
            False,
            "No queda ninguna semana de lectura antes del examen: los temas pendientes no caben.",
        )
    if temas_pendientes <= semanas_de_lectura:
        return Derivacion(ModoDeEstudio.EXTENSIVO, 1, True, None)
    if temas_pendientes <= semanas_de_lectura * 2:
        return Derivacion(ModoDeEstudio.INTENSIVO, 2, True, None)
    return Derivacion(
        ModoDeEstudio.INTENSIVO,
        2,
        False,
        (
            f"{temas_pendientes} temas pendientes no caben en {semanas_de_lectura} semanas "
            "ni a dos temas por semana."
        ),
    )


def _dias_de_estudio(descanso: frozenset[int]) -> int:
    """Los dias que se estudia en una semana, quitando los de descanso."""
    return max(len([dia for dia in range(7) if dia not in descanso]), 1)


def _semanas_de_fase_2(total_semanas: int) -> int:
    """Cuantas de las ultimas semanas se dedican a la fase 2.

    **La fase 2 no se come el plan**: se queda con lo que sobra despues de reservar
    `SEMANAS_DE_LECTURA_MINIMAS` semanas de lectura, con un maximo de `FASE_2_SEMANAS`.
    Con cuatro semanas eso deja tres de lectura y una de fase 2; con dos o tres, una de
    fase 2 y el resto de lectura; con una o ninguna, **no hay fase 2**: se lee y no se
    inventa un simulacro que el calendario no da.
    """
    if total_semanas < 2:
        return 0
    return min(FASE_2_SEMANAS, max(1, total_semanas - SEMANAS_DE_LECTURA_MINIMAS))


def _orden(tema: TemaDelPlan) -> tuple[bool, int, str]:
    """Flojos primero, luego los de mas preguntas, y despues por codigo."""
    return (not tema.flojo, -tema.preguntas, tema.codigo)


def _tarea_de_leer(tema: TemaDelPlan) -> Tarea:
    return Tarea(
        tipo=TipoDeTarea.LEER,
        codigo=tema.codigo,
        titulo=f"Lee {tema.codigo}: {tema.titulo}",
        minutos=MINUTOS_POR_TEMA,
        bloque_codigo=tema.bloque_codigo or None,
        bloque_titulo=tema.bloque_titulo or None,
    )


def _tarea_de_test(tema: TemaDelPlan) -> Tarea:
    return Tarea(
        tipo=TipoDeTarea.TEST,
        codigo=tema.codigo,
        titulo=f"Test de {min(20, max(tema.preguntas, 5))} de {tema.codigo}",
        minutos=MINUTOS_TEST,
        bloque_codigo=tema.bloque_codigo or None,
        bloque_titulo=tema.bloque_titulo or None,
    )


def _tarea_de_repaso(tema: TemaDelPlan) -> Tarea:
    return Tarea(
        tipo=TipoDeTarea.REPASO,
        codigo=tema.codigo,
        titulo=f"Repaso de {tema.codigo}: {tema.titulo}",
        minutos=MINUTOS_REPASO,
        bloque_codigo=tema.bloque_codigo or None,
        bloque_titulo=tema.bloque_titulo or None,
    )


def _aviso_de_horas(minutos_pedidos: int, horas_por_semana: int, minutos_por_semana: int) -> str:
    """Lo que la semana pide por encima de lo declarado, **sin quitar trabajo obligatorio**."""
    return (
        f"La semana pide {minutos_pedidos} min y has declarado {horas_por_semana} h "
        f"({minutos_por_semana} min): sobran {minutos_pedidos - minutos_por_semana} min. "
        "El plan no quita las tareas obligatorias: amplia las horas o reparte el ritmo."
    )


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
    preguntas, y despues el resto por codigo. **Un tema flojo y con peso alto va antes**:
    el examen pesa lo que pesa, y lo que se falla cuenta doble.

    **La fase 2 no se come el plan**: se reserva como mucho las cuatro ultimas semanas,
    pero solo despues de dejar tres de lectura; con una semana o menos se lee hasta el
    final, sin simulacro. Asi un calendario de cuatro semanas se reparte en tres de
    lectura y una de fase 2, y los temas pendientes no se declaran fuera por la reserva.
    """
    if fecha_examen <= hoy:
        return Plan(
            semanas=(),
            fuera=tuple(tema.codigo for tema in temas),
            dentro=(),
            fuera_detalle=tuple(sorted(temas, key=_orden)),
            planificable=False,
            motivo="La fecha del examen ya ha pasado: no hay semanas que repartir.",
        )

    dias = (fecha_examen - hoy).days
    total_semanas = dias // 7
    fase_2 = _semanas_de_fase_2(total_semanas)
    semanas_lectura = total_semanas - fase_2
    derivacion = derivar_modo(len(temas), semanas_lectura)

    semanas_por_semana = derivacion.temas_por_semana
    capacidad = semanas_lectura * semanas_por_semana
    ordenados = sorted(temas, key=_orden)
    dentro = ordenados[:capacidad]
    fuera = ordenados[capacidad:]

    minutos_por_semana = horas_por_semana * 60
    dias_de_estudio = _dias_de_estudio(dias_de_descanso)

    # **Los repasos se deciden antes de pintar las semanas**: cada tema leido genera
    # tres citas, y solo se conservan las que caben en la semana de destino.
    repasos: dict[int, list[Tarea]] = {}
    # Los que se quedan fuera de la fase de lectura no desaparecen en silencio: se
    # nombran en la semana en la que se leyo el tema para que el hueco se vea.
    recortes_por_fase: dict[int, list[tuple[str, int]]] = {}
    for indice, tema in enumerate(dentro):
        semana_de_lectura = (indice // semanas_por_semana) + 1 if semanas_por_semana else 0
        for intervalo in INTERVALOS_REPASO:
            destino = semana_de_lectura + intervalo
            if destino <= semanas_lectura:
                repasos.setdefault(destino, []).append(_tarea_de_repaso(tema))
            else:
                recortes_por_fase.setdefault(semana_de_lectura, []).append((tema.codigo, intervalo))

    lunes = hoy - timedelta(days=hoy.weekday())
    semanas: list[Semana] = []
    for numero in range(1, total_semanas + 1):
        if numero <= semanas_lectura:
            inicio = (numero - 1) * semanas_por_semana
            del_semana = dentro[inicio : inicio + semanas_por_semana]
            tareas: list[Tarea] = [_tarea_de_leer(tema) for tema in del_semana]
            if del_semana:
                # **Un test por semana del tema mas flojo de los leidos**: leer sin
                # contestar no fija nada.
                flojo = next((tema for tema in del_semana if tema.flojo), del_semana[0])
                tareas.append(_tarea_de_test(flojo))
            gastado = sum(tarea.minutos for tarea in tareas)
            recortes: list[str] = []
            # **El modo intensivo puede pedir mas de lo declarado**: dos temas y su test son
            # 320 min. El plan no borra temas para cuadrar la cifra; lo dice y deja decidir.
            if gastado > minutos_por_semana:
                recortes.append(_aviso_de_horas(gastado, horas_por_semana, minutos_por_semana))
            fuera_por_fase = recortes_por_fase.get(numero, [])
            if fuera_por_fase:
                detalle = ", ".join(
                    f"{codigo} (+{intervalo})" for codigo, intervalo in fuera_por_fase
                )
                if fase_2:
                    recortes.append(
                        "Repasos no programados por el limite de fase: "
                        f"{detalle} caen en la fase 2, que se dedica a supuestos y simulacro."
                    )
                else:
                    recortes.append(
                        "Repasos no programados por el limite del calendario: "
                        f"{detalle} no caben antes del examen."
                    )
            quitados = 0
            for repaso in repasos.get(numero, []):
                if gastado + repaso.minutos <= minutos_por_semana:
                    tareas.append(repaso)
                    gastado += repaso.minutos
                else:
                    quitados += 1
            if quitados:
                recortes.append(
                    f"Se quitaron {quitados} repasos de {MINUTOS_REPASO} min para no pasar "
                    f"de las {horas_por_semana} h semanales en tus {dias_de_estudio} dias "
                    "de estudio."
                )
            if numero == total_semanas and not fase_2:
                # **Lo que no cabe es el simulacro, no los temas**: con una semana o menos
                # no hay fase 2, pero el poco calendario que queda se dedica a leer.
                recortes.append(
                    "No se planifica simulacro: con una semana o menos no hay fase 2. "
                    "Los temas pendientes no se descartan por ello; se reparten en la "
                    "semana que queda."
                )
            semanas.append(
                Semana(
                    numero=numero,
                    empieza=lunes,
                    tareas=tuple(tareas),
                    fase="lectura",
                    recortes=tuple(recortes),
                )
            )
        else:
            # **Los minutos son la duracion declarada de la tarea, no un hueco en la semana**:
            # acortar el simulacro a lo que sobra lo volveria otro examen. Si no cabe, se avisa.
            tareas = [
                Tarea(
                    tipo=TipoDeTarea.SUPUESTO,
                    codigo=None,
                    titulo="Supuesto practico de la semana",
                    minutos=MINUTOS_SUPUESTO,
                )
            ]
            if numero == total_semanas:
                tareas.append(
                    Tarea(
                        tipo=TipoDeTarea.SIMULACRO,
                        codigo=None,
                        titulo="Simulacro completo",
                        minutos=MINUTOS_SIMULACRO,
                    )
                )
            recortes: list[str] = []
            gastado = sum(tarea.minutos for tarea in tareas)
            if gastado > minutos_por_semana:
                recortes.append(_aviso_de_horas(gastado, horas_por_semana, minutos_por_semana))
            semanas.append(
                Semana(
                    numero=numero,
                    empieza=lunes,
                    tareas=tuple(tareas),
                    fase="fase-2",
                    recortes=tuple(recortes),
                )
            )
        lunes += timedelta(days=7)

    motivo = derivacion.motivo
    if fuera and motivo is None:
        motivo = (
            f"Se quedan fuera {len(fuera)} temas: el calendario da para "
            f"{len(dentro)} con el ritmo {derivacion.modo.value}."
        )

    return Plan(
        semanas=tuple(semanas),
        fuera=tuple(tema.codigo for tema in fuera),
        dentro=tuple(tema.codigo for tema in dentro),
        fuera_detalle=tuple(fuera),
        modo=derivacion.modo,
        temas_por_semana=semanas_por_semana,
        planificable=derivacion.planificable,
        motivo=motivo,
        total_semanas=total_semanas,
        semanas_de_lectura=semanas_lectura,
        fase_2_desde=(semanas_lectura + 1) if fase_2 else None,
    )
