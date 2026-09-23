"""Pruebas de integración de la clasificación y la revisión (S04) por la API real.

El camino que se recorre es el del usuario: pegar material de verdad, dejarlo copiar y extraer,
lo extraiga, pedir una pasada de clasificación y revisar lo que propone. Nada de esto se inventa: el
texto pegado es sintético y menciona títulos del programa **sembrado**, que la propia prueba lee
de la API para no depender de un fixture escrito a mano.

Lo que se comprueba aquí es lo que no se puede comprobar en una prueba unitaria: que una decisión
crea (o retira) su mapeo, que la cobertura cambia con ella, que deshacer la revierte y deja traza,
que el lote respeta las excepciones, que un eje crítico no se aplica solo y que el mismo texto
dos veces se reconoce como duplicado.
"""

from __future__ import annotations

from typing import Any

import pytest
from fastapi.testclient import TestClient

from opofuente.domain.errors import JobCancelledError
from opofuente.domain.jobs import Job, JobStatus, JobType
from opofuente_testing.jobs import FakeExecution, FixedClock, run_one_job

ALLOWED_ORIGIN = {"Origin": "http://127.0.0.1:5173"}


# --- ayudantes ------------------------------------------------------------------------------


def _pegar(client: TestClient, texto: str, titulo: str) -> str:
    respuesta = client.post(
        "/api/v1/ingestion-batches/paste",
        json={"text": texto, "title": titulo},
        headers=ALLOWED_ORIGIN,
    )
    assert respuesta.status_code == 200, respuesta.text
    batch_id: str = respuesta.json()["id"]
    # Dos pasadas del worker: la copia y la extracción que se encola al terminar la copia.
    run_one_job(client, attempts=3)
    detalle = client.get(f"/api/v1/ingestion-batches/{batch_id}").json()
    assert detalle["batch"]["status"] == "succeeded", detalle
    return batch_id


def _primera_representacion(client: TestClient, batch_id: str) -> dict[str, Any]:
    respuesta = client.get(f"/api/v1/ingestion-batches/{batch_id}/representations")
    assert respuesta.status_code == 200, respuesta.text
    representaciones: list[dict[str, Any]] = respuesta.json()
    assert representaciones, "el pegado debería haber dejado una representación con texto"
    return representaciones[0]


def _un_tema_del_programa(client: TestClient) -> dict[str, Any]:
    """Devuelve un nodo del programa sembrado (id, path y título) para pegarlo en el texto."""
    oposiciones = client.get("/api/v1/oppositions").json()
    activa = next(oposicion for oposicion in oposiciones if oposicion["active"])
    convocatorias = client.get(f"/api/v1/oppositions/{activa['id']}/convocations").json()
    convocatoria = convocatorias[0]
    curriculum = client.get(f"/api/v1/convocations/{convocatoria['id']}/curriculum").json()

    def _recorrer(nodos: list[dict[str, Any]]) -> dict[str, Any] | None:
        for nodo in nodos:
            if nodo["node_type"] == "topic":
                return nodo
            encontrado = _recorrer(nodo.get("children", []))
            if encontrado is not None:
                return encontrado
        return None

    tema = _recorrer(curriculum["nodes"])
    assert tema is not None, "el perfil sembrado debería tener algún tema"
    return tema


def _propuestas(client: TestClient, **filtros: Any) -> list[dict[str, Any]]:
    respuesta = client.get("/api/v1/classification-proposals", params=filtros)
    assert respuesta.status_code == 200, respuesta.text
    return respuesta.json()["proposals"]


def _clasificar(client: TestClient) -> dict[str, Any]:
    """Encola la pasada de clasificación del corpus y **la ejecuta** (DEBT-024).

    Clasificar dejó de ser una petición larga: la ruta responde **202** con el trabajo encolado y
    el trabajador lo ejecuta. En las pruebas lo corre `run_one_job`, para que el resultado no
    dependa de cuándo despierte el worker.
    """
    respuesta = client.post("/api/v1/classification-runs", headers=ALLOWED_ORIGIN)
    assert respuesta.status_code == 202, respuesta.text
    trabajo: dict[str, Any] = respuesta.json()
    assert trabajo["job_type"] == "classify_document"
    run_one_job(client, attempts=3)
    detalle: dict[str, Any] = client.get(f"/api/v1/jobs/{trabajo['id']}").json()
    return detalle


