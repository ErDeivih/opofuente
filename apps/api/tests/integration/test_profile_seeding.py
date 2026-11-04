"""Pruebas de integración de la siembra de perfiles y de sus restricciones reales."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import replace
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError

from opofuente.application.profiles_service import ProfilesService
from opofuente.config import Settings, project_root
from opofuente.domain.errors import InvariantViolationError
from opofuente.domain.profiles import ConvocationStatus, NodeType
from opofuente.infrastructure.clock import SystemClock
from opofuente.infrastructure.db import build_engine, build_session_factory
from opofuente.infrastructure.db_models import (
    ConvocationCurriculumRefRecord,
    ConvocationVersionRecord,
    CurriculumMappingRecord,
    CurriculumNodeRecord,
    CurriculumVersionRecord,
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


def _version_of(session, convocation_id: str) -> str:
    """Versión del programa publicado de una convocatoria: el nuevo dueño de sus nodos."""
    return str(
        session.execute(
            select(ConvocationCurriculumRefRecord.curriculum_version_id).where(
                ConvocationCurriculumRefRecord.convocation_version_id == convocation_id,
                ConvocationCurriculumRefRecord.role == "official",
            )
        ).scalar_one()
    )


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
        "celador-sacyl-2022": {NodeType.BLOCK: 0, NodeType.TOPIC: 16, NodeType.EPIGRAPH: 0},
    }
    with session_factory() as session:
        for code, esperado in esperados.items():
            convocation = session.execute(
                select(ConvocationVersionRecord).where(ConvocationVersionRecord.code == code)
            ).scalar_one()
            rows = (
                session.execute(
                    select(CurriculumNodeRecord).where(
                        CurriculumNodeRecord.curriculum_version_id
                        == _version_of(session, convocation.id)
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
        assert total == 4


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
    # Explícito a propósito: con tres perfiles, «el que no es TAI» ya no identifica a uno solo.
    otro = next(
        profile for profile in profiles if profile.convocation.code == "gc-cabos-guardias-2026"
    )

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
        assert oposiciones == {
            "tai-age": True,
            "gc-cabos-guardias": False,
            "celador-sacyl": False,
        }


def test_borrar_una_convocatoria_arrastra_su_examen_pero_no_su_programa(
    seeded_settings: Settings, session_factory
) -> None:
    """El programa publicado **no** es una parte de la convocatoria: es su evidencia.

    Antes de `0021` los nodos colgaban de la convocatoria y borrarla se los llevaba por delante.
    Ahora cuelgan de una versión de temario `published`, así que sobreviven (con sus `id`, que es
    lo que sostiene los mapeos de material); lo que sí se va con la convocatoria es su examen
    (`exam_parts`, `exam_rules`) y su referencia `official`. La oposición tampoco se borra.
    """
    with session_factory() as session:
        convocation = session.execute(
            select(ConvocationVersionRecord).where(ConvocationVersionRecord.code == "tai-age-2025")
        ).scalar_one()
        convocation_id = convocation.id
        version_id = _version_of(session, convocation_id)

        assert _count_nodes(session, version_id) == 37
        assert _count(session, ExamPartRecord, convocation_id) == 3
        assert _count(session, ExamRuleRecord, convocation_id) == 8

        session.delete(convocation)
        session.commit()

        assert _count_nodes(session, version_id) == 37, (
            "los nodos son del programa publicado: no se borran por la espalda"
        )
        assert _count(session, ExamPartRecord, convocation_id) == 0
        assert _count(session, ExamRuleRecord, convocation_id) == 0
        referencias = session.execute(
            select(func.count())
            .select_from(ConvocationCurriculumRefRecord)
            .where(ConvocationCurriculumRefRecord.convocation_version_id == convocation_id)
        ).scalar_one()
        assert referencias == 0, "la referencia a la convocatoria sí cascadea"
        assert session.execute(select(func.count()).select_from(OppositionRecord)).scalar_one() == 3


def test_si_el_fixture_cambia_la_siembra_lo_actualiza(
    seeded_settings: Settings, session_factory, profiles
) -> None:
    tai = next(profile for profile in profiles if profile.convocation.code == "tai-age-2025")
    otro = next(
        profile for profile in profiles if profile.convocation.code == "gc-cabos-guardias-2026"
    )
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
                CurriculumNodeRecord.curriculum_version_id == _version_of(session, convocation.id),
                CurriculumNodeRecord.path == original.path,
            )
        ).scalar_one()
        assert row.title == "Título corregido en el fixture"


def test_las_rutas_del_programa_sembrado_son_unicas_en_su_version(
    seeded_settings: Settings, session_factory
) -> None:
    """La ruta identifica un nodo **dentro de su versión de temario**, no en toda la base.

    Dos convocatorias pueden numerar sus temas igual: Guardia Civil y Celador cuelgan sus temas de
    la raíz con las rutas «1», «2», …. La restricción real es la de la base
    (`uq_curriculum_node_path`: versión + ruta), así que la prueba comprueba eso y no más.
    """
    with session_factory() as session:
        rows = session.execute(select(CurriculumNodeRecord)).scalars().all()

    por_version: dict[str, list[str]] = defaultdict(list)
    for row in rows:
        por_version[row.curriculum_version_id].append(row.path)

    assert len(por_version) == 3
    for version_id, paths in por_version.items():
        assert len(paths) == len(set(paths)), f"rutas repetidas en {version_id}"
    assert len(rows) == 37 + 198 + 16


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
                CurriculumNodeRecord.curriculum_version_id == _version_of(session, convocation.id),
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
    otro = next(profile for profile in profiles if profile.convocation.code == "tai-age-2025")

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
                    CurriculumNodeRecord.curriculum_version_id
                    == _version_of(session, convocation.id)
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


def test_la_siembra_da_a_cada_convocatoria_su_programa_publicado(
    seeded_settings: Settings, session_factory
) -> None:
    """El programa deja de colgar de la convocatoria: cuelga de una versión de temario.

    `ESPECIFICACION.md` §5 y §6: cada convocatoria que publica temario conserva su árbol en una
    `curriculum_versions` de tipo `published`, con sus `id` intactos y una referencia `official`.
    La siembra tiene que crear ese envoltorio de forma idempotente, igual que la migración lo hizo
    con los datos que ya existían: si no, una instalación nueva (migrar y sembrar) perdería la
    referencia que enlaza convocatoria y programa.
    """

    with session_factory() as session:
        filas = session.execute(
            text(
                "SELECT c.code, c.kind, v.code, v.status, v.version_no, r.role, "
                "r.convocation_version_id, count(n.id) "
                "FROM curricula c "
                "JOIN curriculum_versions v ON v.curriculum_id = c.id "
                "JOIN convocation_curriculum_refs r ON r.curriculum_version_id = v.id "
                "LEFT JOIN curriculum_nodes n ON n.curriculum_version_id = v.id "
                "WHERE c.kind = 'published' "
                "GROUP BY c.code, c.kind, v.code, v.status, v.version_no, r.role, "
                "r.convocation_version_id ORDER BY c.code"
            )
        ).all()
        sin_version = session.execute(
            text("SELECT count(*) FROM curriculum_nodes WHERE curriculum_version_id IS NULL")
        ).scalar_one()
        origenes = (
            session.execute(text("SELECT DISTINCT origin_kind FROM curriculum_nodes"))
            .scalars()
            .all()
        )

    assert sin_version == 0, "ningún nodo sembrado puede quedarse sin versión de temario"
    assert [fila[0] for fila in filas] == [
        "celador-sacyl-2022-programa",
        "gc-cabos-guardias-2026-programa",
        "tai-age-2025-programa",
    ]
    assert {fila[1] for fila in filas} == {"published"}
    assert {fila[3] for fila in filas} == {"active"}
    assert {int(fila[4]) for fila in filas} == {1}
    assert {fila[5] for fila in filas} == {"official"}
    assert [int(fila[7]) for fila in filas] == [16, 198, 37]
    assert list(origenes) == ["base"], "lo que publica la convocatoria no es enriquecimiento"


def test_sembrar_dos_veces_no_duplica_el_programa_publicado(
    seeded_settings: Settings, session_factory
) -> None:
    """La segunda siembra no crea otro temario publicado ni otra referencia: es idempotente."""

    second = seed_official_profiles(seeded_settings)

    assert second.created == 0
    assert second.updated == 0
    assert second.changed is False

    with session_factory() as session:
        publicados = session.execute(
            text("SELECT count(*) FROM curricula WHERE kind = 'published'")
        ).scalar_one()
        versiones = session.execute(
            text(
                "SELECT count(*) FROM curriculum_versions v "
                "JOIN curricula c ON c.id = v.curriculum_id WHERE c.kind = 'published'"
            )
        ).scalar_one()
        referencias = session.execute(
            text("SELECT count(*) FROM convocation_curriculum_refs")
        ).scalar_one()
    assert publicados == 3
    assert versiones == 3, "una versión publicada por convocatoria con programa"
    assert referencias == 3, "una referencia official por convocatoria con programa"


def test_una_convocatoria_sin_programa_publicado_devuelve_arbol_vacio(
    seeded_settings: Settings, session_factory
) -> None:
    """Una convocatoria que no publica temario existe, pero su árbol está vacío (no es 404/500).

    Antes de `0021` el árbol vacío salía solo porque no había nodos de esa convocatoria; ahora hay
    que resolver la referencia `official` y **no** confundir «no publica programa» con «no existe».
    Es el camino que sigue Guardia Civil y Celador hasta que decidan referenciar el común.
    """
    with session_factory() as session:
        oposicion = session.execute(
            select(OppositionRecord).where(OppositionRecord.code == "tai-age")
        ).scalar_one()
        convocatoria = ConvocationVersionRecord(
            id=str(uuid4()),
            opposition_id=oposicion.id,
            code="tai-age-2026-sin-programa",
            title="Convocatoria sin programa publicado",
            official_url="https://www.boe.es/",
            published_at=datetime(2026, 1, 15).date(),
            exam_date=None,
            status=ConvocationStatus.DRAFT.value,
            source_reference=None,
            supersedes_id=None,
            created_at=NOW,
            updated_at=NOW,
        )
        session.add(convocatoria)
        session.commit()
        convocatoria_id = convocatoria.id

        vista = SqlAlchemyProfileRepository(session_factory).get_curriculum(convocatoria_id)

    assert vista is not None, "la convocatoria existe aunque no publique temario"
    assert vista.nodes == (), "sin programa publicado no hay árbol que enseñar"
    assert vista.counts == {node_type.value: 0 for node_type in NodeType}


def test_la_ficha_de_un_nodo_del_temario_comun_queda_para_la_api_del_temario(
    seeded_settings: Settings, session_factory
) -> None:
    """Un nodo común no tiene convocatoria: devolver `None` es la decisión D-008, no un fallo.

    `NodeDetail` exige datos de la convocatoria (código, título, URL, fecha). Mientras la ficha del
    temario común no exista (B-004), inventar una convocatoria o devolver campos vacíos sería mentir
    en el contrato; por eso se devuelve «no existe» y B-004 sustituirá este retorno y esta prueba.
    """
    with session_factory() as session:
        version = session.execute(
            select(CurriculumVersionRecord).where(
                CurriculumVersionRecord.code == "informatica-c1-v1"
            )
        ).scalar_one()
        session.add(
            CurriculumNodeRecord(
                id="nodo-comun",
                curriculum_version_id=version.id,
                parent_id=None,
                node_type="topic",
                official_code="1",
                title="Tema 1",
                position=1,
                path="1",
                depth=0,
                origin_kind="base",
                origin_convocation_version_id=None,
            )
        )
        session.commit()

        assert SqlAlchemyProfileRepository(session_factory).get_node("nodo-comun") is None


def test_la_siembra_no_reactiva_un_programa_publicado_sustituido(
    seeded_settings: Settings, session_factory, profiles
) -> None:
    """Una v1 `superseded` no se revive al sembrar: la edición vigente la decide la publicación.

    Si el programa publicado recibe una edición nueva, la v1 queda `superseded` y la v2 `active`.
    Volver a poner la v1 `active` desde la siembra chocaría con
    `uq_curriculum_version_single_active` o, peor, resucitaría en silencio una versión retirada. La
    siembra avisa y no escribe.
    """
    tai = next(profile for profile in profiles if profile.convocation.code == "tai-age-2025")

    with session_factory() as session:
        version = session.execute(
            select(CurriculumVersionRecord).where(
                CurriculumVersionRecord.code == "tai-age-2025-programa-v1"
            )
        ).scalar_one()
        version.status = "superseded"
        session.add(
            CurriculumVersionRecord(
                id=str(uuid4()),
                curriculum_id=version.curriculum_id,
                version_no=2,
                code="tai-age-2025-programa-v2",
                title="Programa revisado",
                status="active",
                source_reference=None,
                supersedes_id=version.id,
                created_at=NOW,
                updated_at=NOW,
            )
        )
        session.commit()

        service = ProfilesService(SqlAlchemyProfileRepository(session_factory), SystemClock())
        with pytest.raises(InvariantViolationError, match="no la reactiva"):
            service.seed((tai,))

        estados = {
            str(code): str(estado)
            for code, estado in session.execute(
                select(CurriculumVersionRecord.code, CurriculumVersionRecord.status)
            ).all()
            if str(code).startswith("tai-age-2025-programa")
        }

    assert estados == {
        "tai-age-2025-programa-v1": "superseded",
        "tai-age-2025-programa-v2": "active",
    }, "la siembra no puede cambiar qué edición está vigente"


def _count(session, model, convocation_id: str) -> int:
    """Cuenta partes o reglas de examen de una convocatoria (siguen colgando de ella)."""
    return session.execute(
        select(func.count())
        .select_from(model)
        .where(model.convocation_version_id == convocation_id)
    ).scalar_one()


def _count_nodes(session, version_id: str) -> int:
    """Cuenta los nodos de una versión de temario (el programa publicado)."""
    return session.execute(
        select(func.count())
        .select_from(CurriculumNodeRecord)
        .where(CurriculumNodeRecord.curriculum_version_id == version_id)
    ).scalar_one()
