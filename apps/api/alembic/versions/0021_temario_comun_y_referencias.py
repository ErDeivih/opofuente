"""Temario común versionado y convocatorias que lo referencian (S13).

Revision ID: 0021_temario_comun_y_referencias
Revises: 0020_changes_and_derivatives
Create Date: 2026-11-04

Cambia de dueño el programa sin cambiar sus nodos. Hasta ahora un nodo de programa colgaba de
**una** convocatoria (`convocation_version_id`), así que el temario era una copia por convocatoria:
la misma pregunta clasificada contra el nodo de una convocatoria no aparecía al estudiar otra. Este
paso implanta el modelo aprobado en `ESPECIFICACION.md` §5 y §6:

1. **cinco tablas nuevas**: `curricula` (la identidad del temario: común o publicado),
   `curriculum_versions` (sus ediciones), `convocation_curriculum_refs` (qué versión estudia cada
   convocatoria y cuál publica, con su cita), `convocation_curriculum_adjustments` (sus
   particularidades: omite, pondera, renumera, renombra) y `curriculum_equivalences` (el puente
   entre un nodo publicado y uno común);
2. `curriculum_nodes` pasa a colgar de `curriculum_version_id` (NOT NULL, FK CASCADE) y gana
   `origin_kind` (`base`/`enrichment`) y `origin_convocation_version_id` (procedencia del
   enriquecimiento, `SET NULL` al borrar la convocatoria). La unicidad pasa de
   `unique(convocation_version_id, path)` a `unique(curriculum_version_id, path)`;
3. **ningún nodo se borra ni cambia de `id`**: los 235 de la base viva se conservan tal cual. Cada
   convocatoria que publicaba programa conserva su árbol, ahora en una versión `published`, y una
   fila `convocation_curriculum_refs` con `role='official'` la enlaza de nuevo. Ese es el puente de
   ida y vuelta del `downgrade`.

Qué **no** hace esta migración, a propósito (§6.1, §6.3):

- no inventa títulos: el temario común se crea **vacío y en `draft`**; el contenido (5 bloques,
  40 temas) entra por fixture y lo publica la siembra, igual que los perfiles oficiales (ADR-006);
- no decide qué convocatorias son de informática C1: la referencia `primary` del TAI también la
  crea la siembra, porque es una decisión de producto, no de esquema;
- no re-apunta preguntas ni fallos al temario común: eso es la tarea de equivalencias (B-003), con
  su informe por fila y su inverso probado.

El `downgrade` reconstruye `convocation_version_id` desde las referencias `official` y comprueba que
no queda ningún nodo sin convocatoria; si lo hay, **falla** en vez de inventar una. Consecuencia
honesta: cuando la siembra haya creado los 40 temas del temario común (B-002), esos nodos no tendrán
programa publicado al que volver y la bajada fallará a propósito; entonces se decidirá si los
descarta o si deja de ofrecerse. Con datos solo publicados —el estado de esta migración— la
bajada devuelve el esquema **funcionalmente** a `0020`: mismas columnas, índices y restricciones con
las mismas acciones, aunque SQLite reconstruya la tabla y las restricciones queden con nombre (y
cambie el orden de columnas). Ningún camino del producto depende de esos nombres.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import sqlalchemy as sa

from alembic import op

revision = "0021_temario_comun_y_referencias"
down_revision = "0020_changes_and_derivatives"
branch_labels = None
depends_on = None

# ---------------------------------------------------------------------------------- nombres fijos
#
# La recreación de una tabla en SQLite copia las restricciones reflejadas. Las claves foráneas de
# `curriculum_nodes` no tenían nombre (`0002`), así que la recreación les da uno con esta convención
# (lo documenta la `0007`) y, sobre todo, permite retirar por nombre las que crea y retira esta
# migración. No se confía en la reflexión para lo que hay que poder quitar después.

_CONVENCION_NOMBRES = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

_FK_VERSION = "fk_curriculum_node_version"
_FK_ORIGEN = "fk_curriculum_node_origin_convocation"
_UQ_NODO = "uq_curriculum_node_path"
_IX_VERSION = "ix_curriculum_node_version"
_CK_ORIGEN = "ck_node_origin_kind"

#: Identidad del temario común (§5.2). La versión nace en `draft`: la publica la siembra cuando el
#: contenido cuadra (§6.2 C.2 y §6.7).
_TEMARIO_COMUN = "informatica-c1"
_TEMARIO_COMUN_NOMBRE = "Temario común de informática C1"
_TEMARIO_COMUN_VERSION = "informatica-c1-v1"
#: Hash abreviado tal y como consta en `ESPECIFICACION.md` §6.2 C.2. No se inventa el completo: el
#: fixture y su generador (B-002) son quienes lo calculan de la fuente real y lo verifican.
_TEMARIO_COMUN_FUENTE = "minicerebro/temario-c1.md, sha256 50d8fa7f…dcea"


def _comprobar_integridad_referencial(momento: str) -> None:
    """Comprueba con `PRAGMA foreign_key_check` que la recreación no dejó referencias rotas.

    La conexión de Alembic no enciende `PRAGMA foreign_keys` (la de la aplicación sí), así que la
    comprobación explícita es la única red dentro de la migración; las pruebas también la hacen por
    fuera.
    """
    filas = op.get_bind().execute(sa.text("PRAGMA foreign_key_check")).all()
    if filas:
        raise RuntimeError(
            f"0021 ({momento}): {len(filas)} violaciones de clave foránea tras la migración; "
            f"primeras: {filas[:5]}"
        )


def _ahora() -> datetime:
    return datetime.now(UTC)


def _nuevo_id() -> str:
    return str(uuid4())


def _lista(valores: tuple[str, ...]) -> str:
    return ", ".join(repr(valor) for valor in valores)


def upgrade() -> None:
    ahora = _ahora()

    # ---------------------------------------------------------------- A. estructura nueva (§6.2 A)
    op.create_table(
        "curricula",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("code", sa.String(length=64), nullable=False, unique=True),
        sa.Column("kind", sa.String(length=16), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("group_code", sa.String(length=8), nullable=True),
        sa.Column("family", sa.String(length=32), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            f"kind IN ({_lista(('common', 'published'))})", name="ck_curriculum_kind"
        ),
    )

    op.create_table(
        "curriculum_versions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "curriculum_id",
            sa.String(length=36),
            sa.ForeignKey("curricula.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("version_no", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False, unique=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("source_reference", sa.Text(), nullable=True),
        sa.Column(
            "supersedes_id",
            sa.String(length=36),
            sa.ForeignKey("curriculum_versions.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("version_no >= 1", name="ck_curriculum_version_no"),
        sa.CheckConstraint(
            f"status IN ({_lista(('draft', 'active', 'superseded', 'archived'))})",
            name="ck_curriculum_version_status",
        ),
        sa.CheckConstraint(
            "supersedes_id IS NULL OR supersedes_id <> id", name="ck_curriculum_version_self"
        ),
        sa.UniqueConstraint("curriculum_id", "version_no", name="uq_curriculum_version_no"),
    )
    # Solo una versión activa por temario: es la restricción que hace cumplir I1 en la base, no solo
    # en el servicio.
    op.execute(
        "CREATE UNIQUE INDEX uq_curriculum_version_single_active "
        "ON curriculum_versions(curriculum_id) WHERE status = 'active'"
    )

    op.create_table(
        "convocation_curriculum_refs",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "convocation_version_id",
            sa.String(length=36),
            sa.ForeignKey("convocation_versions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "curriculum_version_id",
            sa.String(length=36),
            sa.ForeignKey("curriculum_versions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("role", sa.String(length=16), nullable=False),
        sa.Column("source_reference", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            f"role IN ({_lista(('primary', 'official', 'complementary'))})", name="ck_ref_role"
        ),
        sa.UniqueConstraint(
            "convocation_version_id", "curriculum_version_id", name="uq_convocation_curriculum_ref"
        ),
    )
    op.create_index(
        "ix_conv_curriculum_ref_convocation",
        "convocation_curriculum_refs",
        ["convocation_version_id"],
    )
    # Una convocatoria tiene a lo sumo un temario de estudio (`primary`) y un programa publicado
    # (`official`): dos «primarios» serían dos verdades sobre qué se estudia (I3).
    op.execute(
        "CREATE UNIQUE INDEX uq_convocation_primary_ref "
        "ON convocation_curriculum_refs(convocation_version_id) WHERE role = 'primary'"
    )
    op.execute(
        "CREATE UNIQUE INDEX uq_convocation_official_ref "
        "ON convocation_curriculum_refs(convocation_version_id) WHERE role = 'official'"
    )

    op.create_table(
        "convocation_curriculum_adjustments",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "ref_id",
            sa.String(length=36),
            sa.ForeignKey("convocation_curriculum_refs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "curriculum_node_id",
            sa.String(length=36),
            sa.ForeignKey("curriculum_nodes.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("kind", sa.String(length=16), nullable=False),
        sa.Column("weight", sa.Float(), nullable=True),
        sa.Column("official_code_override", sa.String(length=32), nullable=True),
        sa.Column("title_override", sa.Text(), nullable=True),
        # La cita es obligatoria: no se inventa que una convocatoria omite o pondera algo (I8).
        sa.Column("evidence_quote", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            f"kind IN ({_lista(('omitted', 'weighted', 'renumbered', 'renamed'))})",
            name="ck_adjustment_kind",
        ),
        sa.CheckConstraint("weight IS NULL OR weight >= 0", name="ck_adjustment_weight_range"),
        sa.CheckConstraint(
            "kind <> 'weighted' OR (weight IS NOT NULL AND weight >= 0)",
            name="ck_adjustment_weighted",
        ),
        sa.CheckConstraint(
            "kind <> 'renumbered' OR official_code_override IS NOT NULL",
            name="ck_adjustment_renumbered",
        ),
        sa.CheckConstraint(
            "kind <> 'renamed' OR title_override IS NOT NULL", name="ck_adjustment_renamed"
        ),
        sa.CheckConstraint("length(trim(evidence_quote)) > 0", name="ck_adjustment_evidence"),
        sa.UniqueConstraint("ref_id", "curriculum_node_id", "kind", name="uq_adjustment_identity"),
    )
    op.create_index(
        "ix_conv_curriculum_adjustment_ref", "convocation_curriculum_adjustments", ["ref_id"]
    )
    op.create_index(
        "ix_conv_curriculum_adjustment_node",
        "convocation_curriculum_adjustments",
        ["curriculum_node_id"],
    )

    op.create_table(
        "curriculum_equivalences",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "source_node_id",
            sa.String(length=36),
            sa.ForeignKey("curriculum_nodes.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "target_node_id",
            sa.String(length=36),
            sa.ForeignKey("curriculum_nodes.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("relation", sa.String(length=16), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("evidence_note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            f"relation IN ({_lista(('equivalent', 'subset', 'superset', 'partial'))})",
            name="ck_equivalence_relation",
        ),
        sa.CheckConstraint(
            f"status IN ({_lista(('proposed', 'accepted', 'rejected'))})",
            name="ck_equivalence_status",
        ),
        sa.CheckConstraint("confidence >= 0 AND confidence <= 1", name="ck_equivalence_confidence"),
        sa.CheckConstraint("source_node_id <> target_node_id", name="ck_equivalence_distinct"),
        sa.CheckConstraint(
            "status <> 'accepted' OR decided_at IS NOT NULL", name="ck_equivalence_decided"
        ),
        sa.UniqueConstraint("source_node_id", "target_node_id", name="uq_equivalence_pair"),
    )
    op.create_index(
        "ix_curriculum_equivalence_source", "curriculum_equivalences", ["source_node_id"]
    )
    op.create_index(
        "ix_curriculum_equivalence_target", "curriculum_equivalences", ["target_node_id"]
    )

    # ----------------------------------------------- B. abrir curriculum_nodes en caliente (§6.2 B)
    #
    # La columna nueva entra **sin FK y nullable**: la FK y el NOT NULL esperan al paso D, cuando ya
    # no queda ningún NULL. `origin_kind` es NOT NULL con valor por defecto porque los nodos que ya
    # existen salen todos del programa que publicó su convocatoria: son `base`, no enriquecimiento.
    op.add_column(
        "curriculum_nodes", sa.Column("curriculum_version_id", sa.String(length=36), nullable=True)
    )
    op.add_column(
        "curriculum_nodes",
        sa.Column(
            "origin_kind", sa.String(length=16), nullable=False, server_default=sa.text("'base'")
        ),
    )
    op.add_column(
        "curriculum_nodes",
        sa.Column("origin_convocation_version_id", sa.String(length=36), nullable=True),
    )

    # ----------------------------------------------------- C. rellenar, sin inventar (§6.2 C)
    conexion = op.get_bind()
    convocatorias = conexion.execute(
        sa.text(
            "SELECT c.id, c.code, c.title, c.source_reference "
            "FROM convocation_versions c "
            "WHERE EXISTS (SELECT 1 FROM curriculum_nodes n "
            "              WHERE n.convocation_version_id = c.id) "
            "ORDER BY c.code"
        )
    ).all()

    for convocatoria_id, code, title, source_reference in convocatorias:
        curriculum_id = _nuevo_id()
        version_id = _nuevo_id()
        conexion.execute(
            sa.text(
                "INSERT INTO curricula (id, code, kind, name, description, group_code, family, "
                "created_at, updated_at) VALUES (:id, :code, 'published', :name, NULL, NULL, "
                "NULL, :ahora, :ahora)"
            ),
            {
                "id": curriculum_id,
                "code": f"{code}-programa",
                "name": title,
                "ahora": ahora,
            },
        )
        conexion.execute(
            sa.text(
                "INSERT INTO curriculum_versions (id, curriculum_id, version_no, code, title, "
                "status, source_reference, supersedes_id, created_at, updated_at) VALUES "
                "(:id, :curriculum, 1, :code, :title, 'active', :fuente, NULL, :ahora, :ahora)"
            ),
            {
                "id": version_id,
                "curriculum": curriculum_id,
                "code": f"{code}-programa-v1",
                "title": title,
                "fuente": source_reference,
                "ahora": ahora,
            },
        )
        # Los `id` de los nodos no se tocan: son el eje de `curriculum_mappings` y `learning_errors`
        # (§4.2). Solo cambia la clave por la que cuelgan.
        conexion.execute(
            sa.text(
                "UPDATE curriculum_nodes SET curriculum_version_id = :version "
                "WHERE convocation_version_id = :convocatoria"
            ),
            {"version": version_id, "convocatoria": convocatoria_id},
        )
        # La referencia `official` es la evidencia de lo que publicó la convocatoria y, a la vez, el
        # camino de vuelta del `downgrade`.
        conexion.execute(
            sa.text(
                "INSERT INTO convocation_curriculum_refs (id, convocation_version_id, "
                "curriculum_version_id, role, source_reference, created_at, updated_at) VALUES "
                "(:id, :convocatoria, :version, 'official', :fuente, :ahora, :ahora)"
            ),
            {
                "id": _nuevo_id(),
                "convocatoria": convocatoria_id,
                "version": version_id,
                "fuente": source_reference,
                "ahora": ahora,
            },
        )

    # El temario común nace vacío y en borrador: el contenido no lo pone una migración (§6.7).
    conexion.execute(
        sa.text(
            "INSERT INTO curricula (id, code, kind, name, description, group_code, family, "
            "created_at, updated_at) VALUES (:id, :code, 'common', :name, NULL, 'C1', "
            "'informatica', :ahora, :ahora)"
        ),
        {
            "id": _nuevo_id(),
            "code": _TEMARIO_COMUN,
            "name": _TEMARIO_COMUN_NOMBRE,
            "ahora": ahora,
        },
    )
    conexion.execute(
        sa.text(
            "INSERT INTO curriculum_versions (id, curriculum_id, version_no, code, title, status, "
            "source_reference, supersedes_id, created_at, updated_at) "
            "SELECT :id, id, 1, :code, :nombre, 'draft', :fuente, NULL, :ahora, :ahora "
            "FROM curricula WHERE code = :temario"
        ),
        {
            "id": _nuevo_id(),
            "code": _TEMARIO_COMUN_VERSION,
            "nombre": _TEMARIO_COMUN_NOMBRE,
            "fuente": _TEMARIO_COMUN_FUENTE,
            "temario": _TEMARIO_COMUN,
            "ahora": ahora,
        },
    )

    # Comprobación dura: sin versión no se puede cerrar el NOT NULL, y rellenar a ciegas sería
    # inventar de qué programa era el nodo.
    sin_version = conexion.execute(
        sa.text("SELECT count(*) FROM curriculum_nodes WHERE curriculum_version_id IS NULL")
    ).scalar_one()
    if sin_version:
        raise RuntimeError(
            f"0021: {sin_version} nodos de programa no se han podido asignar a una versión de "
            "temario; la migración no continúa"
        )

    # ------------------------------- D. cerrar: recrear la tabla (SQLite no altera restricciones)
    with op.batch_alter_table(
        "curriculum_nodes",
        recreate="always",
        naming_convention=_CONVENCION_NOMBRES,
    ) as batch:
        batch.alter_column(
            "curriculum_version_id", existing_type=sa.String(length=36), nullable=False
        )
        batch.create_foreign_key(
            _FK_VERSION,
            "curriculum_versions",
            ["curriculum_version_id"],
            ["id"],
            ondelete="CASCADE",
        )
        batch.create_foreign_key(
            _FK_ORIGEN,
            "convocation_versions",
            ["origin_convocation_version_id"],
            ["id"],
            ondelete="SET NULL",
        )
        batch.create_check_constraint(
            _CK_ORIGEN, f"origin_kind IN ({_lista(('base', 'enrichment'))})"
        )
        batch.create_unique_constraint(_UQ_NODO, ["curriculum_version_id", "path"])
        # Primero se retiran el índice y la unicidad de la columna vieja: si se quitara la columna
        # antes, se quedarían apuntando a algo que ya no existe.
        batch.drop_index("ix_curriculum_convocation")
        batch.drop_constraint("uq_curriculum_path", type_="unique")
        batch.drop_column("convocation_version_id")

    op.create_index(_IX_VERSION, "curriculum_nodes", ["curriculum_version_id"])

    _comprobar_integridad_referencial("tras la subida")


def downgrade() -> None:
    # ------------------------------------------- 1. reabrir curriculum_nodes y devolver su dueño
    with op.batch_alter_table(
        "curriculum_nodes",
        recreate="always",
        naming_convention=_CONVENCION_NOMBRES,
    ) as batch:
        batch.add_column(sa.Column("convocation_version_id", sa.String(length=36), nullable=True))

    # La convocatoria de cada nodo se recupera de la referencia `official`: es el mismo dato que la
    # migración escribió al subir, no una suposición nueva.
    conexion = op.get_bind()
    conexion.execute(
        sa.text(
            "UPDATE curriculum_nodes SET convocation_version_id = ("
            "SELECT r.convocation_version_id FROM convocation_curriculum_refs r "
            "WHERE r.curriculum_version_id = curriculum_nodes.curriculum_version_id "
            "AND r.role = 'official' LIMIT 1)"
        )
    )
    sin_convocatoria = conexion.execute(
        sa.text("SELECT count(*) FROM curriculum_nodes WHERE convocation_version_id IS NULL")
    ).scalar_one()
    if sin_convocatoria:
        raise RuntimeError(
            f"0021 (downgrade): {sin_convocatoria} nodos no tienen programa publicado al que "
            "volver; no se les inventa una convocatoria y la bajada no continúa"
        )

    # ---------------------- 2. recuperar la forma de 0020 y retirar lo que esta migración añadió
    with op.batch_alter_table(
        "curriculum_nodes",
        recreate="always",
        naming_convention=_CONVENCION_NOMBRES,
    ) as batch:
        batch.alter_column(
            "convocation_version_id", existing_type=sa.String(length=36), nullable=False
        )
        batch.create_foreign_key(
            "fk_curriculum_node_convocation",
            "convocation_versions",
            ["convocation_version_id"],
            ["id"],
            ondelete="CASCADE",
        )
        batch.create_unique_constraint("uq_curriculum_path", ["convocation_version_id", "path"])
        # Retirar por nombre todo lo que cuelga de las columnas nuevas, **antes** de quitarlas.
        batch.drop_constraint(_FK_VERSION, type_="foreignkey")
        batch.drop_constraint(_FK_ORIGEN, type_="foreignkey")
        batch.drop_constraint(_UQ_NODO, type_="unique")
        batch.drop_constraint(_CK_ORIGEN, type_="check")
        batch.drop_index(_IX_VERSION)
        batch.drop_column("curriculum_version_id")
        batch.drop_column("origin_kind")
        batch.drop_column("origin_convocation_version_id")

    op.create_index(
        "ix_curriculum_convocation", "curriculum_nodes", ["convocation_version_id"], unique=False
    )

    # --------------------------- 3. borrar las tablas nuevas en orden inverso a su creación (§6.5)
    op.drop_index("ix_curriculum_equivalence_target", table_name="curriculum_equivalences")
    op.drop_index("ix_curriculum_equivalence_source", table_name="curriculum_equivalences")
    op.drop_table("curriculum_equivalences")
    op.drop_index(
        "ix_conv_curriculum_adjustment_node",
        table_name="convocation_curriculum_adjustments",
    )
    op.drop_index(
        "ix_conv_curriculum_adjustment_ref", table_name="convocation_curriculum_adjustments"
    )
    op.drop_table("convocation_curriculum_adjustments")
    op.drop_index("uq_convocation_official_ref", table_name="convocation_curriculum_refs")
    op.drop_index("uq_convocation_primary_ref", table_name="convocation_curriculum_refs")
    op.drop_index("ix_conv_curriculum_ref_convocation", table_name="convocation_curriculum_refs")
    op.drop_table("convocation_curriculum_refs")
    op.drop_index("uq_curriculum_version_single_active", table_name="curriculum_versions")
    op.drop_table("curriculum_versions")
    op.drop_table("curricula")

    _comprobar_integridad_referencial("tras la bajada")
