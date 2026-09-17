"""Migración 0016: sesiones de estudio, composición congelada, intentos y evaluaciones (S07).

Lo que se prueba no es que las tablas existan, sino **lo que la base impide**, que es lo
que sostiene los criterios de aceptación del slice:

1. una sesión no se puede quedar «en marcha» sin reloj de inicio ni «terminada» sin su final;
2. el vocabulario de modos, estados, corrección, confianza y desenlaces es cerrado: un valor
   inventado se rechaza, y un desenlace que no cuenta en la puntuación tampoco entra por la
   puerta de atrás;
3. **una pregunta no se repite en la misma sesión** y no comparte posición con otra: la
   composición congelada es un dato, no una lista que se pueda desordenar;
4. una reserva sin orden de reserva no entra: si no se sabe cuál es la primera, no hay
   sustitución;
5. **un intento por pregunta**: el intento se congela, así que reenviar la misma respuesta no
   puede crear un segundo;
6. **la evaluación guarda la puntuación exacta** (numerador y denominador, con denominador
   positivo) y no se puede duplicar para la misma clave; recalcular con otra clave añade una
   fila que sustituye a la anterior (invariante 7);
7. borrar la sesión se lleva sus preguntas e intentos, pero **no puede borrar una pregunta ni
   una clave** (`ON DELETE RESTRICT`): lo que se presentó no desaparece por debajo.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from opofuente.config import Settings
from opofuente.infrastructure.db import build_engine
from opofuente.infrastructure.migrations import run_migrations

AHORA = datetime(2026, 9, 17, 12, 0, tzinfo=UTC)


def _settings(tmp_path: Path) -> Settings:
    return Settings(data_dir=tmp_path / "datos", _env_file=None)


def _ejecutar(
    settings: Settings, sentencia: str, parametros: dict[str, object] | None = None
) -> None:
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.begin() as conexion:
            conexion.execute(text(sentencia), parametros or {})
    finally:
        engine.dispose()


def _sembrar(settings: Settings) -> None:
    """Oposición, conjunto, clave activa y una pregunta: lo mínimo para colgar una sesión."""
    _ejecutar(
        settings,
        "INSERT INTO oppositions (id, code, name, active, created_at, updated_at) "
        "VALUES ('op-1', 'tai-age', 'TAI', 1, :ahora, :ahora)",
        {"ahora": AHORA},
    )
    _ejecutar(
        settings,
        "INSERT INTO question_sets (id, title, opposition_id, set_type, status, created_at, "
        "updated_at) VALUES ('set-1', 'Examen de prueba', 'op-1', 'official_exam', 'confirmed', "
        ":ahora, :ahora)",
        {"ahora": AHORA},
    )
    _ejecutar(
        settings,
        "INSERT INTO question_versions (id, question_set_id, stable_key, version_no, stem, "
        "question_type, position, origin_type, created_at) VALUES ('q-1', 'set-1', 'q001', 1, "
        "'Enunciado de prueba', 'single_choice', 1, 'official', :ahora)",
        {"ahora": AHORA},
    )
    _ejecutar(
        settings,
        "INSERT INTO answer_key_versions (id, question_set_id, version_no, status, approved_at, "
        "created_at) VALUES ('key-1', 'set-1', 1, 'active', :ahora, :ahora)",
        {"ahora": AHORA},
    )


def _sesion(settings: Settings, **campos: object) -> None:
    valores: dict[str, object] = {
        "id": "ses-1",
        "modo": "practice",
        "estado": "draft",
        "feedback": "immediate",
        "inicio": None,
        "final": None,
    }
    valores.update(campos)
    _ejecutar(
        settings,
        "INSERT INTO study_sessions (id, opposition_id, question_set_id, answer_key_version_id, "
        "mode, status, feedback, configuration_json, time_limit_minutes, total_questions, "
        "started_at, finished_at, created_at) VALUES (:id, 'op-1', 'set-1', 'key-1', :modo, "
        ":estado, :feedback, '{}', NULL, 0, :inicio, :final, :ahora)",
        {**valores, "ahora": AHORA},
    )


def _pregunta_de_sesion(
    settings: Settings,
    *,
    identificador: str = "sq-1",
    posicion: int = 1,
    reserva: int | None = None,
) -> None:
    _ejecutar(
        settings,
        "INSERT INTO session_questions (id, session_id, question_version_id, stable_key, position, "
        "part_code, is_reserve, reserve_order, key_outcome, correct_option_keys_json) VALUES "
        "(:id, 'ses-1', 'q-1', 'q001', :posicion, 'primera_parte', :reserva_bool, :reserva, "
        "'keyed', '[\"b\"]')",
        {
            "id": identificador,
            "posicion": posicion,
            "reserva": reserva,
            "reserva_bool": 1 if reserva is not None else 0,
        },
    )


def _intento(settings: Settings, *, identificador: str = "att-1") -> None:
    _ejecutar(
        settings,
        "INSERT INTO attempts (id, session_question_id, chosen_option_keys_json, elapsed_ms, "
        "confidence, client_sequence, answered_at) VALUES (:id, 'sq-1', '[\"b\"]', 4200, 'low', 1, "
        ":ahora)",
        {"id": identificador, "ahora": AHORA},
    )


# --- estados y vocabularios ---------------------------------------------------------------------


def test_una_sesion_en_marcha_necesita_su_reloj_y_una_terminada_su_final(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    run_migrations(settings, revision="head")
    _sembrar(settings)

    with pytest.raises(IntegrityError):
        _sesion(settings, estado="running")
    with pytest.raises(IntegrityError):
        _sesion(settings, estado="finished", inicio=AHORA)

    _sesion(settings, estado="running", inicio=AHORA)
    _sesion(settings, id="ses-2", estado="finished", inicio=AHORA, final=AHORA)


def test_los_vocabularios_de_la_sesion_son_cerrados(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    run_migrations(settings, revision="head")
    _sembrar(settings)

    with pytest.raises(IntegrityError):
        _sesion(settings, modo="inventado")
    with pytest.raises(IntegrityError):
        _sesion(settings, feedback="cuando-quiera")
    with pytest.raises(IntegrityError):
        _sesion(settings, estado="a-medias")


def test_una_pregunta_no_se_repite_ni_comparte_posicion(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    run_migrations(settings, revision="head")
    _sembrar(settings)
    _sesion(settings, estado="running", inicio=AHORA)
    _pregunta_de_sesion(settings)

    with pytest.raises(IntegrityError):
        _pregunta_de_sesion(settings, identificador="sq-2", posicion=1)
    with pytest.raises(IntegrityError):
        _pregunta_de_sesion(settings, identificador="sq-3", posicion=2)


def test_una_reserva_necesita_su_orden_y_el_desenlace_es_un_vocabulario(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    run_migrations(settings, revision="head")
    _sembrar(settings)
    _sesion(settings, estado="running", inicio=AHORA)

    with pytest.raises(IntegrityError):
        _ejecutar(
            settings,
            "INSERT INTO session_questions (id, session_id, question_version_id, stable_key, "
            "position, is_reserve, key_outcome) VALUES ('sq-mal', 'ses-1', 'q-1', 'q001', 1, 1, "
            "'keyed')",
        )
    with pytest.raises(IntegrityError):
        _ejecutar(
            settings,
            "INSERT INTO session_questions (id, session_id, question_version_id, stable_key, "
            "position, is_reserve, key_outcome) VALUES ('sq-mal', 'ses-1', 'q-1', 'q001', 1, 0, "
            "'inventado')",
        )
    _pregunta_de_sesion(settings, reserva=1)


# --- intentos y evaluaciones --------------------------------------------------------------------


def test_un_intento_por_pregunta_y_su_desenlace_cerrado(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    run_migrations(settings, revision="head")
    _sembrar(settings)
    _sesion(settings, estado="running", inicio=AHORA)
    _pregunta_de_sesion(settings)
    _intento(settings)

    with pytest.raises(IntegrityError):
        _intento(settings, identificador="att-2")

    with pytest.raises(IntegrityError):
        _ejecutar(
            settings,
            "INSERT INTO attempts (id, session_question_id, chosen_option_keys_json, elapsed_ms, "
            "confidence, answered_at) VALUES ('att-3', 'sq-1', '[]', 10, 'altísima', :ahora)",
            {"ahora": AHORA},
        )
    with pytest.raises(IntegrityError):
        _ejecutar(
            settings,
            "INSERT INTO attempts (id, session_question_id, chosen_option_keys_json, elapsed_ms, "
            "answered_at) VALUES ('att-4', 'sq-1', '[]', -1, :ahora)",
            {"ahora": AHORA},
        )


def test_la_evaluacion_guarda_la_puntuacion_exacta_y_no_se_duplica_por_clave(
    tmp_path: Path,
) -> None:
    settings = _settings(tmp_path)
    run_migrations(settings, revision="head")
    _sembrar(settings)
    _sesion(settings, estado="running", inicio=AHORA)
    _pregunta_de_sesion(settings)
    _intento(settings)

    # Un tercio se guarda como 1/3, no como 0,3333333333.
    _ejecutar(
        settings,
        "INSERT INTO attempt_evaluations (id, attempt_id, answer_key_version_id, outcome, "
        "score_numerator, score_denominator, evaluated_at) VALUES ('ev-1', 'att-1', 'key-1', "
        "'wrong', -1, 3, :ahora)",
        {"ahora": AHORA},
    )

    with pytest.raises(IntegrityError):
        _ejecutar(
            settings,
            "INSERT INTO attempt_evaluations (id, attempt_id, answer_key_version_id, outcome, "
            "score_numerator, score_denominator, evaluated_at) VALUES ('ev-2', 'att-1', 'key-1', "
            "'correct', 1, 1, :ahora)",
            {"ahora": AHORA},
        )
    with pytest.raises(IntegrityError):
        _ejecutar(
            settings,
            "INSERT INTO attempt_evaluations (id, attempt_id, answer_key_version_id, outcome, "
            "score_numerator, score_denominator, evaluated_at) VALUES ('ev-3', 'att-1', 'key-1', "
            "'inventado', 0, 1, :ahora)",
            {"ahora": AHORA},
        )
    with pytest.raises(IntegrityError):
        _ejecutar(
            settings,
            "INSERT INTO attempt_evaluations (id, attempt_id, answer_key_version_id, outcome, "
            "score_numerator, score_denominator, evaluated_at) VALUES ('ev-4', 'att-1', 'key-1', "
            "'wrong', -1, 0, :ahora)",
            {"ahora": AHORA},
        )

    # Con una clave nueva entra una evaluación **nueva** que sustituye a la anterior (invariante 7).
    _ejecutar(
        settings,
        "INSERT INTO answer_key_versions (id, question_set_id, version_no, status, created_at) "
        "VALUES ('key-2', 'set-1', 2, 'draft', :ahora)",
        {"ahora": AHORA},
    )
    _ejecutar(
        settings,
        "INSERT INTO attempt_evaluations (id, attempt_id, answer_key_version_id, outcome, "
        "score_numerator, score_denominator, supersedes_id, evaluated_at) VALUES ('ev-5', 'att-1', "
        "'key-2', 'correct', 1, 1, 'ev-1', :ahora)",
        {"ahora": AHORA},
    )


def test_borrar_la_sesion_no_borra_la_pregunta_ni_la_clave(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    run_migrations(settings, revision="head")
    _sembrar(settings)
    _sesion(settings, estado="running", inicio=AHORA)
    _pregunta_de_sesion(settings)
    _intento(settings)
    _ejecutar(
        settings,
        "INSERT INTO attempt_evaluations (id, attempt_id, answer_key_version_id, outcome, "
        "score_numerator, score_denominator, evaluated_at) VALUES ('ev-1', 'att-1', 'key-1', "
        "'correct', 1, 1, :ahora)",
        {"ahora": AHORA},
    )

    # La pregunta y la clave están protegidas: la sesión no se las lleva por delante.
    with pytest.raises(IntegrityError):
        _ejecutar(settings, "DELETE FROM question_versions WHERE id = 'q-1'")
    with pytest.raises(IntegrityError):
        _ejecutar(settings, "DELETE FROM answer_key_versions WHERE id = 'key-1'")

    # Borrar la sesión se lleva su composición, sus intentos y sus evaluaciones.
    _ejecutar(settings, "DELETE FROM study_sessions WHERE id = 'ses-1'")
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.connect() as conexion:
            # Una consulta por tabla, sin interpolar nombres: el recuento es explícito.
            restos = {
                "session_questions": conexion.execute(
                    text("SELECT count(*) FROM session_questions")
                ).scalar_one(),
                "attempts": conexion.execute(text("SELECT count(*) FROM attempts")).scalar_one(),
                "attempt_evaluations": conexion.execute(
                    text("SELECT count(*) FROM attempt_evaluations")
                ).scalar_one(),
            }
    finally:
        engine.dispose()
    assert restos == {"session_questions": 0, "attempts": 0, "attempt_evaluations": 0}
    # Y la pregunta sigue donde estaba.
    _ejecutar(settings, "SELECT 1 FROM question_versions WHERE id = 'q-1'")
