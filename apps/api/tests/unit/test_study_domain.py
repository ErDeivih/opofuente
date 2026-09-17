"""Pruebas unitarias del dominio de estudio (S07): aritmética exacta, corrección y reservas.

Lo que se comprueba aquí son los criterios de aceptación del slice, sin base de datos ni API:

- **casos matemáticos de la puntuación directa TAI**, calculados a mano en la propia prueba;
- **la penalización de un tercio es exacta**: tres errores descuentan un punto justo, sin residuo
  binario (DEBT-006);
- **una pregunta que no se corrige no penaliza** y se informa con su motivo;
- **la reserva solo entra cuando se anula una ordinaria**, y se dice cuál sustituye a cuál;
- **la calificación oficial no se inventa**: sin baremo importado no hay 0-50 ni aprobado.
"""

from __future__ import annotations

from fractions import Fraction

import pytest

from opofuente.domain.errors import InvariantViolationError
from opofuente.domain.study import (
    OFFICIAL_UNAVAILABLE_NOTE,
    AttemptOutcome,
    Confidence,
    Feedback,
    FrozenQuestion,
    GradedAttempt,
    SessionConfiguration,
    SessionMode,
    SessionSource,
    Substitution,
    aggregate,
    assign_positions,
    decimal_text,
    effective_composition,
    exact_fraction,
    exact_score,
    grade_attempt,
)

TERCIO = Fraction(1, 3)


# --- aritmética exacta ---------------------------------------------------------------------------


def test_el_tercio_almacenado_es_una_fraccion_exacta() -> None:
    """El `0.3333333333` de la convocatoria es un tercio, y aquí se recupera como fracción."""
    assert exact_fraction(0.3333333333) == TERCIO
    assert exact_fraction(0.25) == Fraction(1, 4)
    assert exact_fraction(0) == Fraction(0)


def test_una_penalizacion_que_no_es_una_fraccion_sencilla_falla() -> None:
    """0,1234567891 no es media ni un tercio ni un cuarto: antes que aproximar, el cálculo para."""
    with pytest.raises(InvariantViolationError):
        exact_fraction(0.1234567891)
    # Y se aceptan las fracciones publicadas habituales, con sus decimales redondeados.
    assert exact_fraction(0.1666666667) == Fraction(1, 6)
    assert exact_fraction(0.5) == Fraction(1, 2)


def test_tres_errores_descuentan_exactamente_un_punto() -> None:
    """El caso que DEBT-006 pedía probar: sin residuo binario visible."""
    puntuacion = exact_score(0, 3, TERCIO)

    assert puntuacion == Fraction(-1)
    assert decimal_text(puntuacion) == "-1.0000"
    # Con `float`, 3 * 0.3333333333 deja 0.9999999999 y la resta se nota en el cuarto decimal.
    assert puntuacion + 1 == 0


def test_los_aciertos_menos_los_errores_dan_la_puntuacion_directa() -> None:
    """Caso TAI a mano: 68 aciertos, 10 errores y 2 en blanco sobre 80 preguntas."""
    aciertos, errores = 68, 10

    assert exact_score(aciertos, errores, TERCIO) == Fraction(68) - Fraction(10, 3)
    assert decimal_text(exact_score(aciertos, errores, TERCIO)) == "64.6667"


def test_una_penalizacion_negativa_no_se_acepta() -> None:
    with pytest.raises(InvariantViolationError):
        exact_fraction(-0.25)
    with pytest.raises(InvariantViolationError):
        exact_score(1, 1, Fraction(-1, 3))


def test_el_decimal_de_una_puntuacion_redondea_a_la_mitad_hacia_arriba() -> None:
    """Una nota se redondea al mostrarla, y el valor exacto sigue viajando aparte."""
    assert decimal_text(Fraction(2, 3)) == "0.6667"
    assert decimal_text(Fraction(1, 8)) == "0.1250"
    assert decimal_text(Fraction(20)) == "20.0000"


# --- corrección ----------------------------------------------------------------------------------


def _pregunta(
    identificador: str,
    *,
    part_code: str | None = "primera_parte",
    is_reserve: bool = False,
    reserve_order: int | None = None,
    position: int = 1,
    key_outcome: str | None = "keyed",
    correct: tuple[str, ...] = ("b",),
    stable_key: str | None = None,
) -> FrozenQuestion:
    return FrozenQuestion(
        question_version_id=identificador,
        stable_key=stable_key or f"q{position:03d}",
        position=position,
        part_code=part_code,
        is_reserve=is_reserve,
        reserve_order=reserve_order,
        key_outcome=key_outcome,
        correct_option_keys=correct,
    )


