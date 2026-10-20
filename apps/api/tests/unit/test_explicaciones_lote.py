"""El lote: qué entra, qué se queda fuera y con qué motivo (M1 de la fase 3)."""

from __future__ import annotations

from opofuente.application.explicaciones import (
    ExplicacionPropuesta,
    PreguntaAExplicar,
    validar_lote,
)
from opofuente_testing.explanation_proposer import FakeExplanationProposer

APARTADO = "El plazo de resolución es de tres meses. La Administración notifica la resolución."


def _pregunta(
    ident: str, *, apartado: str = APARTADO, clave: tuple[str, ...] = ("b",)
) -> PreguntaAExplicar:
    return PreguntaAExplicar(
        question_version_id=ident,
        enunciado="¿Cuál es el plazo?",
        opciones=(("a", "Seis meses"), ("b", "Tres meses")),
        clave=clave,
        apartado=apartado,
        note_anchor_id="ancla-" + ident,
    )


def _buena(ident: str) -> ExplicacionPropuesta:
    return ExplicacionPropuesta(
        question_version_id=ident,
        texto="La Administración tiene tres meses. Ese plazo es el que corrige la letra b.",
        cita="El plazo de resolución es de tres meses",
        letra="b",
    )


def test_lo_que_no_tiene_ancla_no_gasta_una_llamada() -> None:
    sin_apartado = _pregunta("q1", apartado="   ")
    sin_clave = _pregunta("q2", clave=())
    doble = FakeExplanationProposer()
    salida = validar_lote((sin_apartado, sin_clave), doble)
    assert salida.sin_material == ("q1", "q2")
    assert salida.aceptadas == ()
    assert doble.lotes == []  # no se ha llamado a nadie


def test_la_que_pasa_las_cuatro_entra() -> None:
    doble = FakeExplanationProposer(propuestas={"q1": _buena("q1")})
    salida = validar_lote((_pregunta("q1"),), doble)
    assert [p.question_version_id for p in salida.aceptadas] == ["q1"]
    assert salida.rechazadas == ()


def test_la_que_no_pasa_dice_por_que() -> None:
    mala = ExplicacionPropuesta(
        question_version_id="q1",
        texto="Una sola frase.",
        cita="esta cita no está en el apartado",
        letra="c",
    )
    doble = FakeExplanationProposer(propuestas={"q1": mala})
    salida = validar_lote((_pregunta("q1"),), doble)
    assert salida.aceptadas == ()
    ((ident, motivos),) = salida.rechazadas
    assert ident == "q1"
    assert len(motivos) == 3  # cita, letra y frases


def test_un_id_que_no_es_del_lote_se_ignora() -> None:
    doble = FakeExplanationProposer(propuestas={"inventado": _buena("inventado")})
    salida = validar_lote((_pregunta("q1"),), doble)
    assert salida.aceptadas == ()
    assert salida.rechazadas == ()


def test_se_pide_por_tandas_del_tamano_pedido() -> None:
    preguntas = tuple(_pregunta(f"q{i}") for i in range(5))
    doble = FakeExplanationProposer()
    validar_lote(preguntas, doble, tamano=2)
    assert [len(lote) for lote in doble.lotes] == [2, 2, 1]
