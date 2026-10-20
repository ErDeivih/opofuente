"""El repaso espaciado, escrito en el dominio y sin dependencias nuevas (M3 de la fase 3).

**Por qué SM-2 y no FSRS.** El §3 del hito dice: «usa la biblioteca de código abierto si su
licencia lo permite: verifícala y apúntalo; si no, SM-2 escrito en el dominio». **Aquí se
eligió SM-2, y el motivo no es la licencia: es que añadir una dependencia nueva es una decisión
del arquitecto, no de quien escribe el hito** (es la primera regla de `AGENTS.md`). **SM-2 es un
algoritmo publicado, pequeño y comprobable, y no compra nada que no se pueda escribir aquí.**

**Lo que se guarda por tarjeta**: el **factor de facilidad** (cuánto crece el intervalo cuando se acierta),
**el intervalo en días** y **cuántas veces seguidas se ha acertado**. **Nada más**: el historial de
respuestas se guarda aparte, porque es lo que se mira al revisar y no lo que decide la fecha.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

#: El factor de facilidad no baja de aquí, o una tarjeta difícil no se volvería a ver nunca.
FACTOR_MINIMO = 1.3
#: El de partida, el que fija el artículo de SM-2.
FACTOR_INICIAL = 2.5
#: Los dos primeros intervalos, en días. A partir del tercero, el intervalo por el factor.
PRIMER_INTERVALO = 1
SEGUNDO_INTERVALO = 6


class Respuesta(StrEnum):
    """Las cuatro respuestas de la pantalla, que es lo que el alumno puede decir."""

    OTRA_VEZ = "otra_vez"
    DIFICIL = "dificil"
    BIEN = "bien"
    FACIL = "facil"


#: La nota de SM-2 (0 a 5) que corresponde a cada respuesta. Otra vez y Difícil suspenden.
_NOTA = {
    Respuesta.OTRA_VEZ: 0,
    Respuesta.DIFICIL: 3,
    Respuesta.BIEN: 4,
    Respuesta.FACIL: 5,
}


@dataclass(frozen=True, slots=True)
class EstadoDeRepaso:
    """Lo que se guarda por tarjeta para saber cuándo vuelve."""

    factor: float = FACTOR_INICIAL
    intervalo_dias: int = 0
    aciertos_seguidos: int = 0


def _factor(nuevo: float, nota: int) -> float:
    """La fórmula del artículo: el factor sube al acertar fácil y baja al fallar."""
    ajuste = 0.1 - (5 - nota) * (0.08 + (5 - nota) * 0.02)
    return max(FACTOR_MINIMO, nuevo + ajuste)


def repasar(estado: EstadoDeRepaso, respuesta: Respuesta) -> EstadoDeRepaso:
    """El estado siguiente. **Suspender vuelve a empezar**: no se castiga más que reiniciar.

    Es la decisión de SM-2 y es la correcta para estudiar: **una tarjeta que se falla no se entierra**,
    vuelve al día siguiente y se recupera con dos aciertos.
    """
    nota = _NOTA[respuesta]
    factor = _factor(estado.factor, nota)
    if nota < 3:
        return EstadoDeRepaso(factor=factor, intervalo_dias=PRIMER_INTERVALO, aciertos_seguidos=0)
    aciertos = estado.aciertos_seguidos + 1
    if aciertos == 1:
        intervalo = PRIMER_INTERVALO
    elif aciertos == 2:
        intervalo = SEGUNDO_INTERVALO
    else:
        intervalo = max(1, round(estado.intervalo_dias * factor))
    return EstadoDeRepaso(
        factor=factor,
        intervalo_dias=intervalo,
        aciertos_seguidos=aciertos,
    )
