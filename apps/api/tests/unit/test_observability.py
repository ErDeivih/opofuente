"""Pruebas unitarias del registro de logs y de su saneado."""

from __future__ import annotations

import json
import logging

from opofuente.infrastructure.correlation import reset_correlation_id, set_correlation_id
from opofuente.infrastructure.observability import SAFE_EXTRA_KEYS, JsonFormatter


def _formatter() -> JsonFormatter:
    return JsonFormatter(service="opofuente", version="0.0.0-test")


def test_formato_json_basico() -> None:
    record = logging.LogRecord(
        name="opofuente.test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="evento de prueba",
        args=(),
        exc_info=None,
    )
    payload = json.loads(_formatter().format(record))
    assert payload["message"] == "evento de prueba"
    assert payload["level"] == "INFO"
    assert payload["service"] == "opofuente"
    assert payload["version"] == "0.0.0-test"


def test_campos_extra_desconocidos_se_descartan() -> None:
    record = logging.LogRecord(
        name="opofuente.test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="evento",
        args=(),
        exc_info=None,
    )
    record.document_text = "TEXTO-PRIVADO-DEL-USUARIO"
    record.api_key = "clave-secreta"
    rendered = _formatter().format(record)
    assert "TEXTO-PRIVADO-DEL-USUARIO" not in rendered
    assert "clave-secreta" not in rendered


def test_campos_extra_permitidos_se_incluyen() -> None:
    record = logging.LogRecord(
        name="opofuente.test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="petición",
        args=(),
        exc_info=None,
    )
    record.method = "GET"
    record.path = "/api/v1/health/live"
    record.status_code = 200
    payload = json.loads(_formatter().format(record))
    assert payload["method"] == "GET"
    assert payload["status_code"] == 200
    assert "probe" in SAFE_EXTRA_KEYS


def test_identificador_de_correlacion_se_incluye() -> None:
    token = set_correlation_id("corr-123")
    try:
        record = logging.LogRecord(
            name="opofuente.test",
            level=logging.INFO,
            pathname=__file__,
            lineno=1,
            msg="evento",
            args=(),
            exc_info=None,
        )
        payload = json.loads(_formatter().format(record))
    finally:
        reset_correlation_id(token)
    assert payload["correlation_id"] == "corr-123"


def test_excepcion_registra_solo_el_tipo() -> None:
    try:
        raise ValueError("detalle interno con /ruta/absoluta/privada")
    except ValueError:
        import sys

        record = logging.LogRecord(
            name="opofuente.test",
            level=logging.ERROR,
            pathname=__file__,
            lineno=1,
            msg="fallo",
            args=(),
            exc_info=sys.exc_info(),
        )
    rendered = _formatter().format(record)
    payload = json.loads(rendered)
    assert payload["exception"] == "ValueError"
    assert "/ruta/absoluta/privada" not in rendered
