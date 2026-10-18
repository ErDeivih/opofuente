"""La clave derivada, en los sitios reales: la ruta auditada, la composición y la decisión (F29).

Lo que se prueba aquí no es que exista una tabla: es que la pregunta **vuelve al estudio** con su
letra, que esa letra **nunca** se guarda como la clave del conjunto, que una clave **oficial** se
rechaza, que una pregunta sin clave fiable **sigue fuera** aunque su conjunto vuelva, y que la
decisión de cada conjunto **queda auditada con su cifra**.

Las dos fuentes se escriben por las rutas del proyecto: la de los apuntes, con el mismo
`save_checks` que usa la corrida de un tema; la del modelo, con un doble que contesta lo que se le
diga (nadie llama a nadie y no cuesta nada).
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError

from opofuente.application.study_service import CompositionSpec, PartSpec
from opofuente.config import Settings
from opofuente.domain.derived_keys import (
    ACCION_CLAVE_DERIVADA,
    ACCION_DECISION,
    ACCION_HUECOS,
    ACCION_RECHAZO,
    ACTOR,
    RespuestaDelModelo,
    RespuestasBatch,
)
from opofuente.domain.key_reliability import ACTOR as ACTOR_CLAVES
from opofuente.domain.key_reliability import KeyReliability
from opofuente.domain.question_file import TIPO_OFICIAL
from opofuente.domain.study import SessionMode
from opofuente.domain.topic_notes import Coverage, KeyStatus, NotesCheck
from opofuente.infrastructure.db_models import (
    AnswerKeyEntryRecord,
    AnswerKeyVersionRecord,
    AuditEventRecord,
    DerivedKeyRecord,
    KeyGapRecord,
    QuestionSetRecord,
)
from opofuente.infrastructure.derived_key_repository import (
    SqlAlchemyDerivedKeyRepository,
)
from opofuente.infrastructure.key_reliability_repository import (
    SqlAlchemyKeyReliabilityRepository,
)
from opofuente.infrastructure.study_repository import SqlAlchemyStudyRepository
from opofuente.infrastructure.topic_notes_repository import SqlAlchemyTopicNotesRepository
from opofuente.tools.claves_derivadas import Preparado, _decisiones, _derivar, parse_args

ALLOWED_ORIGIN = {"Origin": "http://127.0.0.1:5173"}
AHORA = datetime(2026, 10, 15, 9, 0, tzinfo=UTC)

CITA = "La respuesta correcta es la b, según el artículo 18."


# --- el andamiaje ---------------------------------------------------------------------------------


def _texto(*, desde: int = 1, cuantas: int = 12) -> str:
    return "\n".join(
        linea
        for numero in range(desde, desde + cuantas)
        for linea in (
            f"{numero}. La pregunta numero {numero} del banco de prueba se contesta sola:",
            "a) Opcion A",
            "b) Opcion B",
            "c) Opcion C",
            "d) Opcion D",
            "Respuesta correcta: a",
            "",
        )
    )


def _aplanar(nodos: list[dict[str, Any]]) -> list[dict[str, Any]]:
    planos: list[dict[str, Any]] = []
    for nodo in nodos:
        planos.append(nodo)
        planos.extend(_aplanar(nodo.get("children", [])))
    return planos


def _rutas(client: TestClient) -> dict[str, str]:
    oposiciones = client.get("/api/v1/oppositions").json()
    convocatoria = next(item["active_convocation"]["id"] for item in oposiciones if item["active"])
    programa = client.get(f"/api/v1/convocations/{convocatoria}/curriculum").json()
    return {str(nodo["path"]): str(nodo["id"]) for nodo in _aplanar(programa["nodes"])}


def _oposicion(client: TestClient) -> dict[str, Any]:
    oposiciones = client.get("/api/v1/oppositions").json()
    return dict(next(oposicion for oposicion in oposiciones if oposicion["active"]))


def _conjunto(
    client: TestClient,
    *,
    titulo: str,
    desde: int = 1,
    cuantas: int = 12,
    set_type: str = "private_bank",
    activar: bool = True,
) -> tuple[str, list[str]]:
    """Un conjunto con sus preguntas y, si se pide, su clave activa.

    `activar=False` es para los conjuntos **oficiales**: la invariante del proyecto no deja activar
    la clave de un examen oficial sin su plantilla enlazada —y saltarla sería relajar el juez—, y la
    ruta de las claves derivadas no necesita una clave activa para decidir que **no** se deriva.
    """
    oposicion = _oposicion(client)
    creado = client.post(
        "/api/v1/question-sets",
        json={
            "title": titulo,
            "opposition_id": oposicion["id"],
            "set_type": set_type,
            "convocation_version_id": oposicion["active_convocation"]["id"],
        },
        headers=ALLOWED_ORIGIN,
    )
    assert creado.status_code == 201, creado.text
    set_id = str(creado.json()["id"])
    importado = client.post(
        f"/api/v1/question-sets/{set_id}/parse",
        json={"kind": "questions", "text": _texto(desde=desde, cuantas=cuantas)},
        headers=ALLOWED_ORIGIN,
    )
    assert importado.status_code == 200, importado.text
    if activar:
        claves = client.get(f"/api/v1/question-sets/{set_id}/answer-keys").json()
        activada = client.post(
            f"/api/v1/question-sets/{set_id}/answer-keys/{claves[0]['id']}/activate",
            headers=ALLOWED_ORIGIN,
        )
        assert activada.status_code == 200, activada.text
    preguntas = [
        str(fila["id"])
        for fila in client.get("/api/v1/questions", params={"set_id": set_id, "limit": 200}).json()[
            "questions"
        ]
    ]
    assert len(preguntas) == cuantas, f"se importaron {len(preguntas)} de {cuantas}"
    return set_id, preguntas


def _catalogar(client: TestClient, pregunta_id: str, *, tema: str) -> None:
    respuesta = client.post(
        f"/api/v1/questions/{pregunta_id}/topics",
        json={"curriculum_node_id": _rutas(client)[tema]},
        headers=ALLOWED_ORIGIN,
    )
    assert respuesta.status_code in (200, 201), respuesta.text


def _cuarentena(client: TestClient, set_id: str, veredicto: KeyReliability) -> None:
    cambiado = SqlAlchemyKeyReliabilityRepository(client.app.state.session_factory).set_verdict(
        set_id,
        veredicto,
        now=AHORA,
        actor=ACTOR_CLAVES,
        reason="prueba de las claves derivadas (Â§1 de F29)",
    )
    assert cambiado, "el veredicto no se pudo poner"


def _procedencia(client: TestClient, set_id: str, *, ambito: str) -> None:
    """Marca la procedencia del conjunto por la ruta auditada (`origin_scope`, D10)."""
    respuesta = client.patch(
        f"/api/v1/question-sets/{set_id}", json={"origin_scope": ambito}, headers=ALLOWED_ORIGIN
    )
    assert respuesta.status_code == 200, respuesta.text


def _ancla(
    client: TestClient,
    *,
    pregunta_id: str,
    node_id: str,
    letra: str | None,
    cita: str | None = CITA,
    key_status: KeyStatus = KeyStatus.ACTIVE,
) -> None:
    """La primera fuente, por la ruta del proyecto: el `save_checks` de la corrida de un tema."""
    guardadas = SqlAlchemyTopicNotesRepository(client.app.state.session_factory).save_checks(
        node_id,
        [
            NotesCheck(
                question_version_id=pregunta_id,
                group_signature=f"grupo-{pregunta_id}",
                section_key="cualquiera",
                anchor="apartado de prueba",
                coverage=Coverage.CUBIERTA if cita else Coverage.DUDOSA,
                note=None,
                quote=cita,
                letter=letra,
                expected=("a",),
                key_status=key_status,
                attempts=1,
            )
        ],
        now=AHORA,
    )
    assert guardadas == 1


class _ModeloDeMentira:
    """El doble del modelo: contesta lo que se le diga, sin llamar a nadie y sin costar nada."""

    name = "de-mentira"
    version = "1"

    def __init__(self, letras: dict[str, str]) -> None:
        self._letras = letras

    def responder(self, preguntas: Any) -> RespuestasBatch:
        return RespuestasBatch(
            respuestas=tuple(
                RespuestaDelModelo(
                    question_version_id=pregunta.question_version_id,
                    letra=self._letras.get(pregunta.question_version_id),
                )
                for pregunta in preguntas
            ),
            input_tokens=10,
            output_tokens=2,
        )


def _corrida(client: TestClient, modelo: _ModeloDeMentira, *, seco: bool = False) -> int:
    """La corrida real del comando, con el modelo cambiado por el doble."""
    repo = SqlAlchemyDerivedKeyRepository(client.app.state.session_factory)
    preparado = Preparado(repo)
    args = parse_args(["--derivar"] + (["--seco"] if seco else []))
    return _derivar(preparado, repo, modelo, args)  # type: ignore[arg-type]


def _hechos(client: TestClient, *, accion: str) -> list[AuditEventRecord]:
    with client.app.state.session_factory() as session:
        return list(
            session.query(AuditEventRecord)
            .filter(AuditEventRecord.action == accion)
            .order_by(AuditEventRecord.created_at)
            .all()
        )


def _derivada(client: TestClient, pregunta_id: str) -> DerivedKeyRecord | None:
    with client.app.state.session_factory() as session:
        return session.get(DerivedKeyRecord, pregunta_id)


def _hueco(client: TestClient, pregunta_id: str) -> KeyGapRecord | None:
    with client.app.state.session_factory() as session:
        return session.get(KeyGapRecord, pregunta_id)


def _congeladas(client: TestClient, session_id: str) -> tuple[Any, ...]:
    return SqlAlchemyStudyRepository(client.app.state.session_factory).session_questions(session_id)


# --- 1. la corrida: la clave derivada, guardada y auditada ------------------------------------


def test_la_corrida_guarda_la_clave_derivada_cuando_las_dos_fuentes_coinciden(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """La letra de los apuntes (con su cita) y la del modelo sin apuntes coinciden: hay clave."""
    rutas = _rutas(seeded_client)
    malo, preguntas = _conjunto(seeded_client, titulo="Banco con la clave mal")
    for pregunta in preguntas:
        _catalogar(seeded_client, pregunta, tema="IV.1")
    _cuarentena(seeded_client, malo, KeyReliability.NO_FIABLE)
    _ancla(seeded_client, pregunta_id=preguntas[0], node_id=rutas["IV.1"], letra="b")

    assert _corrida(seeded_client, _ModeloDeMentira({preguntas[0]: "b"})) == 0

    derivada = _derivada(seeded_client, preguntas[0])
    assert derivada is not None, "la clave derivada se guarda"
    assert derivada.key_state == "derived", "y se guarda como `derived`, nunca como `active`"
    assert derivada.correct_option_keys_json == '["b"]', "con la letra que dijeron las dos fuentes"
    assert derivada.notes_letter == "b"
    assert derivada.notes_quote == CITA, "con la cita que la sostiene"
    assert derivada.question_set_id == malo
    assert derivada.model_name == "de-mentira"
    eventos = _hechos(seeded_client, accion=ACCION_CLAVE_DERIVADA)
    assert [evento.object_id for evento in eventos] == [preguntas[0]]
    assert '"letra": "b"' in str(eventos[0].after_json)


def test_la_corrida_no_toca_la_clave_del_conjunto(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """La clave extraída del material sigue donde estaba: la derivada vive a su lado.

    Es la comprobación de que «nunca `active`» no es una promesa: la plantilla del conjunto no
    cambia ni de estado ni de letras, y **no se crea ninguna versión de plantilla nueva**.
    """
    rutas = _rutas(seeded_client)
    malo, preguntas = _conjunto(seeded_client, titulo="Banco con la clave mal")
    for pregunta in preguntas:
        _catalogar(seeded_client, pregunta, tema="IV.1")
    _cuarentena(seeded_client, malo, KeyReliability.NO_FIABLE)
    _ancla(seeded_client, pregunta_id=preguntas[0], node_id=rutas["IV.1"], letra="b")
    antes = _foto_de_las_claves(seeded_client, malo)

    assert _corrida(seeded_client, _ModeloDeMentira({preguntas[0]: "b"})) == 0

    assert _foto_de_las_claves(seeded_client, malo) == antes


def _foto_de_las_claves(client: TestClient, set_id: str) -> list[tuple[str, str, str]]:
    """Las versiones de plantilla del conjunto y sus entradas, letra a letra."""
    with client.app.state.session_factory() as session:
        versiones = (
            session.query(AnswerKeyVersionRecord)
            .filter(AnswerKeyVersionRecord.question_set_id == set_id)
            .order_by(AnswerKeyVersionRecord.version_no)
            .all()
        )
        foto: list[tuple[str, str, str]] = []
        for version in versiones:
            entradas = (
                session.query(AnswerKeyEntryRecord)
                .filter(AnswerKeyEntryRecord.answer_key_version_id == version.id)
                .order_by(AnswerKeyEntryRecord.question_version_id)
                .all()
            )
            foto.append((str(version.id), str(version.status), str(version.version_no)))
            foto.extend(
                (
                    str(entrada.question_version_id),
                    str(entrada.outcome),
                    str(entrada.correct_option_keys_json),
                )
                for entrada in entradas
            )
        return foto


def test_una_clave_derivada_no_se_puede_guardar_como_active(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """La base **rechaza** una clave derivada guardada como `active`: no es una regla de estilo.

    Es la prueba de que «nunca `active`» no depende de que alguien se acuerde: el `CHECK` de la
    tabla solo admite `derived`, así que la escritura imposible falla donde no se puede saltar.
    """
    rutas = _rutas(seeded_client)
    malo, preguntas = _conjunto(seeded_client, titulo="Banco con la clave mal")
    _catalogar(seeded_client, preguntas[0], tema="IV.1")
    _cuarentena(seeded_client, malo, KeyReliability.NO_FIABLE)
    _ancla(seeded_client, pregunta_id=preguntas[0], node_id=rutas["IV.1"], letra="b")
    assert _corrida(seeded_client, _ModeloDeMentira({preguntas[0]: "b"})) == 0
    ancla = _derivada(seeded_client, preguntas[0])
    assert ancla is not None

    with seeded_client.app.state.session_factory() as session:
        session.add(
            DerivedKeyRecord(
                question_version_id=preguntas[1],
                question_set_id=malo,
                correct_option_keys_json='["a"]',
                key_state="active",
                notes_letter="a",
                notes_quote=CITA,
                notes_anchor_id=ancla.notes_anchor_id,
                notes_key_status="active",
                model_letter="a",
                model_name="de-mentira",
                model_version="1",
                prompt_version="clave-derivada-1",
                actor=ACTOR,
                created_at=AHORA,
            )
        )
        with pytest.raises(IntegrityError) as fallo:
            session.commit()
    # La prueba dice **por qué** falla: no es una clave foránea ni una columna que falta, es el
    # `CHECK` que solo admite `derived`.
    assert "ck_derived_key_state" in str(fallo.value), fallo.value


def test_la_corrida_no_deriva_dos_veces_por_lo_mismo(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """Una pregunta ya derivada no se le vuelve a preguntar al modelo: no se paga dos veces."""
    rutas = _rutas(seeded_client)
    malo, preguntas = _conjunto(seeded_client, titulo="Banco con la clave mal")
    for pregunta in preguntas:
        _catalogar(seeded_client, pregunta, tema="IV.1")
    _cuarentena(seeded_client, malo, KeyReliability.NO_FIABLE)
    _ancla(seeded_client, pregunta_id=preguntas[0], node_id=rutas["IV.1"], letra="b")
    assert _corrida(seeded_client, _ModeloDeMentira({preguntas[0]: "b"})) == 0

    repo = SqlAlchemyDerivedKeyRepository(seeded_client.app.state.session_factory)
    preparado = Preparado(repo)

    assert preguntas[0] not in preparado.pedidas, "ya está derivada y no se vuelve a pedir"


# --- 2. lo que no coincide: el motivo, para la bandeja ---------------------------------------


def test_lo_que_no_coincide_queda_fuera_con_su_motivo(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """Las dos fuentes hablan y no dicen lo mismo: la pregunta sigue fuera y lo dice."""
    rutas = _rutas(seeded_client)
    malo, preguntas = _conjunto(seeded_client, titulo="Banco con la clave mal")
    for pregunta in preguntas:
        _catalogar(seeded_client, pregunta, tema="IV.1")
    _cuarentena(seeded_client, malo, KeyReliability.NO_FIABLE)
    _ancla(seeded_client, pregunta_id=preguntas[0], node_id=rutas["IV.1"], letra="b")
    _ancla(seeded_client, pregunta_id=preguntas[1], node_id=rutas["IV.1"], letra="b", cita=None)
    # La tercera no tiene ancla: los apuntes no la han mirado.

    assert _corrida(seeded_client, _ModeloDeMentira({preguntas[0]: "c", preguntas[1]: "b"})) == 0

    assert _derivada(seeded_client, preguntas[0]) is None
    assert _hueco(seeded_client, preguntas[0]).reason == "sin_coincidencia"
    assert _hueco(seeded_client, preguntas[1]).reason == "sin_cita"
    assert _hueco(seeded_client, preguntas[2]).reason == "sin_material"
    eventos = _hechos(seeded_client, accion=ACCION_HUECOS)
    assert len(eventos) == 1, "un evento por conjunto, no uno por pregunta"
    assert '"sin_coincidencia": 1' in str(eventos[0].after_json)


# --- 3. las claves oficiales no se derivan ---------------------------------------------------


def test_un_examen_oficial_no_se_deriva_y_queda_auditado(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """Un examen oficial con la clave en cuarentena **se rechaza**, con su motivo auditado."""
    rutas = _rutas(seeded_client)
    oficial, preguntas = _conjunto(
        seeded_client, titulo="Examen oficial", set_type=TIPO_OFICIAL, activar=False
    )
    _catalogar(seeded_client, preguntas[0], tema="IV.1")
    _cuarentena(seeded_client, oficial, KeyReliability.NO_FIABLE)
    _ancla(seeded_client, pregunta_id=preguntas[0], node_id=rutas["IV.1"], letra="b")

    assert _corrida(seeded_client, _ModeloDeMentira({preguntas[0]: "b"})) == 0

    assert _derivada(seeded_client, preguntas[0]) is None, "no se deriva nada de un oficial"
    rechazos = _hechos(seeded_client, accion=ACCION_RECHAZO)
    assert [evento.object_id for evento in rechazos] == [oficial]
    assert "examen oficial" in str(rechazos[0].after_json)


def test_un_ejercicio_de_la_age_no_se_deriva(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """Tercer camino de «oficial»: de la AGE con su respuesta publicada, sin plantilla."""
    rutas = _rutas(seeded_client)
    de_la_age, preguntas = _conjunto(seeded_client, titulo="Ejercicio de la AGE")
    _catalogar(seeded_client, preguntas[0], tema="IV.1")
    _procedencia(seeded_client, de_la_age, ambito="age")
    _cuarentena(seeded_client, de_la_age, KeyReliability.NO_FIABLE)
    _ancla(seeded_client, pregunta_id=preguntas[0], node_id=rutas["IV.1"], letra="b")

    assert _corrida(seeded_client, _ModeloDeMentira({preguntas[0]: "b"})) == 0

    assert _derivada(seeded_client, preguntas[0]) is None
    assert [evento.object_id for evento in _hechos(seeded_client, accion=ACCION_RECHAZO)] == [
        de_la_age
    ]


# --- 4. la pregunta derivada entra, y la que no la tiene sigue fuera -------------------------


def _composicion(node_id: str, *, count: int = 6) -> CompositionSpec:
    return CompositionSpec(
        parts=(PartSpec(code="temas", node_ids=(node_id,), count=count),),
        mode=SessionMode.PRACTICE,
    )


def test_la_pregunta_derivada_entra_en_el_test_con_su_letra(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """La pregunta vuelve al estudio y se corrige con la letra derivada, no con la clave."""
    rutas = _rutas(seeded_client)
    malo, preguntas = _conjunto(seeded_client, titulo="Banco con la clave mal")
    for pregunta in preguntas:
        _catalogar(seeded_client, pregunta, tema="IV.1")
    _cuarentena(seeded_client, malo, KeyReliability.NO_FIABLE)
    _ancla(seeded_client, pregunta_id=preguntas[0], node_id=rutas["IV.1"], letra="d")
    assert _corrida(seeded_client, _ModeloDeMentira({preguntas[0]: "d"})) == 0

    servicio = seeded_client.app.state.study_service
    resultado = servicio.compose(
        _composicion(rutas["IV.1"]), opposition_id=_oposicion(seeded_client)["id"]
    )

    congeladas = _congeladas(seeded_client, resultado.session.id)
    usadas = {str(congelada.question_version_id) for congelada in congeladas}
    assert usadas == {preguntas[0]}, "entra la derivada y solo la derivada"
    suya = next(c for c in congeladas if str(c.question_version_id) == preguntas[0])
    assert tuple(suya.frozen_correct_keys) == ("d",), "con la letra derivada, no con la del banco"
    assert resultado.parts[0].available == 1, "lo disponible es lo que tiene clave fiable"


def test_el_alumno_ve_la_marca_de_la_clave_derivada(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """La marca que ve el alumno, por la API que la pinta: `derived_key`, no `in_review`.

    Son dos cosas distintas y el contrato las separa: `in_review` avisa de una duda (el conjunto
    discrepa de los apuntes entre el 15 % y el 30 %) y `derived_key` dice de dónde sale la letra.
    Aquí el conjunto está `no_fiable` y la pregunta tiene clave derivada: la interfaz enseña
    «clave revisada automáticamente».
    """
    rutas = _rutas(seeded_client)
    malo, preguntas = _conjunto(seeded_client, titulo="Banco con la clave mal")
    for pregunta in preguntas:
        _catalogar(seeded_client, pregunta, tema="IV.1")
    _cuarentena(seeded_client, malo, KeyReliability.NO_FIABLE)
    _ancla(seeded_client, pregunta_id=preguntas[0], node_id=rutas["IV.1"], letra="b")
    assert _corrida(seeded_client, _ModeloDeMentira({preguntas[0]: "b"})) == 0

    creado = seeded_client.post(
        "/api/v1/student/tests",
        json={"nodes": ["IV.1"], "count": 1, "filter": "all", "feedback": "immediate"},
        headers=ALLOWED_ORIGIN,
    )
    assert creado.status_code == 201, creado.text
    arrancado = seeded_client.post(
        f"/api/v1/student/sessions/{creado.json()['id']}/start", headers=ALLOWED_ORIGIN
    )
    assert arrancado.status_code == 200, arrancado.text
    cuerpo = arrancado.json()

    assert cuerpo["total"] == 1, "la única pregunta que entra es la derivada"
    assert cuerpo["questions_derived"] == 1
    assert cuerpo["question"]["derived_key"] is True, "la interfaz pinta la marca con esto"
    assert cuerpo["question"]["in_review"] is False, "no está en revisión: está reconstruida"


def test_la_pregunta_sin_clave_fiable_sigue_fuera_aunque_el_conjunto_vuelva(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """La mitad del encargo que se olvida: las que no tienen clave fiable siguen fuera.

    Aunque el conjunto vuelva a los tests �”aquí se le devuelve `fiable` por la vía auditada�”, la
    pregunta con su motivo de fuera escrito **no entra**: no hay letra de la que fiarse. Y la que sí
    tiene clave derivada **sí** entra, con la del conjunto o sin ella.
    """
    rutas = _rutas(seeded_client)
    malo, preguntas = _conjunto(seeded_client, titulo="Banco con la clave mal")
    for pregunta in preguntas:
        _catalogar(seeded_client, pregunta, tema="IV.1")
    _cuarentena(seeded_client, malo, KeyReliability.NO_FIABLE)
    _ancla(seeded_client, pregunta_id=preguntas[0], node_id=rutas["IV.1"], letra="b")
    _ancla(seeded_client, pregunta_id=preguntas[1], node_id=rutas["IV.1"], letra="b", cita=None)
    # La 2 no coincide, la 1 no tiene cita y las demás no tienen ancla: las tres quedan fuera.
    assert (
        _corrida(
            seeded_client,
            _ModeloDeMentira({preguntas[0]: "b", preguntas[1]: "b", preguntas[2]: "b"}),
        )
        == 0
    )
    assert _derivada(seeded_client, preguntas[0]) is not None
    assert _hueco(seeded_client, preguntas[2]) is not None

    _cuarentena(seeded_client, malo, KeyReliability.FIABLE)

    servicio = seeded_client.app.state.study_service
    resultado = servicio.compose(
        _composicion(rutas["IV.1"]), opposition_id=_oposicion(seeded_client)["id"]
    )

    usadas = {
        str(congelada.question_version_id)
        for congelada in _congeladas(seeded_client, resultado.session.id)
    }
    assert usadas == {preguntas[0]}, (
        "vuelve la que tiene clave derivada; las que tienen motivo de fuera siguen fuera "
        "aunque el conjunto ya no esté en cuarentena"
    )


# --- 5. la decision, por conjunto y con su cifra ---------------------------------------------


def test_la_decision_queda_auditada_con_su_cifra_y_no_cambia_el_veredicto(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """La decisión de volver se toma **por conjunto y con su número**, y queda escrita.

    Y no cambia el veredicto del conjunto: devolverlo a `fiable` metería en los tests, por la puerta
    de atrás, las preguntas cuyo motivo de fuera sigue escrito.
    """
    rutas = _rutas(seeded_client)
    malo, preguntas = _conjunto(seeded_client, titulo="Banco con la clave mal")
    for pregunta in preguntas:
        _catalogar(seeded_client, pregunta, tema="IV.1")
    _cuarentena(seeded_client, malo, KeyReliability.NO_FIABLE)
    for pregunta in preguntas[:6]:
        _ancla(seeded_client, pregunta_id=pregunta, node_id=rutas["IV.1"], letra="b")
    assert _corrida(seeded_client, _ModeloDeMentira(dict.fromkeys(preguntas[:6], "b"))) == 0

    repo = SqlAlchemyDerivedKeyRepository(seeded_client.app.state.session_factory)
    decisiones = _decisiones(Preparado(repo), repo)

    assert [decision.set_id for decision in decisiones] == [malo]
    decision = decisiones[0]
    assert decision.preguntas == 12
    assert decision.derivadas == 6
    assert decision.con_clave == 6
    assert not decision.vuelve_a_los_tests, "6 de 12 no llega al 90 %"
    eventos = _hechos(seeded_client, accion=ACCION_DECISION)
    assert [evento.object_id for evento in eventos] == [malo]
    assert '"con_clave": 6' in str(eventos[0].after_json)
    assert '"vuelve_a_los_tests": false' in str(eventos[0].after_json)
    with seeded_client.app.state.session_factory() as session:
        fila = session.get(QuestionSetRecord, malo)
        assert fila is not None and fila.key_reliability == "no_fiable"


def test_un_conjunto_que_llega_al_liston_vuelve(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """Con 9 de 10 la decisión es volver, se dice con la cifra delante y **vuelve de verdad**.

    Volver es devolver el conjunto a los tests por la **vía auditada** (`set_verdict`, la misma
    puerta que puso la cuarentena): el veredicto cambia a `fiable` y queda su evento. Es la otra
    mitad de la regla del 90 %, y la que hace que el listón signifique algo.
    """
    rutas = _rutas(seeded_client)
    malo, preguntas = _conjunto(seeded_client, titulo="Banco con la clave mal", cuantas=10)
    for pregunta in preguntas:
        _catalogar(seeded_client, pregunta, tema="IV.1")
    _cuarentena(seeded_client, malo, KeyReliability.NO_FIABLE)
    for pregunta in preguntas[:9]:
        _ancla(seeded_client, pregunta_id=pregunta, node_id=rutas["IV.1"], letra="b")
    assert _corrida(seeded_client, _ModeloDeMentira(dict.fromkeys(preguntas[:9], "b"))) == 0

    repo = SqlAlchemyDerivedKeyRepository(seeded_client.app.state.session_factory)
    fiabilidad = SqlAlchemyKeyReliabilityRepository(seeded_client.app.state.session_factory)
    decision = _decisiones(Preparado(repo), repo, fiabilidad=fiabilidad)[0]

    assert decision.con_clave == 9
    assert decision.preguntas == 10
    assert decision.vuelve_a_los_tests
    assert "alcanza el liston" in decision.motivo()
    with seeded_client.app.state.session_factory() as session:
        fila = session.get(QuestionSetRecord, malo)
        assert fila is not None
        assert fila.key_reliability == "fiable", "el conjunto ha vuelto por la via auditada"
    # Y la pregunta que no tenía clave fiable sigue fuera: su motivo está escrito.
    assert _hueco(seeded_client, preguntas[9]) is not None
