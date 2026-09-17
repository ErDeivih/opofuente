"""Pruebas de integración de las rutas del banco de preguntas (S06) por la API real.

Los criterios de aceptación del slice, por su ruta:

- **una fila inválida no aborta el lote**: el informe la trae con su causa y las buenas entran;
- **sin plantilla, el examen oficial queda sin clave**: activar una clave sin plantilla oficial
  responde **409 con el motivo**;
- **respuesta privada no se convierte en oficial**: lo importado nace privado y con su estado;
- **negaciones se conservan** y **claves conflictivas no se fusionan**: el informe lo dice.
"""

from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient

from opofuente.config import Settings

ALLOWED_ORIGIN = {"Origin": "http://127.0.0.1:5173"}

TEXTO = """1. La Constitucion espanola se aprobo en:
a) 1976
b) 1978
c) 1980
Respuesta correcta: b

2. El plazo de alegaciones es de diez dias habiles.
a) Verdadero
b) Falso
"""

CSV = "stem;option_a;option_b;correct\n;Verdadero;Falso;a\nPregunta buena;uno;dos;b\n"


def _conjunto(
    client: TestClient, *, set_type: str = "private_bank", **extra: Any
) -> dict[str, Any]:
    """Crea un conjunto sobre la oposición que ya trae la siembra de las pruebas."""
    oposiciones = client.get("/api/v1/oppositions").json()
    activa = next(oposicion for oposicion in oposiciones if oposicion["active"])
    respuesta = client.post(
        "/api/v1/question-sets",
        json={
            "title": "Examen de prueba",
            "opposition_id": activa["id"],
            "set_type": set_type,
            **extra,
        },
        headers=ALLOWED_ORIGIN,
    )
    assert respuesta.status_code == 201, respuesta.text
    return respuesta.json()


def _importar(client: TestClient, set_id: str, **cuerpo: Any) -> Any:
    return client.post(f"/api/v1/question-sets/{set_id}/parse", json=cuerpo, headers=ALLOWED_ORIGIN)


