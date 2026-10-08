"""La decisión del clasificador y la lectura de lo que contesta el modelo (F4).

Todo lo que se prueba aquí es **puro**: no hay red, ni base de datos, ni modelo. Es lo que se puede
comprobar sin gastar un céntimo, y es donde viven las dos cosas que el propietario revisa antes de
lanzar la corrida: los umbrales (qué entra solo y qué va a la cola) y la lectura de la respuesta
(qué se sostiene y qué se descarta).
"""

from __future__ import annotations

import json

import pytest

from opofuente.domain.errors import ConfigurationError, ExternalServiceError
from opofuente.domain.topic_classification import (
    UMBRAL_ALTA,
    ClassifiableQuestion,
    OutOfSyllabus,
    ProposalOutcome,
    Syllabus,
    SyllabusEpigraph,
    SyllabusTopic,
    TopicProposal,
    build_system_prompt,
    build_user_prompt,
    decide,
)
from opofuente.infrastructure.topic_classification_client import (
    DeepSeekTopicProposer,
    read_response,
)


def _temario() -> Syllabus:
    """Un temario de juguete con la forma del real: un tema con dos epígrafes y otro sin ninguno."""
    return Syllabus(
        opposition_code="tai-age",
        topics=(
            SyllabusTopic(
                code="I.1",
                title="La Constitución Española de 1978",
                node_id="nodo-i-1",
                block_code="I",
                epigraphs=(
                    SyllabusEpigraph(
                        code="I.1.1",
                        title="La Constitución Española de 1978.",
                        node_id="nodo-i-1-1",
                        topic_code="I.1",
                    ),
                    SyllabusEpigraph(
                        code="I.1.2",
                        title="Derechos y deberes fundamentales.",
                        node_id="nodo-i-1-2",
                        topic_code="I.1",
                    ),
                ),
            ),
            SyllabusTopic(
                code="IV.1",
                title="Sin epígrafes",
                node_id="nodo-iv-1",
                block_code="IV",
                epigraphs=(),
            ),
        ),
    )


def _propuesta(**cambios: object) -> TopicProposal:
    base: dict[str, object] = {
        "question_version_id": "pregunta-1",
        "topic_code": "I.1",
        "epigraph_code": None,
        "confidence": 0.9,
        "out_of_syllabus": None,
        "note": None,
    }
    base.update(cambios)
    return TopicProposal(**base)  # type: ignore[arg-type]


# --- umbrales -----------------------------------------------------------------------------------


def test_una_confianza_alta_asigna_el_tema() -> None:
    decision = decide(_propuesta(), syllabus=_temario())

    assert decision.outcome is ProposalOutcome.ASSIGN
    assert decision.topic is not None and decision.topic.node_id == "nodo-i-1"
    assert decision.writes is True


def test_justo_en_el_umbral_alto_sigue_entrando_solo() -> None:
    """El umbral es «a partir de», no «por encima de»: el número que se documenta es el que vale."""
    decision = decide(_propuesta(confidence=UMBRAL_ALTA), syllabus=_temario())

    assert decision.outcome is ProposalOutcome.ASSIGN


def test_una_confianza_media_va_a_la_cola_de_revision() -> None:
    """Ni se da por buena ni se tira: se guarda como propuesta y la revisa una persona."""
    decision = decide(_propuesta(confidence=0.6), syllabus=_temario())

    assert decision.outcome is ProposalOutcome.REVIEW
    assert decision.topic is not None
    assert decision.writes is True


def test_una_confianza_baja_no_escribe_nada() -> None:
    decision = decide(_propuesta(confidence=0.2), syllabus=_temario())

    assert decision.outcome is ProposalOutcome.NOTHING
    assert decision.writes is False


def test_un_modelo_que_no_lo_tiene_claro_deja_la_pregunta_sin_clasificar() -> None:
    """Inventarle un tema para no dejar el hueco es justo lo que no se puede hacer."""
    decision = decide(_propuesta(topic_code=None, confidence=0.9), syllabus=_temario())

    assert decision.outcome is ProposalOutcome.NOTHING
    assert decision.topic is None


