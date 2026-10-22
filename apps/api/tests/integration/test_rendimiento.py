"""Que las pantallas del alumno sigan siendo rapidas (M7).

**Lo que vigila, y por que con un tope y no con una cifra exacta**: **una
prueba de rendimiento que compara milisegundos exactos falla en cuanto la
maquina esta cargada**, **y entonces se ignora, y una prueba de rendimiento
ignorada no vigila nada**. **El tope es el del hito —2 s por pantalla— y es
lo bastante ancho para que una regresion de verdad lo reviente.**

**Y lo que la hace util es que se ejecuta contra la base sembrada**: **los
2 s se miden con los datos que hay, no con una base vacia en la que todo
tarda cero.**

**El 2 s es el limite escrito en el hito**, **no el que tarda hoy**: **hoy
`/student/progress` tarda 230 ms con la copia real**, **y si algun dia
tarda 3 s esta prueba lo dice.**
"""

from __future__ import annotations

import time

import pytest
from fastapi.testclient import TestClient

#: El limite del hito, en segundos.
LIMITE = 2.0

#: Lo que se mide: **las pantallas del alumno que el hito nombra**.
PANTALLAS = (
    "/api/v1/student/progress",
    "/api/v1/stats",
    "/api/v1/plan/hoy",
    "/api/v1/cards/pending",
)


def _cronometrar(client: TestClient, ruta: str) -> float:
    """Los segundos de una llamada, **en caliente**: la primera paga el arranque."""
    client.get(ruta)  # calienta
    inicio = time.perf_counter()
    respuesta = client.get(ruta)
    segundos = time.perf_counter() - inicio
    assert respuesta.status_code == 200, f"{ruta} respondio {respuesta.status_code}"
    return segundos


@pytest.mark.parametrize("ruta", PANTALLAS)
def test_la_pantalla_responde_en_menos_de_dos_segundos(
    ruta: str, seeded_client: TestClient
) -> None:
    """Cada pantalla del alumno, **por debajo del tope del hito**.

    **Se mide dos veces y se queda la segunda**: la primera incluye el
    arranque de la consulta y de las caches, **y medir esa seria medir a la
    maquina, no al codigo.**
    """
    segundos = _cronometrar(seeded_client, ruta)
    assert segundos < LIMITE, f"{ruta} tardo {segundos:.2f} s y el tope son {LIMITE:.1f} s"
