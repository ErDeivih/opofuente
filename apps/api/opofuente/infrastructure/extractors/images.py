"""Imágenes: se conservan siempre, se leen sus metadatos y no se inventan su texto.

Una imagen no tiene texto nativo. Sin OCR configurado, lo honesto no es guardar una representación
vacía como si fuera contenido: se guarda una representación de **metadatos** utilizable (medidas,
formato, si parece escaneada) y se marca el artefacto como **candidato a OCR**.

Con OCR configurado, la representación de OCR es **otra** representación distinta (04_INGESTION §5):
nunca se fusiona con la nativa, ni siquiera cuando la nativa no existe.

Las medidas se leen de la **cabecera** del fichero (PNG, GIF, JPEG, BMP, TIFF y WebP), no
decodificando la imagen: decodificar un PNG de 30000 por 30000 píxeles para saber que mide eso
reservaría gigabytes. Para lo que no se sabe leer con seguridad se dice que no consta, en lugar de
adivinar.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass
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
)
from opofuente.infrastructure.extractors.base import DetectedFormat, read_head

EXTRACTOR_NAME = "image_metadata"
EXTRACTOR_VERSION = "1"

#: Cabecera que se lee para sacar las medidas. Ningún formato habitual necesita más.
HEADER_BYTES = 64 * 1024


@dataclass(frozen=True, slots=True)
class ImageSize:
    """Medidas leídas de la cabecera, o «no consta» si el formato no se sabe leer con seguridad."""

    width: int | None
    height: int | None
    format: str


def read_image_size(path: Path, *, head: bytes | None = None) -> ImageSize:
    """Medidas de la imagen leídas de su cabecera, sin decodificarla."""
    data = head if head is not None else read_head(path, size=HEADER_BYTES)
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return _png(data)
    if data.startswith(b"GIF8"):
        return _gif(data)
    if data.startswith(b"BM"):
        return _bmp(data)
    if data.startswith(b"\xff\xd8"):
        return _jpeg(data)
    if data.startswith((b"II*\x00", b"MM\x00*")):
        return _tiff(data)
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return _webp(data)
    return ImageSize(None, None, "desconocido")


def _png(data: bytes) -> ImageSize:
    if len(data) < 24 or data[12:16] != b"IHDR":
        return ImageSize(None, None, "png")
    width, height = struct.unpack(">II", data[16:24])
    return ImageSize(int(width), int(height), "png")


def _gif(data: bytes) -> ImageSize:
    if len(data) < 10:
        return ImageSize(None, None, "gif")
    width, height = struct.unpack("<HH", data[6:10])
    return ImageSize(int(width), int(height), "gif")


def _bmp(data: bytes) -> ImageSize:
    if len(data) < 26:
        return ImageSize(None, None, "bmp")
    width, height = struct.unpack("<ii", data[18:26])
    return ImageSize(abs(int(width)), abs(int(height)), "bmp")


def _jpeg(data: bytes) -> ImageSize:
    """Recorre los marcadores JPEG hasta el `SOFn`, que es el que trae las medidas."""
    index = 2
    while index + 9 < len(data):
        if data[index] != 0xFF:
            index += 1
            continue
        marker = data[index + 1]
        if marker in {0xD8, 0x01} or 0xD0 <= marker <= 0xD7:
            index += 2
            continue
        if index + 4 > len(data):
            break
        length = struct.unpack(">H", data[index + 2 : index + 4])[0]
        if 0xC0 <= marker <= 0xCF and marker not in {0xC4, 0xC8, 0xCC}:
            if index + 9 > len(data):
                break
            height, width = struct.unpack(">HH", data[index + 5 : index + 9])
            return ImageSize(int(width), int(height), "jpeg")
        index += 2 + max(length, 2)
    return ImageSize(None, None, "jpeg")


def _tiff(data: bytes) -> ImageSize:
    """Lee las etiquetas 256 y 257 de la primera IFD (ImageWidth e ImageLength)."""
    little = data[:2] == b"II"
    order = "<" if little else ">"
    if len(data) < 8:
        return ImageSize(None, None, "tiff")
    offset = struct.unpack(f"{order}I", data[4:8])[0]
    if offset + 2 > len(data):
        return ImageSize(None, None, "tiff")
    count = struct.unpack(f"{order}H", data[offset : offset + 2])[0]
    width: int | None = None
    height: int | None = None
    for index in range(count):
        entry = offset + 2 + index * 12
        if entry + 12 > len(data):
            break
        tag, kind = struct.unpack(f"{order}HH", data[entry : entry + 4])
        if kind == 3:  # SHORT: el valor va en los dos primeros bytes del campo
            value = struct.unpack(f"{order}H", data[entry + 8 : entry + 10])[0]
        elif kind == 4:  # LONG
            value = struct.unpack(f"{order}I", data[entry + 8 : entry + 12])[0]
        else:
            continue
        if tag == 256:
            width = int(value)
        elif tag == 257:
            height = int(value)
        if width is not None and height is not None:
            break
    return ImageSize(width, height, "tiff")


def _webp(data: bytes) -> ImageSize:
    chunk = data[12:16]
    if chunk == b"VP8X" and len(data) >= 30:
        width = int.from_bytes(data[24:27], "little") + 1
        height = int.from_bytes(data[27:30], "little") + 1
        return ImageSize(width, height, "webp")
    if chunk == b"VP8L" and len(data) >= 25:
        bits = int.from_bytes(data[21:25], "little")
        return ImageSize((bits & 0x3FFF) + 1, ((bits >> 14) & 0x3FFF) + 1, "webp")
    return ImageSize(None, None, "webp")


class ImageMetadataExtractor:
    """Metadatos de una imagen conservada. No inventa texto."""

    name = EXTRACTOR_NAME
    version = EXTRACTOR_VERSION

    def __init__(self, *, ocr_configured: bool = False, max_bytes: int | None = None) -> None:
        self._ocr_configured = ocr_configured
        self._max_bytes = max_bytes

    def extract(self, path: Path, *, detected: DetectedFormat) -> ExtractionResult:
        size_bytes = path.stat().st_size
        if self._max_bytes is not None and size_bytes > self._max_bytes:
            # Una imagen enorme se conserva igual: solo se renuncia a describirla en memoria.
            return ExtractionResult(
                kind=RepresentationKind.IMAGE_METADATA,
                status=RepresentationStatus.PENDING,
                text="",
                extractor=ExtractorRef(self.name, self.version),
                quality=Quality.POOR,
                warnings=(WarningCode.TOO_LARGE, WarningCode.OCR_CANDIDATE),
                ocr_candidate=True,
                metadata={"size_bytes": size_bytes, "limit_bytes": self._max_bytes},
            )

        size = read_image_size(path)
        metadata: dict[str, object] = {
            "width": size.width,
            "height": size.height,
            "format": size.format,
            "size_bytes": size_bytes,
        }
        warnings: list[WarningCode] = [WarningCode.OCR_CANDIDATE]
        if not self._ocr_configured:
            warnings.append(WarningCode.OCR_NOT_EXECUTED)

        if size.width is not None and size.height is not None:
            summary = (
                f"Imagen de {size.width} por {size.height} píxeles "
                f"({size.format}, {size_bytes} bytes)"
            )
        else:
            # El texto lo dice tal cual: no se adivinan medidas que no se han podido leer.
            summary = f"Imagen en formato {size.format} ({size_bytes} bytes); medidas no consta"
        section = ExtractedSection(
            section_type=SectionType.METADATA,
            position=1,
            char_start=0,
            char_end=len(summary),
            title="metadatos de la imagen",
        )
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
