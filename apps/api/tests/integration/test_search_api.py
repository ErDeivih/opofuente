"""Pruebas de integración de las rutas de búsqueda y RAG (08_API-CONTRACT §8).

Lo que sostienen, por ruta y por criterio de aceptación del slice:

1. **buscar no responde**: `POST /search` devuelve fragmentos con su cita y no genera respuesta;
2. **la pregunta negativa devuelve `insufficient`** (y con incertidumbres, no con un texto vacío);
3. **las citas solo apuntan a fragmentos entregados**: cada afirmación de una respuesta trae
   sus evidencias, y todas se pueden abrir por `GET /evidence-spans/{id}`;
4. **el corpus elegible filtra de verdad**: lo no publicado no sale y se dice por qué, y el
   histórico solo aparece si se pide;
5. **todo queda auditable**: la consulta, su recuperación completa (con los usados) y su respuesta.
"""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi.testclient import TestClient
from sqlalchemy import text

from opofuente.config import Settings
from opofuente.infrastructure.db import build_engine

AHORA = datetime(2026, 9, 17, 12, 0, tzinfo=UTC)
ALLOWED_ORIGIN = {"Origin": "http://127.0.0.1:5173"}


def _ejecutar(
    settings: Settings, sentencia: str, parametros: dict[str, object] | None = None
) -> None:
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.begin() as conexion:
            conexion.execute(text(sentencia), parametros or {})
    finally:
        engine.dispose()


def _corpus(settings: Settings) -> None:
    """Un documento publicado con dos fragmentos y otro sin publicar, para probar el filtro."""
    for version_id, estado, titulo in (
        ("v-ok", "accepted", "Temario TAI"),
        ("v-borrador", "candidate", "Apuntes sin publicar"),
    ):
        _ejecutar(
            settings,
            "INSERT INTO source_artifacts (id, sha256, size_bytes, media_type, storage_key, "
            "first_seen_at) VALUES (:id, :sha, 10, 'text/plain', 'k', :ahora)",
            {"id": f"art-{version_id}", "sha": f"{version_id}-".ljust(64, "b"), "ahora": AHORA},
        )
        _ejecutar(
            settings,
            "INSERT INTO extracted_representations (id, artifact_id, extractor_name, "
            "extractor_version, kind, status, quality, char_count, created_at) VALUES (:rep, "
            ":art, 'text', '1', 'plain_text', 'extracted', 'good', 100, :ahora)",
            {"rep": f"rep-{version_id}", "art": f"art-{version_id}", "ahora": AHORA},
        )
        _ejecutar(
            settings,
            "INSERT INTO logical_documents (id, canonical_title, document_type, owner_scope, "
            "created_at, updated_at) VALUES (:doc, :titulo, 'curriculum', 'private_user', :ahora, "
            ":ahora)",
            {"doc": f"doc-{version_id}", "titulo": titulo, "ahora": AHORA},
        )
        _ejecutar(
            settings,
            "INSERT INTO document_versions (id, logical_document_id, artifact_id, "
            "representation_id, status, approved_at, language, created_at) VALUES (:id, :doc, "
            ":art, :rep, :estado, :aprobado, 'es', :ahora)",
            {
                "id": version_id,
                "doc": f"doc-{version_id}",
                "art": f"art-{version_id}",
                "rep": f"rep-{version_id}",
                "estado": estado,
                "aprobado": AHORA if estado == "accepted" else None,
                "ahora": AHORA,
            },
        )
        _ejecutar(
            settings,
            "INSERT INTO document_sections (id, document_version_id, section_type, title, "
            "position, ordinal, page_start, page_end, char_start, char_end) VALUES (:sec, :ver, "
            "'topic', 'Tema 1: plazos', 1, 1, 3, 3, 0, 100)",
            {"sec": f"sec-{version_id}", "ver": version_id},
        )
        _ejecutar(
            settings,
            "INSERT INTO evidence_spans (id, document_version_id, section_id, ordinal, page, "
            "citation_label, quality, index_status, text, normalized_text, created_at) VALUES "
            "(:span, :ver, :sec, 1, 3, 'Tema 1: plazos, pág. 3', 'good', 'indexed', :texto, "
            ":normalizado, :ahora)",
            {
                "span": f"span-{version_id}",
                "ver": version_id,
                "sec": f"sec-{version_id}",
                "texto": (
                    "El plazo de alegaciones es de diez dias habiles desde la notificacion."
                    if version_id == "v-ok"
                    else "El plazo de alegaciones es de veinte dias segun mis apuntes."
                ),
                "normalizado": "el plazo de alegaciones es de diez dias habiles",
                "ahora": AHORA,
            },
        )


