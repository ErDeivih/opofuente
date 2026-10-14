"""La composición declarada (`StudyService.compose`): el test de varios temas y el simulacro real.

Es el §4 de `DECISIONES-Y-SIGUIENTE-TANDA-2026-10.md`, y lo que se comprueba aquí es lo que hace
falta para que exista **una sola forma** de montar un test:

- de qué nodos del programa sale cada parte y cuántas preguntas se piden;
- que la clave y la penalización se congelen por el **mismo** camino que en las sesiones que ya
  existían (`_clave_activa` + `FrozenQuestion`), sin un segundo sitio donde decidirlo;
- que un bloque traiga las preguntas de sus temas y que una pregunta no caiga dos veces;
- y el simulacro: 80 + 5 de la primera parte y 20 + 5 del supuesto elegido, con su **nota por
  parte** (el caso del propietario: 50 aciertos y 15 fallos → 28,125 sobre 50).
"""

from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient

from opofuente.application.study_service import (
    AnswerInput,
    CompositionSpec,
    PartSpec,
)
from opofuente.config import Settings
from opofuente.domain.study import Feedback, ScoringKind, SessionMode
from opofuente.infrastructure.question_repository import SqlAlchemyQuestionRepository
from opofuente.infrastructure.study_repository import SqlAlchemyStudyRepository

ALLOWED_ORIGIN = {"Origin": "http://127.0.0.1:5173"}


def _aplanar(nodos: list[dict[str, Any]]) -> list[dict[str, Any]]:
    planos: list[dict[str, Any]] = []
    for nodo in nodos:
        planos.append(nodo)
        planos.extend(_aplanar(nodo.get("children", [])))
    return planos


def _rutas(client: TestClient) -> dict[str, str]:
    """El identificador de cada nodo del programa por su ruta (`IV.1`, `I.1.1`…)."""
    oposiciones = client.get("/api/v1/oppositions").json()
    convocatoria = next(item["active_convocation"]["id"] for item in oposiciones if item["active"])
    programa = client.get(f"/api/v1/convocations/{convocatoria}/curriculum").json()
    return {str(nodo["path"]): str(nodo["id"]) for nodo in _aplanar(programa["nodes"])}


def _oposicion(client: TestClient) -> dict[str, Any]:
    oposiciones = client.get("/api/v1/oppositions").json()
    return dict(next(oposicion for oposicion in oposiciones if oposicion["active"]))


def _texto(preguntas: int, *, reservas: int, desde: int = 1) -> str:
    """Preguntas distintas de verdad: el enunciado lleva su número, que la huella no normaliza."""
    lineas: list[str] = []
    for numero in range(desde, desde + preguntas + reservas):
        marca = "[R] " if numero >= desde + preguntas else ""
        lineas.append(f"{numero}. {marca}El supuesto practico {numero} se resuelve en diez dias:")
        for indice in range(4):
            lineas.append(f"{chr(ord('a') + indice)}) Opcion {chr(ord('A') + indice)}")
        lineas.append("Respuesta correcta: a")
        lineas.append("")
    return "\n".join(lineas)


def _conjunto(
    client: TestClient,
    *,
    texto: str,
    titulo: str,
) -> tuple[str, list[dict[str, Any]]]:
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
    conjunto = creado.json()
    importado = client.post(
        f"/api/v1/question-sets/{conjunto['id']}/parse",
        json={"kind": "questions", "text": texto},
        headers=ALLOWED_ORIGIN,
    )
    assert importado.status_code == 200, importado.text
    claves = client.get(f"/api/v1/question-sets/{conjunto['id']}/answer-keys").json()
    activada = client.post(
        f"/api/v1/question-sets/{conjunto['id']}/answer-keys/{claves[0]['id']}/activate",
        headers=ALLOWED_ORIGIN,
    )
    assert activada.status_code == 200, activada.text
    preguntas = list(
        client.get(
            "/api/v1/questions",
            params={"set_id": conjunto["id"], "limit": 200},
        ).json()["questions"]
    )
    return str(conjunto["id"]), preguntas


def _catalogar(client: TestClient, pregunta_id: str, *, tema: str) -> None:
    rutas = _rutas(client)
    respuesta = client.post(
        f"/api/v1/questions/{pregunta_id}/topics",
        json={"curriculum_node_id": rutas[tema]},
        headers=ALLOWED_ORIGIN,
    )
    assert respuesta.status_code in (200, 201), respuesta.text


def _congeladas(client: TestClient, session_id: str) -> tuple[Any, ...]:
    """Las preguntas congeladas de una sesión, leídas de donde se guardan."""
    repositorio = SqlAlchemyStudyRepository(client.app.state.session_factory)
    return repositorio.session_questions(session_id)


def _nodos_de(client: TestClient, pregunta_id: str) -> tuple[str, ...]:
    repositorio = SqlAlchemyQuestionRepository(client.app.state.session_factory)
    return repositorio.node_ids_of_question(pregunta_id)


