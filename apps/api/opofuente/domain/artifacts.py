"""Artefactos: contenido identificado por el hash de sus bytes.

Reglas del modelo (03_DATA-MODEL §10):

1. un `sha256` identifica exactamente unos bytes;
2. un artefacto aceptado nunca cambia de bytes;
10. borrar un lote no borra un artefacto compartido mientras queden referencias.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum

from opofuente.domain.errors import InvariantViolationError

_SHA256 = re.compile(r"^[0-9a-f]{64}$")

#: Tipos MIME que se reconocen por extensión. Es una **pista**, no una verificación: el tipo real
#: por contenido llega con los extractores (S03).
_MEDIA_TYPES: dict[str, str] = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".doc": "application/msword",
    ".txt": "text/plain",
    ".md": "text/markdown",
    ".csv": "text/csv",
    ".json": "application/json",
    ".html": "text/html",
    ".htm": "text/html",
    ".xml": "application/xml",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".zip": "application/zip",
    ".epub": "application/epub+zip",
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
}

UNKNOWN_MEDIA_TYPE = "application/octet-stream"


class OriginType(StrEnum):
    FILE = "file"
    URL = "url"
    PASTE = "paste"
    GENERATED = "generated"


@dataclass(frozen=True, slots=True)
class Sha256:
    """Hash de contenido. Valida el formato en construcción: no hay hashes a medias."""

    value: str

    def __post_init__(self) -> None:
        if not _SHA256.match(self.value):
            raise InvariantViolationError("un sha256 son 64 caracteres hexadecimales en minúscula")

    @property
    def prefix(self) -> str:
        return self.value[:2]

    @property
    def suffix(self) -> str:
        return self.value[2:4]

    @property
    def storage_key(self) -> str:
        """Ruta relativa dentro del almacén: `sha256/ab/cd/<hash>` (02_ARCHITECTURE §5)."""
        return f"sha256/{self.prefix}/{self.suffix}/{self.value}"

    def __str__(self) -> str:
        return self.value


def media_type_for(name: str) -> str:
    """Tipo MIME probable por extensión. Nunca se usa para decidir seguridad."""
    lowered = name.lower()
    for extension, media_type in _MEDIA_TYPES.items():
        if lowered.endswith(extension):
            return media_type
    return UNKNOWN_MEDIA_TYPE


def is_recognised_media_type(media_type: str) -> bool:
    return media_type != UNKNOWN_MEDIA_TYPE


@dataclass(frozen=True, slots=True)
class StoredArtifact:
    """Resultado de guardar un contenido en el almacén."""

    sha256: Sha256
    size_bytes: int
    storage_key: str
    reused: bool

    @property
    def hash_is_new(self) -> bool:
        return not self.reused
