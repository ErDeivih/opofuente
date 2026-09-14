"""Pruebas de integración del inventario en lectura.

Regla que se comprueba siempre: **el inventario no toca el material del usuario**. Se verifica
comparando la lista de ficheros y sus fechas antes y después.
"""

from __future__ import annotations

import os
import subprocess
from datetime import UTC, datetime
from pathlib import Path

import pytest

from opofuente.domain.errors import InvalidSourceError
from opofuente.domain.ingestion import IssueCode, ItemStatus
from opofuente.infrastructure.filesystem_inventory import FilesystemInventory

MAX_FILE_BYTES = 1024 * 1024


@pytest.fixture
def inventory() -> FilesystemInventory:
    return FilesystemInventory(max_file_bytes=MAX_FILE_BYTES, max_entries=1000)


def snapshot(root: Path) -> dict[str, tuple[int, float]]:
    """Qué hay y cuándo se tocó por última vez: sirve para demostrar que nada cambió."""
    result: dict[str, tuple[int, float]] = {}
    for path in sorted(root.rglob("*")):
        if path.is_file():
            stat = path.stat()
            result[path.relative_to(root).as_posix()] = (stat.st_size, stat.st_mtime)
    return result


def build_material(root: Path) -> None:
    (root / "apuntes").mkdir(parents=True)
    (root / "preguntas").mkdir(parents=True)
    (root / "node_modules").mkdir(parents=True)
    (root / "apuntes" / "ley.md").write_text("ley 39/2015", encoding="utf-8")
    (root / "apuntes" / "ley-copia.md").write_text("ley 39/2015", encoding="utf-8")
    (root / "apuntes" / "ley-revision.md").write_text("ley 40/2015", encoding="utf-8")
    (root / "preguntas" / "banco.csv").write_text("pregunta;opcion\n1;a", encoding="utf-8")
    (root / "preguntas" / "vacio.txt").write_text("", encoding="utf-8")
    (root / ".oculto.txt").write_text("no", encoding="utf-8")
    (root / "~$temporal.docx").write_text("no", encoding="utf-8")
    (root / "instalador.exe").write_text("no", encoding="utf-8")
    (root / "presentacion.pptx").write_text("no", encoding="utf-8")
    (root / "node_modules" / "paquete.js").write_text("no", encoding="utf-8")


def test_inventario_cuenta_y_clasifica(inventory: FilesystemInventory, tmp_path: Path) -> None:
    root = tmp_path / "material"
    build_material(root)
    antes = snapshot(root)

    result = inventory.scan(root)

    assert result.counters.inventoried == 5
    assert result.counters.omitted_hidden == 1
    assert result.counters.omitted_temporary == 1
    assert result.counters.omitted_executable == 1
    assert result.counters.omitted_unsupported == 1
    assert result.counters.omitted_directory == 1
    # `directories` cuenta los directorios recorridos; el omitido se cuenta aparte.
    assert result.counters.directories == 2
    assert result.counters.discovered == len(result.entries)
    assert result.counters.total_bytes == sum(entry.size_bytes for entry in result.included)

    incluidos = {entry.relative_path for entry in result.included}
    assert incluidos == {
        "apuntes/ley-copia.md",
        "apuntes/ley-revision.md",
        "apuntes/ley.md",
        "preguntas/banco.csv",
        "preguntas/vacio.txt",
    }
    assert result.formats[".md"] == 3
    assert result.formats[".csv"] == 1
    assert snapshot(root) == antes


def test_el_inventario_no_copia_nada(inventory: FilesystemInventory, tmp_path: Path) -> None:
    root = tmp_path / "material"
    build_material(root)
    inventario = inventory.scan(root)
    assert inventario.counters.total_bytes > 0
    # Ninguna entrada apunta a un artefacto: el inventario no ha copiado nada.
    assert all(entry.included for entry in inventario.included)
    assert not any(entry.relative_path.startswith("data/") for entry in inventario.entries)


def test_fichero_vacio_se_inventaria_con_aviso(
    inventory: FilesystemInventory, tmp_path: Path
) -> None:
    root = tmp_path / "material"
    root.mkdir()
    (root / "vacio.txt").write_text("", encoding="utf-8")

    result = inventory.scan(root)

    assert [entry.relative_path for entry in result.included] == ["vacio.txt"]
    assert result.issues[0].code is IssueCode.EMPTY_FILE
    assert result.issues[0].severity.value == "info"


