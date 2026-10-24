"""Marca las preguntas «sin material» de la bandeja (remate, punto 7, decisión 2).

**Qué son**: **las 423 decisiones que ni son de examen oficial ni las resolvió la
cuarentena del conjunto** —el `resto` de `tools/bandeja.py`—. **Son de bancos privados
cuya materia no está en los apuntes**: no se pueden estudiar con ellos, y no son del
propietario.

**Dónde se marca, y por qué ahí**: **en `question_key_gaps`, con el motivo
`sin_material`** —que ya existe y ya lo usan 678 preguntas—. **Es la tabla que mira la
política de claves** (`clave_servible`) para decidir que una pregunta **no entra en tests
ni en repasos**, así que marcarla ahí es lo que la saca de verdad, **sin borrar nada**.

**Y por qué no en `question_curriculum_exclusions`**: esa tabla dice otra cosa —«esta
pregunta no es de esta administración» o «su enunciado está roto»— y **la usan la ficha de
la pregunta y el clasificador**; meter ahí un motivo que no es de fuera de temario habría
cambiado dos pantallas que no tienen nada que ver.

**Qué más hace**: **cierra su incidencia como `dismissed`** con su nota, para que dejen de
pedir criterio **y sigan listadas en el panel**. **Es idempotente.**

**Y vuelven solas**: en cuanto un tema nuevo cubra su materia, se les quita el hueco y
vuelven a los tests — eso es lo que `notes verify` comprueba.

**Uso**:

```
uv run python -m opofuente.tools.marcar_sin_material            # cuenta, sin escribir
uv run python -m opofuente.tools.marcar_sin_material --aplicar  # escribe
```

**El conjunto es el mismo que cuenta la bandeja**: se repite aquí su consulta, con las
mismas condiciones, para que el número que se marca sea el que el propietario ve.
"""

from __future__ import annotations

import argparse
import sqlite3

from opofuente.config import get_settings

#: El `resto` de la bandeja: abiertas, que piden criterio, y **ni oficiales ni en
#: cuarentena**. **El SQL va literal**: los dos motivos automatizables son los mismos que
#: cuenta `tools/bandeja.py`, y montarlo con un `format` es una inyección esperando —lo que
#: `ruff` marca con razón (`S608`)—.
_RESTO = """
    select i.id, i.question_version_id, v.question_set_id
    from notes_incidents as i
    join question_versions as v on v.id = i.question_version_id
    left join question_sets as qs on qs.id = v.question_set_id
    where i.status = 'open'
      and i.reason not in ('sin_frase_en_los_apuntes', 'clave_sin_definir')
      and coalesce(qs.set_type, '') <> 'official_exam'
      and coalesce(qs.key_reliability, '') not in ('dudosa', 'no_fiable')
      and not exists (
          select 1 from question_key_gaps as g
          where g.question_version_id = i.question_version_id
            and g.reason = 'sin_material'
      )
"""

_NOTA = "sin material: es de un banco privado y los apuntes no cubren su materia (remate, punto 7)"


def marcar(*, aplicar: bool) -> int:
    conexion = sqlite3.connect(str(get_settings().data_paths.database), timeout=60)
    try:
        filas = conexion.execute(_RESTO).fetchall()
        print(f"  preguntas sin material pendientes de marcar: {len(filas)}")
        if not aplicar:
            print("  (sin --aplicar no se escribe nada)")
            return 0
        for incidencia, pregunta, conjunto in filas:
            conexion.execute(
                "insert or ignore into question_key_gaps "
                "(question_version_id, question_set_id, reason, actor, created_at) "
                "values (?, ?, 'sin_material', 'remate-punto-7', datetime('now'))",
                (pregunta, conjunto),
            )
            conexion.execute(
                "update notes_incidents set status = 'dismissed', "
                "resolution_note = coalesce(resolution_note, ?) where id = ?",
                (_NOTA, incidencia),
            )
        conexion.commit()
        print(f"  marcadas: {len(filas)}")
        return 0
    finally:
        conexion.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--aplicar", action="store_true", help="escribe de verdad")
    args = parser.parse_args(argv)
    return marcar(aplicar=args.aplicar)


if __name__ == "__main__":
    raise SystemExit(main())
