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
    """Ejecuta el SQL y devuelve las filas: **para las lecturas**.

    **Sin `type: ignore`**, y no por suerte: `conexion` está declarada `Any`, así que `mypy`
    no ve el overload de `execute` que le disgusta y no hay nada que silenciar. `ruff` no
    tiene entonces ningún comentario que mover.
    """
    return list(conexion.execute(text(sql), dict(params or {})))


def ejecutar(conexion: Any, sql: str, params: Mapping[str, Any] | None = None) -> None:
    """Ejecuta el SQL y **no devuelve nada**: para las escrituras.

    **No es `filas` sin `list`**: envolver un `INSERT` en `list(...)` lo ejecuta igual, pero
    deja un resultado que nadie mira y una prueba que parece leer cuando escribe. Aquí se
    dice lo que hace.
    """
    conexion.execute(text(sql), dict(params or {}))
