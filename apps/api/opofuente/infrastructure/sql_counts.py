"""Cuántas filas ha tocado una escritura, sin pelearse con los tipos de SQLAlchemy.

**Por qué existe este módulo de tres líneas.** `Session.execute` está declarado como si devolviera
un `Result`, y `Result` no publica `rowcount`; quien lo devuelve de verdad cuando la sentencia es un
`DELETE` o un `UPDATE` es un `CursorResult`, que sí lo publica. La casa venía evitándolo contando
antes de escribir (ver `question_file_repository` y `housekeeping_repository`), y para una cifra que
va a un documento eso es lo correcto; aquí la cifra es la respuesta de una operación —«he borrado
cuatro sesiones»— y volver a contar antes sería hacer dos consultas para decir lo mismo.

Se resuelve en un sitio y con el porqué escrito, para que no acabe cada repositorio inventándose su
propio `type: ignore`.
"""

from __future__ import annotations

from typing import Any, cast

from sqlalchemy import CursorResult
from sqlalchemy.engine import Result


def affected_rows(result: Result[Any]) -> int:
    """Las filas que ha tocado un `INSERT`, `UPDATE` o `DELETE`."""
    return int(cast("CursorResult[Any]", result).rowcount or 0)


__all__ = ["affected_rows"]
