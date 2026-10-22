"""La nota estimada del examen, con su intervalo (M6).

**Que es**: una nota en la escala del examen —**sobre 100, con 100
preguntas**— **calculada con los ultimos intentos**, ponderando cada tema
por sus preguntas. **Y un intervalo alrededor**, que se calcula con la
dispersion de esos intentos.

**Y la regla que hace que el intervalo no sea decorativo**: **si no hay
dispersion suficiente —un solo intento, o todos iguales—, el intervalo no
se devuelve**. **Una nota sola sin intervalo es una nota inventada**, y
ponerle `+-0` seria mentir con mas precision de la que hay.

**La escala, y por que es esta**: el examen son **80 preguntas de la
primera parte y 20 del supuesto, con 120 minutos**, y **cada error no
resta** —segun la convocatoria de TAI—. **Asi que la nota es
`aciertos / preguntas * 100`**, sin penalizacion. **Si algun dia la
convocatoria penaliza, se cambia aqui y se dice.**
"""

from __future__ import annotations

from dataclasses import dataclass

#: Preguntas del examen: es la base de la nota.
PREGUNTAS_DEL_EXAMEN = 100

#: La nota maxima y la minima, en la escala del examen.
NOTA_MAXIMA = 100.0

#: Con menos de dos intentos no hay dispersion y el intervalo no se da.
INTENTOS_MINIMOS_PARA_INTERVALO = 2


@dataclass(frozen=True, slots=True)
class Intento:
    """Un intento reciente: cuantas contesto bien y cuantas eran."""

    aciertos: int
    preguntas: int

    @property
    def acierto(self) -> float:
        """La proporcion de acierto, **entre 0 y 1**."""
        return self.aciertos / self.preguntas if self.preguntas > 0 else 0.0


@dataclass(frozen=True, slots=True)
class NotaEstimada:
    """La nota, su intervalo y **de cuantos intentos sale**."""

    nota: float
    #: Los extremos del intervalo, o `None` si no hay dispersion con la que
    #: calcularlo. **`None` no es un error: es «todavia no se puede decir».**
    minimo: float | None
    maximo: float | None
    intentos: int

    @property
    def hay_intervalo(self) -> bool:
        return self.minimo is not None and self.maximo is not None

    @property
    def frase(self) -> str:
        """La cifra con su intervalo, **compuesta aqui y no en la pantalla**."""
        if self.hay_intervalo:
            return (
                f"Nota estimada: {self.nota:.0f} de 100 "
                f"(entre {self.minimo:.0f} y {self.maximo:.0f}), "
                f"con {self.intentos} intentos."
            )
        return (
            f"Nota estimada: {self.nota:.0f} de 100, con {self.intentos} "
            "intentos. Con uno solo no se puede dar un margen."
        )


def estimar(
    intentos: tuple[Intento, ...], *, escala: int = PREGUNTAS_DEL_EXAMEN
) -> NotaEstimada | None:
    """La nota ponderada y su intervalo, **o `None` si no hay intentos**.

    **Se pondera por preguntas**: un intento de 20 preguntas no dice lo
    mismo que uno de 100, y promediar sin ponderar le daria el mismo peso
    al corto.

    **El intervalo sale de la desviacion tipica de la media**: con `n`
    intentos, el margen es `1,96 * desviacion / sqrt(n)`, que es el
    intervalo de confianza habitual. **Con dos intentos sale ancho, y eso
    es correcto**: con dos no se sabe casi nada.

    **Y si la desviacion es cero** —todos los intentos iguales—, **el
    intervalo es `None`**: `+-0` seria decir que no hay error, y un margen
    de cero no es un margen.
    """
    if not intentos:
        return None
    total = sum(intento.preguntas for intento in intentos)
    if total == 0:
        return None
    nota = (sum(intento.aciertos for intento in intentos) / total) * escala
    nota = min(nota, NOTA_MAXIMA)

    if len(intentos) < INTENTOS_MINIMOS_PARA_INTERVALO:
        return NotaEstimada(nota=nota, minimo=None, maximo=None, intentos=len(intentos))

    media = sum(intento.acierto for intento in intentos) / len(intentos)
    varianza = sum((intento.acierto - media) ** 2 for intento in intentos) / (len(intentos) - 1)
    # **Casi cero, no cero**: tres 0,7 iguales no dan una varianza
    # exactamente 0 en coma flotante, y `== 0` dejaria pasar un +-0.
    if abs(varianza) < 1e-12:
        return NotaEstimada(nota=nota, minimo=None, maximo=None, intentos=len(intentos))
    margen = 1.96 * (varianza**0.5) / (len(intentos) ** 0.5) * escala
    return NotaEstimada(
        nota=nota,
        minimo=max(nota - margen, 0.0),
        maximo=min(nota + margen, NOTA_MAXIMA),
        intentos=len(intentos),
    )
