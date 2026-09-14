"""Pruebas de los fixtures de perfil: procedencia, recuentos y reglas de examen.

Estas pruebas defienden los criterios de aceptación de S01 sobre los datos sembrados:

- TAI tiene exactamente 4 bloques y 33 temas;
- Guardia Civil tiene 25 temas y sus partes escritas configuradas;
- todo dato numérico tiene su cita, y lo que la convocatoria no publica se queda sin valor.
"""

from __future__ import annotations

import json

import pytest

from opofuente.config import project_root
from opofuente.domain.profiles import NodeType, PartKind, RuleKind, count_by_type, flatten
from opofuente.infrastructure.fixture_loader import load_profiles

FIXTURES = project_root() / "fixtures" / "profiles"


@pytest.fixture(scope="module")
def profiles():
    return {profile.convocation.code: profile for profile in load_profiles(FIXTURES)}


def test_se_cargan_los_dos_perfiles_oficiales(profiles) -> None:
    assert set(profiles) == {"tai-age-2025", "gc-cabos-guardias-2026"}


def test_manifiesto_declara_las_fuentes_y_sus_derechos() -> None:
    manifest = json.loads((FIXTURES / "manifest.json").read_text(encoding="utf-8"))
    sources = {source["id"]: source for source in manifest["sources"]}
    for source_id in (
        "tai-boe-convocatoria-xml",
        "gc-boe-convocatoria-xml",
        "gc-boe-convocatoria-pdf",
        "gc-temario-oficial-pdf",
        "boe-aviso-legal-html",
        "gc-nota-legal-html",
    ):
        source = sources[source_id]
        assert source["canonical_url"].startswith("https://")
        assert len(source["sha256"]) == 64
        assert source["rights_status"]
        assert source["rights_note"]
        assert source["retrieved_at"]
    # El temario de Guardia Civil está limitado a uso privado: la aplicación no puede publicarlo.
    assert sources["gc-temario-oficial-pdf"]["rights_status"] == "private_use_only"
    assert "uso privado" in sources["gc-temario-oficial-pdf"]["rights_quote"].lower()


def test_tai_tiene_cuatro_bloques_y_treinta_y_tres_temas(profiles) -> None:
    curriculum = profiles["tai-age-2025"].curriculum
    assert count_by_type(curriculum) == {
        NodeType.BLOCK: 4,
        NodeType.TOPIC: 33,
        NodeType.EPIGRAPH: 0,
    }
    bloques = list(curriculum)
    assert [node.official_code for node in bloques] == ["I", "II", "III", "IV"]
    for bloque in bloques:
        posiciones = [hijo.position for hijo in bloque.children]
        assert posiciones == list(range(1, len(bloque.children) + 1))
        assert all(hijo.node_type is NodeType.TOPIC for hijo in bloque.children)
    assert sum(len(node.children) for node in bloques) == 33


def test_guardia_civil_tiene_veinticinco_temas_con_bloques_y_epigrafes(profiles) -> None:
    curriculum = profiles["gc-cabos-guardias-2026"].curriculum
    counts = count_by_type(curriculum)
    # Cifras del documento oficial: se fijan para detectar cualquier cambio de la fuente.
    assert counts == {NodeType.BLOCK: 48, NodeType.TOPIC: 25, NodeType.EPIGRAPH: 125}
    temas = list(curriculum)
    assert [tema.official_code for tema in temas] == [str(n) for n in range(1, 26)]
    assert temas[0].title == "DERECHOS HUMANOS"
    assert temas[-1].title == "LENGUA ESPAÑOLA"
    for tema in temas:
        assert tema.children, f"el tema {tema.official_code} no tiene bloques"
        assert all(bloque.node_type is NodeType.BLOCK for bloque in tema.children)


def test_hay_bloques_sin_epigrafes_porque_el_temario_oficial_los_publica_asi(profiles) -> None:
    """El temario oficial lista temas cuyo bloque es solo la referencia legal.

    Por ejemplo, el tema 14 («Ministerio del Interior. Ministerio de Defensa») tiene dos bloques
    sin subitems. El fixture lo refleja tal cual: no se inventan epígrafes para rellenar.
    """
    curriculum = profiles["gc-cabos-guardias-2026"].curriculum
    bloques_sin_epigrafes = [
        (tema.official_code, bloque.title)
        for tema in curriculum
        for bloque in tema.children
        if not bloque.children
    ]
    assert bloques_sin_epigrafes, "el documento oficial sí tiene bloques sin epígrafes"
    tema_14 = next(tema for tema in curriculum if tema.official_code == "14")
    assert [bloque.title for bloque in tema_14.children] == [
        "Bloque 1. Estructura orgánica básica del Ministerio del Interior.",
        "Bloque 2. Estructura orgánica básica del Ministerio de Defensa.",
    ]


