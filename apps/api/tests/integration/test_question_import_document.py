"""Importar preguntas **desde una versión de documento**, con su cita (DEBT-010).

Lo que se comprueba aquí es el enlace que no existía: una pregunta que sale de un documento de la
biblioteca tiene que poder decir de qué **fragmento** y de qué **sección** salió, y la ficha tiene
que poder abrir el original en esa página. El material es sintético y se escribe en la base como lo
deja la extracción: una sección con páginas y fragmentos de texto, en su orden.

Y una cosa que se comprueba **en contra**: que no se invente la cita. Una versión sin fragmentos no
produce evidencias vacías; produce un informe que dice que no se reconoció ninguna pregunta.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy import text

from opofuente.config import Settings
from opofuente.infrastructure.db import build_engine

ALLOWED_ORIGIN = {"Origin": "http://127.0.0.1:4173"}
AHORA = datetime(2026, 9, 20, 10, 0, tzinfo=UTC)

#: Dos preguntas numeradas dentro de una cabecera de parte, como llegan en un examen real. El rótulo
#: «PARTE 2» no es texto suelto: el parser lo reconoce como cabecera y lo declara en el informe.
TEXTO_PARTE_2 = (
    "PARTE 2\n"
    "1. El plazo de alegaciones del procedimiento es de:\n"
    "a) Diez dias habiles\n"
    "b) Veinte dias habiles\n"
    "c) Un mes\n"
    "2. El silencio administrativo se regula en:\n"
    "a) La Ley 39/2015\n"
    "b) La Ley 40/2015\n"
    "c) Ninguna de las anteriores\n"
)

TEXTO_PARTE_1 = "1. La Constitucion Espanola se aprobo en:\na) 1978\nb) 1979\nc) 1980\n"

#: Cuestionario escrito en Markdown, como lo guarda quien estudia con Obsidian: encabezado, viñetas
#: y la clave en negrita. Sin quitar el adorno, el importador leía dos preguntas sin opciones y sin
#: clave («orphan option»).
TEXTO_MARKDOWN = (
    "## Tema 5. Los plazos\n"
    "**1.** El plazo del procedimiento es de:\n"
    "- a) diez dias habiles\n"
    "- b) veinte dias habiles\n"
    "**Respuesta correcta: a**\n"
    "\n"
    "3. El silencio administrativo se regula en:\n"
    "a) la Ley 39/2015\n"
    "b) la Ley 40/2015\n"
    "Respuesta correcta: a\n"
)


def _version_con_fragmentos(
    settings: Settings,
    *,
    secciones: list[tuple[str, int, list[str]]],
    version_id: str = "ver-1",
) -> str:
    """Una versión con sus secciones y sus fragmentos, tal como los deja la extracción.

    `secciones` es una lista de (título, página, [texto de cada fragmento]). Se inserta por SQL
    porque lo que se prueba aquí es el importador, no el extractor: dar de alta la extracción entera
    haría que la prueba midiera otra cosa.
    """
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.begin() as conexion:
            conexion.execute(
                text(
                    "INSERT INTO source_artifacts (id, sha256, size_bytes, media_type, "
                    "storage_key, first_seen_at) VALUES ('art-1', :sha, 100, 'text/plain', 'k', "
                    ":ahora)"
                ),
                {"sha": "a" * 64, "ahora": AHORA.isoformat()},
            )
            conexion.execute(
                text(
                    "INSERT INTO extracted_representations (id, artifact_id, extractor_name, "
                    "extractor_version, kind, status, quality, char_count, created_at) VALUES "
                    "('rep-1', 'art-1', 'text', '1', 'plain_text', 'extracted', 'good', 100, "
                    ":ahora)"
                ),
                {"ahora": AHORA.isoformat()},
            )
            conexion.execute(
                text(
                    "INSERT INTO logical_documents (id, canonical_title, document_type, "
                    "authority_tier, owner_scope, created_at, updated_at) VALUES "
                    "('doc-1', 'Temario sintetico', 'curriculum', 'A', 'private_user', :ahora, "
                    ":ahora)"
                ),
                {"ahora": AHORA.isoformat()},
            )
            conexion.execute(
                text(
                    "INSERT INTO document_versions (id, logical_document_id, artifact_id, "
                    "representation_id, status, approved_at, created_at) VALUES "
                    "(:version, 'doc-1', 'art-1', 'rep-1', 'accepted', :ahora, :ahora)"
                ),
                {"version": version_id, "ahora": AHORA.isoformat()},
            )
            ordinal = 0
            for indice, (titulo, pagina, fragmentos) in enumerate(secciones, start=1):
                seccion_id = f"sec-{indice}"
                conexion.execute(
                    text(
                        "INSERT INTO document_sections (id, document_version_id, section_type, "
                        "label, title, position, page_start, page_end, char_start, char_end, "
                        "ordinal) VALUES (:id, :version, 'chapter', :titulo, :titulo, :pos, "
                        ":pagina, :pagina, 0, 0, :ordinal)"
                    ),
                    {
                        "id": seccion_id,
                        "version": version_id,
                        "titulo": titulo,
                        "pos": indice,
                        "pagina": pagina,
                        "ordinal": indice,
                    },
                )
                for texto_fragmento in fragmentos:
                    ordinal += 1
                    conexion.execute(
                        text(
                            "INSERT INTO evidence_spans (id, document_version_id, section_id, "
                            "ordinal, page, citation_label, quality, index_status, text, "
                            "normalized_text, created_at) VALUES (:id, :version, :seccion, "
                            ":ordinal, :pagina, :etiqueta, 'good', 'indexed', :texto, "
                            ":normalizado, :ahora)"
                        ),
                        {
                            "id": f"span-{ordinal}",
                            "version": version_id,
                            "seccion": seccion_id,
                            "ordinal": ordinal,
                            "pagina": pagina,
                            "etiqueta": f"pág. {pagina}",
                            "texto": texto_fragmento,
                            "normalizado": texto_fragmento.lower(),
                            "ahora": AHORA.isoformat(),
                        },
                    )
    finally:
        engine.dispose()
    return version_id


def _asignar_version_al_programa(settings: Settings, *, version_id: str, node_path: str) -> None:
    """Asigna la versión a un nodo del programa, aceptado, como lo deja la revisión."""
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.begin() as conexion:
            nodo = conexion.execute(
                text("SELECT id FROM curriculum_nodes WHERE path = :path LIMIT 1"),
                {"path": node_path},
            ).scalar_one()
            conexion.execute(
                text(
                    "INSERT INTO curriculum_mappings (id, curriculum_node_id, subject_type, "
                    "subject_id, coverage_type, depth, confidence, status, created_at, "
                    "approved_at) VALUES (:id, :nodo, 'document_version', :version, 'partial', 1, "
                    "0.9, 'accepted', :ahora, :ahora)"
                ),
                {
                    "id": f"map-{version_id}",
                    "nodo": nodo,
                    "version": version_id,
                    "ahora": AHORA.isoformat(),
                },
            )
    finally:
        engine.dispose()


def _conjunto(client: TestClient) -> str:
    oposiciones = client.get("/api/v1/oppositions").json()
    activa = next(oposicion for oposicion in oposiciones if oposicion["active"])
    creado = client.post(
        "/api/v1/question-sets",
        json={
            "title": "Examen importado de un documento",
            "opposition_id": activa["id"],
            "set_type": "official_exam",
            "convocation_version_id": activa["active_convocation"]["id"],
        },
        headers=ALLOWED_ORIGIN,
    )
    assert creado.status_code == 201, creado.text
    return str(creado.json()["id"])


def _preguntas(client: TestClient, set_id: str) -> list[dict[str, Any]]:
    respuesta = client.get(f"/api/v1/question-sets/{set_id}/questions?limit=50")
    assert respuesta.status_code == 200, respuesta.text
    return list(respuesta.json()["questions"])


def test_importar_desde_un_documento_enlaza_cada_pregunta_con_su_fragmento(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """DEBT-010, criterios 1 y 3: la cita con su fragmento, su página y su etiqueta; y la parte."""
    version = _version_con_fragmentos(
        seeded_settings,
        secciones=[
            ("Tema 1", 1, [TEXTO_PARTE_1]),
            ("Tema 2", 4, [TEXTO_PARTE_2]),
        ],
    )
    set_id = _conjunto(seeded_client)

    respuesta = seeded_client.post(
        f"/api/v1/question-sets/{set_id}/import-document",
        json={"document_version_id": version},
        headers=ALLOWED_ORIGIN,
    )

    assert respuesta.status_code == 200, respuesta.text
    informe = respuesta.json()
    assert informe["created"] == 3, "las tres preguntas del documento"
    assert informe["existing"] == 0
    assert informe["evidence_links"] == 3, "cada pregunta con su cita"
    # El rótulo de parte que trae el material se declara: no se pierde en silencio (criterio 3).
    assert informe["parts_detected"] == ["2"]
    assert informe["issues"] == []

    preguntas = _preguntas(seeded_client, set_id)
    assert len(preguntas) == 3
    # La sección de origen se guarda en la pregunta: es de donde salió, no una suposición.
    por_enunciado = {pregunta["stem"]: pregunta for pregunta in preguntas}
    primera = por_enunciado["La Constitucion Espanola se aprobo en:"]
    segunda = por_enunciado["El plazo de alegaciones del procedimiento es de:"]
    assert primera["source_section_id"] == "sec-1"
    assert segunda["source_section_id"] == "sec-2"

    # Y la evidencia: una cita aceptada, con su fragmento, su página y su etiqueta.
    evidencia = seeded_client.get(f"/api/v1/questions/{segunda['id']}/evidence")
    assert evidencia.status_code == 200, evidencia.text
    citas = evidencia.json()
    assert len(citas) == 1
    cita = citas[0]
    assert cita["role"] == "stem"
    assert cita["status"] == "accepted"
    assert cita["span_id"] == "span-2"
    assert cita["page"] == 4
    assert cita["citation_label"] == "pág. 4"
    assert cita["section_id"] == "sec-2"
    assert cita["document_version_id"] == version
    assert "El plazo de alegaciones" in cita["text"]

    # La primera pregunta apunta a la primera sección, con su propia página: no se cruzan.
    primera_evidencia = seeded_client.get(f"/api/v1/questions/{primera['id']}/evidence").json()
    assert [cita["span_id"] for cita in primera_evidencia] == ["span-1"]
    assert primera_evidencia[0]["page"] == 1


def test_importar_dos_veces_el_mismo_documento_no_duplica_ni_la_pregunta_ni_la_cita(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """Volver a importar no duplica: las preguntas ya estaban y la cita ya estaba enlazada."""
    version = _version_con_fragmentos(seeded_settings, secciones=[("Tema 1", 1, [TEXTO_PARTE_1])])
    set_id = _conjunto(seeded_client)
    ruta = f"/api/v1/question-sets/{set_id}/import-document"

    primera = seeded_client.post(
        ruta, json={"document_version_id": version}, headers=ALLOWED_ORIGIN
    )
    assert primera.status_code == 200, primera.text
    assert primera.json()["created"] == 1
    assert primera.json()["evidence_links"] == 1

    segunda = seeded_client.post(
        ruta, json={"document_version_id": version}, headers=ALLOWED_ORIGIN
    )

    assert segunda.status_code == 200, segunda.text
    assert segunda.json()["created"] == 0
    assert segunda.json()["existing"] == 1
    assert segunda.json()["evidence_links"] == 0, "la cita ya estaba: no se cuenta dos veces"
    assert len(_preguntas(seeded_client, set_id)) == 1
    pregunta_id = _preguntas(seeded_client, set_id)[0]["id"]
    assert len(seeded_client.get(f"/api/v1/questions/{pregunta_id}/evidence").json()) == 1


def test_una_version_sin_fragmentos_no_inventa_citas(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """Sin texto extraído no hay de dónde citar: se dice, no se crea una evidencia vacía."""
    version = _version_con_fragmentos(seeded_settings, secciones=[])
    set_id = _conjunto(seeded_client)

    respuesta = seeded_client.post(
        f"/api/v1/question-sets/{set_id}/import-document",
        json={"document_version_id": version},
        headers=ALLOWED_ORIGIN,
    )

    assert respuesta.status_code == 200, respuesta.text
    assert respuesta.json()["created"] == 0
    assert respuesta.json()["evidence_links"] == 0
    assert [aviso["code"] for aviso in respuesta.json()["issues"]] == ["no_questions"]
    assert _preguntas(seeded_client, set_id) == []


def test_importar_de_una_version_que_no_existe_es_un_404(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    set_id = _conjunto(seeded_client)

    respuesta = seeded_client.post(
        f"/api/v1/question-sets/{set_id}/import-document",
        json={"document_version_id": "ver-que-no-existe"},
        headers=ALLOWED_ORIGIN,
    )

    assert respuesta.status_code == 404, respuesta.text
    assert respuesta.json()["code"] == "not_found"


def test_importar_un_cuestionario_en_markdown_lee_preguntas_opciones_y_clave(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """Un cuestionario en Markdown entra completo: enunciado, opciones y clave, con su cita.

    El adorno de Markdown (`##`, `- `, `**`) no es contenido. Antes de S12.3, la clave en negrita no
    se leía y las opciones con viñeta se quedaban huérfanas: el informe lo declaraba, pero el
    cuestionario entraba a medias.
    """
    version = _version_con_fragmentos(seeded_settings, secciones=[("Tema 5", 7, [TEXTO_MARKDOWN])])
    set_id = _conjunto(seeded_client)

    respuesta = seeded_client.post(
        f"/api/v1/question-sets/{set_id}/import-document",
        json={"document_version_id": version},
        headers=ALLOWED_ORIGIN,
    )

    assert respuesta.status_code == 200, respuesta.text
    informe = respuesta.json()
    assert informe["created"] == 2
    assert informe["evidence_links"] == 2
    # Las dos preguntas entran **con su clave**: sin leer `**Respuesta correcta: a**`
    # como preguntas incompletas (sin opción correcta).
    assert informe["with_key"] == 2
    assert informe["incomplete"] == 0
    assert informe["issues"] == []

    preguntas = _preguntas(seeded_client, set_id)
    por_enunciado = {pregunta["stem"]: pregunta for pregunta in preguntas}
    primera = por_enunciado["El plazo del procedimiento es de:"]
    assert primera["source_section_id"] == "sec-1"
    assert primera["question_type"] == "single_choice"
    assert primera["status"] == "complete"
    detalle = seeded_client.get(f"/api/v1/questions/{primera['id']}").json()
    assert [opcion["text"] for opcion in detalle["options"]] == [
        "diez dias habiles",
        "veinte dias habiles",
    ]
    # La respuesta correcta no viaja en la ficha de la pregunta: eso lo dice la clave.
    assert "is_correct" not in detalle["options"][0]


def test_importar_a_mano_tambien_cataloga_por_bloque_y_tema(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """La catalogación no depende de que la importación la haga la aplicación sola (S12.6).

    Si el documento está asignado al programa, sus preguntas heredan el tema también cuando la
    importación la pide una persona. Si no, las preguntas importadas a mano se quedarían fuera del
    diagnóstico por temas, que es lo que agrupa lo contestado por bloque y tema.
    """
    version = _version_con_fragmentos(seeded_settings, secciones=[("Tema 1", 1, [TEXTO_PARTE_1])])
    _asignar_version_al_programa(seeded_settings, version_id=version, node_path="I.1")
    set_id = _conjunto(seeded_client)

    respuesta = seeded_client.post(
        f"/api/v1/question-sets/{set_id}/import-document",
        json={"document_version_id": version},
        headers=ALLOWED_ORIGIN,
    )

    assert respuesta.status_code == 200, respuesta.text
    informe = respuesta.json()
    assert informe["created"] == 1
    assert informe["mapped_to_topics"] == 1

    pregunta_id = _preguntas(seeded_client, set_id)[0]["id"]
    mapeos = seeded_client.get(
        f"/api/v1/mappings?subject_type=question_version&subject_id={pregunta_id}"
    ).json()
    assert [mapeo["node_path"] for mapeo in mapeos] == ["I.1"]
    assert mapeos[0]["status"] == "accepted"
