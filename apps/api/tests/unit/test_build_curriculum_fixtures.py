"""Pruebas del generador del fixture del temario común (B-002).

Son herméticas: fabrican un Markdown con la **misma forma** que `temario-c1.md` (cinco bloques y
cuarenta temas numerados) y comprueban que el generador extrae exactamente lo que hay, une las
líneas partidas, calcula las rutas `I.1`…`V.40` y **falla** si el documento pierde un tema. No
dependen de que la fuente real esté en la máquina: la comprobación contra la fuente real es la
puerta `build_curriculum_fixtures --check`.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from opofuente.domain.errors import InvariantViolationError
from opofuente.tools import build_curriculum_fixtures as generador

#: Los cinco bloques de la v1 con sus rangos de temas, como los publica la fuente.
RANGOS = (
    ("I", "Bloque uno", 1, 12),
    ("II", "Bloque dos", 13, 17),
    ("III", "Bloque tres", 18, 26),
    ("IV", "Bloque cuatro", 27, 33),
    ("V", "Bloque cinco", 34, 40),
)


def _markdown() -> str:
    lineas = ["# Temario de prueba", ""]
    for romano, titulo, primero, ultimo in RANGOS:
        lineas.append(f"## BLOQUE {romano} — {titulo} (temas {primero}-{ultimo})")
        lineas.append("")
        for numero in range(primero, ultimo + 1):
            lineas.append(f"{numero}. **Tema {numero}**: primera parte del tema {numero} que sigue")
            lineas.append(f"   en una segunda línea del mismo tema {numero}.")
        lineas.append("")
    lineas.extend(["---", "", "## Otra sección que no es temario", "", "1. No soy un tema."])
    return "\n".join(lineas) + "\n"


def test_el_generador_extrae_solo_los_bloques_del_temario() -> None:
    bloques = generador.parse_blocks(_markdown())

    assert [bloque.roman for bloque, _temas in bloques] == ["I", "II", "III", "IV", "V"]
    assert [len(temas) for _bloque, temas in bloques] == [12, 5, 9, 7, 7]
    assert [numero for _bloque, temas in bloques for numero, _texto in temas] == list(range(1, 41))


def test_el_generador_une_las_lineas_partidas_sin_cambiar_palabras() -> None:
    bloques = generador.parse_blocks(_markdown())
    primer_bloque, temas = bloques[0]
    numero, texto = temas[0]

    assert numero == 1
    assert (
        texto == "Tema 1: primera parte del tema 1 que sigue en una segunda línea del mismo tema 1."
    )
    assert primer_bloque.title == "Bloque uno"
    assert (primer_bloque.first_topic, primer_bloque.last_topic) == (1, 12)


def test_el_generador_calcula_rutas_y_codigos_oficiales() -> None:
    nodes = generador.build_nodes(generador.parse_blocks(_markdown()), "minicerebro/temario-c1.md")

    rutas = [nodo["path"] for bloque in nodes for nodo in bloque["children"]]
    assert rutas == [
        *(f"I.{numero}" for numero in range(1, 13)),
        *(f"II.{numero}" for numero in range(13, 18)),
        *(f"III.{numero}" for numero in range(18, 27)),
        *(f"IV.{numero}" for numero in range(27, 34)),
        *(f"V.{numero}" for numero in range(34, 41)),
    ]
    assert [nodo["official_code"] for bloque in nodes for nodo in bloque["children"]] == [
        str(numero) for numero in range(1, 41)
    ]
    assert nodes[0]["source_reference"] == (
        "minicerebro/temario-c1.md, BLOQUE I — Bloque uno (temas 1-12)"
    )


def test_un_temario_al_que_le_falta_un_tema_no_se_acepta() -> None:
    markdown = _markdown().replace(
        "7. **Tema 7**: primera parte del tema 7 que sigue\n"
        "   en una segunda línea del mismo tema 7.\n",
        "",
    )

    with pytest.raises(InvariantViolationError, match="se esperaban los temas"):
        generador.build_nodes(generador.parse_blocks(markdown), "minicerebro/temario-c1.md")


def test_la_fuente_se_comprueba_por_hash(tmp_path: Path) -> None:
    fuente = tmp_path / "temario.md"
    fuente.write_text("contenido distinto al manifestado", encoding="utf-8")
    source = generador.Source(
        id="temario-c1-md",
        document="minicerebro/temario-c1.md",
        local_path=fuente,
        sha256="0" * 64,
    )

    with pytest.raises(InvariantViolationError, match="no coincide con el manifiesto"):
        generador._verify_source(fuente, source)

    with pytest.raises(InvariantViolationError, match="falta la fuente"):
        generador._verify_source(tmp_path / "no-existe.md", source)
