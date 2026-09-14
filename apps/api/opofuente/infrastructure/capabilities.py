"""Informe honesto de capacidades.

Regla dura: nada se declara operativo sin comprobarlo. Lo que todavía no existe se
declara `planned` con el slice en el que llega, y lo configurado pero no verificado se
declara `configured_unverified` (16_TRACEABILITY §4: prohibido el botón falso).
"""

from __future__ import annotations

import os
from uuid import uuid4

from sqlalchemy import Engine, text
from sqlalchemy.exc import SQLAlchemyError

from opofuente.config import DataPaths, Settings
from opofuente.domain.system import Capability, CapabilityStatus
from opofuente.infrastructure.worker_liveness import WorkerLiveness

_OCR_SLICE = "S03"
_SEARCH_SLICE = "S09"


class ConfigurationCapabilityProvider:
    """Capacidades que dependen solo de configuración (OCR, LLM, embeddings)."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def provide(self) -> tuple[Capability, ...]:
        return (self._ocr(), self._llm(), self._embeddings())

    def _ocr(self) -> Capability:
        path = self._settings.tesseract_path
        if path is None:
            return Capability(
                id="ocr",
                label="OCR (Tesseract)",
                status=CapabilityStatus.DISABLED,
                detail=(
                    "Sin ruta configurada. Las imágenes y los PDF escaneados quedan "
                    "pendientes sin bloquear la aplicación."
                ),
                planned_slice=_OCR_SLICE,
            )
        if not path.is_file():
            return Capability(
                id="ocr",
                label="OCR (Tesseract)",
                status=CapabilityStatus.UNAVAILABLE,
                detail="La ruta configurada en OPOFUENTE_TESSERACT_PATH no existe en este equipo.",
                planned_slice=_OCR_SLICE,
            )
        return Capability(
            id="ocr",
            label="OCR (Tesseract)",
            status=CapabilityStatus.CONFIGURED_UNVERIFIED,
            detail="Binario presente. La extracción OCR real se implementa en S03.",
            planned_slice=_OCR_SLICE,
        )

    def _llm(self) -> Capability:
        provider = self._settings.llm_provider
        if provider == "disabled":
            return Capability(
                id="llm",
                label="Modelo de lenguaje",
                status=CapabilityStatus.DISABLED,
                detail="Ninguna función básica depende de IA. Proveedor desactivado por defecto.",
                planned_slice="S09",
            )
        extra = (
            " Los fragmentos enviados saldrían del equipo."
            if self._settings.sends_data_off_device
            else " El modelo elegido es local."
        )
        return Capability(
            id="llm",
            label="Modelo de lenguaje",
            status=CapabilityStatus.CONFIGURED_UNVERIFIED,
            detail=(
                f"Proveedor {provider} configurado con modelo "
                f"{self._settings.llm_model or 'sin especificar'}. La verificación real "
                f"llega en S09; hasta entonces no se usa para responder.{extra}"
            ),
            planned_slice="S09",
        )

    def _embeddings(self) -> Capability:
        provider = self._settings.embedding_provider
        if provider == "disabled":
            return Capability(
                id="embeddings",
                label="Embeddings",
                status=CapabilityStatus.DISABLED,
                detail="Sin proveedor configurado. La búsqueda literal no depende de embeddings.",
                planned_slice=_SEARCH_SLICE,
            )
        return Capability(
            id="embeddings",
            label="Embeddings",
            status=CapabilityStatus.CONFIGURED_UNVERIFIED,
            detail=(
                f"Proveedor {provider} configurado. El benchmark en español y la indexación "
                "llegan en S09."
            ),
            planned_slice=_SEARCH_SLICE,
        )


class IngestionCapabilityProvider:
    """Almacén de originales y cola de trabajos (S02), comprobados de verdad.

    El almacén se declara operativo solo si el directorio de artefactos admite una escritura real.
    El worker se declara operativo solo si su tarea está corriendo en este proceso: la configuración
    por sí sola no basta (lo mismo que `configured_unverified` no equivale a funcionar).
    """

    def __init__(
        self,
        *,
        paths: DataPaths,
        settings: Settings,
        liveness: WorkerLiveness,
    ) -> None:
        self._paths = paths
        self._settings = settings
        self._liveness = liveness

    def provide(self) -> tuple[Capability, ...]:
        return (self._artifact_store(), self._worker())

    def _artifact_store(self) -> Capability:
        try:
            self._paths.ensure_directories()
            probe = self._paths.artifacts / f"write-probe-{os.getpid()}-{uuid4().hex}"
            probe.write_text("ok", encoding="utf-8")
            probe.unlink()
        except OSError as exc:
            return Capability(
                id="artifact_store",
                label="Almacén de originales por SHA-256",
                status=CapabilityStatus.UNAVAILABLE,
                detail=(
                    "El directorio de artefactos no admite escritura "
                    f"({type(exc).__name__}); no se puede importar nada."
                ),
            )
        return Capability(
            id="artifact_store",
            label="Almacén de originales por SHA-256",
            status=CapabilityStatus.ENABLED,
            detail=(
                "Copia inmutable por contenido en <datos>/artifacts/sha256/ab/cd/<hash>. "
                "Dos ficheros idénticos comparten un artefacto y conservan dos orígenes."
            ),
        )

    def _worker(self) -> Capability:
        label = "Cola de trabajos local"
        if not self._settings.worker_enabled:
            return Capability(
                id="worker",
                label=label,
                status=CapabilityStatus.DISABLED,
                detail=(
                    "OPOFUENTE_WORKER_ENABLED=false: los lotes se encolan y no avanzan hasta "
                    "reactivarlo."
                ),
            )
        if not self._liveness.running:
            return Capability(
                id="worker",
                label=label,
                status=CapabilityStatus.UNAVAILABLE,
                detail=(
                    "Ninguna tarea está trabajando la cola en este proceso. Si la base de datos "
                    "no estaba migrada al arrancar, el worker arranca al reiniciar."
                ),
            )
        return Capability(
            id="worker",
            label=label,
            status=CapabilityStatus.ENABLED,
            detail=(
                "Cola persistida en SQLite con lease, trabajada por este proceso; sin Redis ni "
                "Celery. Cerrar la pestaña no cancela el trabajo."
            ),
        )


class PlannedCapabilityProvider:
    """Capacidades que todavía no existen en el código, declaradas sin ambigüedad."""

    def provide(self) -> tuple[Capability, ...]:
        return (
            Capability(
                id="vector_index",
                label="Índice vectorial local",
                status=CapabilityStatus.PLANNED,
                detail="Qdrant local, reconstruible desde SQLite. Llega en S09.",
                planned_slice="S09",
            ),
        )


class SqliteCapabilityProvider:
    """Comprueba de verdad si el SQLite de este equipo soporta FTS5."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def provide(self) -> tuple[Capability, ...]:
        try:
            with self._engine.connect() as connection:
                connection.execute(text("CREATE VIRTUAL TABLE temp.fts5_probe USING fts5(sample)"))
                connection.execute(text("DROP TABLE temp.fts5_probe"))
        except SQLAlchemyError as exc:
            return (
                Capability(
                    id="fts5",
                    label="Búsqueda literal (FTS5)",
                    status=CapabilityStatus.UNAVAILABLE,
                    detail=(
                        "El SQLite de este equipo no soporta FTS5 "
                        f"({type(exc).__name__}); la búsqueda literal no podrá construirse."
                    ),
                    planned_slice=_SEARCH_SLICE,
                ),
            )
        return (
            Capability(
                id="fts5",
                label="Búsqueda literal (FTS5)",
                status=CapabilityStatus.PLANNED,
                detail=(
                    "El SQLite de este equipo soporta FTS5 (comprobado). El índice y las "
                    "consultas se implementan en S09."
                ),
                planned_slice=_SEARCH_SLICE,
            ),
        )
