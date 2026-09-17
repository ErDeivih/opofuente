"""Extractores de texto: TXT/MD, CSV, JSON y HTML (04_INGESTION §3).

Ninguno ejecuta nada: leer bytes, decodificarlos y recorrer una estructura de datos no ejecuta
código. El HTML se convierte en texto con `html.parser`, el analizador de la biblioteca estándar:
no hay motor de plantillas, no se sigue ningún recurso externo y no se interpreta ningún script.

Lo que sale de aquí es texto **con estructura**, no una transcripción perfecta: las secciones dicen
de dónde viene cada tramo y los avisos dicen qué se descartó.
"""

from __future__ import annotations

import csv
import io
import json
from dataclasses import dataclass
from pathlib import Path

from bs4 import BeautifulSoup, Comment

from opofuente.domain.extraction import (
    ExtractedSection,
    ExtractionResult,
    ExtractorRef,
    Quality,
    RepresentationKind,
    RepresentationStatus,
    SectionType,
    WarningCode,
    clamp_sections,
    measure_quality,
    merge_warnings,
    normalise_text,
    truncate_text,
)
from opofuente.infrastructure.extractors.base import (
    DetectedFormat,
    decode_with_warning,
    read_bounded,
)

#: Filas y caracteres que se muestran en una vista previa de CSV/JSON.
PREVIEW_ROWS = 40
PREVIEW_CHARS = 4000
#: Profundidad máxima del recorrido de un JSON. Más allá se avisa y se corta: no es un parser de
#: datos, es una vista previa para decidir si el fichero sirve.
MAX_JSON_DEPTH = 6
#: Tope de tramos que se sacan de un texto plano. Un fichero con miles de bloques no puede llenar
#: la base de secciones: a partir de ahí se deja de partir y el texto sigue entero en la
#: representación.
MAX_BLOCK_SECTIONS = 500


@dataclass(frozen=True, slots=True)
class _Preview:
    text: str
    sections: tuple[ExtractedSection, ...]
    warnings: tuple[WarningCode, ...]
    metadata: dict[str, object]


def _piece(text: str) -> str:
    """Tramo de HTML: normaliza y colapsa espacios **de presentación**.

    En HTML el colapso es parte del texto (el navegador muestra un bloque de espacios como uno),
    así que se unen líneas y espacios repetidos. La normalización Unicode (NFC) va antes de medir,
    porque puede **cambiar la longitud** de un tramo —una `e` seguida de un acento combinante pasa a
    ser una sola `é`— y medir antes desplazaba todas las secciones siguientes.
    """
    return normalise_text(" ".join(text.split()))


def _piece_literal(text: str) -> str:
    """Tramo de CSV o JSON: **solo** se normaliza; los espacios se conservan tal cual.

    Son datos, no presentación: `Con  dos  espacios` y `Con dos espacios` son contenidos
    distintos, y colapsarlos cambiaría el material extraído. La regla del dominio lo dice
    explícitamente (`normalise_text`: «no se colapsan espacios»).
    """
    return normalise_text(text)


def _finish(
    *,
    kind: RepresentationKind,
    text: str,
    sections: tuple[ExtractedSection, ...],
    extractor: ExtractorRef,
    warnings: tuple[WarningCode, ...],
    max_chars: int,
    metadata: dict[str, object] | None = None,
    page_count: int | None = None,
) -> ExtractionResult:
    """Cierra un resultado: normaliza, recorta, ajusta las secciones y mide la calidad.

    El orden importa: los extractores miden sus tramos sobre piezas **ya normalizadas** (`_piece`) y
    aquí se ajustan al texto final con `clamp_sections`, porque además el texto se recorta. Sin lo
    primero, un offset apuntaba a otro contenido; sin lo segundo, podía caerse fuera del texto.
    """
    normalised = normalise_text(text)
    trimmed, truncation = truncate_text(normalised, max_chars=max_chars)
    secciones = clamp_sections(sections, char_count=len(trimmed))
    quality = measure_quality(trimmed, kind=kind)
    status = RepresentationStatus.EXTRACTED if trimmed.strip() else RepresentationStatus.EMPTY
    return ExtractionResult(
        kind=kind,
        status=status,
        text=trimmed,
        extractor=extractor,
        sections=secciones,
        page_count=page_count,
        quality=quality.quality,
        warnings=merge_warnings(warnings, truncation, quality.warnings),
        metadata=metadata or {},
    )