def test_un_codigo_que_no_esta_en_el_temario_es_un_error_de_la_propuesta() -> None:
    """Asignar «lo más parecido» sería inventar la clasificación con el nombre del modelo."""
    decision = decide(_propuesta(topic_code="XX.99"), syllabus=_temario())

    assert decision.outcome is ProposalOutcome.ERROR
    assert decision.writes is False
    assert decision.note is not None and "XX.99" in decision.note


# --- fuera de temario ---------------------------------------------------------------------------


def test_fuera_de_temario_se_declara_con_su_motivo() -> None:
    decision = decide(
        _propuesta(
            topic_code=None,
            out_of_syllabus=OutOfSyllabus.OTRA_ADMINISTRACION,
            confidence=0.8,
            note="ley autonómica de Aragón",
        ),
        syllabus=_temario(),
    )

    assert decision.outcome is ProposalOutcome.OUT_OF_SYLLABUS
    assert decision.out_of_syllabus is OutOfSyllabus.OTRA_ADMINISTRACION
    assert decision.topic is None, "fuera de temario no se asigna a ningún tema, aunque diga uno"


def test_fuera_de_temario_manda_sobre_el_tema_propuesto() -> None:
    """Decir «no es de este programa» y además asignarle un tema es contradecirse."""
    decision = decide(
        _propuesta(out_of_syllabus=OutOfSyllabus.ENUNCIADO_ROTO, confidence=0.9),
        syllabus=_temario(),
    )

    assert decision.outcome is ProposalOutcome.OUT_OF_SYLLABUS
    assert decision.topic is None


def test_fuera_de_temario_con_confianza_baja_no_se_escribe() -> None:
    """Excluir una pregunta con una corazonada es peor que dejarla sin clasificar."""
    decision = decide(
        _propuesta(out_of_syllabus=OutOfSyllabus.OTRA_ADMINISTRACION, confidence=0.3),
        syllabus=_temario(),
    )

    assert decision.outcome is ProposalOutcome.NOTHING


# --- epígrafes ----------------------------------------------------------------------------------


def test_un_epigrafe_sin_tema_deduce_el_tema_del_arbol_oficial() -> None:
    decision = decide(_propuesta(topic_code=None, epigraph_code="I.1.2"), syllabus=_temario())

    assert decision.outcome is ProposalOutcome.ASSIGN
    assert decision.topic is not None and decision.topic.code == "I.1"
    assert decision.epigraph is not None and decision.epigraph.node_id == "nodo-i-1-2"


def test_un_epigrafe_que_no_existe_se_descarta_y_el_tema_se_queda() -> None:
    """Un epígrafe mal puesto es peor que ninguno, pero no invalida el tema, que sí se resolvió."""
    decision = decide(_propuesta(epigraph_code="I.1.99"), syllabus=_temario())

    assert decision.outcome is ProposalOutcome.ASSIGN
    assert decision.epigraph is None
    assert decision.note is not None and "I.1.99" in decision.note


def test_si_el_epigrafe_es_de_otro_tema_manda_el_epigrafe() -> None:
    """El epígrafe viene del árbol oficial: su tema es el suyo, aunque el modelo diga otro."""
    decision = decide(_propuesta(topic_code="IV.1", epigraph_code="I.1.1"), syllabus=_temario())

    assert decision.topic is not None and decision.topic.code == "I.1"
    assert decision.epigraph is not None and decision.epigraph.code == "I.1.1"
    assert decision.note is not None and "IV.1" in decision.note


# --- el prompt ----------------------------------------------------------------------------------


def test_el_prompt_lleva_el_temario_con_sus_codigos() -> None:
    """El modelo tiene que poder contestar con un código: el temario va delante de cada línea."""
    sistema = build_system_prompt(_temario())

    assert "I.1 — La Constitución Española de 1978" in sistema
    assert "    I.1.1 — La Constitución Española de 1978." in sistema
    assert "IV.1 — Sin epígrafes" in sistema
    assert "otra_administracion" in sistema, "el motivo de fuera de temario se explica"


