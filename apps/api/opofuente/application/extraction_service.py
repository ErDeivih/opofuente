"""Caso de uso de la extracción (S03): del artefacto copiado al texto utilizable.

Qué hace, y qué no:

- recorre las entradas **copiadas y aún sin extraer** de un lote, extrae su texto con el
  extractor que corresponda y guarda una representación por artefacto con su calidad y sus avisos;
- lo que **no** tiene extractor se marca `unsupported_preserved`: el original ya está copiado y se
  conserva sin ejecutar ni extraer nada (DEBT-008);
- lo que directamente **no se debe conservar** (un ejecutable que haya llegado dentro de un ZIP) se
  marca `failed` con su incidencia y no se copia;
- un documento sin texto nativo (imagen, PDF escaneado) deja su representación en `pending` y el
  artefacto marcado como candidato a OCR: sin OCR configurado, la aplicación sigue y lo dice.

No clasifica nada: no decide tipo documental, ni tema, ni autoridad. Eso es S04.
"""

from __future__ import annotations

import logging
import shutil
from dataclasses import dataclass, replace
from pathlib import Path
from uuid import uuid4

from opofuente.application.job_service import JobExecution
from opofuente.application.ports import Clock, IngestionRepository, JobQueue
from opofuente.application.read_models import RepresentationView
from opofuente.domain.artifacts import OriginType, media_type_for
from opofuente.domain.errors import (
    InvalidSourceError,
    JobCancelledError,
    JobPausedError,
    NotFoundError,
    UnsafeContentError,
)
from opofuente.domain.extraction import (
    REPRESENTATION_FORMAT_VERSION,
    Quality,
    RepresentationKind,
    RepresentationStatus,
    WarningCode,
)
from opofuente.domain.ingestion import (
    BatchKind,
    BatchStatus,
    DiscoveredEntry,
    ImportIssue,
    IssueCode,
    IssueSeverity,
    ItemStatus,
)
from opofuente.domain.jobs import JobType
from opofuente.infrastructure.artifact_store import ArtifactStore
from opofuente.infrastructure.extraction_repository import (
    PendingExtraction,
    SqlAlchemyExtractionRepository,
)
from opofuente.infrastructure.extractors import ExtractorRegistry
from opofuente.infrastructure.representation_store import RepresentationStore, TextSlice
from opofuente.infrastructure.safe_paths import resolve_within, safe_display_name
from opofuente.infrastructure.safe_zip import extract_zip_safely

logger = logging.getLogger(__name__)

#: Entradas que se extraen en una sola pasada del trabajo. Acota la unidad de cancelación y de
#: informe: un lote enorme se extrae en varias pasadas, todas idempotentes.
EXTRACTION_CHUNK = 200


@dataclass(frozen=True, slots=True)
class ExtractionReport:
    """Resultado de una pasada de extracción."""

    processed: int
    extracted: int
    preserved: int
    failed: int
    pending_ocr: int
    remaining: int

    @property
    def all_done(self) -> bool:
        return self.remaining == 0


