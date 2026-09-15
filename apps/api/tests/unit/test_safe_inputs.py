"""Pruebas de las defensas frente a entrada no confiable (DEBT-004).

Todas son **negativas**: comprueban que el ataque se rechaza, no que el caso feliz funcione. Un
ZIP con traversal, un ZIP bomba, un XML con entidades externas, una URL a red interna o una
redirección hacia ella tienen que fallar con un error propio y sin tocar nada fuera de su sitio.
"""

from __future__ import annotations

import io
import zipfile
from pathlib import Path

import pytest

from opofuente.domain.errors import UnsafeContentError, UrlRejectedError
from opofuente.infrastructure.safe_xml import parse_xml_bytes
from opofuente.infrastructure.safe_zip import (
    ZipLimits,
    check_member_name,
    extract_zip_safely,
    inspect_zip,
)
from opofuente.infrastructure.url_guard import (
    is_blocked_address,
    url_limits_from_settings,
    validate_url,
)

LIMITS = ZipLimits(max_entries=50, max_uncompressed_bytes=1024 * 1024, max_ratio=100)


def build_zip(path: Path, members: dict[str, bytes], *, compress: bool = True) -> Path:
    mode = zipfile.ZIP_DEFLATED if compress else zipfile.ZIP_STORED
    with zipfile.ZipFile(path, "w", mode) as archive:
        for name, content in members.items():
            archive.writestr(name, content)
    return path


def build_zip_with_raw_name(path: Path, replacement: str) -> Path:
    """Escribe un ZIP y cambia el nombre de un miembro en los bytes del fichero.

    Python normaliza los separadores al escribir, así que para simular un ZIP hecho por otra
    herramienta (que sí puede dejar barras invertidas en el nombre) hay que tocar los bytes. El
    nombre de reemplazo tiene que medir lo mismo que el original, para no romper el archivo.
    """
    original = "xx/x.txt"
    build_zip(path, {original: b"no", "ok.txt": b"si"})
    assert len(replacement) == len(original), "el reemplazo debe medir lo mismo"
    reemplazado = path.read_bytes().replace(original.encode(), replacement.encode())
    assert reemplazado.count(replacement.encode()) == 2, "debe aparecer en cabecera y directorio"
    path.write_bytes(reemplazado)
    return path


# --- ZIP: traversal, bomba, enlaces -------------------------------------------------------


def test_zip_con_punto_punto_se_rechaza(tmp_path: Path) -> None:
    archivo = build_zip(tmp_path / "traversal.zip", {"../fuera.txt": b"no"})

    with pytest.raises(UnsafeContentError) as error:
        inspect_zip(archivo, limits=LIMITS)

    assert "sale de la carpeta" in str(error.value)
    # Y no ha aparecido nada fuera del destino.
    assert not (tmp_path / "fuera.txt").exists()


def test_zip_con_ruta_absoluta_se_rechaza(tmp_path: Path) -> None:
    archivo = build_zip(tmp_path / "absoluto.zip", {"/etc/passwd": b"no"})
    with pytest.raises(UnsafeContentError):
        inspect_zip(archivo, limits=LIMITS)


def test_zip_con_barra_invertida_se_rechaza(tmp_path: Path) -> None:
    """Un ZIP con `..\\` se rechaza: en Windows `zipfile` lo normaliza a `../` y lo caza el `..`."""
    archivo = build_zip_with_raw_name(tmp_path / "windows.zip", "..\\x.txt")

    with pytest.raises(UnsafeContentError) as error:
        inspect_zip(archivo, limits=LIMITS)

    assert "sale de la carpeta" in str(error.value)


def test_la_guarda_de_nombres_rechaza_barra_invertida_y_letra_de_unidad() -> None:
    """La comprobación de nombres se prueba directa, sin depender de lo que normalice zipfile."""
    for nombre in ("..\\x.txt", "apuntes\\tema.txt"):
        with pytest.raises(UnsafeContentError) as error:
            check_member_name(nombre)
        assert "barra invertida" in str(error.value)

    with pytest.raises(UnsafeContentError):
        check_member_name("C:/material/notas.txt")
    with pytest.raises(UnsafeContentError):
        check_member_name("  ")

    # Un nombre normal no se rechaza.
    check_member_name("apuntes/tema-01.pdf")


