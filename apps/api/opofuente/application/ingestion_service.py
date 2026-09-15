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
import time
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
    InvalidBatchStateError,
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
from opofuente.infrastructure.safe_paths import abbreviate, is_within, redact_paths

logger = logging.getLogger(__name__)

#: Entradas del lote que se muestran por defecto en la vista previa y en el detalle.
PREVIEW_ENTRIES = 25
PREVIEW_ISSUES = 50
#: Cada cuánto, como mucho, se renueva el lease. Es tiempo y no número de ficheros: un solo fichero
#: grande puede tardar más que un lease entero, así que la cuenta por ficheros no protege de nada.
DEFAULT_HEARTBEAT_SECONDS = 15.0
#: Tolerancia al comparar la fecha de modificación del inventario con la del origen. Evita rechazar
#: una copia por redondeos de la base de datos, no por un cambio real.
SOURCE_MTIME_TOLERANCE_SECONDS = 1.0
#: Estados del lote desde los que tiene sentido reintentar: parado y con trabajo por hacer.
_RETRYABLE_BATCH_STATUSES = frozenset({BatchStatus.FAILED, BatchStatus.CANCELLED})


@dataclass(frozen=True, slots=True)
class InventoryResult:
    batch: BatchView
    sample: tuple[EntryView, ...]
    formats: dict[str, int]
    issues: tuple[IssueView, ...]


