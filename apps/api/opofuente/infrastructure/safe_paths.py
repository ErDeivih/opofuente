"""Rutas seguras: nada sale de donde debe.

Reglas que se aplican aquí (02_ARCHITECTURE §5, 09_SECURITY-PRIVACY-AND-RIGHTS §3):

- toda escritura se valida resolved dentro de `OPOFUENTE_DATA_DIR`;
- los nombres originales son **metadatos**, nunca rutas de destino;
- un enlace simbólico o junction que salga de la raíz seleccionada no se sigue;
- no se ejecuta ni se abre nada con el shell.
"""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path, PurePosixPath, PureWindowsPath

from opofuente.domain.errors import InvariantViolationError

_WINDOWS_RESERVED = {
    "con",
    "prn",
    "aux",
    "nul",
    *(f"com{index}" for index in range(1, 10)),
    *(f"lpt{index}" for index in range(1, 10)),
}
_CONTROL_CHARS = re.compile(r"[\x00-\x1f\x7f]")


class PathOutsideRootError(InvariantViolationError):
    """La ruta resuelta queda fuera de la raíz permitida."""


def is_within(root: Path, candidate: Path) -> bool:
    """¿`candidate` está dentro de `root`? Compara rutas ya resueltas."""
    resolved_root = root.resolve(strict=False)
    resolved_candidate = candidate.resolve(strict=False)
    return resolved_candidate == resolved_root or resolved_root in resolved_candidate.parents


def resolve_within(root: Path, candidate: Path) -> Path:
    """Resuelve y comprueba; lanza `PathOutsideRootError` si se sale."""
    resolved = candidate.resolve(strict=False)
    if not is_within(root, resolved):
        raise PathOutsideRootError(
            f"la ruta resuelta queda fuera de la raíz permitida ({root.name})"
        )
    return resolved


def safe_display_name(name: str, *, fallback: str = "sin-nombre") -> str:
    """Nombre para mostrar y guardar como metadato.

    No se usa nunca para construir una ruta de destino: el destino sale del hash. Se eliminan
    separadores de ruta, caracteres de control y nombres reservados de Windows.
    """
    cleaned = unicodedata.normalize("NFC", name)
    cleaned = _CONTROL_CHARS.sub("", cleaned)
    cleaned = cleaned.replace("/", "_").replace("\\", "_").strip()
    cleaned = cleaned.strip(". ") or fallback
    stem = cleaned.split(".")[0].lower()
    if stem in _WINDOWS_RESERVED:
        cleaned = f"_{cleaned}"
    return cleaned[:200]


def safe_display_path(name: str, *, fallback: str = "sin-nombre", max_length: int = 400) -> str:
    """Ruta relativa para mostrar, segmento a segmento, conservando la estructura de carpetas.

    Al soltar una carpeta entera, el navegador manda cada fichero con su ruta relativa
    («Apuntes TAI/Tema 3/resumen.pdf»). Aplanar esa ruta a un nombre suelto pierde la única pista de
    dónde estaba el material: es lo que el usuario ve en su disco y lo que ayuda a clasificarlo. Se
    sanea **cada segmento** con `safe_display_name` y se vuelven a unir con «/».

    Sigue siendo un **metadato**: el destino de la copia sale del hash, no de esto.
    """
    limpio = unicodedata.normalize("NFC", name)
    limpio = _CONTROL_CHARS.sub("", limpio)
    segmentos = [segmento for segmento in re.split(r"[/\\]+", limpio) if segmento.strip(". ")]
    if not segmentos:
        return fallback
    saneados = [safe_display_name(segmento, fallback=fallback) for segmento in segmentos]
    return "/".join(saneados)[:max_length]


def relative_display(root: Path, path: Path) -> str:
    """Ruta relativa a la raíz para mostrar. Nunca incluye la raíz absoluta del usuario."""
    try:
        return path.resolve(strict=False).relative_to(root.resolve(strict=False)).as_posix()
    except ValueError:
        return f"<fuera-de-raiz>/{path.name}"


