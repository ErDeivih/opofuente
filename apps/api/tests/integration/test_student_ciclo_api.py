"""El ciclo de contestar, como **una sola máquina de estados** (§3.2 del encargo F36).

Los defectos 5, 6 y 8 del recorrido son uno: la sesión dice que una pregunta «ya está respondida y
no
se reescribe», y con eso encadena cuatro síntomas que aquí se miden por separado porque cada uno
tiene
su código HTTP y su pantalla:

1. **volver a una pregunta contestada**: la hoja de respuestas del test tiene que poder abrir
   cualquier fila (`GET …/sessions/{id}?position=N`), no solo la primera sin contestar;
2. **cambiar una respuesta**: mientras el test no ha terminado, cambiar de opción **se puede**; el
   código lo dice (200) y la hoja queda con lo nuevo;
3. **contestar dos veces seguidas**: es **idempotente** y nunca un 500. El 500 que midió el
recorrido
   (`UNIQUE constraint failed: attempts.session_question_id`) sale cuando dos peticiones leen antes
   de
   que ninguna escriba, así que se prueba con peticiones de verdad en paralelo;
4. **un fallo interno se lee como lo que es**: el 500 de arriba salía sin cabeceras de CORS y el
   navegador lo contaba como «blocked by CORS policy», que manda a mirar donde no es.

Las cuatro pruebas son de la capa del alumno porque es la que se recorrió, pero la máquina de
estados
es la misma para el runner del panel: la comparte `StudyService.answer`.
"""

from __future__ import annotations

import threading
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any

import pytest
from fastapi.testclient import TestClient

from opofuente.application.study_models import AttemptView
from opofuente.application.study_service import AnswerInput, StudyService
from opofuente.config import Settings
from opofuente.infrastructure.clock import SystemClock
from opofuente.infrastructure.db import build_engine, build_session_factory
from opofuente.infrastructure.profile_repository import SqlAlchemyProfileRepository
from opofuente.infrastructure.question_repository import SqlAlchemyQuestionRepository
from opofuente.infrastructure.study_repository import SqlAlchemyStudyRepository
from opofuente.main import create_app

ALLOWED_ORIGIN = {"Origin": "http://127.0.0.1:5173"}

#: Cuatro preguntas cuya respuesta correcta es la **A**, con su clave en la línea `Respuesta
# correcta`.
TEXTO = "\n".join(
    [
        "1. El plazo del procedimiento administrativo comun es de diez dias habiles.",
        "a) Verdadero",
        "b) Falso",
        "Respuesta correcta: a",
        "2. El Esquema Nacional de Seguridad se regula en el Real Decreto 311/2022.",
        "a) Verdadero",
        "b) Falso",
        "Respuesta correcta: a",
        "3. El modelo TCP/IP tiene cuatro capas.",
        "a) Verdadero",
        "b) Falso",
        "Respuesta correcta: a",
        "4. La sede electronica se regula en la Ley 39/2015.",
        "a) Verdadero",
        "b) Falso",
        "Respuesta correcta: a",
    ]
)


@dataclass
class EnMarcha:
    """Un test del alumno arrancado, con su cliente y sus códigos de tema."""

    client: TestClient
    session_id: str
    total: int


def _aplanar(nodos: list[dict[str, Any]]) -> list[dict[str, Any]]:
    planos: list[dict[str, Any]] = []
    for nodo in nodos:
        planos.append(nodo)
        planos.extend(_aplanar(nodo.get("children", [])))
    return planos


def _cliente(settings: Settings) -> TestClient:
    return TestClient(create_app(Settings(data_dir=settings.data_dir, _env_file=None)))


def _temas(client: TestClient) -> dict[str, dict[str, Any]]:
    oposicion = next(
        op for op in client.get("/api/v1/oppositions").json() if op["code"] == "tai-age"
    )
    programa = client.get(
        f"/api/v1/convocations/{oposicion['active_convocation']['id']}/curriculum"
    ).json()
    return {nodo["path"]: nodo for nodo in _aplanar(programa["nodes"])}


def _conjunto_con_clave(client: TestClient) -> str:
    """Un banco con cuatro preguntas y su plantilla **activa**: sin clave no hay test que corregir.

    La clave se activa por la ruta de verdad: una plantilla en borrador no corrige nada.
    """
    oposicion = next(
        op for op in client.get("/api/v1/oppositions").json() if op["code"] == "tai-age"
    )
    creado = client.post(
        "/api/v1/question-sets",
        json={
            "title": "Ciclo de contestar (prueba)",
            "opposition_id": oposicion["id"],
            "set_type": "private_bank",
            "convocation_version_id": oposicion["active_convocation"]["id"],
        },
        headers=ALLOWED_ORIGIN,
    )
    assert creado.status_code == 201, creado.text
    set_id = str(creado.json()["id"])
    importado = client.post(
        f"/api/v1/question-sets/{set_id}/parse",
        json={"kind": "questions", "text": TEXTO},
        headers=ALLOWED_ORIGIN,
    )
    assert importado.status_code == 200, importado.text
    claves = client.get(f"/api/v1/question-sets/{set_id}/answer-keys").json()
    activada = client.post(
        f"/api/v1/question-sets/{set_id}/answer-keys/{claves[0]['id']}/activate",
        headers=ALLOWED_ORIGIN,
    )
    assert activada.status_code == 200, activada.text
    return set_id


