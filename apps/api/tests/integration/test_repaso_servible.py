"""El repaso de fallos sirve lo que Inicio promete (F39, §2 y §3.6 de la revisión).

**Qué se comprueba, y por qué es lo que hay que comprobar.** El recorrido del 16-oct dijo que
«Repasar fallos» no funcionaba **por falta de material**; el propietario lo corrigió: es un fallo
del programa. Inicio prometía «5 preguntas para repasar hoy» y el repaso contestaba 409. La causa
era que los tests de práctica y el repaso usaban **dos políticas de claves distintas**: la práctica
aceptaba las derivadas y el repaso exigía plantilla `active`. Aquí se fija la regla que lo cierra:

- **la cifra de Inicio y lo que el repaso sirve son la misma cifra**, con la política de los
tests de práctica (`key_policy.clave_servible`) por los dos lados;
- **lo que no se puede corregir no se cuenta**: una pregunta fallada cuyo conjunto se archivó o cuya
  plantilla se sustituyó no se promete, porque ninguna sesión la puede servir;
- y **un fallo con clave derivada sí se repasa**, que es el caso que se perdía.

Las pruebas están escritas para **fallar con la política vieja**: la primera siembra dos fallos
vencidos de los que solo uno tiene clave, así que la cuenta ingenua (2) y el repaso (1) no
coinciden.
"""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from fastapi.testclient import TestClient

from opofuente.config import Settings
from opofuente.domain.derived_keys import RespuestaDelModelo, RespuestasBatch
from opofuente.domain.key_reliability import KeyReliability
from opofuente.domain.topic_notes import Coverage, KeyStatus, NotesCheck
from opofuente.infrastructure.db_models import AnswerKeyVersionRecord, ReviewItemRecord
from opofuente.infrastructure.key_reliability_repository import (
    SqlAlchemyKeyReliabilityRepository,
)
from opofuente.infrastructure.study_repository import SqlAlchemyStudyRepository
from opofuente.infrastructure.topic_notes_repository import SqlAlchemyTopicNotesRepository
from opofuente.tools.claves_derivadas import Preparado, _derivar, parse_args

ALLOWED_ORIGIN = {"Origin": "http://127.0.0.1:5173"}
AHORA = datetime(2026, 10, 17, 9, 0, tzinfo=UTC)
CITA = "La respuesta correcta es la b, según el artículo 18."


# --- el andamiaje ---------------------------------------------------------------------------------


def _texto(*, desde: int = 1, cuantas: int = 6) -> str:
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
    return dict(
        next(oposicion for opcion in [0] for oposicion in oposiciones if oposicion["active"])
    )


def _conjunto(
    client: TestClient,
    *,
    titulo: str,
    desde: int = 1,
    cuantas: int = 6,
    set_type: str = "private_bank",
    activar: bool = True,
) -> tuple[str, list[str]]:
    """Un conjunto con sus preguntas y, si se pide, su clave activa."""
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


def _catalogar(client: TestClient, pregunta_id: str, *, tema: str = "IV.1") -> None:
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
        actor="prueba:repaso-servible",
        reason="prueba del repaso con la política de claves (F39)",
    )
    assert cambiado, "el veredicto no se pudo poner"


def _ancla(
    client: TestClient,
    *,
    pregunta_id: str,
    node_id: str,
    letra: str | None,
    cita: str | None = CITA,
) -> None:
    """La primera fuente de la clave derivada: la comprobación de la corrida de un tema."""
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
                key_status=KeyStatus.ACTIVE,
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


def _derivar_todo(client: TestClient, modelo: _ModeloDeMentira) -> int:
    from opofuente.infrastructure.derived_key_repository import (
        SqlAlchemyDerivedKeyRepository,
    )

    repo = SqlAlchemyDerivedKeyRepository(client.app.state.session_factory)
    preparado = Preparado(repo)
    args = parse_args(["--derivar"])
    return _derivar(preparado, repo, modelo, args)  # type: ignore[arg-type]


def _sesion(client: TestClient, set_id: str, cantidad: int) -> str:
    oposicion = _oposicion(client)
    creada = client.post(
        "/api/v1/study-sessions",
        json={
            "opposition_id": oposicion["id"],
            "mode": "practice",
            "sources": [
                {
                    "question_set_id": set_id,
                    "part_code": "primera_parte",
                    "count": cantidad,
                    "include_reserves": False,
                }
            ],
            "convocation_version_id": oposicion["active_convocation"]["id"],
            "feedback": "immediate",
        },
        headers=ALLOWED_ORIGIN,
    )
    assert creada.status_code == 201, creada.text
    session_id = str(creada.json()["id"])
    arrancada = client.post(f"/api/v1/study-sessions/{session_id}/start", headers=ALLOWED_ORIGIN)
    assert arrancada.status_code == 200, arrancada.text
    return session_id


