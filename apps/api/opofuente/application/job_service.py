"""Casos de uso de trabajos: consultarlos y pedir su cancelación.

El bucle que los ejecuta vive en la capa del worker (`opofuente.workers.job_worker`); aquí solo
se define el contrato que recibe un manejador de trabajo.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence

from opofuente.application.ports import Clock, JobQueue
from opofuente.application.read_models import JobView, job_to_view
from opofuente.domain.errors import JobCancelledError, NotFoundError
from opofuente.domain.jobs import Job, JobStatus


class JobExecution:
    """Lo que recibe un manejador: el trabajo, cómo informar y cómo saber si le han pedido parar."""

    def __init__(
        self,
        job: Job,
        *,
        report: Callable[[float, str | None], None],
        heartbeat: Callable[[], None],
        is_cancelled: Callable[[], bool],
    ) -> None:
        self.job = job
        self._report = report
        self._heartbeat = heartbeat
        self._is_cancelled = is_cancelled

    @property
    def payload(self) -> Mapping[str, object]:
        return self.job.payload

    def progress(self, value: float, step: str | None = None) -> None:
        self._report(value, step)

    def heartbeat(self) -> None:
        """Renueva el lease para que un trabajo largo no se considere abandonado."""
        self._heartbeat()

    def cancelled(self) -> bool:
        return self._is_cancelled()

    def require_not_cancelled(self) -> None:
        """Corta la ejecución si se ha pedido cancelar. Se comprueba entre unidades de trabajo."""
        if self._is_cancelled():
            raise JobCancelledError("el trabajo se canceló a petición del usuario")


JobHandler = Callable[[JobExecution], None]


class JobService:
    def __init__(self, queue: JobQueue, clock: Clock) -> None:
        self._queue = queue
        self._clock = clock

    def list_jobs(
        self, *, limit: int = 50, statuses: Sequence[JobStatus] = ()
    ) -> tuple[JobView, ...]:
        jobs = self._queue.list(limit=limit, statuses=tuple(statuses))
        return tuple(self._view(job) for job in jobs)

    def get_job(self, job_id: str) -> JobView:
        job = self._queue.get(job_id)
        if job is None:
            raise NotFoundError("trabajo", job_id)
        return self._view(job)

    def cancel_job(self, job_id: str) -> JobView:
        job = self._queue.get(job_id)
        if job is None:
            raise NotFoundError("trabajo", job_id)
        self._queue.request_cancel(job_id, now=self._clock.now())
        refreshed = self._queue.get(job_id)
        return self._view(refreshed if refreshed is not None else job)

    @staticmethod
    def _view(job: Job) -> JobView:
        return job_to_view(job)
