"""Cuenta cuántas veces se llama a cada pieza caliente al montar un simulacro.

Es una sonda de medida, no código de la aplicación: envuelve los métodos y cuenta. Sirve para decir
**dónde** se va el tiempo, no solo cuánto.
"""

from __future__ import annotations

import os
import sys
from collections import Counter
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "apps" / "api"))

from fastapi.testclient import TestClient

from opofuente.application.study_service import StudyService
from opofuente.config import Settings
from opofuente.infrastructure.question_repository import (
    SqlAlchemyQuestionRepository as Q,
)
from opofuente.main import create_app

LLAMADAS: Counter[str] = Counter()
NODOS: list[int] = []


def envolver(clase: type, nombre: str, etiqueta: str) -> None:
    original = getattr(clase, nombre)

    def nuevo(*args: Any, **kwargs: Any) -> Any:
        LLAMADAS[etiqueta] += 1
        return original(*args, **kwargs)

    setattr(clase, nombre, nuevo)


for _nombre in (
    "questions_by_ids",
    "sets_by_ids",
    "keys_by_set_ids",
    "excluded_question_ids",
    "question_ids_of_nodes",
    "derived_keys",
    "questions_without_reliable_key",
    "sets_with_derived_keys",
    "list_keys",
):
    if hasattr(Q, _nombre):
        envolver(Q, _nombre, f"Q.{_nombre}")

_candidatas_original = StudyService._candidatas


def _candidatas(  # type: ignore[no-untyped-def]
    self, parte, spec, vistas, banco, leidas
):
    LLAMADAS["S._candidatas"] += 1
    NODOS.append(len(parte.node_ids))
    return _candidatas_original(self, parte, spec, vistas, banco, leidas)


StudyService._candidatas = _candidatas  # type: ignore[method-assign]

os.environ.pop("OPOFUENTE_DATA_DIR", None)
_app = create_app(Settings(data_dir=Path(sys.argv[1]), worker_enabled=False, _env_file=None))
with TestClient(_app) as _cliente:
    _respuesta = _cliente.post("/api/v1/student/mock-exams", json={})
    print("estado", _respuesta.status_code)
    _cuerpo = _respuesta.json()
    print(
        "total_questions",
        _cuerpo.get("total_questions"),
        "limite",
        _cuerpo.get("time_limit_minutes"),
    )

for _etiqueta, _veces in LLAMADAS.most_common():
    print(f"{_veces:6d}  {_etiqueta}")
print("partes compuestas (nodos por parte):", NODOS)
