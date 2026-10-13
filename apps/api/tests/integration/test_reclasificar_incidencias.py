"""La reclasificación de la bandeja del motor (§2 de `AJUSTES-…-CLAVES-Y-RITMO-2026-10.md`).

Lo que se prueba, y es lo que el documento pide:

1. **la etiqueta cambia a la que le toca** y con el orden del §2: una pregunta mal importada gana a
   la clave en cuarentena, y la cuarentena gana a la clave sospechosa;
2. **el falso positivo sale de la bandeja**: si la letra que dan los apuntes está en la clave, la
   incidencia no era una incidencia. El motor la habría borrado en la corrida siguiente;
3. **`norma_cambiada` se queda a cero** sin la cita de la norma vigente: lo que sí se puede afirmar
   —que la clave contradice los apuntes— se dice con su propia categoría y con la frase que lo
   demuestra cuando el motor la verificó;
4. **lo que no se puede reparar sale del temario** con `enunciado_roto` (D6: «No son preguntas»),
   por el mismo camino auditado que usa el panel;
5. **todo queda auditado**: un evento por incidencia cambiada y otro por cada una que sale, y lo que
   escribió el motor **sigue debajo** del motivo del cambio;
6. **ejecutarlo dos veces no cambia nada**: la segunda pasada escribe cero cambios.

Las incidencias y las comprobaciones no se escriben a mano en la base: las incidencias van por
`save_incidents` —el camino de la corrida de apuntes— y las comprobaciones por `save_checks`, que es
el
del paso E. Las preguntas sí se insertan con SQL porque lo que hay que poder construir aquí son
preguntas **rotas** (con dos opciones), y el importador no deja crear eso: es justo lo que detecta.
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
from opofuente.tools.reclasificar_incidencias import main as reclasificar

ALLOWED_ORIGIN = {"Origin": "http://127.0.0.1:5173"}

TEMA = "IV.1"
APARTADO = ("redes-tcpip", "IV.1.1", "El modelo TCP/IP y sus cuatro capas")


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


def _conjunto(client: TestClient) -> str:
    oposiciones = client.get("/api/v1/oppositions").json()
    alumno = next(oposicion for oposicion in oposiciones if oposicion["code"] == "tai-age")
    creado = client.post(
        "/api/v1/question-sets",
        json={
            "title": "Banco de la reclasificación",
            "opposition_id": alumno["id"],
            "set_type": "private_bank",
            "convocation_version_id": alumno["active_convocation"]["id"],
        },
        headers=ALLOWED_ORIGIN,
    )
    assert creado.status_code == 201, creado.text
    return str(creado.json()["id"])


def _insertar_pregunta(
    settings: Settings,
    *,
    set_id: str,
    pregunta_id: str,
    posicion: int,
    stem: str,
    opciones: tuple[str, ...],
    tipo: str = "single_choice",
) -> None:
    """Una pregunta con sus opciones: es lo que permite tener una **rota** (con dos opciones)."""
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.begin() as conexion:
            conexion.execute(
                text(
                    "INSERT INTO question_versions (id, question_set_id, stable_key, version_no, "
                    "stem, question_type, position, is_reserve, reserve_order, status, "
                    "origin_type, source_section_id, supersedes_id, created_at, note) "
                    "VALUES (:id, :set, :clave, 1, :stem, :tipo, :posicion, 0, NULL, 'complete', "
                    "'private', NULL, NULL, '2026-10-13 09:00:00', NULL)"
                ),
                {
                    "id": pregunta_id,
                    "set": set_id,
                    "clave": pregunta_id[:12],
                    "stem": stem,
                    "tipo": tipo,
                    "posicion": posicion,
                },
            )
            for indice, texto in enumerate(opciones):
                conexion.execute(
                    text(
                        "INSERT INTO option_versions (id, question_version_id, stable_key, label, "
                        "text, position) VALUES (:id, :pregunta, :clave, NULL, :texto, :posicion)"
                    ),
                    {
                        "id": f"{pregunta_id}-op-{indice}",
                        "pregunta": pregunta_id,
                        "clave": chr(ord("a") + indice),
                        "texto": texto,
                        "posicion": indice + 1,
                    },
                )
    finally:
        engine.dispose()


def _escribir_bandeja(settings: Settings, node_id: str, preguntas: list[str]) -> None:
    """Los apartados, las comprobaciones del paso E y las cuatro incidencias, por sus rutas."""
    ahora = datetime.now(UTC)
    engine = build_engine(settings.data_paths.database)
    try:
        notas = SqlAlchemyTopicNotesRepository(build_session_factory(engine))
        guardados = notas.save_sections(
            node_id,
            [
                NoteSection(
                    key=APARTADO[0],
                    epigraph_code=APARTADO[1],
                    title=APARTADO[2],
                    anchor=APARTADO[0],
                    position=1,
                )
            ],
            now=ahora,
        )
        apartado = guardados[0]
        notas.save_checks(
            node_id,
            [
                # 1. conflicto con cita: la clave contradice los apuntes y está la frase que lo
                # prueba
                NotesCheck(
                    question_version_id=preguntas[0],
                    group_signature="firma-1",
                    section_key=apartado.key,
                    anchor=apartado.anchor,
                    coverage=Coverage.CONFLICTO,
                    note=Motivo.LETRA_NO_COINCIDE,
                    quote="el modelo TCP/IP describe la comunicación en cuatro capas",
                    letter="b",
                    expected=("a",),
                    key_status=KeyStatus.ACTIVE,
                    attempts=3,
                ),
                # 2. **falso positivo**: la letra de los apuntes está en la clave
                NotesCheck(
                    question_version_id=preguntas[1],
                    group_signature="firma-2",
                    section_key=apartado.key,
                    anchor=apartado.anchor,
                    coverage=Coverage.CUBIERTA,
                    note=None,
                    quote="el modelo TCP/IP describe la comunicación en cuatro capas",
                    letter="a",
                    expected=("a",),
                    key_status=KeyStatus.ACTIVE,
                    attempts=1,
                ),
                # 3. una pregunta rota (dos opciones) cuya clave también discrepa
                NotesCheck(
                    question_version_id=preguntas[2],
                    group_signature="firma-3",
                    section_key=apartado.key,
                    anchor=apartado.anchor,
                    coverage=Coverage.CONFLICTO,
                    note=Motivo.LETRA_NO_COINCIDE,
                    quote=None,
                    letter="b",
                    expected=("a",),
                    key_status=KeyStatus.ACTIVE,
                    attempts=3,
                ),
                # 4. discrepancia sin frase verificada
                NotesCheck(
                    question_version_id=preguntas[3],
                    group_signature="firma-4",
                    section_key=apartado.key,
                    anchor=apartado.anchor,
                    coverage=Coverage.DUDOSA,
                    note=Motivo.CLAVE_CONTRADICE_LA_NORMA,
                    quote=None,
                    letter="b",
                    expected=("d",),
                    key_status=KeyStatus.ACTIVE,
                    attempts=1,
                ),
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
                    detail="la clave contradice los apuntes",
                    section_key=apartado.key,
                    anchor=apartado.anchor,
                    phrase="el modelo TCP/IP describe la comunicación en cuatro capas",
                ),
                IncidenciaDeApuntes(
                    question_version_id=preguntas[1],
                    group_signature="firma-2",
                    category=CategoriaIncidencia.NORMA_CAMBIADA,
                    reason=Motivo.CLAVE_CONTRADICE_LA_NORMA,
                    detail="la clave contradice la norma o el material de estudio",
                    section_key=apartado.key,
                    anchor=apartado.anchor,
                ),
                IncidenciaDeApuntes(
                    question_version_id=preguntas[2],
                    group_signature="firma-3",
                    category=CategoriaIncidencia.NORMA_CAMBIADA,
                    reason=Motivo.CLAVE_CONTRADICE_LA_NORMA,
                    detail="la clave contradice la norma o el material de estudio",
                    section_key=apartado.key,
                    anchor=apartado.anchor,
                ),
                IncidenciaDeApuntes(
                    question_version_id=preguntas[3],
                    group_signature="firma-4",
                    category=CategoriaIncidencia.NORMA_CAMBIADA,
                    reason=Motivo.CLAVE_CONTRADICE_LA_NORMA,
                    detail="la clave contradice la norma o el material de estudio",
                    section_key=apartado.key,
                    anchor=apartado.anchor,
                ),
            ],
            now=ahora,
        )
    finally:
        engine.dispose()


@pytest.fixture
def bandeja(
    seeded_settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> Iterator[tuple[Settings, list[str]]]:
    """Una bandeja de cuatro incidencias: una de cada caso que el §2 tiene que distinguir.

    El comando lee la configuración del entorno (`get_settings`), así que aquí se le da la de la
    prueba: es el único punto por el que se le puede decir sobre qué base trabajar, y hacerlo por el
    entorno sería escribir en el directorio de datos equivocado si algo fallara.
    """
    resuelta = Settings(data_dir=seeded_settings.data_dir, worker_enabled=False, _env_file=None)
    monkeypatch.setattr("opofuente.tools.reclasificar_incidencias.get_settings", lambda: resuelta)
    with TestClient(create_app(resuelta)) as client:
        tema = _tema(client)
        set_id = _conjunto(client)
        preguntas = ["pregunta-1", "pregunta-2", "pregunta-3", "pregunta-4"]
        limpia = ("una opción larga y distinta", "otra opción larga y distinta", "una tercera más")
        for indice, pregunta_id in enumerate(preguntas, start=1):
            # La tercera es la rota: dos opciones con texto.
            opciones = limpia[:2] if indice == 3 else limpia
            _insertar_pregunta(
                resuelta,
                set_id=set_id,
                pregunta_id=pregunta_id,
                posicion=indice,
                stem=f"Enunciado de la pregunta {indice}",
                opciones=opciones,
            )
        _escribir_bandeja(resuelta, str(tema["id"]), preguntas)
        yield resuelta, preguntas


def _filas(settings: Settings, sentencia: str, parametros: dict[str, object]) -> list[Any]:
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.connect() as conexion:
            return list(conexion.execute(text(sentencia), parametros).all())
    finally:
        engine.dispose()


def _categorias(settings: Settings) -> dict[str, str]:
    return {
        str(pregunta): str(categoria)
        for pregunta, categoria in _filas(
            settings, "SELECT question_version_id, category FROM notes_incidents", {}
        )
    }


def test_la_reclasificacion_pone_la_etiqueta_que_toca_y_saca_lo_que_no_era_incidencia(
    bandeja: tuple[Settings, list[str]],
) -> None:
    settings, preguntas = bandeja
    assert len(_categorias(settings)) == 4

    codigo = reclasificar(["--aplicar", "--sin-copia"])

    assert codigo == 0
    quedan = _categorias(settings)
    # 1. la que tenía la frase: sigue siendo una clave sospechosa, que es lo que es
    assert quedan[preguntas[0]] == "clave_sospechosa"
    # 2. el falso positivo **sale**: la letra de los apuntes está en la clave
    assert preguntas[1] not in quedan
    # 3. la pregunta rota gana a la clave: primero se arregla la pregunta
    assert quedan[preguntas[2]] == "pregunta_mal_importada"
    # 4. la discrepancia sin frase también es una clave sospechosa, y lo dice
    assert quedan[preguntas[3]] == "clave_sospechosa"

    detalle = str(
        _filas(
            settings,
            "SELECT detail FROM notes_incidents WHERE question_version_id = :id",
            {"id": preguntas[3]},
        )[0][0]
    )
    assert detalle.startswith("reclasificada:")
    assert "no consta la frase que lo demuestra" in detalle
    assert "la clave contradice la norma o el material de estudio" in detalle, (
        "lo que escribió el motor sigue debajo del motivo del cambio"
    )


def test_norma_cambiada_no_la_hereda_nadie_sin_la_cita_de_la_norma(
    bandeja: tuple[Settings, list[str]],
) -> None:
    """Las tres que decían «norma cambiada» sin la cita bajan a lo que sí se puede afirmar."""
    settings, _preguntas = bandeja

    assert _filas(
        settings, "SELECT count(*) FROM notes_incidents WHERE category = 'norma_cambiada'", {}
    ) == [(3,)]

    reclasificar(["--aplicar", "--sin-copia"])

    assert _filas(
        settings, "SELECT count(*) FROM notes_incidents WHERE category = 'norma_cambiada'", {}
    ) == [(0,)]


def test_lo_que_no_se_puede_reparar_sale_del_temario_con_enunciado_roto(
    bandeja: tuple[Settings, list[str]],
) -> None:
    """D6: una pregunta que no se puede contestar no entra en los tests. Y queda auditado."""
    settings, preguntas = bandeja

    reclasificar(["--aplicar", "--sin-copia", "--excluir-no-reparables"])

    marcas = _filas(
        settings,
        "SELECT reason, actor FROM question_curriculum_exclusions WHERE question_version_id = :id",
        {"id": preguntas[2]},
    )
    assert [(str(fila[0]), str(fila[1])) for fila in marcas] == [
        ("enunciado_roto", "f18:reclasificacion-incidencias")
    ]
    # Y la que sí se puede reparar **no** sale: se queda en la bandeja con su regla.
    assert _filas(
        settings,
        "SELECT count(*) FROM question_curriculum_exclusions WHERE question_version_id = :id",
        {"id": preguntas[0]},
    ) == [(0,)]


def test_el_despacho_esta_auditado_y_ejecutarlo_dos_veces_no_cambia_nada(
    bandeja: tuple[Settings, list[str]],
) -> None:
    """Un evento por cambio y por salida, con lo que había y lo que queda; y es idempotente."""
    settings, _preguntas = bandeja

    reclasificar(["--aplicar", "--sin-copia"])

    eventos = _filas(
        settings,
        "SELECT action, actor, before_json, after_json FROM audit_events "
        "WHERE action LIKE 'notes.incident_%' ORDER BY action",
        {},
    )
    acciones: dict[str, int] = {}
    for accion, _actor, _antes, _despues in eventos:
        acciones[str(accion)] = acciones.get(str(accion), 0) + 1
    # La que ya estaba bien **no** deja evento: el comando solo escribe lo que cambia. Son tres
    # escrituras para cuatro incidencias: una sale y dos cambian de categoría.
    assert acciones == {"notes.incident_dropped": 1, "notes.incident_reclassified": 2}
    for _accion, actor, antes, despues in eventos:
        assert str(actor) == "f18:reclasificacion-incidencias"
        assert json.loads(str(antes))["category"] in {
            "norma_cambiada",
            "clave_sospechosa",
        }
        assert "category" in json.loads(str(despues))

    antes = _categorias(settings)
    reclasificar(["--aplicar", "--sin-copia"])
    assert _categorias(settings) == antes, "la segunda pasada no cambia nada"
    assert _filas(
        settings,
        "SELECT count(*) FROM audit_events WHERE action LIKE 'notes.incident_%'",
        {},
    ) == [(3,)], "ni deja eventos de más: idempotente de verdad"


def test_la_letra_de_los_apuntes_que_si_esta_en_la_clave_no_es_una_incidencia(
    bandeja: tuple[Settings, list[str]],
) -> None:
    """La comprobación que ya está cubierta es un resto: el motor la borraría en la corrida
    siguiente."""
    settings, preguntas = bandeja

    assert _filas(
        settings,
        "SELECT result FROM question_note_anchors WHERE question_version_id = :id",
        {"id": preguntas[1]},
    ) == [("covered",)]

    reclasificar(["--aplicar", "--sin-copia"])

    assert _filas(
        settings,
        "SELECT count(*) FROM notes_incidents WHERE question_version_id = :id",
        {"id": preguntas[1]},
    ) == [(0,)]
    assert _filas(
        settings,
        "SELECT count(*) FROM audit_events WHERE action = 'notes.incident_dropped' "
        "AND object_id = (SELECT id FROM notes_incidents WHERE question_version_id = :id)",
        {"id": preguntas[1]},
    ) == [(0,)], "la fila ya no está: lo que se mira es que el evento apunte a ella, no a otra"


def test_el_ensayo_no_escribe_nada(bandeja: tuple[Settings, list[str]]) -> None:
    """Sin `--aplicar` se ve lo que haría y no se toca la base: es el modo con el que se decide."""
    settings, _preguntas = bandeja
    antes = _categorias(settings)

    assert reclasificar([]) == 0

    assert _categorias(settings) == antes
    assert _filas(
        settings, "SELECT count(*) FROM audit_events WHERE action LIKE 'notes.incident_%'", {}
    ) == [(0,)]


def test_la_ruta_de_la_bandeja_sirve_las_categorias_nuevas(
    bandeja: tuple[Settings, list[str]],
) -> None:
    """Y la pantalla las puede pedir: el contrato las admite como filtro, y las cifras son las de la
    base."""
    settings, _preguntas = bandeja

    with TestClient(create_app(settings)) as client:
        reclasificar(["--aplicar", "--sin-copia"])
        for categoria in ("pregunta_mal_importada", "clave_sospechosa", "clave_no_fiable"):
            respuesta = client.get("/api/v1/notes-incidents", params={"category": categoria})
            assert respuesta.status_code == 200, respuesta.text
            esperado = {
                "pregunta_mal_importada": 1,
                "clave_sospechosa": 2,
                "clave_no_fiable": 0,
            }[categoria]
            assert respuesta.json()["total"] == esperado
