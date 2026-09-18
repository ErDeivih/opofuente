"""Pruebas unitarias del dominio de búsqueda y RAG (S09).

Lo que se comprueba aquí son los criterios de aceptación del slice, sin base de datos ni API:

- **la búsqueda funciona sin vectores ni modelo**: la expresión léxica se construye sola y la
  respuesta se compone por extracción, sin proveedor;
- **una pregunta fuera del corpus es `insufficient`** y no lleva afirmaciones inventadas;
- **una pregunta a la que le falta un término es `partial`** y dice cuál falta;
- **las afirmaciones solo citan fragmentos entregados**: `assert_grounded` lo impide, no lo
  aconseja;
- **el corpus elegible excluye lo no publicado** y dice por qué;
- **la fusión es por posiciones** (RRF), así que dos búsquedas con escalas distintas no se mezclan
  mal, y la diversificación no deja sin evidencia.
"""

from __future__ import annotations

from datetime import date

import pytest

from opofuente.domain.errors import InvariantViolationError
from opofuente.domain.rag import (
    AnswerStatus,
    CandidateSpan,
    Claim,
    ClaimSupport,
    CorpusDecision,
    RagDraft,
    SearchStrategy,
    VersionMode,
    assert_grounded,
    compose_extractive_answer,
    corpus_eligible,
    diversify,
    fuse_candidates,
    match_expression,
    normalise,
    reciprocal_rank_fusion,
    significant_terms,
)


def _span(
    identificador: str,
    texto: str,
    *,
    documento: str = "doc-1",
    titulo: str = "Temario",
    cita: str = "Tema 1, pág. 3",
    seccion: str | None = "Tema 1",
    score: float = 1.0,
    strategy: SearchStrategy = SearchStrategy.LEXICAL,
) -> CandidateSpan:
    return CandidateSpan(
        span_id=identificador,
        document_version_id="ver-1",
        document_id=documento,
        document_title=titulo,
        document_type="curriculum",
        authority_tier="A",
        version_status="accepted",
        citation_label=cita,
        page=3,
        section_id=seccion,
        section_title=seccion,
        text=texto,
        score=score,
        strategy=strategy,
    )


# --- normalización y consulta -------------------------------------------------------------------


def test_la_normalizacion_quita_acentos_y_signos() -> None:
    assert normalise("El plazo es de DIEZ días, ¿verdad?") == "el plazo es de diez dias verdad"


def test_los_terminos_significativos_dejan_fuera_las_palabras_vacias() -> None:
    terminos = significant_terms("¿Cuál es el plazo del artículo 5?")

    assert "plazo" in terminos
    assert "articulo" in terminos
    assert "5" in terminos
    assert "cual" not in terminos and "es" not in terminos and "del" not in terminos
    assert terminos == tuple(dict.fromkeys(terminos)), "sin repetidos"


def test_la_expresion_fts5_entrecomilla_cada_termino() -> None:
    expresion = match_expression("plazo de alegaciones")

    assert expresion == '"plazo"* OR "alegaciones"*', (
        "los términos van entre comillas y con prefijo"
    )


def test_una_busqueda_vacia_no_se_acepta() -> None:
    with pytest.raises(InvariantViolationError):
        match_expression("   ")


# --- corpus elegible ----------------------------------------------------------------------------


def test_una_version_no_publicada_no_se_recupera_y_se_dice_por_que() -> None:
    decision = corpus_eligible(
        version_status="candidate",
        representation_quality="good",
        valid_from=None,
        valid_to=None,
        reference_date=None,
    )

    assert decision.eligible is False
    assert decision.reason is not None and "candidate" in decision.reason


def test_una_representacion_pobre_no_sostiene_una_cita() -> None:
    decision = corpus_eligible(
        version_status="accepted",
        representation_quality="poor",
        valid_from=None,
        valid_to=None,
        reference_date=None,
    )

    assert decision.eligible is False
    assert "no sostiene una cita" in (decision.reason or "")


