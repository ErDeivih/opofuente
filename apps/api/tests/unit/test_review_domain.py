"""Pruebas unitarias de errores, repaso y dominio estimado (S10).

Lo que se comprueba aquí es lo que la especificación fija con números: la escalera de intervalos de
`06_QUESTIONS` §8, la traducción de desenlaces, la agrupación de conceptos y la honestidad de la
estimación de dominio de §9 (con pocos datos, «evidencia insuficiente»).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from opofuente.domain.review import (
    DIAS_RECIENTES,
    INTERVALO_BAJA_CONFIANZA,
    INTERVALO_MAXIMO,
    INTERVALO_TRAS_FALLO,
    INTERVALO_TRAS_FALLO_SUPERADO,
    MIN_INTENTOS_DOMINIO,
    AttemptStat,
    ErrorCause,
    ErrorStatus,
    MasteryLevel,
    ReviewOutcome,
    ReviewStatus,
    concept_key,
    mastery_from,
    next_due_at,
    review_outcome_for,
    schedule,
)
from opofuente.domain.study import AttemptOutcome, Confidence

AHORA = datetime(2026, 9, 18, 12, 0, tzinfo=UTC)


def _stat(*, correct: bool, dias: int = 0, horas: int = 0) -> AttemptStat:
    return AttemptStat(correct=correct, answered_at=AHORA - timedelta(days=dias, hours=horas))


# --- vocabulario y desenlaces -------------------------------------------------------------------


def test_las_causas_son_las_del_modelo_de_datos() -> None:
    assert [causa.value for causa in ErrorCause] == [
        "knowledge",
        "confusion",
        "reading",
        "time",
        "calculation",
        "ambiguous",
        "other",
    ]
    assert [estado.value for estado in ErrorStatus] == ["open", "resolved"]
    assert [estado.value for estado in ReviewStatus] == ["active", "suspended"]


@pytest.mark.parametrize(
    ("outcome", "esperado"),
    [
        (AttemptOutcome.CORRECT, ReviewOutcome.CORRECT),
        (AttemptOutcome.WRONG, ReviewOutcome.WRONG),
        # Un blanco no demuestra que se sepa: cuenta como fallo del repaso.
        (AttemptOutcome.BLANK, ReviewOutcome.WRONG),
        # Lo que la clave anuló (o no se pudo corregir) no dice nada de nadie.
        (AttemptOutcome.ANNULLED, None),
        (AttemptOutcome.EXCLUDED, None),
        (AttemptOutcome.CONFLICTING, None),
        (AttemptOutcome.UNUSED_RESERVE, None),
    ],
)
def test_el_desenlace_del_intento_se_traduce_al_del_repaso(
    outcome: AttemptOutcome, esperado: ReviewOutcome | None
) -> None:
    assert review_outcome_for(outcome) is esperado


# --- la escalera de intervalos (§8) -------------------------------------------------------------


def test_un_fallo_repasa_manana_y_vuelve_a_empezar() -> None:
    plan = schedule(outcome=ReviewOutcome.WRONG, previous_interval_days=0, repetitions=0)
    assert plan.interval_days == INTERVALO_TRAS_FALLO
    assert plan.repetitions == 0
    assert "mañana" in plan.reason


def test_un_fallo_reduce_el_intervalo_y_lo_dice() -> None:
    plan = schedule(outcome=ReviewOutcome.WRONG, previous_interval_days=30, repetitions=6)
    assert plan.interval_days == INTERVALO_TRAS_FALLO
    assert plan.repetitions == 0
    assert "de 30 días a 1" in plan.reason, "el motivo dice de dónde a dónde, no solo el resultado"


def test_un_acierto_con_baja_confianza_repasa_en_dos_dias() -> None:
    plan = schedule(
        outcome=ReviewOutcome.CORRECT,
        previous_interval_days=16,
        repetitions=3,
        confidence=Confidence.LOW,
    )
    assert plan.interval_days == INTERVALO_BAJA_CONFIANZA
    assert "baja confianza" in plan.reason


def test_no_declarar_confianza_no_es_dudar() -> None:
    sin_declarar = schedule(outcome=ReviewOutcome.CORRECT, previous_interval_days=4, repetitions=1)
    con_confianza = schedule(
        outcome=ReviewOutcome.CORRECT,
        previous_interval_days=4,
        repetitions=1,
        confidence=Confidence.MEDIUM,
    )
    assert sin_declarar == con_confianza


def test_un_acierto_tras_un_fallo_repasa_en_cuatro_dias() -> None:
    plan = schedule(
        outcome=ReviewOutcome.CORRECT, previous_interval_days=INTERVALO_TRAS_FALLO, repetitions=0
    )
    assert plan.interval_days == INTERVALO_TRAS_FALLO_SUPERADO
    assert plan.repetitions == 1
    assert "después de un fallo" in plan.reason


def test_los_aciertos_seguidos_recorren_la_escalera_y_se_quedan_en_el_maximo() -> None:
    anterior = INTERVALO_TRAS_FALLO
    recorrido: list[int] = []
    for repeticion in range(6):
        plan = schedule(
            outcome=ReviewOutcome.CORRECT,
            previous_interval_days=anterior,
            repetitions=repeticion,
        )
        recorrido.append(plan.interval_days)
        anterior = plan.interval_days
    assert recorrido == [4, 8, 16, 30, 30, 30]
    assert recorrido[-1] == INTERVALO_MAXIMO


def test_la_fecha_de_repaso_son_dias_enteros_desde_ahora() -> None:
    assert next_due_at(AHORA, 1) == datetime(2026, 9, 19, 12, 0, tzinfo=UTC)
    assert next_due_at(AHORA, 30) == datetime(2026, 10, 18, 12, 0, tzinfo=UTC)
    # Un intervalo negativo no puede programar el pasado: se queda en «ahora».
    assert next_due_at(AHORA, -5) == AHORA


# --- conceptos ----------------------------------------------------------------------------------


def test_los_fallos_se_agrupan_por_nodo_o_por_etiqueta_normalizada() -> None:
    assert concept_key("Plazos", curriculum_node_id=None) == "label:plazos"
    assert concept_key("  PLÁZOS  ", curriculum_node_id=None) == "label:plazos"
    assert concept_key("Plazos, del procedimiento", curriculum_node_id=None) == (
        "label:plazos del procedimiento"
    )
    # El nodo del programa manda: es el dato, no la etiqueta libre.
    assert concept_key("lo que sea", curriculum_node_id="nodo-1") == "node:nodo-1"
    assert concept_key(None, curriculum_node_id=None) == "sin-concepto"
    assert concept_key("   ", curriculum_node_id=None) == "sin-concepto"


# --- dominio estimado (§9) ----------------------------------------------------------------------


def test_sin_intentos_no_hay_nada_que_estimar() -> None:
    dominio = mastery_from([], now=AHORA)
    assert dominio.level is MasteryLevel.NO_DATA
    assert dominio.attempts == 0
    assert dominio.accuracy is None
    assert not dominio.has_estimate


def test_con_pocos_intentos_se_dice_evidencia_insuficiente_y_no_un_porcentaje() -> None:
    dominio = mastery_from(
        [_stat(correct=True) for _ in range(MIN_INTENTOS_DOMINIO - 1)], now=AHORA
    )
    assert dominio.level is MasteryLevel.INSUFFICIENT
    assert dominio.accuracy is None, "no se enseña un porcentaje que parezca una medición"
    assert f"hacen falta {MIN_INTENTOS_DOMINIO}" in dominio.explanation
    assert f"{MIN_INTENTOS_DOMINIO - 1} intento(s)" in dominio.explanation


def test_los_intentos_viejos_no_sostienen_una_estimacion_de_hoy() -> None:
    viejos = [_stat(correct=True, dias=DIAS_RECIENTES + 1, horas=1) for _ in range(20)]
    dominio = mastery_from(viejos, now=AHORA)
    assert dominio.level is MasteryLevel.INSUFFICIENT
    assert dominio.attempts == 20, "se dice cuántos hay en total, aunque no cuenten para estimar"
    assert dominio.recent_attempts == 0


@pytest.mark.parametrize(
    ("aciertos", "esperado"),
    [
        (1, MasteryLevel.LOW),
        (3, MasteryLevel.MEDIUM),
        (5, MasteryLevel.HIGH),
    ],
)
def test_el_nivel_sale_del_acierto_reciente_con_su_recuento(
    aciertos: int, esperado: MasteryLevel
) -> None:
    intentos = [_stat(correct=indice < aciertos) for indice in range(5)]
    dominio = mastery_from(intentos, now=AHORA)
    assert dominio.level is esperado
    assert dominio.recent_attempts == 5
    assert dominio.correct == aciertos
    assert dominio.accuracy == pytest.approx(aciertos / 5)
    # La explicación declara los umbrales y lo que **no** entra en la estimación.
    assert "umbrales provisionales" in dominio.explanation
    assert "dificultad observada no entra" in dominio.explanation
