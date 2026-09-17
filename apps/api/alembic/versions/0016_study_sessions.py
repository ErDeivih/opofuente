"""Sesiones de estudio, composición congelada, intentos y evaluaciones (S07).

Revision ID: 0016_study_sessions
Revises: 0015_question_notes_and_issues
Create Date: 2026-09-17

Cuatro tablas, y el porqué de cada una:

1. **`study_sessions`**: la sesión con su modo, su estado y —congelada al iniciar— su configuración.
   `answer_key_version_id` guarda **la clave con la que se corrige**: activar otra después no
   reescribe lo pasado (invariante 7), y S08 añadirá la reevaluación.
2. **`session_questions`**: la composición exacta que se presentó: la versión de la pregunta, su
   parte declarada, si es reserva y con qué orden, y **la clave congelada** de esa pregunta. Sin esa
   foto, recargar la sesión o activar una plantilla nueva cambiaría lo que la persona ya vio.
3. **`attempts`**: lo que hizo la persona (qué marcó, cuánto tardó, con qué confianza y en qué orden
   de cliente). El acierto **no** se guarda aquí: se deduce de su evaluación, para que no haya dos
   verdades que puedan separarse.
4. **`attempt_evaluations`**: la corrección con la clave congelada, con la puntuación **exacta**
   (`score_numerator`/`score_denominator`: un tercio no es un decimal) y con `supersedes_id` para
   que recalcular con una clave nueva sea una evaluación nueva y no un borrón (DEBT-006, ADR-010).

`learning_errors` y `review_items` (03_DATA-MODEL §7) llegan en S10, que es el slice de errores y
repaso: no se crean aquí vacías para no fingir que ya existen.
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0016_study_sessions"
down_revision = "0015_question_notes_and_issues"
branch_labels = None
depends_on = None

_MODES = ("practice", "error_review", "official_exam", "mock_exam", "diagnostic")
_STATUSES = ("draft", "running", "finished", "abandoned")
_FEEDBACK = ("immediate", "at_end")
_CONFIDENCE = ("low", "medium", "high")
_OUTCOMES = ("correct", "wrong", "blank", "annulled", "excluded", "conflicting", "unused_reserve")
_KEY_OUTCOMES = ("keyed", "annulled", "unanswered", "conflicting")


def _in(values: tuple[str, ...]) -> str:
    return ", ".join(repr(value) for value in values)


def upgrade() -> None:
    op.create_table(
        "study_sessions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "opposition_id",
            sa.String(length=36),
            sa.ForeignKey("oppositions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "convocation_version_id",
            sa.String(length=36),
            sa.ForeignKey("convocation_versions.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column(
            "question_set_id",
            sa.String(length=36),
            sa.ForeignKey("question_sets.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column(
            "answer_key_version_id",
            sa.String(length=36),
            sa.ForeignKey("answer_key_versions.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column("mode", sa.String(length=16), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="draft"),
        sa.Column("feedback", sa.String(length=16), nullable=False),
        sa.Column("configuration_json", sa.Text(), nullable=False),
        sa.Column("result_json", sa.Text(), nullable=True),
        sa.Column("time_limit_minutes", sa.Integer(), nullable=True),
        sa.Column("total_questions", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(f"mode IN ({_in(_MODES)})", name="ck_session_mode"),
        sa.CheckConstraint(f"status IN ({_in(_STATUSES)})", name="ck_session_status"),
        sa.CheckConstraint(f"feedback IN ({_in(_FEEDBACK)})", name="ck_session_feedback"),
        sa.CheckConstraint("total_questions >= 0", name="ck_session_total"),
        # Una sesión en marcha tiene que tener reloj de inicio, y una terminada también su final.
        sa.CheckConstraint(
            "status <> 'running' OR started_at IS NOT NULL", name="ck_session_running_started"
        ),
        sa.CheckConstraint(
            "status <> 'finished' OR finished_at IS NOT NULL", name="ck_session_finished_at"
        ),
    )
    op.create_index("ix_study_sessions_opposition", "study_sessions", ["opposition_id", "status"])

    op.create_table(
        "session_questions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "session_id",
            sa.String(length=36),
            sa.ForeignKey("study_sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "question_version_id",
            sa.String(length=36),
            sa.ForeignKey("question_versions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("stable_key", sa.String(length=64), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("part_code", sa.String(length=64), nullable=True),
        sa.Column("is_reserve", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("reserve_order", sa.Integer(), nullable=True),
        # La clave tal como estaba al iniciar: desenlace y opciones correctas, congelados.
        sa.Column("key_outcome", sa.String(length=16), nullable=True),
        sa.Column("correct_option_keys_json", sa.Text(), nullable=False, server_default="[]"),
        sa.CheckConstraint("position > 0", name="ck_session_question_position"),
        sa.CheckConstraint(
            "key_outcome IS NULL OR key_outcome IN " + f"({_in(_KEY_OUTCOMES)})",
            name="ck_session_question_key_outcome",
        ),
        sa.CheckConstraint(
            "is_reserve = 0 OR reserve_order IS NOT NULL",
            name="ck_session_question_reserve_order",
        ),
        sa.UniqueConstraint("session_id", "position", name="uq_session_question_position"),
        sa.UniqueConstraint(
            "session_id", "question_version_id", name="uq_session_question_version"
        ),
    )
    op.create_index("ix_session_questions_session", "session_questions", ["session_id", "position"])

    op.create_table(
        "attempts",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "session_question_id",
            sa.String(length=36),
            sa.ForeignKey("session_questions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("chosen_option_keys_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("elapsed_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("confidence", sa.String(length=16), nullable=True),
        sa.Column("client_sequence", sa.Integer(), nullable=True),
        sa.Column("answered_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("elapsed_ms >= 0", name="ck_attempt_elapsed"),
        sa.CheckConstraint(
            "confidence IS NULL OR confidence IN " + f"({_in(_CONFIDENCE)})",
            name="ck_attempt_confidence",
        ),
        # Un intento por pregunta: el intento se **congela** al registrarlo (06_QUESTIONS §6), así
        # que reenviar lo mismo tras recargar devuelve el intento que ya había en vez de crear otro.
        sa.UniqueConstraint("session_question_id", name="uq_attempt_per_question"),
    )

    op.create_table(
        "attempt_evaluations",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "attempt_id",
            sa.String(length=36),
            sa.ForeignKey("attempts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "answer_key_version_id",
            sa.String(length=36),
            sa.ForeignKey("answer_key_versions.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column("outcome", sa.String(length=16), nullable=False),
        sa.Column("score_numerator", sa.Integer(), nullable=False),
        sa.Column("score_denominator", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column(
            "supersedes_id",
            sa.String(length=36),
            sa.ForeignKey("attempt_evaluations.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("evaluated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(f"outcome IN ({_in(_OUTCOMES)})", name="ck_evaluation_outcome"),
        sa.CheckConstraint("score_denominator > 0", name="ck_evaluation_denominator"),
        sa.UniqueConstraint("attempt_id", "answer_key_version_id", name="uq_evaluation_per_key"),
    )
    op.create_index("ix_evaluations_attempt", "attempt_evaluations", ["attempt_id", "evaluated_at"])


def downgrade() -> None:
    op.drop_index("ix_evaluations_attempt", table_name="attempt_evaluations")
    op.drop_table("attempt_evaluations")
    op.drop_table("attempts")
    op.drop_index("ix_session_questions_session", table_name="session_questions")
    op.drop_table("session_questions")
    op.drop_index("ix_study_sessions_opposition", table_name="study_sessions")
    op.drop_table("study_sessions")