def test_la_vigencia_se_comprueba_con_la_fecha_de_la_consulta() -> None:
    antes = corpus_eligible(
        version_status="accepted",
        representation_quality="good",
        valid_from=date(2026, 1, 1),
        valid_to=None,
        reference_date=date(2025, 12, 31),
    )
    despues = corpus_eligible(
        version_status="accepted",
        representation_quality="good",
        valid_from=date(2020, 1, 1),
        valid_to=date(2024, 12, 31),
        reference_date=date(2026, 9, 17),
    )

    assert antes.eligible is False and "no estaba vigente" in (antes.reason or "")
    assert despues.eligible is False and "ya no estaba vigente" in (despues.reason or "")


def test_pedir_el_historico_permite_una_version_sustituida() -> None:
    actual = corpus_eligible(
        version_status="superseded",
        representation_quality="good",
        valid_from=None,
        valid_to=None,
        reference_date=None,
    )
    historico = corpus_eligible(
        version_status="superseded",
        representation_quality="good",
        valid_from=None,
        valid_to=None,
        reference_date=None,
        version_mode=VersionMode.EXPLICIT_HISTORICAL,
    )

    assert actual.eligible is False
    assert historico.eligible is True, (
        "mirar el histórico es una decisión explícita, no un descuido"
    )


# --- respuesta con citas ------------------------------------------------------------------------


def test_una_pregunta_fuera_del_corpus_es_insuficiente_y_no_inventa_nada() -> None:
    """Criterio de aceptación: la pregunta negativa devuelve «insuficiente», sin afirmaciones."""
    borrador = compose_extractive_answer("¿Cuánto cuesta el alquiler de un dron?", [])

    assert borrador.status is AnswerStatus.INSUFFICIENT
    assert borrador.claims == ()
    assert "No hay evidencia" in borrador.short_answer
    assert borrador.missing_terms, "se dice qué no se ha encontrado"


def test_una_respuesta_respaldada_cita_los_fragmentos_entregados() -> None:
    entregados = [
        _span("s1", "El plazo de alegaciones es de diez días hábiles."),
        _span("s2", "El plazo se cuenta desde la notificación."),
    ]

    borrador = compose_extractive_answer("¿Cuál es el plazo de alegaciones?", entregados)

    assert borrador.status is AnswerStatus.SUPPORTED
    assert borrador.claims, "una respuesta respaldada lleva afirmaciones"
    assert set(borrador.evidence_ids) <= {span.span_id for span in entregados}
    assert borrador.claims[0].text in entregados[0].text
    assert "extraída" in borrador.explanation, (
        "se dice que es texto de las evidencias, no redacción"
    )


def test_si_falta_un_termino_la_respuesta_es_parcial_y_lo_dice() -> None:
    entregados = [_span("s1", "El plazo de alegaciones es de diez días hábiles.")]

    borrador = compose_extractive_answer("¿Cuál es el plazo de subsanación?", entregados)

    assert borrador.status is AnswerStatus.PARTIAL
    assert "subsanacion" in borrador.missing_terms
    assert any("subsanacion" in texto for texto in borrador.uncertainties)
    assert borrador.claims, "lo que sí está respaldado se muestra citado"


def test_una_afirmacion_sin_evidencia_no_se_publica() -> None:
    with pytest.raises(InvariantViolationError):
        assert_grounded(
            RagDraft(
                status=AnswerStatus.PARTIAL,
                short_answer="algo",
                explanation="algo",
                claims=(Claim(text="una afirmación suelta", evidence_ids=()),),
            ),
            ["s1"],
        )


