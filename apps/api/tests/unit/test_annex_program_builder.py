"""Pruebas del parser de anexos de temario del BOE (`annex_program` y `a2_curriculum`).

Qué prueban y qué **no**: el XML de estas pruebas es un extracto sintético mínimo, escrito a mano,
con la forma que el parser declara (encabezado de anexo, apartado de programa, bloques en cursiva y
temas numerados). Sirven para fijar el contrato del parser: rutas, posiciones, profundidades y que
la partición en epígrafes no pierda texto. No demuestran que el ANEXO IX real de A2 tenga esa forma;
eso exige el documento oficial descargado y verificado, que este slice no tiene.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from opofuente.domain.errors import InvariantViolationError
from opofuente.tools.build_profile_fixtures import (
    A2_ANNEX,
    A2_PROGRAM,
    a2_curriculum,
    annex_program,
    tai_curriculum,
)

SINTETICO = """<?xml version="1.0" encoding="UTF-8"?>
<documento>
  <p class="anexo_num">ANEXO VIII</p>
  <p class="centro_negrita">3. Programa.</p>
  <p>1. Tema de otro anexo que no debe entrar.</p>
  <p class="anexo_num">{anexo}</p>
  <p class="centro_negrita">Temario</p>
  <p class="centro_negrita">1. Normas generales.</p>
  <p>9. Párrafo numerado antes del programa, que tampoco es un tema.</p>
  <p class="centro_negrita">{programa}</p>
  <p class="centro_cursiva">I. Bloque uno</p>
  <p>1. Tema uno. Epígrafe a. Epígrafe b.</p>
  <p>2. Tema con <i>cursiva</i>. Plataforma.NET sigue entero.</p>
  <p class="centro_cursiva">II. Bloque dos</p>
  <p>3. Tema tres. Sólo un epígrafe.</p>
  <p class="anexo_num">ANEXO X</p>
  <p class="centro_cursiva">I. Bloque ajeno</p>
  <p>1. Tema de un anexo posterior que no debe entrar.</p>
</documento>
"""


@pytest.fixture()
def xml_sintetico(tmp_path: Path) -> Path:
    path = tmp_path / "boe-sintetico.xml"
    contenido = SINTETICO.format(anexo="ANEXO IX", programa="3. Programa.")
    path.write_text(contenido, encoding="utf-8")
    return path


def programa_a2(path: Path) -> list[dict[str, Any]]:
    return annex_program(path, annex_heading=A2_ANNEX, program_heading=A2_PROGRAM)


def test_annex_program_extrae_bloques_temas_y_epigrafes(xml_sintetico: Path) -> None:
    bloques = programa_a2(xml_sintetico)

    assert [bloque["official_code"] for bloque in bloques] == ["I", "II"]
    assert [bloque["title"] for bloque in bloques] == ["Bloque uno", "Bloque dos"]
    assert [bloque["path"] for bloque in bloques] == ["I", "II"]
    assert [bloque["depth"] for bloque in bloques] == [0, 0]

    primero, segundo = bloques
    assert [tema["official_code"] for tema in primero["children"]] == ["1", "2"]
    assert [tema["title"] for tema in primero["children"]] == [
        "Tema uno. Epígrafe a. Epígrafe b.",
        "Tema con cursiva. Plataforma.NET sigue entero.",
    ]
    assert [tema["path"] for tema in primero["children"]] == ["I.1", "I.2"]
    assert [tema["position"] for tema in primero["children"]] == [1, 2]
    assert all(tema["depth"] == 1 for tema in primero["children"])

    # La segunda parte empieza en 1: `position` es la posición dentro del bloque y el número oficial
    # viaja en `official_code`, igual que en los demás programas.
    assert [tema["official_code"] for tema in segundo["children"]] == ["3"]
    assert [tema["position"] for tema in segundo["children"]] == [1]
    assert [tema["path"] for tema in segundo["children"]] == ["II.1"]


def test_annex_program_reparte_epigrafes_sin_perder_texto(xml_sintetico: Path) -> None:
    bloques = programa_a2(xml_sintetico)

    epigrafes = [
        hijo for bloque in bloques for tema in bloque["children"] for hijo in tema["children"]
    ]
    assert [(hijo["path"], hijo["title"]) for hijo in epigrafes] == [
        ("I.1.1", "Tema uno."),
        ("I.1.2", "Epígrafe a."),
        ("I.1.3", "Epígrafe b."),
        ("I.2.1", "Tema con cursiva."),
        ("I.2.2", "Plataforma.NET sigue entero."),
        ("II.1.1", "Tema tres."),
        ("II.1.2", "Sólo un epígrafe."),
    ]
    assert [hijo["position"] for hijo in epigrafes] == [1, 2, 3, 1, 2, 1, 2]
    assert all(hijo["depth"] == 2 for hijo in epigrafes)
    # Unir los epígrafes devuelve el título oficial: la partición no se come caracteres.
    for bloque in bloques:
        for tema in bloque["children"]:
            assert " ".join(hijo["title"] for hijo in tema["children"]) == tema["title"]


def test_annex_program_no_mezcla_anexos_ni_parrafos_previos(xml_sintetico: Path) -> None:
    bloques = programa_a2(xml_sintetico)

    titulos = [tema["title"] for bloque in bloques for tema in bloque["children"]]
    assert titulos == [
        "Tema uno. Epígrafe a. Epígrafe b.",
        "Tema con cursiva. Plataforma.NET sigue entero.",
        "Tema tres. Sólo un epígrafe.",
    ]
    assert not any("otro anexo" in titulo or "antes del programa" in titulo for titulo in titulos)


def test_annex_program_falla_si_no_encuentra_el_anexo(xml_sintetico: Path) -> None:
    with pytest.raises(InvariantViolationError, match="ANEXO XI"):
        annex_program(xml_sintetico, annex_heading="ANEXO XI", program_heading="3. Programa.")


def test_annex_program_falla_si_no_encuentra_el_apartado_de_programa(xml_sintetico: Path) -> None:
    with pytest.raises(InvariantViolationError, match="4. Programa"):
        annex_program(xml_sintetico, annex_heading="ANEXO IX", program_heading="4. Programa.")


def test_a2_curriculum_usa_el_anexo_ix_y_su_apartado_declarados(xml_sintetico: Path) -> None:
    assert (A2_ANNEX, A2_PROGRAM) == ("ANEXO IX", "3. Programa.")
    assert a2_curriculum(xml_sintetico) == programa_a2(xml_sintetico)


def test_tai_curriculum_sigue_leyendo_el_anexo_v(xml_sintetico: Path) -> None:
    """El parser compartido no cambia el contrato de TAI, pero TAI sigue atado a su ANEXO V."""
    with pytest.raises(InvariantViolationError, match="ANEXO V"):
        tai_curriculum(xml_sintetico)
