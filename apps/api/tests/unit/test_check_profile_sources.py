"""Comprobador del estado de las fuentes de perfiles (DEBT-028), sin red ni base de datos.

La puerta 17 tiene que poder distinguir tres situaciones: fuentes que faltan (bloquea), fuentes que
cambiaron en origen (se omite la verificación de perfiles con motivo) y fuentes que coinciden (se
verifica todo). Esta prueba fija esa tabla de decisión con ficheros temporales.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from opofuente.tools.build_profile_fixtures import Source
from opofuente.tools.check_profile_sources import evaluate_sources


def _source(tmp_path: Path, identificador: str, contenido: bytes) -> Source:
    ruta = tmp_path / f"{identificador}.bin"
    ruta.write_bytes(contenido)
    return Source(
        id=identificador,
        local_path=ruta,
        sha256=hashlib.sha256(contenido).hexdigest(),
        role="prueba",
        profile_code="tai-age-2025",
    )


def test_si_todo_coincide_no_bloquea(tmp_path: Path) -> None:
    fuentes = [_source(tmp_path, "uno", b"contenido")]
    estados, codigo = evaluate_sources(fuentes)

    assert codigo == 0
    assert [estado.state for estado in estados] == ["ok"]


def test_una_fuente_que_cambio_se_informa_pero_no_bloquea(tmp_path: Path) -> None:
    fuente = _source(tmp_path, "uno", b"contenido")
    ruta = tmp_path / "uno.bin"
    ruta.write_bytes(b"contenido cambiado en origen")

    estados, codigo = evaluate_sources([fuente])

    assert codigo == 2, "el drift se omite con motivo, no se trata como fallo"
    assert estados[0].state == "drifted"
    assert estados[0].expected_sha256 == fuente.sha256
    assert estados[0].actual_sha256 != fuente.sha256


def test_una_fuente_que_falta_bloquea(tmp_path: Path) -> None:
    fuente = _source(tmp_path, "uno", b"contenido")
    (tmp_path / "uno.bin").unlink()

    estados, codigo = evaluate_sources([fuente])

    assert codigo == 1, "sin la fuente no se puede verificar; esto sí bloquea"
    assert estados[0].state == "missing"


def test_si_falta_una_y_otra_cambio_gana_el_bloqueo(tmp_path: Path) -> None:
    primera = _source(tmp_path, "uno", b"contenido")
    segunda = _source(tmp_path, "dos", b"otro contenido")
    (tmp_path / "uno.bin").unlink()
    (tmp_path / "dos.bin").write_bytes(b"cambiado")

    _estados, codigo = evaluate_sources([primera, segunda])

    assert codigo == 1
