"""Las cuatro comprobaciones de una explicación: lo que entra y lo que no (M1 de la fase 3)."""

from __future__ import annotations

import pytest

from opofuente.domain.explicaciones import cita_literal, frases, habla_del_examen, problemas

APARTADO = """El plazo de resolución es de tres meses. La Administración debe notificar la
resolución expresa dentro de ese plazo."""


def test_una_explicacion_buena_no_tiene_ningun_problema() -> None:
    texto = (
        "La Administración tiene tres meses para resolver. "
        "Ese plazo es el que fija el apartado y el que corrige la letra b."
    )
    assert problemas(
        texto,
        cita="El plazo de resolución es de tres meses",
        apartado=APARTADO,
        letra="b",
        clave=("b",),
    ) == ()


def test_la_cita_que_no_esta_para_la_explicacion() -> None:
    fallos = problemas(
        "Una frase. Otra frase.",
        cita="el plazo es de seis meses",
        apartado=APARTADO,
        letra="b",
        clave=("b",),
    )
    assert any("no está literalmente" in fallo for fallo in fallos)


def test_la_letra_que_justifica_tiene_que_ser_la_que_corrige() -> None:
    fallos = problemas(
        "Una frase. Otra frase.",
        cita="El plazo de resolución es de tres meses",
        apartado=APARTADO,
        letra="c",
        clave=("b",),
    )
    assert any("no es la que corrige" in fallo for fallo in fallos)


@pytest.mark.parametrize(
    "texto",
    [
        "Esto suele caer en el examen. Y se repite.",
        "Es muy frecuente que aparezca. Y se repite.",
    ],
)
def test_prometer_sobre_el_examen_no_entra(texto: str) -> None:
    assert habla_del_examen(texto) != ()


def test_de_dos_a_cinco_frases() -> None:
    assert len(frases("Una. Dos.")) == 2
    assert len(frases("Una. Dos. Tres. Cuatro. Cinco. Seis.")) == 6
    assert any(
        "frases" in fallo
        for fallo in problemas(
            "Una sola frase.",
            cita="El plazo de resolución es de tres meses",
            apartado=APARTADO,
            letra="b",
            clave=("b",),
        )
    )


def test_la_cita_se_compara_sin_que_estorbe_el_formato() -> None:
    assert cita_literal("El plazo   de resolución\nes de tres meses", APARTADO)