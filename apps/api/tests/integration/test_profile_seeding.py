"""Pruebas de integración de la siembra de perfiles y de sus restricciones reales."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from opofuente.application.profiles_service import ProfilesService
from opofuente.config import Settings, project_root
from opofuente.domain.profiles import ConvocationStatus, NodeType
from opofuente.infrastructure.clock import SystemClock
from opofuente.infrastructure.db import build_engine, build_session_factory
from opofuente.infrastructure.db_models import (
    ConvocationVersionRecord,
    CurriculumMappingRecord,
    CurriculumNodeRecord,
    ExamPartRecord,
    ExamRuleRecord,
    OppositionRecord,
)
from opofuente.infrastructure.fixture_loader import load_profiles
from opofuente.infrastructure.profile_repository import SqlAlchemyProfileRepository
from tests.conftest import seed_official_profiles

NOW = datetime(2026, 9, 14, 12, 0, tzinfo=UTC)


@pytest.fixture
def session_factory(migrated_settings: Settings):
    engine = build_engine(migrated_settings.data_paths.database)
    try:
        yield build_session_factory(engine)
    finally:
        engine.dispose()


@pytest.fixture
def profiles():
    return load_profiles(project_root() / "fixtures" / "profiles")


def test_la_siembra_es_idempotente(seeded_settings: Settings) -> None:
    """Sembrar dos veces no duplica nada y deja el mismo estado."""
    second = seed_official_profiles(seeded_settings)

    assert second.created == 0
    assert second.updated == 0
    assert second.unchanged > 0
    assert second.changed is False


def test_recuentos_sembrados_coinciden_con_los_fixtures(
    seeded_settings: Settings, session_factory
) -> None:
    esperados = {
        "tai-age-2025": {NodeType.BLOCK: 4, NodeType.TOPIC: 33, NodeType.EPIGRAPH: 0},
        "gc-cabos-guardias-2026": {NodeType.TOPIC: 25},
    }
    with session_factory() as session:
        for code, esperado in esperados.items():
            convocation = session.execute(
                select(ConvocationVersionRecord).where(ConvocationVersionRecord.code == code)
            ).scalar_one()
            rows = (
                session.execute(
                    select(CurriculumNodeRecord).where(
                        CurriculumNodeRecord.convocation_version_id == convocation.id
                    )
                )
                .scalars()
                .all()
            )
            counts = dict.fromkeys(NodeType, 0)
            for row in rows:
                counts[NodeType(row.node_type)] += 1
            for node_type, value in esperado.items():
                assert counts[node_type] == value, f"{code}: {node_type}"


def test_solo_una_convocatoria_activa_por_oposicion(
    seeded_settings: Settings, session_factory
) -> None:
    """La restricción la impone la base de datos con un índice único parcial."""
    with session_factory() as session:
        oposicion = session.execute(
            select(OppositionRecord).where(OppositionRecord.code == "tai-age")
        ).scalar_one()
        session.add(
            ConvocationVersionRecord(
                id=str(uuid4()),
                opposition_id=oposicion.id,
                code="tai-age-2027-prueba",
                title="Convocatoria de prueba",
                official_url="https://www.boe.es/",
                published_at=datetime(2027, 1, 1).date(),
                exam_date=None,
                status=ConvocationStatus.ACTIVE.value,
                source_reference=None,
                supersedes_id=None,
                created_at=NOW,
                updated_at=NOW,
            )
        )
        with pytest.raises(IntegrityError):
            session.commit()


def test_una_segunda_convocatoria_en_borrador_si_se_permite(
    seeded_settings: Settings, session_factory
) -> None:
    with session_factory() as session:
        oposicion = session.execute(
            select(OppositionRecord).where(OppositionRecord.code == "tai-age")
        ).scalar_one()
        session.add(
            ConvocationVersionRecord(
                id=str(uuid4()),
                opposition_id=oposicion.id,
                code="tai-age-2027-borrador",
                title="Convocatoria futura",
                official_url="https://www.boe.es/",
                published_at=datetime(2027, 1, 1).date(),
                exam_date=None,
                status=ConvocationStatus.DRAFT.value,
                source_reference=None,
                supersedes_id=None,
                created_at=NOW,
                updated_at=NOW,
            )
        )
        session.commit()
        total = session.execute(
            select(func.count()).select_from(ConvocationVersionRecord)
        ).scalar_one()
        assert total == 3


def test_solo_una_oposicion_activa(seeded_client) -> None:
    """Activar una oposición desactiva la anterior."""
    oppositions = seeded_client.get("/api/v1/oppositions").json()
    activa = [item for item in oppositions if item["active"]]
    assert len(activa) == 1
    assert activa[0]["code"] == "tai-age"
    assert activa[0]["active_convocation"]["code"] == "tai-age-2025"

    otra = next(item for item in oppositions if item["code"] == "gc-cabos-guardias")
    response = seeded_client.post(f"/api/v1/oppositions/{otra['id']}/activate")
    assert response.status_code == 200
    assert response.json()["active"] is True

    despues = seeded_client.get("/api/v1/oppositions").json()
    assert [item["code"] for item in despues if item["active"]] == ["gc-cabos-guardias"]


def test_una_oposicion_existente_sin_cambios_se_activa_si_el_fixture_lo_pide(
    seeded_settings: Settings, session_factory, profiles
) -> None:
    """Fallo real encontrado en la prueba manual: el retorno temprano saltaba la activación.

    Si el fixture pasa a declarar activa una oposición que ya existía y no había cambiado, la
    siembra tiene que activarla igualmente.
    """
    tai = next(profile for profile in profiles if profile.convocation.code == "tai-age-2025")
    otro = next(profile for profile in profiles if profile.convocation.code != "tai-age-2025")

    with session_factory() as session:
        service = ProfilesService(SqlAlchemyProfileRepository(session_factory), SystemClock())
        # Se activa solo la otra oposición, para dejar TAI inactiva sin tocar sus datos.
        service.seed((replace(otro, opposition=replace(otro.opposition, active=True)),))

        # TAI ya existe, sus datos no cambian y el fixture la declara activa: debe activarse.
        report = service.seed((tai,))
        assert report.changed is True

        oposiciones = {
            row.code: row.active
            for row in session.execute(select(OppositionRecord)).scalars().all()
        }
        assert oposiciones == {"tai-age": True, "gc-cabos-guardias": False}


def test_borrar_una_convocatoria_arrastra_su_contenido_pero_no_la_oposicion(
    seeded_settings: Settings, session_factory
) -> None:
    with session_factory() as session:
        convocation = session.execute(
            select(ConvocationVersionRecord).where(ConvocationVersionRecord.code == "tai-age-2025")
        ).scalar_one()
        convocation_id = convocation.id

        assert _count(session, CurriculumNodeRecord, convocation_id) == 37
        assert _count(session, ExamPartRecord, convocation_id) == 3
        assert _count(session, ExamRuleRecord, convocation_id) == 8

        session.delete(convocation)
        session.commit()

        assert _count(session, CurriculumNodeRecord, convocation_id) == 0
        assert _count(session, ExamPartRecord, convocation_id) == 0
        assert session.execute(select(func.count()).select_from(OppositionRecord)).scalar_one() == 2


def test_si_el_fixture_cambia_la_siembra_lo_actualiza(
    seeded_settings: Settings, session_factory, profiles
) -> None:
    tai = next(profile for profile in profiles if profile.convocation.code == "tai-age-2025")
    otro = next(profile for profile in profiles if profile.convocation.code != "tai-age-2025")
    original = tai.curriculum[0]
    perfil_modificado = replace(
        tai,
        curriculum=(replace(original, title="Título corregido en el fixture"), *tai.curriculum[1:]),
    )

    with session_factory() as session:
        service = ProfilesService(SqlAlchemyProfileRepository(session_factory), SystemClock())
        report = service.seed((perfil_modificado, otro))
        assert report.updated == 1
        assert report.created == 0

        convocation = session.execute(
            select(ConvocationVersionRecord).where(ConvocationVersionRecord.code == "tai-age-2025")
        ).scalar_one()
        row = session.execute(
            select(CurriculumNodeRecord).where(
                CurriculumNodeRecord.convocation_version_id == convocation.id,
                CurriculumNodeRecord.path == original.path,
            )
        ).scalar_one()
        assert row.title == "Título corregido en el fixture"


def test_las_rutas_del_programa_sembrado_son_unicas(
    seeded_settings: Settings, session_factory
) -> None:
    with session_factory() as session:
        paths = [row.path for row in session.execute(select(CurriculumNodeRecord)).scalars().all()]
    assert len(paths) == len(set(paths))
    assert len(paths) == 37 + 198


def test_un_nodo_con_material_asignado_no_se_retira_al_sembrar(
    seeded_settings: Settings, session_factory, profiles
) -> None:
    """DEBT-005: la siembra no puede borrar un nodo que tiene material asignado.

    Reproduce el caso real: el fixture reorganiza el temario y dos temas desaparecen. Uno tiene un
    mapeo (material asignado) y el otro no. El que no tiene nada se retira como siempre; el que sí
    tiene material **se conserva** y la siembra lo declara como conflicto en lugar de destruir la
    clasificación del usuario (ADR-007). El resto del perfil se aplica con normalidad.
    """
    gc = next(
        profile for profile in profiles if profile.convocation.code == "gc-cabos-guardias-2026"
    )
    anterior = gc.curriculum[-2]
    ultimo = gc.curriculum[-1]

    with session_factory() as session:
        convocation = session.execute(
            select(ConvocationVersionRecord).where(
                ConvocationVersionRecord.code == "gc-cabos-guardias-2026"
            )
        ).scalar_one()
        nodo_con_material = session.execute(
            select(CurriculumNodeRecord).where(
                CurriculumNodeRecord.convocation_version_id == convocation.id,
                CurriculumNodeRecord.path == anterior.path,
            )
        ).scalar_one()
        session.add(
            CurriculumMappingRecord(
                id="map-debt-005",
                curriculum_node_id=nodo_con_material.id,
                subject_type="artifact",
                subject_id="art-1",
                coverage_type="partial",
                depth=nodo_con_material.depth,
                confidence=0.7,
                status="accepted",
                source_proposal_id=None,
                created_at=NOW,
                approved_at=NOW,
            )
        )
        session.commit()

    # El fixture nuevo ya no trae los dos últimos temas.
    perfil_sin_los_ultimos = replace(gc, curriculum=gc.curriculum[:-2])
    otro = next(profile for profile in profiles if profile is not gc)

    with session_factory() as session:
        service = ProfilesService(SqlAlchemyProfileRepository(session_factory), SystemClock())
        report = service.seed((perfil_sin_los_ultimos, otro))
        convocation = session.execute(
            select(ConvocationVersionRecord).where(
                ConvocationVersionRecord.code == "gc-cabos-guardias-2026"
            )
        ).scalar_one()
        paths = {
            row.path
            for row in session.execute(
                select(CurriculumNodeRecord).where(
                    CurriculumNodeRecord.convocation_version_id == convocation.id
                )
            )
            .scalars()
            .all()
        }
        mapeos = session.execute(
            select(func.count()).select_from(CurriculumMappingRecord)
        ).scalar_one()

    assert report.blocked == 1, "un nodo con material: un conflicto declarado"
    assert report.changed is True, (
        "no converge con el fixture, y eso hay que decirlo, no esconderlo"
    )
    assert anterior.path in paths, "el nodo con material asignado sigue ahí"
    assert ultimo.path not in paths, "el nodo sin material sí se retira"
    assert mapeos == 1, "el mapeo no se ha perdido"

    perfil = next(o for o in report.profiles if o.profile_code == "gc-cabos-guardias-2026")
    bloqueado = [entity for entity in perfil.entities if entity.blocked]
    assert [entity.code for entity in bloqueado] == [f"node:{anterior.path}"]
    assert bloqueado[0].unchanged is False, "bloqueado no es «sin cambios»"


def _count(session, model, convocation_id: str) -> int:
    return session.execute(
        select(func.count())
        .select_from(model)
        .where(model.convocation_version_id == convocation_id)
    ).scalar_one()
