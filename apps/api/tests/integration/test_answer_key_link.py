"""Enlazar la plantilla de respuestas con su examen (S12.6, última parte).

Una plantilla es un documento **independiente**: llega aparte del examen y no dice a qué examen
pertenece más que por su contenido. Lo que se prueba aquí es la regla que decide el enlace y, sobre
todo, lo que se hace cuando **no** se puede decidir: enlazar la plantilla de un modelo con el examen
de otro corrige el examen entero con las respuestas equivocadas.

Se recorre por la API real: el examen entra como material, se clasifica, se acepta (y sus preguntas
van al banco), y después llega la plantilla, que también se acepta. Lo que la aplicación hace con
ella se lee en el aviso del documento y en el banco.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy import text

from opofuente.config import Settings
from opofuente.domain.extraction import (
    ExtractionResult,
    ExtractorRef,
    Quality,
    RepresentationKind,
    RepresentationStatus,
)
from opofuente.infrastructure.db import build_engine, build_session_factory
from opofuente.infrastructure.extraction_repository import SqlAlchemyExtractionRepository
from opofuente.infrastructure.representation_store import RepresentationStore

ALLOWED_ORIGIN = {"Origin": "http://127.0.0.1:5173"}
AHORA = datetime(2026, 9, 22, 20, 0, tzinfo=UTC)

#: Un examen de cuatro preguntas **sin las respuestas**: un examen oficial no las trae, la plantilla
#: se publica aparte. Es justo el caso que hay que enlazar.
EXAMEN = (
    "1. El plazo del procedimiento del caso A es de diez dias habiles:\n"
    "a) Verdadero\n"
    "b) Falso\n"
    "2. El plazo del procedimiento del caso B es de veinte dias habiles:\n"
    "a) Verdadero\n"
    "b) Falso\n"
    "3. El plazo del procedimiento del caso C es de treinta dias habiles:\n"
    "a) Verdadero\n"
    "b) Falso\n"
    "4. El plazo del procedimiento del caso D es de cuarenta dias habiles:\n"
    "a) Verdadero\n"
    "b) Falso\n"
)

#: La plantilla suelta del mismo examen: cuatro respuestas y ninguna pregunta.
PLANTILLA = "1. a\n2. a\n3. a\n4. a\n"


def _version(
    settings: Settings,
    *,
    texto: str,
    version_id: str,
    document_type: str,
    titulo: str,
) -> str:
    """Una versión con su texto, su papel documental y su artefacto, como la deja la extracción.

    Dos cosas se preparan de verdad, porque las dos hacen falta según el camino:

    - el texto de la **representación** (`RepresentationStore` y el repositorio de extracción),
      que es de donde lee la plantilla suelta (`version_text`);
    - una **sección** y su **fragmento** con el texto entero, que es de donde lee el importador de
      preguntas de un documento: sin fragmento no hay cita, y sin cita no entra ninguna pregunta
      (DEBT-010).

    El artefacto, el documento, la versión y su clasificación van por SQL porque lo que se prueba
    es el enlace automático, no la extracción.
    """
    engine = build_engine(settings.data_paths.database)
    sesiones = build_session_factory(engine)
    try:
        with engine.begin() as conexion:
            conexion.execute(
                text(
                    "INSERT INTO source_artifacts (id, sha256, size_bytes, media_type, "
                    "storage_key, first_seen_at) VALUES (:art, :sha, 100, 'text/plain', 'k', "
                    ":ahora)"
                ),
                {
                    "art": f"art-{version_id}",
                    "sha": version_id.encode().hex().ljust(64, "0")[:64],
                    "ahora": AHORA.isoformat(),
                },
            )
        resultado = ExtractionResult(
            kind=RepresentationKind.NATIVE_TEXT,
            status=RepresentationStatus.EXTRACTED,
            text=texto,
            extractor=ExtractorRef("extractor-de-prueba", "1"),
            quality=Quality.GOOD,
            sections=(),
        )
        clave = RepresentationStore(settings.data_paths).save(f"rep-{version_id}", resultado)
        SqlAlchemyExtractionRepository(sesiones).save(
            result=resultado,
            artifact_id=f"art-{version_id}",
            representation_id=f"rep-{version_id}",
            text_storage_key=clave,
            now=AHORA,
        )
        with engine.begin() as conexion:
            conexion.execute(
                text(
                    "INSERT INTO logical_documents (id, canonical_title, document_type, "
                    "authority_tier, owner_scope, created_at, updated_at) VALUES (:doc, :titulo, "
                    ":tipo, 'A', 'public', :ahora, :ahora)"
                ),
                {
                    "doc": f"doc-{version_id}",
                    "titulo": titulo,
                    "tipo": document_type,
                    "ahora": AHORA.isoformat(),
                },
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
                    "art": f"art-{version_id}",
                    "rep": f"rep-{version_id}",
                    "ahora": AHORA.isoformat(),
                },
            )
            # La sección y su fragmento: de aquí sale la cita de cada pregunta importada.
            conexion.execute(
                text(
                    "INSERT INTO document_sections (id, document_version_id, section_type, label, "
                    "title, position, char_start, char_end, ordinal) VALUES (:id, :version, "
                    "'chapter', 'Documento', 'Documento', 1, 0, :largo, 1)"
                ),
                {
                    "id": f"sec-{version_id}",
                    "version": version_id,
                    "largo": len(texto),
                },
            )
            conexion.execute(
                text(
                    "INSERT INTO evidence_spans (id, document_version_id, section_id, ordinal, "
                    "citation_label, quality, index_status, text, normalized_text, created_at) "
                    "VALUES (:id, :version, :seccion, 1, 'pág. 1', 'good', 'indexed', :texto, "
                    ":normalizado, :ahora)"
                ),
                {
                    "id": f"span-{version_id}",
                    "version": version_id,
                    "seccion": f"sec-{version_id}",
                    "texto": texto,
                    "normalizado": texto.lower(),
                    "ahora": AHORA.isoformat(),
                },
            )
            conexion.execute(
                text(
                    "INSERT INTO classification_proposals (id, subject_type, subject_id, axis, "
                    "proposed_value, confidence, engine_name, engine_version, status, created_at, "
                    "decided_at, decision_note) VALUES (:id, 'artifact', :art, 'document_type', "
                    ":tipo, 0.9, 'determinista', '1', 'auto_applied_provisional', :ahora, :ahora, "
                    "'motor')"
                ),
                {
                    "id": f"prop-{version_id}",
                    "art": f"art-{version_id}",
                    "tipo": document_type,
                    "ahora": AHORA.isoformat(),
                },
            )
    finally:
        engine.dispose()
    return version_id


def _asignar(settings: Settings, *, version_id: str, node_path: str) -> None:
    """Asigna la versión al programa, como hace una persona al revisar."""
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
                    "approved_at) VALUES (:id, :nodo, 'document_version', :version, 'complete', 1, "
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


def _aceptar(client: TestClient, *, version_id: str) -> dict[str, Any]:
    respuesta = client.post(
        f"/api/v1/documents/doc-{version_id}/versions/{version_id}/accept",
        headers=ALLOWED_ORIGIN,
    )
    assert respuesta.status_code == 200, respuesta.text
    return dict(respuesta.json())


def _preparar_examen(
    settings: Settings, seeded_client: TestClient, *, version_id: str = "examen"
) -> dict[str, Any]:
    """Deja un examen oficial aceptado, con sus preguntas en el banco y **sin clave**.

    Un examen oficial no trae las respuestas: llegan en su plantilla, que es un documento aparte.
    que el conjunto nace sin ninguna clave, y es el sitio donde tiene que aterrizar la plantilla.
    """
    _version(
        settings,
        texto=EXAMEN,
        version_id=version_id,
        document_type="official_exam",
        titulo="Examen oficial de prueba",
    )
    _asignar(settings, version_id=version_id, node_path="I.1")
    return _aceptar(seeded_client, version_id=version_id)


def _plantilla(
    settings: Settings,
    seeded_client: TestClient,
    *,
    texto: str = PLANTILLA,
    version_id: str = "plantilla",
    titulo: str = "Plantilla de respuestas del examen",
    asignar: bool = True,
) -> dict[str, Any]:
    """Acepta un documento de plantilla, como haría el propietario al soltarlo."""
    _version(
        settings,
        texto=texto,
        version_id=version_id,
        document_type="answer_key",
        titulo=titulo,
    )
    if asignar:
        _asignar(settings, version_id=version_id, node_path="I.1")
    return _aceptar(seeded_client, version_id=version_id)


def _claves(client: TestClient, set_id: str) -> list[dict[str, Any]]:
    respuesta = client.get(f"/api/v1/question-sets/{set_id}/answer-keys")
    assert respuesta.status_code == 200, respuesta.text
    return list(respuesta.json())


def _oposicion_activa(client: TestClient) -> dict[str, Any]:
    return dict(next(op for op in client.get("/api/v1/oppositions").json() if op["active"]))


def test_una_plantilla_suelta_se_enlaza_con_su_examen(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """La plantilla entra sola: se enlaza con el examen y queda esperando que alguien la active."""
    examen = _preparar_examen(seeded_settings, seeded_client)
    assert examen["questions_imported"] == 4
    set_id = str(examen["question_set_id"])
    assert _claves(seeded_client, set_id) == [], "un examen oficial no trae su clave dentro"

    resultado = _plantilla(seeded_settings, seeded_client)

    assert resultado["questions_imported"] == 0, "una plantilla no trae preguntas"
    assert resultado["question_set_id"] == set_id, "se dice con qué examen se enlazó"
    assert "plantilla enlazada" in str(resultado["questions_note"])
    assert "borrador" in str(resultado["questions_note"]), (
        "activar es aprobar (ADR-009): el aviso tiene que decir que eso lo hace una persona"
    )

    claves = _claves(seeded_client, set_id)
    assert len(claves) == 1, "la plantilla enlazada es la primera clave del conjunto"
    enlazada = claves[0]
    assert enlazada["source_document_version_id"] == "plantilla", "queda dicho de dónde salió"
    assert enlazada["status"] == "draft"
    assert len(enlazada["entries"]) == 4
    assert all(entrada["outcome"] == "keyed" for entrada in enlazada["entries"])


def test_una_plantilla_que_no_dice_el_modelo_no_se_enlaza_si_hay_dos_examenes(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """Con dos exámenes que encajan, no se elige por el propietario: se dice y se para.

    Es el caso que hay que proteger: enlazar la plantilla de un modelo con el examen de otro corrige
    el examen entero con las respuestas equivocadas, y eso no se nota hasta que se estudia con ello.
    """
    primero = _preparar_examen(seeded_settings, seeded_client, version_id="examen-a")
    _preparar_examen(seeded_settings, seeded_client, version_id="examen-b")

    resultado = _plantilla(seeded_settings, seeded_client, titulo="Plantilla sin modelo")

    assert "encaja con 2 exámenes" in str(resultado["questions_note"]), resultado["questions_note"]
    # Y no se ha guardado ninguna plantilla en ninguno de los dos.
    assert _claves(seeded_client, str(primero["question_set_id"])) == []


def test_si_la_plantilla_declara_el_modelo_se_enlaza_con_el_del_modelo(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """«Modelo B» en la plantilla desempata: se enlaza con el examen B y con ningún otro.

    Los dos conjuntos van declarados con su modelo, que es lo que hace un examen oficial cuando se
    publica en modelo A y modelo B: sin declararlo no hay forma de saber de quién es la plantilla.
    """
    oposicion = _oposicion_activa(seeded_client)
    convocatoria = oposicion["active_convocation"]["id"]
    for sufijo, modelo in (("examen-a", "A"), ("examen-b", "B")):
        _version(
            seeded_settings,
            texto=EXAMEN,
            version_id=sufijo,
            document_type="official_exam",
            titulo=f"Examen oficial modelo {modelo}",
        )
        creado = seeded_client.post(
            "/api/v1/question-sets",
            json={
                "title": f"Examen oficial modelo {modelo}",
                "opposition_id": oposicion["id"],
                "set_type": "official_exam",
                "convocation_version_id": convocatoria,
                "model_code": modelo,
                "source_document_version_id": sufijo,
            },
            headers=ALLOWED_ORIGIN,
        )
        assert creado.status_code == 201, creado.text
        importado = seeded_client.post(
            f"/api/v1/question-sets/{creado.json()['id']}/import-document",
            json={"document_version_id": sufijo},
            headers=ALLOWED_ORIGIN,
        )
        assert importado.status_code == 200, importado.text
        assert importado.json()["created"] == 4

    resultado = _plantilla(
        seeded_settings,
        seeded_client,
        texto="Modelo B\n" + PLANTILLA,
        titulo="Plantilla del modelo B",
    )

    assert "plantilla enlazada con el examen «Examen oficial modelo B»" in str(
        resultado["questions_note"]
    ), resultado["questions_note"]
    modelo_b = seeded_client.get(
        "/api/v1/question-sets", params={"opposition_id": oposicion["id"]}
    ).json()["sets"]
    enlazado = next(conjunto for conjunto in modelo_b if conjunto["model_code"] == "B")
    assert resultado["question_set_id"] == enlazado["id"]
    assert len(_claves(seeded_client, str(enlazado["id"]))) == 1
    modelo_a = next(conjunto for conjunto in modelo_b if conjunto["model_code"] == "A")
    assert _claves(seeded_client, str(modelo_a["id"])) == [], (
        "la plantilla del modelo B no puede acabar en el examen del modelo A"
    )


def test_una_plantilla_que_no_encaja_con_nada_lo_dice_con_su_motivo(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """Una plantilla que no es de este examen no se enlaza, y el aviso dice por qué."""
    examen = _preparar_examen(seeded_settings, seeded_client)
    # Una plantilla de un examen de otro tamaño: sus números no caen en las preguntas de este.
    resultado = _plantilla(
        seeded_settings,
        seeded_client,
        texto="1. a\n2. b\n3. c\n4. a\n5. b\n6. c\n",
        titulo="Plantilla de otro examen",
    )

    assert "no encaja con ningún examen" in str(resultado["questions_note"]), resultado[
        "questions_note"
    ]
    assert "%" in str(resultado["questions_note"]), "el aviso dice cuánto se parece"
    assert _claves(seeded_client, str(examen["question_set_id"])) == []


def test_una_plantilla_sin_asignar_no_se_enlaza_con_nada(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """Sin asignación al programa no se sabe de qué oposición es: no se adivina."""
    _preparar_examen(seeded_settings, seeded_client)
    _version(
        seeded_settings,
        texto=PLANTILLA,
        version_id="plantilla",
        document_type="answer_key",
        titulo="Plantilla huérfana",
    )

    resultado = _aceptar(seeded_client, version_id="plantilla")

    assert "no está asignada a ninguna oposición" in str(resultado["questions_note"])


def _enlazar(client: TestClient, set_id: str, key_id: str, version_id: str | None) -> Any:
    return client.post(
        f"/api/v1/question-sets/{set_id}/answer-keys/{key_id}/source",
        json={"source_document_version_id": version_id},
        headers=ALLOWED_ORIGIN,
    )


def test_la_plantilla_oficial_se_enlaza_a_una_clave_que_ya_existia_si_dice_lo_mismo(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """Informe de claves (octubre de 2026): el enlace solo se hacía al aceptar la plantilla.

    Aquí la clave entra antes, pegada a mano: sin plantilla enlazada, un examen oficial no la deja
    activar. La ruta nueva la enlaza, pero solo si la plantilla dice lo mismo, pregunta a pregunta.
    """
    examen = _preparar_examen(seeded_settings, seeded_client)
    set_id = str(examen["question_set_id"])
    pegada = seeded_client.post(
        f"/api/v1/question-sets/{set_id}/parse",
        json={"kind": "answer_key", "text": PLANTILLA},
        headers=ALLOWED_ORIGIN,
    )
    assert pegada.status_code == 200, pegada.text
    key_id = str(pegada.json()["key_id"])
    activar = f"/api/v1/question-sets/{set_id}/answer-keys/{key_id}/activate"
    assert seeded_client.post(activar, headers=ALLOWED_ORIGIN).status_code == 409

    # Una plantilla que no dice lo mismo no se enlaza, y se dice dónde discrepa.
    _plantilla(
        seeded_settings,
        seeded_client,
        texto="1. a\n2. b\n3. a\n4. a\n",
        version_id="otra",
        asignar=False,
    )
    otra = _enlazar(seeded_client, set_id, key_id, "otra")
    assert otra.status_code == 409, otra.text
    assert "números 2" in otra.json()["detail"]

    # La buena sí, con las cuentas de lo comparado.
    _plantilla(seeded_settings, seeded_client, asignar=False)
    buena = _enlazar(seeded_client, set_id, key_id, "plantilla")
    assert buena.status_code == 200, buena.text
    cuerpo = buena.json()
    assert (cuerpo["agreeing"], cuerpo["disagreeing"], cuerpo["key_entries"]) == (4, 0, 4)
    assert cuerpo["key"]["source_document_version_id"] == "plantilla"
    assert seeded_client.post(activar, headers=ALLOWED_ORIGIN).status_code == 200

    # Activa en un examen oficial, ya no se puede desenlazar.
    assert _enlazar(seeded_client, set_id, key_id, None).status_code == 409
    assert _enlazar(seeded_client, set_id, key_id, "no-existe").status_code == 404


def test_enlazar_compara_en_orden_si_el_examen_reinicia_la_numeracion(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """Los seis exámenes oficiales de 2025-2026 numeran desde 1 en cada parte: comparando por
    número, la ruta se negaba con su plantilla buena («no dicen lo mismo en 17 preguntas»)."""
    examen_por_partes = (
        "PRIMERA PARTE\n" + EXAMEN.split("3. ")[0] + "SEGUNDA PARTE\n"
        "1. El plazo del procedimiento del caso C es de treinta dias habiles:\n"
        "a) Verdadero\n"
        "b) Falso\n"
        "2. El plazo del procedimiento del caso D es de cuarenta dias habiles:\n"
        "a) Verdadero\n"
        "b) Falso\n"
    )
    _version(
        seeded_settings,
        texto=examen_por_partes,
        version_id="examen",
        document_type="official_exam",
        titulo="Examen oficial por partes",
    )
    _asignar(seeded_settings, version_id="examen", node_path="I.1")
    set_id = str(_aceptar(seeded_client, version_id="examen")["question_set_id"])
    plantilla = "1. a\n2. b\n1. b\n2. a\n"
    pegada = seeded_client.post(
        f"/api/v1/question-sets/{set_id}/parse",
        json={"kind": "answer_key", "text": plantilla},
        headers=ALLOWED_ORIGIN,
    )
    assert pegada.status_code == 200, pegada.text
    key_id = str(pegada.json()["key_id"])

    _plantilla(seeded_settings, seeded_client, texto=plantilla, asignar=False)
    enlace = _enlazar(seeded_client, set_id, key_id, "plantilla")

    assert enlace.status_code == 200, enlace.text
    cuerpo = enlace.json()
    assert (cuerpo["agreeing"], cuerpo["disagreeing"], cuerpo["ambiguous"]) == (4, 0, 0)
    activar = f"/api/v1/question-sets/{set_id}/answer-keys/{key_id}/activate"
    assert seeded_client.post(activar, headers=ALLOWED_ORIGIN).status_code == 200
