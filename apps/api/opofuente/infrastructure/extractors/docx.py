"""Extractor de DOCX (04_INGESTION §3).

Tres defensas antes de dejar que python-docx abra el fichero (DEBT-004):

1. el contenedor se inspecciona como ZIP: entradas, tamaño, proporción de expansión, rutas y
   enlaces. Un DOCX es un ZIP y un DOCX bomba es un ZIP bomba;
2. el XML de `word/document.xml` se comprueba por tamaño **antes** de parsearlo;
3. python-docx parsea con `resolve_entities=False` (comprobado en su código y en las pruebas
   negativas) y lxml no resuelve entidades ni sigue la red por defecto.

Las macros no se leen nunca: un `.docm` no llega aquí, porque la política de S02/S03 lo marca como
`unsupported_preserved` y no se extrae (DEBT-008).
"""

from __future__ import annotations

import zipfile
from pathlib import Path

import docx
from docx.document import Document as DocxDocument
from docx.table import Table
from docx.text.paragraph import Paragraph

from opofuente.domain.errors import UnsafeContentError
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
from opofuente.infrastructure.extractors.base import DetectedFormat
from opofuente.infrastructure.safe_zip import ZipLimits, inspect_zip

EXTRACTOR_NAME = "python_docx_text"
EXTRACTOR_VERSION = "1"

#: Estilos de párrafo que se consideran título o encabezado.
TITLE_STYLES = frozenset({"title", "título"})
HEADING_PREFIX = "heading"


def docx_zip_limits(*, entries: int, uncompressed_bytes: int, ratio: int) -> ZipLimits:
    """Límites del contenedor DOCX, que es un ZIP."""
    return ZipLimits(
        max_entries=entries, max_uncompressed_bytes=uncompressed_bytes, max_ratio=ratio
    )


class DocxTextExtractor:
    """Párrafos, títulos y tablas de un DOCX, conservando su orden."""

    name = EXTRACTOR_NAME
    version = EXTRACTOR_VERSION

    def __init__(
        self,
        *,
        max_chars: int,
        limits: ZipLimits,
        max_document_xml_bytes: int = 8 * 1024 * 1024,
    ) -> None:
        self._max_chars = max_chars
        self._limits = limits
        self._max_document_xml_bytes = max_document_xml_bytes

    def extract(self, path: Path, *, detected: DetectedFormat) -> ExtractionResult:
        try:
            self._check_container(path)
            document = docx.Document(str(path))
        except UnsafeContentError:
            raise
        except Exception:  # cualquier fallo de python-docx es «documento ilegible»
            return ExtractionResult(
                kind=RepresentationKind.NATIVE_TEXT,
                status=RepresentationStatus.FAILED,
                text="",
                extractor=ExtractorRef(self.name, self.version),
                quality=Quality.FAILED,
                warnings=(WarningCode.EXTRACTOR_FAILED,),
            )

        sections: list[ExtractedSection] = []
        chunks: list[str] = []
        offset = 0
        position = 0
        tables = 0
        warnings: list[WarningCode] = []

        for block in _iter_blocks(document):
            if isinstance(block, Table):
                tables += 1
                piece = _table_text(block)
                section_type = SectionType.TABLE
                title = None
                label = _table_header(block)
            else:
                piece = _piece(block.text)
                if not piece:
                    continue
                style = (block.style.name or "").lower() if block.style is not None else ""
                if style in TITLE_STYLES:
                    section_type = SectionType.TITLE
                elif style.startswith(HEADING_PREFIX):
                    section_type = SectionType.HEADING
                else:
                    section_type = SectionType.PARAGRAPH
                title = piece[:120] if section_type is not SectionType.PARAGRAPH else None
                label = None
            if not piece:
                continue
            position += 1
            sections.append(
                ExtractedSection(
                    section_type=section_type,
                    position=position,
                    char_start=offset,
                    char_end=offset + len(piece),
                    title=title,
                    label=label,
                )
            )
            chunks.append(piece)
            offset += len(piece) + 1

        body = "\n".join(chunks)
        trimmed, truncation = truncate_text(body, max_chars=self._max_chars)
        # Los tramos se midieron sobre el texto completo: al recortarlo se ajustan al texto final.
        secciones = clamp_sections(tuple(sections), char_count=len(trimmed))
        quality = measure_quality(trimmed, kind=RepresentationKind.NATIVE_TEXT)
        status = RepresentationStatus.EXTRACTED if trimmed.strip() else RepresentationStatus.EMPTY
        return ExtractionResult(
            kind=RepresentationKind.NATIVE_TEXT,
            status=status,
            text=trimmed,
            extractor=ExtractorRef(self.name, self.version),
            sections=secciones,
            quality=quality.quality,
            warnings=merge_warnings(tuple(warnings), truncation, quality.warnings),
            ocr_candidate=status is RepresentationStatus.EMPTY,
            metadata={
                "blocks": len(sections),
                "tables": tables,
                "images": _image_count(document),
            },
        )

    def _check_container(self, path: Path) -> None:
        """Un DOCX es un ZIP: se inspecciona antes de abrirlo con python-docx."""
        inspect_zip(path, limits=self._limits)
        with zipfile.ZipFile(path) as archive:
            try:
                info = archive.getinfo("word/document.xml")
            except KeyError as error:
                raise UnsafeContentError(
                    "el fichero dice ser un DOCX pero no trae word/document.xml"
                ) from error
            if info.file_size > self._max_document_xml_bytes:
                raise UnsafeContentError(
                    f"el XML del DOCX supera el límite y no se parsea ({info.file_size} bytes)"
                )
            head = archive.open(info, "r").read(4096)
        if b"<!DOCTYPE" in head:
            raise UnsafeContentError("el DOCX trae un DOCTYPE: no se admiten entidades externas")


def _iter_blocks(document: DocxDocument) -> list[Paragraph | Table]:
    """Recorre párrafos y tablas en el orden real del documento."""
    from docx.oxml.ns import qn

    blocks: list[Paragraph | Table] = []
    body = document.element.body
    for child in body.iterchildren():
        if child.tag == qn("w:p"):
            blocks.append(Paragraph(child, document))
        elif child.tag == qn("w:tbl"):
            blocks.append(Table(child, document))
    return blocks


def _piece(text: str) -> str:
    """Prepara un tramo antes de medirlo: normaliza y colapsa espacios.

    Igual que en los extractores de texto: la normalización Unicode puede cambiar la longitud de un
    tramo, así que medir antes de normalizar desplazaría las secciones siguientes.
    """
    return normalise_text(" ".join(text.split()))


def _table_text(table: Table) -> str:
    rows = []
    for row in table.rows:
        cells = [_piece(cell.text) for cell in row.cells]
        rows.append(" | ".join(cells))
    return "\n".join(rows)


def _table_header(table: Table) -> str | None:
    if not table.rows:
        return None
    first = table.rows[0]
    header = " | ".join(_piece(cell.text) for cell in first.cells)
    return header or None


def _image_count(document: DocxDocument) -> int:
    try:
        return len(document.inline_shapes)
    except Exception:  # un DOCX raro no puede tumbar la extracción
        return 0
