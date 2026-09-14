"""Pruebas de seguridad: Origin, cabeceras, correlación y errores sin rutas.

Se prueban los middlewares ASGI directamente, con una aplicación mínima que sí acepta POST,
porque en S00 el contrato todavía no tiene endpoints de escritura.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient as FastApiTestClient
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from opofuente.api.errors import PROBLEM_MEDIA_TYPE
from opofuente.api.middleware import (
    SECURITY_HEADERS,
    CorrelationIdMiddleware,
    OriginCheckMiddleware,
    SecurityHeadersMiddleware,
)

ALLOWED_ORIGIN = "http://127.0.0.1:5173"


async def _create_thing(_request: Any) -> JSONResponse:
    return JSONResponse({"ok": True}, status_code=201)


async def _list_things(_request: Any) -> JSONResponse:
    return JSONResponse({"items": []}, status_code=200)


def _write_app() -> Starlette:
    app = Starlette(
        routes=[
            Route("/things", _create_thing, methods=["POST"]),
            Route("/things", _list_things, methods=["GET"]),
        ]
    )
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(OriginCheckMiddleware, allowed_origins=(ALLOWED_ORIGIN,))
    app.add_middleware(CorrelationIdMiddleware)
    return app


@pytest.fixture
def write_client() -> Iterator[TestClient]:
    with TestClient(_write_app()) as client:
        yield client


def test_post_con_origen_ajeno_se_rechaza(write_client: TestClient) -> None:
    response = write_client.post("/things", headers={"Origin": "http://malicioso.example"})
    assert response.status_code == 403
    assert response.headers["content-type"].startswith(PROBLEM_MEDIA_TYPE)
    body = response.json()
    assert body["code"] == "forbidden_origin"
    assert body["status"] == 403
    assert body["correlation_id"]
    assert response.headers["x-correlation-id"] == body["correlation_id"]


def test_post_con_origen_autorizado_se_acepta(write_client: TestClient) -> None:
    response = write_client.post("/things", headers={"Origin": ALLOWED_ORIGIN})
    assert response.status_code == 201


def test_post_sin_cabecera_origen_se_acepta(write_client: TestClient) -> None:
    # Herramientas locales (curl, scripts) no envían Origin; no hay credenciales que robar.
    assert write_client.post("/things").status_code == 201


def test_lectura_con_origen_ajeno_no_se_bloquea(write_client: TestClient) -> None:
    # La comprobación de Origin es una defensa CSRF: solo afecta a métodos de escritura.
    response = write_client.get("/things", headers={"Origin": "http://otro.example"})
    assert response.status_code == 200


def test_cabeceras_de_seguridad_en_la_api(client: FastApiTestClient) -> None:
    response = client.get("/api/v1/health/live")
    for header, expected in SECURITY_HEADERS.items():
        assert response.headers[header] == expected


def test_identificador_de_correlacion_devuelto(client: FastApiTestClient) -> None:
    response = client.get("/api/v1/health/live")
    assert response.headers["x-correlation-id"]

    explicit = client.get("/api/v1/health/live", headers={"X-Correlation-ID": "prueba-123"})
    assert explicit.headers["x-correlation-id"] == "prueba-123"


def test_error_404_en_formato_problem_sin_rutas(client: FastApiTestClient) -> None:
    response = client.get("/api/v1/no-existe")
    assert response.status_code == 404
    assert response.headers["content-type"].startswith(PROBLEM_MEDIA_TYPE)
    body = response.json()
    assert body["instance"] == "/api/v1/no-existe"
    assert body["code"] == "not_found"
    assert "F:\\" not in response.text
    assert "\\\\" not in response.text


def test_cors_solo_para_origenes_locales(client: FastApiTestClient) -> None:
    allowed = client.get(
        "/api/v1/health/live",
        headers={"Origin": "http://127.0.0.1:5173"},
    )
    assert allowed.headers.get("access-control-allow-origin") == "http://127.0.0.1:5173"

    rejected = client.get(
        "/api/v1/health/live",
        headers={"Origin": "http://malicioso.example"},
    )
    assert "access-control-allow-origin" not in rejected.headers
