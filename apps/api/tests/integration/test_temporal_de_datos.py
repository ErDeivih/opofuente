"""El temporal del árbol de datos: si no se puede escribir, se dice y se cae al de repuesto (§6).

**El hecho que lo motiva, medido en este equipo**: `datos\\tmp` es un enlace a
`E:\\OpoFuente-archivo\\datos-tmp`, de los 41,6 GB que se movieron para liberar `F:`. Si `E:` no
está
conectado, el temporal configurado **existe en el nombre y no en los hechos**: se puede listar y no
se
puede escribir. Sin esta comprobación, lo que falla a media operación es la importación de un
artefacto, la instantánea antes de una copia y la restauración —es decir, lo peor posible: páginas
que
cargan y acciones que no—.

**Cómo se simula la ausencia sin desenchufar `E:`.** Apuntando el temporal a una ruta que no se
puede
escribir. En Windows, un directorio que no se puede usar se consigue de dos formas: una ruta cuyo
padre
es un **fichero** (no se puede crear el directorio debajo) o una ruta absoluta de una unidad que no
existe. Se usa la primera, que no depende de qué unidades haya en la máquina que ejecute la suite.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from opofuente.config import Settings, resolve_tmp_directory, writable_directory_problem
from opofuente.domain.errors import ConfigurationError
from opofuente.main import create_app


def test_un_directorio_normal_se_puede_escribir(tmp_path: Path) -> None:
    assert writable_directory_problem(tmp_path / "cualquiera") is None


def test_un_temporal_imposible_se_detecta_escribiendo(tmp_path: Path) -> None:
    """La comprobación escribe de verdad, y por eso ve lo que `exists()` no ve.

    Se prepara el caso exacto que motivó esto: una ruta que *parece* un directorio y en la que no se
    puede escribir, porque su padre es un fichero. `Path.exists()` sobre ella contesta que no existe
    y
    el programa seguiría adelante contento; la sonda, no.
    """
    imposible = tmp_path / "un-fichero" / "tmp"
    (tmp_path / "un-fichero").write_text("no soy un directorio", encoding="utf-8")

    problema = writable_directory_problem(imposible)

    assert problema is not None, "escribir ahí tiene que fallar y decirse"
    assert ":" in problema or "Error" in problema or "error" in problema


def test_si_el_temporal_no_vale_se_usa_el_de_repuesto(tmp_path: Path) -> None:
    """El de repuesto vive en el **mismo árbol** que la base: misma unidad, siempre disponible."""
    datos = tmp_path / "datos"
    datos.mkdir()
    (datos / "tmp").write_text("aquí no se puede escribir: es un fichero", encoding="utf-8")
    ajustes = Settings(data_dir=datos, worker_enabled=False, _env_file=None)

    decision = resolve_tmp_directory(ajustes.data_paths)

    assert decision.fallback_used is True
    assert decision.nothing_writable is False
    assert decision.paths.tmp == datos / "_tmp"
    assert decision.paths.tmp.exists()
    assert "no admite escritura" in decision.detail
    assert "repuesto" in decision.detail


def test_la_aplicacion_arranca_con_el_temporal_de_repuesto_y_lo_dice(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """**Ejecutado, no prometido**: con el temporal roto, la aplicación arranca y lo cuenta.

    Y arranca **usando** el de repuesto, que es lo que hace que siga funcionando de verdad: el
    servicio de copias y el almacén de artefactos apuntan al mismo `paths.tmp` que se decidió aquí.
    """
    datos = tmp_path / "datos"
    datos.mkdir()
    (datos / "tmp").write_text("roto", encoding="utf-8")
    ajustes = Settings(data_dir=datos, worker_enabled=False, _env_file=None)

    with caplog.at_level("INFO"), TestClient(create_app(ajustes)) as cliente:
        assert cliente.get("/api/v1/health/live").status_code == 200
        assert cliente.app.state.tmp_decision.fallback_used is True
        assert cliente.app.state.tmp_decision.paths.tmp == datos / "_tmp"

    avisos = [
        registro for registro in caplog.records if getattr(registro, "event", "") == "tmp_fallback"
    ]
    assert avisos, "el arranque tiene que decir que ha cambiado de temporal"
    assert "no admite escritura" in avisos[0].getMessage()


def test_sin_ningun_temporal_escribible_no_se_arranca_a_medias(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """Si no vale ninguno de los dos, el arranque **falla** con la ruta y qué hacer.

    No se arranca «a medias»: un proceso que acepta peticiones sabiendo que la mitad de sus
    escrituras
    van a fallar es peor que uno que no arranca, porque el fallo aparece lejos de su causa.
    """
    datos = tmp_path / "datos"
    datos.mkdir()
    (datos / "tmp").write_text("roto", encoding="utf-8")
    (datos / "_tmp").write_text("también roto", encoding="utf-8")
    ajustes = Settings(data_dir=datos, worker_enabled=False, _env_file=None)

    with (
        caplog.at_level("ERROR"),
        pytest.raises(ConfigurationError) as error,
        TestClient(create_app(ajustes)),
    ):
        pass

    mensaje = str(error.value)
    assert "no hay ningún temporal escribible" in mensaje
    assert "tmp" in mensaje and "_tmp" in mensaje, "el mensaje tiene que dar las dos rutas"

    errores = [registro for registro in caplog.records if registro.levelname == "ERROR"]
    assert errores, "además de fallar, hay que decirlo en el registro del arranque"
    aviso = errores[0].getMessage()
    assert "unidad" in aviso, "y decir qué puede pasar (la unidad del temporal)"
    assert "datos\\tmp" in aviso or "datos/tmp" in aviso, "con la ruta exacta que falla"


def test_la_configuracion_de_un_temporal_normal_no_cambia_nada(tmp_path: Path) -> None:
    """Sin nada roto, el temporal es el de siempre: cero cambios para quien ya usa esto."""
    datos = tmp_path / "datos"
    datos.mkdir()
    ajustes = Settings(data_dir=datos, worker_enabled=False, _env_file=None)

    decision = resolve_tmp_directory(ajustes.data_paths)

    assert decision.fallback_used is False
    assert decision.nothing_writable is False
    assert decision.paths.tmp == datos / "tmp"
    assert decision.paths == ajustes.data_paths, "los caminos tienen que ser los mismos que antes"
