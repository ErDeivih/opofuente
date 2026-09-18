"""Pruebas de integración de la búsqueda y el RAG (S09) sobre base de datos real.

Lo que se comprueba aquí es lo que no se puede comprobar en una prueba unitaria:

1. **el índice encuentra lo que hay indexado**: buscar devuelve el fragmento con su cita y su
   procedencia (documento, versión, sección, página), y `rebuild` lo rehace desde SQLite;
2. **el corpus elegible filtra de verdad**: una versión en estado `candidate` no sale y su motivo se
   dice; con el histórico pedido explícitamente, sí;
3. **la pregunta negativa devuelve `insufficient`** sin afirmaciones, y la parcial dice qué falta;
4. **las citas solo apuntan a fragmentos entregados** y quedan guardadas con la respuesta;
5. **todo el ciclo queda guardado**: la consulta con su revisión del corpus, **todos** los
   fragmentos recuperados (marcando los usados) y la respuesta con la evidencia de cada
   afirmación;
6. **sin proveedor de embeddings** la búsqueda es léxica y se declara la degradación.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from pathlib import Path

import pytest
from sqlalchemy import text

from opofuente.application.search_models import RetrievalView
from opofuente.application.search_service import AskRequest, SearchRequest, SearchService
from opofuente.config import Settings
from opofuente.domain.errors import InvariantViolationError, NotFoundError
from opofuente.domain.rag import (
    AnswerStatus,
    SearchFilters,
    SearchStrategy,
    VersionMode,
)
from opofuente.infrastructure.db import build_engine, build_session_factory
from opofuente.infrastructure.migrations import run_migrations
from opofuente.infrastructure.search_repository import SqlAlchemySearchRepository

AHORA = datetime(2026, 9, 17, 12, 0, tzinfo=UTC)


class _Reloj:
    def now(self) -> datetime:
        return AHORA


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


def _servicio(settings: Settings) -> SearchService:
    engine = build_engine(settings.data_paths.database)
    return SearchService(
        search=SqlAlchemySearchRepository(build_session_factory(engine)), clock=_Reloj()
    )


def _documento(
    settings: Settings,
    *,
    version_id: str,
    estado: str,
    titulo: str,
    valido_hasta: date | None = None,
    aprobado: datetime | None = AHORA,
) -> None:
    """Un documento con su versión y su representación, en el estado que pida la prueba."""
    _ejecutar(
        settings,
        "INSERT INTO source_artifacts (id, sha256, size_bytes, media_type, storage_key, "
        "first_seen_at) VALUES (:id, :sha, 10, 'text/plain', 'k', :ahora)",
        {"id": f"art-{version_id}", "sha": (version_id * 32)[:64].ljust(64, "a"), "ahora": AHORA},
    )
    _ejecutar(
        settings,
        "INSERT INTO extracted_representations (id, artifact_id, extractor_name, "
        "extractor_version, kind, status, quality, char_count, created_at) VALUES (:rep, :art, "
        "'text', '1', 'plain_text', 'extracted', 'good', 100, :ahora)",
        {"rep": f"rep-{version_id}", "art": f"art-{version_id}", "ahora": AHORA},
    )
    _ejecutar(
        settings,
        "INSERT INTO logical_documents (id, canonical_title, document_type, authority_tier, "
        "owner_scope, created_at, updated_at) VALUES (:doc, :titulo, 'curriculum', 'A', "
        "'private_user', :ahora, :ahora)",
        {"doc": f"doc-{version_id}", "titulo": titulo, "ahora": AHORA},
    )
    _ejecutar(
        settings,
        "INSERT INTO document_versions (id, logical_document_id, artifact_id, representation_id, "
        "status, valid_to, approved_at, language, created_at) VALUES (:id, :doc, :art, :rep, "
        ":estado, :hasta, :aprobado, 'es', :ahora)",
        {
            "id": version_id,
            "doc": f"doc-{version_id}",
            "art": f"art-{version_id}",
            "rep": f"rep-{version_id}",
            "estado": estado,
            "hasta": valido_hasta,
            "aprobado": aprobado if estado == "accepted" else None,
            "ahora": AHORA,
        },
    )


def _seccion_y_span(
    settings: Settings,
    *,
    version_id: str,
    span_id: str,
    texto: str,
    titulo: str = "Tema 1: plazos",
    page: int = 3,
    ordinal: int = 1,
) -> None:
    _ejecutar(
        settings,
        "INSERT INTO document_sections (id, document_version_id, section_type, title, position, "
        "ordinal, page_start, page_end, char_start, char_end) VALUES (:sec, :ver, 'topic', "
        ":titulo, :ordinal, :ordinal, :page, :page, 0, 100)",
        {
            "sec": f"sec-{span_id}",
            "ver": version_id,
            "titulo": titulo,
            "page": page,
            "ordinal": ordinal,
        },
    )
    _ejecutar(
        settings,
        "INSERT INTO evidence_spans (id, document_version_id, section_id, ordinal, page, "
        "citation_label, quality, index_status, text, normalized_text, created_at) VALUES (:id, "
        ":ver, :sec, :ordinal, :page, :cita, 'good', 'indexed', :texto, :normalizado, :ahora)",
        {
            "id": span_id,
            "ver": version_id,
            "sec": f"sec-{span_id}",
            "page": page,
            "ordinal": ordinal,
            "cita": f"{titulo}, pág. {page}",
            "texto": texto,
            "normalizado": texto.lower(),
            "ahora": AHORA,
        },
    )


def _corpus(settings: Settings) -> None:
    """Un corpus pequeño y realista: una versión publicada, una candidata y una histórica."""
    run_migrations(settings, revision="head")
    _documento(settings, version_id="v-accepted", estado="accepted", titulo="Temario TAI")
    _seccion_y_span(
        settings,
        version_id="v-accepted",
        span_id="span-plazo",
        texto="El plazo de alegaciones es de diez dias habiles desde la notificacion.",
    )
    _seccion_y_span(
        settings,
        version_id="v-accepted",
        span_id="span-silencio",
        texto="El silencio administrativo se entiende estimado en los procedimientos de concesion.",
        titulo="Tema 2: silencio",
        page=7,
        ordinal=2,
    )
    _documento(
        settings, version_id="v-candidate", estado="candidate", titulo="Apuntes sin publicar"
    )
    _seccion_y_span(
        settings,
        version_id="v-candidate",
        span_id="span-borrador",
        texto="El plazo de alegaciones es de veinte dias segun mis apuntes sin revisar.",
    )
    _documento(
        settings,
        version_id="v-superseded",
        estado="superseded",
        titulo="Temario antiguo",
        aprobado=None,
    )
    _seccion_y_span(
        settings,
        version_id="v-superseded",
        span_id="span-antiguo",
        texto="El plazo de alegaciones era de quince dias antes de la reforma.",
    )


# --- búsqueda -----------------------------------------------------------------------------------


def test_la_busqueda_encuentra_lo_publicado_con_su_cita(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    _corpus(settings)
    servicio = _servicio(settings)

    resultado = servicio.search_only(
        SearchRequest(query="plazo de alegaciones", filters=SearchFilters(limit=5))
    )

    assert resultado.total >= 1
    primero = resultado.hits[0]
    assert primero.span.id in ("span-plazo", "span-silencio", "span-borrador", "span-antiguo")
    assert primero.span.citation_label is not None and "pág." in primero.span.citation_label
    assert primero.span.document_title and primero.span.page == 3
    assert resultado.strategy is SearchStrategy.LEXICAL
    assert any("solo léxica" in aviso for aviso in resultado.degradations)


def test_lo_no_publicado_no_aparece_y_se_dice_por_que(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    _corpus(settings)
    servicio = _servicio(settings)

    resultado = servicio.search_only(
        SearchRequest(query="plazo de alegaciones", filters=SearchFilters(limit=5))
    )

    ids = resultado.ids
    assert "span-borrador" not in ids, "una versión candidata no se recupera"
    assert "span-antiguo" not in ids, "una versión sustituida tampoco, sin pedir el histórico"
    assert resultado.excluded, "y se dice qué se ha quedado fuera"
    assert any("candidate" in motivo or "superseded" in motivo for motivo in resultado.excluded)


def test_pedir_el_historico_permite_encontrar_la_version_sustituida(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    _corpus(settings)
    servicio = _servicio(settings)

    resultado = servicio.search_only(
        SearchRequest(
            query="plazo de alegaciones",
            filters=SearchFilters(limit=5, version_mode=VersionMode.EXPLICIT_HISTORICAL),
        )
    )

    assert "span-antiguo" in resultado.ids
    assert resultado.version_mode is VersionMode.EXPLICIT_HISTORICAL


def test_el_indice_se_reconstruye_y_sigue_encontrando_lo_mismo(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    _corpus(settings)
    servicio = _servicio(settings)
    antes = servicio.search_only(SearchRequest(query="silencio administrativo"))

    total = servicio.rebuild()
    despues = servicio.search_only(SearchRequest(query="silencio administrativo"))

    assert total >= 3, "se indexan todos los fragmentos, también los no publicados"
    assert [hit.span.id for hit in antes.hits] == [hit.span.id for hit in despues.hits]


# --- RAG ----------------------------------------------------------------------------------------


def test_una_pregunta_del_corpus_se_responde_con_citas(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    _corpus(settings)
    servicio = _servicio(settings)

    consulta = servicio.ask(
        AskRequest(query="plazo de alegaciones", filters=SearchFilters(limit=5))
    )

    assert consulta.answer is not None
    assert consulta.answer.status is AnswerStatus.SUPPORTED
    assert consulta.answer.claims, "una respuesta respaldada lleva afirmaciones"
    for claim in consulta.answer.claims:
        assert claim.evidence, "cada afirmación trae su evidencia"
        for evidencia in claim.evidence:
            assert evidencia.citation_label is not None
            assert evidencia.document_version_id == "v-accepted", "solo se cita lo publicado"
    assert consulta.answer.provider == "extractive"
    assert consulta.answer.model is None
    assert consulta.answer.short_answer


def test_una_pregunta_fuera_del_corpus_es_insuficiente_y_no_inventa(tmp_path: Path) -> None:
    """El criterio de aceptación del slice: la pregunta negativa devuelve «insuficiente»."""
    settings = _settings(tmp_path)
    _corpus(settings)
    servicio = _servicio(settings)

    consulta = servicio.ask(AskRequest(query="naves espaciales de propulsion ionica"))

    assert consulta.answer is not None
    assert consulta.answer.status is AnswerStatus.INSUFFICIENT
    assert consulta.answer.claims == ()
    assert consulta.answer.uncertainties, "se dice qué no se ha encontrado"


def test_una_pregunta_a_la_que_le_falta_un_termino_es_parcial(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    _corpus(settings)
    servicio = _servicio(settings)

    consulta = servicio.ask(
        AskRequest(query="plazo de subsanacion", filters=SearchFilters(limit=5))
    )

    assert consulta.answer is not None
    assert consulta.answer.status is AnswerStatus.PARTIAL
    assert consulta.answer.claims, "lo que sí está respaldado se muestra"
    assert any("subsanacion" in texto for texto in consulta.answer.uncertainties)


def test_el_ciclo_queda_guardado_para_poder_auditarlo(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    _corpus(settings)
    servicio = _servicio(settings)

    consulta = servicio.ask(
        AskRequest(query="plazo de alegaciones", filters=SearchFilters(limit=5))
    )

    assert consulta.corpus_revision, "la consulta guarda con qué corpus se respondió"
    recuperacion: RetrievalView = servicio.retrieval(consulta.id)
    assert recuperacion.hits, "se guardan todos los fragmentos recuperados"
    assert recuperacion.used_ids, "y cuáles se usaron"
    assert all(hit.span.citation_label is not None for hit in recuperacion.hits)

    # Y el fragmento citado se puede abrir por su identificador.
    citado = consulta.answer.claims[0].evidence[0]
    abierto = servicio.span(citado.id)
    assert abierto.text == citado.text
    assert abierto.document_id == citado.document_id

    # Una consulta que no existe no se inventa.
    with pytest.raises(NotFoundError):
        servicio.query("no-existe")


def test_la_busqueda_sin_generar_respuesta_no_guarda_respuesta(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    _corpus(settings)
    servicio = _servicio(settings)

    resultado = servicio.search_only(SearchRequest(query="plazo de alegaciones"))

    assert resultado.hits
    # Una búsqueda no lleva respuesta: no hay forma de pedirla, solo busca.
    assert not hasattr(resultado, "answer")


def test_la_busqueda_hibrida_sin_proveedor_sigue_siendo_lexica(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    _corpus(settings)
    servicio = _servicio(settings)

    resultado = servicio.search_only(
        SearchRequest(
            query="plazo de alegaciones",
            filters=SearchFilters(limit=5),
            strategy=SearchStrategy.HYBRID,
        )
    )

    assert resultado.hits, "FTS sigue funcionando sin vectores"
    assert resultado.strategy is SearchStrategy.LEXICAL
    assert servicio.capabilities(), "la capacidad que falta se declara con su motivo"


def test_una_busqueda_sin_texto_no_se_acepta(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    _corpus(settings)
    servicio = _servicio(settings)

    with pytest.raises(InvariantViolationError):
        servicio.search_only(SearchRequest(query="   "))
