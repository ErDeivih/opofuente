"""La zona del alumno por la API real: contrato sin fugas, orden, aislamiento y modo público.

Estas cuatro pruebas son la razón de ser de la capa `/api/v1/student/*`, y la primera es la más
importante de la fase: **ninguna respuesta del alumno puede llevar evidencias, conjuntos, claves,
versiones ni rutas**. No se comprueba que un campo venga vacío, sino que la respuesta entera —el
JSON tal cual se sirve, claves y valores— no contenga nada de la lista prohibida, con datos
sembrados que sí tienen todo eso dentro.

Las otras tres defienden lo que hace útil a la capa:

2. **Orden**: el temario sale en orden numérico (`IV.1` antes de `IV.10`, `I.1` antes de `I.2`), que
   es lo que se arregló en la consulta del programa y lo que la pantalla pinta tal cual.
3. **Aislamiento**: con la oposición de Celador sembrada, por aquí no aparece **nada** suyo: ni su
   nombre, ni su identificador, ni sus preguntas. El filtro vive en el servidor, no en la pantalla.
4. **Modo público**: con `OPOFUENTE_PUBLIC_MODE=1` no se sirve ningún conjunto `personal`; los
   `public` sí. Es la comprobación de que «abrir al público» no es una promesa de la pantalla.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

import pytest
from fastapi.testclient import TestClient

from opofuente.config import Settings
from opofuente.domain.topic_notes import Coverage, KeyStatus, NotesCheck, NoteSection
from opofuente.infrastructure.db import build_engine, build_session_factory
from opofuente.infrastructure.topic_notes_repository import SqlAlchemyTopicNotesRepository
from opofuente.main import create_app

ALLOWED_ORIGIN = {"Origin": "http://127.0.0.1:5173"}

#: La oposición que sirve la zona del alumno, por su código de configuración.
OPOSICION_ALUMNO = "tai-age"

#: La oposición ajena que se siembra para la prueba de aislamiento. Es su **código de oposición**
#: (`celador-sacyl`), que no es el de su convocatoria (`celador-sacyl-2022`): son dos vocabularios y
#: confundirlos es justo el error que esta prueba tiene que no cometer.
OPOSICION_AJENA = "celador-sacyl"

#: El nombre que se le da al banco privado sembrado. Es un título de banco como los de verdad: si
#: apareciera en cualquier respuesta del alumno, la prueba de contrato lo tiene que ver.
TITULO_BANCO_PRIVADO = "Rojo -General (banco privado del propietario)"

#: El título del material de la oposición ajena, con su nombre dentro para poder buscarlo.
TITULO_AJENO = "Cuestionario oficial de Celador SACYL 2022"

#: Claves que **no** pueden aparecer en ninguna respuesta del alumno. Se comprueba por partes: la
#: lista incluye la clave completa y el prefijo que la delata (`key_`, `answer_key`), de modo que un
#: campo nuevo con ese vocabulario también falle aunque nadie lo añada aquí.
CLAVES_PROHIBIDAS: tuple[str, ...] = (
    "evidence",
    "source",
    "question_set_id",
    "answer_key",
    "key_",
    "correct_option_keys",
    "document",
    "origin_type",
    "context_label",
    "question_version_id",
    "session_question_id",
    "stable_key",
    "curriculum_node_id",
    "node_id",
    "opposition_id",
    "convocation_version_id",
    "url",
    "path",
    "file",
)

#: Valores que **no** pueden aparecer en ninguna respuesta del alumno: rutas, extensiones, nombres
#: de bancos y de otras oposiciones, y los identificadores internos de lo sembrado. La lista se
#: amplía por prueba con lo que se ha sembrado (identificadores y títulos).
VALORES_PROHIBIDOS: tuple[str, ...] = (
    "F:",
    ":\\",
    ".pdf",
    ".docx",
    "Rojo",
    "GSI",
    "Celador",
    "celador",
    "Guardia Civil",
    "banco privado",
    "Tests de",
)

#: El programa que se usa en las pruebas: dos temas del bloque IV (el 1 y el 10, que es el caso que
#: ordenaba mal por texto) y dos del bloque I.
TEMAS_CON_PREGUNTAS = ("IV.1", "IV.10", "I.1", "I.2")

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
class ZonaAlumno:
    """Lo sembrado y el cliente con el que se consulta la zona del alumno."""

    client: TestClient
    settings: Settings
    #: Todo lo que no puede aparecer en una respuesta: identificadores internos y títulos.
    prohibidos: list[str] = field(default_factory=list)
    #: Lo que sí tiene que aparecer, para que la prueba no pase por vacío.
    esperados: list[str] = field(default_factory=list)


def _cliente(
    settings: Settings,
    *,
    public_mode: bool | None = None,
    student_opposition: str | None = None,
) -> TestClient:
    """Un cliente sobre los **mismos** datos, con la configuración que pida la prueba.

    Los dos parámetros parten de lo que ya tenía la configuración de la prueba: construirla otra vez
    desde cero y pasar solo lo que cambia es como se cuela el fallo de estar probando siempre lo
    mismo sin enterarse.
    """
    resuelto = Settings(
        data_dir=settings.data_dir,
        public_mode=settings.public_mode if public_mode is None else public_mode,
        student_opposition=(
            settings.student_opposition if student_opposition is None else student_opposition
        ),
        _env_file=None,
    )
    return TestClient(create_app(resuelto))


def _aplanar(nodos: list[dict[str, Any]]) -> list[dict[str, Any]]:
    planos: list[dict[str, Any]] = []
    for nodo in nodos:
        planos.append(nodo)
        planos.extend(_aplanar(nodo.get("children", [])))
    return planos


def _oposicion(client: TestClient, code: str) -> dict[str, Any]:
    oposiciones = client.get("/api/v1/oppositions").json()
    return next(oposicion for oposicion in oposiciones if oposicion["code"] == code)


def _nodos(client: TestClient, opposition: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Los nodos del programa por su ruta legible (`IV.10`). Solo nodos de tipo tema."""
    convocatoria = opposition["active_convocation"]["id"]
    programa = client.get(f"/api/v1/convocations/{convocatoria}/curriculum").json()
    return {
        nodo["path"]: nodo for nodo in _aplanar(programa["nodes"]) if nodo["node_type"] == "topic"
    }


