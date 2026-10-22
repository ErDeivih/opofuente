"""La invitacion, de punta a punta (M8).

**Lo que se afirma aqui es lo que hace que una invitacion sea una invitacion**
y no un enlace que se puede reenviar:

1. **canjearla crea la cuenta**;
2. **canjearla otra vez falla**: un solo uso;
3. **canjearla con otro correo falla**: vale para una direccion y no para otra;
4. **una caducada no canjea**;
5. **y el token no esta guardado en la base**: lo que se guarda es su hash.

**El punto 5 es el que mas importa y el que menos se nota**: si el token
estuviera en la tabla, quien la leyera podria invitar a quien quisiera.
"""

from __future__ import annotations

import hashlib
import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from opofuente.config import Settings
from opofuente.tools.canjear import canjear
from opofuente.tools.invitar import crear

CONTRASENA = "contrasena-larga-1"


@pytest.fixture()
def base(migrated_settings: Settings, seeded_client: TestClient) -> Path:
    """La base **migrada por el propio fixture**, que si la publica.

    **Las rondas anteriores fallaban por esto**: `get_settings()` devuelve la
    base del repositorio y ademas esta memorizada, asi que el test no tenia
    forma de llegar a la que el fixture migro. **Depender de
    `migrated_settings` da la ruta de verdad**, sin tocar el entorno.
    """
    return Path(migrated_settings.data_paths.database)


def test_canjear_crea_la_cuenta_y_no_se_puede_repetir(base: Path) -> None:
    """El caso bueno, y el segundo intento."""
    token, _caduca = crear("amigo@ejemplo.test", ruta=str(base))
    bien, que = canjear(token, "amigo@ejemplo.test", CONTRASENA, ruta=str(base))
    assert bien is True, que
    assert "creada" in que

    otra_vez, motivo = canjear(token, "amigo@ejemplo.test", CONTRASENA, ruta=str(base))
    assert otra_vez is False
    assert "ya se uso" in motivo


def test_el_token_no_esta_guardado_en_la_base(base: Path) -> None:
    """**Lo que se guarda es el hash**: el token en claro no aparece."""
    token, _caduca = crear("amigo@ejemplo.test", ruta=str(base))
    conexion = sqlite3.connect(base)
    try:
        guardados = [
            fila[0] for fila in conexion.execute("select token_hash from account_invitations")
        ]
    finally:
        conexion.close()
    assert token not in guardados
    assert hashlib.sha256(token.encode("utf-8")).hexdigest() in guardados


def test_otra_direccion_no_canjea(base: Path) -> None:
    """El enlace vale para quien se invito y no para otro."""
    token, _caduca = crear("amigo@ejemplo.test", ruta=str(base))
    bien, motivo = canjear(token, "otro@ejemplo.test", CONTRASENA, ruta=str(base))
    assert bien is False
    assert "otra direccion" in motivo


def test_una_caducada_no_canjea(base: Path) -> None:
    """**Una invitacion que no caduca no es una invitacion.**"""
    hace_dos_semanas = datetime.now(UTC) - timedelta(days=14)
    token, _ = crear("amigo@ejemplo.test", ahora=hace_dos_semanas, ruta=str(base))
    bien, motivo = canjear(token, "amigo@ejemplo.test", CONTRASENA, ruta=str(base))
    assert bien is False
    assert "caducado" in motivo


def test_un_token_inventado_no_canjea(base: Path) -> None:
    """Y el mensaje no distingue: **no confirma que el enlace exista**."""
    bien, motivo = canjear("token-que-no-existe", "amigo@ejemplo.test", CONTRASENA, ruta=str(base))
    assert bien is False
    assert "no existe" in motivo
