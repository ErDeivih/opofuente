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

from datetime import date
from fractions import Fraction

import pytest

from opofuente.config import project_root
from opofuente.domain.errors import InvariantViolationError, SessionStateError
from opofuente.domain.study import (
    BAREMO_NO_IMPORTADO,
    OFFICIAL_UNAVAILABLE_NOTE,
    AttemptOutcome,
    Baremo,
    BaremoInvalidError,
    BaremoProcedencia,
    Confidence,
    Feedback,
    FrozenQuestion,
    GradedAttempt,
    PartRule,
    ScoringKind,
    SessionConfiguration,
    SessionMode,
    SessionSource,
    SessionStatus,
    Substitution,
    aggregate,
    assign_positions,
    calificacion_oficial,
    cargar_baremo,
    decimal_text,
    effective_composition,
    exact_fraction,
    exact_score,
    grade_attempt,
    score_part,
    verdict_for,
)
from opofuente.infrastructure.fixture_loader import load_profiles

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
    from datetime import UTC, datetime

    from opofuente.domain.study import (
        SessionState,
        assert_can_answer,
        assert_can_finish,
    )

    ahora = datetime(2026, 9, 17, 12, 0, tzinfo=UTC)

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
    # Un estado que no admite la operación es un 409, no un invariante roto: la API lo explica.
    with pytest.raises(SessionStateError):
        assert_can_answer(borrador)
    with pytest.raises(SessionStateError):
        assert_can_finish(borrador)

    en_marcha = SessionState(
        session_id="s-1",
        mode=SessionMode.PRACTICE,
        status=SessionStatus.RUNNING,
        feedback=Feedback.IMMEDIATE,
        answer_key_version_id="k-1",
        total_questions=10,
        answered_questions=3,
        started_at=ahora,
        finished_at=None,
        time_limit_minutes=None,
    )
    assert_can_answer(en_marcha)
    assert_can_finish(en_marcha)

    terminada = SessionState(
        session_id="s-1",
        mode=SessionMode.PRACTICE,
        status=SessionStatus.FINISHED,
        feedback=Feedback.IMMEDIATE,
        answer_key_version_id="k-1",
        total_questions=10,
        answered_questions=10,
        started_at=ahora,
        finished_at=ahora,
        time_limit_minutes=None,
    )
    with pytest.raises(SessionStateError):
        assert_can_answer(terminada)
    assert_can_finish(terminada), "terminar lo ya terminado devuelve el resultado, no falla"


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
            "primera_parte": PartRule(
                code="primera_parte",
                name="Primera parte",
                ordinary_items=80,
                score_min=0.0,
                score_max=50.0,
                pass_score=25.0,
                penalty=penalty,
            )
        },
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


def test_el_total_es_la_suma_de_las_partes_aunque_penalicen_distinto() -> None:
    """Con dos penalizaciones distintas, recalcular el total con una sola daría otra cifra."""
    preguntas = [
        _pregunta("a1", part_code="primera_parte", position=1),
        _pregunta("a2", part_code="primera_parte", position=2),
        _pregunta("b1", part_code="segunda_parte", position=3),
        _pregunta("b2", part_code="segunda_parte", position=4),
    ]
    intentos = {
        "a1": GradedAttempt(AttemptOutcome.CORRECT, Fraction(1)),
        "a2": GradedAttempt(AttemptOutcome.WRONG, -TERCIO),
        "b1": GradedAttempt(AttemptOutcome.CORRECT, Fraction(1)),
        "b2": GradedAttempt(AttemptOutcome.WRONG, Fraction(-1, 4)),
    }
    efectivas, sustituciones = effective_composition(preguntas, intentos)

    resultado = aggregate(
        session_id="s-1",
        mode=SessionMode.PRACTICE,
        answer_key_version_id="k-1",
        items=efectivas,
        substitutions=sustituciones,
        part_rules={
            "primera_parte": PartRule(code="primera_parte", penalty=TERCIO),
            "segunda_parte": PartRule(code="segunda_parte", penalty=Fraction(1, 4)),
        },
    )

    assert [(parte.part_code, parte.score) for parte in resultado.parts] == [
        ("primera_parte", Fraction(2, 3)),
        ("segunda_parte", Fraction(3, 4)),
    ]
    assert resultado.total.score == Fraction(2, 3) + Fraction(3, 4)
    assert resultado.total.penalty is None, "no hay una sola penalización que describa la sesión"
    assert resultado.score_decimal == "1.4167"


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


