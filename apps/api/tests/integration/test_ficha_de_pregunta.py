"""La ficha de pregunta: leerla, cambiar la respuesta correcta y reparar (F20, §4.2 del objetivo).

Es la pantalla que el objetivo llama «el sitio donde el propietario arregla las claves dudosas», y
lo
que se prueba aquí es lo que la hace servir para eso:

1. **enseña de dónde sale la respuesta correcta**: la plantilla, su número de versión, su estado y
el
   material del que salió con el estado de **esa** versión del material. Y el veredicto de
fiabilidad
   del conjunto: si la columna del §1 no está, lo dice en vez de recalcularlo;
2. **enseña qué dicen los apuntes** con la frase verificada y el apartado exacto, y **cuáles son las
   incidencias** que cuelgan de la pregunta con su categoría;
3. **marcar la correcta es una escritura auditada**: plantilla nueva, la anterior `superseded` —las
dos
   se pueden leer después— y el antes, el después y el actor en el **mismo** evento de auditoría;
4. **una clave oficial no se toca**: el conjunto `official_exam`, y también el banco privado cuya
   plantilla viene de un documento. Las dos se rechazan con un 409 que dice por qué y **sin escribir
   nada**;
5. **una letra que la pregunta no tiene es un 422**, antes de tocar la base;
6. **reparar escribe una versión nueva y se lleva el sitio de la pregunta**: sus temas y sus anclas
de
   apuntes se mudan a la versión nueva (sin eso, limpiar un enunciado la sacaría del temario), la
   clave sigue a la pregunta con las **mismas letras**, y la versión anterior queda `superseded`;
7. **las incidencias de la pregunta se despachan** al repararla, por la ruta auditada de la bandeja.

Las preguntas no se insertan con SQL: entran por el importador real, sus anclas e incidencias por el
repositorio del motor (`save_checks` y `save_incidents`, los mismos que usa una corrida de apuntes)
y
la opción fundida se crea con la ruta de corrección local que ya existía. El único SQL de
preparación
es el documento del que se enlaza una plantilla, porque no hay ninguna ruta que invente un material
sin
pasar por la extracción entera.
"""

from __future__ import annotations

from collections.abc import Iterator
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
from opofuente.infrastructure.topic_notes_repository import SqlAlchemyTopicNotesRepository
from opofuente.main import create_app

ALLOWED_ORIGIN = {"Origin": "http://127.0.0.1:5173"}

#: El tema del programa sembrado donde se catalogan las preguntas de la prueba.
TEMA = "IV.1"

#: Dos apartados: el ancla de una incidencia y el del párrafo que sostiene una respuesta.
APARTADOS: tuple[tuple[str, str, str], ...] = (
    ("redes-tcpip", "IV.1.1", "El modelo TCP/IP y sus cuatro capas"),
    ("puertos-familias", "IV.1.1", "Puertos bien conocidos, por familias"),
)

#: La frase de los apuntes que sostiene la respuesta y la letra que dan.
FRASE = "el puerto de LDAPS es el 636, no el 389"

#: Un enunciado con la referencia del examen pegada, medido en la copia de la base real.
ENUNCIADO_CON_REFERENCIA = (
    "El puerto de LDAPS es el 389: 2013 Cuerpo de Gestión de Sistemas e Informática "
    "de la AGE - Gr.B"
)