def _fallar(client: TestClient, session_id: str) -> str:
    """Contesta mal la pregunta que toca y devuelve la pregunta fallada.

    La clave de estas preguntas dice `a`; se contesta `d`, así que el desenlace es `wrong` y el
    intento entra en la cola de repaso.
    """
    actual = client.get(f"/api/v1/study-sessions/{session_id}/current-question").json()
    pregunta = actual["question"]
    assert pregunta is not None, "la sesión no tiene pregunta que contestar"
    respuesta = client.post(
        f"/api/v1/study-sessions/{session_id}/answers",
        json={
            "question_version_id": pregunta["question_version_id"],
            "chosen_option_keys": ["d"],
        },
        headers=ALLOWED_ORIGIN,
    )
    assert respuesta.status_code == 201, respuesta.text
    return str(pregunta["question_version_id"])


def _vencer_todo(client: TestClient) -> int:
    """Pone la cola de repaso entera en el pasado: sin eso, nada vence y no hay nada que repasar."""
    with client.app.state.session_factory() as session:
        filas = list(session.query(ReviewItemRecord).all())
        for fila in filas:
            fila.due_at = AHORA - timedelta(days=1)
        session.commit()
        return len(filas)


def _sustituir_la_plantilla(client: TestClient, set_id: str) -> None:
    """Deja el conjunto **sin plantilla activa**, como el duplicado que se archivó del importador.

    Es cómo el propietario acabó con cuatro fallos que ninguna sesión podía corregir: su conjunto se
    quedó con una plantilla sustituida y el examen vivo es otro.
    """
    with client.app.state.session_factory() as session:
        versiones = (
            session.query(AnswerKeyVersionRecord)
            .filter(AnswerKeyVersionRecord.question_set_id == set_id)
            .all()
        )
        assert versiones, "el conjunto no tenía plantilla que sustituir"
        for version in versiones:
            version.status = "superseded"
        session.commit()


def _repaso(client: TestClient) -> Any:
    oposicion = _oposicion(client)
    return client.post(
        "/api/v1/study-sessions",
        json={"opposition_id": oposicion["id"], "mode": "error_review"},
        headers=ALLOWED_ORIGIN,
    )


@pytest.fixture
def dos_bancos(seeded_settings: Settings) -> Iterator[dict[str, Any]]:
    """Dos bancos contestados: uno con su clave viva y otro al que se le sustituye la plantilla."""
    from opofuente.main import create_app

    app = create_app(seeded_settings)
    with TestClient(app) as client:
        bueno, preguntas_bueno = _conjunto(client, titulo="Banco con la clave viva")
        malo, preguntas_malo = _conjunto(
            client, titulo="Banco con la plantilla sustituida", desde=20
        )
        for pregunta in preguntas_bueno:
            _catalogar(client, pregunta)
        for pregunta in preguntas_malo:
            _catalogar(client, pregunta)

        fallada_buena = _fallar(client, _sesion(client, bueno, 2))
        fallada_mala = _fallar(client, _sesion(client, malo, 2))
        _sustituir_la_plantilla(client, malo)
        vencidas = _vencer_todo(client)
        assert vencidas == 2, f"la cola de repaso tenía {vencidas} preguntas y se esperaban 2"
        yield {
            "client": client,
            "bueno": bueno,
            "malo": malo,
            "fallada_buena": fallada_buena,
            "fallada_mala": fallada_mala,
        }


# --- 1. la cifra de Inicio y la que sirve el repaso ------------------------------------------


def test_la_cifra_de_inicio_es_la_que_el_repaso_sirve(dos_bancos: dict[str, Any]) -> None:
    """Dos fallos vencidos, uno servible: Inicio dice 1 y el repaso sirve 1. La misma cifra.

    Con la política vieja esta prueba falla en la primera línea: Inicio contaba los dos y el repaso
    «no hay ninguna plantilla activa» o dejaba uno fuera según por dónde entrara.
    """
    client: TestClient = dos_bancos["client"]

    resumen = client.get("/api/v1/student/overview").json()
    assert resumen["due_reviews"] == 1, "solo se promete lo que se puede corregir"

    respuesta = _repaso(client)
    assert respuesta.status_code == 201, respuesta.text
    sesion = respuesta.json()
    assert sesion["total_questions"] == resumen["due_reviews"], (
        "lo que Inicio promete y lo que el repaso sirve son la misma cifra"
    )
    # Y la sesión dice qué se ha quedado fuera, en vez de callarlo.
    nota = str(sesion["configuration"]["note"])
    assert "1 pregunta(s) de tu cola de repaso se han dejado fuera" in nota
    assert "no hay con" in nota, "el motivo, con sus palabras: no hay con qué corregirla"


