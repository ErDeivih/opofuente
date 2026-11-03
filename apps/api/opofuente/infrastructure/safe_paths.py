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
from pathlib import Path

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


#: Separadores de los dos mundos: el producto vive en Windows y las puertas corren en Linux, y la
#: abreviatura tiene que decir lo mismo en los dos sitios.
_PATH_SEPARATORS = re.compile(r"[\\/]+")
_DRIVE_PREFIX = re.compile(r"^[A-Za-z]:")
_DOUBLE_SEPARATOR_START = re.compile(r"^[\\/]{2,}")


def abbreviate(path: Path, *, keep: int = 2) -> str:
    r"""Versión corta de una ruta para logs y para la interfaz («…/padre/hijo»).

    **Nunca** devuelve la ruta completa: se descarta siempre la raíz (letra de unidad, UNC o `/`)
    y se conservan como mucho los últimos `keep` componentes. Si no queda ningún componente
    (una raíz suelta) se devuelve «…».

    Se segmenta el **texto** y no `path.parts`, a propósito: en POSIX `Path("C:/Material")` es un
    único componente, así que la misma ruta se abreviaba de dos formas según el anfitrión
    (`…/C:/Material` en Linux, `…/Material` en Windows) y la unidad se colaba en el resultado.
    Aquí se separa por los dos separadores y se descarta la raíz en todas sus formas: unidad
    (`C:`), arranque UNC (`\servidor\recurso`) y raíz POSIX.
    """
    text = str(path)
    segments = [segment for segment in _PATH_SEPARATORS.split(text) if segment]
    if segments and _DRIVE_PREFIX.match(segments[0]):
        # `C:` suelto se cae entero; `C:material` conserva lo que va detrás de la unidad.
        rest = segments[0][2:]
        segments = segments[1:]
        if rest:
            segments.insert(0, rest)
    elif _DOUBLE_SEPARATOR_START.match(text):
        # `\\servidor\recurso\…`: el servidor y la compartición son la raíz, no la ruta.
        segments = segments[2:]
    if not segments:
        return "…"
    return "…/" + "/".join(segments[-keep:])


#: Rutas absolutas con separador de Windows: letra de unidad (`C:\…`, `C:/…`), UNC
#: (`\\servidor\recurso\…`) y las que arrancan en la raíz de una unidad (`\carpeta\fichero`), que
#: es la forma en que Python compone el texto de un `PermissionError`.
_WINDOWS_PATH = re.compile(r"(?:[A-Za-z]:[\\/]|\\+[^\\/\s]+[\\/])[^\s\"'<>|?*\r\n]*")


def redact_paths(text: str, *, keep: int = 1) -> str:
    r"""Sustituye las rutas absolutas de un texto por su forma abreviada.

    Los mensajes de error de terceros (un `PermissionError` de Python, un error de SQLite)
    suelen incluir la ruta completa del fichero. Ese texto acaba en `jobs.error_message` y en la
    interfaz, así que aquí se recorta antes: el nombre del fichero es metadato y puede verse, la
    carpeta del usuario no.

    Se cubren las formas que produce este producto (Windows 11): letra de unidad, UNC y la ruta sin
    letra de unidad que Python pone en el texto de una excepción (`\carpeta\fichero`). En otras
    formas de ruta (por ejemplo, una ruta POSIX relativa en prosa) el texto se deja tal cual; quien
    lo use no debe asumir que ya viene saneado.
    """

    def _replace(match: re.Match[str]) -> str:
        return abbreviate(Path(match.group(0)), keep=keep)

    return _WINDOWS_PATH.sub(_replace, text)
