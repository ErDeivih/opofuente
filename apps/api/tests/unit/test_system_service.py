"""Pruebas unitarias del informe de capacidades y de la resiliencia de las sondas."""

from __future__ import annotations

from pathlib import Path

from opofuente.application.system_service import SystemService
from opofuente.config import Settings
from opofuente.domain.system import CapabilityStatus, CheckResult, CheckStatus
from opofuente.infrastructure.capabilities import (
    ConfigurationCapabilityProvider,
    PlannedCapabilityProvider,
)


def _report(settings: Settings) -> dict[str, object]:
    service = SystemService(
        version="0.0.0-test",
        probes=(),
        capability_providers=(
            ConfigurationCapabilityProvider(settings),
            PlannedCapabilityProvider(),
        ),
    )
    return {capability.id: capability for capability in service.capabilities().capabilities}


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


def test_capacidades_futuras_declaran_su_slice() -> None:
    capabilities = _report(Settings(_env_file=None))
    for capability_id in ("artifact_store", "worker", "vector_index"):
        assert capabilities[capability_id].status is CapabilityStatus.PLANNED
        assert capabilities[capability_id].planned_slice is not None


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