def test_tai_queda_activo_al_sembrar(profiles) -> None:
    """El fixture declara qué oposición queda activa; no se decide en el código."""
    tai = profiles["tai-age-2025"]
    gc = profiles["gc-cabos-guardias-2026"]
    assert tai.opposition.active is True
    assert gc.opposition.active is False


def test_tai_configura_sus_dos_partes_y_su_tiempo(profiles) -> None:
    parts = {part.code: part for part in profiles["tai-age-2025"].parts}
    assert parts["ejercicio_unico"].kind is PartKind.GROUP
    assert parts["ejercicio_unico"].time_minutes == 120
    primera = parts["primera_parte"]
    assert (primera.ordinary_items, primera.reserve_items) == (80, 5)
    assert (primera.score_min, primera.score_max, primera.pass_score) == (0, 50, 25)
    segunda = parts["segunda_parte"]
    assert (segunda.ordinary_items, segunda.reserve_items) == (20, 5)
    assert segunda.parent_code == "ejercicio_unico"


def test_tai_no_inventa_el_numero_de_alternativas(profiles) -> None:
    """La convocatoria no publica cuántas alternativas tiene cada pregunta: se deja sin valor."""
    for part in profiles["tai-age-2025"].parts:
        assert part.options_per_question is None


def test_tai_declara_que_la_calificacion_oficial_necesita_criterio_publicado(profiles) -> None:
    rules = {rule.code: rule for rule in profiles["tai-age-2025"].rules}
    regla = rules["official_scaled_score_requires_published_criteria"]
    assert regla.kind is RuleKind.BOOLEAN
    assert regla.value_text == "true"
    assert "baremos" in regla.evidence_quote
    assert rules["wrong_answer_penalty"].value_text == "1/3 del valor de una respuesta correcta"
    assert rules["blank_answer_penalty"].value_text == "0"


def test_guardia_civil_configura_sus_partes_escritas(profiles) -> None:
    parts = {part.code: part for part in profiles["gc-cabos-guardias-2026"].parts}
    assert parts["teorico_practico"].time_minutes == 140

    ortografia = parts["ortografia"]
    assert ortografia.format is not None and ortografia.format.value == "multi_mark_error"
    assert (ortografia.ordinary_items, ortografia.reserve_items) == (20, 4)
    assert ortografia.fail_if_errors_gte == 6
    # Apto o no apto: no tiene puntuación.
    assert ortografia.score_max is None

    assert parts["gramatica"].fail_if_errors_gte == 6

    conocimientos = parts["conocimientos_generales"]
    assert (conocimientos.ordinary_items, conocimientos.reserve_items) == (100, 5)
    assert (conocimientos.score_min, conocimientos.score_max, conocimientos.pass_score) == (
        0,
        100,
        50,
    )
    assert conocimientos.options_per_question == 4

    ingles = parts["lengua_inglesa"]
    assert (ingles.ordinary_items, ingles.reserve_items) == (20, 1)
    assert (ingles.score_max, ingles.pass_score) == (20, 8)

    aptitudes = parts["aptitudes_intelectuales"]
    assert (aptitudes.ordinary_items, aptitudes.time_minutes) == (80, 55)
    assert (aptitudes.score_max, aptitudes.pass_score) == (30, 12)


def test_guardia_civil_declara_la_formula_y_que_no_puntua_personalidad(profiles) -> None:
    rules = {rule.code: rule for rule in profiles["gc-cabos-guardias-2026"].rules}
    assert (
        rules["scoring_formula"].value_text == "Px = (Y / T) * (A - E / (N - 1)); Pf = suma de Px"
    )
    assert "100 100 4" in rules["scoring_formula"].evidence_quote
    assert rules["personality_scoring_supported"].value_text == "false"
    assert rules["psychophysical_not_prepared"].value_text == "true"


def test_todo_dato_numerico_tiene_cita_de_su_fuente(profiles) -> None:
    for profile in profiles.values():
        for part in profile.parts:
            assert part.evidence_quote.strip(), f"{profile.convocation.code}:{part.code}"
        for rule in profile.rules:
            assert rule.evidence_quote.strip(), f"{profile.convocation.code}:{rule.code}"


def test_el_programa_no_tiene_huecos_ni_titulos_vacios(profiles) -> None:
    for profile in profiles.values():
        for node, _parent in flatten(profile.curriculum):
            assert node.title.strip()
            assert node.path.strip()
            assert node.depth >= 0


def test_la_fecha_de_examen_no_se_inventa(profiles) -> None:
    for profile in profiles.values():
        assert profile.convocation.exam_date is None


def test_los_documentos_originales_no_estan_en_el_repositorio() -> None:
    """Los PDF y XML descargados viven en la caché local ignorada por git, no en fixtures."""
    extensiones = {path.suffix for path in FIXTURES.iterdir() if path.is_file()}
    assert extensiones == {".json"}
