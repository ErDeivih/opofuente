"""El resumen de preparación (S12.6): «¿puedo estudiar ya, o me falta algo?».

Dos estados, los dos reales y por el camino de verdad: una base recién sembrada, donde no falta un
dato sino todo, y una oposición con material aceptado, asignado a su programa y con clave activa.

Las cifras se comprueban contra lo que la API sirve en las demás pantallas (el conjunto, sus
preguntas, sus claves) y no contra lo que el resumen dice de sí mismo: si el resumen contara otra
cosa que el banco, esta prueba tiene que fallar.
"""

from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient

from opofuente_testing.jobs import run_one_job

ALLOWED_ORIGIN = {"Origin": "http://127.0.0.1:5173"}

#: Un temario: prosa sobre un tema del programa, sin preguntas dentro.
TEMARIO = (
    "Tema 1. El procedimiento administrativo comun se regula en la Ley 39/2015, de 1 de octubre, "
    "que fija los plazos y la forma de las notificaciones.\n"
)

#: Un cuestionario con su tema en una columna: el importador lo resuelve contra el programa.
CSV_CON_TEMA = (
    "stem;option_a;option_b;correct;topic\n"
    "El plazo de alegaciones del caso A es de diez dias;Verdadero;Falso;a;I.1\n"
    "El silencio administrativo del caso B se regula en;La Ley 39/2015;La Ley 40/2015;a;I.1\n"
)


# --- ayudantes -------------------------------------------------------------------------------


def _oposicion_activa(client: TestClient) -> dict[str, Any]:
    return dict(next(op for op in client.get("/api/v1/oppositions").json() if op["active"]))


def _primer_tema(client: TestClient, convocatoria_id: str) -> dict[str, Any]:
    """El primer nodo de tipo tema del programa sembrado, con su ruta."""
    curriculum = client.get(f"/api/v1/convocations/{convocatoria_id}/curriculum").json()

    def recorrer(nodos: list[dict[str, Any]]) -> dict[str, Any] | None:
        for nodo in nodos:
            if nodo["node_type"] == "topic":
                return dict(nodo)
            encontrado = recorrer(nodo.get("children", []))
            if encontrado is not None:
                return encontrado
        return None

    tema = recorrer(curriculum["nodes"])
    assert tema is not None, "el perfil sembrado debería tener algún tema"
    return tema


def _pegar(client: TestClient, texto: str, titulo: str) -> str:
    """Pega material y deja que el pipeline lo copie, lo extraiga y lo clasifique."""
    respuesta = client.post(
        "/api/v1/ingestion-batches/paste",
        json={"text": texto, "title": titulo},
        headers=ALLOWED_ORIGIN,
    )
    assert respuesta.status_code == 200, respuesta.text
    batch_id = str(respuesta.json()["id"])
    run_one_job(client, attempts=3)
    detalle = client.get(f"/api/v1/ingestion-batches/{batch_id}").json()
    assert detalle["batch"]["status"] == "succeeded", detalle
    return batch_id


def _promover(client: TestClient, batch_id: str, *, titulo: str, papel: str) -> dict[str, Any]:
    """Convierte el material pegado en una versión de documento con su papel declarado."""
    representaciones = client.get(f"/api/v1/ingestion-batches/{batch_id}/representations").json()
    assert representaciones, "el pegado debería haber dejado una representación"
    artifact_id = representaciones[0]["artifact_id"]
    promocion = client.post(
        "/api/v1/documents",
        json={
            "artifact_id": artifact_id,
            "title": titulo,
            "document_type": papel,
            "authority_tier": "C",
        },
        headers=ALLOWED_ORIGIN,
    )
    assert promocion.status_code == 200, promocion.text
    return dict(promocion.json())


def _aceptar(client: TestClient, *, document_id: str, version_id: str) -> dict[str, Any]:
    respuesta = client.post(
        f"/api/v1/documents/{document_id}/versions/{version_id}/accept",
        headers=ALLOWED_ORIGIN,
    )
    assert respuesta.status_code == 200, respuesta.text
    return dict(respuesta.json())


def _resumen(client: TestClient, opposition_id: str) -> dict[str, Any]:
    respuesta = client.get(f"/api/v1/oppositions/{opposition_id}/readiness")
    assert respuesta.status_code == 200, respuesta.text
    return dict(respuesta.json())


def _paso(resumen: dict[str, Any], clave: str) -> dict[str, Any]:
    return dict(next(paso for paso in resumen["steps"] if paso["key"] == clave))


