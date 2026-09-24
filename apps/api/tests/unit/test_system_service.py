"""Pruebas unitarias del informe de capacidades y de la resiliencia de las sondas."""

from __future__ import annotations

from pathlib import Path

from opofuente.application.system_service import SystemService
from opofuente.config import Settings
from opofuente.domain.system import Capability, CapabilityStatus, CheckResult, CheckStatus
from opofuente.infrastructure.capabilities import (
    ConfigurationCapabilityProvider,
    IngestionCapabilityProvider,
    VectorIndexCapabilityProvider,
)
from opofuente.infrastructure.ocr import CompletedRun, TesseractOcr
from opofuente.infrastructure.worker_liveness import WorkerLiveness


def _report(settings: Settings) -> dict[str, Capability]:
    service = SystemService(
        version="0.0.0-test",
        probes=(),
        capability_providers=(
            ConfigurationCapabilityProvider(settings),
            VectorIndexCapabilityProvider(),
        ),
    )
    return {capability.id: capability for capability in service.capabilities().capabilities}


def _ingestion(settings: Settings, *, worker_running: bool) -> dict[str, Capability]:
    liveness = WorkerLiveness()
    if worker_running:
        liveness.mark_running()
    provider = IngestionCapabilityProvider(
        paths=settings.data_paths,
        settings=settings,
        liveness=liveness,
    )
    return {capability.id: capability for capability in provider.provide()}


def test_ocr_sin_configurar_esta_deshabilitado() -> None:
    capabilities = _report(Settings(tesseract_path=None, _env_file=None))
    assert capabilities["ocr"].status is CapabilityStatus.DISABLED


def test_ocr_con_ruta_inexistente_es_no_disponible(tmp_path: Path) -> None:
    settings = Settings(tesseract_path=tmp_path / "no-existe.exe", _env_file=None)
    service = SystemService(
        version="0.0.0-test",
        probes=(),
        capability_providers=(ConfigurationCapabilityProvider(settings),),
    )
    report = service.capabilities()
    ocr = report.by_id["ocr"]
    assert ocr.status is CapabilityStatus.UNAVAILABLE
    assert any(degradation.code == "ocr.unavailable" for degradation in report.degradations)


def _ocr_sondeable(tmp_path: Path, *, idiomas: tuple[str, ...]) -> TesseractOcr:
    """Adaptador con el binario falseado: la sonda de verdad, el proceso no."""
    binario = tmp_path / "tesseract-falso.exe"
    binario.write_bytes(b"ruta que existe")

    def runner(command, timeout):
        if "--version" in command:
            return CompletedRun(returncode=0, stdout="tesseract v5.4.0.20240606\n")
        if "--list-langs" in command:
            listado = "List of available languages (n):\n" + "\n".join(idiomas) + "\n"
            return CompletedRun(returncode=0, stdout=listado)
        return CompletedRun(returncode=0, stdout="")

    return TesseractOcr(binary=binario, languages="spa", runner=runner)


def _report_con_ocr(settings: Settings, adaptador: TesseractOcr):
    service = SystemService(
        version="0.0.0-test",
        probes=(),
        capability_providers=(ConfigurationCapabilityProvider(settings, ocr=adaptador),),
    )
    return service.capabilities()


def test_el_ocr_se_declara_operativo_solo_si_la_sonda_pasa(tmp_path: Path) -> None:
    settings = Settings(tesseract_path=tmp_path / "tesseract.exe", _env_file=None)

    report = _report_con_ocr(settings, _ocr_sondeable(tmp_path, idiomas=("eng", "osd", "spa")))

    ocr = report.by_id["ocr"]
    assert ocr.status is CapabilityStatus.ENABLED
    assert "v5.4.0.20240606" in ocr.detail, "la capacidad dice qué binario ha respondido"
    assert "spa" in ocr.detail
    assert not [item for item in report.degradations if item.code == "ocr.unavailable"]


