"""Nota de corrección, incidencias reportadas y mapeos de preguntas (S06).

Revision ID: 0015_question_notes_and_issues
Revises: 0014_questions_and_keys
Create Date: 2026-09-17

Tres huecos que aparecieron al implementar las rutas de §9 del contrato y que el modelo de datos no
cubría. Se añaden aquí, con su porqué, en lugar de improvisar un sitio peor:

1. **`question_versions.note`**: el contrato pide `POST /questions/{id}/local-corrections`, y una
   corrección local se hace **con motivo** («modificar una transcripción oficial crea corrección
   local con motivo», 06_QUESTIONS §4). El motivo tiene que quedar en la pregunta corregida, no
   solo en la auditoría: quien lea la pregunta después tiene que ver por qué cambió.
2. **`question_issue_reports`**: `POST /questions/{id}/report-issue` («reportar
   ambigua/conflicto») no tenía dónde guardarse. No es una clasificación ni una propuesta: es lo
   que dice quien estudia, y tiene que poder revisarse. Se guarda con su tipo, su detalle y su
   estado.
3. **Preguntas en mapeos y colecciones**: `curriculum_mappings.subject_type` y
   `collection_items.subject_type` se amplían con `question_version`, para poder asignar una
   pregunta a un tema del programa (07_UI-UX §7: «asignación temática») y meterla en una
   colección. En SQLite hay que reconstruir las tablas, así que se hace con `batch_alter_table`,
   igual que la 0013.
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0015_question_notes_and_issues"
down_revision = "0014_questions_and_keys"
branch_labels = None
depends_on = None

#: Vocabulario de mapeos y colecciones **con** la pregunta: el de 0013 más `question_version`.
_SUBJECTS_WITH_QUESTIONS = (
    "artifact",
    "representation",
    "document_version",
    "section",
    "evidence",
    "question_version",
)
_SUBJECTS_WITHOUT_QUESTIONS = (
    "artifact",
    "representation",
    "document_version",
    "section",
    "evidence",
)
_ISSUE_KINDS = ("ambiguous", "wrong_key", "typo", "outdated", "other")
_ISSUE_STATUSES = ("open", "reviewed", "dismissed")


def _in(values: tuple[str, ...]) -> str:
    return ", ".join(repr(value) for value in values)


def upgrade() -> None:
    # 1. El motivo de una corrección local vive con la pregunta corregida.
    with op.batch_alter_table("question_versions") as batch:
        batch.add_column(sa.Column("note", sa.Text(), nullable=True))

    # 2. Lo que reporta quien estudia, con su estado de revisión.
    op.create_table(
        "question_issue_reports",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "question_version_id",
            sa.String(length=36),
            sa.ForeignKey("question_versions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("kind", sa.String(length=16), nullable=False),
        sa.Column("detail", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="open"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(f"kind IN ({_in(_ISSUE_KINDS)})", name="ck_issue_kind"),
        sa.CheckConstraint(f"status IN ({_in(_ISSUE_STATUSES)})", name="ck_issue_status"),
        sa.CheckConstraint("length(trim(detail)) > 0", name="ck_issue_detail"),
    )
    op.create_index(
        "ix_issue_reports_question", "question_issue_reports", ["question_version_id", "status"]
    )

    # 3. Una pregunta se puede asignar a un tema del programa y meter en una colección.
    with op.batch_alter_table("curriculum_mappings") as batch:
        batch.drop_constraint("ck_mapping_subject", type_="check")
        batch.create_check_constraint(
            "ck_mapping_subject", f"subject_type IN ({_in(_SUBJECTS_WITH_QUESTIONS)})"
        )
    with op.batch_alter_table("collection_items") as batch:
        batch.drop_constraint("ck_collection_subject", type_="check")
        batch.create_check_constraint(
            "ck_collection_subject", f"subject_type IN ({_in(_SUBJECTS_WITH_QUESTIONS)})"
        )


def downgrade() -> None:
    with op.batch_alter_table("collection_items") as batch:
        batch.drop_constraint("ck_collection_subject", type_="check")
        batch.create_check_constraint(
            "ck_collection_subject", f"subject_type IN ({_in(_SUBJECTS_WITHOUT_QUESTIONS)})"
        )
    with op.batch_alter_table("curriculum_mappings") as batch:
        batch.drop_constraint("ck_mapping_subject", type_="check")
        batch.create_check_constraint(
            "ck_mapping_subject", f"subject_type IN ({_in(_SUBJECTS_WITHOUT_QUESTIONS)})"
        )
    op.drop_index("ix_issue_reports_question", table_name="question_issue_reports")
    op.drop_table("question_issue_reports")
    with op.batch_alter_table("question_versions") as batch:
        batch.drop_column("note")