def _read_text_file(
    path: Path, *, max_bytes: int
) -> tuple[str, tuple[WarningCode, ...], bool, bool]:
    """Lee un fichero de texto con tope de bytes.

    Devuelve el texto decodificado, los avisos, si hubo que recodificar y si el fichero era más
    grande que el límite (en cuyo caso se lee el principio y se dice, en lugar de cargarlo entero).
    """
    data, truncated = read_bounded(path, max_bytes=max_bytes)
    text, recoded = decode_with_warning(data)
    warnings: list[WarningCode] = []
    if recoded:
        warnings.append(WarningCode.LANGUAGE_UNKNOWN)
    if truncated:
        warnings.append(WarningCode.TRUNCATED)
    return text, tuple(warnings), recoded, truncated


class PlainTextExtractor:
    """TXT/MD: texto plano. En Markdown, los encabezados se convierten en secciones."""

    name = "plain_text"
    version = "1"

    def __init__(self, *, max_chars: int, max_bytes: int) -> None:
        self._max_chars = max_chars
        self._max_bytes = max_bytes

    def extract(self, path: Path, *, detected: DetectedFormat) -> ExtractionResult:
        text, warnings, recoded, truncated = _read_text_file(path, max_bytes=self._max_bytes)
        # Las secciones se calculan sobre el **texto normalizado**: es el que se guarda, así que es
        # el único sobre el que un offset significa algo.
        normalised = normalise_text(text)
        sections = (
            _markdown_sections(normalised)
            if detected.suffix in {".md", ".markdown"}
            else _block_sections(normalised)
        )
        return _finish(
            kind=RepresentationKind.NATIVE_TEXT,
            text=normalised,
            sections=sections,
            extractor=ExtractorRef(self.name, self.version),
            warnings=warnings,
            max_chars=self._max_chars,
            metadata={
                "encoding": "cp1252" if recoded else "utf-8",
                "sections": len(sections),
                "read_truncated": truncated,
            },
        )


def _block_sections(text: str) -> tuple[ExtractedSection, ...]:
    """Tramos de un texto plano: **uno por bloque separado por una línea en blanco**.

    A nada se le llama «título»: en un texto plano no hay forma de saber qué línea es un encabezado
    sin adivinar, y adivinar jerarquía está prohibido en este proyecto. Cada bloque es un tramo con
    sus offsets, que es lo que permite citar un fragmento concreto y comparar dos versiones del
    mismo texto.

    Un fichero sin líneas en blanco produce **un** tramo con todo el texto, y uno vacío no produce
    ninguno: mejor una sección que ninguna, nunca una inventada de más.
    """
    sections: list[ExtractedSection] = []
    inicio: int | None = None
    fin = 0
    offset = 0
    position = 0
    for line in text.splitlines(keepends=True):
        if line.strip() == "":
            if inicio is not None:
                position += 1
                sections.append(_tramo(position, inicio, fin))
                inicio = None
        else:
            if inicio is None:
                inicio = offset
            fin = offset + len(line.rstrip("\r\n"))
        offset += len(line)
        if len(sections) >= MAX_BLOCK_SECTIONS:
            return tuple(sections)
    if inicio is not None:
        position += 1
        sections.append(_tramo(position, inicio, fin))
    return tuple(sections)


def _tramo(position: int, char_start: int, char_end: int) -> ExtractedSection:
    return ExtractedSection(
        section_type=SectionType.PARAGRAPH,
        position=position,
        char_start=char_start,
        char_end=char_end,
    )