def _material_clasificable(client: TestClient) -> tuple[str, dict[str, Any]]:
    """Pega material que menciona un tema real del programa y devuelve (batch_id, tema)."""
    tema = _un_tema_del_programa(client)
    texto = (
        f"Apuntes de estudio sobre {tema['title']}. "
        "Resumen personal del tema, con esquemas propios y ejemplos."
    )
    batch_id = _pegar(client, texto, "mis-apuntes.txt")
    return batch_id, tema


# --- clasificación --------------------------------------------------------------------------


def test_una_pasada_de_clasificacion_propone_con_evidencia_y_sin_inventar(
    seeded_client: TestClient,
) -> None:
    """Clasificar deja propuestas con su evidencia; el material sin señales no genera relleno."""
    _, tema = _material_clasificable(seeded_client)

    # El pipeline se encadena solo: al terminar la extracción se encola la clasificación, así que el
    # material recién pegado ya tiene propuestas **sin** haber pedido una pasada a mano.
    assert _propuestas(seeded_client), "clasificar no puede depender de que alguien lo pida"

    informe = _clasificar(seeded_client)

    # El trabajo termina y su resumen viaja en el paso: es lo que la pantalla enseña al terminar.
    assert informe["status"] == "succeeded", informe
    assert "sujetos" in (informe["step"] or ""), informe
    # Volver a clasificar no crea propuestas nuevas: se cuentan antes y después.
    total_antes = len(_propuestas(seeded_client))
    _clasificar(seeded_client)
    assert len(_propuestas(seeded_client)) == total_antes, "clasificar dos veces no duplica"
    propuestas = _propuestas(seeded_client)
    temas = [propuesta for propuesta in propuestas if propuesta["axis"] == "topic"]
    assert temas, f"debería haberse propuesto el tema pegado: {propuestas}"
    propuesta = temas[0]
    # El motor propone **un** nodo, y puede haber varios cuyo título aparezca en el texto: lo que se
    # exige es que el tema propuesto sea uno de los que el material menciona, no cualquiera.
    assert propuesta["value_label"], "el valor viaja con su título legible"
    assert propuesta["proposed_value"] == tema["path"] or (
        tema["title"] in propuesta["value_label"] or propuesta["value_label"] in tema["title"]
    ), f"se propuso un tema que el texto no menciona: {propuesta}"
    assert propuesta["evidence"], "una propuesta sin evidencia no se puede revisar"
    assert propuesta["band"] in {"high", "medium", "low"}
    assert propuesta["status"] in {"pending", "auto_applied_provisional"}


def test_la_clasificacion_es_idempotente(seeded_client: TestClient) -> None:
    """Volver a clasificar el mismo material no duplica propuestas."""
    _material_clasificable(seeded_client)
    _clasificar(seeded_client)
    total_antes = len(_propuestas(seeded_client))

    segunda = _clasificar(seeded_client)

    assert segunda["status"] == "succeeded", segunda
    assert len(_propuestas(seeded_client)) == total_antes


def test_dos_pasadas_seguidas_no_encolan_dos_trabajos(seeded_client: TestClient) -> None:
    """Pulsar dos veces «Buscar propuestas ahora» no clasifica dos veces (DEBT-024).

    La clave de idempotencia es una sola para el corpus: mientras hay una pasada viva, la segunda
    petición devuelve **esa** pasada en lugar de encolar otra.
    """
    primera = seeded_client.post("/api/v1/classification-runs", headers=ALLOWED_ORIGIN)
    segunda = seeded_client.post("/api/v1/classification-runs", headers=ALLOWED_ORIGIN)

    assert primera.status_code == 202, primera.text
    assert segunda.status_code == 202, segunda.text
    assert primera.json()["id"] == segunda.json()["id"], "debería devolver la pasada que ya había"

    # Y al ejecutarla, el trabajo queda terminado con su resumen.
    run_one_job(seeded_client, attempts=3)
    detalle = seeded_client.get(f"/api/v1/jobs/{primera.json()['id']}").json()
    assert detalle["status"] == "succeeded", detalle
    assert detalle["progress"] == 1.0


