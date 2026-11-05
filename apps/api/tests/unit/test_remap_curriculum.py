"""Fixture y respaldo de la re-atribución del banco (B-003), sin base de datos."""

from __future__ import annotations

from pathlib import Path

import pytest

from opofuente.config import Settings
from opofuente.domain.errors import InvariantViolationError
from opofuente.infrastructure.equivalence_fixture_loader import load_equivalences
from opofuente.tools.remap_curriculum import backup_database

#: Los 33 temas del programa publicado del TAI y los 40 del temario común.
TEMAS_TAI = (
    *(f"I.{numero}" for numero in range(1, 10)),
    *(f"II.{numero}" for numero in range(1, 6)),
    *(f"III.{numero}" for numero in range(1, 10)),
    *(f"IV.{numero}" for numero in range(1, 11)),
)
TEMAS_COMUN = (
    *(f"I.{numero}" for numero in range(1, 13)),
    *(f"II.{numero}" for numero in range(13, 18)),
    *(f"III.{numero}" for numero in range(18, 27)),
    *(f"IV.{numero}" for numero in range(27, 34)),
    *(f"V.{numero}" for numero in range(34, 41)),
)


def test_el_fixture_cubre_los_33_temas_publicados_y_apunta_a_temas_del_comun() -> None:
    fixture = load_equivalences()

    assert fixture.source_version_code == "tai-age-2025-programa-v1"
    assert fixture.target_version_code == "informatica-c1-v1"
    assert {fila.source_path for fila in fixture.rows} == set(TEMAS_TAI)
    assert all(fila.target_path in TEMAS_COMUN for fila in fixture.rows)
    assert all(fila.evidence_note.strip() for fila in fixture.rows)


def test_lo_dudoso_es_la_minoria_y_lo_claro_lo_aceptado() -> None:
    fixture = load_equivalences()
    por_estado: dict[str, int] = {}
    for fila in fixture.rows:
        por_estado[fila.status] = por_estado.get(fila.status, 0) + 1

    assert por_estado == {"accepted": 20, "proposed": 13}
    assert all(fila.confidence >= 0.75 for fila in fixture.rows if fila.status == "accepted"), (
        "lo aceptado tiene confianza suficiente"
    )

    relaciones = {fila.relation for fila in fixture.rows}
    assert relaciones <= {"equivalent", "subset", "superset", "partial"}


def test_la_copia_previa_guarda_la_base_y_sus_auxiliares(tmp_path: Path) -> None:
    settings = Settings(data_dir=tmp_path / "datos", _env_file=None)
    settings.data_paths.ensure_directories()
    base = settings.data_paths.database
    base.write_bytes(b"sqlite-de-prueba" * 100)
    Path(f"{base}-wal").write_bytes(b"wal-de-prueba")

    destino = backup_database(settings)

    assert (destino / base.name).read_bytes() == base.read_bytes()
    assert (destino / f"{base.name}-wal").read_bytes() == b"wal-de-prueba"
    assert destino.parent == settings.data_paths.backups


def test_no_se_hace_copia_si_no_hay_base(tmp_path: Path) -> None:
    settings = Settings(data_dir=tmp_path / "datos", _env_file=None)
    settings.data_paths.ensure_directories()

    with pytest.raises(InvariantViolationError, match="no existe la base"):
        backup_database(settings)