# --- S08: corrección de Guardia Civil y partes de apto/no apto ------------------------------------


def _gc(codigo: str, **campos: object) -> PartRule:
    """Las partes de Guardia Civil, tal como las publica su convocatoria."""
    base: dict[str, object] = {
        "primera_parte": {
            "name": "Conocimientos generales",
            "ordinary_items": 100,
            "score_max": 100.0,
            "pass_score": 50.0,
            "options_per_question": 4,
            "kind": ScoringKind.SCALED,
            "format": "single_choice",
        },
        "lengua_inglesa": {
            "name": "Lengua inglesa",
            "ordinary_items": 20,
            "score_max": 20.0,
            "pass_score": 8.0,
            "options_per_question": 4,
            "kind": ScoringKind.SCALED,
            "format": "single_choice",
        },
        "aptitudes_intelectuales": {
            "name": "Aptitudes intelectuales",
            "ordinary_items": 80,
            "score_max": 30.0,
            "pass_score": 12.0,
            "options_per_question": 4,
            "kind": ScoringKind.SCALED,
            "format": "psychotechnical",
        },
        "ortografia": {
            "name": "Ortografía",
            "ordinary_items": 20,
            "fail_if_errors_gte": 6,
            "kind": ScoringKind.PASS_FAIL,
            "format": "multi_mark_error",
        },
    }[codigo]
    base.update(campos)
    return PartRule(code=codigo, **base)  # type: ignore[arg-type]


def test_la_formula_de_guardia_civil_se_calcula_exacta() -> None:
    """`Px = (Y/T)·(A - E/(N-1))`, con un caso a mano: 60 aciertos y 12 errores sobre 100."""
    regla = _gc("primera_parte")

    assert score_part(regla, correct=60, wrong=12) == Fraction(56)
    assert verdict_for(regla, Fraction(56), wrong=12).passed is True

    # Y con la lengua inglesa: (20/20)·(15 - 3/3) = 14, por encima del mínimo de 8.
    ingles = _gc("lengua_inglesa")
    assert score_part(ingles, correct=15, wrong=3) == Fraction(14)
    assert verdict_for(ingles, Fraction(14), wrong=3).passed is True

    # Por debajo del mínimo: (20/20)·(10 - 12/3) = 6 < 8.
    assert score_part(ingles, correct=10, wrong=12) == Fraction(6)
    assert verdict_for(ingles, Fraction(6), wrong=12).passed is False


def test_la_psicotecnica_se_escala_con_la_misma_formula() -> None:
    """(30/80)·(60 - 6/3) = 21,75 exacto, y su mínimo publicado es 12."""
    regla = _gc("aptitudes_intelectuales")

    puntuacion = score_part(regla, correct=60, wrong=6)

    assert puntuacion == Fraction(87, 4)
    assert decimal_text(puntuacion) == "21.7500"
    assert verdict_for(regla, puntuacion, wrong=6).passed is True


def test_la_regla_de_seis_errores_es_exacta() -> None:
    """Ortografía se evalúa como apto o no apto: con cinco errores se pasa y con seis, no."""
    regla = _gc("ortografia")

    assert score_part(regla, correct=18, wrong=5) == 0, "una parte de apto/no apto no da puntos"
    assert verdict_for(regla, Fraction(0), wrong=5).passed is True
    assert verdict_for(regla, Fraction(0), wrong=6).passed is False
    assert "apto o no apto" in (verdict_for(regla, Fraction(0), wrong=6).reason or "")


def test_una_parte_escalada_necesita_sus_datos_publicados() -> None:
    with pytest.raises(InvariantViolationError):
        PartRule(code="x", kind=ScoringKind.SCALED, ordinary_items=20, score_max=20.0)
    with pytest.raises(InvariantViolationError):
        PartRule(code="x", kind=ScoringKind.SCALED, ordinary_items=20, options_per_question=4)
    with pytest.raises(InvariantViolationError):
        PartRule(code="x", kind=ScoringKind.PASS_FAIL, ordinary_items=20)


