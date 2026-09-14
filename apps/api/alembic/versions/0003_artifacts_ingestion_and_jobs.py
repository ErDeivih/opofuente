"""Almacén de artefactos, inventario, lotes y trabajos.

Revision ID: 0003_artifacts_ingestion_and_jobs
Revises: 0002_profiles_and_curriculum
Create Date: 2026-09-14

Crea las tablas de S02 (03_DATA-MODEL §3 y §9 más los `jobs` de 02_ARCHITECTURE §6):

- `source_artifacts` y `artifact_origins`: un artefacto por contenido (sha256 único) y un origen
  por cada sitio donde se ha visto. Dos archivos idénticos con nombres distintos producen **un**
  artefacto y **dos** orígenes.
- `ingestion_batches`, `ingestion_items` e `import_issues`: lotes de inventario o importación, sus
  entradas y sus incidencias.
- `jobs`: cola persistida con lease, intentos y cancelación cooperativa.

"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0003_artifacts_ingestion_and_jobs"
down_revision = "0002_profiles_and_curriculum"
branch_labels = None
depends_on = None

_ITEM_STATUSES = (
    "discovered",
    "inventoried",
    "omitted",
    "copied",
    "hashed",
    "failed",
    "cancelled",
)
_BATCH_STATUSES = (
    "queued",
    "running",
    "succeeded",
    "failed",
    "cancel_requested",
    "cancelled",
)
_JOB_STATUSES = (
    "queued",
    "leased",
    "running",
    "succeeded",
    "failed",
    "cancel_requested",
    "cancelled",
)
_JOB_TYPES = (
    "inventory_source",
    "ingest_batch",
    "extract_artifact",
    "classify_document",
    "parse_question_set",
    "build_fts",
    "embed_spans",
    "diff_versions",
    "invalidate_derivatives",
    "export_backup",
)


def upgrade() -> None:
    op.create_table(
        "source_artifacts",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("sha256", sa.String(length=64), nullable=False, unique=True),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("media_type", sa.String(length=128), nullable=False),
        sa.Column("storage_key", sa.String(length=255), nullable=False),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("quarantine_status", sa.String(length=16), nullable=False, server_default="none"),
        sa.CheckConstraint("size_bytes >= 0", name="ck_artifact_size"),
        sa.CheckConstraint("length(sha256) = 64", name="ck_artifact_sha256_length"),
    )

    op.create_table(
        "artifact_origins",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "artifact_id",
            sa.String(length=36),
            sa.ForeignKey("source_artifacts.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("origin_type", sa.String(length=16), nullable=False),
        sa.Column("display_location", sa.Text(), nullable=False),
        sa.Column("source_path_display", sa.Text(), nullable=True),
        sa.Column("original_name", sa.Text(), nullable=True),
        sa.Column("accessed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=True),
        sa.Column("mtime", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "origin_type IN ('file', 'url', 'paste', 'generated')", name="ck_origin_type"
        ),
        # Un origen se identifica por su ubicación: volver a importar la misma carpeta no duplica
        # orígenes, pero un fichero modificado produce otro artefacto (y por tanto otro origen).
        sa.UniqueConstraint("artifact_id", "display_location", name="uq_artifact_origin"),
    )
    op.create_index("ix_artifact_origins_artifact", "artifact_origins", ["artifact_id"])

    op.create_table(
        "ingestion_batches",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("kind", sa.String(length=16), nullable=False),
        sa.Column("mode", sa.String(length=16), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("source_path_display", sa.Text(), nullable=False),
        # Ruta real de la carpeta señalada por el usuario. Se guarda porque la importación necesita
        # volver a leer el origen, pero **nunca** sale en la API ni en los logs: la interfaz recibe
        # `source_path_display`, que es la versión abreviada.
        sa.Column("source_root", sa.Text(), nullable=True),
        sa.Column("counters_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("manifest_hash", sa.String(length=64), nullable=True),
        sa.Column("error_summary", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("job_id", sa.String(length=36), nullable=True),
        sa.Column(
            "inventory_batch_id",
            sa.String(length=36),
            sa.ForeignKey("ingestion_batches.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.CheckConstraint("kind IN ('inventory', 'import')", name="ck_batch_kind"),
        sa.CheckConstraint("mode IN ('read_only', 'copy')", name="ck_batch_mode"),
        sa.CheckConstraint(
            "status IN ('queued', 'running', 'succeeded', 'failed', 'cancel_requested', "
            "'cancelled')",
            name="ck_batch_status",
        ),
    )

    op.create_table(
        "ingestion_items",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "batch_id",
            sa.String(length=36),
            sa.ForeignKey("ingestion_batches.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("relative_path", sa.Text(), nullable=False),
        sa.Column("original_name", sa.Text(), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("mtime", sa.DateTime(timezone=True), nullable=True),
        sa.Column("media_type", sa.String(length=128), nullable=True),
        sa.Column(
            "artifact_id",
            sa.String(length=36),
            sa.ForeignKey("source_artifacts.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("detail", sa.Text(), nullable=True),
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
        sa.CheckConstraint(
            "status IN ('discovered', 'inventoried', 'omitted', 'copied', 'hashed', 'failed', "
            "'cancelled')",
            name="ck_item_status",
        ),
        sa.UniqueConstraint("batch_id", "relative_path", name="uq_item_path"),
    )
    op.create_index("ix_ingestion_items_batch", "ingestion_items", ["batch_id"])

    op.create_table(
        "import_issues",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "batch_id",
            sa.String(length=36),
            sa.ForeignKey("ingestion_batches.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "item_id",
            sa.String(length=36),
            sa.ForeignKey("ingestion_items.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("code", sa.String(length=48), nullable=False),
        sa.Column("severity", sa.String(length=16), nullable=False),
        sa.Column("safe_message", sa.Text(), nullable=False),
        sa.Column("details_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolution", sa.Text(), nullable=True),
        sa.CheckConstraint("severity IN ('info', 'warning', 'error')", name="ck_issue_severity"),
    )
    op.create_index("ix_import_issues_batch", "import_issues", ["batch_id"])

    op.create_table(
        "jobs",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("job_type", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("progress", sa.Float(), nullable=False, server_default="0"),
        sa.Column("step", sa.Text(), nullable=True),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("error_code", sa.String(length=48), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("idempotency_key", sa.String(length=128), nullable=True),
        sa.Column("lease_owner", sa.String(length=64), nullable=True),
        sa.Column("lease_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancel_requested_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "status IN ('queued', 'leased', 'running', 'succeeded', 'failed', "
            "'cancel_requested', 'cancelled')",
            name="ck_job_status",
        ),
        sa.CheckConstraint(
            "job_type IN ("
            "'inventory_source', 'ingest_batch', 'extract_artifact', 'classify_document', "
            "'parse_question_set', 'build_fts', 'embed_spans', 'diff_versions', "
            "'invalidate_derivatives', 'export_backup')",
            name="ck_job_type",
        ),
        sa.CheckConstraint("progress >= 0 AND progress <= 1", name="ck_job_progress"),
        sa.CheckConstraint("attempts >= 0", name="ck_job_attempts"),
    )
    op.create_index("ix_jobs_status_created", "jobs", ["status", "created_at"])
    # Una misma operación no se encola dos veces mientras siga viva (idempotencia).
    op.execute(
        "CREATE UNIQUE INDEX uq_jobs_idempotency_alive ON jobs(idempotency_key) "
        "WHERE idempotency_key IS NOT NULL AND status IN ('queued', 'leased', 'running', "
        "'cancel_requested')"
    )


def downgrade() -> None:
    op.drop_index("uq_jobs_idempotency_alive", table_name="jobs")
    op.drop_index("ix_jobs_status_created", table_name="jobs")
    op.drop_table("jobs")
    op.drop_index("ix_import_issues_batch", table_name="import_issues")
    op.drop_table("import_issues")
    op.drop_index("ix_ingestion_items_batch", table_name="ingestion_items")
    op.drop_table("ingestion_items")
    op.drop_table("ingestion_batches")
    op.drop_index("ix_artifact_origins_artifact", table_name="artifact_origins")
    op.drop_table("artifact_origins")
    op.drop_table("source_artifacts")
