"""Pruebas de integración de la API de perfiles (S01)."""

from __future__ import annotations

from datetime import date

from fastapi.testclient import TestClient

from opofuente.api.errors import PROBLEM_MEDIA_TYPE
from opofuente.application.profiles_service import ProfilesService
from opofuente.config import Settings
from opofuente.domain.profiles import (
    Convocation,
    ConvocationStatus,
    CurriculumNode,
    ExamPart,
    NodeType,
    Opposition,
    PartFormat,
    PartKind,
    Profile,
)
from opofuente.infrastructure.clock import SystemClock
from opofuente.infrastructure.db import build_engine, build_session_factory
from opofuente.infrastructure.profile_repository import SqlAlchemyProfileRepository

TAI = "tai-age"
GC = "gc-cabos-guardias"
CELADOR = "celador-sacyl"

PRUEBA = "prueba-orden"
PRUEBA_CONVOCATORIA = "prueba-orden-2026"


def _opposition_id(client: TestClient, code: str) -> str:
    oppositions = client.get("/api/v1/oppositions").json()
    return next(item["id"] for item in oppositions if item["code"] == code)


def _convocation(client: TestClient, opposition_code: str, convocation_code: str) -> dict:
    """Una convocatoria concreta de una oposición, por su código.

    Celador tiene dos convocatorias publicadas, así que «la primera de la lista» ya no identifica
    ninguna: las pruebas que quieren la de acceso libre lo dicen por su código.
    """
    oposicion_id = _opposition_id(client, opposition_code)
    filas = client.get(f"/api/v1/oppositions/{oposicion_id}/convocations").json()
    return next(row for row in filas if row["code"] == convocation_code)


def test_lista_de_oposiciones_con_su_convocatoria_activa(seeded_client: TestClient) -> None:
    response = seeded_client.get("/api/v1/oppositions")
    assert response.status_code == 200
    oppositions = response.json()
    assert {item["code"] for item in oppositions} == {TAI, GC, CELADOR}

    tai = next(item for item in oppositions if item["code"] == TAI)
    assert tai["active"] is True
    assert tai["active_convocation"]["code"] == "tai-age-2025"
    assert tai["active_convocation"]["published_at"] == "2025-12-22"
    assert tai["active_convocation"]["status"] == "active"


def test_detalle_de_oposicion_con_sus_convocatorias(seeded_client: TestClient) -> None:
    oposicion_id = _opposition_id(seeded_client, GC)
    response = seeded_client.get(f"/api/v1/oppositions/{oposicion_id}")
    assert response.status_code == 200
    body = response.json()
    assert body["opposition"]["code"] == GC
    assert [row["code"] for row in body["convocations"]] == ["gc-cabos-guardias-2026"]
    convocatoria = body["convocations"][0]
    assert (
        convocatoria["official_url"] == "https://www.boe.es/diario_boe/txt.php?id=BOE-A-2026-9982"
    )
    assert convocatoria["exam_date"] is None


def test_convocatoria_de_una_oposicion_inexistente_devuelve_404(seeded_client: TestClient) -> None:
    response = seeded_client.get("/api/v1/oppositions/no-existe/convocations")
    assert response.status_code == 404
    assert response.headers["content-type"].startswith(PROBLEM_MEDIA_TYPE)
    assert response.json()["code"] == "not_found"


def test_detalle_de_convocatoria_con_partes_y_reglas(seeded_client: TestClient) -> None:
    oposicion_id = _opposition_id(seeded_client, TAI)
    convocatoria = seeded_client.get(f"/api/v1/oppositions/{oposicion_id}/convocations").json()[0]
    response = seeded_client.get(f"/api/v1/convocations/{convocatoria['id']}")
    assert response.status_code == 200
    body = response.json()

    assert body["source_reference"] == "BOE-A-2025-26262 · ANEXO V"
    assert body["opposition_code"] == TAI
    partes = {part["code"]: part for part in body["parts"]}
    assert partes["ejercicio_unico"]["time_minutes"] == 120
    assert partes["primera_parte"]["ordinary_items"] == 80
    assert partes["primera_parte"]["options_per_question"] is None
    # Toda regla viaja con su cita.
    assert all(rule["evidence_quote"] for rule in body["rules"])
    assert "official_scaled_score_requires_published_criteria" in {
        rule["code"] for rule in body["rules"]
    }


