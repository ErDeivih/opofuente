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


def relative_display(root: Path, path: Path) -> str:
    """Ruta relativa a la raíz para mostrar. Nunca incluye la raíz absoluta del usuario."""
    try:
        return path.resolve(strict=False).relative_to(root.resolve(strict=False)).as_posix()
    except ValueError:
        return f"<fuera-de-raiz>/{path.name}"


def abbreviate(path: Path, *, keep: int = 2) -> str:
    """Versión corta de una ruta para logs y para la interfaz («…/padre/hijo»)."""
    parts = [part for part in path.parts if part not in {path.anchor}]
    if len(parts) <= keep:
        return str(path)
    return "…/" + "/".join(parts[-keep:])
