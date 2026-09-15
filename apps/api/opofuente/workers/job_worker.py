"""Worker local: ejecuta los trabajos persistidos sin bloquear la API.

Decisiones:

- **sin Redis ni Celery**: la cola está en SQLite y el worker es una tarea de asyncio del propio
  proceso (02_ARCHITECTURE §6). Cerrar la pestaña del navegador no lo detiene;
- **lease**: cada trabajo reclamado tiene propietario y caducidad; el worker la renueva mientras
  trabaja. Si el proceso muere, el lease vence y el trabajo vuelve a la cola al arrancar;
- **sin bloquear el bucle**: el manejador se ejecuta en un hilo (`asyncio.to_thread`) para que la
  API siga respondiendo mientras se copian gigabytes;
- **cancelación cooperativa**: el manejador comprueba `cancelled()` entre unidades y lanza
  `JobCancelledError`, que el worker traduce a estado `cancelled`.
"""

from __future__ import annotations

import asyncio
import logging
import os
import socket
import time
from collections.abc import Callable, Mapping
from uuid import uuid4

from opofuente.application.job_service import JobExecution, JobHandler
from opofuente.application.ports import Clock, JobQueue
from opofuente.domain.errors import JobCancelledError, NotFoundError
from opofuente.domain.jobs import Job, JobStatus, JobType
from opofuente.infrastructure.safe_paths import redact_paths
from opofuente.infrastructure.worker_liveness import WorkerLiveness

logger = logging.getLogger(__name__)

#: Cuánto se reutiliza el resultado de comprobar la cancelación (evita una consulta por fichero).
CANCEL_CACHE_SECONDS = 0.5

#: Qué hacer cuando un trabajo se queda definitivamente en `failed`. Lo usa quien tenga estado
#: propio que sincronizar (por ejemplo, el lote de una importación, que no puede quedarse en
#: `running` cuando su trabajo ya no va a reintentarse).
JobFailureHook = Callable[[Job], None]


def default_owner_id() -> str:
    """Identidad del worker: host + proceso + sufijo aleatorio."""
    return f"{socket.gethostname()}-{os.getpid()}-{uuid4().hex[:6]}"