def test_un_eje_critico_no_se_aplica_solo_aunque_la_confianza_sea_alta(
    seeded_client: TestClient,
) -> None:
    """Autoridad y derechos siempre pasan por la revisión del usuario (04 §8)."""
    tema = _un_tema_del_programa(seeded_client)
    texto = (
        "Boletín Oficial del Estado. Resolución de 12 de enero de 2025. "
        f"Uso privado. Temario oficial sobre {tema['title']}."
    )
    _pegar(seeded_client, texto, "documento-oficial.txt")

    _clasificar(seeded_client)

    criticas = [
        propuesta
        for propuesta in _propuestas(seeded_client)
        if propuesta["axis"] in {"authority", "rights"}
    ]
    assert criticas, "el texto tiene señales de autoridad y de derechos"
    for propuesta in criticas:
        assert propuesta["is_critical"] is True
        assert propuesta["status"] == "pending", "un eje crítico no se aplica solo, nunca"


# --- decisiones, cobertura y deshacer ---------------------------------------------------------


def test_aceptar_un_tema_crea_mapeo_cobertura_y_deshacer_lo_revierte(
    seeded_client: TestClient,
) -> None:
    """El ciclo completo: aceptar → mapeo y cobertura aceptada → deshacer → todo como estaba."""
    _material_clasificable(seeded_client)
    _clasificar(seeded_client)
    propuesta = _propuestas(seeded_client, axis="topic")[0]

    aceptada = seeded_client.post(
        f"/api/v1/classification-proposals/{propuesta['id']}/accept",
        json={"note": "Confirmado por el usuario", "coverage_type": "partial"},
        headers=ALLOWED_ORIGIN,
    )

    assert aceptada.status_code == 200, aceptada.text
    resultado = aceptada.json()
    assert resultado["applied"] is True
    assert resultado["mapping_id"], "aceptar un tema tiene que crear su mapeo"
    assert resultado["audit_event_id"], "toda decisión deja su traza de auditoría"

    mapeos = seeded_client.get(
        "/api/v1/mappings",
        params={"subject_type": propuesta["subject_type"], "subject_id": propuesta["subject_id"]},
    ).json()
    assert len(mapeos) == 1, mapeos
    mapeo = mapeos[0]
    assert mapeo["node_path"] == propuesta["proposed_value"]
    assert mapeo["status"] == "accepted"
    assert mapeo["approved_at"] is not None

    cobertura = seeded_client.get(f"/api/v1/curriculum-nodes/{mapeo['node_id']}/coverage").json()
    assert cobertura["accepted"] >= 1, cobertura
    nodo_propio = next(nodo for nodo in cobertura["subtree"] if nodo["node_id"] == mapeo["node_id"])
    assert nodo_propio["accepted"] == 1
    assert nodo_propio["materials"], "la cobertura dice con qué material está cubierto el nodo"
    # El artefacto y su representación son el **mismo material**: la cobertura lo cuenta una vez,
    # así que aquí ya no hay provisional (el material está aceptado).
    assert nodo_propio["provisional"] == 0

    deshecha = seeded_client.post(
        f"/api/v1/classification-decisions/{resultado['audit_event_id']}/undo",
        headers=ALLOWED_ORIGIN,
    )

    assert deshecha.status_code == 200, deshecha.text
    assert deshecha.json()["applied"] is True
    # Deshacer restaura el estado **anterior**, no siempre «pendiente»: si la propuesta venía de una
    # aplicación provisional, vuelve ahí: «deshacer restaura mappings/estados».
    vuelta = seeded_client.get(f"/api/v1/classification-proposals/{propuesta['id']}").json()
    assert vuelta["status"] == propuesta["status"]
    assert vuelta["decided_at"] == propuesta["decided_at"]
    # Y el mapeo que había antes de la decisión se recupera en su estado provisional, no se pierde.
    mapeos_despues = seeded_client.get(
        "/api/v1/mappings",
        params={
            "subject_type": propuesta["subject_type"],
            "subject_id": propuesta["subject_id"],
        },
    ).json()
    assert [mapeo["status"] for mapeo in mapeos_despues] == ["provisional"]
    cobertura_final = seeded_client.get(
        f"/api/v1/curriculum-nodes/{mapeo['node_id']}/coverage"
    ).json()
    assert cobertura_final["accepted"] == 0, "el mapeo aceptado se retira al deshacer"
    assert cobertura_final["provisional"] == 1, (
        "el material vuelve a contar una sola vez, como provisional"
    )


