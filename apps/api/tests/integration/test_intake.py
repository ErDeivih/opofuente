"""Pruebas de integración de las entradas directas de S03 y del lector (04_INGESTION §2 y §5).

Cubre lo que el usuario puede hacer además de elegir una carpeta: subir ficheros, pegar texto y
pegar una URL. La URL se prueba con un descargador inyectado (nada de salir a la red en la suite) y,
por separado, se comprueba que una URL interna se rechaza de verdad.

Todo el material es sintético y vive en directorios temporales.
"""

from __future__ import annotations

import io
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from opofuente.application.intake_service import IntakeFile, IntakeService
from opofuente.application.read_models import RepresentationView
from opofuente.config import Settings
from opofuente.domain.errors import InvalidSourceError, UnsafeContentError
from opofuente.domain.ingestion import BatchStatus, ItemStatus
from opofuente.infrastructure.artifact_store import ArtifactStore
from opofuente.infrastructure.clock import SystemClock
from opofuente.infrastructure.db import build_engine, build_session_factory
from opofuente.infrastructure.ingestion_repository import SqlAlchemyIngestionRepository
from opofuente.infrastructure.job_repository import SqlAlchemyJobRepository
from opofuente.infrastructure.url_guard import FetchResult, url_limits_from_settings
from opofuente_testing.jobs import FakeExecution, run_one_job
from opofuente_testing.synthetic_documents import build_csv, build_text_pdf, build_zip

ALLOWED_ORIGIN = {"Origin": "http://127.0.0.1:5173"}


def _representations(client: TestClient, batch_id: str) -> list[dict]:
    respuesta = client.get(f"/api/v1/ingestion-batches/{batch_id}/representations")
    assert respuesta.status_code == 200, respuesta.text
    return respuesta.json()


# --- texto pegado ---------------------------------------------------------------------------


def test_pegar_texto_crea_material_con_texto_extraido(api_only_client: TestClient) -> None:
    respuesta = api_only_client.post(
        "/api/v1/ingestion-batches/paste",
        json={
            "text": "La Ley 39/2015 regula el procedimiento administrativo común.",
            "title": "Apunte",
        },
        headers=ALLOWED_ORIGIN,
    )
    assert respuesta.status_code == 200, respuesta.text
    batch = respuesta.json()
    assert batch["kind"] == "import"
    assert batch["status"] == "queued"
    assert batch["counters"]["copied"] == 1
    assert batch["counters"]["pending"] == 0
    assert batch["source_path_display"] == "Apunte"

    run_one_job(api_only_client)

    detalle = api_only_client.get(f"/api/v1/ingestion-batches/{batch['id']}").json()
    assert detalle["batch"]["status"] == "succeeded"
    entrada = detalle["entries"][0]
    assert entrada["relative_path"] == "Apunte"
    assert entrada["status"] == ItemStatus.EXTRACTED.value

    representaciones = _representations(api_only_client, batch["id"])
    assert len(representaciones) == 1
    representacion = representaciones[0]
    assert representacion["kind"] == "plain_text"
    assert representacion["has_text"] is True
    assert representacion["quality"] in {"good", "usable_with_warnings"}

    texto = api_only_client.get(
        f"/api/v1/representations/{representacion['id']}/text", params={"offset": 0, "limit": 100}
    ).json()
    assert "Ley 39/2015" in texto["text"]
    assert texto["total_chars"] == representacion["char_count"]
    assert texto["truncated"] is False
    assert texto["quality"] == representacion["quality"]


def test_pegar_texto_vacio_se_rechaza(api_only_client: TestClient) -> None:
    respuesta = api_only_client.post(
        "/api/v1/ingestion-batches/paste", json={"text": "   "}, headers=ALLOWED_ORIGIN
    )
    assert respuesta.status_code == 400
    assert respuesta.json()["code"] == "invalid_source"


def test_pegar_mas_texto_del_permitido_se_rechaza_sin_crear_lote(
    migrated_settings: Settings,
) -> None:
    """El tope del pegado es real: no se guarda nada y no queda un lote a medias."""
    engine = build_engine(migrated_settings.data_paths.database)
    try:
        sesiones = build_session_factory(engine)
        repositorio = SqlAlchemyIngestionRepository(sesiones)
        paths = migrated_settings.data_paths
        servicio = IntakeService(
            repository=repositorio,
            jobs=SqlAlchemyJobRepository(sesiones),
            store=ArtifactStore(paths),
            clock=SystemClock(),
            data_root=paths.root,
            max_file_bytes=migrated_settings.max_file_bytes,
            max_paste_bytes=1024,
        )

        with pytest.raises(InvalidSourceError):
            servicio.ingest_paste("a" * 2048)

        assert repositorio.list_batches(limit=10, offset=0) == ()
    finally:
        engine.dispose()


# --- ficheros subidos -----------------------------------------------------------------------


