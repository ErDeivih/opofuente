"""Mide el montaje de una sesión contando **cada consulta** que llega a SQLite.

Uso:
    python artifacts/simulacro/medir.py <data_dir> [--sin-contador] <ruta> [<ruta> ...]

`<ruta>` es la ruta del API que se quiere medir (`POST /api/v1/student/mock-exams`, por ejemplo).
Se cuentan las sentencias por su texto normalizado y se enseña el recuento, el tiempo y las que más
se repiten. Es el instrumento con el que se dice **dónde** se va el tiempo, no solo cuánto.

`--sin-contador` apaga el gancho de medición y deja solo el cronómetro: contar 154.000 consultas
cuesta su tiempo, así que **el antes y el después que se comparan tienen que medirse igual**. Se usa
para el parte de tiempos limpio; con contador, para saber qué consulta se repite.
"""

from __future__ import annotations

import os
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "apps" / "api"))

from fastapi.testclient import TestClient
from sqlalchemy import event
from sqlalchemy.engine import Engine

from opofuente.config import Settings
from opofuente.main import create_app

CONTADOR: Counter[str] = Counter()
TIEMPOS: dict[str, float] = {}
ACTIVO = False


@event.listens_for(Engine, "before_cursor_execute")
def _antes(
    conn: Any, cursor: Any, statement: str, parameters: Any, context: Any, many: bool
) -> None:
    if ACTIVO:
        context._opo_t0 = time.perf_counter()  # type: ignore[attr-defined]


@event.listens_for(Engine, "after_cursor_execute")
def _despues(
    conn: Any, cursor: Any, statement: str, parameters: Any, context: Any, many: bool
) -> None:
    if not ACTIVO:
        return
    t0 = getattr(context, "_opo_t0", None)
    gastado = 0.0 if t0 is None else time.perf_counter() - t0
    texto = " ".join(statement.split())
    CONTADOR[texto] += 1
    TIEMPOS[texto] = TIEMPOS.get(texto, 0.0) + gastado


def main() -> int:
    argumentos = sys.argv[1:]
    if len(argumentos) < 2:
        print(__doc__)
        return 2
    # `--sin-contador` va delante y apaga el gancho: el parte de tiempos se mide igual en los dos
    # lados de la comparación, o la comparación mide el instrumento.
    contar = "--sin-contador" not in argumentos
    argumentos = [uno for uno in argumentos if uno != "--sin-contador"]
    data_dir = Path(argumentos[0])
    rutas = argumentos[1:]
    global ACTIVO

    os.environ.pop("OPOFUENTE_DATA_DIR", None)
    # Sin worker: lo que se mide es la petición, no el trabajo de fondo.
    ajustes = Settings(data_dir=data_dir, worker_enabled=False, _env_file=None)
    app = create_app(ajustes)

    with TestClient(app) as cliente:
        for ruta in rutas:
            metodo, _, camino = ruta.partition(" ")
            CONTADOR.clear()
            TIEMPOS.clear()
            ACTIVO = contar
            t0 = time.perf_counter()
            respuesta = cliente.request(metodo, camino, json={} if metodo == "POST" else None)
            gastado = time.perf_counter() - t0
            ACTIVO = False
            total = sum(CONTADOR.values())
            print(f"\n=== {ruta} -> {respuesta.status_code} | {gastado:.3f} s | {total} sentencias")
            if respuesta.status_code >= 400:
                print(respuesta.text[:3000])
                continue
            if camino.endswith("mock-exams") and metodo == "POST":
                cuerpo = respuesta.json()
                print(
                    f"    sesion {cuerpo.get('id')} | {len(cuerpo.get('questions', []))} preguntas"
                )
            print("    las que mas se repiten:")
            for sentencia, veces in CONTADOR.most_common(10):
                print(f"      {veces:6d} x {TIEMPOS[sentencia]:8.3f} s  {sentencia[:120]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
