"""Los apuntes de un tema, de punta a punta y con un modelo de mentira (pasos B-E).

Ninguna prueba de este fichero llama a DeepSeek: el cliente del modelo se **inyecta** y aquí se usa
un
doble que contesta lo que la prueba necesita. Es lo que permite comprobar, sin gastar un céntimo y
sin
depender de la red, lo que de verdad importa del trabajo de apuntes:

- los **hechos** se guardan con el rastro de las preguntas de las que salen y no se duplican;
- el **esquema** sale de los epígrafes oficiales y el texto escrito no se pierde al recalcularlo;
- la **comprobación** es mecánica: la frase que el modelo dice copiar tiene que estar de verdad en
los
  apuntes, y sin ella la pregunta no se da por cubierta;
- un **hueco** se arregla con un añadido (una vuelta) y lo que sigue sin contestarse queda como duda
  con su motivo, no como cubierto;
- los apuntes **viajan dentro de la versión del tema**, que es el mecanismo de versiones que ya
había:
  archivar guarda el tema entero y una versión antigua se lee como se leyó.
"""

from __future__ import annotations

import os
from collections.abc import Sequence
from typing import Any

import pytest
from fastapi.testclient import TestClient

from opofuente.application.topic_notes_service import TopicNotesService
from opofuente.config import Settings, get_settings
from opofuente.domain.errors import (
    ClassificationAlreadyRunningError,
    ExternalServiceError,
)
from opofuente.domain.notes_quality import (
    PARRAFOS_REPETIDOS,
    marcas_internas,
    revisar_apuntes,
)
from opofuente.domain.rag import normalise
from opofuente.domain.topic_notes import (
    CategoriaIncidencia,
    ComprobacionBatch,
    FactKind,
    Hecho,
    HechosBatch,
    KeyStatus,
    MaterialPassage,
    Motivo,
    NoteSection,
    QuestionGroup,
    QuoteCheck,
    RedaccionBatch,
)
from opofuente.infrastructure.clock import SystemClock
from opofuente.infrastructure.dossier_repository import SqlAlchemyDossierRepository
from opofuente.infrastructure.run_lock import (
    CLAVE_APUNTES,
    ClassificationRunLock,
    current_run,
)
from opofuente.infrastructure.topic_notes_repository import SqlAlchemyTopicNotesRepository
from opofuente.tools import apuntes

ALLOWED_ORIGIN = {"Origin": "http://127.0.0.1:5173"}

#: Una pregunta que no dice de qué habla: ni nombra un artículo, ni una institución, ni un protocolo
#: Es la forma real de 209 grupos de I.1 («Una de las siguientes afirmaciones es falsa»), y la única
#: salida honesta cuando ni su enunciado ni sus hechos la sitúan es la bandeja del propietario.
TEXTO_SIN_MATERIA = (
    "1. Una de las siguientes afirmaciones es falsa:\n"
    "a) La primera\n"
    "b) La segunda\n"
    "Respuesta correcta: b\n"
)

#: Dos preguntas del **mismo epígrafe** y de materias distintas: es lo que deja ver si la
#: comprobación manda el epígrafe entero o solo los apartados de la pregunta.
TEXTO_DOS_MATERIAS = (
    "1. ¿Qué resuelve los nombres de dominio?\n"
    "a) SMTP\n"
    "b) DNS\n"
    "Respuesta correcta: b\n"
    "2. ¿Qué se usa para transferir páginas web?\n"
    "a) HTTP\n"
    "b) FTP\n"
    "Respuesta correcta: a\n"
)

TEXTO = (
    "1. ¿Cuántas capas tiene el modelo OSI?\n"
    "a) Cuatro\n"
    "b) Siete\n"
    "Respuesta correcta: b\n"
    "2. ¿Qué protocolo resuelve nombres de dominio?\n"
    "a) SMTP\n"
    "b) DNS\n"
    "Respuesta correcta: b\n"
)


class _ModeloFalso:
    """Un modelo de mentira que escribe apuntes con los hechos que le llegan y cita lo que hay.

    `falla_la_primera` sirve para provocar un hueco: la primera comprobación de ese grupo contesta
    «NO ESTÁ» y la segunda cita el añadido. Con eso se prueba la vuelta entera del paso E sin red.
    """

    name = "falso"
    version = "prueba-1"

    def __init__(
        self,
        *,
        letra: str = "b",
        falla_la_primera: bool = False,
        siempre_sin_frase: bool = False,
        dudosa: bool = False,
        hechos_por_grupo: int = 1,
    ) -> None:
        self.letra = letra
        self.falla_la_primera = falla_la_primera
        self.siempre_sin_frase = siempre_sin_frase
        self.dudosa = dudosa
        self.hechos_por_grupo = hechos_por_grupo
        self.lotes_hechos: list[list[str]] = []
        self.veces: dict[str, int] = {}
        self.apuntes_vistos: list[str] = []

    # --- paso B
    def hechos(
        self,
        grupos: Sequence[QuestionGroup],
        *,
        topic_code: str,
        topic_title: str,
        epigraphs: Sequence[tuple[str, str]],
    ) -> HechosBatch:
        self.lotes_hechos.append([grupo.signature for grupo in grupos])
        hechos = tuple(
            Hecho(
                # El hecho empieza por **su pregunta**, que es lo que hace el modelo de verdad: así
                # el reparto por materia (§2.1.1) manda cada hecho al apartado de lo que afirma, y
                # cada pregunta de este escenario tiene el suyo.
                text=(
                    f"Hecho {numero} del grupo {grupo.signature[:6]}: "
                    f"{grupo.representative.stem.strip()} tiene siete capas y se estudia por "
                    "niveles."
                ),
                kind=FactKind.TECNICO,
                epigraph_code=epigraphs[0][0],
                source_groups=(grupo.signature,),
                source_questions=grupo.question_ids,
                doubtful=self.dudosa,
                note="la plantilla contradice el material" if self.dudosa else None,
            )
            for grupo in grupos
            for numero in range(1, self.hechos_por_grupo + 1)
        )
        return HechosBatch(hechos=hechos, input_tokens=100 * len(grupos), output_tokens=20)

    # --- paso D
    def redactar(
        self,
        section: NoteSection,
        *,
        topic_code: str,
        topic_title: str,
        material: Sequence[MaterialPassage],
        es_tabla_de_puertos: bool = False,
    ) -> RedaccionBatch:
        # Cada hecho, su párrafo: es lo que hace el modelo de verdad, y es lo que deja ver la
        # repetición (el mismo texto con otro número de grupo delante).
        cuerpo = f"## {section.title}\n\n" + "\n\n".join(
            f"- {hecho.text}" for hecho in section.facts
        )
        return RedaccionBatch(
            titulo=section.title, markdown=cuerpo, input_tokens=200, output_tokens=100
        )

    # --- paso E
    def comprobar(self, grupos: Sequence[QuestionGroup], *, apuntes: str) -> ComprobacionBatch:
        self.apuntes_vistos.append(apuntes)
        checks: list[QuoteCheck] = []
        for grupo in grupos:
            veces = self.veces.get(grupo.signature, 0) + 1
            self.veces[grupo.signature] = veces
            if self.siempre_sin_frase or (self.falla_la_primera and veces == 1):
                checks.append(QuoteCheck(grupo.signature, None, None))
                continue
            checks.append(QuoteCheck(grupo.signature, self.letra, _frase_de(apuntes)))
        return ComprobacionBatch(checks=tuple(checks), input_tokens=300, output_tokens=40)

    def anadir(
        self, section: NoteSection, grupos: Sequence[QuestionGroup], hechos: Sequence[Hecho]
    ) -> RedaccionBatch:
        cuerpo = "### Añadido\n\n" + "\n".join(hecho.text for hecho in hechos)
        return RedaccionBatch(titulo=None, markdown=cuerpo, input_tokens=150, output_tokens=80)


