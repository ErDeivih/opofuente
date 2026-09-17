"""Pruebas de integración de la biblioteca por la API (S05).

Se promociona material que entró por el pipeline de verdad (pegado, copiado y extraído) y se
recorre lo
que el contrato promete: la biblioteca lista el documento con su versión activa, aceptar una
versión es
una promoción crítica, secciones y evidencia se sirven para poder citar, y lo que no se puede
aplicar
responde **409 con el motivo** en lugar de decir que sí.
"""

from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy import text

from opofuente.config import Settings
from opofuente.infrastructure.db import build_engine
from opofuente_testing.jobs import run_one_job

ALLOWED_ORIGIN = {"Origin": "http://127.0.0.1:5173"}


def _artefacto_de(settings: Settings, titulo: str) -> str:
    """Identificador del artefacto que dejó el pegado: la API no lo publica, la base sí lo tiene."""
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.connect() as conexion:
            fila = conexion.execute(
                text(
                    "SELECT artifact_id FROM ingestion_items WHERE original_name = :nombre "
                    "AND artifact_id IS NOT NULL ORDER BY position LIMIT 1"
                ),
                {"nombre": titulo},
            ).scalar_one_or_none()
    finally:
        engine.dispose()
    assert fila is not None, f"el pegado no dejó artefacto para {titulo}"
    return str(fila)


def _pegar(client: TestClient, texto: str, titulo: str) -> None:
    respuesta = client.post(
        "/api/v1/ingestion-batches/paste",
        json={"text": texto, "title": titulo},
        headers=ALLOWED_ORIGIN,
    )
    assert respuesta.status_code == 200, respuesta.text
    run_one_job(client, attempts=3)


def _promocionar(client: TestClient, artifact_id: str, titulo: str) -> dict[str, Any]:
    respuesta = client.post(
        "/api/v1/documents",
        json={"artifact_id": artifact_id, "title": titulo, "document_type": "curriculum"},
        headers=ALLOWED_ORIGIN,
    )
    assert respuesta.status_code == 200, respuesta.text
    return respuesta.json()


