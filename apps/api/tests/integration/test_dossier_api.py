"""Pruebas de integración del dossier del tema (S13, parte 1).

Se monta un corpus sintético con SQL directo —dos documentos publicados, uno sin publicar, uno con
calidad pobre y uno con dos secciones de las que solo una está asignada— y se comprueba lo que el
dossier **dice** y lo que **no** dice:

1. los pasajes de todas las fuentes, cada uno con su procedencia (documento, versión, página);
2. el mismo texto en dos fuentes se cita una vez y se declara dónde más está;
3. lo que no se puede citar no se cita: se declara como hueco con su motivo;
4. un tema sin material lo dice con su hueco, y un nodo que no existe responde 404;
5. archivar guarda la historia: la versión anterior se lee como se leyó, y con material nuevo
aparece
   una versión nueva;
6. **un mapeo de sección alcanza a esa sección**, no al documento entero, y la búsqueda por ámbito
dice
   lo mismo que el dossier (dos definiciones de «pertenece» serían dos verdades).
"""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi.testclient import TestClient
from sqlalchemy import text

from opofuente.application.search_service import SearchRequest, SearchService
from opofuente.config import Settings
from opofuente.domain.rag import SearchFilters
from opofuente.infrastructure.db import build_engine, build_session_factory
from opofuente.infrastructure.dossier_repository import (
    _TRAMOS_DEL_TEMA,
    SqlAlchemyDossierRepository,
)
from opofuente.infrastructure.search_repository import SqlAlchemySearchRepository

AHORA = datetime(2026, 9, 24, 9, 0, tzinfo=UTC)
ALLOWED_ORIGIN = {"Origin": "http://127.0.0.1:5173"}

REPETIDO = "El plazo de alegaciones es de diez dias habiles."


def _ejecutar(
    settings: Settings, sentencia: str, parametros: dict[str, object] | None = None
) -> None:
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.begin() as conexion:
            conexion.execute(text(sentencia), parametros or {})
    finally:
        engine.dispose()


def _documento(
    settings: Settings,
    *,
    version_id: str,
    titulo: str,
    estado: str = "accepted",
    calidad: str = "good",
) -> None:
    _ejecutar(
        settings,
        "INSERT INTO source_artifacts (id, sha256, size_bytes, media_type, storage_key, "
        "first_seen_at) VALUES (:id, :sha, 10, 'text/plain', 'k', :ahora)",
        {"id": f"art-{version_id}", "sha": f"{version_id}-".ljust(64, "b"), "ahora": AHORA},
    )
    _ejecutar(
        settings,
        "INSERT INTO extracted_representations (id, artifact_id, extractor_name, "
        "extractor_version, kind, status, quality, char_count, created_at) VALUES (:rep, :art, "
        "'text', '1', 'native_text', 'extracted', :calidad, 100, :ahora)",
        {
            "rep": f"rep-{version_id}",
            "art": f"art-{version_id}",
            "calidad": calidad,
            "ahora": AHORA,
        },
    )
    _ejecutar(
        settings,
        "INSERT INTO logical_documents (id, canonical_title, document_type, owner_scope, "
        "created_at, updated_at) VALUES (:doc, :titulo, 'personal_notes', 'private_user', :ahora, "
        ":ahora)",
        {"doc": f"doc-{version_id}", "titulo": titulo, "ahora": AHORA},
    )
    _ejecutar(
        settings,
        "INSERT INTO document_versions (id, logical_document_id, artifact_id, representation_id, "
        "status, approved_at, language, created_at) VALUES (:id, :doc, :art, :rep, :estado, "
        ":aprobado, 'es', :ahora)",
        {
            "id": version_id,
            "doc": f"doc-{version_id}",
            "art": f"art-{version_id}",
            "rep": f"rep-{version_id}",
            "estado": estado,
            "aprobado": AHORA if estado == "accepted" else None,
            "ahora": AHORA,
        },
    )


def _seccion_y_span(
    settings: Settings,
    *,
    version_id: str,
    span_id: str,
    texto: str,
    titulo: str,
    pagina: int,
    ordinal: int,
) -> None:
    seccion = f"sec-{span_id}"
    _ejecutar(
        settings,
        "INSERT INTO document_sections (id, document_version_id, section_type, title, position, "
        "ordinal, page_start, page_end, char_start, char_end) VALUES (:sec, :ver, 'topic', "
        ":titulo, :ordinal, :ordinal, :pagina, :pagina, 0, 100)",
        {
            "sec": seccion,
            "ver": version_id,
            "titulo": titulo,
            "ordinal": ordinal,
            "pagina": pagina,
        },
    )
    _ejecutar(
        settings,
        "INSERT INTO evidence_spans (id, document_version_id, section_id, ordinal, page, "
        "citation_label, quality, index_status, text, normalized_text, created_at) VALUES "
        "(:span, :ver, :sec, :ordinal, :pagina, :etiqueta, 'good', 'indexed', :texto, :texto, "
        ":ahora)",
        {
            "span": span_id,
            "ver": version_id,
            "sec": seccion,
            "ordinal": ordinal,
            "pagina": pagina,
            "etiqueta": f"{titulo}, pág. {pagina}",
            "texto": texto,
            "ahora": AHORA,
        },
    )


