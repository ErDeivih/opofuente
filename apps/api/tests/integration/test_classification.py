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

from fastapi.testclient import TestClient

from opofuente_testing.jobs import run_one_job

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
    respuesta = client.post("/api/v1/classification-runs", headers=ALLOWED_ORIGIN)
    assert respuesta.status_code == 200, respuesta.text
    return respuesta.json()


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

    assert informe["subjects"] >= 2, "se clasifican la representación y su artefacto"
    assert informe["proposals_created"] == 0, "volver a clasificar no duplica propuestas"
    assert informe["proposals_unchanged"] >= 1
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
    primera = _clasificar(seeded_client)
    total_antes = len(_propuestas(seeded_client))

    segunda = _clasificar(seeded_client)

    assert segunda["proposals_created"] == 0
    assert segunda["proposals_unchanged"] >= primera["proposals_created"]
    assert len(_propuestas(seeded_client)) == total_antes


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