def _montar_test(client: TestClient, *, feedback: str = "immediate", count: int = 4) -> EnMarcha:
    """Un test del alumno de `count` preguntas de IV.1, ya arrancado.

    Se monta por las rutas de verdad —conjunto, importación, clave activa, catalogación en el tema y
    `POST /student/tests`— porque lo que se mide es el ciclo entero, y un doble del servicio no
    diría
    nada del 500 ni de las cabeceras de CORS.
    """
    set_id = _conjunto_con_clave(client)
    temas = _temas(client)
    preguntas = client.get("/api/v1/questions", params={"set_id": set_id}).json()["questions"]
    for pregunta in preguntas:
        asignada = client.post(
            f"/api/v1/questions/{pregunta['id']}/topics",
            json={"curriculum_node_id": temas["IV.1"]["id"]},
            headers=ALLOWED_ORIGIN,
        )
        assert asignada.status_code in (200, 201), asignada.text

    creado = client.post(
        "/api/v1/student/tests",
        json={
            "nodes": ["IV.1"],
            "count": count,
            "filter": "all",
            "feedback": feedback,
        },
        headers=ALLOWED_ORIGIN,
    )
    assert creado.status_code == 201, creado.text
    session_id = str(creado.json()["id"])
    arrancado = client.post(f"/api/v1/student/sessions/{session_id}/start", headers=ALLOWED_ORIGIN)
    assert arrancado.status_code == 200, arrancado.text
    return EnMarcha(client=client, session_id=session_id, total=int(arrancado.json()["total"]))


@pytest.fixture
def en_marcha(seeded_settings: Settings) -> Iterator[EnMarcha]:
    with _cliente(seeded_settings) as client:
        yield _montar_test(client)


def _fila(run: dict[str, Any], posicion: int) -> dict[str, Any]:
    return next(fila for fila in run["sheet"] if fila["position"] == posicion)


# --------------------------------------------------------------- 1. volver a una pregunta
# contestada


def test_leer_una_posicion_concreta_de_la_hoja_devuelve_esa_pregunta(en_marcha: EnMarcha) -> None:
    """La hoja tiene que poder abrir **cualquier** fila, no solo la primera sin contestar.

    Es la mitad del defecto 5 del recorrido: los números de la hoja «parecen botones y no hacen
    nada». Sin esto, la pantalla no tiene a qué llamar cuando se pulsa una fila.
    """
    cliente, sesion = en_marcha.client, en_marcha.session_id
    primera = cliente.get(f"/api/v1/student/sessions/{sesion}").json()
    assert primera["position"] == 1, "un test recién arrancado empieza por la primera"

    cliente.post(
        f"/api/v1/student/sessions/{sesion}/answers",
        json={"position": 1, "chosen": ["a"], "elapsed_ms": 10},
        headers=ALLOWED_ORIGIN,
    )

    # Y ahora la primera ya está contestada: la lectura sin posición salta a la siguiente (es el
    # avance automático de siempre)…
    segunda = cliente.get(f"/api/v1/student/sessions/{sesion}").json()
    assert segunda["position"] == 2

    # …pero se puede volver a la 1 pidiéndola.
    vuelta = cliente.get(f"/api/v1/student/sessions/{sesion}", params={"position": 1})
    assert vuelta.status_code == 200, vuelta.text
    assert vuelta.json()["position"] == 1
    assert vuelta.json()["question"]["position"] == 1

    fuera = cliente.get(f"/api/v1/student/sessions/{sesion}", params={"position": 99})
    assert fuera.status_code == 404, fuera.text


# --------------------------------------------------------------------- 2. cambiar una respuesta


