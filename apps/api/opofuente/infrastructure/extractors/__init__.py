"""Registro de extractores: qué se extrae, con qué y qué se conserva sin extraer.

Cinco decisiones que se toman aquí y en ningún otro sitio:

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
  miembro se trata por separado, hasta la profundidad configurada;
- **cuando no hay texto del material y hay OCR, se OCRiza** (ver `extract`): una sola vez, en un
  solo sitio, y con la sonda del binario como única puerta.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path

from opofuente.config import Settings
from opofuente.domain.errors import InvariantViolationError
from opofuente.domain.extraction import (
    ExtractionResult,
    RepresentationKind,
    RepresentationStatus,
    WarningCode,
    merge_warnings,
)
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
from opofuente.infrastructure.extractors.ocr import OcrExtractor
from opofuente.infrastructure.extractors.pdf import PdfTextExtractor
from opofuente.infrastructure.extractors.text_files import (
    CsvPreviewExtractor,
    HtmlTextExtractor,
    JsonPreviewExtractor,
    PlainTextExtractor,
)
from opofuente.infrastructure.ocr import TesseractOcr, tesseract_from_settings
from opofuente.infrastructure.safe_zip import ZipLimits

#: Familias que se conservan sin extraer, con el motivo que se muestra al usuario (DEBT-008).
PRESERVED_FAMILIES: dict[str, str] = {
    "spreadsheet": "hoja de cálculo: se conserva, todavía no se extrae",
    "presentation": "presentación: se conserva, todavía no se extrae",
    "epub": "libro electrónico: se conserva, todavía no se extrae",
}

#: Familias en las que tiene sentido OCRizar cuando no hay texto nativo: un PDF escaneado y una
#: imagen. Un DOCX sin texto o un TXT vacío no son un escaneo, y pasarlos por OCR sería buscarle
#: tres pies al gato (y, en el caso del TXT, inventar una imagen que no existe).
_OCR_FAMILIES = frozenset({"pdf", "image"})

#: Avisos que describen el **contenido** de una representación, y que por tanto **no** se arrastran
#: a la del OCR: `measure_quality` los vuelve a medir sobre el texto reconocido. Arrastrar un
#: `empty_text` a una representación que sí tiene texto es decir en la interfaz lo contrario de lo
#: que ha pasado (medido: un escaneo de 1675 caracteres salía con «sin texto» entre sus avisos).
_CONTENT_WARNINGS = frozenset(
    {
        WarningCode.EMPTY_TEXT,
        WarningCode.LOW_USEFUL_TEXT,
        WarningCode.HIGH_SYMBOL_RATIO,
        WarningCode.REPEATED_LINES,
    }
)

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

    def __init__(
        self,
        settings: Settings,
        *,
        ocr: TesseractOcr | None = None,
    ) -> None:
        self._settings = settings
        #: OCR disponible: se construye desde la configuración, pero **solo cuenta si su sonda
        #: pasa** (binario presente y con el idioma pedido). Así, tener una ruta escrita en el
        #: `.env` no convierte a la aplicación en una que lee escaneos. No hay forma de declararlo
        #: desde fuera: el único camino es que la sonda pase.
        self._ocr_extractor: OcrExtractor | None = None
        candidato = ocr if ocr is not None else tesseract_from_settings(settings)
        if candidato is not None and candidato.probe().available:
            self._ocr_extractor = OcrExtractor(
                ocr=candidato,
                max_chars=settings.max_representation_chars,
                max_pages=settings.max_pdf_pages,
            )
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
                # Lo que importa es si el OCR **está en condiciones** de usarse, no si hay una ruta
                # escrita: si la sonda no pasa, la imagen tiene que decirlo con su aviso.
                ocr_configured=self._ocr_extractor is not None,
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

        **Cuando no hay texto del material y hay OCR, se OCRiza.** La decisión se toma aquí, en un
        solo sitio, y con dos reglas:

        - un PDF con capa de texto **no** pasa por OCR: el OCR es otra representación y no se
          fusiona con el nativo (04_INGESTION §5);
        - si el OCR no está configurado o su sonda no pasa, se devuelve el resultado nativo tal
          cual (con su aviso de `ocr_not_executed`/`empty_text`), que es lo honesto: mejor decir que
          no se ha leído que devolver texto inventado.

        Los avisos del resultado nativo que siguen siendo ciertos se **conservan** en el del OCR: si
        la página venía sin capa de texto, eso se sigue sabiendo.
        """
        resolved = plan if plan is not None else self.plan(path)
        if resolved.extractor is None or resolved.detected is None:
            raise InvariantViolationError(
                f"ese artefacto no se extrae ({resolved.action}): {resolved.reason}"
            )
        nativo = resolved.extractor.extract(path, detected=resolved.detected)
        if self._ocr_extractor is None or _trae_texto_del_material(nativo):
            return nativo
        # Sin texto del material: una imagen siempre; un PDF solo si de verdad no trae nada.
        if resolved.detected.family not in _OCR_FAMILIES:
            return nativo
        reconocido = self._ocr_extractor.extract(path, detected=resolved.detected)
        if reconocido.status is RepresentationStatus.FAILED:
            # El OCR existe pero falló: el aviso del OCR es el que informa, y se conserva el nativo.
            return replace(
                nativo,
                warnings=merge_warnings(nativo.warnings, reconocido.warnings),
                metadata={**nativo.metadata, **reconocido.metadata},
            )
        return replace(
            reconocido,
            warnings=merge_warnings(_sin_contenido(nativo.warnings), reconocido.warnings),
            ocr_candidate=True,
        )


def _sin_contenido(warnings: tuple[WarningCode, ...]) -> tuple[WarningCode, ...]:
    """Los avisos del nativo que siguen siendo ciertos del texto reconocido.

    Lo que describe **su** contenido (`empty_text`, `low_useful_text`…) se queda fuera: de eso ya
    informa la medida de calidad del propio OCR.
    """
    return tuple(code for code in warnings if code not in _CONTENT_WARNINGS)


def _trae_texto_del_material(resultado: ExtractionResult) -> bool:
    """¿El resultado nativo trae texto **del documento**, o solo metadatos?

    Los metadatos de una imagen no son su texto (lo dice el propio tipo de representación): que se
    sepan sus píxeles no la convierte en un documento leído. Confundir una cosa con la otra dejaba
    las imágenes sin OCR cuando sí estaba configurado, porque su resumen de metadatos contaba como
    «texto nativo» y el OCR nunca llegaba a ejecutarse.
    """
    return resultado.has_text and resultado.kind is not RepresentationKind.IMAGE_METADATA