def test_programa_de_tai_tiene_cuatro_bloques_treinta_y_tres_temas_y_sus_epigrafes(
    seeded_client: TestClient,
) -> None:
    oposicion_id = _opposition_id(seeded_client, TAI)
    convocatoria = seeded_client.get(f"/api/v1/oppositions/{oposicion_id}/convocations").json()[0]
    response = seeded_client.get(f"/api/v1/convocations/{convocatoria['id']}/curriculum")
    assert response.status_code == 200
    body = response.json()

    assert body["counts"] == {"block": 4, "topic": 33, "epigraph": 134}
    assert len(body["nodes"]) == 4
    temas = [tema for bloque in body["nodes"] for tema in bloque["children"]]
    assert len(temas) == 33
    assert body["nodes"][0]["official_code"] == "I"
    assert temas[0]["path"] == "I.1"
    # Los epígrafes llegan colgando de su tema, con su ruta y su nivel, y en orden.
    epigrafes = [epigrafe for tema in temas for epigrafe in tema["children"]]
    assert len(epigrafes) == 134
    assert all(epigrafe["node_type"] == "epigraph" for epigrafe in epigrafes)
    assert all(epigrafe["depth"] == 2 for epigrafe in epigrafes)
    assert [epigrafe["path"] for epigrafe in temas[0]["children"]] == [
        "I.1.1",
        "I.1.2",
        "I.1.3",
        "I.1.4",
    ]
    # `IV.10` va después de `IV.9` y sus epígrafes, en orden numérico: `IV.10.3` antes de `IV.10.4`.
    iv = body["nodes"][3]
    assert [tema["path"] for tema in iv["children"]][-2:] == ["IV.9", "IV.10"]
    tema_iv10 = next(tema for tema in iv["children"] if tema["path"] == "IV.10")
    assert [epigrafe["path"] for epigrafe in tema_iv10["children"]] == [
        f"IV.10.{numero}" for numero in range(1, 6)
    ]
    # `.NET` entero: la partición no parte el punto que va pegado a la palabra.
    iii = body["nodes"][2]
    tema_iii5 = next(tema for tema in iii["children"] if tema["path"] == "III.5")
    assert tema_iii5["children"][0]["title"] == (
        "Arquitectura Java EE/Jakarta EE y plataforma.NET: componentes, persistencia y seguridad."
    )


def test_programa_de_guardia_civil_tiene_veinticinco_temas(seeded_client: TestClient) -> None:
    oposicion_id = _opposition_id(seeded_client, GC)
    convocatoria = seeded_client.get(f"/api/v1/oppositions/{oposicion_id}/convocations").json()[0]
    response = seeded_client.get(f"/api/v1/convocations/{convocatoria['id']}/curriculum")
    body = response.json()

    assert body["counts"]["topic"] == 25
    assert len(body["nodes"]) == 25
    assert body["nodes"][0]["title"] == "DERECHOS HUMANOS"
    assert body["nodes"][0]["children"], "cada tema debe traer sus bloques"
    primer_bloque = body["nodes"][0]["children"][0]
    assert primer_bloque["children"], "cada bloque debe traer sus epígrafes"


def test_programa_de_celador_tiene_dieciseis_temas_sin_bloques(seeded_client: TestClient) -> None:
    convocatoria = _convocation(seeded_client, CELADOR, "celador-sacyl-2022")
    assert convocatoria["exam_date"] == "2023-11-12"

    response = seeded_client.get(f"/api/v1/convocations/{convocatoria['id']}/curriculum")
    assert response.status_code == 200
    body = response.json()
    assert body["counts"] == {"block": 0, "topic": 16, "epigraph": 0}
    assert len(body["nodes"]) == 16
    assert body["nodes"][0]["official_code"] == "1"
    assert body["nodes"][0]["title"].startswith("Estructura de la Consejería de Sanidad.")
    assert all(not node["children"] for node in body["nodes"])


def _tema(path: str, *, position: int) -> CurriculumNode:
    return CurriculumNode(
        node_type=NodeType.TOPIC,
        official_code=path.split(".")[-1],
        title=f"Tema {path}",
        position=position,
        path=path,
        depth=1,
    )


def _bloque(code: str, *, position: int, children: tuple[CurriculumNode, ...]) -> CurriculumNode:
    return CurriculumNode(
        node_type=NodeType.BLOCK,
        official_code=code,
        title=f"Bloque {code}",
        position=position,
        path=code,
        depth=0,
        children=children,
    )