def test_zip_con_letra_de_unidad_se_rechaza(tmp_path: Path) -> None:
    archivo = build_zip(tmp_path / "unidad.zip", {"C:/material/notas.txt": b"no"})
    with pytest.raises(UnsafeContentError):
        inspect_zip(archivo, limits=LIMITS)


def test_zip_con_demasiadas_entradas_se_rechaza(tmp_path: Path) -> None:
    archivo = build_zip(tmp_path / "muchas.zip", {f"tema-{index}.txt": b"x" for index in range(60)})
    with pytest.raises(UnsafeContentError) as error:
        inspect_zip(archivo, limits=LIMITS)
    assert "entradas" in str(error.value)


def test_zip_bomba_por_ratio_se_rechaza(tmp_path: Path) -> None:
    """Un fichero muy comprimible declara una expansión imposible: se corta antes de extraer."""
    archivo = build_zip(tmp_path / "bomba.zip", {"relleno.txt": b"\0" * (512 * 1024)})
    with pytest.raises(UnsafeContentError) as error:
        inspect_zip(
            archivo, limits=ZipLimits(max_entries=10, max_uncompressed_bytes=10**9, max_ratio=20)
        )
    assert "expansión" in str(error.value)


def test_zip_bomba_por_tamano_se_rechaza(tmp_path: Path) -> None:
    archivo = build_zip(tmp_path / "grande.zip", {"relleno.txt": b"\0" * (256 * 1024)})
    with pytest.raises(UnsafeContentError) as error:
        inspect_zip(
            archivo,
            limits=ZipLimits(max_entries=10, max_uncompressed_bytes=64 * 1024, max_ratio=10_000),
        )
    assert "descomprime" in str(error.value)


def test_zip_con_enlace_simbolico_se_rechaza(tmp_path: Path) -> None:
    archivo = tmp_path / "enlace.zip"
    with zipfile.ZipFile(archivo, "w") as archive:
        info = zipfile.ZipInfo("enlace")
        info.external_attr = 0o120777 << 16  # marca de enlace simbólico
        archive.writestr(info, "../../fuera")

    with pytest.raises(UnsafeContentError) as error:
        inspect_zip(archivo, limits=LIMITS)
    assert "enlace" in str(error.value)


def test_zip_corrupto_se_rechaza(tmp_path: Path) -> None:
    falso = tmp_path / "no-es-zip.zip"
    falso.write_bytes(b"esto no es un zip")
    with pytest.raises(UnsafeContentError) as error:
        inspect_zip(falso, limits=LIMITS)
    assert "no es un ZIP" in str(error.value)


def test_zip_legitimo_se_extrae_y_la_basura_del_sistema_se_salta(tmp_path: Path) -> None:
    archivo = build_zip(
        tmp_path / "bueno.zip",
        {
            "tema-01.txt": b"contenido",
            "apuntes/tema-02.txt": "más contenido".encode(),
            "__MACOSX/tema-01.txt": b"basura",
            ".DS_Store": b"basura",
        },
    )
    destino = tmp_path / "salida"

    inspeccion = inspect_zip(archivo, limits=LIMITS)
    escritos = extract_zip_safely(archivo, destino, limits=LIMITS)

    assert inspeccion.file_count == 2
    assert inspeccion.skipped_junk == 2
    assert sorted(path.name for path in escritos) == ["tema-01.txt", "tema-02.txt"]
    assert (destino / "apuntes" / "tema-02.txt").read_text(encoding="utf-8") == "más contenido"
    assert not (destino / "__MACOSX").exists()


