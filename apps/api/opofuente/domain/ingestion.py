"""Ingestión: lotes, entradas, incidencias y sus estados.

La máquina de estados es la de 04_INGESTION-AND-CLASSIFICATION §4, recortada a lo que existe en
S02. Los estados posteriores (`extracted`, `classified`, `review_pending`, `accepted`, `indexed`)
llegan con los extractores (S03) y la clasificación (S04) y se añadirán con su migración.
"""

from __future__ import annotations

from collections.abc import Mapping
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
    PAUSED = "paused"
    """En pausa: el lote no avanza, pero **no** se pierde lo hecho.

    No es lo mismo que `cancel_requested`: cancelar termina el lote, pausar lo deja donde está para
    seguir después. Una entrada ya copiada sigue copiada, y al reanudar el trabajo retoma por la
    primera entrada que no esté hecha (DEBT-027 §4).
    """


class ItemStatus(StrEnum):
    DISCOVERED = "discovered"
    INVENTORIED = "inventoried"
    OMITTED = "omitted"
    COPIED = "copied"
    HASHED = "hashed"
    EXTRACTED = "extracted"
    """El contenido está copiado **y** se le ha extraído texto utilizable (S03)."""

    UNSUPPORTED_PRESERVED = "unsupported_preserved"
    """Copiado y conservado sin extraer: no hay extractor para ese formato (DEBT-008)."""

    OCR_PENDING = "ocr_pending"
    """Copiada y sin texto nativo utilizable: pendiente de OCR, que no se ha ejecutado."""

    EXPANDED = "expanded"
    """Contenedor (ZIP) cuyo contenido se ha expandido en entradas propias del lote.

    El contenedor se conserva tal cual y sus miembros se tratan como material aparte, así que no
    tiene texto propio que extraer: la operación ya terminó.
    """

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
    # --- S03: extracción y conservación sin extraer (04_INGESTION §5, DEBT-008) ---
    UNSUPPORTED_PRESERVED = "unsupported_preserved"
    """Se conserva el original pero no se extrae: no hay extractor para ese formato."""

    EXTRACTION_FAILED = "extraction_failed"
    """El extractor no pudo con el documento (o el propio documento era ilegible)."""

    OCR_PENDING = "ocr_pending"
    """No hay texto nativo utilizable: queda pendiente de OCR, que no se ha ejecutado."""

    EXTRACTION_POOR_QUALITY = "extraction_poor_quality"
    """Se extrajo texto, pero la calidad no permite usarlo sin revisión."""

    UNSAFE_CONTAINER = "unsafe_container"
    """El contenedor (ZIP) se rechazó por seguridad: traversal, bomba o anidamiento excesivo."""

    CONTAINER_EXPANDED = "container_expanded"
    """El contenedor se expandió: sus miembros son entradas propias del lote."""


