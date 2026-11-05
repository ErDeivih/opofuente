"""Re-atribución del banco al temario común (B-003) por el camino real.

Se siembran los perfiles (programa publicado del TAI) y el temario común, se crean preguntas y un
fallo mapeados a temas publicados, y se aplica el fixture de equivalencias. Se comprueba lo que el
slice exige:

1. solo se mueve el material de las equivalencias `accepted`; lo `proposed` se queda como estaba y
   se informa (O3: lo dudoso se revisa);
2. el informe tiene una fila por equivalencia y una entrada por mapeo/fallo movido, con su
   antes/después;
3. un choque de unicidad no se fuerza: se informa como conflicto y el mapeo sigue en su nodo;
4. re-ejecutar no duplica ni cambia nada, y
5. el inverso, desde el informe, devuelve el banco a los nodos publicados y retira las equivalencias
   que creó la operación.
"""

from __future__ import annotations

from dataclasses import asdict, replace
from datetime import UTC, datetime

import pytest
from sqlalchemy import text

from opofuente.application.remap_models import RemapPlan
from opofuente.config import Settings
from opofuente.domain.errors import InvariantViolationError
from opofuente.infrastructure.db import build_engine, build_session_factory
from opofuente.infrastructure.equivalence_fixture_loader import load_equivalences
from opofuente.infrastructure.remap_repository import SqlAlchemyRemapRepository
from tests.conftest import seed_common_curriculum

AHORA = datetime(2026, 11, 5, 9, 0, tzinfo=UTC)
PROGRAMA_TAI = "tai-age-2025-programa-v1"
COMUN = "informatica-c1-v1"


def _conectar(settings: Settings):
    engine = build_engine(settings.data_paths.database)
    return engine, build_session_factory(engine)


def _nodo_id(conexion, version_code: str, path: str) -> str:
    return str(
        conexion.execute(
            text(
                "SELECT n.id FROM curriculum_nodes n "
                "JOIN curriculum_versions v ON v.id = n.curriculum_version_id "
                "WHERE v.code = :version AND n.path = :path"
            ),
            {"version": version_code, "path": path},
        ).scalar_one()
    )


def _preparar(settings: Settings) -> None:
    """Crea cuatro preguntas y un fallo: dos mapeos claros, uno dudoso y uno con choque."""
    seed_common_curriculum(settings)
    engine, _sesiones = _conectar(settings)
    try:
        with engine.begin() as conexion:
            oposicion = str(
                conexion.execute(
                    text("SELECT id FROM oppositions WHERE code = 'tai-age'")
                ).scalar_one()
            )
            i1 = _nodo_id(conexion, PROGRAMA_TAI, "I.1")
            i2 = _nodo_id(conexion, PROGRAMA_TAI, "I.2")
            i4 = _nodo_id(conexion, PROGRAMA_TAI, "I.4")
            i7 = _nodo_id(conexion, PROGRAMA_TAI, "I.7")
            v37 = _nodo_id(conexion, COMUN, "V.37")
            conexion.execute(
                text(
                    "INSERT INTO question_sets (id, title, opposition_id, set_type, status, "
                    "created_at, updated_at) VALUES ('qs-1', 'Banco TAI', :oposicion, "
                    "'private_bank', 'draft', :ahora, :ahora)"
                ),
                {"oposicion": oposicion, "ahora": AHORA},
            )
            for indice in range(1, 5):
                conexion.execute(
                    text(
                        "INSERT INTO question_versions (id, question_set_id, stable_key, "
                        "version_no, stem, question_type, position, origin_type, status, "
                        "created_at) VALUES (:id, 'qs-1', :clave, 1, :enunciado, "
                        "'single_choice', :posicion, 'official', 'complete', :ahora)"
                    ),
                    {
                        "id": f"qv-{indice}",
                        "clave": f"k{indice}",
                        "enunciado": f"Pregunta {indice}",
                        "posicion": indice,
                        "ahora": AHORA,
                    },
                )

            def mapeo(mapeo_id: str, nodo: str, pregunta: str) -> None:
                conexion.execute(
                    text(
                        "INSERT INTO curriculum_mappings (id, curriculum_node_id, subject_type, "
                        "subject_id, coverage_type, depth, confidence, status, created_at, "
                        "approved_at) VALUES (:id, :nodo, 'question_version', :pregunta, "
                        "'complete', 0, 1.0, 'accepted', :ahora, :ahora)"
                    ),
                    {"id": mapeo_id, "nodo": nodo, "pregunta": pregunta, "ahora": AHORA},
                )

            mapeo("map-1", i1, "qv-1")  # I.1 -> I.1 (accepted)
            mapeo("map-2", i4, "qv-2")  # I.4 es proposed: se queda
            mapeo("map-3", i7, "qv-3")  # I.7 -> V.37 (accepted)
            mapeo("map-4", i7, "qv-4")  # I.7 -> V.37, pero V.37 ya tiene qv-4: conflicto
            mapeo("map-5", v37, "qv-4")

            # Un fallo declarado sobre I.2, que se re-atribuye a I.1 (accepted).
            conexion.execute(
                text(
                    "INSERT INTO study_sessions (id, opposition_id, mode, feedback, "
                    "configuration_json, total_questions, created_at) VALUES ('sesion-1', "
                    ":oposicion, 'practice', 'immediate', '{}', 1, :ahora)"
                ),
                {"oposicion": oposicion, "ahora": AHORA},
            )
            conexion.execute(
                text(
                    "INSERT INTO session_questions (id, session_id, question_version_id, "
                    "stable_key, position) VALUES ('sq-1', 'sesion-1', 'qv-1', 'k1', 1)"
                )
            )
            conexion.execute(
                text(
                    "INSERT INTO attempts (id, session_question_id, chosen_option_keys_json, "
                    "elapsed_ms, answered_at) VALUES ('att-1', 'sq-1', '[]', 1000, :ahora)"
                ),
                {"ahora": AHORA},
            )
            conexion.execute(
                text(
                    "INSERT INTO learning_errors (id, attempt_id, curriculum_node_id, cause, "
                    "status, occurrences, first_seen_at, last_seen_at) VALUES ('le-1', 'att-1', "
                    ":nodo, 'knowledge', 'open', 1, :ahora, :ahora)"
                ),
                {"nodo": i2, "ahora": AHORA},
            )
    finally:
        engine.dispose()


