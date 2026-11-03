"""Reglas de coherencia del registro de convocatorias y errores de carga.

Lo que se defiende aquí es que un registro mal formado no se pueda publicar como si fuera oficial:
enlace que no es del BOE, procedencia ausente, fuente inexistente, cifras imposibles o campos que
el esquema no conoce.
"""

from __future__ import annotations

import dataclasses
import json
from datetime import date
from pathlib import Path

import pytest

from opofuente.domain.classification import AuthorityTier, RightsStatus
from opofuente.domain.convocation_registry import (
    ConvocatoriaRegistrada,
    FuenteOficial,
    Grupo,
    Procedencia,
    SistemaAcceso,
    validate_registry,
)
from opofuente.domain.errors import InvariantViolationError
from opofuente.infrastructure.convocation_registry_loader import (
    default_registry_path,
    load_registry,
)

FUENTE = FuenteOficial(
    id="boe-a-2025-26262",
    title="Resolución de 18 de diciembre de 2025",
    publisher="Agencia Estatal Boletín Oficial del Estado",
    identifier="BOE-A-2025-26262",
    canonical_url="https://www.boe.es/diario_boe/txt.php?id=BOE-A-2025-26262",
    authority_tier=AuthorityTier.A,
    rights_status=RightsStatus.REUSE_WITH_CONDITIONS,
    published_at=date(2025, 12, 22),
)

ENTRADA = ConvocatoriaRegistrada(
    code="tai-age-2025",
    cuerpo="Cuerpo de Técnicos Auxiliares de Informática de la Administración del Estado",
    grupo=Grupo.C1,
    administracion="Administración General del Estado",
    sistemas=(SistemaAcceso.OPOSICION, SistemaAcceso.CONCURSO_OPOSICION),
    plazas_libres=844,
    plazas_promocion_interna=186,
    plazo_dias_habiles=20,
    enlace_oficial="https://www.boe.es/diario_boe/txt.php?id=BOE-A-2025-26262",
    published_at=date(2025, 12, 22),
    procedencia=Procedencia(
        source_id="boe-a-2025-26262",
        quote="Las plazas convocadas se ajustan a lo dispuesto en los siguientes cuadros:",
    ),
)


def test_un_registro_coherente_se_acepta() -> None:
    validate_registry((ENTRADA,), (FUENTE,))


def test_plazas_totales_suma_libre_y_promocion_interna() -> None:
    assert ENTRADA.plazas_totales == 1030


@pytest.mark.parametrize(
    "enlace",
    [
        "http://www.boe.es/diario_boe/txt.php?id=BOE-A-2025-26262",
        "https://example.com/diario_boe/txt.php?id=BOE-A-2025-26262",
        "https://boe.es.example.com/diario_boe/txt.php?id=BOE-A-2025-26262",
    ],
)
def test_un_enlace_que_no_es_oficial_se_rechaza(enlace: str) -> None:
    with pytest.raises(InvariantViolationError, match="no es oficial"):
        validate_registry((dataclasses.replace(ENTRADA, enlace_oficial=enlace),), (FUENTE,))


def test_una_cita_vacia_se_rechaza() -> None:
    entrada = dataclasses.replace(ENTRADA, procedencia=Procedencia("boe-a-2025-26262", "   "))
    with pytest.raises(InvariantViolationError, match="no cita su fuente"):
        validate_registry((entrada,), (FUENTE,))


def test_una_fuente_inexistente_se_rechaza() -> None:
    entrada = dataclasses.replace(ENTRADA, procedencia=Procedencia("boe-inexistente", "cita"))
    with pytest.raises(InvariantViolationError, match="no está en el registro"):
        validate_registry((entrada,), (FUENTE,))


def test_el_enlace_debe_coincidir_con_el_de_su_fuente() -> None:
    entrada = dataclasses.replace(
        ENTRADA,
        enlace_oficial="https://www.boe.es/diario_boe/txt.php?id=BOE-A-2025-25938",
    )
    with pytest.raises(InvariantViolationError, match="no coincide"):
        validate_registry((entrada,), (FUENTE,))


def test_no_se_repiten_codigos() -> None:
    with pytest.raises(InvariantViolationError, match="repetida"):
        validate_registry((ENTRADA, ENTRADA), (FUENTE,))


def test_el_codigo_debe_ser_un_slug() -> None:
    with pytest.raises(InvariantViolationError, match="slug"):
        validate_registry((dataclasses.replace(ENTRADA, code="TAI AGE 2025"),), (FUENTE,))


@pytest.mark.parametrize(
    ("cambios", "mensaje"),
    [
        ({"sistemas": ()}, "no declara sistema"),
        (
            {"sistemas": (SistemaAcceso.OPOSICION, SistemaAcceso.OPOSICION)},
            "sistemas de acceso repetidos",
        ),
        ({"plazas_libres": 0, "plazas_promocion_interna": 0}, "no convoca plazas"),
        ({"plazas_libres": -1}, "plazas libres negativas"),
        ({"plazas_promocion_interna": -1}, "promoción interna negativas"),
        ({"plazo_dias_habiles": 0}, "plazo"),
        ({"cuerpo": "  "}, "no dice el cuerpo"),
        ({"administracion": ""}, "no dice administración"),
    ],
)
def test_las_cifras_y_textos_imposibles_se_rechazan(
    cambios: dict[str, object], mensaje: str
) -> None:
    with pytest.raises(InvariantViolationError, match=mensaje):
        validate_registry((dataclasses.replace(ENTRADA, **cambios),), (FUENTE,))


def test_un_registro_sin_convocatorias_se_rechaza() -> None:
    with pytest.raises(InvariantViolationError, match="está vacío"):
        validate_registry((), (FUENTE,))


def test_el_loader_rechaza_campos_desconocidos(tmp_path: Path) -> None:
    datos = json.loads(default_registry_path().read_text(encoding="utf-8"))
    datos["convocations"][0]["campo_inventado"] = True
    destino = tmp_path / "convocation-registry.json"
    destino.write_text(json.dumps(datos), encoding="utf-8")

    with pytest.raises(InvariantViolationError, match="no cumple el formato"):
        load_registry(destino)


def test_el_loader_lee_el_mismo_json_desde_otra_ruta(tmp_path: Path) -> None:
    """El loader recibe la ruta por parámetro: sirve igual para pruebas y para el fichero real."""
    destino = tmp_path / "copia.json"
    destino.write_text(default_registry_path().read_text(encoding="utf-8"), encoding="utf-8")

    registro = load_registry(destino)

    assert registro.convocatorias == load_registry().convocatorias


def test_el_loader_avisa_si_falta_el_fichero(tmp_path: Path) -> None:
    with pytest.raises(InvariantViolationError, match="falta el registro"):
        load_registry(tmp_path / "no-existe.json")


def test_promocion_interna_ausente_queda_como_nula(tmp_path: Path) -> None:
    datos = json.loads(default_registry_path().read_text(encoding="utf-8"))
    del datos["convocations"][0]["plazas_promocion_interna"]
    destino = tmp_path / "convocation-registry.json"
    destino.write_text(json.dumps(datos), encoding="utf-8")

    registro = load_registry(destino)

    assert registro.convocatorias[0].plazas_promocion_interna is None
    assert registro.convocatorias[0].plazas_totales == registro.convocatorias[0].plazas_libres
