"""Pruebas de la API del plan (O4).

El planificador ya tiene sus pruebas de dominio. Aqui se comprueba lo que la pantalla recibe:
que el calendario guardado se puede volver a leer, que el progreso no se inventa sin plan y que
los repasos que no caben en la fase de lectura **se dicen** en la respuesta del `PUT /plan`.

El corpus es sintetico y minimo: dos temas de un bloque con una pregunta anclada cada uno. Es lo
que `temas()` exige para no dejar el plan vacio, sin depender de los perfiles sembrados (que traen
curriculo pero ninguna pregunta).
"""

from __future__ import annotations

from datetime import date, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import text

from opofuente.infrastructure.db import build_engine


def _ejecutar(
    client: TestClient, sentencia: str, parametros: dict[str, object] | None = None
) -> None:
    engine = build_engine(client.app.state.settings.data_paths.database)
    try:
        with engine.begin() as conexion:
            conexion.execute(text(sentencia), parametros or {})
    finally:
        engine.dispose()


def _programa(client: TestClient) -> None:
    """Un bloque con dos temas y una pregunta anclada a cada uno."""
    _ejecutar(
        client,
        "INSERT INTO oppositions (id, code, name, active, created_at, updated_at) VALUES "
        "('op-plan', 'tai-plan', 'TAI', 0, '2026-01-01', '2026-01-01')",
    )
    _ejecutar(
        client,
        "INSERT INTO convocation_versions (id, opposition_id, code, title, official_url, "
        "published_at, status, created_at, updated_at) VALUES ('conv-plan', 'op-plan', "
        "'tai-plan-2026', 'TAI 2026', 'https://boe.es/x', '2026-01-01', 'available', "
        "'2026-01-01', '2026-01-01')",
    )
    _ejecutar(
        client,
        "INSERT INTO curriculum_nodes (id, convocation_version_id, parent_id, node_type, "
        "official_code, title, position, path, depth) VALUES "
        "('bloque-plan', 'conv-plan', NULL, 'block', 'III', 'Bloque III', 1, 'III', 0), "
        "('tema-plan-1', 'conv-plan', 'bloque-plan', 'topic', 'III.1', 'Tema III.1', 1, 'III.1', 1), "
        "('tema-plan-2', 'conv-plan', 'bloque-plan', 'topic', 'III.2', 'Tema III.2', 2, 'III.2', 1)",
    )
    # La pregunta existe de verdad (conjunto y version) aunque el contenido no se use: el ancla
    # declara que el tema esta practicado y la base no admite apuntar a una pregunta inexistente.
    _ejecutar(
        client,
        "INSERT INTO question_sets (id, title, opposition_id, set_type, status, distribution, "
        "origin_scope, key_reliability, key_checked_count, key_discrepant_count, created_at, "
        "updated_at) VALUES ('set-plan', 'Banco del plan', 'op-plan', 'private_bank', "
        "'confirmed', 'personal', 'desconocida', 'fiable', 0, 0, '2026-01-01', '2026-01-01')",
    )
    for indice in (1, 2):
        _ejecutar(
            client,
            "INSERT INTO question_versions (id, question_set_id, stable_key, version_no, stem, "
            "question_type, position, status, origin_type, created_at) VALUES (:id, 'set-plan', "
            ":clave, 1, 'Enunciado', 'single_choice', :posicion, 'verified', 'private', "
            "'2026-01-01')",
            {
                "id": f"pregunta-plan-{indice}",
                "clave": f"clave-plan-{indice}",
                "posicion": indice,
            },
        )
    for indice, nodo in enumerate(("tema-plan-1", "tema-plan-2"), start=1):
        _ejecutar(
            client,
            "INSERT INTO question_note_anchors (id, question_version_id, curriculum_node_id, "
            "anchor, group_signature, key_status, result, attempts, checked_at) VALUES "
            "(:id, :pregunta, :nodo, 'apartado', 'firma', 'draft', 'covered', 1, '2026-10-01')",
            {
                "id": f"ancla-plan-{indice}",
                "pregunta": f"pregunta-plan-{indice}",
                "nodo": nodo,
            },
        )


def test_sin_plan_el_calendario_y_el_progreso_son_404(client: TestClient) -> None:
    guardado = client.get("/api/v1/plan")
    assert guardado.status_code == 200
    assert guardado.json()["exam_date"] is None

    assert client.get("/api/v1/plan/calendario").status_code == 404
    assert client.get("/api/v1/plan/progreso").status_code == 404


def test_sin_temas_no_hay_plan_que_guardar(client: TestClient) -> None:
    respuesta = client.put(
        "/api/v1/plan",
        json={
            "exam_date": (date.today() + timedelta(weeks=8)).isoformat(),
            "hours_per_week": 20,
            "rest_days": [6],
        },
    )

    assert respuesta.status_code == 404, respuesta.text


def test_el_plan_guardado_se_vuelve_a_leer_con_su_progreso(client: TestClient) -> None:
    _programa(client)
    exam_date = date.today() + timedelta(weeks=8, days=1)

    guardado = client.put(
        "/api/v1/plan",
        json={
            "exam_date": exam_date.isoformat(),
            "hours_per_week": 40,
            "rest_days": [6],
        },
    )

    assert guardado.status_code == 200, guardado.text
    plan = guardado.json()
    assert plan["modo"] == "extensivo"
    assert plan["temas_por_semana"] == 1
    assert plan["total_semanas"] == 8
    assert plan["semanas_de_lectura"] == 4
    assert plan["fase_2_desde"] == 5
    assert plan["dentro"] == ["III.1", "III.2"]
    assert [semana["fase"] for semana in plan["semanas"]][4:] == ["fase-2"] * 4

    # El calendario que se pide al volver a entrar es el mismo que devolvio el PUT.
    calendario = client.get("/api/v1/plan/calendario")
    assert calendario.status_code == 200
    assert calendario.json() == plan

    progreso = client.get("/api/v1/plan/progreso")
    assert progreso.status_code == 200, progreso.text
    cuerpo = progreso.json()
    assert cuerpo["total"] == 2
    assert cuerpo["leidos"] == 0
    assert [bloque["codigo"] for bloque in cuerpo["bloques"]] == ["III"]


def test_los_repasos_que_caen_en_la_fase_2_se_dicen_en_el_calendario(client: TestClient) -> None:
    _programa(client)

    respuesta = client.put(
        "/api/v1/plan",
        json={
            "exam_date": (date.today() + timedelta(weeks=8, days=1)).isoformat(),
            "hours_per_week": 40,
            "rest_days": [6],
        },
    )
    assert respuesta.status_code == 200, respuesta.text
    semanas = respuesta.json()["semanas"]

    # Ninguna tarea de lectura o repaso se cuela en la fase 2.
    for semana in semanas[4:]:
        assert all(tarea["tipo"] in ("supuesto", "simulacro") for tarea in semana["tareas"]), semana

    # El +7 del tema leido en la primera semana no se puede programar: la semana 1 lo dice.
    recortes = " ".join(semanas[0]["recortes"])
    assert "fase 2" in recortes
    assert "III.1" in recortes
    assert "+7" in recortes
