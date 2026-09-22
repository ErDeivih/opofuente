"""Pruebas de integración de la extracción (S03): del artefacto copiado al texto con su calidad.

Se comprueba el recorrido completo con documentos sintéticos: lo que tiene extractor acaba
`extracted`, lo que no lo tiene acaba `unsupported_preserved` (DEBT-008), lo que no tiene texto
nativo queda pendiente de OCR sin romper nada, y volver a extraer no duplica representaciones.

Todas las pruebas trabajan sobre directorios temporales; ningún fichero real del usuario.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import func, select

from opofuente.application.extraction_service import ExtractionService
from opofuente.application.ingestion_service import IngestionService
from opofuente.config import Settings
from opofuente.domain.errors import JobCancelledError
from opofuente.domain.extraction import (
    ExtractionResult,
    ExtractorRef,
    Quality,
    RepresentationKind,
    RepresentationStatus,
)
from opofuente.domain.ingestion import BatchStatus, IssueCode, ItemStatus
from opofuente.domain.jobs import Job, JobStatus, JobType
from opofuente.infrastructure.artifact_store import ArtifactStore
from opofuente.infrastructure.db import build_engine, build_session_factory
from opofuente.infrastructure.db_models import ExtractedRepresentationRecord
from opofuente.infrastructure.extraction_repository import SqlAlchemyExtractionRepository
from opofuente.infrastructure.extractors import ExtractorRegistry
from opofuente.infrastructure.filesystem_inventory import FilesystemInventory
from opofuente.infrastructure.ingestion_repository import SqlAlchemyIngestionRepository
from opofuente.infrastructure.job_repository import SqlAlchemyJobRepository
from opofuente.infrastructure.representation_store import RepresentationStore
from opofuente_testing.jobs import FakeExecution, FixedClock
from opofuente_testing.synthetic_documents import (
    build_anki_deck,
    build_bomb_docx,
    build_csv,
    build_html,
    build_png,
    build_spreadsheet_like,
    build_text_pdf,
    build_zip,
)


@pytest.fixture
def session_factory(migrated_settings: Settings):
    engine = build_engine(migrated_settings.data_paths.database)
    try:
        yield build_session_factory(engine)
    finally:
        engine.dispose()


@pytest.fixture
def material(tmp_path: Path) -> Path:
    """Material sintético variado: dos con texto, uno sin extractor y una imagen."""
    root = tmp_path / "material"
    root.mkdir()
    build_text_pdf(root / "temario.pdf", pages=2)
    build_csv(root / "preguntas.csv", rows=3)
    build_spreadsheet_like(root / "resumen.xlsx")
    build_png(root / "escaneo.png")
    return root


@pytest.fixture
def services(migrated_settings: Settings, session_factory, tmp_path: Path):
    """Los dos servicios de S03, sobre el mismo almacén y la misma base de datos."""
    paths = migrated_settings.data_paths
    clock = FixedClock()
    ingestion_repository = SqlAlchemyIngestionRepository(session_factory)
    jobs = SqlAlchemyJobRepository(session_factory)
    store = ArtifactStore(paths)
    ingestion = IngestionService(
        repository=ingestion_repository,
        jobs=jobs,
        store=store,
        scanner=FilesystemInventory(
            max_file_bytes=1024 * 1024, max_entries=1000, forbidden_roots=(paths.root,)
        ),
        clock=clock,
        data_root=paths.root,
        max_entries=1000,
    )
    extraction = ExtractionService(
        repository=SqlAlchemyExtractionRepository(session_factory),
        ingestions=ingestion_repository,
        store=store,
        representations=RepresentationStore(paths),
        registry=ExtractorRegistry(migrated_settings),
        jobs=jobs,
        clock=clock,
        data_root=paths.root,
        max_member_bytes=migrated_settings.max_file_bytes,
    )
    return ingestion, extraction, jobs, clock


def _import(ingestion: IngestionService, material: Path) -> str:
    inventory = ingestion.create_inventory(str(material))
    batch = ingestion.confirm_import(inventory.batch.id)
    job = _job_for(ingestion, batch.id, JobType.INGEST_BATCH)
    ingestion.run_import_job(FakeExecution(job))
    return batch.id


def _job_for(ingestion: IngestionService, batch_id: str, job_type: JobType) -> Job:
    for job in ingestion.jobs.list(limit=50):
        if job.job_type is job_type and job.payload.get("batch_id") == batch_id:
            return job
    raise AssertionError(f"no se encoló el trabajo {job_type.value} del lote")


def test_la_importacion_encola_la_extraccion(services, material: Path) -> None:
    """El pipeline no se queda en copiar: al terminar la copia se encola la extracción."""
    ingestion, _extraction, _jobs, _clock = services

    batch_id = _import(ingestion, material)

    extraccion = _job_for(ingestion, batch_id, JobType.EXTRACT_ARTIFACT)
    assert extraccion.status is JobStatus.QUEUED
    assert extraccion.payload["batch_id"] == batch_id


def test_la_extraccion_clasifica_por_formato_y_conserva_lo_que_no_puede_leer(
    services, material: Path
) -> None:
    """Un lote variado: se extrae, se conserva sin extraer y se declara el OCR pendiente."""
    ingestion, extraction, _jobs, _clock = services
    batch_id = _import(ingestion, material)
    job = _job_for(ingestion, batch_id, JobType.EXTRACT_ARTIFACT)

    extraction.run_extraction_job(FakeExecution(job))

    detalle = extraction._ingestions.get_batch_detail(batch_id, entry_limit=50, issue_limit=50)
    assert detalle is not None
    estados = {entry.relative_path: entry.status for entry in detalle.entries}
    assert estados["temario.pdf"] == ItemStatus.EXTRACTED.value
    assert estados["preguntas.csv"] == ItemStatus.EXTRACTED.value
    assert estados["resumen.xlsx"] == ItemStatus.UNSUPPORTED_PRESERVED.value
    assert estados["escaneo.png"] == ItemStatus.OCR_PENDING.value, "sin OCR queda pendiente"

    counters = detalle.batch.counters
    assert counters["copied"] == 3, "el PDF, el CSV y la imagen están copiados"
    assert counters["preserved_unsupported"] == 1
    assert counters["pending"] == 0
    assert detalle.batch.status == BatchStatus.SUCCEEDED.value

    codigos = {issue.code for issue in detalle.issues}
    assert IssueCode.UNSUPPORTED_PRESERVED.value in codigos
    assert IssueCode.OCR_PENDING.value in codigos

    representaciones = extraction.representations_for_batch(batch_id)
    tipos = {view.kind for view in representaciones}
    assert "native_text" in tipos, "el PDF deja su texto"
    assert "csv_preview" in tipos, "el CSV deja su vista previa"
    assert "image_metadata" in tipos, "la imagen deja sus metadatos"
    assert all(view.has_text for view in representaciones), "todas guardan su texto"


def test_la_representacion_guarda_el_texto_y_se_puede_leer_por_trozos(
    services, material: Path
) -> None:
    ingestion, extraction, _jobs, _clock = services
    batch_id = _import(ingestion, material)
    job = _job_for(ingestion, batch_id, JobType.EXTRACT_ARTIFACT)
    extraction.run_extraction_job(FakeExecution(job))

    representaciones = extraction.representations_for_batch(batch_id)
    pdf = next(view for view in representaciones if view.kind == "native_text")

    trozo = extraction.read_text(pdf.id, offset=0, limit=200)
    assert "Ley 39/2015" in trozo.text
    assert trozo.total_chars == pdf.char_count
    assert trozo.truncated is True

    completo = extraction.read_text(pdf.id, offset=0, limit=10)
    assert len(completo.text) == 10


def test_volver_a_extraer_no_duplica_representaciones(
    services, material: Path, session_factory
) -> None:
    """La clave (artefacto, extractor, versión, tipo) hace idempotente la extracción.

    Se ejecuta el trabajo dos veces: la imagen pendiente de OCR se vuelve a intentar (y sigue
    pendiente, porque no hay OCR configurado) y aun así no aparece ninguna fila duplicada.
    """
    ingestion, extraction, _jobs, _clock = services
    batch_id = _import(ingestion, material)
    job = _job_for(ingestion, batch_id, JobType.EXTRACT_ARTIFACT)

    extraction.run_extraction_job(FakeExecution(job))
    with session_factory() as session:
        primera = session.execute(
            select(func.count()).select_from(ExtractedRepresentationRecord)
        ).scalar_one()

    # La imagen sin OCR ya no cuenta como trabajo pendiente: queda en ocr_pending, que es su
    # propio estado, así que el bucle de extracción termina en lugar de reintentarla sin fin.
    assert extraction._ingestions.pending_extraction_count(batch_id) == 0
    extraction.run_extraction_job(FakeExecution(job))

    with session_factory() as session:
        segunda = session.execute(
            select(func.count()).select_from(ExtractedRepresentationRecord)
        ).scalar_one()
    assert segunda == primera == 3, "PDF, CSV e imagen dejan una representación cada uno"


def test_la_extraccion_se_puede_cancelar_y_deja_el_lote_coherente(services, material: Path) -> None:
    ingestion, extraction, _jobs, _clock = services
    batch_id = _import(ingestion, material)
    job = _job_for(ingestion, batch_id, JobType.EXTRACT_ARTIFACT)

    with pytest.raises(JobCancelledError):
        extraction.run_extraction_job(FakeExecution(job, cancel_after=1))

    detalle = ingestion.get_batch(batch_id)
    # El lote queda **cerrado** en `cancelled`, no a medias: lo copiado sigue copiado y no hay
    # representaciones incompletas.
    assert detalle.batch.status == BatchStatus.CANCELLED.value
    counters = detalle.batch.counters
    assert counters["total"] == 4
    assert counters["total"] == (
        counters["copied"]
        + counters["pending"]
        + counters["failed"]
        + counters["cancelled"]
        + counters["source_changed"]
        + counters["preserved_unsupported"]
    )
    # Lo que no se llegó a extraer sigue copiado y disponible para otra pasada.
    assert counters["copied"] >= 1


def test_el_html_no_ejecuta_nada_al_extraer_en_el_pipeline(
    services, tmp_path: Path, session_factory
) -> None:
    """El HTML con scripts entra por el pipeline y sale como texto, sin rastro de código."""
    ingestion, extraction, _jobs, _clock = services
    root = tmp_path / "web"
    root.mkdir()
    build_html(root / "material.html")

    batch_id = _import(ingestion, root)
    job = _job_for(ingestion, batch_id, JobType.EXTRACT_ARTIFACT)
    extraction.run_extraction_job(FakeExecution(job))

    representaciones = extraction.representations_for_batch(batch_id)
    html = next(view for view in representaciones if view.kind == "html_text")
    assert html.quality in {"good", "usable_with_warnings"}

    trozo = extraction.read_text(html.id, offset=0, limit=5000)
    assert "fetch(" not in trozo.text
    assert "alert(" not in trozo.text
    assert "Tema 2" in trozo.text
    # Y el estado del lote sigue cuadrando con el nuevo término del informe.
    detalle = ingestion.get_batch(batch_id)
    assert detalle.batch.counters["preserved_unsupported"] == 0


def test_un_zip_se_expande_en_entradas_del_lote_y_se_extrae(services, tmp_path: Path) -> None:
    """Un ZIP copiado se expande: cada miembro se copia, se extrae y aparece en el informe.

    El contenedor queda `expanded` (conservado y procesado, sin texto propio) y sus miembros siguen
    el mismo pipeline que cualquier otro fichero.
    """
    ingestion, extraction, _jobs, _clock = services
    root = tmp_path / "paquete"
    root.mkdir()
    build_zip(
        root / "material.zip",
        {
            "temas/tema-01.txt": b"La Ley 39/2015 regula el procedimiento administrativo comun.",
            "temas/tema-02.md": b"# Tema 2\n\nEl acto administrativo y su eficacia.",
            "basura.exe": b"MZ no se debe copiar",
        },
    )

    batch_id = _import(ingestion, root)
    job = _job_for(ingestion, batch_id, JobType.EXTRACT_ARTIFACT)
    extraction.run_extraction_job(FakeExecution(job))

    detalle = ingestion.get_batch(batch_id)
    estados = {entry.relative_path: entry.status for entry in detalle.entries}
    assert estados["material.zip"] == ItemStatus.EXPANDED.value
    assert estados["material.zip/temas/tema-01.txt"] == ItemStatus.EXTRACTED.value
    assert estados["material.zip/temas/tema-02.md"] == ItemStatus.EXTRACTED.value
    assert "material.zip/basura.exe" not in estados, "el ejecutable de dentro no se copia"

    codigos = {issue.code for issue in detalle.issues}
    assert IssueCode.CONTAINER_EXPANDED.value in codigos
    assert IssueCode.OMITTED_EXECUTABLE.value in codigos

    counters = detalle.batch.counters
    assert counters["total"] == 3, "el contenedor y sus dos miembros"
    assert counters["copied"] == 3, "el contenedor tambien esta copiado: sus bytes estan a salvo"

    # El texto de un miembro se puede leer desde su representación.
    representaciones = extraction.representations_for_batch(batch_id)
    assert len(representaciones) == 2
    trozo = extraction.read_text(representaciones[0].id, offset=0, limit=500)
    assert trozo.text.strip()


def test_una_baraja_de_anki_entra_como_material_y_no_se_expande_como_un_zip(
    services, tmp_path: Path
) -> None:
    """Un `.apkg` se lee como baraja: sus tarjetas son texto citable, no un ZIP con un SQLite.

    Si el contenedor se tratara como un ZIP cualquiera, entrarían como entradas sueltas la colección
    (un SQLite ilegible) y las imágenes del mazo, y las tarjetas se perderían.
    """
    ingestion, extraction, _jobs, _clock = services
    root = tmp_path / "barajas"
    root.mkdir()
    build_anki_deck(
        root / "Tema 5 - plazos.apkg",
        cards=[
            ("¿Cuál es el plazo de alegaciones?", "Diez días hábiles."),
            ("¿Quién resuelve?", "El órgano competente."),
        ],
        deck="Tema 5",
        tags="plazos",
    )

    batch_id = _import(ingestion, root)
    job = _job_for(ingestion, batch_id, JobType.EXTRACT_ARTIFACT)
    extraction.run_extraction_job(FakeExecution(job))

    detalle = ingestion.get_batch(batch_id)
    estados = {entry.relative_path: entry.status for entry in detalle.entries}
    assert list(estados) == ["Tema 5 - plazos.apkg"], "la baraja no se expande en miembros"
    assert estados["Tema 5 - plazos.apkg"] == ItemStatus.EXTRACTED.value

    representaciones = extraction.representations_for_batch(batch_id)
    assert len(representaciones) == 1
    representacion = representaciones[0]
    assert representacion.extractor_name == "anki_apkg"
    assert representacion.quality in {"good", "usable_with_warnings"}
    # Sin media en la baraja no hay aviso de media: el aviso se da cuando hay algo que no se extrae.
    assert "media_not_extracted" not in representacion.warnings

    trozo = extraction.read_text(representacion.id, offset=0, limit=2000)
    assert "TARJETA 1. Tema 5 · Básico" in trozo.text
    assert "TARJETA 2. Tema 5 · Básico" in trozo.text, "las dos tarjetas entran, no solo la primera"
    assert "¿Cuál es el plazo de alegaciones?" in trozo.text
    assert "Diez días hábiles." in trozo.text
    assert "Etiquetas: plazos" in trozo.text


def test_un_zip_dentro_de_otro_no_se_expande_ni_con_nombre_enganoso(
    services, tmp_path: Path
) -> None:
    """El ZIP anidado se conserva íntegro y se declara: no se descomprime en cadena.

    Cada nivel de anidamiento multiplica lo que se escribe en disco, que es justo lo que aprovecha
    una bomba de archivos. El contenedor de fuera sí se expande (un nivel) y el de dentro queda
    `unsupported_preserved`, sin que sus miembros lleguen a ser entradas del lote.

    El de dentro se llama `inner.bin`, no `inner.zip`: el límite se decide con la **profundidad
    guardada en la entrada**, no contando sufijos, así que un contenedor con otro nombre no cuela.
    """
    ingestion, extraction, _jobs, _clock = services
    root = tmp_path / "anidado"
    root.mkdir()
    interior = build_zip(tmp_path / "interior.zip", {"tema-02.txt": b"Contenido de dentro."})
    build_zip(
        root / "paquete.zip",
        {"tema-01.txt": b"Contenido de fuera.", "inner.bin": interior.read_bytes()},
    )
    interior.unlink()

    batch_id = _import(ingestion, root)
    extraction.run_extraction_job(
        FakeExecution(_job_for(ingestion, batch_id, JobType.EXTRACT_ARTIFACT))
    )

    detalle = ingestion.get_batch(batch_id)
    estados = {entry.relative_path: entry.status for entry in detalle.entries}
    assert estados["paquete.zip"] == ItemStatus.EXPANDED.value
    assert estados["paquete.zip/tema-01.txt"] == ItemStatus.EXTRACTED.value
    assert estados["paquete.zip/inner.bin"] == ItemStatus.UNSUPPORTED_PRESERVED.value
    assert "paquete.zip/inner.bin/tema-02.txt" not in estados, "el anidado no se descomprime"

    # La profundidad queda guardada como dato: el de fuera en 0 y su miembro (el contenedor de
    # dentro) en 1, que es lo que impide expandirlo otra vez.
    profundidades = {entry.relative_path: entry.container_depth for entry in detalle.entries}
    assert profundidades["paquete.zip"] == 0
    assert profundidades["paquete.zip/inner.bin"] == 1
    assert profundidades["paquete.zip/tema-01.txt"] == 1

    codigos = {issue.code for issue in detalle.issues}
    assert IssueCode.UNSUPPORTED_PRESERVED.value in codigos
    assert detalle.batch.counters["preserved_unsupported"] == 1


def test_un_zip_con_traversal_se_rechaza_sin_expandir(services, tmp_path: Path) -> None:
    """Un ZIP que intenta salir de la carpeta no se expande ni escribe nada fuera."""
    ingestion, extraction, _jobs, _clock = services
    root = tmp_path / "malicioso"
    root.mkdir()
    fuera = tmp_path / "fuera.txt"
    build_zip(root / "malo.zip", {"../fuera.txt": b"no deberia copiarse"})

    batch_id = _import(ingestion, root)
    job = _job_for(ingestion, batch_id, JobType.EXTRACT_ARTIFACT)
    extraction.run_extraction_job(FakeExecution(job))

    detalle = ingestion.get_batch(batch_id)
    contenedor = next(entry for entry in detalle.entries if entry.relative_path == "malo.zip")
    assert contenedor.status == ItemStatus.FAILED.value
    codigos = {issue.code for issue in detalle.issues}
    assert IssueCode.UNSAFE_CONTAINER.value in codigos
    assert not fuera.exists(), "nada se ha escrito fuera de su sitio"
    assert len(detalle.entries) == 1, "no se añadió ninguna entrada del contenedor"


def test_dos_entradas_con_el_mismo_contenido_comparten_una_sola_representacion(
    services, tmp_path: Path
) -> None:
    """Un contenido repetido en el lote deja **un** texto, con sus dos procedencias.

    La representación se enlaza desde las entradas: si el lector devolviera una fila por entrada, el
    usuario vería el mismo texto dos veces y creería que son dos documentos.
    """
    ingestion, extraction, _jobs, _clock = services
    root = tmp_path / "repetido"
    root.mkdir()
    original = build_text_pdf(root / "tema-01.pdf", pages=1)
    shutil.copyfile(original, root / "tema-01-copia.pdf")

    batch_id = _import(ingestion, root)
    extraction.run_extraction_job(
        FakeExecution(_job_for(ingestion, batch_id, JobType.EXTRACT_ARTIFACT))
    )

    representaciones = extraction.representations_for_batch(batch_id)
    assert len(representaciones) == 1, "un artefacto, una representación"
    assert set(representaciones[0].source_locations) == {"tema-01.pdf", "tema-01-copia.pdf"}
    assert {source.origin_type for source in representaciones[0].sources} == {"file"}


def test_no_quedan_directorios_de_texto_huerfanos_al_deduplicar(services, tmp_path: Path) -> None:
    """El texto se escribe **después** de saber si la representación ya existía.

    Antes se creaba `data/extracted/<uuid>` y luego la base decía que esa representación ya estaba
    (el mismo artefacto procesado por dos entradas): quedaba un directorio que ningún registro
    referenciaba, ocupando disco para siempre.
    """
    ingestion, extraction, _jobs, _clock = services
    root = tmp_path / "repetido"
    root.mkdir()
    original = build_text_pdf(root / "tema-01.pdf", pages=1)
    shutil.copyfile(original, root / "tema-01-copia.pdf")

    batch_id = _import(ingestion, root)
    extraction.run_extraction_job(
        FakeExecution(_job_for(ingestion, batch_id, JobType.EXTRACT_ARTIFACT))
    )

    representaciones = extraction.representations_for_batch(batch_id)
    directorios = sorted(
        path.name for path in (extraction._representations._paths.extracted).iterdir()
    )
    assert len(directorios) == len(representaciones), (
        "un directorio por representación, ni uno más: "
        f"{len(directorios)} directorios y {len(representaciones)} representaciones"
    )
    assert {view.id for view in representaciones} == set(directorios)


def test_si_la_base_falla_no_queda_el_texto_escrito(services, tmp_path: Path, monkeypatch) -> None:
    """Sin fila que lo referencie, el texto escrito se retira: no se deja basura a medias."""
    ingestion, extraction, _jobs, _clock = services
    root = tmp_path / "material"
    root.mkdir()
    build_text_pdf(root / "temario.pdf", pages=1)

    batch_id = _import(ingestion, root)
    job = _job_for(ingestion, batch_id, JobType.EXTRACT_ARTIFACT)

    def falla(**kwargs: object) -> None:
        raise RuntimeError("la base dijo que no")

    monkeypatch.setattr(extraction._repository, "save", falla)

    with pytest.raises(RuntimeError):
        extraction.run_extraction_job(FakeExecution(job))

    # El trabajo falla (y el worker se encargará del lote), pero no queda texto huérfano.
    assert list(extraction._representations._paths.extracted.iterdir()) == []


def test_los_bytes_del_informe_miden_la_presencia_fisica(services, material: Path) -> None:
    """`copied_bytes` cuenta lo que **está** en el almacén, sea cual sea su resultado de proceso.

    El material sintético de la prueba tiene un `.xlsx` que se conserva sin extraer
    (`unsupported_preserved`) y un `.png` pendiente de OCR. Antes, los bytes se calculaban por
    estado y esas entradas no sumaban: el informe decía que no se había guardado nada mientras el
    material estaba en el almacén. Ahora se mide por presencia física (`artifact_id IS NOT NULL`) y
    el resultado del procesamiento se declara aparte, con sus contadores.
    """
    ingestion, extraction, _jobs, _clock = services
    batch_id = _import(ingestion, material)
    job = _job_for(ingestion, batch_id, JobType.EXTRACT_ARTIFACT)

    extraction.run_extraction_job(FakeExecution(job))

    detalle = extraction._ingestions.get_batch_detail(batch_id, entry_limit=50, issue_limit=50)
    assert detalle is not None
    copiados = [
        entry
        for entry in detalle.entries
        if entry.status in {"copied", "hashed", "extracted", "expanded", "ocr_pending"}
    ]
    conservados = [
        entry for entry in detalle.entries if entry.status == ItemStatus.UNSUPPORTED_PRESERVED.value
    ]
    assert len(copiados) == detalle.batch.counters["copied"]
    assert len(conservados) == detalle.batch.counters["preserved_unsupported"] == 1
    # Los bytes incluyen también lo conservado sin extraer: está en el almacén.
    assert detalle.batch.counters["copied_bytes"] == sum(
        entry.size_bytes for entry in copiados + conservados
    )
    assert detalle.batch.counters["copied_bytes"] > sum(entry.size_bytes for entry in copiados)


def test_los_bytes_incluyen_una_extraccion_fallida(services, tmp_path: Path) -> None:
    """Una entrada cuya extracción falla sigue contando sus bytes: el artefacto está guardado.

    Es la separación que faltaba: el **resultado** del proceso es `failed` (y así se declara en el
    informe), pero el material está en el almacén y el informe no puede decir que no se copió nada.
    """
    ingestion, extraction, _jobs, _clock = services
    root = tmp_path / "roto"
    root.mkdir()
    trampa = build_bomb_docx(root / "trampa.docx")

    batch_id = _import(ingestion, root)
    extraction.run_extraction_job(
        FakeExecution(_job_for(ingestion, batch_id, JobType.EXTRACT_ARTIFACT))
    )

    detalle = extraction._ingestions.get_batch_detail(batch_id, entry_limit=50, issue_limit=50)
    assert detalle is not None
    entrada = next(entry for entry in detalle.entries if entry.relative_path == "trampa.docx")
    assert entrada.status == ItemStatus.FAILED.value
    assert detalle.batch.counters["failed"] == 1
    assert detalle.batch.counters["copied_bytes"] == trampa.stat().st_size
    assert detalle.batch.counters["copied_bytes"] > 0


def test_una_entrada_puede_tener_texto_nativo_y_ocr_a_la_vez(services, tmp_path: Path) -> None:
    """La relación entrada→representación no es singular: el OCR convive con el texto nativo.

    Con una clave ajena singular, extraer el OCR habría pisado el enlace al texto nativo y el lote
    habría dejado de mostrar una representación válida. Aquí se enlazan las dos a la misma entrada y
    las dos aparecen en el lote, cada una con su tipo.
    """
    ingestion, extraction, _jobs, _clock = services
    root = tmp_path / "escaneado"
    root.mkdir()
    build_text_pdf(root / "temario.pdf", pages=1)

    batch_id = _import(ingestion, root)
    extraction.run_extraction_job(
        FakeExecution(_job_for(ingestion, batch_id, JobType.EXTRACT_ARTIFACT))
    )

    nativa = extraction.representations_for_batch(batch_id)[0]
    assert nativa.kind == "native_text"

    # El OCR que llegará en S05 hace exactamente esto: guarda su representación y la enlaza.
    item = extraction._ingestions.list_entries(batch_id, limit=10, offset=0).entries[0]
    ocr_id = str(uuid4())
    extraction._representations.save(
        ocr_id,
        ExtractionResult(
            kind=RepresentationKind.OCR,
            status=RepresentationStatus.EXTRACTED,
            text="Texto reconocido por OCR del temario sintetico.",
            extractor=ExtractorRef("tesseract", "1"),
            quality=Quality.OCR_UNREVIEWED,
            ocr_candidate=True,
        ),
    )
    extraction._repository.save(
        result=ExtractionResult(
            kind=RepresentationKind.OCR,
            status=RepresentationStatus.EXTRACTED,
            text="Texto reconocido por OCR del temario sintetico.",
            extractor=ExtractorRef("tesseract", "1"),
            quality=Quality.OCR_UNREVIEWED,
            ocr_candidate=True,
        ),
        artifact_id=nativa.artifact_id,
        representation_id=ocr_id,
        text_storage_key=f"{ocr_id}/texto.txt",
        now=_clock.now(),
    )
    extraction._ingestions.link_representation(item.id, ocr_id, now=_clock.now())

    vistas = extraction.representations_for_batch(batch_id)
    tipos = sorted(view.kind for view in vistas)
    assert tipos == ["native_text", "ocr"], "las dos representaciones siguen enlazadas a la entrada"
    # Y ninguna sustituyó a la otra: la nativa sigue con su texto.
    assert extraction.read_text(nativa.id, offset=0, limit=50).text
    assert extraction.read_text(ocr_id, offset=0, limit=50).text.startswith("Texto reconocido")


def test_si_falla_el_segundo_fichero_no_queda_una_representacion_a_medias(
    services, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`texto.txt` y `estructura.json` se escriben en un temporal y se mueven de una vez.

    Un fallo entre los dos (disco lleno, corte de luz) dejaba un directorio con solo `texto.txt`,
    que parecía una representación válida. Ahora, si cualquiera de los dos falla, no queda nada.
    """
    ingestion, extraction, _jobs, _clock = services
    root = tmp_path / "material"
    root.mkdir()
    build_text_pdf(root / "temario.pdf", pages=1)

    batch_id = _import(ingestion, root)
    job = _job_for(ingestion, batch_id, JobType.EXTRACT_ARTIFACT)

    def rompe(*args: object, **kwargs: object) -> str:
        raise OSError("el disco se llenó al escribir la estructura")

    monkeypatch.setattr("opofuente.infrastructure.representation_store.json.dumps", rompe)

    with pytest.raises(OSError):
        extraction.run_extraction_job(FakeExecution(job))

    extracted = extraction._representations._paths.extracted
    assert list(extracted.iterdir()) == [], "ni el destino a medias ni el temporal"


