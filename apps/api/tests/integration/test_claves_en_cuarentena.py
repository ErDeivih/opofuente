"""La cuarentena de claves, en los sitios **reales** donde se eligen preguntas (§1 del objetivo).

No se prueba que exista una columna: se prueba que un conjunto con la clave en cuarentena
(`no_fiable`) **no entra** donde el alumno estudia, y que uno dudoso entra **marcado**. Los sitios
son los que son, y cada uno tiene su prueba:

1. `compose` — el test de varios temas y el simulacro;
2. `create_session` con conjuntos — la práctica por conjunto y el examen oficial;
3. `_create_topic_session` — la práctica de un tema, que cuenta lo que deja fuera;
4. `_create_review_session` — el repaso de los fallos;
5. `question_groups` — el denominador de la cobertura de los apuntes;
6. la marca «clave en revisión» de las dudosas, por donde la ve el alumno;
7. la **puerta de datos**: un conjunto que cruza el 30 % entra en cuarentena solo.

Todas menos la 7 empiezan con el veredicto puesto a mano por la vía auditada
(`set_verdict`), que es la misma que usará el propietario al reparar una clave.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from fastapi.testclient import TestClient

from opofuente.application.review_models import DueItemView, ReviewItemView
from opofuente.application.study_service import (
    CompositionSpec,
    CreateSessionInput,
    PartSpec,
    SourceInput,
)
from opofuente.config import Settings
from opofuente.domain.errors import UnsupportedError
from opofuente.domain.key_reliability import ACTOR, KeyReliability
from opofuente.domain.study import SessionMode
from opofuente.domain.topic_notes import Coverage, KeyStatus, Motivo, NotesCheck
from opofuente.infrastructure.clock import SystemClock
from opofuente.infrastructure.key_reliability_repository import (
    SqlAlchemyKeyReliabilityRepository,
)
from opofuente.infrastructure.study_repository import SqlAlchemyStudyRepository
from opofuente.infrastructure.topic_notes_repository import SqlAlchemyTopicNotesRepository
from opofuente.tools.apuntes import _puerta_de_claves

ALLOWED_ORIGIN = {"Origin": "http://127.0.0.1:5173"}


def _texto(*, desde: int = 1, cuantas: int = 12) -> str:
    """Preguntas distintas de verdad: el enunciado lleva su número, que la huella no normaliza."""
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


def _parte_de_la_convocatoria(client: TestClient) -> str:
    """El código de la parte **con preguntas** de la convocatoria sembrada.

    No vale cualquiera: la convocatoria publica también grupos (`ejercicio_unico`) que agrupan
    partes, y una sesión no se monta sobre un grupo. La primera parte es la del cuestionario.
    """
    oposicion = _oposicion(client)
    convocatoria = client.get(
        f"/api/v1/convocations/{oposicion['active_convocation']['id']}"
    ).json()
    partes = convocatoria.get("parts") or []
    codigos = [str(parte["code"]) for parte in partes]
    assert "primera_parte" in codigos, f"la convocatoria sembrada publica {codigos}"
    return "primera_parte"


def _conjunto(
    client: TestClient, *, titulo: str, desde: int = 1, cuantas: int = 12
) -> tuple[str, list[str]]:
    """Un conjunto con su clave activa y sus preguntas, listas para catalogar."""
    oposicion = _oposicion(client)
    creado = client.post(
        "/api/v1/question-sets",
        json={
            "title": titulo,
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
        json={"kind": "questions", "text": _texto(desde=desde, cuantas=cuantas)},
        headers=ALLOWED_ORIGIN,
    )
    assert importado.status_code == 200, importado.text
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


def _fiabilidad(client: TestClient) -> SqlAlchemyKeyReliabilityRepository:
    return SqlAlchemyKeyReliabilityRepository(client.app.state.session_factory)


def _cuarentena(client: TestClient, set_id: str, veredicto: KeyReliability) -> None:
    """Pone el veredicto por la vía auditada: la misma que usará el propietario al reparar."""
    cambiado = _fiabilidad(client).set_verdict(
        set_id,
        veredicto,
        now=SystemClock().now(),
        actor=ACTOR,
        reason="prueba de la cuarentena del §1",
    )
    assert cambiado, "el veredicto no se pudo poner"


def _congeladas(client: TestClient, session_id: str) -> tuple[Any, ...]:
    return SqlAlchemyStudyRepository(client.app.state.session_factory).session_questions(session_id)


# --- 1. compose: el test de varios temas y el simulacro -------------------------------------------


def test_el_test_de_varios_temas_no_lleva_preguntas_de_un_conjunto_en_cuarentena(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """`compose` es el embudo del test de temas y del simulacro: lo que no entra, no entra aquí."""
    rutas = _rutas(seeded_client)
    sano, preguntas_sanas = _conjunto(seeded_client, titulo="Banco sano")
    malo, preguntas_malas = _conjunto(seeded_client, titulo="Banco en cuarentena", desde=100)
    for pregunta in preguntas_sanas:
        _catalogar(seeded_client, pregunta, tema="IV.1")
    for pregunta in preguntas_malas:
        _catalogar(seeded_client, pregunta, tema="IV.1")
    _cuarentena(seeded_client, malo, KeyReliability.NO_FIABLE)

    servicio = seeded_client.app.state.study_service
    resultado = servicio.compose(
        _composicion(rutas["IV.1"], count=6),
        opposition_id=_oposicion(seeded_client)["id"],
    )

    congeladas = _congeladas(seeded_client, resultado.session.id)
    usadas = {str(congelada.question_version_id) for congelada in congeladas}
    assert usadas, "la sesión se monta con el material que sí es de fiar"
    assert not (usadas & set(preguntas_malas)), "ninguna pregunta del banco en cuarentena entró"
    assert usadas <= set(preguntas_sanas)
    assert resultado.parts[0].available == 12, "lo disponible son las doce del banco sano"
    assert sano, "el conjunto sano existe y se usó"


def _composicion(node_id: str, *, count: int) -> CompositionSpec:
    return CompositionSpec(
        parts=(PartSpec(code="test", node_ids=(node_id,), count=count),),
        mode=SessionMode.PRACTICE,
    )


# --- 2. create_session con conjuntos: práctica por conjunto y examen oficial ----------------------


def test_una_sesion_por_conjunto_se_niega_si_la_clave_esta_en_cuarentena(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """`_preguntas` es el embudo de la práctica por conjunto y del examen oficial."""
    malo, _ = _conjunto(seeded_client, titulo="Banco en cuarentena")
    _cuarentena(seeded_client, malo, KeyReliability.NO_FIABLE)

    servicio = seeded_client.app.state.study_service
    with pytest.raises(UnsupportedError) as fallo:
        servicio.create_session(
            CreateSessionInput(
                opposition_id=_oposicion(seeded_client)["id"],
                mode=SessionMode.PRACTICE,
                sources=(
                    SourceInput(
                        question_set_id=malo,
                        part_code=_parte_de_la_convocatoria(seeded_client),
                        count=5,
                    ),
                ),
            )
        )
    assert "cuarentena" in str(fallo.value)
    assert "no entran en tests" in str(fallo.value)


# --- 3. la práctica por tema ----------------------------------------------------------------------


def test_la_practica_por_tema_deja_fuera_lo_que_esta_en_cuarentena_y_lo_dice(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    rutas = _rutas(seeded_client)
    sano, preguntas_sanas = _conjunto(seeded_client, titulo="Banco sano")
    malo, preguntas_malas = _conjunto(seeded_client, titulo="Banco en cuarentena", desde=100)
    for pregunta in (*preguntas_sanas, *preguntas_malas):
        _catalogar(seeded_client, pregunta, tema="IV.2")
    _cuarentena(seeded_client, malo, KeyReliability.NO_FIABLE)

    servicio = seeded_client.app.state.study_service
    sesion = servicio.create_session(
        CreateSessionInput(
            opposition_id=_oposicion(seeded_client)["id"],
            mode=SessionMode.PRACTICE,
            sources=(),
            curriculum_node_id=rutas["IV.2"],
        )
    )

    congeladas = _congeladas(seeded_client, sesion.id)
    usadas = {str(congelada.question_version_id) for congelada in congeladas}
    assert usadas <= set(preguntas_sanas)
    assert not (usadas & set(preguntas_malas))
    nota = sesion.configuration.note or ""
    assert "cuarentena" in nota, "lo que se deja fuera, se dice"
    assert sano


# --- 4. el repaso de los fallos -------------------------------------------------------------------


class _ColaDeRepaso:
    """Una cola de repaso de mentira con **una** pregunta vencida, la que diga la prueba.

    Se sustituye la cola y no la regla: lo que se prueba es la regla —el repaso no pregunta por una
    clave en cuarentena—, no la cola, que tiene sus propias pruebas.
    """

    def __init__(self, vencida: DueItemView) -> None:
        self._vencida = vencida

    def due_for_session(self, *, opposition_id: str, limit: int) -> tuple[DueItemView, ...]:
        del opposition_id, limit
        return (self._vencida,)


def _vencida(client: TestClient, *, set_id: str, pregunta_id: str, part_code: str) -> DueItemView:
    ahora = datetime.now(UTC)
    return DueItemView(
        item=ReviewItemView(
            id="repaso-1",
            question_version_id=pregunta_id,
            opposition_id=_oposicion(client)["id"],
            learning_error_id=None,
            due_at=ahora - timedelta(days=1),
            interval_days=1,
            repetitions=0,
            lapses=1,
            last_reviewed_at=None,
            last_reason=None,
            created_at=ahora - timedelta(days=2),
            updated_at=ahora - timedelta(days=2),
        ),
        question_version_id=pregunta_id,
        question_set_id=set_id,
        stable_key="1",
        stem="La pregunta numero 1 del banco de prueba se contesta sola:",
        part_code=part_code,
        is_reserve=False,
        origin_type="private",
        overdue_days=1,
        explanation="se falló y no se ha repasado",
        options=(("a", "Opcion A"), ("b", "Opcion B")),
        session_id="sesion-1",
    )


def test_el_repaso_no_pregunta_por_una_clave_en_cuarentena(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    malo, preguntas_malas = _conjunto(seeded_client, titulo="Banco en cuarentena")
    _cuarentena(seeded_client, malo, KeyReliability.NO_FIABLE)

    servicio = seeded_client.app.state.study_service
    original = servicio._review
    try:
        servicio._review = _ColaDeRepaso(
            _vencida(
                seeded_client,
                set_id=malo,
                pregunta_id=preguntas_malas[0],
                part_code=_parte_de_la_convocatoria(seeded_client),
            )
        )
        with pytest.raises(UnsupportedError) as fallo:
            servicio.create_session(
                CreateSessionInput(
                    opposition_id=_oposicion(seeded_client)["id"],
                    mode=SessionMode.ERROR_REVIEW,
                    sources=(),
                )
            )
        assert "cuarentena" in str(fallo.value)
        assert "no se te puede preguntar" in str(fallo.value)
    finally:
        servicio._review = original


# --- 5. el denominador de la cobertura ------------------------------------------------------------


def test_la_cobertura_de_los_apuntes_no_cuenta_las_preguntas_en_cuarentena(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """`question_groups` es de donde sale el denominador de la puerta del 90 %."""
    rutas = _rutas(seeded_client)
    sano, preguntas_sanas = _conjunto(seeded_client, titulo="Banco sano")
    malo, preguntas_malas = _conjunto(seeded_client, titulo="Banco en cuarentena", desde=100)
    for pregunta in (*preguntas_sanas, *preguntas_malas):
        _catalogar(seeded_client, pregunta, tema="IV.2")

    notas = SqlAlchemyTopicNotesRepository(seeded_client.app.state.session_factory)
    antes = notas.question_groups(rutas["IV.2"])
    assert len(antes) == 24, "sin cuarentena, las veinticuatro cuentan"

    _cuarentena(seeded_client, malo, KeyReliability.NO_FIABLE)

    despues = notas.question_groups(rutas["IV.2"])
    assert len(despues) == 12, "las doce en cuarentena no cuentan en el denominador"
    firmas = {grupo.signature for grupo in despues}
    firmas_malas = {grupo.signature for grupo in antes if grupo.representative.set_id == malo}
    assert not (firmas & firmas_malas)
    assert sano


# --- 6. la marca «clave en revisión» --------------------------------------------------------------


def test_una_clave_dudosa_entra_en_el_test_con_la_marca_a_la_vista(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """Entre el 15 % y el 30 % el conjunto entra, pero el alumno lo ve: es el §1, literal."""
    rutas = _rutas(seeded_client)
    dudoso, preguntas = _conjunto(seeded_client, titulo="Banco dudoso")
    for pregunta in preguntas:
        _catalogar(seeded_client, pregunta, tema="IV.1")
    _cuarentena(seeded_client, dudoso, KeyReliability.DUDOSA)

    zona = seeded_client
    creado = zona.post(
        "/api/v1/student/tests",
        json={"nodes": ["IV.1"], "count": 3, "filter": "all", "feedback": "immediate"},
        headers=ALLOWED_ORIGIN,
    )
    assert creado.status_code == 201, creado.text
    sesion = creado.json()["id"]
    arrancado = zona.post(f"/api/v1/student/sessions/{sesion}/start", headers=ALLOWED_ORIGIN)
    assert arrancado.status_code == 200, arrancado.text
    cuerpo = arrancado.json()
    assert cuerpo["total"] == 3, "el dudoso entra en el test"
    assert cuerpo["questions_in_review"] == 3, "y las tres van marcadas"
    assert cuerpo["question"]["in_review"] is True
    assert rutas


# --- 7. la puerta de datos permanente -------------------------------------------------------------


def _anclas(client: TestClient, set_id: str, preguntas: list[str], *, tema: str) -> None:
    """Escribe anclas de verdad (paso E) con la letra de los apuntes que diga la prueba.

    Se usa la vía auditada —`save_checks`— y no SQL suelto: la puerta mide exactamente las filas que
    escribe el motor de apuntes, así que la prueba tiene que escribir esas mismas filas.
    """
    notas = SqlAlchemyTopicNotesRepository(client.app.state.session_factory)
    node_id = _rutas(client)[tema]
    node = notas.node(node_id)
    assert node is not None
    resultados = []
    for pregunta_id in preguntas:
        resultados.append(
            NotesCheck(
                question_version_id=pregunta_id,
                group_signature=f"firma-{pregunta_id}",
                section_key="udp",
                anchor="udp",
                coverage=Coverage.CONFLICTO,
                note=Motivo.LETRA_NO_COINCIDE,
                quote="la respuesta es la b",
                # Los apuntes dicen «b»; la clave guardada dice «a»: discrepancia en todas.
                letter="b",
                expected=("a",),
                key_status=KeyStatus.ACTIVE,
                attempts=2,
            )
        )
    assert node
    notas.save_checks(node_id, resultados, now=SystemClock().now())


def test_la_puerta_de_datos_pone_en_cuarentena_el_conjunto_que_cruza_el_30_por_ciento(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """Al terminar el tema, la discrepancia se recalcula y el que cruza el 30 % cae solo."""
    rutas = _rutas(seeded_client)
    set_id, preguntas = _conjunto(seeded_client, titulo="Banco que se tuerce", cuantas=18)
    for pregunta in preguntas:
        _catalogar(seeded_client, pregunta, tema="IV.2")
    # Las 18, con los apuntes diciendo «b» y la clave diciendo «a»: 18/18 = 100 %, por encima del
    # 30 %. Y 18 ≥ 15, que es el mínimo para poder opinar.
    _anclas(seeded_client, set_id, preguntas, tema="IV.2")

    fiabilidad = _fiabilidad(seeded_client)
    antes = fiabilidad.stored()[set_id]
    assert antes[0] == "fiable", "de entrada, y sin haberlo medido, es fiable"

    lineas = _puerta_de_claves(fiabilidad, ejecutar=True)

    despues = fiabilidad.stored()[set_id]
    assert despues[0] == "no_fiable", despues
    assert despues[1:] == (18, 18)
    assert any("no_fiable" in linea for linea in lineas)
    assert any("han cambiado de veredicto" in linea for linea in lineas)
    assert rutas

    # Y es **idempotente**: volver a pasar la puerta no cambia nada ni vuelve a auditar.
    segundas = _puerta_de_claves(fiabilidad, ejecutar=True)
    assert any("ningún conjunto ha cambiado" in linea for linea in segundas)
