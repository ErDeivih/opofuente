"""El clasificador de preguntas, con un modelo de mentira (F4).

Ninguna prueba de este fichero llama a DeepSeek: el cliente del modelo se **inyecta** y aquí se usa
un doble que contesta lo que la prueba necesita. Es lo que permite comprobar, sin gastar un céntimo
y sin depender de la red, lo que de verdad importa del clasificador:

- los **umbrales**: lo seguro se asigna, lo dudoso va a la cola de revisión (como propuesta, que no
  cuenta en ningún recuento) y lo que no se sabe no se escribe;
- el **fuera de temario**: se declara con su motivo y se puede consultar;
- la **selección**: por banco, de mayor a menor, y solo las preguntas sin tema;
- el **ensayo**: `--dry-run` llama al modelo y no escribe nada;
- el **prompt**: el temario sale de la base (los 33 temas y los 134 epígrafes de la convocatoria),
  no de una lista escrita a mano;
- el **comando**: sin la variable de entorno de la clave, para y lo dice.
"""

from __future__ import annotations

import os
from collections.abc import Mapping, Sequence
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from opofuente.application.topic_classification_service import TopicClassificationService
from opofuente.config import Settings, get_settings
from opofuente.domain.errors import ClassificationAlreadyRunningError, ExternalServiceError
from opofuente.domain.topic_classification import (
    ClassifiableQuestion,
    OutOfSyllabus,
    ProposalBatch,
    Syllabus,
    TopicProposal,
)
from opofuente.infrastructure.db import build_engine
from opofuente.infrastructure.profile_repository import SqlAlchemyProfileRepository
from opofuente.infrastructure.run_lock import ClassificationRunLock, current_run
from opofuente.infrastructure.topic_classification_repository import (
    SqlAlchemyTopicClassificationRepository,
)
from opofuente.tools import clasificar_preguntas

ALLOWED_ORIGIN = {"Origin": "http://127.0.0.1:5173"}

TEXTO = (
    "1. La Constitucion espanola se aprobo en:\n"
    "a) 1976\n"
    "b) 1978\n"
    "Respuesta correcta: b\n"
    "2. El plazo de alegaciones es de diez dias habiles.\n"
    "a) Verdadero\n"
    "b) Falso\n"
    "Respuesta correcta: a\n"
    "3. El regimen local de Aragon se regula en:\n"
    "a) su ley de administracion local\n"
    "b) la Constitucion\n"
    "Respuesta correcta: a\n"
    "4. La ley 39/2015 regula el procedimiento comun.\n"
    "a) Verdadero\n"
    "b) Falso\n"
    "Respuesta correcta: a\n"
)


class _PropositorFalso:
    """Un modelo de mentira: contesta por **enunciado** lo que la prueba le ha dicho que conteste.

    Guarda el temario que le llegó y los lotes que le pidieron, que es lo que permite comprobar el
    prompt y la selección sin llamar a nadie.
    """

    name = "falso"
    version = "prueba-1"

    def __init__(self, respuestas: Mapping[str, dict[str, Any]] | None = None) -> None:
        self.respuestas = dict(respuestas or {})
        self.lotes: list[list[str]] = []
        self.temario: Syllabus | None = None
        self.enunciados: list[str] = []

    def propose(
        self, questions: Sequence[ClassifiableQuestion], *, syllabus: Syllabus
    ) -> ProposalBatch:
        self.temario = syllabus
        self.lotes.append([pregunta.question_version_id for pregunta in questions])
        propuestas: list[TopicProposal] = []
        for pregunta in questions:
            self.enunciados.append(pregunta.stem)
            respuesta = self._respuesta(pregunta.stem)
            propuestas.append(
                TopicProposal(
                    question_version_id=pregunta.question_version_id,
                    topic_code=respuesta.get("tema"),
                    epigraph_code=respuesta.get("epigrafe"),
                    confidence=float(respuesta.get("confianza", 0.9)),
                    out_of_syllabus=(
                        OutOfSyllabus(respuesta["fuera_de_temario"])
                        if respuesta.get("fuera_de_temario")
                        else None
                    ),
                    note=respuesta.get("motivo"),
                )
            )
        return ProposalBatch(proposals=tuple(propuestas), input_tokens=500, output_tokens=50)

    def _respuesta(self, enunciado: str) -> dict[str, Any]:
        for clave, respuesta in self.respuestas.items():
            if clave in enunciado:
                return respuesta
        return {"tema": "I.1", "confianza": 0.9}


