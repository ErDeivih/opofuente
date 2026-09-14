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
from collections.abc import Mapping
from uuid import uuid4

from opofuente.application.job_service import JobExecution, JobHandler
from opofuente.application.ports import Clock, JobQueue
from opofuente.domain.errors import JobCancelledError, NotFoundError
from opofuente.domain.jobs import Job, JobType
from opofuente.infrastructure.worker_liveness import WorkerLiveness

logger = logging.getLogger(__name__)

#: Cuánto se reutiliza el resultado de comprobar la cancelación (evita una consulta por fichero).
CANCEL_CACHE_SECONDS = 0.5


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
        owner: str | None = None,
        liveness: WorkerLiveness | None = None,
    ) -> None:
        self._queue = queue
        self._handlers = dict(handlers)
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
        """Devuelve a la cola los trabajos cuyo lease venció (proceso caído a mitad)."""
        requeued = self._queue.requeue_expired_leases(now=self._clock.now())
        if requeued:
            logger.warning(
                "worker.requeued_interrupted",
                extra={"event": "worker_requeued", "status_code": requeued},
            )
        return requeued

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
            self._queue.fail(
                job.id,
                error_code="unsupported_job",
                error_message=f"no hay manejador para el tipo {job.job_type.value}",
                now=self._clock.now(),
            )
            logger.error(
                "worker.unsupported_job",
                extra={"event": "worker_unsupported", "job_id": job.id},
            )
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
            self._queue.fail(
                job.id,
                error_code="not_found",
                error_message=str(error),
                now=self._clock.now(),
            )
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
        else:
            if is_cancelled():
                # El trabajo terminó justo cuando se pidió cancelar: manda la cancelación.
                self._queue.acknowledge_cancel(job.id, owner=self._owner, now=self._clock.now())
                return
            self._queue.finish(job.id, owner=self._owner, now=self._clock.now())
            logger.info("worker.job_done", extra={"event": "job_done", "job_id": job.id})


def _safe_message(error: Exception) -> str:
    """Mensaje de error sin rutas absolutas ni contenido: el tipo y, si cabe, el texto corto."""
    text = str(error).strip().replace("\n", " ")
    if len(text) > 200:
        text = text[:200] + "…"
    return text or type(error).__name__
