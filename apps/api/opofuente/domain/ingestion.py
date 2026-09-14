"""Ingestión: lotes, entradas, incidencias y sus estados.

La máquina de estados es la de 04_INGESTION-AND-CLASSIFICATION §4, recortada a lo que existe en
S02. Los estados posteriores (`extracted`, `classified`, `review_pending`, `accepted`, `indexed`)
llegan con los extractores (S03) y la clasificación (S04) y se añadirán con su migración.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Protocol

from opofuente.domain.errors import InvariantViolationError


class BatchKind(StrEnum):
    INVENTORY = "inventory"
    IMPORT = "import"


class BatchMode(StrEnum):
    READ_ONLY = "read_only"
    COPY = "copy"


class BatchStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCEL_REQUESTED = "cancel_requested"
    CANCELLED = "cancelled"


class ItemStatus(StrEnum):
    DISCOVERED = "discovered"
    INVENTORIED = "inventoried"
    OMITTED = "omitted"
    COPIED = "copied"
    HASHED = "hashed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class IssueSeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class IssueCode(StrEnum):
    """Motivos por los que una entrada se omite, falla o necesita atención."""

    OMITTED_BY_POLICY = "omitted_by_policy"
    OMITTED_HIDDEN = "omitted_hidden"
    OMITTED_TEMPORARY = "omitted_temporary"
    OMITTED_EXECUTABLE = "omitted_executable"
    OMITTED_DIRECTORY = "omitted_directory"
    OMITTED_UNSUPPORTED = "omitted_unsupported"
    PATH_OUTSIDE_ROOT = "path_outside_root"
    LINK_ESCAPES_ROOT = "link_escapes_root"
    UNREADABLE = "unreadable"
    SIZE_LIMIT = "size_limit"
    COPY_FAILED = "copy_failed"
    SOURCE_CHANGED = "source_changed"
    EMPTY_FILE = "empty_file"
    DUPLICATE_CONTENT = "duplicate_content"
    STORE_ERROR = "store_error"


#: Transiciones válidas de una entrada. Cualquier otra cosa es un error de programación.
_ITEM_TRANSITIONS: dict[ItemStatus, frozenset[ItemStatus]] = {
    ItemStatus.DISCOVERED: frozenset(
        {ItemStatus.INVENTORIED, ItemStatus.OMITTED, ItemStatus.FAILED, ItemStatus.CANCELLED}
    ),
    ItemStatus.INVENTORIED: frozenset(
        {ItemStatus.COPIED, ItemStatus.FAILED, ItemStatus.CANCELLED, ItemStatus.OMITTED}
    ),
    ItemStatus.COPIED: frozenset({ItemStatus.HASHED, ItemStatus.FAILED, ItemStatus.CANCELLED}),
    ItemStatus.HASHED: frozenset(),
    ItemStatus.OMITTED: frozenset(),
    ItemStatus.FAILED: frozenset({ItemStatus.INVENTORIED, ItemStatus.CANCELLED}),
    ItemStatus.CANCELLED: frozenset(),
}

_BATCH_TRANSITIONS: dict[BatchStatus, frozenset[BatchStatus]] = {
    BatchStatus.QUEUED: frozenset({BatchStatus.RUNNING, BatchStatus.CANCELLED}),
    BatchStatus.RUNNING: frozenset(
        {
            BatchStatus.SUCCEEDED,
            BatchStatus.FAILED,
            BatchStatus.CANCEL_REQUESTED,
            BatchStatus.CANCELLED,
        }
    ),
    BatchStatus.CANCEL_REQUESTED: frozenset({BatchStatus.CANCELLED, BatchStatus.FAILED}),
    BatchStatus.SUCCEEDED: frozenset(),
    BatchStatus.FAILED: frozenset({BatchStatus.QUEUED}),
    BatchStatus.CANCELLED: frozenset(),
}


def can_transition_item(current: ItemStatus, target: ItemStatus) -> bool:
    return target in _ITEM_TRANSITIONS[current]


def require_item_transition(current: ItemStatus, target: ItemStatus) -> None:
    if not can_transition_item(current, target):
        raise InvariantViolationError(f"transición de entrada inválida: {current} -> {target}")


def can_transition_batch(current: BatchStatus, target: BatchStatus) -> bool:
    return target in _BATCH_TRANSITIONS[current]


def require_batch_transition(current: BatchStatus, target: BatchStatus) -> None:
    if not can_transition_batch(current, target):
        raise InvariantViolationError(f"transición de lote inválida: {current} -> {target}")


def is_terminal_item(status: ItemStatus) -> bool:
    return not _ITEM_TRANSITIONS[status]


@dataclass(slots=True)
class InventoryCounters:
    """Contadores del informe. Cada cifra debe poder explicarse con sus entradas (04 §11)."""

    directories: int = 0
    discovered: int = 0
    inventoried: int = 0
    omitted_by_policy: int = 0
    omitted_hidden: int = 0
    omitted_temporary: int = 0
    omitted_executable: int = 0
    omitted_directory: int = 0
    omitted_unsupported: int = 0
    linked_outside_root: int = 0
    unreadable: int = 0
    total_bytes: int = 0

    def to_dict(self) -> dict[str, int]:
        return {
            "directories": self.directories,
            "discovered": self.discovered,
            "inventoried": self.inventoried,
            "omitted_by_policy": self.omitted_by_policy,
            "omitted_hidden": self.omitted_hidden,
            "omitted_temporary": self.omitted_temporary,
            "omitted_executable": self.omitted_executable,
            "omitted_directory": self.omitted_directory,
            "omitted_unsupported": self.omitted_unsupported,
            "linked_outside_root": self.linked_outside_root,
            "unreadable": self.unreadable,
            "total_bytes": self.total_bytes,
        }


@dataclass(frozen=True, slots=True)
class ImportIssue:
    code: IssueCode
    severity: IssueSeverity
    safe_message: str
    relative_path: str | None = None
    details: dict[str, object] = field(default_factory=dict)


@dataclass(slots=True)
class ImportCounters:
    """Contadores del informe de importación. Deben cuadrar: total = copiadas + fallidas + omitidas.

    Se calculan **a partir del estado de las entradas** al terminar cada ejecución, no acumulando en
    memoria: así el informe de un lote reintentado o reanudado refleja lo que hay de verdad y no
    solo lo que hizo la última pasada. `copied` incluye el contenido repetido (el artefacto ya
    estaba en el almacén): en los dos casos el material está a salvo.
    """

    total: int = 0
    copied: int = 0
    copied_bytes: int = 0
    source_changed: int = 0
    failed: int = 0
    cancelled: int = 0

    @property
    def accounted(self) -> int:
        return self.copied + self.source_changed + self.failed + self.cancelled

    @property
    def balanced(self) -> bool:
        return self.accounted == self.total

    def to_dict(self) -> dict[str, int]:
        return {
            "total": self.total,
            "copied": self.copied,
            "copied_bytes": self.copied_bytes,
            "source_changed": self.source_changed,
            "failed": self.failed,
            "cancelled": self.cancelled,
        }


class CountersLike(Protocol):
    """Cualquier contador de lote que se pueda guardar como JSON."""

    def to_dict(self) -> dict[str, int]: ...


@dataclass(frozen=True, slots=True)
class Batch:
    kind: BatchKind
    mode: BatchMode
    status: BatchStatus
    source_path_display: str
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    manifest_hash: str | None = None
    error_summary: str | None = None


@dataclass(frozen=True, slots=True)
class DiscoveredEntry:
    """Una entrada encontrada al recorrer la carpeta: incluida u omitida, con su motivo."""

    relative_path: str
    original_name: str
    size_bytes: int
    mtime: datetime | None
    media_type: str
    status: ItemStatus
    issue: ImportIssue | None = None

    @property
    def included(self) -> bool:
        return self.status is ItemStatus.INVENTORIED


@dataclass(frozen=True, slots=True)
class ScanResult:
    entries: tuple[DiscoveredEntry, ...]
    counters: InventoryCounters
    issues: tuple[ImportIssue, ...] = field(default=())

    @property
    def included(self) -> tuple[DiscoveredEntry, ...]:
        return tuple(entry for entry in self.entries if entry.included)

    @property
    def formats(self) -> dict[str, int]:
        """Formatos entre las entradas incluidas (extensión → cuántos)."""
        from pathlib import PurePosixPath

        result: dict[str, int] = {}
        for entry in self.included:
            suffix = PurePosixPath(entry.original_name).suffix.lower() or "(sin extensión)"
            result[suffix] = result.get(suffix, 0) + 1
        return dict(sorted(result.items()))

    @property
    def sample(self) -> tuple[DiscoveredEntry, ...]:
        return self.included[:25]


def manifest_hash(entries: tuple[DiscoveredEntry, ...]) -> str:
    """Huella del inventario: qué se vio, con qué tamaño y con qué fecha.

    Sirve para detectar que la carpeta cambió entre el inventario y la importación: la copia no se
    hace a ciegas sobre algo que ya no es lo que el usuario revisó.
    """
    import hashlib

    digest = hashlib.sha256()
    for entry in sorted(entries, key=lambda item: item.relative_path):
        if not entry.included:
            continue
        stamp = entry.mtime.isoformat() if entry.mtime else ""
        digest.update(f"{entry.relative_path}\x1f{entry.size_bytes}\x1f{stamp}\x1e".encode())
    return digest.hexdigest()