# --- sin nada todavía ------------------------------------------------------------------------


def test_sin_material_el_resumen_dice_que_falta_todo_y_por_donde_empezar(
    seeded_client: TestClient,
) -> None:
    """Una base recién sembrada no está lista, y el resumen dice qué hacer en vez de callarse."""
    oposicion = _oposicion_activa(seeded_client)

    resumen = _resumen(seeded_client, oposicion["id"])

    assert resumen["ready"] is False
    assert [paso["key"] for paso in resumen["steps"]] == ["material", "preguntas", "claves"]
    assert {paso["status"] for paso in resumen["steps"]} == {"empty"}
    assert [paso["count"] for paso in resumen["steps"]] == [0, 0, 0]
    # Lo que falta se dice con palabras y con la pantalla donde se resuelve.
    assert len(resumen["missing"]) == 3
    assert any("suelta tus carpetas" in frase for frase in resumen["missing"])
    assert all(paso["action_href"].startswith("/") for paso in resumen["steps"])
    assert resumen["opposition_name"] == oposicion["name"]

    # Y sin nada pendiente, la lista de lo que espera a una persona está vacía, no con ceros.
    pendientes = seeded_client.get("/api/v1/pending-actions").json()
    assert pendientes["actions"] == []
    assert pendientes["total"] == 0


def test_una_oposicion_que_no_existe_lo_dice_sin_inventar_un_resumen(
    seeded_client: TestClient,
) -> None:
    respuesta = seeded_client.get("/api/v1/oppositions/no-existe/readiness")

    assert respuesta.status_code == 404, respuesta.text
    assert respuesta.json()["code"] == "not_found"


# --- con material, preguntas y clave ---------------------------------------------------------


def test_con_material_asignado_preguntas_con_tema_y_clave_activa_esta_listo(
    seeded_client: TestClient,
) -> None:
    """El camino completo: temario aceptado y asignado, preguntas con tema y clave activa.

    Es el estado que el propietario quiere alcanzar sin saber qué pasos dio. Se recorre con la API
    real —pegar, promover, aceptar, asignar, importar y activar— y al final el resumen dice que sí.
    """
    oposicion = _oposicion_activa(seeded_client)
    convocatoria = oposicion["active_convocation"]["id"]
    tema = _primer_tema(seeded_client, convocatoria)

    # 1. Un temario: se pega, se promueve con su papel y se asigna a su tema.
    batch = _pegar(seeded_client, TEMARIO, "temario.txt")
    promocion = _promover(
        seeded_client, batch, titulo="Temario del procedimiento", papel="private_syllabus"
    )
    document_id = str(promocion["document_id"])
    version_id = str(promocion["version_id"])
    mapeo = seeded_client.post(
        f"/api/v1/document-versions/{version_id}/mappings",
        json={"curriculum_node_id": tema["id"], "coverage_type": "partial"},
        headers=ALLOWED_ORIGIN,
    )
    assert mapeo.status_code == 201, mapeo.text
    aceptada = _aceptar(seeded_client, document_id=document_id, version_id=version_id)
    assert aceptada["applied"] is True
    # Un temario no trae preguntas: no se inventa un conjunto vacío.
    assert aceptada["questions_imported"] == 0

    # 2. Un banco de preguntas con su tema en la columna: se importa y se activa su clave.
    conjunto = seeded_client.post(
        "/api/v1/question-sets",
        json={
            "title": "Banco del tema 1",
            "opposition_id": oposicion["id"],
            "set_type": "private_bank",
            "convocation_version_id": convocatoria,
        },
        headers=ALLOWED_ORIGIN,
    ).json()
    importado = seeded_client.post(
        f"/api/v1/question-sets/{conjunto['id']}/parse",
        json={"kind": "csv", "text": CSV_CON_TEMA},
        headers=ALLOWED_ORIGIN,
    )
    assert importado.status_code == 200, importado.text
    assert importado.json()["created"] == 2
    claves = seeded_client.get(f"/api/v1/question-sets/{conjunto['id']}/answer-keys").json()
    activada = seeded_client.post(
        f"/api/v1/question-sets/{conjunto['id']}/answer-keys/{claves[0]['id']}/activate",
        headers=ALLOWED_ORIGIN,
    )
    assert activada.status_code == 200, activada.text

    resumen = _resumen(seeded_client, oposicion["id"])

    assert resumen["ready"] is True, resumen
    assert resumen["missing"] == []
    material = _paso(resumen, "material")
    assert material["status"] == "ready"
    assert material["count"] == 1
    assert "Temario particular (1)" in material["detail"], material["detail"]
    preguntas = _paso(resumen, "preguntas")
    assert preguntas["status"] == "ready"
    # Las dos cifras coinciden con lo que sirve el banco, que es de donde salen.
    banco = seeded_client.get(
        "/api/v1/questions", params={"set_id": conjunto["id"], "limit": 50}
    ).json()
    assert preguntas["count"] == banco["total"] == 2
    claves_paso = _paso(resumen, "claves")
    assert claves_paso["status"] == "ready"
    assert claves_paso["count"] == 1
    assert "1 de 1" in claves_paso["detail"]


