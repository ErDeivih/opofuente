"""El recuperador de temario consolida lo que ya existe sin reescribirlo."""

from __future__ import annotations

import json
from pathlib import Path

from opofuente.tools.recover_temario import (
    parse_apunte,
    parse_question_bank,
    recover,
    seleccionar,
)


def _apunte(tmp: Path) -> Path:
    apuntes = tmp / "APUNTES"
    apuntes.mkdir()
    path = apuntes / "1.1 Tema de prueba.md"
    path.write_text(
        "# Tema 1.1 — Tema de prueba\n\n**Bloque 1.** BLOQUE DE PRUEBA\n\n"
        "## Resumen del tema\n\nTexto del apunte con `fuentes\\origen.pdf` citado.\n\n"
        "### 1. Apartado\n\n| A | B |\n|---|---|\n| 1 | 2 |\n",
        encoding="utf-8",
    )
    resumenes = tmp / "RESUMENES"
    resumenes.mkdir()
    (resumenes / "1.1.md").write_text("# Resumen\n", encoding="utf-8")
    return path


def _banco(tmp: Path) -> Path:
    banco = tmp / "BANCO" / "por-tema-de-la-app" / "TAI"
    banco.mkdir(parents=True)
    bloques = []
    for numero in range(1, 13):
        respondida = True
        bloques.append(
            f"**{numero}. ¿Pregunta {numero}?**\n\n"
            f"- a) Opción A {numero}\n- b) Opción B {numero}"
            + (" ⟵ **correcta**" if respondida else "")
            + "\n- c) Opción C\n- d) Opción D\n\n"
            "  <sub>fuentes\\examen.pdf — pregunta " + str(numero) + "</sub>\n"
        )
    (banco / "I.1.md").write_text("\n".join(bloques), encoding="utf-8")
    return banco / "I.1.md"


def test_el_recuperador_conserva_el_apunte_y_extrae_diez_preguntas(tmp_path: Path) -> None:
    apunte = _apunte(tmp_path)
    banco = _banco(tmp_path)

    titulo, apartados, tablas, fuentes = parse_apunte(apunte)
    assert "Tema de prueba" in titulo
    assert apartados >= 2
    assert tablas >= 1
    assert any("origen.pdf" in fuente for fuente in fuentes)

    preguntas = parse_question_bank(banco)
    assert len(preguntas) == 12
    elegidas = seleccionar(preguntas)
    assert len(elegidas) == 10
    assert all(pregunta.correcta is not None for pregunta in elegidas)

    manifiesto = recover(source_root=tmp_path, out=tmp_path / "salida", extract_images=False)
    assert manifiesto["resumen"]["temas_recuperados"] == 1
    assert manifiesto["resumen"]["faltan"], "faltan los otros 32 temas TAI"
    assert (tmp_path / "salida" / "temas" / "I.1.md").is_file()
    assert (tmp_path / "salida" / "preguntas" / "I.1.json").is_file()
    preguntas_json = json.loads(
        (tmp_path / "salida" / "preguntas" / "I.1.json").read_text(encoding="utf-8")
    )
    assert len(preguntas_json) == 10
    assert all(pregunta["respuesta"] for pregunta in preguntas_json)
    assert "no publicar" in (tmp_path / "salida" / "temas" / "I.1.md").read_text(encoding="utf-8")