def _frase_de(apuntes: str) -> str:
    """Una frase larga de verdad de los apuntes: el doble no puede inventarse la cita.

    Se saltan las líneas de título (`#`, que las añade el servicio para situar el apartado): un
    encabezado no justifica una respuesta y el servicio no lo acepta como cita.
    """
    for linea in apuntes.splitlines():
        limpia = linea.lstrip("- ").strip()
        if limpia.startswith("#"):
            continue
        if len(normalise(limpia)) >= 30:
            return limpia
    return apuntes[:60]


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


def _preguntas(client: TestClient, set_id: str, *, texto: str = TEXTO) -> list[dict[str, Any]]:
    respuesta = client.post(
        f"/api/v1/question-sets/{set_id}/parse",
        json={"kind": "questions", "text": texto},
        headers=ALLOWED_ORIGIN,
    )
    assert respuesta.status_code == 200, respuesta.text
    return list(client.get("/api/v1/questions", params={"set_id": set_id}).json()["questions"])


def _activar_clave(client: TestClient, set_id: str) -> None:
    """Activa la plantilla del conjunto: es lo que convierte la letra en criterio de
    comprobación."""
    claves = client.get(f"/api/v1/question-sets/{set_id}/answer-keys").json()
    assert claves, "el texto trae respuestas: tiene que haber una plantilla"
    respuesta = client.post(
        f"/api/v1/question-sets/{set_id}/answer-keys/{claves[0]['id']}/activate",
        headers=ALLOWED_ORIGIN,
    )
    assert respuesta.status_code == 200, respuesta.text


def _rutas(client: TestClient) -> dict[str, str]:
    """El identificador de cada nodo del programa por su ruta (`I.1`, `I.1.1`…)."""
    oposiciones = client.get("/api/v1/oppositions").json()
    convocatoria = next(item["active_convocation"]["id"] for item in oposiciones if item["active"])
    programa = client.get(f"/api/v1/convocations/{convocatoria}/curriculum").json()
    return {str(nodo["path"]): str(nodo["id"]) for nodo in _aplanar(programa["nodes"])}


def _aplanar(nodos: list[dict[str, Any]]) -> list[dict[str, Any]]:
    planos: list[dict[str, Any]] = []
    for nodo in nodos:
        planos.append(nodo)
        planos.extend(_aplanar(nodo.get("children", [])))
    return planos


def _asignar_tema(client: TestClient, pregunta_id: str, *, tema: str, epigrafe: str) -> None:
    rutas = _rutas(client)
    respuesta = client.post(
        f"/api/v1/questions/{pregunta_id}/topics",
        json={"curriculum_node_id": rutas[tema], "epigraph_node_id": rutas[epigrafe]},
        headers=ALLOWED_ORIGIN,
    )
    assert respuesta.status_code in (200, 201), respuesta.text


def _escenario(
    client: TestClient,
    *,
    tema: str = "IV.7",
    epigrafe: str = "IV.7.1",
    titulo: str,
    activar: bool = True,
) -> tuple[SqlAlchemyTopicNotesRepository, list[dict[str, Any]], str]:
    """Un conjunto con dos preguntas clasificadas en un tema, con su clave activa o en borrador."""
    conjunto = _conjunto(client, titulo=titulo)
    preguntas = _preguntas(client, conjunto["id"])
    assert len(preguntas) == 2
    if activar:
        _activar_clave(client, conjunto["id"])
    for pregunta in preguntas:
        _asignar_tema(client, pregunta["id"], tema=tema, epigrafe=epigrafe)
    fabrica = client.app.state.session_factory
    repositorio = SqlAlchemyTopicNotesRepository(fabrica)
    node_id = repositorio.node_id(tema)
    assert node_id is not None
    return repositorio, preguntas, node_id


class _ModeloConHechosCortos(_ModeloFalso):
    """Un modelo cuyos hechos dicen **solo** lo que dice su pregunta.

    El doble de siempre escribe el mismo relleno en todos sus hechos («tiene siete capas y se
    estudia
    por niveles»), y con dos preguntas distintas eso los hace casi iguales: la deduplicación los
    agrupa en uno y las dos preguntas acaban ancladas al mismo apartado. Para ver de qué apartado
    recibe el texto cada pregunta, sus hechos no pueden parecerse.
    """

    def hechos(
        self,
        grupos: Sequence[QuestionGroup],
        *,
        topic_code: str,
        topic_title: str,
        epigraphs: Sequence[tuple[str, str]],
    ) -> HechosBatch:
        hechos = tuple(
            Hecho(
                text=grupo.representative.stem.strip(),
                kind=FactKind.TECNICO,
                epigraph_code=epigraphs[0][0],
                source_groups=(grupo.signature,),
                source_questions=grupo.question_ids,
            )
            for grupo in grupos
        )
        return HechosBatch(hechos=hechos, input_tokens=10, output_tokens=10)


class _ModeloQueNoDiceNada(_ModeloFalso):
    """Un modelo cuyos hechos tampoco dicen de qué hablan: ni la pregunta ni el hecho sitúan nada.

    Es el otro caso de I.1, el que no se arregla con patrones: cuando ni el enunciado ni los hechos
    nombran una materia, no hay a qué agarrarse y la pregunta es del propietario.
    """

    def hechos(
        self,
        grupos: Sequence[QuestionGroup],
        *,
        topic_code: str,
        topic_title: str,
        epigraphs: Sequence[tuple[str, str]],
    ) -> HechosBatch:
        hechos = tuple(
            Hecho(
                text="El plazo para resolver es de tres meses desde la solicitud.",
                kind=FactKind.TECNICO,
                epigraph_code=epigraphs[0][0],
                source_groups=(grupo.signature,),
                source_questions=grupo.question_ids,
            )
            for grupo in grupos
        )
        return HechosBatch(hechos=hechos, input_tokens=10, output_tokens=10)


