"""Pruebas de integración de las rutas del banco de preguntas (S06) por la API real.

Los criterios de aceptación del slice, por su ruta:

- **una fila inválida no aborta el lote**: el informe la trae con su causa y las buenas entran;
- **sin plantilla, el examen oficial queda sin clave**: activar una clave sin plantilla oficial
  responde **409 con el motivo**;
- **respuesta privada no se convierte en oficial**: lo importado nace privado y con su estado;
- **negaciones se conservan** y **claves conflictivas no se fusionan**: el informe lo dice.

Y desde S12.6, el caso de **1.000 filas** de 07_UI-UX §14: el banco se pagina y todas las preguntas
son alcanzables (la pantalla pide 100 por página, así que el DOM nunca tiene mil filas).
"""

from __future__ import annotations

import json
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

#: Un CSV con la explicación de cada opción en sus propias columnas (S12.7).
CSV_CON_EXPLICACIONES = (
    "stem;option_a;option_b;correct;explanation_a;explanation_b\n"
    "El plazo del caso A es de diez dias;Verdadero;Falso;a;"
    "es la correcta: la ley dice diez dias;la ley no dice veinte\n"
    "El plazo del caso B es de veinte dias;Verdadero;Falso;b;;falso por la misma razon\n"
)


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
    # Criterio del slice: lo importado por aquí es privado; nadie lo declara oficial al importarlo.
    assert all(pregunta["origin_type"] == "private" for pregunta in preguntas["questions"]), (
        "una respuesta privada no se convierte en oficial"
    )


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