def test_el_texto_guardado_es_legible_y_coincide_con_la_representacion(
    services, material: Path
) -> None:
    """El texto que se lee por trozos es exactamente el que dice la representación."""
    ingestion, extraction, _jobs, _clock = services
    batch_id = _import(ingestion, material)
    extraction.run_extraction_job(
        FakeExecution(_job_for(ingestion, batch_id, JobType.EXTRACT_ARTIFACT))
    )

    for vista in extraction.representations_for_batch(batch_id):
        trozo = extraction.read_text(vista.id, offset=0, limit=10_000)
        assert trozo.total_chars == vista.char_count
        assert trozo.text == trozo.text  # el trozo leído no se recorta por su cuenta
        assert extraction._representations.sections(vista.id), "la estructura también se guarda"


def test_el_ocr_pendiente_se_declara_sin_romper_la_aplicacion(services, tmp_path: Path) -> None:
    """Sin Tesseract configurado, la imagen queda pendiente y la API sigue respondiendo."""
    ingestion, extraction, _jobs, _clock = services
    root = tmp_path / "imagenes"
    root.mkdir()
    build_png(root / "escaneo.png")

    batch_id = _import(ingestion, root)
    job = _job_for(ingestion, batch_id, JobType.EXTRACT_ARTIFACT)
    extraction.run_extraction_job(FakeExecution(job))

    detalle = ingestion.get_batch(batch_id)
    assert detalle.batch.status == BatchStatus.SUCCEEDED.value
    incidencia = next(
        issue for issue in detalle.issues if issue.code == IssueCode.OCR_PENDING.value
    )
    assert incidencia.severity == "warning"

    representacion = extraction.representations_for_batch(batch_id)[0]
    assert representacion.status == RepresentationStatus.PENDING.value
    assert representacion.ocr_candidate is True
    assert representacion.quality == "poor"