class _PropositorQueFalla:
    """Un modelo que no contesta: para probar que un fallo de fuera suelta la marca de corrida."""

    name = "falso"
    version = "prueba-1"

    def propose(
        self, questions: Sequence[ClassifiableQuestion], *, syllabus: Syllabus
    ) -> ProposalBatch:
        raise ExternalServiceError("el modelo no ha contestado")


def _conjunto(client: TestClient, *, titulo: str) -> dict[str, Any]:
    oposiciones = client.get("/api/v1/oppositions").json()
    activa = next(oposicion for oposicion in oposiciones if oposicion["active"])
    respuesta = client.post(
        "/api/v1/question-sets",
        json={"title": titulo, "opposition_id": activa["id"], "set_type": "private_bank"},
        headers=ALLOWED_ORIGIN,
    )
    assert respuesta.status_code == 201, respuesta.text
    return dict(respuesta.json())


def _preguntas(client: TestClient, set_id: str, texto: str = TEXTO) -> list[dict[str, Any]]:
    respuesta = client.post(
        f"/api/v1/question-sets/{set_id}/parse",
        json={"kind": "questions", "text": texto},
        headers=ALLOWED_ORIGIN,
    )
    assert respuesta.status_code == 200, respuesta.text
    return list(client.get("/api/v1/questions", params={"set_id": set_id}).json()["questions"])


def _clasificador(
    client: TestClient,
    propositor: _PropositorFalso,
    *,
    batch_size: int = 20,
    run_lock: ClassificationRunLock | None = None,
) -> TopicClassificationService:
    """El servicio de verdad, con el modelo de mentira: la escritura es la de la aplicación.

    La marca de corrida se construye como en el comando (misma base, misma oposición): es la que
    impide que dos clasificaciones se pisen, y por eso las pruebas la usan de verdad.
    """
    fabrica = client.app.state.session_factory
    return TopicClassificationService(
        classification=SqlAlchemyTopicClassificationRepository(fabrica),
        profiles=SqlAlchemyProfileRepository(fabrica),
        questions=client.app.state.question_service,
        proposer=propositor,
        lock=run_lock
        or ClassificationRunLock(fabrica, opposition_code="tai-age", hours_before_stale=0.0001),
        batch_size=batch_size,
    )


def _temas(client: TestClient, pregunta_id: str) -> list[dict[str, Any]]:
    return list(client.get(f"/api/v1/questions/{pregunta_id}/topics").json())


def _exclusiones(client: TestClient) -> list[dict[str, Any]]:
    return list(client.get("/api/v1/question-exclusions").json()["exclusions"])


def _aplanar(nodos: list[dict[str, Any]]) -> list[dict[str, Any]]:
    planos: list[dict[str, Any]] = []
    for nodo in nodos:
        planos.append(nodo)
        planos.extend(_aplanar(nodo.get("children", [])))
    return planos


def _rutas(client: TestClient) -> dict[str, str]:
    """El identificador de cada nodo del programa por su ruta (`I.1`, `I.1.1`…).

    Se comparan identificadores y no códigos oficiales porque el código oficial de un tema de TAI es
    el número que publica la convocatoria («1») y la ruta es la que se lee en la pantalla («I.1»).
    """
    oposiciones = client.get("/api/v1/oppositions").json()
    convocatoria = next(item["active_convocation"]["id"] for item in oposiciones if item["active"])
    programa = client.get(f"/api/v1/convocations/{convocatoria}/curriculum").json()
    return {str(nodo["path"]): str(nodo["id"]) for nodo in _aplanar(programa["nodes"])}


def _eventos(settings: Settings) -> list[dict[str, Any]]:
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.connect() as conexion:
            filas = conexion.execute(
                text(
                    "SELECT action, actor FROM audit_events "
                    "WHERE action IN ('question.mapped', 'question.out_of_syllabus') "
                    "ORDER BY created_at, id"
                )
            ).all()
    finally:
        engine.dispose()
    return [{"action": str(fila[0]), "actor": str(fila[1])} for fila in filas]


def _disponibles(client: TestClient) -> dict[str, int]:
    """Preguntas disponibles por tema, tal como las cuenta la zona del alumno."""
    bloques = client.get("/api/v1/student/syllabus").json()["blocks"]
    return {
        tema["code"]: tema["available_questions"] for bloque in bloques for tema in bloque["topics"]
    }


