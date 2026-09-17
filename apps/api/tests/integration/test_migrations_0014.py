"""Migración 0014: preguntas, opciones, claves, evidencias y explicaciones (S06).

Aquí no se prueba que las tablas existan (eso lo dice la migración), sino **lo que la base impide**,
que es lo que sostiene los criterios de aceptación del slice:

1. una pregunta no puede repetir su identidad (`conjunto`, `clave estable`, `versión`), y dos
   opciones de la misma versión no comparten ni clave ni sitio: el reordenado de los modelos A/B es
   un dato, no una casualidad;
2. una pregunta que no es reserva no puede llevar orden de reserva, y ninguna pregunta se sustituye
   a sí misma;
3. **una clave activa necesita aprobación**, y **solo puede haber una activa por conjunto**
   (invariante 5): la anterior permanece, con su estado;
4. un desenlace «con clave» sin clave no entra: eso es un hueco, y el hueco se llama `unanswered`;
5. **una evidencia citada por una pregunta no se puede borrar** (`ON DELETE RESTRICT`): la cita no
   se pierde por debajo;
6. una explicación **generada** sin decir con qué modelo no entra: sin eso no es trazable;
7. y los vocabularios son cerrados: un tipo, un estado o un rol inventados se rechazan.
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
SHA_A = "a" * 64


def _settings(tmp_path: Path) -> Settings:
    return Settings(data_dir=tmp_path / "datos", _env_file=None)


def _sembrar(settings: Settings, *, conjunto: str = "set-1", preguntas: int = 1) -> None:
    """Crea lo mínimo para poder hablar de preguntas: oposición, conjunto, preguntas y opciones."""
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.begin() as conexion:
            conexion.execute(
                text(
                    "INSERT INTO oppositions (id, code, name, active, created_at, updated_at) "
                    "VALUES ('op-1', 'tai-age', 'TAI', 1, :ahora, :ahora)"
                ),
                {"ahora": AHORA},
            )
            conexion.execute(
                text(
                    "INSERT INTO question_sets (id, title, opposition_id, set_type, status, "
                    "created_at, updated_at) VALUES (:id, 'Examen de prueba', 'op-1', "
                    "'official_exam', 'confirmed', :ahora, :ahora)"
                ),
                {"id": conjunto, "ahora": AHORA},
            )
            for indice in range(1, preguntas + 1):
                conexion.execute(
                    text(
                        "INSERT INTO question_versions (id, question_set_id, stable_key, "
                        "version_no, stem, question_type, position, origin_type, created_at) "
                        "VALUES (:id, :conjunto, :clave, 1, 'Enunciado de prueba', "
                        "'single_choice', :posicion, 'official', :ahora)"
                    ),
                    {
                        "id": f"q-{indice}",
                        "conjunto": conjunto,
                        "clave": f"q{indice}",
                        "posicion": indice,
                        "ahora": AHORA,
                    },
                )
                conexion.execute(
                    text(
                        "INSERT INTO option_versions (id, question_version_id, stable_key, label, "
                        "text, position) VALUES (:id, :pregunta, 'a', 'A', 'Opcion A', 1)"
                    ),
                    {"id": f"opt-{indice}", "pregunta": f"q-{indice}"},
                )
    finally:
        engine.dispose()


def _ejecutar(
    settings: Settings, sentencia: str, parametros: dict[str, object] | None = None
) -> None:
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.begin() as conexion:
            conexion.execute(text(sentencia), parametros or {})
    finally:
        engine.dispose()


def _clave(settings: Settings, clave: str, **campos: object) -> None:
    valores: dict[str, object] = {
        "id": clave,
        "conjunto": "set-1",
        "version": 1,
        "estado": "draft",
        "aprobada": None,
    }
    valores.update(campos)
    _ejecutar(
        settings,
        "INSERT INTO answer_key_versions (id, question_set_id, version_no, status, approved_at, "
        "created_at) VALUES (:id, :conjunto, :version, :estado, :aprobada, :ahora)",
        {**valores, "ahora": AHORA},
    )


# --- identidad y estructura -------------------------------------------------------------------


def test_una_pregunta_no_repite_su_identidad_de_version(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    run_migrations(settings, revision="head")
    _sembrar(settings)

    with pytest.raises(IntegrityError):
        _ejecutar(
            settings,
            "INSERT INTO question_versions (id, question_set_id, stable_key, version_no, stem, "
            "question_type, position, origin_type, created_at) VALUES ('q-repe', 'set-1', 'q1', 1, "
            "'Otro enunciado', 'single_choice', 9, 'official', :ahora)",
            {"ahora": AHORA},
        )

    # La misma clave estable con **otra** versión sí entra: corregir una pregunta no la borra.
    _ejecutar(
        settings,
        "INSERT INTO question_versions (id, question_set_id, stable_key, version_no, stem, "
        "question_type, position, origin_type, created_at) VALUES ('q-v2', 'set-1', 'q1', 2, "
        "'Enunciado corregido', 'single_choice', 1, 'official', :ahora)",
        {"ahora": AHORA},
    )


def test_dos_opciones_no_comparten_clave_ni_sitio(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    run_migrations(settings, revision="head")
    _sembrar(settings)

    with pytest.raises(IntegrityError):
        _ejecutar(
            settings,
            "INSERT INTO option_versions (id, question_version_id, stable_key, label, text, "
            "position) VALUES ('opt-repe', 'q-1', 'a', 'A', 'Otra A', 2)",
        )
    with pytest.raises(IntegrityError):
        _ejecutar(
            settings,
            "INSERT INTO option_versions (id, question_version_id, stable_key, label, text, "
            "position) VALUES ('opt-sitio', 'q-1', 'b', 'B', 'Opcion B', 1)",
        )
    # Misma opción en **otra** versión de la pregunta, con otra posición: el modelo B.
    _ejecutar(
        settings,
        "INSERT INTO question_versions (id, question_set_id, stable_key, version_no, stem, "
        "question_type, position, origin_type, created_at) VALUES ('q1-b', 'set-1', 'q1', 2, "
        "'Enunciado', 'single_choice', 1, 'official', :ahora)",
        {"ahora": AHORA},
    )
    _ejecutar(
        settings,
        "INSERT INTO option_versions (id, question_version_id, stable_key, label, text, position) "
        "VALUES ('opt-b', 'q1-b', 'a', 'B', 'Opcion A reordenada', 3)",
    )


def test_una_reserva_lleva_orden_y_una_pregunta_no_se_sustituye_a_si_misma(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    run_migrations(settings, revision="head")
    _sembrar(settings)

    with pytest.raises(IntegrityError):
        _ejecutar(
            settings,
            "INSERT INTO question_versions (id, question_set_id, stable_key, version_no, stem, "
            "question_type, position, is_reserve, reserve_order, origin_type, created_at) VALUES "
            "('q-mal', 'set-1', 'q9', 1, 'Enunciado', 'single_choice', 9, 0, 3, 'official', "
            ":ahora)",
            {"ahora": AHORA},
        )
    _ejecutar(
        settings,
        "INSERT INTO question_versions (id, question_set_id, stable_key, version_no, stem, "
        "question_type, position, is_reserve, reserve_order, origin_type, created_at) VALUES "
        "('q-res', 'set-1', 'q9', 1, 'Reserva', 'single_choice', 9, 1, 1, 'official', :ahora)",
        {"ahora": AHORA},
    )
    with pytest.raises(IntegrityError):
        _ejecutar(settings, "UPDATE question_versions SET supersedes_id = id WHERE id = 'q-res'")


# --- claves y desenlaces -----------------------------------------------------------------------


def test_una_clave_activa_necesita_aprobacion(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    run_migrations(settings, revision="head")
    _sembrar(settings)

    with pytest.raises(IntegrityError):
        _clave(settings, "key-sin-aprobar", estado="active")

    _clave(settings, "key-1", estado="active", aprobada=AHORA)


def test_solo_una_clave_activa_por_conjunto_y_las_anteriores_permanecen(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    run_migrations(settings, revision="head")
    _sembrar(settings)

    _clave(settings, "key-v1", estado="active", aprobada=AHORA)

    with pytest.raises(IntegrityError):
        _clave(settings, "key-v2", version=2, estado="active", aprobada=AHORA)

    # La v1 se retira y la v2 puede activarse: corregir la clave no borra la anterior.
    _ejecutar(settings, "UPDATE answer_key_versions SET status = 'superseded' WHERE id = 'key-v1'")
    _clave(settings, "key-v2", version=2, estado="active", aprobada=AHORA)

    engine = build_engine(settings.data_paths.database)
    try:
        with engine.connect() as conexion:
            estados = dict(
                conexion.execute(
                    text("SELECT id, status FROM answer_key_versions ORDER BY id")
                ).all()
            )
    finally:
        engine.dispose()
    assert estados == {"key-v1": "superseded", "key-v2": "active"}


def test_un_desenlace_con_clave_necesita_la_clave(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    run_migrations(settings, revision="head")
    _sembrar(settings, preguntas=2)
    _clave(settings, "key-1", estado="active", aprobada=AHORA)

    with pytest.raises(IntegrityError):
        _ejecutar(
            settings,
            "INSERT INTO answer_key_entries (answer_key_version_id, question_version_id, outcome, "
            "correct_option_keys_json) VALUES ('key-1', 'q-1', 'keyed', NULL)",
        )
    with pytest.raises(IntegrityError):
        _ejecutar(
            settings,
            "INSERT INTO answer_key_entries (answer_key_version_id, question_version_id, outcome, "
            "correct_option_keys_json) VALUES ('key-1', 'q-1', 'keyed', '[]')",
        )
    with pytest.raises(IntegrityError):
        _ejecutar(
            settings,
            "INSERT INTO answer_key_entries (answer_key_version_id, question_version_id, outcome) "
            "VALUES ('key-1', 'q-1', 'inventado')",
        )

    _ejecutar(
        settings,
        "INSERT INTO answer_key_entries (answer_key_version_id, question_version_id, outcome, "
        "correct_option_keys_json) VALUES ('key-1', 'q-1', 'keyed', '[\"a\"]')",
    )
    # Anulada y sin responder no llevan clave: son desenlaces distintos de «con clave».
    _ejecutar(
        settings,
        "INSERT INTO answer_key_entries (answer_key_version_id, question_version_id, outcome, "
        "notes) VALUES ('key-1', 'q-2', 'annulled', 'Pregunta anulada por la comision')",
    )


# --- evidencias y explicaciones ----------------------------------------------------------------


def _documento_con_evidencia(settings: Settings) -> None:
    """Un documento con su versión y un span de evidencia: es lo que una pregunta puede citar."""
    _ejecutar(
        settings,
        "INSERT INTO source_artifacts (id, sha256, size_bytes, media_type, storage_key, "
        "first_seen_at) VALUES ('art-1', :sha, 100, 'application/pdf', 'sha256/aa', :ahora)",
        {"sha": SHA_A, "ahora": AHORA},
    )
    _ejecutar(
        settings,
        "INSERT INTO logical_documents (id, canonical_title, document_type, owner_scope, "
        "created_at, updated_at) VALUES ('doc-1', 'Temario', 'curriculum', 'private_user', :ahora, "
        ":ahora)",
        {"ahora": AHORA},
    )
    _ejecutar(
        settings,
        "INSERT INTO document_versions (id, logical_document_id, artifact_id, status, created_at) "
        "VALUES ('ver-1', 'doc-1', 'art-1', 'candidate', :ahora)",
        {"ahora": AHORA},
    )
    _ejecutar(
        settings,
        "INSERT INTO evidence_spans (id, document_version_id, ordinal, text, normalized_text, "
        "created_at) VALUES ('span-1', 'ver-1', 1, 'El plazo es de diez dias.', "
        "'el plazo es de diez dias.', :ahora)",
        {"ahora": AHORA},
    )


def test_una_evidencia_citada_por_una_pregunta_no_se_puede_borrar(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    run_migrations(settings, revision="head")
    _sembrar(settings)
    _documento_con_evidencia(settings)
    _ejecutar(
        settings,
        "INSERT INTO question_evidence (question_version_id, evidence_span_id, role, claim, "
        "created_at) VALUES ('q-1', 'span-1', 'correct', 'Sostiene la respuesta correcta', :ahora)",
        {"ahora": AHORA},
    )

    with pytest.raises(IntegrityError):
        _ejecutar(settings, "DELETE FROM evidence_spans WHERE id = 'span-1'")

    # Y un rol que no existe se rechaza: la evidencia dice qué parte sostiene, no «algo».
    with pytest.raises(IntegrityError):
        _ejecutar(
            settings,
            "INSERT INTO question_evidence (question_version_id, evidence_span_id, role, "
            "created_at) VALUES ('q-1', 'span-1', 'inventado', :ahora)",
            {"ahora": AHORA},
        )


def test_una_explicacion_generada_dice_con_que_modelo_se_genero(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    run_migrations(settings, revision="head")
    _sembrar(settings)

    with pytest.raises(IntegrityError):
        _ejecutar(
            settings,
            "INSERT INTO question_explanations (id, question_version_id, origin, created_at, text) "
            "VALUES ('exp-1', 'q-1', 'generated', :ahora, 'Porque sí')",
            {"ahora": AHORA},
        )

    _ejecutar(
        settings,
        "INSERT INTO question_explanations (id, question_version_id, origin, model_name, "
        "prompt_template_version, created_at, text) VALUES ('exp-1', 'q-1', 'generated', "
        "'modelo-x', 'v3', :ahora, 'Porque el plazo es de diez días')",
        {"ahora": AHORA},
    )
    # Una sola explicación de la pregunta entera por versión (el NULL no lo cubre el único normal).
    with pytest.raises(IntegrityError):
        _ejecutar(
            settings,
            "INSERT INTO question_explanations (id, question_version_id, origin, created_at, text) "
            "VALUES ('exp-2', 'q-1', 'official', :ahora, 'Otra explicación de la pregunta')",
            {"ahora": AHORA},
        )
    # Pero sí puede haber una por opción, además de la de la pregunta.
    _ejecutar(
        settings,
        "INSERT INTO question_explanations (id, question_version_id, option_stable_key, origin, "
        "created_at, text) VALUES ('exp-3', 'q-1', 'a', 'official', :ahora, "
        "'La A es correcta por esto')",
        {"ahora": AHORA},
    )