def test_zip_con_cabecera_mentirosa_se_corta_al_leer(tmp_path: Path) -> None:
    """Un miembro que declara poco tamaño y trae mucho se corta mientras se escribe."""
    archivo = build_zip(tmp_path / "mentiroso.zip", {"grande.txt": b"x" * (128 * 1024)})
    destino = tmp_path / "salida"
    # Se deja el ratio alto a propósito: aquí se prueba el tope al leer, no la inspección previa.
    holgado = ZipLimits(max_entries=10, max_uncompressed_bytes=10**9, max_ratio=10_000)

    with pytest.raises(UnsafeContentError) as error:
        extract_zip_safely(archivo, destino, limits=holgado, max_bytes_per_member=4096)

    assert "supera el límite" in str(error.value)
    # El fichero a medias se retira: no queda basura con contenido no verificado.
    assert not (destino / "grande.txt").exists()


# --- XML: entidades externas, DOCTYPE, tamaño --------------------------------------------


def test_xml_con_entidad_externa_se_rechaza() -> None:
    """El ataque clásico: leer un fichero local a través de una entidad del DOCTYPE."""
    ataque = (
        b'<?xml version="1.0"?>'
        b'<!DOCTYPE raiz [<!ENTITY xxe SYSTEM "file:///C:/Windows/win.ini">]>'
        b"<raiz>&xxe;</raiz>"
    )
    with pytest.raises(UnsafeContentError) as error:
        parse_xml_bytes(ataque)
    assert "DOCTYPE" in str(error.value)


def test_xml_con_billion_laughs_se_rechaza() -> None:
    ataque = (
        b'<?xml version="1.0"?>'
        b"<!DOCTYPE lolz [<!ENTITY lol 'lol'>"
        b"<!ENTITY lol2 '&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;'>]>"
        b"<lolz>&lol2;</lolz>"
    )
    with pytest.raises(UnsafeContentError):
        parse_xml_bytes(ataque)


def test_xml_demasiado_grande_se_rechaza() -> None:
    with pytest.raises(UnsafeContentError) as error:
        parse_xml_bytes(b"<raiz>" + b"x" * 5000 + b"</raiz>", max_bytes=1024)
    assert "límite" in str(error.value)


def test_xml_bien_formado_se_parsea() -> None:
    from opofuente.infrastructure.safe_xml import element_text

    raiz = parse_xml_bytes(b"<raiz><titulo>Tema 1</titulo><p>Ley 39/2015</p></raiz>")
    assert "Tema 1" in element_text(raiz)
    assert "Ley 39/2015" in element_text(raiz)


def test_xml_no_bien_formado_se_rechaza_sin_reventar() -> None:
    with pytest.raises(UnsafeContentError):
        parse_xml_bytes(b"<raiz><sin cerrar>")


# --- URL: SSRF, redirecciones, límites ---------------------------------------------------


@pytest.mark.parametrize(
    "address",
    [
        "127.0.0.1",
        "10.0.0.5",
        "172.16.3.9",
        "192.168.1.10",
        "169.254.169.254",  # metadatos de nube
        "0.0.0.0",  # noqa: S104 - es una dirección que hay que BLOQUEAR, no un bind
        "::1",
        "fe80::1",
        "fd00::1",
        "::ffff:10.0.0.1",  # IPv4 embebida en IPv6
        "2002:0a00:0001::1",  # 6to4 sobre 10.0.0.1
    ],
)
def test_direcciones_internas_estan_bloqueadas(address: str) -> None:
    assert is_blocked_address(address) is True


def test_direcciones_publicas_no_estan_bloqueadas() -> None:
    assert is_blocked_address("8.8.8.8") is False
    assert is_blocked_address("2606:4700:4700::1111") is False


def test_url_con_esquema_no_permitido_se_rechaza() -> None:
    for url in ("file:///C:/Windows/win.ini", "ftp://ejemplo.test/x", "javascript:alert(1)"):
        with pytest.raises(UrlRejectedError):
            validate_url(url, resolver=lambda _host: ("93.184.216.34",))


