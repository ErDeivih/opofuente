"""Pruebas de integración de la telemetría propia del despliegue de demo.

Lo que se comprueba, en el mismo orden en que lo promete el contrato:

1. un `page_view` suma y el resumen lo cuenta por pantalla;
2. una pantalla fuera de la lista blanca se rechaza con 422 y no crea una pantalla nueva;
3. el mensaje de un error se recorta, se le quitan las rutas absolutas y el resumen no guarda
   ningún campo de contenido;
4. el cuerpo de la petición está acotado y el mensaje guardado nunca pasa de 200 caracteres.
"""

from __future__ import annotations

from fastapi.testclient import TestClient
from httpx import Response

from opofuente.api.errors import PROBLEM_MEDIA_TYPE

EVENTS = "/api/v1/telemetry/events"
SUMMARY = "/api/v1/telemetry/summary"


def _event(
    client: TestClient,
    event_type: str,
    screen: str,
    message: str | None = None,
) -> Response:
    payload: dict[str, object] = {"type": event_type, "screen": screen}
    if message is not None:
        payload["message"] = message
    return client.post(EVENTS, json=payload)


def test_page_view_incrementa_y_el_resumen_cuenta_por_pantalla(
    api_only_client: TestClient,
) -> None:
    assert _event(api_only_client, "page_view", "inicio").status_code == 202
    assert _event(api_only_client, "page_view", "inicio").status_code == 202
    assert _event(api_only_client, "page_view", "bandeja").status_code == 202

    response = api_only_client.get(SUMMARY)
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 3
    assert body["by_type"] == {"page_view": 3, "error": 0}
    assert body["by_screen"]["inicio"] == 2
    assert body["by_screen"]["bandeja"] == 1
    assert body["by_screen"]["temario"] == 0
    assert body["recent_errors"] == []


def test_pantalla_desconocida_se_rechaza_con_422(api_only_client: TestClient) -> None:
    response = api_only_client.post(EVENTS, json={"type": "page_view", "screen": "inventada"})

    assert response.status_code == 422
    assert response.headers["content-type"].startswith(PROBLEM_MEDIA_TYPE)
    problem = response.json()
    assert problem["code"] == "validation_error"
    assert any(error["field"].endswith("screen") for error in problem["field_errors"])

    # Un nombre inventado no se contabiliza ni aparece en el resumen.
    summary = api_only_client.get(SUMMARY)
    assert summary.json()["total"] == 0
    assert "inventada" not in summary.text


def test_el_error_recorta_el_mensaje_y_no_guarda_contenido(api_only_client: TestClient) -> None:
    mensaje = "No se pudo abrir C:\\Users\\David\\datos\\documento.pdf y la lectura falló"
    response = api_only_client.post(
        EVENTS,
        json={
            "type": "error",
            "screen": "biblioteca",
            "message": mensaje,
            # Campo fuera del contrato: no puede acabar en el resumen.
            "content": "texto privado del documento",
        },
    )

    assert response.status_code == 202
    summary = api_only_client.get(SUMMARY).json()
    assert summary["total"] == 1
    assert summary["by_type"]["error"] == 1
    assert summary["by_screen"]["biblioteca"] == 1

    assert len(summary["recent_errors"]) == 1
    error = summary["recent_errors"][0]
    # Ni contenido ni datos de la conexión: exactamente los tres campos documentados.
    assert set(error) == {"screen", "message", "at"}
    assert error["screen"] == "biblioteca"
    assert "C:\\" not in error["message"]
    assert "Users" not in error["message"]
    assert "[ruta]" in error["message"]
    # El contenido que la web nunca manda tampoco se guarda si llega colado.
    assert "texto privado" not in str(summary)


def test_limita_el_payload_y_la_longitud_del_mensaje(api_only_client: TestClient) -> None:
    # Un mensaje largo se acepta (202) pero solo se guardan 200 caracteres.
    accepted = _event(api_only_client, "error", "errores", "x" * 1500)
    assert accepted.status_code == 202
    summary = api_only_client.get(SUMMARY).json()
    assert len(summary["recent_errors"][0]["message"]) == 200

    # La ventana de errores recientes está acotada: nunca crece por encima de 20.
    for _ in range(25):
        assert _event(api_only_client, "error", "errores", "fallo corto").status_code == 202
    assert len(api_only_client.get(SUMMARY).json()["recent_errors"]) == 20

    # Un cuerpo por encima del límite se rechaza sin contarse.
    total_antes = api_only_client.get(SUMMARY).json()["total"]
    oversized = b'{"type": "page_view", "screen": "inicio"} ' + b"x" * 5000
    response = api_only_client.post(
        EVENTS,
        content=oversized,
        headers={"content-type": "application/json"},
    )
    assert response.status_code == 413
    assert response.headers["content-type"].startswith(PROBLEM_MEDIA_TYPE)
    assert response.json()["code"] == "payload_too_large"
    assert api_only_client.get(SUMMARY).json()["total"] == total_antes
