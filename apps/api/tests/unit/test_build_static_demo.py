"""La demo estática de Pages: temario completo, cobertura visible y estados honestos.

Se construye el JSON de verdad y se comprueba lo que la demo promete: 40 temas, sellos de apuntes y
práctica, avance por bloque, 12 convocatorias, cada tema completo con 3+ apartados, fuente y 10
preguntas, y ningún perfil privado.
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
    assert counts["pending"] == counts["topics"] - counts["complete"]
    assert counts["questions"] == counts["complete"] * 10
    assert counts["convocatorias"] == 12

    data = json.loads(salida.read_text(encoding="utf-8"))
    assert data["progress"] == {
        "total": 40,
        "apuntesCompletos": counts["complete"],
        "soloResumen": 0,
        "pendientes": counts["pending"],
        "conPractica": counts["withQuestions"],
        "sinPractica": 40 - counts["withQuestions"],
        "questions": counts["questions"],
        "convocatorias": 12,
    }
    assert data["convocatorias"]["total"] == 12
    assert data["convocatorias"]["draft"] + data["convocatorias"]["archived"] == 12

    topics = {
        topic["path"]: topic for block in data["curriculum"]["blocks"] for topic in block["topics"]
    }
    assert len(topics) == 40
    if counts["pending"] > 0:
        assert any(topic["apuntesStatus"] == "pendiente" for topic in topics.values())
    assert all("apuntesStatus" in topic and "practicaStatus" in topic for topic in topics.values())

    for block in data["curriculum"]["blocks"]:
        coverage = block["coverage"]
        assert coverage["total"] == len(block["topics"])
        assert (
            coverage["conApuntes"] + coverage["soloResumen"] + coverage["pendientes"]
            == coverage["total"]
        )
        assert coverage["conPractica"] == sum(
            1 for topic in block["topics"] if topic["practicaStatus"] == "con_practica"
        )

    for path, contenido in data["topics"].items():
        if contenido["apuntesStatus"] != "completos":
            continue
        assert topics[path]["apuntesStatus"] == "completos"
        assert len(contenido["sections"]) >= 3
        assert contenido["source"]["label"].strip() != ""
        assert any("table" in section for section in contenido["sections"]), (
            f"{path}: un tema completo debe incluir una tabla"
        )
        assert 3 <= len(contenido["memorizar"]) <= 5, f"{path}: memorizar incompleto"
        assert 2 <= len(contenido["errores"]) <= 4, f"{path}: errores incompletos"
        assert contenido["practicaStatus"] == "con_practica"
        practica = next(item for item in data["practices"] if item["tema_path"] == path)
        assert len(practica["questions"]) == 10
        assert practica["source"]["label"].strip() != ""
        for pregunta in practica["questions"]:
            assert len(pregunta["options"]) == 4
            assert pregunta["correct"] in {"a", "b", "c", "d"}
            assert pregunta["explanation"].strip() != ""
            assert pregunta["source"]["label"].strip() != ""

    # Sin material restringido: la demo se publica en un repositorio público.
    texto = salida.read_text(encoding="utf-8").lower()
    assert "guardia civil" not in texto
    assert "celador" not in texto