def test_una_afirmacion_que_cita_lo_que_no_se_entrego_no_se_publica() -> None:
    """La regla del contrato §6: si fallan las citas, la respuesta no se muestra como respaldada."""
    with pytest.raises(InvariantViolationError) as error:
        assert_grounded(
            RagDraft(
                status=AnswerStatus.PARTIAL,
                short_answer="algo",
                explanation="algo",
                claims=(Claim(text="cita inventada", evidence_ids=("s-que-no-existe",)),),
            ),
            ["s1"],
        )

    assert "no se entregó" in str(error.value)


def test_una_respuesta_respaldada_sin_afirmaciones_tampoco_se_publica() -> None:
    with pytest.raises(InvariantViolationError):
        assert_grounded(
            RagDraft(status=AnswerStatus.SUPPORTED, short_answer="sí", explanation="porque sí"),
            ["s1"],
        )


def test_una_respuesta_bien_formada_pasa_la_comprobacion() -> None:
    entregados = [_span("s1", "El plazo es de diez días hábiles.")]
    borrador = compose_extractive_answer("¿Cuál es el plazo?", entregados)

    assert_grounded(borrador, [span.span_id for span in entregados])


# --- fusión y diversificación -------------------------------------------------------------------


def test_la_fusion_usa_posiciones_y_no_puntuaciones() -> None:
    """RRF: un fragmento segundo en las dos listas sube por delante del primero de una sola."""
    fusion = reciprocal_rank_fusion([["a", "b"], ["c", "b"]])

    assert fusion[0][0] == "b"
    assert dict(fusion)["b"] > dict(fusion)["a"]


def test_sin_vectores_la_busqueda_es_lexical_y_lo_dice() -> None:
    lexical = [_span("s1", "uno"), _span("s2", "dos")]

    paquete = fuse_candidates(lexical, [], limit=5)

    assert [span.span_id for span in paquete.hits] == ["s1", "s2"]
    assert paquete.strategies == (SearchStrategy.LEXICAL,)
    assert any("solo léxica" in aviso for aviso in paquete.degradations)


def test_con_vectores_se_fusionan_las_dos_estrategias() -> None:
    lexical = [_span("s1", "uno"), _span("s2", "dos")]
    vector = [_span("s3", "tres", strategy=SearchStrategy.HYBRID), _span("s1", "uno")]

    paquete = fuse_candidates(lexical, vector, limit=5)

    assert SearchStrategy.HYBRID in paquete.strategies
    assert {span.span_id for span in paquete.hits} == {"s1", "s2", "s3"}
    assert paquete.degradations == (), "con las dos estrategias no hay nada que declarar"


def test_la_diversificacion_limita_por_documento_pero_no_deja_sin_evidencia() -> None:
    spans = [_span(f"s{i}", f"texto {i}", documento="doc-1") for i in range(1, 6)]

    elegidos = diversify(spans, limit=4, max_por_documento=2)

    assert len(elegidos) == 4, "si solo hay un documento, se repite antes que quedarse corto"


def test_la_diversificacion_reparte_entre_documentos_cuando_los_hay() -> None:
    spans = [
        _span("a1", "uno", documento="doc-1"),
        _span("a2", "dos", documento="doc-1"),
        _span("a3", "tres", documento="doc-1"),
        _span("b1", "cuatro", documento="doc-2"),
    ]

    elegidos = diversify(spans, limit=3, max_por_documento=2)

    assert [span.span_id for span in elegidos] == ["a1", "a2", "b1"]


def test_un_fragmento_sin_titulo_de_seccion_no_sugiere_busquedas() -> None:
    entregados = [_span("s1", "El plazo es de diez días hábiles.", seccion=None)]

    borrador = compose_extractive_answer("¿plazo?", entregados)

    assert borrador.suggested_followups == ()


def test_el_soporte_de_una_afirmacion_por_defecto_es_directo() -> None:
    claim = Claim(text="algo citado", evidence_ids=("s1",))

    assert claim.support is ClaimSupport.DIRECT


def test_la_decision_de_corpus_se_puede_leer_como_booleano() -> None:
    assert CorpusDecision(True).eligible is True
    assert CorpusDecision(True).reason is None
