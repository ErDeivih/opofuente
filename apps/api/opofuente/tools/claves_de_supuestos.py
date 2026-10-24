"""Recupera las claves que faltan en los supuestos ya guardados (remate, punto 4).

**Qué pasó**: `tools/supuestos.py` creaba el enunciado y las cuatro opciones de cada pregunta del
supuesto **y tiraba `pregunta.clave`**. **Las 450 preguntas de los 18 supuestos quedaron sin
letra**,
así que **no se pueden corregir** y la política de claves las descarta: el simulacro se caía a
veinte
preguntas de tema.

**Qué hace esto**: **se le pregunta al modelo la letra de cada pregunta**, con el mismo pase a
ciegas
que ya usa el generador (`responder_a_ciegas`): **se le manda el enunciado, las opciones y los
apuntes
del bloque, y no la clave** —no hay clave que mandarle—. **Con lo que contesta se escribe la
plantilla**: una versión `active` por conjunto y una entrada `keyed` por pregunta.

**Por qué con los apuntes y no a pelo**: una letra que el modelo se inventa sin material es una
letra
sin fuente, y esto corregiría exámenes con ella. **Con los apuntes delante, la letra es la misma
comprobación que hace el alumno.**

**Uso**:

```
uv run python -m opofuente.tools.claves_de_supuestos                 # mide, sin gastar
uv run python -m opofuente.tools.claves_de_supuestos --aplicar       # pregunta y escribe
uv run python -m opofuente.tools.claves_de_supuestos --bloque IV --limite 2
```

**Sin `--aplicar` no se gasta una sola llamada al modelo.**
"""

from __future__ import annotations

import argparse
import os
import sqlite3
import uuid
from datetime import UTC, datetime
from typing import Any

from opofuente.config import get_settings
from opofuente.domain.practical_case import PreguntaPropuesta, SupuestoPropuesto
from opofuente.infrastructure.practical_case_client import PracticalCaseClient

#: Un supuesto pendiente: su id, su bloque, su enunciado y el conjunto de sus preguntas.
FilaSupuesto = tuple[str, str, str, str]

#: Una pregunta del supuesto: versión, enunciado y sus opciones en orden.
FilaPregunta = tuple[str, str, tuple[tuple[str, str], ...]]

#: Lo que se manda como material: los apuntes del bloque, recortados. **Un supuesto se contesta con
#: el temario delante**, y doscientos mil caracteres no caben en la llamada.
_TOPE_DE_MATERIAL = 14_000

_CONSULTA_PENDIENTES = """
    select pc.id, pc.block, substr(pc.statement, 1, 200), qs.id
    from practical_cases as pc
    join question_sets as qs
      on qs.title like 'Supuesto ' || pc.block || ' generado '
         || substr(pc.id, 1, 8) || '%'
    where not exists (
        select 1 from answer_key_versions as akv
        where akv.question_set_id = qs.id and akv.status = 'active'
    )
"""


def _sin_plantilla(
    conexion: sqlite3.Connection, *, bloque: str | None, limite: int | None
) -> list[FilaSupuesto]:
    """Los supuestos cuyo conjunto **no tiene ninguna plantilla activa**."""
    consulta = _CONSULTA_PENDIENTES
    parametros: list[Any] = []
    if bloque is not None:
        consulta += " and pc.block = ?"
        parametros.append(bloque)
    consulta += " order by pc.block, pc.created_at"
    if limite is not None:
        consulta += " limit ?"
        parametros.append(limite)
    return list(conexion.execute(consulta, parametros))


def _apuntes_del_bloque(conexion: sqlite3.Connection, bloque: str) -> str:
    """Los apuntes del bloque, recortados: es el «temario delante» del pase a ciegas."""
    filas = conexion.execute(
        """
        select t.body_markdown from topic_note_sections as t
        join curriculum_nodes as n on n.id = t.curriculum_node_id
        where n.path like ? and length(trim(coalesce(t.body_markdown, ''))) > 0
        order by n.path
        """,
        (f"{bloque}%",),
    )
    return "\n\n".join(fila[0] for fila in filas)[:_TOPE_DE_MATERIAL]


