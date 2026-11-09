"""La base de demostración sirve temario, banco y un tema completo con su práctica.

Es la base que el Dockerfile empaqueta para la demo pública. Este test la construye de verdad en
un directorio temporal y comprueba lo que la demo promete: temario común completo, un banco
sintético, el tema I.1 con apuntes propios y una práctica terminable, y **ningún** perfil de Guardia
Civil ni Celador (DEBT-003).
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from opofuente.tools.build_demo_database import build_demo_database


def test_la_base_de_demo_tiene_temario_banco_y_un_tema_completo(tmp_path: Path) -> None:
    out = tmp_path / "demo.sqlite3"
    counts = build_demo_database(out=out, workdir=tmp_path / "trabajo")

    assert counts["curriculum_nodes"] >= 45, "falta el temario común (5 bloques / 40 temas)"
    assert counts["question_sets"] == 2, "banco sintético + práctica del tema de demo"
    assert counts["questions"] == 50, "40 del banco + 10 de la práctica del tema"
    assert counts["answer_keys"] == 50, "las preguntas entran con su clave"
    assert counts["imported"] == 50
    assert counts["tema_questions"] == 10
    assert counts["apuntes_chars"] > 1000, "el tema de demo necesita apuntes de verdad"
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

        apuntes = conexion.execute(
            "SELECT description FROM curriculum_nodes n "
            "JOIN curriculum_versions cv ON cv.id = n.curriculum_version_id "
            "WHERE cv.code = 'informatica-c1-v1' AND n.path = 'I.1'"
        ).fetchone()[0]
        assert apuntes is not None
        assert len(apuntes) > 1000, "el tema I.1 debe tener un desarrollo, no una línea"
        assert "Constitución" in apuntes

        conjuntos = {
            fila[0]: (fila[1], fila[2])
            for fila in conexion.execute("SELECT title, status, set_type FROM question_sets")
        }
        assert len(conjuntos) == 2
        banco = next(titulo for titulo in conjuntos if "Banco de demostración" in titulo)
        practica = next(titulo for titulo in conjuntos if "Tema I.1" in titulo)
        assert conjuntos[banco][0] == "confirmed", "el banco no debe quedar en borrador"
        assert conjuntos[practica][0] == "confirmed", "la práctica no debe quedar en borrador"
        assert conjuntos[practica][1] == "practice"

        preguntas_tema = conexion.execute(
            "SELECT count(*) FROM question_versions qv "
            "JOIN question_sets qs ON qs.id = qv.question_set_id WHERE qs.title = ?",
            (practica,),
        ).fetchone()[0]
        assert preguntas_tema == 10

        activas = conexion.execute(
            "SELECT count(*) FROM answer_key_versions WHERE status = 'active'"
        ).fetchone()[0]
        assert activas >= 2, "el banco y la práctica necesitan su clave activa"
    finally:
        conexion.close()
