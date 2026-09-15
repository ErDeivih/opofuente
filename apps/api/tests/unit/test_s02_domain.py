"""Pruebas unitarias de rutas seguras, artefactos y estado de la ingestión."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from opofuente.domain.artifacts import Sha256, media_type_for
from opofuente.domain.errors import InvariantViolationError
from opofuente.domain.ingestion import (
    BatchStatus,
    DiscoveredEntry,
    ImportCounters,
    ItemStatus,
    balanced_counters,
    can_transition_batch,
    can_transition_item,
    is_terminal_item,
    manifest_hash,
    require_item_transition,
)
from opofuente.domain.jobs import (
    JobStatus,
    is_cancellable,
    is_terminal,
    lease_expiry,
    retry_delay_seconds,
    should_retry,
)
from opofuente.infrastructure.safe_paths import (
    PathOutsideRootError,
    abbreviate,
    is_within,
    relative_display,
    resolve_within,
    safe_display_name,
)

SHA_A = "a" * 64
SHA_B = "b" * 64


# --------------------------------------------------------------------- rutas seguras


def test_ruta_dentro_de_la_raiz(tmp_path: Path) -> None:
    root = tmp_path / "raiz"
    (root / "sub").mkdir(parents=True)
    assert is_within(root, root / "sub" / "f.txt")


def test_ruta_fuera_de_la_raiz_se_rechaza(tmp_path: Path) -> None:
    root = tmp_path / "raiz"
    root.mkdir()
    with pytest.raises(PathOutsideRootError):
        resolve_within(root, tmp_path / "otro.txt")
    assert not is_within(root, tmp_path / "otro.txt")


def test_ruta_con_punto_punto_que_escapa_se_rechaza(tmp_path: Path) -> None:
    root = tmp_path / "raiz"
    (root / "sub").mkdir(parents=True)
    with pytest.raises(PathOutsideRootError):
        resolve_within(root, root / "sub" / ".." / ".." / "fuera.txt")


def test_nombre_para_mostrar_elimina_separadores_y_control() -> None:
    assert safe_display_name("../../etc/passwd") == "_.._etc_passwd"
    assert safe_display_name("a\\b.txt") == "a_b.txt"
    assert safe_display_name("con.txt") == "_con.txt"
    assert safe_display_name("   ") == "sin-nombre"
    assert safe_display_name("normal.pdf") == "normal.pdf"
    assert "\x00" not in safe_display_name("a\x00b.pdf")


def test_ruta_relativa_para_mostrar(tmp_path: Path) -> None:
    root = tmp_path / "raiz"
    (root / "sub").mkdir(parents=True)
    file = root / "sub" / "f.txt"
    file.write_text("x", encoding="utf-8")
    assert relative_display(root, file) == "sub/f.txt"
    assert relative_display(root, tmp_path / "fuera.txt") == "<fuera-de-raiz>/fuera.txt"


def test_ruta_abreviada_no_expone_toda_la_ruta(tmp_path: Path) -> None:
    root = tmp_path / "uno" / "dos" / "material"
    root.mkdir(parents=True)
    assert abbreviate(root) == "…/dos/material"


# --------------------------------------------------------------------- artefactos


def test_sha256_valida_el_formato() -> None:
    assert str(Sha256(SHA_A)) == SHA_A
    with pytest.raises(InvariantViolationError):
        Sha256("no-es-un-hash")
    with pytest.raises(InvariantViolationError):
        Sha256(SHA_A.upper())


def test_clave_de_almacen_por_hash() -> None:
    digest = Sha256("ab" + "c" * 62)
    assert digest.storage_key == f"sha256/ab/cc/{digest.value}"


def test_tipo_mime_por_extension() -> None:
    assert media_type_for("ley.pdf") == "application/pdf"
    assert media_type_for("notas.MD") == "text/markdown"
    assert media_type_for("raro.xyz") == "application/octet-stream"


# --------------------------------------------------------------------- ingestión


def _entry(path: str, size: int, status: ItemStatus = ItemStatus.INVENTORIED) -> DiscoveredEntry:
    return DiscoveredEntry(
        relative_path=path,
        original_name=Path(path).name,
        size_bytes=size,
        mtime=datetime(2026, 9, 14, tzinfo=UTC),
        media_type="text/plain",
        status=status,
    )


def test_transiciones_de_entrada() -> None:
    assert can_transition_item(ItemStatus.INVENTORIED, ItemStatus.COPIED)
    assert can_transition_item(ItemStatus.COPIED, ItemStatus.HASHED)
    assert not can_transition_item(ItemStatus.HASHED, ItemStatus.INVENTORIED)
    assert not can_transition_item(ItemStatus.OMITTED, ItemStatus.COPIED)
    assert is_terminal_item(ItemStatus.OMITTED)
    with pytest.raises(InvariantViolationError):
        require_item_transition(ItemStatus.HASHED, ItemStatus.CANCELLED)


def test_desde_s03_una_entrada_copiada_se_extrae_o_se_conserva_sin_extraer() -> None:
    """`hashed` deja de ser terminal en S03: el pipeline sigue (04_INGESTION §4 y §5).

    Lo copiado pasa a `extracted` (con texto) o a `unsupported_preserved` (sin extractor, DEBT-008).
    Ninguna de las dos vuelve atrás: si el fichero cambia, es otra entrada de otro lote.
    """
    assert can_transition_item(ItemStatus.HASHED, ItemStatus.EXTRACTED)
    assert can_transition_item(ItemStatus.HASHED, ItemStatus.UNSUPPORTED_PRESERVED)
    assert not can_transition_item(ItemStatus.HASHED, ItemStatus.INVENTORIED)
    assert is_terminal_item(ItemStatus.EXTRACTED)
    assert is_terminal_item(ItemStatus.UNSUPPORTED_PRESERVED)


def test_transiciones_de_lote() -> None:
    assert can_transition_batch(BatchStatus.QUEUED, BatchStatus.RUNNING)
    assert can_transition_batch(BatchStatus.RUNNING, BatchStatus.CANCELLED)
    assert can_transition_batch(BatchStatus.FAILED, BatchStatus.QUEUED)
    assert not can_transition_batch(BatchStatus.CANCELLED, BatchStatus.RUNNING)


def test_los_contadores_del_informe_cuadran() -> None:
    counters = ImportCounters(total=3, copied=1, source_changed=1, failed=1)
    assert counters.accounted == 3
    assert counters.balanced is True
    counters.cancelled += 1
    assert counters.balanced is False


def test_las_entradas_pendientes_cuentan_en_el_informe() -> None:
    """Regresión: `pending` forma parte de la ecuación.

    Un lote reintentado queda con entradas por copiar. Si no se declaran, el informe no cuadra y la
    API devolvía `balanced: false` en un estado perfectamente normal.
    """
    counters = ImportCounters(total=3, copied=1, pending=2)
    assert counters.accounted == 3
    assert counters.balanced is True
    assert counters.to_dict()["pending"] == 2

    counters.pending -= 1
    assert counters.balanced is False


def test_la_regla_del_cuadre_es_la_misma_para_los_contadores_servidos() -> None:
    """La API sirve diccionarios: la regla tiene que ser la misma que la del dominio."""
    assert balanced_counters({"total": 3, "copied": 1, "pending": 2}) is True
    assert balanced_counters({"total": 3, "copied": 1, "pending": 1, "failed": 1}) is True
    assert balanced_counters({"total": 3, "copied": 1}) is False
    # Un contador sin `total` no se puede dar por bueno.
    assert balanced_counters({"copied": 0}) is False


def test_la_huella_del_inventario_cambia_con_el_tamano() -> None:
    primera = (_entry("a.txt", 10), _entry("b.txt", 20))
    misma = (_entry("a.txt", 10), _entry("b.txt", 20))
    distinta = (_entry("a.txt", 11), _entry("b.txt", 20))
    assert manifest_hash(primera) == manifest_hash(misma)
    assert manifest_hash(primera) != manifest_hash(distinta)


def test_la_huella_ignora_las_entradas_omitidas() -> None:
    incluidas = (_entry("a.txt", 10),)
    con_omitida = (_entry("a.txt", 10), _entry("b.txt", 0, ItemStatus.OMITTED))
    assert manifest_hash(incluidas) == manifest_hash(con_omitida)


# --------------------------------------------------------------------- trabajos


def test_lease_minimo() -> None:
    now = datetime(2026, 9, 14, tzinfo=UTC)
    assert lease_expiry(now, 30) > now
    with pytest.raises(InvariantViolationError):
        lease_expiry(now, 1)


def test_estados_de_trabajo() -> None:
    assert is_terminal(JobStatus.SUCCEEDED)
    assert not is_terminal(JobStatus.RUNNING)
    assert is_cancellable(JobStatus.QUEUED)
    assert not is_cancellable(JobStatus.CANCELLED)


def test_reintentos_acotados() -> None:
    assert should_retry(attempts=1, max_attempts=3)
    assert not should_retry(attempts=3, max_attempts=3)
    assert retry_delay_seconds(1) == 2
    assert retry_delay_seconds(9) == 30
    with pytest.raises(InvariantViolationError):
        should_retry(attempts=0, max_attempts=0)