class ExtractionService:
    """Ejecuta la extracción de un lote y deja su estado coherente."""

    def __init__(
        self,
        *,
        repository: SqlAlchemyExtractionRepository,
        ingestions: IngestionRepository,
        store: ArtifactStore,
        representations: RepresentationStore,
        registry: ExtractorRegistry,
        jobs: JobQueue,
        clock: Clock,
        data_root: Path,
        max_member_bytes: int,
    ) -> None:
        self._repository = repository
        self._ingestions = ingestions
        self._store = store
        self._representations = representations
        self._registry = registry
        self._jobs = jobs
        self._clock = clock
        self._data_root = data_root
        self._max_member_bytes = max_member_bytes

    # ------------------------------------------------------------------ trabajo

    def run_extraction_job(self, execution: JobExecution) -> None:
        """Manejador del trabajo `extract_artifact`: extrae las entradas pendientes del lote.

        El nombre del tipo de trabajo viene de la arquitectura; la unidad de trabajo es el lote,
        igual que en la importación, porque el informe del lote es lo que el usuario revisa y la
        cancelación tiene que dejar ese informe coherente.
        """
        batch_id = str(execution.payload.get("batch_id", ""))
        batch = self._ingestions.get_batch(batch_id)
        if batch is None:
            raise NotFoundError("lote", batch_id)
        if batch.kind != BatchKind.IMPORT.value:
            raise InvalidSourceError("solo se extrae de un lote de importación")

        now = self._clock.now()
        if not self._ingestions.start_running(batch_id, now=now):
            # El lote se pausó entre la reclamación del trabajo y esta línea: no se arranca.
            raise JobPausedError("el lote está en pausa")
        tick = _Ticker(execution)
        tick.start()

        try:
            report = self._extract_pending(batch_id, execution, tick)
        except JobCancelledError:
            # Cancelar deja el lote cerrado con lo que sí se extrajo: lo copiado sigue copiado y no
            # queda ninguna representación a medias (se guarda entera o no se guarda).
            self._finish_cancelled(batch_id)
            raise
        except JobPausedError:
            # Pausar **no** cierra el lote: se guarda el informe con lo extraído hasta aquí y el
            # trabajo queda detenido para retomarlo.
            self._ingestions.confirm_pause(
                batch_id,
                self._ingestions.summarize_import(batch_id),
                now=self._clock.now(),
            )
            raise
        self._finish(batch_id, report)
        tick.report(report)
        self._enqueue_classification(batch_id, report)

    def _enqueue_classification(self, batch_id: str, report: ExtractionReport) -> None:
        """Encola la clasificación de lo extraído: el pipeline sigue solo, sin pedirlo a mano.

        La clasificación es idempotente, así que encolarla al terminar la extracción no duplica
        propuestas; y como se encola **después** de cerrar el lote, un fallo al encolarla no deja el
        informe del lote a medias. Si no se extrajo nada, no hay nada que clasificar.
        """
        if report.extracted <= 0:
            return
        self._jobs.enqueue(
            job_type=JobType.CLASSIFY_DOCUMENT,
            payload={"batch_id": batch_id, "limit": max(report.extracted * 2, 50)},
            now=self._clock.now(),
            idempotency_key=f"classify_document:{batch_id}",
        )

    def _extract_pending(
        self, batch_id: str, execution: JobExecution, tick: _Ticker
    ) -> ExtractionReport:
        processed = extracted = preserved = failed = pending_ocr = 0
        while True:
            pending = self._repository.pending_extraction(batch_id, limit=EXTRACTION_CHUNK)
            if not pending:
                break
            for entry in pending:
                if execution.cancelled():
                    raise JobCancelledError("la extracción se canceló a petición del usuario")
                if self._ingestions.is_paused(batch_id):
                    raise JobPausedError("el lote está en pausa")
                outcome = self._extract_entry(batch_id, entry)
                processed += 1
                extracted += outcome == ItemStatus.EXTRACTED
                preserved += outcome == ItemStatus.UNSUPPORTED_PRESERVED
                failed += outcome == ItemStatus.FAILED
                pending_ocr += outcome == ItemStatus.OCR_PENDING
                tick.step(processed, entry.relative_path)
                tick.heartbeat_if_due()
            # Sin `break` por tamaño: la expansión de un ZIP añade entradas que también hay que
            # extraer, y el bucle termina solo cuando no queda ninguna en `hashed` (cada entrada
            # procesada sale de ese estado).
        return ExtractionReport(
            processed=processed,
            extracted=int(extracted),
            preserved=int(preserved),
            failed=int(failed),
            pending_ocr=int(pending_ocr),
            remaining=self._repository.pending_extraction_count(batch_id),
        )

    def _extract_entry(self, batch_id: str, entry: PendingExtraction) -> ItemStatus:
        """Extrae una entrada y deja su estado final. Nunca lanza por un documento raro."""
        path = self._artifact_path(entry)
        if path is None:
            self._issue(
                batch_id,
                entry,
                IssueCode.STORE_ERROR,
                IssueSeverity.ERROR,
                "El artefacto no está en el almacén: no se puede extraer.",
            )
            self._ingestions.mark_item(entry.item_id, ItemStatus.FAILED, detail="artefacto ausente")
            return ItemStatus.FAILED

        # El nombre original viaja al registro: en el almacén el fichero se llama como su hash, así
        # que la extensión con la que se decide la política sale de la entrada, no de la ruta.
        plan = self._registry.plan(path, name=entry.original_name or entry.relative_path)
        if plan.action == "refuse":
            self._issue(
                batch_id,
                entry,
                IssueCode.OMITTED_EXECUTABLE,
                IssueSeverity.WARNING,
                "Ejecutable o biblioteca: no se extrae ni se conserva su contenido.",
            )
            self._ingestions.mark_item(
                entry.item_id, ItemStatus.FAILED, detail="ejecutable: no se procesa"
            )
            return ItemStatus.FAILED
        if plan.action == "expand_zip":
            anidado = self._registry.nested_container_refusal(container_depth=entry.container_depth)
            if anidado is not None:
                # Un contenedor dentro de otro no se expande: se conserva íntegro y se dice.
                # Expandir cada nivel multiplicaría el espacio de una bomba de archivos anidados.
                self._issue(
                    batch_id,
                    entry,
                    IssueCode.UNSUPPORTED_PRESERVED,
                    IssueSeverity.INFO,
                    f"Conservado sin expandir: {anidado}.",
                )
                self._ingestions.mark_item(
                    entry.item_id,
                    ItemStatus.UNSUPPORTED_PRESERVED,
                    detail="contenedor anidado",
                )
                return ItemStatus.UNSUPPORTED_PRESERVED
            return self._expand_zip_entry(batch_id, entry, path)
        if plan.action == "preserve":
            self._issue(
                batch_id,
                entry,
                IssueCode.UNSUPPORTED_PRESERVED,
                IssueSeverity.INFO,
                f"Conservado sin extraer: {plan.reason}.",
            )
            self._ingestions.mark_item(
                entry.item_id,
                ItemStatus.UNSUPPORTED_PRESERVED,
                detail="conservado sin extraer",
            )
            return ItemStatus.UNSUPPORTED_PRESERVED

        try:
            result = self._registry.extract(path, plan=plan)
        except Exception as error:
            self._issue(
                batch_id,
                entry,
                IssueCode.EXTRACTION_FAILED,
                IssueSeverity.ERROR,
                f"No se pudo extraer el texto ({type(error).__name__}).",
            )
            self._ingestions.mark_item(
                entry.item_id, ItemStatus.FAILED, detail="extracción fallida"
            )
            logger.warning(
                "extraction.failed",
                extra={"event": "extraction_failed", "error_type": type(error).__name__},
            )
            return ItemStatus.FAILED

        if (
            entry.origin_type == OriginType.PASTE.value
            and result.kind is RepresentationKind.NATIVE_TEXT
        ):
            # El extractor de texto no puede saber de dónde viene el contenido; el origen sí. Un
            # texto pegado se marca `plain_text` para no confundirlo con el texto nativo de un
            # documento.
            result = replace(result, kind=RepresentationKind.PLAIN_TEXT)

        # La clave natural se consulta **antes** de escribir el texto: el texto vive en un
        # directorio propio, y escribirlo para descubrir después que la fila ya existía dejaba ese
        # directorio huérfano en `data/extracted` (basura física que nadie lee y nadie limpia).
        existente = self._repository.find_id(
            artifact_id=entry.artifact_id,
            extractor_name=result.extractor.name,
            extractor_version=result.extractor.version,
            kind=result.kind.value,
        )
        representation_id = existente
        if existente is not None:
            # La representación ya existía (el mismo contenido extraído antes): la entrada se enlaza
            # igualmente, porque el enlace es de la entrada a la representación, y dos entradas con
            # el mismo contenido comparten el texto.
            self._ingestions.link_representation(entry.item_id, existente, now=self._clock.now())
        if existente is None:
            representation_id = str(uuid4())
            storage_key = (
                self._representations.save(representation_id, result) if result.text else None
            )
            try:
                self._repository.save(
                    result=result,
                    artifact_id=entry.artifact_id,
                    representation_id=representation_id,
                    text_storage_key=storage_key,
                    now=self._clock.now(),
                    format_version=REPRESENTATION_FORMAT_VERSION,
                )
            except Exception:
                # Si la fila no se guarda, el texto escrito tampoco puede quedarse: una
                # representación sin fila que la referencie es un fichero que nadie va a leer.
                self._representations.remove(representation_id)
                raise
            self._ingestions.link_representation(
                entry.item_id, representation_id, now=self._clock.now()
            )

        if result.status is RepresentationStatus.FAILED:
            demasiado_grande = WarningCode.TOO_LARGE in result.warnings
            self._issue(
                batch_id,
                entry,
                IssueCode.EXTRACTION_FAILED,
                IssueSeverity.ERROR,
                "El documento supera el límite de lectura del extractor: se conserva sin leer."
                if demasiado_grande
                else "El extractor no pudo leer el documento.",
            )
            self._ingestions.mark_item(
                entry.item_id,
                ItemStatus.FAILED,
                detail="supera el límite de lectura" if demasiado_grande else "documento ilegible",
            )
            return ItemStatus.FAILED

        if result.status is RepresentationStatus.PENDING:
            # Sin texto utilizable (imagen, PDF escaneado): el original ya está copiado y es válido,
            # así que la entrada no falla; queda pendiente de OCR y se declara. Se distingue «no se
            # ha ejecutado» de «se ejecutó y no reconoció nada»: son cosas distintas y la primera no
            # se puede decir cuando ya se ha llamado al OCR.
            ejecutado = result.kind is RepresentationKind.OCR
            self._issue(
                batch_id,
                entry,
                IssueCode.OCR_PENDING,
                IssueSeverity.WARNING,
                (
                    "El OCR se ha ejecutado y no ha reconocido texto: la representación queda "
                    "pendiente."
                )
                if ejecutado
                else "Sin texto nativo: queda pendiente de OCR, que no se ha ejecutado.",
            )
            self._ingestions.mark_item(
                entry.item_id,
                ItemStatus.OCR_PENDING,
                detail="pendiente de OCR",
            )
            return ItemStatus.OCR_PENDING

        if result.status is RepresentationStatus.EMPTY:
            # El extractor funcionó y el documento no traía nada (un fichero vacío, por ejemplo): la
            # entrada queda procesada, y es la representación la que dice que está vacía.
            self._issue(
                batch_id,
                entry,
                IssueCode.EMPTY_FILE,
                IssueSeverity.INFO,
                "El documento no contiene texto que extraer.",
            )
            self._ingestions.mark_item(
                entry.item_id,
                ItemStatus.EXTRACTED,
                detail="extraído sin texto",
            )
            return ItemStatus.EXTRACTED

        if result.quality in {Quality.POOR, Quality.FAILED}:
            self._issue(
                batch_id,
                entry,
                IssueCode.EXTRACTION_POOR_QUALITY,
                IssueSeverity.WARNING,
                "Texto extraído con calidad pobre: no se usará sin revisión.",
            )
        self._ingestions.mark_item(
            entry.item_id,
            ItemStatus.EXTRACTED,
            detail=f"{result.kind.value}: {result.char_count} caracteres",
        )
        return ItemStatus.EXTRACTED

    # ------------------------------------------------------------------ ZIP

    def _expand_zip_entry(self, batch_id: str, entry: PendingExtraction, path: Path) -> ItemStatus:
        """Expande un ZIP en entradas propias del lote, con los límites del módulo `safe_zip`.

        Cada miembro se copia al almacén y se le añade una entrada `hashed`, así que sigue el mismo
        pipeline que el resto: se extrae en la vuelta siguiente y aparece en el informe. El ZIP
        queda `expanded` (conservado y ya procesado, sin texto propio).

        Lo que no se admite (traversal, bomba, anidamiento excesivo) rechaza el contenedor entero
        con su incidencia; un miembro que sea ejecutable se salta con su aviso, sin copiarlo.
        """
        temporales = resolve_within(self._data_root, self._data_root / "tmp" / f"zip-{uuid4().hex}")
        try:
            try:
                miembros = extract_zip_safely(
                    path,
                    temporales,
                    limits=self._registry.zip_limits,
                    max_bytes_per_member=self._max_member_bytes,
                )
            except UnsafeContentError as error:
                self._issue(
                    batch_id,
                    entry,
                    IssueCode.UNSAFE_CONTAINER,
                    IssueSeverity.ERROR,
                    f"El ZIP no se ha expandido por seguridad: {error.reason}.",
                )
                self._ingestions.mark_item(
                    entry.item_id, ItemStatus.FAILED, detail="contenedor no admitido"
                )
                return ItemStatus.FAILED

            añadidos = 0
            for miembro in miembros:
                if not miembro.is_file():
                    continue
                # El miembro se reconoce por **su** nombre (está en el temporal con el suyo) y por
                # su contenido: un `.exe` renombrado a `.txt` no se copia, y una cabecera `MZ`
                # tampoco.
                if self._registry.plan(miembro).action == "refuse":
                    self._issue(
                        batch_id,
                        entry,
                        IssueCode.OMITTED_EXECUTABLE,
                        IssueSeverity.WARNING,
                        "Dentro del ZIP hay un ejecutable: no se copia ni se extrae.",
                    )
                    continue
                if self._store_member(batch_id, entry, miembro, temporales):
                    añadidos += 1
        finally:
            # Los miembros viven en este temporal hasta que se han copiado: se limpia al terminar,
            # tanto si la expansión salió bien como si se rechazó el contenedor.
            shutil.rmtree(temporales, ignore_errors=True)

        self._issue(
            batch_id,
            entry,
            IssueCode.CONTAINER_EXPANDED,
            IssueSeverity.INFO,
            f"Contenedor ZIP expandido en {añadidos} entradas.",
        )
        self._ingestions.mark_item(
            entry.item_id, ItemStatus.EXPANDED, detail=f"zip: {añadidos} entradas"
        )
        return ItemStatus.EXPANDED

    def _store_member(
        self, batch_id: str, entry: PendingExtraction, miembro: Path, temporales: Path
    ) -> bool:
        """Copia un miembro del ZIP al almacén y le crea su entrada en el lote."""
        try:
            stored = self._store.store_file(miembro)
        except OSError:
            self._issue(
                batch_id,
                entry,
                IssueCode.COPY_FAILED,
                IssueSeverity.ERROR,
                "No se pudo copiar un miembro del ZIP al almacén.",
            )
            return False
        relativo = f"{entry.relative_path}/{miembro.relative_to(temporales).as_posix()}"
        artifact_id, _created = self._ingestions.register_artifact(
            digest=stored.sha256,
            size_bytes=stored.size_bytes,
            media_type=media_type_for(miembro.name),
            storage_key=stored.storage_key,
            origin_type=OriginType.FILE,
            display_location=relativo,
            original_name=safe_display_name(miembro.name),
            source_path_display=None,
            file_mtime=None,
            now=self._clock.now(),
        )
        self._ingestions.add_entries(
            batch_id,
            (
                DiscoveredEntry(
                    relative_path=relativo,
                    original_name=safe_display_name(miembro.name),
                    size_bytes=stored.size_bytes,
                    mtime=None,
                    media_type=media_type_for(miembro.name),
                    status=ItemStatus.HASHED,
                    # El miembro está un nivel más adentro que su contenedor. Es un dato persistido:
                    # el límite de anidamiento se decide con él y no con el nombre del fichero.
                    container_depth=entry.container_depth + 1,
                    # Dentro de un ZIP el origen es el propio contenedor: así la procedencia del
                    # texto dice de qué paquete salió.
                    origin_type=OriginType.FILE.value,
                    origin_display=relativo,
                ),
            ),
            status=ItemStatus.HASHED,
        )
        item_id = self._ingestions.item_id_for(batch_id, relativo)
        if item_id is None:  # pragma: no cover - se acaba de añadir
            return False
        self._ingestions.mark_item(item_id, ItemStatus.HASHED, artifact_id=artifact_id)
        return True

    # ------------------------------------------------------------------ consultas

    def representations_for_batch(self, batch_id: str) -> tuple[RepresentationView, ...]:
        if self._ingestions.get_batch(batch_id) is None:
            raise NotFoundError("lote", batch_id)
        return self._repository.list_for_batch(batch_id)

    def get_representation(self, representation_id: str) -> RepresentationView:
        view = self._repository.get(representation_id)
        if view is None:
            raise NotFoundError("representación", representation_id)
        return view

    def read_text(self, representation_id: str, *, offset: int, limit: int) -> TextSlice:
        """Lee un trozo del texto de una representación. Los avisos van en la vista, no aquí."""
        view = self.get_representation(representation_id)
        if view.storage_key is None:
            return TextSlice(text="", offset=offset, limit=limit, total_chars=0, truncated=False)
        return self._representations.read(view.storage_key, offset=offset, limit=limit)

    # ------------------------------------------------------------------ apoyo

    def _artifact_path(self, entry: PendingExtraction) -> Path | None:
        from opofuente.domain.artifacts import Sha256

        try:
            digest = Sha256(entry.sha256)
        except Exception:
            return None
        path = self._store.path_for(digest)
        return path if path.is_file() else None

    def _issue(
        self,
        batch_id: str,
        entry: PendingExtraction,
        code: IssueCode,
        severity: IssueSeverity,
        message: str,
    ) -> None:
        """Anota una incidencia una sola vez por entrada y motivo (igual que en la importación)."""
        if self._ingestions.issue_exists(batch_id, code.value, entry.relative_path):
            return
        self._ingestions.add_issues(
            batch_id,
            (
                ImportIssue(
                    code=code,
                    severity=severity,
                    safe_message=message,
                    relative_path=entry.relative_path,
                ),
            ),
            now=self._clock.now(),
        )

    def _finish(self, batch_id: str, report: ExtractionReport) -> None:
        """Recalcula el informe del lote desde su estado real y lo cierra."""
        counters = self._ingestions.summarize_import(batch_id)
        self._ingestions.set_counters(batch_id, counters)
        if not report.all_done:  # pragma: no cover - el bucle no termina con trabajo pendiente
            logger.warning(
                "extraction.remaining",
                extra={"event": "extraction_remaining", "status_code": report.remaining},
            )
        failed = counters.failed > 0
        self._ingestions.set_status(
            batch_id,
            BatchStatus.FAILED if failed else BatchStatus.SUCCEEDED,
            now=self._clock.now(),
            error_summary=(
                f"{counters.failed} entradas no se pudieron extraer" if failed else None
            ),
        )
        logger.info(
            "extraction.batch_done",
            extra={
                "event": "extraction_done",
                "status_code": report.extracted,
            },
        )

    def _finish_cancelled(self, batch_id: str) -> None:
        """Cierra el lote cancelado con el estado real de sus entradas."""
        counters = self._ingestions.summarize_import(batch_id)
        self._ingestions.set_counters(batch_id, counters)
        self._ingestions.set_status(batch_id, BatchStatus.CANCELLED, now=self._clock.now())
        logger.info(
            "extraction.cancelled",
            extra={"event": "extraction_cancelled", "status_code": counters.copied},
        )


class _Ticker:
    """Progreso, latido y pasos del trabajo, en un sitio."""

    def __init__(self, execution: JobExecution) -> None:
        self._execution = execution
        self._count = 0

    def start(self) -> None:
        self._execution.progress(0.0, "extrayendo")

    def step(self, count: int, relative_path: str) -> None:
        self._count = count
        self._execution.progress(0.5, f"{count}: {relative_path[:60]}")

    def heartbeat_if_due(self) -> None:
        # Los ficheros se extraen uno a uno y cada extracción es corta: renovar por entrada es
        # suficiente y mantiene el lease fresco aunque el lote sea largo.
        self._execution.heartbeat()

    def report(self, report: ExtractionReport) -> None:
        self._execution.progress(
            1.0,
            f"extraídas {report.extracted}, conservadas {report.preserved}, "
            f"pendientes de OCR {report.pending_ocr}, fallidas {report.failed}",
        )
