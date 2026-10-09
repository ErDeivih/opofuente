"""Los apuntes guiados por las preguntas: hechos, apartados y comprobaciones (pasos B-E).

Revision ID: 0029_apuntes_por_preguntas
Revises: 0028_fuera_de_temario
Create Date: 2026-10-08

Tres tablas, y cada una contesta a una pregunta distinta del trabajo de apuntes
(`APUNTES-COMPLETOS-GUIADOS-POR-PREGUNTAS-2026-10`):

1. **`topic_facts`**: qué hay que saber. Un hecho sale de una o varias preguntas del tema y lleva
   escrito de dónde salió (`source_group_ids`, `source_question_ids`): sin ese rastro no se puede
   decir qué preguntas sostiene un apartado ni volver a pedir los hechos que faltan.
   - `text_hash` es la huella normalizada del texto del hecho (sin acentos, sin signos, en
     minúsculas) y hay un índice único por tema: **una corrida se reanuda** y volver a pasar por el
     mismo lote no puede duplicar los hechos. Un texto libre como clave única sería frágil (un
     espacio de más son dos hechos distintos); la huella no.
   - `subsection_key` es nulo hasta que el esquema reparte los hechos por apartados: así se ve lo
   que
     todavía no tiene sitio, en vez de perderlo.
2. **`topic_note_sections`**: el texto de cada apartado, con su anclaje estable (`anchor`) y su
   subapartado (`subsection_key`). Clave única por tema y subapartado: el esquema es determinista y
   volver a calcularlo **actualiza la fila, no crea otra**, que es lo que permite que un hecho nuevo
   encuentre su sitio sin tocar el texto que ya estaba.
3. **`question_note_anchors`**: el rastro pregunta → párrafo. Una fila por **cada** pregunta (no por
   grupo: las repetidas entre bancos comparten grupo y tienen que poder abrir su párrafo), con el
   resultado (`covered`, `gap`, `doubtful`), la frase copiada de los apuntes que lo justifica y el
   estado de la clave con la que se comprobó. La clave única es `(pregunta, tema)`: una pregunta
   dentro de un tema tiene un solo resultado, el de la última comprobación.

`gap` existe como estado guardado aunque el plan lo llame «hueco»: es el estado intermedio entre la
primera comprobación y el añadido, y guardarlo es lo que permite **reanudar** una corrida larga sin
volver a comprobar lo ya comprobado.
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0029_apuntes_por_preguntas"
down_revision = "0028_fuera_de_temario"
branch_labels = None
depends_on = None

_KINDS = ("normativo", "tecnico")
_COVERAGE = ("covered", "gap", "doubtful")
_KEY_STATUS = ("active", "draft", "ninguna")
_SECTION_STATUS = ("pending", "reviewed")


def _in(valores: tuple[str, ...]) -> str:
    return ", ".join(repr(valor) for valor in valores)


def upgrade() -> None:
    op.create_table(
        "topic_facts",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "curriculum_node_id",
            sa.String(length=36),
            sa.ForeignKey("curriculum_nodes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("epigraph_code", sa.Text(), nullable=False),
        #: Nulo hasta que el esquema lo reparte: un hecho sin apartado es un hecho que se ve.
        sa.Column("subsection_key", sa.Text(), nullable=True),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("text_hash", sa.String(length=64), nullable=False),
        sa.Column("kind", sa.String(length=16), nullable=False),
        sa.Column("doubtful", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("source_group_ids", sa.Text(), nullable=False),
        sa.Column("source_question_ids", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(f"kind IN ({_in(_KINDS)})", name="ck_topic_fact_kind"),
        sa.CheckConstraint("length(trim(text)) > 0", name="ck_topic_fact_text"),
        sa.CheckConstraint("length(text_hash) = 64", name="ck_topic_fact_hash"),
        sa.UniqueConstraint("curriculum_node_id", "text_hash", name="uq_topic_fact_text"),
    )
    op.create_index("ix_topic_facts_node", "topic_facts", ["curriculum_node_id"])
    op.create_index(
        "ix_topic_facts_subsection", "topic_facts", ["curriculum_node_id", "subsection_key"]
    )

    op.create_table(
        "topic_note_sections",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "curriculum_node_id",
            sa.String(length=36),
            sa.ForeignKey("curriculum_nodes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("subsection_key", sa.Text(), nullable=False),
        sa.Column("epigraph_code", sa.Text(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("anchor", sa.Text(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("body_markdown", sa.Text(), nullable=False, server_default=""),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="pending"),
        sa.Column("needs_review_reason", sa.Text(), nullable=True),
        sa.Column("model", sa.Text(), nullable=True),
        sa.Column("prompt_template_version", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(f"status IN ({_in(_SECTION_STATUS)})", name="ck_note_section_status"),
        sa.CheckConstraint("position >= 1", name="ck_note_section_position"),
        sa.CheckConstraint("length(trim(subsection_key)) > 0", name="ck_note_section_key"),
        sa.CheckConstraint("length(trim(anchor)) > 0", name="ck_note_section_anchor"),
        sa.UniqueConstraint("curriculum_node_id", "subsection_key", name="uq_note_section_key"),
    )
    op.create_index(
        "ix_note_sections_node_position", "topic_note_sections", ["curriculum_node_id", "position"]
    )

    op.create_table(
        "question_note_anchors",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "question_version_id",
            sa.String(length=36),
            sa.ForeignKey("question_versions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "curriculum_node_id",
            sa.String(length=36),
            sa.ForeignKey("curriculum_nodes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        #: El apartado al que apunta la pregunta. Nulo solo si el apartado se borró: el resultado de
        #: la comprobación sigue siendo verdad aunque el texto desaparezca.
        sa.Column(
            "section_id",
            sa.String(length=36),
            sa.ForeignKey("topic_note_sections.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("anchor", sa.Text(), nullable=False),
        sa.Column("group_signature", sa.String(length=64), nullable=False),
        sa.Column("quoted_sentence", sa.Text(), nullable=True),
        sa.Column("answer_letter", sa.String(length=4), nullable=True),
        sa.Column("expected_letters", sa.Text(), nullable=True),
        sa.Column("key_status", sa.String(length=16), nullable=False),
        sa.Column("result", sa.String(length=16), nullable=False),
        sa.Column("note", sa.String(length=48), nullable=True),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("checked_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(f"key_status IN ({_in(_KEY_STATUS)})", name="ck_anchor_key_status"),
        sa.CheckConstraint(f"result IN ({_in(_COVERAGE)})", name="ck_anchor_result"),
        sa.CheckConstraint("attempts >= 1", name="ck_anchor_attempts"),
        sa.UniqueConstraint(
            "question_version_id", "curriculum_node_id", name="uq_anchor_question_node"
        ),
    )
    op.create_index(
        "ix_anchors_node_result", "question_note_anchors", ["curriculum_node_id", "result"]
    )
    op.create_index("ix_anchors_section", "question_note_anchors", ["section_id"])


def downgrade() -> None:
    op.drop_index("ix_anchors_section", table_name="question_note_anchors")
    op.drop_index("ix_anchors_node_result", table_name="question_note_anchors")
    op.drop_table("question_note_anchors")
    op.drop_index("ix_note_sections_node_position", table_name="topic_note_sections")
    op.drop_table("topic_note_sections")
    op.drop_index("ix_topic_facts_subsection", table_name="topic_facts")
    op.drop_index("ix_topic_facts_node", table_name="topic_facts")
    op.drop_table("topic_facts")
