"""Pruebas unitarias del ajuste del esquema OpenAPI (media type de los errores)."""

from __future__ import annotations

from typing import Any

from opofuente.api.openapi import JSON_MEDIA_TYPE, PROBLEM_MEDIA_TYPE, apply_problem_media_type


def _schema_con(respuestas: dict[str, Any]) -> dict[str, Any]:
    return {
        "openapi": "3.1.0",
        "paths": {"/recurso": {"get": {"responses": respuestas}}},
    }


def test_mueve_el_esquema_de_error_al_media_type_real() -> None:
    schema = _schema_con(
        {
            "503": {
                "content": {JSON_MEDIA_TYPE: {"schema": {"$ref": "#/components/schemas/Problema"}}},
                "description": "no listo",
            }
        }
    )
    resultado = apply_problem_media_type(schema)
    content = resultado["paths"]["/recurso"]["get"]["responses"]["503"]["content"]
    assert set(content) == {PROBLEM_MEDIA_TYPE}
    assert content[PROBLEM_MEDIA_TYPE]["schema"]["$ref"].endswith("/Problema")


def test_no_toca_las_respuestas_correctas() -> None:
    schema = _schema_con(
        {"200": {"content": {JSON_MEDIA_TYPE: {"schema": {"$ref": "#/components/schemas/Bien"}}}}}
    )
    resultado = apply_problem_media_type(schema)
    content = resultado["paths"]["/recurso"]["get"]["responses"]["200"]["content"]
    assert set(content) == {JSON_MEDIA_TYPE}


def test_no_pisa_un_esquema_ya_documentado_como_problema() -> None:
    schema = _schema_con(
        {
            "503": {
                "content": {
                    PROBLEM_MEDIA_TYPE: {"schema": {"$ref": "#/components/schemas/Problema"}}
                }
            }
        }
    )
    resultado = apply_problem_media_type(schema)
    content = resultado["paths"]["/recurso"]["get"]["responses"]["503"]["content"]
    assert set(content) == {PROBLEM_MEDIA_TYPE}


def test_es_idempotente() -> None:
    schema = _schema_con(
        {"503": {"content": {JSON_MEDIA_TYPE: {"schema": {"$ref": "#/components/schemas/P"}}}}}
    )
    una_vez = apply_problem_media_type(schema)
    dos_veces = apply_problem_media_type(una_vez)
    assert una_vez == dos_veces


def test_tolera_esquemas_incompletos() -> None:
    assert apply_problem_media_type({}) == {}
    assert apply_problem_media_type({"paths": {"/x": {"get": {}}}})["paths"]["/x"]["get"] == {}