# --- los umbrales y las tres bandas ---------------------------------------------------------------


def test_lo_seguro_se_asigna_lo_dudoso_va_a_la_cola_y_lo_que_no_se_sabe_no_se_escribe(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """Las tres bandas, con las cuatro preguntas del banco y un modelo que contesta distinto a cada
    una: alta confianza, confianza media, abstención y fuera de temario."""
    conjunto = _conjunto(seeded_client, titulo="Banco de las tres bandas")
    preguntas = _preguntas(seeded_client, conjunto["id"])
    assert len(preguntas) == 4
    por_enunciado = {pregunta["stem"]: pregunta for pregunta in preguntas}

    propositor = _PropositorFalso(
        {
            "La Constitucion espanola": {"tema": "I.1", "confianza": 0.95, "motivo": "claro"},
            "plazo de alegaciones": {"tema": "I.2", "confianza": 0.6},
            "regimen local de Aragon": {
                "fuera_de_temario": "otra_administracion",
                "confianza": 0.8,
                "motivo": "ley autonómica",
            },
            "ley 39/2015": {"tema": None, "confianza": 0.9, "motivo": "no lo tengo claro"},
        }
    )

    informe = _clasificador(seeded_client, propositor).run("tai-age", banks=1)

    assert informe.assigned == 1
    assert informe.proposed == 1
    assert informe.out_of_syllabus == 1
    assert informe.nothing == 1
    assert informe.processed == 4
    assert informe.errors == 0

    # La de confianza alta: mapeo aceptado, que es lo que cuenta.
    rutas = _rutas(seeded_client)
    seguro = por_enunciado["La Constitucion espanola se aprobo en:"]
    mapeos = _temas(seeded_client, seguro["id"])
    assert len(mapeos) == 1
    assert mapeos[0]["curriculum_node_id"] == rutas["I.1"]
    assert mapeos[0]["status"] == "accepted"
    assert mapeos[0]["confidence"] == 0.95

    # La dudosa: está en la cola (propuesta provisional), y no cuenta en el progreso del alumno.
    dudosa = por_enunciado["El plazo de alegaciones es de diez dias habiles."]
    cola = _temas(seeded_client, dudosa["id"])
    assert len(cola) == 1
    assert cola[0]["curriculum_node_id"] == rutas["I.2"]
    assert cola[0]["status"] == "provisional", "sin confirmar: se ve, pero no se da por bueno"
    disponibles = _disponibles(seeded_client)
    assert disponibles["I.1"] == 1
    assert disponibles["I.2"] == 0, "una propuesta sin revisar no cuenta como pregunta del tema"

    # La que el modelo no tiene clara: no se escribe nada.
    sin_claro = por_enunciado["La ley 39/2015 regula el procedimiento comun."]
    assert _temas(seeded_client, sin_claro["id"]) == []

    # La de otra administración: fuera de temario, con su motivo, y sin mapeo.
    ajena = por_enunciado["El regimen local de Aragon se regula en:"]
    assert _temas(seeded_client, ajena["id"]) == []
    marcas = _exclusiones(seeded_client)
    assert [marca["question_version_id"] for marca in marcas] == [ajena["id"]]
    assert marcas[0]["reason"] == "otra_administracion"
    assert marcas[0]["note"] == "ley autonómica"

    # Y todo lo escrito se firma con el actor de la máquina.
    eventos = _eventos(seeded_settings)
    assert {evento["actor"] for evento in eventos} == {"llm:deepseek-flash"}
    assert [evento["action"] for evento in eventos].count("question.mapped") == 2
    assert [evento["action"] for evento in eventos].count("question.out_of_syllabus") == 1
    assert informe.estimated_cost_usd > 0


def test_un_codigo_que_no_esta_en_el_temario_se_cuenta_como_error_y_no_se_escribe(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """Un tema inventado por el modelo es un error de la propuesta: va al informe, no a la base."""
    conjunto = _conjunto(seeded_client, titulo="Banco del código inventado")
    pregunta = _preguntas(seeded_client, conjunto["id"])[0]
    propositor = _PropositorFalso({"La Constitucion": {"tema": "XX.99", "confianza": 0.99}})

    informe = _clasificador(seeded_client, propositor).run("tai-age", banks=1, limit=1)

    assert informe.errors == 1
    assert informe.assigned == 0
    assert _temas(seeded_client, pregunta["id"]) == []
    assert _eventos(seeded_settings) == []


def test_el_epigrafe_se_escribe_con_su_tema(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """El epígrafe dice dónde encaja y el tema mantiene los recuentos: se escriben los dos."""
    conjunto = _conjunto(seeded_client, titulo="Banco del epígrafe")
    pregunta = _preguntas(seeded_client, conjunto["id"])[0]
    propositor = _PropositorFalso(
        {"La Constitucion": {"tema": "I.1", "epigrafe": "I.1.1", "confianza": 0.9}}
    )

    _clasificador(seeded_client, propositor).run("tai-age", banks=1, limit=1)

    rutas = _rutas(seeded_client)
    mapeos = _temas(seeded_client, pregunta["id"])
    assert {mapeo["curriculum_node_id"] for mapeo in mapeos} == {rutas["I.1"], rutas["I.1.1"]}
    assert _disponibles(seeded_client)["I.1"] == 1, "el tema cuenta la pregunta del epígrafe"


# --- el ensayo ------------------------------------------------------------------------------------


def test_el_ensayo_llama_al_modelo_y_no_escribe_nada(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """`--dry-run` sirve para ver lo que haría: si escribiera, no sería un ensayo."""
    conjunto = _conjunto(seeded_client, titulo="Banco del ensayo")
    preguntas = _preguntas(seeded_client, conjunto["id"])

    informe = _clasificador(seeded_client, _PropositorFalso()).run("tai-age", banks=1, dry_run=True)

    assert informe.dry_run is True
    assert informe.assigned == len(preguntas), "el informe dice lo que haría"
    assert informe.input_tokens > 0, "el ensayo sí llama al modelo"
    for pregunta in preguntas:
        assert _temas(seeded_client, pregunta["id"]) == []
    assert _exclusiones(seeded_client) == []
    assert _eventos(seeded_settings) == []
    assert "ENSAYO" in "\n".join(informe.lines())


# --- la selección y el prompt ---------------------------------------------------------------------


def test_la_seleccion_es_por_banco_de_mayor_a_menor_y_solo_las_que_no_tienen_tema(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """Clasificar por bancos y de mayor a menor es lo que permite parar tras los dos primeros."""
    grande = _conjunto(seeded_client, titulo="Banco grande")
    grande_preguntas = _preguntas(seeded_client, grande["id"])
    pequeño = _conjunto(seeded_client, titulo="Banco pequeño")
    _preguntas(
        seeded_client,
        pequeño["id"],
        texto=(
            "1. Pregunta suelta del banco pequeño.\na) Verdadero\nb) Falso\nRespuesta correcta: a\n"
        ),
    )

    propositor = _PropositorFalso()
    servicio = _clasificador(seeded_client, propositor, batch_size=2)
    bancos = servicio.banks("tai-age")

    assert [banco.pending for banco in bancos] == [4, 1]
    assert bancos[0].set_id == grande["id"]

    # Un límite de una pregunta: se clasifica una y el resto del banco no se toca.
    informe = servicio.run("tai-age", banks=1, limit=1)
    assert informe.processed == 1
    assert len(propositor.lotes) == 1 and len(propositor.lotes[0]) == 1

    # Y una pregunta que ya tiene tema no se vuelve a pedir.
    informe2 = _clasificador(seeded_client, _PropositorFalso(), batch_size=10).run(
        "tai-age", banks=1
    )
    assert informe2.processed == 3, "la ya clasificada no se repite"
    assert len(grande_preguntas) == 4


def test_el_prompt_lleva_el_temario_real_de_la_convocatoria(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """El temario sale de la base: 33 temas y 134 epígrafes, con sus códigos oficiales."""
    conjunto = _conjunto(seeded_client, titulo="Banco del prompt")
    _preguntas(seeded_client, conjunto["id"])
    propositor = _PropositorFalso()

    _clasificador(seeded_client, propositor).run("tai-age", banks=1, limit=1)

    temario = propositor.temario
    assert temario is not None
    assert len(temario.topics) == 33, "los temas del programa sembrado, no una lista a mano"
    assert temario.epigraph_count == 134
    assert temario.topic("I.1") is not None
    epigrafe = temario.epigraph("IV.10.4")
    assert epigrafe is not None and epigrafe.topic_code == "IV.10"
    # El identificador de la pregunta viaja al modelo: sin él no se puede emparejar la respuesta.
    assert propositor.lotes[0], "el lote no puede ir vacío"


# --- el comando -----------------------------------------------------------------------------------


def test_el_comando_para_y_lo_dice_si_falta_la_clave(
    seeded_settings: Settings,
    seeded_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """La clave se lee del entorno: sin ella el comando para en vez de gastar una corrida."""
    monkeypatch.delenv(clasificar_preguntas.VARIABLE_DE_LA_CLAVE, raising=False)
    monkeypatch.setenv("OPOFUENTE_DATA_DIR", str(seeded_settings.data_dir))
    get_settings.cache_clear()
    try:
        codigo = clasificar_preguntas.main(["--bancos", "1"])
    finally:
        get_settings.cache_clear()
        os.environ.pop("OPOFUENTE_DATA_DIR", None)

    assert codigo == 2
    salida = capsys.readouterr()
    assert "DEEPSEEK_API_KEY" in salida.err
    assert _eventos(seeded_settings) == [], "no se ha escrito nada"


def test_el_comando_lista_los_bancos_sin_necesitar_la_clave(
    seeded_settings: Settings,
    seeded_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Ver lo que hay no cuesta nada: `--listar` no llama al modelo ni necesita clave."""
    conjunto = _conjunto(seeded_client, titulo="Banco que se lista")
    _preguntas(seeded_client, conjunto["id"])
    monkeypatch.delenv(clasificar_preguntas.VARIABLE_DE_LA_CLAVE, raising=False)
    monkeypatch.setenv("OPOFUENTE_DATA_DIR", str(seeded_settings.data_dir))
    get_settings.cache_clear()
    try:
        codigo = clasificar_preguntas.main(["--listar"])
    finally:
        get_settings.cache_clear()
        os.environ.pop("OPOFUENTE_DATA_DIR", None)

    assert codigo == 0
    salida = capsys.readouterr().out
    assert "Banco que se lista" in salida
    assert "4 sin tema" in salida


# --- la marca de corrida: dos clasificaciones a la vez se pisan -----------------------------------


def test_dos_corridas_a_la_vez_sobre_la_misma_base_la_segunda_se_niega(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """El fallo real del 8 de octubre: dos corridas propusieron temas a las mismas preguntas.

    La segunda tiene que **negarse**, no escribir encima: cada corrida calcula su lista de
    pendientes antes de que la otra escriba, así que dos a la vez dejan preguntas con dos temas
    propuestos.
    """
    conjunto = _conjunto(seeded_client, titulo="Banco de las dos corridas")
    _preguntas(seeded_client, conjunto["id"])
    fabrica = seeded_client.app.state.session_factory
    #: La corrida que ya está en marcha: se toma la marca como la toma un proceso vivo.
    en_marcha = ClassificationRunLock(fabrica, opposition_code="tai-age")
    segunda = _clasificador(
        seeded_client,
        _PropositorFalso(),
        run_lock=ClassificationRunLock(fabrica, opposition_code="tai-age"),
    )

    with en_marcha.hold():
        with pytest.raises(ClassificationAlreadyRunningError) as fallo:
            segunda.run("tai-age", banks=1)
        assert "en curso" in str(fallo.value)
        assert "tai-age" in str(fallo.value)

    # Y cuando la primera suelta la marca, la segunda sí puede: la marca no bloquea para siempre.
    informe = segunda.run("tai-age", banks=1)
    assert informe.processed == 4
    assert current_run(fabrica) is None, "al terminar, la marca se retira"


def test_la_marca_se_suelta_aunque_la_corrida_falle(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """Un fallo al llamar al modelo no puede dejar la clasificación bloqueada para siempre."""
    conjunto = _conjunto(seeded_client, titulo="Banco de la corrida que falla")
    _preguntas(seeded_client, conjunto["id"])
    fabrica = seeded_client.app.state.session_factory
    servicio = _clasificador(
        seeded_client,
        _PropositorQueFalla(),
        run_lock=ClassificationRunLock(fabrica, opposition_code="tai-age"),
    )

    with pytest.raises(Exception):  # noqa: B017 - el tipo lo prueba el cliente del modelo
        servicio.run("tai-age", banks=1)

    assert current_run(fabrica) is None, "la marca se suelta en el `finally`, no al terminar bien"
