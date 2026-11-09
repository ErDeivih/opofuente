"""La demo estática de Pages: temario completo, dos prácticas y ningún perfil privado."""

from __future__ import annotations

import json
from pathlib import Path

from opofuente.config import project_root
from opofuente.tools.build_static_demo import build_static_demo


def test_la_demo_estatica_lleva_temario_dos_practicas_y_solo_datos_publicos(
    tmp_path: Path,
) -> None:
    salida = tmp_path / "data.json"
    counts = build_static_demo(out=salida, root=project_root())

    assert counts == {"blocks": 5, "topics": 40, "practices": 2, "questions": 20}
    texto = salida.read_text(encoding="utf-8")
    data = json.loads(texto)
    assert data["curriculum"]["code"] == "informatica-c1"
    assert len(data["curriculum"]["blocks"]) == 5
    assert len(data["practices"]) == 2

    practicas = {practica["tema_path"]: practica for practica in data["practices"]}
    assert set(practicas) == {"I.1", "II.13"}
    assert len(practicas["I.1"]["questions"]) == 10
    assert len(practicas["II.13"]["questions"]) == 10
    assert all(
        len(pregunta["options"]) == 4
        for practica in data["practices"]
        for pregunta in practica["questions"]
    )

    # Sin material restringido: la demo se publica en un repositorio público.
    assert "Guardia Civil" not in texto
    assert "guardia civil" not in texto.lower()
    assert "celador" not in texto.lower()
