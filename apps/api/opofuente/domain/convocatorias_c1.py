"""Convocatorias de informática C1 que referencian el temario común (B-006).

El temario común no se copia por convocatoria: cada una lo **referencia** con papel `primary` y su
cita de procedencia (`ESPECIFICACION.md` §5.5). Este módulo describe el fixture que las importa y
las comprobaciones que debe cumplir antes de sembrarse.

Dos niveles de confianza, explícitos en el estado de la convocatoria:

- `draft`: entrada de un listado/agregador sin bases oficiales verificadas (por confirmar);
- `archived`: convocatoria cerrada, con enlace y estado que constan en el inventario.

No hay un tercer valor «inventado»: lo que la fuente no publica (fecha oficial, bases) se dice en
`published_at_note` o en `source_reference`, no se rellena a ojo.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from opofuente.domain.errors import InvariantViolationError

#: Estados admitidos para una convocatoria importada (los mismos del modelo).
CONVOCATORIA_IMPORT_STATUSES = ("draft", "archived")


@dataclass(frozen=True, slots=True)
class C1Source:
    id: str
    document: str
    sha256: str
    observed_at: str


@dataclass(frozen=True, slots=True)
class C1Convocatoria:
    code: str
    title: str
    administration: str | None
    territory: str | None
    official_url: str
    published_at: date
    published_at_note: str | None
    status: str
    source_reference: str
    source_id: str


@dataclass(frozen=True, slots=True)
class DiscardedRow:
    source_id: str
    row: int
    title: str
    reason: str


@dataclass(frozen=True, slots=True)
class C1ConvocatoriasFixture:
    opposition_code: str
    opposition_name: str
    opposition_description: str
    convocatorias: tuple[C1Convocatoria, ...]
    sources: tuple[C1Source, ...]
    discarded: tuple[DiscardedRow, ...]


def validate_c1_convocatorias(fixture: C1ConvocatoriasFixture) -> None:
    """Comprueba el fixture; la colisión contra la base se resuelve al sembrarlo."""
    if not fixture.opposition_code.strip() or not fixture.opposition_name.strip():
        raise InvariantViolationError("el fixture de convocatorias C1 no declara su oposición")
    if not fixture.convocatorias:
        raise InvariantViolationError("el fixture de convocatorias C1 está vacío")
    codigos: set[str] = set()
    for convocatoria in fixture.convocatorias:
        if convocatoria.code in codigos:
            raise InvariantViolationError(
                f"la convocatoria {convocatoria.code} aparece dos veces en el fixture"
            )
        codigos.add(convocatoria.code)
        if len(convocatoria.code) > 64:
            raise InvariantViolationError(
                f"código de convocatoria demasiado largo: {convocatoria.code}"
            )
        if convocatoria.status not in CONVOCATORIA_IMPORT_STATUSES:
            raise InvariantViolationError(
                f"{convocatoria.code}: estado no admitido para una importada ("
                f"{convocatoria.status})"
            )
        if not convocatoria.title.strip():
            raise InvariantViolationError(f"{convocatoria.code}: no tiene título")
        if not convocatoria.official_url.startswith("http"):
            raise InvariantViolationError(f"{convocatoria.code}: el enlace no es una URL")
        if not convocatoria.source_reference.strip():
            raise InvariantViolationError(
                f"{convocatoria.code}: no cita de dónde sale la convocatoria"
            )
        if convocatoria.published_at.year < 2000:
            raise InvariantViolationError(
                f"{convocatoria.code}: fecha de publicación fuera de rango"
            )
        if not convocatoria.source_id.strip():
            raise InvariantViolationError(f"{convocatoria.code}: no dice de qué fuente sale")
    for fuente in fixture.sources:
        if len(fuente.sha256) != 64:
            raise InvariantViolationError(f"la fuente {fuente.id} no tiene un sha256 completo")
    for descartada in fixture.discarded:
        if not descartada.reason.strip():
            raise InvariantViolationError(
                f"la fila {descartada.row} de {descartada.source_id} se descarta sin motivo"
            )