def test_aceptar_un_tema_que_no_esta_en_el_programa_es_un_conflicto(
    seeded_client: TestClient,
) -> None:
    """No se acepta a medias: si el nodo no existe, la decisión no se aplica y se explica (409)."""
    _material_clasificable(seeded_client)
    _clasificar(seeded_client)
    propuesta = _propuestas(seeded_client, axis="topic")[0]

    respuesta = seeded_client.post(
        f"/api/v1/classification-proposals/{propuesta['id']}/accept",
        json={"override_value": "tema/que-no-existe"},
        headers=ALLOWED_ORIGIN,
    )

    assert respuesta.status_code == 409, respuesta.text
    assert respuesta.json()["code"] == "classification_conflict"
    sigue = seeded_client.get(f"/api/v1/classification-proposals/{propuesta['id']}").json()
    assert sigue["status"] == propuesta["status"], "una decisión fallida no cambia el estado"


def test_el_lote_respeta_las_excepciones_y_no_es_todo_o_nada(seeded_client: TestClient) -> None:
    """Una aceptación masiva puede excluir filas, y la respuesta dice qué se aplicó y qué no."""
    _material_clasificable(seeded_client)
    _clasificar(seeded_client)
    pendientes = list(_propuestas(seeded_client, status="pending"))
    assert len(pendientes) >= 2, f"hacen falta dos propuestas pendientes: {pendientes}"
    excepcion = pendientes[0]["id"]
    en_lote = [propuesta["id"] for propuesta in pendientes[1:]]

    respuesta = seeded_client.post(
        "/api/v1/classification-proposals/bulk-decision",
        json={
            "proposal_ids": [excepcion, *en_lote],
            "decision": "accepted",
            "note": "Revisión en lote",
            "excluded": [excepcion],
        },
        headers=ALLOWED_ORIGIN,
    )

    assert respuesta.status_code == 200, respuesta.text
    cuerpo = respuesta.json()
    assert cuerpo["excluded"] == [excepcion]
    assert cuerpo["requested"] == len(en_lote) + 1
    assert cuerpo["applied"] == len(en_lote)
    assert len(cuerpo["outcomes"]) == len(en_lote)
    assert seeded_client.get(f"/api/v1/classification-proposals/{excepcion}").json()["status"] == (
        "pending"
    ), "la excepción se queda como estaba para decidirla aparte"


def test_los_grupos_de_revision_agrupan_por_eje_y_valor(seeded_client: TestClient) -> None:
    """La cola de revisión se agrupa por eje y valor propuesto, con su confianza mínima y máxima."""
    _material_clasificable(seeded_client)
    _clasificar(seeded_client)

    grupos = seeded_client.get("/api/v1/review-groups").json()

    assert grupos, "debería haber grupos con propuestas pendientes"
    for grupo in grupos:
        assert grupo["proposal_ids"], "un grupo sin propuestas no es un grupo"
        assert grupo["size"] == len(grupo["proposal_ids"])
        assert grupo["min_confidence"] <= grupo["max_confidence"]
        assert grupo["label"]
    claves = [grupo["key"] for grupo in grupos]
    assert len(claves) == len(set(claves)), "las claves de grupo no se repiten"


