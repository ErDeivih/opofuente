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


def _auditoria_de(settings: Settings, object_id: str) -> list[str]:
    """Acciones auditadas sobre un objeto, en orden: la API no publica la auditoría, la base sí."""
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.connect() as conexion:
            filas = (
                conexion.execute(
                    text(
                        "SELECT action FROM audit_events WHERE object_id = :object_id "
                        "ORDER BY created_at, id"
                    ),
                    {"object_id": object_id},
                )
                .scalars()
                .all()
            )
    finally:
        engine.dispose()
    return [str(fila) for fila in filas]


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


def test_una_version_suelta_se_sirve_con_su_documento(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """Contrato §7: `GET /document-versions/{id}`, sin pedir la ficha entera."""
    _pegar(seeded_client, "Tema 1. Texto para la version suelta.", "suelta.txt")
    artifact_id = _artefacto_de(seeded_settings, "suelta.txt")
    promocion = _promocionar(seeded_client, artifact_id, "Documento suelto")

    respuesta = seeded_client.get(f"/api/v1/document-versions/{promocion['version_id']}")

    assert respuesta.status_code == 200, respuesta.text
    detalle = respuesta.json()
    assert detalle["document_id"] == promocion["document_id"]
    assert detalle["document_title"] == "Documento suelto"
    assert detalle["document_type"] == "curriculum"
    assert detalle["owner_scope"] == "private_user"
    assert detalle["version"]["id"] == promocion["version_id"]
    assert detalle["mapping_count"] == 0
    assert seeded_client.get("/api/v1/document-versions/no-existe").status_code == 404


def test_el_contenido_de_la_version_se_lee_del_texto_extraido(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """Contrato §7: `GET /document-versions/{id}/content`, por trozos y con su calidad."""
    _pegar(
        seeded_client,
        "Tema 1. Plazos del procedimiento administrativo comun.",
        "contenido.txt",
    )
    artifact_id = _artefacto_de(seeded_settings, "contenido.txt")
    promocion = _promocionar(seeded_client, artifact_id, "Documento con contenido")

    respuesta = seeded_client.get(f"/api/v1/document-versions/{promocion['version_id']}/content")

    assert respuesta.status_code == 200, respuesta.text
    cuerpo = respuesta.json()
    assert cuerpo["document_version_id"] == promocion["version_id"]
    assert "Plazos del procedimiento" in cuerpo["text"]
    assert cuerpo["total_chars"] >= len("Plazos del procedimiento")
    assert cuerpo["quality"] in {"good", "usable_with_warnings", "ocr_unreviewed", "poor"}
    assert cuerpo["representation_id"], "el texto sale de una representación de verdad"

    trozo = seeded_client.get(
        f"/api/v1/document-versions/{promocion['version_id']}/content",
        params={"offset": 0, "limit": 5},
    ).json()
    assert trozo["text"] == cuerpo["text"][:5]
    assert trozo["truncated"] is True
    assert seeded_client.get("/api/v1/document-versions/no-existe/content").status_code == 404


def test_el_original_de_la_version_se_sirve_con_su_tipo_y_su_rango(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """Contrato §7: `GET /document-versions/{id}/original`, con `inline` solo si es seguro."""
    texto = "Tema 1. Original que se sirve tal cual."
    _pegar(seeded_client, texto, "original.txt")
    artifact_id = _artefacto_de(seeded_settings, "original.txt")
    promocion = _promocionar(seeded_client, artifact_id, "Documento original")

    respuesta = seeded_client.get(f"/api/v1/document-versions/{promocion['version_id']}/original")

    assert respuesta.status_code == 200, respuesta.text
    assert respuesta.content.decode("utf-8") == texto, "el original se sirve sin tocar"
    assert respuesta.headers["content-type"].startswith("text/plain")
    assert "inline" in respuesta.headers["content-disposition"]

    # `Range` soportado: los diez primeros bytes, con su total declarado.
    parcial = seeded_client.get(
        f"/api/v1/document-versions/{promocion['version_id']}/original",
        headers={"Range": "bytes=0-9"},
    )
    assert parcial.status_code == 206, parcial.text
    assert parcial.content.decode("utf-8") == texto[:10]
    assert parcial.headers["content-range"] == f"bytes 0-9/{len(texto.encode('utf-8'))}"

    assert seeded_client.get("/api/v1/document-versions/no-existe/original").status_code == 404


def test_las_asignaciones_de_una_version_se_sirven_por_su_ruta(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """Contrato §7: `GET /document-versions/{id}/mappings`, mismo formato que la clasificación."""
    _pegar(seeded_client, "Tema 1. Material para asignar por su ruta.", "asignado.txt")
    artifact_id = _artefacto_de(seeded_settings, "asignado.txt")
    promocion = _promocionar(seeded_client, artifact_id, "Documento asignado")
    nodo = _dos_nodos_del_programa(seeded_settings)[0]

    vacias = seeded_client.get(f"/api/v1/document-versions/{promocion['version_id']}/mappings")
    assert vacias.status_code == 200
    assert vacias.json() == []

    creada = seeded_client.post(
        f"/api/v1/document-versions/{promocion['version_id']}/mappings",
        json={"curriculum_node_id": nodo, "coverage_type": "complete"},
        headers=ALLOWED_ORIGIN,
    )
    assert creada.status_code == 201, creada.text
    # La respuesta trae el mapeo entero —con su nodo—, no solo el identificador.
    assert creada.json()["node_id"] == nodo
    assert creada.json()["node_path"]
    assert creada.json()["coverage_type"] == "complete"
    assert creada.json()["status"] == "accepted"

    listado = seeded_client.get(
        f"/api/v1/document-versions/{promocion['version_id']}/mappings"
    ).json()
    assert [mapeo["id"] for mapeo in listado] == [creada.json()["id"]]
    assert seeded_client.get("/api/v1/document-versions/no-existe/mappings").status_code == 404


def test_editar_un_documento_por_la_api_y_lo_que_no_se_puede_aplicar(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """Contrato §7: `PATCH /documents/{id}`. Publicar exige derechos revisados: si no, 409."""
    _pegar(seeded_client, "Tema 1. Material para editar metadatos.", "metadatos.txt")
    artifact_id = _artefacto_de(seeded_settings, "metadatos.txt")
    promocion = _promocionar(seeded_client, artifact_id, "Titulo provisional")

    renombrado = seeded_client.patch(
        f"/api/v1/documents/{promocion['document_id']}",
        json={"canonical_title": "  Titulo definitivo  ", "authority_tier": "A"},
        headers=ALLOWED_ORIGIN,
    )

    assert renombrado.status_code == 200, renombrado.text
    assert renombrado.json()["canonical_title"] == "Titulo definitivo"
    assert renombrado.json()["authority_tier"] == "A"
    # La ficha lo refleja: no es una respuesta de cortesía.
    ficha = seeded_client.get(f"/api/v1/documents/{promocion['document_id']}").json()
    assert ficha["document"]["canonical_title"] == "Titulo definitivo"
    assert ficha["document"]["authority_tier"] == "A"
    assert _auditoria_de(seeded_settings, promocion["document_id"]).count("document.updated") == 1

    # Una petición sin ningún campo que cambiar no escribe ni audita un cambio que no ha ocurrido.
    sin_cambios = seeded_client.patch(
        f"/api/v1/documents/{promocion['document_id']}",
        json={},
        headers=ALLOWED_ORIGIN,
    )
    assert sin_cambios.status_code == 200, sin_cambios.text
    assert sin_cambios.json()["canonical_title"] == "Titulo definitivo"
    assert _auditoria_de(seeded_settings, promocion["document_id"]).count("document.updated") == 1

    publico = seeded_client.patch(
        f"/api/v1/documents/{promocion['document_id']}",
        json={"owner_scope": "public"},
        headers=ALLOWED_ORIGIN,
    )
    assert publico.status_code == 409, publico.text
    assert publico.json()["code"] == "classification_conflict"
    assert "derechos" in publico.json()["detail"]
    assert (
        seeded_client.get(f"/api/v1/documents/{promocion['document_id']}").json()["document"][
            "owner_scope"
        ]
        == "private_user"
    ), "un conflicto no cambia nada"

    vacio = seeded_client.patch(
        f"/api/v1/documents/{promocion['document_id']}",
        json={"canonical_title": "   "},
        headers=ALLOWED_ORIGIN,
    )
    assert vacio.status_code in {409, 422}, vacio.text

    desconocido = seeded_client.patch(
        f"/api/v1/documents/{promocion['document_id']}",
        json={"document_type": "tipo-que-no-existe"},
        headers=ALLOWED_ORIGIN,
    )
    assert desconocido.status_code == 409, desconocido.text
    assert (
        seeded_client.patch(
            f"/api/v1/documents/{promocion['document_id']}",
            json={"owner_scope": "generated"},
            headers=ALLOWED_ORIGIN,
        ).status_code
        == 422
    ), "«generated» no se concede desde la API"
    assert (
        seeded_client.patch(
            "/api/v1/documents/no-existe", json={"canonical_title": "X"}, headers=ALLOWED_ORIGIN
        ).status_code
        == 404
    )


def test_el_diff_compara_dos_versiones_del_mismo_documento(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """Ruta añadida al contrato: compara secciones por etiqueta y no fusiona nada."""
    _pegar(seeded_client, "Tema 1. Primera redaccion del tema.", "primera.txt")
    primero = _promocionar(
        seeded_client, _artefacto_de(seeded_settings, "primera.txt"), "Temario versionado"
    )
    _pegar(seeded_client, "Tema 1. Segunda redaccion, mas larga, del tema.", "segunda.txt")
    segunda = seeded_client.post(
        "/api/v1/documents",
        json={
            "artifact_id": _artefacto_de(seeded_settings, "segunda.txt"),
            "title": "Temario versionado",
            "document_type": "curriculum",
            "document_id": primero["document_id"],
        },
        headers=ALLOWED_ORIGIN,
    )
    assert segunda.status_code == 200, segunda.text
    segunda_version = segunda.json()["version_id"]
    assert segunda_version != primero["version_id"]

    comparacion = seeded_client.get(
        f"/api/v1/documents/{primero['document_id']}/diff",
        params={"from_version_id": primero["version_id"], "to_version_id": segunda_version},
    )

    assert comparacion.status_code == 200, comparacion.text
    diff = comparacion.json()
    assert diff["document_id"] == primero["document_id"]
    assert diff["from_version_id"] == primero["version_id"]
    assert diff["to_version_id"] == segunda_version
    assert diff["has_changes"] is False, (
        "sin secciones que comparar no hay cambios que anunciar: el recuento manda, y aquí es cero"
    )
    assert diff["sections"] == [], (
        "el texto pegado entra como texto plano y el extractor de texto plano todavía no parte "
        "secciones (DEBT-009), así que aquí no hay nada que comparar; el diff **con** secciones "
        "está probado en test_library.py sobre representaciones reales con secciones"
    )
    assert diff["added"] + diff["removed"] + diff["changed"] + diff["unchanged"] == len(
        diff["sections"]
    )
    assert all(
        seccion["kind"] in {"added", "removed", "changed", "unchanged"}
        for seccion in diff["sections"]
    )

    # Una versión de otro documento no es un diff: es un 404, no una comparación inventada.
    _pegar(seeded_client, "Tema 1. Otro documento distinto.", "ajeno.txt")
    ajeno = _promocionar(
        seeded_client, _artefacto_de(seeded_settings, "ajeno.txt"), "Documento ajeno"
    )
    assert (
        seeded_client.get(
            f"/api/v1/documents/{primero['document_id']}/diff",
            params={"from_version_id": primero["version_id"], "to_version_id": ajeno["version_id"]},
        ).status_code
        == 404
    )
    assert (
        seeded_client.get(
            f"/api/v1/documents/{primero['document_id']}/diff",
            params={"from_version_id": "no-existe", "to_version_id": segunda_version},
        ).status_code
        == 404
    )