def test_una_parte_de_tai_no_declara_superada() -> None:
    """Su umbral es de la calificación oficial: aplicarlo a la puntuación directa sería inventar."""
    regla = PartRule(code="primera_parte", name="Primera parte", pass_score=25.0, penalty=TERCIO)

    veredicto = verdict_for(regla, Fraction(30), wrong=2)

    assert veredicto.passed is None
    assert "baremos" in (veredicto.reason or "")


# --- la puntuación «estimada» (el caso del propietario: 28,125) -----------------------------------


def _parte_de_tai(codigo: str) -> PartRule:
    """La parte de TAI tal como la publica **su perfil**, leída del fixture y no de memoria.

    Es lo que hace verdad la decisión: el número de alternativas por pregunta
    (`options_per_question`) viene **nulo** del anexo V, y por eso la parte se puntúa con la
    estimación y no con la fórmula de Guardia Civil.
    """
    perfil = next(
        profile
        for profile in load_profiles(project_root() / "fixtures" / "profiles")
        if profile.convocation.code == "tai-age-2025"
    )
    parte = next(candidata for candidata in perfil.parts if candidata.code == codigo)
    assert parte.options_per_question is None, "el anexo V no publica las alternativas"
    assert parte.wrong_penalty_fraction is not None
    return PartRule(
        code=parte.code,
        name=parte.name,
        ordinary_items=parte.ordinary_items,
        score_min=parte.score_min,
        score_max=parte.score_max,
        pass_score=parte.pass_score,
        penalty=exact_fraction(parte.wrong_penalty_fraction),
        kind=ScoringKind.ESTIMATED,
    )


def test_la_puntuacion_estimada_de_tai_da_28_125_exacto() -> None:
    """El caso del propietario: 50 aciertos y 15 fallos en la primera parte → `225/8`.

    La directa ya existía y da 45 (`50 - 15/3`). Lo que faltaba es **escalarla a la banda de la
    parte**, que es lo que el propietario pidió: `50 · 45/80 = 225/8 = 28,125`, exacto con
    `Fraction` (nada de `float`).
    """
    regla = _parte_de_tai("primera_parte")

    directa = exact_score(50, 15, regla.penalty)
    estimada = score_part(regla, correct=50, wrong=15)

    assert directa == Fraction(45)
    assert estimada == Fraction(225, 8)
    assert estimada == Fraction("28.125")
    assert decimal_text(estimada) == "28.1250"
    assert estimada != directa, "escalar no es lo mismo que no escalar: son dos cifras distintas"


def test_la_estimacion_no_se_declara_aprobado_y_lo_dice() -> None:
    """Una estimación no es la calificación oficial: se dice si llega al mínimo y no se aprueba."""
    regla = _parte_de_tai("primera_parte")
    estimada = score_part(regla, correct=50, wrong=15)

    veredicto = verdict_for(regla, estimada, wrong=15)

    assert veredicto.passed is None, "la calificación oficial sale de los baremos, que no están"
    aviso = veredicto.reason or ""
    assert "estimación" in aviso
    # La cifra va **en español** (§2.2): la nota con coma y dos decimales, y el mínimo sin ceros de
    # más. Esta aserción esperaba `28.1250` —el decimal del contrato dentro de una frase—, que es el
    # punto del decimal que el propietario vio en su captura. `decimal_text` sigue dando `28.1250`
    # donde de verdad es un dato de máquina (arriba, línea 655): lo que cambia es la **prosa**.
    assert "es 28,13 sobre 50" in aviso
    assert "llega al mínimo publicado" in aviso, (
        "25 es alcanzable y se dice, sin declararlo aprobado"
    )
    assert "baremos" in aviso

    # Y por debajo del mínimo se dice igual, también sin declarar nada.
    baja = score_part(regla, correct=30, wrong=30)
    assert verdict_for(regla, baja, wrong=30).passed is None
    assert "no llega al mínimo publicado" in (verdict_for(regla, baja, wrong=30).reason or "")


