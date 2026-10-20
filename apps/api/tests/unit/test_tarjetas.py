"""De un hecho a una tarjeta: solo cuando la forma es regular (M3 de la fase 3)."""

from __future__ import annotations

import pytest

from opofuente.domain.tarjetas import tarjeta_estructural


def test_puerto_a_servicio() -> None:
    tarjeta = tarjeta_estructural(
        "El puerto 137 corresponde al servicio NetBIOS Name Service y el 139 a NetBIOS Session."
    )
    assert tarjeta is not None
    assert tarjeta.anverso == "¿Qué servicio corresponde al puerto 137?"
    assert tarjeta.reverso == "NetBIOS Name Service"


def test_servicio_a_puerto() -> None:
    tarjeta = tarjeta_estructural("El protocolo NTP utiliza el puerto 123 en UDP.")
    assert tarjeta is not None
    assert tarjeta.anverso == "¿Qué puerto utiliza El protocolo NTP?"
    assert tarjeta.reverso == "123"


@pytest.mark.parametrize(
    "texto",
    [
        "La Constitución se aprobó en 1978.",
        "El puerto de SMTPS es el 465.",
        "",
    ],
)
def test_lo_que_no_encaja_no_se_convierte_en_tarjeta(texto: str) -> None:
    assert tarjeta_estructural(texto) is None


def test_un_reverso_no_arrastra_el_dato_siguiente() -> None:
    tarjeta = tarjeta_estructural(
        "el puerto 25 corresponde al servicio SMTP y el 587 al envío autenticado"
    )
    assert tarjeta is not None
    assert "587" not in tarjeta.reverso