def test_cambiar_una_respuesta_se_puede_mientras_el_test_no_ha_terminado(
    en_marcha: EnMarcha,
) -> None:
    """El defecto 5 medido: cambiar de opción devolvía **409** y la pantalla no cambiaba nada.

    La decisión del §3.2 es que se puede cambiar mientras el test no esté terminado. Se comprueba
    con
    lo que de verdad importa: que la hoja quede con la opción nueva **y** que la corrección se
    rehaga.
    """
    cliente, sesion = en_marcha.client, en_marcha.session_id
    correcta = "a"

    primera = cliente.post(
        f"/api/v1/student/sessions/{sesion}/answers",
        json={"position": 1, "chosen": ["b"], "elapsed_ms": 100},
        headers=ALLOWED_ORIGIN,
    )
    assert primera.status_code == 200, primera.text
    assert primera.json()["question"]["correction"]["outcome"] == "wrong"

    cambiada = cliente.post(
        f"/api/v1/student/sessions/{sesion}/answers",
        json={"position": 1, "chosen": [correcta], "elapsed_ms": 200},
        headers=ALLOWED_ORIGIN,
    )
    assert cambiada.status_code == 200, cambiada.text
    assert cambiada.json()["question"]["correction"]["outcome"] == "correct", (
        "la corrección se rehace con la respuesta nueva"
    )

    # La hoja entera queda con lo nuevo, que es lo que pinta la pantalla.
    run = cliente.get(f"/api/v1/student/sessions/{sesion}", params={"position": 1}).json()
    fila = _fila(run, 1)
    assert fila["chosen"] == [correcta]
    assert fila["outcome"] == "correct"
    assert run["answered"] == 1, "cambiar no contesta una segunda pregunta"


def test_cambiar_la_respuesta_de_un_test_terminado_se_rechaza_con_su_codigo(
    en_marcha: EnMarcha,
) -> None:
    """Lo que **no** cambia: un test terminado tiene las respuestas congeladas.

    Es la otra mitad de la decisión, y se dice con su motivo: el alumno ya vio la corrección y la
    nota
    está calculada, así que reescribir el intento cambiaría un resultado ya cerrado.
    """
    cliente, sesion = en_marcha.client, en_marcha.session_id
    cliente.post(
        f"/api/v1/student/sessions/{sesion}/answers",
        json={"position": 1, "chosen": ["b"], "elapsed_ms": 10},
        headers=ALLOWED_ORIGIN,
    )
    cerrado = cliente.post(f"/api/v1/student/sessions/{sesion}/finish", headers=ALLOWED_ORIGIN)
    assert cerrado.status_code == 200, cerrado.text

    tarde = cliente.post(
        f"/api/v1/student/sessions/{sesion}/answers",
        json={"position": 1, "chosen": ["a"], "elapsed_ms": 10},
        headers=ALLOWED_ORIGIN,
    )
    assert tarde.status_code == 409, tarde.text
    assert tarde.json()["code"] == "attempt_frozen"


# ------------------------------------------------------- 3. contestar dos veces seguidas:
# idempotente


def test_contestar_dos_veces_lo_mismo_devuelve_el_mismo_intento(en_marcha: EnMarcha) -> None:
    """La repetición tranquila ya era idempotente; esto la fija para que no se pierda."""
    cliente, sesion = en_marcha.client, en_marcha.session_id
    cuerpo = {"position": 1, "chosen": ["a"], "elapsed_ms": 10}

    primera = cliente.post(
        f"/api/v1/student/sessions/{sesion}/answers", json=cuerpo, headers=ALLOWED_ORIGIN
    )
    segunda = cliente.post(
        f"/api/v1/student/sessions/{sesion}/answers",
        json=dict(cuerpo, elapsed_ms=9999),
        headers=ALLOWED_ORIGIN,
    )

    assert primera.status_code == 200, primera.text
    assert segunda.status_code == 200, segunda.text
    # `server_now` es el reloj del test en marcha (§3.4, F37): cambia en cada respuesta A PROPOSITO.
    # Lo que esta prueba fija es que la SEGUNDA no cree un intento nuevo. Todo lo demas, igual.
    segunda_cuerpo = segunda.json()
    primera_cuerpo = primera.json()
    segunda_cuerpo["session"].pop("server_now", None)
    primera_cuerpo["session"].pop("server_now", None)
    assert segunda_cuerpo == primera_cuerpo, "la segunda vez devuelve el mismo resultado"


