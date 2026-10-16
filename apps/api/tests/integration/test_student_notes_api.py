"""Los apuntes en la zona del alumno: leerlos y avisar de un error (F13, decisiones D2 y D12).

Cuatro cosas que se prueban aquí y que son las que hacen que la pantalla de lectura sea de verdad:

1. **un tema publicado sirve su texto** con sus apartados en orden, su índice navegable (el
   `anchor` de cada uno) y el recuento de preguntas que contesta cada apartado;
2. **un tema en borrador se lee igual**, y lo dice: no se esconde (D2). Un tema **sin apuntes**
   no es un error —devuelve su estado y una lista vacía— y un tema que no existe sí (404);
3. **el aviso «esto está mal» se guarda de verdad**: en `notes_reports`, con el apartado y su
   anclaje, y con su **evento de auditoría** en la misma escritura (nada de un `console.log`);
4. **el propietario lo ve**: `GET /notes-reports` devuelve el aviso con su tema y su apartado, y el
   anclaje guardado es el del servidor, no el que mandó la petición.

Y desde F16 (el bloque C del objetivo), la quinta: **el propietario lo despacha**. La bandeja tiene
su ruta de escritura (`PATCH /notes-reports/{id}`), con su evento de auditoría en la misma
transacción, la nota de lo que se ha hecho y los cuatro estados que el modelo tiene. Es lo que
convierte «el propietario lo ve» en «el propietario lo resuelve».
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from datetime import UTC, datetime
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from opofuente.config import Settings
from opofuente.domain.topic_notes import Coverage, KeyStatus, NotesCheck, NoteSection
from opofuente.infrastructure.db import build_engine, build_session_factory
from opofuente.infrastructure.topic_notes_repository import SqlAlchemyTopicNotesRepository
from opofuente.main import create_app

ALLOWED_ORIGIN = {"Origin": "http://127.0.0.1:5173"}

#: El tema con apuntes de esta prueba. Es un tema de verdad del programa sembrado.
TEMA = "IV.1"

#: Los tres apartados que se escriben: el texto es de la prueba, no del propietario. El tercero va
#: en **otro epígrafe oficial** (`IV.1.2`) para poder probar la lectura por capítulos (F35, §3.1):
#: con todos en el mismo epígrafe no habría nada que paginar.
APARTADOS: tuple[tuple[str, str, str], ...] = (
    ("redes-tcpip", "IV.1.1", "El modelo TCP/IP y sus cuatro capas"),
    ("puertos-familias", "IV.1.1", "Puertos bien conocidos, por familias"),
    ("correo-electronico", "IV.1.2", "El correo electrónico y sus protocolos"),
)

CUERPO = "\n".join(
    [
        "## Las cuatro capas",
        "",
        "El modelo TCP/IP describe la comunicación en cuatro capas: acceso al medio, Internet,",
        "transporte y aplicación.",
        "",
        "| Capa | Unidad |",
        "| --- | --- |",
        "| Transporte | Segmento |",
        "| Internet | Paquete |",
    ]
)

TEXTO_PREGUNTAS = "\n".join(
    [
        "1. El modelo TCP/IP tiene cuatro capas.",
        "a) Verdadero",
        "b) Falso",
        "Respuesta correcta: a",
        "2. La sede electronica se regula en la Ley 39/2015.",
        "a) Verdadero",
        "b) Falso",
        "Respuesta correcta: a",
        "",
    ]
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


def _tema(client: TestClient) -> dict[str, Any]:
    oposiciones = client.get("/api/v1/oppositions").json()
    alumno = next(oposicion for oposicion in oposiciones if oposicion["code"] == "tai-age")
    programa = client.get(
        f"/api/v1/convocations/{alumno['active_convocation']['id']}/curriculum"
    ).json()
    return next(
        nodo
        for nodo in _aplanar(programa["nodes"])
        if nodo["node_type"] == "topic" and nodo["path"] == TEMA
    )


def _preguntas_catalogadas(client: TestClient, tema: dict[str, Any]) -> list[str]:
    """Dos preguntas de un conjunto nuevo, catalogadas en el tema: devuelve sus identificadores."""
    oposiciones = client.get("/api/v1/oppositions").json()
    alumno = next(oposicion for oposicion in oposiciones if oposicion["code"] == "tai-age")
    creado = client.post(
        "/api/v1/question-sets",
        json={
            "title": "Conjunto de la prueba de apuntes",
            "opposition_id": alumno["id"],
            "set_type": "private_bank",
            "convocation_version_id": alumno["active_convocation"]["id"],
        },
        headers=ALLOWED_ORIGIN,
    )
    assert creado.status_code == 201, creado.text
    set_id = str(creado.json()["id"])
    importado = client.post(
        f"/api/v1/question-sets/{set_id}/parse",
        json={"kind": "questions", "text": TEXTO_PREGUNTAS},
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


def _escribir_apuntes(settings: Settings, node_id: str, preguntas: list[str]) -> None:
    """Escribe los apuntes del tema por el repositorio de apuntes (la ruta de verdad)."""
    ahora = datetime.now(UTC)
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
                    position=posicion,
                )
                for posicion, (clave, epigrafe, titulo) in enumerate(APARTADOS, start=1)
            ],
            now=ahora,
        )
        primero = guardados[0]
        notas.save_section_body(
            primero,
            title=None,
            body=CUERPO,
            needs_review_reason=None,
            model="modelo-de-la-prueba",
            now=ahora,
        )
        # Una pregunta anclada al primer apartado: es lo que da la cifra de la nota al margen.
        notas.save_checks(
            node_id,
            [
                NotesCheck(
                    question_version_id=preguntas[0],
                    group_signature="firma-de-la-prueba",
                    section_key=primero.key,
                    anchor=primero.anchor,
                    coverage=Coverage.CUBIERTA,
                    note=None,
                    quote="El modelo TCP/IP describe la comunicación en cuatro capas",
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


def _archivar_version(settings: Settings, node_id: str) -> None:
    """Archiva una versión del tema: es lo que lo convierte en **publicado** para el alumno."""
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.begin() as conexion:
            conexion.execute(
                text(
                    "INSERT INTO dossier_snapshots (id, curriculum_node_id, content_hash, "
                    "built_at, created_at, sources_count, passages_count, payload_json) "
                    "VALUES ('version-1', :nodo, :hash, '2026-10-11 08:00:00', "
                    "'2026-10-11 08:00:00', 0, 0, '{}')"
                ),
                {"nodo": node_id, "hash": "a" * 64},
            )
    finally:
        engine.dispose()


@pytest.fixture
def alumno(seeded_settings: Settings) -> Iterator[tuple[TestClient, Settings, dict[str, Any]]]:
    """La zona del alumno con un tema que tiene apuntes escritos y una pregunta anclada."""
    resuelta = _settings(seeded_settings)
    with TestClient(create_app(resuelta)) as client:
        tema = _tema(client)
        preguntas = _preguntas_catalogadas(client, tema)
        _escribir_apuntes(resuelta, str(tema["id"]), preguntas)
        yield client, resuelta, tema


def _avisos(settings: Settings) -> list[tuple[Any, ...]]:
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.connect() as conexion:
            return list(
                conexion.execute(
                    text(
                        "SELECT section_key, anchor, reason, status, owner_id "
                        "FROM notes_reports ORDER BY created_at"
                    )
                ).all()
            )
    finally:
        engine.dispose()


def _auditoria(settings: Settings) -> list[tuple[Any, ...]]:
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.connect() as conexion:
            return list(
                conexion.execute(
                    text("SELECT actor, action, after_json FROM audit_events ORDER BY created_at")
                ).all()
            )
    finally:
        engine.dispose()


# ---------------------------------------------------------------- 1. leer los apuntes


def test_los_apuntes_de_un_tema_publicado_salen_con_su_indice_y_su_texto(
    alumno: tuple[TestClient, Settings, dict[str, Any]],
) -> None:
    """El texto, en orden, con su anclaje y con la cifra real de preguntas que contesta."""
    client, settings, tema = alumno
    _archivar_version(settings, str(tema["id"]))

    respuesta = client.get(f"/api/v1/student/topics/{TEMA}/notes")

    assert respuesta.status_code == 200, respuesta.text
    cuerpo = respuesta.json()
    assert cuerpo["code"] == TEMA
    assert cuerpo["state"] == "published"
    assert cuerpo["generated_at"] is not None, "los apuntes escritos dicen de cuándo son"
    assert [apartado["number"] for apartado in cuerpo["sections"]] == [1, 2]
    # Y solo los del **capítulo servido**: el tercero vive en `IV.1.2` y se lee en su capítulo.
    assert [apartado["key"] for apartado in cuerpo["sections"]] == [
        clave for clave, _, _ in APARTADOS[:2]
    ]
    assert [apartado["title"] for apartado in cuerpo["sections"]] == [
        titulo for _, _, titulo in APARTADOS[:2]
    ]
    assert all(apartado["anchor"] for apartado in cuerpo["sections"]), "el índice necesita anclas"
    primero = cuerpo["sections"][0]
    assert primero["body_markdown"].startswith("## Las cuatro capas")
    assert "| Capa | Unidad |" in primero["body_markdown"], "la tabla viaja entera"
    assert primero["questions_covered"] == 1
    assert cuerpo["sections"][1]["questions_covered"] == 0


def test_un_tema_en_borrador_se_lee_igual_y_lo_dice(
    alumno: tuple[TestClient, Settings, dict[str, Any]],
) -> None:
    """D2: un tema que no ha pasado las puertas no se esconde; se sirve con su estado."""
    client, _settings_sin_version, _tema = alumno

    respuesta = client.get(f"/api/v1/student/topics/{TEMA}/notes")

    assert respuesta.status_code == 200, respuesta.text
    cuerpo = respuesta.json()
    assert cuerpo["state"] == "draft"
    assert len(cuerpo["sections"]) == 2, "el texto del borrador se sirve entero"


def test_un_tema_sin_apuntes_no_es_un_error(
    seeded_client: TestClient,
) -> None:
    """Un tema sin texto devuelve su estado y una lista vacía.

    El 404 es para el tema que no está en el programa: no tener apuntes no es lo mismo que no
    existir.
    """
    sin_apuntes = seeded_client.get("/api/v1/student/topics/IV.10/notes")

    assert sin_apuntes.status_code == 200, sin_apuntes.text
    assert sin_apuntes.json() == {
        "code": "IV.10",
        "state": "none",
        "generated_at": None,
        "sections": [],
        # Un tema sin apuntes no tiene capítulos que enseñar, y eso no es un error.
        "chapter": None,
        "chapters": [],
    }
    assert seeded_client.get("/api/v1/student/topics/XX.99/notes").status_code == 404


# ------------------------------------------------- 1-bis. leerlos **por capítulos** (F35, §3.1)


def test_los_apuntes_se_sirven_por_capitulos_y_el_indice_viaja_entero(
    alumno: tuple[TestClient, Settings, dict[str, Any]],
) -> None:
    """Un capítulo por respuesta, con el índice completo **sin los textos**.

    Es lo que convierte un tema de 314.000 px en una pantalla que se lee: `sections` trae el texto
    del capítulo abierto y `chapters` el índice de todos, con sus apartados y sin sus cuerpos.
    Servir el tema entero fue lo que dejó el índice en 1.405 px dentro de una ventana de 800.
    """
    client, _settings_sin_version, _tema = alumno

    respuesta = client.get(f"/api/v1/student/topics/{TEMA}/notes")

    assert respuesta.status_code == 200, respuesta.text
    cuerpo = respuesta.json()
    assert cuerpo["chapter"] == "IV.1.1", "sin pedir capítulo se sirve el primero"
    # El índice completo: los dos epígrafes oficiales del tema, en su orden, con lo que tienen
    # dentro.
    assert [capitulo["code"] for capitulo in cuerpo["chapters"]] == ["IV.1.1", "IV.1.2"]
    assert [capitulo["position"] for capitulo in cuerpo["chapters"]] == [1, 2]
    assert [len(capitulo["sections"]) for capitulo in cuerpo["chapters"]] == [2, 1]
    assert all(capitulo["title"] for capitulo in cuerpo["chapters"]), "el capítulo se titula"
    # Los apartados del índice llevan su anclaje y **no** su texto: es lo que hace que el índice
    # quepa.
    del_indice = cuerpo["chapters"][1]["sections"][0]
    assert del_indice["anchor"] == "correo-electronico"
    assert "body_markdown" not in del_indice
    assert all(apartado["anchor"] for apartado in cuerpo["sections"])


def test_el_capitulo_se_elige_por_la_peticion(
    alumno: tuple[TestClient, Settings, dict[str, Any]],
) -> None:
    """`?capitulo=` sirve el epígrafe pedido, con sus apartados y con su número del tema entero."""
    client, _settings_sin_version, _tema = alumno

    respuesta = client.get(f"/api/v1/student/topics/{TEMA}/notes", params={"capitulo": "IV.1.2"})

    assert respuesta.status_code == 200, respuesta.text
    cuerpo = respuesta.json()
    assert cuerpo["chapter"] == "IV.1.2"
    assert [apartado["key"] for apartado in cuerpo["sections"]] == ["correo-electronico"]
    # El número es el del tema entero (3), no el de dentro del capítulo: es el que se cita en todas
    # las pantallas y el que sale en el índice completo.
    assert [apartado["number"] for apartado in cuerpo["sections"]] == [3]


def test_un_capitulo_que_ya_no_existe_no_es_un_404(
    alumno: tuple[TestClient, Settings, dict[str, Any]],
) -> None:
    """Un enlace guardado a un epígrafe que el programa reorganizó tiene que llevar a leer.

    No es un 404: se sirve el primero y la respuesta dice **cuál** se sirvió, para que la pantalla
    corrija la dirección en vez de dejar al alumno en un error que él no puede arreglar.
    """
    client, _settings_sin_version, _tema = alumno

    respuesta = client.get(f"/api/v1/student/topics/{TEMA}/notes", params={"capitulo": "IV.1.9"})

    assert respuesta.status_code == 200, respuesta.text
    cuerpo = respuesta.json()
    assert cuerpo["chapter"] == "IV.1.1", "se sirve el primero y se dice cuál"
    assert len(cuerpo["sections"]) == 2


def test_el_estado_de_los_apuntes_viaja_con_cada_tema_del_temario(
    alumno: tuple[TestClient, Settings, dict[str, Any]],
) -> None:
    """El temario dice qué temas tienen apuntes y cuáles están en borrador, sin abrir cada uno."""
    client, _settings_sin_version, _tema = alumno

    cuerpo = client.get("/api/v1/student/syllabus").json()
    estados = {
        tema["code"]: tema["notes_state"]
        for bloque in cuerpo["blocks"]
        for tema in bloque["topics"]
    }

    assert estados[TEMA] == "draft", "los apuntes escritos y sin versión están en borrador"
    assert estados["IV.10"] == "none", "un tema sin escribir no se anuncia como borrador"


# ---------------------------------------------------------------- 2. avisar de un error


def test_el_aviso_del_alumno_se_guarda_con_su_ancla_y_queda_auditado(
    alumno: tuple[TestClient, Settings, dict[str, Any]],
) -> None:
    """La escritura de verdad: la fila del aviso y su evento, y el anclaje lo pone el servidor."""
    client, settings, _tema = alumno

    respuesta = client.post(
        f"/api/v1/student/topics/{TEMA}/reports",
        json={"section_key": "puertos-familias", "reason": "  El puerto de LDAPS\nno es 389.  "},
        headers=ALLOWED_ORIGIN,
    )

    assert respuesta.status_code == 201, respuesta.text
    cuerpo = respuesta.json()
    assert cuerpo["section_key"] == "puertos-familias"
    assert cuerpo["reason"] == "El puerto de LDAPS no es 389.", "el motivo se guarda en una línea"
    assert cuerpo["status"] == "open"
    assert cuerpo["created_at"]

    assert _avisos(settings) == [
        (
            "puertos-familias",
            "puertos-familias",
            "El puerto de LDAPS no es 389.",
            "open",
            "local",
        )
    ]

    # El resto de la siembra de la prueba también deja auditoría (el conjunto, la catalogación), así
    # que lo que se busca es **su** evento, no que la tabla esté vacía.
    eventos = [evento for evento in _auditoria(settings) if evento[1] == "notes.report_created"]
    assert len(eventos) == 1, "el aviso entra con su evento de auditoría, no solo en su tabla"
    actor, accion, despues = eventos[0]
    assert (actor, accion) == ("alumno", "notes.report_created")
    assert json.loads(str(despues))["section_key"] == "puertos-familias"
    assert json.loads(str(despues))["anchor"] == "puertos-familias"
    assert "LDAPS" not in str(despues), "la auditoría guarda referencias, no el texto del alumno"


def test_el_anclaje_del_aviso_es_el_del_apartado_aunque_la_peticion_mienta(
    alumno: tuple[TestClient, Settings, dict[str, Any]],
) -> None:
    """La dirección la pone el servidor: la petición solo dice **qué apartado**, no dónde está."""
    client, settings, _tema = alumno

    respuesta = client.post(
        f"/api/v1/student/topics/{TEMA}/reports",
        json={"section_key": "redes-tcpip", "reason": "La tabla de capas está al revés."},
        headers=ALLOWED_ORIGIN,
    )

    assert respuesta.status_code == 201, respuesta.text
    assert _avisos(settings)[0][1] == "redes-tcpip"


def test_un_aviso_sin_motivo_o_de_un_apartado_que_no_es_del_tema_se_rechaza(
    alumno: tuple[TestClient, Settings, dict[str, Any]],
) -> None:
    """Sin motivo no hay nada que arreglar; y un apartado de otro tema no es de este."""
    client, settings, _tema = alumno

    sin_motivo = client.post(
        f"/api/v1/student/topics/{TEMA}/reports",
        json={"section_key": "redes-tcpip", "reason": "   "},
        headers=ALLOWED_ORIGIN,
    )
    assert sin_motivo.status_code == 422, sin_motivo.text
    assert sin_motivo.json()["field_errors"][0]["field"] == "body.reason"

    ajeno = client.post(
        f"/api/v1/student/topics/{TEMA}/reports",
        json={"section_key": "un-apartado-que-no-existe", "reason": "Esto está mal."},
        headers=ALLOWED_ORIGIN,
    )
    assert ajeno.status_code == 404, ajeno.text
    assert _avisos(settings) == [], "un aviso rechazado no deja fila"


# ---------------------------------------------------------------- 3. la bandeja del propietario


def test_el_aviso_aparece_en_la_bandeja_del_propietario_con_su_tema_y_su_apartado(
    alumno: tuple[TestClient, Settings, dict[str, Any]],
) -> None:
    """Lo que el propietario ve: dónde está el problema, qué dice y cuántos esperan."""
    client, _settings_sin_version, _tema = alumno
    creado = client.post(
        f"/api/v1/student/topics/{TEMA}/reports",
        json={"section_key": "redes-tcpip", "reason": "La tabla mezcla capas con protocolos."},
        headers=ALLOWED_ORIGIN,
    )
    assert creado.status_code == 201, creado.text

    bandeja = client.get("/api/v1/notes-reports")

    assert bandeja.status_code == 200, bandeja.text
    cuerpo = bandeja.json()
    assert cuerpo["pending"] == 1
    assert len(cuerpo["reports"]) == 1
    aviso = cuerpo["reports"][0]
    assert aviso["topic_code"] == TEMA
    assert aviso["section_key"] == "redes-tcpip"
    assert aviso["section_title"] == APARTADOS[0][2], "el título lo resuelve el servidor al leer"
    assert aviso["reason"] == "La tabla mezcla capas con protocolos."
    assert aviso["status"] == "open"

    # Y el filtro: por estado y por tema.
    assert client.get("/api/v1/notes-reports?status=reviewed").json()["reports"] == []
    assert client.get(f"/api/v1/notes-reports?topic={TEMA}").json()["pending"] == 1
    assert client.get("/api/v1/notes-reports?topic=IV.10").json()["reports"] == []


def test_un_aviso_de_un_apartado_borrado_sigue_en_la_bandeja_con_su_motivo(
    alumno: tuple[TestClient, Settings, dict[str, Any]],
) -> None:
    """El aviso más útil es el que apunta a un texto que ya no está: se lee, sin título."""
    client, settings, tema = alumno
    creado = client.post(
        f"/api/v1/student/topics/{TEMA}/reports",
        json={"section_key": "redes-tcpip", "reason": "Aquí faltaba IPv6."},
        headers=ALLOWED_ORIGIN,
    )
    assert creado.status_code == 201, creado.text

    engine = build_engine(settings.data_paths.database)
    try:
        with engine.begin() as conexion:
            conexion.execute(
                text(
                    "DELETE FROM topic_note_sections WHERE curriculum_node_id = :nodo "
                    "AND subsection_key = 'redes-tcpip'"
                ),
                {"nodo": str(tema["id"])},
            )
    finally:
        engine.dispose()

    aviso = client.get("/api/v1/notes-reports").json()["reports"][0]

    assert aviso["section_title"] is None, "el apartado ya no existe y se dice"
    assert aviso["reason"] == "Aquí faltaba IPv6."
    assert aviso["anchor"] == "redes-tcpip"


# ---------------------------------------------------------------- 4. el propietario lo despacha


def _avisar(client: TestClient, *, section_key: str, reason: str) -> dict[str, Any]:
    """Manda un aviso como el alumno y devuelve el aviso creado."""
    creado = client.post(
        f"/api/v1/student/topics/{TEMA}/reports",
        json={"section_key": section_key, "reason": reason},
        headers=ALLOWED_ORIGIN,
    )
    assert creado.status_code == 201, creado.text
    return client.get("/api/v1/notes-reports").json()["reports"][0]


def _despachos(settings: Settings) -> list[tuple[Any, ...]]:
    """Los eventos de despacho, con su objeto: actor, acción, objeto e identificador."""
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.connect() as conexion:
            return list(
                conexion.execute(
                    text(
                        "SELECT actor, action, object_type, object_id, before_json, after_json "
                        "FROM audit_events WHERE action = 'notes.report_updated' "
                        "ORDER BY created_at"
                    )
                ).all()
            )
    finally:
        engine.dispose()


def test_el_propietario_despacha_el_aviso_con_su_nota_y_su_evento(
    alumno: tuple[TestClient, Settings, dict[str, Any]],
) -> None:
    """El despacho de verdad: el estado, la nota y el evento, en la misma escritura."""
    client, settings, _tema = alumno
    aviso = _avisar(client, section_key="redes-tcpip", reason="La tabla mezcla capas y protocolos.")

    respuesta = client.patch(
        f"/api/v1/notes-reports/{aviso['id']}",
        json={"status": "reviewed", "note": "  Arreglado en la versión\ndel 12-oct.  "},
        headers=ALLOWED_ORIGIN,
    )

    assert respuesta.status_code == 200, respuesta.text
    cuerpo = respuesta.json()
    assert cuerpo["status"] == "reviewed"
    assert cuerpo["resolution_note"] == "Arreglado en la versión del 12-oct.", (
        "la nota es una línea"
    )
    assert cuerpo["reviewed_at"] is not None, "cerrar un aviso deja su fecha"
    assert cuerpo["topic_code"] == TEMA, "el despacho devuelve el aviso con su tema resuelto"
    assert cuerpo["section_title"] == APARTADOS[0][2]

    assert _avisos(settings)[0][3] == "reviewed", (
        "el estado está en la fila, no solo en la respuesta"
    )

    eventos = _despachos(settings)
    assert len(eventos) == 1
    actor, accion, objeto, object_id, antes, despues = eventos[0]
    assert (actor, accion, objeto) == ("local", "notes.report_updated", "note_report")
    assert str(object_id) == aviso["id"], "el evento apunta al aviso que se ha despachado"
    assert json.loads(str(antes))["status"] == "open"
    assert json.loads(str(despues))["status"] == "reviewed"
    assert json.loads(str(despues))["has_note"] is True
    assert "12-oct" not in str(despues), (
        "la auditoría guarda referencias, no la nota del propietario"
    )


def test_el_aviso_pasa_por_en_curso_antes_de_resolverse_y_eso_se_cuenta(
    alumno: tuple[TestClient, Settings, dict[str, Any]],
) -> None:
    """«Lo he visto y estoy en ello»: el estado que faltaba, y lo que hace al contador."""
    client, _settings_sin_version, _tema = alumno
    aviso = _avisar(client, section_key="redes-tcpip", reason="Falta la máscara /26.")

    assert client.get("/api/v1/notes-reports").json()["pending"] == 1

    en_curso = client.patch(
        f"/api/v1/notes-reports/{aviso['id']}",
        json={"status": "in_progress"},
        headers=ALLOWED_ORIGIN,
    )
    assert en_curso.status_code == 200, en_curso.text
    assert en_curso.json()["status"] == "in_progress"
    assert en_curso.json()["reviewed_at"] is None, "en curso no es estar despachado"

    bandeja = client.get("/api/v1/notes-reports").json()
    assert bandeja["pending"] == 0, "un aviso en curso ya no espera a nadie"
    assert bandeja["in_progress"] == 1
    assert bandeja["total"] == 1
    assert (
        client.get("/api/v1/notes-reports?status=in_progress").json()["reports"][0]["id"]
        == aviso["id"]
    )
    assert client.get("/api/v1/notes-reports?status=open").json()["reports"] == []


def test_reabrir_un_aviso_borra_la_fecha_de_revision_y_conserva_la_nota(
    alumno: tuple[TestClient, Settings, dict[str, Any]],
) -> None:
    """La fecha dice cuándo se despachó: un aviso abierto con fecha de revisión sería mentira."""
    client, _settings_sin_version, _tema = alumno
    aviso = _avisar(client, section_key="redes-tcpip", reason="El ejemplo está al revés.")

    cerrado = client.patch(
        f"/api/v1/notes-reports/{aviso['id']}",
        json={"status": "dismissed", "note": "No era un error: el ejemplo es correcto."},
        headers=ALLOWED_ORIGIN,
    )
    assert cerrado.json()["reviewed_at"] is not None

    abierto = client.patch(
        f"/api/v1/notes-reports/{aviso['id']}",
        json={"status": "open"},
        headers=ALLOWED_ORIGIN,
    )
    assert abierto.status_code == 200, abierto.text
    assert abierto.json()["status"] == "open"
    assert abierto.json()["reviewed_at"] is None, "reabrir borra la fecha"
    assert abierto.json()["resolution_note"] == "No era un error: el ejemplo es correcto.", (
        "lo que se hizo no se tira al reabrir"
    )


def test_despachar_un_aviso_que_no_existe_es_un_404_y_no_escribe_nada(
    alumno: tuple[TestClient, Settings, dict[str, Any]],
) -> None:
    """La bandeja se maneja con identificadores de verdad: uno inventado no es un despacho."""
    client, settings, _tema = alumno

    respuesta = client.patch(
        "/api/v1/notes-reports/no-existe",
        json={"status": "reviewed"},
        headers=ALLOWED_ORIGIN,
    )

    assert respuesta.status_code == 404, respuesta.text
    assert respuesta.json()["code"] == "not_found"
    assert _despachos(settings) == [], "un despacho rechazado no deja evento"


def test_el_actor_del_despacho_viaja_en_la_cabecera_y_una_nota_larga_se_rechaza(
    alumno: tuple[TestClient, Settings, dict[str, Any]],
) -> None:
    """Quién despacha se audita; y una nota que no cabe no se guarda a medias."""
    client, settings, _tema = alumno
    aviso = _avisar(client, section_key="redes-tcpip", reason="Falta la máscara /26.")

    larga = client.patch(
        f"/api/v1/notes-reports/{aviso['id']}",
        json={"status": "reviewed", "note": "x" * 301},
        headers=ALLOWED_ORIGIN,
    )
    assert larga.status_code == 422, larga.text
    assert _despachos(settings) == [], "una nota rechazada no deja el estado cambiado"

    con_cabecera = client.patch(
        f"/api/v1/notes-reports/{aviso['id']}",
        json={"status": "in_progress"},
        headers={**ALLOWED_ORIGIN, "X-OpoFuente-Actor": "propietario"},
    )
    assert con_cabecera.status_code == 200, con_cabecera.text
    assert _despachos(settings)[0][0] == "propietario", "la auditoría distingue a quien escribe"


def test_la_bandeja_filtra_por_estado_tema_y_busqueda(
    alumno: tuple[TestClient, Settings, dict[str, Any]],
) -> None:
    """Encontrar un aviso entre cientos: por estado, por tema y por lo que dice."""
    client, _settings_sin_version, _tema = alumno
    puertos = _avisar(
        client, section_key="puertos-familias", reason="El puerto de LDAPS no es 389."
    )
    _avisar(client, section_key="redes-tcpip", reason="La tabla mezcla capas y protocolos.")
    client.patch(
        f"/api/v1/notes-reports/{puertos['id']}",
        json={"status": "reviewed", "note": "Corregido."},
        headers=ALLOWED_ORIGIN,
    )

    por_estado = client.get("/api/v1/notes-reports?status=reviewed").json()
    assert por_estado["total"] == 1
    assert por_estado["reports"][0]["id"] == puertos["id"]
    assert por_estado["pending"] == 1, "el contador de pendientes no mira el filtro"

    por_tema = client.get(f"/api/v1/notes-reports?topic={TEMA}").json()
    assert por_tema["total"] == 2
    assert client.get("/api/v1/notes-reports?topic=IV.10").json()["total"] == 0

    # Por lo que escribió el alumno y por el título del apartado, que es lo que se recuerda.
    assert client.get("/api/v1/notes-reports?q=LDAPS").json()["total"] == 1
    assert client.get("/api/v1/notes-reports?q=mezcla").json()["total"] == 1
    assert client.get("/api/v1/notes-reports?q=puertos").json()["total"] == 1
    assert client.get("/api/v1/notes-reports?q=no-existe-esta-palabra").json()["total"] == 0
