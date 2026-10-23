"""El servicio del supuesto: del modelo a la tabla, con la comprobacion de
por medio (M5).

**El orden, y es el unico orden valido:**

1. **se escribe el caso** —una llamada—;
2. **se valida la forma** —sin red—, **y si no pasa, se descarta aqui**:
   un supuesto con doce preguntas no merece que nadie lo responda;
3. **se responde a ciegas** —la segunda llamada—
4. **se mide la coincidencia**, **y si no llega al 90 %, se descarta**.

**Lo que NO hace**: **no arregla un supuesto que no pasa**. **No cambia una
pregunta, no le quita la cita a otra, no rellena respuestas que faltan.**
**Un supuesto que se arregla a mano deja de ser una prueba de si el
temario tiene respuestas defendibles**: **se descarta y se prueba con otro
apartado.**

**Y gasta, y lo dice**: **dos llamadas por intento**, **unas cuatro mil
palabras de salida la primera**. **El tope del hito son 6 $ y llevarlos
contados es parte del trabajo.**
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from opofuente.domain.practical_case import (
    SupuestoPropuesto,
    Veredicto,
    recortar_al_numero,
    validar_con_respuestas,
    validar_forma,
)
from opofuente.infrastructure.practical_case_client import PracticalCaseClient


@dataclass(frozen=True, slots=True)
class Intento:
    """Lo que salio de intentar un supuesto, **se acepte o no**."""

    aceptado: bool
    veredicto: Veredicto
    #: El supuesto aceptado, o `None` si se descarto.
    supuesto: SupuestoPropuesto | None
    #: Cuantas preguntas contesto bien el segundo modelo, **si se llego a preguntar**.
    aciertos: int = 0


class PracticalCaseService:
    """Escribe supuestos con el modelo y **solo devuelve los que pasan**."""

    def __init__(self, cliente: PracticalCaseClient | None) -> None:
        self._cliente = cliente

    @property
    def hay_modelo(self) -> bool:
        """Si hay clave y por tanto se puede generar."""
        return self._cliente is not None

    def intentar(self, *, block: str, apartado: str) -> Intento:
        """Una pasada entera: escribir, validar, preguntar a ciegas y decidir.

        **Si no hay modelo, no se intenta**: devuelve un veredicto con el
        motivo, **no una excepcion**. La ruta lo convierte en 503 y la
        herramienta en un mensaje.
        """
        if self._cliente is None:
            return Intento(
                aceptado=False,
                veredicto=Veredicto(
                    aceptado=False,
                    problemas=("falta la clave del modelo: no se puede generar",),
                ),
                supuesto=None,
            )

        propuesto = self._cliente.proponer(block=block, apartado=apartado)
        # **El numero de preguntas se ajusta, no se descarta** (fase 3, §2.4): pedir
        # veinticinco y tirar el supuesto entero porque vinieron veintiseis es tirar
        # un supuesto bueno por un error de contar. Se quitan las sobrantes por el
        # final —donde el modelo anade lo que le sobra— y se sigue.
        propuesto = recortar_al_numero(propuesto)
        forma = validar_forma(propuesto)
        if not forma.aceptado:
            # **Sin gastar la segunda llamada**: un supuesto mal formado no se
            # pregunta, se descarta.
            return Intento(aceptado=False, veredicto=forma, supuesto=None)

        respuestas = self._cliente.responder_a_ciegas(supuesto=propuesto, apartado=apartado)
        final = validar_con_respuestas(propuesto, respuestas=respuestas)
        aciertos = sum(
            1
            for indice, pregunta in enumerate(propuesto.preguntas)
            if indice < len(respuestas) and respuestas[indice] == pregunta.clave
        )
        return Intento(
            aceptado=final.aceptado,
            veredicto=final,
            supuesto=propuesto if final.aceptado else None,
            aciertos=aciertos,
        )


def nuevo_id() -> str:
    """El identificador de un supuesto nuevo, **en un solo sitio**."""
    return str(uuid.uuid4())
