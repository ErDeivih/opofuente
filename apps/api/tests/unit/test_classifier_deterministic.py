"""Pruebas unitarias del motor determinista de clasificación (S04).

El motor es puro: entra un `ClassificationSubject` y salen propuestas. Nada de base de datos ni de
red y nada de azar, así que todo lo que se comprueba aquí se puede reproducir a mano.
"""

from __future__ import annotations

from opofuente.domain.classification import (
    AuthorityTier,
    Axis,
    ClassificationSubject,
    DocumentType,
    ProfileCandidate,
    Proposal,
    RightsStatus,
    SubjectType,
    TopicCandidate,
)
from opofuente.infrastructure.classifiers import ENGINE_VERSION, DeterministicClassifier

MOTOR = DeterministicClassifier()


def _sujeto(**cambios: object) -> ClassificationSubject:
    base: dict[str, object] = {
        "subject_type": SubjectType.ARTIFACT,
        "subject_id": "art-1",
    }
    base.update(cambios)
    return ClassificationSubject(**base)  # type: ignore[arg-type]


def _por_eje(sujeto: ClassificationSubject) -> dict[Axis, Proposal]:
    return {propuesta.axis: propuesta for propuesta in MOTOR.propose(sujeto)}


def test_el_mismo_material_da_siempre_la_misma_propuesta() -> None:
    """Reproducible: dos ejecuciones sobre el mismo material no pueden diferir."""
    sujeto = _sujeto(
        original_name="Convocatoria TAI 2025.pdf",
        text="Bases de la convocatoria. Boletín Oficial del Estado. Anexo V: temario oficial.",
    )

    primera = MOTOR.propose(sujeto)
    segunda = MOTOR.propose(sujeto)

    assert primera == segunda
    assert MOTOR.name == "determinista"
    assert MOTOR.version == ENGINE_VERSION


def test_sin_senales_no_hay_propuesta() -> None:
    """Un eje sin evidencia no genera relleno: es «sin clasificar», no un `unknown`."""
    assert MOTOR.propose(_sujeto()) == ()


def test_la_convocatoria_del_boe_se_reconoce_y_se_cita_la_evidencia() -> None:
    sujeto = _sujeto(
        original_name="resolucion-convocatoria.pdf",
        text="Resolución de 12 de enero. Bases de la convocatoria publicadas en el Boletín "
        "Oficial del Estado.",
        origin_display="https://www.boe.es/diario_boe/txt.php?id=BOE-A-2025-1",
    )

    propuestas = _por_eje(sujeto)

    documento = propuestas[Axis.DOCUMENT_TYPE]
    autoridad = propuestas[Axis.AUTHORITY]
    assert documento.proposed_value == DocumentType.CONVOCATION.value
    assert documento.confidence >= 0.7
    assert documento.evidence
    assert autoridad.proposed_value == AuthorityTier.A.value
    assert autoridad.is_critical is True


def test_una_plantilla_de_respuestas_gana_al_examen_oficial() -> None:
    """Con las dos señales manda la más específica; el empate se rompe de forma estable."""
    sujeto = _sujeto(
        text="Examen oficial. Plantilla de respuestas: 1-A, 2-C, 3-B.",
    )

    propuestas = _por_eje(sujeto)

    assert propuestas[Axis.DOCUMENT_TYPE].proposed_value == DocumentType.ANSWER_KEY.value


def test_el_pegado_se_propone_como_apuntes_propios_con_confianza_baja() -> None:
    """Un pegado lo escribió el usuario: es una señal floja, no una certeza."""
    sujeto = _sujeto(origin_type="paste", text="Resumen de lo que he estudiado hoy.")

    propuestas = _por_eje(sujeto)

    documento = propuestas[Axis.DOCUMENT_TYPE]
    assert documento.proposed_value == DocumentType.PERSONAL_NOTES.value
    assert documento.confidence == 0.4


