"""Pruebas de integración de cambios e invalidación (S11; RF-09 y demo D de `16_TRACEABILITY`).

La demo D, entera y por la API real: tener un resumen que depende de la versión 1 de un documento,
importar una versión 2 con una sección modificada, confirmar el diff y observar que **solo** los
derivados afectados quedan pendientes de revisar, con la versión 1 todavía accesible.

El material entra por el camino de verdad (pegado → copiado → extraído) y las dependencias se crean
al crear el resumen, no se infieren después.
"""

from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy import text

from opofuente.config import Settings
from opofuente.infrastructure.db import build_engine
from opofuente_testing.jobs import run_one_job

ALLOWED_ORIGIN = {"Origin": "http://127.0.0.1:5173"}

#: Dos bloques separados por una línea en blanco: dos secciones citables (ADR-008). La segunda es la
#: que cambia entre versiones, así que un resumen que solo use la primera **no** debe invalidarse.
V1 = "Tema 1. Plazos administrativos\n\nEl plazo es de diez dias habiles.\n"
V2 = "Tema 1. Plazos administrativos\n\nEl plazo es de veinte dias habiles.\n"


def _pegar(client: TestClient, texto: str, titulo: str) -> str:
    respuesta = client.post(
        "/api/v1/ingestion-batches/paste",
        json={"text": texto, "title": titulo},
        headers=ALLOWED_ORIGIN,
    )
    assert respuesta.status_code == 200, respuesta.text
    run_one_job(client, attempts=3)
    engine = build_engine(client.app.state.settings.data_paths.database)
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


def _promocionar(
    client: TestClient, artifact_id: str, titulo: str, *, document_id: str | None = None
) -> dict[str, Any]:
    cuerpo: dict[str, Any] = {
        "artifact_id": artifact_id,
        "title": titulo,
        "document_type": "curriculum",
    }
    if document_id is not None:
        cuerpo["document_id"] = document_id
    respuesta = client.post("/api/v1/documents", json=cuerpo, headers=ALLOWED_ORIGIN)
    assert respuesta.status_code == 200, respuesta.text
    return respuesta.json()


def _aceptar(client: TestClient, document_id: str, version_id: str) -> None:
    respuesta = client.post(
        f"/api/v1/documents/{document_id}/versions/{version_id}/accept", headers=ALLOWED_ORIGIN
    )
    assert respuesta.status_code == 200, respuesta.text


def _secciones(client: TestClient, version_id: str) -> list[dict[str, Any]]:
    respuesta = client.get(f"/api/v1/document-versions/{version_id}/sections")
    assert respuesta.status_code == 200, respuesta.text
    return list(respuesta.json())


def _resumir(
    client: TestClient, version_id: str, section_ids: list[str], titulo: str
) -> dict[str, Any]:
    respuesta = client.post(
        "/api/v1/derived-artifacts",
        json={"document_version_id": version_id, "section_ids": section_ids, "title": titulo},
        headers=ALLOWED_ORIGIN,
    )
    assert respuesta.status_code == 201, respuesta.text
    return respuesta.json()


def _documento_aceptado(client: TestClient) -> tuple[str, str, list[dict[str, Any]]]:
    """Un documento con su versión 1 aceptada y sus secciones.

    Devuelve `(document_id, version_id, secciones)`.
    """
    artifact = _pegar(client, V1, "plazos-v1.txt")
    promocion = _promocionar(client, artifact, "Plazos administrativos")
    _aceptar(client, promocion["document_id"], promocion["version_id"])
    return (
        promocion["document_id"],
        promocion["version_id"],
        _secciones(client, promocion["version_id"]),
    )


def _etiqueta(seccion: dict[str, Any]) -> str:
    """Cómo se llama esa sección en un diff: su título o «sección N» (la misma regla que S11)."""
    titulo = seccion.get("title") or seccion.get("label")
    return str(titulo) if titulo else f"sección {seccion['ordinal']}"


# --- el cambio se propone -----------------------------------------------------------------------


