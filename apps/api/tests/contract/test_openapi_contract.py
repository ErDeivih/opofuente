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
from pathlib import Path
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
    "/api/v1/oppositions",
    "/api/v1/oppositions/{opposition_id}",
    "/api/v1/oppositions/{opposition_id}/activate",
    "/api/v1/oppositions/{opposition_id}/convocations",
    "/api/v1/convocations/{convocation_id}",
    "/api/v1/convocations/{convocation_id}/activate",
    "/api/v1/convocations/{convocation_id}/curriculum",
    "/api/v1/curriculum-nodes/{node_id}",
    "/api/v1/inventories",
    "/api/v1/inventories/{inventory_id}",
    "/api/v1/inventories/{inventory_id}/confirm-import",
    "/api/v1/ingestion-batches",
    "/api/v1/ingestion-batches/{batch_id}",
    "/api/v1/ingestion-batches/{batch_id}/cancel",
    "/api/v1/ingestion-batches/{batch_id}/pause",
    "/api/v1/ingestion-batches/{batch_id}/resume",
    "/api/v1/ingestion-batches/{batch_id}/retry",
    "/api/v1/ingestion-batches/{batch_id}/items",
    "/api/v1/ingestion-batches/{batch_id}/issues",
    "/api/v1/ingestion-batches/{batch_id}/report",
    "/api/v1/jobs",
    "/api/v1/jobs/{job_id}",
    "/api/v1/jobs/{job_id}/cancel",
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
        for method, operation in schema["paths"][path].items():
            responses = operation["responses"]
            assert "500" in responses, f"{method.upper()} {path} no documenta el 500"
            content = responses["500"]["content"]
            assert set(content) == {PROBLEM_MEDIA_TYPE}, (
                f"{method.upper()} {path} documenta el 500 con otro media type"
            )
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


def test_el_422_se_documenta_con_el_cuerpo_que_se_sirve(schema: dict[str, Any]) -> None:
    """DEBT-002: FastAPI documentaría `HTTPValidationError`, que no es lo que devolvemos.

    Al declarar el 422 en cada ruta, el contrato publica `ProblemDetail` (con `field_errors`) bajo
    `application/problem+json`, que es exactamente el cuerpo del manejador de validación.
    """
    assert "HTTPValidationError" not in json.dumps(schema), (
        "el contrato no debe documentar HTTPValidationError: el cuerpo real es ProblemDetail"
    )
    for path in ("/api/v1/oppositions/{opposition_id}", "/api/v1/curriculum-nodes/{node_id}"):
        responses = schema["paths"][path]["get"]["responses"]
        assert "422" in responses, f"{path} debería documentar el 422"
        content = responses["422"]["content"]
        assert set(content) == {PROBLEM_MEDIA_TYPE}
        assert content[PROBLEM_MEDIA_TYPE]["schema"]["$ref"].endswith("/ProblemDetail")
    assert "field_errors" in schema["components"]["schemas"]["ProblemDetail"]["properties"]


def test_la_primera_ruta_de_escritura_documenta_el_403(schema: dict[str, Any]) -> None:
    """El 403 lo produce el middleware de Origin y solo afecta a métodos de escritura."""
    responses = schema["paths"]["/api/v1/oppositions/{opposition_id}/activate"]["post"]["responses"]
    assert "403" in responses
    content = responses["403"]["content"]
    assert set(content) == {PROBLEM_MEDIA_TYPE}
    assert content[PROBLEM_MEDIA_TYPE]["schema"]["$ref"].endswith("/ProblemDetail")

    # Una ruta de solo lectura no documenta un 403 que no puede ocurrir.
    read_responses = schema["paths"]["/api/v1/oppositions/{opposition_id}"]["get"]["responses"]
    assert "403" not in read_responses