def _markdown_sections(text: str) -> tuple[ExtractedSection, ...]:
    """Secciones de un Markdown: los encabezados `#` marcan los cortes."""
    sections: list[ExtractedSection] = []
    offset = 0
    position = 0
    for line in text.splitlines(keepends=True):
        stripped = line.lstrip()
        if stripped.startswith("#"):
            hashes = len(stripped) - len(stripped.lstrip("#"))
            title = stripped[hashes:].strip()
            if title:
                position += 1
                sections.append(
                    ExtractedSection(
                        section_type=SectionType.TITLE if hashes == 1 else SectionType.HEADING,
                        position=position,
                        char_start=offset,
                        char_end=offset + len(line),
                        title=title,
                    )
                )
        offset += len(line)
    return tuple(sections)


class CsvPreviewExtractor:
    """CSV/TSV: vista previa tabular con el separador y la codificación detectados.

    No interpreta columnas ni adivina cabeceras semánticas: eso es el asistente de columnas, que
    pertenece al importador de preguntas (S06).
    """

    name = "csv_preview"
    version = "1"

    def __init__(self, *, max_chars: int, max_bytes: int, max_rows: int = PREVIEW_ROWS) -> None:
        self._max_chars = max_chars
        self._max_bytes = max_bytes
        self._max_rows = max_rows

    def extract(self, path: Path, *, detected: DetectedFormat) -> ExtractionResult:
        text, warnings, recoded, read_truncated = _read_text_file(path, max_bytes=self._max_bytes)
        delimiter = _detect_delimiter(text, detected.suffix)
        rows = list(csv.reader(io.StringIO(text), delimiter=delimiter))
        preview = rows[: self._max_rows]
        lines = [_piece_literal(delimiter.join(cell.strip() for cell in row)) for row in preview]
        avisos = list(warnings)
        if len(rows) > len(preview):
            avisos.append(WarningCode.TRUNCATED)
            lines.append(f"… {len(rows) - len(preview)} filas más")
        body = "\n".join(lines)
        section = ExtractedSection(
            section_type=SectionType.TABLE,
            position=1,
            char_start=0,
            char_end=len(body),
            title=f"{len(rows)} filas y {len(rows[0]) if rows else 0} columnas",
            label=delimiter,
        )
        return _finish(
            kind=RepresentationKind.CSV_PREVIEW,
            text=body,
            sections=(section,),
            extractor=ExtractorRef(self.name, self.version),
            warnings=tuple(avisos),
            max_chars=self._max_chars,
            metadata={
                "delimiter": delimiter,
                "rows": len(rows),
                "columns": len(rows[0]) if rows else 0,
                "encoding": "cp1252" if recoded else "utf-8",
                "read_truncated": read_truncated,
            },
        )


def _detect_delimiter(text: str, suffix: str) -> str:
    """Separador por contenido; la extensión `.tsv` solo desempata."""
    sample = [line for line in text.splitlines() if line.strip()][:5]
    if not sample:
        return "\t" if suffix == ".tsv" else ";"
    best = max((";", ",", "\t", "|"), key=lambda candidate: _delimiter_score(sample, candidate))
    if _delimiter_score(sample, best) == 0:
        return "\t" if suffix == ".tsv" else ";"
    return best


def _delimiter_score(sample: list[str], delimiter: str) -> int:
    counts = [line.count(delimiter) for line in sample]
    if counts[0] == 0 or len(set(counts)) != 1:
        return 0
    return counts[0] * len(sample)


