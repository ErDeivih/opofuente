"""La revisión de los apuntes en el panel: ver, leer, aprobar y rechazar (F24, §4.3 del objetivo).

Lo que se prueba, que es lo que el punto (4) del objetivo pide y lo que el propietario necesita:

1. **la tabla**: los temas del programa activo con su estado, y el **motivo con su cifra** de los
   que esperan una decisión. La tabla **mide solo los borradores** —los publicados ya pasaron las
   puertas— y eso se comprueba: el publicado sale `measured: false` y el borrador `measured: true`;
2. **la ficha de un borrador**: su texto apartado a apartado, y **el mismo texto** que sirve la zona
   del alumno (se comprueba contra `GET /student/topics/{codigo}/notes`);
3. **aprobar publica** cuando las dos puertas del §2.3 pasan —archiva la versión por el camino de
   siempre— y, cuando no pasan, deja el tema aprobado, **no** publica y dice **qué puerta** lo
   frena;
4. **rechazar exige motivo**: sin él es un 422 con su campo y **no se escribe nada**;
5. **la decisión y su evento entran en la misma escritura**, con el actor, el antes y el después, y
   el evento **no** copia la nota (es texto de una persona);
6. **la decisión sobrevive a una corrida del motor**: el motor vuelve a escribir sus comprobaciones
   y su bandeja y la fila de la decisión sigue donde estaba, con su nota.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from opofuente.config import Settings
from opofuente.domain.topic_notes import (
    CategoriaIncidencia,
    Coverage,
    IncidenciaDeApuntes,
    KeyStatus,
    Motivo,
    NotesCheck,
    NoteSection,
)
from opofuente.infrastructure.db import build_engine, build_session_factory
from opofuente.infrastructure.notes_review_repository import ACCION_REVISION, OBJETO_TEMA
from opofuente.infrastructure.topic_notes_repository import SqlAlchemyTopicNotesRepository
from opofuente.main import create_app

ALLOWED_ORIGIN = {"Origin": "http://127.0.0.1:5173"}

#: Los dos temas de la prueba, del programa sembrado: uno en borrador y otro publicado.
BORRADOR = "IV.1"
PUBLICADO = "IV.2"

#: El apartado y el texto del borrador: es texto de la prueba, no del propietario. La pregunta y el
#: texto hablan de **PowerShell**, que es lo que reconoce el índice de IV.1 (`catalogo_iv_1`): una
#: pregunta que el índice no sabe situar se cuenta además como no cubierta por
#: `Motivo.SIN_MATERIA_EN_EL_INDICE`, y entonces la cobertura mediría dos cosas a la vez. El texto
#: cabe en el tope de extensión (40 palabras por hecho, y sin hechos el tope es una vez 40) para que
#: la **forma** pase y lo que decida sea la cobertura.
APARTADO = ("administracion-de-windows", "IV.1.1", "La administración de Windows: PowerShell")
CUERPO = (
    "## PowerShell y los cmdlet\n\n"
    "Un cmdlet de PowerShell es un comando del sistema de administración de Windows.\n"
)
PREGUNTA = "¿Qué cmdlet de PowerShell muestra la información del equipo?"
OPCIONES = ("Get-ComputerInfo", "Get-Date")


@dataclass(frozen=True, slots=True)
class Panel:
    """Lo que la prueba necesita del panel montado: el cliente, los datos y qué hay dentro."""

    client: TestClient
    settings: Settings
    temas: dict[str, dict[str, Any]]
    preguntas: list[str]

    def fila(self, code: str) -> dict[str, Any]:
        """Una fila de la tabla de la revisión, leída por la ruta que lee la pantalla."""
        tabla = self.client.get("/api/v1/notes-review")
        assert tabla.status_code == 200, tabla.text
        return next(tema for tema in tabla.json()["topics"] if tema["code"] == code)

    def tabla(self) -> dict[str, Any]:
        tabla = self.client.get("/api/v1/notes-review")
        assert tabla.status_code == 200, tabla.text
        return tabla.json()

    def versiones(self, code: str) -> list[Any]:
        return _filas(
            self.settings,
            "SELECT id FROM dossier_snapshots WHERE curriculum_node_id = :nodo",
            {"nodo": str(self.temas[code]["id"])},
        )


def _settings(settings: Settings) -> Settings:
    """La misma configuración de datos, sin worker: la prueba no espera a ningún trabajo."""
    return Settings(data_dir=settings.data_dir, worker_enabled=False, _env_file=None)


def _aplanar(nodos: list[dict[str, Any]]) -> list[dict[str, Any]]:
    planos: list[dict[str, Any]] = []
    for nodo in nodos:
        planos.append(nodo)
        planos.extend(_aplanar(nodo.get("children", [])))
    return planos


def _temas(client: TestClient) -> dict[str, dict[str, Any]]:
    """El programa del panel: los temas de la **oposición activa**, por su código legible."""
    oposiciones = client.get("/api/v1/oppositions").json()
    activa = next(oposicion for oposicion in oposiciones if oposicion["active"] is True)
    programa = client.get(
        f"/api/v1/convocations/{activa['active_convocation']['id']}/curriculum"
    ).json()
    return {
        nodo["path"]: nodo for nodo in _aplanar(programa["nodes"]) if nodo["node_type"] == "topic"
    }


def _catalogar(client: TestClient, tema: dict[str, Any], cuantas: int = 1) -> list[str]:
    """Crea un conjunto con `cuantas` preguntas y su clave activa, y las cataloga en el tema."""
    oposiciones = client.get("/api/v1/oppositions").json()
    activa = next(oposicion for oposicion in oposiciones if oposicion["active"] is True)
    creado = client.post(
        "/api/v1/question-sets",
        json={
            "title": "Conjunto de la prueba de revisión de apuntes",
            "opposition_id": activa["id"],
            "set_type": "private_bank",
            "convocation_version_id": activa["active_convocation"]["id"],
        },
        headers=ALLOWED_ORIGIN,
    )
    assert creado.status_code == 201, creado.text
    set_id = str(creado.json()["id"])
    lineas: list[str] = []
    for numero in range(1, cuantas + 1):
        lineas.extend(
            [
                f"{numero}. {PREGUNTA}",
                f"a) {OPCIONES[0]} ({numero})",
                f"b) {OPCIONES[1]} ({numero})",
                "Respuesta correcta: a",
            ]
        )
    importado = client.post(
        f"/api/v1/question-sets/{set_id}/parse",
        json={"kind": "questions", "text": "\n".join([*lineas, ""])},
        headers=ALLOWED_ORIGIN,
    )
    assert importado.status_code == 200, importado.text
    claves = client.get(f"/api/v1/question-sets/{set_id}/answer-keys").json()
    activada = client.post(
        f"/api/v1/question-sets/{set_id}/answer-keys/{claves[0]['id']}/activate",
        headers=ALLOWED_ORIGIN,
    )
    assert activada.status_code == 200, activada.text
    listado = client.get("/api/v1/questions", params={"set_id": set_id}).json()
    identificadores: list[str] = []
    for pregunta in listado["questions"]:
        asignada = client.post(
            f"/api/v1/questions/{pregunta['id']}/topics",
            json={"curriculum_node_id": tema["id"]},
            headers=ALLOWED_ORIGIN,
        )
        assert asignada.status_code in (200, 201), asignada.text
        identificadores.append(str(pregunta["id"]))
    return identificadores


def _firmas(settings: Settings, node_id: str) -> dict[str, str]:
    """La firma de grupo de cada pregunta del tema, leída del repositorio (no inventada).

    La cobertura se cuenta buscando esa firma: una firma inventada daría un tema con 0 cubiertas y
    la prueba mediría otra cosa de la que cree.
    """
    engine = build_engine(settings.data_paths.database)
    try:
        notas = SqlAlchemyTopicNotesRepository(build_session_factory(engine))
        return {
            pregunta.question_version_id: grupo.signature
            for grupo in notas.question_groups(node_id)
            for pregunta in grupo.questions
        }
    finally:
        engine.dispose()


def _escribir_apuntes(
    settings: Settings,
    node_id: str,
    *,
    cubiertas: list[str],
    sin_cubrir: list[str] | None = None,
) -> None:
    """Escribe el apartado del tema y sus comprobaciones, por el repositorio de verdad."""
    ahora = datetime.now(UTC)
    clave, epigrafe, titulo = APARTADO
    firmas = _firmas(settings, node_id)
    engine = build_engine(settings.data_paths.database)
    try:
        notas = SqlAlchemyTopicNotesRepository(build_session_factory(engine))
        guardados = notas.save_sections(
            node_id,
            [
                NoteSection(
                    key=clave,
                    epigraph_code=epigrafe,
                    title=titulo,
                    anchor=clave,
                    position=1,
                )
            ],
            now=ahora,
        )
        notas.save_section_body(
            guardados[0],
            title=None,
            body=CUERPO,
            needs_review_reason=None,
            model="modelo-de-la-prueba",
            now=ahora,
        )
        comprobaciones = [
            NotesCheck(
                question_version_id=pregunta,
                group_signature=firmas[pregunta],
                section_key=clave,
                anchor=clave,
                coverage=Coverage.CUBIERTA,
                note=None,
                quote="Un cmdlet de PowerShell es un comando",
                letter="a",
                expected=("a",),
                key_status=KeyStatus.ACTIVE,
                attempts=1,
            )
            for pregunta in cubiertas
        ]
        comprobaciones.extend(
            NotesCheck(
                question_version_id=pregunta,
                group_signature=firmas[pregunta],
                section_key=clave,
                anchor=clave,
                coverage=Coverage.HUECO,
                note=Motivo.SIN_FRASE_EN_LOS_APUNTES,
                quote=None,
                letter=None,
                expected=("a",),
                key_status=KeyStatus.ACTIVE,
                attempts=1,
            )
            for pregunta in sin_cubrir or []
        )
        notas.save_checks(node_id, comprobaciones, now=ahora)
    finally:
        engine.dispose()


def _archivar_version(settings: Settings, node_id: str) -> None:
    """Archiva una versión del tema: es lo que lo convierte en **publicado**."""
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.begin() as conexion:
            conexion.execute(
                text(
                    "INSERT INTO dossier_snapshots (id, curriculum_node_id, content_hash, "
                    "built_at, created_at, sources_count, passages_count, payload_json) "
                    "VALUES ('version-de-la-prueba', :nodo, :hash, '2026-10-12 08:00:00', "
                    "'2026-10-12 08:00:00', 0, 0, '{}')"
                ),
                {"nodo": node_id, "hash": "a" * 64},
            )
    finally:
        engine.dispose()


def _filas(settings: Settings, sentencia: str, parametros: dict[str, object]) -> list[Any]:
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.connect() as conexion:
            return list(conexion.execute(text(sentencia), parametros).all())
    finally:
        engine.dispose()


def _decisiones(settings: Settings) -> list[tuple[Any, ...]]:
    return _filas(
        settings,
        "SELECT n.path, r.decision, r.note, r.actor, r.reviewed_at "
        "FROM topic_notes_reviews r "
        "JOIN curriculum_nodes n ON n.id = r.curriculum_node_id",
        {},
    )


def _eventos(settings: Settings) -> list[tuple[Any, ...]]:
    return _filas(
        settings,
        "SELECT actor, action, object_type, object_id, before_json, after_json "
        "FROM audit_events WHERE action = :accion ORDER BY created_at",
        {"accion": ACCION_REVISION},
    )


def _montar(seeded_settings: Settings, *, cuantas: int = 1) -> Iterator[Panel]:
    """El panel con la oposición activa sembrada, un borrador y un tema publicado.

    El borrador es un tema con un apartado escrito y **una** pregunta cubierta: su cobertura es del
    100 % y su forma pasa, así que aprobarlo **publica** (el caso de I.4 el 14 de octubre de 2026).
    El publicado tiene apuntes y su versión archivada, como cualquier tema que pasó las puertas.
    """
    resuelta = _settings(seeded_settings)
    with TestClient(create_app(resuelta)) as client:
        temas = _temas(client)
        preguntas = _catalogar(client, temas[BORRADOR], cuantas=cuantas)
        # Las que no se marcan como cubiertas se guardan como hueco: un grupo **sin comprobación
        # guardada no cuenta** en la puerta (ni arriba ni abajo), así que dejarlo sin escribir
        # mediría un tema más pequeño del que es.
        _escribir_apuntes(
            resuelta,
            str(temas[BORRADOR]["id"]),
            cubiertas=preguntas[:1],
            sin_cubrir=preguntas[1:],
        )
        # El tema publicado no necesita comprobaciones: lo que lo hace «publicado» es su versión
        # archivada, y las preguntas de la prueba están catalogadas en el otro tema.
        _escribir_apuntes(resuelta, str(temas[PUBLICADO]["id"]), cubiertas=[])
        _archivar_version(resuelta, str(temas[PUBLICADO]["id"]))
        yield Panel(client=client, settings=resuelta, temas=temas, preguntas=preguntas)


@pytest.fixture
def panel(seeded_settings: Settings) -> Iterator[Panel]:
    yield from _montar(seeded_settings)


@pytest.fixture
def panel_a_medias(seeded_settings: Settings) -> Iterator[Panel]:
    """El mismo panel con **dos** preguntas y una sola cubierta: la cobertura no llega al listón."""
    yield from _montar(seeded_settings, cuantas=2)


class TestLaTabla:
    def test_ensena_los_temas_con_su_estado_y_el_motivo_medido_de_los_borradores(
        self, panel: Panel
    ) -> None:
        tabla = panel.tabla()

        assert tabla["counters"]["topics_total"] == len(panel.temas)
        assert tabla["counters"]["with_notes"] == 2
        assert tabla["counters"]["draft"] == 1
        assert tabla["counters"]["published"] == 1
        assert tabla["counters"]["without_notes"] == len(panel.temas) - 2

        borrador = panel.fila(BORRADOR)
        assert borrador["state"] == "draft"
        # La tabla **no mide**: medir los borradores costaba 3,7 s de los 5,37 s que tardaba la
        # pantalla, así que la cifra de la puerta se mide al abrir la ficha. La fila lo dice con su
        # razón `sin_medida` en vez de enseñar un cero que parecería un suspenso.
        assert borrador["measured"] is False
        assert borrador["coverage"] is None
        assert borrador["coverage_threshold"] == 0.9
        codigos = [razon["code"] for razon in borrador["reasons"]]
        assert "sin_medida" in codigos
        assert "sin_decision" in codigos
        assert "a_las_puertas" not in codigos
        sin_medida = next(razon for razon in borrador["reasons"] if razon["code"] == "sin_medida")
        assert sin_medida["figure"] is None
        assert "se miden al abrir su ficha" in sin_medida["text"]

    def test_no_mide_los_temas_publicados_y_lo_dice(self, panel: Panel) -> None:
        fila = panel.fila(PUBLICADO)

        assert fila["state"] == "published"
        assert fila["measured"] is False
        assert fila["coverage"] is None
        publicado = next(razon for razon in fila["reasons"] if razon["code"] == "publicado")
        assert publicado["figure"] is None
        # Y no le pide una decisión a un tema que ya está publicado.
        assert "sin_decision" not in [razon["code"] for razon in fila["reasons"]]

    def test_el_contador_del_menu_cuenta_los_borradores_que_esperan_una_decision(
        self, panel: Panel
    ) -> None:
        resumen = panel.client.get("/api/v1/notes-review/summary")

        assert resumen.status_code == 200
        assert resumen.json()["pending_decision"] == 1
        assert resumen.json()["with_notes"] == 2


class TestLaFichaDeUnBorrador:
    def test_mide_el_tema_y_ensena_la_cifra_de_la_puerta(self, panel: Panel) -> None:
        """La medida vive donde se decide: abrir la ficha la hace, y la tabla dice dónde está."""
        datos = panel.client.get(f"/api/v1/notes-review/{BORRADOR}").json()

        tema = datos["topic"]
        assert tema["measured"] is True
        assert tema["coverage"] == [1, 1]
        puertas = next(razon for razon in tema["reasons"] if razon["code"] == "a_las_puertas")
        # La cifra de la puerta, con **coma** (§2.2): la compone el servidor y viaja ya escrita.
        assert puertas["figure"] == "1/1 = 100,0 %"
        assert "Aprobarlo la publica" in puertas["text"]
        assert "sin_medida" not in [razon["code"] for razon in tema["reasons"]]

    def test_sirve_una_hoja_de_seis_apartados_y_dice_cuantas_hojas_hay(self, panel: Panel) -> None:
        """La ficha va paginada: los cuerpos de todos los apartados eran el 92 % de la respuesta."""
        datos = panel.client.get(f"/api/v1/notes-review/{BORRADOR}").json()

        assert datos["page"] == 1
        assert datos["page_size"] == 6
        assert datos["pages"] == 1
        assert datos["sections_total"] == len(datos["sections"])

    def test_trae_sus_apartados_con_su_texto_y_su_forma(self, panel: Panel) -> None:
        ficha = panel.client.get(f"/api/v1/notes-review/{BORRADOR}")

        assert ficha.status_code == 200
        datos = ficha.json()
        assert datos["topic"]["state"] == "draft"
        assert len(datos["sections"]) == 1
        apartado = datos["sections"][0]
        assert apartado["title"] == APARTADO[2]
        assert apartado["position"] == 1
        assert apartado["body_markdown"].startswith("## PowerShell y los cmdlet")
        assert apartado["covered"] == 1
        assert apartado["worst"] == 0
        assert apartado["facts_total"] == 0

    def test_es_el_mismo_texto_que_lee_el_alumno(self, panel: Panel) -> None:
        """El panel no tiene una segunda versión de los apuntes: se comprueba contra el alumno."""
        ficha = panel.client.get(f"/api/v1/notes-review/{BORRADOR}").json()
        alumno = panel.client.get(f"/api/v1/student/topics/{BORRADOR}/notes").json()

        assert alumno["state"] == "draft"
        assert [apartado["body_markdown"] for apartado in ficha["sections"]] == [
            apartado["body_markdown"] for apartado in alumno["sections"]
        ]
        assert [apartado["title"] for apartado in ficha["sections"]] == [
            apartado["title"] for apartado in alumno["sections"]
        ]

    def test_un_tema_sin_apuntes_sale_con_su_estado_y_uno_que_no_existe_es_un_404(
        self, panel: Panel
    ) -> None:
        sin_apuntes = next(
            tema["code"] for tema in panel.tabla()["topics"] if tema["state"] == "none"
        )

        ficha = panel.client.get(f"/api/v1/notes-review/{sin_apuntes}")

        assert ficha.status_code == 200
        assert ficha.json()["topic"]["state"] == "none"
        assert ficha.json()["sections"] == []
        assert panel.client.get("/api/v1/notes-review/XX.9").status_code == 404


class TestAprobarYRechazar:
    def test_aprobar_un_tema_que_pasa_las_puertas_lo_publica(self, panel: Panel) -> None:
        assert panel.versiones(BORRADOR) == []

        respuesta = panel.client.post(
            f"/api/v1/notes-review/{BORRADOR}/decision",
            json={"decision": "approved", "note": "leído y repasado el 14 de octubre"},
            headers=ALLOWED_ORIGIN,
        )

        assert respuesta.status_code == 200, respuesta.text
        datos = respuesta.json()
        assert datos["published"] is True
        assert datos["version_created"] is True
        assert datos["blocked_by"] is None
        assert datos["topic"]["review"]["decision"] == "approved"
        assert datos["topic"]["review"]["actor"] == "local"
        # La versión archivada es la que hace que el tema esté publicado para todos.
        assert len(panel.versiones(BORRADOR)) == 1
        assert panel.fila(BORRADOR)["state"] == "published"
        notas_alumno = panel.client.get(f"/api/v1/student/topics/{BORRADOR}/notes").json()
        assert notas_alumno["state"] == "published"

    def test_aprobar_un_tema_que_no_llega_no_lo_publica_y_dice_que_puerta_lo_frena(
        self, panel_a_medias: Panel
    ) -> None:
        """El listón no se toca: aprobar no convierte un 50 % en un 90 %."""
        respuesta = panel_a_medias.client.post(
            f"/api/v1/notes-review/{BORRADOR}/decision",
            json={"decision": "approved"},
            headers=ALLOWED_ORIGIN,
        )

        assert respuesta.status_code == 200, respuesta.text
        datos = respuesta.json()
        assert datos["published"] is False
        assert datos["version_created"] is None
        assert datos["blocked_by"] == "cobertura"
        assert datos["topic"]["state"] == "draft"
        assert datos["topic"]["coverage"] == [1, 2]
        assert panel_a_medias.versiones(BORRADOR) == []
        # La decisión **sí** queda escrita: el propietario ya la tomó.
        assert datos["topic"]["review"]["decision"] == "approved"
        assert [fila[0] for fila in _decisiones(panel_a_medias.settings)] == [BORRADOR]

    def test_rechazar_sin_motivo_es_un_422_con_su_campo_y_no_escribe_nada(
        self, panel: Panel
    ) -> None:
        for cuerpo in ({"decision": "rejected"}, {"decision": "rejected", "note": "   "}):
            respuesta = panel.client.post(
                f"/api/v1/notes-review/{BORRADOR}/decision",
                json=cuerpo,
                headers=ALLOWED_ORIGIN,
            )
            assert respuesta.status_code == 422, respuesta.text
            assert respuesta.json()["code"] == "validation_error"
            assert respuesta.json()["field_errors"][0]["field"].endswith("note")

        assert _decisiones(panel.settings) == []
        assert _eventos(panel.settings) == []

    def test_rechazar_guarda_el_motivo_y_no_publica(self, panel: Panel) -> None:
        respuesta = panel.client.post(
            f"/api/v1/notes-review/{BORRADOR}/decision",
            json={
                "decision": "rejected",
                "note": "faltan 43 preguntas por contestar",
                "actor": "propietario-de-la-prueba",
            },
            headers=ALLOWED_ORIGIN,
        )

        assert respuesta.status_code == 200, respuesta.text
        datos = respuesta.json()
        assert datos["published"] is False
        assert datos["version_created"] is None
        assert datos["topic"]["review"]["note"] == "faltan 43 preguntas por contestar"
        assert datos["topic"]["review"]["actor"] == "propietario-de-la-prueba"
        assert panel.versiones(BORRADOR) == []
        # Y el motivo sigue a la vista, con el titular del rechazo delante.
        assert next(razon["code"] for razon in datos["topic"]["reasons"]) == "rechazado"

    def test_la_decision_y_su_evento_entran_en_la_misma_escritura(self, panel: Panel) -> None:
        nota = "leído el 14 de octubre: el texto está bien"

        respuesta = panel.client.post(
            f"/api/v1/notes-review/{BORRADOR}/decision",
            json={"decision": "approved", "note": nota},
            headers={**ALLOWED_ORIGIN, "X-OpoFuente-Actor": "propietario"},
        )

        assert respuesta.status_code == 200, respuesta.text
        filas = _decisiones(panel.settings)
        assert len(filas) == 1
        assert filas[0][:4] == (BORRADOR, "approved", nota, "propietario")

        eventos = _eventos(panel.settings)
        assert len(eventos) == 1
        actor, accion, objeto, object_id, antes, despues = eventos[0]
        assert (actor, accion, objeto) == ("propietario", ACCION_REVISION, OBJETO_TEMA)
        assert object_id == str(panel.temas[BORRADOR]["id"])
        assert '"decision": null' in str(antes)
        assert '"decision": "approved"' in str(despues)
        assert '"has_note": true' in str(despues)
        # La auditoría guarda referencias, no el texto de una persona.
        assert nota not in str(antes)
        assert nota not in str(despues)

    def test_la_segunda_revision_actualiza_la_primera_y_deja_su_evento(self, panel: Panel) -> None:
        panel.client.post(
            f"/api/v1/notes-review/{BORRADOR}/decision",
            json={"decision": "rejected", "note": "primero lo rechacé"},
            headers=ALLOWED_ORIGIN,
        )
        segunda = panel.client.post(
            f"/api/v1/notes-review/{BORRADOR}/decision",
            json={"decision": "approved", "note": "lo he releído y ya está"},
            headers=ALLOWED_ORIGIN,
        )

        assert segunda.status_code == 200, segunda.text
        filas = _decisiones(panel.settings)
        assert len(filas) == 1
        assert filas[0][1] == "approved"
        assert filas[0][2] == "lo he releído y ya está"
        # Los dos pasos quedan en la auditoría, con su antes y su después.
        eventos = _eventos(panel.settings)
        assert len(eventos) == 2
        assert '"decision": "rejected"' in str(eventos[1][4])
        assert '"decision": "approved"' in str(eventos[1][5])


class TestLaDecisionSobreviveAlMotor:
    def test_una_corrida_que_escribe_sus_filas_no_toca_la_decision(self, panel: Panel) -> None:
        """El motor reescribe sus comprobaciones y su bandeja; la decisión es del propietario."""
        nota = "lo he mirado y lo apruebo"
        panel.client.post(
            f"/api/v1/notes-review/{BORRADOR}/decision",
            json={"decision": "approved", "note": nota},
            headers=ALLOWED_ORIGIN,
        )

        # Una corrida del motor: vuelve a comprobar (con otra huella de texto) y rellena su bandeja.
        ahora = datetime.now(UTC)
        firmas = _firmas(panel.settings, str(panel.temas[BORRADOR]["id"]))
        engine = build_engine(panel.settings.data_paths.database)
        try:
            notas = SqlAlchemyTopicNotesRepository(build_session_factory(engine))
            notas.save_checks(
                str(panel.temas[BORRADOR]["id"]),
                [
                    NotesCheck(
                        question_version_id=pregunta,
                        group_signature=firmas[pregunta],
                        section_key=APARTADO[0],
                        anchor=APARTADO[0],
                        coverage=Coverage.DUDOSA,
                        note=Motivo.LETRA_NO_COINCIDE,
                        quote=None,
                        letter="b",
                        expected=("a",),
                        key_status=KeyStatus.DRAFT,
                        attempts=2,
                    )
                    for pregunta in panel.preguntas
                ],
                now=ahora,
            )
            notas.save_incidents(
                str(panel.temas[BORRADOR]["id"]),
                [
                    IncidenciaDeApuntes(
                        question_version_id=panel.preguntas[0],
                        group_signature=firmas[panel.preguntas[0]],
                        category=CategoriaIncidencia.CLAVE_SOSPECHOSA,
                        reason=Motivo.LETRA_NO_COINCIDE,
                        detail="la corrida nueva vuelve a señalar lo mismo",
                        section_key=APARTADO[0],
                        anchor=APARTADO[0],
                        phrase=None,
                    )
                ],
                now=ahora,
            )
        finally:
            engine.dispose()

        # La decisión sigue donde estaba, con su nota, y la tabla la sigue enseñando.
        assert _decisiones(panel.settings)[0][1:3] == ("approved", nota)
        fila = panel.fila(BORRADOR)
        assert fila["review"]["decision"] == "approved"
        assert fila["review"]["note"] == nota
        # Y el tema sigue publicado: lo que el motor reescribe son sus comprobaciones, no la
        # versión.
        assert fila["state"] == "published"

    def test_un_tema_sin_apuntes_escritos_no_se_puede_aprobar(self, panel: Panel) -> None:
        vacio = next(tema["code"] for tema in panel.tabla()["topics"] if tema["state"] == "none")

        respuesta = panel.client.post(
            f"/api/v1/notes-review/{vacio}/decision",
            json={"decision": "approved"},
            headers=ALLOWED_ORIGIN,
        )

        assert respuesta.status_code == 422, respuesta.text
        assert respuesta.json()["code"] == "invalid_review"
        assert _decisiones(panel.settings) == []
