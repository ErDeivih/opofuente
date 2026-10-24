"""Recupera las explicaciones privadas que sustituyó M1, archivadas (remate, punto 1).

**Qué pasó**: `--sustituir-lo-privado` **reemplazó en la misma fila** 5.939 explicaciones privadas
del propietario por otras generadas. **El `id` no cambió y el texto original se perdió**: quedó solo
en la copia `base-real-20261023-112631-antes-de-M1.sqlite3`.

**Qué hace esto**: **copia de la copia a la base real las 5.939, con `status = 'archived'`**. No se
sirven al alumno —`explanations_of` filtra las archivadas—, **no pisan a las generadas** —que son
mejores y se quedan— y **la sustitución se puede deshacer**.

**Por qué la fila archivada lleva un `id` nuevo**: **la privada y la generada son la misma fila
hoy**, con el mismo `id`. **Reinsertar con el `id` original sería pisar la generada**; con uno nuevo
conviven, que es el sentido de archivar.

**Uso**:

```
uv run python -m opofuente.tools.recuperar_explicaciones_privadas --copia <ruta.sqlite3>
# mide
uv run python -m opofuente.tools.recuperar_explicaciones_privadas --copia <ruta.sqlite3> --aplicar
# escribe
```

**Sin `--aplicar` no escribe nada**: leer una base de 2,5 GB y contestar qué haría es barato;
equivocarse no.
"""

from __future__ import annotations

import argparse
import sqlite3
import uuid
from dataclasses import dataclass
from pathlib import Path

from opofuente.config import get_settings


@dataclass(frozen=True, slots=True)
class Recuperacion:
    """Lo que ha pasado, para poder contarlo sin releer la base."""

    candidatas: int
    ya_archivadas: int
    sin_pregunta: int
    recuperadas: int


def _pendientes(destino: sqlite3.Connection) -> list[tuple[object, ...]]:
    """Las privadas de la copia cuya pregunta hoy tiene una generada.

    **Solo esas**: las que siguen siendo privadas en la base real **no se han perdido** y no hay
    nada que recuperar. Y **las que ya tienen una archivada quedan fuera**, para poder relanzar.

    **Se lee de `copia` y se comprueba en `main`**, que es al revés de lo que parece a primera
    vista: el original está en la copia, y quien dice si se sustituyó es la base real.

    **El SQL va literal, sin montarlo con f-strings**: `ruff` lo marca con razón —una cadena
    construida es una inyección esperando— y aquí no hace falta ninguna.
    """
    return destino.execute(
        """
        select
            privada.question_version_id, privada.option_stable_key, privada.text,
            privada.prompt_template_version, privada.created_at, privada.citation,
            privada.note_anchor_id
        from copia.question_explanations as privada
        where privada.origin = 'private'
          and exists (
              select 1 from main.question_explanations as viva
              where viva.question_version_id = privada.question_version_id
                and viva.origin = 'generated'
          )
          and not exists (
              select 1 from main.question_explanations as archivada
              where archivada.question_version_id = privada.question_version_id
                and archivada.status = 'archived'
          )
        """,
    ).fetchall()


def recuperar(ruta_copia: Path, *, aplicar: bool) -> Recuperacion:
    ajustes = get_settings()
    destino = sqlite3.connect(ajustes.data_paths.database, timeout=60)
    destino.execute("attach database ? as copia", (str(ruta_copia),))
    try:
        filas = _pendientes(destino)
        ya = int(
            destino.execute(
                "select count(*) from question_explanations where status = 'archived'"
            ).fetchone()[0]
        )
        preguntas = {
            fila[0] for fila in destino.execute("select id from question_versions").fetchall()
        }
        sin_pregunta = [f for f in filas if f[0] not in preguntas]
        validas = [f for f in filas if f[0] in preguntas]

        recuperadas = 0
        if aplicar and validas:
            # **La referencia se comprueba fila a fila**, no con un `insert ... select`: si una
            # pregunta no existe, con el `select` se pierde la fila sin decir cuál.
            destino.executemany(
                """
                insert into question_explanations
                    (id, question_version_id, option_stable_key, text, origin, status,
                     model_name, prompt_template_version, created_at, citation, note_anchor_id)
                values (?, ?, ?, ?, 'private', 'archived', null, ?, ?, ?, ?)
                """,
                [
                    (
                        str(uuid.uuid4()),
                        fila[0],
                        fila[1],
                        fila[2],
                        fila[3],
                        fila[4],
                        fila[5],
                        fila[6],
                    )
                    for fila in validas
                ],
            )
            recuperadas = len(validas)
            destino.commit()
        return Recuperacion(
            candidatas=len(filas),
            ya_archivadas=ya,
            sin_pregunta=len(sin_pregunta),
            recuperadas=recuperadas,
        )
    finally:
        destino.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--copia", required=True, type=Path, help="copia de antes de M1")
    parser.add_argument(
        "--aplicar",
        action="store_true",
        help="escribe de verdad; sin esto solo cuenta lo que haría",
    )
    args = parser.parse_args()
    if not args.copia.is_file():
        raise SystemExit(f"no existe la copia: {args.copia}")

    resultado = recuperar(args.copia, aplicar=args.aplicar)
    print(f"  candidatas a recuperar:   {resultado.candidatas}")
    print(f"  ya archivadas antes:      {resultado.ya_archivadas}")
    print(f"  sin pregunta en la base:  {resultado.sin_pregunta}")
    print(f"  recuperadas ahora:        {resultado.recuperadas}")
    if not args.aplicar:
        print("  (sin --aplicar no se ha escrito nada)")


if __name__ == "__main__":
    main()
