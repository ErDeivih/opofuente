"""Modelos del informe de re-atribución del banco (B-003).

El informe es el contrato que hace verificable la operación: una fila por equivalencia, con el nodo
publicado, el nodo común, su estado y **cada** mapeo o fallo que se movió (con su identificador y su
antes/después). Con esas filas se puede revisar la re-atribución y deshacerla: el inverso del tool
usa la lista `changes` del informe, no una suposición de cómo estaba la base.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class NodeChange:
    """Un mapeo o un fallo que cambia de nodo, con su antes y su después."""

    object_type: str
    object_id: str
    subject_type: str | None
    subject_id: str | None
    from_node_id: str
    from_path: str
    to_node_id: str
    to_path: str


@dataclass(frozen=True, slots=True)
class EquivalenceReportRow:
    """Una equivalencia del fixture y lo que le ha pasado al material que colgaba del nodo."""

    source_path: str
    target_path: str
    relation: str
    status: str
    confidence: float
    evidence_note: str
    applied: bool
    source_node_id: str
    target_node_id: str
    equivalence_id: str | None
    equivalence_action: str
    mappings: tuple[NodeChange, ...] = ()
    learning_errors: tuple[NodeChange, ...] = ()
    conflicts: tuple[str, ...] = ()
    kept_mappings: int = 0
    kept_learning_errors: int = 0


@dataclass(frozen=True, slots=True)
class RemapPlan:
    """Lo que la operación haría (o ha hecho): filas, recuentos y avisos."""

    source_version_code: str
    target_version_code: str
    rows: tuple[EquivalenceReportRow, ...]
    equivalences_created: int
    equivalences_updated: int
    equivalences_unchanged: int
    mappings_examined: int
    mappings_moved: int
    mappings_conflicts: int
    errors_examined: int
    errors_moved: int
    created_equivalence_ids: tuple[str, ...] = ()

    @property
    def changed(self) -> bool:
        return (
            self.equivalences_created > 0
            or self.equivalences_updated > 0
            or self.mappings_moved > 0
            or self.errors_moved > 0
        )

    def summary(self) -> str:
        return (
            f"{len(self.rows)} equivalencias: {self.equivalences_created} nuevas, "
            f"{self.equivalences_updated} actualizadas, {self.equivalences_unchanged} sin cambios; "
            f"mapeos movidos {self.mappings_moved}/{self.mappings_examined} "
            f"({self.mappings_conflicts} en conflicto, se quedan como están); "
            f"fallos movidos {self.errors_moved}/{self.errors_examined}"
        )


@dataclass(frozen=True, slots=True)
class InverseResult:
    """Resultado de deshacer una re-atribución desde su informe."""

    mappings_reverted: int
    errors_reverted: int
    equivalences_removed: int
    skipped: int

    def summary(self) -> str:
        return (
            f"inverso: {self.mappings_reverted} mapeos y {self.errors_reverted} fallos devueltos a "
            f"su nodo publicado, {self.equivalences_removed} equivalencias retiradas, "
            f"{self.skipped} filas no se han podido deshacer (cambiaron después)"
        )