def test_la_activacion_de_convocatoria_documenta_su_conflicto(schema: dict[str, Any]) -> None:
    """Elegir la convocatoria vigente puede rechazarse por estado: el contrato lo declara.

    El resto de escrituras de perfil no produce 409, así que no lo documentan: documentar un error
    que no ocurre es prometer algo que la interfaz tendría que gestionar sin motivo.
    """
    responses = schema["paths"]["/api/v1/convocations/{convocation_id}/activate"]["post"][
        "responses"
    ]
    assert set(responses) >= {"200", "404", "409", "422", "403"}
    content = responses["409"]["content"]
    assert set(content) == {PROBLEM_MEDIA_TYPE}
    assert content[PROBLEM_MEDIA_TYPE]["schema"]["$ref"].endswith("/ProblemDetail")

    otras = schema["paths"]["/api/v1/oppositions/{opposition_id}/activate"]["post"]["responses"]
    assert "409" not in otras
    # Y devuelve la convocatoria, no el árbol: el selector de la interfaz solo necesita su fila.
    ok = responses["200"]["content"]["application/json"]["schema"]
    assert ok["$ref"].endswith("/ConvocationReferenceSchema")


def test_las_rutas_de_perfil_documentan_el_404(schema: dict[str, Any]) -> None:
    for path in (
        "/api/v1/oppositions/{opposition_id}",
        "/api/v1/oppositions/{opposition_id}/convocations",
        "/api/v1/convocations/{convocation_id}",
        "/api/v1/convocations/{convocation_id}/curriculum",
        "/api/v1/curriculum-nodes/{node_id}",
    ):
        responses = schema["paths"][path]["get"]["responses"]
        assert "404" in responses, path
        assert responses["404"]["content"][PROBLEM_MEDIA_TYPE]["schema"]["$ref"].endswith(
            "/ProblemDetail"
        )


def test_el_programa_documenta_su_estructura(schema: dict[str, Any]) -> None:
    node = schema["components"]["schemas"]["CurriculumNodeSchema"]
    assert set(node["properties"]) >= {
        "id",
        "node_type",
        "official_code",
        "title",
        "position",
        "path",
        "depth",
        "children",
    }
    assert schema["components"]["schemas"]["NodeType"]["enum"] == ["block", "topic", "epigraph"]


def test_el_nodo_declara_que_la_cobertura_no_existe_todavia(schema: dict[str, Any]) -> None:
    """La cobertura llega en S05: el contrato no puede prometer un cálculo que no se hace."""
    properties = schema["components"]["schemas"]["CurriculumNodeDetailSchema"]["properties"]
    assert "coverage" in properties
    # El contrato la declara nula, no como un número que la interfaz pudiera mostrar como cero.
    assert properties["coverage"]["type"] == "null"


def test_el_404_servido_cumple_el_esquema_documentado(
    seeded_client: TestClient, schema: dict[str, Any]
) -> None:
    """El esquema y el cuerpo real tienen que coincidir también en los errores de S01."""
    problem = schema["components"]["schemas"]["ProblemDetail"]
    response = seeded_client.get("/api/v1/curriculum-nodes/no-existe")

    assert response.status_code == 404
    assert response.headers["content-type"].startswith(PROBLEM_MEDIA_TYPE)
    for field in problem["required"]:
        assert field in response.json(), field


def test_el_422_servido_cumple_el_esquema_documentado(
    api_only_client: TestClient, schema: dict[str, Any]
) -> None:
    """DEBT-002: un 422 real (no inventado) comparado con el esquema documentado.

    S02 trae las primeras rutas con cuerpo y parámetros validados, así que ya existe una petición
    que produce un 422 de verdad: se comprueba el cuerpo servido campo a campo, incluido
    `field_errors`, que es lo que hasta ahora solo estaba documentado.
    """
    problem = schema["components"]["schemas"]["ProblemDetail"]
    field_error = schema["components"]["schemas"]["FieldError"]

    cuerpo = api_only_client.post("/api/v1/inventories", json={"source_path": ""})
    assert cuerpo.status_code == 422
    assert cuerpo.headers["content-type"].startswith(PROBLEM_MEDIA_TYPE)
    body = cuerpo.json()
    for field in problem["required"]:
        assert field in body, field
    assert body["code"] == "validation_error"
    assert body["instance"] == "/api/v1/inventories"
    assert body["field_errors"], "un 422 debe decir qué campo falla"
    for error in body["field_errors"]:
        assert set(error) == set(field_error["properties"]), error
        assert error["field"] == "body.source_path"

    # El mismo manejador cubre los parámetros de consulta de una ruta de lectura.
    lista = api_only_client.get("/api/v1/ingestion-batches?limit=0")
    assert lista.status_code == 422
    assert lista.json()["code"] == "validation_error"
    assert {error["field"] for error in lista.json()["field_errors"]} == {"query.limit"}