@pytest.fixture
def escenario(seeded_settings: Settings):
    _preparar(seeded_settings)
    engine, sesiones = _conectar(seeded_settings)
    yield seeded_settings, sesiones
    engine.dispose()


def _aplicar(settings: Settings) -> RemapPlan:
    engine, sesiones = _conectar(settings)
    try:
        return SqlAlchemyRemapRepository(sesiones).apply(load_equivalences(), now=AHORA)
    finally:
        engine.dispose()


def _plan(settings: Settings) -> RemapPlan:
    engine, sesiones = _conectar(settings)
    try:
        return SqlAlchemyRemapRepository(sesiones).plan(load_equivalences())
    finally:
        engine.dispose()


def _mapeo_node(sesiones, mapeo_id: str) -> str:
    with sesiones() as session:
        return str(
            session.execute(
                text("SELECT curriculum_node_id FROM curriculum_mappings WHERE id = :id"),
                {"id": mapeo_id},
            ).scalar_one()
        )


def _error_node(sesiones, error_id: str) -> str:
    with sesiones() as session:
        return str(
            session.execute(
                text("SELECT curriculum_node_id FROM learning_errors WHERE id = :id"),
                {"id": error_id},
            ).scalar_one()
        )


def test_el_plan_no_escribe_nada_y_solo_mueve_lo_aceptado(escenario) -> None:
    settings, sesiones = escenario
    plan = _plan(settings)

    assert plan.changed is True
    assert plan.equivalences_created == 33
    assert plan.mappings_examined == 4
    assert plan.mappings_moved == 2, "I.1 y I.7 son accepted; I.4 está proposed y no se toca"
    assert plan.mappings_conflicts == 1
    assert plan.errors_moved == 1
    filas = {fila.source_path: fila for fila in plan.rows}
    assert filas["I.1"].applied is True
    assert filas["I.4"].applied is False
    assert filas["I.4"].kept_mappings == 1, "lo dudoso se queda y se informa"
    assert filas["I.7"].conflicts, "el choque de unicidad se informa como conflicto"

    # Nada se ha escrito: ni equivalencias ni nodos movidos.
    with sesiones() as session:
        equivalencias = session.execute(
            text("SELECT COUNT(*) FROM curriculum_equivalences")
        ).scalar_one()
        nodo_map1 = str(
            session.execute(
                text(
                    "SELECT n.path FROM curriculum_nodes n JOIN curriculum_mappings m "
                    "ON m.curriculum_node_id = n.id WHERE m.id = 'map-1'"
                )
            ).scalar_one()
        )
    assert equivalencias == 0
    assert nodo_map1 == "I.1"