def test_el_ocr_sin_el_idioma_pedido_no_se_declara_operativo(tmp_path: Path) -> None:
    """Un Tesseract instalado sin español no lee este material: no es «tener OCR»."""
    settings = Settings(tesseract_path=tmp_path / "tesseract.exe", _env_file=None)

    report = _report_con_ocr(settings, _ocr_sondeable(tmp_path, idiomas=("eng", "osd")))

    ocr = report.by_id["ocr"]
    assert ocr.status is CapabilityStatus.UNAVAILABLE
    assert ocr.status is not CapabilityStatus.CONFIGURED_UNVERIFIED
    assert "spa" in ocr.detail
    assert any(degradation.code == "ocr.unavailable" for degradation in report.degradations)


def test_llm_configurado_no_se_declara_operativo() -> None:
    settings = Settings(
        llm_provider="ollama",
        llm_base_url="http://127.0.0.1:11434",
        llm_model="modelo-local",
        _env_file=None,
    )
    llm = _report(settings)["llm"]
    assert llm.status is CapabilityStatus.CONFIGURED_UNVERIFIED
    assert llm.status is not CapabilityStatus.ENABLED
    # S09 no promete un modelo: las respuestas se componen del corpus y se dice.
    assert "extractivo" in llm.detail


def test_el_indice_vectorial_no_promete_un_slice() -> None:
    """Sin proveedor de embeddings no hay vectores: se declara no disponible, no «previsto»."""
    capabilities = _report(Settings(_env_file=None))
    vectorial = capabilities["vector_index"]
    assert vectorial.status is CapabilityStatus.UNAVAILABLE
    assert vectorial.planned_slice is None
    assert "DEBT-014" in vectorial.detail
    assert capabilities["embeddings"].status is CapabilityStatus.DISABLED
    assert capabilities["embeddings"].planned_slice is None


def test_almacen_de_artefactos_se_comprueba_escribiendo(tmp_path: Path) -> None:
    settings = Settings(data_dir=tmp_path / "datos", _env_file=None)
    store = _ingestion(settings, worker_running=False)["artifact_store"]
    assert store.status is CapabilityStatus.ENABLED
    # La comprobación es real: ha dejado el directorio de artefactos creado y vacío.
    assert settings.data_paths.artifacts.is_dir()
    assert list(settings.data_paths.artifacts.iterdir()) == []


def test_almacen_de_artefactos_no_escribible_se_declara_no_disponible(tmp_path: Path) -> None:
    settings = Settings(data_dir=tmp_path / "datos", _env_file=None)
    paths = settings.data_paths
    paths.artifacts.parent.mkdir(parents=True, exist_ok=True)
    # Un fichero donde debería ir el directorio: `mkdir` fallará y la capacidad debe decirlo.
    paths.artifacts.write_text("estorbando", encoding="utf-8")
    store = _ingestion(settings, worker_running=False)["artifact_store"]
    assert store.status is CapabilityStatus.UNAVAILABLE
    assert store.planned_slice is None


def test_worker_solo_se_declara_operativo_si_su_tarea_corre(tmp_path: Path) -> None:
    settings = Settings(data_dir=tmp_path / "datos", _env_file=None)
    parado = _ingestion(settings, worker_running=False)["worker"]
    trabajando = _ingestion(settings, worker_running=True)["worker"]
    assert parado.status is CapabilityStatus.UNAVAILABLE
    assert trabajando.status is CapabilityStatus.ENABLED


def test_worker_desactivado_por_configuracion(tmp_path: Path) -> None:
    settings = Settings(data_dir=tmp_path / "datos", worker_enabled=False, _env_file=None)
    worker = _ingestion(settings, worker_running=True)["worker"]
    assert worker.status is CapabilityStatus.DISABLED
    assert "OPOFUENTE_WORKER_ENABLED=false" in worker.detail


class _ProbeRota:
    """Sonda que falla de forma inesperada: no debe tumbar /health/ready."""

    name = "rota"

    def check(self) -> CheckResult:
        raise RuntimeError("fallo simulado de la sonda")


def test_sonda_que_lanza_no_aborta_el_informe() -> None:
    service = SystemService(
        version="0.0.0-test",
        probes=(_ProbeRota(),),
        capability_providers=(),
    )
    report = service.readiness()
    assert report.ready is False
    assert report.checks[0].status is CheckStatus.FAILED
    assert report.checks[0].detail == "comprobación interrumpida (RuntimeError)"
