"""La bandeja del motor: leerla, encontrarla y despacharla (F18, §4.1 del objetivo).

Seis cosas que se prueban aquí y que son las que hacen que la bandeja sirva de algo:

1. **se ve lo que el motor encontró**: la categoría, el motivo, el porqué del dominio, el enunciado
   de la pregunta que la provoca y el detalle que escribió la corrida;
2. **se puede ir a mirarlo**: el apartado del que habla llega con su ancla —la misma que usan los
   apuntes— y con su título, y la pregunta con su identificador. La que **no se pudo situar en
   ninguna materia** no manda a un ancla que no está: lo dice;
3. **las cuatro cifras salen de la base**: con una página de una sola fila, los totales por
categoría
   siguen diciendo las cuatro de la bandeja entera. Contarlas de la página daría un número que
   miente;
4. **se despacha por la ruta auditada**: `PATCH /notes-incidents/{id}` con el estado y la nota, y el
   **evento** en la misma escritura, sin copiar el texto de la nota a la traza;
5. **el vocabulario del despacho es el del dominio**: pasar por «en curso», resolver, descartar… y
   reabrir borra la fecha y conserva la nota;
6. **una incidencia que no existe es un 404**, y no una escritura silenciosa.

Las incidencias **no se insertan a mano**: las escribe el motor por su camino de verdad, que es
`SqlAlchemyTopicNotesRepository.save_incidents`, el mismo que usa la corrida de apuntes. Si la
prueba las metiera con SQL, estaría probando una bandeja que no existe.
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
from opofuente.domain.topic_notes import (
    TEXTO_DE_CATEGORIA,
    TEXTO_SIN_MATERIA,
    CategoriaIncidencia,
    IncidenciaDeApuntes,
    Motivo,
    NoteSection,
)
from opofuente.infrastructure.db import build_engine, build_session_factory
from opofuente.infrastructure.topic_notes_repository import SqlAlchemyTopicNotesRepository
from opofuente.main import create_app

ALLOWED_ORIGIN = {"Origin": "http://127.0.0.1:5173"}

#: El tema de la prueba: uno del programa sembrado, con apuntes que se escriben aquí.
TEMA = "IV.1"

#: Los dos apartados del tema: sus anclas son las que resuelven el enlace de una incidencia.
APARTADOS: tuple[tuple[str, str, str], ...] = (
    ("redes-tcpip", "IV.1.1", "El modelo TCP/IP y sus cuatro capas"),
    ("puertos-familias", "IV.1.1", "Puertos bien conocidos, por familias"),
)

TEXTO_PREGUNTAS = "\n".join(
    [
        "1. El modelo TCP/IP tiene cuatro capas.",
        "a) Verdadero",
        "b) Falso",
        "Respuesta correcta: a",
        "2. El puerto de LDAPS es el 389.",
        "a) Verdadero",
        "b) Falso",
        "Respuesta correcta: a",
        "3. El modelo OSI tiene siete capas.",
        "a) Verdadero",
        "b) Falso",
        "Respuesta correcta: a",
        "4. La sede electronica se regula en la Ley 39/2015.",
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
    """Cuatro preguntas nuevas, catalogadas en el tema: devuelve sus identificadores."""
    oposiciones = client.get("/api/v1/oppositions").json()
    alumno = next(oposicion for oposicion in oposiciones if oposicion["code"] == "tai-age")
    creado = client.post(
        "/api/v1/question-sets",
        json={
            "title": "Banco del que salen las claves de la prueba",
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
    assert len(identificadores) >= 4, "la bandeja necesita una pregunta por incidencia"
    return identificadores


def _escribir_apuntes_y_bandeja(settings: Settings, node_id: str, preguntas: list[str]) -> None:
    """Escribe los apartados del tema y deja cuatro incidencias por el camino del motor.

    Las cuatro son de una categoría distinta, que es lo que permite comprobar las cuatro cifras; y
    una de ellas —la pregunta que no se pudo situar— llega **sin ancla**, que es el caso que la
    pantalla tiene que saber decir.
    """
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
        primero, segundo = guardados[0], guardados[1]
        notas.save_incidents(
            node_id,
            [
                IncidenciaDeApuntes(
                    question_version_id=preguntas[0],
                    group_signature="firma-hueco",
                    category=CategoriaIncidencia.HUECO_SIN_MATERIAL,
                    reason=Motivo.SIN_FRASE_EN_LOS_APUNTES,
                    detail="los apuntes no contienen el dato ni se ha podido rellenar",
                    section_key=primero.key,
                    anchor=primero.anchor,
                ),
                IncidenciaDeApuntes(
                    question_version_id=preguntas[1],
                    group_signature="firma-clave",
                    category=CategoriaIncidencia.CLAVE_SOSPECHOSA,
                    reason=Motivo.LETRA_NO_COINCIDE,
                    detail="la clave contradice los apuntes: los apuntes dicen que es 636",
                    section_key=segundo.key,
                    anchor=segundo.anchor,
                    phrase="el puerto de LDAPS es el 636",
                ),
                IncidenciaDeApuntes(
                    question_version_id=preguntas[2],
                    group_signature="firma-norma",
                    category=CategoriaIncidencia.NORMA_CAMBIADA,
                    reason=Motivo.CLAVE_CONTRADICE_LA_NORMA,
                    detail="la clave contradice la norma o el material de estudio",
                    section_key=segundo.key,
                    anchor=segundo.anchor,
                ),
                IncidenciaDeApuntes(
                    question_version_id=preguntas[3],
                    group_signature="firma-ambigua",
                    category=CategoriaIncidencia.PREGUNTA_AMBIGUA,
                    reason=Motivo.SIN_MATERIA_EN_EL_INDICE,
                    detail="la pregunta no se puede situar en ninguna materia del tema",
                ),
            ],
            now=ahora,
        )
    finally:
        engine.dispose()


@pytest.fixture
def bandeja(seeded_settings: Settings) -> Iterator[tuple[TestClient, Settings, dict[str, Any]]]:
    """La bandeja del motor con cuatro incidencias, una por categoría, escritas por el motor."""
    resuelta = _settings(seeded_settings)
    with TestClient(create_app(resuelta)) as client:
        tema = _tema(client)
        preguntas = _preguntas_catalogadas(client, tema)
        _escribir_apuntes_y_bandeja(resuelta, str(tema["id"]), preguntas)
        yield client, resuelta, tema


def _filas_de_la_bandeja(settings: Settings) -> list[tuple[Any, ...]]:
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.connect() as conexion:
            return list(
                conexion.execute(
                    text(
                        "SELECT category, status, resolution_note FROM notes_incidents "
                        "ORDER BY category"
                    )
                ).all()
            )
    finally:
        engine.dispose()


def _despachos(settings: Settings) -> list[tuple[Any, ...]]:
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.connect() as conexion:
            return list(
                conexion.execute(
                    text(
                        "SELECT actor, action, object_type, object_id, before_json, after_json "
                        "FROM audit_events WHERE action = 'notes.incident_updated' "
                        "ORDER BY created_at"
                    )
                ).all()
            )
    finally:
        engine.dispose()


def _por_categoria(cuerpo: dict[str, Any], categoria: str) -> dict[str, Any]:
    return next(
        incidencia for incidencia in cuerpo["incidents"] if incidencia["category"] == categoria
    )


def _una(client: TestClient, categoria: str) -> dict[str, Any]:
    """La incidencia de esa categoría, leída de la bandeja.

    Las cuatro se escriben en la misma corrida, así que comparten fecha y el orden de la lista no
    dice cuál es cuál: cada prueba pide la suya por su categoría en lugar de por su posición.
    """
    return _por_categoria(client.get("/api/v1/notes-incidents").json(), categoria)


# ------------------------------------------------------------------ 1. leer la bandeja


def test_la_bandeja_ensena_cada_incidencia_con_su_categoria_su_motivo_y_su_porque(
    bandeja: tuple[TestClient, Settings, dict[str, Any]],
) -> None:
    """Lo que el propietario necesita para decidir: qué es, por qué está ahí y qué la provoca."""
    client, _settings_sin_version, _tema = bandeja

    respuesta = client.get("/api/v1/notes-incidents")

    assert respuesta.status_code == 200, respuesta.text
    cuerpo = respuesta.json()
    assert cuerpo["total"] == 4
    assert len(cuerpo["incidents"]) == 4

    hueco = _por_categoria(cuerpo, "hueco_sin_material")
    assert hueco["reason"] == "sin_frase_en_los_apuntes"
    assert hueco["coverage"] == "doubtful"
    assert hueco["category_help"] == TEXTO_DE_CATEGORIA[CategoriaIncidencia.HUECO_SIN_MATERIAL]
    assert "no contienen el dato" in hueco["detail"]
    assert hueco["phrase"] is None, "un hueco no tiene frase: el dato no está escrito"
    assert hueco["stem"] == "El modelo TCP/IP tiene cuatro capas.", (
        "el enunciado viaja para poder juzgarla sin abrir nada"
    )
    assert hueco["set_title"] == "Banco del que salen las claves de la prueba"
    assert hueco["status"] == "open"
    assert hueco["reviewed_at"] is None
    assert hueco["topic_code"] == TEMA
    assert hueco["attempts"] == 1

    clave = _por_categoria(cuerpo, "clave_sospechosa")
    assert clave["coverage"] == "conflict", "una letra que no coincide es un conflicto, no una duda"
    assert clave["phrase"] == "el puerto de LDAPS es el 636", "la cita que lo demuestra"


def test_se_puede_ir_al_apartado_y_a_la_pregunta_sin_buscarlos(
    bandeja: tuple[TestClient, Settings, dict[str, Any]],
) -> None:
    """El enlace a lo que la provoca: el apartado de los apuntes y la pregunta del banco.

    Y el caso que hay que saber decir: la pregunta que **no se pudo situar en ninguna materia** no
    tiene apartado. Mandarla a un ancla que no existe dejaría al propietario buscando a mano, que es
    justo lo que esta bandeja viene a evitar; su texto lo explica.
    """
    client, _settings_sin_version, _tema = bandeja

    cuerpo = client.get("/api/v1/notes-incidents").json()

    clave = _por_categoria(cuerpo, "clave_sospechosa")
    assert clave["anchor"] == "puertos-familias"
    assert clave["section_title"] == APARTADOS[1][2], "el título del apartado, resuelto al leer"
    assert clave["question_version_id"], "la pregunta se puede abrir por su identificador"

    ambigua = _por_categoria(cuerpo, "pregunta_ambigua")
    assert ambigua["anchor"] == ""
    assert ambigua["section_title"] is None
    assert ambigua["category_help"] == TEXTO_SIN_MATERIA, (
        "su categoría es «pregunta ambigua», pero lo que le pasa no es que le falte la clave"
    )
    assert ambigua["question_version_id"]


def test_las_cifras_por_categoria_se_cuentan_en_la_base_y_no_en_la_pagina(
    bandeja: tuple[TestClient, Settings, dict[str, Any]],
) -> None:
    """Con una página de una fila, las cifras siguen siendo las de la bandeja entera."""
    client, _settings_sin_version, _tema = bandeja

    cuerpo = client.get("/api/v1/notes-incidents", params={"limit": 1}).json()

    assert len(cuerpo["incidents"]) == 1, "la página trae una"
    assert cuerpo["total"] == 4, "y el total es el del filtro, contado en la base"
    assert cuerpo["totals_by_category"] == {
        "hueco_sin_material": 1,
        "clave_sospechosa": 1,
        "pregunta_ambigua": 1,
        "norma_cambiada": 1,
        # Las dos que asigna la reclasificación salen **con cero**: un botón de filtro que
        # desapareciera cuando su número es cero obligaría a la pantalla a inventarse la ausencia.
        "pregunta_mal_importada": 0,
        "clave_no_fiable": 0,
    }
    assert cuerpo["pending"] == 4
    assert cuerpo["in_progress"] == 0
    assert cuerpo["reviewed"] == 0
    assert cuerpo["dismissed"] == 0


def test_los_cuentos_no_miran_el_filtro_pero_el_total_si(
    bandeja: tuple[TestClient, Settings, dict[str, Any]],
) -> None:
    """El botón de una categoría dice cuántas hay de esa categoría, no cuántas de la filtrada."""
    client, _settings_sin_version, _tema = bandeja

    cuerpo = client.get(
        "/api/v1/notes-incidents", params={"category": "clave_sospechosa", "topic": TEMA}
    ).json()

    assert cuerpo["total"] == 1
    assert cuerpo["totals_by_category"]["norma_cambiada"] == 1, "la cifra no se filtra"
    assert cuerpo["pending"] == 4, "el contador de pendientes tampoco"
    assert cuerpo["incidents"][0]["category"] == "clave_sospechosa"


def test_la_bandeja_filtra_por_estado_tema_y_busqueda(
    bandeja: tuple[TestClient, Settings, dict[str, Any]],
) -> None:
    """Encontrar una incidencia entre cientos: por estado, por tema y por lo que dicen."""
    client, _settings_sin_version, _tema = bandeja

    por_estado = client.get("/api/v1/notes-incidents", params={"status": "open"}).json()
    assert por_estado["total"] == 4
    assert client.get("/api/v1/notes-incidents", params={"status": "reviewed"}).json()["total"] == 0

    por_tema = client.get("/api/v1/notes-incidents", params={"topic": TEMA}).json()
    assert por_tema["total"] == 4
    assert client.get("/api/v1/notes-incidents", params={"topic": "IV.10"}).json()["total"] == 0

    # Por el enunciado de la pregunta, por la frase citada y por el título del apartado: las tres
    # cosas que se recuerdan cuando se busca una incidencia concreta.
    assert client.get("/api/v1/notes-incidents", params={"q": "LDAPS"}).json()["total"] == 1
    assert client.get("/api/v1/notes-incidents", params={"q": "636"}).json()["total"] == 1
    assert (
        client.get("/api/v1/notes-incidents", params={"q": "bien conocidos"}).json()["total"] == 2
    )
    assert client.get("/api/v1/notes-incidents", params={"q": "zzz"}).json()["total"] == 0

    # Y los filtros se combinan: una búsqueda que casa en dos categorías, con una de ellas puesta.
    combinado = client.get(
        "/api/v1/notes-incidents",
        params={"q": "bien conocidos", "category": "norma_cambiada"},
    ).json()
    assert combinado["total"] == 1
    assert combinado["incidents"][0]["category"] == "norma_cambiada"


# ------------------------------------------------------------------ 2. despachar


def test_el_propietario_despacha_la_incidencia_con_su_nota_y_su_evento(
    bandeja: tuple[TestClient, Settings, dict[str, Any]],
) -> None:
    """El despacho de verdad: el estado, la nota y el evento, en la misma escritura."""
    client, settings, _tema = bandeja
    incidencia = _una(client, "hueco_sin_material")

    respuesta = client.patch(
        f"/api/v1/notes-incidents/{incidencia['id']}",
        json={
            "status": "reviewed",
            "note": "  La clave estaba mal;\ncorregida en el banco.  ",
        },
        headers=ALLOWED_ORIGIN,
    )

    assert respuesta.status_code == 200, respuesta.text
    cuerpo = respuesta.json()
    assert cuerpo["status"] == "reviewed"
    assert cuerpo["resolution_note"] == "La clave estaba mal; corregida en el banco.", (
        "la nota es una línea"
    )
    assert cuerpo["reviewed_at"] is not None, "cerrar una incidencia deja su fecha"
    assert cuerpo["topic_code"] == TEMA, "el despacho devuelve la incidencia con su tema resuelto"
    assert cuerpo["section_title"] == APARTADOS[0][2]

    assert ("hueco_sin_material", "reviewed", "La clave estaba mal; corregida en el banco.") in [
        (str(fila[0]), str(fila[1]), str(fila[2])) for fila in _filas_de_la_bandeja(settings)
    ], "el estado y la nota están en la fila, no solo en la respuesta"

    eventos = _despachos(settings)
    assert len(eventos) == 1
    actor, accion, objeto, object_id, antes, despues = eventos[0]
    assert (actor, accion, objeto) == ("local", "notes.incident_updated", "note_incident")
    assert str(object_id) == incidencia["id"], "el evento apunta a la incidencia despachada"
    assert json.loads(str(antes))["status"] == "open"
    assert json.loads(str(despues))["status"] == "reviewed"
    assert json.loads(str(despues))["has_note"] is True
    assert "corregida" not in str(despues), (
        "la auditoría guarda referencias, no la nota del propietario"
    )


def test_la_incidencia_pasa_por_en_curso_antes_de_resolverse_y_eso_se_cuenta(
    bandeja: tuple[TestClient, Settings, dict[str, Any]],
) -> None:
    """«Lo he visto y estoy en ello»: el estado que no existía, y lo que hace al contador."""
    client, _settings_sin_version, _tema = bandeja
    incidencia = _una(client, "clave_sospechosa")

    en_curso = client.patch(
        f"/api/v1/notes-incidents/{incidencia['id']}",
        json={"status": "in_progress"},
        headers=ALLOWED_ORIGIN,
    )
    assert en_curso.status_code == 200, en_curso.text
    assert en_curso.json()["status"] == "in_progress"
    assert en_curso.json()["reviewed_at"] is None, "en curso no es estar despachada"

    cuerpo = client.get("/api/v1/notes-incidents").json()
    assert cuerpo["pending"] == 3, "una incidencia en curso ya no espera a nadie"
    assert cuerpo["in_progress"] == 1
    assert cuerpo["total"] == 4

    solo_curso = client.get("/api/v1/notes-incidents", params={"status": "in_progress"}).json()
    assert solo_curso["total"] == 1
    assert solo_curso["incidents"][0]["id"] == incidencia["id"]
    assert client.get("/api/v1/notes-incidents", params={"status": "open"}).json()["total"] == 3


def test_reabrir_una_incidencia_borra_la_fecha_y_conserva_la_nota(
    bandeja: tuple[TestClient, Settings, dict[str, Any]],
) -> None:
    """La fecha dice cuándo se despachó: una incidencia abierta con fecha sería mentira."""
    client, _settings_sin_version, _tema = bandeja
    incidencia = _una(client, "norma_cambiada")

    cerrada = client.patch(
        f"/api/v1/notes-incidents/{incidencia['id']}",
        json={"status": "dismissed", "note": "El motor se equivoca: la clave es correcta."},
        headers=ALLOWED_ORIGIN,
    )
    assert cerrada.json()["reviewed_at"] is not None
    assert cerrada.json()["status"] == "dismissed"

    abierta = client.patch(
        f"/api/v1/notes-incidents/{incidencia['id']}",
        json={"status": "open"},
        headers=ALLOWED_ORIGIN,
    )
    assert abierta.status_code == 200, abierta.text
    assert abierta.json()["status"] == "open"
    assert abierta.json()["reviewed_at"] is None, "reabrir borra la fecha"
    assert abierta.json()["resolution_note"] == "El motor se equivoca: la clave es correcta.", (
        "lo que se decidió no se tira al reabrir"
    )


def test_una_incidencia_que_no_existe_es_un_404_y_no_escribe_nada(
    bandeja: tuple[TestClient, Settings, dict[str, Any]],
) -> None:
    """La bandeja se maneja con identificadores de verdad: uno inventado no es un despacho."""
    client, settings, _tema = bandeja

    respuesta = client.patch(
        "/api/v1/notes-incidents/no-existe",
        json={"status": "reviewed"},
        headers=ALLOWED_ORIGIN,
    )

    assert respuesta.status_code == 404, respuesta.text
    assert respuesta.json()["code"] == "not_found"
    assert _despachos(settings) == [], "un despacho rechazado no deja evento"


def test_el_actor_viaja_en_la_cabecera_y_una_nota_larga_se_rechaza(
    bandeja: tuple[TestClient, Settings, dict[str, Any]],
) -> None:
    """Quién despacha se audita; y una nota que no cabe no se guarda a medias."""
    client, settings, _tema = bandeja
    incidencia = _una(client, "pregunta_ambigua")

    larga = client.patch(
        f"/api/v1/notes-incidents/{incidencia['id']}",
        json={"status": "reviewed", "note": "x" * 301},
        headers=ALLOWED_ORIGIN,
    )
    assert larga.status_code == 422, larga.text
    assert _despachos(settings) == [], "una nota rechazada no deja el estado cambiado"

    con_cabecera = client.patch(
        f"/api/v1/notes-incidents/{incidencia['id']}",
        json={"status": "in_progress"},
        headers={**ALLOWED_ORIGIN, "X-OpoFuente-Actor": "propietario"},
    )
    assert con_cabecera.status_code == 200, con_cabecera.text
    assert _despachos(settings)[0][0] == "propietario", "la auditoría distingue a quien escribe"
