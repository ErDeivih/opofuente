"""Pruebas unitarias de configuración (capa sin framework)."""

from __future__ import annotations

from pathlib import Path

import pytest

from opofuente.config import Settings, project_root
from opofuente.domain.errors import ConfigurationError
from opofuente.domain.providers import (
    DataDestination,
    classify_provider,
    sends_content_off_device,
)


def test_host_no_loopback_falla() -> None:
    with pytest.raises(ConfigurationError):
        # S104: la IP comodín se usa a propósito para comprobar que se rechaza.
        Settings(host="0.0.0.0", _env_file=None)  # noqa: S104


def test_host_loopback_alternativos_aceptados() -> None:
    assert Settings(host="127.0.0.1", _env_file=None).host == "127.0.0.1"
    assert Settings(host="LOCALHOST", _env_file=None).host == "localhost"
    assert Settings(host=" ::1 ", _env_file=None).host == "::1"


def test_data_dir_relativo_se_resuelve_contra_la_raiz(tmp_path: Path) -> None:
    settings = Settings(data_dir="data", _env_file=None)
    assert settings.data_dir == (project_root() / "data").resolve()
    assert settings.data_paths.database.name == "opofuente.sqlite3"


def test_data_dir_absoluto_se_respeta(tmp_path: Path) -> None:
    settings = Settings(data_dir=tmp_path / "otro", _env_file=None)
    assert settings.data_dir == (tmp_path / "otro").resolve()


def test_data_dir_que_es_fichero_falla(tmp_path: Path) -> None:
    fichero = tmp_path / "no-soy-un-directorio"
    fichero.write_text("x", encoding="utf-8")
    with pytest.raises(ConfigurationError):
        Settings(data_dir=fichero, _env_file=None)


def test_proveedor_llm_exige_endpoint() -> None:
    with pytest.raises(ConfigurationError):
        Settings(llm_provider="ollama", _env_file=None)
    with pytest.raises(ConfigurationError):
        Settings(llm_provider="openai_compatible", llm_model="gpt-local", _env_file=None)


def test_proveedor_llm_completo_es_valido() -> None:
    settings = Settings(
        llm_provider="openai_compatible",
        llm_base_url="http://127.0.0.1:11434/v1",
        llm_model="modelo-local",
        _env_file=None,
    )
    assert settings.llm_provider == "openai_compatible"
    # DEBT-001, corregido en S12: un endpoint en loopback **no** saca los datos del equipo. Antes
    # esta prueba afirmaba lo contrario porque el booleano no miraba el endpoint: ese era el fallo.
    assert settings.llm_destination.destination is DataDestination.LOCAL
    assert sends_content_off_device(settings.llm_destination) is False


def test_un_endpoint_remoto_si_saca_los_datos_del_equipo() -> None:
    """La clasificación mira el endpoint efectivo: el nombre del proveedor no decide nada."""
    remoto = Settings(
        llm_provider="ollama",
        llm_base_url="https://modelos.ejemplo.test/v1",
        llm_model="modelo",
        _env_file=None,
    )
    local = Settings(
        llm_provider="ollama",
        llm_base_url="http://192.168.1.50:11434",
        llm_model="modelo",
        _env_file=None,
    )

    assert remoto.llm_destination.destination is DataDestination.REMOTE
    assert local.llm_destination.destination is DataDestination.LOCAL


def test_embedding_local_sin_endpoint_no_se_presenta_como_local() -> None:
    """Un proveedor configurado sin endpoint es `unknown`, y `unknown` cuenta como que sí sale."""
    settings = Settings(
        embedding_provider="openai_compatible",
        embedding_model="modelo",
        _env_file=None,
    )

    assert settings.embeddings_destination.destination is DataDestination.UNKNOWN
    assert sends_content_off_device(settings.embeddings_destination) is True, (
        "sin endpoint no se puede afirmar que sea local"
    )


def test_el_destino_de_cada_proveedor_se_clasifica_aparte() -> None:
    """DEBT-001: el destino de los embeddings no se informa dentro del bloque del lenguaje."""
    llm = classify_provider(name="el modelo de lenguaje", provider="disabled", endpoint=None)
    embeddings = classify_provider(
        name="el proveedor de embeddings",
        provider="openai_compatible",
        endpoint="https://embeddings.ejemplo.test/v1",
    )

    assert llm.destination is DataDestination.DISABLED
    assert embeddings.destination is DataDestination.REMOTE
    assert "tercero" in embeddings.reason


def test_por_defecto_no_sale_datos_del_equipo() -> None:
    settings = Settings(_env_file=None)
    assert settings.llm_provider == "disabled"
    assert settings.embedding_provider == "disabled"
    assert settings.llm_destination.destination is DataDestination.DISABLED
    assert settings.embeddings_destination.destination is DataDestination.DISABLED


def test_clave_nunca_se_serializa() -> None:
    settings = Settings(
        llm_provider="openai_compatible",
        llm_base_url="http://127.0.0.1:11434/v1",
        llm_model="modelo-local",
        llm_api_key="clave-secreta-de-prueba",
        _env_file=None,
    )
    assert settings.llm_api_key_configured is True
    assert "clave-secreta-de-prueba" not in settings.model_dump_json()
    assert "clave-secreta-de-prueba" not in repr(settings)


def test_cadenas_vacias_se_convierten_en_none() -> None:
    settings = Settings(tesseract_path="", llm_model="", _env_file=None)
    assert settings.tesseract_path is None
    assert settings.llm_model is None
