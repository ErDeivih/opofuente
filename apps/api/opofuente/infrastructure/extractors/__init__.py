"""Registro de extractores: qué se extrae, con qué y qué se conserva sin extraer.

Cuatro decisiones que se toman aquí y en ningún otro sitio:

- **el formato manda el contenido**, no la extensión (`detect_format`); si algo dice `.pdf` pero no
  empieza por `%PDF-`, se trata por lo que es de verdad;
- **la extensión se lee del nombre original**, no de la ruta del almacén: allí el fichero se llama
  como su hash, así que un `.docm`, un `.json` o un `.mp3` guardados por contenido dejaban de
  reconocerse por su sufijo y se extraían o se conservaban mal;
- **sin extractor no se inventa**: el artefacto se conserva como `unsupported_preserved` (DEBT-008:
  PPTX, XLSX, EPUB, audio, vídeo y Office con macros). Lo que **no** se conserva son los
  ejecutables: se rechazan por sufijo **y** por firma (`MZ`, ELF), porque un nombre inocente no
  convierte un binario en material de estudio;
- **un ZIP no es un documento**: se expande en sus miembros (con los límites de `safe_zip`) y cada
  miembro se trata por separado, hasta la profundidad configurada.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from opofuente.config import Settings
from opofuente.domain.errors import InvariantViolationError
from opofuente.domain.extraction import ExtractionResult
from opofuente.domain.formats import (
    DANGEROUS_SUFFIXES,
    PRESERVED_SUFFIXES,
    ZIP_SUFFIXES,
    FileSignature,
    is_dangerous_suffix,
    match_signature,
)
from opofuente.infrastructure.extractors.anki import AnkiExtractor
from opofuente.infrastructure.extractors.base import (
    DetectedFormat,
    Extractor,
    detect_format,
    read_head,
)
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

__all__ = [
    "DANGEROUS_SUFFIXES",
    "PRESERVED_FAMILIES",
    "PRESERVED_SUFFIXES",
    "ZIP_SUFFIXES",
    "ExtractionPlan",
    "ExtractorRegistry",
    "is_dangerous_suffix",
]


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
            "text": PlainTextExtractor(
                max_chars=settings.max_representation_chars, max_bytes=settings.max_text_bytes
            ),
            "csv": CsvPreviewExtractor(
                max_chars=settings.max_representation_chars, max_bytes=settings.max_text_bytes
            ),
            "json": JsonPreviewExtractor(
                max_chars=settings.max_representation_chars, max_bytes=settings.max_json_bytes
            ),
            "html": HtmlTextExtractor(
                max_chars=settings.max_representation_chars, max_bytes=settings.max_text_bytes
            ),
            "image": ImageMetadataExtractor(
                ocr_configured=(
                    ocr_configured
                    if ocr_configured is not None
                    else settings.tesseract_path is not None
                ),
                max_bytes=settings.max_image_bytes,
            ),
            "anki": AnkiExtractor(
                max_chars=settings.max_representation_chars,
                max_bytes=settings.max_text_bytes,
                limits=self._limits,
            ),
        }

    @property
    def zip_limits(self) -> ZipLimits:
        return self._limits

    def plan(
        self,
        path: Path,
        *,
        detected: DetectedFormat | None = None,
        name: str | None = None,
    ) -> ExtractionPlan:
        """Decide qué hacer con un fichero. No extrae nada todavía.

        `name` es el nombre **original** del fichero (el de la entrada, no el del almacén): de ahí
        sale la extensión con la que se aplican las políticas de sufijo.
        """
        formato = detected if detected is not None else detect_format(path, name=name)
        suffix = formato.suffix

        if suffix in DANGEROUS_SUFFIXES:
            return ExtractionPlan(
                action="refuse",
                reason="ejecutable o biblioteca: no se extrae ni se conserva",
                detected=formato,
            )
        if formato.family == "executable":
            # El nombre no lo decía, pero los bytes sí: un binario con cualquier extensión no entra.
            firma = self.refusal_by_signature(path) or "firma de ejecutable"
            return ExtractionPlan(
                action="refuse",
                reason=f"{firma}: no se extrae ni se conserva",
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

    def nested_container_refusal(self, *, container_depth: int) -> str | None:
        """¿Se puede expandir un contenedor que está a esta profundidad? Motivo, si no se puede.

        `container_depth` son los niveles de contenedor ya recorridos para llegar a esta entrada
        (0 = venía del origen tal cual). Expandirla añadiría un nivel más, y cada nivel multiplica
        el trabajo y el espacio de lo que se descomprime: es lo que aprovecha una bomba de archivos
        anidados.

        El dato está **persistido en la entrada**, no deducido del nombre: contar segmentos acabados
        en `.zip` dejaba pasar un `paquete.zip/inner.bin` que el contenido reconoce como contenedor.
        """
        if container_depth + 1 > self._settings.max_zip_depth:
            return (
                "ZIP dentro de otro ZIP: se conserva sin expandir "
                f"(profundidad máxima {self._settings.max_zip_depth})"
            )
        return None

    def refusal_by_signature(self, path: Path) -> str | None:
        """¿Tienen estos bytes firma de ejecutable? Devuelve el motivo, si la tienen.

        Se usa también al subir un fichero: un ejecutable se rechaza **antes** de copiarlo, no
        después de haberlo guardado en el almacén.
        """
        try:
            head = read_head(path)
        except OSError:
            return None
        match = match_signature(head)
        if match.signature is FileSignature.EXECUTABLE:
            return f"firma de ejecutable ({match.label})"
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