def test_el_fallo_sin_clave_no_se_cuenta_ni_se_ofrece_en_fallos(dos_bancos: dict[str, Any]) -> None:
    """El fallo que no se puede corregir se enseña —es un hecho— pero no se promete."""
    client: TestClient = dos_bancos["client"]

    fallos = client.get("/api/v1/student/mistakes").json()
    assert fallos["total"] == 2, "las dos preguntas se fallaron: eso es un hecho"
    assert fallos["servable_total"] == 1, "de las dos, solo una se puede corregir"
    assert fallos["due_total"] == 1, "y solo una toca repasar hoy"

    # El que no tiene clave no se puede montar: no se ofrece un test que contestaría 409.
    sin_clave = [fallo for fallo in fallos["questions"] if fallo["stem"].endswith(("20:", "21:"))]
    for fallo in sin_clave:  # pragma: no branch - informativo si no cae ninguno
        assert fallo["due"] is False, "una pregunta sin clave no vence: no hay nada que repasar"


# --- 2. el caso que se pierde: un fallo con clave derivada ----------------------------------------


def test_un_fallo_con_clave_derivada_se_puede_repasar(seeded_settings: Settings) -> None:
    """La pregunta está en cuarentena y su clave derivada la devuelve al estudio: se repasa.

    Es el caso que hoy se pierde: la clave del conjunto no es de fiar, el repaso exigía plantilla
    `active` y la pregunta —que la práctica sí sirve, porque tiene dos fuentes independientes que
    dicen la misma letra— se quedaba sin poder repasar.
    """
    from opofuente.main import create_app

    app = create_app(seeded_settings)
    with TestClient(app) as client:
        rutas = _rutas(client)
        set_id, preguntas = _conjunto(client, titulo="Banco con la clave mal")
        for pregunta in preguntas:
            _catalogar(client, pregunta)
        _cuarentena(client, set_id, KeyReliability.NO_FIABLE)
        # La letra de los apuntes (con su cita) y la del modelo sin apuntes coinciden: hay derivada.
        _ancla(client, pregunta_id=preguntas[0], node_id=rutas["IV.1"], letra="b")
        assert _derivar_todo(client, _ModeloDeMentira({preguntas[0]: "b"})) == 0

        fallada = _fallar(client, _sesion(client, set_id, 1))
        assert fallada == preguntas[0], "la primera que cae es la que tiene la clave derivada"
        _vencer_todo(client)

        resumen = client.get("/api/v1/student/overview").json()
        assert resumen["due_reviews"] == 1, "la derivada cuenta: su letra tiene dos apoyos"

        respuesta = _repaso(client)
        assert respuesta.status_code == 201, respuesta.text
        assert respuesta.json()["total_questions"] == 1

        # Y se corrige con la letra derivada, no con la de la plantilla en cuarentena.
        congeladas = SqlAlchemyStudyRepository(client.app.state.session_factory).session_questions(
            str(respuesta.json()["id"])
        )
        assert [tuple(fila.frozen_correct_keys) for fila in congeladas] == [("b",)]


# --- 3. los datos raros: la fila del examen dice lo que el examen tiene ---------------------------


def test_la_fila_del_examen_cuenta_lo_que_el_examen_tiene(
    seeded_settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Un examen oficial con 85 preguntas y 0 reservas se ofrece como 80: lo que pide la parte.

    Es el §3.7 con los números del propietario: su cuestionario del INAP trae 135 preguntas (115
    ordinarias y 20 de reserva) y el examen de TAI sirve 85, porque la convocatoria publica 80 + 5
    para su primera parte. La fila decía 135 y el examen tenía 85.
    """
    from opofuente.main import create_app

    app = create_app(seeded_settings)
    with TestClient(app) as client:
        # Un examen oficial no puede tener la clave activa sin la plantilla oficial enlazada
        # (ADR-009), así que se importa sin activarla: lo que se comprueba aquí es el **tamaño** de
        # la fila y por qué no se puede hacer, no la activación.
        _, preguntas = _conjunto(
            client,
            titulo="TAI ingreso libre de prueba",
            cuantas=85,
            set_type="official_exam",
            activar=False,
        )
        for pregunta in preguntas:
            _catalogar(client, pregunta)

        examenes = client.get("/api/v1/student/official-exams").json()["exams"]
        assert len(examenes) == 1
        fila = examenes[0]
        assert fila["questions"] == 80, (
            "la parte pide 80 ordinarias y 5 de reserva: el examen tiene 80, no las 85 del conjunto"
        )
        assert fila["ready"] is False
        assert fila["blocked_reason"] == "faltan_respuestas"
        # Y la fecha: el título declara el año, así que la fila lo puede decir.
        assert fila["held_at"] is None
        assert fila["held_year"] is None, "este título de prueba no declara año"
