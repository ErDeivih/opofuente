"""Migración 0021: el temario común y las convocatorias que lo referencian (S13).

Comprueba lo que no se ve leyendo el fichero de la migración:

1. el esquema queda creado al llegar a la cabeza, con la revisión marcada;
2. la **subida conserva todos los nodos** y su `id`: cada convocatoria que publicaba programa
   recibe su versión `published` y su referencia `official`, y ningún nodo queda sin versión
   (`ESPECIFICACION.md` §6.8). Es lo que mantiene vivos `curriculum_mappings` y `learning_errors`;
3. el temario común nace **vacío y en `draft`**: el contenido lo pone la siembra, no la migración;
4. la **bajada se ejecuta de verdad** y devuelve `convocation_version_id` con el mismo valor que
   tenía, recrea `uq_curriculum_path` e `ix_curriculum_convocation` y retira las cinco tablas;
5. la bajada **falla** en vez de inventar una convocatoria si un nodo no tiene programa publicado
   al que volver;
6. las restricciones nuevas rechazan lo que el modelo prohíbe (dos temarios `primary` en una
   convocatoria, dos versiones activas de un temario, un ajuste `weighted` sin peso, una
   equivalencia aceptada sin fecha de decisión).

La cadena completa se prueba desde cero y desde una base con datos, que es lo que hay de verdad
(`ESPECIFICACION.md` §6.2 y §6.5).
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
import sqlalchemy as sa
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from alembic import command
from opofuente.config import Settings
from opofuente.infrastructure.db import build_engine
from opofuente.infrastructure.migrations import alembic_config, run_migrations, script_head

AHORA = datetime(2026, 11, 4, 12, 0, tzinfo=UTC)
REVISION_ANTERIOR = "0020_changes_and_derivatives"

TABLAS_DEL_TEMARIO = (
    "curricula",
    "curriculum_versions",
    "convocation_curriculum_refs",
    "convocation_curriculum_adjustments",
    "curriculum_equivalences",
)


def _settings(tmp_path: Path) -> Settings:
    return Settings(data_dir=tmp_path / "datos", _env_file=None)


def _bajar_a(settings: Settings, revision: str) -> None:
    """Baja de revisión de verdad: `run_migrations` solo sube."""
    command.downgrade(alembic_config(settings), revision)


def _tablas(settings: Settings) -> set[str]:
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.connect() as conexion:
            return {
                str(fila[0])
                for fila in conexion.execute(
                    text("SELECT name FROM sqlite_master WHERE type = 'table'")
                )
            }
    finally:
        engine.dispose()


def _revision(settings: Settings) -> str:
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.connect() as conexion:
            return str(conexion.execute(text("SELECT version_num FROM alembic_version")).scalar())
    finally:
        engine.dispose()


def _columnas(settings: Settings, tabla: str) -> set[str]:
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.connect() as conexion:
            filas = conexion.execute(text(f"PRAGMA table_info({tabla})")).all()
        return {str(fila[1]) for fila in filas}
    finally:
        engine.dispose()


def _foreign_key_check(settings: Settings) -> list[tuple[object, ...]]:
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.connect() as conexion:
            return [tuple(fila) for fila in conexion.execute(text("PRAGMA foreign_key_check"))]
    finally:
        engine.dispose()


def _sembrar_mundo_antiguo(settings: Settings, revision: str = REVISION_ANTERIOR) -> None:
    """Dos convocatorias con programa (una con dos nodos y otra con uno) y una sin él.

    Se siembra **antes** de subir a 0021, con el esquema de la revisión que se pida: por defecto
    0020, y `0004_issue_relative_path` para reproducir la base viva de `ESPECIFICACION.md` §4.4
    (el esquema de convocatorias y programa no cambió entre ambas). Así la prueba mide la subida
    sobre datos reales y no sobre una base vacía.
    """
    run_migrations(settings, revision=revision)
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.begin() as conexion:
            conexion.execute(
                text(
                    "INSERT INTO oppositions (id, code, name, active, created_at, updated_at) "
                    "VALUES ('op-1', 'tai-age', 'TAI', 1, :ahora, :ahora)"
                ),
                {"ahora": AHORA},
            )
            for indice, code in enumerate(("tai-age-2025", "tai-age-2026"), start=1):
                conexion.execute(
                    text(
                        "INSERT INTO convocation_versions (id, opposition_id, code, title, "
                        "official_url, published_at, exam_date, status, source_reference, "
                        "created_at, updated_at) VALUES (:id, 'op-1', :code, :title, "
                        "'https://www.boe.es/', '2025-12-22', NULL, :estado, :fuente, :ahora, "
                        ":ahora)"
                    ),
                    {
                        "id": f"conv-{indice}",
                        "code": code,
                        "title": f"Convocatoria {indice}",
                        "estado": "active" if indice == 1 else "draft",
                        "fuente": f"ANEXO {indice}",
                        "ahora": AHORA,
                    },
                )
            # Una convocatoria sin programa: existe, pero no publica temario (§6.4).
            conexion.execute(
                text(
                    "INSERT INTO convocation_versions (id, opposition_id, code, title, "
                    "official_url, published_at, exam_date, status, source_reference, "
                    "created_at, updated_at) VALUES ('conv-sin-programa', 'op-1', "
                    "'tai-age-sin-programa', 'Sin programa', 'https://www.boe.es/', "
                    "'2025-12-22', NULL, 'draft', NULL, :ahora, :ahora)"
                ),
                {"ahora": AHORA},
            )
            nodos = (
                ("nodo-1", "conv-1", None, "block", "I", "Bloque I", 1, "I", 0),
                ("nodo-2", "conv-1", "nodo-1", "topic", "1", "Tema 1", 1, "I.1", 1),
                ("nodo-3", "conv-2", None, "topic", "1", "Tema único", 1, "1", 0),
            )
            for nodo_id, convocatoria, padre, tipo, codigo, titulo, posicion, ruta, hondo in nodos:
                conexion.execute(
                    text(
                        "INSERT INTO curriculum_nodes (id, convocation_version_id, parent_id, "
                        "node_type, official_code, title, position, path, depth) VALUES "
                        "(:id, :conv, :padre, :tipo, :codigo, :titulo, :posicion, :ruta, :hondo)"
                    ),
                    {
                        "id": nodo_id,
                        "conv": convocatoria,
                        "padre": padre,
                        "tipo": tipo,
                        "codigo": codigo,
                        "titulo": titulo,
                        "posicion": posicion,
                        "ruta": ruta,
                        "hondo": hondo,
                    },
                )
    finally:
        engine.dispose()


def _nodos(settings: Settings) -> list[tuple[object, ...]]:
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.connect() as conexion:
            return [
                tuple(fila)
                for fila in conexion.execute(
                    text(
                        "SELECT id, curriculum_version_id, origin_kind, path "
                        "FROM curriculum_nodes ORDER BY id"
                    )
                )
            ]
    finally:
        engine.dispose()


def test_el_esquema_del_temario_queda_creado(tmp_path: Path) -> None:
    """Al llegar a la cabeza están las cinco tablas y la columna nueva; la vieja ya no está."""
    settings = _settings(tmp_path)
    run_migrations(settings, revision="head")

    assert _revision(settings) == script_head(settings)
    tablas = _tablas(settings)
    for tabla in TABLAS_DEL_TEMARIO:
        assert tabla in tablas, f"falta la tabla {tabla}"

    columnas = _columnas(settings, "curriculum_nodes")
    assert "curriculum_version_id" in columnas
    assert "origin_kind" in columnas
    assert "origin_convocation_version_id" in columnas
    assert "convocation_version_id" not in columnas


def test_la_subida_conserva_los_nodos_y_les_da_una_version(tmp_path: Path) -> None:
    """Ningún nodo se pierde, ninguno cambia de id y cada uno queda en su programa publicado."""
    settings = _settings(tmp_path)
    _sembrar_mundo_antiguo(settings)

    run_migrations(settings, revision="head")

    nodos = _nodos(settings)
    assert [fila[0] for fila in nodos] == ["nodo-1", "nodo-2", "nodo-3"]
    assert all(fila[1] is not None for fila in nodos), "hay nodos sin versión de temario"
    assert {fila[2] for fila in nodos} == {"base"}, "los nodos heredados no son enriquecimiento"

    engine = build_engine(settings.data_paths.database)
    try:
        with engine.connect() as conexion:
            programas = conexion.execute(
                text(
                    "SELECT c.code, c.kind, v.status, r.role, r.convocation_version_id "
                    "FROM curricula c "
                    "JOIN curriculum_versions v ON v.curriculum_id = c.id "
                    "JOIN convocation_curriculum_refs r "
                    "  ON r.curriculum_version_id = v.id "
                    "WHERE c.kind = 'published' ORDER BY c.code"
                )
            ).all()
            sin_programa = conexion.execute(
                text(
                    "SELECT count(*) FROM convocation_curriculum_refs "
                    "WHERE convocation_version_id = 'conv-sin-programa'"
                )
            ).scalar_one()
            nodos_por_version = conexion.execute(
                text(
                    "SELECT curriculum_version_id, count(*) FROM curriculum_nodes "
                    "GROUP BY curriculum_version_id"
                )
            ).all()
    finally:
        engine.dispose()

    # Una convocatoria con nodos tiene su programa publicado y su referencia official; la que no
    # publica temario no recibe ninguna de las dos cosas inventadas (§6.4).
    assert [fila[0] for fila in programas] == ["tai-age-2025-programa", "tai-age-2026-programa"]
    assert {fila[1] for fila in programas} == {"published"}
    assert {fila[2] for fila in programas} == {"active"}
    assert {fila[3] for fila in programas} == {"official"}
    assert {fila[4] for fila in programas} == {"conv-1", "conv-2"}
    assert sin_programa == 0, "no se inventa programa para una convocatoria que no lo publica"
    assert sorted(int(fila[1]) for fila in nodos_por_version) == [1, 2]
    assert _foreign_key_check(settings) == []


def test_la_subida_funciona_desde_la_revision_de_la_base_viva(tmp_path: Path) -> None:
    """`ESPECIFICACION.md` §6.8: la cadena completa se prueba desde la revisión de la base viva.

    La base de trabajo de la especificación está en `0004`; las puertas solo prueban desde vacío.
    Esta prueba sube desde ahí con datos con la forma del mundo antiguo y comprueba que no se pierde
    nada.
    """
    settings = _settings(tmp_path)
    _sembrar_mundo_antiguo(settings, revision="0004_issue_relative_path")

    run_migrations(settings, revision="head")

    assert _revision(settings) == script_head(settings)
    nodos = _nodos(settings)
    assert [str(fila[0]) for fila in nodos] == ["nodo-1", "nodo-2", "nodo-3"]
    assert all(fila[1] is not None for fila in nodos), "algún nodo se quedó sin versión de temario"
    assert _foreign_key_check(settings) == []


def test_el_temario_comun_nace_vacio_y_en_borrador(tmp_path: Path) -> None:
    """El contenido no lo pone la migración: lo pone el fixture y lo publica la siembra (§6.7)."""
    settings = _settings(tmp_path)
    _sembrar_mundo_antiguo(settings)

    run_migrations(settings, revision="head")

    engine = build_engine(settings.data_paths.database)
    try:
        with engine.connect() as conexion:
            comun = conexion.execute(
                text(
                    "SELECT c.code, c.kind, c.group_code, c.family, v.code, v.status, "
                    "v.source_reference FROM curricula c "
                    "JOIN curriculum_versions v ON v.curriculum_id = c.id "
                    "WHERE c.kind = 'common'"
                )
            ).one()
            nodos = conexion.execute(
                text(
                    "SELECT count(*) FROM curriculum_nodes n "
                    "JOIN curriculum_versions v ON v.id = n.curriculum_version_id "
                    "JOIN curricula c ON c.id = v.curriculum_id WHERE c.kind = 'common'"
                )
            ).scalar_one()
    finally:
        engine.dispose()

    assert comun[0] == "informatica-c1"
    assert comun[1] == "common"
    assert comun[2] == "C1"
    assert comun[3] == "informatica"
    assert comun[4] == "informatica-c1-v1"
    assert comun[5] == "draft", "el temario común no se publica en la migración"
    assert "temario-c1.md" in str(comun[6])
    assert nodos == 0, "la migración no inventa los 40 temas"


def test_la_bajada_devuelve_cada_nodo_a_su_convocatoria(tmp_path: Path) -> None:
    """`downgrade` rellena `convocation_version_id` desde la referencia official y deja 0020."""
    settings = _settings(tmp_path)
    _sembrar_mundo_antiguo(settings)
    run_migrations(settings, revision="head")

    _bajar_a(settings, REVISION_ANTERIOR)

    assert _revision(settings) == REVISION_ANTERIOR
    tablas = _tablas(settings)
    for tabla in TABLAS_DEL_TEMARIO:
        assert tabla not in tablas, f"{tabla} sigue ahí tras bajar"

    columnas = _columnas(settings, "curriculum_nodes")
    assert columnas == {
        "id",
        "convocation_version_id",
        "parent_id",
        "node_type",
        "official_code",
        "title",
        "description",
        "position",
        "path",
        "depth",
    }, "la bajada deja las mismas columnas que tenía 0020"
    assert "curriculum_version_id" not in columnas
    assert "origin_kind" not in columnas

    engine = build_engine(settings.data_paths.database)
    try:
        with engine.connect() as conexion:
            nodos = {
                str(fila[0]): str(fila[1])
                for fila in conexion.execute(
                    text("SELECT id, convocation_version_id FROM curriculum_nodes")
                )
            }
        inspector = sa.inspect(engine)
        unicos = {fila["name"] for fila in inspector.get_unique_constraints("curriculum_nodes")}
        indices = {fila["name"] for fila in inspector.get_indexes("curriculum_nodes")}
        acciones = {
            str(fila["constrained_columns"][0]): str(fila["options"].get("ondelete") or "")
            for fila in inspector.get_foreign_keys("curriculum_nodes")
        }
    finally:
        engine.dispose()

    # El `id` no cambió y cada nodo volvió a la convocatoria de la que salió.
    assert nodos == {"nodo-1": "conv-1", "nodo-2": "conv-1", "nodo-3": "conv-2"}
    assert "uq_curriculum_path" in unicos
    assert "ix_curriculum_convocation" in indices
    assert "uq_curriculum_node_path" not in unicos
    assert "ix_curriculum_node_version" not in indices
    # Las acciones de borrado son las de 0020: el programa cuelga de la convocatoria y el árbol de
    # su padre; si se perdieran, borrar una convocatoria o un bloque dejaría nodos huérfanos.
    assert acciones == {"convocation_version_id": "CASCADE", "parent_id": "CASCADE"}
    assert _foreign_key_check(settings) == []


def test_un_mapeo_de_material_sobrevive_a_la_subida_y_a_la_bajada(tmp_path: Path) -> None:
    """Lo que de verdad protege el cambio de dueño: el material no pierde su tema.

    `curriculum_mappings` apunta a `curriculum_nodes.id` con `ON DELETE RESTRICT` (ADR-007). La
    subida recrea la tabla y la bajada la vuelve a recrear; si en cualquiera de las dos se perdiera
    un nodo, el mapeo quedaría huérfano. La prueba siembra el mapeo **antes** de subir y comprueba
    que sigue apuntando al mismo nodo después de subir, y otra vez después de bajar.
    """
    settings = _settings(tmp_path)
    _sembrar_mundo_antiguo(settings)
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.begin() as conexion:
            conexion.execute(
                text(
                    "INSERT INTO curriculum_mappings (id, curriculum_node_id, subject_type, "
                    "subject_id, coverage_type, depth, confidence, status, created_at, "
                    "approved_at) VALUES ('map-1', 'nodo-2', 'artifact', 'art-1', 'partial', 0, "
                    "0.8, 'accepted', :ahora, :ahora)"
                ),
                {"ahora": AHORA},
            )
    finally:
        engine.dispose()

    run_migrations(settings, revision="head")

    engine = build_engine(settings.data_paths.database)
    try:
        with engine.connect() as conexion:
            mapeo = conexion.execute(
                text("SELECT curriculum_node_id FROM curriculum_mappings WHERE id = 'map-1'")
            ).one()
            version = conexion.execute(
                text("SELECT curriculum_version_id FROM curriculum_nodes WHERE id = 'nodo-2'")
            ).scalar_one()
            versiones = conexion.execute(
                text(
                    "SELECT count(*) FROM curricula c JOIN curriculum_versions v "
                    "ON v.curriculum_id = c.id WHERE c.code = 'tai-age-2025-programa' "
                    "AND v.id = :version"
                ),
                {"version": version},
            ).scalar_one()
    finally:
        engine.dispose()

    assert str(mapeo[0]) == "nodo-2", "el material no ha perdido su tema al cambiar de dueño"
    assert versiones == 1, "el nodo quedó en la versión publicada de su convocatoria"
    assert _foreign_key_check(settings) == []

    _bajar_a(settings, REVISION_ANTERIOR)

    engine = build_engine(settings.data_paths.database)
    try:
        with engine.connect() as conexion:
            mapeo = conexion.execute(
                text("SELECT curriculum_node_id FROM curriculum_mappings WHERE id = 'map-1'")
            ).one()
            convocatoria = conexion.execute(
                text("SELECT convocation_version_id FROM curriculum_nodes WHERE id = 'nodo-2'")
            ).scalar_one()
    finally:
        engine.dispose()

    assert str(mapeo[0]) == "nodo-2", "la bajada tampoco puede dejar huérfano el material"
    assert str(convocatoria) == "conv-1"
    assert _foreign_key_check(settings) == []


def test_la_bajada_falla_si_un_nodo_no_tiene_programa_publicado(tmp_path: Path) -> None:
    """No se inventa una convocatoria: si un nodo es del temario común, la bajada se detiene."""
    settings = _settings(tmp_path)
    run_migrations(settings, revision="head")
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.begin() as conexion:
            version_comun = conexion.execute(
                text("SELECT id FROM curriculum_versions WHERE code = 'informatica-c1-v1'")
            ).scalar_one()
            conexion.execute(
                text(
                    "INSERT INTO curriculum_nodes (id, curriculum_version_id, parent_id, "
                    "node_type, official_code, title, position, path, depth, origin_kind) "
                    "VALUES ('nodo-comun', :version, NULL, 'topic', '1', 'Tema 1', 1, '1', 0, "
                    "'base')"
                ),
                {"version": version_comun},
            )
    finally:
        engine.dispose()

    with pytest.raises(RuntimeError, match="no tienen programa publicado"):
        _bajar_a(settings, REVISION_ANTERIOR)


def test_una_convocatoria_no_puede_tener_dos_temarios_primarios(tmp_path: Path) -> None:
    """I3 en la base: un solo `primary` por convocatoria (índice único parcial)."""
    settings = _settings(tmp_path)
    _sembrar_mundo_antiguo(settings)
    run_migrations(settings, revision="head")

    engine = build_engine(settings.data_paths.database)
    try:
        with engine.begin() as conexion:
            versiones = conexion.execute(
                text("SELECT id FROM curriculum_versions WHERE status = 'active'")
            ).scalars()
            versiones = list(versiones)
            conexion.execute(
                text(
                    "INSERT INTO convocation_curriculum_refs (id, convocation_version_id, "
                    "curriculum_version_id, role, source_reference, created_at, updated_at) "
                    "VALUES ('ref-1', 'conv-sin-programa', :version, 'primary', 'cita', :ahora, "
                    ":ahora)"
                ),
                {"version": versiones[0], "ahora": AHORA},
            )
        with pytest.raises(IntegrityError), engine.begin() as conexion:
            conexion.execute(
                text(
                    "INSERT INTO convocation_curriculum_refs (id, convocation_version_id, "
                    "curriculum_version_id, role, source_reference, created_at, updated_at) "
                    "VALUES ('ref-2', 'conv-sin-programa', :version, 'primary', 'cita', :ahora, "
                    ":ahora)"
                ),
                {"version": versiones[1], "ahora": AHORA},
            )
    finally:
        engine.dispose()


def test_un_temario_no_puede_tener_dos_versiones_activas(tmp_path: Path) -> None:
    """I1 en la base: el índice único parcial impide dos `active` del mismo temario."""
    settings = _settings(tmp_path)
    run_migrations(settings, revision="head")

    engine = build_engine(settings.data_paths.database)
    try:
        with engine.begin() as conexion:
            comun = conexion.execute(
                text("SELECT id FROM curricula WHERE code = 'informatica-c1'")
            ).scalar_one()
            conexion.execute(
                text(
                    "INSERT INTO curriculum_versions (id, curriculum_id, version_no, code, title, "
                    "status, created_at, updated_at) VALUES ('v2', :comun, 2, "
                    "'informatica-c1-v2', 'v2', 'active', :ahora, :ahora)"
                ),
                {"comun": comun, "ahora": AHORA},
            )
        with pytest.raises(IntegrityError), engine.begin() as conexion:
            conexion.execute(
                text(
                    "INSERT INTO curriculum_versions (id, curriculum_id, version_no, code, title, "
                    "status, created_at, updated_at) VALUES ('v3', :comun, 3, "
                    "'informatica-c1-v3', 'v3', 'active', :ahora, :ahora)"
                ),
                {"comun": comun, "ahora": AHORA},
            )
    finally:
        engine.dispose()


def test_un_ajuste_no_se_guarda_sin_su_cita_ni_sin_lo_que_declara(tmp_path: Path) -> None:
    """I8 y las coherencias de columna: `weighted` con peso, y todo ajuste con cita literal."""
    settings = _settings(tmp_path)
    _sembrar_mundo_antiguo(settings)
    run_migrations(settings, revision="head")

    engine = build_engine(settings.data_paths.database)
    try:
        with engine.begin() as conexion:
            version = conexion.execute(
                text("SELECT curriculum_version_id FROM curriculum_nodes WHERE id = 'nodo-1'")
            ).scalar_one()
            curriculum = conexion.execute(
                text("SELECT curriculum_id FROM curriculum_versions WHERE id = :version"),
                {"version": version},
            ).scalar_one()
            # Una segunda edición en borrador: la convocatoria ya tiene su ref `official` a la v1,
            # así que el `primary` usa otra versión (la unicidad lo exige).
            conexion.execute(
                text(
                    "INSERT INTO curriculum_versions (id, curriculum_id, version_no, code, title, "
                    "status, created_at, updated_at) VALUES ('v2', :curriculum, 2, "
                    "'tai-age-2025-programa-v2', 'v2', 'draft', :ahora, :ahora)"
                ),
                {"curriculum": curriculum, "ahora": AHORA},
            )
            conexion.execute(
                text(
                    "INSERT INTO convocation_curriculum_refs (id, convocation_version_id, "
                    "curriculum_version_id, role, source_reference, created_at, updated_at) "
                    "VALUES ('ref-1', 'conv-1', 'v2', 'primary', 'ANEXO V', :ahora, :ahora)"
                ),
                {"ahora": AHORA},
            )
    finally:
        engine.dispose()

    with pytest.raises(IntegrityError):
        _ejecutar_ajuste(settings, ajuste_id="aj-1", kind="weighted", weight=None, evidence="cita")
    with pytest.raises(IntegrityError):
        _ejecutar_ajuste(settings, ajuste_id="aj-2", kind="omitted", weight=None, evidence="   ")

    _ejecutar_ajuste(
        settings,
        ajuste_id="aj-3",
        kind="weighted",
        weight=0.4,
        evidence="el bloque III pondera el 40 %",
    )

    engine = build_engine(settings.data_paths.database)
    try:
        with engine.connect() as conexion:
            total = conexion.execute(
                text("SELECT count(*) FROM convocation_curriculum_adjustments")
            ).scalar_one()
    finally:
        engine.dispose()
    assert total == 1, "solo el ajuste que trae su cita y su peso se ha guardado"


def _ejecutar_ajuste(
    settings: Settings, *, ajuste_id: str, kind: str, weight: float | None, evidence: str
) -> None:
    """Inserta un ajuste sobre el nodo `nodo-1`; la prueba decide si eso debe caber o no."""
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.begin() as conexion:
            conexion.execute(
                text(
                    "INSERT INTO convocation_curriculum_adjustments (id, ref_id, "
                    "curriculum_node_id, kind, weight, evidence_quote, created_at, updated_at) "
                    "VALUES (:id, 'ref-1', 'nodo-1', :kind, :weight, :evidence, :ahora, :ahora)"
                ),
                {
                    "id": ajuste_id,
                    "kind": kind,
                    "weight": weight,
                    "evidence": evidence,
                    "ahora": AHORA,
                },
            )
    finally:
        engine.dispose()


def test_una_equivalencia_aceptada_exige_fecha_de_decision(tmp_path: Path) -> None:
    """`accepted` sin `decided_at` es una decisión que nadie tomó: la base la rechaza."""
    settings = _settings(tmp_path)
    _sembrar_mundo_antiguo(settings)
    run_migrations(settings, revision="head")

    engine = build_engine(settings.data_paths.database)
    try:
        with engine.begin() as conexion:
            comun = conexion.execute(
                text("SELECT id FROM curriculum_versions WHERE code = 'informatica-c1-v1'")
            ).scalar_one()
            conexion.execute(
                text(
                    "INSERT INTO curriculum_nodes (id, curriculum_version_id, parent_id, "
                    "node_type, official_code, title, position, path, depth, origin_kind) "
                    "VALUES ('nodo-comun', :version, NULL, 'topic', '1', 'Tema 1', 1, '1', 0, "
                    "'base')"
                ),
                {"version": comun},
            )
    finally:
        engine.dispose()

    engine = build_engine(settings.data_paths.database)
    try:
        with pytest.raises(IntegrityError), engine.begin() as conexion:
            conexion.execute(
                text(
                    "INSERT INTO curriculum_equivalences (id, source_node_id, target_node_id, "
                    "relation, confidence, status, evidence_note, created_at, decided_at) VALUES "
                    "('eq-1', 'nodo-1', 'nodo-comun', 'equivalent', 0.9, 'accepted', "
                    "'mismo título', :ahora, NULL)"
                ),
                {"ahora": AHORA},
            )
    finally:
        engine.dispose()


def test_borrar_la_convocatoria_que_motivo_un_tema_no_borra_el_tema(tmp_path: Path) -> None:
    """I6: un tema que entró al temario común por una convocatoria sobrevive a borrarla.

    La procedencia se queda sin convocatoria (`ON DELETE SET NULL`), no el tema: el temario común es
    uno y lo estudian todas, y borrar sus temas al borrar la convocatoria que los motivó sería
    perder contenido (y una migración destructiva, que es Nivel 3).
    """
    settings = _settings(tmp_path)
    _sembrar_mundo_antiguo(settings)
    run_migrations(settings, revision="head")

    engine = build_engine(settings.data_paths.database)
    try:
        with engine.begin() as conexion:
            version_comun = conexion.execute(
                text("SELECT id FROM curriculum_versions WHERE code = 'informatica-c1-v1'")
            ).scalar_one()
            conexion.execute(
                text(
                    "INSERT INTO curriculum_nodes (id, curriculum_version_id, parent_id, "
                    "node_type, official_code, title, position, path, depth, origin_kind, "
                    "origin_convocation_version_id) VALUES ('nodo-comun', :version, NULL, "
                    "'topic', '1', 'Tema 1', 1, '1', 0, 'enrichment', 'conv-1')"
                ),
                {"version": version_comun},
            )
            conexion.execute(text("DELETE FROM convocation_versions WHERE id = 'conv-1'"))
            fila = conexion.execute(
                text(
                    "SELECT origin_kind, origin_convocation_version_id FROM curriculum_nodes "
                    "WHERE id = 'nodo-comun'"
                )
            ).one()
    finally:
        engine.dispose()

    assert str(fila[0]) == "enrichment", "el tema sigue en el temario común"
    assert fila[1] is None, "solo se pierde la procedencia, no el tema"
    assert _foreign_key_check(settings) == []


def test_borrar_una_version_de_temario_se_lleva_sus_nodos(tmp_path: Path) -> None:
    """La FK `ON DELETE CASCADE` del nodo a su versión, de verdad (es la que hace que la versión
    mande sobre el árbol; los nodos con material siguen protegidos por `curriculum_mappings`)."""
    settings = _settings(tmp_path)
    _sembrar_mundo_antiguo(settings)
    run_migrations(settings, revision="head")

    engine = build_engine(settings.data_paths.database)
    try:
        with engine.begin() as conexion:
            version = conexion.execute(
                text("SELECT curriculum_version_id FROM curriculum_nodes WHERE id = 'nodo-3'")
            ).scalar_one()
            # La referencia `official` protege la versión con RESTRICT: para borrar el temario hay
            # que retirar antes la referencia (es el orden que seguiría la aplicación).
            conexion.execute(
                text(
                    "DELETE FROM convocation_curriculum_refs WHERE curriculum_version_id = :version"
                ),
                {"version": version},
            )
            conexion.execute(
                text("DELETE FROM curriculum_versions WHERE id = :version"), {"version": version}
            )
            vivos = conexion.execute(
                text("SELECT count(*) FROM curriculum_nodes WHERE id = 'nodo-3'")
            ).scalar_one()
    finally:
        engine.dispose()
    assert vivos == 0, "el nodo colgaba de la versión y se va con ella"


def test_el_esquema_0020_tiene_una_sola_columna_de_dueno(tmp_path: Path) -> None:
    """Control explícito: en 0020 el dueño es la convocatoria y en la cabeza es la versión.

    Sin esta comprobación, una migración que dejara las dos columnas pasaría las pruebas de subida
    y volvería a permitir la copia del temario por convocatoria que la decisión prohíbe (I2).
    """
    settings = _settings(tmp_path)
    run_migrations(settings, revision=REVISION_ANTERIOR)
    assert "convocation_version_id" in _columnas(settings, "curriculum_nodes")

    run_migrations(settings, revision="head")
    columnas = _columnas(settings, "curriculum_nodes")
    assert "convocation_version_id" not in columnas
    assert "curriculum_version_id" in columnas


def test_el_esquema_admite_una_version_publicada_por_cada_convocatoria(tmp_path: Path) -> None:
    """Cada convocatoria que publica temario tiene su versión `published`: es la evidencia (§5.2).

    Guardia Civil y Celador existen y se migran como programas publicados; no son estudiables
    porque no tienen `primary`, y eso no los borra ni los convierte en comunes (§6.4).
    """
    settings = _settings(tmp_path)
    _sembrar_mundo_antiguo(settings)
    run_migrations(settings, revision="head")

    engine = build_engine(settings.data_paths.database)
    try:
        with engine.connect() as conexion:
            publicados = conexion.execute(
                text(
                    "SELECT c.code, v.status, count(n.id) FROM curricula c "
                    "JOIN curriculum_versions v ON v.curriculum_id = c.id "
                    "LEFT JOIN curriculum_nodes n ON n.curriculum_version_id = v.id "
                    "WHERE c.kind = 'published' GROUP BY c.code, v.status ORDER BY c.code"
                )
            ).all()
            primarios = conexion.execute(
                text("SELECT count(*) FROM convocation_curriculum_refs WHERE role = 'primary'")
            ).scalar_one()
    finally:
        engine.dispose()

    assert [(fila[0], fila[1], int(fila[2])) for fila in publicados] == [
        ("tai-age-2025-programa", "active", 2),
        ("tai-age-2026-programa", "active", 1),
    ]
    assert primarios == 0, "la migración no decide qué convocatorias son de informática C1"
