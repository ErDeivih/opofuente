"""Guardado del texto extraído en el árbol de datos (03_DATA-MODEL §3).

El texto de una representación **no** vive en la base de datos: vive en
`data/extracted/<representación>/texto.txt`, con su estructura en `estructura.json`, y la fila de
`extracted_representations` apunta a él con `text_storage_key`. Así el texto se puede leer por
trozos (el lector no carga megabytes) y la base sigue siendo pequeña.

Todas las escrituras pasan por `resolve_within`: nada puede salir del directorio de datos. El nombre
del fichero sale del identificador de la representación, nunca del nombre del original.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from opofuente.config import DataPaths
from opofuente.domain.errors import InvariantViolationError
from opofuente.domain.extraction import (
    REPRESENTATION_FORMAT_VERSION,
    ExtractedSection,
    ExtractionResult,
)
from opofuente.infrastructure.safe_paths import resolve_within

TEXT_FILENAME = "texto.txt"
STRUCTURE_FILENAME = "estructura.json"


@dataclass(frozen=True, slots=True)
class TextSlice:
    """Trozo de texto leído, con lo necesario para paginar sin cargarlo entero."""

    text: str
    offset: int
    limit: int
    total_chars: int
    truncated: bool


class RepresentationStore:
    """Escribe y lee el texto de las representaciones dentro del directorio de datos."""

    def __init__(self, paths: DataPaths) -> None:
        self._paths = paths

    def directory(self, representation_id: str) -> Path:
        return resolve_within(self._paths.root, self._paths.extracted / representation_id)

    def save(self, representation_id: str, result: ExtractionResult) -> str:
        """Guarda el texto y la estructura. Devuelve la clave relativa que se guarda en la base."""
        directory = self.directory(representation_id)
        directory.mkdir(parents=True, exist_ok=True)
        text_path = resolve_within(self._paths.root, directory / TEXT_FILENAME)
        text_path.write_text(result.text, encoding="utf-8", newline="\n")
        structure_path = resolve_within(self._paths.root, directory / STRUCTURE_FILENAME)
        structure_path.write_text(
            json.dumps(
                {
                    "format_version": REPRESENTATION_FORMAT_VERSION,
                    "kind": result.kind.value,
                    "page_count": result.page_count,
                    "sections": [_section_to_dict(section) for section in result.sections],
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
            newline="\n",
        )
        return f"{representation_id}/{TEXT_FILENAME}"

    def read(self, storage_key: str, *, offset: int = 0, limit: int = 20_000) -> TextSlice:
        """Lee un trozo de texto por **caracteres**.

        El texto extraído ya está acotado por configuración (2 millones de caracteres por defecto),
        así que se lee entero y se recorta: intentar buscar por desplazamiento dentro de un fichero
        de texto en UTF-8 daría offsets de bytes y partiría caracteres por la mitad.
        """
        if offset < 0 or limit <= 0:
            raise InvariantViolationError("offset y limit deben ser positivos")
        path = resolve_within(self._paths.root, self._paths.extracted / Path(storage_key))
        if not path.is_file():
            return TextSlice(text="", offset=offset, limit=limit, total_chars=0, truncated=False)
        full = path.read_text(encoding="utf-8")
        chunk = full[offset : offset + limit]
        return TextSlice(
            text=chunk,
            offset=offset,
            limit=limit,
            total_chars=len(full),
            truncated=offset + len(chunk) < len(full),
        )

    def sections(self, representation_id: str) -> tuple[ExtractedSection, ...]:
        """Lee la estructura guardada con el texto."""
        path = resolve_within(
            self._paths.root, self.directory(representation_id) / STRUCTURE_FILENAME
        )
        if not path.is_file():
            return ()
        payload = json.loads(path.read_text(encoding="utf-8"))
        return tuple(_section_from_dict(item) for item in payload.get("sections", []))


def _section_to_dict(section: ExtractedSection) -> dict[str, object]:
    return {
        "section_type": section.section_type.value,
        "position": section.position,
        "char_start": section.char_start,
        "char_end": section.char_end,
        "label": section.label,
        "title": section.title,
        "page_start": section.page_start,
        "page_end": section.page_end,
    }


def _section_from_dict(payload: dict[str, Any]) -> ExtractedSection:
    from opofuente.domain.extraction import SectionType

    return ExtractedSection(
        section_type=SectionType(str(payload["section_type"])),
        position=int(payload["position"]),
        char_start=int(payload["char_start"]),
        char_end=int(payload["char_end"]),
        label=str(payload["label"]) if payload.get("label") is not None else None,
        title=str(payload["title"]) if payload.get("title") is not None else None,
        page_start=int(payload["page_start"]) if payload.get("page_start") is not None else None,
        page_end=int(payload["page_end"]) if payload.get("page_end") is not None else None,
    )
