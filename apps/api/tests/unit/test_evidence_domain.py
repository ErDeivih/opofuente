"""Troceado del texto en evidencias citables (§4.1 del traspaso de octubre de 2026)."""

from __future__ import annotations

import hashlib

import pytest

from opofuente.domain.evidence import (
    MAX_EVIDENCE_CHARS,
    evidence_cuts,
    uncovered_ranges,
)


def _sin_blancos(texto: str) -> str:
    return "".join(texto.split())


def test_una_seccion_corta_es_una_sola_evidencia_sin_blancos_en_los_bordes() -> None:
    texto = "  \n Hola, mundo.  \n"
    assert evidence_cuts(texto, 0, len(texto)) == ((4, 16),)
    assert texto[4:16] == "Hola, mundo."


def test_una_seccion_larga_se_parte_y_no_se_pierde_nada() -> None:
    """Antes, 50.000 caracteres dejaban una evidencia de 1.200 y el resto se perdía."""
    texto = ("El plazo es de diez días hábiles. " * 1500).strip()
    cortes = evidence_cuts(texto, 0, len(texto))
    assert len(cortes) > 40
    assert all(fin - inicio <= MAX_EVIDENCE_CHARS for inicio, fin in cortes)
    assert _sin_blancos("".join(texto[a:b] for a, b in cortes)) == _sin_blancos(texto)


def test_los_cortes_prefieren_el_salto_de_parrafo() -> None:
    parrafo = "palabra " * 90  # ~720 caracteres
    texto = parrafo.strip() + "\n\n" + parrafo.strip() + "\n\n" + parrafo.strip()
    cortes = evidence_cuts(texto, 0, len(texto))
    assert [texto[a:b] for a, b in cortes] == [parrafo.strip()] * 3


def test_un_texto_sin_espacios_se_corta_a_pelo_en_el_tope() -> None:
    texto = "x" * 3000
    cortes = evidence_cuts(texto, 0, len(texto))
    assert [fin - inicio for inicio, fin in cortes] == [1200, 1200, 600]


def test_los_offsets_son_absolutos_y_respetan_los_limites_de_la_seccion() -> None:
    texto = "AAAA\n" + "b " * 2000 + "\nCCCC"
    inicio, fin = 5, 5 + 4000
    cortes = evidence_cuts(texto, inicio, fin)
    assert cortes[0][0] >= inicio
    assert cortes[-1][1] <= fin
    assert all("A" not in texto[a:b] and "C" not in texto[a:b] for a, b in cortes)


def test_solo_blancos_no_produce_evidencias() -> None:
    assert evidence_cuts("   \n\n  ", 0, 7) == ()
    assert evidence_cuts("abc", 2, 1) == ()


def _texto_pseudoaleatorio(semilla: int) -> str:
    """Texto determinista con letras, acentos, puntuación y saltos, de 0 a ~6.000 caracteres."""
    alfabeto = "abcdefghij ñáé.,;\n"
    bloques: list[str] = []
    contador = 0
    longitud = hashlib.sha256(f"longitud-{semilla}".encode()).digest()[0] * 24
    while sum(len(bloque) for bloque in bloques) < longitud:
        resumen = hashlib.sha256(f"{semilla}-{contador}".encode()).digest()
        bloques.append("".join(alfabeto[byte % len(alfabeto)] for byte in resumen))
        contador += 1
    return "".join(bloques)[:longitud]


def test_no_se_pierde_nada_con_texto_pseudoaleatorio() -> None:
    for semilla in range(50):
        texto = _texto_pseudoaleatorio(semilla)
        cortes = evidence_cuts(texto, 0, len(texto))
        assert all(0 < fin - inicio <= MAX_EVIDENCE_CHARS for inicio, fin in cortes)
        assert all(cortes[i][1] <= cortes[i + 1][0] for i in range(len(cortes) - 1))
        assert all(texto[a:b] == texto[a:b].strip() for a, b in cortes)
        assert _sin_blancos("".join(texto[a:b] for a, b in cortes)) == _sin_blancos(texto)


def test_parametros_imposibles_se_rechazan() -> None:
    with pytest.raises(ValueError):
        evidence_cuts("abc", 0, 3, max_chars=10, target_chars=20)


def test_huecos_entre_rangos_que_se_solapan() -> None:
    assert uncovered_ranges(100, [(10, 20), (15, 30), (50, 60)]) == ((0, 10), (30, 50), (60, 100))
    assert uncovered_ranges(10, []) == ((0, 10),)
    assert uncovered_ranges(10, [(0, 10)]) == ()
    assert uncovered_ranges(10, [(-5, 3), (8, 50)]) == ((3, 8),)