def test_el_prompt_del_lote_lleva_el_identificador_y_las_opciones() -> None:
    usuario = build_user_prompt(
        (
            ClassifiableQuestion(
                question_version_id="pregunta-7",
                stem="¿Qué artículo reconoce el derecho de petición?",
                options=(("a", "El 23"), ("b", "El 29")),
            ),
        )
    )

    assert "id: pregunta-7" in usuario
    assert "enunciado: ¿Qué artículo reconoce el derecho de petición?" in usuario
    assert "  b) El 29" in usuario


# --- lectura de la respuesta del modelo ---------------------------------------------------------


def _sobre(asignaciones: list[dict[str, object]], *, uso: dict[str, int] | None = None) -> str:
    """Una respuesta con la forma de la API: el JSON de verdad dentro de `content`."""
    return json.dumps(
        {
            "choices": [
                {"message": {"content": json.dumps({"asignaciones": asignaciones})}},
            ],
            "usage": uso or {"prompt_tokens": 1200, "completion_tokens": 80},
        }
    )


def test_la_lectura_trae_las_propuestas_y_lo_que_costo() -> None:
    lote = read_response(
        _sobre(
            [
                {
                    "id": "pregunta-1",
                    "tema": "I.1",
                    "epigrafe": None,
                    "fuera_de_temario": None,
                    "confianza": 0.9,
                    "motivo": "es la Constitución",
                }
            ]
        ),
        requested=["pregunta-1"],
    )

    assert [propuesta.question_version_id for propuesta in lote.proposals] == ["pregunta-1"]
    assert lote.proposals[0].topic_code == "I.1"
    assert lote.input_tokens == 1200
    assert lote.output_tokens == 80


def test_la_lectura_descarta_lo_que_apunta_a_una_pregunta_que_no_se_pregunto() -> None:
    """Clasificar una pregunta que no está en el lote no se puede: se descarta, no se inventa."""
    lote = read_response(
        _sobre([{"id": "otra", "tema": "I.1", "confianza": 0.9}]),
        requested=["pregunta-1"],
    )

    assert lote.proposals == ()


def test_la_lectura_lee_los_motivos_de_fuera_de_temario() -> None:
    lote = read_response(
        _sobre(
            [
                {
                    "id": "pregunta-1",
                    "tema": None,
                    "fuera_de_temario": "enunciado_roto",
                    "confianza": 0.85,
                    "motivo": "es un trozo de norma",
                }
            ]
        ),
        requested=["pregunta-1"],
    )

    assert lote.proposals[0].out_of_syllabus is OutOfSyllabus.ENUNCIADO_ROTO
    assert lote.proposals[0].note == "es un trozo de norma"


def test_una_confianza_que_no_es_un_numero_se_lee_como_cero() -> None:
    """Una respuesta que no se puede interpretar no se escribe: no se adivina la confianza."""
    lote = read_response(
        _sobre([{"id": "pregunta-1", "tema": "I.1", "confianza": "mucha"}]),
        requested=["pregunta-1"],
    )

    assert lote.proposals[0].confidence == 0.0
    assert decide(lote.proposals[0], syllabus=_temario()).outcome is ProposalOutcome.NOTHING


@pytest.mark.parametrize(
    "respuesta",
    [
        "esto no es json",
        json.dumps({"choices": []}),
        json.dumps({"choices": [{"message": {"content": "tampoco es json"}}]}),
        json.dumps({"choices": [{"message": {"content": json.dumps({"otra": []})}}]}),
    ],
)
def test_una_respuesta_ilegible_se_dice_en_vez_de_traducirse(respuesta: str) -> None:
    with pytest.raises(ExternalServiceError):
        read_response(respuesta, requested=["pregunta-1"])


# --- el cliente ----------------------------------------------------------------------------------


def test_el_cliente_no_arranca_sin_clave() -> None:
    """La clave se lee del entorno: un cliente sin clave no se construye, no se inventa."""
    with pytest.raises(ConfigurationError):
        DeepSeekTopicProposer(api_key="   ")


def test_el_cliente_no_arranca_con_una_direccion_que_no_es_http() -> None:
    with pytest.raises(ConfigurationError):
        DeepSeekTopicProposer(api_key="clave", base_url="ftp://sitio")
