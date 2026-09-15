"""Pruebas de integración de las entradas directas de S03 y del lector (04_INGESTION §2 y §5).

Cubre lo que el usuario puede hacer además de elegir una carpeta: subir ficheros, pegar texto y
pegar una URL. La URL se prueba con un descargador inyectado (nada de salir a la red en la suite) y,
por separado, se comprueba que una URL interna se rechaza de verdad.

Todo el material es sintético y vive en directorios temporales.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from support import run_one_job
from synthetic_documents import build_csv, build_text_pdf, build_zip

from opofuente.application.intake_service import IntakeService
from opofuente.config import Settings
from opofuente.domain.errors import InvalidSourceError
from opofuente.domain.ingestion import ItemStatus
from opofuente.infrastructure.artifact_store import ArtifactStore
from opofuente.infrastructure.clock import SystemClock
from opofuente.infrastructure.db import build_engine, build_session_factory
from opofuente.infrastructure.ingestion_repository import SqlAlchemyIngestionRepository
from opofuente.infrastructure.job_repository import SqlAlchemyJobRepository
from opofuente.infrastructure.url_guard import FetchResult, url_limits_from_settings

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