def test_subir_ficheros_los_copia_y_los_extrae(api_only_client: TestClient, tmp_path: Path) -> None:
    pdf = build_text_pdf(tmp_path / "temario.pdf", pages=1)
    csv = build_csv(tmp_path / "preguntas.csv", rows=2)

    respuesta = api_only_client.post(
        "/api/v1/ingestion-batches/files",
        files=[
            ("files", (pdf.name, pdf.read_bytes(), "application/pdf")),
            ("files", (csv.name, csv.read_bytes(), "text/csv")),
        ],
        headers=ALLOWED_ORIGIN,
    )
    assert respuesta.status_code == 200, respuesta.text
    batch = respuesta.json()
    assert batch["counters"]["copied"] == 2
    assert batch["source_path_display"] == "2 fichero(s) seleccionados"

    run_one_job(api_only_client)

    detalle = api_only_client.get(f"/api/v1/ingestion-batches/{batch['id']}").json()
    estados = {entry["relative_path"]: entry["status"] for entry in detalle["entries"]}
    assert estados == {
        "temario.pdf": ItemStatus.EXTRACTED.value,
        "preguntas.csv": ItemStatus.EXTRACTED.value,
    }
    tipos = {view["kind"] for view in _representations(api_only_client, batch["id"])}
    assert tipos == {"native_text", "csv_preview"}


def test_dos_ficheros_con_el_mismo_nombre_no_se_pisan(
    api_only_client: TestClient, tmp_path: Path
) -> None:
    """El nombre es metadato, pero dos entradas del mismo lote no pueden compartir ruta."""
    uno = tmp_path / "notas.txt"
    uno.write_text("primera versión", encoding="utf-8")

    respuesta = api_only_client.post(
        "/api/v1/ingestion-batches/files",
        files=[
            ("files", ("notas.txt", uno.read_bytes(), "text/plain")),
            ("files", ("notas.txt", b"segunda version distinta", "text/plain")),
        ],
        headers=ALLOWED_ORIGIN,
    )
    assert respuesta.status_code == 200, respuesta.text
    batch = respuesta.json()

    detalle = api_only_client.get(f"/api/v1/ingestion-batches/{batch['id']}").json()
    rutas = sorted(entry["relative_path"] for entry in detalle["entries"])
    assert rutas == ["notas (2).txt", "notas.txt"]
    assert detalle["batch"]["counters"]["copied"] == 2
    # Dos contenidos distintos: dos artefactos, no uno.
    assert detalle["report"]["artifacts_total"] == 2


def test_subir_un_zip_lo_expande_al_extraer(api_only_client: TestClient, tmp_path: Path) -> None:
    paquete = build_zip(
        tmp_path / "material.zip",
        {"temas/tema-01.txt": b"Contenido sintetico del tema uno.", "leeme.md": b"# Lee me"},
    )

    respuesta = api_only_client.post(
        "/api/v1/ingestion-batches/files",
        files=[("files", ("material.zip", paquete.read_bytes(), "application/zip"))],
        headers=ALLOWED_ORIGIN,
    )
    assert respuesta.status_code == 200, respuesta.text
    batch = respuesta.json()
    assert batch["counters"]["copied"] == 1, "de momento solo el contenedor"

    run_one_job(api_only_client)

    detalle = api_only_client.get(f"/api/v1/ingestion-batches/{batch['id']}").json()
    estados = {entry["relative_path"]: entry["status"] for entry in detalle["entries"]}
    assert estados["material.zip"] == ItemStatus.EXPANDED.value
    assert estados["material.zip/temas/tema-01.txt"] == ItemStatus.EXTRACTED.value
    assert estados["material.zip/leeme.md"] == ItemStatus.EXTRACTED.value
    codigos = {issue["code"] for issue in detalle["issues"]}
    assert "container_expanded" in codigos


def test_una_subida_no_deja_temporales_sueltos(
    api_only_client: TestClient, migrated_settings: Settings, tmp_path: Path
) -> None:
    """El temporal de la subida se borra al copiar: `data/tmp` no se llena de `.part` huérfanos."""
    archivo = tmp_path / "notas.txt"
    archivo.write_text("material sintetico para la prueba", encoding="utf-8")

    respuesta = api_only_client.post(
        "/api/v1/ingestion-batches/files",
        files=[("files", ("notas.txt", archivo.read_bytes(), "text/plain"))],
        headers=ALLOWED_ORIGIN,
    )
    assert respuesta.status_code == 200, respuesta.text

    temporales = list((migrated_settings.data_paths.root / "tmp").glob("*.part"))
    assert temporales == [], f"quedaron temporales sin borrar: {temporales}"


def test_subir_sin_ficheros_se_rechaza(api_only_client: TestClient) -> None:
    respuesta = api_only_client.post(
        "/api/v1/ingestion-batches/files", files=[], headers=ALLOWED_ORIGIN
    )
    assert respuesta.status_code in {400, 422}


def test_una_subida_rechazada_tampoco_deja_temporales(migrated_settings: Settings) -> None:
    """Con el tope de tamaño superado, el temporal en curso se borra.

    El temporal no entraba en la lista de «preparados» hasta terminar de escribirse, así que el
    fichero que reventaba el límite dejaba su `.part` abandonado en `data/tmp` para siempre.
    """
    engine = build_engine(migrated_settings.data_paths.database)
    try:
        sesiones = build_session_factory(engine)
        paths = migrated_settings.data_paths
        servicio = IntakeService(
            repository=SqlAlchemyIngestionRepository(sesiones),
            jobs=SqlAlchemyJobRepository(sesiones),
            store=ArtifactStore(paths),
            clock=SystemClock(),
            data_root=paths.root,
            max_file_bytes=1024,
        )

        with pytest.raises(UnsafeContentError):
            servicio.stage_uploads([("grande.bin", io.BytesIO(b"x" * 4096))])

        assert list((paths.root / "tmp").glob("*.part")) == []
    finally:
        engine.dispose()