def test_la_respuesta_de_programa_cumple_el_esquema(seeded_client: TestClient) -> None:
    oppositions = seeded_client.get("/api/v1/oppositions").json()
    convocation_id = next(
        item["active_convocation"]["id"] for item in oppositions if item["active"]
    )
    body = seeded_client.get(f"/api/v1/convocations/{convocation_id}/curriculum").json()

    assert set(body) == {"convocation_id", "convocation_code", "opposition_code", "counts", "nodes"}
    assert body["counts"] == {"block": 4, "topic": 33, "epigraph": 0}
    primer_nodo = body["nodes"][0]
    assert set(primer_nodo) >= {"id", "node_type", "official_code", "title", "path", "depth"}


def test_las_rutas_de_ingestion_estan_documentadas(schema: dict[str, Any]) -> None:
    """S02: inventario, lotes y trabajos con sus errores, y sin prometer lo que no existe."""
    inventario = schema["paths"]["/api/v1/inventories"]["post"]
    assert "400" in inventario["responses"], "una carpeta no utilizable debe documentar el 400"
    assert "403" in inventario["responses"], "una escritura debe documentar el rechazo por Origin"
    for status in ("400", "403", "422", "500"):
        content = inventario["responses"][status]["content"]
        assert set(content) == {PROBLEM_MEDIA_TYPE}
        assert content[PROBLEM_MEDIA_TYPE]["schema"]["$ref"].endswith("/ProblemDetail")

    # S03 estrena las tres entradas del MVP: ficheros, texto pegado y URL. Cada una documenta sus
    # errores reales, incluido el 400 de contenido rechazado por seguridad.
    for ruta in (
        "/api/v1/ingestion-batches/files",
        "/api/v1/ingestion-batches/paste",
        "/api/v1/ingestion-batches/url",
    ):
        operacion = schema["paths"][ruta]["post"]
        assert "400" in operacion["responses"], f"{ruta} debe documentar el 400"
        assert "403" in operacion["responses"], (
            f"{ruta} es una escritura: documenta el rechazo por Origin"
        )
        for status in ("400", "403", "422", "500"):
            content = operacion["responses"][status]["content"]
            assert set(content) == {PROBLEM_MEDIA_TYPE}, ruta
            assert content[PROBLEM_MEDIA_TYPE]["schema"]["$ref"].endswith("/ProblemDetail"), ruta

    # El lector: representaciones del lote y texto por trozos, con la calidad y los avisos.
    representaciones = schema["paths"]["/api/v1/ingestion-batches/{batch_id}/representations"][
        "get"
    ]
    assert "404" in representaciones["responses"]
    texto = schema["paths"]["/api/v1/representations/{representation_id}/text"]["get"]
    assert "404" in texto["responses"]
    esquema_texto = schema["components"]["schemas"]["RepresentationTextSchema"]
    assert set(esquema_texto["required"]) >= {
        "representation_id",
        "text",
        "offset",
        "limit",
        "total_chars",
        "truncated",
        "quality",
    }

    # Lo que S03 sigue sin implementar no se documenta: un botón falso es peor que una ausencia.
    for ausente in ("/api/v1/events",):
        assert ausente not in schema["paths"], ausente


def test_reintentar_documenta_el_409(schema: dict[str, Any]) -> None:
    """Reintentar solo vale para un lote fallido o cancelado, y eso se documenta.

    Un lote en cola, trabajando o terminado responde 409 `invalid_state`: devolver entradas a la
    cola mientras el worker trabaja sobre ellas descuadraría el informe y copiaría dos veces.
    """
    responses = schema["paths"]["/api/v1/ingestion-batches/{batch_id}/retry"]["post"]["responses"]
    assert "409" in responses
    content = responses["409"]["content"]
    assert set(content) == {PROBLEM_MEDIA_TYPE}
    assert content[PROBLEM_MEDIA_TYPE]["schema"]["$ref"].endswith("/ProblemDetail")

    # Y el 409 es exclusivo de reintentar: cancelar un lote terminado no falla, devuelve su estado.
    cancel = schema["paths"]["/api/v1/ingestion-batches/{batch_id}/cancel"]["post"]["responses"]
    assert "409" not in cancel, "cancelar no rechaza por estado del lote"
    assert "404" in cancel and "403" in cancel