def _perfil_de_prueba() -> Profile:
    """Un programa con los temas **numerados en el orden del texto de la ruta**.

    `IV.1` es la fila 1, `IV.10` la 2 y `IV.2` la 3: exactamente lo que sale de un generador que
    recorre la fuente y numera lo que encuentra. Las posiciones son consecutivas —el programa es
    válido— y el número oficial del tema solo está en la ruta.
    """
    return Profile(
        opposition=Opposition(code=PRUEBA, name="Oposición de prueba del orden"),
        convocation=Convocation(
            code=PRUEBA_CONVOCATORIA,
            title="Convocatoria de prueba del orden del programa",
            official_url="https://example.invalid/convocatoria-de-prueba",
            published_at=date(2026, 1, 2),
            status=ConvocationStatus.ACTIVE,
        ),
        curriculum=(
            _bloque("I", position=1, children=(_tema("I.1", position=1),)),
            _bloque(
                "IV",
                position=2,
                children=(
                    _tema("IV.1", position=1),
                    _tema("IV.10", position=2),
                    _tema("IV.2", position=3),
                ),
            ),
        ),
        parts=(
            ExamPart(
                code="unico",
                name="Ejercicio único",
                kind=PartKind.TEST,
                format=PartFormat.SINGLE_CHOICE,
                position=1,
                ordinary_items=10,
                evidence_quote="cita de la convocatoria de prueba",
            ),
        ),
        rules=(),
    )


def _sembrar_programa_de_prueba(settings: Settings) -> None:
    engine = build_engine(settings.data_paths.database)
    try:
        repositorio = SqlAlchemyProfileRepository(build_session_factory(engine))
        ProfilesService(repositorio, SystemClock()).seed([_perfil_de_prueba()])
    finally:
        engine.dispose()