class _ThrottledHeartbeat:
    """Renueva el lease como mucho una vez cada `interval` segundos.

    Se apoya en el reloj monótono: da igual cuántos ficheros haya ni cuánto tarde uno solo, lo que
    importa es no dejar pasar más de `interval` segundos sin renovar. El almacén llama a
    `on_chunk` mientras copia, así que un fichero enorme tampoco deja vencer el lease.
    """

    def __init__(self, execution: JobExecution, interval: float) -> None:
        self._execution = execution
        self._interval = interval
        self._last = time.monotonic()

    def maybe(self) -> None:
        now = time.monotonic()
        if now - self._last >= self._interval:
            self._execution.heartbeat()
            self._last = now

    def on_chunk(self) -> None:
        self.maybe()


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
        heartbeat_seconds: float = DEFAULT_HEARTBEAT_SECONDS,
    ) -> None:
        self._repository = repository
        self.jobs = jobs
        self._store = store
        self._scanner = scanner
        self._clock = clock
        self._data_root = data_root
        self._max_entries = max_entries
        self._heartbeat_seconds = max(heartbeat_seconds, 1.0)

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
        # Resumen inicial desde el estado real de las entradas: un lote recién confirmado tiene
        # `total = pending`, no 0 de 0. Sin esto, entre la confirmación y la primera pasada del
        # worker el informe decía «0 de 0» y `balanced: false` sin que hubiera nada roto.
        self._repository.set_counters(batch_id, self._repository.summarize_import(batch_id))
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
        """Reencola un lote fallido o cancelado, por la fase en la que se quedó.

        Solo se puede reintentar lo que está parado y a medias: un lote que sigue trabajando no se
        toca (devolver entradas a la cola mientras el worker las está copiando descuadraría el
        informe y podría copiar dos veces), y uno que terminó bien no tiene nada que reintentar. En
        esos casos se responde 409 (`invalid_state`).

        Hay **dos fases** y cada una tiene su trabajo (esto antes era un solo camino y estaba mal):

        - entradas **sin artefacto**: no llegó a copiarse nada, así que hay que volver a copiar
          (vuelven a `inventoried` y se encola `ingest_batch`). Necesitan la carpeta de origen;
        - entradas **con artefacto**: el contenido ya está en el almacén y lo que falló fue la
          extracción, así que vuelven a `hashed` y se encola `extract_artifact`. Un lote que entró
          por ficheros subidos, texto pegado o URL **no tiene** carpeta de origen, y antes el
          reintento terminaba con «el lote no conserva la carpeta de origen».

        Las entradas cuyo fichero cambió desde el inventario **no** se recuperan para copiar: ese
        inventario ya no describe el origen y volverían a fallar; para esas hace falta un inventario
        nuevo, y el error lo dice.
        """
        batch = self._repository.get_batch(batch_id)
        if batch is None or batch.kind != BatchKind.IMPORT.value:
            raise NotFoundError("lote de importación", batch_id)
        if batch.status not in _RETRYABLE_BATCH_STATUSES:
            raise InvalidBatchStateError(
                batch.status,
                tuple(status.value for status in _RETRYABLE_BATCH_STATUSES),
            )
        now = self._clock.now()
        recovered = self._repository.reset_items_for_retry(batch_id)
        self._repository.set_counters(batch_id, self._repository.summarize_import(batch_id))
        self._repository.set_status(batch_id, BatchStatus.QUEUED, now=now, error_summary="")
        por_copiar = self._repository.count_items_in_status(batch_id, ItemStatus.INVENTORIED)
        if por_copiar:
            rondas = self._jobs_for_batch(batch_id, JobType.INGEST_BATCH)
            job, _created = self.jobs.enqueue(
                job_type=JobType.INGEST_BATCH,
                payload={
                    "batch_id": batch_id,
                    "inventory_batch_id": batch.inventory_batch_id or "",
                },
                now=now,
                idempotency_key=f"ingest_batch:{batch_id}:{rondas}",
            )
            self._repository.set_job(batch_id, job.id)
        else:
            job_id = self.enqueue_extraction(batch_id)
            if job_id is not None:
                self._repository.set_job(batch_id, job_id)
        refreshed = self._repository.get_batch(batch_id)
        logger.info(
            "ingestion.import_retried",
            extra={
                "event": "import_retried",
                "job_id": (refreshed.job_id if refreshed is not None else None) or "",
                "status_code": recovered,
            },
        )
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
        """Manejador del trabajo `ingest_batch`: copia las entradas al almacén por hash.

        El lease se renueva **por tiempo**, no cada N ficheros: un solo fichero de 500 MiB puede
        tardar más que el lease entero, así que la renovación también ocurre dentro de la copia de
        cada fichero (el almacén avisa por trozos).

        Si algo inesperado revienta, el lote no se queda diciendo que sigue trabajando: cuando ya no
        quedan reintentos, se cierra como `failed` con sus contadores reales.
        """
        batch_id = str(execution.payload.get("batch_id", ""))
        batch = self._repository.get_batch(batch_id)
        if batch is None:
            raise NotFoundError("lote", batch_id)

        now = self._clock.now()
        self._repository.set_status(batch_id, BatchStatus.RUNNING, now=now)
        pending = self._repository.pending_entries(batch_id)

        source_root = self._repository.source_root_of(batch_id)
        if source_root is None and pending:
            # Sin carpeta de origen no se puede copiar nada. Un lote que entró por ficheros subidos,
            # texto pegado o URL no tiene origen, pero tampoco tiene entradas por copiar: si las
            # tiene, es que algo lo ha devuelto a la fase de copia y eso sí es un error de verdad.
            raise InvalidSourceError("el lote no conserva la carpeta de origen")
        root = Path(source_root) if source_root is not None else None

        counters = ImportCounters(total=len(pending))
        execution.progress(0.0, "copiando")
        heartbeat = _ThrottledHeartbeat(execution, self._heartbeat_seconds)

        try:
            for index, entry in enumerate(pending, start=1):
                if execution.cancelled():
                    self._finish_cancelled(batch_id, counters, tuple(pending[index - 1 :]))
                    raise JobCancelledError(
                        "el lote de importación se canceló a petición del usuario"
                    )

                if root is not None:
                    self._copy_entry(batch_id, root, entry, execution, heartbeat)
                execution.progress(index / max(len(pending), 1), f"{index}/{len(pending)}")
                heartbeat.maybe()
        except JobCancelledError:
            raise
        except Exception as error:
            if not execution.retry_pending:
                # Sin más intentos no hay quien cierre el lote: se cierra aquí, con el estado real
                # de sus entradas, para que no se quede en `running` para siempre.
                self._finish_failed(batch_id, error)
            else:
                logger.warning(
                    "ingestion.import_interrupted",
                    extra={
                        "event": "import_interrupted",
                        "error_type": type(error).__name__,
                        "revision": execution.job.attempts,
                    },
                )
            raise

        counters = self._repository.summarize_import(batch_id)
        self._repository.set_counters(batch_id, counters)
        status = BatchStatus.SUCCEEDED if counters.failed == 0 else BatchStatus.FAILED
        summary = (
            None if counters.failed == 0 else f"{counters.failed} entradas no se pudieron copiar"
        )
        if counters.copied and self._pending_extraction(batch_id):
            # Queda texto por extraer, así que el lote **no** ha terminado: vuelve a la cola y el
            # trabajo de extracción lo cierra. Si no, el lote diría «terminado» a mitad del
            # pipeline. El trabajo se guarda en el lote: es el que la interfaz sigue y el que se
            # cancela.
            self._repository.set_status(
                batch_id, BatchStatus.QUEUED, now=self._clock.now(), error_summary=summary or ""
            )
            job_id = self.enqueue_extraction(batch_id)
            if job_id is not None:
                self._repository.set_job(batch_id, job_id)
            return
        self._repository.set_status(batch_id, status, now=self._clock.now(), error_summary=summary)

    def enqueue_extraction(self, batch_id: str) -> str | None:
        """Encola la extracción del lote, si queda algo por extraer.

        La clave de idempotencia lleva el número de veces que ya se ha encolado, para que volver a
        extraer un lote (por ejemplo, tras añadir un extractor nuevo) sea posible sin crear dos
        trabajos vivos a la vez.
        """
        pending = self._pending_extraction(batch_id)
        if pending == 0:
            return None
        rounds = self._jobs_for_batch(batch_id, JobType.EXTRACT_ARTIFACT)
        job, created = self.jobs.enqueue(
            job_type=JobType.EXTRACT_ARTIFACT,
            payload={"batch_id": batch_id},
            now=self._clock.now(),
            idempotency_key=f"extract_batch:{batch_id}:{rounds}",
        )
        if created:
            logger.info(
                "ingestion.extraction_queued",
                extra={"event": "extraction_queued", "job_id": job.id, "status_code": pending},
            )
        return job.id

    def _pending_extraction(self, batch_id: str) -> int:
        """Entradas copiadas y todavía sin extraer."""
        return self._repository.pending_extraction_count(batch_id)

    def _jobs_for_batch(self, batch_id: str, job_type: JobType) -> int:
        return sum(
            1
            for job in self.jobs.list(limit=500)
            if job.job_type is job_type and job.payload.get("batch_id") == batch_id
        )

    def on_job_failed(self, job: object) -> None:
        """Cierra el lote cuando su trabajo se queda `failed` y ya no se va a reintentar.

        Lo llama el worker (no el manejador) porque hay fallos que no pasan por el manejador: un
        lease vencido tras varias caídas deja el trabajo `failed` sin haber llegado a ejecutarse.
        """
        payload = getattr(job, "payload", None)
        if not isinstance(payload, dict):
            return
        batch_id = payload.get("batch_id")
        if not isinstance(batch_id, str) or not batch_id:
            return
        batch = self._repository.get_batch(batch_id)
        if batch is None or batch.status not in {
            BatchStatus.QUEUED.value,
            BatchStatus.RUNNING.value,
        }:
            # Ya está cerrado (o lo cerró el propio manejador): no se pisa un informe bueno.
            return
        job_error = getattr(job, "error_message", None)
        self._finish_failed(
            batch_id, RuntimeError(job_error or "el trabajo de importación terminó en fallo")
        )

    def _finish_failed(self, batch_id: str, error: Exception) -> None:
        """Estado coherente para un lote que no puede continuar: contadores reales y motivo."""
        counters = self._repository.summarize_import(batch_id)
        self._repository.set_counters(batch_id, counters)
        self._repository.set_status(
            batch_id,
            BatchStatus.FAILED,
            now=self._clock.now(),
            error_summary=_safe_error_summary(error),
        )
        logger.error(
            "ingestion.import_failed",
            extra={
                "event": "import_failed",
                "error_type": type(error).__name__,
                "status_code": counters.failed,
            },
        )

    def _copy_entry(
        self,
        batch_id: str,
        root: Path,
        entry: EntryView,
        execution: JobExecution,
        heartbeat: _ThrottledHeartbeat,
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
                "El fichero cambió de tamaño desde el inventario: no se copia lo que no se revisó.",
                now,
            )
            self._repository.mark_item(
                entry.id, ItemStatus.FAILED, detail="el fichero cambió después del inventario"
            )
            return

        if _mtime_changed(entry.mtime, stat.st_mtime):
            self._record_issue(
                batch_id,
                entry,
                IssueCode.SOURCE_CHANGED,
                IssueSeverity.WARNING,
                "El fichero cambió de fecha desde el inventario: no se copia lo que no se revisó.",
                now,
            )
            self._repository.mark_item(
                entry.id, ItemStatus.FAILED, detail="el fichero cambió después del inventario"
            )
            return

        try:
            stored = self._store.store_file(source, on_chunk=heartbeat.on_chunk)
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
        """Anota una incidencia del lote, una sola vez por entrada y motivo.

        Un lote reintentado vuelve a pasar por las mismas entradas: repetir la incidencia inflaría
        los contadores (y descuadraría el informe) sin aportar nada nuevo.
        """
        if self._repository.issue_exists(batch_id, code.value, entry.relative_path):
            return
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

    Se conservan el tamaño **y la fecha** que vio el inventario: son lo que permite detectar que el
    fichero cambió entre la vista previa y la copia. El contenido se hashea igualmente al copiar,
    así que un cambio que se cuele produce un artefacto distinto, nunca una copia silenciosa de algo
    que el usuario no revisó.
    """
    return DiscoveredEntry(
        relative_path=entry.relative_path,
        original_name=entry.original_name,
        size_bytes=entry.size_bytes,
        mtime=entry.mtime,
        media_type=entry.media_type or "",
        status=ItemStatus.INVENTORIED,
        # La procedencia viaja con la entrada: en un lote desde carpeta es el fichero y su ruta.
        # Guardarla aquí permite que el lector diga de dónde salió cada texto sin deducirlo.
        origin_type=OriginType.FILE.value,
        origin_display=entry.relative_path,
    )


def _mtime_changed(inventoried: datetime | None, current: float) -> bool:
    """¿Cambió la fecha de modificación del fichero desde el inventario?

    Se compara con una tolerancia de un segundo para no rechazar una copia legítima por redondeos
    del viaje a la base de datos. Si el inventario no guardó fecha (lotes anteriores a esta
    corrección), no se puede afirmar nada y no se bloquea la copia.
    """
    if inventoried is None:
        return False
    return abs(current - inventoried.timestamp()) > SOURCE_MTIME_TOLERANCE_SECONDS


def _safe_error_summary(error: Exception) -> str:
    """Motivo del fallo para el informe: sin trazas y sin rutas del usuario."""
    detail = redact_paths(str(error).strip().replace("\n", " "))
    if len(detail) > 160:
        detail = detail[:160] + "…"
    return f"{type(error).__name__}: {detail}" if detail else type(error).__name__
