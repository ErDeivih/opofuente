"""La bandeja agrupada por conjunto y sus acciones en bloque (F31, §2 del cierre del objetivo).

Lo que se prueba aquí es lo que hace que la bandeja se pueda **trabajar** en vez de mirar: que un
conjunto salga como **una fila** con lo que espera dentro, que las tres acciones en bloque cierren
el conjunto entero dejando su **evento de auditoría**, que aplicarlas dos veces no dupliquen nada, y
—lo que no se negocia— que **una clave oficial no se toque**: la ruta la rechaza con el motivo y no
escribe nada.

Dos cosas del montaje que conviene decir porque no son del propietario:

- los conjuntos oficiales se marcan con un `UPDATE` sobre la base **de la suite** (`.pytest-tmp`),
  no sobre ninguna real: no hay ruta que cambie el tipo de un conjunto, y el tipo es lo que hace
  que su clave esté protegida;
- la tabla de claves derivadas la escribe el bloque del §1, que **no está fusionado todavía**. Aquí
  se crea a mano con las columnas que este bloque lee. Sin ella, la acción de aceptar derivadas no
  tendría nada que aceptar y la prueba no probaría la escritura de la clave, que es justo lo que hay
  que demostrar que se rechaza cuando el conjunto es oficial.
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
    CategoriaIncidencia,
    IncidenciaDeApuntes,
    Motivo,
    NoteSection,
)
from opofuente.infrastructure.db import build_engine, build_session_factory
from opofuente.infrastructure.topic_notes_repository import SqlAlchemyTopicNotesRepository
from opofuente.main import create_app

ALLOWED_ORIGIN = {"Origin": "http://127.0.0.1:5173"}
TEMA = "IV.1"

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

#: Lo que la prueba aprobaría en bloque: la letra que dicen los apuntes con cita y el modelo, y que
#: **no** es la que el conjunto tiene hoy (que es `a` para todas las preguntas del banco).
LETRA_DERIVADA = "b"


def _settings(settings: Settings) -> Settings:
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


def _banco(client: TestClient, tema: dict[str, Any]) -> tuple[str, list[str]]:
    """Un banco privado con cuatro preguntas catalogadas. Devuelve su identificador y sus preguntas.

    Nace **privado** aunque la prueba lo vaya a marcar como oficial: importar y activar la plantilla
    de un examen oficial es una escritura que la aplicación ya protege, y lo que esta prueba
    necesita es un conjunto con incidencias cuya clave esté protegida, no montar un examen público.
    """
    oposiciones = client.get("/api/v1/oppositions").json()
    alumno = next(oposicion for oposicion in oposiciones if oposicion["code"] == "tai-age")
    creado = client.post(
        "/api/v1/question-sets",
        json={
            "title": "Banco de la bandeja por conjunto",
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
    assert len(identificadores) >= 3
    return set_id, identificadores


def _escribir_bandeja(settings: Settings, node_id: str, preguntas: list[str]) -> None:
    """Deja tres incidencias por el camino del motor, una de cada categoría que aquí importa."""
    ahora = datetime.now(UTC)
    engine = build_engine(settings.data_paths.database)
    try:
        notas = SqlAlchemyTopicNotesRepository(build_session_factory(engine))
        guardados = notas.save_sections(
            node_id,
            [
                NoteSection(
                    key="redes-tcpip",
                    epigraph_code="IV.1.1",
                    title="El modelo TCP/IP y sus cuatro capas",
                    anchor="redes-tcpip",
                    position=1,
                )
            ],
            now=ahora,
        )
        apartado = guardados[0]
        notas.save_incidents(
            node_id,
            [
                IncidenciaDeApuntes(
                    question_version_id=preguntas[0],
                    group_signature="firma-sospechosa",
                    category=CategoriaIncidencia.CLAVE_SOSPECHOSA,
                    reason=Motivo.LETRA_NO_COINCIDE,
                    detail="la clave contradice los apuntes: los apuntes dicen que es la b",
                    section_key=apartado.key,
                    anchor=apartado.anchor,
                    phrase="el puerto de LDAPS es el 636",
                ),
                IncidenciaDeApuntes(
                    question_version_id=preguntas[1],
                    group_signature="firma-sospechosa",
                    category=CategoriaIncidencia.CLAVE_SOSPECHOSA,
                    reason=Motivo.LETRA_NO_COINCIDE,
                    detail="la clave contradice los apuntes: los apuntes dicen que es la b",
                    section_key=apartado.key,
                    anchor=apartado.anchor,
                    phrase="el modelo OSI tiene siete capas",
                ),
                IncidenciaDeApuntes(
                    question_version_id=preguntas[2],
                    group_signature="firma-hueco",
                    category=CategoriaIncidencia.HUECO_SIN_MATERIAL,
                    reason=Motivo.SIN_FRASE_EN_LOS_APUNTES,
                    detail="los apuntes no contienen el dato ni se ha podido rellenar",
                    section_key=apartado.key,
                    anchor=apartado.anchor,
                ),
            ],
            now=ahora,
        )
    finally:
        engine.dispose()


def _crear_tabla_de_derivadas(settings: Settings) -> None:
    """La tabla que escribe el bloque del §1, con las columnas que este bloque lee.

    Se crea a mano porque su migración no está fusionada todavía. Cuando lo esté, esta función sobra
    y la prueba sigue valiendo: lo que comprueba es la **aprobación en bloque**, no quién creó la
    tabla.
    """
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.begin() as conexion:
            conexion.execute(
                text(
                    "CREATE TABLE IF NOT EXISTS question_derived_keys ("
                    " question_version_id VARCHAR(36) PRIMARY KEY,"
                    " question_set_id VARCHAR(36) NOT NULL,"
                    " correct_option_keys_json TEXT NOT NULL,"
                    " key_state VARCHAR(16) NOT NULL,"
                    " notes_letter VARCHAR(4),"
                    " notes_quote TEXT,"
                    " notes_anchor_id VARCHAR(36),"
                    " notes_key_status VARCHAR(16),"
                    " model_letter VARCHAR(4),"
                    " model_name VARCHAR(64),"
                    " model_version VARCHAR(64),"
                    " prompt_version VARCHAR(64),"
                    " actor VARCHAR(64),"
                    " created_at DATETIME)"
                )
            )
            conexion.execute(
                text(
                    "INSERT OR REPLACE INTO question_derived_keys ("
                    " question_version_id, question_set_id, correct_option_keys_json, key_state,"
                    " notes_letter, notes_quote, notes_key_status, model_letter, actor, created_at)"
                    " SELECT v.id, v.question_set_id, :letras, 'derived', :letra,"
                    "        'la clave del material esta mal: es la b', 'draft', :letra,"
                    "        'f29:claves-derivadas', :ahora"
                    "   FROM question_versions v"
                    "   JOIN question_sets s ON s.id = v.question_set_id"
                    "  WHERE s.title = 'Banco de la bandeja por conjunto'"
                ),
                {
                    "letras": json.dumps([LETRA_DERIVADA]),
                    "letra": LETRA_DERIVADA,
                    "ahora": datetime.now(UTC).replace(tzinfo=None),
                },
            )
    finally:
        engine.dispose()


def _es_clave_oficial(settings: Settings, set_id: str) -> None:
    """Marca el conjunto como examen oficial: es lo que protege su clave, por el mismo camino."""
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.begin() as conexion:
            conexion.execute(
                text("UPDATE question_sets SET set_type = 'official_exam' WHERE id = :id"),
                {"id": set_id},
            )
    finally:
        engine.dispose()


def _incidencias(settings: Settings) -> list[tuple[Any, ...]]:
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.connect() as conexion:
            return list(
                conexion.execute(
                    text(
                        "SELECT category, status, resolution_note FROM notes_incidents ORDER BY id"
                    )
                ).all()
            )
    finally:
        engine.dispose()


def _fiabilidad(settings: Settings, set_id: str) -> str:
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.connect() as conexion:
            return str(
                conexion.execute(
                    text("SELECT key_reliability FROM question_sets WHERE id = :id"),
                    {"id": set_id},
                ).scalar_one()
            )
    finally:
        engine.dispose()


def _eventos(settings: Settings, accion: str) -> list[tuple[str, str, str]]:
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.connect() as conexion:
            return [
                (str(actor), str(object_id), str(after))
                for actor, object_id, after in conexion.execute(
                    text(
                        "SELECT actor, object_id, after_json FROM audit_events "
                        "WHERE action = :accion ORDER BY created_at"
                    ),
                    {"accion": accion},
                ).all()
            ]
    finally:
        engine.dispose()


def _clave_de(settings: Settings, pregunta: str) -> str:
    """La clave que **manda** para una pregunta, por el mismo camino que la lee el banco."""
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.connect() as conexion:
            return str(
                conexion.execute(
                    text(
                        "SELECT e.correct_option_keys_json FROM answer_key_entries e "
                        "  JOIN answer_key_versions v ON v.id = e.answer_key_version_id "
                        " WHERE e.question_version_id = :pregunta "
                        " ORDER BY (v.status = 'active') DESC, v.version_no DESC LIMIT 1"
                    ),
                    {"pregunta": pregunta},
                ).scalar_one()
            )
    finally:
        engine.dispose()


def _exclusiones(settings: Settings) -> int:
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.connect() as conexion:
            return int(
                conexion.execute(
                    text("SELECT count(*) FROM question_curriculum_exclusions")
                ).scalar_one()
            )
    finally:
        engine.dispose()


@pytest.fixture
def bandeja(seeded_settings: Settings) -> Iterator[tuple[TestClient, Settings, str, list[str]]]:
    """Un banco privado con tres incidencias del motor, listo para decidirlo en bloque."""
    resuelta = _settings(seeded_settings)
    with TestClient(create_app(resuelta)) as client:
        tema = _tema(client)
        set_id, preguntas = _banco(client, tema)
        _escribir_bandeja(resuelta, str(tema["id"]), preguntas)
        yield client, resuelta, set_id, preguntas


def test_la_bandeja_agrupada_ensena_el_conjunto_como_una_fila(
    bandeja: tuple[TestClient, Settings, str, list[str]],
) -> None:
    """Una fila por conjunto, con su resumen, sus acciones y **la cifra** de la medida de éxito."""
    client, _settings_prueba, set_id, _preguntas = bandeja

    respuesta = client.get("/api/v1/notes-incidents/tray")
    assert respuesta.status_code == 200, respuesta.text
    cuerpo = respuesta.json()

    fila = next(cual for cual in cuerpo["rest"] if cual["set_id"] == set_id)
    assert fila["total_pendiente"] == 3
    assert fila["resumen"] == "2 claves sospechosas · 1 huecos sin material"
    assert fila["acciones"] == ["aceptar_derivadas", "dejar_fuera", "no_son_preguntas"]
    assert fila["official"] is False
    # La cifra: tres incidencias en un conjunto no oficial son **una** cosa que atender.
    assert fila["entradas_de_decision"] == 1
    assert cuerpo["entradas_de_decision"] == 1
    assert cuerpo["official_section"] == []


def test_dejar_el_conjunto_fuera_cierra_la_fila_y_es_idempotente(
    bandeja: tuple[TestClient, Settings, str, list[str]],
) -> None:
    """«Dejar el conjunto fuera» deja el veredicto, cierra lo que esperaba y no se puede repetir."""
    client, settings, set_id, _preguntas = bandeja

    primera = client.post(
        "/api/v1/notes-incidents/tray/bulk",
        json={"action": "dejar_fuera", "set_id": set_id},
        headers=ALLOWED_ORIGIN,
    )
    assert primera.status_code == 200, primera.text
    assert primera.json()["incidents"] == 3

    # El veredicto del §1 y las incidencias cerradas, cada uno por su ruta.
    assert _fiabilidad(settings, set_id) == "no_fiable"
    estados = {fila[1] for fila in _incidencias(settings)}
    assert estados == {"reviewed"}
    # Y el rastro: un evento por incidencia, firmado por quien lo pidió.
    eventos = _eventos(settings, "notes.incident_bulk_dispatched")
    assert len(eventos) == 3
    assert {evento[0] for evento in eventos} == {"local"}
    assert all('"set_id"' in evento[2] for evento in eventos)

    # La segunda pasada no encuentra nada que cerrar: ni duplica ni vuelve a proponer.
    segunda = client.post(
        "/api/v1/notes-incidents/tray/bulk",
        json={"action": "dejar_fuera", "set_id": set_id},
        headers=ALLOWED_ORIGIN,
    )
    assert segunda.status_code == 200, segunda.text
    assert segunda.json()["incidents"] == 0
    assert len(_eventos(settings, "notes.incident_bulk_dispatched")) == 3

    # Y el conjunto ya no tiene fila: la bandeja solo enseña lo que hay que atender.
    cuerpo = client.get("/api/v1/notes-incidents/tray").json()
    assert all(cual["set_id"] != set_id for cual in cuerpo["rest"])


def test_marcar_el_conjunto_como_no_son_preguntas_las_saca_del_temario(
    bandeja: tuple[TestClient, Settings, str, list[str]],
) -> None:
    """«No son preguntas»: salen del temario por su ruta auditada y la fila se cierra."""
    client, settings, set_id, preguntas = bandeja
    assert _exclusiones(settings) == 0

    respuesta = client.post(
        "/api/v1/notes-incidents/tray/bulk",
        json={"action": "no_son_preguntas", "set_id": set_id},
        headers=ALLOWED_ORIGIN,
    )
    assert respuesta.status_code == 200, respuesta.text
    assert respuesta.json()["incidents"] == 3

    assert _exclusiones(settings) == 3
    assert {fila[1] for fila in _incidencias(settings)} == {"no_son_preguntas"}
    assert len(_eventos(settings, "question.out_of_syllabus")) == 3
    assert len(_eventos(settings, "notes.incident_bulk_dispatched")) == 3
    assert preguntas  # las tres preguntas señaladas son las que salieron


def test_aceptar_las_derivadas_escribe_la_clave_y_cierra_la_incidencia(
    bandeja: tuple[TestClient, Settings, str, list[str]],
) -> None:
    """La aprobación en bloque escribe la letra derivada y cierra la incidencia, con su evento.

    Solo entran las **dos** claves sospechosas: el hueco sin material no tiene propuesta —no hay
    letra que aprobar— y se queda esperando criterio. Aceptar derivadas no cierra un conjunto:
    cierra
    lo que tiene propuesta, que es justo la diferencia entre «resuelto» y «propuesto en bloque».
    """
    client, settings, set_id, preguntas = bandeja
    _crear_tabla_de_derivadas(settings)
    assert _clave_de(settings, preguntas[0]) == '["a"]'

    bandeja_antes = client.get("/api/v1/notes-incidents/tray").json()
    fila = next(cual for cual in bandeja_antes["rest"] if cual["set_id"] == set_id)
    assert fila["propuestas"] == 2
    # Lo propuesto **no** cuenta como decisión: se aprueba en bloque.
    assert fila["entradas_de_decision"] == 1

    respuesta = client.post(
        "/api/v1/notes-incidents/tray/bulk",
        json={"action": "aceptar_derivadas", "set_id": set_id},
        headers=ALLOWED_ORIGIN,
    )
    assert respuesta.status_code == 200, respuesta.text
    assert respuesta.json() == {
        "action": "aceptar_derivadas",
        "set_id": set_id,
        "incidents": 2,
        "keys_written": 2,
    }

    assert _clave_de(settings, preguntas[0]) == '["b"]'
    assert {fila[1] for fila in _incidencias(settings)} == {"reviewed", "open"}
    assert len(_eventos(settings, "answer_key.derived_accepted")) == 2
    assert len(_eventos(settings, "notes.incident_bulk_dispatched")) == 2

    # Idempotencia: la segunda vez no hay propuestas ni incidencias que cerrar.
    otra_vez = client.post(
        "/api/v1/notes-incidents/tray/bulk",
        json={"action": "aceptar_derivadas", "set_id": set_id},
        headers=ALLOWED_ORIGIN,
    )
    assert otra_vez.status_code == 200, otra_vez.text
    assert otra_vez.json()["incidents"] == 0
    assert otra_vez.json()["keys_written"] == 0
    assert len(_eventos(settings, "answer_key.derived_accepted")) == 2


def test_una_clave_oficial_no_se_toca_y_la_ruta_lo_rechaza_con_su_prueba(
    seeded_settings: Settings,
) -> None:
    """**Una clave oficial no se cambia jamás**: la acción se rechaza y no se escribe ni una fila.

    Es la prueba que tiene que estar: si el rechazo no existiera, este botón cambiaría la plantilla
    publicada de un examen del INAP. Se comprueba el estado de la respuesta, el motivo, que la clave
    sigue donde estaba, que ninguna incidencia se cerró y que no hay ningún evento de escritura.
    """
    resuelta = _settings(seeded_settings)
    with TestClient(create_app(resuelta)) as client:
        tema = _tema(client)
        set_id, preguntas = _banco(client, tema)
        _escribir_bandeja(resuelta, str(tema["id"]), preguntas)
        _es_clave_oficial(resuelta, set_id)
        _crear_tabla_de_derivadas(resuelta)

        clave_antes = _clave_de(resuelta, preguntas[0])
        incidencias_antes = _incidencias(resuelta)

        for accion in ("aceptar_derivadas", "dejar_fuera", "no_son_preguntas"):
            respuesta = client.post(
                "/api/v1/notes-incidents/tray/bulk",
                json={"action": accion, "set_id": set_id},
                headers=ALLOWED_ORIGIN,
            )
            assert respuesta.status_code == 409, respuesta.text
            assert "examen oficial" in respuesta.json()["detail"]

        # Nada se movió: ni la clave, ni el estado de las incidencias, ni el temario.
        assert _clave_de(resuelta, preguntas[0]) == clave_antes
        assert _incidencias(resuelta) == incidencias_antes
        assert _exclusiones(resuelta) == 0
        assert _eventos(resuelta, "notes.incident_bulk_dispatched") == []
        assert _eventos(resuelta, "answer_key.derived_accepted") == []
        assert _fiabilidad(resuelta, set_id) == "fiable"

        # Y la bandeja lo enseña donde toca: en su sección, sin acciones.
        cuerpo = client.get("/api/v1/notes-incidents/tray").json()
        fila = next(cual for cual in cuerpo["official_section"] if cual["set_id"] == set_id)
        assert fila["official"] is True
        assert fila["acciones"] == []
        # Lo oficial no se agrupa: cada incidencia suya es una cosa que atender.
        assert fila["entradas_de_decision"] == 3