def test_lo_que_falta_se_dice_una_a_una_aunque_haya_material(
    seeded_client: TestClient,
) -> None:
    """Con material aceptado pero sin preguntas ni clave, el resumen señala lo que falta.

    Es el caso que de verdad importa para el propietario: no «no está listo», sino **qué** falta. Y
    un material que todavía no dice a qué parte del programa pertenece se declara en su paso, porque
    la cobertura por temas no lo ve, aunque no impida estudiar con él.
    """
    oposicion = _oposicion_activa(seeded_client)
    batch = _pegar(seeded_client, TEMARIO, "apuntes.txt")
    promocion = _promover(
        seeded_client, batch, titulo="Apuntes sin asignar", papel="personal_notes"
    )
    _aceptar(
        seeded_client,
        document_id=str(promocion["document_id"]),
        version_id=str(promocion["version_id"]),
    )

    resumen = _resumen(seeded_client, oposicion["id"])

    assert resumen["ready"] is False
    material = _paso(resumen, "material")
    # Hay apuntes: hay con qué estudiar. Lo que falta son las preguntas y la clave.
    assert material["status"] == "ready", material
    assert material["count"] == 1
    assert "sin decir todavía a qué parte de este programa" in material["detail"]
    # Y lo que falta se dice con las frases del resumen, no con otras compuestas por quien lee.
    assert len(resumen["missing"]) == 2, resumen
    assert {_paso(resumen, "preguntas")["detail"], _paso(resumen, "claves")["detail"]} == set(
        resumen["missing"]
    )


def test_lo_que_espera_a_una_persona_se_cuenta_con_la_cifra_de_su_pantalla(
    seeded_client: TestClient,
) -> None:
    """La lista de pendientes cuenta lo mismo que las pantallas donde se resuelve.

    No es una lista de todo lo que existe: es la de lo que **hoy** espera a alguien. Un material sin
    aceptar y las decisiones que dejó la clasificación aparecen; lo que no hay, no aparece.
    """
    batch = _pegar(seeded_client, TEMARIO, "temario-pendiente.txt")
    promocion = _promover(seeded_client, batch, titulo="Temario sin aceptar", papel="unknown")
    assert promocion["created_version"] is True

    pendientes = seeded_client.get("/api/v1/pending-actions").json()
    acciones = {accion["key"]: accion for accion in pendientes["actions"]}

    # El material promocionado está importado y sin aceptar: eso espera a una persona.
    assert acciones["versiones"]["count"] == 1
    assert acciones["versiones"]["href"] == "/biblioteca"
    # Y las propuestas que dejó el pipeline: la cifra es la que sirve la pantalla donde se resuelven
    # —`/revision`, que enseña grupos de revisión—. Una decisión puede llevar dos propuestas dentro
    # (el material y su texto, DEBT-018), así que contar propuestas no es contar decisiones.
    grupos = seeded_client.get("/api/v1/review-groups").json()
    assert acciones["clasificaciones"]["count"] == len(grupos)
    assert acciones["clasificaciones"]["count"] > 0, "clasificar tiene que haber propuesto algo"
    assert acciones["clasificaciones"]["href"] == "/revision"
    # Y agrupar no borra: las propuestas siguen estando, y son más que las decisiones.
    propuestas = seeded_client.get(
        "/api/v1/classification-proposals", params={"status": "pending", "limit": 1}
    ).json()
    assert propuestas["total"] >= len(grupos), "el grupo decide propuestas que existen"
    # Lo que no hay no se enseña: sin cambios de fuente propuestos, esa acción no está.
    assert "cambios" not in acciones
    assert pendientes["total"] == sum(accion["count"] for accion in pendientes["actions"])