# --- el test de varios temas ----------------------------------------------------------------------


def test_un_test_de_tres_temas_de_bloques_distintos_se_compone_en_una_sola_forma(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """Tres temas de bloques distintos, nueve preguntas, y todas del mismo camino de composición."""
    rutas = _rutas(seeded_client)
    temas = ("I.1", "III.1", "IV.1")
    texto = _texto(12, reservas=0)
    _set_id, preguntas = _conjunto(seeded_client, texto=texto, titulo="Banco de tres temas")
    assert len(preguntas) == 12
    for indice, pregunta in enumerate(preguntas):
        _catalogar(seeded_client, pregunta["id"], tema=temas[indice // 4])

    servicio = seeded_client.app.state.study_service
    resultado = servicio.compose(
        CompositionSpec(
            parts=(PartSpec(code="test", node_ids=tuple(rutas[tema] for tema in temas), count=9),),
            mode=SessionMode.PRACTICE,
            label="Test de tres temas",
        ),
        opposition_id=_oposicion(seeded_client)["id"],
    )

    assert resultado.session.mode is SessionMode.PRACTICE
    assert resultado.session.total_questions == 9
    assert resultado.parts[0].requested == 9
    assert resultado.parts[0].selected == 9
    assert resultado.parts[0].available == 12
    assert resultado.short == (), "había material de sobra: no falta nada"

    # Las nueve salen de los tres temas, y de los tres: el reparto es proporcional a lo que hay.
    congeladas = _congeladas(seeded_client, resultado.session.id)
    assert len(congeladas) == 9
    por_tema: dict[str, int] = dict.fromkeys(temas, 0)
    for congelada in congeladas:
        for nodo in _nodos_de(seeded_client, str(congelada.question_version_id)):
            for tema in temas:
                if nodo == rutas[tema]:
                    por_tema[tema] += 1
    assert all(por_tema[tema] == 3 for tema in temas), por_tema

    # Y la clave se congeló por el camino de siempre: cada pregunta trae su respuesta correcta.
    assert all(congelada.frozen_correct_keys for congelada in congeladas)
    assert len({congelada.question_version_id for congelada in congeladas}) == 9, "sin repetidas"


def test_una_pregunta_de_dos_temas_no_cae_dos_veces(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """Una pregunta catalogada en dos de los temas pedidos entra **una vez**, no dos.

    Es la misma pregunta y responderla dos veces en el mismo test mediría dos veces lo mismo. El
    reparto la cuenta en el primero de los nodos pedidos y los demás la ven ya usada.
    """
    rutas = _rutas(seeded_client)
    temas = ("III.1", "IV.1")
    _set_id, preguntas = _conjunto(
        seeded_client, texto=_texto(6, reservas=0), titulo="Banco de dos temas"
    )
    for pregunta in preguntas:
        # Las seis están catalogadas en **los dos** temas.
        for tema in temas:
            _catalogar(seeded_client, pregunta["id"], tema=tema)

    servicio = seeded_client.app.state.study_service
    resultado = servicio.compose(
        CompositionSpec(
            parts=(PartSpec(code="test", node_ids=tuple(rutas[t] for t in temas), count=6),),
            mode=SessionMode.PRACTICE,
        ),
        opposition_id=_oposicion(seeded_client)["id"],
    )

    assert resultado.session.total_questions == 6
    assert resultado.parts[0].available == 6, "cada pregunta cuenta una vez en el total disponible"


# --- el simulacro real ----------------------------------------------------------------------------


def _simulacro(client: TestClient, *, primera: tuple[str, ...], supuesto: str) -> tuple[Any, str]:
    """Un simulacro con las dos partes del perfil y el supuesto elegido."""
    rutas = _rutas(client)
    _set_id, preguntas = _conjunto(
        client, texto=_texto(100, reservas=10), titulo="Banco del simulacro"
    )
    assert len(preguntas) == 110
    ordinarias = [pregunta for pregunta in preguntas if not pregunta.get("is_reserve")]
    reservas = [pregunta for pregunta in preguntas if pregunta.get("is_reserve")]
    assert len(ordinarias) == 100 and len(reservas) == 10
    for indice, pregunta in enumerate(ordinarias):
        tema = primera[indice // 40] if indice < 80 else supuesto
        _catalogar(client, pregunta["id"], tema=tema)
    for indice, pregunta in enumerate(reservas):
        _catalogar(client, pregunta["id"], tema=primera[0] if indice < 5 else supuesto)

    servicio = client.app.state.study_service
    compuesto = servicio.compose(
        CompositionSpec(
            parts=(
                PartSpec(
                    code="primera_parte",
                    node_ids=tuple(rutas[tema] for tema in primera),
                    count=80,
                    reserve=5,
                ),
                PartSpec(
                    code="segunda_parte",
                    node_ids=(rutas[supuesto],),
                    count=20,
                    reserve=5,
                    alternative_group="supuesto",
                ),
            ),
            mode=SessionMode.MOCK_EXAM,
            label="Simulacro real",
        ),
        opposition_id=_oposicion(client)["id"],
    )
    return compuesto, rutas[supuesto]


def test_el_simulacro_monta_80_mas_20_con_su_supuesto_y_su_nota_por_parte(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """El caso del propietario, de punta a punta: 50 aciertos y 15 fallos dan 28,125.

    Es la primera parte del simulacro (80 preguntas, 50 de máximo, un tercio por error), y se
    comprueba pasando por la composición real, no montando la regla a mano.
    """
    compuesto, _nodo_del_supuesto = _simulacro(
        seeded_client, primera=("IV.1", "IV.2"), supuesto="III.1"
    )
    sesion = compuesto.session
    servicio = seeded_client.app.state.study_service

    assert sesion.mode is SessionMode.MOCK_EXAM
    assert sesion.feedback is Feedback.AT_END, "un simulacro corrige al terminar"
    assert sesion.time_limit_minutes == 120, "el tiempo lo fija la convocatoria, no la petición"
    assert compuesto.parts[0].selected == 80
    assert compuesto.parts[0].reserves_selected == 5
    assert compuesto.parts[1].selected == 20
    assert compuesto.parts[1].reserves_selected == 5

    congeladas = _congeladas(seeded_client, sesion.id)
    assert len(congeladas) == 110
    por_parte = {
        codigo: [pregunta for pregunta in congeladas if pregunta.part_code == codigo]
        for codigo in ("primera_parte", "segunda_parte")
    }
    assert len(por_parte["primera_parte"]) == 85
    assert len(por_parte["segunda_parte"]) == 25
    assert sum(1 for p in congeladas if p.is_reserve) == 10

    # Se contesta: 50 bien y 15 mal en la primera parte (el resto, en blanco).
    servicio.start(sesion.id)
    for indice in range(65):
        actual = servicio.current_question(sesion.id)
        assert actual.question is not None
        pregunta = actual.question
        if indice < 50:
            elegidas = tuple(pregunta.frozen_correct_keys)
        else:
            elegidas = (
                next(
                    opcion.stable_key
                    for opcion in pregunta.options
                    if opcion.stable_key not in pregunta.frozen_correct_keys
                ),
            )
        servicio.answer(
            sesion.id,
            AnswerInput(
                question_version_id=pregunta.question_version_id,
                chosen_option_keys=elegidas,
                elapsed_ms=1000,
            ),
        )

    resultado = servicio.finish(sesion.id)
    partes = {parte.part_code: parte for parte in resultado.parts}
    primera = partes["primera_parte"]

    assert primera.correct == 50
    assert primera.wrong == 15
    assert primera.kind == ScoringKind.ESTIMATED.value
    assert primera.score.fraction == "225/8"
    assert primera.score.decimal == "28.1250"
    assert primera.passed is None, "una estimación no declara aprobado"
    assert "estimación" in (primera.verdict_note or "")
    assert partes["segunda_parte"].kind == ScoringKind.ESTIMATED.value
    assert resultado.total.kind == ScoringKind.ESTIMATED.value
    assert resultado.official_available is False


def test_dos_supuestos_del_mismo_grupo_no_se_montan_los_dos(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """El alumno elige III o IV: si llegan los dos, se compone el primero y no se duplica."""
    rutas = _rutas(seeded_client)
    _set_id, preguntas = _conjunto(
        seeded_client, texto=_texto(30, reservas=0), titulo="Banco de los dos supuestos"
    )
    for indice, pregunta in enumerate(preguntas):
        _catalogar(seeded_client, pregunta["id"], tema="III.1" if indice < 15 else "IV.1")

    servicio = seeded_client.app.state.study_service
    compuesto = servicio.compose(
        CompositionSpec(
            parts=(
                PartSpec(
                    code="segunda_parte",
                    node_ids=(rutas["III.1"],),
                    count=10,
                    alternative_group="supuesto",
                ),
                PartSpec(
                    code="segunda_parte",
                    node_ids=(rutas["IV.1"],),
                    count=10,
                    alternative_group="supuesto",
                ),
            ),
            mode=SessionMode.MOCK_EXAM,
        ),
        opposition_id=_oposicion(seeded_client)["id"],
    )

    assert len(compuesto.parts) == 1, "del grupo de partes excluyentes se monta una"
    assert compuesto.session.total_questions == 10
    congeladas = _congeladas(seeded_client, compuesto.session.id)
    nodos = {
        nodo
        for congelada in congeladas
        for nodo in _nodos_de(seeded_client, str(congelada.question_version_id))
    }
    assert nodos == {rutas["III.1"]}, "y es la primera: el supuesto de III"
