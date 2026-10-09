"""La lectura de las respuestas del modelo en los apuntes (pasos B, D y E), sin red.

Lo que se prueba aquí es lo que hace que una corrida larga no se pierda por una respuesta mal
formada:
se lee **elemento a elemento** —lo que se puede sostener entra, lo que no se descarta— y los tokens
se
copian del sobre para que el informe pueda decir lo que costó.
"""

from __future__ import annotations

import json
from typing import Any

import pytest

from opofuente.domain.errors import ExternalServiceError
from opofuente.domain.topic_notes import FactKind
from opofuente.infrastructure.topic_notes_client import (
    DeepSeekNotesModel,
    read_comprobacion,
    read_hechos,
    read_redaccion,
)


def _sobre(
    contenido: dict[str, Any], *, entrada: int = 1200, salida: int = 300, cache: int = 900
) -> str:
    """El sobre de una respuesta de la API compatible con OpenAI, con su `usage`."""
    return json.dumps(
        {
            "choices": [{"message": {"content": json.dumps(contenido)}}],
            "usage": {
                "prompt_tokens": entrada,
                "completion_tokens": salida,
                "prompt_cache_hit_tokens": cache,
            },
        }
    )


# --- paso B: los hechos ---------------------------------------------------------------------------


def test_los_hechos_se_leen_con_sus_tokens_y_su_rastro() -> None:
    lote = read_hechos(
        _sobre(
            {
                "hechos": [
                    {
                        "id": "firma-1",
                        "epigrafe": "IV.7.1",
                        "dudosa": False,
                        "motivo": None,
                        "hechos": [
                            {"texto": "El modelo OSI tiene siete capas.", "tipo": "tecnico"},
                            {"texto": "El modelo TCP/IP tiene cuatro niveles.", "tipo": "tecnico"},
                        ],
                    }
                ]
            }
        ),
        requested=["firma-1"],
    )
    assert len(lote.hechos) == 2
    assert lote.hechos[0].kind is FactKind.TECNICO
    assert lote.hechos[0].source_groups == ("firma-1",)
    assert lote.input_tokens == 1200 and lote.output_tokens == 300 and lote.cache_hit_tokens == 900
    assert lote.sin_hechos == ()


def test_un_hecho_con_la_clave_señalada_se_lee_como_dudoso_y_con_su_motivo() -> None:
    lote = read_hechos(
        _sobre(
            {
                "hechos": [
                    {
                        "id": "firma-1",
                        "epigrafe": "I.1.2",
                        "dudosa": True,
                        "motivo": "la plantilla dice 1976 y la Constitución es de 1978",
                        "hechos": [
                            {"texto": "La Constitución Española es de 1978.", "tipo": "normativo"}
                        ],
                    }
                ]
            }
        ),
        requested=["firma-1"],
    )
    assert lote.hechos[0].doubtful is True
    assert "1978" in (lote.hechos[0].note or "")
    assert lote.hechos[0].kind is FactKind.NORMATIVO


def test_lo_que_no_se_puede_sostener_se_descarta_sin_perder_el_lote() -> None:
    """Un hecho sin texto, sin epígrafe o con un id que no se preguntó no entra; el resto, sí."""
    lote = read_hechos(
        _sobre(
            {
                "hechos": [
                    {"id": "otra-firma", "epigrafe": "IV.7.1", "hechos": [{"texto": "No es mío."}]},
                    {"id": "firma-1", "epigrafe": None, "hechos": [{"texto": "Sin epígrafe."}]},
                    {"id": "firma-1", "epigrafe": "IV.7.1", "hechos": [{"texto": "   "}]},
                    {
                        "id": "firma-1",
                        "epigrafe": "IV.7.1",
                        "hechos": [{"texto": "Este sí vale.", "tipo": "normativo"}],
                    },
                ]
            }
        ),
        requested=["firma-1"],
    )
    assert [hecho.text for hecho in lote.hechos] == ["Este sí vale."]


def test_un_lote_sin_la_lista_de_hechos_es_un_fallo_del_proveedor() -> None:
    with pytest.raises(ExternalServiceError):
        read_hechos(_sobre({"otra_cosa": []}), requested=["firma-1"])
    with pytest.raises(ExternalServiceError):
        read_hechos("no es json", requested=["firma-1"])


# --- paso D: la redacción -------------------------------------------------------------------------


def test_la_redaccion_se_lee_con_su_titulo() -> None:
    lote = read_redaccion(_sobre({"titulo": "Modelo OSI", "markdown": "## Capas\n\nSiete."}))
    assert lote.titulo == "Modelo OSI"
    assert lote.markdown.startswith("## Capas")
    assert lote.input_tokens == 1200


def test_un_apartado_sin_texto_es_un_fallo_y_no_se_guarda_vacio() -> None:
    with pytest.raises(ExternalServiceError):
        read_redaccion(_sobre({"titulo": "Sin texto", "markdown": "  "}))


# --- paso E: la comprobación ----------------------------------------------------------------------


def test_la_comprobacion_lee_la_letra_y_la_frase_y_marca_lo_que_no_esta() -> None:
    lote = read_comprobacion(
        _sobre(
            {
                "respuestas": [
                    {
                        "id": "firma-1",
                        "letra": "B)",
                        "frase": "siete capas del modelo OSI",
                    },
                    {"id": "firma-2", "letra": "a", "frase": "NO ESTÁ"},
                    {"id": "firma-3", "letra": None, "frase": "tampoco la encuentro"},
                ]
            }
        ),
        requested=["firma-1", "firma-2", "firma-3", "firma-4"],
    )
    por_firma = {check.group_signature: check for check in lote.checks}
    assert por_firma["firma-1"].letter == "b", "la letra se normaliza"
    assert por_firma["firma-1"].quote == "siete capas del modelo OSI"
    assert por_firma["firma-2"].quote is None, "«NO ESTÁ» no es una cita"
    assert por_firma["firma-3"].letter is None, "una letra que no es una letra no decide"
    assert lote.sin_respuesta == ("firma-4",), "lo que el modelo no contestó se cuenta"


# --- el cliente -----------------------------------------------------------------------------------


def test_el_cliente_exige_clave_y_direccion() -> None:
    from opofuente.domain.errors import ConfigurationError

    with pytest.raises(ConfigurationError):
        DeepSeekNotesModel(api_key="  ")
    with pytest.raises(ConfigurationError):
        DeepSeekNotesModel(api_key="clave", base_url="no-es-una-url")


def test_el_cliente_monta_el_endpoint_compatible_con_openai() -> None:
    cliente = DeepSeekNotesModel(
        api_key="clave", model="deepseek-flash", base_url="https://api.deepseek.com/v1"
    )
    assert cliente.version == "deepseek-flash"
    assert cliente.name == "deepseek"
