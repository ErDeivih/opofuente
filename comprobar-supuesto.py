"""¿Las 25 preguntas del supuesto del bloque IV tienen clave servible? (remate, punto 4)."""

import sqlite3

from opofuente.config import get_settings
from opofuente.infrastructure.key_policy import clave_servible

BASE = get_settings().data_paths.database
c = sqlite3.connect(BASE, timeout=30)

caso = c.execute(
    "select id from practical_cases where block = 'IV' "
    "order by (origin <> 'official'), created_at limit 1"
).fetchone()[0]
ids = [
    fila[0]
    for fila in c.execute(
        "select question_version_id from practical_case_questions "
        "where practical_case_id = ? order by position",
        (caso,),
    )
]
print("supuesto:", caso, "· preguntas:", len(ids))

# ¿cuántas tienen opciones y cuántas una marca de correcta?
con_opciones = 0
con_clave = 0
for qid in ids:
    opciones = c.execute(
        "select count(*) from question_options where question_version_id = ?", (qid,)
    ).fetchone()[0]
    if opciones:
        con_opciones += 1
print("con opciones:", con_opciones, "de", len(ids))

# La política del sistema, aplicada tal cual.
print("clave_servible:", clave_servible(3) if callable(clave_servible) else "(no es invocable)")
c.close()
