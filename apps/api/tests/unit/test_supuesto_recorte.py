"""El recorte de preguntas de un supuesto (fase 3, §2.4).

**Lo que se comprueba y por que importa**: **pedir veinticinco preguntas y descartar el supuesto
entero porque vinieron veintiseis es tirar un supuesto bueno por un error de contar.** El documento
manda quitar las sobrantes, y que las de menos sigan siendo un descarte —**no se inventa ninguna**—.
"""

from __future__ import annotations

from opofuente.domain.practical_case import (
    PREGUNTAS_DEL_SUPUESTO,
    PreguntaPropuesta,
    SupuestoPropuesto,
    recortar_al_numero,
    validar_forma,
)


def _pregunta(numero: int) -> PreguntaPropuesta:
    return PreguntaPropuesta(
        enunciado=f"pregunta {numero}",
        opciones=(("a", "uno"), ("b", "dos"), ("c", "tres"), ("d", "cuatro")),
        clave="a",
        cita="una cita del apartado",
    )


def _supuesto(cuantas: int) -> SupuestoPropuesto:
    return SupuestoPropuesto(
        block="III",
        statement="Un enunciado de caso practico.",
        preguntas=tuple(_pregunta(n) for n in range(1, cuantas + 1)),
    )


def test_veintiseis_preguntas_se_quedan_en_veinticinco() -> None:
    recortado = recortar_al_numero(_supuesto(26))

    assert len(recortado.preguntas) == PREGUNTAS_DEL_SUPUESTO
    assert validar_forma(recortado).aceptado is True


def test_se_quitan_las_ultimas_y_el_orden_se_respeta() -> None:
    recortado = recortar_al_numero(_supuesto(28))

    assert [p.enunciado for p in recortado.preguntas][0] == "pregunta 1"
    assert [p.enunciado for p in recortado.preguntas][-1] == f"pregunta {PREGUNTAS_DEL_SUPUESTO}"


def test_veinticinco_se_quedan_igual() -> None:
    original = _supuesto(PREGUNTAS_DEL_SUPUESTO)

    assert recortar_al_numero(original) is original


def test_veinticuatro_no_se_completan_con_nada() -> None:
    """**Las de menos no se inventan**: el supuesto sigue siendo un descarte, y se dice."""
    recortado = recortar_al_numero(_supuesto(24))

    assert len(recortado.preguntas) == 24
    veredicto = validar_forma(recortado)
    assert veredicto.aceptado is False
    assert any("24" in problema for problema in veredicto.problemas)
