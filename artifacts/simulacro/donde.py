"""Dónde se va el tiempo que queda: cronometra cada lectura por lotes de la composición.

Uso:
    python artifacts/simulacro/donde.py <data_dir>

Envuelve las lecturas por lotes del repositorio y las cronometra, más la composición entera.
Es la continuación de `medir.py`: aquel dice **cuántas** consultas, este dice **cuál** de las
lecturas por lotes se lleva el tiempo que queda.
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "apps" / "api"))

from fastapi.testclient import TestClient

from opofuente.config import Settings
from opofuente.infrastructure.question_repository import (
    SqlAlchemyQuestionRepository as Repo,
)
from opofuente.main import create_app

TIEMPOS: dict[str, float] = {}
VECES: dict[str, int] = {}


def cronometrar(clase: type, nombre: str) -> None:
    original = getattr(clase, nombre)

    def envuelto(*args: Any, **kwargs: Any) -> Any:
        t0 = time.perf_counter()
        try:
            return original(*args, **kwargs)
        finally:
            TIEMPOS[nombre] = TIEMPOS.get(nombre, 0.0) + (time.perf_counter() - t0)
            VECES[nombre] = VECES.get(nombre, 0) + 1

    setattr(clase, nombre, envuelto)


for _nombre in (
    "questions_by_ids",
    "sets_by_ids",
    "keys_by_set_ids",
    "excluded_question_ids_by_set",
    "question_ids_of_nodes",
    "derived_keys",
    "questions_without_reliable_key",
    "sets_with_derived_keys",
):
    cronometrar(Repo, _nombre)

os.environ.pop("OPOFUENTE_DATA_DIR", None)
_app = create_app(Settings(data_dir=Path(sys.argv[1]), worker_enabled=False, _env_file=None))
with TestClient(_app) as _cliente:
    _t0 = time.perf_counter()
    _respuesta = _cliente.post("/api/v1/student/mock-exams", json={})
    _total = time.perf_counter() - _t0

print(f"estado {_respuesta.status_code} · total {_total:.3f} s")
print(f"suma de lo cronometrado: {sum(TIEMPOS.values()):.3f} s")
for _clave, _gastado in sorted(TIEMPOS.items(), key=lambda par: -par[1]):
    print(f"  {_gastado:8.3f} s  (veces: {VECES[_clave]})  {_clave}")