def test_el_programa_sale_en_orden_numerico_aunque_la_fila_no_lo_traiga(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """`IV.1`, `IV.2`, `IV.10` — y `I.1` antes que `I.2`—, no `IV.1, IV.10, IV.2`.

    El programa sembrado tiene las posiciones en el orden del **texto** de la ruta (`IV.1` = 1,
    `IV.10` = 2, `IV.2` = 3), que es lo que hoy decide el orden: la pantalla enseñaba `IV.10` justo
    detrás de `IV.1`. El orden tiene que salir del número del bloque y del tema que lleva la ruta.
    """
    _sembrar_programa_de_prueba(seeded_settings)
    convocatoria = _convocation(seeded_client, PRUEBA, PRUEBA_CONVOCATORIA)

    body = seeded_client.get(f"/api/v1/convocations/{convocatoria['id']}/curriculum").json()

    assert [bloque["path"] for bloque in body["nodes"]] == ["I", "IV"]
    assert [tema["path"] for tema in body["nodes"][0]["children"]] == ["I.1"]
    assert [tema["path"] for tema in body["nodes"][1]["children"]] == ["IV.1", "IV.2", "IV.10"]
    # El código oficial del tema es el número que se lee: 1, 2 y 10, en ese orden.
    assert [tema["official_code"] for tema in body["nodes"][1]["children"]] == ["1", "2", "10"]


def test_el_programa_real_de_tai_termina_en_iv_diez(seeded_client: TestClient) -> None:
    """El programa oficial entero, en orden, con `IV.10` al final del bloque IV."""
    oposicion_id = _opposition_id(seeded_client, TAI)
    convocatoria = seeded_client.get(f"/api/v1/oppositions/{oposicion_id}/convocations").json()[0]
    body = seeded_client.get(f"/api/v1/convocations/{convocatoria['id']}/curriculum").json()

    assert [bloque["official_code"] for bloque in body["nodes"]] == ["I", "II", "III", "IV"]
    for bloque in body["nodes"]:
        numeros = [int(tema["official_code"]) for tema in bloque["children"]]
        assert numeros == sorted(numeros), f"el bloque {bloque['path']} no va en orden numérico"
    assert [tema["path"] for tema in body["nodes"][0]["children"]][:2] == ["I.1", "I.2"]
    assert [tema["path"] for tema in body["nodes"][3]["children"]][-2:] == ["IV.9", "IV.10"]


def test_una_oposicion_puede_tener_dos_convocatorias_con_programas_distintos(
    seeded_client: TestClient,
) -> None:
    """Celador tiene dos: la de acceso libre de 2022 y la de estabilización, y no dicen lo mismo."""
    oposicion_id = _opposition_id(seeded_client, CELADOR)
    filas = seeded_client.get(f"/api/v1/oppositions/{oposicion_id}/convocations").json()
    assert [row["code"] for row in filas] == [
        "celador-sacyl-estabilizacion-2022",
        "celador-sacyl-2022",
    ]
    estados = {row["code"]: row["status"] for row in filas}
    assert estados == {
        "celador-sacyl-estabilizacion-2022": "available",
        "celador-sacyl-2022": "active",
    }
    # La vigente es la ordinaria: la de estabilización está publicada y disponible, pero no es la
    # que la aplicación usa para trabajar mientras su proceso siga sin ejercicio.
    detalle = seeded_client.get(f"/api/v1/oppositions/{oposicion_id}").json()
    assert detalle["opposition"]["active_convocation"]["code"] == "celador-sacyl-2022"

    nueva = seeded_client.get(f"/api/v1/convocations/{filas[0]['id']}/curriculum").json()
    vieja = seeded_client.get(f"/api/v1/convocations/{filas[1]['id']}/curriculum").json()
    assert nueva["counts"] == {"block": 2, "topic": 14, "epigraph": 0}
    assert vieja["counts"] == {"block": 0, "topic": 16, "epigraph": 0}


def test_convocatoria_de_celador_sirve_su_ejercicio_y_sus_reglas(seeded_client: TestClient) -> None:
    convocatoria = _convocation(seeded_client, CELADOR, "celador-sacyl-2022")
    response = seeded_client.get(f"/api/v1/convocations/{convocatoria['id']}")
    assert response.status_code == 200
    body = response.json()

    assert body["source_reference"] == (
        "BOCYL-D-22122022-7 · ANEXO I (descripción del proceso) y ANEXO II (programa)"
    )
    partes = {part["code"]: part for part in body["parts"]}
    ejercicio = partes["ejercicio_unico"]
    assert (ejercicio["ordinary_items"], ejercicio["reserve_items"]) == (70, 7)
    assert ejercicio["options_per_question"] == 4
    assert ejercicio["time_minutes"] == 90
    assert ejercicio["pass_score"] is None
    reglas = {rule["code"]: rule for rule in body["rules"]}
    assert reglas["published_exam_date"]["value_text"] == "2023-11-12"
    assert all(rule["evidence_quote"] for rule in body["rules"])


def test_convocatoria_de_estabilizacion_sirve_su_ejercicio_y_sus_reglas(
    seeded_client: TestClient,
) -> None:
    convocatoria = _convocation(seeded_client, CELADOR, "celador-sacyl-estabilizacion-2022")
    body = seeded_client.get(f"/api/v1/convocations/{convocatoria['id']}").json()

    partes = {part["code"]: part for part in body["parts"]}
    ejercicio = partes["ejercicio_unico"]
    assert (ejercicio["ordinary_items"], ejercicio["reserve_items"]) == (40, 4)
    assert ejercicio["options_per_question"] == 3
    assert ejercicio["time_minutes"] == 60
    assert ejercicio["pass_score"] is None
    assert body["exam_date"] is None
    # Y la nota dice por qué no hay fecha, en lugar de dejar un «no consta» que se lee igual cuando
    # falta el dato que cuando lo dirá otra resolución.
    assert "plazo de solicitudes cerró en enero de 2023" in body["exam_date_note"]
    reglas = {rule["code"]: rule for rule in body["rules"]}
    assert reglas["convoked_places"]["value_text"] == "406"
    assert reglas["wrong_answer_penalty"]["value_text"] == "1/9 del valor de una respuesta correcta"
    assert all(rule["evidence_quote"] for rule in body["rules"])


def test_cambiar_de_convocatoria_deja_la_anterior_disponible(seeded_client: TestClient) -> None:
    """El selector de convocatoria de la interfaz usa esta ruta."""
    oposicion_id = _opposition_id(seeded_client, CELADOR)
    nueva = _convocation(seeded_client, CELADOR, "celador-sacyl-estabilizacion-2022")
    respuesta = seeded_client.post(f"/api/v1/convocations/{nueva['id']}/activate")
    assert respuesta.status_code == 200
    assert respuesta.json()["status"] == "active"

    detalle = seeded_client.get(f"/api/v1/oppositions/{oposicion_id}").json()
    assert (
        detalle["opposition"]["active_convocation"]["code"] == "celador-sacyl-estabilizacion-2022"
    )
    estados = {row["code"]: row["status"] for row in detalle["convocations"]}
    # La ordinaria no queda «superada»: nada la ha reemplazado, sigue publicada y utilizable.
    assert estados["celador-sacyl-2022"] == "available"

    # Se puede volver: la disponible sigue siendo activable y conserva su programa.
    vieja = _convocation(seeded_client, CELADOR, "celador-sacyl-2022")
    vuelta = seeded_client.post(f"/api/v1/convocations/{vieja['id']}/activate")
    assert vuelta.status_code == 200
    assert vuelta.json()["status"] == "active"
    programa = seeded_client.get(f"/api/v1/convocations/{vuelta.json()['id']}/curriculum").json()
    assert programa["counts"]["topic"] == 16
    detalle = seeded_client.get(f"/api/v1/oppositions/{oposicion_id}").json()
    assert detalle["opposition"]["active_convocation"]["code"] == "celador-sacyl-2022"
    assert {row["code"]: row["status"] for row in detalle["convocations"]}[
        "celador-sacyl-estabilizacion-2022"
    ] == "available"


def test_activar_una_convocatoria_inexistente_devuelve_404(seeded_client: TestClient) -> None:
    respuesta = seeded_client.post("/api/v1/convocations/no-existe/activate")
    assert respuesta.status_code == 404
    assert respuesta.headers["content-type"].startswith(PROBLEM_MEDIA_TYPE)
    assert respuesta.json()["code"] == "not_found"


def test_activar_celador_deja_una_convocatoria_con_la_que_trabajar(
    seeded_client: TestClient,
) -> None:
    """Una oposición con dos convocatorias sigue teniendo una vigente al activarse.

    Las pantallas de Programa, Estudio, Repaso y Banco resuelven su convocatoria con
    `active_convocation` de la oposición activa. Si la oposición de Celador no tuviera ninguna
    vigente, activarla dejaría la aplicación sin programa: esta prueba defiende eso.
    """
    oposicion_id = _opposition_id(seeded_client, CELADOR)
    respuesta = seeded_client.post(f"/api/v1/oppositions/{oposicion_id}/activate")
    assert respuesta.status_code == 200
    assert respuesta.json()["active"] is True

    activa = next(
        item for item in seeded_client.get("/api/v1/oppositions").json() if item["active"]
    )
    assert activa["code"] == CELADOR
    assert activa["active_convocation"]["code"] == "celador-sacyl-2022"
    assert activa["active_convocation"]["status"] == "active"

    curriculum = seeded_client.get(
        f"/api/v1/convocations/{activa['active_convocation']['id']}/curriculum"
    )
    assert curriculum.status_code == 200
    assert curriculum.json()["counts"]["topic"] == 16


def test_detalle_de_nodo_con_ancestros_y_procedencia(seeded_client: TestClient) -> None:
    oposicion_id = _opposition_id(seeded_client, TAI)
    convocatoria = seeded_client.get(f"/api/v1/oppositions/{oposicion_id}/convocations").json()[0]
    curriculum = seeded_client.get(f"/api/v1/convocations/{convocatoria['id']}/curriculum").json()
    tema = curriculum["nodes"][0]["children"][0]

    response = seeded_client.get(f"/api/v1/curriculum-nodes/{tema['id']}")
    assert response.status_code == 200
    body = response.json()
    assert body["node"]["path"] == tema["path"]
    assert [ancestor["official_code"] for ancestor in body["ancestors"]] == ["I"]
    assert body["official_url"] == "https://www.boe.es/diario_boe/txt.php?id=BOE-A-2025-26262"
    # La cobertura todavía no se calcula: se declara nula, no cero.
    assert body["coverage"] is None


def test_nodo_inexistente_devuelve_404(seeded_client: TestClient) -> None:
    response = seeded_client.get("/api/v1/curriculum-nodes/no-existe")
    assert response.status_code == 404
    assert response.json()["code"] == "not_found"


def test_activar_una_oposicion_inexistente_devuelve_404(seeded_client: TestClient) -> None:
    response = seeded_client.post("/api/v1/oppositions/no-existe/activate")
    assert response.status_code == 404
    assert response.headers["content-type"].startswith(PROBLEM_MEDIA_TYPE)


def test_escritura_desde_un_origen_ajeno_se_rechaza(seeded_client: TestClient) -> None:
    """La primera ruta de escritura del proyecto pasa por la comprobación de Origin."""
    oposicion_id = _opposition_id(seeded_client, GC)
    response = seeded_client.post(
        f"/api/v1/oppositions/{oposicion_id}/activate",
        headers={"Origin": "http://malicioso.example"},
    )
    assert response.status_code == 403
    body = response.json()
    assert body["code"] == "forbidden_origin"
    assert response.headers["content-type"].startswith(PROBLEM_MEDIA_TYPE)


def test_activar_desde_el_origen_del_frontend_funciona(seeded_client: TestClient) -> None:
    oposicion_id = _opposition_id(seeded_client, GC)
    response = seeded_client.post(
        f"/api/v1/oppositions/{oposicion_id}/activate",
        headers={"Origin": "http://127.0.0.1:5173"},
    )
    assert response.status_code == 200


def test_la_api_sin_sembrar_no_inventa_perfiles(client: TestClient) -> None:
    """Con la base migrada pero sin sembrar, la lista está vacía, no con datos falsos."""
    response = client.get("/api/v1/oppositions")
    assert response.status_code == 200
    assert response.json() == []