#: Las seis preguntas del banco de la prueba, en el orden en que se importan. La 1 trae la
#: referencia
#: pegada, la 2 es la que se funde después, y las demás rellenan el conjunto.
TEXTO = "\n".join(
    [
        "1. El puerto de LDAPS es el 389: 2013 Cuerpo de Gestión de Sistemas e Informática "
        "de la AGE - Gr.B",
        "a) Verdadero",
        "b) Falso",
        "Respuesta correcta: a",
        "2. ¿Cuál NO es una sentencia del lenguaje JCL (Job Control Language)?",
        "a) EXEC",
        "b) DD",
        "c) JOB",
        "Respuesta correcta: c",
        "3. El modelo OSI tiene siete capas.",
        "a) Verdadero",
        "b) Falso",
        "Respuesta correcta: a",
        "4. La sede electronica se regula en la Ley 39/2015.",
        "a) Verdadero",
        "b) Falso",
        "Respuesta correcta: a",
        "5. El Esquema Nacional de Seguridad se regula en el Real Decreto 311/2022.",
        "a) Verdadero",
        "b) Falso",
        "Respuesta correcta: a",
        "6. El plazo del procedimiento administrativo comun es de diez dias habiles.",
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


def _oposicion(client: TestClient) -> dict[str, Any]:
    return next(
        oposicion
        for oposicion in client.get("/api/v1/oppositions").json()
        if oposicion["code"] == "tai-age"
    )


def _tema(client: TestClient, oposicion: dict[str, Any]) -> dict[str, Any]:
    programa = client.get(
        f"/api/v1/convocations/{oposicion['active_convocation']['id']}/curriculum"
    ).json()
    return next(
        nodo
        for nodo in _aplanar(programa["nodes"])
        if nodo["node_type"] == "topic" and nodo["path"] == TEMA
    )


def _banco(
    client: TestClient,
    oposicion: dict[str, Any],
    tema: dict[str, Any],
    *,
    set_type: str,
    titulo: str,
) -> tuple[str, list[str]]:
    """Un conjunto importado, con su plantilla activa y sus preguntas catalogadas en el tema."""
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
        json={"kind": "questions", "text": TEXTO},
        headers=ALLOWED_ORIGIN,
    )
    assert importado.status_code == 200, importado.text
    claves = client.get(f"/api/v1/question-sets/{set_id}/answer-keys").json()
    # Activar una clave oficial exige la plantilla oficial enlazada, que en esta prueba no hay: para
    # el examen oficial se deja la plantilla tal como la deja el importador (en borrador), que basta
    # para probar que su respuesta correcta no se cambia desde la ficha. Las demás se activan.
    if set_type != "official_exam":
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
    return set_id, identificadores


def _fundir_la_opcion(client: TestClient, pregunta_id: str) -> str:
    """Deja la opción fundida por la ruta de corrección local que ya existía.

        El importador parte «JOB» y «CALL» porque reconoce el rótulo; el estado que hay que probar
        es el
        que trae la copia de la base real —«JOB 0d) CALL» en una sola opción— y se llega a él con la
        corrección local, que es una ruta auditada y no SQL.

        Devuelve el identificador de la **versión nueva**, que es la que queda vigente: escribir
        sobre
    la
        vieja sería escribir sobre una pregunta que ya no es la del banco.
    """
    corregida = client.post(
        f"/api/v1/questions/{pregunta_id}/local-corrections",
        json={
            "note": "la extracción fundió dos opciones en una (preparación de la prueba)",
            "options": ["EXEC", "DD", "JOB 0d) CALL"],
        },
        headers=ALLOWED_ORIGIN,
    )
    assert corregida.status_code == 201, corregida.text
    return str(corregida.json()["question"]["id"])


def _documento_de_plantilla(settings: Settings, set_id: str) -> None:
    """Enlaza la plantilla del conjunto con un documento, por SQL y solo de preparación.

        Es el segundo camino a «oficial»: una plantilla que salió de un papel. No hay ninguna ruta
        que
        invente un material sin pasar por la extracción entera, así que aquí se escriben las dos
        filas
    del
        documento y se apunta la plantilla a él.
    """
    ahora = datetime(2026, 10, 13, 12, 0, tzinfo=UTC).isoformat()
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.begin() as conexion:
            # El artefacto va delante porque una versión de documento cuelga de él: la base no
            # admite
            # una versión sin el fichero del que salió.
            conexion.execute(
                text(
                    "INSERT INTO source_artifacts (id, sha256, size_bytes, media_type, "
                    "storage_key, first_seen_at) VALUES ('art-plantilla', :sha, 100, 'text/plain', "
                    "'k', :ahora)"
                ),
                {"sha": "a" * 64, "ahora": ahora},
            )
            conexion.execute(
                text(
                    "INSERT INTO logical_documents (id, canonical_title, document_type, "
                    "authority_tier, owner_scope, created_at, updated_at) VALUES "
                    "('doc-plantilla', 'Plantilla de respuestas de la prueba', 'answer_key', 'A', "
                    "'public', :ahora, :ahora)"
                ),
                {"ahora": ahora},
            )
            conexion.execute(
                text(
                    "INSERT INTO document_versions (id, logical_document_id, artifact_id, "
                    "version_label, retrieved_at, language, status, approved_at, approved_by, "
                    "created_at) VALUES ('ver-plantilla', 'doc-plantilla', 'art-plantilla', "
                    "'definitiva', :ahora, 'es', 'accepted', :ahora, 'local', :ahora)"
                ),
                {"ahora": ahora},
            )
            conexion.execute(
                text(
                    "UPDATE answer_key_versions SET source_document_version_id = 'ver-plantilla' "
                    "WHERE question_set_id = :conjunto"
                ),
                {"conjunto": set_id},
            )
    finally:
        engine.dispose()


def _apuntes(settings: Settings, node_id: str, preguntas: list[str]) -> None:
    """Escribe los apartados, una comprobación de los apuntes y dos incidencias del motor.

        Se usan los dos métodos que usa una corrida de apuntes de verdad (`save_sections`,
    `save_checks`,
        `save_incidents`): si la ficha se probara con filas metidas a mano, estaría probando datos
        que
    no
        existen.
    """
    ahora = datetime(2026, 10, 13, 12, 0, tzinfo=UTC)
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
        notas.save_checks(
            node_id,
            [
                NotesCheck(
                    question_version_id=preguntas[0],
                    group_signature="firma-1",
                    section_key=segundo.key,
                    anchor=segundo.anchor,
                    coverage=Coverage.CONFLICTO,
                    note=Motivo.LETRA_NO_COINCIDE,
                    # La frase que el motor verificó contra el texto de los apuntes.
                    quote=FRASE,
                    letter="b",
                    expected=("a",),
                    key_status=KeyStatus.ACTIVE,
                    attempts=1,
                )
            ],
            now=ahora,
        )
        notas.save_incidents(
            node_id,
            [
                IncidenciaDeApuntes(
                    question_version_id=preguntas[0],
                    group_signature="firma-1",
                    category=CategoriaIncidencia.CLAVE_SOSPECHOSA,
                    reason=Motivo.LETRA_NO_COINCIDE,
                    detail="la clave contradice los apuntes: el puerto de LDAPS es el 636",
                    section_key=segundo.key,
                    anchor=segundo.anchor,
                    phrase=FRASE,
                ),
                IncidenciaDeApuntes(
                    question_version_id=preguntas[2],
                    group_signature="firma-2",
                    category=CategoriaIncidencia.HUECO_SIN_MATERIAL,
                    reason=Motivo.SIN_FRASE_EN_LOS_APUNTES,
                    detail="los apuntes no contienen el dato",
                    section_key=primero.key,
                    anchor=primero.anchor,
                ),
            ],
            now=ahora,
        )
    finally:
        engine.dispose()


@pytest.fixture
def ficha(seeded_settings: Settings) -> Iterator[dict[str, Any]]:
    """Cuatro conjuntos: el banco de la ficha, un banco limpio, un examen oficial y una plantilla de
    documento.

    Son cuatro y no uno porque cada uno prueba una cosa distinta y mezclarlas haría que el estado de
    una prueba dependiera de otra: el banco de la ficha lleva la opción fundida, sus anclas y sus
    incidencias; el banco limpio no tiene nada de eso y es donde se prueba marcar la correcta sin
    contar con lo que dejaron las correcciones anteriores.
    """
    resuelta = _settings(seeded_settings)
    with TestClient(create_app(resuelta)) as client:
        oposicion = _oposicion(client)
        tema = _tema(client, oposicion)
        banco, preguntas = _banco(
            client, oposicion, tema, set_type="private_bank", titulo="Banco de la ficha"
        )
        # La opción fundida se prepara **antes** de escribir anclas e incidencias: la corrección
        # crea
        # una versión nueva y lo que hay que apuntar después es esa, no la sustituida.
        original_de_la_fundida = preguntas[1]
        preguntas[1] = _fundir_la_opcion(client, preguntas[1])
        _, limpias = _banco(
            client, oposicion, tema, set_type="private_bank", titulo="Banco limpio de la ficha"
        )
        oficial, de_examen = _banco(
            client, oposicion, tema, set_type="official_exam", titulo="Examen oficial de la ficha"
        )
        con_plantilla, con_documento = _banco(
            client,
            oposicion,
            tema,
            set_type="private_bank",
            titulo="Banco con la plantilla de un documento",
        )
        _documento_de_plantilla(resuelta, con_plantilla)
        _apuntes(resuelta, str(tema["id"]), preguntas)
        yield {
            "client": client,
            "settings": resuelta,
            "tema": tema,
            "banco": banco,
            "preguntas": preguntas,
            "limpias": limpias,
            "original_de_la_fundida": original_de_la_fundida,
            "oficial": oficial,
            "de_examen": de_examen,
            "con_plantilla": con_plantilla,
            "con_documento": con_documento,
        }


def _ficha(client: TestClient, pregunta: str) -> dict[str, Any]:
    respuesta = client.get(f"/api/v1/question-files/{pregunta}")
    assert respuesta.status_code == 200, respuesta.text
    return respuesta.json()


def _claves(settings: Settings, set_id: str) -> list[tuple[Any, ...]]:
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.connect() as conexion:
            return list(
                conexion.execute(
                    text(
                        "SELECT id, version_no, status, approved_at, supersedes_id "
                        "FROM answer_key_versions WHERE question_set_id = :conjunto "
                        "ORDER BY version_no"
                    ),
                    {"conjunto": set_id},
                ).all()
            )
    finally:
        engine.dispose()


def _eventos(settings: Settings, accion: str) -> list[tuple[Any, ...]]:
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.connect() as conexion:
            return list(
                conexion.execute(
                    text(
                        "SELECT actor, object_type, object_id, before_json, after_json "
                        "FROM audit_events WHERE action = :accion ORDER BY created_at"
                    ),
                    {"accion": accion},
                ).all()
            )
    finally:
        engine.dispose()


def _filas(settings: Settings, consulta: str, **parametros: Any) -> list[tuple[Any, ...]]:
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.connect() as conexion:
            return list(conexion.execute(text(consulta), parametros).all())
    finally:
        engine.dispose()


# ------------------------------------------------------------------ 1. leer la ficha


def test_la_ficha_ensena_la_pregunta_sus_opciones_y_cual_esta_marcada_como_correcta(
    ficha: dict[str, Any],
) -> None:
    """Lo primero: qué se está mirando y qué se da por bueno hoy."""
    client, preguntas = ficha["client"], ficha["preguntas"]

    cuerpo = _ficha(client, preguntas[2])

    assert cuerpo["stem"] == "El modelo OSI tiene siete capas."
    assert [opcion["stable_key"] for opcion in cuerpo["options"]] == ["a", "b"]
    assert [opcion["label"] for opcion in cuerpo["options"]] == ["A", "B"]
    assert cuerpo["set_title"] == "Banco de la ficha"
    assert cuerpo["set_type"] == "private_bank"
    assert cuerpo["key"]["correct_option_keys"] == ["a"]
    assert cuerpo["key"]["status"] == "active", "la plantilla activa es la que corrige"
    assert cuerpo["key"]["outcome"] == "keyed"
    assert cuerpo["version_no"] == 1
    assert cuerpo["superseded_by"] is None


def test_la_ficha_dice_de_donde_sale_la_clave_y_en_que_estado_esta_su_material(
    ficha: dict[str, Any],
) -> None:
    """Sin la procedencia, una letra no se puede juzgar: es la mitad del trabajo de la pantalla."""
    client, preguntas = ficha["client"], ficha["preguntas"]

    cuerpo = _ficha(client, preguntas[2])

    assert cuerpo["key"]["answer_key_version_id"]
    assert cuerpo["key"]["approved_at"] is not None, "activar una plantilla es aprobarla"
    assert cuerpo["key"]["source_document_title"] is None, (
        "este banco no vino de un documento y la ficha no se lo inventa"
    )

    con_documento = _ficha(client, ficha["con_documento"][0])
    assert con_documento["key"]["source_document_title"] == "Plantilla de respuestas de la prueba"
    assert con_documento["key"]["source_document_type"] == "answer_key"
    assert con_documento["key"]["source_version_label"] == "definitiva"
    assert con_documento["key"]["source_version_status"] == "accepted"
    assert con_documento["key"]["source_document_id"] == "doc-plantilla"


def test_la_fiabilidad_del_conjunto_se_lee_y_se_dice_de_donde_sale(ficha: dict[str, Any]) -> None:
    """El veredicto del §1 no se recalcula aquí: se lee, o se dice que la columna no está.

        En esta base la columna `question_sets.key_reliability` todavía no existe —la añade el
        bloque
    del
        §1 con su migración—, y lo que la ficha hace entonces es **decirlo**, no inventarse un
        veredicto
        con una segunda regla.
    """
    client, preguntas = ficha["client"], ficha["preguntas"]

    cuerpo = _ficha(client, preguntas[0])

    assert "reliability_source" in cuerpo
    if cuerpo["key_reliability"] is None:
        assert "todavía no existe" in cuerpo["reliability_source"]
    else:
        assert cuerpo["key_reliability"] in {"fiable", "dudosa", "no_fiable"}
        assert "key_reliability" in cuerpo["reliability_source"]


def test_la_ficha_ensena_la_clave_de_los_apuntes_con_su_frase_y_su_apartado(
    ficha: dict[str, Any],
) -> None:
    """Lo que contesta el material de estudio, que es contra lo que se compara la clave."""
    client, preguntas = ficha["client"], ficha["preguntas"]

    cuerpo = _ficha(client, preguntas[0])

    assert len(cuerpo["notes"]) == 1
    contraste = cuerpo["notes"][0]
    assert contraste["answer_letter"] == "b"
    assert contraste["expected_letters"] == ["a"]
    assert contraste["phrase"] == FRASE
    assert contraste["anchor"] == APARTADOS[1][0], "el ancla del párrafo exacto de los apuntes"
    assert contraste["section_title"] == APARTADOS[1][2]
    assert contraste["topic_code"] == TEMA
    assert contraste["result"] == "conflict"
    assert contraste["coincides"] is False

    sin_apuntes = _ficha(client, preguntas[3])
    assert sin_apuntes["notes"] == [], "una pregunta sin comprobar no tiene contraste"


def test_la_ficha_ensena_las_incidencias_que_cuelgan_de_la_pregunta(ficha: dict[str, Any]) -> None:
    """Las incidencias del motor, con su categoría: es lo que hay que resolver."""
    client, preguntas = ficha["client"], ficha["preguntas"]

    cuerpo = _ficha(client, preguntas[0])

    assert len(cuerpo["incidents"]) == 1
    incidencia = cuerpo["incidents"][0]
    assert incidencia["category"] == "clave_sospechosa"
    assert incidencia["reason"] == "letra_no_coincide"
    assert incidencia["status"] == "open"
    assert incidencia["phrase"] == FRASE
    assert incidencia["topic_code"] == TEMA
    assert incidencia["resolution_note"] is None

    assert _ficha(client, preguntas[1])["incidents"] == []


def test_la_ficha_ensena_el_historial_de_la_pregunta_y_el_de_su_clave(
    ficha: dict[str, Any],
) -> None:
    """Los dos historiales: el de la pregunta y el de la plantilla, con la letra de cada versión."""
    client, preguntas = ficha["client"], ficha["preguntas"]

    cuerpo = _ficha(client, preguntas[1])

    assert [version["version_no"] for version in cuerpo["versions"]] == [2, 1], (
        "la corrección local dejó dos versiones, de la más nueva a la más vieja"
    )
    assert cuerpo["versions"][0]["status"] == "complete"
    assert cuerpo["versions"][1]["status"] == "superseded"
    assert cuerpo["versions"][1]["note"] is None
    assert "la extracción fundió" in str(cuerpo["versions"][0]["note"])
    assert cuerpo["versions"][1]["id"] == ficha["original_de_la_fundida"], (
        "el historial enseña la versión sustituida con su identificador"
    )
    assert [clave["version_no"] for clave in cuerpo["keys"]] == [2, 1], (
        "la corrección local escribió una plantilla nueva, y las dos se ven"
    )
    assert cuerpo["keys"][0]["status"] == "draft"
    assert cuerpo["keys"][0]["correct_option_keys"] == ["c"], (
        "la plantilla que escribió la corrección lleva la letra de la versión nueva"
    )
    assert cuerpo["key"] is None, (
        "y la pregunta corregida se queda **sin clave que mande**: la activa es la de antes, que"
        " apunta a la versión sustituida. Es lo que hace hoy la corrección local y la ficha lo dice"
        " en vez de enseñar una letra que no le corresponde"
    )

    # La ficha de la versión **sustituida** dice quién la sustituye en vez de fingir que es la
    # actual.
    vieja = cuerpo["versions"][1]["id"]
    assert _ficha(client, vieja)["superseded_by"] == preguntas[1]


def test_marcar_la_correcta_le_devuelve_la_clave_a_una_pregunta_corregida(
    ficha: dict[str, Any],
) -> None:
    """Una pregunta que se quedó sin clave que mande se arregla marcando su correcta.

    El caso es el que deja la corrección local cuando el conjunto tiene una plantilla **activa**: la
    corrección escribe la suya en borrador y la activa sigue mandando, apuntando a la versión
    sustituida. Desde la ficha, marcar la correcta escribe una plantilla con el estado de la que
    mandaba y con la entrada de esta pregunta, así que la deja con clave otra vez.
    """
    client, preguntas = ficha["client"], ficha["preguntas"]

    corregida = _ficha(client, preguntas[1])
    assert corregida["key"] is None, "la preparación la dejó sin clave que mande"

    respuesta = client.post(
        f"/api/v1/question-files/{preguntas[1]}/answer-key",
        json={"correct_option_keys": ["c"], "note": "la correcta es CALL"},
        headers=ALLOWED_ORIGIN,
    )

    assert respuesta.status_code == 200, respuesta.text
    assert respuesta.json()["file"]["key"]["correct_option_keys"] == ["c"]
    assert respuesta.json()["file"]["key"]["status"] == "active"
    assert respuesta.json()["file"]["key"]["outcome"] == "keyed"


# ------------------------------------------------------------------ 2. marcar la correcta


def test_marcar_la_correcta_escribe_una_plantilla_nueva_y_deja_la_anterior_en_el_historial(
    ficha: dict[str, Any],
) -> None:
    """El corazón de la pantalla: cambiar la clave sin pisar la que había."""
    client, settings, preguntas = ficha["client"], ficha["settings"], ficha["limpias"]

    antes = _ficha(client, preguntas[2])
    respuesta = client.post(
        f"/api/v1/question-files/{preguntas[2]}/answer-key",
        json={"correct_option_keys": ["b"], "note": "los apuntes dicen que es la b"},
        headers=ALLOWED_ORIGIN,
    )

    assert respuesta.status_code == 200, respuesta.text
    cuerpo = respuesta.json()
    assert cuerpo["correct_option_keys"] == ["b"]
    assert cuerpo["previous_option_keys"] == ["a"]
    assert cuerpo["file"]["key"]["correct_option_keys"] == ["b"]
    assert cuerpo["superseded_key_version_id"] == antes["key"]["answer_key_version_id"]
    assert cuerpo["key_version_id"] != antes["key"]["answer_key_version_id"]

    # En la base: la de antes queda `superseded` y la nueva activa, aprobada y apuntándola.
    filas = _claves(settings, antes["question_set_id"])
    assert [(int(fila[1]), str(fila[2])) for fila in filas] == [(1, "superseded"), (2, "active")]
    assert filas[1][3] is not None, "una plantilla activa lleva su aprobación"
    assert str(filas[1][4]) == str(filas[0][0]), "la plantilla nueva dice a cuál sustituye"
    nueva = _ficha(client, preguntas[2])
    assert nueva["key"]["version_no"] == 2
    assert [clave["version_no"] for clave in nueva["keys"]] == [2, 1]
    assert nueva["keys"][1]["correct_option_keys"] == ["a"], (
        "la letra que daba la plantilla anterior sigue leyéndose"
    )
    assert nueva["keys"][1]["status"] == "superseded"


def test_el_evento_de_auditoria_lleva_el_actor_el_antes_y_el_despues_en_la_misma_escritura(
    ficha: dict[str, Any],
) -> None:
    """La traza del cambio: quién, de qué a qué y con qué plantilla, sin la nota dentro."""
    import json

    client, settings, preguntas = ficha["client"], ficha["settings"], ficha["limpias"]

    respuesta = client.post(
        f"/api/v1/question-files/{preguntas[2]}/answer-key",
        json={"correct_option_keys": ["b"], "note": "nota del propietario que no viaja"},
        headers={**ALLOWED_ORIGIN, "X-OpoFuente-Actor": "propietario"},
    )
    assert respuesta.status_code == 200, respuesta.text

    eventos = _eventos(settings, "question.answer_key_marked")
    assert len(eventos) == 1, "un cambio, un evento"
    actor, objeto, object_id, antes, despues = eventos[0]
    assert (actor, objeto) == ("propietario", "question_version")
    assert str(object_id) == preguntas[2]
    previo = json.loads(str(antes))
    nuevo = json.loads(str(despues))
    assert (previo["correct_option_keys"], previo["key_version_no"]) == (["a"], 1)
    assert (nuevo["correct_option_keys"], nuevo["key_version_no"]) == (["b"], 2)
    assert nuevo["superseded_key_version_id"] == previo["key_version_id"]
    assert nuevo["has_note"] is True
    assert "no viaja" not in str(despues), "la nota del propietario no se copia a la auditoría"


def test_una_letra_que_la_pregunta_no_tiene_se_rechaza_antes_de_escribir(
    ficha: dict[str, Any],
) -> None:
    """Escribir una respuesta que nadie puede elegir sería una clave imposible."""
    client, settings, preguntas = ficha["client"], ficha["settings"], ficha["limpias"]
    antes = len(_claves(settings, ficha["banco"]))

    respuesta = client.post(
        f"/api/v1/question-files/{preguntas[2]}/answer-key",
        json={"correct_option_keys": ["d"]},
        headers=ALLOWED_ORIGIN,
    )

    assert respuesta.status_code == 422, respuesta.text
    assert respuesta.json()["code"] == "invalid_answer"
    assert len(_claves(settings, ficha["banco"])) == antes, "un rechazo no escribe una plantilla"
    assert _eventos(settings, "question.answer_key_marked") == []


def test_marcar_la_correcta_de_una_pregunta_que_no_existe_es_un_404(ficha: dict[str, Any]) -> None:
    client, settings = ficha["client"], ficha["settings"]

    respuesta = client.post(
        "/api/v1/question-files/no-existe/answer-key",
        json={"correct_option_keys": ["a"]},
        headers=ALLOWED_ORIGIN,
    )

    assert respuesta.status_code == 404, respuesta.text
    assert _eventos(settings, "question.answer_key_marked") == []


# ------------------------------------------------------------------ 3. la clave oficial


def test_la_clave_de_un_examen_oficial_no_se_cambia_y_la_ficha_dice_por_que(
    ficha: dict[str, Any],
) -> None:
    """La regla que el encargo pone como primera: una clave oficial no se toca, nunca."""
    client, settings = ficha["client"], ficha["settings"]
    pregunta = ficha["de_examen"][0]

    cuerpo = _ficha(client, pregunta)
    assert cuerpo["protection"]["protected"] is True
    assert "examen oficial" in cuerpo["protection"]["reason"]
    assert cualquier(cuerpo["protection"]["sets"], ficha["oficial"]), (
        "la lista de conjuntos protegidos trae el suyo, con su nombre"
    )

    antes = _claves(settings, ficha["oficial"])
    respuesta = client.post(
        f"/api/v1/question-files/{pregunta}/answer-key",
        json={"correct_option_keys": ["b"]},
        headers=ALLOWED_ORIGIN,
    )

    assert respuesta.status_code == 409, respuesta.text
    assert respuesta.json()["code"] == "classification_conflict"
    assert "examen oficial" in respuesta.json()["detail"]
    assert _claves(settings, ficha["oficial"]) == antes, "no se escribe ni una plantilla"
    assert _eventos(settings, "question.answer_key_marked") == []


def test_una_plantilla_que_viene_de_un_documento_tambien_protege_su_clave(
    ficha: dict[str, Any],
) -> None:
    """El segundo camino a «oficial»: la plantilla salió de un papel, aunque el conjunto sea un"""
    """ banco."""
    client, settings = ficha["client"], ficha["settings"]
    pregunta = ficha["con_documento"][0]

    cuerpo = _ficha(client, pregunta)
    assert cuerpo["set_type"] == "private_bank"
    assert cuerpo["protection"]["protected"] is True
    assert "material de origen" in cuerpo["protection"]["reason"]

    respuesta = client.post(
        f"/api/v1/question-files/{pregunta}/answer-key",
        json={"correct_option_keys": ["b"]},
        headers=ALLOWED_ORIGIN,
    )

    assert respuesta.status_code == 409, respuesta.text
    assert "material de origen" in respuesta.json()["detail"]
    assert len(_claves(settings, ficha["con_plantilla"])) == 1


def test_la_lista_de_conjuntos_protegidos_dice_cuales_son_y_por_que(
    ficha: dict[str, Any],
) -> None:
    """«No se puede» a secas obligaría a adivinar cuál de los conjuntos estorba."""
    client, preguntas = ficha["client"], ficha["preguntas"]

    cuerpo = _ficha(client, preguntas[0])

    protegidos = {conjunto["id"]: conjunto for conjunto in cuerpo["protection"]["sets"]}
    assert ficha["oficial"] in protegidos
    assert ficha["con_plantilla"] in protegidos
    assert ficha["banco"] not in protegidos, "un banco privado sin plantilla enlazada no está aquí"
    assert protegidos[ficha["oficial"]]["set_type"] == "official_exam"
    assert "examen oficial" in protegidos[ficha["oficial"]]["reason"]
    assert protegidos[ficha["con_plantilla"]]["source_document_title"] == (
        "Plantilla de respuestas de la prueba"
    )


def cualquier(conjuntos: list[dict[str, Any]], identificador: str) -> bool:
    return any(conjunto["id"] == identificador for conjunto in conjuntos)


# ------------------------------------------------------------------ 4. reparar


def test_la_ficha_ofrece_la_reparacion_que_una_regla_puede_hacer(ficha: dict[str, Any]) -> None:
    """Dos casos reales: la referencia pegada y la opción fundida, cada uno con lo que hará."""
    client, preguntas = ficha["client"], ficha["preguntas"]

    con_referencia = _ficha(client, preguntas[0])
    assert con_referencia["repair"]["reglas"] == ["quitar_referencia_del_examen"]
    assert con_referencia["repair"]["titulos"] == ["Quitar la referencia del examen"]
    assert con_referencia["repair"]["stem"] == "El puerto de LDAPS es el 389:"
    assert con_referencia["repair"]["opciones"] is None
    assert con_referencia["repair"]["por_que_no"] is None

    fundida = _ficha(client, preguntas[1])
    assert fundida["repair"]["reglas"] == ["partir_opcion_fundida"]
    assert fundida["repair"]["opciones"] == ["EXEC", "DD", "JOB", "CALL"]
    assert fundida["repair"]["stem"] is None

    limpia = _ficha(client, preguntas[2])
    assert limpia["repair"]["reglas"] == []
    assert limpia["repair"]["por_que_no"] is None, (
        "una pregunta que el motor no señaló no tiene nada que explicar"
    )


def test_reparar_escribe_una_version_nueva_y_se_lleva_el_sitio_de_la_pregunta(
    ficha: dict[str, Any],
) -> None:
    """Lo que impide que reparar un enunciado saque la pregunta del temario sin decirlo."""
    client, settings, preguntas = ficha["client"], ficha["settings"], ficha["preguntas"]
    anterior = _ficha(client, preguntas[0])
    temas_antes = _filas(
        settings,
        "SELECT subject_id FROM curriculum_mappings WHERE subject_id = :pregunta",
        pregunta=preguntas[0],
    )
    anclas_antes = _filas(
        settings,
        "SELECT question_version_id FROM question_note_anchors "
        "WHERE question_version_id = :pregunta",
        pregunta=preguntas[0],
    )
    assert temas_antes and anclas_antes, "la preparación tiene que dejar tema y ancla"

    respuesta = client.post(
        f"/api/v1/question-files/{preguntas[0]}/repairs",
        json={"note": "se limpia la referencia del examen pegada al enunciado"},
        headers=ALLOWED_ORIGIN,
    )

    assert respuesta.status_code == 200, respuesta.text
    cuerpo = respuesta.json()
    nueva = cuerpo["new_question_version_id"]
    assert nueva != preguntas[0]
    assert cuerpo["superseded_question_version_id"] == preguntas[0]
    assert cuerpo["reglas"] == ["quitar_referencia_del_examen"]
    assert cuerpo["file"]["stem"] == "El puerto de LDAPS es el 389:"
    assert cuerpo["file"]["version_no"] == anterior["version_no"] + 1
    assert cuerpo["moved_topics"] == len(temas_antes)
    assert cuerpo["moved_anchors"] == len(anclas_antes)
    assert cuerpo["moved_exclusion"] is False

    # El sitio viajó, no se copió: la pregunta vieja no conserva su tema y la nueva lo tiene.
    assert (
        _filas(
            settings,
            "SELECT subject_id FROM curriculum_mappings WHERE subject_id = :pregunta",
            pregunta=preguntas[0],
        )
        == []
    )
    assert _filas(
        settings,
        "SELECT subject_id FROM curriculum_mappings WHERE subject_id = :pregunta",
        pregunta=nueva,
    )
    assert _filas(
        settings,
        "SELECT question_version_id FROM question_note_anchors "
        "WHERE question_version_id = :pregunta",
        pregunta=nueva,
    )
    # La anterior queda en el historial, con su motivo.
    historial = cuerpo["file"]["versions"]
    assert [version["version_no"] for version in historial] == [2, 1]
    assert historial[1]["id"] == preguntas[0]
    assert historial[1]["status"] == "superseded"
    assert "referencia del examen" in str(historial[0]["note"])


def test_reparar_escribe_la_version_nueva_y_despacha_sus_incidencias(ficha: dict[str, Any]) -> None:
    """Una bandeja que siguiera enseñando una pregunta ya reparada estaría mintiendo."""
    client, preguntas = ficha["client"], ficha["preguntas"]

    respuesta = client.post(
        f"/api/v1/question-files/{preguntas[0]}/repairs",
        json={"note": "reparada la referencia del examen"},
        headers=ALLOWED_ORIGIN,
    )

    assert respuesta.status_code == 200, respuesta.text
    assert respuesta.json()["dispatched_incidents"] == 1
    incidencia = respuesta.json()["file"]["incidents"][0]
    assert incidencia["status"] == "reviewed"
    assert incidencia["reviewed_at"] is not None
    assert "reparada" in str(incidencia["resolution_note"])


def test_la_clave_sigue_a_la_pregunta_reparada_sin_cambiarle_ninguna_letra(
    ficha: dict[str, Any],
) -> None:
    """El invariante que permite limpiar el enunciado de un examen oficial: las letras no se"""
    """ mueven."""
    client, settings, preguntas = ficha["client"], ficha["settings"], ficha["preguntas"]
    antes = _ficha(client, preguntas[0])

    respuesta = client.post(
        f"/api/v1/question-files/{preguntas[0]}/repairs",
        json={"note": "limpieza del enunciado"},
        headers=ALLOWED_ORIGIN,
    )

    assert respuesta.status_code == 200, respuesta.text
    cuerpo = respuesta.json()
    assert cuerpo["file"]["key"]["correct_option_keys"] == antes["key"]["correct_option_keys"]
    assert cuerpo["key_version_id"] is not None
    filas = _claves(settings, ficha["banco"])
    assert filas[-1][2] == "active", "la plantilla nueva conserva el estado de la que sustituye"

    # Y el evento de la reparación dice qué reglas se aplicaron y cuánto se movió.
    eventos = _eventos(settings, "question.repaired")
    assert len(eventos) == 1
    import json

    despues = json.loads(str(eventos[0][4]))
    assert despues["reglas"] == ["quitar_referencia_del_examen"]
    assert despues["temas_movidos"] == 1
    assert despues["anclas_movidas"] == 1


def test_reparar_una_pregunta_sin_reparacion_posible_se_rechaza_con_el_motivo(
    ficha: dict[str, Any],
) -> None:
    """Lo que no se puede arreglar con una regla no se toca: ni una versión con texto inventado."""
    client, settings, preguntas = ficha["client"], ficha["settings"], ficha["preguntas"]

    respuesta = client.post(
        f"/api/v1/question-files/{preguntas[2]}/repairs",
        json={"note": "esto no debería escribir nada"},
        headers=ALLOWED_ORIGIN,
    )

    assert respuesta.status_code == 409, respuesta.text
    assert respuesta.json()["code"] == "classification_conflict"
    assert _eventos(settings, "question.repaired") == []
    assert (
        len(
            _filas(
                settings,
                "SELECT id FROM question_versions WHERE question_set_id = :conjunto "
                "AND stable_key = (SELECT stable_key FROM question_versions WHERE id = :pregunta)",
                conjunto=ficha["banco"],
                pregunta=preguntas[2],
            )
        )
        == 1
    )


def test_a_una_pregunta_de_un_examen_oficial_no_se_le_cambian_las_opciones(
    ficha: dict[str, Any],
) -> None:
    """Mover las opciones cambiaría lo que significan las letras de su plantilla oficial."""
    client, settings = ficha["client"], ficha["settings"]
    pregunta = ficha["de_examen"][1]
    # El enunciado de esa pregunta sí se puede limpiar; lo que no se puede es tocar sus opciones.
    antes = _filas(
        settings,
        "SELECT id FROM question_versions WHERE question_set_id = :conjunto",
        conjunto=ficha["oficial"],
    )

    respuesta = client.post(
        f"/api/v1/question-files/{pregunta}/repairs",
        json={
            "note": "no debería tocar las opciones de un examen oficial",
            "reglas": ["partir_opcion_fundida"],
        },
        headers=ALLOWED_ORIGIN,
    )

    # La pregunta del examen oficial no tiene ninguna de las dos reparaciones, así que el 409 llega
    # antes por «no hay nada que reparar»: el rechazo por opciones se prueba en el dominio
    # (`test_una_plantilla_que_viene_de_un_documento_protege_aunque_el_conjunto_no_sea_oficial`) y
    # aquí se comprueba que no se ha escrito nada.
    assert respuesta.status_code == 409, respuesta.text
    assert (
        _filas(
            settings,
            "SELECT id FROM question_versions WHERE question_set_id = :conjunto",
            conjunto=ficha["oficial"],
        )
        == antes
    )
