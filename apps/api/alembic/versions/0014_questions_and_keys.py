"""Preguntas, opciones, claves, evidencias y explicaciones (S06).

Revision ID: 0014_questions_and_keys
Revises: 0013_documents_versions_and_rights
Create Date: 2026-09-17

Qué añade S06 al esquema (03_DATA-MODEL §6):

1. `question_sets`: el conjunto (examen oficial, banco privado, práctica o lote generado) con su
   convocatoria, su **modelo** (A/B) y el documento del que sale. El modelo vive aquí y no en cada
   pregunta: un examen modelo A es un conjunto, y su clave es la de ese conjunto.
2. `question_versions`: la pregunta con su **clave estable** (su identidad entre versiones) y su
   número de versión, su enunciado, su tipo, su posición, si es reserva y con qué orden, de dónde
   viene (`origin_type`: oficial, privada o generada) y la **sección que la sostiene**.
3. `option_versions`: las opciones. La clave estable y la posición son distintas a propósito: así
   se pueden relacionar modelos A/B con las mismas opciones en otro orden (03_DATA-MODEL §6).
4. `answer_key_versions` y `answer_key_entries`: la plantilla, versionada y aprobada, con el
   desenlace de cada pregunta (`keyed`, `annulled`, `unanswered`, `conflicting`). **Una clave
   activa necesita aprobación**, y solo puede haber **una activa por conjunto** (invariante 5), lo
   que se impone con un índice único parcial: SQLite sí sabe hacerlo.
5. `question_evidence`: qué evidencia sostiene qué parte de la pregunta (enunciado, respuesta
   correcta, distractor o explicación), con su claim y su estado de revisión. El span va con
   `ON DELETE RESTRICT`: una pregunta que cita algo no se queda sin su cita porque alguien borre el
   documento por otra vía.
6. `question_explanations`: la explicación de la pregunta y de cada opción, con su origen y —si la
   escribió un modelo— **con qué modelo y qué versión de plantilla**.

Lo que **no** se puede garantizar con un `CHECK` de SQLite y vive en el servicio, con su prueba:

- que una **clave oficial** tenga plantilla oficial enlazada y aprobada (invariante 4): depende del
  tipo del conjunto, que está en otra tabla;
- que una pregunta **oficial** cite documento de origen oficial (invariante 3): una etiqueta no
  basta.
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0014_questions_and_keys"
down_revision = "0013_documents_versions_and_rights"
branch_labels = None
depends_on = None

_SET_TYPES = ("official_exam", "private_bank", "practice", "generated_batch")
_SET_STATUSES = ("draft", "confirmed", "archived")
_QUESTION_TYPES = ("single_choice", "multi_mark_error", "true_false", "free_text_reference")
_QUESTION_STATUSES = (
    "incomplete",
    "complete",
    "verified",
    "conflicting",
    "annulled",
    "superseded",
)
_ORIGINS = ("official", "private", "generated")
_KEY_STATUSES = ("draft", "active", "superseded", "rejected")
_OUTCOMES = ("keyed", "annulled", "unanswered", "conflicting")
_EVIDENCE_ROLES = ("stem", "correct", "distractor", "explanation")
_EVIDENCE_STATUSES = ("proposed", "accepted", "rejected")
_EXPLANATION_STATUSES = ("draft", "reviewed", "rejected")


def _in(values: tuple[str, ...]) -> str:
    return ", ".join(repr(value) for value in values)


def upgrade() -> None:
    op.create_table(
        "question_sets",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column(
            "opposition_id",
            sa.String(length=36),
            sa.ForeignKey("oppositions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "convocation_version_id",
            sa.String(length=36),
            sa.ForeignKey("convocation_versions.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("set_type", sa.String(length=24), nullable=False),
        # El modelo (A/B) es del conjunto: la plantilla y las reservas cambian con él.
        sa.Column("model_code", sa.String(length=8), nullable=True),
        sa.Column("held_at", sa.Date(), nullable=True),
        sa.Column(
            "source_document_version_id",
            sa.String(length=36),
            sa.ForeignKey("document_versions.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="draft"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(f"set_type IN ({_in(_SET_TYPES)})", name="ck_question_set_type"),
        sa.CheckConstraint(f"status IN ({_in(_SET_STATUSES)})", name="ck_question_set_status"),
        sa.CheckConstraint("length(trim(title)) > 0", name="ck_question_set_title"),
    )
    op.create_index("ix_question_sets_opposition", "question_sets", ["opposition_id"])
    op.create_index("ix_question_sets_type", "question_sets", ["set_type", "status"])

    op.create_table(
        "question_versions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "question_set_id",
            sa.String(length=36),
            sa.ForeignKey("question_sets.id", ondelete="CASCADE"),
            nullable=False,
        ),
        # La identidad de una pregunta entre versiones: la clave estable no cambia al corregirla.
        sa.Column("stable_key", sa.String(length=64), nullable=False),
        sa.Column("version_no", sa.Integer(), nullable=False),
        sa.Column("stem", sa.Text(), nullable=False),
        sa.Column("question_type", sa.String(length=24), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("is_reserve", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("reserve_order", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="incomplete"),
        sa.Column("origin_type", sa.String(length=16), nullable=False),
        sa.Column(
            "source_section_id",
            sa.String(length=36),
            sa.ForeignKey("document_sections.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "supersedes_id",
            sa.String(length=36),
            sa.ForeignKey("question_versions.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(f"question_type IN ({_in(_QUESTION_TYPES)})", name="ck_question_type"),
        sa.CheckConstraint(f"status IN ({_in(_QUESTION_STATUSES)})", name="ck_question_status"),
        sa.CheckConstraint(f"origin_type IN ({_in(_ORIGINS)})", name="ck_question_origin"),
        sa.CheckConstraint("length(trim(stem)) > 0", name="ck_question_stem"),
        sa.CheckConstraint("version_no >= 1", name="ck_question_version_no"),
        sa.CheckConstraint("position >= 1", name="ck_question_position"),
        sa.CheckConstraint(
            "reserve_order IS NULL OR reserve_order >= 1", name="ck_question_reserve_order"
        ),
        # Una pregunta que no es reserva no tiene orden de reserva: o es reserva, o no lo es.
        sa.CheckConstraint("is_reserve OR reserve_order IS NULL", name="ck_question_reserve_flag"),
        sa.CheckConstraint(
            "supersedes_id IS NULL OR supersedes_id <> id", name="ck_question_not_self"
        ),
        sa.UniqueConstraint(
            "question_set_id", "stable_key", "version_no", name="uq_question_version"
        ),
    )
    op.create_index("ix_question_positions", "question_versions", ["question_set_id", "position"])

    op.create_table(
        "option_versions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "question_version_id",
            sa.String(length=36),
            sa.ForeignKey("question_versions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("stable_key", sa.String(length=16), nullable=False),
        sa.Column("label", sa.String(length=16), nullable=True),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.CheckConstraint("position >= 1", name="ck_option_position"),
        sa.CheckConstraint("length(trim(text)) > 0", name="ck_option_text"),
        sa.UniqueConstraint("question_version_id", "stable_key", name="uq_option_key"),
        # Dos opciones de la misma versión no comparten sitio: el orden es del modelo, no del azar.
        sa.UniqueConstraint("question_version_id", "position", name="uq_option_position"),
    )

    op.create_table(
        "answer_key_versions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "question_set_id",
            sa.String(length=36),
            sa.ForeignKey("question_sets.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "source_document_version_id",
            sa.String(length=36),
            sa.ForeignKey("document_versions.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("version_no", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="draft"),
        sa.Column(
            "supersedes_id",
            sa.String(length=36),
            sa.ForeignKey("answer_key_versions.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("published_at", sa.Date(), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(f"status IN ({_in(_KEY_STATUSES)})", name="ck_key_status"),
        sa.CheckConstraint("version_no >= 1", name="ck_key_version_no"),
        # Una clave activa está aprobada: sin aprobación no se corrige con ella.
        sa.CheckConstraint("status <> 'active' OR approved_at IS NOT NULL", name="ck_key_approved"),
        sa.CheckConstraint("supersedes_id IS NULL OR supersedes_id <> id", name="ck_key_not_self"),
        sa.UniqueConstraint("question_set_id", "version_no", name="uq_key_version"),
    )
    # Una sola clave activa por conjunto (invariante 5). Las anteriores permanecen con su estado.
    op.create_index(
        "uq_answer_key_active",
        "answer_key_versions",
        ["question_set_id"],
        unique=True,
        sqlite_where=sa.text("status = 'active'"),
    )

    op.create_table(
        "answer_key_entries",
        sa.Column(
            "answer_key_version_id",
            sa.String(length=36),
            sa.ForeignKey("answer_key_versions.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "question_version_id",
            sa.String(length=36),
            sa.ForeignKey("question_versions.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("outcome", sa.String(length=16), nullable=False),
        sa.Column("correct_option_keys_json", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.CheckConstraint(f"outcome IN ({_in(_OUTCOMES)})", name="ck_key_entry_outcome"),
        # «Con clave» sin clave no es un desenlace: es un hueco, y el hueco se llama `unanswered`.
        sa.CheckConstraint(
            "outcome <> 'keyed' OR (correct_option_keys_json IS NOT NULL "
            "AND correct_option_keys_json <> '[]')",
            name="ck_key_entry_has_key",
        ),
    )

    op.create_table(
        "question_evidence",
        sa.Column(
            "question_version_id",
            sa.String(length=36),
            sa.ForeignKey("question_versions.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        # La cita de una pregunta no se queda sin su span: el documento no se borra por debajo.
        sa.Column(
            "evidence_span_id",
            sa.String(length=36),
            sa.ForeignKey("evidence_spans.id", ondelete="RESTRICT"),
            primary_key=True,
        ),
        sa.Column("role", sa.String(length=16), primary_key=True),
        sa.Column("claim", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="proposed"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(f"role IN ({_in(_EVIDENCE_ROLES)})", name="ck_question_evidence_role"),
        sa.CheckConstraint(
            f"status IN ({_in(_EVIDENCE_STATUSES)})", name="ck_question_evidence_status"
        ),
    )

    op.create_table(
        "question_explanations",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "question_version_id",
            sa.String(length=36),
            sa.ForeignKey("question_versions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        # Nulo = explicación de la pregunta entera; con valor, de esa opción.
        sa.Column("option_stable_key", sa.String(length=16), nullable=True),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("origin", sa.String(length=16), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="draft"),
        sa.Column("model_name", sa.Text(), nullable=True),
        sa.Column("prompt_template_version", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(f"origin IN ({_in(_ORIGINS)})", name="ck_explanation_origin"),
        sa.CheckConstraint(
            f"status IN ({_in(_EXPLANATION_STATUSES)})", name="ck_explanation_status"
        ),
        sa.CheckConstraint("length(trim(text)) > 0", name="ck_explanation_text"),
        # Una explicación generada dice con qué se generó: sin eso no es trazable.
        sa.CheckConstraint(
            "origin <> 'generated' OR model_name IS NOT NULL", name="ck_explanation_generated"
        ),
        sa.UniqueConstraint(
            "question_version_id", "option_stable_key", name="uq_explanation_option"
        ),
    )
    # Una sola explicación de la pregunta entera (el NULL no lo cubre el único de arriba en SQLite).
    op.create_index(
        "uq_explanation_question",
        "question_explanations",
        ["question_version_id"],
        unique=True,
        sqlite_where=sa.text("option_stable_key IS NULL"),
    )


def downgrade() -> None:
    # El orden inverso: primero lo que cuelga de lo demás.
    op.drop_index("uq_explanation_question", table_name="question_explanations")
    op.drop_table("question_explanations")
    op.drop_table("question_evidence")
    op.drop_table("answer_key_entries")
    op.drop_index("uq_answer_key_active", table_name="answer_key_versions")
    op.drop_table("answer_key_versions")
    op.drop_table("option_versions")
    op.drop_index("ix_question_positions", table_name="question_versions")
    op.drop_table("question_versions")
    op.drop_index("ix_question_sets_type", table_name="question_sets")
    op.drop_index("ix_question_sets_opposition", table_name="question_sets")
    op.drop_table("question_sets")
