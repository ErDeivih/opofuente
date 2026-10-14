"""De dónde sale cada conjunto: `origin_scope` en los datos, en el simulacro y en la guarda (D10).

Lo que se prueba aquí es lo que el encargo pide de este campo y nada más:

1. **se guarda y se cambia por la ruta auditada**: un conjunto nace con su procedencia declarada, y
   cambiarla deja su evento con el antes y el después;
2. **el vocabulario está cerrado**: un ámbito que no existe y un `PATCH` que no cambia nada se
   rechazan **antes** de tocar la base;
3. **un simulacro no lleva material de otra administración**: la misma composición con
   `exam_like=True` deja fuera las preguntas del conjunto `otra_administracion` y con
   `exam_like=False` las trae. Es la única consecuencia del campo, y es la que justifica que exista;
4. **un examen oficial importado queda protegido**: su respuesta correcta no se cambia desde la
   ficha, y el motivo que se lee es el del conjunto oficial — no una lista de nombres.

Las preguntas entran por el importador real (la ruta `parse`), la clave por la suya y la procedencia
por el `PATCH`: el único SQL de preparación es el del documento de la plantilla, porque no hay
ninguna ruta que invente un material sin pasar por la extracción entera.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy import text

from opofuente.application.study_service import (
    CompositionSpec,
    PartSpec,
    SessionMode,
)
from opofuente.config import Settings
from opofuente.infrastructure.db import build_engine, build_session_factory
from opofuente.infrastructure.question_file_repository import (
    SqlAlchemyQuestionFileRepository,
)

ALLOWED_ORIGIN = {"Origin": "http://127.0.0.1:5173"}

#: El tema donde se catalogan las preguntas de la prueba.
TEMA = "IV.1"


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


def _tema(client: TestClient, oposicion: dict[str, Any]) -> str:
    programa = client.get(
        f"/api/v1/convocations/{oposicion['active_convocation']['id']}/curriculum"
    ).json()
    return str(
        next(
            nodo
            for nodo in _aplanar(programa["nodes"])
            if nodo["node_type"] == "topic" and nodo["path"] == TEMA
        )["id"]
    )


def _texto(preguntas: int, *, desde: int = 1) -> str:
    """Preguntas distintas de verdad: el enunciado lleva su número, que la huella no normaliza."""
    lineas: list[str] = []
    for numero in range(desde, desde + preguntas):
        lineas.append(f"{numero}. El supuesto practico {numero} se resuelve en diez dias:")
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
    origen: str,
    set_type: str = "private_bank",
    activar_clave: bool = True,
) -> tuple[str, list[dict[str, Any]]]:
    """Un conjunto con su procedencia declarada, sus preguntas y (si se pide) su clave activa."""
    oposicion = _oposicion(client)
    creado = client.post(
        "/api/v1/question-sets",
        json={
            "title": titulo,
            "opposition_id": oposicion["id"],
            "set_type": set_type,
            "convocation_version_id": oposicion["active_convocation"]["id"],
            "origin_scope": origen,
        },
        headers=ALLOWED_ORIGIN,
    )
    assert creado.status_code == 201, creado.text
    assert creado.json()["origin_scope"] == origen
    conjunto = creado.json()
    importado = client.post(
        f"/api/v1/question-sets/{conjunto['id']}/parse",
        json={"kind": "questions", "text": texto},
        headers=ALLOWED_ORIGIN,
    )
    assert importado.status_code == 200, importado.text
    if activar_clave:
        claves = client.get(f"/api/v1/question-sets/{conjunto['id']}/answer-keys").json()
        activada = client.post(
            f"/api/v1/question-sets/{conjunto['id']}/answer-keys/{claves[0]['id']}/activate",
            headers=ALLOWED_ORIGIN,
        )
        assert activada.status_code == 200, activada.text
    preguntas = list(
        client.get("/api/v1/questions", params={"set_id": conjunto["id"], "limit": 200}).json()[
            "questions"
        ]
    )
    return str(conjunto["id"]), preguntas


def _catalogar(client: TestClient, pregunta_id: str, *, tema: str) -> None:
    respuesta = client.post(
        f"/api/v1/questions/{pregunta_id}/topics",
        json={"curriculum_node_id": tema},
        headers=ALLOWED_ORIGIN,
    )
    assert respuesta.status_code in (200, 201), respuesta.text


def test_la_procedencia_se_declara_se_cambia_y_se_audita(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """Un conjunto nace con su procedencia y cambiarla deja el antes y el después auditados."""
    oposicion = _oposicion(seeded_client)
    creado = seeded_client.post(
        "/api/v1/question-sets",
        json={
            "title": "Examen de prueba de procedencia",
            "opposition_id": oposicion["id"],
            "set_type": "official_exam",
            "origin_scope": "age",
        },
        headers=ALLOWED_ORIGIN,
    )
    assert creado.status_code == 201, creado.text
    set_id = str(creado.json()["id"])
    assert creado.json()["origin_scope"] == "age"

    # Sin decir nada, `desconocida`: no se afirma lo que no se sabe.
    otro = seeded_client.post(
        "/api/v1/question-sets",
        json={
            "title": "Banco de prueba sin procedencia declarada",
            "opposition_id": oposicion["id"],
            "set_type": "private_bank",
        },
        headers=ALLOWED_ORIGIN,
    )
    assert otro.status_code == 201, otro.text
    assert otro.json()["origin_scope"] == "desconocida"

    cambio = seeded_client.patch(
        f"/api/v1/question-sets/{set_id}",
        json={"origin_scope": "otra_administracion"},
        headers={**ALLOWED_ORIGIN, "X-OpoFuente-Actor": "prueba:procedencia"},
    )
    assert cambio.status_code == 200, cambio.text
    assert cambio.json()["origin_scope"] == "otra_administracion"

    leido = seeded_client.get(f"/api/v1/question-sets/{set_id}").json()
    assert leido["origin_scope"] == "otra_administracion"

    engine = build_engine(seeded_settings.data_paths.database)
    try:
        with engine.begin() as conexion:
            filas = conexion.execute(
                text(
                    "SELECT actor, before_json, after_json FROM audit_events "
                    "WHERE action = 'question_set.origin_scope_changed' AND object_id = :id"
                ),
                {"id": set_id},
            ).all()
    finally:
        engine.dispose()
    assert len(filas) == 1, "un cambio, un evento"
    actor, antes, despues = filas[0]
    assert actor == "prueba:procedencia"
    assert "age" in str(antes) and "otra_administracion" in str(despues)


def test_el_vocabulario_esta_cerrado_y_un_cambio_vacio_se_rechaza(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """Un ámbito que no existe y un `PATCH` que no cambia nada no llegan a la base."""
    oposicion = _oposicion(seeded_client)
    creado = seeded_client.post(
        "/api/v1/question-sets",
        json={
            "title": "Conjunto para el vocabulario cerrado",
            "opposition_id": oposicion["id"],
            "set_type": "private_bank",
        },
        headers=ALLOWED_ORIGIN,
    )
    set_id = str(creado.json()["id"])

    marciano = seeded_client.patch(
        f"/api/v1/question-sets/{set_id}",
        json={"origin_scope": "marciano"},
        headers=ALLOWED_ORIGIN,
    )
    assert marciano.status_code == 422, marciano.text

    vacio = seeded_client.patch(f"/api/v1/question-sets/{set_id}", json={}, headers=ALLOWED_ORIGIN)
    assert vacio.status_code == 422, vacio.text

    # Y el conjunto sigue como estaba: los dos rechazos no escribieron nada.
    assert seeded_client.get(f"/api/v1/question-sets/{set_id}").json()["origin_scope"] == (
        "desconocida"
    )


def test_un_simulacro_no_lleva_material_de_otra_administracion(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """La única consecuencia del campo: `exam_like` deja fuera lo que no es de esta
    administración."""
    oposicion = _oposicion(seeded_client)
    tema = _tema(seeded_client, oposicion)

    _set_edad, preguntas_edad = _conjunto(
        seeded_client,
        texto=_texto(6),
        titulo="Banco de la AGE para el simulacro",
        origen="age",
    )
    _set_otra, preguntas_otra = _conjunto(
        seeded_client,
        texto=_texto(6, desde=101),
        titulo="Banco de otra administración para el simulacro",
        origen="otra_administracion",
    )
    for pregunta in (*preguntas_edad, *preguntas_otra):
        _catalogar(seeded_client, str(pregunta["id"]), tema=tema)

    servicio = seeded_client.app.state.study_service
    especificacion = CompositionSpec(
        parts=(PartSpec(code="test", node_ids=(tema,), count=12),),
        mode=SessionMode.MOCK_EXAM,
        label="Simulacro de la prueba",
    )
    con_otra = servicio.compose(especificacion, opposition_id=oposicion["id"])
    assert con_otra.parts[0].available == 12, (
        "sin `exam_like`, el material de otra administración cuenta"
    )

    como_un_examen = servicio.compose(
        CompositionSpec(
            parts=(PartSpec(code="test", node_ids=(tema,), count=12),),
            mode=SessionMode.MOCK_EXAM,
            exam_like=True,
            label="Simulacro que se parece al examen",
        ),
        opposition_id=oposicion["id"],
    )
    assert como_un_examen.parts[0].available == 6, (
        "las 6 de otra administración no son de este examen"
    )
    assert como_un_examen.session.total_questions == 6

    # Y en un test por tema **sí cuentan**: son material para estudiar, y el test del alumno se
    # compone sin `exam_like` (solo el simulacro y el examen se parecen al examen real).
    por_tema = servicio.compose(
        CompositionSpec(
            parts=(PartSpec(code="test", node_ids=(tema,), count=12),),
            mode=SessionMode.PRACTICE,
            label="Test por tema",
        ),
        opposition_id=oposicion["id"],
    )
    assert por_tema.parts[0].available == 12


def test_un_examen_oficial_importado_queda_protegido(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """Un examen oficial no se «arregla» desde la ficha: su clave la publicó la administración.

    El examen se monta como lo deja el importador del INAP —conjunto oficial, procedencia `age` y su
    plantilla enlazada a un documento— y se comprueba que la guarda lo cubre **sin ampliarla**: la
    protección es del tipo del conjunto, no de una lista de nombres.
    """
    oposicion = _oposicion(seeded_client)
    assert oposicion["code"] == "tai-age"
    set_id, preguntas = _conjunto(
        seeded_client,
        texto=_texto(3),
        titulo="TAI ingreso libre 2019 · ejercicio único (examen oficial INAP)",
        origen="age",
        set_type="official_exam",
        activar_clave=False,
    )
    _documento_de_plantilla(seeded_settings, set_id)

    repositorio = SqlAlchemyQuestionFileRepository(
        build_session_factory(build_engine(seeded_settings.data_paths.database))
    )
    protegidos = {fila.id: fila for fila in repositorio.protected_sets()}
    assert set_id in protegidos, "el examen importado tiene que quedar protegido"
    assert protegidos[set_id].reason, "y con el motivo a la vista, no con un «no se puede» a secas"

    # La ficha lo rechaza con un 409 y **sin escribir nada**: la clave sigue donde estaba.
    intento = seeded_client.post(
        f"/api/v1/question-files/{preguntas[0]['id']}/answer-key",
        json={"correct_option_keys": ["b"], "note": "la clave oficial no se toca"},
        headers=ALLOWED_ORIGIN,
    )
    assert intento.status_code == 409, intento.text
    leida = seeded_client.get(f"/api/v1/questions/{preguntas[0]['id']}").json()
    assert leida["correct_option_keys"] == ["a"], "la clave oficial se queda como estaba"


def _documento_de_plantilla(settings: Settings, set_id: str) -> None:
    """Enlaza la plantilla del conjunto con un documento, por SQL y solo de preparación.

    Es el segundo camino a «oficial»: una plantilla que salió de un papel. No hay ninguna ruta que
    invente un material sin pasar por la extracción entera, así que aquí se escriben las filas del
    documento y se apunta la plantilla a él.
    """
    ahora = datetime(2026, 10, 13, 12, 0, tzinfo=UTC).isoformat()
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.begin() as conexion:
            # El artefacto va delante porque una versión de documento cuelga de él.
            conexion.execute(
                text(
                    "INSERT INTO source_artifacts (id, sha256, size_bytes, media_type, "
                    "storage_key, first_seen_at) VALUES ('art-origen', :sha, 100, 'text/plain', "
                    "'k', :ahora)"
                ),
                {"sha": "a" * 64, "ahora": ahora},
            )
            conexion.execute(
                text(
                    "INSERT INTO logical_documents (id, canonical_title, document_type, "
                    "authority_tier, owner_scope, created_at, updated_at) VALUES "
                    "('doc-origen', 'Plantilla de respuestas del examen de prueba', "
                    "'answer_key', 'A', 'public', :ahora, :ahora)"
                ),
                {"ahora": ahora},
            )
            conexion.execute(
                text(
                    "INSERT INTO document_versions (id, logical_document_id, artifact_id, "
                    "version_label, retrieved_at, language, status, approved_at, approved_by, "
                    "created_at) VALUES ('ver-origen', 'doc-origen', 'art-origen', 'definitiva', "
                    ":ahora, 'es', 'accepted', :ahora, 'local', :ahora)"
                ),
                {"ahora": ahora},
            )
            conexion.execute(
                text(
                    "UPDATE answer_key_versions SET source_document_version_id = 'ver-origen' "
                    "WHERE question_set_id = :id"
                ),
                {"id": set_id},
            )
    finally:
        engine.dispose()
