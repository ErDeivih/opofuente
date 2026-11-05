"""Equivalencias entre un nodo publicado y un nodo del temario común (B-003).

Una equivalencia dice qué tema del temario común corresponde a un tema del programa publicado por
una convocatoria (`ESPECIFICACION.md` §5.7). Su estado decide si se aplica o no:

- `accepted`: se guarda como decidida y **se usa** para re-apuntar el material
  (`curriculum_mappings`) y los fallos del alumno (`learning_errors`) del nodo publicado al nodo
  común;
- `proposed`: se guarda para revisión humana y **no se aplica sola**; es la respuesta a «lo dudoso
  se queda como está y se revisa» (O3);
- `rejected`: consta que se descartó.

El emparejamiento es una decisión de producto, no una heurística: por eso el fixture es curado y
cada fila lleva su nota de por qué se propone o se acepta.
"""

from __future__ import annotations

from dataclasses import dataclass

from opofuente.domain.errors import InvariantViolationError

#: Relación entre el nodo publicado (origen) y el nodo común (destino).
EQUIVALENCE_RELATIONS = ("equivalent", "subset", "superset", "partial")
#: Estado de la equivalencia: solo `accepted` se aplica al material.
EQUIVALENCE_STATUSES = ("proposed", "accepted", "rejected")


@dataclass(frozen=True, slots=True)
class EquivalenceRow:
    """Una fila del fixture de equivalencias, con su motivo."""

    source_path: str
    target_path: str
    relation: str
    confidence: float
    status: str
    evidence_note: str


@dataclass(frozen=True, slots=True)
class EquivalenceFixture:
    """El juego completo de equivalencias de un programa publicado a una versión del común."""

    source_version_code: str
    target_version_code: str
    rows: tuple[EquivalenceRow, ...]


def validate_equivalences(fixture: EquivalenceFixture) -> None:
    """Comprueba el fixture; los nodos concretos se resuelven contra la base al aplicarlo."""
    if not fixture.source_version_code.strip() or not fixture.target_version_code.strip():
        raise InvariantViolationError(
            "las equivalencias deben declarar la versión de origen y la de destino"
        )
    if fixture.source_version_code == fixture.target_version_code:
        raise InvariantViolationError("las equivalencias no pueden unir una versión consigo misma")
    if not fixture.rows:
        raise InvariantViolationError("el fixture de equivalencias está vacío")

    vistas: set[str] = set()
    for fila in fixture.rows:
        if fila.source_path in vistas:
            raise InvariantViolationError(
                f"el tema publicado {fila.source_path} aparece dos veces en las equivalencias"
            )
        vistas.add(fila.source_path)
        if not fila.source_path.strip() or not fila.target_path.strip():
            raise InvariantViolationError("una equivalencia no tiene ruta de origen o de destino")
        if fila.relation not in EQUIVALENCE_RELATIONS:
            raise InvariantViolationError(
                f"{fila.source_path}: relación desconocida: {fila.relation}"
            )
        if fila.status not in EQUIVALENCE_STATUSES:
            raise InvariantViolationError(f"{fila.source_path}: estado desconocido: {fila.status}")
        if not 0.0 <= fila.confidence <= 1.0:
            raise InvariantViolationError(
                f"{fila.source_path}: la confianza {fila.confidence} no está entre 0 y 1"
            )
        if not fila.evidence_note.strip():
            raise InvariantViolationError(
                f"{fila.source_path}: la equivalencia no explica por qué se propone"
            )
