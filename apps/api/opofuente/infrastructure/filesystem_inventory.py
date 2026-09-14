"""Inventario en lectura de una carpeta: qué hay, qué se omite y por qué.

No copia, no mueve y no borra: solo recorre y describe (04_INGESTION-AND-CLASSIFICATION §2).

Política de omisión por defecto, siempre reflejada en el informe:

- ficheros ocultos (los que empiezan por punto) y basura del sistema (`Thumbs.db`, `desktop.ini`);
- temporales de Office (`~$…`);
- ejecutables y bibliotecas (`.exe`, `.dll`, `.msi`, `.bat`, `.cmd`, `.com`, `.scr`, `.ps1`,
  `.jar`);
- formatos que el MVP conserva pero todavía no extrae (`.epub`, `.pptx`, …);
- directorios que no aportan material (`.git`, `node_modules`, `__pycache__`, `.venv`, cachés);
- enlaces (symlink/junction) cuyo destino sale de la raíz seleccionada;
- ficheros por encima del límite configurado;
- y el propio directorio de datos de OpoFuente, para no importar el almacén sobre sí mismo.

Los directorios no son entradas del inventario: se recorren y se cuentan aparte.
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path

from opofuente.domain.artifacts import media_type_for
from opofuente.domain.ingestion import (
    DiscoveredEntry,
    ImportIssue,
    InventoryCounters,
    IssueCode,
    IssueSeverity,
    ItemStatus,
    ScanResult,
)
from opofuente.infrastructure.safe_paths import is_within, relative_display, safe_display_name

IGNORED_DIRECTORIES = frozenset(
    {
        ".git",
        ".hg",
        ".svn",
        ".venv",
        "venv",
        "node_modules",
        "__pycache__",
        ".mypy_cache",
        ".ruff_cache",
        ".pytest_cache",
        ".idea",
        ".vscode",
        ".cache",
        "System Volume Information",
        "$RECYCLE.BIN",
    }
)

UNSUPPORTED_EXTENSIONS = frozenset({".epub", ".pptx", ".ppt", ".xlsx", ".xls", ".odt", ".ods"})
EXECUTABLE_EXTENSIONS = frozenset(
    {".exe", ".dll", ".msi", ".bat", ".cmd", ".com", ".scr", ".ps1", ".jar", ".so", ".dylib"}
)
JUNK_FILE_NAMES = frozenset({"thumbs.db", "desktop.ini", ".ds_store"})

_OMISSION_COUNTERS: dict[IssueCode, str] = {
    IssueCode.OMITTED_HIDDEN: "omitted_hidden",
    IssueCode.OMITTED_TEMPORARY: "omitted_temporary",
    IssueCode.OMITTED_EXECUTABLE: "omitted_executable",
    IssueCode.OMITTED_DIRECTORY: "omitted_directory",
    IssueCode.OMITTED_UNSUPPORTED: "omitted_unsupported",
    IssueCode.LINK_ESCAPES_ROOT: "linked_outside_root",
    IssueCode.OMITTED_BY_POLICY: "omitted_by_policy",
}

_OMISSION_MESSAGES: dict[IssueCode, str] = {
    IssueCode.OMITTED_HIDDEN: "Omitido: fichero oculto.",
    IssueCode.OMITTED_TEMPORARY: "Omitido: fichero temporal de Office.",
    IssueCode.OMITTED_EXECUTABLE: "Omitido: ejecutable o biblioteca.",
    IssueCode.OMITTED_DIRECTORY: "Omitido: directorio que no aporta material.",
    IssueCode.OMITTED_UNSUPPORTED: "Omitido: formato no soportado todavía.",
    IssueCode.OMITTED_BY_POLICY: "Omitido: excluido por política.",
    IssueCode.LINK_ESCAPES_ROOT: (
        "Omitido: enlace cuyo destino queda fuera de la carpeta seleccionada."
    ),
    IssueCode.UNREADABLE: "No se pudo leer: permisos o fichero bloqueado.",
}


class FilesystemInventory:
    """Implementa el puerto `InventoryScanner` recorriendo el sistema de archivos."""

    def __init__(
        self,
        *,
        max_file_bytes: int,
        max_entries: int,
        forbidden_roots: tuple[Path, ...] = (),
        ignored_directories: frozenset[str] = IGNORED_DIRECTORIES,
        ignored_extensions: frozenset[str] = UNSUPPORTED_EXTENSIONS,
    ) -> None:
        self._max_file_bytes = max_file_bytes
        self._max_entries = max_entries
        self._forbidden_roots = tuple(root.resolve(strict=False) for root in forbidden_roots)
        self._ignored_directories = ignored_directories
        self._ignored_extensions = ignored_extensions

    def scan(self, root: Path) -> ScanResult:
        resolved_root = root.resolve(strict=False)
        counters = InventoryCounters()
        issues: list[ImportIssue] = []
        entries: list[DiscoveredEntry] = []

        for entry in self._walk(resolved_root, counters, issues):
            if len(entries) >= self._max_entries:
                issues.append(
                    ImportIssue(
                        code=IssueCode.SIZE_LIMIT,
                        severity=IssueSeverity.WARNING,
                        safe_message=(
                            f"Se alcanzó el límite de {self._max_entries} entradas: "
                            "el inventario se detiene aquí."
                        ),
                    )
                )
                break
            entries.append(entry)

        entries.sort(key=lambda item: item.relative_path)
        counters.discovered = len(entries)
        counters.total_bytes = sum(entry.size_bytes for entry in entries if entry.included)
        return ScanResult(entries=tuple(entries), counters=counters, issues=tuple(issues))

    def _walk(
        self,
        root: Path,
        counters: InventoryCounters,
        issues: list[ImportIssue],
    ) -> Iterator[DiscoveredEntry]:
        stack: list[Path] = [root]
        while stack:
            current = stack.pop()
            try:
                children = sorted(current.iterdir(), key=lambda item: item.name.lower())
            except OSError:
                counters.unreadable += 1
                issues.append(
                    ImportIssue(
                        code=IssueCode.UNREADABLE,
                        severity=IssueSeverity.WARNING,
                        safe_message=_OMISSION_MESSAGES[IssueCode.UNREADABLE],
                        relative_path=relative_display(root, current),
                    )
                )
                continue

            for child in children:
                if child.is_dir():
                    issue = self._classify_directory(root, child)
                    if issue is None:
                        counters.directories += 1
                        stack.append(child)
                        continue
                    counter = _OMISSION_COUNTERS.get(issue.code, "omitted_directory")
                    setattr(counters, counter, getattr(counters, counter) + 1)
                    issues.append(issue)
                    continue

                entry = self._classify_file(root, child)
                if entry.issue is not None:
                    issues.append(entry.issue)
                if entry.included:
                    counters.inventoried += 1
                else:
                    file_counter: str | None = (
                        _OMISSION_COUNTERS.get(entry.issue.code)
                        if entry.issue is not None
                        else None
                    )
                    if file_counter is not None:
                        setattr(counters, file_counter, getattr(counters, file_counter) + 1)
                    elif entry.status is ItemStatus.FAILED:
                        counters.unreadable += 1
                yield entry

    def _classify_directory(self, root: Path, path: Path) -> ImportIssue | None:
        """None si el directorio se puede recorrer; un motivo si se omite."""
        if not self._is_traversable(root, path):
            return ImportIssue(
                code=IssueCode.LINK_ESCAPES_ROOT,
                severity=IssueSeverity.WARNING,
                safe_message=_OMISSION_MESSAGES[IssueCode.LINK_ESCAPES_ROOT],
                relative_path=relative_display(root, path),
            )
        if path.name.lower() in self._ignored_directories:
            return ImportIssue(
                code=IssueCode.OMITTED_DIRECTORY,
                severity=IssueSeverity.INFO,
                safe_message=_OMISSION_MESSAGES[IssueCode.OMITTED_DIRECTORY],
                relative_path=relative_display(root, path),
            )
        if any(is_within(forbidden, path) for forbidden in self._forbidden_roots):
            return ImportIssue(
                code=IssueCode.OMITTED_BY_POLICY,
                severity=IssueSeverity.INFO,
                safe_message="Omitido: es el directorio de datos de OpoFuente o está dentro de él.",
                relative_path=relative_display(root, path),
            )
        return None

    def _is_traversable(self, root: Path, path: Path) -> bool:
        """Un enlace solo se sigue si su destino sigue dentro de la raíz seleccionada."""
        if not is_within(root, path):
            return False
        if path.is_symlink() or self._is_reparse_point(path):
            return is_within(root, path.resolve(strict=False))
        return True

    def _classify_file(self, root: Path, path: Path) -> DiscoveredEntry:
        name = path.name
        lowered = name.lower()
        relative = relative_display(root, path)

        def omitted(
            code: IssueCode, severity: IssueSeverity, status: ItemStatus
        ) -> DiscoveredEntry:
            return DiscoveredEntry(
                relative_path=relative,
                original_name=safe_display_name(name),
                size_bytes=0,
                mtime=None,
                media_type="",
                status=status,
                issue=ImportIssue(
                    code=code,
                    severity=severity,
                    safe_message=_OMISSION_MESSAGES[code],
                    relative_path=relative,
                ),
            )

        if not self._is_traversable(root, path):
            return omitted(IssueCode.LINK_ESCAPES_ROOT, IssueSeverity.WARNING, ItemStatus.OMITTED)
        if lowered in JUNK_FILE_NAMES or name.startswith("."):
            return omitted(IssueCode.OMITTED_HIDDEN, IssueSeverity.INFO, ItemStatus.OMITTED)
        if name.startswith("~$"):
            return omitted(IssueCode.OMITTED_TEMPORARY, IssueSeverity.INFO, ItemStatus.OMITTED)

        suffix = path.suffix.lower()
        if suffix in EXECUTABLE_EXTENSIONS:
            return omitted(IssueCode.OMITTED_EXECUTABLE, IssueSeverity.WARNING, ItemStatus.OMITTED)
        if suffix in self._ignored_extensions:
            return omitted(IssueCode.OMITTED_UNSUPPORTED, IssueSeverity.INFO, ItemStatus.OMITTED)

        try:
            stat = path.stat()
        except OSError:
            return omitted(IssueCode.UNREADABLE, IssueSeverity.ERROR, ItemStatus.FAILED)

        mtime = datetime.fromtimestamp(stat.st_mtime, tz=UTC)
        if stat.st_size == 0:
            return DiscoveredEntry(
                relative_path=relative,
                original_name=safe_display_name(name),
                size_bytes=0,
                mtime=mtime,
                media_type=media_type_for(name),
                status=ItemStatus.INVENTORIED,
                issue=ImportIssue(
                    code=IssueCode.EMPTY_FILE,
                    severity=IssueSeverity.INFO,
                    safe_message="El fichero está vacío.",
                    relative_path=relative,
                ),
            )
        if stat.st_size > self._max_file_bytes:
            return DiscoveredEntry(
                relative_path=relative,
                original_name=safe_display_name(name),
                size_bytes=stat.st_size,
                mtime=mtime,
                media_type=media_type_for(name),
                status=ItemStatus.OMITTED,
                issue=ImportIssue(
                    code=IssueCode.SIZE_LIMIT,
                    severity=IssueSeverity.WARNING,
                    safe_message=(
                        f"El fichero supera el límite de {self._max_file_bytes} bytes: no se copia."
                    ),
                    relative_path=relative,
                    details={"size_bytes": stat.st_size},
                ),
            )

        return DiscoveredEntry(
            relative_path=relative,
            original_name=safe_display_name(name),
            size_bytes=stat.st_size,
            mtime=mtime,
            media_type=media_type_for(name),
            status=ItemStatus.INVENTORIED,
        )

    @staticmethod
    def _is_reparse_point(path: Path) -> bool:
        """En Windows una junction es un punto de reanálisis y `is_symlink()` puede no verlo."""
        if os.name != "nt":  # pragma: no cover - depende del sistema
            return False
        try:
            attributes = int(path.lstat().st_file_attributes)
        except (OSError, AttributeError):  # pragma: no cover
            return False
        return bool(attributes & 0x400)
