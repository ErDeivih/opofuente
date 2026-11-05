"""Generador del fixture de convocatorias C1 (B-006), sin base de datos.

Comprueba el criterio de importación con fuentes sintéticas (solo entran convocatorias de grupo C1
con enlace; el TAI se descarta porque ya está sembrado) y la coherencia del fixture real.
"""

from __future__ import annotations

from pathlib import Path

from opofuente.infrastructure.convocatorias_fixture_loader import load_c1_convocatorias
from opofuente.tools import build_c1_convocatorias_fixtures as generador

FUENTE = generador.Source(
    id="c1-agregador",
    document="fuentes/oposicionesinformatica/c1.txt",
    local_path=Path("data/sources/c1.txt"),
    sha256="a" * 64,
    observed_at="2026-11-02",
)


def test_el_listado_se_lee_por_pares_de_titulo_y_enlace() -> None:
    texto = (
        "- 1 Plaza De Técnico/A Auxiliar De Informática, Ayuntamiento De Sallent, Barcelona\n"
        "https://oposicionesinformatica.com/1-plaza-sallent/\n"
        "- 2 Plazas De Técnicos/As Auxiliares De Informática — Bolsa\n"
        "https://oposicionesinformatica.com/2-plazas-bolsa/\n"
    )

    convocatorias = generador._parse_listado(texto, FUENTE)

    assert len(convocatorias) == 2
    assert {item.status for item in convocatorias} == {"draft"}
    assert all(item.published_at == "2026-11-02" for item in convocatorias)
    assert all("sin bases oficiales verificadas" in item.source_reference for item in convocatorias)
    assert convocatorias[0].administration == "Ayuntamiento De Sallent"
    assert convocatorias[0].territory == "Barcelona"
    assert len({item.code for item in convocatorias}) == 2
    assert convocatorias[0].official_url.startswith("https://oposicionesinformatica.com/")


def test_el_inventario_importa_solo_c1_con_enlace_y_descarta_con_motivo() -> None:
    texto = (
        "administracion;ambito;puesto;grupo;titulacion;plazas;estado;plazo;publicacion;enlace;notas\n"
        "SACYL;Autonómico;Técnico Especialista en Informática (C1) - SALAMANCA;C1;FP;Bolsa;"
        "CERRADO;15/01/2026 (baremo provisional);BOP CyL;"
        "https://www.saludcastillayleon.es/salamanca;nota\n"
        "Estado (AGE) - TAI;Estatal;Cuerpo de Técnicos Auxiliares de Informática;C1;Bachillerato;"
        "1030;CERRADO;Inscripción hasta 09/01/2026;BOE 22/12/2025;"
        "https://administracion.gob.es/tai;nota\n"
        "Ayuntamiento de Sevilla;Local;Técnico/a Superior (informática);A1;Licenciatura;6;ABIERTO;"
        "Hasta 12/11/2026;BOP Sevilla;https://administracion.gob.es/sevilla;nota\n"
        "Diputación de Salamanca;Provincial;Bolsa TIC;Varios;Según puesto;Varios;VIGILAR;"
        "Según convocatoria;BOP;https://www.diputacionsalamanca.es/;nota\n"
    )

    convocatorias, descartadas = generador._parse_inventario(
        texto,
        generador.Source(
            id="convocatorias-csv",
            document="minicerebro/convocatorias.csv",
            local_path=Path("data/sources/convocatorias.csv"),
            sha256="b" * 64,
            observed_at="2026-10-29",
        ),
    )

    assert [item.code for item in convocatorias] == ["c1-sacyl-salamanca"]
    assert convocatorias[0].status == "archived"
    assert convocatorias[0].published_at == "2026-01-15"
    assert convocatorias[0].administration == "SACYL"
    assert convocatorias[0].territory == "SALAMANCA"
    motivos = [fila["reason"] for fila in descartadas]
    assert len(descartadas) == 3
    assert any("no es C1 (grupo=A1)" in motivo for motivo in motivos)
    assert any("no es C1 (grupo=Varios)" in motivo for motivo in motivos)
    assert any(
        "ya está sembrada como convocatoria del perfil TAI 2025" in motivo for motivo in motivos
    )


def test_el_fixture_real_tiene_doce_convocatorias_y_deja_constancia_de_los_descartes() -> None:
    fixture = load_c1_convocatorias()

    assert fixture.opposition_code == "informatica-c1"
    assert len(fixture.convocatorias) == 12
    assert len(fixture.discarded) == 21
    assert len(fixture.sources) == 2
    assert {item.status for item in fixture.convocatorias} == {"draft", "archived"}
    assert sum(1 for item in fixture.convocatorias if item.status == "draft") == 10
    assert sum(1 for item in fixture.convocatorias if item.status == "archived") == 2
    assert all(item.source_reference.strip() for item in fixture.convocatorias)
    assert all(item.official_url.startswith("https://") for item in fixture.convocatorias)
    assert "tai-age-2025" not in {item.code for item in fixture.convocatorias}
    assert all(item.reason.strip() for item in fixture.discarded)