def test_la_re_atribucion_mueve_el_material_y_deja_informe_por_fila(escenario) -> None:
    settings, sesiones = escenario
    plan = _aplicar(settings)

    assert plan.changed is True
    assert len(plan.rows) == 33, "una fila por tema publicado"
    assert plan.created_equivalence_ids, "el informe lleva los ids de las equivalencias creadas"

    with sesiones() as session:
        i1 = str(
            session.execute(
                text(
                    "SELECT id FROM curriculum_nodes WHERE path = 'I.1' "
                    "AND curriculum_version_id = "
                    "(SELECT id FROM curriculum_versions WHERE code = :codigo)"
                ),
                {"codigo": COMUN},
            ).scalar_one()
        )
        v37 = str(
            session.execute(
                text(
                    "SELECT id FROM curriculum_nodes WHERE path = 'V.37' "
                    "AND curriculum_version_id = "
                    "(SELECT id FROM curriculum_versions WHERE code = :codigo)"
                ),
                {"codigo": COMUN},
            ).scalar_one()
        )
        mapeos = {
            str(fila[0]): str(fila[1])
            for fila in session.execute(
                text("SELECT id, curriculum_node_id FROM curriculum_mappings")
            )
        }
        equivalencias = session.execute(
            text(
                "SELECT status, COUNT(*), SUM(decided_at IS NOT NULL) "
                "FROM curriculum_equivalences GROUP BY status ORDER BY status"
            )
        ).all()

    assert mapeos["map-1"] == i1, "la pregunta de I.1 aparece bajo el tema común I.1"
    assert mapeos["map-3"] == v37, "la pregunta de I.7 aparece bajo V.37"
    assert mapeos["map-2"] != i1, "el mapeo de un tema proposed no se mueve"
    assert mapeos["map-4"] != v37, "el mapeo en conflicto se queda donde estaba"
    assert _error_node(sesiones, "le-1") == i1, "el fallo también se re-atribuye"
    assert [(str(f[0]), int(f[1]), int(f[2])) for f in equivalencias] == [
        ("accepted", 20, 20),
        ("proposed", 13, 0),
    ], "las accepted quedan decididas; las proposed esperan revisión"

    fila_i1 = next(fila for fila in plan.rows if fila.source_path == "I.1")
    assert fila_i1.equivalence_action == "create"
    assert len(fila_i1.mappings) == 1
    assert fila_i1.mappings[0].from_path == "I.1"
    assert fila_i1.mappings[0].to_path == "I.1"
    assert fila_i1.mappings[0].object_type == "curriculum_mapping"


def test_re_ejecutar_no_duplica_ni_cambia_nada(escenario) -> None:
    settings, sesiones = escenario
    _aplicar(settings)

    segundo_plan = _plan(settings)
    assert segundo_plan.changed is False
    assert segundo_plan.equivalences_created == 0
    assert segundo_plan.equivalences_updated == 0
    assert segundo_plan.mappings_moved == 0
    assert segundo_plan.errors_moved == 0

    _aplicar(settings)
    with sesiones() as session:
        total = session.execute(text("SELECT COUNT(*) FROM curriculum_equivalences")).scalar_one()
    assert total == 33, "re-ejecutar no duplica equivalencias"


def test_el_inverso_devuelve_el_banco_a_su_nodo_publicado(escenario) -> None:
    settings, sesiones = escenario
    plan = _aplicar(settings)
    cambios = [
        asdict(cambio) for fila in plan.rows for cambio in (*fila.mappings, *fila.learning_errors)
    ]
    informe = {
        "changes": cambios,
        "created_equivalence_ids": list(plan.created_equivalence_ids),
    }

    engine, sesiones_inverso = _conectar(settings)
    try:
        resultado = SqlAlchemyRemapRepository(sesiones_inverso).inverse(informe)
    finally:
        engine.dispose()

    assert resultado.mappings_reverted == 2
    assert resultado.errors_reverted == 1
    assert resultado.equivalences_removed == 33
    assert resultado.skipped == 0

    with sesiones() as session:
        nodos = {
            str(fila[0]): str(fila[1])
            for fila in session.execute(
                text(
                    "SELECT m.id, n.path FROM curriculum_mappings m "
                    "JOIN curriculum_nodes n ON n.id = m.curriculum_node_id"
                )
            )
        }
        restantes = session.execute(
            text("SELECT COUNT(*) FROM curriculum_equivalences")
        ).scalar_one()
        error = str(
            session.execute(
                text(
                    "SELECT n.path FROM learning_errors e JOIN curriculum_nodes n "
                    "ON n.id = e.curriculum_node_id WHERE e.id = 'le-1'"
                )
            ).scalar_one()
        )

    assert nodos["map-1"] == "I.1", "vuelve al nodo publicado"
    assert nodos["map-3"] == "I.7"
    assert nodos["map-2"] == "I.4"
    assert error == "I.2"
    assert restantes == 0, "el inverso retira las equivalencias que creó la operación"


def test_un_fixture_que_no_cubre_todos_los_temas_publicados_se_rechaza(escenario) -> None:
    settings, _sesiones = escenario
    fixture = load_equivalences()
    incompleto = replace(fixture, rows=fixture.rows[:-1])

    engine, sesiones = _conectar(settings)
    try:
        with pytest.raises(
            InvariantViolationError, match="no cubre exactamente los temas publicados"
        ):
            SqlAlchemyRemapRepository(sesiones).plan(incompleto)
    finally:
        engine.dispose()
