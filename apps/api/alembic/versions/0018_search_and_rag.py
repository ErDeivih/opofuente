"""Índice léxico y consultas de RAG (S09).

Revision ID: 0018_search_and_rag
Revises: 0017_previous_result
Create Date: 2026-09-17

Tres piezas, y el porqué de cada una:

1. **`evidence_fts`**: un índice FTS5 sobre los fragmentos de evidencia (`05_RAG §4`). Es de
   **contenido externo** (`content='evidence_spans'`): el texto no se duplica, se indexa el que ya
   está, y los disparadores lo mantienen en sincronía. Se indexa también la etiqueta de cita porque
   lleva el título de la sección, que es lo que se busca cuando la pregunta nombra un tema.
2. **Las tablas del ciclo de RAG** (`03_DATA-MODEL §8`): `rag_queries`, `retrieval_hits`,
   `generated_answers` y `answer_claims` + su tabla de evidencias. Se guardan **todos** los
   fragmentos recuperados y cuáles se usaron (`05_RAG §5`, paso 9), y cada afirmación queda enlazada
   a los fragmentos que cita: una respuesta se puede auditar después, que es el punto.
3. **`answer_claim_evidence`**: una afirmación puede apoyarse en varios fragmentos. Un JSON habría
   sido más corto y no habría impedido citar un fragmento que no existe; con clave foránea
   `ON DELETE RESTRICT`, borrar una evidencia citada por una respuesta falla, que es lo correcto.

El índice es **reconstruible** (`INSERT INTO evidence_fts(evidence_fts) VALUES('rebuild')`), que es
lo que exige §4: si algo se desincroniza, se rehace desde SQLite sin volver a extraer nada.
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0018_search_and_rag"
down_revision = "0017_previous_result"
branch_labels = None
depends_on = None

_STATUSES = ("supported", "partial", "insufficient")
_STRATEGIES = ("lexical", "hybrid")
_SUPPORTS = ("direct", "inferred")

#: Las columnas del índice, escritas en cada sentencia: SQL literal, sin interpolar nada.
_FTS_COLUMNS = "id, text, normalized_text, citation_label"


def upgrade() -> None:
    # 1. El índice léxico, con su contenido externo en `evidence_spans`.
    op.execute(
        """
        CREATE VIRTUAL TABLE evidence_fts USING fts5(
            id, text, normalized_text, citation_label,
            content='evidence_spans',
            content_rowid='rowid',
            tokenize='unicode61 remove_diacritics 2'
        )
        """
    )
    # Y sus disparadores: sin ellos, el índice se queda atrás en cuanto se promociona material.
    op.execute(
        """
        CREATE TRIGGER evidence_spans_fts_ai AFTER INSERT ON evidence_spans BEGIN
            INSERT INTO evidence_fts(rowid, id, text, normalized_text, citation_label)
            VALUES (new.rowid, new.id, new.text, new.normalized_text, new.citation_label);
        END
        """
    )
    op.execute(
        """
        CREATE TRIGGER evidence_spans_fts_ad AFTER DELETE ON evidence_spans BEGIN
            INSERT INTO evidence_fts(evidence_fts, rowid, id, text, normalized_text,
                                     citation_label)
            VALUES ('delete', old.rowid, old.id, old.text, old.normalized_text,
                    old.citation_label);
        END
        """
    )
    op.execute(
        """
        CREATE TRIGGER evidence_spans_fts_au AFTER UPDATE ON evidence_spans BEGIN
            INSERT INTO evidence_fts(evidence_fts, rowid, id, text, normalized_text,
                                     citation_label)
            VALUES ('delete', old.rowid, old.id, old.text, old.normalized_text,
                    old.citation_label);
            INSERT INTO evidence_fts(rowid, id, text, normalized_text, citation_label)
            VALUES (new.rowid, new.id, new.text, new.normalized_text, new.citation_label);
        END
        """
    )

    # 2. Las consultas, sus recuperaciones y sus respuestas.
    op.create_table(
        "rag_queries",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "opposition_id",
            sa.String(length=36),
            sa.ForeignKey("oppositions.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column(
            "convocation_version_id",
            sa.String(length=36),
            sa.ForeignKey("convocation_versions.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("filters_json", sa.Text(), nullable=False),
        sa.Column("strategy", sa.String(length=16), nullable=False),
        sa.Column("version_mode", sa.String(length=24), nullable=False, server_default="current"),
        #: Revisión del corpus con la que se respondió: si el corpus cambia, la respuesta se marca
        #: como de otra revisión en lugar de reutilizarse a ciegas (`05_RAG §13`).
        sa.Column("corpus_revision", sa.String(length=64), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False, server_default="extractive"),
        sa.Column("model", sa.Text(), nullable=True),
        sa.Column("prompt_template_version", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            f"strategy IN ({', '.join(repr(valor) for valor in _STRATEGIES)})",
            name="ck_rag_strategy",
        ),
        sa.CheckConstraint(
            "version_mode IN ('current', 'explicit_historical')", name="ck_rag_version_mode"
        ),
        sa.CheckConstraint("length(trim(question)) > 0", name="ck_rag_question"),
    )
    op.create_index("ix_rag_queries_created", "rag_queries", ["created_at"])

    op.create_table(
        "retrieval_hits",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "query_id",
            sa.String(length=36),
            sa.ForeignKey("rag_queries.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "span_id",
            sa.String(length=36),
            sa.ForeignKey("evidence_spans.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("strategy", sa.String(length=16), nullable=False, server_default="lexical"),
        #: Si el fragmento llegó a entregarse al redactor o se quedó fuera por diversificación.
        sa.Column("used", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.CheckConstraint("rank > 0", name="ck_hit_rank"),
        sa.CheckConstraint(
            f"strategy IN ({', '.join(repr(valor) for valor in _STRATEGIES)})",
            name="ck_hit_strategy",
        ),
        sa.UniqueConstraint("query_id", "span_id", name="uq_hit_span"),
    )

    op.create_table(
        "generated_answers",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "query_id",
            sa.String(length=36),
            sa.ForeignKey("rag_queries.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("short_answer", sa.Text(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("uncertainties_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("suggested_followups_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("provider", sa.String(length=32), nullable=False, server_default="extractive"),
        sa.Column("model", sa.Text(), nullable=True),
        sa.Column("prompt_template_version", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            f"status IN ({', '.join(repr(valor) for valor in _STATUSES)})",
            name="ck_answer_status",
        ),
        sa.UniqueConstraint("query_id", name="uq_answer_per_query"),
    )

    op.create_table(
        "answer_claims",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "answer_id",
            sa.String(length=36),
            sa.ForeignKey("generated_answers.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("support", sa.String(length=16), nullable=False, server_default="direct"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("position > 0", name="ck_claim_position"),
        sa.CheckConstraint(
            f"support IN ({', '.join(repr(valor) for valor in _SUPPORTS)})",
            name="ck_claim_support",
        ),
        sa.CheckConstraint("length(trim(text)) > 0", name="ck_claim_text"),
        sa.UniqueConstraint("answer_id", "position", name="uq_claim_position"),
    )

    op.create_table(
        "answer_claim_evidence",
        sa.Column(
            "claim_id",
            sa.String(length=36),
            sa.ForeignKey("answer_claims.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "span_id",
            sa.String(length=36),
            sa.ForeignKey("evidence_spans.id", ondelete="RESTRICT"),
            primary_key=True,
        ),
    )


def downgrade() -> None:
    op.drop_table("answer_claim_evidence")
    op.drop_table("answer_claims")
    op.drop_table("generated_answers")
    op.drop_table("retrieval_hits")
    op.drop_index("ix_rag_queries_created", table_name="rag_queries")
    op.drop_table("rag_queries")
    op.execute("DROP TRIGGER evidence_spans_fts_au")
    op.execute("DROP TRIGGER evidence_spans_fts_ad")
    op.execute("DROP TRIGGER evidence_spans_fts_ai")
    op.execute("DROP TABLE evidence_fts")
