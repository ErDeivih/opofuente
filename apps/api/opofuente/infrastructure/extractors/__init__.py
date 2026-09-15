"""Registro de extractores: qué se extrae, con qué y qué se conserva sin extraer.

Tres decisiones que se toman aquí y en ningún otro sitio:

- **el formato manda el contenido**, no la extensión (`detect_format`); si algo dice `.pdf` pero no
  empieza por `%PDF-`, se trata por lo que es de verdad;
- **sin extractor no se inventa**: el artefacto se conserva como `unsupported_preserved` (DEBT-008:
  PPTX, XLSX, EPUB, audio, vídeo y Office con macros). Lo que **no** se conserva son los
  ejecutables:
  esos ni siquiera llegan aquí, porque el inventario los omite por seguridad;
- **un ZIP no es un documento**: se expande en sus miembros (con los límites de safe_zip)
  y
  cada miembro se trata por separado.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from opofuente.config import Settings
from opofuente.domain.errors import InvariantViolationError
from opofuente.domain.extraction import ExtractionResult
from opofuente.infrastructure.extractors.base import DetectedFormat, Extractor, detect_format
from opofuente.infrastructure.extractors.docx import DocxTextExtractor, docx_zip_limits
from opofuente.infrastructure.extractors.images import ImageMetadataExtractor
from opofuente.infrastructure.extractors.pdf import PdfTextExtractor
from opofuente.infrastructure.extractors.text_files import (
    CsvPreviewExtractor,
    HtmlTextExtractor,
    JsonPreviewExtractor,
    PlainTextExtractor,
)
from opofuente.infrastructure.safe_zip import ZipLimits

#: Familias que se conservan sin extraer, con el motivo que se muestra al usuario (DEBT-008).
PRESERVED_FAMILIES: dict[str, str] = {
    "spreadsheet": "hoja de cálculo: se conserva, todavía no se extrae",
    "presentation": "presentación: se conserva, todavía no se extrae",
    "epub": "libro electrónico: se conserva, todavía no se extrae",
}

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

#: Sufijos que no se extraen **ni se conservan** por decisión de seguridad (04_INGESTION §2). El
#: inventario ya los omite; si alguno llegara por otra vía (dentro de un ZIP, por ejemplo) tampoco
#: se copia ni se extrae.
DANGEROUS_SUFFIXES = frozenset(
    {".exe", ".dll", ".msi", ".bat", ".cmd", ".com", ".scr", ".ps1", ".jar", ".so", ".dylib"}
)


#: Sufijos que cuentan como contenedor al medir el anidamiento. El formato se decide por contenido,
#: pero para **contar niveles** solo se puede mirar la ruta persistida de la entrada.
ZIP_SUFFIXES = frozenset({".zip"})


@dataclass(frozen=True, slots=True)
class ExtractionPlan:
    """Qué va a pasar con un artefacto: extraerlo, conservarlo sin extraer o expandirlo."""

    action: str
    """`extract`, `preserve`, `expand_zip` o `refuse`."""

    reason: str = ""
    extractor: Extractor | None = None
    detected: DetectedFormat | None = None


class ExtractorRegistry:
    """Elige el extractor por contenido y decide qué se conserva sin extraer."""

    def __init__(self, settings: Settings, *, ocr_configured: bool | None = None) -> None:
        self._settings = settings
        self._limits = ZipLimits(
            max_entries=settings.max_zip_entries,
            max_uncompressed_bytes=settings.max_zip_uncompressed_bytes,
            max_ratio=settings.max_zip_ratio,
        )
        self._extractors: dict[str, Extractor] = {
            "pdf": PdfTextExtractor(
                max_chars=settings.max_representation_chars, max_pages=settings.max_pdf_pages
            ),
            "docx": DocxTextExtractor(
                max_chars=settings.max_representation_chars,
                limits=docx_zip_limits(
                    entries=settings.max_zip_entries,
                    uncompressed_bytes=settings.max_zip_uncompressed_bytes,
                    ratio=settings.max_zip_ratio,
                ),
            ),
            "text": PlainTextExtractor(max_chars=settings.max_representation_chars),
            "csv": CsvPreviewExtractor(max_chars=settings.max_representation_chars),
            "json": JsonPreviewExtractor(max_chars=settings.max_representation_chars),
            "html": HtmlTextExtractor(max_chars=settings.max_representation_chars),
            "image": ImageMetadataExtractor(
                ocr_configured=(
                    ocr_configured
                    if ocr_configured is not None
                    else settings.tesseract_path is not None
                )
            ),
        }

    @property
    def zip_limits(self) -> ZipLimits:
        return self._limits

    def plan(self, path: Path, *, detected: DetectedFormat | None = None) -> ExtractionPlan:
        """Decide qué hacer con un fichero. No extrae nada todavía."""
        formato = detected if detected is not None else detect_format(path)
        suffix = path.suffix.lower()

        if suffix in DANGEROUS_SUFFIXES:
            return ExtractionPlan(
                action="refuse",
                reason="ejecutable o biblioteca: no se extrae ni se conserva",
                detected=formato,
            )
        if suffix in PRESERVED_SUFFIXES:
            return ExtractionPlan(
                action="preserve", reason=PRESERVED_SUFFIXES[suffix], detected=formato
            )
        if formato.family in PRESERVED_FAMILIES:
            return ExtractionPlan(
                action="preserve", reason=PRESERVED_FAMILIES[formato.family], detected=formato
            )
        if formato.family == "zip":
            return ExtractionPlan(
                action="expand_zip",
                reason="contenedor ZIP: se expande y cada miembro se trata aparte",
                detected=formato,
            )
        extractor = self._extractors.get(formato.family)
        if extractor is None:
            return ExtractionPlan(
                action="preserve",
                reason="formato sin extractor: se conserva sin extraer",
                detected=formato,
            )
        return ExtractionPlan(action="extract", extractor=extractor, detected=formato)

    def nested_container_reason(self, relative_path: str) -> str | None:
        """¿Este contenedor está dentro de otro contenedor? Devuelve el motivo si lo está.

        Cada nivel de anidamiento multiplica el trabajo y el espacio de lo que se descomprime, que
        es justo lo que aprovecha una bomba de archivos anidados; por eso el límite es de
        **profundidad** y no solo de tamaño. La cuenta se hace sobre la ruta de la entrada
        (`paquete.zip/inner.zip` → 2), que es un dato persistido: el límite no depende de que el
        trabajo se ejecute de una vez ni de que el proceso siga vivo.
        """
        profundidad = sum(
            1
            for parte in PurePosixPath(relative_path).parts
            if Path(parte).suffix.lower() in ZIP_SUFFIXES
        )
        if profundidad > self._settings.max_zip_depth:
            return (
                "ZIP dentro de otro ZIP: se conserva sin expandir "
                f"(profundidad máxima {self._settings.max_zip_depth})"
            )
        return None

    def extract(self, path: Path, *, plan: ExtractionPlan | None = None) -> ExtractionResult:
        """Extrae con el extractor que toque según el plan.

        Si el plan no es de extracción, es un error de programación del llamante: el servicio tiene
        que conservar el artefacto, no pedir texto que no existe.
        """
        resolved = plan if plan is not None else self.plan(path)
        if resolved.extractor is None or resolved.detected is None:
            raise InvariantViolationError(
                f"ese artefacto no se extrae ({resolved.action}): {resolved.reason}"
            )
        return resolved.extractor.extract(path, detected=resolved.detected)


def is_dangerous_suffix(suffix: str) -> bool:
    return suffix.lower() in DANGEROUS_SUFFIXES
