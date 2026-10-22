"""El servicio de estadisticas: junta las tres consultas con la nota (M6).

**Lo que hace y lo que no**: lee los temas flojos, el tiempo y las semanas,
**y calcula la nota con `estimar`**. **No escribe nada**: esta pantalla es
de solo lectura, y una estadistica que escribe en la base es una
estadistica que puede cambiar lo que mide.

**La nota sale de los ultimos intentos, ponderados por preguntas**: se
leen los `attempts` de las ultimas semanas y se pasan a `estimar`. **Con
menos de dos, la nota sale sin intervalo**, y la frase lo dice.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from opofuente.domain.estimate import Intento, NotaEstimada, estimar
from opofuente.infrastructure.stats_repository import (
    Estadisticas,
    SemanaDeAcierto,
    SqlAlchemyStatsRepository,
    TemaFlojo,
)

#: De donde salen los intentos que sostienen la nota: las ultimas seis
#: semanas, que es lo que el hito pide («los ultimos simulacros y tests»).
SEMANAS_PARA_LA_NOTA = 6


@dataclass(frozen=True, slots=True)
class Resumen:
    """Todo lo que la pantalla de progreso necesita, **y nada mas**."""

    nota: NotaEstimada | None
    flojos: tuple[TemaFlojo, ...]
    estadisticas: Estadisticas


class StatsService:
    """Las cifras de M6, calculadas y juntas."""

    def __init__(self, stats: SqlAlchemyStatsRepository) -> None:
        self._stats = stats

    def resumen(self, *, limite: int = 5) -> Resumen:
        """La nota con su intervalo, los flojos y las tres cifras."""
        flojos = self._stats.flojos(limite=limite)
        semanas = self._stats.semanas(cuantas=SEMANAS_PARA_LA_NOTA)
        intentos = tuple(
            Intento(
                aciertos=round(semana.acierto * _preguntas_de_la_semana(semana)),
                preguntas=max(_preguntas_de_la_semana(semana), 1),
            )
            for semana in semanas
        )
        return Resumen(
            nota=estimar(intentos),
            flojos=flojos,
            estadisticas=Estadisticas(
                flojos=flojos,
                segundos_por_pregunta=self._stats.tiempo_medio(),
                semanas=semanas,
            ),
        )


def _preguntas_de_la_semana(semana: SemanaDeAcierto) -> int:
    """Cuantas preguntas sostienen el acierto de una semana.

    **Se usa el numero de intentos**: cada intento es una pregunta
    contestada, y la proporcion de acierto ya viene calculada sobre ellos.
    **Redondear el acierto por el numero de intentos reconstruye los
    aciertos que hubo**, que es lo que `estimar` necesita.
    """
    return semana.intentos


def _semana_actual() -> str:
    """El lunes de esta semana, **en el formato que usa la consulta**."""
    hoy = datetime.now(UTC)
    return (hoy - timedelta(days=hoy.weekday())).strftime("%Y-%m-%d")


__all__ = ["Resumen", "StatsService", "TemaFlojo", "_semana_actual"]