def test_buscar_devuelve_fragmentos_con_su_cita_y_no_responde(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    _corpus(seeded_settings)

    respuesta = seeded_client.post(
        "/api/v1/search", json={"query": "plazo de alegaciones"}, headers=ALLOWED_ORIGIN
    )

    assert respuesta.status_code == 200, respuesta.text
    cuerpo = respuesta.json()
    assert cuerpo["total"] >= 1
    primero = cuerpo["hits"][0]
    assert primero["span"]["citation_label"] == "Tema 1: plazos, pág. 3"
    assert primero["span"]["page"] == 3
    assert primero["span"]["document_title"] == "Temario TAI"
    assert "answer" not in cuerpo, "una búsqueda no genera respuesta"
    # Sin proveedor de embeddings, la degradación se declara.
    assert cuerpo["strategy"] == "lexical"
    assert any("solo léxica" in aviso for aviso in cuerpo["degradations"])
    # Y lo no publicado se queda fuera, diciendo por qué.
    assert all(hit["span"]["version_status"] == "accepted" for hit in cuerpo["hits"])
    assert cuerpo["excluded"], "se dice qué se ha quedado fuera"


def test_preguntar_devuelve_una_respuesta_con_citas_abribles(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    _corpus(seeded_settings)

    respuesta = seeded_client.post(
        "/api/v1/rag/queries",
        json={"query": "plazo de alegaciones", "style": "teach"},
        headers=ALLOWED_ORIGIN,
    )

    assert respuesta.status_code == 201, respuesta.text
    consulta = respuesta.json()
    assert consulta["corpus_revision"], "la consulta guarda con qué corpus se respondió"
    assert consulta["answer"]["status"] == "supported"
    assert consulta["answer"]["provider"] == "extractive"
    assert consulta["answer"]["model"] is None
    assert consulta["prompt_template_version"].endswith("teach")
    afirmaciones = consulta["answer"]["claims"]
    assert afirmaciones, "una respuesta respaldada lleva afirmaciones"

    # Cada afirmación trae su evidencia, y esa evidencia se puede abrir por su ruta.
    for afirmacion in afirmaciones:
        assert afirmacion["evidence"], "sin evidencia no hay afirmación"
        for evidencia in afirmacion["evidence"]:
            abierto = seeded_client.get(f"/api/v1/evidence-spans/{evidencia['id']}")
            assert abierto.status_code == 200
            assert abierto.json()["text"] == evidencia["text"]
            assert abierto.json()["document_id"] == evidencia["document_id"]


def test_una_pregunta_fuera_del_corpus_responde_insuficiente(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    _corpus(seeded_settings)

    respuesta = seeded_client.post(
        "/api/v1/rag/queries",
        json={"query": "motor de curvatura para naves espaciales"},
        headers=ALLOWED_ORIGIN,
    )

    assert respuesta.status_code == 201, respuesta.text
    respuesta_json = respuesta.json()["answer"]
    assert respuesta_json["status"] == "insufficient"
    assert respuesta_json["claims"] == []
    assert respuesta_json["uncertainties"], "y se dice qué no se ha encontrado"


def test_la_recuperacion_guardada_ensena_lo_usado_y_lo_descartado(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    _corpus(seeded_settings)
    creada = seeded_client.post(
        "/api/v1/rag/queries", json={"query": "plazo de alegaciones"}, headers=ALLOWED_ORIGIN
    ).json()

    recuperacion = seeded_client.get(f"/api/v1/rag/queries/{creada['id']}/retrieval")

    assert recuperacion.status_code == 200
    cuerpo = recuperacion.json()
    assert cuerpo["corpus_revision"] == creada["corpus_revision"]
    assert cuerpo["hits"], "se guardan todos los fragmentos recuperados"
    assert cuerpo["used_ids"], "y cuáles se usaron"
    assert all("used" in hit for hit in cuerpo["hits"])

    # Y la consulta se puede releer con su respuesta.
    leida = seeded_client.get(f"/api/v1/rag/queries/{creada['id']}").json()
    assert leida["question"] == "plazo de alegaciones"
    assert leida["answer"]["id"] == creada["answer"]["id"]
    assert seeded_client.get("/api/v1/rag/queries/no-existe").status_code == 404


def test_el_material_privado_se_puede_dejar_fuera(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """`allow_private_sources=false` excluye el material privado, que aquí es todo."""
    _corpus(seeded_settings)

    respuesta = seeded_client.post(
        "/api/v1/rag/queries",
        json={"query": "plazo de alegaciones", "allow_private_sources": False},
        headers=ALLOWED_ORIGIN,
    )

    assert respuesta.status_code == 201
    assert respuesta.json()["answer"]["status"] == "insufficient", (
        "sin material privado no queda nada que citar, y se dice"
    )
