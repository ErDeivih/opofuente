"""Piezas comunes de los extractores: contrato, sniffing de formato y decodificación.

Ningún extractor decide rutas ni escribe en el almacén: recibe la ruta de un artefacto ya copiado
(que es de solo lectura) y devuelve un `ExtractionResult`. Así el mismo extractor se prueba sin base
de datos y sin API.

Dos reglas de seguridad que se aplican aquí (09_SECURITY §3, DEBT-004):

- el **formato se decide por el contenido** (magic bytes y estructura); la extensión es solo una
  señal secundaria, nunca la que manda;
- la decodificación de texto **no adivina en silencio**: si el fichero no es UTF-8 y se lee como
  Windows-1252, se avisa.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from opofuente.domain.extraction import ExtractionResult

#: Firma de un PDF, un ZIP (DOCX/PPTX/XLSX/EPUB) y las imágenes que se reconocen.
PDF_MAGIC = b"%PDF-"
ZIP_MAGIC = b"PK\x03\x04"
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
JPEG_MAGIC = b"\xff\xd8\xff"
GIF_MAGIC = b"GIF8"

#: Extensiones de texto plano que se decodifican como texto si el contenido lo parece.
TEXT_SUFFIXES = frozenset({".txt", ".md", ".markdown", ".log", ".rst"})
CSV_SUFFIXES = frozenset({".csv", ".tsv"})
JSON_SUFFIXES = frozenset({".json"})
HTML_SUFFIXES = frozenset({".html", ".htm", ".xhtml"})
IMAGE_SUFFIXES = frozenset({".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tif", ".tiff", ".webp"})

#: Cuántos bytes se leen para decidir el formato.
SNIFF_BYTES = 4096


@dataclass(frozen=True, slots=True)
class DetectedFormat:
    """Formato detectado por contenido, con la extensión como señal secundaria."""

    family: str
    """`pdf`, `zip`, `docx`, `image`, `text`, `csv`, `json`, `html`, `binary` o `unknown`."""

    suffix: str
    matches_extension: bool
    """Si lo que dice el contenido coincide con lo que dice la extensión."""


class Extractor(Protocol):
    """Contrato de un extractor. Todos son funciones puras sobre un fichero de solo lectura."""

    name: str
    version: str

    def extract(self, path: Path, *, detected: DetectedFormat) -> ExtractionResult: ...


def read_head(path: Path, *, size: int = SNIFF_BYTES) -> bytes:
    """Lee el principio del fichero. Solo lectura y con tamaño acotado."""
    with path.open("rb") as stream:
        return stream.read(size)


def detect_format(path: Path, *, head: bytes | None = None) -> DetectedFormat:
    """Decide el formato por contenido y compara con la extensión (señal secundaria)."""
    data = head if head is not None else read_head(path)
    suffix = path.suffix.lower()

    if data.startswith(PDF_MAGIC):
        return DetectedFormat("pdf", suffix, suffix == ".pdf")
    if data.startswith(PNG_MAGIC) or data.startswith(JPEG_MAGIC) or data.startswith(GIF_MAGIC):
        return DetectedFormat("image", suffix, suffix in IMAGE_SUFFIXES)
    if data.startswith(ZIP_MAGIC):
        return DetectedFormat(_zip_family(path), suffix, True)
    if _looks_like_json(data) and suffix in JSON_SUFFIXES:
        return DetectedFormat("json", suffix, True)
    if _looks_like_html(data):
        return DetectedFormat("html", suffix, suffix in HTML_SUFFIXES)
    decoded = try_decode_text(data)
    if decoded is not None:
        if suffix in JSON_SUFFIXES and _looks_like_json(data):
            return DetectedFormat("json", suffix, True)
        if suffix in CSV_SUFFIXES or _looks_like_csv(decoded):
            return DetectedFormat("csv", suffix, suffix in CSV_SUFFIXES)
        if suffix in HTML_SUFFIXES or _looks_like_html(data):
            return DetectedFormat("html", suffix, suffix in HTML_SUFFIXES)
        return DetectedFormat("text", suffix, suffix in TEXT_SUFFIXES or True)
    return DetectedFormat("binary", suffix, False)


def _zip_family(path: Path) -> str:
    """Mira dentro del ZIP para saber si es un DOCX, un PPTX, un XLSX, un EPUB o un ZIP normal."""
    import zipfile

    try:
        with zipfile.ZipFile(path) as archive:
            names = set(archive.namelist())
    except (zipfile.BadZipFile, OSError):
        return "binary"
    if "word/document.xml" in names:
        return "docx"
    if any(name.startswith("xl/") for name in names):
        return "spreadsheet"
    if any(name.startswith("ppt/") for name in names):
        return "presentation"
    if "mimetype" in names:
        return "epub"
    return "zip"


def try_decode_text(data: bytes) -> str | None:
    """Intenta leer bytes como texto.

    Devuelve `None` si el contenido no parece texto: bytes nulos o demasiados caracteres de
    control. Primero UTF-8; si falla, Windows-1252, que es lo que aparece en material real.
    """
    if not data.strip():
        return ""
    if b"\x00" in data:
        return None
    for encoding in ("utf-8", "cp1252"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return None


def decode_with_warning(data: bytes) -> tuple[str, bool]:
    """Decodifica y dice si hubo que caer a Windows-1252 (para avisar de ello)."""
    try:
        return data.decode("utf-8"), False
    except UnicodeDecodeError:
        return data.decode("cp1252", errors="replace"), True


def _looks_like_json(data: bytes) -> bool:
    stripped = data.lstrip()
    return stripped.startswith((b"{", b"["))


def _looks_like_html(data: bytes) -> bool:
    head = data[:512].lstrip().lower()
    return head.startswith((b"<!doctype html", b"<html", b"<?xml")) and b"<" in head


def _looks_like_csv(text: str) -> bool:
    """Un CSV tiene al menos dos líneas con el mismo separador y el mismo número de campos."""
    lines: list[str] = []
    for raw in text.splitlines():
        if raw.strip():
            lines.append(raw)
        if len(lines) >= 4:
            break
    if len(lines) < 2:
        return False
    for delimiter in (";", ",", "\t", "|"):
        counts = [line.count(delimiter) for line in lines]
        if counts[0] > 0 and len(set(counts)) == 1:
            return True
    return False
