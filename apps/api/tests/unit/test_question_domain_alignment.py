"""Alineación de una plantilla suelta por número (informe de claves de octubre de 2026)."""

from __future__ import annotations

from opofuente.domain.questions import (
    KeyOutcome,
    ParsedKeyLine,
    key_alignment,
    ordered_key_mapping,
    parse_answer_key,
)


def _lineas(*posiciones: int) -> tuple[ParsedKeyLine, ...]:
    return tuple(
        ParsedKeyLine(position=p, outcome=KeyOutcome.KEYED, correct_option_keys=("a",))
        for p in posiciones
    )


def test_una_plantilla_completa_encaja_al_cien_por_cien() -> None:
    por_posicion = {n: (f"q{n}",) for n in range(1, 5)}
    alineacion = key_alignment(_lineas(1, 2, 3, 4), por_posicion)
    assert alineacion.score == 1.0


def test_cubrir_solo_parte_del_conjunto_no_es_encajar() -> None:
    """93 líneas sobre 135 preguntas daban «100 %»: ahora cuenta lo que queda sin respuesta."""
    por_posicion = {n: (f"q{n}",) for n in range(1, 136)}
    alineacion = key_alignment(_lineas(*range(1, 94)), por_posicion)
    assert alineacion.matched == 93
    assert alineacion.covered == 93
    assert round(alineacion.score, 2) == round(93 / 135, 2)


def test_una_numeracion_que_se_reinicia_es_ambigua() -> None:
    """Dos secciones que numeran desde 1: por número no se sabe a qué pregunta va cada línea."""
    por_posicion = {n: (f"a{n}", f"b{n}") if n <= 42 else (f"a{n}",) for n in range(1, 94)}
    alineacion = key_alignment(_lineas(*range(1, 94)), por_posicion)
    assert alineacion.ambiguous == 42
    assert alineacion.matched == 51
    assert alineacion.score < 0.95


def test_sin_lineas_o_sin_preguntas_no_encaja() -> None:
    assert key_alignment((), {1: ("q1",)}).score == 0.0
    assert key_alignment(_lineas(1), {}).score == 0.0


def _en_orden(*posiciones: int) -> tuple[tuple[str, int], ...]:
    return tuple((f"q{indice}", posicion) for indice, posicion in enumerate(posiciones))


def test_una_plantilla_de_un_examen_que_reinicia_la_numeracion_se_alinea_en_orden() -> None:
    """Dos partes que numeran desde 1 (TAI 2025): por número no se puede, en orden sí."""
    preguntas = _en_orden(1, 2, 3, 1, 2)
    assert ordered_key_mapping(_lineas(1, 2, 3, 1, 2), preguntas) == ("q0", "q1", "q2", "q3", "q4")


def test_en_orden_solo_si_encaja_uno_a_uno() -> None:
    preguntas = _en_orden(1, 2, 3, 1, 2)
    assert ordered_key_mapping(_lineas(1, 2, 3, 1), preguntas) is None, "una línea de menos"
    assert ordered_key_mapping(_lineas(1, 2, 3, 2, 1), preguntas) is None, "números cambiados"
    assert ordered_key_mapping((), preguntas) is None


def test_sin_numeros_repetidos_no_hace_falta_el_orden() -> None:
    assert ordered_key_mapping(_lineas(1, 2, 3), _en_orden(1, 2, 3)) is None


def test_la_plantilla_con_el_numero_y_la_letra_en_lineas_distintas_se_lee() -> None:
    """Las plantillas oficiales del INAP (TAI 2025) salen del PDF así para las preguntas 1 a 9,
    y la de Guardia Civil 2026 así entera: antes no se leía ninguna de esas líneas."""
    texto = (
        "Primera parte \n1. \nc \n2. \nb, d \n10. d \nPreguntas de reserva \n1 \nA \n11 \nanulada\n"
    )
    lineas, incidencias = parse_answer_key(texto)
    assert [(linea.position, linea.correct_option_keys) for linea in lineas] == [
        (1, ("c",)),
        (2, ("b", "d")),
        (10, ("d",)),
        (1, ("a",)),
        (11, ()),
    ]
    assert lineas[-1].outcome is KeyOutcome.ANNULLED
    assert [aviso.line for aviso in incidencias] == [1, 7], "los rótulos se informan, no se pegan"


def test_un_numero_suelto_no_se_pega_a_un_rotulo_ni_a_un_enunciado() -> None:
    lineas, _ = parse_answer_key("1.\nSupuesto I\n2.\nEl plazo es de diez días\n")
    assert lineas == ()


def test_una_respuesta_modificada_se_lee_y_conserva_la_marca() -> None:
    """La plantilla definitiva de promoción interna (TAI 2025) escribe la 7 como «d MODIFICADA»,
    debajo de su número: antes se perdía. La marca se conserva como nota de la respuesta."""
    lineas, incidencias = parse_answer_key("7.\nd MODIFICADA\n8. b (rectificada)\n9.\nModificada\n")
    assert [(linea.position, linea.correct_option_keys, linea.note) for linea in lineas] == [
        (7, ("d",), "respuesta modificada"),
        (8, ("b",), "respuesta rectificada"),
    ]
    assert len(incidencias) == 2, "«Modificada» sin letra no es una respuesta: se informa"
