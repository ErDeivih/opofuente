"""Lo que está fuera del temario no entra en un simulacro ni en un examen oficial (F4).

El examen de TAI se parece al examen real: la normativa y la organización propias de otra
administración no caen en él. Por eso una pregunta declarada fuera de temario se queda fuera de
**estos dos modos** y no de los demás: en un test por tema y en los apuntes sí cuenta, porque ahí
es material para estudiar.

Lo que se prueba, y con las dos rutas de composición que existen hoy:

1. el conjunto tiene 81 ordinarias (una más de las 80 del examen) y 5 reservas; se declara **fuera
   de temario** la **primera** de las ordinarias, que es la que entraría por orden del documento;
2. el simulacro y el examen oficial se montan **igual** (80 + 5) sin ella: entra la 81, la que
   estaba de más. No se pierde el examen, se cambia una pregunta por la siguiente;
3. sin la marca, esa misma pregunta sí entra y la 81 no: la prueba no puede pasar por casualidad.
"""

from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient

from opofuente.config import Settings

ALLOWED_ORIGIN = {"Origin": "http://127.0.0.1:5173"}


def _texto(preguntas: int, *, reservas: int = 0) -> str:
    lineas: list[str] = []
    for numero in range(1, preguntas + reservas + 1):
        marca = "[R] " if numero > preguntas else ""
        lineas.append(
            f"{numero}. {marca}El supuesto practico numero {numero} se resuelve en diez dias:"
        )
        for indice in range(4):
            lineas.append(f"{chr(ord('a') + indice)}) Opcion {chr(ord('A') + indice)}")
        lineas.append("Respuesta correcta: a")
        lineas.append("")
    return "\n".join(lineas)


def _conjunto(client: TestClient, *, preguntas: int, reservas: int) -> dict[str, Any]:
    oposiciones = client.get("/api/v1/oppositions").json()
    activa = next(oposicion for oposicion in oposiciones if oposicion["active"])
    creado = client.post(
        "/api/v1/question-sets",
        json={
            "title": "Examen con una pregunta fuera de temario",
            "opposition_id": activa["id"],
            "set_type": "private_bank",
            "convocation_version_id": activa["active_convocation"]["id"],
        },
        headers=ALLOWED_ORIGIN,
    )
    assert creado.status_code == 201, creado.text
    conjunto = dict(creado.json())
    importado = client.post(
        f"/api/v1/question-sets/{conjunto['id']}/parse",
        json={"kind": "questions", "text": _texto(preguntas, reservas=reservas)},
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


def _preguntas(client: TestClient, set_id: str) -> list[dict[str, Any]]:
    listado = client.get(f"/api/v1/question-sets/{set_id}/questions", params={"limit": 200}).json()
    return list(listado["questions"])


def _marcar_fuera_de_temario(client: TestClient, pregunta_id: str) -> None:
    respuesta = client.post(
        "/api/v1/questions/topics/bulk",
        json={
            "actor": "llm:deepseek-flash",
            "assignments": [
                {
                    "question_version_id": pregunta_id,
                    "exclusion_reason": "otra_administracion",
                    "reason": "ley autonómica de otra administración",
                }
            ],
        },
        headers=ALLOWED_ORIGIN,
    )
    assert respuesta.status_code == 200, respuesta.text
    assert respuesta.json()["results"][0]["outcome"] == "excluded"


def _montar(client: TestClient, set_id: str, *, modo: str) -> dict[str, Any]:
    oposiciones = client.get("/api/v1/oppositions").json()
    activa = next(oposicion for oposicion in oposiciones if oposicion["active"])
    respuesta = client.post(
        "/api/v1/study-sessions",
        json={
            "opposition_id": activa["id"],
            "mode": modo,
            "sources": [{"question_set_id": set_id, "part_code": "primera_parte"}],
        },
        headers=ALLOWED_ORIGIN,
    )
    assert respuesta.status_code == 201, respuesta.text
    return dict(respuesta.json())


def _ids_de_la_sesion(client: TestClient, session_id: str) -> list[str]:
    revision = client.get(f"/api/v1/study-sessions/{session_id}/review").json()
    return [entrada["question_version_id"] for entrada in revision["entries"]]


def test_una_pregunta_fuera_de_temario_no_entra_ni_en_el_simulacro_ni_en_el_examen_oficial(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """81 ordinarias y 5 reservas: la excluida se queda fuera y entra la 81 en su lugar.

    Se excluye la **primera** a propósito: es la que entraría por orden del documento, así que si el
    filtro no estuviera, esta prueba fallaría por partida doble (estaría ella y no estaría la 81).
    """
    conjunto = _conjunto(seeded_client, preguntas=81, reservas=5)
    preguntas = _preguntas(seeded_client, conjunto["id"])
    ordinarias = [pregunta for pregunta in preguntas if not pregunta["is_reserve"]]
    assert len(ordinarias) == 81
    excluida, de_mas = ordinarias[0], ordinarias[-1]
    _marcar_fuera_de_temario(seeded_client, excluida["id"])

    for modo in ("mock_exam", "official_exam"):
        sesion = _montar(seeded_client, conjunto["id"], modo=modo)

        assert sesion["total_questions"] == 85, f"{modo}: 80 ordinarias y sus 5 reservas"
        ids = _ids_de_la_sesion(seeded_client, sesion["id"])
        assert excluida["id"] not in ids, f"{modo}: una pregunta fuera de temario no es del examen"
        assert len(ids) == 85, f"{modo}: el examen se monta con las que quedan, sin quedarse corto"
        assert de_mas["id"] in ids, f"{modo}: ocupa su hueco la que estaba de más"


def test_sin_la_marca_esa_misma_pregunta_si_entraria(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """La prueba de que el filtro es el que excluye: sin marca, entra la primera y no la 81."""
    conjunto = _conjunto(seeded_client, preguntas=81, reservas=5)
    preguntas = _preguntas(seeded_client, conjunto["id"])
    ordinarias = [pregunta for pregunta in preguntas if not pregunta["is_reserve"]]
    primera, de_mas = ordinarias[0], ordinarias[-1]

    sesion = _montar(seeded_client, conjunto["id"], modo="mock_exam")

    ids = _ids_de_la_sesion(seeded_client, sesion["id"])
    assert primera["id"] in ids, "sin marca, la pregunta 1 es de las 80 que entran"
    assert de_mas["id"] not in ids, "y la 81 se queda fuera: no hay hueco para ella"
