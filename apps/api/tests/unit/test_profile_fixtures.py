"""Pruebas de los fixtures de perfil: procedencia, recuentos y reglas de examen.

Estas pruebas defienden los criterios de aceptación de S01 sobre los datos sembrados:

- TAI tiene exactamente 4 bloques y 33 temas;
- Guardia Civil tiene 25 temas y sus partes escritas configuradas;
- Celador (SACYL) tiene 16 temas sin bloques y un ejercicio único de 70 preguntas más 7 de reserva;
- todo dato numérico tiene su cita, y lo que la convocatoria no publica se queda sin valor.
"""

from __future__ import annotations

import json
from datetime import date

import pytest

from opofuente.config import project_root
from opofuente.domain.profiles import (
    ConvocationStatus,
    NodeType,
    PartKind,
    RuleKind,
    count_by_type,
    flatten,
)
from opofuente.infrastructure.fixture_loader import load_profiles

FIXTURES = project_root() / "fixtures" / "profiles"


@pytest.fixture(scope="module")
def profiles():
    return {profile.convocation.code: profile for profile in load_profiles(FIXTURES)}


def test_se_cargan_los_cuatro_perfiles_oficiales(profiles) -> None:
    assert set(profiles) == {
        "tai-age-2025",
        "gc-cabos-guardias-2026",
        "celador-sacyl-2022",
        "celador-sacyl-estabilizacion-2022",
    }


def test_las_dos_convocatorias_de_celador_son_la_misma_oposicion(profiles) -> None:
    """Compartir oposición no es compartir convocatoria.

    La siembra identifica la oposición por su código y **actualiza** su nombre y su descripción con
    lo que declara el fixture que se está sembrando. Si los dos ficheros de Celador no dijeran
    exactamente lo mismo, el último en sembrarse reescribiría la oposición y el resultado dependería
    del orden de los ficheros. Esta prueba fija que digan lo mismo.
    """
    acceso_libre = profiles["celador-sacyl-2022"].opposition
    estabilizacion = profiles["celador-sacyl-estabilizacion-2022"].opposition
    assert acceso_libre.code == estabilizacion.code == "celador-sacyl"
    assert acceso_libre.name == estabilizacion.name
    assert acceso_libre.description == estabilizacion.description
    assert acceso_libre.active is estabilizacion.active is False


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
        "celador-2022-bocyl-orden-html",
        "celador-2022-bocyl-orden-pdf",
        "celador-2023-bocyl-resolucion-salamanca-html",
        "celador-2022-cuestionario-pdf",
        "celador-2022-plantilla-respuestas-pdf",
        "celador-2023-cuestionario-aplazado-pdf",
        "celador-2022-bocyl-estabilizacion-html",
        "bocyl-aviso-legal-html",
        "saludcastillayleon-aviso-legal-html",
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
    # Las fuentes del BOCYL no publican condiciones de reutilización: se declaran desconocidas en
    # lugar de dar por supuesto un permiso que nadie ha concedido.
    assert sources["celador-2022-bocyl-orden-html"]["rights_status"] == "unknown"
    assert sources["celador-2022-cuestionario-pdf"]["rights_status"] == "unknown"


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
    """Una convocatoria sin fecha publicada se queda sin fecha; una con fecha la cita.

    TAI y Guardia Civil no publican el día del ejercicio en sus bases: se quedan a nulo. Celador
    sí lo tiene, porque el BOCYL publicó la resolución que lo fija, y la fecha del fixture tiene
    que ser exactamente la que esa resolución dice.
    """
    assert profiles["tai-age-2025"].convocation.exam_date is None
    assert profiles["gc-cabos-guardias-2026"].convocation.exam_date is None

    celador = profiles["celador-sacyl-2022"]
    assert celador.convocation.exam_date == date(2023, 11, 12)
    regla = next(rule for rule in celador.rules if rule.code == "published_exam_date")
    assert regla.value_text == celador.convocation.exam_date.isoformat()
    assert regla.evidence_quote.startswith("para la realización del ejercicio de la fase")