def _is_windows_shape(text: str) -> bool:
    """¿`text` está escrito con la sintaxis de rutas de Windows?

    Se decide por la cadena y no por el anfitrión: unidad (`C:`), cualquier barra invertida
    (`\\`, que en POSIX no separa nada) o raíz de unidad actual (`\\Users\\…`).
    """
    if "\\" in text:
        return True
    return len(text) >= 2 and text[0].isalpha() and text[1] == ":"


def _components(text: str) -> tuple[str, ...]:
    """Componentes de `text` analizados según **su propia** sintaxis, descartando el ancla.

    `pathlib.Path` interpreta la cadena con las reglas del sistema donde corre el proceso: en
    POSIX, `C:/Material` son dos segmentos (`C:` y `Material`) y `\\` no separa nada. Eso hacía que
    la misma ruta diera una salida distinta —y filtrara la unidad o el nombre del usuario— según el
    anfitrión. Aquí la forma se decide por la cadena: una ruta con unidad, UNC, raíz de unidad
    actual o cualquier barra invertida se lee como ruta de Windows; el resto, como POSIX.
    """
    parsed = PureWindowsPath(text) if _is_windows_shape(text) else PurePosixPath(text)
    anchor = parsed.anchor
    return tuple(part for part in parsed.parts if part != anchor)


def abbreviate(path: Path, *, keep: int = 2) -> str:
    """Versión corta de una ruta para logs y para la interfaz («…/padre/hijo»).

    **Nunca** devuelve la ruta completa: se descarta siempre la raíz (letra de unidad, UNC, raíz de
    unidad actual o `/`) y se conservan como mucho los últimos `keep` componentes. Si no queda
    ningún componente (una raíz suelta) se devuelve «…».

    La forma de la ruta se decide por la cadena (`_components`), así que la salida es la misma en
    Windows y en un anfitrión POSIX.
    """
    components = _components(str(path))
    if not components:
        return "…"
    return "…/" + "/".join(components[-keep:])


#: Rutas absolutas de Windows dentro de un texto: unidad (`C:\…`, `C:/…`), UNC
#: (`\\servidor\recurso\…`) y raíz de la unidad actual (`\Windows\…`). El *lookbehind* exige que
#: la coincidencia empiece donde empieza la ruta, para no tocar nombres relativos (`carpeta\a.txt`)
#: ni prosa con `/`; tampoco se confunde con el esquema de una URL (`https://…`) ni con la cola de
#: otra ruta ya abreviada.
_WINDOWS_PATH = re.compile(
    r"(?<![\w:.\\])(?:[A-Za-z]:[\\/]|\\\\[^\\/\s\"'<>|?*]+[\\/]|\\\\)[^\s\"'<>|?*\r\n]*",
)


def redact_paths(text: str, *, keep: int = 1) -> str:
    """Sustituye las rutas absolutas de un texto por su forma abreviada.

    Los mensajes de error de terceros (un `PermissionError` de Python, un error de SQLite)
    suelen incluir la ruta completa del fichero. Ese texto acaba en `jobs.error_message` y en la
    interfaz, así que aquí se recorta antes: el nombre del fichero es metadato y puede verse, la
    carpeta del usuario no.

    Se cubren las tres formas absolutas que produce este producto (Windows 11): letra de unidad,
    UNC y raíz de la unidad actual (`\\Users\\…`, la que aparece cuando la ruta se construyó sin
    unidad). Las rutas POSIX y las relativas se dejan tal cual: no las produce el producto y
    tocarlas rompería mensajes legítimos; quien lo use no debe asumir que ya viene saneado.
    """

    def _replace(match: re.Match[str]) -> str:
        return abbreviate(Path(match.group(0)), keep=keep)

    return _WINDOWS_PATH.sub(_replace, text)