# --- duplicados ------------------------------------------------------------------------------


def test_el_mismo_texto_pegado_dos_veces_se_reconoce_como_duplicado(
    seeded_client: TestClient,
) -> None:
    """Mismo texto con otra maquetación: bytes distintos, contenido igual, y se agrupa.

    Pegar dos veces **exactamente** lo mismo no llega aquí: son los mismos bytes, así que el almacén
    los reconoce por hash y queda un artefacto con dos orígenes (eso lo prueba S02). Aquí se prueba
    aquí es el caso que sí necesita detección: el mismo texto escrito con otros espacios.
    """
    mismo_texto = (
        "Resumen personal del bloque de legislación. Incluye un esquema propio y ejemplos."
    )
    _pegar(seeded_client, mismo_texto, "resumen-a.txt")
    # Mismo texto con el espaciado cambiado: otro fichero, mismo contenido.
    _pegar(seeded_client, mismo_texto.replace(" ", "  "), "resumen-b.txt")

    _clasificar(seeded_client)

    clusters = seeded_client.get("/api/v1/duplicate-clusters").json()
    mismo_texto = [cluster for cluster in clusters if cluster["kind"] == "same_text"]
    assert mismo_texto, f"el mismo texto debería agruparse: {clusters}"
    cluster = mismo_texto[0]
    assert len(cluster["members"]) == 2
    assert cluster["status"] == "open", "un duplicado no se resuelve solo"


def test_resolver_un_duplicado_queda_auditado_y_no_borra_nada(seeded_client: TestClient) -> None:
    """Resolver un cluster solo lo marca: el material sigue entero."""
    _pegar(
        seeded_client,
        "Apuntes repetidos a propósito para comprobar los duplicados de texto.",
        "duplicado-a.txt",
    )
    _pegar(
        seeded_client,
        "Apuntes  repetidos  a  propósito  para  comprobar  los  duplicados  de  texto.",
        "duplicado-b.txt",
    )
    _clasificar(seeded_client)
    cluster = next(
        cluster
        for cluster in seeded_client.get("/api/v1/duplicate-clusters").json()
        if cluster["kind"] == "same_text"
    )
    ids_antes = {miembro["subject_id"] for miembro in cluster["members"]}

    respuesta = seeded_client.post(
        f"/api/v1/duplicate-clusters/{cluster['id']}/resolve",
        json={"relation": "revision_candidate", "note": "Es una revisión del mismo resumen"},
        headers=ALLOWED_ORIGIN,
    )

    assert respuesta.status_code == 200, respuesta.text
    resuelto = respuesta.json()
    assert resuelto["status"] == "resolved"
    assert resuelto["relation"] == "revision_candidate"
    assert {miembro["subject_id"] for miembro in resuelto["members"]} == ids_antes
    listado = seeded_client.get("/api/v1/duplicate-clusters?status=resolved").json()
    assert [cluster["id"] for cluster in listado] == [cluster["id"]]


# --- deshacer: regresiones del corrector ------------------------------------------------------


def test_deshacer_una_aceptacion_sin_estado_previo_vuelve_a_pendiente(
    seeded_client: TestClient,
) -> None:
    """Si la propuesta no venía de ninguna aplicación automática, deshacer la deja pendiente."""
    _material_clasificable(seeded_client)
    _clasificar(seeded_client)
    # Una propuesta de banda media no se aplica sola: está pendiente de verdad y sin efecto previo.
    propuesta = next(
        p
        for p in _propuestas(seeded_client)
        if p["axis"] == "document_type" and p["status"] == "pending"
    )
    assert propuesta["status"] == "pending"
    aceptada = seeded_client.post(
        f"/api/v1/classification-proposals/{propuesta['id']}/accept",
        json={},
        headers=ALLOWED_ORIGIN,
    )
    assert aceptada.status_code == 200, aceptada.text

    deshecha = seeded_client.post(
        f"/api/v1/classification-decisions/{aceptada.json()['audit_event_id']}/undo",
        headers=ALLOWED_ORIGIN,
    )

    assert deshecha.status_code == 200, deshecha.text
    vuelta = seeded_client.get(f"/api/v1/classification-proposals/{propuesta['id']}").json()
    assert vuelta["status"] == "pending"
    assert vuelta["decided_at"] is None
    assert vuelta["decision_note"] is None


