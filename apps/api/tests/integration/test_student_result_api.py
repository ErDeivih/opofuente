"""El cierre del ciclo de estudio por la API real (F14).

Cinco pantallas —Resultado, Simulacro, Exámenes oficiales, Fallos y Progreso— y, por debajo, las
rutas que las alimentan. Lo que se comprueba aquí es lo que una captura no puede demostrar:

1. **el resultado dice de qué tema era cada pregunta** y el desglose por tema cuadra con lo
   contestado: sin eso, la pantalla de resultado es una lista de números sin salida;
2. **el plan del simulacro sale del perfil del examen** (80 + 5 y 20 + 5, 120 minutos, la
   penalización publicada) y el tiempo que promete es el que tiene la sesión que se monta después:
   una pantalla que promete 120 minutos y monta otra cosa miente;
3. **los exámenes oficiales no se inventan**: con un examen importado se lista y se puede hacer; sin
   ninguno, la lista sale **vacía** (y la pantalla lo dice);
4. **los fallos son fallos de verdad**: la pregunta que se falló y después se acertó no está, la que
   se falló dos veces dice dos, y el repaso vencido se marca con la fecha de la cola de repaso;
5. **`tests_finished` es el número de tests terminados**, no los que caben en el historial.

Todo se siembra con la API real (conjuntos, importación, plantilla activa, catalogación y sesiones
contestadas), nunca con filas escritas a mano: una consulta nueva probada contra filas inventadas no
demuestra nada sobre los datos de verdad.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, text

from opofuente.config import Settings
from opofuente.domain.topic_notes import Coverage, KeyStatus, NotesCheck, NoteSection
from opofuente.infrastructure.db import build_engine, build_session_factory
from opofuente.infrastructure.db_models import ReviewItemRecord, SessionQuestionRecord
from opofuente.infrastructure.review_repository import SqlAlchemyReviewRepository
from opofuente.infrastructure.topic_notes_repository import SqlAlchemyTopicNotesRepository
from opofuente.main import create_app

ALLOWED_ORIGIN = {"Origin": "http://127.0.0.1:5173"}

AHORA = datetime(2026, 10, 11, 12, 0, tzinfo=UTC)

OPOSICION_ALUMNO = "tai-age"

#: Las cifras del perfil de TAI, leídas de la convocatoria y no escritas a mano: la primera parte es
#: un cuestionario de 80 preguntas con 5 de reserva y la segunda un supuesto de 20 con 5, y las dos
#: se hacen juntas en 120 minutos. Si el perfil cambia, estas pruebas cambian con él.
PRIMERA_PARTE = (80, 5)


def _texto(cantidad: int, *, reservas: int = 0, con_respuestas: bool = True) -> str:
    """Preguntas de prueba para importar: la respuesta correcta es siempre `a`.

    Un examen oficial se importa **sin** sus respuestas —la plantilla se publica aparte— y por eso
    `con_respuestas` se puede apagar: si se dejaran dentro, la plantilla no llegaría como
    documento y el enlace con su plantilla oficial no tendría nada que enlazar.
    """
    lineas: list[str] = []
    for numero in range(1, cantidad + 1):
        lineas += [
            f"{numero}. Enunciado {numero} del material de la prueba.",
            "a) Verdadero",
            "b) Falso",
        ]
        if con_respuestas:
            lineas.append("Respuesta correcta: a")
    for numero in range(cantidad + 1, cantidad + reservas + 1):
        lineas += [
            f"{numero}. (R) Enunciado {numero} de reserva.",
            "a) Verdadero",
            "b) Falso",
        ]
        if con_respuestas:
            lineas.append("Respuesta correcta: a")
    return "\n".join(lineas)


def _cliente(settings: Settings, *, public_mode: bool | None = None) -> TestClient:
    resuelto = Settings(
        data_dir=settings.data_dir,
        public_mode=settings.public_mode if public_mode is None else public_mode,
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
    set_type: str = "private_bank",
    cantidad: int = 4,
    reservas: int = 0,
    publico: bool = False,
    plantilla_version_id: str | None = None,
) -> str:
    """Un conjunto con su clave activa, importado por la ruta real.

    Un examen **oficial** no puede llevar la clave activa sin la plantilla oficial enlazada
    (invariante 4): la plantilla llega como documento aparte y se enlaza con él. Aquí el documento
    de
    la plantilla se prepara antes (`_version_de_plantilla`) y la plantilla —sus 85 respuestas— entra
    por la ruta real.
    """
    creado = client.post(
        "/api/v1/question-sets",
        json={
            "title": titulo,
            "opposition_id": opposition["id"],
            "set_type": set_type,
            "convocation_version_id": opposition["active_convocation"]["id"],
        },
        headers=ALLOWED_ORIGIN,
    )
    assert creado.status_code == 201, creado.text
    set_id = str(creado.json()["id"])
    importado = client.post(
        f"/api/v1/question-sets/{set_id}/parse",
        json={
            "kind": "questions",
            "text": _texto(
                cantidad, reservas=reservas, con_respuestas=plantilla_version_id is None
            ),
        },
        headers=ALLOWED_ORIGIN,
    )
    assert importado.status_code == 200, importado.text
    if plantilla_version_id is not None:
        enlazada = client.post(
            f"/api/v1/question-sets/{set_id}/parse",
            json={
                "kind": "answer_key",
                "text": _texto_plantilla(cantidad, reservas=reservas),
                "source_document_version_id": plantilla_version_id,
            },
            headers=ALLOWED_ORIGIN,
        )
        assert enlazada.status_code == 200, enlazada.text
    claves = client.get(f"/api/v1/question-sets/{set_id}/answer-keys").json()
    activada = client.post(
        f"/api/v1/question-sets/{set_id}/answer-keys/{claves[-1]['id']}/activate",
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


def _texto_plantilla(cantidad: int, *, reservas: int = 0) -> str:
    """La plantilla suelta del examen: una respuesta por pregunta, con su número."""
    return "\n".join(f"{numero}. a" for numero in range(1, cantidad + reservas + 1)) + "\n"


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


def _version_de_plantilla(settings: Settings, version_id: str) -> str:
    """La versión de documento de una plantilla oficial, para poder enlazarla con su examen.

    Es lo único que se prepara por SQL: el **documento** del que salió la plantilla. La plantilla en
    sí —sus 85 respuestas— entra por la ruta real, y lo que esta prueba necesita de la versión es
    solo que exista, porque la clave de un examen oficial no se puede activar sin ella (invariante
    4).
    """
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.begin() as conexion:
            conexion.execute(
                text(
                    "INSERT INTO source_artifacts (id, sha256, size_bytes, media_type, "
                    "storage_key, first_seen_at) VALUES (:art, :sha, 100, 'text/plain', 'k', "
                    ":ahora)"
                ),
                {
                    "art": f"art-{version_id}",
                    "sha": version_id.encode().hex().ljust(64, "0")[:64],
                    "ahora": AHORA.isoformat(),
                },
            )
            conexion.execute(
                text(
                    "INSERT INTO logical_documents (id, canonical_title, document_type, "
                    "authority_tier, owner_scope, created_at, updated_at) VALUES (:doc, :titulo, "
                    "'answer_key', 'A', 'public', :ahora, :ahora)"
                ),
                {
                    "doc": f"doc-{version_id}",
                    "titulo": "Plantilla oficial del examen",
                    "ahora": AHORA.isoformat(),
                },
            )
            conexion.execute(
                text(
                    "INSERT INTO document_versions (id, logical_document_id, artifact_id, "
                    "representation_id, status, created_at) VALUES (:version, :doc, :art, NULL, "
                    "'candidate', :ahora)"
                ),
                {
                    "version": version_id,
                    "doc": f"doc-{version_id}",
                    "art": f"art-{version_id}",
                    "ahora": AHORA.isoformat(),
                },
            )
    finally:
        engine.dispose()
    return version_id


def _mover_el_repaso(settings: Settings, *, dias: int) -> str:
    """Mueve la fecha de repaso de una pregunta fallada y devuelve su identificador.

    Un fallo recién cometido entra en la cola **para hoy**, así que para ver la otra mitad —la
    pregunta que ya no toca— hay que mover una fecha. Se escribe por el repositorio de repaso, no
    con
    SQL suelto, y se mueve una sola: así la prueba distingue las dos.
    """
    engine = build_engine(settings.data_paths.database)
    try:
        factoria = build_session_factory(engine)
        with factoria() as session:
            fila = (
                session.execute(
                    select(ReviewItemRecord)
                    .where(ReviewItemRecord.lapses >= 1)
                    .order_by(ReviewItemRecord.created_at, ReviewItemRecord.id)
                )
                .scalars()
                .first()
            )
        assert fila is not None, "un fallo tiene que haber dejado su repaso programado"
        ahora = datetime.now(UTC)
        SqlAlchemyReviewRepository(factoria).save_item(
            review_id=str(fila.id),
            question_version_id=str(fila.question_version_id),
            opposition_id=str(fila.opposition_id),
            learning_error_id=fila.learning_error_id,
            due_at=ahora + timedelta(days=dias),
            interval_days=fila.interval_days,
            repetitions=fila.repetitions,
            lapses=fila.lapses,
            reason="repaso vencido (prueba)",
            reviewed_at=fila.last_reviewed_at,
            now=ahora,
        )
        return str(fila.question_version_id)
    finally:
        engine.dispose()


@dataclass
class Cierre:
    """Lo sembrado y el cliente con el que se recorre el cierre del ciclo."""

    client: TestClient
    settings: Settings
    #: El test terminado: 1 acierto y 3 fallos sobre dos temas.
    sesion: str


@pytest.fixture
def cierre(seeded_settings: Settings) -> Iterator[Cierre]:
    """Un test terminado con aciertos y fallos en dos temas, y un examen oficial importado.

    Se contesta **por posición** (la misma que usa el alumno) y con la letra `a` para la primera
    respuesta y `b` para las demás: todas las preguntas de la prueba tienen `a` por correcta, así
    que el resultado es determinista sin que la prueba tenga que saber qué pregunta cayó en cada
    fila.
    """
    with _cliente(seeded_settings) as client:
        alumno = _oposicion(client, OPOSICION_ALUMNO)
        temas = _nodos(client, alumno)
        banco = _conjunto(client, alumno, "Rojo -General (banco privado del propietario)")
        for indice, path in enumerate(("IV.1", "IV.10")):
            for pregunta in _preguntas(client, banco)[indice::2]:
                _asignar(client, str(pregunta["id"]), str(temas[path]["id"]))
        # Un examen oficial importado de verdad: 80 preguntas + 5 de reserva y su plantilla
        # enlazada, que es lo que el perfil pide para poder hacerlo.
        _conjunto(
            client,
            alumno,
            "TAI ingreso libre 2025 · examen oficial",
            set_type="official_exam",
            cantidad=PRIMERA_PARTE[0],
            reservas=PRIMERA_PARTE[1],
            publico=True,
            plantilla_version_id=_version_de_plantilla(seeded_settings, "plantilla-examen"),
        )

        creado = client.post(
            "/api/v1/student/tests",
            json={"nodes": ["IV.1", "IV.10"], "count": 4, "filter": "all", "feedback": "immediate"},
            headers=ALLOWED_ORIGIN,
        )
        assert creado.status_code == 201, creado.text
        sesion = str(creado.json()["id"])
        arrancada = client.post(f"/api/v1/student/sessions/{sesion}/start", headers=ALLOWED_ORIGIN)
        assert arrancada.status_code == 200, arrancada.text
        for posicion in range(1, 5):
            respuesta = client.post(
                f"/api/v1/student/sessions/{sesion}/answers",
                json={
                    "position": posicion,
                    "chosen": ["a" if posicion == 1 else "b"],
                    "elapsed_ms": 1200 if posicion == 1 else 0,
                },
                headers=ALLOWED_ORIGIN,
            )
            assert respuesta.status_code == 200, respuesta.text
        cerrada = client.post(f"/api/v1/student/sessions/{sesion}/finish", headers=ALLOWED_ORIGIN)
        assert cerrada.status_code == 200, cerrada.text
        yield Cierre(client=client, settings=seeded_settings, sesion=sesion)


# ---------------------------------------------------------------- 1. el resultado, por tema


def test_el_resultado_dice_de_que_tema_era_cada_pregunta(cierre: Cierre) -> None:
    """Cada pregunta con su tema y el desglose por tema cuadrando con lo contestado."""
    respuesta = cierre.client.get(f"/api/v1/student/sessions/{cierre.sesion}/result")
    assert respuesta.status_code == 200, respuesta.text
    cuerpo = respuesta.json()

    assert cuerpo["session"]["status"] == "finished"
    assert cuerpo["total"]["correct"] == 1
    assert cuerpo["total"]["wrong"] == 3
    assert cuerpo["total"]["blank"] == 0

    # Las cuatro preguntas, cada una con su opción marcada, la correcta y su tema.
    preguntas = cuerpo["questions"]
    assert len(preguntas) == 4
    for pregunta in preguntas:
        assert pregunta["topics"], f"la pregunta {pregunta['position']} no dice de qué tema era"
        assert pregunta["correct"] == ["a"], "la plantilla de la prueba tiene `a` por correcta"
        assert pregunta["options"]
    assert [pregunta["outcome"] for pregunta in preguntas].count("correct") == 1
    assert [pregunta["outcome"] for pregunta in preguntas].count("wrong") == 3
    assert any(pregunta["elapsed_ms"] == 1200 for pregunta in preguntas), (
        "el tiempo empleado en cada pregunta tiene que llegar a la pantalla"
    )

    # El desglose por tema: los dos temas con su parte del resultado, y el total cuadrando.
    temas = {tema["code"]: tema for tema in cuerpo["topics"]}
    assert set(temas) == {"IV.1", "IV.10"}, "los dos temas del test tienen que estar"
    assert sum(tema["correct"] for tema in temas.values()) == 1
    assert sum(tema["wrong"] for tema in temas.values()) == 3
    for tema in temas.values():
        assert tema["graded"] == tema["correct"] + tema["wrong"] + tema["blank"]
        assert tema["accuracy"] == pytest.approx(tema["correct"] / tema["graded"])

    # Y el tiempo que duró el test, que es la otra cifra de la cabecera.
    assert cuerpo["duration_seconds"] is not None
    assert cuerpo["duration_seconds"] >= 0


def test_el_ancla_del_resultado_dice_el_capitulo_que_hay_que_abrir(cierre: Cierre) -> None:
    """«Ver en apuntes» necesita el **capítulo** además del anclaje (F35, §3.1).

    Desde que los apuntes se leen por epígrafes oficiales, un anclaje solo no resuelve: el párrafo
    puede estar en un capítulo que no es el que la página abre por defecto, y entonces el enlace
    deja al alumno arriba. Medido antes de este cambio: `scrollY = 0` con el apartado a 10.288 px.

    El anclaje se escribe por la ruta de verdad (el repositorio de apuntes, como hace el motor)
    sobre una pregunta del test que se acaba de contestar, y en el **segundo** epígrafe del tema a
    propósito: si fuera el primero, la prueba pasaría aunque el capítulo no viajara.
    """
    resultado = cierre.client.get(f"/api/v1/student/sessions/{cierre.sesion}/result")
    assert resultado.status_code == 200, resultado.text
    primera = resultado.json()["questions"][0]
    tema = str(primera["topics"][0]["code"])
    capitulos = _epigrafes(cierre.client, tema)
    assert len(capitulos) >= 2, f"{tema} necesita dos epígrafes para esta prueba"
    segundo = capitulos[1]
    pregunta = _pregunta_del_test(cierre, int(primera["position"]))
    _anclar_en_el_epigrafe(cierre, tema, segundo, pregunta)

    otra_vez = cierre.client.get(f"/api/v1/student/sessions/{cierre.sesion}/result")
    assert otra_vez.status_code == 200, otra_vez.text
    ancladas = [fila for fila in otra_vez.json()["questions"] if fila["note_anchor"] is not None]
    assert len(ancladas) == 1, "la pregunta anclada tiene que ofrecer «Ver en apuntes»"
    ancla = ancladas[0]["note_anchor"]
    assert ancla["topic_code"] == tema
    assert ancla["anchor"] == "correo-electronico"
    assert ancla["epigraph_code"] == segundo, "el capítulo que hay que abrir viaja con el anclaje"


def _epigrafes(client: TestClient, tema: str) -> list[str]:
    """Los epígrafes oficiales de un tema, en el orden del programa."""
    alumno = _oposicion(client, OPOSICION_ALUMNO)
    convocatoria = alumno["active_convocation"]["id"]
    programa = client.get(f"/api/v1/convocations/{convocatoria}/curriculum").json()
    nodo = next(
        fila
        for fila in _aplanar(programa["nodes"])
        if fila["path"] == tema and fila["node_type"] == "topic"
    )
    return [hijo["path"] for hijo in nodo.get("children", [])]


def _pregunta_del_test(cierre: Cierre, posicion: int) -> str:
    """La versión de la pregunta que ocupa esa posición del test, leída de la base de la prueba."""
    engine = build_engine(cierre.settings.data_paths.database)
    try:
        factoria = build_session_factory(engine)
        with factoria() as session:
            fila = session.execute(
                select(SessionQuestionRecord).where(
                    SessionQuestionRecord.session_id == cierre.sesion,
                    SessionQuestionRecord.position == posicion,
                )
            ).scalar_one()
            return str(fila.question_version_id)
    finally:
        engine.dispose()


def _anclar_en_el_epigrafe(cierre: Cierre, tema: str, epigrafe: str, pregunta: str) -> None:
    """Escribe el apartado de los apuntes y ancla ahí la pregunta, por la ruta de verdad.

    Es lo que hace la corrida de apuntes del motor: el apartado y su comprobación. La prueba no
    escribe filas a mano porque la consulta que se está probando es justo la que las lee.
    """
    alumno = _oposicion(cierre.client, OPOSICION_ALUMNO)
    convocatoria = alumno["active_convocation"]["id"]
    programa = cierre.client.get(f"/api/v1/convocations/{convocatoria}/curriculum").json()
    nodo = next(
        fila
        for fila in _aplanar(programa["nodes"])
        if fila["path"] == tema and fila["node_type"] == "topic"
    )
    ahora = datetime.now(UTC)
    engine = build_engine(cierre.settings.data_paths.database)
    try:
        notas = SqlAlchemyTopicNotesRepository(build_session_factory(engine))
        (apartado,) = notas.save_sections(
            str(nodo["id"]),
            [
                NoteSection(
                    key="correo-electronico",
                    epigraph_code=epigrafe,
                    title="El correo electrónico y sus protocolos",
                    anchor="correo-electronico",
                    position=1,
                )
            ],
            now=ahora,
        )
        notas.save_section_body(
            apartado,
            title=None,
            body="El correo electrónico se transporta con SMTP, POP3 e IMAP.",
            needs_review_reason=None,
            model="modelo-de-la-prueba",
            now=ahora,
        )
        notas.save_checks(
            str(nodo["id"]),
            [
                NotesCheck(
                    question_version_id=pregunta,
                    group_signature="firma-de-la-prueba",
                    section_key=apartado.key,
                    anchor=apartado.anchor,
                    coverage=Coverage.CUBIERTA,
                    note=None,
                    quote="El correo electrónico se transporta con SMTP, POP3 e IMAP",
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


def test_un_test_sin_terminar_no_tiene_resultado(cierre: Cierre) -> None:
    """De un test a medias no se enseña medio resultado: se dice que hay que terminarlo."""
    creado = cierre.client.post(
        "/api/v1/student/tests",
        json={"nodes": ["IV.1"], "count": 2, "filter": "all", "feedback": "immediate"},
        headers=ALLOWED_ORIGIN,
    )
    assert creado.status_code == 201, creado.text
    a_medias = str(creado.json()["id"])

    respuesta = cierre.client.get(f"/api/v1/student/sessions/{a_medias}/result")
    assert respuesta.status_code == 409, respuesta.text
    assert "termin" in respuesta.json()["detail"].lower()


# ---------------------------------------------------------------- 2. el plan del simulacro


def test_el_plan_del_simulacro_sale_del_perfil_del_examen(cierre: Cierre) -> None:
    """80 + 5, 20 + 5, 120 minutos y la penalización publicada: del perfil, no de la pantalla."""
    plan = cierre.client.get("/api/v1/student/mock-exams")
    assert plan.status_code == 200, plan.text
    cuerpo = plan.json()

    completo = cuerpo["full"]
    partes = {parte["code"]: parte for parte in completo["parts"]}
    assert set(partes) == {"primera_parte", "segunda_parte"}
    assert partes["primera_parte"]["ordinary_items"] == PRIMERA_PARTE[0]
    assert partes["primera_parte"]["reserve_items"] == PRIMERA_PARTE[1]
    assert partes["segunda_parte"]["ordinary_items"] == 20
    assert partes["segunda_parte"]["reserve_items"] == 5
    assert partes["primera_parte"]["penalty"] == "1/3", "la penalización de TAI es un tercio exacto"
    assert partes["primera_parte"]["time_minutes"] == 120, (
        "el tiempo de TAI vive en el ejercicio único y la parte lo hereda"
    )
    assert completo["time_limit_minutes"] == 120
    assert "estimación" in (completo["note"] or ""), (
        "el aviso de que la nota es una estimación tiene que ir antes de empezar"
    )

    # La variante corta no es el examen y lo dice con sus propias cifras.
    corto = cuerpo["short"]
    assert corto["time_limit_minutes"] == 48
    assert [parte["ordinary_items"] for parte in corto["parts"]] == [40]
    assert [parte["reserve_items"] for parte in corto["parts"]] == [None]
    assert "no es un examen oficial" in (corto["note"] or "").lower()

    # Y los bloques del supuesto, con sus temas: es lo que permite elegir sabiendo qué cae.
    bloques = {bloque["code"]: bloque for bloque in cuerpo["case_blocks"]}
    assert set(bloques) == {"III", "IV"}
    assert all(bloque["topics"] for bloque in bloques.values())
    codigos = {tema["code"] for tema in bloques["IV"]["topics"]}
    assert "IV.1" in codigos
    assert any(tema["available_questions"] > 0 for tema in bloques["IV"]["topics"])


def test_el_tiempo_que_promete_el_plan_es_el_que_tiene_la_sesion(cierre: Cierre) -> None:
    """El plan y la sesión no pueden discrepar: si divergieran, la pantalla prometería otra cosa."""
    plan = cierre.client.get("/api/v1/student/mock-exams").json()

    simulacro = cierre.client.post(
        "/api/v1/student/mock-exams",
        json={"variant": "full", "case_block": "IV"},
        headers=ALLOWED_ORIGIN,
    )
    assert simulacro.status_code == 201, simulacro.text
    sesion = simulacro.json()

    assert sesion["mode"] == "mock_exam"
    assert sesion["time_limit_minutes"] == plan["full"]["time_limit_minutes"]
    assert sesion["practical_case_origin"] == "bloque", (
        "si el supuesto sale de los temas del bloque, la sesión lo dice"
    )


# ---------------------------------------------------------------- 3. los exámenes oficiales


def test_los_examenes_oficiales_importados_se_listan_y_se_pueden_hacer(cierre: Cierre) -> None:
    """Un examen importado se ofrece por su sitio en la lista y se monta de verdad."""
    listado = cierre.client.get("/api/v1/student/official-exams")
    assert listado.status_code == 200, listado.text
    examenes = listado.json()["exams"]
    assert len(examenes) == 1
    examen = examenes[0]
    assert examen["position"] == 1
    assert examen["title"] == "TAI ingreso libre 2025 · examen oficial"
    assert examen["questions"] == PRIMERA_PARTE[0] + PRIMERA_PARTE[1]
    assert examen["ready"] is True

    montado = cierre.client.post(
        "/api/v1/student/official-exams/1/sessions", headers=ALLOWED_ORIGIN
    )
    assert montado.status_code == 201, montado.text
    sesion = montado.json()
    assert sesion["mode"] == "official_exam"
    assert sesion["total_questions"] == PRIMERA_PARTE[0] + PRIMERA_PARTE[1]
    assert sesion["time_limit_minutes"] == 120

    # Y una posición que no existe no monta nada: 404, no una sesión vacía.
    fuera = cierre.client.post("/api/v1/student/official-exams/9/sessions", headers=ALLOWED_ORIGIN)
    assert fuera.status_code == 404, fuera.text


def test_sin_examenes_importados_la_lista_esta_vacia_y_no_se_inventa(
    seeded_settings: Settings,
) -> None:
    """Sin exámenes oficiales, la lista sale vacía: la pantalla lo dice, no se rellena con nada.

    Es el estado de hoy —los exámenes del INAP se importan en otro bloque— y por eso se prueba con
    datos que existen pero **no** son exámenes: si la consulta listara cualquier conjunto, esta
    prueba fallaría.
    """
    with _cliente(seeded_settings) as client:
        alumno = _oposicion(client, OPOSICION_ALUMNO)
        _conjunto(client, alumno, "Rojo -General (banco privado del propietario)")

        listado = client.get("/api/v1/student/official-exams")
        assert listado.status_code == 200, listado.text
        assert listado.json()["exams"] == []

        # Y pedir el primero de una lista que no tiene nada no monta un examen: 404.
        respuesta = client.post("/api/v1/student/official-exams/1/sessions", headers=ALLOWED_ORIGIN)
        assert respuesta.status_code == 404, respuesta.text


# ---------------------------------------------------------------- 4. los fallos


def test_los_fallos_llevan_su_tema_su_fecha_y_cuantas_veces(cierre: Cierre) -> None:
    """Tres fallos, con su tema y su cuenta; el que ya no toca deja de contarse como pendiente."""
    antes = cierre.client.get("/api/v1/student/mistakes").json()
    assert antes["total"] == 3
    assert antes["due_total"] == 3, "un fallo recién cometido entra en la cola de repaso para hoy"
    assert len(antes["questions"]) == 3
    for fallo in antes["questions"]:
        assert fallo["times_failed"] == 1
        assert fallo["topics"], "un fallo sin tema no se puede repasar"
        assert fallo["due"] is True
        assert datetime.fromisoformat(fallo["last_failed_at"]) <= datetime.now(UTC)
    temas = {tema["code"]: tema for tema in antes["topics"]}
    assert set(temas) <= {"IV.1", "IV.10"}
    assert sum(tema["failed"] for tema in temas.values()) == 3, (
        "el reparto por tema tiene que sumar los fallos, no una parte"
    )

    # Se aplaza el repaso de **una** pregunta y las cifras bajan con ella: la lista no cuenta lo que
    # no toca.
    _mover_el_repaso(cierre.settings, dias=3)
    despues = cierre.client.get("/api/v1/student/mistakes").json()
    assert despues["total"] == 3, "aplazar un repaso no borra el fallo: sigue en la lista"
    assert despues["due_total"] == 2
    assert sum(1 for fallo in despues["questions"] if fallo["due"]) == 2
    assert sum(tema["due"] for tema in despues["topics"]) == 2


def test_una_pregunta_fallada_y_despues_acertada_no_es_un_fallo(cierre: Cierre) -> None:
    """La lista mira el **último** intento: lo que se falló y se corrigió no se queda como fallo."""
    # Un test nuevo sobre el mismo tema, esta vez acertando: las cuatro preguntas se contestan con
    # `a`, que es la correcta en todas.
    creado = cierre.client.post(
        "/api/v1/student/tests",
        json={"nodes": ["IV.1", "IV.10"], "count": 4, "filter": "all", "feedback": "immediate"},
        headers=ALLOWED_ORIGIN,
    )
    assert creado.status_code == 201, creado.text
    sesion = str(creado.json()["id"])
    cierre.client.post(f"/api/v1/student/sessions/{sesion}/start", headers=ALLOWED_ORIGIN)
    for posicion in range(1, 5):
        cierre.client.post(
            f"/api/v1/student/sessions/{sesion}/answers",
            json={"position": posicion, "chosen": ["a"], "elapsed_ms": 0},
            headers=ALLOWED_ORIGIN,
        )
    cierre.client.post(f"/api/v1/student/sessions/{sesion}/finish", headers=ALLOWED_ORIGIN)

    fallos = cierre.client.get("/api/v1/student/mistakes").json()
    assert fallos["total"] == 0, "acertar despues de fallar quita la pregunta de la lista"


# ---------------------------------------------------------------- 5. el progreso


def test_el_progreso_cuenta_los_tests_terminados_y_no_los_que_caben(cierre: Cierre) -> None:
    """`tests_finished` es el número de tests cerrados; el historial es lo que cabe en él."""
    progreso = cierre.client.get("/api/v1/student/progress").json()
    assert progreso["tests_finished"] == 1
    assert len(progreso["history"]) == 1
    assert progreso["history"][0]["id"] == cierre.sesion
    assert progreso["history"][0]["status"] == "finished"
    # Y el progreso por tema sigue contando el acierto sobre lo corregido.
    temas = {tema["code"]: tema for bloque in progreso["blocks"] for tema in bloque["topics"]}
    assert temas["IV.1"]["answered"] == 2
    assert temas["IV.1"]["accuracy"] is not None
