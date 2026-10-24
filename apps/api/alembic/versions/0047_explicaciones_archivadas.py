"""Las explicaciones privadas del propietario se archivan, no se pierden (remate, punto 1).

**Qué es**: **dos cambios que solo tienen sentido juntos**.

1. **El estado `archived`.** **Cuando una explicación generada sustituye a una privada, la privada
   no se borra**: se queda en la misma tabla, con su texto original y `status = 'archived'`, **para
   que la sustitución se pueda deshacer**. **El `CHECK` de estados no lo permitía**, así que
   cualquier intento de guardar el original habría fallado en vez de archivar.
2. **El único por pregunta pasa a ser parcial.** `uq_explanation_question` garantiza **una sola
   explicación de la pregunta entera por versión**; **con las archivadas tienen que convivir la
   viva y las archivadas**, así que el índice pasa a cubrir solo las que no están archivadas.
   **Sigue habiendo una sola viva**, que es exactamente lo que protegía.

**Lo que no cambia**: **lo que se sirve al alumno**. **Las lecturas filtran
`status <> 'archived'`**, así que el texto que se ve es el mismo de antes.

**Por qué la tabla se reconstruye a mano y no con `batch_alter_table`**: **el modo por lotes refleja
la tabla con SQLAlchemy, y SQLAlchemy no refleja los `CHECK` de SQLite**. **Reconstruir por ahí
habría borrado `ck_explanation_origin`, `ck_explanation_text` y `ck_explanation_generated`** — tres
comprobaciones que hoy están y que nadie notaría al día siguiente. **Aquí el `CREATE TABLE` se
escribe entero**, con las tres y con la nueva.

**Y el SQL va literal, sin construirlo con f-strings**: en una migración **lo que se lee tiene que
ser exactamente lo que se ejecuta**, y una cadena montada esconde eso.

Revision ID: 0047_explicaciones_archivadas
Revises: 0046_invitaciones
"""

from __future__ import annotations

from alembic import op

revision = "0047_explicaciones_archivadas"
down_revision = "0046_invitaciones"
branch_labels = None
depends_on = None

_TABLA = "question_explanations"
_ANTERIOR = "question_explanations_anterior"

#: La tabla de siempre **con el estado nuevo**. Las tres comprobaciones que no se tocan,
#: tal cual.
_CUERPO_CON_ARCHIVADAS = """
    CREATE TABLE question_explanations (
        id VARCHAR(36) NOT NULL,
        question_version_id VARCHAR(36) NOT NULL,
        option_stable_key VARCHAR(16),
        text TEXT NOT NULL,
        origin VARCHAR(16) NOT NULL,
        status VARCHAR(16) DEFAULT 'draft' NOT NULL,
        model_name TEXT,
        prompt_template_version TEXT,
        created_at DATETIME NOT NULL,
        citation TEXT,
        note_anchor_id VARCHAR(36),
        PRIMARY KEY (id),
        CONSTRAINT ck_explanation_origin
            CHECK (origin IN ('official', 'private', 'generated')),
        CONSTRAINT ck_explanation_status
            CHECK (status IN ('draft', 'reviewed', 'rejected', 'archived')),
        CONSTRAINT ck_explanation_text CHECK (length(trim(text)) > 0),
        CONSTRAINT ck_explanation_generated
            CHECK (origin <> 'generated' OR model_name IS NOT NULL),
        CONSTRAINT uq_explanation_option UNIQUE (question_version_id, option_stable_key),
        FOREIGN KEY(question_version_id) REFERENCES question_versions (id) ON DELETE CASCADE
    )
"""

#: La misma tabla sin el estado nuevo: es a la que se vuelve si se baja.
_CUERPO_SIN_ARCHIVADAS = """
    CREATE TABLE question_explanations (
        id VARCHAR(36) NOT NULL,
        question_version_id VARCHAR(36) NOT NULL,
        option_stable_key VARCHAR(16),
        text TEXT NOT NULL,
        origin VARCHAR(16) NOT NULL,
        status VARCHAR(16) DEFAULT 'draft' NOT NULL,
        model_name TEXT,
        prompt_template_version TEXT,
        created_at DATETIME NOT NULL,
        citation TEXT,
        note_anchor_id VARCHAR(36),
        PRIMARY KEY (id),
        CONSTRAINT ck_explanation_origin
            CHECK (origin IN ('official', 'private', 'generated')),
        CONSTRAINT ck_explanation_status CHECK (status IN ('draft', 'reviewed', 'rejected')),
        CONSTRAINT ck_explanation_text CHECK (length(trim(text)) > 0),
        CONSTRAINT ck_explanation_generated
            CHECK (origin <> 'generated' OR model_name IS NOT NULL),
        CONSTRAINT uq_explanation_option UNIQUE (question_version_id, option_stable_key),
        FOREIGN KEY(question_version_id) REFERENCES question_versions (id) ON DELETE CASCADE
    )
"""

#: Las columnas, en su orden. **Copiar con `select *` sería más corto y también más frágil**: si
#: mañana alguien añade una columna en medio, el `insert` se lleva lo que no debe.
_COPIAR = """
    INSERT INTO question_explanations (
        id, question_version_id, option_stable_key, text, origin, status,
        model_name, prompt_template_version, created_at, citation, note_anchor_id
    )
    SELECT
        id, question_version_id, option_stable_key, text, origin, status,
        model_name, prompt_template_version, created_at, citation, note_anchor_id
    FROM question_explanations_anterior
"""

#: **Una sola explicación viva por versión**: la archivada convive con la que la sustituyó.
_INDICE_CON_ARCHIVADAS = """
    CREATE UNIQUE INDEX uq_explanation_question
    ON question_explanations (question_version_id)
    WHERE option_stable_key IS NULL AND status <> 'archived'
"""

_INDICE_SIN_ARCHIVADAS = """
    CREATE UNIQUE INDEX uq_explanation_question
    ON question_explanations (question_version_id)
    WHERE option_stable_key IS NULL
"""


def upgrade() -> None:
    op.execute(f"ALTER TABLE {_TABLA} RENAME TO {_ANTERIOR}")
    op.execute(_CUERPO_CON_ARCHIVADAS)
    op.execute(_COPIAR)
    op.execute(f"DROP TABLE {_ANTERIOR}")
    op.execute(_INDICE_CON_ARCHIVADAS)


def downgrade() -> None:
    # **Bajar borra las archivadas**: no hay sitio para ellas con el `CHECK` viejo. Se dice aquí
    # para que nadie lo descubra después de ejecutarlo.
    op.execute("DELETE FROM question_explanations WHERE status = 'archived'")
    op.execute(f"ALTER TABLE {_TABLA} RENAME TO {_ANTERIOR}")
    op.execute(_CUERPO_SIN_ARCHIVADAS)
    op.execute(_COPIAR)
    op.execute(f"DROP TABLE {_ANTERIOR}")
    op.execute(_INDICE_SIN_ARCHIVADAS)