def test_acierto_error_y_blanco_se_distinguen_y_puntuan_distinto() -> None:
    acierto = grade_attempt(
        chosen_option_keys=["b"], frozen_outcome="keyed", frozen_correct_keys=["b"], penalty=TERCIO
    )
    error = grade_attempt(
        chosen_option_keys=["a"], frozen_outcome="keyed", frozen_correct_keys=["b"], penalty=TERCIO
    )
    blanco = grade_attempt(
        chosen_option_keys=[], frozen_outcome="keyed", frozen_correct_keys=["b"], penalty=TERCIO
    )

    assert (acierto.outcome, acierto.score) == (AttemptOutcome.CORRECT, Fraction(1))
    assert (error.outcome, error.score) == (AttemptOutcome.WRONG, Fraction(-1, 3))
    assert (blanco.outcome, blanco.score) == (AttemptOutcome.BLANK, Fraction(0))
    assert blanco.counts_in_score, "un blanco cuenta (vale cero), no se puede confundir con ausente"


def test_una_pregunta_anulada_no_penaliza_aunque_se_conteste_mal() -> None:
    anulada = grade_attempt(
        chosen_option_keys=["a"],
        frozen_outcome="annulled",
        frozen_correct_keys=[],
        penalty=TERCIO,
    )

    assert anulada.outcome is AttemptOutcome.ANNULLED
    assert anulada.score == 0
    assert not anulada.counts_in_score
    assert "anuló" in (anulada.reason or "")


def test_dos_claves_en_conflicto_no_se_corrige_solo() -> None:
    """La aplicación no elige entre dos claves que se contradicen: queda fuera con su motivo."""
    conflicto = grade_attempt(
        chosen_option_keys=["b"],
        frozen_outcome="conflicting",
        frozen_correct_keys=["a"],
        penalty=TERCIO,
    )

    assert conflicto.outcome is AttemptOutcome.CONFLICTING
    assert not conflicto.counts_in_score
    assert "contradicen" in (conflicto.reason or "")


def test_una_pregunta_sin_entrada_en_la_clave_queda_fuera_del_calculo() -> None:
    sin_clave = grade_attempt(
        chosen_option_keys=["b"], frozen_outcome=None, frozen_correct_keys=[], penalty=TERCIO
    )

    assert sin_clave.outcome is AttemptOutcome.EXCLUDED
    assert sin_clave.reason == "la clave no tiene entrada para esta pregunta"


def test_la_clave_dice_que_hay_respuesta_pero_no_cual_queda_fuera() -> None:
    """Un dato incoherente no se corrige inventando: se excluye y se explica."""
    raro = grade_attempt(
        chosen_option_keys=["b"], frozen_outcome="keyed", frozen_correct_keys=[], penalty=TERCIO
    )

    assert raro.outcome is AttemptOutcome.EXCLUDED
    assert "no cuál" in (raro.reason or "")


def test_marcar_varias_opciones_solo_acierta_si_son_exactamente_las_correctas() -> None:
    exacta = grade_attempt(
        chosen_option_keys=["b", "c"],
        frozen_outcome="keyed",
        frozen_correct_keys=["c", "b"],
        penalty=TERCIO,
    )
    de_mas = grade_attempt(
        chosen_option_keys=["b", "c"],
        frozen_outcome="keyed",
        frozen_correct_keys=["b"],
        penalty=TERCIO,
    )

    assert exacta.outcome is AttemptOutcome.CORRECT
    assert de_mas.outcome is AttemptOutcome.WRONG


def test_solo_se_corrige_en_una_sesion_en_marcha() -> None:
    from opofuente.domain.study import (
        SessionState,
        SessionStatus,
        assert_can_answer,
        assert_can_finish,
    )

    borrador = SessionState(
        session_id="s-1",
        mode=SessionMode.PRACTICE,
        status=SessionStatus.DRAFT,
        feedback=Feedback.IMMEDIATE,
        answer_key_version_id="k-1",
        total_questions=10,
        answered_questions=0,
        started_at=None,
        finished_at=None,
        time_limit_minutes=None,
    )
    with pytest.raises(InvariantViolationError):
        assert_can_answer(borrador)
    with pytest.raises(InvariantViolationError):
        assert_can_finish(borrador)


