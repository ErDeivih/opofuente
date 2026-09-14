"""Casos de uso de ingestión: inventariar una carpeta y copiarla al almacén.

Reglas que aplica este servicio:

- el inventario **no copia nada**: solo recorre y describe (04_INGESTION §2);
- la importación sí copia, y solo después de que el usuario la confirme sobre un inventario previo;
- el origen se lee, nunca se escribe: si un fichero cambió entre el inventario y la copia, se
  detecta y se informa en vez de copiar algo que el usuario no revisó;
- la copia es idempotente: el mismo contenido no se guarda dos veces y repetir una importación
  interrumpida no duplica artefactos;
- la cancelación se comprueba entre ficheros y deja el informe cuadrado.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from opofuente.application.job_service import JobExecution
from opofuente.application.ports import (
    ArtifactStorePort,
    Clock,
    IngestionRepository,
    InventoryScanner,
    JobQueue,
)
from opofuente.application.read_models import (
    BatchDetail,
    BatchView,
    EntryPage,
    EntryView,
    IssuePage,
    IssueView,
)
from opofuente.domain.artifacts import OriginType
from opofuente.domain.errors import (
    InvalidSourceError,
    JobCancelledError,
    NotFoundError,
)
from opofuente.domain.ingestion import (
    BatchKind,
    BatchMode,
    BatchStatus,
    DiscoveredEntry,
    ImportCounters,
    ImportIssue,
    IssueCode,
    IssueSeverity,
    ItemStatus,
    manifest_hash,
)
from opofuente.domain.jobs import JobType
from opofuente.infrastructure.safe_paths import abbreviate, is_within

logger = logging.getLogger(__name__)

#: Entradas del lote que se muestran por defecto en la vista previa y en el detalle.
PREVIEW_ENTRIES = 25
PREVIEW_ISSUES = 50
#: Cada cuántos ficheros se comprueba la cancelación y se renueva el lease.
HEARTBEAT_EVERY = 10


@dataclass(frozen=True, slots=True)
class InventoryResult:
    batch: BatchView
    sample: tuple[EntryView, ...]
    formats: dict[str, int]
    issues: tuple[IssueView, ...]


class IngestionService:
    def __init__(
        self,
        *,
        repository: IngestionRepository,
        jobs: JobQueue,
        store: ArtifactStorePort,
        scanner: InventoryScanner,
        clock: Clock,
        data_root: Path,
        max_entries: int,
    ) -> None:
        self._repository = repository
        self.jobs = jobs
        self._store = store
        self._scanner = scanner
        self._clock = clock
        self._data_root = data_root
        self._max_entries = max_entries

    # ------------------------------------------------------------------ inventario

    def create_inventory(self, source_path: str) -> InventoryResult:
        """Recorre la carpeta en modo lectura y guarda el inventario. No copia nada."""
        root = self._resolve_source(source_path)
        scan = self._scanner.scan(root)
        now = self._clock.now()
        digest = manifest_hash(scan.entries)

        batch_id = self._repository.create_batch(
            kind=BatchKind.INVENTORY,
            mode=BatchMode.READ_ONLY,
            source_path_display=abbreviate(root),
            source_root=str(root),
            now=now,
            status=BatchStatus.SUCCEEDED,
            manifest_hash=digest,
        )
        self._repository.add_entries(batch_id, scan.entries)
        self._repository.add_issues(batch_id, scan.issues, now=now)
        self._repository.set_counters(batch_id, scan.counters, manifest_hash=digest)

        logger.info(
            "ingestion.inventory_created",
            extra={"event": "inventory_created", "path": abbreviate(root)},
        )
        detail = self._repository.get_batch_detail(
            batch_id, entry_limit=PREVIEW_ENTRIES, issue_limit=PREVIEW_ISSUES
        )
        if detail is None:  # pragma: no cover - se acaba de crear
            raise NotFoundError("lote", batch_id)
        return InventoryResult(
            batch=detail.batch,
            sample=tuple(
                entry for entry in detail.entries if entry.status == ItemStatus.INVENTORIED.value
            ),
            formats=detail.batch.formats,
            issues=detail.issues,
        )

    def get_inventory(self, inventory_id: str) -> InventoryResult:
        detail = self.get_batch(inventory_id)
        if detail.batch.kind != BatchKind.INVENTORY.value:
            raise NotFoundError("inventario", inventory_id)
        return InventoryResult(
            batch=detail.batch,
            sample=tuple(
                entry for entry in detail.entries if entry.status == ItemStatus.INVENTORIED.value
            ),
            formats=detail.batch.formats,
            issues=detail.issues,
        )

    # ------------------------------------------------------------------ importación

    def confirm_import(self, inventory_id: str) -> BatchView:
        """Crea el lote de importación a partir del inventario y encola el trabajo.

        Es idempotente: si ese inventario ya tiene una importación, devuelve la existente en vez de
        crear otra. Así, pulsar dos veces «Importar una copia» no duplica el trabajo.
        """
        inventory = self._repository.get_batch(inventory_id)
        if inventory is None or inventory.kind != BatchKind.INVENTORY.value:
            raise NotFoundError("inventario", inventory_id)

        existing = self._repository.find_import_for(inventory_id)
        if existing is not None:
            return existing

        source_root = self._repository.source_root_of(inventory_id)
        if source_root is None:
            raise InvalidSourceError("el inventario no conserva la carpeta de origen")

        now = self._clock.now()
        batch_id = self._repository.create_batch(
            kind=BatchKind.IMPORT,
            mode=BatchMode.COPY,
            source_path_display=inventory.source_path_display,
            source_root=source_root,
            now=now,
            status=BatchStatus.QUEUED,
            manifest_hash=inventory.manifest_hash,
            inventory_batch_id=inventory_id,
        )

        page = self._repository.list_entries(
            inventory_id, limit=self._max_entries, offset=0, status=ItemStatus.INVENTORIED
        )
        entries = tuple(
            entry for entry in page.entries if entry.status == ItemStatus.INVENTORIED.value
        )
        self._repository.add_entries(
            batch_id,
            tuple(_to_discovered(entry) for entry in entries),
            status=ItemStatus.INVENTORIED,
        )
        job, _created = self.jobs.enqueue(
            job_type=JobType.INGEST_BATCH,
            payload={"batch_id": batch_id, "inventory_batch_id": inventory_id},
            now=now,
            idempotency_key=f"ingest_batch:{batch_id}",
        )
        self._repository.set_job(batch_id, job.id)

        logger.info(
            "ingestion.import_queued",
            extra={"event": "import_queued", "job_id": job.id},
        )
        view = self._repository.get_batch(batch_id)
        if view is None:  # pragma: no cover - se acaba de crear
            raise NotFoundError("lote", batch_id)
        return view

    def retry_batch(self, batch_id: str) -> BatchView:
        """Reencola un lote fallido o cancelado. Los artefactos ya copiados se reutilizan."""
        batch = self._repository.get_batch(batch_id)
        if batch is None or batch.kind != BatchKind.IMPORT.value:
            raise NotFoundError("lote de importación", batch_id)
        now = self._clock.now()
        self._repository.set_status(batch_id, BatchStatus.QUEUED, now=now, error_summary="")
        job, _created = self.jobs.enqueue(
            job_type=JobType.INGEST_BATCH,
            payload={
                "batch_id": batch_id,
                "inventory_batch_id": batch.inventory_batch_id or "",
            },
            now=now,
            idempotency_key=f"ingest_batch:{batch_id}",
        )
        self._repository.set_job(batch_id, job.id)
        refreshed = self._repository.get_batch(batch_id)
        return refreshed if refreshed is not None else batch

    def cancel_batch(self, batch_id: str) -> BatchView:
        batch = self._repository.get_batch(batch_id)
        if batch is None:
            raise NotFoundError("lote", batch_id)
        self._repository.request_cancel(batch_id)
        if batch.job_id:
            self.jobs.request_cancel(batch.job_id, now=self._clock.now())
        refreshed = self._repository.get_batch(batch_id)
        return refreshed if refreshed is not None else batch

    # ------------------------------------------------------------------ consultas

    def list_batches(self, *, limit: int, offset: int) -> tuple[BatchView, ...]:
        return self._repository.list_batches(limit=limit, offset=offset)

    def get_batch(self, batch_id: str) -> BatchDetail:
        detail = self._repository.get_batch_detail(
            batch_id, entry_limit=PREVIEW_ENTRIES, issue_limit=PREVIEW_ISSUES
        )
        if detail is None:
            raise NotFoundError("lote", batch_id)
        return detail

    def list_entries(
        self,
        batch_id: str,
        *,
        limit: int,
        offset: int,
        status: ItemStatus | None = None,
    ) -> EntryPage:
        if self._repository.get_batch(batch_id) is None:
            raise NotFoundError("lote", batch_id)
        return self._repository.list_entries(batch_id, limit=limit, offset=offset, status=status)

    def list_issues(self, batch_id: str, *, limit: int, offset: int) -> IssuePage:
        if self._repository.get_batch(batch_id) is None:
            raise NotFoundError("lote", batch_id)
        return self._repository.list_issues(batch_id, limit=limit, offset=offset)

    def count_batch_artifacts(self, batch_id: str) -> int:
        """Cuántos artefactos distintos ha dejado el lote en el almacén."""
        return self._repository.count_batch_artifacts(batch_id)

    # ------------------------------------------------------------------ trabajo

    def run_import_job(self, execution: JobExecution) -> None:
        """Manejador del trabajo `ingest_batch`: copia las entradas al almacén por hash."""
        batch_id = str(execution.payload.get("batch_id", ""))
        batch = self._repository.get_batch(batch_id)
        if batch is None:
            raise NotFoundError("lote", batch_id)

        source_root = self._repository.source_root_of(batch_id)
        if source_root is None:
            raise InvalidSourceError("el lote no conserva la carpeta de origen")
        root = Path(source_root)

        now = self._clock.now()
        self._repository.set_status(batch_id, BatchStatus.RUNNING, now=now)
        pending = self._repository.pending_entries(batch_id)
        counters = ImportCounters(total=len(pending))
        execution.progress(0.0, "copiando")

        for index, entry in enumerate(pending, start=1):
            if execution.cancelled():
                self._finish_cancelled(batch_id, counters, tuple(pending[index - 1 :]))
                raise JobCancelledError("el lote de importación se canceló a petición del usuario")

            self._copy_entry(batch_id, root, entry, execution)
            execution.progress(index / max(len(pending), 1), f"{index}/{len(pending)}")
            if index % HEARTBEAT_EVERY == 0:
                execution.heartbeat()

        counters = self._repository.summarize_import(batch_id)
        self._repository.set_counters(batch_id, counters)
        status = BatchStatus.SUCCEEDED if counters.failed == 0 else BatchStatus.FAILED
        summary = (
            None if counters.failed == 0 else f"{counters.failed} entradas no se pudieron copiar"
        )
        self._repository.set_status(batch_id, status, now=self._clock.now(), error_summary=summary)

    def _copy_entry(
        self,
        batch_id: str,
        root: Path,
        entry: EntryView,
        execution: JobExecution,
    ) -> None:
        now = self._clock.now()
        try:
            source = (root / entry.relative_path).resolve(strict=False)
        except OSError:
            source = root / entry.relative_path
        if not is_within(root, source):
            self._record_issue(
                batch_id,
                entry,
                IssueCode.PATH_OUTSIDE_ROOT,
                IssueSeverity.ERROR,
                "La ruta resuelta queda fuera de la carpeta de origen.",
                now,
            )
            self._repository.mark_item(
                entry.id, ItemStatus.FAILED, detail="ruta fuera de la carpeta de origen"
            )
            return

        if not source.is_file():
            self._record_issue(
                batch_id,
                entry,
                IssueCode.UNREADABLE,
                IssueSeverity.ERROR,
                "El fichero ya no está en el origen.",
                now,
            )
            self._repository.mark_item(entry.id, ItemStatus.FAILED, detail="ausente en el origen")
            return

        try:
            stat = source.stat()
        except OSError:
            self._record_issue(
                batch_id,
                entry,
                IssueCode.UNREADABLE,
                IssueSeverity.ERROR,
                "No se pudo leer el fichero de origen.",
                now,
            )
            self._repository.mark_item(entry.id, ItemStatus.FAILED, detail="ilegible")
            return

        if stat.st_size != entry.size_bytes:
            self._record_issue(
                batch_id,
                entry,
                IssueCode.SOURCE_CHANGED,
                IssueSeverity.WARNING,
                "El fichero cambió después del inventario: no se copia lo que no se revisó.",
                now,
            )
            self._repository.mark_item(
                entry.id, ItemStatus.FAILED, detail="el fichero cambió después del inventario"
            )
            return

        try:
            stored = self._store.store_file(source)
        except OSError:
            self._record_issue(
                batch_id,
                entry,
                IssueCode.COPY_FAILED,
                IssueSeverity.ERROR,
                "No se pudo copiar el fichero al almacén.",
                now,
            )
            self._repository.mark_item(entry.id, ItemStatus.FAILED, detail="fallo de copia")
            return

        artifact_id, _created = self._repository.register_artifact(
            digest=stored.sha256,
            size_bytes=stored.size_bytes,
            media_type=entry.media_type or "application/octet-stream",
            storage_key=stored.storage_key,
            origin_type=OriginType.FILE,
            display_location=entry.relative_path,
            original_name=entry.original_name,
            source_path_display=f"{abbreviate(root)}/{entry.relative_path}",
            file_mtime=datetime.fromtimestamp(stat.st_mtime, tz=UTC),
            now=now,
        )
        self._repository.mark_item(
            entry.id,
            ItemStatus.HASHED,
            artifact_id=artifact_id,
            detail=f"sha256:{stored.sha256.value[:12]}",
        )

    def _finish_cancelled(
        self,
        batch_id: str,
        counters: ImportCounters,
        remaining: tuple[EntryView, ...],
    ) -> None:
        for entry in remaining:
            self._repository.mark_item(entry.id, ItemStatus.CANCELLED, detail="cancelado")
        # Los contadores se recalculan del estado real: el informe cuadra aunque el lote se
        # reintente después.
        counters = self._repository.summarize_import(batch_id)
        self._repository.set_counters(batch_id, counters)
        self._repository.set_status(batch_id, BatchStatus.CANCELLED, now=self._clock.now())
        logger.info(
            "ingestion.import_cancelled",
            extra={"event": "import_cancelled", "status_code": counters.cancelled},
        )
        if not counters.balanced:  # pragma: no cover - salvaguarda del informe
            logger.warning("ingestion.report_unbalanced", extra={"event": "report_unbalanced"})

    def _record_issue(
        self,
        batch_id: str,
        entry: EntryView,
        code: IssueCode,
        severity: IssueSeverity,
        message: str,
        now: datetime,
    ) -> None:
        self._repository.add_issues(
            batch_id,
            (
                ImportIssue(
                    code=code,
                    severity=severity,
                    safe_message=message,
                    relative_path=entry.relative_path,
                ),
            ),
            now=now,
        )

    # ------------------------------------------------------------------ validación

    def _resolve_source(self, source_path: str) -> Path:
        cleaned = source_path.strip().strip('"').strip("'")
        if not cleaned:
            raise InvalidSourceError("indica una carpeta para inventariar")
        candidate = Path(cleaned).expanduser()
        if not candidate.is_absolute():
            raise InvalidSourceError("la carpeta debe indicarse con una ruta absoluta")
        if not candidate.exists():
            raise InvalidSourceError("la carpeta indicada no existe")
        if not candidate.is_dir():
            raise InvalidSourceError("la ruta indicada no es una carpeta")
        root = candidate.resolve(strict=False)
        if is_within(self._data_root, root):
            raise InvalidSourceError(
                "esa carpeta es el directorio de datos de OpoFuente: elige la carpeta del material"
            )
        try:
            next(iter(root.iterdir()), None)
        except OSError as error:
            raise InvalidSourceError("no se puede leer esa carpeta") from error
        return root


def _to_discovered(entry: EntryView) -> DiscoveredEntry:
    """Convierte una entrada inventariada en la entrada que copiará el lote de importación.

    Se conserva el tamaño del inventario para poder detectar que el fichero cambió antes de
    copiarlo. El contenido se hashea igualmente al copiar, así que un cambio del mismo tamaño no
    pasa inadvertido en el almacén: produce otro artefacto.
    """
    return DiscoveredEntry(
        relative_path=entry.relative_path,
        original_name=entry.original_name,
        size_bytes=entry.size_bytes,
        mtime=None,
        media_type=entry.media_type or "",
        status=ItemStatus.INVENTORIED,
    )
