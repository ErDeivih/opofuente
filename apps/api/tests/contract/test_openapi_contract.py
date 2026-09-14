"""Pruebas de contrato: el esquema OpenAPI commiteado y los tipos derivados.

OpenAPI es la fuente de verdad (08_API-CONTRACT §13). Si la API cambia y el contrato no, esta
prueba falla e indica el comando exacto que hay que ejecutar.
"""

from __future__ import annotations

import json
import re
from typing import Any

import pytest

from opofuente.config import project_root
from opofuente.tools.export_openapi import render_schema

CONTRACT_PATH = project_root() / "packages" / "contracts" / "openapi.json"
TYPES_PATH = project_root() / "packages" / "contracts" / "src" / "openapi.d.ts"

REQUIRED_PATHS = (
    "/api/v1/health/live",
    "/api/v1/health/ready",
    "/api/v1/capabilities",
    "/api/v1/settings",
)

SECRET_PROPERTY = re.compile(r"(^|_)(api_key|secret|password|token|credential)$")


@pytest.fixture(scope="module")
def schema() -> dict[str, Any]:
    return json.loads(render_schema())


def test_contrato_commiteado_esta_sincronizado(schema: dict[str, Any]) -> None:
    assert CONTRACT_PATH.is_file(), (
        "Falta packages/contracts/openapi.json. Ejecuta: "
        "uv run python -m opofuente.tools.export_openapi"
    )
    assert CONTRACT_PATH.read_text(encoding="utf-8") == render_schema(), (
        "El contrato commiteado no coincide con la API. Ejecuta: "
        "uv run python -m opofuente.tools.export_openapi && npm run contracts:generate"
    )


def test_tipos_typescript_derivados_existen() -> None:
    assert TYPES_PATH.is_file(), "Faltan los tipos derivados. Ejecuta: npm run contracts:generate"
    contenido = TYPES_PATH.read_text(encoding="utf-8")
    assert "/api/v1/capabilities" in contenido


def test_rutas_del_contrato_presentes(schema: dict[str, Any]) -> None:
    for path in REQUIRED_PATHS:
        assert path in schema["paths"], path


def test_ready_documenta_el_error_503_como_problem_json(schema: dict[str, Any]) -> None:
    responses = schema["paths"]["/api/v1/health/ready"]["get"]["responses"]
    assert "503" in responses
    assert "application/problem+json" in responses["503"]["content"]


def test_problem_detail_incluye_code_y_correlation_id(schema: dict[str, Any]) -> None:
    properties = schema["components"]["schemas"]["ProblemDetail"]["properties"]
    for field in ("type", "title", "status", "detail", "instance", "code", "correlation_id"):
        assert field in properties, field
    assert "field_errors" in properties


def test_ninguna_respuesta_documenta_secretos(schema: dict[str, Any]) -> None:
    schemas = schema["components"]["schemas"]
    for name in ("CapabilitiesSchema", "SettingsSchema", "LlmSettingsSchema"):
        properties = schemas[name]["properties"]
        for property_name in properties:
            assert not SECRET_PROPERTY.search(property_name), f"{name}.{property_name}"
    # La única traza de la clave es un booleano que indica si está configurada.
    assert "api_key_configured" in schemas["LlmSettingsSchema"]["properties"]


def test_capabilities_documenta_estados_reales(schema: dict[str, Any]) -> None:
    status_enum = schema["components"]["schemas"]["CapabilityStatus"]["enum"]
    assert status_enum == [
        "enabled",
        "disabled",
        "unavailable",
        "configured_unverified",
        "planned",
    ]