def test_url_a_red_interna_se_rechaza() -> None:
    with pytest.raises(UrlRejectedError) as error:
        validate_url("http://interno.test/notas.pdf", resolver=lambda _host: ("192.168.0.10",))
    assert "red interna" in str(error.value)


def test_url_que_resuelve_a_varias_direcciones_se_rechaza_si_alguna_es_interna() -> None:
    """Basta con que una respuesta del DNS sea interna para no descargar nada."""
    with pytest.raises(UrlRejectedError):
        validate_url("http://mixto.test/x", resolver=lambda _host: ("93.184.216.34", "127.0.0.1"))


def test_url_sin_resolucion_se_rechaza() -> None:
    with pytest.raises(UrlRejectedError):
        validate_url("http://no-existe.test/x", resolver=lambda _host: ())


def test_url_con_credenciales_se_rechaza() -> None:
    with pytest.raises(UrlRejectedError) as error:
        validate_url("https://usuario:clave@ejemplo.test/x", resolver=lambda _h: ("93.184.216.34",))
    assert "credenciales" in str(error.value)


def test_url_publica_valida_devuelve_destino_y_direcciones() -> None:
    destino = validate_url(
        "https://www.boe.es/diario_boe/x", resolver=lambda _h: ("93.184.216.34",)
    )
    assert destino.host == "www.boe.es"
    assert destino.scheme == "https"
    assert destino.port == 443
    assert destino.addresses == ("93.184.216.34",)


def test_la_redireccion_a_red_interna_se_rechaza(monkeypatch: pytest.MonkeyPatch) -> None:
    """Cada salto se valida: una redirección a 127.0.0.1 no se sigue."""
    from opofuente.infrastructure import url_guard

    def_resolver = {"publico.test": ("93.184.216.34",), "interno.test": ("127.0.0.1",)}
    monkeypatch.setattr(
        url_guard, "default_resolver", lambda host: def_resolver.get(host, ("93.184.216.34",))
    )

    # La validación del segundo salto ocurre antes de cualquier conexión, así que no hace falta red.
    with pytest.raises(UrlRejectedError):
        url_guard.validate_url("http://interno.test/x")


def test_el_fetch_sigue_redirecciones_validadas_y_corta_el_tamano(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Simulación del salto completo: la primera respuesta redirige; la segunda corta por tamaño."""
    from opofuente.infrastructure import url_guard

    respuestas: dict[str, tuple[int, dict[str, str], bytes]] = {
        "/inicio": (302, {"location": "/final"}, b""),
        "/final": (200, {"content-type": "text/plain"}, b"x" * 2048),
    }

    class RespuestaFalsa(io.BytesIO):
        def __init__(self, status: int, headers: dict[str, str], body: bytes) -> None:
            super().__init__(body)
            self.status = status
            self._headers = headers

        def getheaders(self) -> list[tuple[str, str]]:
            return list(self._headers.items())

    class ConexionFalsa:
        def __init__(self, *_args, **_kwargs) -> None:
            self._path = ""

        def request(
            self, method: str, path: str, body: object = None, headers: object = None
        ) -> None:
            self._path = path

        def getresponse(self) -> RespuestaFalsa:
            status, headers, body = respuestas[self._path]
            return RespuestaFalsa(status, headers, body)

        def close(self) -> None:
            return None

    monkeypatch.setattr(url_guard, "_PinnedConnection", ConexionFalsa)
    monkeypatch.setenv("NO_PROXY", "*")

    limite = url_limits_from_settings(timeout_seconds=5, max_bytes=1024, max_redirects=3)
    with pytest.raises(UrlRejectedError) as error:
        url_guard.fetch_url(
            "http://publico.test/inicio",
            destination=tmp_path / "descarga.bin",
            limits=limite,
            resolver=lambda _host: ("93.184.216.34",),
        )

    assert "supera el límite" in str(error.value)
    assert not (tmp_path / "descarga.bin").exists()