def test_la_formula_de_guardia_civil_no_se_puede_usar_en_tai() -> None:
    """`E/(N-1)` necesita la `N`, y TAI no la publica: construir la parte escalada **falla**.

    Es la razón de que exista la estimación, y se comprueba con el perfil real: sin
    `options_per_question` no hay forma de descontar por alternativa, y un número inventado (4)
    corregiría con un dato que nadie ha publicado.
    """
    parte = _parte_de_tai("primera_parte")

    with pytest.raises(InvariantViolationError):
        PartRule(
            code=parte.code,
            ordinary_items=parte.ordinary_items,
            score_max=parte.score_max,
            pass_score=parte.pass_score,
            penalty=parte.penalty,
            kind=ScoringKind.SCALED,
        )

    # Y con las dos cifras publicadas, la estimación sí se puede construir y da el mismo número que
    # el propietario calculó a mano.
    assert score_part(parte, correct=50, wrong=15) == Fraction(225, 8)


def test_la_segunda_parte_de_tai_tambien_se_estima() -> None:
    """El supuesto práctico son 20 preguntas sobre 50: `50/20 · (A - E/3)`.

    Con 15 aciertos y 3 fallos: `2,5 · 14 = 35` sobre 50, que es la «nota por parte» de la segunda
    parte del simulacro.
    """
    regla = _parte_de_tai("segunda_parte")

    assert (regla.ordinary_items, regla.score_max) == (20, 50)
    assert score_part(regla, correct=15, wrong=3) == Fraction(35)
    assert verdict_for(regla, Fraction(35), wrong=3).passed is None


def test_los_veredictos_no_se_reparten_entre_partes_del_total() -> None:
    """El total no declara superado nada: el proceso depende del concurso y de las plazas."""
    resultado = _resultado(
        {"q1": GradedAttempt(AttemptOutcome.CORRECT, Fraction(1))},
    )

    assert resultado.total.passed is None
    assert resultado.total.kind is ScoringKind.DIRECT


def test_una_parte_de_apto_no_apto_queda_fuera_de_la_suma() -> None:
    preguntas = [
        _pregunta("q1", part_code="primera_parte", position=1),
        _pregunta("q2", part_code="primera_parte", position=2),
        _pregunta("q3", part_code="ortografia", position=3),
    ]
    intentos = {
        "q1": GradedAttempt(AttemptOutcome.CORRECT, Fraction(1)),
        "q2": GradedAttempt(AttemptOutcome.WRONG, -Fraction(1, 3)),
        "q3": GradedAttempt(AttemptOutcome.WRONG, Fraction(0)),
    }
    efectivas, sustituciones = effective_composition(preguntas, intentos)

    resultado = aggregate(
        session_id="s-1",
        mode=SessionMode.OFFICIAL_EXAM,
        answer_key_version_id="k-1",
        items=efectivas,
        substitutions=sustituciones,
        part_rules={"primera_parte": _gc("primera_parte"), "ortografia": _gc("ortografia")},
    )

    partes = {parte.part_code: parte for parte in resultado.parts}
    assert partes["primera_parte"].score == Fraction(100, 100) * (Fraction(1) - Fraction(1, 3)), (
        "un acierto menos un tercio, escalado a la puntuación máxima de la prueba"
    )
    assert partes["ortografia"].kind is ScoringKind.PASS_FAIL
    assert partes["ortografia"].penalty is None, "no hay penalización que enseñar en apto/no apto"
    assert partes["ortografia"].passed is True, "un solo error no llega a los seis"
    assert resultado.total.score == partes["primera_parte"].score, (
        "la parte de apto/no apto no suma puntos"
    )


# --- baremos oficiales: la procedencia es lo que se importa --------------------------------------


def _baremo_valido() -> dict[str, object]:
    """Un baremo *sintético* que cumple los cinco requisitos, para probar el cargador.

    La URL y el hash son inventados a propósito: esta prueba no afirma que exista ninguna tabla
    publicada, solo que el cargador acepta una procedencia completa. Los datos reales de TAI no
    están importados y no se inventan aquí.
    """
    return {
        "url_oficial": "https://sede.inap.gob.es/ejemplo.pdf",
        "fecha_consulta": "2026-10-30",
        "sha256": "a" * 64,
        "cita_literal": "Nota = (A - E/3) · 50/80",
        "formula_transformacion": "Nota = (A - E/3) · 50/80",
    }