def test_el_nombre_del_fichero_no_inventa_autoridad() -> None:
    """`TAI 2025` no dice quién publica: sin señales, el eje de autoridad queda vacío."""
    propuestas = _por_eje(_sujeto(original_name="TAI 2025.pdf", text="Tema 1. La Constitución."))

    assert Axis.AUTHORITY not in propuestas
    assert Axis.RIGHTS not in propuestas


def test_las_condiciones_de_uso_se_proponen_como_documento_de_derechos() -> None:
    sujeto = _sujeto(
        original_name="aviso-legal.html",
        text="Condiciones de uso del portal. La reproducción está prohibida sin autorización.",
    )

    propuestas = _por_eje(sujeto)

    derechos = propuestas[Axis.RIGHTS]
    assert derechos.proposed_value in {
        RightsStatus.RIGHTS_DOCUMENT.value,
        RightsStatus.PRIVATE_USE_ONLY.value,
    }
    assert derechos.is_critical is True


def test_el_tema_se_propone_por_el_titulo_del_programa_y_se_guardan_alternativas() -> None:
    """Coincidencia de títulos (04 §7): los nodos que coinciden se ordenan y el resto se lista."""
    perfil = ProfileCandidate(
        opposition_code="tai-age-2025",
        opposition_name="Técnico Auxiliar de Informática",
        convocation_code="tai-age-2025",
        topics=(
            TopicCandidate(
                node_id="n1",
                path="bloque-4/tema-1",
                title="Protección de datos personales",
                depth=1,
            ),
            TopicCandidate(
                node_id="n2", path="bloque-4/tema-2", title="Seguridad de sistemas", depth=1
            ),
        ),
    )
    sujeto = _sujeto(
        text="Apuntes sobre protección de datos personales y seguridad de sistemas.",
        profiles=(perfil,),
    )

    propuestas = _por_eje(sujeto)

    tema = propuestas[Axis.TOPIC]
    # Empate a 0,8 (los dos títulos aparecen enteros): lo rompe la ruta, que es estable.
    assert tema.proposed_value == "bloque-4/tema-1"
    assert tema.confidence == 0.8
    assert tema.evidence
    assert [alternativa.value for alternativa in tema.alternatives] == ["bloque-4/tema-2"]


def test_un_titulo_con_menos_de_la_mitad_de_sus_palabras_no_sostiene_una_propuesta_de_tema() -> (
    None
):
    """El umbral documentado es el 50 %: por debajo no se propone nada, no se adivina el tema."""
    perfil = ProfileCandidate(
        opposition_code="tai-age-2025",
        opposition_name="Técnico Auxiliar de Informática",
        convocation_code="tai-age-2025",
        topics=(
            TopicCandidate(
                node_id="n1",
                path="bloque-4/tema-1",
                title="Protección de datos personales y seguridad",
                depth=1,
            ),
        ),
    )
    # 1 de 4 palabras significativas (protección): 25 %, por debajo del umbral.
    sujeto = _sujeto(text="Apuntes sobre protección.", profiles=(perfil,))

    assert Axis.TOPIC not in _por_eje(sujeto)


def test_justo_la_mitad_de_las_palabras_del_titulo_si_propone_tema() -> None:
    """El límite es inclusivo y así queda fijado: 2 de 4 palabras dan una propuesta de 0,55."""
    perfil = ProfileCandidate(
        opposition_code="tai-age-2025",
        opposition_name="Técnico Auxiliar de Informática",
        convocation_code="tai-age-2025",
        topics=(
            TopicCandidate(
                node_id="n1",
                path="bloque-4/tema-1",
                title="Protección de datos personales y seguridad",
                depth=1,
            ),
        ),
    )
    sujeto = _sujeto(text="Apuntes sobre protección de datos.", profiles=(perfil,))

    propuestas = _por_eje(sujeto)

    assert Axis.TOPIC in propuestas
    assert propuestas[Axis.TOPIC].confidence == 0.55


