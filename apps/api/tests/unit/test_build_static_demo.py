"""La demo estática de Pages: temario completo, temas con contenido real y estados honestos.

Se construye el JSON de verdad y se comprueba lo que la demo promete: 40 temas, progreso por estado,
cada tema completo con 3+ apartados, fuente y 10 preguntas, y ningún perfil privado.
"""

from __future__ import annotations

import json
from pathlib import Path

from opofuente.config import project_root
from opofuente.tools.build_static_demo import build_static_demo


def test_la_demo_estatica_tiene_temario_progreso_y_contenido_real(tmp_path: Path) -> None:
    salida = tmp_path / "data.json"
    counts = build_static_demo(out=salida, root=project_root())

    assert counts["blocks"] == 5
    assert counts["topics"] == 40
    assert counts["complete"] >= 5, "la demo debe publicar varios temas redactados"
    assert counts["withQuestions"] == counts["complete"], "hoy todo tema completo tiene su práctica"
    assert counts["complete"] + counts["pending"] == counts["topics"]
    assert counts["practices"] == counts["complete"], "cada tema completo tiene su práctica"
    assert counts["pending"] >= 1, "debe quedar algún tema en preparación (es honesto)"
    assert counts["questions"] == counts["complete"] * 10

    data = json.loads(salida.read_text(encoding="utf-8"))
    assert data["progress"] == {
        "total": 40,
        "complete": counts["complete"],
        "withQuestions": counts["withQuestions"],
        "pending": counts["pending"],
        "questions": counts["questions"],
    }

    topics = {
        topic["path"]: topic for block in data["curriculum"]["blocks"] for topic in block["topics"]
    }
    assert len(topics) == 40
    assert any(topic["status"] == "pendiente" for topic in topics.values())

    for path, contenido in data["topics"].items():
        if contenido["status"] != "completo":
            continue
        assert topics[path]["status"] == "completo"
        assert len(contenido["sections"]) >= 3
        assert contenido["source"]["label"].strip() != ""
        assert any("table" in section for section in contenido["sections"]), (
            f"{path}: un tema completo debe incluir una tabla"
        )
        practica = next(item for item in data["practices"] if item["tema_path"] == path)
        assert len(practica["questions"]) == 10
        for pregunta in practica["questions"]:
            assert len(pregunta["options"]) == 4
            assert pregunta["correct"] in {"a", "b", "c", "d"}
            assert pregunta["explanation"].strip() != ""

    # Sin material restringido: la demo se publica en un repositorio público.
    texto = salida.read_text(encoding="utf-8").lower()
    assert "guardia civil" not in texto
    assert "celador" not in texto
