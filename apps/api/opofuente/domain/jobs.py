"""Trabajos persistidos: estados, lease y reintentos.

Estados (02_ARCHITECTURE §6): `queued`, `leased`, `running`, `succeeded`, `failed`,
`cancel_requested`, `cancelled`.

Reglas que se comprueban aquí y en la base de datos:

- un trabajo en ejecución tiene propietario de lease y fecha de caducidad;
- un lease vencido vuelve a la cola (así un reinicio no pierde trabajo ni lo duplica);
- un trabajo cancelado no vuelve a ejecutarse;
- un trabajo que falla se reintenta hasta `max_attempts` y después queda `failed`.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum

from opofuente.domain.errors import InvariantViolationError

#: Un lease más corto que esto haría que un trabajo lento se considerara abandonado.
MIN_LEASE_SECONDS = 5


class JobType(StrEnum):
    """Tipos previstos por la arquitectura. En S02 solo se encola `ingest_batch`."""

    INVENTORY_SOURCE = "inventory_source"
    INGEST_BATCH = "ingest_batch"
    EXTRACT_ARTIFACT = "extract_artifact"
    CLASSIFY_DOCUMENT = "classify_document"
    PARSE_QUESTION_SET = "parse_question_set"
    BUILD_FTS = "build_fts"
    EMBED_SPANS = "embed_spans"
    DIFF_VERSIONS = "diff_versions"
    INVALIDATE_DERIVATIVES = "invalidate_derivatives"
    EXPORT_BACKUP = "export_backup"


class JobStatus(StrEnum):
    QUEUED = "queued"
    LEASED = "leased"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCEL_REQUESTED = "cancel_requested"
    PAUSED = "paused"
    """Detenido a propósito y sin terminar: el trabajo se reanuda, no se reintenta.

    No es `cancelled` (que es terminal) ni `queued` (que lo reclamaría el worker en la siguiente
    vuelta). Un trabajo en pausa **sigue vivo** y por tanto conserva su clave de idempotencia: si
    no, pausar un lote permitiría encolar un segundo trabajo para el mismo lote (DEBT-027 §4).
    """

    CANCELLED = "cancelled"


#: Estados en los que un trabajo sigue vivo y por tanto ocupa su clave de idempotencia.
ALIVE_STATUSES = (
    JobStatus.QUEUED,
    JobStatus.LEASED,
    JobStatus.RUNNING,
    JobStatus.CANCEL_REQUESTED,
    JobStatus.PAUSED,
)

_TERMINAL = frozenset({JobStatus.SUCCEEDED, JobStatus.FAILED, JobStatus.CANCELLED})


def is_terminal(status: JobStatus) -> bool:
    return status in _TERMINAL


def is_cancellable(status: JobStatus) -> bool:
    return status in ALIVE_STATUSES


def is_pausable(status: JobStatus) -> bool:
    """Un trabajo se puede pausar si todavía no ha empezado; uno en marcha lo para su manejador."""
    return status in {JobStatus.QUEUED, JobStatus.LEASED, JobStatus.CANCEL_REQUESTED}


def lease_expiry(now: datetime, seconds: int) -> datetime:
    if seconds < MIN_LEASE_SECONDS:
        raise InvariantViolationError(
            f"un lease de {seconds}s es demasiado corto: mínimo {MIN_LEASE_SECONDS}s"
        )
    return now + timedelta(seconds=seconds)


def should_retry(attempts: int, max_attempts: int) -> bool:
    """`attempts` cuenta los intentos ya consumidos."""
    if max_attempts < 1:
        raise InvariantViolationError("max_attempts debe ser al menos 1")
    return attempts < max_attempts


def retry_delay_seconds(attempts: int) -> int:
    """Espera creciente y acotada entre reintentos, para no girar en vacío."""
    return min(int(2 ** max(attempts, 1)), 30)


@dataclass(frozen=True, slots=True)
class Job:
    id: str
    job_type: JobType
    status: JobStatus
    payload: dict[str, object]
    progress: float
    attempts: int
    max_attempts: int
    created_at: datetime
    updated_at: datetime
    step: str | None = None
    error_code: str | None = None
    error_message: str | None = None
    lease_owner: str | None = None
    lease_expires_at: datetime | None = None
    #: A partir de cuándo se puede reclamar el trabajo (espera entre reintentos).
    not_before: datetime | None = None
    cancel_requested_at: datetime | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None

    @property
    def cancellation_requested(self) -> bool:
        return self.cancel_requested_at is not None