class JsonPreviewExtractor:
    """JSON: claves y valores de los primeros niveles, con profundidad acotada."""

    name = "json_preview"
    version = "1"

    def __init__(self, *, max_chars: int, max_bytes: int, max_depth: int = MAX_JSON_DEPTH) -> None:
        self._max_chars = max_chars
        self._max_bytes = max_bytes
        self._max_depth = max_depth

    def extract(self, path: Path, *, detected: DetectedFormat) -> ExtractionResult:
        data, truncated = read_bounded(path, max_bytes=self._max_bytes)
        if truncated:
            # Un JSON hay que parsearlo entero para describirlo: si no cabe en el límite, se dice y
            # no se intenta. Antes se cargaba el fichero completo en memoria y un JSON enorme podía
            # agotarla; el material admite ficheros de cientos de megabytes.
            return ExtractionResult(
                kind=RepresentationKind.JSON_PREVIEW,
                status=RepresentationStatus.FAILED,
                text="",
                extractor=ExtractorRef(self.name, self.version),
                quality=Quality.FAILED,
                warnings=(WarningCode.TOO_LARGE,),
                metadata={"limit_bytes": self._max_bytes},
            )
        text, recoded = decode_with_warning(data)
        warnings: list[WarningCode] = []
        if recoded:
            warnings.append(WarningCode.LANGUAGE_UNKNOWN)
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            return ExtractionResult(
                kind=RepresentationKind.JSON_PREVIEW,
                status=RepresentationStatus.FAILED,
                text="",
                extractor=ExtractorRef(self.name, self.version),
                quality=Quality.FAILED,
                warnings=merge_warnings((WarningCode.MALFORMED_STRUCTURE,), tuple(warnings)),
            )
        lines, depth_cut = _describe(parsed, depth=1, max_depth=self._max_depth)
        if depth_cut:
            warnings.append(WarningCode.TRUNCATED)
        # Cada línea se normaliza antes de unirse: el tramo se mide sobre el texto final.
        cuerpo = "\n".join(_piece_literal(line) for line in lines)
        body, truncation = truncate_text(cuerpo, max_chars=PREVIEW_CHARS)
        section = ExtractedSection(
            section_type=SectionType.METADATA,
            position=1,
            char_start=0,
            char_end=len(body),
            title="estructura JSON",
        )
        return _finish(
            kind=RepresentationKind.JSON_PREVIEW,
            text=body,
            sections=(section,),
            extractor=ExtractorRef(self.name, self.version),
            warnings=merge_warnings(tuple(warnings), truncation),
            max_chars=self._max_chars,
            metadata={"top_level": type(parsed).__name__},
        )


def _describe(value: object, *, depth: int, max_depth: int) -> tuple[list[str], bool]:
    """Convierte una estructura JSON en líneas `clave: valor` con sangría por profundidad."""
    indent = "  " * (depth - 1)
    lines: list[str] = []
    cut = False
    if isinstance(value, dict):
        for key, item in value.items():
            if isinstance(item, (dict, list)):
                if depth >= max_depth:
                    lines.append(f"{indent}{key}: <{type(item).__name__} sin detallar>")
                    cut = True
                    continue
                lines.append(f"{indent}{key}:")
                nested, nested_cut = _describe(item, depth=depth + 1, max_depth=max_depth)
                lines.extend(nested)
                cut = cut or nested_cut
            else:
                lines.append(f"{indent}{key}: {_scalar(item)}")
    elif isinstance(value, list):
        for index, item in enumerate(value[:20]):
            if isinstance(item, (dict, list)):
                if depth >= max_depth:
                    lines.append(f"{indent}[{index}]: <{type(item).__name__} sin detallar>")
                    cut = True
                    continue
                lines.append(f"{indent}[{index}]:")
                nested, nested_cut = _describe(item, depth=depth + 1, max_depth=max_depth)
                lines.extend(nested)
                cut = cut or nested_cut
            else:
                lines.append(f"{indent}[{index}]: {_scalar(item)}")
        if len(value) > 20:
            lines.append(f"{indent}… {len(value) - 20} elementos más")
            cut = True
    else:
        lines.append(f"{indent}{_scalar(value)}")
    return lines, cut


def _scalar(value: object) -> str:
    if value is None:
        return "(nulo)"
    if isinstance(value, bool):
        return "sí" if value else "no"
    return str(value)


