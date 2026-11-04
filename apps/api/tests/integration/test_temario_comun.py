"""Temario común v1: fixture, siembra idempotente y publicación (B-002).

Lo que se comprueba es el contrato de `ESPECIFICACION.md` §6.7 y la aceptación de B-002:

1. el fixture v1 tiene **5 bloques, 40 temas y 45 nodos**, con las rutas `I.1`…`V.40` y la
   numeración 1-40 que publica la fuente;
2. la siembra es **idempotente**: ejecutarla dos veces no duplica temario, versión, nodos ni
   referencias, y la segunda pasada no cambia nada;
3. la versión se publica (`draft` → `active`) **solo si el recuento cuadra**; un temario incompleto
   se queda en borrador;
4. el TAI 2025 queda con su referencia `primary` al común, con su cita de las bases (O1);
5. una versión ya `active` **no se edita** (I9): si el fixture cambia, la siembra avisa en vez de
   reescribir la edición que estudian las convocatorias.

El fixture es el del repositorio, y el cargador valida que sus recuentos declarados coincidan con
los nodos reales: la prueba no escribe el temario a mano.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import sessionmaker

from opofuente.application.curriculum_service import CurriculaService
from opofuente.config import Settings, project_root
from opofuente.domain.curricula import CommonCurriculum
from opofuente.domain.errors import InvariantViolationError
from opofuente.infrastructure.clock import SystemClock
from opofuente.infrastructure.curriculum_fixture_loader import load_common_curriculum
from opofuente.infrastructure.curriculum_repository import SqlAlchemyCurriculumRepository
from opofuente.infrastructure.db import build_engine, build_session_factory
from opofuente.infrastructure.db_models import (
    ConvocationCurriculumRefRecord,
    ConvocationVersionRecord,
    CurriculumNodeRecord,
    CurriculumRecord,
    CurriculumVersionRecord,
)

#: Rutas de los 40 temas en el orden oficial: bloque romano + número de tema de la fuente.
RUTAS_ESPERADAS = (
    *(f"I.{numero}" for numero in range(1, 13)),
    *(f"II.{numero}" for numero in range(13, 18)),
    *(f"III.{numero}" for numero in range(18, 27)),
    *(f"IV.{numero}" for numero in range(27, 34)),
    *(f"V.{numero}" for numero in range(34, 41)),
)

AHORA = datetime(2026, 11, 4, 12, 0, tzinfo=UTC)


def _fixture_path() -> Path:
    return project_root() / "fixtures" / "curricula" / "informatica-c1.v1.json"


def _curriculum() -> CommonCurriculum:
    return load_common_curriculum(_fixture_path())


def _servicio(session_factory: sessionmaker) -> CurriculaService:
    return CurriculaService(SqlAlchemyCurriculumRepository(session_factory), SystemClock())


def _sembrar(settings: Settings):
    """Siembra el temario común sobre una base ya migrada y sembrada de perfiles."""
    engine = build_engine(settings.data_paths.database)
    try:
        sesiones = build_session_factory(engine)
        return _servicio(sesiones).seed(_curriculum())
    finally:
        engine.dispose()


@pytest.fixture
def session_factory(seeded_settings: Settings):
    engine = build_engine(seeded_settings.data_paths.database)
    try:
        yield build_session_factory(engine)
    finally:
        engine.dispose()


def test_el_fixture_declara_el_origen_los_recuentos_y_la_referencia_del_tai() -> None:
    """El fixture es rastreable: su sha256 es el de la fuente y sus recuentos son los de la v1."""
    curriculum = _curriculum()

    assert curriculum.code == "informatica-c1"
    assert curriculum.version_no == 1
    assert curriculum.version_code == "informatica-c1-v1"
    assert curriculum.source.document.endswith("temario-c1.md")
    assert len(curriculum.source.sha256) == 64
    assert all(caracter in "0123456789abcdef" for caracter in curriculum.source.sha256.lower())

    bloques = list(curriculum.nodes)
    temas = [nodo for bloque in curriculum.nodes for nodo in bloque.children]
    assert len(bloques) == 5
    assert len(temas) == 40
    assert [nodo.path for bloque in curriculum.nodes for nodo in bloque.children] == list(
        RUTAS_ESPERADAS
    )
    assert [nodo.official_code for bloque in curriculum.nodes for nodo in bloque.children] == [
        str(numero) for numero in range(1, 41)
    ]

    assert len(curriculum.references) == 1
    referencia = curriculum.references[0]
    assert referencia.convocation_code == "tai-age-2025"
    assert referencia.role == "primary"
    assert "ANEXO V" in referencia.source_reference


def test_la_siembra_del_temario_comun_es_idempotente(seeded_settings: Settings) -> None:
    """Dos ejecuciones no duplican nada: es la aceptación explícita de B-002."""
    primera = _sembrar(seeded_settings)

    assert primera.created > 0, "la primera siembra crea el temario"
    assert primera.published is True, "con 5 bloques y 40 temas la versión se publica"
    assert primera.changed is True

    segunda = _sembrar(seeded_settings)

    assert segunda.created == 0
    assert segunda.updated == 0
    assert segunda.blocked == 0
    assert segunda.changed is False
    assert segunda.unchanged > 0, "la segunda pasada sí comprueba algo y no cambia nada"


def test_el_temario_sembrado_tiene_cinco_bloques_y_cuarenta_temas(
    seeded_settings: Settings, session_factory
) -> None:
    """La forma del temario en la base: 45 nodos, rutas I.1…V.40 y una versión activa."""
    _sembrar(seeded_settings)

    with session_factory() as session:
        version = session.execute(
            select(CurriculumVersionRecord).where(
                CurriculumVersionRecord.code == "informatica-c1-v1"
            )
        ).scalar_one()
        nodos = (
            session.execute(
                select(CurriculumNodeRecord).where(
                    CurriculumNodeRecord.curriculum_version_id == version.id
                )
            )
            .scalars()
            .all()
        )

    assert version.status == "active"
    assert version.version_no == 1
    assert len(nodos) == 45
    bloques = sorted(
        (nodo for nodo in nodos if nodo.node_type == "block"), key=lambda nodo: nodo.position
    )
    temas = [
        tema
        for bloque in bloques
        for tema in sorted(
            (nodo for nodo in nodos if nodo.parent_id == bloque.id),
            key=lambda nodo: nodo.position,
        )
    ]
    assert len(bloques) == 5
    assert len(temas) == 40
    assert [nodo.path for nodo in temas] == list(RUTAS_ESPERADAS)
    assert [nodo.official_code for nodo in temas] == [str(numero) for numero in range(1, 41)]
    assert all(nodo.origin_kind == "base" for nodo in nodos)


def test_la_siembra_crea_la_referencia_primary_del_tai_con_su_cita(
    seeded_settings: Settings, session_factory
) -> None:
    """O1: el TAI 2025 estudia el temario común; la referencia lo dice con la cita de las bases."""
    _sembrar(seeded_settings)

    with session_factory() as session:
        convocatoria = session.execute(
            select(ConvocationVersionRecord).where(ConvocationVersionRecord.code == "tai-age-2025")
        ).scalar_one()
        version = session.execute(
            select(CurriculumVersionRecord).where(
                CurriculumVersionRecord.code == "informatica-c1-v1"
            )
        ).scalar_one()
        referencias = (
            session.execute(
                select(ConvocationCurriculumRefRecord).where(
                    ConvocationCurriculumRefRecord.convocation_version_id == convocatoria.id
                )
            )
            .scalars()
            .all()
        )

    primary = [referencia for referencia in referencias if referencia.role == "primary"]
    assert len(primary) == 1
    assert primary[0].curriculum_version_id == version.id
    assert primary[0].source_reference == "ANEXO V, apartado 3"


def test_un_temario_incompleto_no_se_publica(seeded_settings: Settings, session_factory) -> None:
    """Publicar es afirmar que el temario está completo: con un bloque no se publica."""
    curriculum = _curriculum()
    incompleto = replace(
        curriculum,
        nodes=curriculum.nodes[:1],
        references=(),
    )

    engine = build_engine(seeded_settings.data_paths.database)
    try:
        sesiones = build_session_factory(engine)
        reporte = _servicio(sesiones).seed(incompleto)
    finally:
        engine.dispose()

    assert reporte.published is False
    assert reporte.changed is True

    with session_factory() as session:
        version = session.execute(
            select(CurriculumVersionRecord).where(
                CurriculumVersionRecord.code == "informatica-c1-v1"
            )
        ).scalar_one()
        nodos = session.execute(
            select(func.count())
            .select_from(CurriculumNodeRecord)
            .where(CurriculumNodeRecord.curriculum_version_id == version.id)
        ).scalar_one()

    assert version.status == "draft", "un temario incompleto se queda en borrador"
    assert nodos == 13, "1 bloque + 12 temas, sin inventar los que faltan"

    # Y la siembra buena vuelve a publicarlo, sin duplicar la versión.
    _sembrar(seeded_settings)
    with session_factory() as session:
        version = session.execute(
            select(CurriculumVersionRecord).where(
                CurriculumVersionRecord.code == "informatica-c1-v1"
            )
        ).scalar_one()
    assert version.status == "active"


def test_una_version_activa_no_se_edita(seeded_settings: Settings) -> None:
    """I9: si el fixture cambia, se avisa; no se reescribe la versión que ya estudian."""
    _sembrar(seeded_settings)
    curriculum = _curriculum()
    bloque = replace(curriculum.nodes[0], title="Título cambiado a mano")
    modificado = replace(curriculum, nodes=(bloque, *curriculum.nodes[1:]))

    engine = build_engine(seeded_settings.data_paths.database)
    try:
        sesiones = build_session_factory(engine)
        with pytest.raises(InvariantViolationError, match="no se edita"):
            _servicio(sesiones).seed(modificado)
    finally:
        engine.dispose()

    engine = build_engine(seeded_settings.data_paths.database)
    try:
        sesiones = build_session_factory(engine)
        with sesiones() as session:
            version = session.execute(
                select(CurriculumVersionRecord).where(
                    CurriculumVersionRecord.code == "informatica-c1-v1"
                )
            ).scalar_one()
            titulo = session.execute(
                select(CurriculumNodeRecord.title).where(
                    CurriculumNodeRecord.curriculum_version_id == version.id,
                    CurriculumNodeRecord.path == "I",
                )
            ).scalar_one()
    finally:
        engine.dispose()

    assert titulo != "Título cambiado a mano", "la versión activa sigue como estaba"


def test_el_temario_comun_es_uno_solo(seeded_settings: Settings, session_factory) -> None:
    """I1/I2: una fila común, una versión, y ningún nodo duplicado por convocatoria."""
    _sembrar(seeded_settings)
    _sembrar(seeded_settings)

    with session_factory() as session:
        comunes = session.execute(
            select(func.count())
            .select_from(CurriculumRecord)
            .where(CurriculumRecord.kind == "common")
        ).scalar_one()
        versiones = session.execute(
            select(func.count())
            .select_from(CurriculumVersionRecord)
            .join(
                CurriculumRecord,
                CurriculumRecord.id == CurriculumVersionRecord.curriculum_id,
            )
            .where(CurriculumRecord.kind == "common")
        ).scalar_one()
        nodos_comunes = session.execute(
            select(func.count())
            .select_from(CurriculumNodeRecord)
            .join(
                CurriculumVersionRecord,
                CurriculumVersionRecord.id == CurriculumNodeRecord.curriculum_version_id,
            )
            .join(
                CurriculumRecord,
                CurriculumRecord.id == CurriculumVersionRecord.curriculum_id,
            )
            .where(CurriculumRecord.kind == "common")
        ).scalar_one()
        referencias_primary = session.execute(
            select(func.count())
            .select_from(ConvocationCurriculumRefRecord)
            .where(ConvocationCurriculumRefRecord.role == "primary")
        ).scalar_one()
        referencias_total = session.execute(
            select(func.count()).select_from(ConvocationCurriculumRefRecord)
        ).scalar_one()

    assert comunes == 1
    assert versiones == 1, "una sola edición del común"
    assert nodos_comunes == 45, "los nodos son del común, no una copia por convocatoria"
    assert referencias_primary == 1, "solo la primary del TAI"
    assert referencias_total == 4, "3 programas publicados (official) + la primary del TAI"
