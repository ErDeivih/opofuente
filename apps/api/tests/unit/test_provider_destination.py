"""Pruebas de la clasificación del destino de datos por proveedor (DEBT-001, criterio 2).

El defecto que cerró esta deuda era de **información**: la aplicación decía que el contenido salía
del equipo cuando el endpoint era este mismo equipo, y metía el destino de los embeddings dentro del
bloque del modelo de lenguaje. Aquí se comprueba la clasificación que lo arregla, caso por caso, y
la regla conservadora que la acompaña: lo que no se puede determinar **no** se presenta como local.
"""

from __future__ import annotations

import pytest

from opofuente.config import Settings
from opofuente.domain.providers import (
    DataDestination,
    classify_endpoint,
    classify_provider,
    sends_content_off_device,
)


@pytest.mark.parametrize(
    "endpoint",
    [
        "http://127.0.0.1:11434/v1",
        "http://localhost:1234/v1",
        "https://LOCALHOST:8080",
        "http://[::1]:11434/v1",
        "http://10.0.0.5:8000",
        "http://192.168.1.20:8000/v1",
        "http://172.16.4.9:8000",
        "http://169.254.10.10:8000",
    ],
)
def test_un_endpoint_de_este_equipo_o_de_la_red_privada_es_local(endpoint: str) -> None:
    clasificado = classify_endpoint(endpoint)

    assert clasificado.destination is DataDestination.LOCAL
    assert sends_content_off_device(clasificado) is False, "no sale: no se avisa de que sale"


@pytest.mark.parametrize(
    "endpoint",
    [
        "https://api.openai.com/v1",
        "https://generativelanguage.googleapis.com/v1beta",
        "http://8.8.8.8:8000",
        "http://172.32.0.1:8000",
    ],
)
def test_un_endpoint_de_fuera_es_remoto(endpoint: str) -> None:
    clasificado = classify_endpoint(endpoint)

    assert clasificado.destination is DataDestination.REMOTE
    assert sends_content_off_device(clasificado) is True
    assert clasificado.endpoint is not None and "://" not in clasificado.endpoint, (
        "el motivo nombra el host, no la URL entera"
    )


@pytest.mark.parametrize("endpoint", [None, "", "   ", "no-es-una-url", "ftp://ejemplo.test/x"])
def test_lo_que_no_se_puede_determinar_es_unknown_y_no_local(endpoint: str | None) -> None:
    clasificado = classify_endpoint(endpoint)

    if endpoint is None or not endpoint.strip():
        assert clasificado.destination is DataDestination.DISABLED
        assert sends_content_off_device(clasificado) is False
        return
    assert clasificado.destination is DataDestination.UNKNOWN
    assert sends_content_off_device(clasificado) is True, "unknown cuenta como que sí sale"


def test_el_nombre_y_el_endpoint_viajan_en_el_motivo() -> None:
    """El motivo es lo que la pantalla enseña al lado, así que tiene que explicar el caso."""
    local = classify_endpoint("http://127.0.0.1:11434")
    remoto = classify_endpoint("https://api.openai.com/v1")

    assert "loopback" in local.reason
    assert "tercero" in remoto.reason
    assert remoto.endpoint == "api.openai.com"


def test_un_proveedor_desactivado_no_es_un_destino() -> None:
    """`disabled` es «no hay proveedor»: no se confunde con «no sale del equipo»."""
    clasificado = classify_provider(
        name="el modelo de lenguaje", provider="disabled", endpoint=None
    )

    assert clasificado.destination is DataDestination.DISABLED
    assert "no está configurado" in clasificado.reason


def test_un_proveedor_activo_sin_endpoint_es_unknown() -> None:
    """Está configurado y no se sabe a dónde iría: no se adivina que es local."""
    clasificado = classify_provider(
        name="el proveedor de embeddings",
        provider="openai_compatible",
        endpoint=None,
    )

    assert clasificado.destination is DataDestination.UNKNOWN
    assert "no declara endpoint" in clasificado.reason
    assert sends_content_off_device(clasificado) is True


def test_cada_proveedor_tiene_su_destino_y_no_se_mezclan() -> None:
    """El defecto registrado: el destino de los embeddings se informaba dentro del del lenguaje.

    Con el endpoint del modelo en loopback y el de embeddings remoto, cada uno dice lo suyo —y el
    modelo **no** aparece como que envía a un tercero—.
    """
    settings = Settings(
        data_dir=".",
        _env_file=None,
        llm_provider="ollama",
        llm_base_url="http://127.0.0.1:11434/v1",
        llm_model="llama3.2",
        embedding_provider="openai_compatible",
        embedding_base_url="https://api.openai.com/v1",
        embedding_model="text-embedding-3-small",
    )

    assert settings.llm_destination.destination is DataDestination.LOCAL
    assert settings.embeddings_destination.destination is DataDestination.REMOTE
    assert sends_content_off_device(settings.llm_destination) is False
    assert sends_content_off_device(settings.embeddings_destination) is True