def test_el_temporal_se_borra_tambien_si_falla_la_copia(
    migrated_settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Si la copia al almacén falla a mitad, el temporal de la subida se retira igual."""
    engine = build_engine(migrated_settings.data_paths.database)
    try:
        sesiones = build_session_factory(engine)
        paths = migrated_settings.data_paths
        servicio = IntakeService(
            repository=SqlAlchemyIngestionRepository(sesiones),
            jobs=SqlAlchemyJobRepository(sesiones),
            store=ArtifactStore(paths),
            clock=SystemClock(),
            data_root=paths.root,
            max_file_bytes=migrated_settings.max_file_bytes,
        )
        preparados = servicio.stage_uploads([("notas.txt", io.BytesIO(b"material sintetico"))])
        assert list((paths.root / "tmp").glob("*.part")), "el temporal existe antes de copiar"

        def falla(*args: object, **kwargs: object) -> None:
            raise OSError("el disco dijo que no")

        monkeypatch.setattr(servicio._store, "store_file", falla)

        with pytest.raises(OSError):
            servicio.ingest_files(preparados)

        assert list((paths.root / "tmp").glob("*.part")) == []
    finally:
        engine.dispose()


# --- ejecutables: se rechazan antes de copiarlos (regresión S03) ------------------------------


@pytest.mark.parametrize(
    ("nombre", "contenido"),
    [
        ("instalador.exe", b"MZ" + b"\x00" * 64),
        ("script.ps1", b"Write-Output 'no se admite'"),
        ("libreria.dll", b"MZ" + b"\x00" * 64),
        # Nombre inocente con firma de ejecutable: los bytes mandan.
        ("apuntes.dat", b"MZ" + b"\x00" * 64),
        ("material.bin", b"\x7fELF" + b"\x00" * 64),
    ],
)
def test_un_ejecutable_subido_se_rechaza_antes_de_guardarlo(
    api_only_client: TestClient,
    migrated_settings: Settings,
    nombre: str,
    contenido: bytes,
) -> None:
    """Un binario no llega al almacén: se rechaza con su motivo y no queda nada por el camino.

    Antes se copiaba primero y se rechazaba después (al extraer), así que el ejecutable ya estaba en
    el almacén y el lote tenía una entrada fallida que no debía existir. Además, al perderse la
    extensión en la ruta del almacén, el rechazo por sufijo no funcionaba en absoluto.
    """
    antes_artefactos = len(list((migrated_settings.data_paths.artifacts / "sha256").rglob("*")))
    antes_lotes = len(api_only_client.get("/api/v1/ingestion-batches").json())

    respuesta = api_only_client.post(
        "/api/v1/ingestion-batches/files",
        files=[("files", (nombre, contenido, "application/octet-stream"))],
        headers=ALLOWED_ORIGIN,
    )

    assert respuesta.status_code == 400, respuesta.text
    cuerpo = respuesta.json()
    assert cuerpo["code"] == "unsafe_content"
    assert "ejecutable" in cuerpo["detail"] or "firma" in cuerpo["detail"]
    # Ni copia, ni lote, ni temporal.
    assert (
        len(list((migrated_settings.data_paths.artifacts / "sha256").rglob("*")))
        == antes_artefactos
    )
    assert list((migrated_settings.data_paths.root / "tmp").glob("*.part")) == []
    assert len(api_only_client.get("/api/v1/ingestion-batches").json()) == antes_lotes, (
        "un ejecutable rechazado no puede crear un lote"
    )


def test_un_ejecutable_dentro_de_un_zip_tampoco_se_copia(
    api_only_client: TestClient, tmp_path: Path
) -> None:
    """El de dentro tampoco entra, y aunque se llame `.txt` (firma PE) sigue sin entrar."""
    paquete = build_zip(
        tmp_path / "material.zip",
        {
            "temas/tema-01.txt": b"Contenido sintetico del tema uno.",
            "basura.exe": b"MZ" + b"\x00" * 64,
            "disfrazado.txt": b"MZ" + b"\x00" * 64,
        },
    )
    batch = api_only_client.post(
        "/api/v1/ingestion-batches/files",
        files=[("files", ("material.zip", paquete.read_bytes(), "application/zip"))],
        headers=ALLOWED_ORIGIN,
    ).json()

    run_one_job(api_only_client)

    detalle = api_only_client.get(f"/api/v1/ingestion-batches/{batch['id']}").json()
    rutas = {entry["relative_path"] for entry in detalle["entries"]}
    assert "material.zip/temas/tema-01.txt" in rutas
    assert "material.zip/basura.exe" not in rutas
    assert "material.zip/disfrazado.txt" not in rutas, (
        "la firma PE se reconoce aunque el nombre mienta"
    )


# --- el trabajo de extracción queda enlazado con el lote (regresión S03) ----------------------


def test_el_lote_de_una_entrada_directa_apunta_a_su_trabajo_de_extraccion(
    api_only_client: TestClient,
) -> None:
    """El lote guarda el identificador del trabajo de extracción: el que se sigue y se cancela.

    Antes el trabajo se encolaba pero no se guardaba en el lote (`set_job`), así que la interfaz
    consultaba un trabajo viejo (o ninguno) y el progreso que mostraba no era el de su lote.
    """
    batch = api_only_client.post(
        "/api/v1/ingestion-batches/paste",
        json={"text": "Material sintetico pegado para la prueba del trabajo."},
        headers=ALLOWED_ORIGIN,
    ).json()

    assert batch["job_id"], "una entrada directa deja su trabajo de extracción enlazado"
    trabajo = api_only_client.get(f"/api/v1/jobs/{batch['job_id']}").json()
    assert trabajo["job_type"] == "extract_artifact"
    assert trabajo["status"] == "queued"

    run_one_job(api_only_client)

    # Y el progreso que se muestra es el de ese trabajo, no el de otro.
    terminado = api_only_client.get(f"/api/v1/jobs/{batch['job_id']}").json()
    assert terminado["status"] == "succeeded"
    assert terminado["progress"] == 1.0
    assert terminado["step"], "el trabajo informa del último paso dado"
    detalle = api_only_client.get(f"/api/v1/ingestion-batches/{batch['id']}").json()
    assert detalle["batch"]["status"] == "succeeded"
    assert detalle["batch"]["job_id"] == batch["job_id"]


def test_cancelar_un_lote_de_entrada_directa_cancela_su_extraccion(
    api_only_client: TestClient,
) -> None:
    """Cancelar el lote cancela **su** trabajo: con el enlace roto no se cancelaba nada."""
    batch = api_only_client.post(
        "/api/v1/ingestion-batches/files",
        files=[("files", ("notas.txt", b"material sintetico de la prueba", "text/plain"))],
        headers=ALLOWED_ORIGIN,
    ).json()

    respuesta = api_only_client.post(
        f"/api/v1/ingestion-batches/{batch['id']}/cancel", headers=ALLOWED_ORIGIN
    )
    assert respuesta.status_code == 200, respuesta.text

    trabajo = api_only_client.get(f"/api/v1/jobs/{batch['job_id']}").json()
    assert trabajo["status"] == "cancel_requested"
    assert trabajo["cancel_requested"] is True

    # El worker ejecuta el trabajo cancelado y lo cierra: el lote queda **cancelled**, no cerrado
    # como si hubiera terminado. Aceptar «cancelled o succeeded» no demostraba nada: la extracción
    # se comprueba antes de tocar el primer fichero, así que el resultado es determinista.
    run_one_job(api_only_client)
    detalle = api_only_client.get(f"/api/v1/ingestion-batches/{batch['id']}").json()
    assert detalle["batch"]["status"] == "cancelled"
    assert api_only_client.get(f"/api/v1/jobs/{batch['job_id']}").json()["status"] == "cancelled"
    # Lo copiado sigue copiado y la entrada queda pendiente de extraer: la fase que se canceló fue
    # la de lectura, no la de copia, así que su estado lo dice (`hashed`) y el informe cuadra.
    assert detalle["entries"][0]["status"] == ItemStatus.HASHED.value
    assert detalle["batch"]["counters"]["copied"] == 1
    assert detalle["report"]["balanced"] is True
    # Nada se extrajo: la cancelación corta antes de leer el primer documento.
    assert (
        api_only_client.get(f"/api/v1/ingestion-batches/{batch['id']}/representations").json() == []
    )


# --- procedencia por entrada y URL sin secretos (regresión S03) -------------------------------

CONTENIDO_COMPARTIDO = b"Material sintetico que entra por tres vias distintas."


def _descargador_con_token(url: str, *, destination: Path, limits: object) -> FetchResult:
    """Descarga simulada que acaba en una URL con token en la cadena de consulta."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(CONTENIDO_COMPARTIDO)
    return FetchResult(
        initial_url=url,
        final_url="https://ejemplo.test/material.txt?token=secreto-de-prueba&id=42",
        redirects=(),
        status=200,
        content_type="text/plain",
        size_bytes=destination.stat().st_size,
        path=destination,
    )


def _descargador_con_ejecutable(contenido: bytes, content_type: str = "text/plain") -> Any:
    """Descargador simulado que sirve un ejecutable con nombre y tipo inocentes."""

    def descarga(url: str, *, destination: Path, limits: object) -> FetchResult:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(contenido)
        return FetchResult(
            initial_url=url,
            final_url="https://ejemplo.test/apuntes.txt",
            redirects=(),
            status=200,
            content_type=content_type,
            size_bytes=destination.stat().st_size,
            path=destination,
        )

    return descarga


@pytest.mark.parametrize(
    ("contenido", "etiqueta"),
    [
        (b"MZ" + b"\x00" * 64, "PE"),
        (b"\x7fELF" + b"\x00" * 64, "ELF"),
    ],
)
def test_un_ejecutable_descargado_por_url_no_llega_al_almacen(
    api_only_client: TestClient,
    migrated_settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
    contenido: bytes,
    etiqueta: str,
) -> None:
    """Un PE o un ELF servido por URL con nombre inocente se rechaza antes de crear nada.

    La comprobación de contenido solo estaba en la subida: por URL el binario se creaba como lote y
    se copiaba al almacén. Ahora la política es común a todas las vías.
    """
    intake = api_only_client.app.state.intake_service
    monkeypatch.setattr(intake, "_fetcher", _descargador_con_ejecutable(contenido))
    antes_artefactos = len(list((migrated_settings.data_paths.artifacts / "sha256").rglob("*")))
    antes_lotes = len(api_only_client.get("/api/v1/ingestion-batches").json())

    respuesta = api_only_client.post(
        "/api/v1/ingestion-batches/url",
        json={"url": "https://ejemplo.test/apuntes.txt"},
        headers=ALLOWED_ORIGIN,
    )

    assert respuesta.status_code == 400, f"{etiqueta}: {respuesta.text}"
    assert respuesta.json()["code"] == "unsafe_content"
    assert (
        len(list((migrated_settings.data_paths.artifacts / "sha256").rglob("*")))
        == antes_artefactos
    )
    assert len(api_only_client.get("/api/v1/ingestion-batches").json()) == antes_lotes
    assert list((migrated_settings.data_paths.root / "tmp").glob("*.part")) == []


def test_un_ejecutable_de_la_carpeta_no_llega_al_almacen(
    api_only_client: TestClient, migrated_settings: Settings, tmp_path: Path
) -> None:
    """Un `.exe` renombrado a `.txt` en la carpeta de origen no se copia al almacén.

    El inventario lo ve como texto (su nombre lo dice) y antes la copia lo guardaba: la política de
    contenido se comprueba también al copiar desde carpeta, y el resultado queda declarado como
    incidencia en el lote.
    """
    material = tmp_path / "material"
    material.mkdir()
    (material / "apuntes.txt").write_bytes(b"MZ" + b"\x00" * 64)
    (material / "tema-01.txt").write_text("Material sintetico del tema uno.", encoding="utf-8")

    inventario = api_only_client.post(
        "/api/v1/inventories", json={"source_path": str(material)}, headers=ALLOWED_ORIGIN
    ).json()
    batch = api_only_client.post(
        f"/api/v1/inventories/{inventario['batch']['id']}/confirm-import", headers=ALLOWED_ORIGIN
    ).json()

    # El pipeline son dos trabajos: copiar y, después, extraer.
    run_one_job(api_only_client)
    run_one_job(api_only_client)

    detalle = api_only_client.get(f"/api/v1/ingestion-batches/{batch['id']}").json()
    estados = {entry["relative_path"]: entry["status"] for entry in detalle["entries"]}
    assert estados["tema-01.txt"] == ItemStatus.EXTRACTED.value
    assert estados["apuntes.txt"] == ItemStatus.FAILED.value
    incidencias = {issue["code"] for issue in detalle["issues"]}
    assert "omitted_executable" in incidencias
    # La incidencia dice por qué, y el binario no está en el almacén: solo se copió el de texto.
    assert any("no se admite" in issue["safe_message"] for issue in detalle["issues"])
    assert detalle["report"]["artifacts_total"] == 1


def _servicio_de_entradas(migrated_settings: Settings) -> tuple[Any, Any, Any]:
    """Servicio de entradas con descargador inyectado, sobre la base de datos de la prueba."""
    engine = build_engine(migrated_settings.data_paths.database)
    sesiones = build_session_factory(engine)
    paths = migrated_settings.data_paths
    repositorio = SqlAlchemyIngestionRepository(sesiones)
    servicio = IntakeService(
        repository=repositorio,
        jobs=SqlAlchemyJobRepository(sesiones),
        store=ArtifactStore(paths),
        clock=SystemClock(),
        data_root=paths.root,
        max_file_bytes=migrated_settings.max_file_bytes,
        url_limits=url_limits_from_settings(
            timeout_seconds=5, max_bytes=1024 * 1024, max_redirects=3
        ),
        url_fetcher=_descargador_con_token,
    )
    return servicio, repositorio, engine


@dataclass(frozen=True, slots=True)
class ExtraccionDePrueba:
    """Lo que devuelve una extracción de prueba, ya materializado (sin base de datos abierta)."""

    por_lote: dict[str, tuple[RepresentationView, ...]]
    origenes_por_lote: dict[str, tuple[str | None, ...]]


def _extraer(migrated_settings: Settings, batch_ids: list[str]) -> ExtraccionDePrueba:
    """Extrae esos lotes con los servicios reales (sin worker) y devuelve datos ya leídos."""
    from opofuente.application.extraction_service import ExtractionService
    from opofuente.domain.jobs import JobType
    from opofuente.infrastructure.extraction_repository import SqlAlchemyExtractionRepository
    from opofuente.infrastructure.extractors import ExtractorRegistry
    from opofuente.infrastructure.representation_store import RepresentationStore

    engine = build_engine(migrated_settings.data_paths.database)
    try:
        sesiones = build_session_factory(engine)
        paths = migrated_settings.data_paths
        extraccion = ExtractionService(
            repository=SqlAlchemyExtractionRepository(sesiones),
            ingestions=SqlAlchemyIngestionRepository(sesiones),
            store=ArtifactStore(paths),
            representations=RepresentationStore(paths),
            registry=ExtractorRegistry(migrated_settings),
            clock=SystemClock(),
            data_root=paths.root,
            max_member_bytes=migrated_settings.max_file_bytes,
        )
        jobs = SqlAlchemyJobRepository(sesiones)
        for batch_id in batch_ids:
            for job in jobs.list(limit=200):
                if (
                    job.job_type is JobType.EXTRACT_ARTIFACT
                    and job.payload.get("batch_id") == batch_id
                ):
                    extraccion.run_extraction_job(FakeExecution(job))
                    break

        por_lote = {
            batch_id: extraccion.representations_for_batch(batch_id) for batch_id in batch_ids
        }
        return ExtraccionDePrueba(
            por_lote=por_lote,
            origenes_por_lote={
                batch_id: tuple(source.origin_type for view in vistas for source in view.sources)
                for batch_id, vistas in por_lote.items()
            },
        )
    finally:
        engine.dispose()


def test_los_mismos_bytes_por_tres_vias_conservan_la_procedencia_de_cada_entrada(
    migrated_settings: Settings,
) -> None:
    """Un contenido que entra como fichero, como texto pegado y como URL guarda su procedencia.

    Antes la procedencia de una representación se sacaba uniendo la entrada con todos los orígenes
    del artefacto, así que podía atribuir a una entrada el origen de otra. Y como la lista de un
    lote unía por artefacto, un lote enseñaba representaciones producidas en otro (el mismo
    contenido entrado como fichero deja `native_text` y como texto pegado, `plain_text`).
    """
    servicio, repositorio, engine = _servicio_de_entradas(migrated_settings)
    try:
        temporal = migrated_settings.data_paths.root / "tmp" / "fichero.txt"
        temporal.parent.mkdir(parents=True, exist_ok=True)
        temporal.write_bytes(CONTENIDO_COMPARTIDO)

        lote_fichero = servicio.ingest_files([IntakeFile(name="material.txt", path=temporal)])
        lote_pegado = servicio.ingest_paste(CONTENIDO_COMPARTIDO.decode())
        lote_url = servicio.ingest_url("https://ejemplo.test/material.txt?token=secreto-de-prueba")

        # Los tres lotes comparten artefacto (mismo contenido) y cada entrada tiene su origen.
        origenes = {}
        for lote in (lote_fichero, lote_pegado, lote_url):
            entrada = repositorio.list_entries(lote.id, limit=10, offset=0).entries[0]
            origenes[lote.id] = (entrada.origin_type, entrada.origin_display)
        assert {tipo for tipo, _ in origenes.values()} == {"file", "paste", "url"}
        ids = (lote_fichero.id, lote_pegado.id, lote_url.id)
    finally:
        engine.dispose()

    extraccion = _extraer(migrated_settings, list(ids))

    # Cada lote enseña **su** procedencia: la del texto que salió de sus entradas.
    assert extraccion.origenes_por_lote[lote_fichero.id] == ("file",)
    assert extraccion.origenes_por_lote[lote_pegado.id] == ("paste",)
    assert extraccion.origenes_por_lote[lote_url.id] == ("url",)
    # Y hay una representación por lote, no una lista con el texto de los demás: el mismo contenido
    # entrado como fichero y como texto pegado son representaciones distintas (`native_text` frente
    # a `plain_text`) y cada lote ve solo la suya.
    assert all(len(vistas) == 1 for vistas in extraccion.por_lote.values())
    tipos = {
        batch_id: {view.kind for view in vistas} for batch_id, vistas in extraccion.por_lote.items()
    }
    assert tipos[lote_fichero.id] == {"native_text"}
    assert tipos[lote_pegado.id] == {"plain_text"}


@pytest.mark.parametrize("via", ["ficheros", "pegado", "url"])
def test_un_fallo_de_almacen_no_deja_un_lote_colgado(
    migrated_settings: Settings, monkeypatch: pytest.MonkeyPatch, via: str
) -> None:
    """Si falla la copia al almacén, el lote queda `failed` con su motivo, nunca en `queued`.

    Un lote en `queued` sin entradas ni trabajos es un lote huérfano: nadie lo va a cerrar y el
    usuario lo ve colgado para siempre. La comprobación se hace en las tres vías de entrada.
    """
    servicio, repositorio, engine = _servicio_de_entradas(migrated_settings)
    try:

        def falla(*args: object, **kwargs: object) -> None:
            raise OSError("el disco dijo que no")

        monkeypatch.setattr(servicio._store, "store_file", falla)

        if via == "ficheros":
            preparados = servicio.stage_uploads(
                [("notas.txt", io.BytesIO(b"material sintetico de la prueba"))]
            )
            with pytest.raises(OSError):
                servicio.ingest_files(preparados)
        elif via == "pegado":
            with pytest.raises(OSError):
                servicio.ingest_paste("Material sintetico pegado para la prueba del fallo.")
        else:
            monkeypatch.setattr(servicio, "_fetcher", _descargador_con_token)
            with pytest.raises(OSError):
                servicio.ingest_url("https://ejemplo.test/material.txt")

        lotes = repositorio.list_batches(limit=10, offset=0)
        assert len(lotes) == 1, "solo el lote que falló"
        assert lotes[0].status == BatchStatus.FAILED.value, "nunca se queda en queued"
        assert lotes[0].error_summary, "el motivo queda declarado"
        assert lotes[0].counters["total"] == 0, "no hay entradas a medias"
        assert list((migrated_settings.data_paths.root / "tmp").glob("*.part")) == []
    finally:
        engine.dispose()


def test_un_fallo_al_escribir_el_temporal_pegado_no_deja_lote(
    migrated_settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    """El temporal del texto pegado se escribe **antes** de crear el lote.

    Antes se creaba el lote y después se escribía el temporal, así que un fallo de disco dejaba un
    lote en `queued` sin entradas ni trabajo que lo cerrara: nadie lo iba a cerrar y el usuario lo
    veía colgado. Ahora, si la escritura falla, no hay ni lote ni temporal.
    """
    servicio, repositorio, engine = _servicio_de_entradas(migrated_settings)
    try:
        original = Path.write_text

        def rompe(self: Path, *args: object, **kwargs: object) -> int:
            if self.suffix == ".part":
                raise OSError("el disco dijo que no")
            return original(self, *args, **kwargs)  # type: ignore[arg-type]

        monkeypatch.setattr(Path, "write_text", rompe)

        with pytest.raises(OSError):
            servicio.ingest_paste("Material sintetico pegado para la prueba del fallo.")

        assert repositorio.list_batches(limit=10, offset=0) == (), "no puede quedar ningún lote"
        assert list((migrated_settings.data_paths.root / "tmp").glob("*.part")) == []
    finally:
        engine.dispose()


def test_reintentar_un_lote_de_url_funciona_sin_carpeta_de_origen(
    api_only_client: TestClient,
    migrated_settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """El tercer lote sin carpeta de origen: lo descargado de una URL también se reintenta.

    La descarga se simula (nada de salir a la red en la suite) y la extracción se fuerza a fallar
    para poder reintentar la fase correcta.
    """
    from opofuente.domain.jobs import JobType
    from opofuente.infrastructure.job_repository import SqlAlchemyJobRepository
    from opofuente_testing.jobs import failed_extraction, jobs_for_batch

    app: Any = api_only_client.app
    intake = app.state.intake_service
    monkeypatch.setattr(intake, "_fetcher", _descargador_con_token)

    batch = api_only_client.post(
        "/api/v1/ingestion-batches/url",
        json={"url": "https://ejemplo.test/material.txt"},
        headers=ALLOWED_ORIGIN,
    ).json()
    assert batch["status"] == "queued"

    extraccion = app.state.extraction_service
    registro = extraccion._registry
    original = registro.extract
    monkeypatch.setattr(registro, "extract", lambda *args, **kwargs: failed_extraction())

    run_one_job(api_only_client)
    fallado = api_only_client.get(f"/api/v1/ingestion-batches/{batch['id']}").json()
    assert fallado["batch"]["status"] == "failed"

    monkeypatch.setattr(registro, "extract", original)
    respuesta = api_only_client.post(
        f"/api/v1/ingestion-batches/{batch['id']}/retry", headers=ALLOWED_ORIGIN
    )
    assert respuesta.status_code == 200, (
        f"el reintento de un lote descargado no puede pedir carpeta de origen: {respuesta.text}"
    )

    engine = build_engine(migrated_settings.data_paths.database)
    try:
        cola = SqlAlchemyJobRepository(build_session_factory(engine))
        # Se vuelve a extraer: ningún trabajo de copia y dos de extracción.
        assert jobs_for_batch(cola, batch["id"], JobType.INGEST_BATCH) == []
        assert len(jobs_for_batch(cola, batch["id"], JobType.EXTRACT_ARTIFACT)) == 2
    finally:
        engine.dispose()

    run_one_job(api_only_client)
    final = api_only_client.get(f"/api/v1/ingestion-batches/{batch['id']}").json()
    assert final["batch"]["status"] == "succeeded"
    assert final["entries"][0]["status"] == ItemStatus.EXTRACTED.value


def test_una_url_con_token_no_publica_el_token(migrated_settings: Settings) -> None:
    """La URL final se guarda y se muestra sin cadena de consulta: el token no sale de la app.

    La cadena de consulta puede llevar tokens de sesión o identificadores privados. Se guardaba tal
    cual como procedencia, y de ahí pasaba a la API y a la interfaz.
    """
    servicio, repositorio, engine = _servicio_de_entradas(migrated_settings)
    try:
        lote = servicio.ingest_url("https://ejemplo.test/material.txt?token=secreto-de-prueba")

        assert lote.source_path_display == "https://ejemplo.test/material.txt"
        entrada = repositorio.list_entries(lote.id, limit=10, offset=0).entries[0]
        assert entrada.origin_display == "https://ejemplo.test/material.txt"
        lote_id = lote.id
    finally:
        engine.dispose()

    extraccion = _extraer(migrated_settings, [lote_id])
    assert extraccion.origenes_por_lote[lote_id] == ("url",)
    for source in extraccion.por_lote[lote_id][0].sources:
        assert "secreto-de-prueba" not in source.location
        assert "token" not in source.location


# --- URL ------------------------------------------------------------------------------------


def test_una_url_interna_se_rechaza_sin_descargar(api_only_client: TestClient) -> None:
    """SSRF de verdad: la propia API local es loopback, así que su URL no se descarga."""
    respuesta = api_only_client.post(
        "/api/v1/ingestion-batches/url",
        json={"url": "http://127.0.0.1:8765/api/v1/capabilities"},
        headers=ALLOWED_ORIGIN,
    )
    assert respuesta.status_code == 400
    cuerpo = respuesta.json()
    assert cuerpo["code"] == "url_rejected"
    assert "interna" in cuerpo["detail"]


def test_una_url_con_esquema_no_admitido_se_rechaza(api_only_client: TestClient) -> None:
    respuesta = api_only_client.post(
        "/api/v1/ingestion-batches/url",
        json={"url": "file:///C:/Windows/win.ini"},
        headers=ALLOWED_ORIGIN,
    )
    assert respuesta.status_code == 400
    assert respuesta.json()["code"] == "url_rejected"


def test_una_descarga_correcta_crea_material(migrated_settings: Settings, tmp_path: Path) -> None:
    """Con un descargador inyectado: lo descargado se guarda, se extrae y se puede leer."""
    engine = build_engine(migrated_settings.data_paths.database)
    try:
        sesiones = build_session_factory(engine)
        repositorio = SqlAlchemyIngestionRepository(sesiones)
        jobs = SqlAlchemyJobRepository(sesiones)
        paths = migrated_settings.data_paths

        def descargador(url: str, *, destination: Path, limits: object) -> FetchResult:
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(b"Normativa sintetica descargada para la prueba.")
            return FetchResult(
                initial_url=url,
                final_url="https://ejemplo.test/normativa.txt",
                redirects=("https://ejemplo.test/inicio",),
                status=200,
                content_type="text/plain",
                size_bytes=destination.stat().st_size,
                path=destination,
            )

        servicio = IntakeService(
            repository=repositorio,
            jobs=jobs,
            store=ArtifactStore(paths),
            clock=SystemClock(),
            data_root=paths.root,
            max_file_bytes=migrated_settings.max_file_bytes,
            url_limits=url_limits_from_settings(
                timeout_seconds=5, max_bytes=1024 * 1024, max_redirects=3
            ),
            url_fetcher=descargador,
        )

        batch = servicio.ingest_url("https://ejemplo.test/normativa")

        assert batch.counters["copied"] == 1
        # La cadena de consulta no se publica y el nombre sale de la URL final.
        assert batch.source_path_display == "https://ejemplo.test/normativa"
        assert repositorio.source_root_of(batch.id) is None
        assert repositorio.pending_extraction_count(batch.id) == 1
        entrada = repositorio.list_entries(batch.id, limit=10, offset=0).entries[0]
        assert entrada.relative_path == "normativa.txt"
        assert entrada.status == ItemStatus.HASHED.value
    finally:
        engine.dispose()


# --- lector ---------------------------------------------------------------------------------


def test_el_lector_dice_lo_que_falta_cuando_pide_mas_texto(
    api_only_client: TestClient, tmp_path: Path
) -> None:
    pdf = build_text_pdf(tmp_path / "grande.pdf", pages=3)
    batch = api_only_client.post(
        "/api/v1/ingestion-batches/files",
        files=[("files", ("grande.pdf", pdf.read_bytes(), "application/pdf"))],
        headers=ALLOWED_ORIGIN,
    ).json()
    run_one_job(api_only_client)

    representacion = _representations(api_only_client, batch["id"])[0]
    primero = api_only_client.get(
        f"/api/v1/representations/{representacion['id']}/text", params={"offset": 0, "limit": 50}
    ).json()
    assert primero["truncated"] is True
    assert len(primero["text"]) == 50
    assert primero["total_chars"] == representacion["char_count"]

    segundo = api_only_client.get(
        f"/api/v1/representations/{representacion['id']}/text", params={"offset": 50, "limit": 50}
    ).json()
    assert segundo["offset"] == 50
    assert segundo["text"] != primero["text"]


def test_una_representacion_inexistente_devuelve_404(api_only_client: TestClient) -> None:
    assert api_only_client.get("/api/v1/representations/no-existe").status_code == 404
    assert api_only_client.get("/api/v1/representations/no-existe/text").status_code == 404


def test_el_lote_inexistente_no_tiene_representaciones(api_only_client: TestClient) -> None:
    respuesta = api_only_client.get("/api/v1/ingestion-batches/no-existe/representations")
    assert respuesta.status_code == 404


def test_la_guarda_de_url_rechaza_y_no_crea_lote(api_only_client: TestClient) -> None:
    """Una URL rechazada no deja un lote vacío por el camino."""
    antes = len(api_only_client.get("/api/v1/ingestion-batches").json())

    respuesta = api_only_client.post(
        "/api/v1/ingestion-batches/url",
        json={"url": "http://10.0.0.1/privado.pdf"},
        headers=ALLOWED_ORIGIN,
    )

    assert respuesta.status_code == 400
    assert respuesta.json()["code"] == "url_rejected"
    assert len(api_only_client.get("/api/v1/ingestion-batches").json()) == antes