# --- composición efectiva y reservas -------------------------------------------------------------


def test_una_ordinaria_anulada_la_sustituye_la_primera_reserva() -> None:
    ordinarias = [_pregunta(f"q{i}", position=i) for i in range(1, 4)]
    reservas = [
        _pregunta("r1", is_reserve=True, reserve_order=1, position=4),
        _pregunta("r2", is_reserve=True, reserve_order=2, position=5),
    ]
    intentos = {
        "q1": GradedAttempt(AttemptOutcome.CORRECT, Fraction(1)),
        "q2": GradedAttempt(AttemptOutcome.ANNULLED, Fraction(0), "la clave anuló la pregunta"),
        "q3": GradedAttempt(AttemptOutcome.WRONG, -TERCIO),
        "r1": GradedAttempt(AttemptOutcome.CORRECT, Fraction(1)),
        "r2": GradedAttempt(AttemptOutcome.WRONG, -TERCIO),
    }

    efectivas, sustituciones = effective_composition([*ordinarias, *reservas], intentos)

    assert sustituciones == (Substitution("q2", "r1"),)
    # La anulada sale del cálculo y entra la primera reserva; la segunda no sustituye a nadie.
    calculadas = {item.question.question_version_id: item.attempt for item in efectivas}
    assert "q2" not in calculadas
    assert calculadas["r1"].outcome is AttemptOutcome.CORRECT  # type: ignore[union-attr]
    assert calculadas["r2"].outcome is AttemptOutcome.UNUSED_RESERVE  # type: ignore[union-attr]


def test_una_ordinaria_anulada_sin_reservas_queda_fuera_y_se_dice() -> None:
    efectivas, sustituciones = effective_composition(
        [_pregunta("q1")],
        {"q1": GradedAttempt(AttemptOutcome.ANNULLED, Fraction(0), "la clave anuló la pregunta")},
    )

    assert sustituciones == (Substitution("q1", None),)
    assert efectivas[0].question.question_version_id == "q1"
    assert "sin reserva disponible" in (efectivas[0].attempt.reason or "")  # type: ignore[union-attr]


def test_una_reserva_contestada_sin_anulacion_no_cuenta() -> None:
    """Contarla inflaría el resultado: la convocatoria la valora solo si se anula alguna."""
    efectivas, sustituciones = effective_composition(
        [
            _pregunta("q1"),
            _pregunta("r1", is_reserve=True, reserve_order=1, position=2),
        ],
        {
            "q1": GradedAttempt(AttemptOutcome.CORRECT, Fraction(1)),
            "r1": GradedAttempt(AttemptOutcome.CORRECT, Fraction(1)),
        },
    )

    assert sustituciones == ()
    reserva = next(item for item in efectivas if item.question.is_reserve)
    assert reserva.attempt.outcome is AttemptOutcome.UNUSED_RESERVE  # type: ignore[union-attr]


# --- resultado agregado --------------------------------------------------------------------------


def _resultado(
    intentos: dict[str, GradedAttempt | None],
    *,
    part_code: str | None = "primera_parte",
    reservas: int = 0,
    penalty: Fraction = TERCIO,
):
    preguntas = [_pregunta(f"q{i}", position=i, part_code=part_code) for i in range(1, 9)]
    preguntas += [
        _pregunta(f"r{i}", is_reserve=True, reserve_order=i, position=8 + i, part_code=part_code)
        for i in range(1, reservas + 1)
    ]
    efectivas, sustituciones = effective_composition(preguntas, intentos)
    return aggregate(
        session_id="s-1",
        mode=SessionMode.OFFICIAL_EXAM,
        answer_key_version_id="k-1",
        items=efectivas,
        substitutions=sustituciones,
        part_rules={
            "primera_parte": ("Primera parte", 80, 0.0, 50.0, 25.0),
        },
        penalty=penalty,
    )


