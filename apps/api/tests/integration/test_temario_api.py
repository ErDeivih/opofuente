"""API del temario común: índice, particularidades, «en qué convocatorias aparece» y avance (B-004).

Se siembran los perfiles y el temario común y se comprueba por HTTP lo que el alumno necesita: el
árbol del común, el temario efectivo de una convocatoria (con lo omitido, renombrado y
renumerado), la ficha de un tema con sus convocatorias y la marca de estudiado que alimenta el
avance por bloque.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from opofuente.config import Settings
from opofuente.infrastructure.db import build_engine
from opofuente.main import create_app
from tests.conftest import seed_common_curriculum


def _convocatoria_sin_temario(settings: Settings) -> str:
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.connect() as conexion:
            return str(
                conexion.execute(
                    text(
                        "SELECT id FROM convocation_versions WHERE code = 'gc-cabos-guardias-2026'"
                    )
                ).scalar_one()
            )
    finally:
        engine.dispose()


def _ids(settings: Settings) -> dict[str, str]:
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.connect() as conexion:
            convocatoria = str(
                conexion.execute(
                    text("SELECT id FROM convocation_versions WHERE code = 'tai-age-2025'")
                ).scalar_one()
            )
            version = str(
                conexion.execute(
                    text("SELECT id FROM curriculum_versions WHERE code = 'informatica-c1-v1'")
                ).scalar_one()
            )
            ref = str(
                conexion.execute(
                    text(
                        "SELECT id FROM convocation_curriculum_refs WHERE convocation_version_id "
                        "= :convocatoria AND role = 'primary'"
                    ),
                    {"convocatoria": convocatoria},
                ).scalar_one()
            )
            nodos = {
                str(fila[0]): str(fila[1])
                for fila in conexion.execute(
                    text(
                        "SELECT path, id FROM curriculum_nodes "
                        "WHERE curriculum_version_id = :version"
                    ),
                    {"version": version},
                )
            }
    finally:
        engine.dispose()
    return {"convocatoria": convocatoria, "version": version, "ref": ref, **nodos}


def _ajustes(settings: Settings, ids: dict[str, str]) -> None:
    """Particularidades de ejemplo: I.1 omitido, I.2 renombrado, I.3 renumerado."""
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.begin() as conexion:
            filas = (
                ("aj-1", ids["I.1"], "omitted", None, None, "Las bases no incluyen este tema."),
                (
                    "aj-2",
                    ids["I.2"],
                    "renamed",
                    None,
                    "Las Cortes y el Tribunal Constitucional",
                    "Las bases lo titulan así.",
                ),
                (
                    "aj-3",
                    ids["I.3"],
                    "renumbered",
                    "3 bis",
                    None,
                    "La convocatoria lo renumera.",
                ),
            )
            for identificador, nodo, tipo, codigo, titulo, cita in filas:
                conexion.execute(
                    text(
                        "INSERT INTO convocation_curriculum_adjustments (id, ref_id, "
                        "curriculum_node_id, kind, official_code_override, title_override, "
                        "evidence_quote, created_at, updated_at) VALUES (:id, :ref, :nodo, :tipo, "
                        ":codigo, :titulo, :cita, :ahora, :ahora)"
                    ),
                    {
                        "id": identificador,
                        "ref": ids["ref"],
                        "nodo": nodo,
                        "tipo": tipo,
                        "codigo": codigo,
                        "titulo": titulo,
                        "cita": cita,
                        "ahora": "2026-11-05 10:00:00",
                    },
                )
    finally:
        engine.dispose()


@pytest.fixture
def cliente(seeded_settings: Settings):
    seed_common_curriculum(seeded_settings)
    ids = _ids(seeded_settings)
    _ajustes(seeded_settings, ids)
    app = create_app(seeded_settings)
    with TestClient(app) as test_client:
        yield test_client, seeded_settings, ids


def test_el_indice_del_temario_comun_expone_los_cinco_bloques_y_cuarenta_temas(cliente) -> None:
    test_client, _settings, _ = cliente
    respuesta = test_client.get("/api/v1/curricula", params={"kind": "common"})
    assert respuesta.status_code == 200
    temarios = respuesta.json()
    assert [temario["code"] for temario in temarios] == ["informatica-c1"]
    assert temarios[0]["active_version"]["code"] == "informatica-c1-v1"

    detalle = test_client.get("/api/v1/curricula/informatica-c1")
    assert detalle.status_code == 200
    cuerpo = detalle.json()
    assert cuerpo["counts"] == {"block": 5, "topic": 40, "epigraph": 0}
    assert len(cuerpo["nodes"]) == 5
    assert sum(len(bloque["children"]) for bloque in cuerpo["nodes"]) == 40
    assert [bloque["path"] for bloque in cuerpo["nodes"]] == ["I", "II", "III", "IV", "V"]

    versiones = test_client.get("/api/v1/curricula/informatica-c1/versions")
    assert versiones.status_code == 200
    assert [version["code"] for version in versiones.json()] == ["informatica-c1-v1"]


def test_el_temario_de_la_convocatoria_aplica_sus_particularidades(cliente) -> None:
    test_client, _settings, ids = cliente
    respuesta = test_client.get(f"/api/v1/convocations/{ids['convocatoria']}/temario")
    assert respuesta.status_code == 200
    temario = respuesta.json()

    assert temario["curriculum"]["code"] == "informatica-c1"
    assert temario["omitted_topics"] == 1, "I.1 se omite en esta convocatoria"
    assert temario["counts"]["topic"] == 39
    rutas = {tema["path"]: tema for bloque in temario["nodes"] for tema in bloque["children"]}
    assert "I.1" not in rutas
    assert rutas["I.2"]["title"] == "Las Cortes y el Tribunal Constitucional"
    assert rutas["I.3"]["official_code"] == "3 bis"

    # Una convocatoria sin referencia primary no es estudiable: no hay temario efectivo.
    otra = test_client.get(f"/api/v1/convocations/{_convocatoria_sin_temario(_settings)}/temario")
    assert otra.status_code == 404


def test_las_referencias_de_la_convocatoria_dicen_que_estudia_y_que_publica(cliente) -> None:
    test_client, _settings, ids = cliente
    respuesta = test_client.get(f"/api/v1/convocations/{ids['convocatoria']}/references")
    assert respuesta.status_code == 200
    referencias = respuesta.json()
    por_papel = {referencia["role"]: referencia for referencia in referencias}
    assert por_papel["primary"]["curriculum_code"] == "informatica-c1"
    assert por_papel["primary"]["source_reference"] == "ANEXO V, apartado 3"
    assert por_papel["official"]["curriculum_code"] == "tai-age-2025-programa"


def test_la_ficha_de_un_tema_dice_en_que_convocatorias_aparece(cliente) -> None:
    test_client, _settings, ids = cliente
    detalle = test_client.get(f"/api/v1/curriculum-nodes/{ids['I.2']}")
    assert detalle.status_code == 200
    ficha = detalle.json()
    assert ficha["curriculum"]["kind"] == "common"
    assert ficha["curriculum"]["version_code"] == "informatica-c1-v1"
    assert ficha["convocation"] is None
    assert ficha["studied_at"] is None
    # La ficha trae apuntes reales, no solo el título.
    assert ficha["node"]["description"], "el tema debe llegar con sus apuntes"
    assert [aparicion["convocation_code"] for aparicion in ficha["appears_in"]] == ["tai-age-2025"]
    assert ficha["appears_in"][0]["role"] == "primary"

    # Llegando desde la convocatoria, la ficha trae sus particularidades.
    con_contexto = test_client.get(
        f"/api/v1/curriculum-nodes/{ids['I.2']}",
        params={"convocation_id": ids["convocatoria"]},
    )
    particularidades = con_contexto.json()["particularities"]
    assert [ajuste["kind"] for ajuste in particularidades] == ["renamed"]
    assert particularidades[0]["title_override"] == "Las Cortes y el Tribunal Constitucional"


def test_la_ficha_de_un_nodo_publicado_sigue_resolviendo_su_convocatoria(cliente) -> None:
    test_client, settings, _ = cliente
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.connect() as conexion:
            nodo = str(
                conexion.execute(
                    text(
                        "SELECT n.id FROM curriculum_nodes n JOIN curriculum_versions v ON v.id = "
                        "n.curriculum_version_id WHERE v.code = 'tai-age-2025-programa-v1' AND "
                        "n.path = 'I.1'"
                    )
                ).scalar_one()
            )
    finally:
        engine.dispose()

    ficha = test_client.get(f"/api/v1/curriculum-nodes/{nodo}").json()
    assert ficha["curriculum"]["kind"] == "published"
    assert ficha["convocation"]["code"] == "tai-age-2025"
    assert ficha["appears_in"] == []


def test_marcar_un_tema_como_estudiado_mueve_el_avance(cliente) -> None:
    test_client, _settings, ids = cliente
    inicial = test_client.get("/api/v1/curricula/informatica-c1/progress").json()
    assert inicial["topics_total"] == 40
    assert inicial["topics_studied"] == 0
    assert inicial["percent"] == 0.0

    marca = test_client.post(f"/api/v1/curriculum-nodes/{ids['I.2']}/studied")
    assert marca.status_code == 200
    assert marca.json()["node_id"] == ids["I.2"]

    ficha = test_client.get(f"/api/v1/curriculum-nodes/{ids['I.2']}").json()
    assert ficha["studied_at"] is not None

    avance = test_client.get("/api/v1/curricula/informatica-c1/progress").json()
    assert avance["topics_studied"] == 1
    bloque_i = next(bloque for bloque in avance["blocks"] if bloque["path"] == "I")
    assert (bloque_i["topics_studied"], bloque_i["topics_total"]) == (1, 12)
    assert bloque_i["percent"] == 8.3

    retirada = test_client.delete(f"/api/v1/curriculum-nodes/{ids['I.2']}/studied")
    assert retirada.status_code == 204
    assert (
        test_client.get("/api/v1/curricula/informatica-c1/progress").json()["topics_studied"] == 0
    )


def test_un_temario_o_un_nodo_que_no_existe_da_404(cliente) -> None:
    test_client, _settings, _ = cliente
    assert test_client.get("/api/v1/curricula/no-existe").status_code == 404
    assert test_client.get("/api/v1/curriculum-nodes/no-existe").status_code == 404
    assert test_client.post("/api/v1/curriculum-nodes/no-existe/studied").status_code == 404