#: Transiciones válidas de una entrada. Cualquier otra cosa es un error de programación.
_ITEM_TRANSITIONS: dict[ItemStatus, frozenset[ItemStatus]] = {
    ItemStatus.DISCOVERED: frozenset(
        {ItemStatus.INVENTORIED, ItemStatus.OMITTED, ItemStatus.FAILED, ItemStatus.CANCELLED}
    ),
    ItemStatus.INVENTORIED: frozenset(
        {ItemStatus.COPIED, ItemStatus.FAILED, ItemStatus.CANCELLED, ItemStatus.OMITTED}
    ),
    ItemStatus.COPIED: frozenset(
        {
            ItemStatus.HASHED,
            ItemStatus.FAILED,
            ItemStatus.CANCELLED,
            ItemStatus.UNSUPPORTED_PRESERVED,
        }
    ),
    # Desde S03, una entrada copiada puede extraerse, conservarse sin extraer o expandirse (ZIP).
    # No puede volver atrás: si el fichero cambia, es otra entrada de otro lote.
    ItemStatus.HASHED: frozenset(
        {
            ItemStatus.EXTRACTED,
            ItemStatus.UNSUPPORTED_PRESERVED,
            ItemStatus.EXPANDED,
            ItemStatus.OCR_PENDING,
            ItemStatus.FAILED,
        }
    ),
    ItemStatus.EXTRACTED: frozenset(),
    ItemStatus.UNSUPPORTED_PRESERVED: frozenset(),
    ItemStatus.EXPANDED: frozenset(),
    ItemStatus.OCR_PENDING: frozenset({ItemStatus.EXTRACTED, ItemStatus.FAILED}),
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
            # S03: copiar y extraer son dos trabajos seguidos. Si al terminar la copia queda
            # extracción pendiente, el lote vuelve a la cola en lugar de darse por terminado: así
            # «terminado» significa siempre «no queda nada por hacer».
            BatchStatus.QUEUED,
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


#: Estados de una entrada cuyo contenido está **copiado** en el almacén, tenga ya texto extraído o
#: no. Es la lista única con la que el informe cuenta `copied` y `copied_bytes`: si viviera dos
#: veces, los bytes copiados se quedarían a cero en cuanto la extracción cambiara el estado.
COPIED_ITEM_STATUSES: tuple[ItemStatus, ...] = (
    ItemStatus.COPIED,
    ItemStatus.HASHED,
    ItemStatus.EXTRACTED,
    ItemStatus.EXPANDED,
    ItemStatus.OCR_PENDING,
)


#: Términos que suman el total del informe de importación. La regla vive aquí, una sola vez: la
#: usan el propio `ImportCounters` y la API al servir el informe, para que no puedan discrepar.
BALANCE_TERMS = (
    "copied",
    "pending",
    "failed",
    "cancelled",
    "source_changed",
    # S03: lo conservado sin extraer también es material que el usuario tiene, así que entra en la
    # ecuación en su propio término (DEBT-008) en lugar de esconderse dentro de `copied`.
    "preserved_unsupported",
)


@dataclass(slots=True)
class ImportCounters:
    """Contadores del informe de importación. Deben cuadrar:

    `total = copied + pending + failed + cancelled + source_changed`

    Se calculan **a partir del estado de las entradas** al terminar cada ejecución, no acumulando en
    memoria: así el informe de un lote reintentado o reanudado refleja lo que hay de verdad y no
    solo lo que hizo la última pasada. `copied` incluye el contenido repetido (el artefacto ya
    estaba en el almacén): en los dos casos el material está a salvo.

    `pending` son las entradas todavía por copiar (`inventoried`). Existe para que un lote que está
    a medias —o que acaba de reintentarse— pueda cuadrar sin mentir: antes esas entradas no
    aparecían en ninguna parte y la ecuación solo salía cuando el lote había terminado.
    """

    total: int = 0
    copied: int = 0
    copied_bytes: int = 0
    pending: int = 0
    source_changed: int = 0
    failed: int = 0
    cancelled: int = 0
    preserved_unsupported: int = 0
    """Copiadas y conservadas **sin** extraer: no hay extractor para su formato (DEBT-008)."""

    @property
    def accounted(self) -> int:
        return sum(int(getattr(self, term)) for term in BALANCE_TERMS)

    @property
    def balanced(self) -> bool:
        return self.accounted == self.total

    def to_dict(self) -> dict[str, int]:
        return {
            "total": self.total,
            "copied": self.copied,
            "copied_bytes": self.copied_bytes,
            "pending": self.pending,
            "source_changed": self.source_changed,
            "failed": self.failed,
            "cancelled": self.cancelled,
            "preserved_unsupported": self.preserved_unsupported,
        }


def balanced_counters(counters: Mapping[str, int]) -> bool:
    """¿Cuadra un informe servido como diccionario? Misma regla que `ImportCounters.balanced`.

    Un lote sin ecuación (el inventario, que no copia nada) no se comprueba aquí: eso lo decide
    quien conoce el tipo de lote.
    """
    total = counters.get("total")
    if total is None:
        return False
    return int(total) == sum(int(counters.get(term, 0)) for term in BALANCE_TERMS)


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
    #: Niveles de contenedor recorridos hasta esta entrada: 0 si viene del origen tal cual, 1 si
    #: salió de un ZIP de primer nivel. El límite de anidamiento se decide con este número.
    container_depth: int = 0
    #: De dónde salió **esta** entrada (`file`, `paste`, `url`). Viaja con la entrada porque el
    #: mismo contenido puede haber entrado por tres vías y cada una tiene su procedencia.
    origin_type: str | None = None
    #: Cómo se muestra ese origen (sin cadena de consulta en las URL). Es lo que lee el usuario.
    origin_display: str | None = None

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