def test_la_oposicion_se_reconoce_por_su_codigo_o_por_su_nombre() -> None:
    perfil = ProfileCandidate(
        opposition_code="gc-cabos-guardias-2026",
        opposition_name="Guardia Civil",
        convocation_code="gc-cabos-guardias-2026",
        topics=(),
    )

    por_codigo = _por_eje(_sujeto(text="Temario de gc-cabos-guardias-2026.", profiles=(perfil,)))
    por_nombre = _por_eje(_sujeto(text="Apuntes de Guardia Civil.", profiles=(perfil,)))

    assert por_codigo[Axis.OPPOSITION].proposed_value == "gc-cabos-guardias-2026"
    assert por_nombre[Axis.OPPOSITION].proposed_value == "gc-cabos-guardias-2026"
    assert por_codigo[Axis.OPPOSITION].confidence > por_nombre[Axis.OPPOSITION].confidence


def test_el_extracto_se_acota_y_no_se_mira_mas_alla() -> None:
    """Una señal que solo aparece muy al final del texto no se ve: el extracto es una decisión."""
    sujeto = _sujeto(text=("relleno " * 4000) + "Boletín Oficial del Estado")

    assert Axis.AUTHORITY not in _por_eje(sujeto)


def test_una_baraja_de_anki_se_reconoce_por_su_extension() -> None:
    """La extensión es la señal, y el extractor comprueba además que dentro hay una colección."""
    propuestas = _por_eje(_sujeto(original_name="Tema 5 - plazos.apkg"))

    assert propuestas[Axis.DOCUMENT_TYPE].proposed_value == DocumentType.FLASHCARDS.value
    assert propuestas[Axis.DOCUMENT_TYPE].confidence >= 0.75, "puede aplicarse sola"
    assert "«.apkg»" in propuestas[Axis.DOCUMENT_TYPE].evidence


def test_las_senales_nuevas_dicen_lo_que_son_y_no_mas() -> None:
    """Una baraja y «preguntas tipo test» deciden solas; «cuestionario» y «anotaciones», no.

    Una palabra suelta puede estar en un documento que no es de ese tipo («el cuestionario constará
    de setenta preguntas» está en unas bases de convocatoria), así que se queda en la cola de
    revisión mientras «preguntas tipo test» no aparece por casualidad. «Supuesto práctico» es una
    señal fuerte (0,7) pero tampoco llega sola a la banda alta: la política de qué se aplica sin
    preguntar se decide en S12.4, no cue a cue.
    """
    tipo_test = _por_eje(_sujeto(text="Cuestionario de preguntas tipo test del tema 4."))
    assert tipo_test[Axis.DOCUMENT_TYPE].proposed_value == DocumentType.PRIVATE_QUESTION_BANK.value
    assert tipo_test[Axis.DOCUMENT_TYPE].confidence >= 0.7

    supuesto = _por_eje(_sujeto(text="Supuesto práctico sobre plazos administrativos."))
    assert supuesto[Axis.DOCUMENT_TYPE].proposed_value == DocumentType.PRACTICAL_CASE.value
    assert supuesto[Axis.DOCUMENT_TYPE].confidence >= 0.7

    solo_cuestionario = _por_eje(_sujeto(text="El cuestionario constará de setenta preguntas."))
    assert (
        solo_cuestionario[Axis.DOCUMENT_TYPE].proposed_value
        == DocumentType.PRIVATE_QUESTION_BANK.value
    )
    assert solo_cuestionario[Axis.DOCUMENT_TYPE].confidence < 0.7, "no se aplica sola"

    apuntes = _por_eje(_sujeto(text="Anotaciones de la clase del jueves."))
    assert apuntes[Axis.DOCUMENT_TYPE].proposed_value == DocumentType.PERSONAL_NOTES.value
    assert apuntes[Axis.DOCUMENT_TYPE].confidence < 0.7, "no se aplica sola"
