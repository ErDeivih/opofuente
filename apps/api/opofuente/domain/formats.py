"""Política de formatos: qué se extrae, qué se conserva y qué no se admite (04_INGESTION §2 y §3).

Este módulo es **dominio puro**: no abre ficheros, no conoce bibliotecas y no depende de la
configuración. Responde a una sola pregunta —«con este nombre y estos primeros bytes, ¿qué hago con
este fichero?»— para que la misma respuesta la usen el inventario, la copia, las entradas directas y
el registro de extractores. Antes vivía dentro del registro de extractores (infraestructura), y eso
hacía que la aplicación tuviera que importar infraestructura para saber si un `.exe` se admite.

Tres listas, con motivos distintos:

- `DANGEROUS_SUFFIXES`: no se copian **ni** se conservan (decisión de seguridad, §2);
- `PRESERVED_SUFFIXES`: se copian y se conservan **sin ejecutar ni extraer** (§3, DEBT-008);
- `EXECUTABLE_SIGNATURES`: firmas de ejecutable reconocidas por contenido, para que un `.dat` con
  cabecera `MZ` (PE) o `\\x7fELF` no pase por inocente cuando el nombre engaña.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import PurePosixPath

#: Sufijos que no se extraen **ni se conservan** por decisión de seguridad (04_INGESTION §2).
DANGEROUS_SUFFIXES = frozenset(
    {".exe", ".dll", ".msi", ".bat", ".cmd", ".com", ".scr", ".ps1", ".jar", ".so", ".dylib"}
)

#: Sufijos que se conservan aunque el contenido parezca otra cosa (Office con macros, audio, vídeo).
PRESERVED_SUFFIXES: dict[str, str] = {
    ".docm": "documento de Office con macros: se conserva sin ejecutar ni extraer",
    ".xlsm": "hoja de cálculo con macros: se conserva sin ejecutar ni extraer",
    ".pptm": "presentación con macros: se conserva sin ejecutar ni extraer",
    ".pptx": "presentación: se conserva, todavía no se extrae",
    ".xlsx": "hoja de cálculo: se conserva, todavía no se extrae",
    ".ppt": "presentación: se conserva, todavía no se extrae",
    ".xls": "hoja de cálculo: se conserva, todavía no se extrae",
    ".odt": "documento de texto de OpenDocument: se conserva, todavía no se extrae",
    ".ods": "hoja de cálculo de OpenDocument: se conserva, todavía no se extrae",
    ".epub": "libro electrónico: se conserva, todavía no se extrae",
    ".mp3": "audio: se conserva, todavía no se extrae",
    ".wav": "audio: se conserva, todavía no se extrae",
    ".m4a": "audio: se conserva, todavía no se extrae",
    ".ogg": "audio: se conserva, todavía no se extrae",
    ".mp4": "vídeo: se conserva, todavía no se extrae",
    ".mkv": "vídeo: se conserva, todavía no se extrae",
    ".avi": "vídeo: se conserva, todavía no se extrae",
    ".mov": "vídeo: se conserva, todavía no se extrae",
}

#: Sufijos que cuentan como contenedor ZIP para la política de anidamiento.
ZIP_SUFFIXES = frozenset({".zip"})

#: Barajas de Anki: son contenedores ZIP con una base de datos dentro, pero **no** se expanden como
#: un ZIP (se perderían las tarjetas). Tienen familia y extractor propios (ADR-016).
ANKI_SUFFIXES = frozenset({".apkg", ".colpkg"})

#: Sufijos de texto plano, CSV, JSON y HTML. Se declaran aquí porque varias capas los consultan
#: (el registro de extractores y las entradas directas, que rechazan un ejecutable al subirlo).
TEXT_SUFFIXES = frozenset({".txt", ".md", ".markdown", ".log", ".rst"})
CSV_SUFFIXES = frozenset({".csv", ".tsv"})
JSON_SUFFIXES = frozenset({".json"})
HTML_SUFFIXES = frozenset({".html", ".htm", ".xhtml"})
IMAGE_SUFFIXES = frozenset({".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tif", ".tiff", ".webp"})


class FileSignature(StrEnum):
    """Qué se ha reconocido por el contenido, cuando el nombre no basta o engaña."""

    EXECUTABLE = "executable"
    """Ejecutable o biblioteca: PE (`MZ`), ELF o Mach-O. No se copia ni se conserva."""

    ARCHIVE = "archive"
    """Contenedor ZIP por contenido (puede ser DOCX, XLSX, PPTX, EPUB o un ZIP normal)."""

    UNKNOWN = "unknown"


#: Firmas de ejecutable que se reconocen por contenido. Se comprueban **antes** que la extensión:
#: un `.txt` con cabecera PE no es material de estudio.
_EXECUTABLE_MAGIC: tuple[tuple[bytes, str], ...] = (
    (b"MZ", "PE"),
    (b"\x7fELF", "ELF"),
    (b"\xca\xfe\xba\xbe", "Mach-O"),
    (b"\xcf\xfa\xed\xfe", "Mach-O"),
    (b"\xce\xfa\xed\xfe", "Mach-O"),
    (b"\xfe\xed\xfa\xce", "Mach-O"),
    (b"\xfe\xed\xfa\xcf", "Mach-O"),
)


@dataclass(frozen=True, slots=True)
class SignatureMatch:
    """Firma reconocida y su nombre legible (para el mensaje que ve el usuario)."""

    signature: FileSignature
    label: str


def match_signature(head: bytes) -> SignatureMatch:
    """Reconoce ejecutables y contenedores por sus primeros bytes. No lee el fichero entero."""
    for magic, label in _EXECUTABLE_MAGIC:
        if head.startswith(magic):
            return SignatureMatch(FileSignature.EXECUTABLE, label)
    if head.startswith(b"PK\x03\x04") or head.startswith(b"PK\x05\x06"):
        return SignatureMatch(FileSignature.ARCHIVE, "ZIP")
    return SignatureMatch(FileSignature.UNKNOWN, "")


def is_dangerous_suffix(suffix: str) -> bool:
    return suffix.lower() in DANGEROUS_SUFFIXES


def preserved_reason(suffix: str) -> str | None:
    """Motivo por el que un sufijo se conserva sin extraer, si procede."""
    return PRESERVED_SUFFIXES.get(suffix.lower())


def is_container_suffix(suffix: str) -> bool:
    return suffix.lower() in ZIP_SUFFIXES


def executable_refusal(head: bytes) -> str | None:
    """Motivo por el que unos bytes no se admiten por su firma, si procede.

    Se usa tanto al copiar (para no guardar un binario que el usuario no quiere) como al extraer
    (para un miembro de ZIP con nombre inocente que en realidad es un ejecutable).
    """
    match = match_signature(head)
    if match.signature is FileSignature.EXECUTABLE:
        return f"firma de ejecutable ({match.label})"
    return None


def suffix_of_name(name: str) -> str:
    """Extensión del nombre con el que entró el fichero, en minúsculas y con su punto.

    En el almacén el fichero se llama como su hash, así que la política de sufijos se decide con el
    nombre original de la entrada, no con la ruta interna. Acepta también rutas con `/` para poder
    usarla con las rutas relativas de un lote.
    """
    return PurePosixPath(name.replace("\\", "/")).suffix.lower()


def storage_refusal(*, name: str, head: bytes) -> str | None:
    """Motivo por el que este contenido **no debe guardarse** en el almacén, o `None`.

    Es la comprobación común a todas las vías de entrada (subida, URL, carpeta y miembros de ZIP):
    un ejecutable o una biblioteca se rechazan antes de copiar nada, por su nombre **y** por su
    firma, porque un `.txt` con cabecera PE sigue siendo un binario. El texto pegado no pasa por
    aquí: es texto que escribe OpoFuente, no un fichero que llega de fuera.
    """
    suffix = suffix_of_name(name)
    if is_dangerous_suffix(suffix):
        return f"ejecutable o biblioteca por su extensión ({suffix})"
    return executable_refusal(head)


__all__ = [
    "ANKI_SUFFIXES",
    "CSV_SUFFIXES",
    "DANGEROUS_SUFFIXES",
    "HTML_SUFFIXES",
    "IMAGE_SUFFIXES",
    "JSON_SUFFIXES",
    "PRESERVED_SUFFIXES",
    "TEXT_SUFFIXES",
    "ZIP_SUFFIXES",
    "FileSignature",
    "SignatureMatch",
    "executable_refusal",
    "is_container_suffix",
    "is_dangerous_suffix",
    "match_signature",
    "preserved_reason",
    "storage_refusal",
    "suffix_of_name",
]
