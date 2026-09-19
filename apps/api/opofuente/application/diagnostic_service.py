"""Diagnóstico sanitizado: lo que se puede pegar en una incidencia sin filtrar nada (09_SEC §12).

El contrato pide «exportar versiones, capacidades y estado», y lo que **no** puede salir es lo de
siempre: contenido, claves, prompts, respuestas personales y rutas completas. Aquí se cumple con
tres decisiones explícitas:

1. **las rutas se abrevian** (`abbreviate`), así que se ve la forma del árbol de datos sin publicar
   el nombre del usuario ni de su disco;
2. **el final del registro pasa por el mismo saneado de los logs** (`sanitize_line`): si una línea
   llevara una clave o una ruta absoluta, no llega al diagnóstico;
3. **lo que no se puede medir se dice**: un registro ausente o una tabla que no existe aparecen como
   tal, no como cero.
"""

from __future__ import annotations

import platform
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from opofuente.domain.system import CapabilitiesReport, CheckResult, ReadinessReport
from opofuente.infrastructure.logging_sanitizer import sanitize_line
from opofuente.infrastructure.safe_paths import abbreviate


@dataclass(frozen=True, slots=True)
class DiagnosticReport:
    """Todo lo que lleva el diagnóstico, ya saneado: sin secretos, contenido ni rutas enteras."""

    generated_at: str
    version: str
    schema_revision: str
    python_version: str
    platform: str
    host: str
    port: int
    log_level: str
    data_dir_display: str
    database_file_display: str
    disk_total_bytes: int
    disk_free_bytes: int
    counts: dict[str, int]
    capabilities: CapabilitiesReport
    readiness: ReadinessReport
    log_tail: tuple[str, ...]
    note: str


class DiagnosticService:
    """Compone el diagnóstico a partir de lo que ya saben otros servicios.

    No consulta nada por su cuenta salvo el final del registro: el resto se lo dan hecho, para que
    **haya una sola verdad** sobre capacidades, salud y recuentos.
    """

    def __init__(
        self,
        *,
        version: str,
        host: str,
        port: int,
        log_level: str,
        data_dir: Path,
        database_file: Path,
        disk_usage: Callable[[], tuple[int, int]],
        schema_revision: Callable[[], str],
        counts: Callable[[], dict[str, int]],
        capabilities: Callable[[], CapabilitiesReport],
        readiness: Callable[[], ReadinessReport],
        clock: Callable[[], datetime],
        log_file: Path | None = None,
        log_tail_lines: int = 50,
    ) -> None:
        self._version = version
        self._host = host
        self._port = port
        self._log_level = log_level
        self._data_dir = data_dir
        self._database_file = database_file
        self._disk_usage = disk_usage
        self._schema_revision = schema_revision
        self._counts = counts
        self._capabilities = capabilities
        self._readiness = readiness
        self._clock = clock
        self._log_file = log_file
        self._log_tail_lines = log_tail_lines

    def report(self) -> DiagnosticReport:
        total, libre = self._disk_usage()
        return DiagnosticReport(
            generated_at=self._clock().isoformat(),
            version=self._version,
            schema_revision=self._schema_revision(),
            python_version=platform.python_version(),
            platform=_platform_label(),
            host=self._host,
            port=self._port,
            log_level=self._log_level,
            data_dir_display=abbreviate(self._data_dir),
            database_file_display=abbreviate(self._database_file),
            disk_total_bytes=total,
            disk_free_bytes=libre,
            counts=self._counts(),
            capabilities=self._capabilities(),
            readiness=self._readiness(),
            log_tail=self._tail(),
            note=(
                "Diagnóstico sanitizado: no incluye contenido, claves ni rutas completas. Las "
                "rutas van abreviadas y el registro pasa por el mismo saneado que los logs."
            ),
        )

    def _tail(self) -> tuple[str, ...]:
        """Últimas líneas del registro, saneadas una a una. Sin registro, se dice que no hay."""
        if self._log_file is None or not self._log_file.is_file():
            return ()
        try:
            lineas = self._log_file.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            return ()
        return tuple(sanitize_line(linea) for linea in lineas[-self._log_tail_lines :])

    def as_text(self, report: DiagnosticReport | None = None) -> str:
        """El diagnóstico en texto plano, para pegarlo en una incidencia.

        Se genera aquí y no en la interfaz a propósito: el mismo texto que se enseña en pantalla es
        el que se puede copiar, así que no hay dos versiones del diagnóstico con datos distintos.
        """
        informe = report or self.report()
        lineas: list[str] = [
            "OpoFuente — diagnóstico sanitizado",
            f"generado: {informe.generated_at}",
            f"versión: {informe.version}",
            f"esquema: {informe.schema_revision}",
            f"python: {informe.python_version}",
            f"plataforma: {informe.platform}",
            f"servidor: {informe.host}:{informe.port}",
            f"nivel de registro: {informe.log_level}",
            f"datos: {informe.data_dir_display}",
            f"base: {informe.database_file_display}",
            f"disco: {informe.disk_free_bytes} libres de {informe.disk_total_bytes}",
            "",
            "capacidades:",
        ]
        for capacidad in informe.capabilities.capabilities:
            lineas.append(f"- {capacidad.id} [{capacidad.status.value}]: {capacidad.detail}")
        lineas.append("")
        lineas.append("salud:")
        for check in informe.readiness.checks:
            lineas.append(f"- {check.name} [{check.status.value}]: {check.detail}")
        lineas.append("")
        lineas.append("recuentos:")
        for clave, valor in sorted(informe.counts.items()):
            lineas.append(f"- {clave}: {valor}")
        lineas.append("")
        lineas.append(f"últimas {len(informe.log_tail)} líneas del registro (saneadas):")
        lineas.extend(f"  {linea}" for linea in informe.log_tail)
        lineas.append("")
        lineas.append(informe.note)
        return "\n".join(lineas)


def _platform_label() -> str:
    """Plataforma sin más detalle del necesario: sistema, versión y arquitectura de Python."""
    ancho = 64 if sys.maxsize > 2**32 else 32
    return f"{platform.system()} {platform.release()} (python {ancho} bits)"


def checks_summary(checks: Sequence[CheckResult]) -> str:
    """Resumen de una línea de la salud, para la cabecera del diagnóstico."""
    fallidos = [check.name for check in checks if check.status.value != "ok"]
    if not fallidos:
        return "todas las comprobaciones en orden"
    return "con fallos en: " + ", ".join(fallidos)


__all__ = ["DiagnosticReport", "DiagnosticService", "checks_summary"]
