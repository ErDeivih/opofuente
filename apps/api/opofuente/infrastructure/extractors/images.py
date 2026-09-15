"""Imágenes: se conservan siempre, se leen sus metadatos y no se inventan su texto.

Una imagen no tiene texto nativo. Sin OCR configurado, lo honesto no es guardar una representación
vacía como si fuera contenido: se guarda una representación de **metadatos** utilizable (medidas,
formato, si parece escaneada) y se marca el artefacto como **candidato a OCR**.

Con OCR configurado, la representación de OCR es **otra** representación distinta (04_INGESTION §5):
nunca se fusiona con la nativa, ni siquiera cuando la nativa no existe.
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
)
from opofuente.infrastructure.extractors.base import DetectedFormat

EXTRACTOR_NAME = "image_metadata"
EXTRACTOR_VERSION = "1"


class ImageMetadataExtractor:
    """Metadatos de una imagen conservada. No inventa texto."""

    name = EXTRACTOR_NAME
    version = EXTRACTOR_VERSION

    def __init__(self, *, ocr_configured: bool = False) -> None:
        self._ocr_configured = ocr_configured

    def extract(self, path: Path, *, detected: DetectedFormat) -> ExtractionResult:
        try:
            pixmap = pymupdf.Pixmap(path)
            # Medidas en píxeles: `page.rect` daría puntos (72 por pulgada) y engañaría.
            metadata = {
                "width": int(pixmap.width),
                "height": int(pixmap.height),
                "components": int(pixmap.n),
                "format": path.suffix.lower().lstrip("."),
                "size_bytes": path.stat().st_size,
            }
        except (pymupdf.FileDataError, RuntimeError, ValueError):
            return ExtractionResult(
                kind=RepresentationKind.IMAGE_METADATA,
                status=RepresentationStatus.FAILED,
                text="",
                extractor=ExtractorRef(self.name, self.version),
                quality=Quality.FAILED,
                warnings=(WarningCode.EXTRACTOR_FAILED,),
            )

        summary = (
            f"Imagen de {metadata['width']} por {metadata['height']} píxeles "
            f"({metadata['format']}, {metadata['size_bytes']} bytes)"
        )
        section = ExtractedSection(
            section_type=SectionType.METADATA,
            position=1,
            char_start=0,
            char_end=len(summary),
            title="metadatos de la imagen",
        )
        warnings = [WarningCode.OCR_CANDIDATE]
        if not self._ocr_configured:
            warnings.append(WarningCode.OCR_NOT_EXECUTED)
        return ExtractionResult(
            kind=RepresentationKind.IMAGE_METADATA,
            status=RepresentationStatus.PENDING
            if not self._ocr_configured
            else (RepresentationStatus.EXTRACTED),
            text=summary,
            extractor=ExtractorRef(self.name, self.version),
            sections=(section,),
            page_count=1,
            quality=Quality.USABLE_WITH_WARNINGS if self._ocr_configured else Quality.POOR,
            warnings=tuple(warnings),
            ocr_candidate=True,
            metadata=metadata,
        )