def test_fichero_demasiado_grande_se_omite(inventory: FilesystemInventory, tmp_path: Path) -> None:
    root = tmp_path / "material"
    root.mkdir()
    (root / "grande.txt").write_text("x" * (MAX_FILE_BYTES + 1), encoding="utf-8")

    result = inventory.scan(root)

    assert result.counters.inventoried == 0
    assert result.entries[0].status is ItemStatus.OMITTED
    assert result.entries[0].issue is not None
    assert result.entries[0].issue.code is IssueCode.SIZE_LIMIT


def _make_escape_link(root: Path, target: Path) -> Path | None:
    """Crea un enlace de directorio que sale de la raíz; None si el sistema no lo permite."""
    link = root / "enlace-fuera"
    if os.name == "nt":
        result = subprocess.run(  # noqa: S603 - comando fijo, sin entrada del usuario
            ["cmd", "/c", "mklink", "/J", str(link), str(target)],  # noqa: S607
            capture_output=True,
            text=True,
            check=False,
        )
        return link if result.returncode == 0 and link.exists() else None
    os.symlink(target, link, target_is_directory=True)
    return link


def test_enlace_que_sale_de_la_raiz_se_registra_y_no_se_sigue(
    inventory: FilesystemInventory, tmp_path: Path
) -> None:
    root = tmp_path / "material"
    root.mkdir()
    (root / "propio.txt").write_text("mío", encoding="utf-8")
    fuera = tmp_path / "fuera"
    fuera.mkdir()
    (fuera / "secreto.txt").write_text("no debe aparecer", encoding="utf-8")

    link = _make_escape_link(root, fuera)
    if link is None:  # pragma: no cover - depende de privilegios del sistema
        pytest.fail("no se pudo crear el enlace de directorio para probar la salida de raíz")

    result = inventory.scan(root)

    rutas = {entry.relative_path for entry in result.entries}
    # El enlace no es material: no aparece como entrada, pero sí como incidencia del informe.
    assert rutas == {"propio.txt"}
    assert result.counters.linked_outside_root == 1
    assert any(issue.code is IssueCode.LINK_ESCAPES_ROOT for issue in result.issues)
    assert all("secreto" not in issue.safe_message for issue in result.issues)


def test_el_directorio_de_datos_se_omite(inventory: FilesystemInventory, tmp_path: Path) -> None:
    data_root = tmp_path / "data"
    (data_root / "artifacts").mkdir(parents=True)
    (data_root / "artifacts" / "algo.bin").write_text("guardado", encoding="utf-8")
    root = tmp_path / "material"
    root.mkdir()
    (root / "propio.txt").write_text("mío", encoding="utf-8")

    scoped = FilesystemInventory(
        max_file_bytes=MAX_FILE_BYTES, max_entries=100, forbidden_roots=(data_root,)
    )
    result = scoped.scan(tmp_path)

    incluidas = {entry.relative_path for entry in result.included}
    assert incluidas == {"material/propio.txt"}


def test_origen_inexistente_o_que_no_es_carpeta(
    inventory: FilesystemInventory, tmp_path: Path
) -> None:
    from opofuente.application.ingestion_service import IngestionService

    class _Noop:
        def store_file(self, source: Path):  # pragma: no cover - no se usa
            raise AssertionError("no debe copiarse nada")

        def path_for(self, digest):  # pragma: no cover - no se usa
            raise AssertionError("no debe copiarse nada")

        def exists(self, digest) -> bool:  # pragma: no cover - no se usa
            return False

    fichero = tmp_path / "archivo.txt"
    fichero.write_text("x", encoding="utf-8")
    service = IngestionService(
        repository=_Noop(),  # type: ignore[arg-type]
        jobs=_Noop(),  # type: ignore[arg-type]
        store=_Noop(),  # type: ignore[arg-type]
        scanner=inventory,
        clock=_Clock(),
        data_root=tmp_path / "data",
        max_entries=100,
    )

    for ruta in ("", "  ", "ruta/relativa", str(tmp_path / "no-existe"), str(fichero)):
        with pytest.raises(InvalidSourceError):
            service.create_inventory(ruta)

    with pytest.raises(InvalidSourceError):
        service.create_inventory(str(tmp_path / "data"))


class _Clock:
    def now(self) -> datetime:
        return datetime(2026, 9, 14, tzinfo=UTC)