def test_dos_peticiones_a_la_vez_para_la_misma_pregunta_no_revientan(en_marcha: EnMarcha) -> None:
    """El 500 medido: «si se pulsa dos veces deprisa, el servidor revienta».

    Se lanzan **peticiones de verdad en paralelo** —es la única forma de que las dos lean antes de
    que
    ninguna escriba, que es cuando choca la clave única del intento— y se exige que **todas**
    contesten
    lo mismo: la respuesta es idempotente, no una carrera que a veces gana y a veces revienta.

    Esta prueba es una **guarda**, no la reproducción: la ventana real dura milisegundos y con el
    motor de SQLite en serie no siempre se abre, así que sola no demuestra el arreglo. Quien lo fija
    es
    la prueba siguiente, que escribe el interleaving a mano.
    """
    cliente, sesion = en_marcha.client, en_marcha.session_id
    cuerpo = {"position": 1, "chosen": ["a"], "elapsed_ms": 10}
    cuantas = 16
    # La barrera no es adorno: sin ella las peticiones salen escalonadas y la primera suele escribir
    # antes de que la última lea, así que la carrera no llega a ocurrir. Con ella **todas** entran a
    # la
    # vez, que es el caso que midió el recorrido al pulsar dos veces deprisa.
    salida = threading.Barrier(cuantas)

    def contestar(_indice: int) -> int:
        salida.wait()
        return cliente.post(
            f"/api/v1/student/sessions/{sesion}/answers", json=cuerpo, headers=ALLOWED_ORIGIN
        ).status_code

    with ThreadPoolExecutor(max_workers=cuantas) as pool:
        codigos = list(pool.map(contestar, range(cuantas)))

    assert codigos == [200] * cuantas, f"códigos de las peticiones simultáneas: {codigos}"

    # Y queda **un** intento, no dieciséis: la tabla tiene una fila por pregunta de la sesión.
    run = cliente.get(f"/api/v1/student/sessions/{sesion}").json()
    assert run["answered"] == 1


class _LecturaCiega(SqlAlchemyStudyRepository):
    """El repositorio de verdad, pero `attempt_for_question` **no ve** el intento.

    Fija a mano el interleaving que el recorrido midió al pulsar dos veces deprisa: las dos
    peticiones
    leen antes de que ninguna escriba, así que las dos llegan al `INSERT` y la segunda choca con la
    clave única `uq_attempt_per_question`. Es el momento exacto del 500 —`UNIQUE constraint failed:
    attempts.session_question_id`—, que es lo que hay que arreglar; el 500 entero lo sirve la API
    por
    encima de esto.
    """

    def attempt_for_question(self, session_question_id: str) -> AttemptView | None:
        return None


def _servicio_con_lectura_ciega(settings: Settings) -> StudyService:
    engine = build_engine(settings.data_paths.database)
    sesiones = build_session_factory(engine)
    return StudyService(
        study=_LecturaCiega(sesiones),
        questions=SqlAlchemyQuestionRepository(sesiones),
        profiles=SqlAlchemyProfileRepository(sesiones),
        clock=SystemClock(),
    )


def test_dos_peticiones_que_leen_a_la_vez_no_crean_dos_intentos(seeded_settings: Settings) -> None:
    """El 500, con el interleaving escrito a mano: las dos leen, ninguna ha escrito todavía.

    Lo que se exige no es «no revienta» a secas —eso lo cumpliría tragarse el error—, sino que la
    segunda petición **devuelva el mismo intento** y diga que no ha escrito nada.
    """
    with _cliente(seeded_settings) as cliente:
        montado = _montar_test(cliente)

    servicio = _servicio_con_lectura_ciega(seeded_settings)
    actual = servicio.current_question(montado.session_id)
    assert actual.question is not None
    entrada = AnswerInput(
        question_version_id=actual.question.question_version_id,
        chosen_option_keys=("a",),
        elapsed_ms=10,
    )

    primera = servicio.answer(montado.session_id, entrada)
    segunda = servicio.answer(montado.session_id, entrada)

    assert primera.saved is True and primera.already_answered is False
    assert segunda.saved is False, "la segunda no ha escrito nada"
    assert segunda.already_answered is True
    assert segunda.attempt.id == primera.attempt.id, "es el mismo intento, no otro"


# ------------------------------------------------------------------- 4. la mentira del mensaje


def test_un_fallo_interno_llega_con_cabeceras_de_cors(seeded_settings: Settings) -> None:
    """Un 500 legítimo no puede leerse como un error de CORS.

    Lo que pasó en el recorrido: la excepción no la recogía ningún manejador, así que la contestaba
    el
    middleware de errores, que está **por fuera** del de CORS. La respuesta salía sin
    `Access-Control-Allow-Origin`, el navegador la bloqueaba y en la consola se leía
    «blocked by CORS policy»: un mensaje que manda a mirar donde no es. Se fija con una ruta que
    revienta a propósito.
    """
    app = create_app(Settings(data_dir=seeded_settings.data_dir, _env_file=None))

    @app.get("/api/v1/reventa-de-prueba")
    def _reventar() -> None:
        raise RuntimeError("lo que nadie esperaba")

    cliente = TestClient(app, raise_server_exceptions=False)
    respuesta = cliente.get("/api/v1/reventa-de-prueba", headers=ALLOWED_ORIGIN)

    assert respuesta.status_code == 500
    assert respuesta.headers.get("access-control-allow-origin") == "http://127.0.0.1:5173"
    assert respuesta.json()["code"] == "internal_error"