def test_celador_tiene_dieciseis_temas_sin_bloques(profiles) -> None:
    """El programa oficial de Celador son dieciséis temas que no cuelgan de ningún bloque."""
    curriculum = profiles["celador-sacyl-2022"].curriculum
    assert count_by_type(curriculum) == {
        NodeType.BLOCK: 0,
        NodeType.TOPIC: 16,
        NodeType.EPIGRAPH: 0,
    }
    temas = list(curriculum)
    assert [tema.official_code for tema in temas] == [str(n) for n in range(1, 17)]
    assert [tema.path for tema in temas] == [str(n) for n in range(1, 17)]
    assert all(tema.depth == 0 for tema in temas)
    assert all(not tema.children for tema in temas)
    assert temas[0].title.startswith("Estructura de la Consejería de Sanidad.")
    assert temas[6].title == (
        "La atención al usuario. El derecho a la información y a la confidencialidad."
    )
    assert temas[-1].title.startswith("Plan de emergencias ante incendios.")


def test_celador_configura_su_ejercicio_unico(profiles) -> None:
    parts = {part.code: part for part in profiles["celador-sacyl-2022"].parts}
    assert set(parts) == {"ejercicio_unico"}
    ejercicio = parts["ejercicio_unico"]
    assert ejercicio.kind is PartKind.TEST
    assert ejercicio.format is not None and ejercicio.format.value == "single_choice"
    assert (ejercicio.ordinary_items, ejercicio.reserve_items) == (70, 7)
    assert ejercicio.options_per_question == 4
    assert (ejercicio.score_min, ejercicio.score_max) == (0, 150)
    assert ejercicio.wrong_penalty_fraction == 0.25
    assert ejercicio.time_minutes == 90
    # No hay nota de corte fija: el umbral es relativo a las diez mejores puntuaciones.
    assert ejercicio.pass_score is None


def test_cada_cifra_del_ejercicio_de_celador_tiene_su_regla(profiles) -> None:
    """El tiempo también es una cifra: se cita, no se deja sin respaldo.

    TAI declara 120 minutos sin una regla que los cite (su cita habla de las dos partes); aquí el
    tiempo tiene su propia regla con la frase literal de la convocatoria, y esta prueba impide que
    vuelva a quedarse sin ella.
    """
    perfil = profiles["celador-sacyl-2022"]
    reglas = {rule.code: rule for rule in perfil.rules}
    tiempo = reglas["exercise_total_time"]
    assert tiempo.value_text == str(perfil.parts[0].time_minutes)
    assert "90 minutos" in tiempo.evidence_quote


def test_celador_declara_el_umbral_relativo_y_las_reglas_del_proceso(profiles) -> None:
    rules = {rule.code: rule for rule in profiles["celador-sacyl-2022"].rules}
    umbral = rules["pass_threshold_relative_to_top_ten"]
    assert umbral.kind is RuleKind.TEXT
    assert umbral.value_text == "60 % de la media de las 10 puntuaciones más altas"
    assert "no lo estima" in umbral.description
    assert rules["wrong_answer_penalty"].value_text == "1/4 del valor de una respuesta correcta"
    assert rules["blank_answer_penalty"].value_text == "0"
    assert rules["convoked_places"].value_text == "420"
    assert rules["same_exercise_both_turns"].value_text == "true"
    assert rules["published_questionnaire_matches_bases"].value_text == "true"
    assert "77 preguntas" in rules["published_questionnaire_matches_bases"].evidence_quote


def test_celador_no_queda_activo_al_sembrar(profiles) -> None:
    """Añadir un perfil no cambia qué oposición está activa: lo decide el fixture."""
    celador = profiles["celador-sacyl-2022"]
    assert celador.opposition.active is False
    # La vigente sigue siendo la convocatoria ordinaria: es el perfil de estudio mientras el
    # proceso de estabilización no tenga ejercicio. La de estabilización queda «disponible»: está
    # publicada y se puede estudiar, pero no es la que la aplicación usa para trabajar.
    assert celador.convocation.status is ConvocationStatus.ACTIVE
    estabilizacion = profiles["celador-sacyl-estabilizacion-2022"]
    assert estabilizacion.convocation.status is ConvocationStatus.AVAILABLE
    assert estabilizacion.opposition.code == celador.opposition.code


