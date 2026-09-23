"""Un lote se puede pausar y reanudar (DEBT-027 §4).

Revision ID: 0023_pause_batch
Revises: 0022_convocation_exam_date_note
Create Date: 2026-09-23

`07_UI-UX` §4 pide «pausar/cancelar» en el lote en proceso, y hasta ahora solo existía cancelar.
Pausar no es cancelar: cancelar termina el lote; pausar lo deja donde está para seguir después, con
lo ya copiado copiado. Eso exige dos estados nuevos y una consecuencia que no es evidente:

1. **`ingestion_batches.status`** admite `paused`: el lote no avanza.
2. **`jobs.status`** admite `paused`: el trabajo que lo movía queda detenido sin terminar, para
   poder reencolarlo al reanudar. Un trabajo en curso no se interrumpe: lo para su manejador entre
   entradas.
3. **El índice único parcial de idempotencia se recrea con `paused` en su predicado.** Esto no se ve
   al leer el estado: `uq_jobs_idempotency_alive` impedía encolar dos veces la misma operación
   *mientras siga viva*, y su definición enumeraba los estados vivos. Con `paused` fuera de esa
   lista, pausar un lote liberaría su clave y un segundo `ingest_batch` del mismo lote podría
   encolarse mientras el primero está en pausa: dos trabajos avanzando el mismo lote.

En SQLite, ensanchar una restricción `CHECK` obliga a recrear la tabla. El índice de idempotencia
se retira **antes** de la recreación y se vuelve a crear después, para no depender de si la
recreación lo hubiera conservado o no.
"""

from __future__ import annotations

from alembic import op

revision = "0023_pause_batch"
down_revision = "0022_convocation_exam_date_note"
branch_labels = None
depends_on = None

_JOB_CON_PAUSA = (
    "status IN ('queued', 'leased', 'running', 'succeeded', 'failed', 'cancel_requested', "
    "'cancelled', 'paused')"
)
_JOB_SIN_PAUSA = (
    "status IN ('queued', 'leased', 'running', 'succeeded', 'failed', 'cancel_requested', "
    "'cancelled')"
)
_LOTE_CON_PAUSA = (
    "status IN ('queued', 'running', 'succeeded', 'failed', 'cancel_requested', 'cancelled', "
    "'paused')"
)
_LOTE_SIN_PAUSA = (
    "status IN ('queued', 'running', 'succeeded', 'failed', 'cancel_requested', 'cancelled')"
)

#: Estados que ocupan la clave de idempotencia: un trabajo pausado sigue siendo el trabajo del lote.
_VIVOS_CON_PAUSA = (
    "idempotency_key IS NOT NULL AND status IN ('queued', 'leased', 'running', "
    "'cancel_requested', 'paused')"
)
_VIVOS_SIN_PAUSA = (
    "idempotency_key IS NOT NULL AND status IN ('queued', 'leased', 'running', 'cancel_requested')"
)


def upgrade() -> None:
    op.drop_index("uq_jobs_idempotency_alive", table_name="jobs")
    with op.batch_alter_table("jobs") as batch:
        batch.drop_constraint("ck_job_status", type_="check")
        batch.create_check_constraint("ck_job_status", _JOB_CON_PAUSA)
    op.execute(
        "CREATE UNIQUE INDEX uq_jobs_idempotency_alive ON jobs(idempotency_key) "
        f"WHERE {_VIVOS_CON_PAUSA}"
    )
    with op.batch_alter_table("ingestion_batches") as batch:
        batch.drop_constraint("ck_batch_status", type_="check")
        batch.create_check_constraint("ck_batch_status", _LOTE_CON_PAUSA)


def downgrade() -> None:
    # Los lotes y trabajos en pausa vuelven a la cola antes de estrechar las restricciones: al
    # revés, la recreación de la tabla copiaría filas que la restricción nueva rechaza.
    op.execute("UPDATE ingestion_batches SET status = 'queued' WHERE status = 'paused'")
    op.execute("UPDATE jobs SET status = 'queued' WHERE status = 'paused'")
    with op.batch_alter_table("ingestion_batches") as batch:
        batch.drop_constraint("ck_batch_status", type_="check")
        batch.create_check_constraint("ck_batch_status", _LOTE_SIN_PAUSA)
    op.drop_index("uq_jobs_idempotency_alive", table_name="jobs")
    with op.batch_alter_table("jobs") as batch:
        batch.drop_constraint("ck_job_status", type_="check")
        batch.create_check_constraint("ck_job_status", _JOB_SIN_PAUSA)
    op.execute(
        "CREATE UNIQUE INDEX uq_jobs_idempotency_alive ON jobs(idempotency_key) "
        f"WHERE {_VIVOS_SIN_PAUSA}"
    )
