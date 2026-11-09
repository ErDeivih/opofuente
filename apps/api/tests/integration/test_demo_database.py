"""La base de demostración sirve temario y banco, y no publica perfiles de uso privado.

Es la base que el Dockerfile empaqueta para la demo pública. Este test la construye de verdad en
un directorio temporal y comprueba lo que la demo promete: temario común completo, un conjunto con
sus preguntas y su clave activa, y **ningún** perfil de Guardia Civil ni Celador (DEBT-003).
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from opofuente.tools.build_demo_database import build_demo_database


def test_la_base_de_demo_tiene_temario_y_banco_sin_perfiles_privados(tmp_path: Path) -> None:
    out = tmp_path / "demo.sqlite3"
    counts = build_demo_database(out=out, workdir=tmp_path / "trabajo")

    assert counts["curriculum_nodes"] >= 45, "falta el temario común (5 bloques / 40 temas)"
    assert counts["question_sets"] == 1
    assert counts["questions"] == 40, "hay una pregunta sintética por tema del común"
    assert counts["answer_keys"] == 40, "las preguntas entran con su clave"
    assert counts["imported"] == 40
    assert out.is_file()

    conexion = sqlite3.connect(out)
    try:
        codigos = {fila[0] for fila in conexion.execute("SELECT code FROM oppositions")}
        assert "tai-age" in codigos
        assert "informatica-c1" in codigos, "las convocatorias C1 referencian el temario común"
        assert not any("guardia" in codigo or "celador" in codigo for codigo in codigos), (
            "la demo no debe sembrar oposiciones de uso privado"
        )

        temas = conexion.execute(
            "SELECT count(*) FROM curriculum_nodes n "
            "JOIN curriculum_versions cv ON cv.id = n.curriculum_version_id "
            "WHERE cv.code = 'informatica-c1-v1' AND n.node_type = 'topic'"
        ).fetchone()[0]
        assert temas == 40

        conjuntos = conexion.execute("SELECT title, status FROM question_sets").fetchall()
        assert len(conjuntos) == 1
        assert "demostración" in conjuntos[0][0].lower()
        assert conjuntos[0][1] == "confirmed", "el banco de la demo no debe quedar en borrador"

        activas = conexion.execute(
            "SELECT count(*) FROM answer_key_versions WHERE status = 'active'"
        ).fetchone()[0]
        assert activas >= 1, "el banco de la demo debe tener una clave activa"
    finally:
        conexion.close()