class JobWorker:
    def __init__(
        self,
        *,
        queue: JobQueue,
        handlers: Mapping[JobType, JobHandler],
        clock: Clock,
        lease_seconds: int,
        poll_seconds: float,
        on_failed: Mapping[JobType, JobFailureHook] | None = None,
        owner: str | None = None,
        liveness: WorkerLiveness | None = None,
    ) -> None:
        self._queue = queue
        self._handlers = dict(handlers)
        self._on_failed = dict(on_failed or {})
        self._clock = clock
        self._lease_seconds = lease_seconds
        self._poll_seconds = poll_seconds
        self._owner = owner or default_owner_id()
        self._liveness = liveness or WorkerLiveness()
        self._stop = asyncio.Event()
        self._started = asyncio.Event()

    @property
    def owner(self) -> str:
        return self._owner

    @property
    def liveness(self) -> WorkerLiveness:
        return self._liveness

    async def wait_started(self, timeout: float = 5.0) -> bool:
        """Espera a que la tarea haya empezado de verdad. `False` si no llegó a arrancar."""
        try:
            await asyncio.wait_for(self._started.wait(), timeout=timeout)
        except TimeoutError:
            return False
        return True

    def stop(self) -> None:
        self._stop.set()

    def recover_interrupted(self) -> int:
        """Devuelve a la cola los trabajos cuyo lease venció (proceso caído a mitad).

        Devuelve cuántos se recuperaron. Los que agotaron sus intentos quedan `failed`, así que
        también se avisa de ellos: si no, el lote de esa importación se quedaría diciendo que
        sigue trabajando.
        """
        expired = self._queue.requeue_expired_leases(now=self._clock.now())
        for job in expired:
            if job.status is JobStatus.FAILED:
                self._notify_failed(job)
        if expired:
            logger.warning(
                "worker.requeued_interrupted",
                extra={"event": "worker_requeued", "status_code": len(expired)},
            )
        return len(expired)

    async def run_forever(self) -> None:
        self.recover_interrupted()
        self._liveness.mark_running()
        self._started.set()
        logger.info("worker.started owner=%s", self._owner, extra={"event": "worker_started"})
        try:
            while not self._stop.is_set():
                worked = await self.run_once()
                if not worked:
                    try:
                        await asyncio.wait_for(self._stop.wait(), timeout=self._poll_seconds)
                    except TimeoutError:
                        continue
        finally:
            self._liveness.mark_stopped()
            logger.info("worker.stopped", extra={"event": "worker_stopped"})

    async def run_once(self) -> bool:
        """Reclama y ejecuta un trabajo. Devuelve True si ha hecho algo."""
        now = self._clock.now()
        job = self._queue.claim_next(owner=self._owner, now=now, lease_seconds=self._lease_seconds)
        if job is None:
            return False
        await asyncio.to_thread(self._execute, job)
        return True

    def _execute(self, job: Job) -> None:
        handler = self._handlers.get(job.job_type)
        if handler is None:
            status = self._queue.fail(
                job.id,
                error_code="unsupported_job",
                error_message=f"no hay manejador para el tipo {job.job_type.value}",
                now=self._clock.now(),
            )
            logger.error(
                "worker.unsupported_job",
                extra={"event": "worker_unsupported", "job_id": job.id},
            )
            if status is JobStatus.FAILED:
                self._notify_failed(job)
            return

        self._queue.mark_running(job.id, owner=self._owner, now=self._clock.now())
        last_check = 0.0
        cached_cancelled = False

        def report(progress: float, step: str | None) -> None:
            self._queue.report_progress(job.id, progress=progress, step=step, now=self._clock.now())

        def heartbeat() -> None:
            self._queue.renew_lease(
                job.id, owner=self._owner, now=self._clock.now(), lease_seconds=self._lease_seconds
            )

        def is_cancelled() -> bool:
            nonlocal last_check, cached_cancelled
            now_monotonic = time.monotonic()
            if now_monotonic - last_check >= CANCEL_CACHE_SECONDS:
                cached_cancelled = self._queue.cancellation_requested(job.id)
                last_check = now_monotonic
            return cached_cancelled

        execution = JobExecution(job, report=report, heartbeat=heartbeat, is_cancelled=is_cancelled)
        heartbeat()
        try:
            handler(execution)
        except JobCancelledError:
            self._queue.acknowledge_cancel(job.id, owner=self._owner, now=self._clock.now())
            logger.info("worker.job_cancelled", extra={"event": "job_cancelled", "job_id": job.id})
        except NotFoundError as error:
            status = self._queue.fail(
                job.id,
                error_code="not_found",
                error_message=redact_paths(str(error)),
                now=self._clock.now(),
            )
            if status is JobStatus.FAILED:
                self._notify_failed(job)
        except Exception as error:
            status = self._queue.fail(
                job.id,
                error_code=type(error).__name__,
                error_message=_safe_message(error),
                now=self._clock.now(),
            )
            logger.error(
                "worker.job_failed",
                extra={
                    "event": "job_failed",
                    "job_id": job.id,
                    "error_type": type(error).__name__,
                    "revision": status.value,
                },
            )
            if status is JobStatus.FAILED:
                self._notify_failed(job)
        else:
            # Si el manejador vuelve sin cortar, el trabajo terminó: se cierra como `succeeded`
            # aunque haya llegado una petición de cancelación en el último momento. Marcarlo
            # `cancelled` dejaría el trabajo en un estado que su lote (ya terminado y con todo
            # copiado) no comparte, y la cancelación no puede deshacer lo que ya está hecho.
            self._queue.finish(job.id, owner=self._owner, now=self._clock.now())
            logger.info("worker.job_done", extra={"event": "job_done", "job_id": job.id})

    def _notify_failed(self, job: Job) -> None:
        """Avisa de que un trabajo se queda `failed` sin más reintentos.

        Un gancho que falla no puede tumbar el worker ni dejar el trabajo a medias: se registra y
        se sigue. El estado del trabajo ya está guardado por su cuenta.
        """
        hook = self._on_failed.get(job.job_type)
        if hook is None:
            return
        try:
            hook(job)
        except Exception as error:
            # Un gancho que falla no puede tumbar el worker: el estado del trabajo ya está guardado.
            logger.error(
                "worker.failure_hook_failed",
                extra={
                    "event": "failure_hook_failed",
                    "job_id": job.id,
                    "error_type": type(error).__name__,
                },
            )


def _safe_message(error: Exception) -> str:
    """Mensaje de error sin rutas del usuario ni contenido: el tipo y, si cabe, el texto corto.

    El texto de una excepción de terceros suele traer la ruta absoluta del fichero
    (`PermissionError`, errores de SQLite). Este mensaje se guarda en `jobs.error_message` y se
    publica por la API, así que las rutas se recortan antes de guardarlo.
    """
    text = redact_paths(str(error).strip().replace("\n", " "))
    if len(text) > 200:
        text = text[:200] + "…"
    return text or type(error).__name__