def test_promocionar_por_la_api_deja_el_documento_en_la_biblioteca(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    _pegar(
        seeded_client,
        "Tema 1. La Constitucion espanola. Plazos y silencio administrativo.",
        "tema.txt",
    )
    artifact_id = _artefacto_de(seeded_settings, "tema.txt")

    resultado = _promocionar(seeded_client, artifact_id, "Temario de prueba")

    assert resultado["applied"] is True
    assert resultado["created_document"] is True
    assert resultado["created_version"] is True

    listado = seeded_client.get("/api/v1/documents").json()
    assert listado["total"] == 1
    documento = listado["documents"][0]
    assert documento["canonical_title"] == "Temario de prueba"
    assert documento["owner_scope"] == "private_user", "promocionar no hace público nada"
    assert documento["is_public"] is False
    assert documento["version_count"] == 1
    assert documento["active_version"]["status"] == "candidate"
    assert documento["active_version"]["is_accepted"] is False

    detalle = seeded_client.get(f"/api/v1/documents/{documento['id']}").json()
    assert len(detalle["versions"]) == 1
    assert (
        seeded_client.get(
            f"/api/v1/document-versions/{documento['active_version']['id']}/sections"
        ).status_code
        == 200
    )
    assert (
        seeded_client.get(
            f"/api/v1/document-versions/{documento['active_version']['id']}/evidence"
        ).status_code
        == 200
    )


def test_aceptar_una_version_por_la_api_la_deja_como_activa_y_aceptada(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    _pegar(seeded_client, "Tema 1. Normativa aplicable al procedimiento comun.", "normativa.txt")
    artifact_id = _artefacto_de(seeded_settings, "normativa.txt")
    promocion = _promocionar(seeded_client, artifact_id, "Normativa de prueba")

    respuesta = seeded_client.post(
        f"/api/v1/documents/{promocion['document_id']}/versions/{promocion['version_id']}/accept",
        headers=ALLOWED_ORIGIN,
    )

    assert respuesta.status_code == 200, respuesta.text
    assert respuesta.json()["applied"] is True
    documento = seeded_client.get(f"/api/v1/documents/{promocion['document_id']}").json()[
        "document"
    ]
    assert documento["active_version"]["is_accepted"] is True
    assert documento["active_version"]["status"] == "accepted"
    assert documento["active_version"]["approved_at"] is not None


def test_lo_que_no_se_puede_aplicar_responde_409_con_el_motivo(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """Nada de «ok» sin efecto: si la operación no se puede aplicar, se dice por qué."""
    _pegar(seeded_client, "Tema 1. Contenido cualquiera para probar el conflicto.", "conflicto.txt")
    artifact_id = _artefacto_de(seeded_settings, "conflicto.txt")
    promocion = _promocionar(seeded_client, artifact_id, "Documento con conflicto")

    respuesta = seeded_client.post(
        f"/api/v1/documents/{promocion['document_id']}/versions/{promocion['version_id']}"
        "/mark-supersedes",
        json={"superseded_id": "version-que-no-existe"},
        headers=ALLOWED_ORIGIN,
    )

    assert respuesta.status_code == 409, respuesta.text
    assert respuesta.json()["code"] == "classification_conflict"
    detalle = seeded_client.get(f"/api/v1/documents/{promocion['document_id']}").json()
    assert detalle["document"]["active_version"]["supersedes_id"] is None, (
        "un conflicto no cambia nada"
    )


def test_una_version_que_no_es_del_documento_da_404(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    _pegar(seeded_client, "Tema 1. Material para comprobar el 404.", "otro.txt")
    artifact_id = _artefacto_de(seeded_settings, "otro.txt")
    promocion = _promocionar(seeded_client, artifact_id, "Otro documento")

    respuesta = seeded_client.post(
        f"/api/v1/documents/{promocion['document_id']}/versions/ver-inventada/accept",
        headers=ALLOWED_ORIGIN,
    )

    assert respuesta.status_code == 404


def test_las_colecciones_agrupan_sin_duplicar(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    _pegar(seeded_client, "Tema 1. Material para la coleccion.", "coleccion.txt")
    artifact_id = _artefacto_de(seeded_settings, "coleccion.txt")
    promocion = _promocionar(seeded_client, artifact_id, "Documento de coleccion")

    creada = seeded_client.post(
        "/api/v1/collections",
        json={"name": "Oposicion 2026", "description": "Material del ano"},
        headers=ALLOWED_ORIGIN,
    )
    assert creada.status_code == 200, creada.text
    coleccion = creada.json()

    primera = seeded_client.post(
        f"/api/v1/collections/{coleccion['id']}/items",
        json={"subject_type": "document_version", "subject_id": promocion["version_id"]},
        headers=ALLOWED_ORIGIN,
    )
    segunda = seeded_client.post(
        f"/api/v1/collections/{coleccion['id']}/items",
        json={"subject_type": "document_version", "subject_id": promocion["version_id"]},
        headers=ALLOWED_ORIGIN,
    )

    assert primera.status_code == 200, primera.text
    assert primera.json()["item_count"] == 1
    assert segunda.json()["item_count"] == 1, "añadir dos veces no duplica"
    assert seeded_client.get("/api/v1/collections").json()[0]["name"] == "Oposicion 2026"


def _dos_nodos_del_programa(settings: Settings) -> list[str]:
    """Dos nodos del programa sembrado.

    La API no publica un listado de nodos y la base sí lo tiene, así que la prueba los lee de ahí y
    comprueba que el mapeo creado por la API es el que la cobertura cuenta después.
    """
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.connect() as conexion:
            filas = (
                conexion.execute(text("SELECT id FROM curriculum_nodes ORDER BY path LIMIT 2"))
                .scalars()
                .all()
            )
    finally:
        engine.dispose()
    assert len(filas) == 2, "el programa sembrado tiene que traer al menos dos nodos"
    return [str(fila) for fila in filas]


def test_una_fuente_se_guarda_una_vez_y_se_asigna_a_dos_nodos(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """El criterio de S05 por la API: un artefacto, **una** versión y **dos** mapeos (§7)."""
    _pegar(
        seeded_client,
        "Tema 1. Material que sirve a dos programas a la vez.",
        "compartido.txt",
    )
    artifact_id = _artefacto_de(seeded_settings, "compartido.txt")
    promocion = _promocionar(seeded_client, artifact_id, "Material compartido")
    nodos = _dos_nodos_del_programa(seeded_settings)

    creados = [
        seeded_client.post(
            f"/api/v1/document-versions/{promocion['version_id']}/mappings",
            json={"curriculum_node_id": nodo, "coverage_type": "partial"},
            headers=ALLOWED_ORIGIN,
        )
        for nodo in nodos
    ]

    assert [respuesta.status_code for respuesta in creados] == [201, 201], [
        respuesta.text for respuesta in creados
    ]
    mapeos = seeded_client.get(
        "/api/v1/mappings",
        params={"subject_type": "document_version", "subject_id": promocion["version_id"]},
    ).json()
    assert len(mapeos) == 2, mapeos
    assert {mapeo["node_id"] for mapeo in mapeos} == set(nodos)
    assert all(mapeo["status"] == "accepted" for mapeo in mapeos)
    assert all(mapeo["approved_at"] is not None for mapeo in mapeos), (
        "un mapeo que pide una persona nace aceptado y con fecha"
    )

    # Y el fichero sigue siendo uno: dos mapeos no crean un segundo documento ni otra versión.
    listado = seeded_client.get("/api/v1/documents").json()
    assert listado["total"] == 1
    assert listado["documents"][0]["version_count"] == 1

    repetido = seeded_client.post(
        f"/api/v1/document-versions/{promocion['version_id']}/mappings",
        json={"curriculum_node_id": nodos[0], "coverage_type": "complete"},
        headers=ALLOWED_ORIGIN,
    )
    assert repetido.status_code == 201, repetido.text
    assert (
        len(
            seeded_client.get(
                "/api/v1/mappings",
                params={
                    "subject_type": "document_version",
                    "subject_id": promocion["version_id"],
                },
            ).json()
        )
        == 2
    ), "asignar dos veces el mismo nodo no duplica el mapeo"

    inexistente = seeded_client.post(
        "/api/v1/document-versions/no-existe/mappings",
        json={"curriculum_node_id": nodos[0]},
        headers=ALLOWED_ORIGIN,
    )
    assert inexistente.status_code == 404, inexistente.text
    sin_nodo = seeded_client.post(
        f"/api/v1/document-versions/{promocion['version_id']}/mappings",
        json={"curriculum_node_id": "nodo-que-no-existe"},
        headers=ALLOWED_ORIGIN,
    )
    assert sin_nodo.status_code == 404, sin_nodo.text
    assert (
        len(
            seeded_client.get(
                "/api/v1/mappings",
                params={
                    "subject_type": "document_version",
                    "subject_id": promocion["version_id"],
                },
            ).json()
        )
        == 2
    ), "un 404 no deja mapeo a medias"
