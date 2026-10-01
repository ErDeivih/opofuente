"""Alineación de una plantilla suelta por número (informe de claves de octubre de 2026)."""

from __future__ import annotations

from opofuente.domain.questions import KeyOutcome, ParsedKeyLine, key_alignment


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
