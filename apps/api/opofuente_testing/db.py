"""Utilidades de base de datos para las pruebas: **una sola puerta a SQLAlchemy** (M1).

**Por qué existe este fichero.** `mypy` pide el `type: ignore` de `conexion.execute(...)`
**en la misma línea del error**, y `ruff format` **mueve ese comentario** en cuanto la
llamada no cabe en una línea. Las dos herramientas del árbol se pelean por el mismo sitio,
y el que corre después gana. El síntoma es una prueba que pasa y un `mypy` que la rechaza,
con el aviso «Unused "type: ignore"» tres líneas más abajo.

**La salida no es quitar el comentario**: es **tener una sola llamada**, corta, con el
único `type: ignore` del código de pruebas, en un sitio donde nadie quiera partirlo. Todo
lo demás llama aquí.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from sqlalchemy import text


def filas(conexion: Any, sql: str, params: Mapping[str, Any] | None = None) -> Sequence[Any]:
    """Ejecuta el SQL y devuelve las filas.

    **El único `type: ignore` del árbol de pruebas vive en la línea de abajo**, que son
    sesenta caracteres y no hay formateador que quiera partir.
    """
    return list(conexion.execute(text(sql), dict(params or {})))