def test_crear_listar_y_consultar_un_conjunto(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    creado = _conjunto(seeded_client)
    assert creado["status"] == "draft"
    assert creado["question_count"] == 0

    listado = seeded_client.get("/api/v1/question-sets").json()
    assert listado["total"] == 1
    assert listado["sets"][0]["id"] == creado["id"]

    detalle = seeded_client.get(f"/api/v1/question-sets/{creado['id']}")
    assert detalle.status_code == 200
    assert detalle.json()["title"] == "Examen de prueba"
    assert seeded_client.get("/api/v1/question-sets/no-existe").status_code == 404


def test_un_conjunto_con_tipo_inventado_no_entra(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    respuesta = seeded_client.post(
        "/api/v1/question-sets",
        json={"title": "X", "opposition_id": "op-1", "set_type": "inventado"},
        headers=ALLOWED_ORIGIN,
    )
    assert respuesta.status_code == 422


def test_importar_texto_y_leer_las_preguntas_con_su_clave(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    conjunto = _conjunto(seeded_client)

    informe = _importar(seeded_client, conjunto["id"], kind="questions", text=TEXTO)

    assert informe.status_code == 200, informe.text
    datos = informe.json()
    assert (datos["created"], datos["existing"]) == (2, 0)
    assert datos["key_entries"] == 1, "la clave que venía en el texto se guarda como plantilla"

    preguntas = seeded_client.get("/api/v1/questions", params={"set_id": conjunto["id"]}).json()
    assert preguntas["total"] == 2
    primera = next(p for p in preguntas["questions"] if p["position"] == 1)
    assert [opcion["stable_key"] for opcion in primera["options"]] == ["a", "b", "c"]
    assert primera["correct_option_keys"] == ["b"], "el banco sí enseña la clave"
    assert primera["key_outcome"] == "keyed"

    ficha = seeded_client.get(f"/api/v1/questions/{primera['id']}")
    assert ficha.status_code == 200
    assert ficha.json()["correct_option_keys"] == ["b"]


def test_un_csv_con_filas_malas_las_informa_y_mete_las_buenas(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    conjunto = _conjunto(seeded_client)

    informe = _importar(seeded_client, conjunto["id"], kind="csv", text=CSV)

    assert informe.status_code == 200, informe.text
    datos = informe.json()
    assert datos["created"] == 1, "la fila sin enunciado no aborta el lote"
    assert [fila["cause"] for fila in datos["rejected"]] == ["no_stem"]
    assert datos["rejected"][0]["row_number"] == 2
    assert datos["missing_columns"], "lo que el mapeo pedía y el fichero no trae se declara"


def test_importar_una_plantilla_suelta_avisa_de_lo_que_no_empareja(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    conjunto = _conjunto(seeded_client)
    _importar(seeded_client, conjunto["id"], kind="questions", text=TEXTO)

    informe = _importar(
        seeded_client, conjunto["id"], kind="answer_key", text="1. b\n2. a\n40. c\n"
    )

    assert informe.status_code == 200, informe.text
    datos = informe.json()
    assert datos["key_entries"] == 2
    assert datos["key_id"]
    assert datos["unmatched_positions"] == [40], "lo que no empareja se dice, no se inventa"


def test_una_plantilla_que_no_empareja_con_nada_es_un_conflicto(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    conjunto = _conjunto(seeded_client)

    respuesta = _importar(seeded_client, conjunto["id"], kind="answer_key", text="1. b\n")

    assert respuesta.status_code == 409
    assert respuesta.json()["code"] == "classification_conflict"


def test_activar_claves_por_la_api(seeded_settings: Settings, seeded_client: TestClient) -> None:
    conjunto = _conjunto(seeded_client)
    _importar(seeded_client, conjunto["id"], kind="questions", text=TEXTO)
    _importar(seeded_client, conjunto["id"], kind="answer_key", text="1. b\n2. a\n")

    claves = seeded_client.get(f"/api/v1/question-sets/{conjunto['id']}/answer-keys").json()
    assert len(claves) == 2, "la del texto y la que llegó aparte"
    ultima = claves[-1]

    activada = seeded_client.post(
        f"/api/v1/question-sets/{conjunto['id']}/answer-keys/{ultima['id']}/activate",
        headers=ALLOWED_ORIGIN,
    )

    assert activada.status_code == 200, activada.text
    assert activada.json()["status"] == "active"
    assert activada.json()["approved_at"] is not None, "activar deja la aprobación registrada"
    detalle = seeded_client.get(f"/api/v1/question-sets/{conjunto['id']}").json()
    assert detalle["active_key_id"] == ultima["id"]


def test_una_clave_oficial_sin_plantilla_oficial_responde_409(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    conjunto = _conjunto(seeded_client, set_type="official_exam")
    _importar(seeded_client, conjunto["id"], kind="questions", text=TEXTO)
    clave = _importar(seeded_client, conjunto["id"], kind="answer_key", text="1. b\n2. a\n").json()[
        "key_id"
    ]

    respuesta = seeded_client.post(
        f"/api/v1/question-sets/{conjunto['id']}/answer-keys/{clave}/activate",
        headers=ALLOWED_ORIGIN,
    )

    assert respuesta.status_code == 409, respuesta.text
    assert "plantilla oficial" in respuesta.json()["detail"]
    detalle = seeded_client.get(f"/api/v1/question-sets/{conjunto['id']}").json()
    assert detalle["active_key_id"] is None, "un conflicto no activa nada"


def test_marcar_que_una_clave_sustituye_a_otra(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    conjunto = _conjunto(seeded_client)
    _importar(seeded_client, conjunto["id"], kind="questions", text=TEXTO)
    _importar(seeded_client, conjunto["id"], kind="answer_key", text="1. b\n2. a\n")
    claves = seeded_client.get(f"/api/v1/question-sets/{conjunto['id']}/answer-keys").json()
    primera, segunda = claves[0]["id"], claves[1]["id"]

    respuesta = seeded_client.post(
        f"/api/v1/answer-keys/{segunda}/mark-supersedes",
        json={"superseded_id": primera},
        headers=ALLOWED_ORIGIN,
    )

    assert respuesta.status_code == 200, respuesta.text
    assert respuesta.json()["supersedes_id"] == primera

    inventada = seeded_client.post(
        f"/api/v1/answer-keys/{segunda}/mark-supersedes",
        json={"superseded_id": "no-existe"},
        headers=ALLOWED_ORIGIN,
    )
    assert inventada.status_code == 409


def test_editar_composicion_corregir_con_motivo_y_reportar(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    conjunto = _conjunto(seeded_client)
    _importar(seeded_client, conjunto["id"], kind="questions", text=TEXTO)
    pregunta = seeded_client.get("/api/v1/questions", params={"set_id": conjunto["id"]}).json()[
        "questions"
    ][0]

    editada = seeded_client.patch(
        f"/api/v1/questions/{pregunta['id']}",
        json={"position": 7, "is_reserve": True, "reserve_order": 1},
        headers=ALLOWED_ORIGIN,
    )
    assert editada.status_code == 200, editada.text
    assert editada.json()["position"] == 7
    assert editada.json()["is_reserve"] is True

    correccion = seeded_client.post(
        f"/api/v1/questions/{pregunta['id']}/local-corrections",
        json={"note": "El original decía 1980 por errata de la transcripción"},
        headers=ALLOWED_ORIGIN,
    )

    assert correccion.status_code == 201, correccion.text
    corregida = correccion.json()["question"]
    assert corregida["version_no"] == 2
    assert corregida["supersedes_id"] == pregunta["id"]
    assert "errata" in (corregida["note"] or ""), "el motivo se lee en la pregunta corregida"

    # El original permanece, con su texto y su estado de sustituida.
    original = seeded_client.get(f"/api/v1/questions/{pregunta['id']}").json()
    assert original["status"] == "superseded"
    assert original["stem"] == pregunta["stem"]

    # Sin motivo no hay corrección: cambiar una transcripción oficial se hace diciendo por qué.
    sin_motivo = seeded_client.post(
        f"/api/v1/questions/{pregunta['id']}/local-corrections",
        json={},
        headers=ALLOWED_ORIGIN,
    )
    assert sin_motivo.status_code == 422

    incidencia = seeded_client.post(
        f"/api/v1/questions/{pregunta['id']}/report-issue",
        json={"kind": "ambiguous", "detail": "No queda claro si la B también vale"},
        headers=ALLOWED_ORIGIN,
    )
    assert incidencia.status_code == 201, incidencia.text
    assert incidencia.json()["status"] == "open"
    assert incidencia.json()["kind"] == "ambiguous"

    evidencia = seeded_client.get(f"/api/v1/questions/{pregunta['id']}/evidence")
    assert evidencia.status_code == 200
    assert evidencia.json() == [], "sin evidencia adjunta se dice vacío, no se inventa una cita"

    assert seeded_client.get("/api/v1/questions/no-existe").status_code == 404
    assert (
        seeded_client.post(
            "/api/v1/questions/no-existe/report-issue",
            json={"kind": "typo", "detail": "errata"},
            headers=ALLOWED_ORIGIN,
        ).status_code
        == 404
    )


def test_una_pregunta_que_ya_estaba_con_otra_clave_se_marca_en_el_informe(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """Criterio del slice: dos claves que se contradicen no se fusionan ni se callan."""
    conjunto = _conjunto(seeded_client)
    _importar(
        seeded_client,
        conjunto["id"],
        kind="csv",
        text="stem;option_a;option_b;correct\nEl plazo es de diez dias;Verdadero;Falso;a\n",
    )

    segundo = _importar(
        seeded_client,
        conjunto["id"],
        kind="csv",
        text="stem;option_a;option_b;correct\nEl plazo es de diez dias;Falso;Verdadero;b\n",
    )

    assert segundo.status_code == 200, segundo.text
    datos = segundo.json()
    assert (datos["created"], datos["existing"]) == (0, 1)
    assert datos["keys_in_conflict"] == 1
    pregunta = seeded_client.get("/api/v1/questions", params={"set_id": conjunto["id"]}).json()[
        "questions"
    ][0]
    assert pregunta["status"] == "conflicting"
