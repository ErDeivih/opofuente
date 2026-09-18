"""Pruebas de integración de las exportaciones (08_API-CONTRACT §11) por la API real.

Comprueban el criterio de aceptación del slice: **las exportaciones contienen procedencia y
versiones** y **el material restringido requiere aviso**. Además, el fichero se escribe de verdad
en `<datos>/exports`, así que la prueba lee el disco en lugar de fiarse de la respuesta.
"""

from __future__ import annotations

import csv
import io
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi.testclient import TestClient

from opofuente.config import Settings
from opofuente.domain.export import ANKI_FIELDS, CSV_DELIMITER
from opofuente.infrastructure.db import build_engine, build_session_factory
from opofuente.infrastructure.db_models import (
    CurriculumMappingRecord,
    DocumentVersionRecord,
    EvidenceSpanRecord,
    LogicalDocumentRecord,
    QuestionEvidenceRecord,
    RightsStatusRecord,
    SourceArtifactRecord,
)

ALLOWED_ORIGIN = {"Origin": "http://127.0.0.1:5173"}


def _texto(preguntas: int) -> str:
    lineas: list[str] = []
    for numero in range(1, preguntas + 1):
        caso = chr(ord("A") + (numero - 1) % 26)
        lineas.append(f"{numero}. El plazo del procedimiento del caso {caso} es de diez dias:")
        for indice in range(4):
            lineas.append(f"{chr(ord('a') + indice)}) Opcion {chr(ord('A') + indice)}")
        lineas.append("Respuesta correcta: a")
        lineas.append("")
    return "\n".join(lineas)


def _oposicion_activa(client: TestClient) -> dict[str, Any]:
    oposiciones = client.get("/api/v1/oppositions").json()
    return next(oposicion for oposicion in oposiciones if oposicion["active"])


def _conjunto_con_clave(client: TestClient, *, preguntas: int, titulo: str = "Banco exportable"):
    activa = _oposicion_activa(client)
    creado = client.post(
        "/api/v1/question-sets",
        json={
            "title": titulo,
            "opposition_id": activa["id"],
            "set_type": "private_bank",
            "convocation_version_id": activa["active_convocation"]["id"],
        },
        headers=ALLOWED_ORIGIN,
    )
    assert creado.status_code == 201, creado.text
    conjunto = creado.json()
    importado = client.post(
        f"/api/v1/question-sets/{conjunto['id']}/parse",
        json={"kind": "questions", "text": _texto(preguntas)},
        headers=ALLOWED_ORIGIN,
    )
    assert importado.status_code == 200, importado.text
    claves = client.get(f"/api/v1/question-sets/{conjunto['id']}/answer-keys").json()
    activada = client.post(
        f"/api/v1/question-sets/{conjunto['id']}/answer-keys/{claves[0]['id']}/activate",
        headers=ALLOWED_ORIGIN,
    )
    assert activada.status_code == 200, activada.text
    return conjunto


def _documento_con_evidencia(
    settings: Settings, question_version_ids: list[str], *, rights: str
) -> None:
    """Un documento con derechos concretos y una cita de cada pregunta, escrito en la base.

    El material no se ingiere aquí: lo que se prueba es la exportación, y para eso hace falta una
    cita con derechos conocidos, que es lo que se escribe con los mismos modelos que usa la app.
    """
    engine = build_engine(settings.data_paths.database)
    ahora = datetime.now(UTC)
    identificador = uuid4().hex[:8]
    with build_session_factory(engine)() as session:
        session.add(
            RightsStatusRecord(
                id=f"rights-{identificador}",
                code=f"derechos-{identificador}",
                review_status=rights,
                sharing=rights == "reviewed",
                created_at=ahora,
                updated_at=ahora,
            )
        )
        session.add(
            SourceArtifactRecord(
                id=f"art-{identificador}",
                sha256=identificador * 8,
                size_bytes=1024,
                media_type="application/pdf",
                storage_key=f"sha256/{identificador}",
                first_seen_at=ahora,
            )
        )
        session.add(
            LogicalDocumentRecord(
                id=f"doc-{identificador}",
                canonical_title=f"Temario con derechos {rights}",
                document_type="curriculum",
                owner_scope="private_user",
                created_at=ahora,
                updated_at=ahora,
            )
        )
        session.add(
            DocumentVersionRecord(
                id=f"ver-{identificador}",
                logical_document_id=f"doc-{identificador}",
                artifact_id=f"art-{identificador}",
                status="accepted",
                rights_status_id=f"rights-{identificador}",
                approved_at=ahora,
                approved_by="local",
                created_at=ahora,
            )
        )
        session.flush()
        for indice, question_id in enumerate(question_version_ids, start=1):
            span_id = f"span-{identificador}-{indice}"
            session.add(
                EvidenceSpanRecord(
                    id=span_id,
                    document_version_id=f"ver-{identificador}",
                    ordinal=indice,
                    text="El plazo del procedimiento es de diez dias habiles.",
                    normalized_text="el plazo del procedimiento es de diez dias habiles",
                    citation_label=f"Temario, página {indice}",
                    created_at=ahora,
                )
            )
            session.add(
                QuestionEvidenceRecord(
                    question_version_id=question_id,
                    evidence_span_id=span_id,
                    role="correct",
                    claim="Sostiene la respuesta correcta",
                    status="accepted",
                    created_at=ahora,
                )
            )
        session.commit()