def test_una_version_nueva_propone_un_cambio_con_su_diff_y_sus_afectados(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    document_id, version1, secciones = _documento_aceptado(seeded_client)
    assert len(secciones) == 2, "el material tiene dos bloques: dos secciones citables"

    # Un resumen de la **segunda** sección: es lo que depende de lo que va a cambiar.
    resumen = _resumir(seeded_client, version1, [secciones[1]["id"]], "Resumen de plazos")
    assert "diez dias" in resumen["content"]
    assert resumen["sections"] == [_etiqueta(secciones[1])]
    assert resumen["generator"] == "extractive-summary-v1"
    assert resumen["model"] is None
    assert resumen["needs_review"] is False

    # Llega la versión 2 del mismo documento (sección 2 modificada).
    artifact2 = _pegar(seeded_client, V2, "plazos-v2.txt")
    promocion2 = _promocionar(
        seeded_client, artifact2, "Plazos administrativos", document_id=document_id
    )
    assert promocion2["created_version"] is True

    cambios = seeded_client.get("/api/v1/change-sets").json()
    assert len(cambios) == 1
    cambio = cambios[0]
    assert cambio["status"] == "proposed"
    assert cambio["previous_version_id"] == version1
    assert cambio["new_version_id"] == promocion2["version_id"]
    assert cambio["sections_changed"] == 1
    assert cambio["sections_unchanged"] == 1
    assert cambio["sections_added"] == 0
    # El aviso de lo que la aplicación **no** decide viaja con el cambio.
    assert "No decide si una norma sigue vigente" in cambio["effect_note"]
    # Y lo afectado es solo el resumen que depende de la sección que cambió.
    assert [item["id"] for item in cambio["affected"]] == [resumen["id"]]
    assert "que ha cambiado" in cambio["affected"][0]["reason"]
    # Nada se ha aplicado todavía: el resumen sigue igual y la versión 1 sigue aceptada.
    assert (
        seeded_client.get(f"/api/v1/derived-artifacts/{resumen['id']}").json()["needs_review"]
        is False
    )
    detalle = seeded_client.get(f"/api/v1/documents/{document_id}").json()
    assert detalle["document"]["active_version"]["id"] == version1


def test_lo_que_solo_depende_de_secciones_intactas_no_se_toca(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """La otra mitad del criterio: el derivado que no depende del cambio se queda como estaba."""
    document_id, version1, secciones = _documento_aceptado(seeded_client)
    intacto = _resumir(seeded_client, version1, [secciones[0]["id"]], "Resumen del título")
    afectado = _resumir(seeded_client, version1, [secciones[1]["id"]], "Resumen del plazo")

    artifact2 = _pegar(seeded_client, V2, "plazos-v2b.txt")
    _promocionar(seeded_client, artifact2, "Plazos administrativos", document_id=document_id)

    cambio = seeded_client.get("/api/v1/change-sets").json()[0]
    assert [item["id"] for item in cambio["affected"]] == [afectado["id"]]
    assert intacto["id"] not in [item["id"] for item in cambio["affected"]]

    confirmado = seeded_client.post(
        f"/api/v1/change-sets/{cambio['id']}/confirm", headers=ALLOWED_ORIGIN
    )
    assert confirmado.status_code == 200, confirmado.text
    assert confirmado.json()["applied"] is True
    assert confirmado.json()["marked"] == [afectado["id"]]

    pendiente = seeded_client.get(f"/api/v1/derived-artifacts/{afectado['id']}").json()
    assert pendiente["needs_review"] is True
    assert "ha cambiado" in str(pendiente["needs_review_reason"])
    assert pendiente["review_status"] == "pending"

    # El que solo dependía del título intacto sigue sin marca: no se invalida lo que no cambió.
    assert (
        seeded_client.get(f"/api/v1/derived-artifacts/{intacto['id']}").json()["needs_review"]
        is False
    )


# --- la confirmación aplica el cambio -----------------------------------------------------------


def test_confirmar_acepta_la_version_sustituye_la_anterior_y_conserva_el_historico(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    document_id, version1, secciones = _documento_aceptado(seeded_client)
    _resumir(seeded_client, version1, [secciones[1]["id"]], "Resumen del plazo")
    artifact2 = _pegar(seeded_client, V2, "plazos-v2c.txt")
    promocion2 = _promocionar(
        seeded_client, artifact2, "Plazos administrativos", document_id=document_id
    )
    cambio = seeded_client.get("/api/v1/change-sets").json()[0]

    # Antes de confirmar, la propuesta es la simulación: se puede mirar entera sin consecuencias.
    simulacion = seeded_client.get(f"/api/v1/change-sets/{cambio['id']}/affected").json()
    assert simulacion["status"] == "proposed"
    assert len(simulacion["affected"]) == 1

    confirmado = seeded_client.post(
        f"/api/v1/change-sets/{cambio['id']}/confirm", headers=ALLOWED_ORIGIN
    ).json()
    assert confirmado["superseded_version_id"] == version1
    assert confirmado["change"]["status"] == "confirmed"
    assert confirmado["change"]["confirmed_at"] is not None

    detalle = seeded_client.get(f"/api/v1/documents/{document_id}").json()
    assert detalle["document"]["active_version"]["id"] == promocion2["version_id"]
    assert detalle["document"]["active_version"]["status"] == "accepted"
    # La versión 1 no se borra: queda sustituida y accesible como histórica (demo D, paso 5).
    anteriores = [version for version in detalle["versions"] if version["id"] == version1]
    assert anteriores and anteriores[0]["status"] == "superseded"
    assert seeded_client.get(f"/api/v1/document-versions/{version1}").status_code == 200

    # Confirmar dos veces no se admite: volvería a marcar derivados sin cambio nuevo.
    otra_vez = seeded_client.post(
        f"/api/v1/change-sets/{cambio['id']}/confirm", headers=ALLOWED_ORIGIN
    )
    assert otra_vez.status_code == 409, otra_vez.text
    assert "ya está confirmado" in otra_vez.json()["detail"]


def test_descartar_una_propuesta_no_invalida_nada(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    document_id, version1, secciones = _documento_aceptado(seeded_client)
    resumen = _resumir(seeded_client, version1, [secciones[1]["id"]], "Resumen del plazo")
    artifact2 = _pegar(seeded_client, V2, "plazos-v2d.txt")
    _promocionar(seeded_client, artifact2, "Plazos administrativos", document_id=document_id)
    cambio = seeded_client.get("/api/v1/change-sets").json()[0]

    descartado = seeded_client.post(
        f"/api/v1/change-sets/{cambio['id']}/discard", headers=ALLOWED_ORIGIN
    )
    assert descartado.status_code == 200, descartado.text
    assert descartado.json()["change"]["status"] == "discarded"
    assert descartado.json()["marked"] == []

    # Nada ha cambiado: el resumen sigue sin marca y la versión 1 sigue siendo la activa.
    assert (
        seeded_client.get(f"/api/v1/derived-artifacts/{resumen['id']}").json()["needs_review"]
        is False
    )
    detalle = seeded_client.get(f"/api/v1/documents/{document_id}").json()
    assert detalle["document"]["active_version"]["id"] == version1


# --- la revisión de un derivado -----------------------------------------------------------------


def test_un_derivado_marcado_se_revisa_o_se_aparta(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    document_id, version1, secciones = _documento_aceptado(seeded_client)
    resumen = _resumir(seeded_client, version1, [secciones[1]["id"]], "Resumen del plazo")
    artifact2 = _pegar(seeded_client, V2, "plazos-v2e.txt")
    _promocionar(seeded_client, artifact2, "Plazos administrativos", document_id=document_id)
    cambio = seeded_client.get("/api/v1/change-sets").json()[0]
    seeded_client.post(f"/api/v1/change-sets/{cambio['id']}/confirm", headers=ALLOWED_ORIGIN)

    pendientes = seeded_client.get("/api/v1/derived-artifacts?needs_review=true").json()
    assert [item["id"] for item in pendientes] == [resumen["id"]]

    # Revisar lo que no está pendiente no vale: no hay nada que cerrar.
    otro = seeded_client.post(
        f"/api/v1/derived-artifacts/{resumen['id']}/resolution",
        json={"resolution": "reviewed"},
        headers=ALLOWED_ORIGIN,
    )
    assert otro.status_code == 200
    repetido = seeded_client.post(
        f"/api/v1/derived-artifacts/{resumen['id']}/resolution",
        json={"resolution": "reviewed"},
        headers=ALLOWED_ORIGIN,
    )
    assert repetido.status_code == 409, repetido.text
    assert "no está pendiente" in repetido.json()["detail"]

    # El motivo de la marca se conserva: es la historia de la revisión.
    revisado = otro.json()
    assert revisado["needs_review"] is False
    assert revisado["review_status"] == "reviewed"
    assert revisado["reviewed_at"] is not None
    assert "ha cambiado" in str(revisado["needs_review_reason"])


# --- lo que no se puede hacer -------------------------------------------------------------------


def test_un_resumen_necesita_secciones_con_texto(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    _, version1, _ = _documento_aceptado(seeded_client)

    sin_secciones = seeded_client.post(
        "/api/v1/derived-artifacts",
        json={"document_version_id": version1, "section_ids": []},
        headers=ALLOWED_ORIGIN,
    )
    assert sin_secciones.status_code == 422, sin_secciones.text

    inexistente = seeded_client.post(
        "/api/v1/derived-artifacts",
        json={"document_version_id": version1, "section_ids": ["no-existe"]},
        headers=ALLOWED_ORIGIN,
    )
    assert inexistente.status_code == 404, inexistente.text


def test_la_primera_version_no_propone_ningun_cambio(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """Sin versión anterior aceptada no hay nada que comparar: no se inventa un cambio."""
    _documento_aceptado(seeded_client)
    assert seeded_client.get("/api/v1/change-sets").json() == []