def _conjunto(
    client: TestClient,
    opposition: dict[str, Any],
    titulo: str,
    *,
    publico: bool = False,
) -> str:
    """Un conjunto con cuatro preguntas y su clave activa. Nace `personal` salvo que se diga."""
    creado = client.post(
        "/api/v1/question-sets",
        json={
            "title": titulo,
            "opposition_id": opposition["id"],
            "set_type": "private_bank",
            "convocation_version_id": opposition["active_convocation"]["id"],
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
    if publico:
        publicado = client.patch(
            f"/api/v1/question-sets/{set_id}",
            json={"distribution": "public"},
            headers=ALLOWED_ORIGIN,
        )
        assert publicado.status_code == 200, publicado.text
    return set_id


def _preguntas(client: TestClient, set_id: str) -> list[dict[str, Any]]:
    listado = client.get("/api/v1/questions", params={"set_id": set_id}).json()
    return list(listado["questions"])


def _asignar(client: TestClient, pregunta_id: str, node_id: str) -> None:
    respuesta = client.post(
        f"/api/v1/questions/{pregunta_id}/topics",
        json={"curriculum_node_id": node_id},
        headers=ALLOWED_ORIGIN,
    )
    assert respuesta.status_code in (200, 201), respuesta.text


def _escribir_apuntes(settings: Settings, node_id: str, pregunta_id: str) -> None:
    """Escribe un apartado de apuntes con una pregunta anclada, por la ruta de verdad.

    La prueba de contrato de esta fase recorre **todas** las respuestas de `/student/*` buscando lo
    que no puede salir. Los apuntes del tema (F13) son la respuesta más larga de la zona del alumno,
    así que tienen que estar ahí con texto de verdad: comprobar que un texto vacío no lleva una ruta
    no demuestra nada.
    """
    ahora = datetime.now(UTC)
    engine = build_engine(settings.data_paths.database)
    try:
        notas = SqlAlchemyTopicNotesRepository(build_session_factory(engine))
        (apartado,) = notas.save_sections(
            node_id,
            [
                NoteSection(
                    key="udp",
                    epigraph_code="IV.1.1",
                    title="UDP: datagramas sin conexión",
                    anchor="udp",
                    position=1,
                )
            ],
            now=ahora,
        )
        notas.save_section_body(
            apartado,
            title=None,
            body="El datagrama UDP no tiene conexión ni acuse de recibo.",
            needs_review_reason=None,
            model="modelo-de-la-prueba",
            now=ahora,
        )
        notas.save_checks(
            node_id,
            [
                NotesCheck(
                    question_version_id=pregunta_id,
                    group_signature="firma-de-la-prueba",
                    section_key=apartado.key,
                    anchor=apartado.anchor,
                    coverage=Coverage.CUBIERTA,
                    note=None,
                    quote="El datagrama UDP no tiene conexión ni acuse de recibo",
                    letter="a",
                    expected=("a",),
                    key_status=KeyStatus.ACTIVE,
                    attempts=1,
                )
            ],
            now=ahora,
        )
    finally:
        engine.dispose()


def _responder(client: TestClient, session_id: str, veces: int) -> None:
    """Responde `veces` preguntas de la sesión, una detrás de otra, para que haya progreso real."""
    for _ in range(veces):
        actual = client.get(f"/api/v1/study-sessions/{session_id}/current-question").json()
        pregunta = actual["question"]
        if pregunta is None:
            return
        elegida = pregunta["options"][0]["stable_key"]
        respuesta = client.post(
            f"/api/v1/study-sessions/{session_id}/answers",
            json={
                "question_version_id": pregunta["question_version_id"],
                "chosen_option_keys": [elegida],
            },
            headers=ALLOWED_ORIGIN,
        )
        assert respuesta.status_code == 201, respuesta.text


def _sesion(
    client: TestClient,
    opposition: dict[str, Any],
    set_id: str,
    cantidad: int,
    *,
    part_code: str = "primera_parte",
) -> str:
    creada = client.post(
        "/api/v1/study-sessions",
        json={
            "opposition_id": opposition["id"],
            "mode": "practice",
            "sources": [
                {
                    "question_set_id": set_id,
                    "part_code": part_code,
                    "count": cantidad,
                    "include_reserves": False,
                }
            ],
            "convocation_version_id": opposition["active_convocation"]["id"],
            "feedback": "immediate",
        },
        headers=ALLOWED_ORIGIN,
    )
    assert creada.status_code == 201, creada.text
    session_id = str(creada.json()["id"])
    arrancada = client.post(f"/api/v1/study-sessions/{session_id}/start", headers=ALLOWED_ORIGIN)
    assert arrancada.status_code == 200, arrancada.text
    return session_id


@pytest.fixture
def zona(seeded_settings: Settings) -> Iterator[ZonaAlumno]:
    """Datos sembrados de verdad: dos oposiciones, un banco privado del propietario y progreso.

    Se siembra con la API real —conjunto, importación, clave activa, catalogación en cuatro temas y
    una sesión respondida— porque la prueba de contrato solo vale si en los datos **sí hay** lo que
    no puede salir. Comprobar que una respuesta vacía no lleva una ruta no demuestra nada.
    """
    with _cliente(seeded_settings) as client:
        alumno = _oposicion(client, OPOSICION_ALUMNO)
        ajena = _oposicion(client, OPOSICION_AJENA)
        temas_alumno = _nodos(client, alumno)
        temas_ajenos = _nodos(client, ajena)

        set_propio = _conjunto(client, alumno, TITULO_BANCO_PRIVADO)
        set_ajeno = _conjunto(client, ajena, TITULO_AJENO)

        preguntas_propias = _preguntas(client, set_propio)
        for indice, path in enumerate(TEMAS_CON_PREGUNTAS):
            _asignar(client, str(preguntas_propias[indice]["id"]), str(temas_alumno[path]["id"]))
        # Y apuntes escritos en IV.1, con una pregunta anclada: la pantalla de lectura existe (F13)
        # y su respuesta es la más larga de la zona del alumno, así que entra en la prueba de
        # contrato.
        _escribir_apuntes(
            seeded_settings,
            str(temas_alumno["IV.1"]["id"]),
            str(preguntas_propias[0]["id"]),
        )
        preguntas_ajenas = _preguntas(client, set_ajeno)
        path_ajeno = next(iter(temas_ajenos))
        _asignar(client, str(preguntas_ajenas[0]["id"]), str(temas_ajenos[path_ajeno]["id"]))

        # Un test terminado (para que haya historial y resultado) y otro a medias («Continuar»).
        terminada = _sesion(client, alumno, set_propio, 4)
        _responder(client, terminada, 4)
        cerrada = client.post(f"/api/v1/study-sessions/{terminada}/finish", headers=ALLOWED_ORIGIN)
        assert cerrada.status_code == 200, cerrada.text

        a_medias = _sesion(client, alumno, set_propio, 4)
        _responder(client, a_medias, 1)

        # Y una sesión de la oposición ajena, para que su progreso exista y no pueda colarse aquí.
        ajena_sesion = _sesion(client, ajena, set_ajeno, 4, part_code="ejercicio_unico")
        _responder(client, ajena_sesion, 1)

        prohibidos = [
            str(alumno["id"]),
            str(alumno["active_convocation"]["id"]),
            str(ajena["id"]),
            str(ajena["active_convocation"]["id"]),
            str(ajena["name"]),
            set_propio,
            set_ajeno,
            TITULO_BANCO_PRIVADO,
            TITULO_AJENO,
            ajena_sesion,
            *[str(pregunta["id"]) for pregunta in preguntas_propias],
            *[str(pregunta["id"]) for pregunta in preguntas_ajenas],
        ]
        esperados = [OPOSICION_ALUMNO, "IV.1", "IV.10"]
        yield ZonaAlumno(
            client=client,
            settings=seeded_settings,
            prohibidos=prohibidos,
            esperados=esperados,
        )


# ---------------------------------------------------------------- 1. contrato sin fugas


def _claves(objeto: object, prefijo: str = "") -> list[str]:
    """Todas las claves del JSON, con su ruta, para poder decir **dónde** está la fuga."""
    encontradas: list[str] = []
    if isinstance(objeto, dict):
        for clave, valor in objeto.items():
            ruta = f"{prefijo}.{clave}" if prefijo else str(clave)
            encontradas.append(ruta)
            encontradas.extend(_claves(valor, ruta))
    elif isinstance(objeto, list):
        for indice, valor in enumerate(objeto):
            encontradas.extend(_claves(valor, f"{prefijo}[{indice}]"))
    return encontradas


def _respuestas_de_alumno(zona: ZonaAlumno) -> dict[str, Any]:
    """**Cada** respuesta de `/student/*` con datos sembrados, incluida una de error.

    El 404 entra a propósito: un mensaje de error también es una respuesta, y es donde más fácil se
    cuela un identificador interno al decir qué no se ha encontrado. Y el test en curso entra
    entero —montarlo, arrancarlo, contestarlo y cerrarlo— porque es la pantalla que más datos
    enseña: si algo se colara, se colaría aquí.
    """
    rutas = {
        "overview": "/api/v1/student/overview",
        "syllabus": "/api/v1/student/syllabus",
        "topics/IV.1": "/api/v1/student/topics/IV.1",
        "topics/IV-10": "/api/v1/student/topics/IV-10",
        "topics/I.1": "/api/v1/student/topics/I.1",
        "topics/IV.1/notes": "/api/v1/student/topics/IV.1/notes",
        "topics/IV.10/notes": "/api/v1/student/topics/IV.10/notes",
        "progress": "/api/v1/student/progress",
        "tests/plan": "/api/v1/student/tests/plan",
        "mock-exams/plan": "/api/v1/student/mock-exams",
        "official-exams": "/api/v1/student/official-exams",
        "mistakes": "/api/v1/student/mistakes",
        "topics/inexistente": "/api/v1/student/topics/XX.99",
        "topics/inexistente/notes": "/api/v1/student/topics/XX.99/notes",
    }
    respuestas: dict[str, Any] = {}
    for nombre, ruta in rutas.items():
        respuesta = zona.client.get(ruta)
        assert respuesta.status_code in (200, 404), f"{ruta}: {respuesta.status_code}"
        respuestas[nombre] = respuesta.json()

    # El aviso «esto está mal» (F13) también es una respuesta de esta capa: su cuerpo no puede
    # llevar nada de la trastienda, y el rechazo (un apartado que no existe) entra como el 404.
    aviso = zona.client.post(
        "/api/v1/student/topics/IV.1/reports",
        json={"section_key": "udp", "reason": "La cabecera de UDP no es de 12 bytes."},
        headers=ALLOWED_ORIGIN,
    )
    assert aviso.status_code == 201, aviso.text
    respuestas["topics/IV.1/reports"] = aviso.json()
    respuestas["topics/IV.1/reports/sin-apartado"] = zona.client.post(
        "/api/v1/student/topics/IV.1/reports",
        json={"section_key": "no-existe", "reason": "Esto está mal."},
        headers=ALLOWED_ORIGIN,
    ).json()

    creado = zona.client.post(
        "/api/v1/student/tests",
        json={"nodes": ["IV.1"], "count": 2, "filter": "all", "feedback": "immediate"},
        headers=ALLOWED_ORIGIN,
    )
    assert creado.status_code == 201, creado.text
    respuestas["tests"] = creado.json()
    sesion = str(creado.json()["id"])

    arrancado = zona.client.post(f"/api/v1/student/sessions/{sesion}/start", headers=ALLOWED_ORIGIN)
    assert arrancado.status_code == 200, arrancado.text
    respuestas["sessions/start"] = arrancado.json()

    en_curso = zona.client.get(f"/api/v1/student/sessions/{sesion}")
    assert en_curso.status_code == 200, en_curso.text
    respuestas["sessions/en-curso"] = en_curso.json()
    assert respuestas["sessions/en-curso"]["question"] is not None, "hay una pregunta que contestar"
    primera = respuestas["sessions/en-curso"]["question"]["options"][0]["key"]

    contestado = zona.client.post(
        f"/api/v1/student/sessions/{sesion}/answers",
        json={"position": 1, "chosen": [primera], "elapsed_ms": 1200},
        headers=ALLOWED_ORIGIN,
    )
    assert contestado.status_code == 200, contestado.text
    respuestas["sessions/answers"] = contestado.json()

    cerrado = zona.client.post(f"/api/v1/student/sessions/{sesion}/finish", headers=ALLOWED_ORIGIN)
    assert cerrado.status_code == 200, cerrado.text
    respuestas["sessions/finish"] = cerrado.json()

    # El resultado del test terminado (F14) es la respuesta más larga de esta capa: cada pregunta
    # con sus opciones, lo que se marcó, la correcta y su tema. Si algo se colara, se colaría aquí.
    resultado = zona.client.get(f"/api/v1/student/sessions/{sesion}/result")
    assert resultado.status_code == 200, resultado.text
    respuestas["sessions/result"] = resultado.json()
    assert respuestas["sessions/result"]["questions"], "el resultado tiene preguntas que enseñar"

    simulacro = zona.client.post(
        "/api/v1/student/mock-exams",
        json={"variant": "short", "case_block": "III"},
        headers=ALLOWED_ORIGIN,
    )
    assert simulacro.status_code == 201, simulacro.text
    respuestas["mock-exams"] = simulacro.json()

    respuestas["sessions/inexistente"] = zona.client.get(
        "/api/v1/student/sessions/00000000-0000-0000-0000-000000000000"
    ).json()
    return respuestas


def test_ninguna_respuesta_del_alumno_lleva_evidencias_conjuntos_ni_claves(
    zona: ZonaAlumno,
) -> None:
    """La prueba más importante de la fase: el JSON servido no contiene lo prohibido, ni por clave
    ni por valor."""
    respuestas = _respuestas_de_alumno(zona)
    assert respuestas, "sin respuestas que recorrer, la prueba no demuestra nada"

    # Las respuestas no vienen vacías: si el alumno no tuviera datos, «no hay fugas» sería trivial.
    syllabus = respuestas["syllabus"]
    temas = [tema for bloque in syllabus["blocks"] for tema in bloque["topics"]]
    assert len(temas) >= 33, "el temario sembrado tiene que estar entero"
    assert any(tema["available_questions"] > 0 for tema in temas)
    assert respuestas["overview"]["in_progress"] is not None
    assert respuestas["progress"]["history"], "tiene que haber al menos un test terminado"

    for nombre, cuerpo in respuestas.items():
        claves = _claves(cuerpo)
        for clave in claves:
            for prohibida in CLAVES_PROHIBIDAS:
                assert prohibida not in clave.lower(), (
                    f"{nombre}: la clave «{clave}» contiene «{prohibida}»"
                )

    texto = json.dumps(respuestas, ensure_ascii=False)
    for prohibido in (*VALORES_PROHIBIDOS, *zona.prohibidos):
        assert prohibido not in texto, f"«{prohibido}» aparece en alguna respuesta de /student/*"

    # Y lo que sí tiene que estar está, para que la prueba no pase por haber servido otra cosa.
    for esperado in zona.esperados:
        assert esperado in json.dumps(respuestas["syllabus"], ensure_ascii=False)


# ---------------------------------------------------------------- 2. orden numérico


def test_el_temario_va_en_orden_numerico(zona: ZonaAlumno) -> None:
    """`IV.1` antes de `IV.10` y `I.1` antes de `I.2`: el orden de la consulta, no el del texto."""
    bloques = zona.client.get("/api/v1/student/syllabus").json()["blocks"]

    por_bloque = {bloque["code"]: [tema["code"] for tema in bloque["topics"]] for bloque in bloques}
    assert por_bloque["IV"].index("IV.1") < por_bloque["IV"].index("IV.10")
    assert por_bloque["IV"][:3] == ["IV.1", "IV.2", "IV.3"]
    assert por_bloque["IV"][-1] == "IV.10"
    assert por_bloque["I"].index("I.1") < por_bloque["I"].index("I.2")
    assert [bloque["code"] for bloque in bloques] == ["I", "II", "III", "IV"]

    # El tema por su código legible responde el mismo tema que el temario.
    tema = zona.client.get("/api/v1/student/topics/IV.10").json()
    assert tema["code"] == "IV.10"
    assert tema["number"] == 10
    assert tema["block_code"] == "IV"
    assert tema["title"]


# ---------------------------------------------------------------- 3. aislamiento


def test_nada_de_la_oposicion_ajena_aparece_en_la_zona_del_alumno(zona: ZonaAlumno) -> None:
    """Con Celador sembrado, por `/student/*` no aparece ni su nombre ni su identificador."""
    respuestas = _respuestas_de_alumno(zona)
    texto = json.dumps(respuestas, ensure_ascii=False)

    assert "Celador" not in texto
    assert "celador" not in texto
    assert "SACYL" not in texto
    ajena = _oposicion(zona.client, OPOSICION_AJENA)
    assert str(ajena["id"]) not in texto
    assert str(ajena["active_convocation"]["id"]) not in texto

    # Y la oposición que sí se sirve es la configurada, no «la activa» por casualidad.
    for nombre in ("overview", "syllabus", "progress"):
        assert respuestas[nombre]["opposition"]["code"] == OPOSICION_ALUMNO


# ---------------------------------------------------------------- 3b. el plan del test (F22)


def test_el_plan_del_test_dice_los_tamanos_y_los_minutos_que_luego_se_aplican(
    zona: ZonaAlumno,
) -> None:
    """El plan del test (F22) y lo que de verdad pasa al montarlo: la misma cifra.

    Lo que esta prueba defiende es que la pantalla **no calcule** el reloj: los minutos del plan
    tienen que ser los que la sesión recibe de verdad. Se comprueba montando el test con reloj para
    cada tamaño ofrecido y comparando `time_limit_minutes` con los minutos que anunciaba el plan. Si
    alguien moviera la regla del reloj en el motor y el plan siguiera sirviendo la cifra vieja, esto
    falla —que es justo lo que tiene que pasar cuando las dos cifras se separan—.
    """
    plan = zona.client.get("/api/v1/student/tests/plan")
    assert plan.status_code == 200, plan.text
    cuerpo = plan.json()

    tamanos = [cuenta["questions"] for cuenta in cuerpo["counts"]]
    assert tamanos == [10, 20, 25, 50, 100]
    assert all(cuenta["minutes"] > 0 for cuenta in cuerpo["counts"])
    # Los minutos no son «dos por pregunta» a secas: la regla redondea a cinco. Con el 25, que es el
    # único de la lista que no es múltiplo de cinco, se ve que el plan sirve el número redondeado.
    minutos = {cuenta["questions"]: cuenta["minutes"] for cuenta in cuerpo["counts"]}
    assert minutos[25] == 50
    assert cuerpo["timed_note"], "la nota del reloj tiene que decir de dónde sale el tiempo"

    for tamano in tamanos:
        creada = zona.client.post(
            "/api/v1/student/tests",
            json={"nodes": ["IV.1"], "count": tamano, "timed": True},
            headers=ALLOWED_ORIGIN,
        )
        assert creada.status_code == 201, creada.text
        assert creada.json()["time_limit_minutes"] == minutos[tamano], (
            f"el plan anunciaba {minutos[tamano]} minutos para {tamano} preguntas y la sesión "
            f"recibió {creada.json()['time_limit_minutes']}"
        )

    # Y sin el reloj del test, la sesión **no** se queda sin tiempo: hereda el de la parte del
    # perfil con la que se corrige ese material, que es justo lo que el plan anuncia. Medido aquí
    # porque es una cifra que sorprende: un test de diez preguntas sin reloj sigue llevando 120
    # minutos.
    sin_reloj = zona.client.post(
        "/api/v1/student/tests",
        json={"nodes": ["IV.1"], "count": 10, "timed": False},
        headers=ALLOWED_ORIGIN,
    )
    assert sin_reloj.status_code == 201, sin_reloj.text
    assert cuerpo["convocation_minutes"] is not None, (
        "el perfil sembrado publica el tiempo del ejercicio: si no, esta mitad no probaría nada"
    )
    # **Un test de práctica SIN «con tiempo» no lleva reloj**, aunque la convocatoria publique los
    # 120 minutos de su ejercicio: el reloj es para el simulacro, el examen oficial y el test que lo
    # pide (remate, punto 5). Antes heredaba los 120 y una práctica de tres preguntas enseñaba
    # «Quedan 1:59:59».
    assert sin_reloj.json()["time_limit_minutes"] is None


def test_la_oposicion_configurada_manda_sobre_lo_que_hay(seeded_settings: Settings) -> None:
    """Cambiar `OPOFUENTE_STUDENT_OPPOSITION` cambia lo que sirve la zona, y solo eso."""
    with (
        _cliente(seeded_settings) as client,
        _cliente(seeded_settings, student_opposition=OPOSICION_AJENA) as ajeno,
    ):
        propio = client.get("/api/v1/student/syllabus").json()
        otro = ajeno.get("/api/v1/student/syllabus").json()

    assert propio["opposition"]["code"] == OPOSICION_ALUMNO
    assert otro["opposition"]["code"] == OPOSICION_AJENA
    assert [bloque["code"] for bloque in otro["blocks"]] != [
        bloque["code"] for bloque in propio["blocks"]
    ]


# ---------------------------------------------------------------- 4. modo público


@pytest.fixture
def dos_conjuntos(seeded_settings: Settings) -> Iterator[dict[str, str]]:
    """Un conjunto `personal` en `IV.1` (con un test terminado) y otro `public` en `IV.2`.

    Es lo mínimo para poder afirmar las dos mitades del requisito: con el modo público encendido, el
    `personal` **no** se sirve —ni sus preguntas, ni la nota del test que sostiene— y el `public`
    **sí**.

    El test del banco privado se **termina**, no se deja a medias: un test sin cerrar no tiene
    resultado, y comprobar el historial con tests sin cerrar no demostraría nada.
    """
    with _cliente(seeded_settings) as client:
        alumno = _oposicion(client, OPOSICION_ALUMNO)
        temas = _nodos(client, alumno)
        personal = _conjunto(client, alumno, TITULO_BANCO_PRIVADO)
        publico = _conjunto(
            client, alumno, "TAI ingreso libre 2025 · modelo A (examen oficial INAP)", publico=True
        )
        for path, set_id in (("IV.1", personal), ("IV.2", publico)):
            for pregunta in _preguntas(client, set_id):
                _asignar(client, str(pregunta["id"]), str(temas[path]["id"]))
        sesion = _sesion(client, alumno, personal, 4)
        _responder(client, sesion, 4)
        cerrada = client.post(f"/api/v1/study-sessions/{sesion}/finish", headers=ALLOWED_ORIGIN)
        assert cerrada.status_code == 200, cerrada.text
        yield {"personal": personal, "publico": publico, "sesion": sesion}


def test_el_modo_publico_no_sirve_ningun_conjunto_personal(
    seeded_settings: Settings, dos_conjuntos: dict[str, str]
) -> None:
    """`OPOFUENTE_PUBLIC_MODE=1`: nada de un conjunto `personal`; lo `public` sí.

    Las dos mitades se comprueban: si solo se comprobara que el privado no está, un modo público que
    no sirviera **nada** pasaría la prueba, y eso no es lo que se pide.
    """
    with _cliente(seeded_settings, public_mode=True) as abierto:
        syllabus = abierto.get("/api/v1/student/syllabus")
        bloques = syllabus.json()["blocks"]
        overview = abierto.get("/api/v1/student/overview").json()
        progreso = abierto.get("/api/v1/student/progress").json()

    por_tema = {tema["code"]: tema for bloque in bloques for tema in bloque["topics"]}
    assert por_tema["IV.1"]["available_questions"] == 0, (
        "el tema cuyo material es un banco privado no puede contar en modo público"
    )
    assert por_tema["IV.2"]["available_questions"] == 4, (
        "el conjunto público sí se sirve: si no, «modo público» no serviría nada"
    )
    assert TITULO_BANCO_PRIVADO not in syllabus.text
    assert dos_conjuntos["personal"] not in syllabus.text
    # El progreso tampoco: la sesión del banco privado no puede sostener ninguna cifra.
    assert all(bloque["answered"] == 0 for bloque in overview["blocks"])
    assert overview["due_reviews"] == 0
    assert progreso["history"] == []
    assert progreso["weakest_topics"] == []

    # Con el modo cerrado (el de por defecto, que es el del propietario) sí cuenta todo.
    with _cliente(seeded_settings, public_mode=False) as cerrado:
        bloques_cerrado = cerrado.get("/api/v1/student/syllabus").json()["blocks"]
        progress_cerrado = cerrado.get("/api/v1/student/progress").json()
    por_tema_cerrado = {
        tema["code"]: tema for bloque in bloques_cerrado for tema in bloque["topics"]
    }
    assert por_tema_cerrado["IV.1"]["available_questions"] == 4
    assert por_tema_cerrado["IV.1"]["answered"] == 4
    assert progress_cerrado["history"], "el test del banco privado tiene que estar en el historial"