def _exportar(client: TestClient, ruta: str, cuerpo: dict[str, Any]) -> dict[str, Any]:
    respuesta = client.post(f"/api/v1/exports/{ruta}", json=cuerpo, headers=ALLOWED_ORIGIN)
    assert respuesta.status_code == 200, respuesta.text
    return respuesta.json()


# --- Anki CSV -----------------------------------------------------------------------------------


def test_el_csv_de_anki_lleva_las_preguntas_y_su_procedencia(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    conjunto = _conjunto_con_clave(seeded_client, preguntas=3)

    exportado = _exportar(seeded_client, "anki-csv", {"question_set_id": conjunto["id"]})
    assert exportado["format"] == "anki_csv"
    assert exportado["item_count"] == 3
    assert exportado["bytes"] > 0

    filas = list(csv.reader(io.StringIO(exportado["content"]), delimiter=CSV_DELIMITER))
    assert filas[0] == list(ANKI_FIELDS)
    assert len(filas) == 4, "tres preguntas, tres registros"
    primera = dict(zip(ANKI_FIELDS, filas[1], strict=True))
    assert primera["pregunta"].startswith("El plazo del procedimiento del caso A")
    assert primera["respuesta"] == "A"
    assert primera["conjunto"] == "Banco exportable"
    assert primera["plantilla"] == "plantilla v1"
    assert primera["origen"] == "private"
    assert primera["oposicion"], "la oposición viaja en la exportación"

    # El fichero está escrito de verdad en <datos>/exports y coincide con lo que se devolvió.
    destino = Path(exportado["path"])
    assert destino.parent == seeded_settings.data_paths.exports
    assert destino.is_file()
    assert destino.read_text(encoding="utf-8") == exportado["content"]
    assert exportado["provenance"]["opofuente"]
    assert exportado["provenance"]["generated_at"]


def test_el_markdown_lleva_una_ficha_por_pregunta_con_sus_citas(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    conjunto = _conjunto_con_clave(seeded_client, preguntas=2, titulo="Banco para Obsidian")
    preguntas = seeded_client.get(f"/api/v1/question-sets/{conjunto['id']}/questions").json()[
        "questions"
    ]
    _documento_con_evidencia(
        seeded_settings, [pregunta["id"] for pregunta in preguntas[:1]], rights="reviewed"
    )

    exportado = _exportar(
        seeded_client,
        "markdown",
        {"question_set_id": conjunto["id"], "title": "Repaso de plazos"},
    )
    contenido = exportado["content"]
    assert exportado["format"] == "markdown"
    assert "titulo: Repaso de plazos" in contenido
    assert contenido.count("## ") == 2, "una ficha por pregunta"
    assert "**Respuesta:** A" in contenido
    assert "Evidencia:" in contenido
    assert "Temario, página 1" in contenido
    assert "Temario con derechos reviewed" in contenido
    # La versión del documento citado viaja: es lo que permite comprobar la cita después.
    assert exportado["documents"] and "Temario con derechos reviewed" in exportado["documents"][0]


# --- avisos -------------------------------------------------------------------------------------


def test_el_material_restringido_se_avisa_al_exportar(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    conjunto = _conjunto_con_clave(seeded_client, preguntas=3, titulo="Banco restringido")
    preguntas = seeded_client.get(f"/api/v1/question-sets/{conjunto['id']}/questions").json()[
        "questions"
    ]
    _documento_con_evidencia(seeded_settings, [preguntas[0]["id"]], rights="restricted")
    # Otra cita viene de material sin derechos revisados: también se avisa (es el valor conservador:
    # desconocido no es un permiso).
    _documento_con_evidencia(seeded_settings, [preguntas[1]["id"]], rights="unknown")

    avisado = _exportar(seeded_client, "anki-csv", {"question_set_id": conjunto["id"]})
    assert any("derechos restringidos" in aviso for aviso in avisado["warnings"])
    assert avisado["item_count"] == 3, "el material restringido se exporta, pero con aviso"

    # Y se puede pedir que no salga: entonces se queda fuera y se dice cuántas se han quedado.
    sin_restringido = _exportar(
        seeded_client,
        "anki-csv",
        {"question_set_id": conjunto["id"], "include_restricted": False},
    )
    assert sin_restringido["item_count"] == 1, "la que no cita material restringido sí se exporta"
    assert any("se han quedado fuera" in aviso for aviso in sin_restringido["warnings"])


def test_una_pregunta_sin_plantilla_activa_se_exporta_diciendo_que_no_tiene_respuesta(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    # Un conjunto **sin** activar su clave es el caso real: la plantilla existe y no está aprobada,
    # y entonces la exportación no puede dar una respuesta correcta.
    activa = _oposicion_activa(seeded_client)
    creado = seeded_client.post(
        "/api/v1/question-sets",
        json={
            "title": "Sin clave activa",
            "opposition_id": activa["id"],
            "set_type": "private_bank",
            "convocation_version_id": activa["active_convocation"]["id"],
        },
        headers=ALLOWED_ORIGIN,
    ).json()
    seeded_client.post(
        f"/api/v1/question-sets/{creado['id']}/parse",
        json={"kind": "questions", "text": _texto(1)},
        headers=ALLOWED_ORIGIN,
    )

    exportado = _exportar(seeded_client, "anki-csv", {"question_set_id": creado["id"]})
    assert "sin respuesta conocida" in exportado["content"]
    assert any("no tienen respuesta conocida" in aviso for aviso in exportado["warnings"])


def test_exportar_sin_alcance_no_se_acepta(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    respuesta = seeded_client.post("/api/v1/exports/anki-csv", json={}, headers=ALLOWED_ORIGIN)
    assert respuesta.status_code == 422, respuesta.text
    assert respuesta.json()["field_errors"], "se dice qué falta, no un 500"


def test_una_exportacion_sin_preguntas_lo_dice(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    activa = _oposicion_activa(seeded_client)
    vacio = seeded_client.post(
        "/api/v1/question-sets",
        json={
            "title": "Conjunto vacío",
            "opposition_id": activa["id"],
            "set_type": "private_bank",
            "convocation_version_id": activa["active_convocation"]["id"],
        },
        headers=ALLOWED_ORIGIN,
    ).json()

    respuesta = seeded_client.post(
        "/api/v1/exports/markdown",
        json={"question_set_id": vacio["id"]},
        headers=ALLOWED_ORIGIN,
    )
    assert respuesta.status_code == 409, respuesta.text


def test_exportar_por_tema_solo_saca_las_preguntas_de_ese_tema(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    conjunto = _conjunto_con_clave(seeded_client, preguntas=3, titulo="Banco por tema")
    preguntas = seeded_client.get(f"/api/v1/question-sets/{conjunto['id']}/questions").json()[
        "questions"
    ]
    activa = _oposicion_activa(seeded_client)
    curriculum = seeded_client.get(
        f"/api/v1/convocations/{activa['active_convocation']['id']}/curriculum"
    ).json()

    def aplanar(nodos: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [nodo for nodo in nodos for nodo in [nodo, *aplanar(nodo["children"])]]

    tema = next(nodo for nodo in aplanar(curriculum["nodes"]) if nodo["node_type"] == "topic")
    engine = build_engine(seeded_settings.data_paths.database)
    ahora = datetime.now(UTC)
    with build_session_factory(engine)() as session:
        session.add(
            CurriculumMappingRecord(
                id=str(uuid4()),
                curriculum_node_id=tema["id"],
                subject_type="question_version",
                subject_id=preguntas[0]["id"],
                coverage_type="partial",
                depth=int(tema["depth"]),
                confidence=1.0,
                status="accepted",
                created_at=ahora,
                approved_at=ahora,
            )
        )
        session.commit()

    exportado = _exportar(
        seeded_client, "anki-csv", {"question_set_id": conjunto["id"], "node_id": tema["id"]}
    )
    assert exportado["item_count"] == 1
    filas = list(csv.reader(io.StringIO(exportado["content"]), delimiter=CSV_DELIMITER))
    campos = dict(zip(ANKI_FIELDS, filas[1], strict=True))
    assert campos["tema"] == tema["title"]
