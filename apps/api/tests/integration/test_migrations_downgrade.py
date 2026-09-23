"""La vuelta atrás de las migraciones de S05 a S12, **ejecutada de verdad**.

El método del proyecto es explícito: «escrito no es hecho; ejecutado es hecho». Varios slices
declaraban que su `downgrade` estaba probado y no había ninguna prueba que lo ejecutara (solo 0011 y
0012 lo hacían), así que esta prueba recorre la cadena entera hacia abajo, un escalón cada vez, y
comprueba en cada uno tres cosas:

1. la revisión marcada es la que se pidió;
2. las tablas que esa migración había creado **ya no están** (una migración que solo ensancha una
   restricción no retira ninguna tabla, y por eso su escalón va vacío);
3. volver a subir a la cabeza las recrea: bajar no deja el esquema en un estado del que no se pueda
   salir.

No comprueba la forma de cada tabla recreada (eso lo hacen las pruebas de cada migración): comprueba
que la bajada existe, se ejecuta y devuelve el esquema a su sitio.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import text

from alembic import command
from opofuente.config import Settings
from opofuente.infrastructure.db import build_engine
from opofuente.infrastructure.migrations import alembic_config, run_migrations, script_head

#: Revisión de partida y, por cada escalón, la revisión a la que se baja y las tablas que deben
#: desaparecer al hacerlo. El orden es el de la cadena, de la más nueva a la más antigua.
ESCALONES: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    (
        "0022_convocation_exam_date_note",
        "0021_convocation_available",
        (),
    ),
    (
        "0021_convocation_available",
        "0020_changes_and_derivatives",
        (),
    ),
    (
        "0020_changes_and_derivatives",
        "0019_errors_and_reviews",
        ("derived_artifacts", "dependency_edges", "change_sets"),
    ),
    (
        "0019_errors_and_reviews",
        "0018_search_and_rag",
        ("learning_errors", "review_items", "review_events"),
    ),
    (
        "0018_search_and_rag",
        "0017_previous_result",
        ("rag_queries", "retrieval_hits", "generated_answers", "answer_claims"),
    ),
    (
        "0017_previous_result",
        "0016_study_sessions",
        (),
    ),
    (
        "0016_study_sessions",
        "0015_question_notes_and_issues",
        ("study_sessions", "session_questions", "attempts", "attempt_evaluations"),
    ),
    (
        "0015_question_notes_and_issues",
        "0014_questions_and_keys",
        ("question_issue_reports",),
    ),
    (
        "0014_questions_and_keys",
        "0013_documents_versions_and_rights",
        (
            "question_sets",
            "question_versions",
            "option_versions",
            "answer_key_versions",
            "answer_key_entries",
            "question_explanations",
            "question_evidence",
        ),
    ),
    (
        "0013_documents_versions_and_rights",
        "0012_classification_and_review",
        (
            "logical_documents",
            "document_versions",
            "document_sections",
            "evidence_spans",
            "rights_statuses",
            "collections",
            "collection_items",
        ),
    ),
)


def _settings(tmp_path: Path) -> Settings:
    return Settings(data_dir=tmp_path / "datos", _env_file=None)


def _bajar_a(settings: Settings, revision: str) -> None:
    """Baja de revisión de verdad: `run_migrations` solo sube."""
    command.downgrade(alembic_config(settings), revision)


def _tablas(settings: Settings) -> set[str]:
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.connect() as conexion:
            return {
                str(fila[0])
                for fila in conexion.execute(
                    text("SELECT name FROM sqlite_master WHERE type = 'table'")
                )
            }
    finally:
        engine.dispose()


def _revision(settings: Settings) -> str:
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.connect() as conexion:
            return str(conexion.execute(text("SELECT version_num FROM alembic_version")).scalar())
    finally:
        engine.dispose()


def test_la_cadena_de_s05_a_s09_se_puede_recorrer_hacia_atras(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    run_migrations(settings, revision="head")
    assert _revision(settings) == script_head(settings)

    for desde, hasta, tablas_que_se_van in ESCALONES:
        assert _revision(settings) == desde, f"se esperaba estar en {desde}"
        _bajar_a(settings, hasta)
        assert _revision(settings) == hasta, f"no se bajó de {desde} a {hasta}"
        presentes = _tablas(settings)
        for tabla in tablas_que_se_van:
            assert tabla not in presentes, f"{tabla} sigue ahí tras bajar de {desde}"


def test_volver_a_subir_recrea_lo_que_la_bajada_retiro(tmp_path: Path) -> None:
    """Bajar no deja el esquema inservible: subir otra vez lo devuelve a la cabeza."""
    settings = _settings(tmp_path)
    run_migrations(settings, revision="head")

    _bajar_a(settings, "0012_classification_and_review")
    retiradas = {tabla for _, _, tablas in ESCALONES for tabla in tablas}
    presentes = _tablas(settings)
    for tabla in sorted(retiradas):
        assert tabla not in presentes, f"{tabla} debería haber desaparecido al bajar a 0012"

    run_migrations(settings, revision="head")

    assert _revision(settings) == script_head(settings)
    presentes = _tablas(settings)
    for tabla in sorted(retiradas):
        assert tabla in presentes, f"{tabla} no se ha recreado al volver a subir"


@pytest.mark.parametrize(
    ("revision", "tabla"),
    [
        ("0013_documents_versions_and_rights", "rights_statuses"),
        ("0014_questions_and_keys", "answer_key_entries"),
        ("0016_study_sessions", "attempt_evaluations"),
        ("0018_search_and_rag", "retrieval_hits"),
        ("0019_errors_and_reviews", "review_items"),
        ("0020_changes_and_derivatives", "derived_artifacts"),
    ],
)
def test_cada_migracion_deja_su_tabla_al_llegar_a_ella(
    tmp_path: Path, revision: str, tabla: str
) -> None:
    """Cada escalón se puede alcanzar **desde cero**: la cadena no depende de haber subido antes."""
    settings = _settings(tmp_path)

    run_migrations(settings, revision=revision)

    assert _revision(settings) == revision
    assert tabla in _tablas(settings)