def test_la_estabilizacion_de_celador_tiene_catorce_temas_en_dos_partes(profiles) -> None:
    """El ANEXO V trae el temario de todas las categorías: el de Celador son dos partes y 14."""
    curriculum = profiles["celador-sacyl-estabilizacion-2022"].curriculum
    assert count_by_type(curriculum) == {
        NodeType.BLOCK: 2,
        NodeType.TOPIC: 14,
        NodeType.EPIGRAPH: 0,
    }
    general, especifica = list(curriculum)
    assert (general.path, general.title, len(general.children)) == ("1", "Parte general", 5)
    assert (especifica.path, especifica.title, len(especifica.children)) == (
        "2",
        "Parte específica",
        9,
    )
    assert [hijo.official_code for hijo in general.children] == [f"Tema {n}" for n in range(1, 6)]
    assert [hijo.official_code for hijo in especifica.children] == [
        f"Tema {n}" for n in range(6, 15)
    ]
    assert [hijo.path for hijo in especifica.children] == [f"2.{n}" for n in range(1, 10)]
    # La posición es la del hijo dentro de su parte (el tema 6 abre la parte específica), mientras
    # que el número que publica la convocatoria viaja en `official_code`.
    assert [hijo.position for hijo in general.children] == list(range(1, 6))
    assert [hijo.position for hijo in especifica.children] == list(range(1, 10))
    assert general.children[0].title.startswith("Estructura orgánica de los Servicios Centrales")
    assert especifica.children[0].title.startswith("Funciones de vigilancia.")
    assert especifica.children[-1].title.startswith("Plan de emergencias ante incendios.")


def test_la_estabilizacion_configura_su_ejercicio_de_cuarenta_y_cuatro_preguntas(profiles) -> None:
    parts = {part.code: part for part in profiles["celador-sacyl-estabilizacion-2022"].parts}
    assert set(parts) == {"ejercicio_unico"}
    ejercicio = parts["ejercicio_unico"]
    assert ejercicio.kind is PartKind.TEST
    assert (ejercicio.ordinary_items, ejercicio.reserve_items) == (40, 4)
    assert ejercicio.options_per_question == 3
    assert (ejercicio.score_min, ejercicio.score_max) == (0, 150)
    assert ejercicio.time_minutes == 60
    assert ejercicio.pass_score is None
    # 1/9 no es exacto en coma flotante: el campo lleva el valor redondeado y la regla, el texto.
    assert ejercicio.wrong_penalty_fraction == pytest.approx(1 / 9)


def test_la_estabilizacion_declara_sus_reglas_con_cita(profiles) -> None:
    rules = {rule.code: rule for rule in profiles["celador-sacyl-estabilizacion-2022"].rules}
    assert rules["convoked_places"].value_text == "406"
    assert "343" in rules["convoked_places"].description
    assert "CELADOR 343 63 57 6 406" in rules["convoked_places"].evidence_quote
    assert rules["wrong_answer_penalty"].value_text == "1/9 del valor de una respuesta correcta"
    assert rules["blank_answer_penalty"].value_text == "0"
    assert rules["max_general_questions"].value_text == "15"
    assert rules["three_options_one_correct"].value_text == "3"
    assert rules["questionnaire_size"].value_text == "44"
    assert rules["exercise_total_time"].value_text == "60"
    # La cifra del tiempo y la del cuestionario salen de la misma fila del ANEXO I.
    assert "OTRO PERSONAL 44 60" in rules["exercise_total_time"].evidence_quote
    assert rules["pass_threshold_relative_to_top_ten"].kind is RuleKind.TEXT
    assert "no lo estima" in rules["pass_threshold_relative_to_top_ten"].description
    assert rules["exam_date_fixed_later"].value_text == "true"
    assert "anexo V" in rules["curriculum_source"].evidence_quote


def test_la_estabilizacion_no_se_inventa_la_fecha_del_ejercicio(profiles) -> None:
    """La orden no publica el día: lo fijará la resolución de admitidos, y el fixture lo dice.

    Además lo sitúa en el tiempo: el plazo de solicitudes cerró en enero de 2023 (veinte días
    hábiles desde la publicación) y el proceso sigue pendiente de ejercicio, así que no se presenta
    como un examen disponible.
    """
    convocatoria = profiles["celador-sacyl-estabilizacion-2022"].convocation
    assert convocatoria.exam_date is None
    nota = convocatoria.source_note or ""
    assert "diez días hábiles" in nota
    assert "sigue sin ejercicio" in nota
    assert "enero de 2023" in nota


def test_la_estabilizacion_declara_cuando_cerro_el_plazo_de_solicitudes(profiles) -> None:
    rules = {rule.code: rule for rule in profiles["celador-sacyl-estabilizacion-2022"].rules}
    plazo = rules["application_deadline"]
    assert plazo.value_text == "20 días hábiles desde el día siguiente a la publicación"
    assert "5.1.1" in plazo.evidence_quote


def test_los_documentos_originales_no_estan_en_el_repositorio() -> None:
    """Los PDF y XML descargados viven en la caché local ignorada por git, no en fixtures."""
    extensiones = {path.suffix for path in FIXTURES.iterdir() if path.is_file()}
    assert extensiones == {".json"}