def test_deshacer_sin_decisiones_es_un_conflicto(seeded_client: TestClient) -> None:
    """Sin decisión que deshacer se responde 409 con el motivo, sin inventar una reversión."""
    _material_clasificable(seeded_client)
    _clasificar(seeded_client)
    pendiente = _propuestas(seeded_client, status="pending")[0]
    antes = seeded_client.get(f"/api/v1/classification-proposals/{pendiente['id']}").json()

    respuesta = seeded_client.post(
        f"/api/v1/classification-decisions/{pendiente['id']}/undo",
        headers=ALLOWED_ORIGIN,
    )

    assert respuesta.status_code == 409, respuesta.text
    assert respuesta.json()["code"] == "classification_conflict"
    despues = seeded_client.get(f"/api/v1/classification-proposals/{pendiente['id']}").json()
    assert despues["status"] == antes["status"], "un conflicto no cambia nada"


# --- avance del trabajo (DEBT-024) ------------------------------------------------------------


def _trabajo_de_clasificacion() -> Job:
    """Un trabajo de clasificación en curso, sin encolarlo: aquí lo ejecuta la propia prueba."""
    ahora = FixedClock().now()
    return Job(
        id="job-de-prueba",
        job_type=JobType.CLASSIFY_DOCUMENT,
        status=JobStatus.RUNNING,
        payload={"limit": 200},
        progress=0.0,
        attempts=0,
        max_attempts=3,
        created_at=ahora,
        updated_at=ahora,
    )


def test_la_pasada_de_clasificacion_informa_de_sus_tramos(seeded_client: TestClient) -> None:
    """Clasificar dice por dónde va: el avance del trabajo no salta de 0,05 a 1 (DEBT-024).

    Se ejecuta el manejador del trabajo con una ejecución de prueba, que es lo que permite ver
    **todos** los informes y no solo el último que quedó guardado.
    """
    _material_clasificable(seeded_client)
    app: Any = seeded_client.app
    ejecucion = FakeExecution(_trabajo_de_clasificacion())

    app.state.classification_service.run_classification_job(ejecucion)

    avance = ejecucion.progress_calls
    assert avance[0] == 0.05 and avance[-1] == 1.0, avance
    intermedios = [valor for valor in avance if 0.05 < valor < 1.0]
    assert len(intermedios) >= 3, f"clasificar informa de sus tramos, no de uno solo: {avance}"
    assert avance == sorted(avance), f"el avance no puede retroceder: {avance}"
    pasos = [paso or "" for paso in ejecucion.progress_steps]
    assert any("clasificando material (" in paso for paso in pasos), pasos
    assert any("guardando propuestas" in paso for paso in pasos), pasos
    assert any("buscando duplicados" in paso for paso in pasos), pasos
    # El último paso es el resumen: es lo que la pantalla enseña cuando el trabajo termina.
    assert "sujetos" in pasos[-1], pasos


def test_cancelar_una_pasada_de_clasificacion_la_corta_a_mitad(client: TestClient) -> None:
    """Pedir cancelar corta la pasada entre tramos en lugar de dejarla terminar entera."""
    app: Any = client.app
    # La primera comprobación la hace el propio manejador al empezar; la segunda, ya dentro de la
    # pasada: con `cancel_after=1` lo que se prueba es que se comprueba **durante** el trabajo.
    ejecucion = FakeExecution(_trabajo_de_clasificacion(), cancel_after=1)

    with pytest.raises(JobCancelledError):
        app.state.classification_service.run_classification_job(ejecucion)

    assert ejecucion.progress_calls == [0.05], ejecucion.progress_calls