def _mapeo(
    settings: Settings,
    *,
    mapping_id: str,
    node_id: str,
    subject_type: str,
    subject_id: str,
    status: str = "accepted",
) -> None:
    _ejecutar(
        settings,
        "INSERT INTO curriculum_mappings (id, curriculum_node_id, subject_type, subject_id, "
        "coverage_type, depth, confidence, status, created_at, approved_at) VALUES "
        "(:id, :nodo, :tipo, :sujeto, 'complete', 1, 0.9, :estado, :ahora, :aprobado)",
        {
            "id": mapping_id,
            "nodo": node_id,
            "tipo": subject_type,
            "sujeto": subject_id,
            "estado": status,
            "ahora": AHORA,
            "aprobado": AHORA if status == "accepted" else None,
        },
    )


def _programa(settings: Settings) -> None:
    """Un bloque con su tema, un tema sin nada y material de cinco clases distintas."""
    _ejecutar(
        settings,
        "INSERT INTO oppositions (id, code, name, active, created_at, updated_at) VALUES "
        "('op-dossier', 'tai-dossier', 'TAI', 0, :ahora, :ahora)",
        {"ahora": AHORA},
    )
    _ejecutar(
        settings,
        "INSERT INTO convocation_versions (id, opposition_id, code, title, official_url, "
        "published_at, status, created_at, updated_at) VALUES ('conv-dossier', 'op-dossier', "
        "'tai-dossier-2026', 'TAI 2026', 'https://boe.es/x', '2026-01-01', 'available', :ahora, "
        ":ahora)",
        {"ahora": AHORA},
    )
    _ejecutar(
        settings,
        "INSERT INTO curriculum_nodes (id, convocation_version_id, parent_id, node_type, "
        "official_code, title, position, path, depth) VALUES "
        "('nodo-bloque-d', 'conv-dossier', NULL, 'block', 'I', 'Bloque I', 1, 'I', 0), "
        "('nodo-tema-d', 'conv-dossier', 'nodo-bloque-d', 'topic', '1', 'Tema 1', 1, 'I.1', 1), "
        "('nodo-vacio-d', 'conv-dossier', NULL, 'topic', '2', 'Tema 2', 2, 'II', 0)",
        {},
    )

    # Doc A: dos tramos, mapeado al tema por su versión de documento.
    _documento(settings, version_id="v-alfa", titulo="Apuntes de Alfa")
    _seccion_y_span(
        settings,
        version_id="v-alfa",
        span_id="span-alfa-1",
        texto=REPETIDO,
        titulo="Tema 1: plazos",
        pagina=3,
        ordinal=1,
    )
    _seccion_y_span(
        settings,
        version_id="v-alfa",
        span_id="span-alfa-2",
        texto="El silencio administrativo se regula en la ley.",
        titulo="Tema 1: silencio",
        pagina=4,
        ordinal=2,
    )
    _mapeo(
        settings,
        mapping_id="map-alfa",
        node_id="nodo-tema-d",
        subject_type="document_version",
        subject_id="v-alfa",
    )

    # Doc B: repite el mismo texto y añade otro tramo. Mapeado al bloque (padre).
    _documento(settings, version_id="v-beta", titulo="Apuntes de Beta")
    _seccion_y_span(
        settings,
        version_id="v-beta",
        span_id="span-beta-1",
        texto=f"  {REPETIDO.upper()}  ",
        titulo="Tema 1: plazos",
        pagina=8,
        ordinal=1,
    )
    _seccion_y_span(
        settings,
        version_id="v-beta",
        span_id="span-beta-2",
        texto="La notificación se practica en el domicilio.",
        titulo="Tema 1: notificaciones",
        pagina=9,
        ordinal=2,
    )
    _mapeo(
        settings,
        mapping_id="map-beta",
        node_id="nodo-bloque-d",
        subject_type="document_version",
        subject_id="v-beta",
    )

    # Doc C: sin publicar. Tiene texto, pero no sostiene una cita todavía.
    _documento(
        settings, version_id="v-borrador", titulo="Borrador sin publicar", estado="candidate"
    )
    _seccion_y_span(
        settings,
        version_id="v-borrador",
        span_id="span-borrador",
        texto="Esto es un borrador.",
        titulo="Borrador",
        pagina=1,
        ordinal=1,
    )
    _mapeo(
        settings,
        mapping_id="map-borrador",
        node_id="nodo-tema-d",
        subject_type="document_version",
        subject_id="v-borrador",
    )

    # Doc D: publicado pero con calidad pobre: tampoco sostiene una cita.
    _documento(settings, version_id="v-pobre", titulo="Escaneo ilegible", calidad="poor")
    _seccion_y_span(
        settings,
        version_id="v-pobre",
        span_id="span-pobre",
        texto="1 1 1 1",
        titulo="Escaneo",
        pagina=1,
        ordinal=1,
    )
    _mapeo(
        settings,
        mapping_id="map-pobre",
        node_id="nodo-tema-d",
        subject_type="document_version",
        subject_id="v-pobre",
    )

    # Doc E: dos secciones y **solo una** mapeada, y el mapeo es de sección, no de documento.
    _documento(settings, version_id="v-gamma", titulo="Temario de Gamma")
    _seccion_y_span(
        settings,
        version_id="v-gamma",
        span_id="span-gamma-dentro",
        texto="El procedimiento empieza con la solicitud.",
        titulo="Sección asignada",
        pagina=5,
        ordinal=1,
    )
    _seccion_y_span(
        settings,
        version_id="v-gamma",
        span_id="span-gamma-fuera",
        texto="El plazo de alegaciones es de diez dias habiles en el otro capitulo.",
        titulo="Sección NO asignada",
        pagina=40,
        ordinal=2,
    )
    _mapeo(
        settings,
        mapping_id="map-gamma",
        node_id="nodo-tema-d",
        subject_type="section",
        subject_id="sec-span-gamma-dentro",
    )

    _ejecutar(settings, "INSERT INTO evidence_fts(evidence_fts) VALUES('rebuild')")


