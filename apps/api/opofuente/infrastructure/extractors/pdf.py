"""Extractor de PDF con PyMuPDF (04_INGESTION §5).

Qué hace, en el orden que pide la especificación:

1. extrae **por página** y conserva el número de página de cada sección;
2. mide la calidad de cada página (caracteres útiles, proporción de símbolos, repetición);
3. detecta **cabeceras y pies repetidos** y lo avisa, sin tocar el original;
4. si una página no alcanza calidad suficiente, marca el documento como **candidato a OCR**;
5. nunca mezcla texto nativo con OCR: el OCR es otra representación (04_INGESTION §5).

El PDF no se renderiza ni se ejecuta: se lee su capa de texto. PyMuPDF es AGPL-3.0, uso local y
privado (DEBT-003).
"""

from __future__ import annotations

from pathlib import Path

import pymupdf

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
    repeated_line_ratio,
    truncate_text,
)
from opofuente.infrastructure.extractors.base import DetectedFormat

EXTRACTOR_NAME = "pymupdf_text"
EXTRACTOR_VERSION = "1"

#: Una página con menos caracteres útiles que esto se considera «sin texto»: o está escaneada o es
#: una imagen. Es el disparador del candidato a OCR.
MIN_USEFUL_CHARS_PER_PAGE = 40


class PdfTextExtractor:
    """Texto nativo del PDF, página a página."""

    name = EXTRACTOR_NAME
    version = EXTRACTOR_VERSION

    def __init__(self, *, max_chars: int, max_pages: int) -> None:
        self._max_chars = max_chars
        self._max_pages = max_pages

    def extract(self, path: Path, *, detected: DetectedFormat) -> ExtractionResult:
        warnings: list[WarningCode] = []
        try:
            document = pymupdf.open(path)
        except (pymupdf.FileDataError, RuntimeError, ValueError):
            return ExtractionResult(
                kind=RepresentationKind.NATIVE_TEXT,
                status=RepresentationStatus.FAILED,
                text="",
                extractor=ExtractorRef(self.name, self.version),
                quality=Quality.FAILED,
                warnings=(WarningCode.EXTRACTOR_FAILED,),
            )

        try:
            total_pages = document.page_count
            pages_to_read = min(total_pages, self._max_pages)
            if total_pages > pages_to_read:
                warnings.append(WarningCode.PAGES_TRUNCATED)

            chunks: list[str] = []
            sections: list[ExtractedSection] = []
            offset = 0
            empty_pages = 0
            page_texts: list[str] = []
            for number in range(pages_to_read):
                page = document.load_page(number)
                text = normalise_text(page.get_text("text"))
                page_texts.append(text)
                if len(text.strip()) < MIN_USEFUL_CHARS_PER_PAGE:
                    empty_pages += 1
                    if not text.strip():
                        # Página sin capa de texto: no hay nada que copiar, pero sí que avisar.
                        continue
                sections.append(
                    ExtractedSection(
                        section_type=SectionType.PAGE,
                        position=number + 1,
                        char_start=offset,
                        char_end=offset + len(text),
                        label=f"página {number + 1}",
                        page_start=number + 1,
                        page_end=number + 1,
                    )
                )
                chunks.append(text)
                offset += len(text) + 1
        finally:
            document.close()

        body = "\n".join(chunks)
        trimmed, truncation = truncate_text(body, max_chars=self._max_chars)
        # Las secciones se midieron sobre el texto completo: al recortarlo hay que ajustarlas, o un
        # tramo señalaría texto que ya no está en la representación.
        secciones = clamp_sections(tuple(sections), char_count=len(trimmed))
        quality = measure_quality(trimmed, kind=RepresentationKind.NATIVE_TEXT)

        # Cabeceras y pies: se detectan, se avisan y **no** se borran del original.
        if len(page_texts) >= 3 and repeated_line_ratio(body) > 0.5:
            warnings.append(WarningCode.HEADER_FOOTER_REPEATED)
            warnings.append(WarningCode.REPEATED_LINES)

        ocr_candidate = empty_pages > 0 or quality.quality is Quality.POOR
        if ocr_candidate:
            warnings.append(WarningCode.OCR_CANDIDATE)
        if empty_pages and not body.strip():
            # PDF escaneado: hay páginas pero ninguna tiene capa de texto.
            return ExtractionResult(
                kind=RepresentationKind.NATIVE_TEXT,
                status=RepresentationStatus.PENDING,
                text="",
                extractor=ExtractorRef(self.name, self.version),
                page_count=total_pages,
                quality=Quality.POOR,
                warnings=merge_warnings(tuple(warnings), (WarningCode.EMPTY_TEXT,)),
                ocr_candidate=True,
                metadata={"pages": total_pages, "pages_without_text": empty_pages},
            )

        status = RepresentationStatus.EXTRACTED if trimmed.strip() else RepresentationStatus.PENDING
        return ExtractionResult(
            kind=RepresentationKind.NATIVE_TEXT,
            status=status,
            text=trimmed,
            extractor=ExtractorRef(self.name, self.version),
            sections=secciones,
            page_count=total_pages,
            quality=quality.quality,
            warnings=merge_warnings(tuple(warnings), truncation, quality.warnings),
            ocr_candidate=ocr_candidate,
            metadata={
                "pages": total_pages,
                "pages_read": pages_to_read,
                "pages_without_text": empty_pages,
                "useful_chars": quality.useful_chars,
            },
        )
