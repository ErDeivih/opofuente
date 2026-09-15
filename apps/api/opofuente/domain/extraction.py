"""Extracción de texto y calidad de las representaciones (04_INGESTION §5).

Qué decide este módulo, sin conocer ningún formato ni ninguna biblioteca:

- **qué es una representación** y de qué tipo (`native_text`, `ocr`, `plain_text`, `html_text`,
  `csv_preview`, `json_preview`, `image_metadata`);
- **qué secciones** tiene el texto extraído (título, encabezado, párrafo, tabla, página, artículo…)
  con sus offsets: los offsets siempre refieren al texto de **esta** representación, nunca a otra;
- **qué calidad** tiene (04_INGESTION §5): `good`, `usable_with_warnings`, `ocr_unreviewed`, `poor`
  o `failed`, medida con heurísticas explicables y con avisos en forma de código;
- **si es candidata a OCR**: una página sin texto suficiente no se inventa, se marca.

Lo que **no** decide: de qué tipo documental es el material, a qué tema pertenece ni qué autoridad
tiene. Eso es clasificación y pertenece a S04 (04_INGESTION §6-§8).

Regla de oro del proyecto aplicada aquí: el texto extraído nunca se presenta como completo ni
correcto. Lo que no se pudo leer, se recortó o se descartó aparece como aviso con su código.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from enum import StrEnum

#: Versión del formato de representación. Si cambia la forma en que se guarda el texto o las
#: secciones, sube esta versión: una representación vieja se lee con la versión con la que se creó.
REPRESENTATION_FORMAT_VERSION = 1


class RepresentationKind(StrEnum):
    """De dónde sale el texto de una representación."""

    NATIVE_TEXT = "native_text"
    """Texto que ya venía en el documento (capa de texto del PDF, DOCX, TXT…)."""

    OCR = "ocr"
    """Texto reconocido de una imagen o de una página escaneada. Nunca se fusiona con el nativo."""

    PLAIN_TEXT = "plain_text"
    """Texto pegado por el usuario."""

    HTML_TEXT = "html_text"
    """Texto visible de un HTML, ya sin scripts, estilos ni navegación."""

    CSV_PREVIEW = "csv_preview"
    """Vista previa tabular de un CSV: cabecera y primeras filas, sin interpretar columnas."""

    JSON_PREVIEW = "json_preview"
    """Vista previa de un JSON: claves y valores de los primeros niveles."""

    IMAGE_METADATA = "image_metadata"
    """Metadatos de una imagen conservada. No es texto del material."""


class RepresentationStatus(StrEnum):
    """Estado del intento de extracción."""

    EXTRACTED = "extracted"
    """Se extrajo texto (puede ser pobre, pero hay algo)."""

    PENDING = "pending"
    """No hay texto nativo utilizable y hace falta OCR, que no se ha ejecutado."""

    EMPTY = "empty"
    """El formato tiene extractor y el documento no trae texto (una imagen suelta, por ejemplo)."""

    FAILED = "failed"
    """El extractor no pudo con el documento."""


class Quality(StrEnum):
    """Calidad de una representación (04_INGESTION §5).

    Una representación `poor` no entra en RAG por defecto; decide S09, pero la etiqueta se calcula
    aquí y se guarda con la representación.
    """

    GOOD = "good"
    USABLE_WITH_WARNINGS = "usable_with_warnings"
    OCR_UNREVIEWED = "ocr_unreviewed"
    POOR = "poor"
    FAILED = "failed"


#: Calidades que no deberían indexarse sin revisión humana (04_INGESTION §5).
NOT_INDEXABLE_QUALITIES = frozenset({Quality.POOR, Quality.FAILED})


class WarningCode(StrEnum):
    """Avisos de extracción. Son códigos, no frases: la interfaz los traduce y los cuenta."""

    EMPTY_TEXT = "empty_text"
    LOW_USEFUL_TEXT = "low_useful_text"
    HIGH_SYMBOL_RATIO = "high_symbol_ratio"
    REPEATED_LINES = "repeated_lines"
    HEADER_FOOTER_REPEATED = "header_footer_repeated"
    TRUNCATED = "truncated"
    PAGES_TRUNCATED = "pages_truncated"
    OCR_CANDIDATE = "ocr_candidate"
    OCR_NOT_EXECUTED = "ocr_not_executed"
    SCRIPT_REMOVED = "script_removed"
    ACTIVE_CONTENT_REMOVED = "active_content_removed"
    EXTERNAL_ENTITY_BLOCKED = "external_entity_blocked"
    MALFORMED_STRUCTURE = "malformed_structure"
    EXTRACTOR_FAILED = "extractor_failed"
    UNSUPPORTED_FORMAT = "unsupported_format"
    LANGUAGE_UNKNOWN = "language_unknown"


class SectionType(StrEnum):
    """Tipo de tramo de texto extraído. Deliberadamente pocos y estables."""

    PAGE = "page"
    TITLE = "title"
    HEADING = "heading"
    PARAGRAPH = "paragraph"
    LIST = "list"
    TABLE = "table"
    ARTICLE = "article"
    QUESTION_BLOCK = "question_block"
    METADATA = "metadata"


#: Umbrales de calidad. Están aquí, en una constante con nombre, para poder explicarlos y cambiarlos
#: en un sitio. No son umbrales de clasificación: miden legibilidad, no acierto (04_INGESTION §8).
MIN_USEFUL_CHARS = 24
MAX_SYMBOL_RATIO = 0.35
MAX_REPETITION_RATIO = 0.6
MIN_LINES_FOR_REPETITION = 12

_WORD = re.compile(r"\w", re.UNICODE)
_SYMBOL = re.compile(r"[^\w\s]", re.UNICODE)
_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


@dataclass(frozen=True, slots=True)
class ExtractorRef:
    """Quién extrajo el texto. Guardarlo evita sobrescribir: otra versión, otra representación."""

    name: str
    version: str

    @property
    def label(self) -> str:
        return f"{self.name}@{self.version}"


@dataclass(frozen=True, slots=True)
class ExtractedSection:
    """Un tramo del texto extraído, con offsets sobre **este** texto."""

    section_type: SectionType
    position: int
    char_start: int
    char_end: int
    label: str | None = None
    title: str | None = None
    page_start: int | None = None
    page_end: int | None = None

    @property
    def length(self) -> int:
        return max(self.char_end - self.char_start, 0)


@dataclass(frozen=True, slots=True)
class TextQuality:
    """Medida explicable de la calidad del texto: los números que llevan a la etiqueta."""

    useful_chars: int
    symbol_ratio: float
    repetition_ratio: float
    line_count: int
    quality: Quality
    warnings: tuple[WarningCode, ...] = ()


@dataclass(frozen=True, slots=True)
class ExtractionResult:
    """Lo que devuelve un extractor: texto, estructura, calidad y avisos. Sin base de datos."""

    kind: RepresentationKind
    status: RepresentationStatus
    text: str
    extractor: ExtractorRef
    sections: tuple[ExtractedSection, ...] = ()
    page_count: int | None = None
    language: str | None = None
    quality: Quality = Quality.GOOD
    warnings: tuple[WarningCode, ...] = ()
    ocr_candidate: bool = False
    metadata: dict[str, object] = field(default_factory=dict)

    @property
    def char_count(self) -> int:
        return len(self.text)

    @property
    def has_text(self) -> bool:
        return bool(self.text.strip())

    @property
    def indexable(self) -> bool:
        """¿Debería entrar en el índice sin revisión? Una representación pobre o fallida, no."""
        return self.status is RepresentationStatus.EXTRACTED and self.quality not in (
            NOT_INDEXABLE_QUALITIES
        )


def normalise_text(text: str) -> str:
    """Normaliza sin destruir lo que importa.

    Se unifican finales de línea y se quitan caracteres de control, pero **no** se colapsan espacios
    ni se tocan las negaciones, la puntuación significativa ni los acentos: eso lo decidirá la
    deduplicación de S04, no la extracción.
    """
    unified = text.replace("\r\n", "\n").replace("\r", "\n")
    return _CONTROL.sub("", unicodedata.normalize("NFC", unified))


def _lines(text: str) -> list[str]:
    return [line.strip() for line in text.split("\n")]


def measure_quality(
    text: str,
    *,
    kind: RepresentationKind,
    min_useful_chars: int = MIN_USEFUL_CHARS,
) -> TextQuality:
    """Mide y etiqueta la calidad del texto extraído.

    Reglas, todas explicables:

    - sin caracteres útiles (letras o dígitos) suficientes → `poor` y aviso `low_useful_text`;
    - proporción de símbolos muy alta → `poor` (suele ser una codificación mal leída);
    - muchas líneas repetidas → `usable_with_warnings` (cabeceras o pies repetidos);
    - texto de OCR sin revisar → `ocr_unreviewed`, aunque sea legible.
    """
    useful_chars = len(_WORD.findall(text))
    symbols = len(_SYMBOL.findall(text))
    non_space = useful_chars + symbols
    symbol_ratio = (symbols / non_space) if non_space else 0.0

    all_lines = _lines(text)
    meaningful = [line for line in all_lines if line]
    if meaningful:
        unique = len(set(meaningful))
        repetition_ratio = 1.0 - (unique / len(meaningful))
    else:
        repetition_ratio = 0.0

    warnings: list[WarningCode] = []
    if not meaningful:
        warnings.append(WarningCode.EMPTY_TEXT)
        quality = Quality.POOR
    elif useful_chars < min_useful_chars:
        warnings.append(WarningCode.LOW_USEFUL_TEXT)
        quality = Quality.POOR
    elif symbol_ratio > MAX_SYMBOL_RATIO:
        warnings.append(WarningCode.HIGH_SYMBOL_RATIO)
        quality = Quality.POOR
    elif len(meaningful) >= MIN_LINES_FOR_REPETITION and repetition_ratio > MAX_REPETITION_RATIO:
        warnings.append(WarningCode.REPEATED_LINES)
        warnings.append(WarningCode.HEADER_FOOTER_REPEATED)
        quality = Quality.USABLE_WITH_WARNINGS
    else:
        quality = Quality.GOOD

    if kind is RepresentationKind.OCR and quality not in (Quality.POOR,):
        quality = Quality.OCR_UNREVIEWED

    return TextQuality(
        useful_chars=useful_chars,
        symbol_ratio=symbol_ratio,
        repetition_ratio=repetition_ratio,
        line_count=len(meaningful),
        quality=quality,
        warnings=tuple(warnings),
    )


def truncate_text(text: str, *, max_chars: int) -> tuple[str, tuple[WarningCode, ...]]:
    """Recorta el texto al límite configurado, avisando de que se ha recortado."""
    if len(text) <= max_chars:
        return text, ()
    return text[:max_chars], (WarningCode.TRUNCATED,)


def repeated_line_ratio(text: str) -> float:
    """Proporción de líneas que aparecen más de una vez (cabeceras y pies repetidos)."""
    meaningful = [line for line in _lines(text) if line]
    if not meaningful:
        return 0.0
    repeated = len(meaningful) - len(set(meaningful))
    return repeated / len(meaningful)


def merge_warnings(*groups: tuple[WarningCode, ...]) -> tuple[WarningCode, ...]:
    """Une avisos sin repetirlos y en orden estable (el primero que apareció manda)."""
    seen: dict[WarningCode, None] = {}
    for group in groups:
        for code in group:
            seen.setdefault(code, None)
    return tuple(seen)