class _ModeloQueFalla(_ModeloFalso):
    """Un modelo que falla las primeras veces y después contesta: la red se cae, el lote no se va.

    Con cientos de llamadas, un 502 suelto es normal. Lo que se comprueba con este doble es que la
    llamada se reintenta y que, cuando por fin contesta, el lote se escribe como cualquier otro.
    """

    def __init__(self, *, fallos: int, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.fallos = fallos
        self.intentos = 0

    def hechos(
        self,
        grupos: Sequence[QuestionGroup],
        *,
        topic_code: str,
        topic_title: str,
        epigraphs: Sequence[tuple[str, str]],
    ) -> HechosBatch:
        self.intentos += 1
        if self.intentos <= self.fallos:
            raise ExternalServiceError("el modelo respondió 502")
        return super().hechos(
            grupos, topic_code=topic_code, topic_title=topic_title, epigraphs=epigraphs
        )


class _ModeloQueRepite(_ModeloFalso):
    """Un modelo que escribe el **mismo párrafo** en cada apartado: el defecto de los pilotos.

    Es lo que salía cuando cada apartado era la redacción de su lote puesto detrás de otro: el mismo
    texto, otro número de grupo delante. La revisión de forma tiene que verlo.
    """

    def redactar(
        self,
        section: NoteSection,
        *,
        topic_code: str,
        topic_title: str,
        material: Sequence[MaterialPassage],
        es_tabla_de_puertos: bool = False,
    ) -> RedaccionBatch:
        cuerpo = (
            f"## {section.title}\n\n"
            "El modelo de referencia OSI divide la comunicación en siete capas y cada una tiene su "
            "función propia; esta explicación se escribe igual en todos los apartados, que "
            "es exactamente el defecto que mide la revisión de forma.\n\n"
            + "\n\n".join(f"- {hecho.text}" for hecho in section.facts)
        )
        return RedaccionBatch(
            titulo=section.title, markdown=cuerpo, input_tokens=10, output_tokens=10
        )


class _ModeloQueEscribeMal(_ModeloFalso):
    """Un modelo que deja la forma rota: marcas internas y el título del apartado repetido.

    Es un doble del defecto de IV.7 (50 marcas `[fact N]` en el texto) y del de los apartados
    partidos (el mismo título otra vez dentro del mismo texto). Ninguna llamada sale de aquí.
    """

    def redactar(
        self,
        section: NoteSection,
        *,
        topic_code: str,
        topic_title: str,
        material: Sequence[MaterialPassage],
        es_tabla_de_puertos: bool = False,
    ) -> RedaccionBatch:
        cuerpo = (
            f"## {section.title}\n\n"
            + "\n".join(
                f"- {hecho.text} [fact {numero}]"
                for numero, hecho in enumerate(section.facts, start=1)
            )
            + f"\n\n## {section.title}\n"
        )
        return RedaccionBatch(
            titulo=section.title, markdown=cuerpo, input_tokens=10, output_tokens=10
        )


def _servicio(client: TestClient, modelo: _ModeloFalso, **kwargs: Any) -> TopicNotesService:
    fabrica = client.app.state.session_factory
    return TopicNotesService(
        repository=SqlAlchemyTopicNotesRepository(fabrica),
        dossier=SqlAlchemyDossierRepository(fabrica),
        model=modelo,
        workers=1,
        **kwargs,
    )


# --- el camino entero ----------------------------------------------------------------------------


def test_los_apuntes_se_escriben_y_se_comprueban_pregunta_a_pregunta(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """Los hechos, el apartado y el rastro de cada pregunta, con la cita verificada."""
    repositorio, preguntas, _node_id = _escenario(seeded_client, titulo="Apuntes del tema IV.7")
    modelo = _ModeloFalso()

    informe = _servicio(seeded_client, modelo).run("IV.7", now=SystemClock().now())

    assert informe.coverage.groups == 2
    assert informe.coverage.covered == 2
    assert informe.coverage.covered_primera_vuelta == 2
    assert informe.failed_batches == 0
    assert informe.ledger.calls > 0 and informe.estimated_cost_usd > 0

    # Los hechos se guardan con su rastro y sin duplicarse.
    hechos = repositorio.facts(informe.node_id)
    assert len(hechos) == 2
    assert all(hecho.source_groups and hecho.source_questions for hecho in hechos)

    # Un apartado por **materia** (el índice aprobado), con texto, con su anclaje y con sus hechos:
    # la pregunta del modelo OSI va a su apartado y la del vocabulario al suyo, no las dos al mismo.
    apartados = repositorio.sections(informe.node_id)
    assert [apartado.key for apartado in apartados] == ["osi-capas", "conceptos-del-modelo"]
    assert sum(len(apartado.facts) for apartado in apartados) == 2
    assert all(apartado.body_markdown for apartado in apartados)
    assert any("siete capas" in apartado.body_markdown for apartado in apartados)
    todo_el_texto = "\n\n".join(apartado.body_markdown for apartado in apartados)

    # Y el rastro pregunta a pregunta: cada una apunta a su párrafo con la frase que lo justifica.
    # La cita se copia de los apuntes del **epígrafe** (el modelo los ve juntos: la comprobación va
    # por epígrafe y todos sus apartados son el texto), así que lo que se exige es que la frase esté
    # en los apuntes, que es lo que se verifica de verdad.
    comprobadas = {
        comprobada.question_version_id: comprobada
        for comprobada in repositorio.checks(informe.node_id)
    }
    assert set(comprobadas) == {pregunta["id"] for pregunta in preguntas}
    for comprobada in comprobadas.values():
        assert comprobada.coverage.value == "covered"
        assert comprobada.key_status is KeyStatus.ACTIVE
        assert comprobada.quote is not None
        assert comprobada.quote in todo_el_texto, "la cita se copió de los apuntes"


def test_volver_a_ejecutar_no_vuelve_a_pedir_lo_que_ya_esta(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """Reanudar es no pagar dos veces: la segunda corrida no pide hechos ni comprueba de nuevo."""
    repositorio, _preguntas_del_tema, _node_id = _escenario(
        seeded_client, titulo="Apuntes que se reanudan"
    )
    primero = _ModeloFalso()
    _servicio(seeded_client, primero).run("IV.7", now=SystemClock().now())

    segundo = _ModeloFalso()
    informe = _servicio(seeded_client, segundo).run("IV.7", now=SystemClock().now())

    assert primero.lotes_hechos, "la primera corrida sí pide hechos"
    assert segundo.lotes_hechos == [], "la segunda no vuelve a pedir hechos"
    assert informe.coverage.covered == 2
    assert len(repositorio.facts(informe.node_id)) == 2, "y no duplica los hechos"


def test_una_comprobacion_caduca_cuando_el_apartado_se_reescribe(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """La cita se guarda con la huella del texto que se verificó: si el texto cambia, se
    recomprueba.

    Es el defecto que dejó a I.6 con sus 45 claves sospechosas citando frases que **no están** en
    sus
    apuntes: el texto se rehízo después de comprobarlo y la comprobación se reutilizaba por la
    firma
    del grupo, así que la bandeja del propietario enseñaba una prueba que nadie puede encontrar en
    el
    tema. Aquí se reescribe el apartado y se exige que la corrida siguiente vuelva a comprobar y que
    la cita guardada esté en el texto **de hoy**.
    """
    repositorio, _preguntas_del_tema, node_id = _escenario(
        seeded_client, titulo="Apuntes que se reescriben"
    )
    _servicio(seeded_client, _ModeloFalso()).run("IV.7", now=SystemClock().now())
    secciones = repositorio.sections(node_id)
    assert len(secciones) == 2
    cita_vieja = repositorio.checks(node_id)[0].quote
    assert cita_vieja is not None

    # Se reescriben **todos** los apartados del epígrafe: la comprobación va por epígrafe, así que
    # cambiar uno solo dejaría el texto que el modelo leyó casi igual.
    for seccion in secciones:
        repositorio.save_section_body(
            seccion,
            title=None,
            body=(
                f"## {seccion.title}\n\n"
                f"El apartado «{seccion.key}» se ha reescrito entero y ya no dice lo que decía: "
                "habla de otra cosa, con una frase larga que antes no estaba escrita aquí."
            ),
            needs_review_reason=None,
            model=None,
            now=SystemClock().now(),
        )
    nuevo_texto = "\n\n".join(apartado.body_markdown for apartado in repositorio.sections(node_id))
    assert cita_vieja not in nuevo_texto, "el texto de la cita vieja ya no está"

    segundo = _ModeloFalso()
    _servicio(seeded_client, segundo).run("IV.7", now=SystemClock().now())

    assert segundo.veces, "con el texto cambiado hay que volver a comprobar, no reutilizar la cita"
    guardadas = repositorio.checks(node_id)
    assert guardadas, "la comprobación se guarda"
    for comprobada in guardadas:
        assert comprobada.text_sha256 is not None, "la comprobación guarda la huella de su texto"
        assert comprobada.quote is not None
        assert comprobada.quote in nuevo_texto, "la cita vuelve a estar en los apuntes de hoy"


def test_un_hueco_se_arregla_con_un_anadido(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """La vuelta del paso E: si la frase no está, se añade el párrafo y se vuelve a comprobar."""
    repositorio, _preguntas_del_tema, _node_id = _escenario(
        seeded_client, titulo="Apuntes con un hueco"
    )
    modelo = _ModeloFalso(falla_la_primera=True)

    informe = _servicio(seeded_client, modelo).run("IV.7", now=SystemClock().now())

    assert informe.coverage.covered == 2
    assert informe.coverage.covered_tras_anadido == 2
    apartado = repositorio.sections(informe.node_id)[0]
    assert "### Añadido" in apartado.body_markdown
    assert all(comprobada.attempts == 2 for comprobada in repositorio.checks(informe.node_id))


def test_lo_que_no_se_puede_contestar_queda_señalado_y_no_cubierto(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """Tras dos vueltas, un hueco es una duda con su motivo: no se da por bueno un tema a medias."""
    repositorio, _preguntas_del_tema, _node_id = _escenario(
        seeded_client, titulo="Apuntes que no se pueden contestar"
    )
    modelo = _ModeloFalso(siempre_sin_frase=True)

    informe = _servicio(seeded_client, modelo).run("IV.7", now=SystemClock().now())

    assert informe.coverage.covered == 0
    assert informe.coverage.dudosas_apuntes == 2
    assert informe.coverage.por_motivo, "el motivo se cuenta para el informe"
    assert all(
        comprobada.coverage.value == "doubtful"
        for comprobada in repositorio.checks(informe.node_id)
    )
    # Y lo que no se ha podido rellenar queda en la bandeja del propietario **con su categoría**:
    # es la última vuelta del §2.1.4, y sin ella el resto se perdía al cerrar la terminal.
    incidencias = repositorio.incidents(informe.node_id)
    assert len(incidencias) == 2
    assert {incidencia.category.value for incidencia in incidencias} == {"hueco_sin_material"}
    assert all(incidencia.reason is Motivo.SIN_FRASE_EN_LOS_APUNTES for incidencia in incidencias)
    assert all("no contienen el dato" in incidencia.detail for incidencia in incidencias)
    assert informe.coverage.incidencias == 2


def test_una_clave_señalada_por_el_paso_b_se_cuenta_como_incidencia_de_la_pregunta(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """El paso B puede decir que la plantilla contradice el material: eso no lo arregla el texto."""
    repositorio, _preguntas_del_tema, _node_id = _escenario(
        seeded_client, titulo="Apuntes con la clave señalada"
    )
    modelo = _ModeloFalso(dudosa=True)

    informe = _servicio(seeded_client, modelo).run("IV.7", now=SystemClock().now())

    assert informe.hechos_dudosos == 2
    assert informe.coverage.incidencias_clave_marcada == 2
    assert all(
        comprobada.coverage.value == "doubtful"
        for comprobada in repositorio.checks(informe.node_id)
    ), "la pregunta va a revisión aunque los apuntes la contesten"


def test_si_el_esquema_se_mueve_los_apartados_viejos_no_se_quedan(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """Cuando un apartado guardado ya no está en el plan, el tema se rehace: un texto por apartado.

    Con el **índice aprobado** las claves de los apartados son las de sus materias, así que no se
    mueven al entrar hechos nuevos: el plan crece y los textos que ya estaban se conservan. Lo que
    sí deja apartados fuera del plan es un **cambio de catálogo** (una materia que se parte o
    desaparece), y eso se prueba aquí plantando el apartado viejo a mano: es lo que dejó la corrida
    anterior de este tema (26 apartados con claves `iv-7-1-1…`).

    Sin esto, el tema acabaría con los apartados viejos **y** los del plan nuevo: el mismo contenido
    dos veces y la comprobación mirando los dos.
    """
    repositorio, _preguntas_del_tema, node_id = _escenario(
        seeded_client, titulo="Apuntes con el esquema movido"
    )
    # Un apartado de una corrida con otro esquema: su clave no está en el plan del índice.
    repositorio.save_sections(
        node_id,
        [
            NoteSection(
                key="iv-7-1-1",
                epigraph_code="IV.7.1",
                title="Modelo OSI y modelo TCP/IP: capas y protocolos",
                anchor="iv-7-1-1",
                position=1,
                facts=(),
            )
        ],
        now=SystemClock().now(),
    )
    repositorio.save_section_body(
        repositorio.sections(node_id)[0],
        title=None,
        body="## Uno\n\nTexto de la corrida anterior que ya no vale para este plan.",
        needs_review_reason=None,
        model="falso",
        now=SystemClock().now(),
    )
    assert [apartado.key for apartado in repositorio.sections(node_id)] == ["iv-7-1-1"]

    # La corrida con el plan del índice: el apartado viejo sobra y se rehace todo.
    informe = _servicio(seeded_client, _ModeloFalso(hechos_por_grupo=2)).run(
        "IV.7", now=SystemClock().now()
    )

    claves = [apartado.key for apartado in repositorio.sections(node_id)]
    assert claves == ["osi-capas", "conceptos-del-modelo"], "solo quedan los del plan del índice"
    assert "el esquema se movió" in informe.notes
    assert all(
        "corrida anterior" not in apartado.body_markdown
        for apartado in repositorio.sections(node_id)
    )
    assert all(comprobada.coverage.value == "covered" for comprobada in repositorio.checks(node_id))


def test_cada_pregunta_apunta_al_apartado_que_tiene_sus_hechos(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """El rastro pregunta → párrafo tiene que apuntar al apartado donde están **sus** hechos.

    Es el fallo que tuvo esta pieza: al comprobar se usaban los hechos del paso B, que todavía no
    sabían a qué apartado pertenecían, y todas las preguntas de un epígrafe acababan apuntando a su
    primer apartado. Con el índice aprobado cada pregunta va a la materia de su enunciado, así que
    las dos de este escenario acaban en apartados distintos: si el enlace estuviera mal, las dos
    apuntarían al mismo.
    """
    repositorio, _preguntas_del_tema, node_id = _escenario(
        seeded_client, titulo="Apuntes con dos apartados en un epígrafe"
    )
    informe = _servicio(seeded_client, _ModeloFalso(hechos_por_grupo=3), lote_hechos=1).run(
        "IV.7", now=SystemClock().now()
    )

    apartados = repositorio.sections(node_id)
    assert [apartado.key for apartado in apartados] == ["osi-capas", "conceptos-del-modelo"]
    por_firma = {
        firma: hecho.section_key
        for hecho in repositorio.facts(node_id)
        for firma in hecho.source_groups
    }
    assert len(set(por_firma.values())) == 2, "cada grupo tiene sus hechos en un apartado distinto"
    comprobadas = {
        comprobada.question_version_id: comprobada for comprobada in repositorio.checks(node_id)
    }
    for grupo in repositorio.question_groups(node_id):
        ancla = comprobadas[grupo.representative.question_version_id]
        assert ancla.anchor == por_firma[grupo.signature]
    assert informe.coverage.covered == 2


def test_una_letra_distinta_de_la_clave_es_un_conflicto_y_no_una_pregunta_cubierta(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """La revisión del propietario: 96 preguntas contaban como cubiertas diciendo otra letra.

    Con la clave en borrador mandaba solo la frase, y una pregunta que los apuntes contestan «a»
    cuando su plantilla dice «b» no está cubierta: está en conflicto, y va a la cola de revisión con
    nota propia. Aquí se recorre el camino entero (hueco → añadido → conflicto) con un doble.
    """
    repositorio, preguntas, node_id = _escenario(
        seeded_client, titulo="Apuntes con la letra cambiada", activar=False
    )
    modelo = _ModeloFalso(letra="a")  # la plantilla dice «b»

    informe = _servicio(seeded_client, modelo).run("IV.7", now=SystemClock().now())

    assert informe.coverage.covered == 0, "una letra distinta de la clave no es cobertura"
    assert informe.coverage.conflicts == 2
    assert informe.coverage.conflicts_con_clave_borrador == 2
    assert informe.coverage.dudosas_apuntes == 0
    assert informe.coverage.en_revision == 2

    comprobadas = repositorio.checks(node_id)
    assert {comprobada.coverage.value for comprobada in comprobadas} == {"conflict"}
    assert all(comprobada.note is Motivo.LETRA_NO_COINCIDE for comprobada in comprobadas)
    assert all(comprobada.attempts == 2 for comprobada in comprobadas), "se le da la vuelta"
    # El conflicto llega a la bandeja **categorizado** y con la frase que lo demuestra: es lo que el
    # propietario necesita para decidir si el que está mal es la clave o los apuntes.
    incidencias = repositorio.incidents(node_id)
    assert len(incidencias) == 2
    assert {incidencia.category.value for incidencia in incidencias} == {"clave_sospechosa"}
    assert all(incidencia.phrase for incidencia in incidencias)
    assert all("otra letra que su clave" in incidencia.detail for incidencia in incidencias)

    # Y el tema lo cuenta donde se lee: cubiertas 0, en conflicto 2, con sus preguntas repartidas
    # entre los dos apartados del índice que les tocan.
    dossier = seeded_client.get(f"/api/v1/curriculum-nodes/{node_id}/dossier").json()
    assert dossier["notes"]["covered"] == 0
    assert dossier["notes"]["conflicts"] == 2
    assert dossier["notes"]["questions_total"] == 2
    assert [apartado["key"] for apartado in dossier["notes"]["sections"]] == [
        "osi-capas",
        "conceptos-del-modelo",
    ]
    en_conflicto = sorted(
        identificador
        for apartado in dossier["notes"]["sections"]
        for identificador in apartado["conflict_question_ids"]
    )
    assert en_conflicto == sorted(pregunta["id"] for pregunta in preguntas)


def test_con_la_clave_activa_una_letra_distinta_tambien_es_conflicto(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """Con clave activa el resultado ya no era «cubierta»: ahora se llama por su nombre."""
    repositorio, _preguntas_del_tema, node_id = _escenario(
        seeded_client, titulo="Apuntes con clave activa y letra cambiada"
    )
    modelo = _ModeloFalso(letra="a")

    informe = _servicio(seeded_client, modelo).run("IV.7", now=SystemClock().now())

    assert informe.coverage.conflicts == 2
    assert informe.coverage.conflicts_con_clave_activa == 2
    assert {comprobada.coverage.value for comprobada in repositorio.checks(node_id)} == {"conflict"}


def test_el_informe_mide_la_forma_de_los_apuntes_y_lo_dice(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """La revisión de forma va en el informe de la corrida: sin ella no se sabe qué se ha escrito.

    El doble escribe la misma frase en cada apartado, que es exactamente el defecto de los pilotos
    (cada apartado, la redacción de su lote): la revisión tiene que verlo y decirlo.
    """
    _repositorio, _preguntas_del_tema, _node_id = _escenario(
        seeded_client, titulo="Apuntes que se miden"
    )

    informe = _servicio(seeded_client, _ModeloQueRepite()).run("IV.7", now=SystemClock().now())

    assert informe.revision is not None
    assert informe.revision.palabras > 0
    assert PARRAFOS_REPETIDOS in {hallazgo.codigo for hallazgo in informe.revision.hallazgos}
    lineas = informe.lines()
    assert any("revision de forma: NO PASA" in linea for linea in lineas)
    assert any("de los párrafos se parecen a otro anterior" in linea for linea in lineas)


def test_las_marcas_y_el_encabezado_repetido_los_arregla_el_motor_al_guardar(
    seeded_settings: Settings,
    seeded_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Los dos defectos que el doble escribe los quita el motor: el tema pasa y se archiva.

    Antes esta prueba esperaba un 3: el tema no pasaba por las marcas internas del encargo
    (`[fact N]`) y por el apartado titulándose dos veces. Los dos se arreglan **al guardar**
    (`limpiar_andamios` quita las marcas y `sin_encabezados_repetidos` el encabezado repetido), así
    que lo que se comprueba es el arreglo: en el texto guardado no hay marcas ni encabezados
    repetidos, y el tema se da por bueno porque de verdad lo está.
    """
    _repositorio, _preguntas_del_tema, node_id = _escenario(
        seeded_client, titulo="Apuntes con la forma rota"
    )
    modelo = _ModeloQueEscribeMal()
    monkeypatch.setenv(apuntes.VARIABLE_DE_LA_CLAVE, "clave-de-prueba")
    monkeypatch.setenv("OPOFUENTE_DATA_DIR", str(seeded_settings.data_dir))
    get_settings.cache_clear()
    monkeypatch.setattr(apuntes, "DeepSeekNotesModel", lambda **_: modelo, raising=True)
    try:
        codigo = apuntes.main(["--tema", "IV.7", "--paralelo", "1", "--exigir-calidad"])
    finally:
        get_settings.cache_clear()
        os.environ.pop("OPOFUENTE_DATA_DIR", None)

    salida = capsys.readouterr()
    assert codigo == 0, "el motor quita los dos defectos, así que el tema pasa"
    assert "marca(s) interna(s)" not in salida.out, "las marcas del encargo no llegan al texto"
    assert "encabezado(s) repetidos" not in salida.out, "el encabezado repetido se quita al guardar"
    escritos = SqlAlchemyTopicNotesRepository(seeded_client.app.state.session_factory).sections(
        node_id
    )
    assert all(marcas_internas(apartado.body_markdown) == () for apartado in escritos)
    assert all("fact " not in apartado.body_markdown for apartado in escritos)
    revision = revisar_apuntes(escritos)
    assert revision.pasa
    versiones = seeded_client.get(f"/api/v1/curriculum-nodes/{node_id}/dossier/versions").json()
    assert versiones, "un tema que pasa la puerta sí archiva su versión"


def test_un_tema_con_parrafos_repetidos_no_se_da_por_bueno(
    seeded_settings: Settings,
    seeded_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Lo que el motor **no** puede arreglar solo sigue sin darse por bueno, y no archiva.

    El doble escribe el mismo párrafo en cada apartado, que es el defecto de los pilotos. Eso no se
    arregla quitando una marca ni un encabezado: hay que reescribir, y por eso el tema sale con 3 y
    sin versión archivada.
    """
    _repositorio, _preguntas_del_tema, node_id = _escenario(
        seeded_client, titulo="Apuntes que se repiten"
    )
    modelo = _ModeloQueRepite()
    monkeypatch.setenv(apuntes.VARIABLE_DE_LA_CLAVE, "clave-de-prueba")
    monkeypatch.setenv("OPOFUENTE_DATA_DIR", str(seeded_settings.data_dir))
    get_settings.cache_clear()
    monkeypatch.setattr(apuntes, "DeepSeekNotesModel", lambda **_: modelo, raising=True)
    try:
        codigo = apuntes.main(["--tema", "IV.7", "--paralelo", "1", "--exigir-calidad"])
    finally:
        get_settings.cache_clear()
        os.environ.pop("OPOFUENTE_DATA_DIR", None)

    salida = capsys.readouterr()
    assert codigo == 3, "un tema que no pasa las comprobaciones no se da por bueno"
    assert "de los párrafos se parecen a otro anterior" in salida.out
    versiones = seeded_client.get(f"/api/v1/curriculum-nodes/{node_id}/dossier/versions").json()
    assert versiones == [], "no se archiva la versión de un tema que no pasa"


def test_el_comando_enseña_el_indice_por_materias_sin_la_clave(
    seeded_settings: Settings,
    seeded_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """El esquema antes de redactar: se lee sin llamar a nadie y sin clave (es el paso C)."""
    _repositorio, _preguntas_del_tema, _node_id = _escenario(
        seeded_client, titulo="Apuntes que se esquematizan"
    )
    _servicio(seeded_client, _ModeloFalso()).run("IV.7", now=SystemClock().now())
    monkeypatch.delenv(apuntes.VARIABLE_DE_LA_CLAVE, raising=False)
    monkeypatch.setenv("OPOFUENTE_DATA_DIR", str(seeded_settings.data_dir))
    get_settings.cache_clear()
    try:
        codigo = apuntes.main(["--tema", "IV.7", "--esquema"])
    finally:
        get_settings.cache_clear()
        os.environ.pop("OPOFUENTE_DATA_DIR", None)

    salida = capsys.readouterr().out
    assert codigo == 0
    assert "Índice por materias de [IV.7]" in salida
    assert "Protocolos TCP/IP" in salida, "el índice enseña sus apartados con su materia"
    assert "una sola tabla en todo el tema" in salida


def test_el_esquema_de_un_tema_sin_catalogo_lo_dice_sin_inventarlo(
    seeded_settings: Settings,
    seeded_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _repositorio, _preguntas_del_tema, _node_id = _escenario(
        seeded_client, titulo="Apuntes de un tema sin catálogo"
    )
    monkeypatch.setenv("OPOFUENTE_DATA_DIR", str(seeded_settings.data_dir))
    get_settings.cache_clear()
    try:
        # I.2 todavía no tiene catálogo de materias (I.1 sí desde esta tanda): el índice de un tema
        # se define antes de redactar y no se inventa.
        codigo = apuntes.main(["--tema", "I.2", "--esquema"])
    finally:
        get_settings.cache_clear()
        os.environ.pop("OPOFUENTE_DATA_DIR", None)

    salida = capsys.readouterr().out
    assert codigo == 0
    assert "todavía no tiene catálogo de materias" in salida


# --- la versión del tema -------------------------------------------------------------------------


def test_una_llamada_que_falla_se_reintenta_y_no_pierde_el_lote(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """El lote que falla dos veces y contesta a la tercera se escribe: no se pierde lo ya pagado."""
    repositorio, _preguntas_del_tema, node_id = _escenario(
        seeded_client, titulo="Apuntes con una llamada que falla"
    )
    modelo = _ModeloQueFalla(fallos=2)

    informe = _servicio(seeded_client, modelo).run("IV.7", now=SystemClock().now())

    assert modelo.intentos == 3, "se reintenta antes de darse por vencido"
    assert informe.failed_batches == 0
    assert len(repositorio.facts(node_id)) == 2
    assert informe.coverage.covered == 2


def test_los_apuntes_van_dentro_de_la_version_del_tema(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """El mecanismo de versiones que ya existía: se archiva el tema con sus apuntes dentro."""
    repositorio, _preguntas_del_tema, node_id = _escenario(
        seeded_client, titulo="Apuntes que se versionan"
    )
    _servicio(seeded_client, _ModeloFalso()).run("IV.7", now=SystemClock().now())

    dossier = seeded_client.get(f"/api/v1/curriculum-nodes/{node_id}/dossier").json()
    assert dossier["notes"] is not None
    assert dossier["notes"]["covered"] == 2
    assert dossier["notes"]["sections_total"] == 2
    assert dossier["notes"]["prompt_template_version"]
    apartados = dossier["notes"]["sections"]
    assert [apartado["anchor"] for apartado in apartados] == [
        apartado.key for apartado in repositorio.sections(node_id)
    ]
    assert sum(len(apartado["question_ids"]) for apartado in apartados) == 2

    archivado = seeded_client.post(f"/api/v1/curriculum-nodes/{node_id}/dossier/versions")
    assert archivado.status_code == 201, archivado.text
    assert archivado.json()["created"] is True

    version_id = archivado.json()["version_id"]
    guardada = seeded_client.get(
        f"/api/v1/curriculum-nodes/{node_id}/dossier/versions/{version_id}"
    ).json()
    assert guardada["notes"]["covered"] == 2
    assert any(
        "siete capas" in apartado["body_markdown"] for apartado in guardada["notes"]["sections"]
    )

    # La versión guardada se lee **como se leyó**: reescribir el apartado después no la cambia.
    apartado_actual = repositorio.sections(node_id)[0]
    repositorio.save_section_body(
        apartado_actual,
        title=None,
        body="### Otro texto\n\nOtra cosa completamente distinta que se escribe después.",
        needs_review_reason=None,
        model="falso",
        now=SystemClock().now(),
        append=False,
    )
    otra_vez = seeded_client.get(
        f"/api/v1/curriculum-nodes/{node_id}/dossier/versions/{version_id}"
    ).json()
    guardados = {
        apartado["anchor"]: apartado["body_markdown"] for apartado in guardada["notes"]["sections"]
    }
    releidos = {
        apartado["anchor"]: apartado["body_markdown"] for apartado in otra_vez["notes"]["sections"]
    }
    assert releidos == guardados
    assert "Otra cosa" not in releidos[apartado_actual.anchor]


def test_el_comando_guarda_la_version_al_terminar(
    seeded_settings: Settings, seeded_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """El comando del piloto archiva el tema por el mecanismo que ya existía."""
    _repositorio, _preguntas_del_tema, node_id = _escenario(
        seeded_client, titulo="Apuntes del comando"
    )
    modelo = _ModeloFalso()
    monkeypatch.setenv(apuntes.VARIABLE_DE_LA_CLAVE, "clave-de-prueba")
    monkeypatch.setenv("OPOFUENTE_DATA_DIR", str(seeded_settings.data_dir))
    get_settings.cache_clear()
    monkeypatch.setattr(apuntes, "DeepSeekNotesModel", lambda **_: modelo, raising=True)
    try:
        codigo = apuntes.main(["--tema", "IV.7", "--paralelo", "1"])
    finally:
        get_settings.cache_clear()
        os.environ.pop("OPOFUENTE_DATA_DIR", None)

    assert codigo == 0
    versiones = seeded_client.get(f"/api/v1/curriculum-nodes/{node_id}/dossier/versions").json()
    assert versiones, "el comando tiene que dejar la versión guardada"


# --- las preguntas que el índice no puede situar --------------------------------------------------


def test_una_pregunta_que_no_cabe_en_el_indice_va_a_la_bandeja_y_no_para_la_corrida(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """Lo que no se puede situar no tumba el tema ni se esconde: se le enseña al propietario.

    Antes esto salía con `UnsupportedError`: el tema no se podía redactar **por una pregunta**, y el
    propietario se enteraba de que había un problema pero no de cuál era la pregunta. Ahora el árbol
    se escribe con lo que sí se puede situar, la que no cabe va a la bandeja con su motivo (sin
    cajón de «otros») y la puerta de cobertura la cuenta como no cubierta en vez de dejarla fuera.
    """
    conjunto = _conjunto(seeded_client, titulo="El banco de la pregunta que no cabe")
    preguntas = _preguntas(seeded_client, conjunto["id"], texto=TEXTO_SIN_MATERIA)
    assert len(preguntas) == 1
    _activar_clave(seeded_client, conjunto["id"])
    _asignar_tema(seeded_client, preguntas[0]["id"], tema="IV.7", epigrafe="IV.7.1")
    fabrica = seeded_client.app.state.session_factory
    repositorio = SqlAlchemyTopicNotesRepository(fabrica)
    node_id = repositorio.node_id("IV.7")
    assert node_id is not None

    informe = _servicio(seeded_client, _ModeloQueNoDiceNada()).run("IV.7", now=SystemClock().now())

    assert informe.indice is not None
    assert informe.indice.grupos_sin_materia == 1, "la pregunta no cabe en ninguna materia"
    assert informe.indice.pasa, "el árbol está bien formado: el defecto es de la pregunta"
    assert informe.sin_materia == 1
    # No se cuela por el borde: tiene clave y los apuntes no la contestan, así que cuenta en contra.
    assert informe.coverage.preguntas_con_clave == 1
    assert informe.coverage.preguntas_cubiertas_con_clave == 0
    # Y está en la bandeja, con su motivo y sin cajón: no hay ningún apartado «otros».
    incidencias = repositorio.incidents(node_id)
    assert [incidencia.reason for incidencia in incidencias] == [Motivo.SIN_MATERIA_EN_EL_INDICE]
    assert incidencias[0].category is CategoriaIncidencia.PREGUNTA_AMBIGUA
    assert "afirmaciones es falsa" in incidencias[0].detail
    assert all("otros" not in apartado.key for apartado in repositorio.sections(node_id))


def test_la_comprobacion_recibe_la_union_de_sus_apartados_y_lo_que_quepa_del_epigrafe(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """El texto que se comprueba es la unión de **sus** apartados y, si cabe, el resto del epígrafe.

    Las dos mitades importan: la unión es lo que pide el §2.1.1 y lo que hace que el encargo de I.1
    (nueve apartados de hasta 150 hechos por epígrafe) quepa en la ventana del modelo; el resto del
    epígrafe es lo que abarata la llamada por caché y lo que permite justificar una respuesta con
    frase del apartado hermano. Con dos apartados pequeños, la extensión entra y el texto los lleva
    los dos.
    """
    conjunto = _conjunto(seeded_client, titulo="La comprobación que no manda de más")
    preguntas = _preguntas(seeded_client, conjunto["id"], texto=TEXTO_DOS_MATERIAS)
    assert len(preguntas) == 2
    _activar_clave(seeded_client, conjunto["id"])
    for pregunta in preguntas:
        _asignar_tema(seeded_client, pregunta["id"], tema="IV.7", epigrafe="IV.7.2")
    modelo = _ModeloConHechosCortos()

    informe = _servicio(seeded_client, modelo).run("IV.7", now=SystemClock().now())

    # Un apartado por materia, y cada pregunta con los hechos que son suyos.
    assert [apartado.key for apartado in informe.sections] == ["dns", "web"]
    con_dns = next(texto for texto in modelo.apuntes_vistos if "nombres de dominio" in texto)
    assert "## dns ·" in con_dns
    assert "## web ·" in con_dns, "el epígrafe cabe entero: la llamada se abarata con él"


def test_el_texto_de_la_comprobacion_se_corta_por_presupuesto() -> None:
    """Cuando el epígrafe no cabe, se manda la unión de los apartados de la pregunta y nada más.

    Es lo que hace posible medir I.1: su primer epígrafe son nueve apartados de hasta 150 hechos
    (≈300.000 caracteres), y mandarlo entero no cabe en la ventana del modelo. El corte es
    determinista (por tamaño y orden de lectura), así que el mismo tema da el mismo texto y la misma
    huella.
    """
    from opofuente.application.topic_notes_service import _texto_de_apartados

    secciones = (
        NoteSection(
            key="dns",
            epigraph_code="IV.7.2",
            title="DNS",
            anchor="dns",
            position=1,
            body_markdown="El DNS resuelve los nombres de dominio y usa el puerto 53.",
        ),
        NoteSection(
            key="web",
            epigraph_code="IV.7.2",
            title="HTTP y HTTPS",
            anchor="web",
            position=2,
            body_markdown="HTTP es el protocolo de transferencia de hipertexto y usa el 80/TCP.",
        ),
    )

    entero, verificable = _texto_de_apartados(secciones, {"dns"})
    ajustado, _ = _texto_de_apartados(secciones, {"dns"}, presupuesto=10)

    assert "## dns ·" in entero and "## web ·" in entero
    assert "## web ·" not in ajustado, "sin presupuesto, solo lo que es de la pregunta"
    assert "## dns ·" in ajustado
    assert verificable.startswith("El DNS resuelve los nombres de dominio")


# --- la marca de corrida --------------------------------------------------------------------------


def test_dos_corridas_de_apuntes_a_la_vez_no_se_pisan(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """Escribir apuntes es lo más caro del proyecto: la segunda corrida se niega.

    El 10 de octubre de 2026 se lanzaron dos a la vez sobre I.6 y hubo que matar la segunda. La
    marca
    es la misma que usa el clasificador, con su propia clave: la clasificación y los apuntes no se
    bloquean el uno al otro, pero dos corridas de apuntes sí.
    """
    fabrica = seeded_client.app.state.session_factory
    en_marcha = ClassificationRunLock(
        fabrica, opposition_code="I.6", clave=CLAVE_APUNTES, que="corrida de apuntes"
    )
    segunda = ClassificationRunLock(
        fabrica, opposition_code="I.1", clave=CLAVE_APUNTES, que="corrida de apuntes"
    )

    with en_marcha.hold():
        # La marca de los apuntes no bloquea a la clasificación: son dos trabajos distintos.
        with ClassificationRunLock(fabrica, opposition_code="tai-age").hold():
            pass
        with pytest.raises(ClassificationAlreadyRunningError) as fallo:
            segunda.acquire()
        assert "apuntes" in str(fallo.value)
        assert "en curso" in str(fallo.value)
        assert CLAVE_APUNTES in str(fallo.value)
        assert current_run(fabrica, clave=CLAVE_APUNTES) is not None

    assert current_run(fabrica, clave=CLAVE_APUNTES) is None, "al terminar, la marca se retira"


# --- el comando ----------------------------------------------------------------------------------


def test_el_comando_para_y_lo_dice_si_falta_la_clave(
    seeded_settings: Settings,
    seeded_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """La clave se lee del entorno: sin ella el comando para en vez de gastar una corrida."""
    monkeypatch.delenv(apuntes.VARIABLE_DE_LA_CLAVE, raising=False)
    monkeypatch.setenv("OPOFUENTE_DATA_DIR", str(seeded_settings.data_dir))
    get_settings.cache_clear()
    try:
        codigo = apuntes.main(["--tema", "IV.7"])
    finally:
        get_settings.cache_clear()
        os.environ.pop("OPOFUENTE_DATA_DIR", None)

    assert codigo == 2
    assert apuntes.VARIABLE_DE_LA_CLAVE in capsys.readouterr().err


def test_el_comando_lista_lo_que_hay_sin_necesitar_la_clave(
    seeded_settings: Settings,
    seeded_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Ver lo que hay no cuesta nada: `--listar` no llama al modelo ni necesita clave."""
    repositorio, _preguntas_del_tema, _node_id = _escenario(
        seeded_client, titulo="Apuntes que se listan"
    )
    _servicio(seeded_client, _ModeloFalso()).run("IV.7", now=SystemClock().now())
    monkeypatch.delenv(apuntes.VARIABLE_DE_LA_CLAVE, raising=False)
    monkeypatch.setenv("OPOFUENTE_DATA_DIR", str(seeded_settings.data_dir))
    get_settings.cache_clear()
    try:
        codigo = apuntes.main(["--tema", "IV.7", "--listar"])
    finally:
        get_settings.cache_clear()
        os.environ.pop("OPOFUENTE_DATA_DIR", None)

    salida = capsys.readouterr().out
    assert codigo == 0
    assert "IV.7" in salida
    assert "hechos guardados: 2" in salida
    assert repositorio.node_id("IV.7") is not None


def test_el_comando_mide_el_tema_guardado_sin_llamar_a_nadie(
    seeded_settings: Settings,
    seeded_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """`--medir` da las cifras del tema sin clave y sin llamar al modelo: medir no cuesta dinero.

    Es lo que permite escribir en un informe la cobertura y la forma de un tema **medidas** y no
    heredadas de la corrida que las escribió: la cobertura sale de las comprobaciones guardadas y la
    forma, del texto que hay hoy en la base.
    """
    _escenario(seeded_client, titulo="Apuntes que se miden")
    _servicio(seeded_client, _ModeloFalso()).run("IV.7", now=SystemClock().now())
    monkeypatch.delenv(apuntes.VARIABLE_DE_LA_CLAVE, raising=False)
    monkeypatch.setenv("OPOFUENTE_DATA_DIR", str(seeded_settings.data_dir))
    get_settings.cache_clear()
    try:
        codigo = apuntes.main(["--tema", "IV.7", "--medir"])
    finally:
        get_settings.cache_clear()
        os.environ.pop("OPOFUENTE_DATA_DIR", None)

    salida = capsys.readouterr().out
    assert codigo == 0
    assert "puerta de cobertura" in salida
    assert "revision de forma" in salida
    assert "revision del indice" in salida
    assert "coste estimado 0.0000 $" in salida, "medir no gasta: el informe tiene que decirlo"


def test_el_comando_enseña_el_indice_y_su_revision_sin_la_clave(
    seeded_settings: Settings,
    seeded_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """`--esquema` dice si el árbol cuadra **antes** de pagar una corrida por él."""
    _escenario(seeded_client, titulo="El índice que se revisa")
    _servicio(seeded_client, _ModeloFalso()).run("IV.7", now=SystemClock().now())
    monkeypatch.delenv(apuntes.VARIABLE_DE_LA_CLAVE, raising=False)
    monkeypatch.setenv("OPOFUENTE_DATA_DIR", str(seeded_settings.data_dir))
    get_settings.cache_clear()
    try:
        codigo = apuntes.main(["--tema", "IV.7", "--esquema"])
    finally:
        get_settings.cache_clear()
        os.environ.pop("OPOFUENTE_DATA_DIR", None)

    salida = capsys.readouterr().out
    assert codigo == 0
    assert "Índice por materias" in salida
    assert "revision del indice: PASA" in salida


def test_un_tema_sin_preguntas_clasificadas_lo_dice_y_no_sigue(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """Sin preguntas no hay apuntes guiados por preguntas: se dice en vez de escribir relleno."""
    from opofuente.domain.errors import UnsupportedError

    fabrica = seeded_client.app.state.session_factory
    repositorio = SqlAlchemyTopicNotesRepository(fabrica)
    with pytest.raises(UnsupportedError):
        _servicio(seeded_client, _ModeloFalso()).run("IV.7", now=SystemClock().now())
    node_id = repositorio.node_id("IV.7")
    assert node_id is not None
    assert repositorio.facts(node_id) == ()
    assert repositorio.sections(node_id) == ()