def test_un_json_se_importa_por_la_misma_ruta_que_el_csv(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """El asistente del slice S06 es CSV **y** JSON: la misma ruta, el mismo informe.

    Una entrada mala del JSON no aborta el lote, y la respuesta escrita de una opción se resuelve a
    su letra: es lo que hace útil importar un JSON exportado de otra herramienta.
    """
    conjunto = _conjunto(seeded_client)

    informe = _importar(
        seeded_client,
        conjunto["id"],
        kind="json",
        text=(
            '{"model_code": "A", "questions": ['
            '{"stem": "Pregunta buena", "options": ["uno", "dos"], "correct": "dos"},'
            '{"stem": "", "options": ["uno", "dos"]},'
            '{"stem": "Sin opciones", "options": ["solo una"]}'
            "]}"
        ),
    )

    assert informe.status_code == 200, informe.text
    datos = informe.json()
    assert datos["created"] == 1, "las dos preguntas malas no abortan el lote"
    assert [aviso["code"] for aviso in datos["issues"]] == ["no_stem", "few_options"]
    assert datos["model_code_detected"] == "A"

    preguntas = seeded_client.get(f"/api/v1/question-sets/{conjunto['id']}/questions").json()
    assert preguntas["total"] == 1
    assert preguntas["questions"][0]["stem"] == "Pregunta buena"
    assert preguntas["questions"][0]["correct_option_keys"] == ["b"]


def test_un_json_declarado_como_tal_que_no_es_json_no_rompe_nada(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    conjunto = _conjunto(seeded_client)

    informe = _importar(seeded_client, conjunto["id"], kind="json", text="no soy JSON")

    assert informe.status_code == 200, informe.text
    datos = informe.json()
    assert datos["created"] == 0
    assert [aviso["code"] for aviso in datos["issues"]] == ["not_json"]
    assert (
        seeded_client.get(f"/api/v1/question-sets/{conjunto['id']}/questions").json()["total"] == 0
    )


def test_un_json_declara_los_campos_que_no_guarda(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """`tags` y `source` se leen y no se guardan: el informe lo dice en vez de callarlo."""
    conjunto = _conjunto(seeded_client)

    informe = _importar(
        seeded_client,
        conjunto["id"],
        kind="json",
        text='[{"stem": "Pregunta", "options": ["uno", "dos"], "tags": ["t1"], "source": "x"}]',
    )

    assert informe.status_code == 200, informe.text
    assert informe.json()["ignored_columns"] == ["tags", "source"]


def test_un_mapeo_que_no_encaja_con_el_fichero_es_un_422_y_no_un_500(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """Equivocarse de columna es un error de quien importa: se dice con el campo a corregir.

    Antes esto salía como 500 «error interno», que culpaba al programa de una entrada equivocada y
    dejaba la pantalla sin nada que arreglar.
    """
    conjunto = _conjunto(seeded_client)

    respuesta = _importar(
        seeded_client,
        conjunto["id"],
        kind="csv",
        text="enunciado;opcion_1;opcion_2\nuno;dos;tres\n",
        mapping={"stem": "stem", "options": ["option_a", "option_b"]},
    )

    assert respuesta.status_code == 422, respuesta.text
    problema = respuesta.json()
    assert problema["code"] == "mapping_mismatch"
    assert problema["field_errors"][0]["field"] == "mapping.stem"
    assert "stem" in problema["detail"]
    assert (
        seeded_client.get(f"/api/v1/question-sets/{conjunto['id']}/questions").json()["total"] == 0
    )


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


def test_mil_preguntas_se_recorren_enteras_y_el_total_lo_dice_el_servidor(
    seeded_client: TestClient,
) -> None:
    """El caso de 1.000 filas (07_UI-UX §14): la tabla se pagina y no se pierde ninguna.

    Lo que se comprueba no es la velocidad —eso se midió y está en la ficha del slice—, sino que
    **todas** las preguntas son alcanzables: primera página, última página y que entre todas suman
    el total sin repetir ninguna. La pantalla pide 100 por página, así que el navegador nunca tiene
    mil filas en el DOM.
    """
    conjunto = _conjunto(seeded_client)
    filas = [
        {
            "stem": f"Pregunta del supuesto {numero} del caso {numero}",
            "options": ["uno", "dos"],
            "correct": "uno",
        }
        for numero in range(1, 1001)
    ]
    informe = _importar(seeded_client, conjunto["id"], kind="json", text=json.dumps(filas))
    assert informe.status_code == 200, informe.text
    assert informe.json()["created"] == 1000

    identificadores: set[str] = set()
    for offset in range(0, 1000, 100):
        pagina = seeded_client.get(
            "/api/v1/questions",
            params={"set_id": conjunto["id"], "limit": 100, "offset": offset},
        ).json()
        assert pagina["total"] == 1000, "el total lo cuenta el servidor, no la página"
        assert len(pagina["questions"]) == 100, f"la página {offset} viene incompleta"
        identificadores.update(pregunta["id"] for pregunta in pagina["questions"])

    assert len(identificadores) == 1000, (
        "entre todas las páginas están las mil, sin repetir ninguna"
    )


def test_las_explicaciones_por_opcion_entran_al_importar_y_se_leen_y_se_escriben(
    seeded_client: TestClient,
) -> None:
    """S12.7: cada opción puede llevar su explicación, y la ficha las devuelve atadas a su opción.

    El camino entero: un CSV con columnas `explanation_a`/`explanation_b` (por convenio, como
    `option_a`/`option_b`), el informe que dice cuántas entraron, la lectura por la API y la
    escritura de una nueva que **sustituye** a la del mismo hueco en lugar de acumularse.
    """
    conjunto = _conjunto(seeded_client)

    informe = _importar(seeded_client, conjunto["id"], kind="csv", text=CSV_CON_EXPLICACIONES)

    assert informe.status_code == 200, informe.text
    assert informe.json()["created"] == 2
    assert informe.json()["option_explanations"] == 3, "el informe cuenta las que entraron"

    preguntas = seeded_client.get(
        "/api/v1/questions", params={"set_id": conjunto["id"], "limit": 10}
    ).json()["questions"]
    primera = next(pregunta for pregunta in preguntas if pregunta["position"] == 1)
    segunda = next(pregunta for pregunta in preguntas if pregunta["position"] == 2)

    explicaciones = seeded_client.get(f"/api/v1/questions/{primera['id']}/explanations")
    assert explicaciones.status_code == 200, explicaciones.text
    por_opcion = {item["option_stable_key"]: item["text"] for item in explicaciones.json()}
    assert por_opcion == {
        "a": "es la correcta: la ley dice diez dias",
        "b": "la ley no dice veinte",
    }
    assert all(item["origin"] == "private" for item in explicaciones.json())
    assert all(item["status"] == "draft" for item in explicaciones.json())

    # La segunda fila solo traía la explicación de la «b», y llega solo esa.
    solo_una = seeded_client.get(f"/api/v1/questions/{segunda['id']}/explanations").json()
    assert [item["option_stable_key"] for item in solo_una] == ["b"]

    # Se escribe una nueva para la «a»: sustituye la que había, no se acumula.
    escrita = seeded_client.post(
        f"/api/v1/questions/{segunda['id']}/explanations",
        json={"text": "la correcta porque el plazo es de veinte dias", "option_stable_key": "a"},
        headers=ALLOWED_ORIGIN,
    )
    assert escrita.status_code == 201, escrita.text
    assert escrita.json()["option_stable_key"] == "a"
    de_segunda = seeded_client.get(f"/api/v1/questions/{segunda['id']}/explanations").json()
    assert {item["option_stable_key"]: item["text"] for item in de_segunda} == {
        "a": "la correcta porque el plazo es de veinte dias",
        "b": "falso por la misma razon",
    }
    # Y sustituir otra vez deja una sola entrada para esa opción.
    repetida = seeded_client.post(
        f"/api/v1/questions/{segunda['id']}/explanations",
        json={"text": "otra vez, la a es la correcta", "option_stable_key": "a"},
        headers=ALLOWED_ORIGIN,
    )
    assert repetida.status_code == 201, repetida.text
    assert len(seeded_client.get(f"/api/v1/questions/{segunda['id']}/explanations").json()) == 2

    # La explicación de la pregunta entera no lleva opción.
    entera = seeded_client.post(
        f"/api/v1/questions/{segunda['id']}/explanations",
        json={"text": "el plazo lo fija la Ley 39/2015"},
        headers=ALLOWED_ORIGIN,
    )
    assert entera.status_code == 201, entera.text
    assert entera.json()["option_stable_key"] is None
    todas = seeded_client.get(f"/api/v1/questions/{segunda['id']}/explanations").json()
    assert [item["option_stable_key"] for item in todas] == [None, "a", "b"], (
        "la de la pregunta entera va primero"
    )

    # Una opción que la pregunta no tiene es un **422** con el campo que hay que corregir, no una
    # explicación huérfana: la explicación de una opción que no está no explica nada.
    huerfana = seeded_client.post(
        f"/api/v1/questions/{segunda['id']}/explanations",
        json={"text": "esto no explica nada", "option_stable_key": "z"},
        headers=ALLOWED_ORIGIN,
    )
    assert huerfana.status_code == 422, huerfana.text
    assert huerfana.json()["code"] == "invalid_answer"
    assert huerfana.json()["field_errors"][0]["field"] == "option_stable_key"

    assert seeded_client.get("/api/v1/questions/no-existe/explanations").status_code == 404
    vacio = seeded_client.post(
        "/api/v1/questions/no-existe/explanations",
        json={"text": "x"},
        headers=ALLOWED_ORIGIN,
    )
    assert vacio.status_code == 404


def test_una_pregunta_corregida_no_cuenta_dos_veces(seeded_client: TestClient) -> None:
    """DEBT-025: la versión sustituida se conserva para poder leerla, pero no es una pregunta.

    Corregir una pregunta deja la anterior en la base con su estado `superseded`. Si esa versión
    contara como pregunta del conjunto, un examen oficial de 70 pasaría a tener 71, el banco
    enseñaría el enunciado viejo y una sesión nueva podría componerse con él. Lo que se comprueba
    aquí es el recorrido entero: el conjunto, el banco y la composición de una sesión.
    """
    conjunto = _conjunto(seeded_client)
    _importar(seeded_client, conjunto["id"], kind="questions", text=TEXTO)
    antes = seeded_client.get(f"/api/v1/question-sets/{conjunto['id']}").json()
    pregunta = seeded_client.get("/api/v1/questions", params={"set_id": conjunto["id"]}).json()[
        "questions"
    ][0]
    assert antes["question_count"] == 2

    correccion = seeded_client.post(
        f"/api/v1/questions/{pregunta['id']}/local-corrections",
        json={"note": "El plazo eran quince dias, no diez"},
        headers=ALLOWED_ORIGIN,
    )
    assert correccion.status_code == 201, correccion.text
    corregida = correccion.json()["question"]

    despues = seeded_client.get(f"/api/v1/question-sets/{conjunto['id']}").json()
    assert despues["question_count"] == 2, "corregir no añade una pregunta al conjunto"
    banco = seeded_client.get(
        "/api/v1/questions", params={"set_id": conjunto["id"], "limit": 200}
    ).json()
    assert banco["total"] == 2
    identificadores = [fila["id"] for fila in banco["questions"]]
    assert corregida["id"] in identificadores, "el banco tiene que enseñar la corregida"
    assert pregunta["id"] not in identificadores, "el banco no puede enseñar la sustituida"

    # La historia no se pierde: la versión sustituida se sigue leyendo, y se puede listar aparte.
    sustituida = seeded_client.get(f"/api/v1/questions/{pregunta['id']}").json()
    assert sustituida["status"] == "superseded"
    assert sustituida["stem"] == pregunta["stem"]
    historicas = seeded_client.get(
        "/api/v1/questions", params={"set_id": conjunto["id"], "status": "superseded"}
    ).json()
    assert [fila["id"] for fila in historicas["questions"]] == [pregunta["id"]]

    # Y la sesión se compone con las dos preguntas que hay, no con tres: el aviso del 409 lo dice.
    activa = next(op for op in seeded_client.get("/api/v1/oppositions").json() if op["active"])
    claves = seeded_client.get(f"/api/v1/question-sets/{conjunto['id']}/answer-keys").json()
    activada = seeded_client.post(
        f"/api/v1/question-sets/{conjunto['id']}/answer-keys/{claves[0]['id']}/activate",
        headers=ALLOWED_ORIGIN,
    )
    assert activada.status_code == 200, activada.text
    sesion = seeded_client.post(
        "/api/v1/study-sessions",
        json={
            "opposition_id": activa["id"],
            "mode": "practice",
            "sources": [
                {
                    "question_set_id": conjunto["id"],
                    "part_code": "primera_parte",
                    "count": 3,
                    "include_reserves": False,
                }
            ],
            "convocation_version_id": activa["active_convocation"]["id"],
            "feedback": "immediate",
        },
        headers=ALLOWED_ORIGIN,
    )
    assert sesion.status_code == 409, sesion.text
    assert "tiene 2 preguntas" in sesion.json()["detail"]

    caben = seeded_client.post(
        "/api/v1/study-sessions",
        json={
            "opposition_id": activa["id"],
            "mode": "practice",
            "sources": [
                {
                    "question_set_id": conjunto["id"],
                    "part_code": "primera_parte",
                    "count": 2,
                    "include_reserves": False,
                }
            ],
            "convocation_version_id": activa["active_convocation"]["id"],
            "feedback": "immediate",
        },
        headers=ALLOWED_ORIGIN,
    )
    assert caben.status_code == 201, caben.text
    assert caben.json()["total_questions"] == 2


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


def test_una_plantilla_que_repite_un_numero_no_es_un_500(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """§4.5 del traspaso de octubre de 2026: 500 determinista en 11 de 24 conjuntos.

    Dos líneas con el mismo número apuntaban a la misma pregunta y la plantilla no admite una
    pregunta dos veces: la base lo rechazaba y la API devolvía 500. Ahora se aplica la primera y la
    repetida se informa.
    """
    conjunto = _conjunto(seeded_client)
    _importar(seeded_client, conjunto["id"], kind="questions", text=TEXTO)

    informe = _importar(
        seeded_client, conjunto["id"], kind="answer_key", text="1. b\n1 anulada\n2. a\n"
    )

    assert informe.status_code == 200, informe.text
    datos = informe.json()
    assert datos["key_entries"] == 2
    assert [aviso["code"] for aviso in datos["issues"]] == ["key_position_repeated"]
    assert datos["issues"][0]["line"] == 2


def test_una_plantilla_no_se_aplica_a_ciegas_si_dos_preguntas_comparten_posicion(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """Un conjunto con dos preguntas en la posición 1 no sabe a cuál va «1. b»: se informa.

    Antes la clave caía en cualquiera de las dos, según el orden de la consulta, sin avisar.
    """
    conjunto = _conjunto(seeded_client)
    _importar(seeded_client, conjunto["id"], kind="questions", text=TEXTO)
    _importar(
        seeded_client,
        conjunto["id"],
        kind="questions",
        text="1. Otra pregunta distinta con el mismo numero:\na) uno\nb) dos\n",
    )
    preguntas = seeded_client.get(f"/api/v1/question-sets/{conjunto['id']}/questions").json()
    posiciones = [pregunta["position"] for pregunta in preguntas["questions"]]
    assert posiciones.count(1) == 2, posiciones

    informe = _importar(seeded_client, conjunto["id"], kind="answer_key", text="1. b\n2. a\n")

    assert informe.status_code == 200, informe.text
    datos = informe.json()
    assert datos["key_entries"] == 1, "solo la 2, que no es ambigua"
    assert [aviso["code"] for aviso in datos["issues"]] == ["key_position_ambiguous"]


#: Un examen de dos partes que **numeran desde 1** cada una, como el TAI de 2025.
EXAMEN_POR_PARTES = """PRIMERA PARTE
1. La primera pregunta de la parte uno trata del plazo:
a) uno
b) dos
2. La segunda pregunta de la parte uno trata del silencio:
a) uno
b) dos
SEGUNDA PARTE
1. La primera pregunta de la parte dos trata de redes:
a) uno
b) dos
2. La segunda pregunta de la parte dos trata de bases de datos:
a) uno
b) dos
"""


def test_una_plantilla_de_un_examen_que_reinicia_la_numeracion_se_aplica_en_orden(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """Por número, el «1» es de las dos partes y la plantilla no se podía aplicar (se decía
    `key_position_ambiguous`). En orden encaja uno a uno, así que se aplica entera y bien."""
    conjunto = _conjunto(seeded_client)
    importado = _importar(seeded_client, conjunto["id"], kind="questions", text=EXAMEN_POR_PARTES)
    assert importado.status_code == 200, importado.text
    preguntas = seeded_client.get(f"/api/v1/question-sets/{conjunto['id']}/questions").json()
    assert sorted(p["position"] for p in preguntas["questions"]) == [1, 1, 2, 2]

    informe = _importar(
        seeded_client, conjunto["id"], kind="answer_key", text="1. a\n2. b\n1. b\n2. a\n"
    )

    assert informe.status_code == 200, informe.text
    datos = informe.json()
    assert datos["key_entries"] == 4
    assert datos["issues"] == []
    clave = seeded_client.get(f"/api/v1/question-sets/{conjunto['id']}/answer-keys").json()[-1]
    por_pregunta = {
        entrada["question_version_id"]: entrada["correct_option_keys"]
        for entrada in clave["entries"]
    }
    respuestas = {
        pregunta["stem"].split(" trata ")[0]: por_pregunta[pregunta["id"]]
        for pregunta in preguntas["questions"]
    }
    assert respuestas == {
        "La primera pregunta de la parte uno": ["a"],
        "La segunda pregunta de la parte uno": ["b"],
        "La primera pregunta de la parte dos": ["b"],
        "La segunda pregunta de la parte dos": ["a"],
    }, "cada respuesta en su pregunta, no en la del mismo número de la otra parte"