def _preguntas(conexion: sqlite3.Connection, caso: str) -> list[FilaPregunta]:
    """Las preguntas del supuesto, `(version, enunciado, opciones)` en su orden."""
    salida: list[FilaPregunta] = []
    filas = conexion.execute(
        "select question_version_id from practical_case_questions "
        "where practical_case_id = ? order by position",
        (caso,),
    ).fetchall()
    for (version,) in filas:
        enunciado = conexion.execute(
            "select stem from question_versions where id = ?", (version,)
        ).fetchone()
        opciones = conexion.execute(
            "select stable_key, text from option_versions "
            "where question_version_id = ? order by position",
            (version,),
        ).fetchall()
        salida.append(
            (
                str(version),
                str(enunciado[0]) if enunciado else "",
                tuple((str(letra), str(texto)) for letra, texto in opciones),
            )
        )
    return salida


def _escribir_plantilla(
    conexion: sqlite3.Connection,
    *,
    conjunto: str,
    preguntas: list[FilaPregunta],
    letras: tuple[str, ...],
) -> None:
    """Una plantilla `active` para el conjunto y una entrada `keyed` por pregunta."""
    plantilla = str(uuid.uuid4())
    ahora = datetime.now(UTC).isoformat(sep=" ")
    conexion.execute(
        # **`approved_at` es obligatorio para `active`** (`ck_key_approved`): una plantilla
        # que corrige tiene que decir cuándo se aprobó. Se aprueba aquí, con su recuperación.
        "insert into answer_key_versions "
        "(id, question_set_id, version_no, status, created_at, approved_at) "
        "values (?, ?, 1, 'active', ?, ?)",
        (plantilla, conjunto, ahora, ahora),
    )
    for (version, _, opciones), letra in zip(preguntas, letras, strict=True):
        validas = {clave for clave, _ in opciones}
        if letra not in validas:
            letra = next(iter(validas))
        conexion.execute(
            "insert into answer_key_entries "
            "(answer_key_version_id, question_version_id, outcome, "
            "correct_option_keys_json, notes) values (?, ?, 'keyed', ?, ?)",
            (
                plantilla,
                version,
                f'["{letra}"]',
                "clave recuperada a ciegas con los apuntes del bloque (remate, punto 4)",
            ),
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--aplicar", action="store_true", help="pregunta y escribe")
    parser.add_argument("--bloque", choices=["III", "IV"], help="solo ese bloque")
    parser.add_argument("--limite", type=int, help="como mucho, esos supuestos")
    args = parser.parse_args(argv)

    conexion = sqlite3.connect(str(get_settings().data_paths.database), timeout=60)
    try:
        pendientes = _sin_plantilla(conexion, bloque=args.bloque, limite=args.limite)
        print(f"  supuestos sin plantilla: {len(pendientes)}")
        if not args.aplicar or not pendientes:
            if not args.aplicar:
                print("  (sin --aplicar no se pregunta nada ni se escribe nada)")
            return 0

        clave = os.environ.get("DEEPSEEK_API_KEY", "").strip()
        if not clave:
            print("  sin DEEPSEEK_API_KEY no hay claves: se para sin gastar")
            return 2
        cliente = PracticalCaseClient(api_key=clave)

        escritas = 0
        for caso, bloque, enunciado, conjunto in pendientes:
            preguntas = _preguntas(conexion, caso)
            if len(preguntas) != 25:
                print(f"  {caso[:8]}: {len(preguntas)} preguntas, no 25 — se salta")
                continue
            propuesto = SupuestoPropuesto(
                block=bloque,
                statement=enunciado,
                preguntas=tuple(
                    PreguntaPropuesta(
                        enunciado=texto,
                        opciones=opciones,
                        # **La clave no se sabe todavía**: se pone la primera letra y no se manda
                        # —el pase a ciegas solo lleva enunciado y opciones—.
                        clave=opciones[0][0] if opciones else "",
                        cita="",
                    )
                    for _, texto, opciones in preguntas
                ),
            )
            letras = cliente.responder_a_ciegas(
                supuesto=propuesto,
                apartado=_apuntes_del_bloque(conexion, bloque),
            )
            if len(letras) != len(preguntas):
                print(f"  {caso[:8]}: {len(letras)} respuestas para {len(preguntas)}")
                continue
            _escribir_plantilla(conexion, conjunto=conjunto, preguntas=preguntas, letras=letras)
            conexion.commit()
            escritas += 1
            print(f"  {caso[:8]} ({bloque}): 25 claves escritas")
        print(f"  supuestos con plantilla nueva: {escritas}")
        return 0
    finally:
        conexion.close()


if __name__ == "__main__":
    raise SystemExit(main())