def test_el_409_servido_cumple_el_esquema_documentado(
    api_only_client: TestClient, schema: dict[str, Any], tmp_path: Path
) -> None:
    """El cuerpo real del 409 es el del contrato, con su código y su identificador."""
    problem = schema["components"]["schemas"]["ProblemDetail"]
    material = tmp_path / "material"
    material.mkdir()
    (material / "tema.txt").write_text("contenido", encoding="utf-8")

    inventario = api_only_client.post(
        "/api/v1/inventories", json={"source_path": str(material)}
    ).json()
    # Sin worker, el lote se queda en cola: reintentarlo no tiene sentido y debe rechazarse.
    batch = api_only_client.post(
        f"/api/v1/inventories/{inventario['batch']['id']}/confirm-import"
    ).json()

    response = api_only_client.post(f"/api/v1/ingestion-batches/{batch['id']}/retry")

    assert response.status_code == 409
    assert response.headers["content-type"].startswith(PROBLEM_MEDIA_TYPE)
    body = response.json()
    for field in problem["required"]:
        assert field in body, field
    assert body["code"] == "invalid_state"


def test_el_informe_del_lote_documenta_su_cuadre(schema: dict[str, Any]) -> None:
    schema_informe = schema["components"]["schemas"]["ImportReportSchema"]
    assert set(schema_informe["properties"]) >= {
        "batch_id",
        "kind",
        "status",
        "counters",
        "issue_counts",
        "balanced",
        "artifacts_total",
    }
    assert "balanced" in schema_informe["required"]


def test_el_inventario_declara_que_no_copia_nada(schema: dict[str, Any]) -> None:
    propiedades = schema["components"]["schemas"]["InventorySchema"]["properties"]
    assert "copied_anything" in propiedades
    assert propiedades["copied_anything"]["type"] == "boolean"
    # La ruta real de origen no se publica: solo la versión abreviada.
    batch = schema["components"]["schemas"]["BatchSchema"]["properties"]
    assert "source_path_display" in batch
    assert "source_root" not in batch


def _patron(camino: str) -> re.Pattern[str]:
    """El patrón con el que FastAPI compara una ruta: sus parámetros son un segmento cualquiera."""
    return re.compile("^" + re.sub(r"\{[^}]+\}", "[^/]+", camino) + "$")


def _rutas_tapadas(rutas: list[str]) -> list[str]:
    """Rutas literales que una ruta anterior con parámetros se lleva por delante."""
    tapadas: list[str] = []
    for indice, camino in enumerate(rutas):
        if "{" in camino:  # una ruta con parámetros no puede quedar tapada
            continue
        for anterior in rutas[:indice]:
            if "{" in anterior and _patron(anterior).match(camino):
                tapadas.append(f"{camino} (la sirve {anterior})")
                break
    return tapadas


def test_el_guarda_de_rutas_detecta_una_tapada() -> None:
    """La prueba de abajo solo vale si sabe fallar: se comprueba con el caso real que la motivó."""
    assert _rutas_tapadas(["/api/v1/reviews/{review_id}", "/api/v1/reviews/mastery"]) == [
        "/api/v1/reviews/mastery (la sirve /api/v1/reviews/{review_id})"
    ]
    assert _rutas_tapadas(["/api/v1/reviews/mastery", "/api/v1/reviews/{review_id}"]) == []


def test_ninguna_ruta_literal_queda_tapada_por_una_con_parametro() -> None:
    """FastAPI resuelve por orden: lo literal va antes que lo parametrizado (ADR-018).

    Se recorren las rutas **en el orden en que están registradas** y, por cada ruta sin parámetros,
    se comprueba que ninguna anterior con parámetros encaje con ella. Encontrado en S12.2:
    `/reviews/mastery` estaba declarada detrás de `/reviews/{review_id}`, así que la aplicación
    pedía el dominio por tema y recibía el 404 de «no existe repaso con ese identificador» —la
    columna de dominio del Programa nunca llegó a servirse—. Ni las pruebas unitarias de la
    interfaz (que simulan `fetch`) ni las E2E (que no miraban esa columna) podían verlo.
    """
    from opofuente.config import Settings
    from opofuente.main import create_app

    app = create_app(Settings(data_dir=Path(".") / "no-se-usa", _env_file=None))
    rutas = [
        ruta
        for ruta in (getattr(route, "path", "") for route in app.routes)
        if ruta.startswith("/api/v1")
    ]

    assert _rutas_tapadas(rutas) == []
