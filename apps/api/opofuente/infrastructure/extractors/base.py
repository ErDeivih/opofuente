"""Piezas comunes de los extractores: contrato, sniffing de formato y decodificación.

Ningún extractor decide rutas ni escribe en el almacén: recibe la ruta de un artefacto ya copiado
(que es de solo lectura) y devuelve un `ExtractionResult`. Así el mismo extractor se prueba sin base
de datos y sin API.

Tres reglas que se aplican aquí (09_SECURITY §3, DEBT-004):

- el **formato se decide por el contenido** (magic bytes y estructura); la extensión es solo una
  señal secundaria, nunca la que manda;
- **el nombre original viaja aparte**: en el almacén el fichero se llama como su hash, así que la
  extensión se toma del nombre con el que entró (`name=`), no de la ruta interna. Sin eso, un
  `.docm` o un `.json` guardados por hash dejaban de reconocerse por su extensión;
- la lectura está **acotada**: ningún extractor lee un fichero entero sin límite, porque el material
  admite ficheros de cientos de megabytes y la memoria no es infinita.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from opofuente.domain.extraction import ExtractionResult
from opofuente.domain.formats import (
    CSV_SUFFIXES,
    DANGEROUS_SUFFIXES,
    HTML_SUFFIXES,
    IMAGE_SUFFIXES,
    JSON_SUFFIXES,
    TEXT_SUFFIXES,
    FileSignature,
    match_signature,
    suffix_of_name,
)

__all__ = [
    "CSV_SUFFIXES",
    "DANGEROUS_SUFFIXES",
    "HTML_SUFFIXES",
    "IMAGE_SUFFIXES",
    "JSON_SUFFIXES",
    "TEXT_SUFFIXES",
    "DetectedFormat",
    "Extractor",
    "decode_with_warning",
    "detect_format",
    "read_bounded",
    "read_head",
    "suffix_of",
    "try_decode_text",
]

#: Firma de un PDF, un ZIP (DOCX/PPTX/XLSX/EPUB) y las imágenes que se reconocen.
PDF_MAGIC = b"%PDF-"
ZIP_MAGIC = b"PK\x03\x04"
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
JPEG_MAGIC = b"\xff\xd8\xff"
GIF_MAGIC = b"GIF8"

#: Cuántos bytes se leen para decidir el formato.
SNIFF_BYTES = 4096

#: Bytes que se leen de más en una lectura acotada: con ellos se decide si el corte partió un
#: carácter (una secuencia UTF-8 mide como mucho 4 bytes) y si el fichero continúa.
LOOKAHEAD_BYTES = 4


@dataclass(frozen=True, slots=True)
class DetectedFormat:
    """Formato detectado por contenido, con la extensión como señal secundaria."""

    family: str
    """`pdf`, `zip`, `docx`, `image`, `text`, `csv`, `json`, `html`, `executable`, `binary`…"""

    suffix: str
    matches_extension: bool
    """Si lo que dice el contenido coincide con lo que dice la extensión."""


class Extractor(Protocol):
    """Contrato de un extractor. Todos son funciones puras sobre un fichero de solo lectura."""

    name: str
    version: str

    def extract(self, path: Path, *, detected: DetectedFormat) -> ExtractionResult: ...


def suffix_of(path: Path, name: str | None = None) -> str:
    """Extensión del fichero tal y como entró, no como se llama en el almacén.

    `path` suele ser `data/artifacts/sha256/ab/cd/<hash>`: ahí no hay extensión que valga. El
    nombre original llega por `name` y es el que manda para las decisiones por sufijo.
    """
    if name:
        return suffix_of_name(name)
    return path.suffix.lower()


def read_head(path: Path, *, size: int = SNIFF_BYTES) -> bytes:
    """Lee el principio del fichero. Solo lectura y con tamaño acotado."""
    with path.open("rb") as stream:
        return stream.read(size)


def read_bounded(path: Path, *, max_bytes: int) -> tuple[bytes, bool]:
    """Lee como mucho `max_bytes` y dice si el fichero era más grande.

    Se leen unos bytes de más a propósito: sirven para distinguir «cabe justo» de «hay más» sin
    preguntar antes por el tamaño (que puede cambiar entre la pregunta y la lectura) **y** para
    decidir si el corte ha partido un carácter (ver `_trim_to_character_boundary`).
    """
    with path.open("rb") as stream:
        data = stream.read(max_bytes + LOOKAHEAD_BYTES)
    if len(data) <= max_bytes:
        return data, False
    return _trim_to_character_boundary(data[:max_bytes], data[max_bytes:]), True


def _trim_to_character_boundary(data: bytes, tail: bytes) -> bytes:
    """Devuelve el bloque tal cual si es texto completo; si el corte partió un carácter, lo retira.

    La decisión se toma con **evidencia**, no por la posición del error:

    1. si el bloque decodifica como UTF-8, no hay nada que hacer;
    2. si no decodifica, solo importa el caso de una **secuencia incompleta al final**
       (`unexpected end of data`). Un byte `0xFF` o una continuación inválida no son una secuencia
       truncada: recortar el final no arreglaría la decodificación y perdería contenido que sí
       estaba, así que el bloque se devuelve tal cual y quien decodifique decidirá, avisando de la
       codificación que use;
    3. y si es una secuencia incompleta, se mira lo que viene **después del corte** (`tail`): si
       esos bytes completan la secuencia, el fichero es UTF-8 y el corte partió un carácter, así
       que se retira la parte incompleta. Si no la completan, ese byte no era UTF-8 —en Windows-1252
       un `0xC3` suelto es `Ã`— y el bloque se conserva entero para que la decodificación lo declare
       como CP-1252 sin perder nada.
    """
    try:
        data.decode("utf-8")
    except UnicodeDecodeError as error:
        if error.reason != "unexpected end of data":
            return data
        parcial = data[error.start :]
        if not _completes_with(parcial, tail):
            # No era una secuencia UTF-8 partida: se conserva el bloque entero.
            return data
        return data[: error.start]
    return data


def _completes_with(parcial: bytes, tail: bytes) -> bool:
    """¿La secuencia incompleta del final se completa con los bytes que vienen después del corte?"""
    if not tail:
        return False
    try:
        (parcial + tail[: 4 - len(parcial)]).decode("utf-8")
    except UnicodeDecodeError:
        return False
    return True


def detect_format(
    path: Path, *, head: bytes | None = None, name: str | None = None
) -> DetectedFormat:
    """Decide el formato por contenido y compara con la extensión (señal secundaria).

    `name` es el nombre original del fichero: es de donde sale la extensión, porque en el almacén el
    fichero se llama como su hash.
    """
    data = head if head is not None else read_head(path)
    suffix = suffix_of(path, name)

    firma = match_signature(data)
    if firma.signature is FileSignature.EXECUTABLE:
        # La firma manda sobre el nombre: un `.txt` con cabecera PE (`MZ`) no es material de
        # estudio.
        return DetectedFormat("executable", suffix, suffix in DANGEROUS_SUFFIXES)
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
