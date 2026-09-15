"""Cola de trabajos persistida en SQLite, con lease y cancelación cooperativa.

Reglas:

- **Reclamar** un trabajo es una operación atómica: se elige el más antiguo en cola y se actualiza
  solo si sigue en cola, así que dos workers nunca ejecutan el mismo trabajo;
- **lease**: mientras se ejecuta, el trabajo tiene propietario y caducidad; el worker lo renueva;
- **reinicio**: al arrancar, los leases vencidos vuelven a la cola (un trabajo interrumpido se
  recupera; un trabajo terminado no se repite);
- **idempotencia de encolado**: un índice único parcial impide encolar dos veces la misma operación
  mientras siga viva;
- **cancelación**: se marca `cancel_requested` y el worker la aplica entre unidades de trabajo.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from uuid import uuid4

from sqlalchemy import select, update
from sqlalchemy.orm import Session, sessionmaker

from opofuente.application.read_models import JobView
from opofuente.domain.errors import InvariantViolationError
from opofuente.domain.jobs import (
    ALIVE_STATUSES,
    Job,
    JobStatus,
    JobType,
    is_terminal,
    lease_expiry,
    retry_delay_seconds,
    should_retry,
)
from opofuente.infrastructure.db import as_utc
from opofuente.infrastructure.db_models import JobRecord


def _new_id() -> str:
    return str(uuid4())


class SqlAlchemyJobRepository:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def enqueue(
        self,
        *,
        job_type: JobType,
        payload: dict[str, object],
        now: datetime,
        idempotency_key: str | None = None,
        max_attempts: int = 3,
    ) -> tuple[Job, bool]:
        """Encola un trabajo. Si ya hay uno vivo con la misma clave, devuelve ese."""
        with self._session_factory() as session:
            if idempotency_key is not None:
                existing = session.execute(
                    select(JobRecord).where(
                        JobRecord.idempotency_key == idempotency_key,
                        JobRecord.status.in_([status.value for status in ALIVE_STATUSES]),
                    )
                ).scalar_one_or_none()
                if existing is not None:
                    return self._job(existing), False
            record = JobRecord(
                id=_new_id(),
                job_type=job_type.value,
                status=JobStatus.QUEUED.value,
                payload_json=json.dumps(payload),
                progress=0.0,
                attempts=0,
                max_attempts=max_attempts,
                idempotency_key=idempotency_key,
                created_at=now,
                updated_at=now,
            )
            session.add(record)
            session.commit()
            return self._job(record), True

    def get(self, job_id: str) -> Job | None:
        with self._session_factory() as session:
            record = session.get(JobRecord, job_id)
            return self._job(record) if record is not None else None

    def list(self, *, limit: int, statuses: tuple[JobStatus, ...] = ()) -> tuple[Job, ...]:
        with self._session_factory() as session:
            query = select(JobRecord).order_by(JobRecord.created_at.desc()).limit(limit)
            if statuses:
                query = (
                    select(JobRecord)
                    .where(JobRecord.status.in_([status.value for status in statuses]))
                    .order_by(JobRecord.created_at.desc())
                    .limit(limit)
                )
            return tuple(self._job(row) for row in session.execute(query).scalars().all())

    def claim_next(self, *, owner: str, now: datetime, lease_seconds: int) -> Job | None:
        """Toma el trabajo pendiente más antiguo que ya se pueda reclamar.

        Nunca dos workers el mismo. Se reclaman también los trabajos con cancelación pedida y
        todavía sin empezar: tienen que pasar por el worker para cerrarse en `cancelled` y dejar el
        lote coherente. Si no se reclamaran, un lote cancelado antes de arrancar se quedaría en
        `cancel_requested` para siempre, sin contadores ni informe.

        Un trabajo con `not_before` en el futuro (espera entre reintentos) **no** se reclama: la
        espera es real, no un texto en el paso.
        """
        claimable = (JobStatus.QUEUED.value, JobStatus.CANCEL_REQUESTED.value)
        with self._session_factory() as session:
            candidate = session.execute(
                select(JobRecord)
                .where(
                    JobRecord.status.in_(claimable),
                    (JobRecord.not_before.is_(None)) | (JobRecord.not_before <= now),
                )
                .order_by(JobRecord.created_at)
                .limit(1)
            ).scalar_one_or_none()
            if candidate is None:
                return None
            result = session.execute(
                update(JobRecord)
                .where(
                    JobRecord.id == candidate.id,
                    JobRecord.status.in_(claimable),
                )
                .values(
                    status=JobStatus.LEASED.value,
                    lease_owner=owner,
                    lease_expires_at=lease_expiry(now, lease_seconds),
                    not_before=None,
                    updated_at=now,
                    started_at=candidate.started_at or now,
                )
            )
            del result  # el estado se comprueba leyendo la fila, que es lo que manda
            session.commit()
            refreshed = session.get(JobRecord, candidate.id)
            if (
                refreshed is None
                or refreshed.status != JobStatus.LEASED.value
                or refreshed.lease_owner != owner
            ):  # pragma: no cover - carrera perdida
                return None
            return self._job(refreshed)

    def mark_running(self, job_id: str, *, owner: str, now: datetime) -> None:
        with self._session_factory() as session:
            record = self._owned(session, job_id, owner)
            record.status = JobStatus.RUNNING.value
            record.updated_at = now
            session.commit()

    def renew_lease(self, job_id: str, *, owner: str, now: datetime, lease_seconds: int) -> bool:
        with self._session_factory() as session:
            record = session.get(JobRecord, job_id)
            if (
                record is None
                or record.lease_owner != owner
                or is_terminal(JobStatus(record.status))
            ):
                return False
            record.lease_expires_at = lease_expiry(now, lease_seconds)
            record.updated_at = now
            session.commit()
            return True

    def report_progress(
        self, job_id: str, *, progress: float, step: str | None, now: datetime
    ) -> None:
        bounded = min(max(progress, 0.0), 1.0)
        with self._session_factory() as session:
            record = session.get(JobRecord, job_id)
            if record is None:
                raise InvariantViolationError("el trabajo no existe")
            record.progress = bounded
            if step is not None:
                record.step = step
            record.updated_at = now
            session.commit()

    def cancellation_requested(self, job_id: str) -> bool:
        with self._session_factory() as session:
            record = session.get(JobRecord, job_id)
            return record is not None and record.cancel_requested_at is not None

    def request_cancel(self, job_id: str, *, now: datetime) -> bool:
        with self._session_factory() as session:
            record = session.get(JobRecord, job_id)
            if record is None or is_terminal(JobStatus(record.status)):
                return False
            record.cancel_requested_at = now
            record.status = JobStatus.CANCEL_REQUESTED.value
            record.updated_at = now
            session.commit()
            return True

    def finish(self, job_id: str, *, owner: str, now: datetime) -> None:
        with self._session_factory() as session:
            record = self._owned(session, job_id, owner)
            record.status = JobStatus.SUCCEEDED.value
            record.progress = 1.0
            record.finished_at = now
            record.updated_at = now
            record.lease_owner = None
            record.lease_expires_at = None
            session.commit()

    def acknowledge_cancel(self, job_id: str, *, owner: str, now: datetime) -> None:
        with self._session_factory() as session:
            record = self._owned(session, job_id, owner)
            record.status = JobStatus.CANCELLED.value
            record.finished_at = now
            record.updated_at = now
            record.lease_owner = None
            record.lease_expires_at = None
            session.commit()

    def fail(
        self,
        job_id: str,
        *,
        error_code: str,
        error_message: str,
        now: datetime,
        retry_at: datetime | None = None,
    ) -> JobStatus:
        """Registra el fallo. Devuelve el estado en el que queda el trabajo.

        Si quedan intentos, el trabajo vuelve a la cola **con espera**: `not_before` guarda cuándo
        se podrá reclamar otra vez, y `claim_next` lo respeta. Un fallo que agota los intentos deja
        el trabajo `failed` y `finished_at` puesto.
        """
        with self._session_factory() as session:
            record = session.get(JobRecord, job_id)
            if record is None:
                raise InvariantViolationError("el trabajo no existe")
            record.attempts += 1
            record.error_code = error_code
            record.error_message = error_message
            record.lease_owner = None
            record.lease_expires_at = None
            record.updated_at = now
            if should_retry(record.attempts, record.max_attempts):
                delay = retry_delay_seconds(record.attempts)
                record.status = JobStatus.QUEUED.value
                record.not_before = (
                    retry_at if retry_at is not None else now + timedelta(seconds=delay)
                )
                record.step = f"reintento en {delay}s"
            else:
                record.status = JobStatus.FAILED.value
                record.not_before = None
                record.finished_at = now
            session.commit()
            return JobStatus(record.status)

    def requeue_expired_leases(self, *, now: datetime) -> tuple[Job, ...]:
        """Trabajos cuyo lease venció (proceso caído) vuelven a la cola.

        Devuelve los trabajos afectados con su estado nuevo, para que quien los recupere pueda
        avisar de los que se quedaron `failed` (agotaron sus intentos). Los que vuelven a la cola
        no esperan: los dejó otro proceso, no un fallo propio.
        """
        with self._session_factory() as session:
            rows = (
                session.execute(
                    select(JobRecord).where(
                        JobRecord.status.in_([JobStatus.LEASED.value, JobStatus.RUNNING.value]),
                        JobRecord.lease_expires_at.is_not(None),
                        JobRecord.lease_expires_at < now,
                    )
                )
                .scalars()
                .all()
            )
            for record in rows:
                record.attempts += 1
                record.lease_owner = None
                record.lease_expires_at = None
                record.updated_at = now
                record.step = "reanudado tras interrupción"
                if should_retry(record.attempts, record.max_attempts):
                    record.status = JobStatus.QUEUED.value
                    record.not_before = None
                else:
                    record.status = JobStatus.FAILED.value
                    record.error_code = "lease_expired"
                    record.error_message = "El trabajo se interrumpió demasiadas veces."
                    record.finished_at = now
            session.commit()
            return tuple(self._job(row) for row in rows)

    # ------------------------------------------------------------------ conversión

    @staticmethod
    def _owned(session: Session, job_id: str, owner: str) -> JobRecord:
        record = session.get(JobRecord, job_id)
        if record is None:
            raise InvariantViolationError("el trabajo no existe")
        if record.lease_owner != owner:
            raise InvariantViolationError("el trabajo pertenece a otro worker")
        return record

    @staticmethod
    def _job(record: JobRecord) -> Job:
        return Job(
            id=record.id,
            job_type=JobType(record.job_type),
            status=JobStatus(record.status),
            payload=json.loads(record.payload_json or "{}"),
            progress=record.progress,
            attempts=record.attempts,
            max_attempts=record.max_attempts,
            created_at=record.created_at,
            updated_at=record.updated_at,
            step=record.step,
            error_code=record.error_code,
            error_message=record.error_message,
            lease_owner=record.lease_owner,
            lease_expires_at=as_utc(record.lease_expires_at),
            not_before=as_utc(record.not_before),
            cancel_requested_at=as_utc(record.cancel_requested_at),
            started_at=record.started_at,
            finished_at=record.finished_at,
        )

    @staticmethod
    def to_view(job: Job) -> JobView:
        return JobView(
            id=job.id,
            job_type=job.job_type.value,
            status=job.status.value,
            progress=job.progress,
            attempts=job.attempts,
            max_attempts=job.max_attempts,
            created_at=job.created_at,
            updated_at=job.updated_at,
            step=job.step,
            error_code=job.error_code,
            error_message=job.error_message,
            started_at=job.started_at,
            finished_at=job.finished_at,
            cancel_requested=job.cancellation_requested,
        )
