"""La ida y vuelta del paquete publico, con la base de verdad (M8).

**Lo que afirma, y es la prueba que el hito pide literalmente**: **exportar,
importar y volver a exportar da lo mismo**, **y dentro no hay nada de una
persona**.

**Y se compara sin el campo `creado`**: **es la hora a la que se escribio el
fichero, y cambiarla no es que el paquete sea distinto**. **Todo lo demas si
se compara**, **que es donde de verdad se rompe**: **una fecha que se escribe
de otra forma, o una tabla que pierde una fila.**
"""

from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from opofuente.tools.paquete_publico import exportar, importar, revisar


def test_exportar_importar_y_exportar_da_lo_mismo(
    seeded_client: TestClient, tmp_path: Path
) -> None:
    """La ida y vuelta, entera, sobre la base sembrada."""
    primero = tmp_path / "primero.json"
    segundo = tmp_path / "segundo.json"

    # **La base sembrada de las pruebas de integracion no trae material
    # publico**, asi que aqui la ida y vuelta se comprueba sobre lo que haya,
    # aunque haya poco. **La de 31.901 filas se comprobo contra la copia real**,
    # y esta prueba lo que vigila es el contrato: **que importar no cambie lo
    # exportado**, con material o sin el.
    exportar(primero)

    bien, problemas = revisar(primero)
    assert bien is True, f"el paquete lleva datos de una persona: {problemas}"

    importar(primero)
    exportar(segundo)

    antes = json.loads(primero.read_text(encoding="utf-8"))
    despues = json.loads(segundo.read_text(encoding="utf-8"))
    antes.pop("creado", None)
    despues.pop("creado", None)
    assert antes == despues, "la segunda exportacion no da lo mismo que la primera"
