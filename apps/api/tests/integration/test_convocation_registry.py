"""El registro versionado y su vínculo con los perfiles cargados.

Es integración porque junta tres piezas reales: el JSON versionado dentro del paquete, el loader y
los perfiles curados de `fixtures/profiles`. No usa base de datos: nada de lo que se comprueba aquí
depende de la siembra.
"""

from __future__ import annotations

import pytest

from opofuente.config import project_root
from opofuente.domain.convocation_registry import (
    Grupo,
    convocatorias_del_perfil,
    vincular_con_perfiles,
)
from opofuente.infrastructure.convocation_registry_loader import load_registry
from opofuente.infrastructure.fixture_loader import load_profiles

FIXTURES = project_root() / "fixtures" / "profiles"


@pytest.fixture(scope="module")
def registro():
    return load_registry()


@pytest.fixture(scope="module")
def perfiles():
    return load_profiles(FIXTURES)


def test_el_registro_trae_las_tres_convocatorias_tic_del_boe(registro) -> None:
    assert [entrada.code for entrada in registro.convocatorias] == [
        "csi-age-2025",
        "gsi-age-2025",
        "tai-age-2025",
    ]
    assert {entrada.grupo for entrada in registro.convocatorias} == {
        Grupo.A1,
        Grupo.A2,
        Grupo.C1,
    }


def test_las_cifras_del_registro_son_las_publicadas(registro) -> None:
    por_codigo = {entrada.code: entrada for entrada in registro.convocatorias}

    csi = por_codigo["csi-age-2025"]
    assert (csi.plazas_libres, csi.plazas_promocion_interna, csi.plazas_totales) == (290, 100, 390)

    gsi = por_codigo["gsi-age-2025"]
    assert (gsi.plazas_libres, gsi.plazas_promocion_interna, gsi.plazas_totales) == (634, 46, 680)

    tai = por_codigo["tai-age-2025"]
    assert (tai.plazas_libres, tai.plazas_promocion_interna, tai.plazas_totales) == (
        844,
        186,
        1030,
    )


def test_toda_entrada_tiene_procedencia_y_fuente_del_mismo_enlace(registro) -> None:
    fuentes = {fuente.id: fuente for fuente in registro.fuentes}
    for entrada in registro.convocatorias:
        assert entrada.procedencia.quote.strip()
        assert entrada.plazo_dias_habiles == 20
        assert fuentes[entrada.procedencia.source_id].canonical_url == entrada.enlace_oficial
        assert entrada.enlace_oficial.startswith("https://www.boe.es/")


def test_el_boe_es_la_unica_fuente_de_autoridad_del_registro(registro) -> None:
    assert len(registro.fuentes) == 2
    for fuente in registro.fuentes:
        assert fuente.identifier.startswith("BOE-A-2025-")
        assert fuente.authority_tier.value == "A"
        assert fuente.rights_status.value == "reuse_with_conditions"


def test_solo_tai_tiene_perfil_entre_las_tres_convocatorias(registro, perfiles) -> None:
    vinculos = dict(vincular_con_perfiles(registro.convocatorias, perfiles))

    assert set(vinculos) == {"tai-age"}
    assert [entrada.code for entrada in vinculos["tai-age"]] == ["tai-age-2025"]


def test_el_vinculo_es_por_nombre_de_cuerpo_no_por_codigo(registro, perfiles) -> None:
    tai = next(perfil for perfil in perfiles if perfil.opposition.code == "tai-age")
    assert [entrada.code for entrada in convocatorias_del_perfil(tai, registro.convocatorias)] == [
        "tai-age-2025"
    ]


def test_un_cuerpo_sin_perfil_no_rompe_el_vinculo(registro, perfiles) -> None:
    """A1 y A2 están en el registro aunque la aplicación todavía no prepare su temario."""
    vinculadas = [
        entrada.code
        for _codigo, entradas in vincular_con_perfiles(registro.convocatorias, perfiles)
        for entrada in entradas
    ]
    assert vincular_con_perfiles(registro.convocatorias, perfiles)
    assert "csi-age-2025" not in vinculadas
    assert "gsi-age-2025" not in vinculadas
