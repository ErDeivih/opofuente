"""Extractor de OCR: texto de un escaneo o de una imagen, **aparte** del texto nativo.

La regla de 04_INGESTION §5 es explícita: el texto reconocido no se fusiona con el nativo, es **otra
representación**. Por eso este extractor tiene su propio nombre y su propia versión (el texto se
guarda identificado por extractor y tipo), y solo se usa cuando no hay texto nativo que leer:

- un PDF con capa de texto **no** pasa por OCR;
- un PDF escaneado (sin capa de texto) o con calidad pobre sí, y su representación es `ocr`;
- una imagen (foto o captura de apuntes) también.

Si el OCR no está configurado, no se llega aquí: el registro devuelve el resultado nativo con su
aviso `ocr_pending`/`empty_text`, que es lo que la aplicación hacía antes y sigue haciendo cuando no
hay Tesseract.
"""

from __future__ import annotations

from pathlib import Path

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
    truncate_text,
)
from opofuente.infrastructure.extractors.base import DetectedFormat
from opofuente.infrastructure.ocr import OcrFailedError, PdfOcrText, TesseractOcr

EXTRACTOR_NAME = "tesseract_ocr"
EXTRACTOR_VERSION = "1"


class OcrExtractor:
    """Texto reconocido por Tesseract, con la procedencia de lo que se ha usado."""

    name = EXTRACTOR_NAME
    version = EXTRACTOR_VERSION

    def __init__(self, *, ocr: TesseractOcr, max_chars: int, max_pages: int) -> None:
        self._ocr = ocr
        self._max_chars = max_chars
        self._max_pages = max_pages

    @property
    def ocr(self) -> TesseractOcr:
        return self._ocr

    def extract(self, path: Path, *, detected: DetectedFormat) -> ExtractionResult:
        try:
            if detected.family == "pdf":
                reconocido = self._ocr.text_of_pdf(path, max_pages=self._max_pages)
                texto = reconocido.text
                metadatos: dict[str, object] = {
                    "pages": reconocido.page_count,
                    "pages_read": reconocido.read_pages,
                    "dpi": self._ocr.dpi,
                    "languages": self._ocr.languages,
                }
                secciones = _secciones_por_pagina(reconocido)
                avisos = list(self._avisos_de_paginas(reconocido.read_pages, reconocido.page_count))
                paginas: int | None = reconocido.page_count
            else:
                texto = self._ocr.text_of_image(path)
                metadatos = {"dpi": self._ocr.dpi, "languages": self._ocr.languages}
                secciones = ()
                avisos = []
                # Una imagen es una página: es lo que dice también el extractor de metadatos.
                paginas = 1
        except OcrFailedError as error:
            # El OCR no se pudo hacer: se declara fallido con su motivo, no como «sin texto».
            return ExtractionResult(
                kind=RepresentationKind.OCR,
                status=RepresentationStatus.FAILED,
                text="",
                extractor=ExtractorRef(self.name, self.version),
                quality=Quality.FAILED,
                warnings=(WarningCode.EXTRACTOR_FAILED,),
                metadata={"ocr_error": str(error)[:200]},
            )

        recortado, truncamiento = truncate_text(texto, max_chars=self._max_chars)
        secciones = clamp_sections(secciones, char_count=len(recortado))
        calidad = measure_quality(recortado, kind=RepresentationKind.OCR)
        sin_texto = not recortado.strip()
        return ExtractionResult(
            kind=RepresentationKind.OCR,
            status=(RepresentationStatus.PENDING if sin_texto else RepresentationStatus.EXTRACTED),
            text=recortado,
            extractor=ExtractorRef(self.name, self.version),
            sections=secciones,
            page_count=paginas,
            quality=Quality.POOR if sin_texto else calidad.quality,
            warnings=merge_warnings(merge_warnings(tuple(avisos), truncamiento), calidad.warnings),
            metadata={**metadatos, "useful_chars": calidad.useful_chars},
        )

    def _avisos_de_paginas(self, leidas: int, totales: int) -> tuple[WarningCode, ...]:
        if totales > leidas:
            return (WarningCode.PAGES_TRUNCATED,)
        return ()


def _secciones_por_pagina(reconocido: PdfOcrText) -> tuple[ExtractedSection, ...]:
    """Una sección por página, con los offsets que le corresponden **de verdad**.

    Los tramos salen de `page_spans`, no de partir el texto por sus líneas en blanco: una tabla o un
    párrafo con un hueco no son una página nueva, y atribuir una cita a la página equivocada es peor
    que no citarla. Una página sin texto reconocido no genera sección: no hay nada que señalar.
    """
    if reconocido.read_pages <= 1:
        return ()
    secciones: list[ExtractedSection] = []
    for numero, (inicio, fin) in enumerate(reconocido.page_spans, start=1):
        if inicio >= fin:
            continue
        secciones.append(
            ExtractedSection(
                section_type=SectionType.PAGE,
                position=numero,
                char_start=inicio,
                char_end=fin,
                label=f"página {numero} (OCR)",
                page_start=numero,
                page_end=numero,
            )
        )
    return tuple(secciones)
