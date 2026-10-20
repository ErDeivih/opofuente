"""Una sola cola para el día: tarjetas vencidas y fallos vencidos, mezclados (M3).

El §3 del hito pide **una sola cola diaria** —no dos pantallas, no dos horarios— porque lo que
el alumno tiene que hacer hoy es una lista y no dos. Y pide **un tope configurable** (60 por
defecto), porque una lista de cuatrocientas tarjetas no se empieza.

**La mezcla es alterna y tiene motivo**: si primero van todas las tarjetas y después todos los
fallos, el alumno que se cansa nunca llega a los fallos —que son **justo lo que más le cuesta**—.
Alternando, cada fallo aparece al principio de la lista y no al final.

**Y los dos tipos no se mezclan en la misma lista sin decirlo**: la cola dice de qué es cada
entrada, porque una tarjeta se responde con cuatro botones y un fallo se repasa de otra manera.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum


class TipoDeEntrada(StrEnum):
    """De qué es la entrada: una tarjeta del tema o un fallo de un test."""

    TARJETA = "tarjeta"
    FALLO = "fallo"


@dataclass(frozen=True, slots=True)
class EntradaDeLaCola:
    """Una cosa que hacer hoy. `id` es el de la tarjeta o el de la pregunta fallada."""

    tipo: TipoDeEntrada
    id: str


def _alterna(tarjetas: Sequence[str], fallos: Sequence[str]) -> tuple[EntradaDeLaCola, ...]:
    """Las dos listas entrelazadas: una tarjeta, un fallo, una tarjeta, un fallo."""
    salida: list[EntradaDeLaCola] = []
    i = j = 0
    while i < len(tarjetas) or j < len(fallos):
        if i < len(tarjetas):
            salida.append(EntradaDeLaCola(TipoDeEntrada.TARJETA, tarjetas[i]))
            i += 1
        if j < len(fallos):
            salida.append(EntradaDeLaCola(TipoDeEntrada.FALLO, fallos[j]))
            j += 1
    return tuple(salida)


def cola_del_dia(
    tarjetas: Sequence[str],
    fallos: Sequence[str],
    *,
    tope: int = 60,
) -> tuple[EntradaDeLaCola, ...]:
    """La cola del día: entrelazada y **cortada por el tope**.

    **El tope no recorta por la mitad de cada lista**: recorta **la cola ya mezclada**, así que
    si hay sesenta tarjetas y cinco fallos y el tope es sesenta, **los fallos siguen entrando**
    — van los primeros de la mezcla.
    """
    if tope <= 0:
        raise ValueError("el tope de la cola tiene que ser mayor que cero")
    return _alterna(tarjetas, fallos)[:tope]
