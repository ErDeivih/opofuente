"""Pruebas de integración de la API de perfiles (S01)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from opofuente.api.errors import PROBLEM_MEDIA_TYPE

TAI = "tai-age"
GC = "gc-cabos-guardias"


def _opposition_id(client: TestClient, code: str) -> str:
    oppositions = client.get("/api/v1/oppositions").json()
    return next(item["id"] for item in oppositions if item["code"] == code)


def test_lista_de_oposiciones_con_su_convocatoria_activa(seeded_client: TestClient) -> None:
    response = seeded_client.get("/api/v1/oppositions")
    assert response.status_code == 200
    oppositions = response.json()
    assert {item["code"] for item in oppositions} == {TAI, GC}

    tai = next(item for item in oppositions if item["code"] == TAI)
    assert tai["active"] is True
    assert tai["active_convocation"]["code"] == "tai-age-2025"
    assert tai["active_convocation"]["published_at"] == "2025-12-22"
    assert tai["active_convocation"]["status"] == "active"


def test_detalle_de_oposicion_con_sus_convocatorias(seeded_client: TestClient) -> None:
    oposicion_id = _opposition_id(seeded_client, GC)
    response = seeded_client.get(f"/api/v1/oppositions/{oposicion_id}")
    assert response.status_code == 200
    body = response.json()
    assert body["opposition"]["code"] == GC
    assert [row["code"] for row in body["convocations"]] == ["gc-cabos-guardias-2026"]
    convocatoria = body["convocations"][0]
    assert (
        convocatoria["official_url"] == "https://www.boe.es/diario_boe/txt.php?id=BOE-A-2026-9982"
    )
    assert convocatoria["exam_date"] is None


def test_convocatoria_de_una_oposicion_inexistente_devuelve_404(seeded_client: TestClient) -> None:
    response = seeded_client.get("/api/v1/oppositions/no-existe/convocations")
    assert response.status_code == 404
    assert response.headers["content-type"].startswith(PROBLEM_MEDIA_TYPE)
    assert response.json()["code"] == "not_found"


def test_detalle_de_convocatoria_con_partes_y_reglas(seeded_client: TestClient) -> None:
    oposicion_id = _opposition_id(seeded_client, TAI)
    convocatoria = seeded_client.get(f"/api/v1/oppositions/{oposicion_id}/convocations").json()[0]
    response = seeded_client.get(f"/api/v1/convocations/{convocatoria['id']}")
    assert response.status_code == 200
    body = response.json()

    assert body["source_reference"] == "BOE-A-2025-26262 · ANEXO V"
    assert body["opposition_code"] == TAI
    partes = {part["code"]: part for part in body["parts"]}
    assert partes["ejercicio_unico"]["time_minutes"] == 120
    assert partes["primera_parte"]["ordinary_items"] == 80
    assert partes["primera_parte"]["options_per_question"] is None
    # Toda regla viaja con su cita.
    assert all(rule["evidence_quote"] for rule in body["rules"])
    assert "official_scaled_score_requires_published_criteria" in {
        rule["code"] for rule in body["rules"]
    }


def test_programa_de_tai_tiene_cuatro_bloques_y_treinta_y_tres_temas(
    seeded_client: TestClient,
) -> None:
    oposicion_id = _opposition_id(seeded_client, TAI)
    convocatoria = seeded_client.get(f"/api/v1/oppositions/{oposicion_id}/convocations").json()[0]
    response = seeded_client.get(f"/api/v1/convocations/{convocatoria['id']}/curriculum")
    assert response.status_code == 200
    body = response.json()

    assert body["counts"] == {"block": 4, "topic": 33, "epigraph": 0}
    assert len(body["nodes"]) == 4
    temas = [tema for bloque in body["nodes"] for tema in bloque["children"]]
    assert len(temas) == 33
    assert body["nodes"][0]["official_code"] == "I"
    assert temas[0]["path"] == "I.1"


def test_programa_de_guardia_civil_tiene_veinticinco_temas(seeded_client: TestClient) -> None:
    oposicion_id = _opposition_id(seeded_client, GC)
    convocatoria = seeded_client.get(f"/api/v1/oppositions/{oposicion_id}/convocations").json()[0]
    response = seeded_client.get(f"/api/v1/convocations/{convocatoria['id']}/curriculum")
    body = response.json()

    assert body["counts"]["topic"] == 25
    assert len(body["nodes"]) == 25
    assert body["nodes"][0]["title"] == "DERECHOS HUMANOS"
    assert body["nodes"][0]["children"], "cada tema debe traer sus bloques"
    primer_bloque = body["nodes"][0]["children"][0]
    assert primer_bloque["children"], "cada bloque debe traer sus epígrafes"


def test_detalle_de_nodo_con_ancestros_y_procedencia(seeded_client: TestClient) -> None:
    oposicion_id = _opposition_id(seeded_client, TAI)
    convocatoria = seeded_client.get(f"/api/v1/oppositions/{oposicion_id}/convocations").json()[0]
    curriculum = seeded_client.get(f"/api/v1/convocations/{convocatoria['id']}/curriculum").json()
    tema = curriculum["nodes"][0]["children"][0]

    response = seeded_client.get(f"/api/v1/curriculum-nodes/{tema['id']}")
    assert response.status_code == 200
    body = response.json()
    assert body["node"]["path"] == tema["path"]
    assert [ancestor["official_code"] for ancestor in body["ancestors"]] == ["I"]
    assert body["official_url"] == "https://www.boe.es/diario_boe/txt.php?id=BOE-A-2025-26262"
    # La cobertura todavía no se calcula: se declara nula, no cero.
    assert body["coverage"] is None


def test_nodo_inexistente_devuelve_404(seeded_client: TestClient) -> None:
    response = seeded_client.get("/api/v1/curriculum-nodes/no-existe")
    assert response.status_code == 404
    assert response.json()["code"] == "not_found"


def test_activar_una_oposicion_inexistente_devuelve_404(seeded_client: TestClient) -> None:
    response = seeded_client.post("/api/v1/oppositions/no-existe/activate")
    assert response.status_code == 404
    assert response.headers["content-type"].startswith(PROBLEM_MEDIA_TYPE)


def test_escritura_desde_un_origen_ajeno_se_rechaza(seeded_client: TestClient) -> None:
    """La primera ruta de escritura del proyecto pasa por la comprobación de Origin."""
    oposicion_id = _opposition_id(seeded_client, GC)
    response = seeded_client.post(
        f"/api/v1/oppositions/{oposicion_id}/activate",
        headers={"Origin": "http://malicioso.example"},
    )
    assert response.status_code == 403
    body = response.json()
    assert body["code"] == "forbidden_origin"
    assert response.headers["content-type"].startswith(PROBLEM_MEDIA_TYPE)


def test_activar_desde_el_origen_del_frontend_funciona(seeded_client: TestClient) -> None:
    oposicion_id = _opposition_id(seeded_client, GC)
    response = seeded_client.post(
        f"/api/v1/oppositions/{oposicion_id}/activate",
        headers={"Origin": "http://127.0.0.1:5173"},
    )
    assert response.status_code == 200


def test_la_api_sin_sembrar_no_inventa_perfiles(client: TestClient) -> None:
    """Con la base migrada pero sin sembrar, la lista está vacía, no con datos falsos."""
    response = client.get("/api/v1/oppositions")
    assert response.status_code == 200
    assert response.json() == []
