"""Documentos, versiones, derechos, secciones, evidencias y colecciones (S05).

Revision ID: 0013_documents_versions_and_rights
Revises: 0012_classification_and_review
Create Date: 2026-09-16

Qué añade S05 al esquema:

1. `rights_statuses`: condiciones de uso de una fuente. **Desconocido es un valor explícito** y se
   trata como restringido (09_SECURITY §8): sin revisar la licencia, la aplicación no
   puede afirmar que el material se pueda reutilizar.
2. `logical_documents`: la **obra** (título canónico, tipo documental, autoridad y propietario).
   `owner_scope` es lo que decide si se puede mostrar o compartir, y un documento privado no se hace
   público por clasificación automática (03_DATA-MODEL §4).
3. `document_versions`: los ficheros concretos que representan la obra. El artefacto va con
   `ON DELETE RESTRICT`: la biblioteca **no puede perder el material** del que sale una versión.
4. `document_sections` y `evidence_spans`: la estructura y las unidades citables. Una cita tiene que
   poder abrir la sección o la página correcta, así que la evidencia guarda offsets y página.
5. `collections` y `collection_items`: organización personal; un ítem puede estar en varias
   sin duplicar bytes.
6. **Se amplía el `CHECK` de `curriculum_mappings.subject_type`** para admitir `document_version`,
   `section` y `evidence`: la migración que la 0012 dejó anunciada. En SQLite hay que reconstruir la
   tabla, así que se hace con `batch_alter_table`.

Lo que **no** hace y no se puede garantizar con un `CHECK` de SQLite: que haya una sola
versión activa por documento. Es una regla de la aplicación y vive en el servicio, con su prueba.
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0013_documents_versions_and_rights"
down_revision = "0012_classification_and_review"
branch_labels = None
depends_on = None

_DOCUMENT_TYPES = (
    "convocation",
    "curriculum",
    "law_or_regulation",
    "official_technical",
    "private_syllabus",
    "personal_notes",
    "official_exam",
    "answer_key",
    "private_question_bank",
    "practical_case",
    "flashcards",
    "community_material",
    "unknown",
)
_OWNER_SCOPES = ("public", "private_user", "generated")
_VERSION_STATUSES = ("candidate", "accepted", "outdated", "superseded", "withdrawn", "rejected")
_RIGHTS_REVIEW = ("unknown", "reviewed", "restricted")
_INDEX_STATUSES = ("pending", "indexed", "failed", "stale")
_SECTION_TYPES = ("page", "title", "chapter", "article", "provision", "technical", "topic")
_OLD_MAPPING_SUBJECTS = ("artifact", "representation")
_MAPPING_SUBJECTS = ("artifact", "representation", "document_version", "section", "evidence")


def _in(values: tuple[str, ...]) -> str:
    return ", ".join(repr(value) for value in values)


def upgrade() -> None:
    op.create_table(
        "rights_statuses",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("code", sa.String(length=48), nullable=False),
        sa.Column("license_name", sa.Text(), nullable=True),
        sa.Column("license_url", sa.Text(), nullable=True),
        sa.Column("attribution", sa.Text(), nullable=True),
        sa.Column("commercial_reuse", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("sharing", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("review_status", sa.String(length=16), nullable=False, server_default="unknown"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(f"review_status IN ({_in(_RIGHTS_REVIEW)})", name="ck_rights_review"),
        sa.UniqueConstraint("code", name="uq_rights_code"),
    )

    op.create_table(
        "logical_documents",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("canonical_title", sa.Text(), nullable=False),
        sa.Column("document_type", sa.String(length=32), nullable=False),
        sa.Column("authority_tier", sa.String(length=8), nullable=True),
        sa.Column(
            "owner_scope", sa.String(length=16), nullable=False, server_default="private_user"
        ),
        sa.Column("canonical_identifier", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(f"document_type IN ({_in(_DOCUMENT_TYPES)})", name="ck_document_type"),
        sa.CheckConstraint(f"owner_scope IN ({_in(_OWNER_SCOPES)})", name="ck_document_scope"),
        sa.CheckConstraint("length(trim(canonical_title)) > 0", name="ck_document_title"),
    )
    op.create_index("ix_documents_type", "logical_documents", ["document_type"])
    op.create_index("ix_documents_scope", "logical_documents", ["owner_scope"])

    op.create_table(
        "document_versions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "logical_document_id",
            sa.String(length=36),
            sa.ForeignKey("logical_documents.id", ondelete="CASCADE"),
            nullable=False,
        ),
        # La biblioteca no puede perder el material del que sale una versión.
        sa.Column(
            "artifact_id",
            sa.String(length=36),
            sa.ForeignKey("source_artifacts.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "representation_id",
            sa.String(length=36),
            sa.ForeignKey("extracted_representations.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("version_label", sa.Text(), nullable=True),
        sa.Column("published_at", sa.Date(), nullable=True),
        sa.Column("valid_from", sa.Date(), nullable=True),
        sa.Column("valid_to", sa.Date(), nullable=True),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("language", sa.String(length=16), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="candidate"),
        sa.Column(
            "supersedes_id",
            sa.String(length=36),
            sa.ForeignKey("document_versions.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "rights_status_id",
            sa.String(length=36),
            sa.ForeignKey("rights_statuses.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("official_url", sa.Text(), nullable=True),
        sa.Column("content_hash", sa.String(length=64), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approved_by", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(f"status IN ({_in(_VERSION_STATUSES)})", name="ck_version_status"),
        sa.CheckConstraint(
            "status <> 'accepted' OR approved_at IS NOT NULL", name="ck_version_approved"
        ),
        sa.CheckConstraint(
            "valid_from IS NULL OR valid_to IS NULL OR valid_to >= valid_from",
            name="ck_version_validity",
        ),
        sa.CheckConstraint(
            "supersedes_id IS NULL OR supersedes_id <> id", name="ck_version_not_self"
        ),
        # El mismo artefacto no puede ser dos versiones del mismo documento: son los mismos bytes.
        sa.UniqueConstraint("logical_document_id", "artifact_id", name="uq_version_artifact"),
    )
    op.create_index("ix_versions_document", "document_versions", ["logical_document_id"])
    op.create_index("ix_versions_artifact", "document_versions", ["artifact_id"])
    op.create_index("ix_versions_status", "document_versions", ["status"])

    op.create_table(
        "document_sections",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "document_version_id",
            sa.String(length=36),
            sa.ForeignKey("document_versions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "parent_id",
            sa.String(length=36),
            sa.ForeignKey("document_sections.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("section_type", sa.String(length=16), nullable=False),
        sa.Column("label", sa.Text(), nullable=True),
        sa.Column("title", sa.Text(), nullable=True),
        sa.Column("position", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("page_start", sa.Integer(), nullable=True),
        sa.Column("page_end", sa.Integer(), nullable=True),
        sa.Column("char_start", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("char_end", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("ordinal", sa.Integer(), nullable=False, server_default="1"),
        sa.CheckConstraint(f"section_type IN ({_in(_SECTION_TYPES)})", name="ck_section_type"),
        sa.CheckConstraint("position >= 1", name="ck_section_position"),
        sa.CheckConstraint("char_start >= 0 AND char_end >= char_start", name="ck_section_offsets"),
        sa.CheckConstraint(
            "page_start IS NULL OR page_end IS NULL OR page_end >= page_start",
            name="ck_section_pages",
        ),
        sa.UniqueConstraint("document_version_id", "ordinal", name="uq_section_ordinal"),
    )
    op.create_index("ix_sections_version", "document_sections", ["document_version_id"])
    op.create_index("ix_sections_parent", "document_sections", ["parent_id"])

    op.create_table(
        "evidence_spans",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "document_version_id",
            sa.String(length=36),
            sa.ForeignKey("document_versions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "section_id",
            sa.String(length=36),
            sa.ForeignKey("document_sections.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("ordinal", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("normalized_text", sa.Text(), nullable=False),
        sa.Column("char_start", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("char_end", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("page", sa.Integer(), nullable=True),
        sa.Column("citation_label", sa.Text(), nullable=True),
        sa.Column("quality", sa.String(length=24), nullable=True),
        sa.Column("index_status", sa.String(length=16), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(f"index_status IN ({_in(_INDEX_STATUSES)})", name="ck_evidence_index"),
        sa.CheckConstraint(
            "char_start >= 0 AND char_end >= char_start", name="ck_evidence_offsets"
        ),
        sa.CheckConstraint("ordinal >= 1", name="ck_evidence_ordinal"),
        sa.UniqueConstraint("document_version_id", "ordinal", name="uq_evidence_ordinal"),
    )
    op.create_index("ix_evidence_version", "evidence_spans", ["document_version_id"])
    op.create_index("ix_evidence_section", "evidence_spans", ["section_id"])

    op.create_table(
        "collections",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("length(trim(name)) > 0", name="ck_collection_name"),
    )

    op.create_table(
        "collection_items",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "collection_id",
            sa.String(length=36),
            sa.ForeignKey("collections.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("subject_type", sa.String(length=24), nullable=False),
        sa.Column("subject_id", sa.String(length=36), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("added_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            f"subject_type IN ({_in(_MAPPING_SUBJECTS)})", name="ck_collection_subject"
        ),
        sa.UniqueConstraint(
            "collection_id", "subject_type", "subject_id", name="uq_collection_item"
        ),
    )

    # Los mapeos ya no apuntan solo a artefactos y representaciones: S05 añade documentos,
    # secciones y evidencias. En SQLite hay que reconstruir la tabla para cambiar un CHECK.
    with op.batch_alter_table("curriculum_mappings") as batch:
        batch.drop_constraint("ck_mapping_subject", type_="check")
        batch.create_check_constraint(
            "ck_mapping_subject", f"subject_type IN ({_in(_MAPPING_SUBJECTS)})"
        )


def downgrade() -> None:
    with op.batch_alter_table("curriculum_mappings") as batch:
        batch.drop_constraint("ck_mapping_subject", type_="check")
        batch.create_check_constraint(
            "ck_mapping_subject", f"subject_type IN ({_in(_OLD_MAPPING_SUBJECTS)})"
        )

    op.drop_table("collection_items")
    op.drop_table("collections")

    op.drop_index("ix_evidence_section", table_name="evidence_spans")
    op.drop_index("ix_evidence_version", table_name="evidence_spans")
    op.drop_table("evidence_spans")

    op.drop_index("ix_sections_parent", table_name="document_sections")
    op.drop_index("ix_sections_version", table_name="document_sections")
    op.drop_table("document_sections")

    op.drop_index("ix_versions_status", table_name="document_versions")
    op.drop_index("ix_versions_artifact", table_name="document_versions")
    op.drop_index("ix_versions_document", table_name="document_versions")
    op.drop_table("document_versions")

    op.drop_index("ix_documents_scope", table_name="logical_documents")
    op.drop_index("ix_documents_type", table_name="logical_documents")
    op.drop_table("logical_documents")

    op.drop_table("rights_statuses")
