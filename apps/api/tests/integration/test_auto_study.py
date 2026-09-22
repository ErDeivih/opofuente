"""Lo que la aplicación hace **sola** al aceptar una versión de documento (S12.5, ADR-017).

Se prueba el recorrido completo por la API, porque lo que importa es que ocurra sin que nadie lo
pida: el material entra, la clasificación dice qué es y la versión se acepta; después, las preguntas
tienen que estar ya en el banco con su cita, y el aviso tiene que decir qué ha pasado.

Lo que se defiende, y lo que se defiende **en contra**:

- un material clasificado como banco de preguntas importa sus preguntas solo;
- un temario o unos apuntes **no** crean ningún conjunto (no hay nada que importar);
- sin asignación a una oposición no se inventa de quién son las preguntas;
- volver a aceptar no duplica nada;
- un documento que decía traer preguntas y no trae ninguna no deja un conjunto vacío en la lista.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy import text

from opofuente.config import Settings
from opofuente.infrastructure.db import build_engine

ALLOWED_ORIGIN = {"Origin": "http://127.0.0.1:4173"}
AHORA = datetime(2026, 9, 22, 18, 0, tzinfo=UTC)

#: Un cuestionario de tres preguntas con su clave, como el que entra de un documento real.
TEXTO_PREGUNTAS = (
    "1. El plazo de alegaciones del procedimiento es de:\n"
    "a) Diez dias habiles\n"
    "b) Veinte dias habiles\n"
    "c) Un mes\n"
    "Respuesta correcta: a\n"
    "2. El silencio administrativo se regula en:\n"
    "a) La Ley 39/2015\n"
    "b) La Ley 40/2015\n"
    "Respuesta correcta: a\n"
)

#: Un temario: prosa, sin preguntas. De aquí no se importa nada.
TEXTO_TEMARIO = (
    "Tema 1. El procedimiento administrativo comun se regula en la Ley 39/2015, de 1 de octubre, "
    "que establece los plazos y la forma de las notificaciones.\n"
)


def _version(
    settings: Settings,
    *,
    texto: str,
    version_id: str = "ver-1",
    artifact_id: str = "art-1",
    sha: str | None = None,
) -> str:
    """Una versión aceptada con su fragmento, y el artefacto del que sale.

    Se inserta por SQL porque lo que se prueba aquí es la importación automática, no la extracción.
    """
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.begin() as conexion:
            conexion.execute(
                text(
                    "INSERT INTO source_artifacts (id, sha256, size_bytes, media_type, "
                    "storage_key, first_seen_at) VALUES (:art, :sha, 100, 'text/plain', 'k', "
                    ":ahora)"
                ),
                {
                    "art": artifact_id,
                    # Un sha distinto por artefacto: la columna es única y dos artefactos no pueden
                    # compartir contenido.
                    "sha": sha or artifact_id.encode().hex().ljust(64, "0")[:64],
                    "ahora": AHORA.isoformat(),
                },
            )
            conexion.execute(
                text(
                    "INSERT INTO extracted_representations (id, artifact_id, extractor_name, "
                    "extractor_version, kind, status, quality, char_count, created_at) VALUES "
                    "(:rep, :art, 'text', '1', 'plain_text', 'extracted', 'good', 100, :ahora)"
                ),
                {"rep": f"rep-{version_id}", "art": artifact_id, "ahora": AHORA.isoformat()},
            )
            conexion.execute(
                text(
                    "INSERT INTO logical_documents (id, canonical_title, document_type, "
                    "authority_tier, owner_scope, created_at, updated_at) VALUES "
                    "(:doc, 'Cuestionario sintetico', 'private_question_bank', 'C', "
                    "'private_user', :ahora, :ahora)"
                ),
                {"doc": f"doc-{version_id}", "ahora": AHORA.isoformat()},
            )
            conexion.execute(
                text(
                    "INSERT INTO document_versions (id, logical_document_id, artifact_id, "
                    "representation_id, status, created_at) VALUES (:version, :doc, :art, :rep, "
                    "'candidate', :ahora)"
                ),
                {
                    "version": version_id,
                    "doc": f"doc-{version_id}",
                    "art": artifact_id,
                    "rep": f"rep-{version_id}",
                    "ahora": AHORA.isoformat(),
                },
            )
            conexion.execute(
                text(
                    "INSERT INTO document_sections (id, document_version_id, section_type, label, "
                    "title, position, char_start, char_end, ordinal) VALUES (:seccion, :version, "
                    "'chapter', 'Cuestionario', 'Cuestionario', 1, 0, 0, 1)"
                ),
                {"seccion": f"sec-{version_id}", "version": version_id},
            )
            conexion.execute(
                text(
                    "INSERT INTO evidence_spans (id, document_version_id, section_id, ordinal, "
                    "citation_label, quality, index_status, text, normalized_text, created_at) "
                    "VALUES (:span, :version, :seccion, 1, 'pág. 1', 'good', 'indexed', :texto, "
                    ":normalizado, :ahora)"
                ),
                {
                    "span": f"span-{version_id}",
                    "version": version_id,
                    "seccion": f"sec-{version_id}",
                    "texto": texto,
                    "normalizado": texto.lower(),
                    "ahora": AHORA.isoformat(),
                },
            )
    finally:
        engine.dispose()
    return version_id


def _clasificar(
    settings: Settings, *, artifact_id: str, valor: str, status: str = "auto_applied_provisional"
) -> None:
    """Una propuesta de tipo documental, aplicada como la deja el motor determinista.

    Las propuestas decididas exigen `decided_at` (lo impone la base): una decisión sin fecha no es
    una decisión, y sin decisión no hay nada que deshacer.
    """
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.begin() as conexion:
            conexion.execute(
                text(
                    "INSERT INTO classification_proposals (id, subject_type, subject_id, axis, "
                    "proposed_value, confidence, engine_name, engine_version, status, created_at, "
                    "decided_at, decision_note) VALUES (:id, 'artifact', :art, 'document_type', "
                    ":valor, 0.8, 'determinista', '1', :status, :ahora, :decidido, 'motor')"
                ),
                {
                    "id": f"prop-{artifact_id}",
                    "art": artifact_id,
                    "valor": valor,
                    "status": status,
                    "ahora": AHORA.isoformat(),
                    "decidido": None if status == "pending" else AHORA.isoformat(),
                },
            )
    finally:
        engine.dispose()


def _asignar(settings: Settings, *, version_id: str, node_path: str) -> None:
    """Asigna la versión al programa de la oposición activa, como haría una persona al revisar."""
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


def _aceptar(client: TestClient, *, document_id: str, version_id: str) -> dict[str, Any]:
    respuesta = client.post(
        f"/api/v1/documents/{document_id}/versions/{version_id}/accept",
        headers=ALLOWED_ORIGIN,
    )
    assert respuesta.status_code == 200, respuesta.text
    return dict(respuesta.json())


def test_un_banco_de_preguntas_aceptado_importa_sus_preguntas_solo(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """El propietario acepta la versión y las preguntas ya están en el banco, con su cita.

    Sin esto, el camino era: aceptar, ir al banco, crear un conjunto, elegir «importar de un
    documento», elegir el documento e importar. Cuatro pasos que nadie quiere dar.
    """
    version = _version(seeded_settings, texto=TEXTO_PREGUNTAS)
    _clasificar(seeded_settings, artifact_id="art-1", valor="private_question_bank")
    _asignar(seeded_settings, version_id=version, node_path="I.1")

    resultado = _aceptar(seeded_client, document_id="doc-ver-1", version_id=version)

    assert resultado["applied"] is True
    assert resultado["questions_imported"] == 2
    assert resultado["question_set_id"] is not None
    assert "importadas 2 preguntas" in str(resultado["questions_note"])

    conjunto = seeded_client.get(f"/api/v1/question-sets/{resultado['question_set_id']}").json()
    assert conjunto["question_count"] == 2
    assert conjunto["source_document_version_id"] == version
    assert conjunto["set_type"] == "private_bank"

    # Y cada pregunta sabe de qué fragmento salió: la cita no se pierde por ser automático.
    preguntas = seeded_client.get(
        f"/api/v1/question-sets/{conjunto['id']}/questions?limit=10"
    ).json()["questions"]
    primera = preguntas[0]
    assert primera["source_section_id"] == "sec-ver-1"
    evidencia = seeded_client.get(f"/api/v1/questions/{primera['id']}/evidence").json()
    assert evidencia[0]["span_id"] == "span-ver-1"
    assert evidencia[0]["status"] == "accepted"


def test_las_preguntas_importadas_quedan_catalogadas_por_bloque_y_tema(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """S12.6: el tema se **hereda** del documento, no se adivina.

    Si el documento está asignado al programa —«esto son apuntes del tema 3»—, sus preguntas son del
    tema 3. El diagnóstico por temas cuenta con ese mapeo, así que inventarlo sería peor que no
    tenerlo.
    """
    version = _version(seeded_settings, texto=TEXTO_PREGUNTAS)
    _clasificar(seeded_settings, artifact_id="art-1", valor="private_question_bank")
    _asignar(seeded_settings, version_id=version, node_path="I.1")

    resultado = _aceptar(seeded_client, document_id="doc-ver-1", version_id=version)

    assert resultado["questions_imported"] == 2
    assert resultado["questions_catalogued"] == 2

    # Se comprueba por la API: cada pregunta tiene su nodo del programa.
    preguntas = seeded_client.get(
        f"/api/v1/question-sets/{resultado['question_set_id']}/questions?limit=10"
    ).json()["questions"]
    for pregunta in preguntas:
        mapeos = seeded_client.get(
            f"/api/v1/mappings?subject_type=question_version&subject_id={pregunta['id']}"
        ).json()
        assert len(mapeos) == 1, pregunta["id"]
        assert mapeos[0]["node_path"] == "I.1"
        assert mapeos[0]["status"] == "accepted"


def test_una_asignacion_sin_aceptar_no_cataloga_ni_crea_conjunto(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """Una asignación **provisional** es una sugerencia, no una decisión: no se usa para nada."""
    version = _version(seeded_settings, texto=TEXTO_PREGUNTAS)
    _clasificar(seeded_settings, artifact_id="art-1", valor="private_question_bank")
    engine = build_engine(seeded_settings.data_paths.database)
    try:
        with engine.begin() as conexion:
            nodo = conexion.execute(
                text("SELECT id FROM curriculum_nodes WHERE path = 'I.1' LIMIT 1")
            ).scalar_one()
            conexion.execute(
                text(
                    "INSERT INTO curriculum_mappings (id, curriculum_node_id, subject_type, "
                    "subject_id, coverage_type, depth, confidence, status, created_at) VALUES "
                    "('map-provisional', :nodo, 'document_version', :version, 'partial', 1, 0.5, "
                    "'provisional', :ahora)"
                ),
                {"nodo": nodo, "version": version, "ahora": AHORA.isoformat()},
            )
    finally:
        engine.dispose()

    resultado = _aceptar(seeded_client, document_id="doc-ver-1", version_id=version)

    assert resultado["questions_imported"] == 0
    assert resultado["questions_catalogued"] == 0
    assert "no está asignada a ninguna oposición" in str(resultado["questions_note"])


def test_un_temario_no_crea_ningun_conjunto(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """Lo que no trae preguntas no se convierte en banco: se dice por qué y no se crea nada."""
    version = _version(seeded_settings, texto=TEXTO_TEMARIO)
    _clasificar(seeded_settings, artifact_id="art-1", valor="curriculum")
    _asignar(seeded_settings, version_id=version, node_path="I.1")

    resultado = _aceptar(seeded_client, document_id="doc-ver-1", version_id=version)

    assert resultado["questions_imported"] == 0
    assert resultado["question_set_id"] is None
    assert resultado["questions_note"] == "el material está clasificado como «curriculum»"

    conjuntos = seeded_client.get("/api/v1/question-sets?limit=20").json()
    assert conjuntos["sets"] == []


def test_sin_asignacion_a_una_oposicion_no_se_inventa_de_quien_son_las_preguntas(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """Un banco de preguntas que no está asignado a ningún programa no se puede catalogar."""
    version = _version(seeded_settings, texto=TEXTO_PREGUNTAS)
    _clasificar(seeded_settings, artifact_id="art-1", valor="private_question_bank")

    resultado = _aceptar(seeded_client, document_id="doc-ver-1", version_id=version)

    assert resultado["questions_imported"] == 0
    assert "no está asignada a ninguna oposición" in str(resultado["questions_note"])


def test_sin_clasificar_no_se_supone_que_trae_preguntas(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    version = _version(seeded_settings, texto=TEXTO_PREGUNTAS)
    _asignar(seeded_settings, version_id=version, node_path="I.1")

    resultado = _aceptar(seeded_client, document_id="doc-ver-1", version_id=version)

    assert resultado["questions_imported"] == 0
    assert "no está clasificado" in str(resultado["questions_note"])


def test_una_version_nueva_del_mismo_banco_anade_sus_preguntas_al_mismo_conjunto(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """Un documento es un conjunto, no uno por versión: la revisión añade, no multiplica.

    Al aceptar la versión 2 del mismo documento, las preguntas que ya estaban se reconocen por su
    huella y solo entran las nuevas. Si cada versión creara su conjunto, el banco se llenaría de
    copias que dicen casi lo mismo.
    """
    version = _version(seeded_settings, texto=TEXTO_PREGUNTAS)
    _clasificar(seeded_settings, artifact_id="art-1", valor="private_question_bank")
    _asignar(seeded_settings, version_id=version, node_path="I.1")
    primera = _aceptar(seeded_client, document_id="doc-ver-1", version_id=version)
    assert primera["questions_imported"] == 2

    # La versión 2 del **mismo** documento: la primera pregunta igual y una tercera nueva.
    version2 = _version(
        seeded_settings,
        texto=(
            TEXTO_PREGUNTAS
            + "3. La notificacion por medios electronicos se practica en:\n"
            + "a) La sede electronica\n"
            + "b) El domicilio\n"
            + "Respuesta correcta: a\n"
        ),
        version_id="ver-2",
        artifact_id="art-2",
    )
    engine = build_engine(seeded_settings.data_paths.database)
    try:
        with engine.begin() as conexion:
            conexion.execute(
                text(
                    "UPDATE document_versions SET logical_document_id = 'doc-ver-1' "
                    "WHERE id = 'ver-2'"
                )
            )
    finally:
        engine.dispose()
    # La versión nueva es otro artefacto, así que su material se clasifica por su cuenta.
    _clasificar(seeded_settings, artifact_id="art-2", valor="private_question_bank")
    _asignar(seeded_settings, version_id=version2, node_path="I.1")

    segunda = _aceptar(seeded_client, document_id="doc-ver-1", version_id=version2)

    detalle = seeded_client.get(f"/api/v1/question-sets/{primera['question_set_id']}").json()
    assert segunda["questions_imported"] == 1, (
        segunda["questions_note"],
        detalle["question_count"],
    )
    assert segunda["question_set_id"] == primera["question_set_id"], "el mismo conjunto"
    assert segunda["questions_note"] == "se añadieron las preguntas que traía la versión nueva"
    conjuntos = seeded_client.get("/api/v1/question-sets?limit=20").json()
    assert conjuntos["total"] == 1
    assert (
        seeded_client.get(f"/api/v1/question-sets/{primera['question_set_id']}").json()[
            "question_count"
        ]
        == 3
    )


def test_un_banco_sin_preguntas_reconocibles_no_deja_un_conjunto_vacio(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """Decía traer preguntas y no se reconoció ninguna: se archiva el conjunto, no se deja vacío."""
    version = _version(seeded_settings, texto="Un texto que no tiene ninguna pregunta.\n")
    _clasificar(seeded_settings, artifact_id="art-1", valor="private_question_bank")
    _asignar(seeded_settings, version_id=version, node_path="I.1")

    resultado = _aceptar(seeded_client, document_id="doc-ver-1", version_id=version)

    assert resultado["questions_imported"] == 0
    assert resultado["questions_note"] == "el material no traía preguntas reconocibles"
    # El conjunto no aparece en la lista (está archivado), pero sigue existiendo y no se ha borrado.
    assert seeded_client.get("/api/v1/question-sets?limit=20").json()["total"] == 0
    assert (
        seeded_client.get("/api/v1/question-sets?limit=20&include_archived=true").json()["total"]
        == 1
    )