def test_un_baremo_sin_cita_literal_no_se_importa() -> None:
    """Sin la cita no se sabe qué se importó: el cargador lo rechaza antes de tocar la base."""
    payload = _baremo_valido()
    del payload["cita_literal"]

    with pytest.raises(BaremoInvalidError) as fallo:
        cargar_baremo(payload)
    assert "cita_literal" in str(fallo.value)


def test_un_baremo_sin_hash_no_se_importa_y_dice_que_falta() -> None:
    """El hash es lo que permite cotejar la tabla con el documento: sin él no hay procedencia."""
    payload = _baremo_valido()
    payload["sha256"] = "   "

    with pytest.raises(BaremoInvalidError) as fallo:
        cargar_baremo(payload)
    assert "sha256" in str(fallo.value)


def test_un_hash_que_no_es_sha256_se_rechaza() -> None:
    """Un hash truncado o en otro formato parece procedencia y no lo es."""
    payload = _baremo_valido()
    payload["sha256"] = "a" * 63

    with pytest.raises(BaremoInvalidError):
        cargar_baremo(payload)


def test_una_url_que_no_es_http_se_rechaza() -> None:
    """«memoria local» o un fichero suelto no son una fuente oficial citable."""
    for url in ("file:///C:/baremo.pdf", "baremo.pdf", "https://"):
        payload = _baremo_valido()
        payload["url_oficial"] = url
        with pytest.raises(BaremoInvalidError):
            cargar_baremo(payload)


def test_una_fecha_que_no_es_iso_se_rechaza() -> None:
    """La fecha de consulta es un dato de procedencia: se compara entre filas, no se adivina."""
    payload = _baremo_valido()
    payload["fecha_consulta"] = "30/10/2026"

    with pytest.raises(BaremoInvalidError):
        cargar_baremo(payload)


def test_un_campo_de_mas_en_el_baremo_se_rechaza() -> None:
    """Un umbral que el cargador no entiende entraría sin validar: se rechaza la tabla entera."""
    payload = _baremo_valido()
    payload["nota_minima"] = 25

    with pytest.raises(BaremoInvalidError) as fallo:
        cargar_baremo(payload)
    assert "nota_minima" in str(fallo.value)


def test_un_baremo_bien_citado_se_carga_y_no_finge_calificar() -> None:
    """Con procedencia completa se puede enseñar de dónde saldría la nota, pero no hay nota.

    El cargador no trae la transformación ejecutable, así que la calificación oficial sigue sin
    estar disponible y se responde con su motivo —no con la puntuación directa disfrazada—.
    """
    baremo = cargar_baremo(_baremo_valido())

    assert isinstance(baremo, Baremo)
    assert baremo.transformacion is None
    assert baremo.procedencia.sha256 == "a" * 64
    assert baremo.procedencia.fecha_consulta.year == 2026

    calificacion = calificacion_oficial(Fraction(45))
    assert calificacion.available is False
    assert calificacion.reason == BAREMO_NO_IMPORTADO
    assert calificacion.score is None
    assert calificacion.note == OFFICIAL_UNAVAILABLE_NOTE

    # Y con el baremo cargado pero sin transformación, tampoco: la procedencia sola no es una nota.
    assert calificacion_oficial(Fraction(45), baremo=baremo).reason == BAREMO_NO_IMPORTADO


def test_una_transformacion_declarada_si_calcula_la_nota() -> None:
    """La costura existe y funciona: con una transformación declarada, la nota es la transformada.

    La función de la prueba es **sintética** (dobla la puntuación directa): demuestra el mecanismo,
    no afirma qué tabla publica ninguna convocatoria real.
    """
    procedencia = BaremoProcedencia(
        url_oficial="https://sede.inap.gob.es/ejemplo.pdf",
        fecha_consulta=date(2026, 10, 30),
        sha256="b" * 64,
        cita_literal="Nota = 2 · puntuación directa",
        formula_transformacion="Nota = 2 · puntuación directa",
    )
    baremo = Baremo(procedencia=procedencia, transformacion=lambda directa: directa * 2)

    calificacion = calificacion_oficial(Fraction(45), baremo=baremo)

    assert calificacion.available is True
    assert calificacion.reason is None
    assert calificacion.score == Fraction(90)
    assert calificacion.score_decimal == "90.0000"