# --- reconciliación: la misma pregunta sobre el material y sobre su texto (DEBT-018) -----------


def _grupos(client: TestClient) -> list[dict[str, Any]]:
    respuesta = client.get("/api/v1/review-groups")
    assert respuesta.status_code == 200, respuesta.text
    return respuesta.json()


def _grupo_de_tipo_documental(client: TestClient) -> dict[str, Any]:
    """El grupo de tipo documental del material (no el de su texto): el que manda el artefacto."""
    grupos = _grupos(client)
    grupo = next(
        (
            candidato
            for candidato in grupos
            if candidato["axis"] == "document_type" and candidato["subject_type"] == "artifact"
        ),
        None,
    )
    assert grupo is not None, f"debería haber un grupo de tipo documental del material: {grupos}"
    return grupo


def test_la_misma_propuesta_sobre_el_material_y_su_texto_es_una_decision(
    seeded_client: TestClient,
) -> None:
    """La cola enseña **decisiones**, no filas, y las dos pantallas dicen el mismo número.

    Pegar un fichero deja dos sujetos clasificables —el artefacto y su representación— y los dos se
    clasifican con el mismo texto, así que el motor propone lo mismo dos veces. En la cola eso es
    una fila con las dos propuestas dentro, y esas propuestas existen: agrupar no es borrar.
    """
    _material_clasificable(seeded_client)
    _clasificar(seeded_client)

    propuestas = _propuestas(seeded_client, status="pending")
    grupos = _grupos(seeded_client)
    grupo = _grupo_de_tipo_documental(seeded_client)

    assert grupo["size"] >= 2, f"el material y su texto van juntos: {grupo}"
    assert len(grupo["proposal_ids"]) == grupo["size"]
    assert len(grupos) < len(propuestas), (
        "si cada propuesta fuera un grupo, esto no sería una reconciliación"
    )
    # Nada se esconde: cada propuesta del grupo sigue estando entre las pendientes.
    pendientes = {propuesta["id"] for propuesta in propuestas}
    for candidato in grupos:
        assert set(candidato["proposal_ids"]) <= pendientes

    # Y la pantalla de Inicio cuenta lo mismo que la de Revisión: decisiones, no filas.
    acciones = seeded_client.get("/api/v1/pending-actions").json()["actions"]
    accion = next(accion for accion in acciones if accion["key"] == "clasificaciones")
    assert accion["count"] == len(grupos), acciones


def test_decidir_el_grupo_decide_el_material_y_su_texto(seeded_client: TestClient) -> None:
    """Una decisión decide los dos sujetos: ninguno se queda sin clasificar por ir agrupado.

    Si el grupo juntara las propuestas y decidiera solo una, el material seguiría sin tipo y el
    enlace de plantilla de ADR-017 se rompería justo donde el usuario cree haber decidido.
    """
    _material_clasificable(seeded_client)
    _clasificar(seeded_client)

    grupo = _grupo_de_tipo_documental(seeded_client)
    ids = list(grupo["proposal_ids"])

    respuesta = seeded_client.post(
        "/api/v1/classification-proposals/bulk-decision",
        json={
            "proposal_ids": ids,
            "decision": "accepted",
            "note": "Una decisión, dos sujetos",
        },
        headers=ALLOWED_ORIGIN,
    )

    assert respuesta.status_code == 200, respuesta.text
    assert respuesta.json()["applied"] == len(ids)
    for proposal_id in ids:
        detalle = seeded_client.get(f"/api/v1/classification-proposals/{proposal_id}").json()
        assert detalle["status"] == "accepted", detalle
    # Y el grupo ya no está esperando: una decisión, una fila menos.
    assert all(candidato["key"] != grupo["key"] for candidato in _grupos(seeded_client))
