"""Pruebas de contrato: el esquema OpenAPI commiteado y los tipos derivados.

OpenAPI es la fuente de verdad (08_API-CONTRACT §13). Si la API cambia y el contrato no, esta
prueba falla e indica el comando exacto que hay que ejecutar.

El 503 de `/health/ready` se comprueba en las dos direcciones: que está documentado con su
esquema (`ReadinessProblem` con `checks`) y que el cuerpo que se sirve de verdad cumple ese
esquema. Así el frontend puede consumir el tipo generado en lugar de adivinar la forma.
"""

from __future__ import annotations

import json
import re
from typing import Any

import pytest
from fastapi.testclient import TestClient

from opofuente.api.openapi import PROBLEM_MEDIA_TYPE
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

PROBLEM_FIELDS = ("type", "title", "status", "detail", "instance", "code", "correlation_id")

SECRET_PROPERTY = re.compile(r"(^|_)(api_key|secret|password|token|credential)$")


def _component_name(ref: str) -> str:
    return ref.rsplit("/", 1)[-1]


def _component(schema: dict[str, Any], ref: str) -> dict[str, Any]:
    name = _component_name(ref)
    assert name in schema["components"]["schemas"], f"falta el componente {name}"
    return schema["components"]["schemas"][name]


@pytest.fixture(scope="module")
def schema() -> dict[str, Any]:
    return json.loads(render_schema())


@pytest.fixture(scope="module")
def ready_503(schema: dict[str, Any]) -> dict[str, Any]:
    return schema["paths"]["/api/v1/health/ready"]["get"]["responses"]["503"]


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
    for tipo in ("ReadinessProblem", "CheckSchema", "CapabilitiesSchema"):
        assert tipo in contenido, f"El tipo {tipo} no está en los tipos derivados"


def test_rutas_del_contrato_presentes(schema: dict[str, Any]) -> None:
    for path in REQUIRED_PATHS:
        assert path in schema["paths"], path


def test_problem_detail_incluye_code_y_correlation_id(schema: dict[str, Any]) -> None:
    """El contrato base del problema sigue en el esquema: es el tipo de cualquier error."""
    properties = schema["components"]["schemas"]["ProblemDetail"]["properties"]
    for field in PROBLEM_FIELDS:
        assert field in properties, field
    assert "field_errors" in properties


def test_todas_las_rutas_documentan_el_error_interno_con_el_mismo_esquema(
    schema: dict[str, Any],
) -> None:
    for path in REQUIRED_PATHS:
        responses = schema["paths"][path]["get"]["responses"]
        assert "500" in responses, f"{path} no documenta el 500"
        content = responses["500"]["content"]
        assert set(content) == {PROBLEM_MEDIA_TYPE}, f"{path} documenta el 500 con otro media type"
        assert content[PROBLEM_MEDIA_TYPE]["schema"]["$ref"].endswith("/ProblemDetail")


def test_ready_503_esta_documentado_como_problem_json(ready_503: dict[str, Any]) -> None:
    """El media type documentado debe ser el que se sirve de verdad."""
    content = ready_503["content"]
    assert set(content) == {PROBLEM_MEDIA_TYPE}, (
        f"El 503 debe documentarse solo como {PROBLEM_MEDIA_TYPE}, no como {sorted(content)}"
    )
    assert "$ref" in content[PROBLEM_MEDIA_TYPE]["schema"]


def test_ready_503_documenta_checks_con_su_propio_esquema(
    schema: dict[str, Any], ready_503: dict[str, Any]
) -> None:
    """Si `checks` desaparece del esquema del 503, esta prueba falla."""
    ref = ready_503["content"][PROBLEM_MEDIA_TYPE]["schema"]["$ref"]
    readiness_problem = _component(schema, ref)

    # El 503 describe el problema RFC 9457 completo...
    for field in PROBLEM_FIELDS:
        assert field in readiness_problem["properties"], f"el 503 no documenta {field}"

    # ...y el detalle de cada comprobación, con esquema propio (no una extensión sin tipo).
    checks = readiness_problem["properties"]["checks"]
    assert checks["type"] == "array"
    assert "$ref" in checks["items"]
    assert _component_name(checks["items"]["$ref"]) == "CheckSchema"
    assert "checks" in readiness_problem.get("required", []), "`checks` debe ser obligatorio"

    check_properties = _component(schema, checks["items"]["$ref"])["properties"]
    for field in ("name", "status", "detail"):
        assert field in check_properties, f"CheckSchema no documenta {field}"


def test_cuerpo_servido_del_503_cumple_el_esquema_documentado(
    unmigrated_client: TestClient, schema: dict[str, Any], ready_503: dict[str, Any]
) -> None:
    """El esquema no basta: el cuerpo real tiene que coincidir con lo documentado."""
    documented = _component(schema, ready_503["content"][PROBLEM_MEDIA_TYPE]["schema"]["$ref"])
    check_schema = _component(schema, documented["properties"]["checks"]["items"]["$ref"])

    response = unmigrated_client.get("/api/v1/health/ready")

    assert response.status_code == 503
    assert response.headers["content-type"].startswith(PROBLEM_MEDIA_TYPE)
    body = response.json()

    for field in documented["required"]:
        assert field in body, f"el cuerpo servido no incluye {field}"
    assert isinstance(body["checks"], list)
    assert body["checks"], "el 503 debe explicar qué comprobación falló"
    for check in body["checks"]:
        assert set(check) == set(check_schema["properties"]), "comprobación fuera del contrato"
        assert check["status"] in {"ok", "failed"}


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
