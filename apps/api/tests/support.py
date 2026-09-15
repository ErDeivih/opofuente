"""Ayudantes compartidos por las pruebas de integración.

`FixedClock` da tiempo determinista, `FakeExecution` sustituye el trabajo real del worker cuando la
prueba quiere controlar la cancelación, y `run_one_job` ejecuta el pipeline con el worker de verdad
sobre la aplicación de prueba (despachando **los dos** tipos de trabajo: copiar y extraer).
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any

from opofuente.application.job_service import JobExecution
from opofuente.domain.jobs import Job, JobType
from opofuente.infrastructure.clock import SystemClock
from opofuente.workers.job_worker import JobWorker

if TYPE_CHECKING:  # pragma: no cover - solo para tipos
    from fastapi.testclient import TestClient


class FixedClock:
    """Reloj de prueba: el tiempo solo avanza cuando la prueba lo dice."""

    def __init__(self) -> None:
        self._now = datetime(2026, 9, 15, 12, 0, tzinfo=UTC)

    def now(self) -> datetime:
        return self._now

    def advance(self, seconds: int = 1) -> None:
        self._now += timedelta(seconds=seconds)


class FakeExecution(JobExecution):
    """Ejecución de prueba: informa sin base de datos y permite forzar la cancelación."""

    def __init__(self, job: Job, *, cancel_after: int | None = None) -> None:
        self._cancel_after = cancel_after
        self._checks = 0
        self.progress_calls: list[float] = []
        self.latidos = 0
        super().__init__(
            job,
            report=self._report,
            heartbeat=self._heartbeat,
            is_cancelled=self._is_cancelled,
        )

    def _report(self, value: float, step: str | None) -> None:
        self.progress_calls.append(value)

    def _heartbeat(self) -> None:
        self.latidos += 1

    def _is_cancelled(self) -> bool:
        self._checks += 1
        return self._cancel_after is not None and self._checks > self._cancel_after


def run_one_job(client: TestClient, *, attempts: int = 1) -> None:
    """Ejecuta el worker real de la aplicación sobre los servicios de la app de prueba.

    Despacha los dos tipos de trabajo del pipeline (copiar y extraer), igual que el worker de
    producción: si falta un manejador, el trabajo se marcaría fallido en lugar de ejecutarse.
    """
    app: Any = client.app
    ingestion = app.state.ingestion_service
    extraction = app.state.extraction_service
    worker = JobWorker(
        queue=ingestion.jobs,
        handlers={
            JobType.INGEST_BATCH: ingestion.run_import_job,
            JobType.EXTRACT_ARTIFACT: extraction.run_extraction_job,
        },
        on_failed={
            JobType.INGEST_BATCH: ingestion.on_job_failed,
            JobType.EXTRACT_ARTIFACT: ingestion.on_job_failed,
        },
        clock=SystemClock(),
        lease_seconds=60,
        poll_seconds=0.05,
        owner="worker-de-prueba",
    )
    for _ in range(attempts):
        asyncio.run(worker.run_once())
