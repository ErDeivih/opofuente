"""Migración 0018: índice léxico y consultas de RAG (S09).

Lo que se prueba no es que las tablas existan, sino **lo que la base garantiza**, que es lo que
sostiene los criterios de aceptación del slice:

1. el índice FTS5 se mantiene en sincronía **por disparadores**: insertar un fragmento lo indexa,
   actualizarlo lo reindexa y borrarlo lo saca (y `rebuild` lo rehace desde SQLite);
2. la etiqueta de cita también se indexa: buscar «Tema 1» encuentra el fragmento aunque su texto no
   lo diga, que es lo que hace falta para preguntar por un tema del programa;
3. una respuesta guardada **no puede citar una evidencia que no existe** (clave foránea), y borrar
   una evidencia citada falla: la respuesta se puede auditar después;
4. los vocabularios son cerrados: un estado de respuesta, una estrategia o un soporte inventados no
   entran, y una consulta sin texto tampoco.
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


def _consultar(settings: Settings, sentencia: str) -> list[tuple[object, ...]]:
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.connect() as conexion:
            return list(conexion.execute(text(sentencia)).all())
    finally:
        engine.dispose()


def _documento(settings: Settings) -> None:
    """Un documento aceptado con su versión, que es lo mínimo para tener evidencia."""
    _ejecutar(
        settings,
        "INSERT INTO source_artifacts (id, sha256, size_bytes, media_type, storage_key, "
        "first_seen_at) VALUES ('art-1', :sha, 10, 'text/plain', 'k', :ahora)",
        {"sha": "c" * 64, "ahora": AHORA},
    )
    _ejecutar(
        settings,
        "INSERT INTO logical_documents (id, canonical_title, document_type, owner_scope, "
        "created_at, updated_at) VALUES ('doc-1', 'Temario', 'curriculum', 'private_user', "
        ":ahora, :ahora)",
        {"ahora": AHORA},
    )
    _ejecutar(
        settings,
        "INSERT INTO document_versions (id, logical_document_id, artifact_id, status, "
        "approved_at, created_at) VALUES ('ver-1', 'doc-1', 'art-1', 'accepted', :ahora, :ahora)",
        {"ahora": AHORA},
    )


def _span(
    settings: Settings,
    *,
    identificador: str = "span-1",
    texto: str = "El plazo es de diez días hábiles",
) -> None:
    _ejecutar(
        settings,
        "INSERT INTO evidence_spans (id, document_version_id, ordinal, text, normalized_text, "
        "citation_label, index_status, created_at) VALUES (:id, 'ver-1', 1, :texto, :normalizado, "
        "'Tema 1, pág. 3', 'pending', :ahora)",
        {"id": identificador, "texto": texto, "normalizado": texto.lower(), "ahora": AHORA},
    )


# --- el índice léxico ---------------------------------------------------------------------------


def test_el_indice_se_mantiene_con_disparadores(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    run_migrations(settings, revision="head")
    _documento(settings)

    _span(settings)
    assert _consultar(settings, "SELECT id FROM evidence_fts WHERE evidence_fts MATCH 'plazo'") == [
        ("span-1",)
    ]
    # La etiqueta de cita se indexa: sirve para preguntar por un tema del programa.
    assert _consultar(settings, "SELECT id FROM evidence_fts WHERE evidence_fts MATCH 'Tema'") == [
        ("span-1",)
    ]

    # El texto se indexa junto a su versión normalizada: se actualizan las dos, como hace la
    # aplicación al promocionar, y el índice deja de encontrar lo viejo.
    _ejecutar(
        settings,
        "UPDATE evidence_spans SET text = 'El plazo es de veinte días', "
        "normalized_text = 'el plazo es de veinte dias' WHERE id = 'span-1'",
    )
    assert _consultar(
        settings, "SELECT id FROM evidence_fts WHERE evidence_fts MATCH 'veinte'"
    ) == [("span-1",)]
    assert _consultar(settings, "SELECT id FROM evidence_fts WHERE evidence_fts MATCH 'diez'") == []

    _ejecutar(settings, "DELETE FROM evidence_spans WHERE id = 'span-1'")
    assert (
        _consultar(settings, "SELECT id FROM evidence_fts WHERE evidence_fts MATCH 'plazo'") == []
    )


def test_el_indice_se_reconstruye_desde_sqlite(tmp_path: Path) -> None:
    """«Índices reconstruibles» (§4): se puede vaciar el índice y rehacerlo sin volver a extraer."""
    settings = _settings(tmp_path)
    run_migrations(settings, revision="head")
    _documento(settings)
    _span(settings)
    _ejecutar(settings, "INSERT INTO evidence_fts(evidence_fts) VALUES('delete-all')")
    assert (
        _consultar(settings, "SELECT id FROM evidence_fts WHERE evidence_fts MATCH 'plazo'") == []
    )

    _ejecutar(settings, "INSERT INTO evidence_fts(evidence_fts) VALUES('rebuild')")

    assert _consultar(settings, "SELECT id FROM evidence_fts WHERE evidence_fts MATCH 'plazo'") == [
        ("span-1",)
    ]
    # Y el índice contiene el texto que ya estaba en la base, no una copia aparte.
    assert _consultar(
        settings, "SELECT count(*) FROM evidence_fts WHERE evidence_fts MATCH 'diez'"
    ) == [(1,)]


# --- consultas, recuperaciones y respuestas -----------------------------------------------------


def _consulta(settings: Settings, *, identificador: str = "q-1", **campos: object) -> None:
    valores: dict[str, object] = {
        "id": identificador,
        "pregunta": "¿Cuál es el plazo?",
        "strategy": "lexical",
        "status": "supported",
    }
    valores.update(campos)
    _ejecutar(
        settings,
        "INSERT INTO rag_queries (id, question, filters_json, strategy, version_mode, "
        "corpus_revision, provider, created_at) VALUES (:id, :pregunta, '{}', :strategy, "
        "'current', 'rev-1', 'extractive', :ahora)",
        {**valores, "ahora": AHORA},
    )


def _respuesta(
    settings: Settings, *, identificador: str = "ans-1", estado: str = "supported"
) -> None:
    _ejecutar(
        settings,
        "INSERT INTO generated_answers (id, query_id, status, short_answer, explanation, "
        "created_at) VALUES (:id, 'q-1', :estado, 'corta', 'larga', :ahora)",
        {"id": identificador, "estado": estado, "ahora": AHORA},
    )


def test_una_respuesta_guarda_sus_afirmaciones_y_sus_evidencias(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    run_migrations(settings, revision="head")
    _documento(settings)
    _span(settings)
    _consulta(settings)
    _respuesta(settings)
    _ejecutar(
        settings,
        "INSERT INTO answer_claims (id, answer_id, position, text, support, created_at) "
        "VALUES ('claim-1', 'ans-1', 1, 'El plazo es de diez días', 'direct', :ahora)",
        {"ahora": AHORA},
    )
    _ejecutar(
        settings,
        "INSERT INTO answer_claim_evidence (claim_id, span_id) VALUES ('claim-1', 'span-1')",
    )

    # Una evidencia citada por una respuesta no se puede borrar: la respuesta se audita después.
    with pytest.raises(IntegrityError):
        _ejecutar(settings, "DELETE FROM evidence_spans WHERE id = 'span-1'")

    # Y una cita a una evidencia que no existe no entra.
    with pytest.raises(IntegrityError):
        _ejecutar(
            settings,
            "INSERT INTO answer_claims (id, answer_id, position, text, created_at) "
            "VALUES ('claim-2', 'ans-1', 2, 'Otra', :ahora)",
            {"ahora": AHORA},
        )
        _ejecutar(
            settings,
            "INSERT INTO answer_claim_evidence (claim_id, span_id) VALUES ('claim-2', 'no-existe')",
        )


def test_una_consulta_se_guarda_con_su_revision_del_corpus(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    run_migrations(settings, revision="head")
    _documento(settings)
    _consulta(settings)

    with pytest.raises(IntegrityError):
        _consulta(settings, identificador="q-2", strategy="inventada")

    con_texto_vacio = (
        "INSERT INTO rag_queries (id, question, filters_json, strategy, version_mode, "
        "corpus_revision, provider, created_at) VALUES ('q-3', '   ', '{}', 'lexical', "
        "'current', 'rev-1', 'extractive', :ahora)"
    )
    with pytest.raises(IntegrityError):
        _ejecutar(settings, con_texto_vacio, {"ahora": AHORA})


def test_los_vocabularios_de_la_respuesta_son_cerrados(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    run_migrations(settings, revision="head")
    _documento(settings)
    _consulta(settings)

    with pytest.raises(IntegrityError):
        _respuesta(settings, estado="mas-o-menos")

    _respuesta(settings, estado="insufficient"), "una respuesta insuficiente es un estado válido"

    with pytest.raises(IntegrityError):
        _ejecutar(
            settings,
            "INSERT INTO answer_claims (id, answer_id, position, text, support, created_at) "
            "VALUES ('claim-1', 'ans-1', 1, 'algo', 'inventado', :ahora)",
            {"ahora": AHORA},
        )