def test_el_resultado_cuenta_aciertos_fallos_y_blancos_por_parte() -> None:
    intentos = {
        "q1": GradedAttempt(AttemptOutcome.CORRECT, Fraction(1)),
        "q2": GradedAttempt(AttemptOutcome.CORRECT, Fraction(1)),
        "q3": GradedAttempt(AttemptOutcome.WRONG, -TERCIO),
        "q4": GradedAttempt(AttemptOutcome.WRONG, -TERCIO),
        "q5": GradedAttempt(AttemptOutcome.WRONG, -TERCIO),
        "q6": GradedAttempt(AttemptOutcome.BLANK, Fraction(0)),
        "q7": GradedAttempt(AttemptOutcome.ANNULLED, Fraction(0), "anulada"),
        "q8": None,
    }

    resultado = _resultado(intentos)

    assert resultado.total.correct == 2
    assert resultado.total.wrong == 3
    assert resultado.total.blank == 1
    assert resultado.total.annulled == 1
    assert resultado.total.score == Fraction(1), "2 aciertos menos tres tercios: exactamente 1"
    assert resultado.score_decimal == "1.0000"
    assert resultado.unfinished == 1, "la pregunta sin responder se informa como pendiente"
    assert resultado.parts[0].part_code == "primera_parte"
    assert resultado.parts[0].part_name == "Primera parte"


def test_sin_baremo_importado_no_hay_calificacion_oficial_ni_aprobado() -> None:
    """Criterio de aceptación de S07: la puntuación directa es real; el 0-50, no disponible."""
    resultado = _resultado({"q1": GradedAttempt(AttemptOutcome.CORRECT, Fraction(1))})

    assert resultado.official_available is False
    assert resultado.official_note == OFFICIAL_UNAVAILABLE_NOTE
    assert "aprobado" in OFFICIAL_UNAVAILABLE_NOTE
    parte = resultado.parts[0]
    assert parte.pass_score == 25.0, "el umbral se enseña como dato de la convocatoria"
    assert parte.official_available is False, "pero no se aplica a una puntuación directa"


def test_una_sesion_sin_responder_tiene_puntuacion_cero_y_lo_dice() -> None:
    resultado = _resultado({f"q{i}": None for i in range(1, 9)})

    assert resultado.total.score == 0
    assert resultado.total.graded == 0
    assert resultado.unfinished == 8


# --- configuración -------------------------------------------------------------------------------


def test_un_examen_no_puede_dar_la_correccion_antes_de_terminar() -> None:
    """La regla que impide filtrar la solución, comprobada en el propio dominio."""
    with pytest.raises(InvariantViolationError):
        SessionConfiguration(
            mode=SessionMode.OFFICIAL_EXAM,
            feedback=Feedback.IMMEDIATE,
            sources=(SessionSource(question_set_id="set-1"),),
        )
    with pytest.raises(InvariantViolationError):
        SessionConfiguration(
            mode=SessionMode.OFFICIAL_EXAM,
            feedback=Feedback.AT_END,
            sources=(SessionSource(question_set_id="set-1"),),
            shuffle=True,
        )


def test_una_practica_puede_corregir_al_momento() -> None:
    configuracion = SessionConfiguration(
        mode=SessionMode.PRACTICE,
        feedback=Feedback.IMMEDIATE,
        sources=(SessionSource(question_set_id="set-1", count=20),),
    )

    assert configuracion.feedback is Feedback.IMMEDIATE
    assert configuracion.time_limit_minutes is None


def test_el_orden_de_presentacion_se_congela_al_numerar() -> None:
    preguntas = [
        _pregunta("q3", position=1),
        _pregunta("q1", position=2),
        _pregunta("q2", position=3),
    ]
    # Claves estables desordenadas a propósito: barajar reordena por clave estable, que es lo que
    # hace que el orden sea el mismo en cada lectura de la sesión ya creada.
    desordenadas = [
        _pregunta("q3", position=1, stable_key="q003"),
        _pregunta("q1", position=2, stable_key="q001"),
        _pregunta("q2", position=3, stable_key="q002"),
    ]

    ordenadas = assign_positions(preguntas, shuffle=False)
    barajadas = assign_positions(desordenadas, shuffle=True)

    assert [pregunta.question_version_id for pregunta in ordenadas] == ["q3", "q1", "q2"]
    assert [pregunta.position for pregunta in ordenadas] == [1, 2, 3]
    assert [pregunta.question_version_id for pregunta in barajadas] == ["q1", "q2", "q3"]
    assert assign_positions(desordenadas, shuffle=True) == barajadas, "barajar es determinista"


def test_confianza_y_secuencia_son_datos_del_intento() -> None:
    from opofuente.domain.study import Answer

    respuesta = Answer(chosen_option_keys=("b",), elapsed_ms=4321, confidence=Confidence.LOW)

    assert respuesta.confidence is Confidence.LOW
    assert respuesta.client_sequence is None
    assert respuesta.elapsed_ms == 4321
