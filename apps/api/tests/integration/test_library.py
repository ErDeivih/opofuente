"""Pruebas de integración de la biblioteca (S05) por el camino real.

El material se guarda como lo guarda el pipeline: representación con su texto en el almacén y
su fila en la base. Nada de filas a mano simulando al extractor: si la forma del dato no es la
real, la prueba tiene que fallar.

Lo que se comprueba es la aceptación del slice: una fuente compartida se guarda **una vez** y
a dos programas con dos mapeos; la versión antigua **no se pierde** al sustituirla; los derechos sin
revisar permanecen **restringidos**; y las citas apuntan a **su sección y su página**.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import text

from opofuente.config import Settings
from opofuente.domain.extraction import (
    ExtractedSection,
    ExtractionResult,
    ExtractorRef,
    Quality,
    RepresentationKind,
    RepresentationStatus,
    SectionType,
)
from opofuente.infrastructure.db import build_engine, build_session_factory
from opofuente.infrastructure.document_repository import SqlAlchemyDocumentRepository
from opofuente.infrastructure.extraction_repository import SqlAlchemyExtractionRepository
from opofuente.infrastructure.migrations import run_migrations
from opofuente.infrastructure.representation_store import RepresentationStore

AHORA = datetime(2026, 9, 16, 12, 0, tzinfo=UTC)
TEXTO = (
    "Tema 1. La Constitucion espanola.\n"
    "El plazo para solicitar la cita previa es de diez dias habiles.\n"
    "Tema 2. Documentacion clinica.\n"
)
SECCIONES = (
    ExtractedSection(
        section_type=SectionType.TITLE,
        position=1,
        char_start=0,
        char_end=33,
        title="Tema 1. La Constitucion espanola.",
        label="Tema 1",
        page_start=3,
        page_end=3,
    ),
    ExtractedSection(
        section_type=SectionType.PARAGRAPH,
        position=2,
        char_start=34,
        char_end=97,
        label="Plazos",
        page_start=3,
        page_end=4,
    ),
)


#: Dos redacciones del mismo temario, para comparar versiones de verdad:
#: el título sigue igual, el plazo cambia y aparece un tema nuevo.
_TEXTO_V1 = (
    "Tema 1. La Constitucion espanola.\n"
    "El plazo para solicitar la cita previa es de diez dias habiles.\n"
)
_TEXTO_V2 = (
    "Tema 1. La Constitucion espanola.\n"
    "El plazo para solicitar la cita previa es de veinte dias habiles.\n"
    "Tema 3. Nuevo tema anadido.\n"
)
_SECCIONES_V1 = (
    ExtractedSection(
        section_type=SectionType.TITLE,
        position=1,
        char_start=0,
        char_end=33,
        title="Tema 1. La Constitucion espanola.",
        label="Tema 1",
        page_start=1,
        page_end=1,
    ),
    ExtractedSection(
        section_type=SectionType.PARAGRAPH,
        position=2,
        char_start=34,
        char_end=98,
        label="Plazos",
        page_start=1,
        page_end=1,
    ),
)
_SECCIONES_V2 = (
    _SECCIONES_V1[0],
    ExtractedSection(
        section_type=SectionType.PARAGRAPH,
        position=2,
        char_start=34,
        char_end=100,
        label="Plazos",
        page_start=1,
        page_end=1,
    ),
    ExtractedSection(
        section_type=SectionType.TITLE,
        position=3,
        char_start=100,
        char_end=127,
        title="Tema 3. Nuevo tema anadido.",
        label="Tema 3",
        page_start=1,
        page_end=1,
    ),
)


def _resultado(
    calidad: Quality = Quality.GOOD,
    *,
    texto: str = TEXTO,
    secciones: tuple[ExtractedSection, ...] = SECCIONES,
) -> ExtractionResult:
    return ExtractionResult(
        kind=RepresentationKind.NATIVE_TEXT,
        status=RepresentationStatus.EXTRACTED,
        text=texto,
        extractor=ExtractorRef("extractor-de-prueba", "1"),
        quality=calidad,
        sections=secciones,
    )


def _biblioteca(
    tmp_path: Path,
) -> tuple[SqlAlchemyDocumentRepository, SqlAlchemyExtractionRepository, Settings]:
    settings = Settings(data_dir=tmp_path / "datos", _env_file=None)
    settings.data_paths.ensure_directories()
    run_migrations(settings, revision="head")
    engine = build_engine(settings.data_paths.database)
    sesiones = build_session_factory(engine)
    biblioteca = SqlAlchemyDocumentRepository(sesiones, RepresentationStore(settings.data_paths))
    extraccion = SqlAlchemyExtractionRepository(sesiones)
    return biblioteca, extraccion, settings


def _artefacto(settings: Settings, artifact_id: str, sha: str) -> None:
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.begin() as conexion:
            conexion.execute(
                text(
                    "INSERT INTO source_artifacts (id, sha256, size_bytes, media_type, "
                    "storage_key, first_seen_at) VALUES "
                    "(:id, :sha, 100, 'text/plain', 'sha256/aa', :ahora)"
                ),
                {"id": artifact_id, "sha": sha, "ahora": AHORA},
            )
    finally:
        engine.dispose()


def _guardar_representacion(
    extraccion: SqlAlchemyExtractionRepository,
    settings: Settings,
    *,
    artifact_id: str,
    representacion_id: str,
    calidad: Quality = Quality.GOOD,
    resultado: ExtractionResult | None = None,
) -> str:
    resultado = resultado if resultado is not None else _resultado(calidad)
    clave = RepresentationStore(settings.data_paths).save(representacion_id, resultado)
    extraccion.save(
        result=resultado,
        artifact_id=artifact_id,
        representation_id=representacion_id,
        text_storage_key=clave,
        now=AHORA,
    )
    return clave


def _derechos(settings: Settings, code: str, review: str) -> None:
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.begin() as conexion:
            conexion.execute(
                text(
                    "INSERT INTO rights_statuses (id, code, review_status, sharing, created_at, "
                    "updated_at) VALUES (:id, :code, :review, 0, :ahora, :ahora)"
                ),
                {"id": f"rights-{code}", "code": code, "review": review, "ahora": AHORA},
            )
    finally:
        engine.dispose()


# --- promoción -------------------------------------------------------------------------------


def test_promocionar_lleva_las_secciones_y_las_evidencias_del_texto_real(tmp_path: Path) -> None:
    """La cita sale del texto de la representación recortado con los offsets de cada sección."""
    biblioteca, extraccion, settings = _biblioteca(tmp_path)
    _artefacto(settings, "art-1", "a" * 64)
    _guardar_representacion(extraccion, settings, artifact_id="art-1", representacion_id="rep-1")

    resultado = biblioteca.promote_artifact(
        "art-1",
        now=AHORA,
        title="Temario de prueba",
        document_type="curriculum",
        version_label="v1",
    )

    assert resultado.applied is True
    assert resultado.created_document is True
    assert resultado.created_version is True
    secciones = biblioteca.list_sections(resultado.version_id or "")
    assert [seccion.section_type for seccion in secciones] == ["title", "technical"]
    assert secciones[0].title == "Tema 1. La Constitucion espanola."
    assert secciones[0].page_start == 3

    evidencias = biblioteca.list_evidence(resultado.version_id or "")
    assert len(evidencias) == 2
    assert "diez dias habiles" in evidencias[1].text
    assert evidencias[1].page == 3
    assert evidencias[1].citation_label == "Plazos, pág. 3"
    assert evidencias[1].section_id == secciones[1].id


def test_promocionar_dos_veces_no_crea_dos_documentos(tmp_path: Path) -> None:
    """Los mismos bytes son la misma obra: promocionar de nuevo devuelve lo que ya había."""
    biblioteca, extraccion, settings = _biblioteca(tmp_path)
    _artefacto(settings, "art-1", "a" * 64)
    _guardar_representacion(extraccion, settings, artifact_id="art-1", representacion_id="rep-1")
    primera = biblioteca.promote_artifact(
        "art-1", now=AHORA, title="Temario", document_type="curriculum"
    )

    segunda = biblioteca.promote_artifact("art-1", now=AHORA, title="Otro titulo distinto")

    assert segunda.document_id == primera.document_id
    assert segunda.version_id == primera.version_id
    assert segunda.created_document is False
    assert biblioteca.list_documents().total == 1


def test_sin_titulo_no_se_promociona_y_se_dice_por_que(tmp_path: Path) -> None:
    """Un documento sin título no se inventa: se devuelve el motivo y no se escribe nada."""
    biblioteca, extraccion, settings = _biblioteca(tmp_path)
    _artefacto(settings, "art-1", "a" * 64)
    _guardar_representacion(extraccion, settings, artifact_id="art-1", representacion_id="rep-1")

    resultado = biblioteca.promote_artifact("art-1", now=AHORA, title="   ")

    assert resultado.applied is False
    assert resultado.reason is not None
    assert biblioteca.list_documents().total == 0


# --- versiones -------------------------------------------------------------------------------


def test_una_fuente_compartida_es_un_documento_con_dos_mapeos(tmp_path: Path) -> None:
    """El mismo material asignado a dos programas: un documento, una versión, dos mapeos."""
    biblioteca, extraccion, settings = _biblioteca(tmp_path)
    _artefacto(settings, "art-1", "a" * 64)
    _guardar_representacion(extraccion, settings, artifact_id="art-1", representacion_id="rep-1")
    promocion = biblioteca.promote_artifact(
        "art-1", now=AHORA, title="Temario compartido", document_type="curriculum"
    )

    engine = build_engine(settings.data_paths.database)
    try:
        with engine.begin() as conexion:
            conexion.execute(
                text(
                    "INSERT INTO oppositions (id, code, name, active, created_at, updated_at) "
                    "VALUES ('op-tai', 'tai', 'TAI', 1, :ahora, :ahora), "
                    "('op-gc', 'gc', 'Guardia Civil', 0, :ahora, :ahora)"
                ),
                {"ahora": AHORA},
            )
            for indice, oposicion in enumerate(("op-tai", "op-gc"), start=1):
                conexion.execute(
                    text(
                        "INSERT INTO convocation_versions (id, opposition_id, code, title, "
                        "official_url, published_at, status, created_at, updated_at) VALUES "
                        "(:id, :op, :code, 'Convocatoria', 'https://example.invalid/c', "
                        "'2026-01-15', 'active', :ahora, :ahora)"
                    ),
                    {
                        "id": f"conv-{indice}",
                        "op": oposicion,
                        "code": f"conv-{indice}",
                        "ahora": AHORA,
                    },
                )
                conexion.execute(
                    text(
                        "INSERT INTO curriculum_nodes (id, convocation_version_id, node_type, "
                        "official_code, title, position, path, depth) VALUES "
                        "(:id, :conv, 'topic', :code, 'Tema 1', 1, :path, 0)"
                    ),
                    {
                        "id": f"node-{indice}",
                        "conv": f"conv-{indice}",
                        "code": str(indice),
                        "path": f"tema-{indice}",
                    },
                )
                conexion.execute(
                    text(
                        "INSERT INTO curriculum_mappings (id, curriculum_node_id, subject_type, "
                        "subject_id, coverage_type, depth, confidence, status, created_at, "
                        "approved_at) VALUES (:id, :node, 'document_version', :version, "
                        "'partial', 0, 0.9, 'accepted', :ahora, :ahora)"
                    ),
                    {
                        "id": f"map-{indice}",
                        "node": f"node-{indice}",
                        "version": promocion.version_id,
                        "ahora": AHORA,
                    },
                )
    finally:
        engine.dispose()

    detalle = biblioteca.get_document(promocion.document_id or "")
    assert detalle is not None
    assert detalle.document.version_count == 1, "una sola versión para el mismo material"
    # El mismo material asignado a dos programas: **dos** mapeos sobre una sola versión.
    assert detalle.document.mapping_count == 2
    assert detalle.document.active_version is not None
    assert detalle.document.active_version.status == "candidate"
    assert detalle.document.owner_scope == "private_user", "promocionar no hace público nada"


def test_sustituir_no_borra_la_version_antigua(tmp_path: Path) -> None:
    """`supersedes` confirmado: la nueva manda, la antigua queda y conserva su contenido."""
    biblioteca, extraccion, settings = _biblioteca(tmp_path)
    _artefacto(settings, "art-1", "a" * 64)
    _artefacto(settings, "art-2", "b" * 64)
    _guardar_representacion(extraccion, settings, artifact_id="art-1", representacion_id="rep-1")
    _guardar_representacion(extraccion, settings, artifact_id="art-2", representacion_id="rep-2")
    primera = biblioteca.promote_artifact(
        "art-1", now=AHORA, title="Temario", document_type="curriculum"
    )
    aceptada = biblioteca.accept_version(primera.version_id or "", now=AHORA)
    assert aceptada.applied is True

    segunda = biblioteca.promote_artifact(
        "art-2",
        now=AHORA,
        document_id=primera.document_id,
        version_label="v2",
    )
    assert segunda.created_document is False
    assert segunda.created_version is True

    sustitucion = biblioteca.mark_supersedes(
        segunda.version_id or "", superseded_id=primera.version_id or "", now=AHORA
    )

    assert sustitucion.applied is True
    detalle = biblioteca.get_document(primera.document_id or "")
    assert detalle is not None
    estados = {version.id: version.status for version in detalle.versions}
    assert estados[primera.version_id] == "superseded"
    assert estados[segunda.version_id] == "candidate"
    versiones_antiguas = [
        version for version in detalle.versions if version.id == primera.version_id
    ]
    assert versiones_antiguas[0].evidence_count == 2, "la versión antigua conserva su contenido"
    assert detalle.document.active_version is not None
    assert detalle.document.active_version.id == segunda.version_id


def test_una_version_retirada_no_se_puede_aceptar(tmp_path: Path) -> None:
    biblioteca, extraccion, settings = _biblioteca(tmp_path)
    _artefacto(settings, "art-1", "a" * 64)
    _guardar_representacion(extraccion, settings, artifact_id="art-1", representacion_id="rep-1")
    promocion = biblioteca.promote_artifact(
        "art-1", now=AHORA, title="Temario", document_type="curriculum"
    )

    engine = build_engine(settings.data_paths.database)
    try:
        with engine.begin() as conexion:
            conexion.execute(
                text("UPDATE document_versions SET status = 'withdrawn' WHERE id = :id"),
                {"id": promocion.version_id},
            )
    finally:
        engine.dispose()

    resultado = biblioteca.accept_version(promocion.version_id or "", now=AHORA)

    assert resultado.applied is False
    assert resultado.reason is not None


# --- derechos y colecciones --------------------------------------------------------------------


def test_los_derechos_sin_revisar_permanecen_restringidos(tmp_path: Path) -> None:
    """09_SECURITY §8: sin revisar no hay permiso, y eso tiene que verse en lo que se sirve."""
    biblioteca, extraccion, settings = _biblioteca(tmp_path)
    _derechos(settings, "unknown", "unknown")
    _artefacto(settings, "art-1", "a" * 64)
    _guardar_representacion(extraccion, settings, artifact_id="art-1", representacion_id="rep-1")

    promocion = biblioteca.promote_artifact(
        "art-1", now=AHORA, title="Temario", document_type="curriculum", rights_code="unknown"
    )

    detalle = biblioteca.get_document(promocion.document_id or "")
    assert detalle is not None
    derechos = detalle.document.active_version.rights if detalle.document.active_version else None
    assert derechos is not None
    assert derechos.review_status == "unknown"
    assert derechos.is_restricted is True
    assert derechos.sharing is False


def test_una_representacion_pobre_se_promociona_con_su_calidad(tmp_path: Path) -> None:
    """Una fuente pobre se promociona diciendo que lo es: la cobertura lo tendrá en cuenta."""
    biblioteca, extraccion, settings = _biblioteca(tmp_path)
    _artefacto(settings, "art-1", "a" * 64)
    _guardar_representacion(
        extraccion, settings, artifact_id="art-1", representacion_id="rep-1", calidad=Quality.POOR
    )

    promocion = biblioteca.promote_artifact(
        "art-1", now=AHORA, title="Temario", document_type="curriculum"
    )

    evidencias = biblioteca.list_evidence(promocion.version_id or "")
    assert evidencias
    assert {evidencia.quality for evidencia in evidencias} == {"poor"}


def test_una_coleccion_agrupa_sin_duplicar(tmp_path: Path) -> None:
    biblioteca, extraccion, settings = _biblioteca(tmp_path)
    _artefacto(settings, "art-1", "a" * 64)
    _guardar_representacion(extraccion, settings, artifact_id="art-1", representacion_id="rep-1")
    promocion = biblioteca.promote_artifact(
        "art-1", now=AHORA, title="Temario", document_type="curriculum"
    )
    coleccion = biblioteca.create_collection("Oposicion 2026", description=None, now=AHORA)

    primera = biblioteca.add_to_collection(
        coleccion.id,
        subject_type="document_version",
        subject_id=promocion.version_id or "",
        now=AHORA,
    )
    segunda = biblioteca.add_to_collection(
        coleccion.id,
        subject_type="document_version",
        subject_id=promocion.version_id or "",
        now=AHORA,
    )

    assert primera is not None and primera.item_count == 1
    assert segunda is not None and segunda.item_count == 1, "añadir dos veces no duplica el ítem"
    assert biblioteca.list_collections()[0].name == "Oposicion 2026"


# --- cobertura sobre documentos ------------------------------------------------------------------


def _programa(biblioteca, settings, *, version_id: str, estado: str = "accepted") -> str:
    """Crea oposición, convocatoria, nodo y un mapeo del documento a ese nodo. Devuelve el nodo."""
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.begin() as conexion:
            conexion.execute(
                text(
                    "INSERT INTO oppositions (id, code, name, active, created_at, updated_at) "
                    "VALUES ('op-cyl', 'cyl', 'Castilla y Leon', 1, :ahora, :ahora)"
                ),
                {"ahora": AHORA},
            )
            conexion.execute(
                text(
                    "INSERT INTO convocation_versions (id, opposition_id, code, title, "
                    "official_url, published_at, status, created_at, updated_at) VALUES "
                    "('conv-cyl', 'op-cyl', "
                    "'cyl-2026', 'Convocatoria', 'https://example.invalid/c', '2026-01-15', "
                    "'active', :ahora, :ahora)"
                ),
                {"ahora": AHORA},
            )
            conexion.execute(
                text(
                    "INSERT INTO curriculum_nodes (id, convocation_version_id, node_type, "
                    "official_code, title, position, path, depth) VALUES ('node-1', 'conv-cyl', "
                    "'topic', '1', 'Tema 1', 1, 'tema-1', 0)"
                )
            )
            conexion.execute(
                text(
                    "INSERT INTO curriculum_mappings (id, curriculum_node_id, subject_type, "
                    "subject_id, coverage_type, depth, confidence, status, created_at, "
                    "approved_at) "
                    "VALUES ('map-1', 'node-1', 'document_version', :version, 'partial', 0, 0.9, "
                    "'accepted', :ahora, :ahora)"
                ),
                {"version": version_id, "ahora": AHORA},
            )
    finally:
        engine.dispose()
    return "node-1"


def _cobertura(settings, sesiones):
    from opofuente.infrastructure.document_coverage import document_coverage

    return document_coverage(sesiones, convocation_code="cyl-2026")


def test_una_version_candidata_no_sostiene_cobertura_aceptada(tmp_path: Path) -> None:
    """Es la mitad que faltaba: un mapeo aceptado de una versión **candidata** no es cobertura."""
    from opofuente.infrastructure.db import build_session_factory

    biblioteca, extraccion, settings = _biblioteca(tmp_path)
    _artefacto(settings, "art-1", "a" * 64)
    _guardar_representacion(extraccion, settings, artifact_id="art-1", representacion_id="rep-1")
    promocion = biblioteca.promote_artifact(
        "art-1", now=AHORA, title="Temario", document_type="curriculum"
    )
    _programa(biblioteca, settings, version_id=promocion.version_id or "")

    engine = build_engine(settings.data_paths.database)
    try:
        cobertura = _cobertura(settings, build_session_factory(engine))
    finally:
        engine.dispose()

    assert cobertura.accepted_total == 0, "una candidata no es cobertura aceptada"
    assert cobertura.provisional_total == 1, "pero no se esconde: queda como provisional"
    assert cobertura.classified_subjects == 1
    assert cobertura.materials_total == 1


def test_una_version_aceptada_y_buena_si_es_cobertura_aceptada(tmp_path: Path) -> None:
    from opofuente.infrastructure.db import build_session_factory

    biblioteca, extraccion, settings = _biblioteca(tmp_path)
    _artefacto(settings, "art-1", "a" * 64)
    _guardar_representacion(extraccion, settings, artifact_id="art-1", representacion_id="rep-1")
    promocion = biblioteca.promote_artifact(
        "art-1", now=AHORA, title="Temario", document_type="curriculum"
    )
    biblioteca.accept_version(promocion.version_id or "", now=AHORA)
    _programa(biblioteca, settings, version_id=promocion.version_id or "")

    engine = build_engine(settings.data_paths.database)
    try:
        cobertura = _cobertura(settings, build_session_factory(engine))
    finally:
        engine.dispose()

    assert cobertura.accepted_total == 1
    assert cobertura.provisional_total == 0, "lo aceptado no se cuenta además como provisional"
    nodo = cobertura.nodes[0]
    assert nodo.accepted == 1
    assert nodo.materials == ("Temario",)


def test_una_version_aceptada_con_texto_pobre_no_es_cobertura_aceptada(tmp_path: Path) -> None:
    """La calidad manda: una fuente pobre se promociona, pero no confirma cobertura."""
    from opofuente.infrastructure.db import build_session_factory

    biblioteca, extraccion, settings = _biblioteca(tmp_path)
    _artefacto(settings, "art-1", "a" * 64)
    _guardar_representacion(
        extraccion, settings, artifact_id="art-1", representacion_id="rep-1", calidad=Quality.POOR
    )
    promocion = biblioteca.promote_artifact(
        "art-1", now=AHORA, title="Temario", document_type="curriculum"
    )
    biblioteca.accept_version(promocion.version_id or "", now=AHORA)
    _programa(biblioteca, settings, version_id=promocion.version_id or "")

    engine = build_engine(settings.data_paths.database)
    try:
        cobertura = _cobertura(settings, build_session_factory(engine))
    finally:
        engine.dispose()

    assert cobertura.accepted_total == 0
    assert cobertura.provisional_total == 1


# --- diff entre versiones ---------------------------------------------------------------------


def test_el_diff_dice_que_seccion_cambio_y_cual_es_nueva(tmp_path: Path) -> None:
    """Dos versiones del mismo documento: lo que cambió, lo que se añadió y lo que sigue igual.

    El diff compara el **texto real** de cada sección (leído del almacén por sus offsets) y empareja
    por etiqueta: el título se reconoce en las dos versiones, el tramo sin título se empareja por su
    posición (`sección 2`) y la sección nueva se informa como añadida.
    """
    biblioteca, extraccion, settings = _biblioteca(tmp_path)
    _artefacto(settings, "art-1", "a" * 64)
    _artefacto(settings, "art-2", "b" * 64)
    _guardar_representacion(
        extraccion,
        settings,
        artifact_id="art-1",
        representacion_id="rep-1",
        resultado=_resultado(texto=_TEXTO_V1, secciones=_SECCIONES_V1),
    )
    _guardar_representacion(
        extraccion,
        settings,
        artifact_id="art-2",
        representacion_id="rep-2",
        resultado=_resultado(texto=_TEXTO_V2, secciones=_SECCIONES_V2),
    )

    primera = biblioteca.promote_artifact(
        "art-1", now=AHORA, title="Temario versionado", document_type="curriculum"
    )
    segunda = biblioteca.promote_artifact(
        "art-2",
        now=AHORA,
        document_id=primera.document_id,
        title="Temario versionado",
        document_type="curriculum",
    )

    comparacion = biblioteca.document_diff(
        primera.document_id or "",
        from_version_id=primera.version_id or "",
        to_version_id=segunda.version_id or "",
    )

    assert comparacion is not None
    por_etiqueta = {seccion.label: seccion for seccion in comparacion.sections}
    assert por_etiqueta["Tema 1. La Constitucion espanola."].kind == "unchanged"
    assert por_etiqueta["sección 2"].kind == "changed"
    assert "veinte" in (por_etiqueta["sección 2"].right or "")
    assert "diez" in (por_etiqueta["sección 2"].left or "")
    assert por_etiqueta["Tema 3. Nuevo tema anadido."].kind == "added"
    assert comparacion.added == 1
    assert comparacion.changed == 1
    assert comparacion.removed == 0
    assert comparacion.unchanged == 1
    assert comparacion.has_changes is True

    # Volver a promocionar el mismo artefacto en el mismo documento es idempotente: no crea otra
    # versión, y compararla consigo misma da todo igual.
    repetida = biblioteca.promote_artifact(
        "art-1",
        now=AHORA,
        document_id=primera.document_id,
        title="Temario versionado",
        document_type="curriculum",
    )
    assert repetida.version_id == primera.version_id
    consigo_misma = biblioteca.document_diff(
        primera.document_id or "",
        from_version_id=primera.version_id or "",
        to_version_id=repetida.version_id or "",
    )
    assert consigo_misma is not None
    assert consigo_misma.changed == 0
    assert consigo_misma.unchanged == 2

    # Una versión de **otro** documento no se compara: el diff es del mismo documento, o no es.
    _artefacto(settings, "art-3", "c" * 64)
    _guardar_representacion(
        extraccion,
        settings,
        artifact_id="art-3",
        representacion_id="rep-3",
        resultado=_resultado(texto=_TEXTO_V1, secciones=_SECCIONES_V1),
    )
    otro = biblioteca.promote_artifact(
        "art-3", now=AHORA, title="Otro temario", document_type="curriculum"
    )
    assert otro.document_id != primera.document_id
    assert (
        biblioteca.document_diff(
            primera.document_id or "",
            from_version_id=primera.version_id or "",
            to_version_id=otro.version_id or "",
        )
        is None
    )
    assert (
        biblioteca.document_diff(
            primera.document_id or "",
            from_version_id="no-existe",
            to_version_id=segunda.version_id or "",
        )
        is None
    )