#: Etiquetas que no aportan contenido: navegación, avisos y, sobre todo, código.
DROPPED_TAGS = (
    "script",
    "style",
    "noscript",
    "template",
    "svg",
    "canvas",
    "iframe",
    "object",
    "embed",
    "nav",
    "footer",
    "aside",
    "form",
)
#: Etiquetas cuyo contenido sí es texto del documento.
BLOCK_TAGS = {
    "h1": SectionType.TITLE,
    "h2": SectionType.HEADING,
    "h3": SectionType.HEADING,
    "h4": SectionType.HEADING,
    "h5": SectionType.HEADING,
    "h6": SectionType.HEADING,
    "p": SectionType.PARAGRAPH,
    "li": SectionType.LIST,
    "table": SectionType.TABLE,
    "article": SectionType.ARTICLE,
    "pre": SectionType.PARAGRAPH,
    "blockquote": SectionType.PARAGRAPH,
}


class HtmlTextExtractor:
    """HTML: texto visible, sin scripts, sin estilos y sin navegación repetida.

    Se usa `html.parser` (biblioteca estándar) a propósito: no resuelve entidades externas, no
    descarga nada y no interpreta el documento más allá de su estructura. El HTML **nunca** se
    ejecuta ni se previsualiza como contenido activo (09_SECURITY §3).
    """

    name = "html_text"
    version = "1"

    def __init__(self, *, max_chars: int, max_bytes: int) -> None:
        self._max_chars = max_chars
        self._max_bytes = max_bytes

    def extract(self, path: Path, *, detected: DetectedFormat) -> ExtractionResult:
        text, warnings, _recoded, read_truncated = _read_text_file(path, max_bytes=self._max_bytes)
        soup = BeautifulSoup(text, "html.parser")

        avisos = list(warnings)
        if soup.find("script"):
            avisos.append(WarningCode.SCRIPT_REMOVED)
        if soup.find(["iframe", "object", "embed", "form"]):
            avisos.append(WarningCode.ACTIVE_CONTENT_REMOVED)
        for comment in soup.find_all(string=lambda value: isinstance(value, Comment)):
            comment.extract()
        for tag in soup.find_all(DROPPED_TAGS):
            tag.decompose()

        title = _piece(soup.title.get_text(strip=True)) if soup.title else None
        # El cuerpo se construye **antes** de calcular las secciones: el título se antepone como
        # cabecera del texto, así que los offsets tienen que contar con él. Calcularlos antes y
        # añadir el título después desplazaba todas las secciones.
        pieces: list[tuple[str, SectionType, str | None, str | None]] = []
        for element in soup.find_all(list(BLOCK_TAGS)):
            if element.find_parent(["table", "li", "p", "h1", "h2", "h3", "h4", "h5", "h6"]):
                # Se queda el bloque de más arriba: los hijos ya van dentro de su texto.
                continue
            piece = _piece(element.get_text(" ", strip=True))
            if not piece:
                continue
            section_type = BLOCK_TAGS[element.name]
            label = None
            if element.name == "table":
                first_row = element.find("tr")
                if first_row is not None:
                    label = _piece(
                        " | ".join(
                            cell.get_text(" ", strip=True)
                            for cell in first_row.find_all(["th", "td"])
                        )
                    )
            titulo = (
                piece[:120] if section_type in {SectionType.TITLE, SectionType.HEADING} else None
            )
            pieces.append((piece, section_type, titulo, label))

        prefix = f"{title}\n\n" if title else ""
        body = prefix + "\n".join(piece for piece, _type, _title, _label in pieces)
        sections: list[ExtractedSection] = []
        offset = len(prefix)
        for position, (piece, section_type, titulo, label) in enumerate(pieces, start=1):
            sections.append(
                ExtractedSection(
                    section_type=section_type,
                    position=position,
                    char_start=offset,
                    char_end=offset + len(piece),
                    title=titulo,
                    label=label,
                )
            )
            offset += len(piece) + 1

        return _finish(
            kind=RepresentationKind.HTML_TEXT,
            text=body,
            sections=tuple(sections),
            extractor=ExtractorRef(self.name, self.version),
            warnings=tuple(avisos),
            max_chars=self._max_chars,
            metadata={
                "title": title,
                "blocks": len(sections),
                "read_truncated": read_truncated,
            },
        )