def _dossier(client: TestClient, node_id: str = "nodo-tema-d") -> dict[str, object]:
    respuesta = client.get(f"/api/v1/curriculum-nodes/{node_id}/dossier", headers=ALLOWED_ORIGIN)
    assert respuesta.status_code == 200, respuesta.text
    return respuesta.json()


def test_el_dossier_trae_los_pasajes_de_todas_las_fuentes_con_su_procedencia(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    _programa(seeded_settings)

    cuerpo = _dossier(seeded_client)

    assert cuerpo["title"] == "Tema 1"
    titulos = [fuente["document_title"] for fuente in cuerpo["sources"]]
    # Beta está asignado al **bloque**, no al tema: lo asignado a un bloque no se cuelga de cada uno
    # de sus temas (igual que en la búsqueda por ámbito). Aparece al pedir el bloque, y eso se
    # prueba
    # aparte.
    assert titulos == ["Apuntes de Alfa", "Temario de Gamma"], titulos
    alfa = cuerpo["sources"][0]
    assert alfa["version_status"] == "accepted"
    assert [pasaje["page"] for pasaje in alfa["passages"]] == [3, 4]
    assert alfa["passages"][0]["citation_label"] == "Tema 1: plazos, pág. 3"
    assert all(pasaje["text"] for fuente in cuerpo["sources"] for pasaje in fuente["passages"])
    assert cuerpo["sources_total"] == 2
    assert cuerpo["passages_total"] == 3


def test_el_mismo_texto_se_cita_una_vez_y_se_dice_donde_mas_esta(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    _programa(seeded_settings)

    # Se pide el bloque para que entren las dos fuentes que traen el mismo texto.
    cuerpo = _dossier(seeded_client, "nodo-bloque-d")

    textos = [pasaje["text"] for fuente in cuerpo["sources"] for pasaje in fuente["passages"]]
    assert len(textos) == 4, textos
    assert len({texto.strip().casefold() for texto in textos}) == 4, (
        "el mismo texto no se cita dos veces"
    )
    beta = next(
        fuente for fuente in cuerpo["sources"] if fuente["document_title"] == "Apuntes de Beta"
    )
    assert len(beta["passages"]) == 1, "Beta solo aporta el tramo que no estaba ya"
    assert cuerpo["holes"] and any(
        hueco["code"] == "repetido_en_otra_fuente" for hueco in cuerpo["holes"]
    )


def test_lo_que_no_se_puede_citar_se_declara_como_hueco_con_su_motivo(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    _programa(seeded_settings)

    cuerpo = _dossier(seeded_client)

    titulos = {fuente["document_title"] for fuente in cuerpo["sources"]}
    assert "Borrador sin publicar" not in titulos
    assert "Escaneo ilegible" not in titulos
    motivos = [hueco for hueco in cuerpo["holes"] if hueco["code"] == "no_citable"]
    assert len(motivos) == 2, cuerpo["holes"]
    razones = " ".join(hueco["reason"] or "" for hueco in motivos)
    assert "candidate" in razones, "el hueco dice que la versión no está aceptada"
    assert "poor" in razones, "y que la calidad no sostiene una cita"
    assert sum(hueco["count"] for hueco in motivos) == 2


def test_un_tema_sin_material_lo_dice_con_su_hueco(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    _programa(seeded_settings)

    cuerpo = _dossier(seeded_client, "nodo-vacio-d")

    assert cuerpo["empty"] is True
    assert cuerpo["sources"] == []
    assert cuerpo["passages_total"] == 0
    assert [hueco["code"] for hueco in cuerpo["holes"]] == ["sin_material"]


def test_un_nodo_que_no_existe_responde_404(seeded_client: TestClient) -> None:
    respuesta = seeded_client.get(
        "/api/v1/curriculum-nodes/no-existe/dossier", headers=ALLOWED_ORIGIN
    )

    assert respuesta.status_code == 404


def test_los_tramos_del_tema_son_los_mismos_con_las_dos_consultas(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """La consulta partida en dos devuelve lo mismo: mismos tramos, mismos estados, mismo orden.

    Es la prueba que sostiene el cambio de P0.4 (5 de octubre de 2026). La consulta única tardaba
    **53,6 s** en el tema I.1 de los datos reales, porque el `OR` de cinco condiciones con el que
    unía los mapeos impedía usar los índices. La nueva lee los mapeos por un lado y los tramos por
    otro, y empareja los estados en memoria. Si las dos versiones no coinciden, el cambio no vale:
    el dossier de un tema es lo que se archiva como versión, y un tramo de más o de menos cambia la
    huella de contenido y con ella el historial.
    """
    _programa(seeded_settings)

    engine = build_engine(seeded_settings.data_paths.database)
    try:
        fabrica = build_session_factory(engine)
        repositorio = SqlAlchemyDossierRepository(fabrica)
        for node_id in ("nodo-tema-d", "nodo-bloque"):
            with fabrica() as sesion:
                filas = sesion.execute(text(_TRAMOS_DEL_TEMA), {"node_id": node_id}).all()
            antiguos = [
                (
                    str(fila.evidence_id),
                    tuple(
                        sorted({parte for parte in str(fila.mappings or "").split(",") if parte})
                    ),
                    str(fila.text),
                    int(fila.ordinal),
                )
                for fila in filas
            ]
            nuevos = [
                (hecho.evidence_id, hecho.mappings, hecho.text, hecho.ordinal)
                for hecho in repositorio.passages_for_node(node_id)
            ]
            assert nuevos == antiguos, f"los tramos de {node_id} no coinciden con la consulta única"
    finally:
        engine.dispose()


def test_pedir_el_bloque_trae_lo_de_sus_temas_y_tambien_lo_suyo(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """El ámbito de un bloque es su subárbol, igual que en la cobertura y en la búsqueda.

    Y la otra mitad de la regla: lo asignado al bloque pertenece al bloque, no a cada uno de sus
    temas. Se ve en el mismo par de lecturas: el bloque tiene **una fuente más** que su tema.
    """
    _programa(seeded_settings)

    del_tema = _dossier(seeded_client, "nodo-tema-d")
    del_bloque = _dossier(seeded_client, "nodo-bloque-d")

    assert del_bloque["path"] == "I"
    assert {fuente["document_title"] for fuente in del_bloque["sources"]} == {
        "Apuntes de Alfa",
        "Apuntes de Beta",
        "Temario de Gamma",
    }
    assert del_bloque["passages_total"] == del_tema["passages_total"] + 1
    assert del_bloque["sources_total"] == del_tema["sources_total"] + 1


def test_archivar_guarda_la_historia_y_la_version_anterior_se_lee_como_se_leyo(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    _programa(seeded_settings)

    primera = seeded_client.post(
        "/api/v1/curriculum-nodes/nodo-tema-d/dossier/versions", headers=ALLOWED_ORIGIN
    )
    assert primera.status_code == 201, primera.text
    assert primera.json()["created"] is True
    version_1 = primera.json()["version_id"]

    repetida = seeded_client.post(
        "/api/v1/curriculum-nodes/nodo-tema-d/dossier/versions", headers=ALLOWED_ORIGIN
    )
    assert repetida.json()["created"] is False, "la misma lectura no crea otra versión"
    assert repetida.json()["version_id"] == version_1

    # Entra material nuevo al tema y el dossier cambia: se guarda una versión nueva.
    _documento(seeded_settings, version_id="v-delta", titulo="Apuntes de Delta")
    _seccion_y_span(
        seeded_settings,
        version_id="v-delta",
        span_id="span-delta",
        texto="La caducidad del procedimiento es de seis meses.",
        titulo="Tema 1: caducidad",
        pagina=12,
        ordinal=1,
    )
    _mapeo(
        seeded_settings,
        mapping_id="map-delta",
        node_id="nodo-tema-d",
        subject_type="document_version",
        subject_id="v-delta",
    )

    segunda = seeded_client.post(
        "/api/v1/curriculum-nodes/nodo-tema-d/dossier/versions", headers=ALLOWED_ORIGIN
    )
    assert segunda.json()["created"] is True
    version_2 = segunda.json()["version_id"]
    assert segunda.json()["dossier"]["previous_version_id"] == version_1

    # La versión anterior se lee **como se leyó**: sin el material que llegó después.
    antigua = seeded_client.get(
        f"/api/v1/curriculum-nodes/nodo-tema-d/dossier/versions/{version_1}", headers=ALLOWED_ORIGIN
    )
    assert antigua.status_code == 200, antigua.text
    titulos_antiguos = {fuente["document_title"] for fuente in antigua.json()["sources"]}
    assert "Apuntes de Delta" not in titulos_antiguos
    assert antigua.json()["passages_total"] == primera.json()["dossier"]["passages_total"]

    nueva = seeded_client.get(
        f"/api/v1/curriculum-nodes/nodo-tema-d/dossier/versions/{version_2}", headers=ALLOWED_ORIGIN
    )
    assert {fuente["document_title"] for fuente in nueva.json()["sources"]} == (
        titulos_antiguos | {"Apuntes de Delta"}
    )

    listado = seeded_client.get(
        "/api/v1/curriculum-nodes/nodo-tema-d/dossier/versions", headers=ALLOWED_ORIGIN
    )
    assert listado.status_code == 200
    assert [version["id"] for version in listado.json()] == [version_2, version_1]
    assert listado.json()[1]["passages_count"] == antigua.json()["passages_total"]


def test_una_version_de_otro_tema_no_se_puede_leer_desde_este(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    _programa(seeded_settings)
    creada = seeded_client.post(
        "/api/v1/curriculum-nodes/nodo-tema-d/dossier/versions", headers=ALLOWED_ORIGIN
    ).json()["version_id"]

    ajena = seeded_client.get(
        f"/api/v1/curriculum-nodes/nodo-vacio-d/dossier/versions/{creada}", headers=ALLOWED_ORIGIN
    )

    assert ajena.status_code == 404, "una versión de otro tema no se lee por esta ruta"


def test_el_mapeo_de_una_seccion_no_arrastra_al_documento_entero(
    seeded_settings: Settings, seeded_client: TestClient
) -> None:
    """Y la búsqueda por ámbito dice lo mismo que el dossier: una sola definición de «pertenece».

    El documento de Gamma tiene dos secciones y solo la primera está asignada al tema. Si el ámbito
    tratara el mapeo de sección como un mapeo del documento, el tramo de la sección **no** asignada
    entraría en el tema por la puerta de atrás: aparecería en el dossier y en las respuestas del
    buscador como si alguien lo hubiera asignado.
    """
    _programa(seeded_settings)

    cuerpo = _dossier(seeded_client)
    gamma = next(
        fuente for fuente in cuerpo["sources"] if fuente["document_title"] == "Temario de Gamma"
    )
    assert [pasaje["evidence_id"] for pasaje in gamma["passages"]] == ["span-gamma-dentro"]

    engine = build_engine(seeded_settings.data_paths.database)
    try:
        servicio = SearchService(
            search=SqlAlchemySearchRepository(build_session_factory(engine)),
            clock=None,  # type: ignore[arg-type]  # buscar no usa el reloj: solo preguntar lo usa
        )
        encontrado = servicio.search_only(
            SearchRequest(
                query="diez dias habiles",
                filters=SearchFilters(limit=10, curriculum_node_ids=("nodo-tema-d",)),
            )
        )
    finally:
        engine.dispose()

    assert "span-gamma-fuera" not in encontrado.ids, (
        "la sección no asignada no pertenece al tema: ni en el dossier ni en la búsqueda"
    )
