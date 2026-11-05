"""Importación de convocatorias C1 que referencian el temario común (B-006).

Se siembran perfiles, temario común y las convocatorias C1, y se comprueba lo que el slice exige:

1. las 12 convocatorias importadas cuelgan de la oposición `informatica-c1` (inactiva), conservan su
   estado de confianza (10 por confirmar y 2 cerradas) y **referencian la versión activa del temario
   común** con papel `primary` y su cita;
2. el TAI 2025 no se duplica: ya estaba sembrado por su perfil y conserva una sola referencia;
3. repetir la siembra no cambia nada;
4. la ficha de un tema del común las enseña en «en qué convocatorias aparece», con su estado.
"""

from __future__ import annotations

import pytest
from sqlalchemy import func, select

from opofuente.config import Settings
from opofuente.infrastructure.db import build_engine, build_session_factory
from opofuente.infrastructure.db_models import (
    ConvocationCurriculumRefRecord,
    ConvocationVersionRecord,
    CurriculumVersionRecord,
    OppositionRecord,
)
from tests.conftest import seed_c1_convocatorias, seed_common_curriculum

CONVOCATORIAS_ESPERADAS = 12


@pytest.fixture
def session_factory(seeded_settings: Settings):
    seed_common_curriculum(seeded_settings)
    primer_informe = seed_c1_convocatorias(seeded_settings)
    engine = build_engine(seeded_settings.data_paths.database)
    try:
        sesiones = build_session_factory(engine)
        yield sesiones, primer_informe, seeded_settings
    finally:
        engine.dispose()


def test_la_siembra_importa_doce_convocatorias_y_referencia_el_temario_comun(
    session_factory,
) -> None:
    sesiones, primer_informe, _settings = session_factory

    assert primer_informe.imported == CONVOCATORIAS_ESPERADAS
    assert primer_informe.unverified == 10, "los listados del agregador quedan por confirmar"
    assert primer_informe.discarded == 21, "el inventario deja constancia de lo descartado"

    with sesiones() as session:
        oposicion = session.execute(
            select(OppositionRecord).where(OppositionRecord.code == "informatica-c1")
        ).scalar_one()
        convocatorias = (
            session.execute(
                select(ConvocationVersionRecord).where(
                    ConvocationVersionRecord.opposition_id == oposicion.id
                )
            )
            .scalars()
            .all()
        )
        version_comun = session.execute(
            select(CurriculumVersionRecord).where(
                CurriculumVersionRecord.code == "informatica-c1-v1"
            )
        ).scalar_one()
        primarias = (
            session.execute(
                select(ConvocationCurriculumRefRecord).where(
                    ConvocationCurriculumRefRecord.role == "primary"
                )
            )
            .scalars()
            .all()
        )
        tai = session.execute(
            select(ConvocationVersionRecord).where(ConvocationVersionRecord.code == "tai-age-2025")
        ).scalar_one()
        refs_tai = session.execute(
            select(func.count())
            .select_from(ConvocationCurriculumRefRecord)
            .where(
                ConvocationCurriculumRefRecord.convocation_version_id == tai.id,
                ConvocationCurriculumRefRecord.role == "primary",
            )
        ).scalar_one()

    assert oposicion.active is False, "la oposición importada no desplaza a la activa"
    assert len(convocatorias) == CONVOCATORIAS_ESPERADAS
    estados = [convocatoria.status for convocatoria in convocatorias]
    assert estados.count("draft") == 10
    assert estados.count("archived") == 2
    por_codigo = {convocatoria.code: convocatoria for convocatoria in convocatorias}
    assert oposicion.code == "informatica-c1"
    assert "c1-sacyl-sanidad-cyl-salamanca" in por_codigo
    assert all(convocatoria.official_url.startswith("https://") for convocatoria in convocatorias)
    assert all(convocatoria.source_reference for convocatoria in convocatorias)

    # Una referencia primary por convocatoria: 12 importadas + la del TAI + la de los perfiles que
    # tengan programa publicado no cuentan aquí (solo role primary).
    assert len(primarias) == CONVOCATORIAS_ESPERADAS + 1
    assert all(referencia.curriculum_version_id == version_comun.id for referencia in primarias), (
        "todas estudian la versión activa del común"
    )
    assert refs_tai == 1, "el TAI no se duplica al importar el inventario"


def test_repetir_la_siembra_no_cambia_nada(session_factory) -> None:
    _sesiones, _primer, settings = session_factory

    segundo = seed_c1_convocatorias(settings)

    assert segundo.created == 0
    assert segundo.updated == 0
    assert segundo.changed is False
    assert segundo.unchanged > 0


def test_la_ficha_del_tema_las_enseña_con_su_estado(seeded_settings: Settings) -> None:
    """Las convocatorias importadas aparecen en la ficha del tema, marcadas según su confianza."""
    from fastapi.testclient import TestClient

    from opofuente.main import create_app

    seed_common_curriculum(seeded_settings)
    seed_c1_convocatorias(seeded_settings)
    app = create_app(seeded_settings)
    with TestClient(app) as cliente:
        curriculo = cliente.get("/api/v1/curricula/informatica-c1").json()
        tema = curriculo["nodes"][0]["children"][0]
        ficha = cliente.get(f"/api/v1/curriculum-nodes/{tema['id']}").json()

    apariciones = ficha["appears_in"]
    titulos = [aparicion["convocation_title"] for aparicion in apariciones]
    assert len(apariciones) == CONVOCATORIAS_ESPERADAS + 1, "12 importadas + TAI 2025"
    assert any("Sallent" in titulo for titulo in titulos)
    estados = {aparicion["convocation_status"] for aparicion in apariciones}
    assert estados == {"active", "draft", "archived"}
