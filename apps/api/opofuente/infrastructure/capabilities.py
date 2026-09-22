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
from opofuente.domain.providers import sends_content_off_device
from opofuente.domain.system import Capability, CapabilityStatus
from opofuente.infrastructure.worker_liveness import WorkerLiveness


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
            )
        if not path.is_file():
            return Capability(
                id="ocr",
                label="OCR (Tesseract)",
                status=CapabilityStatus.UNAVAILABLE,
                detail="La ruta configurada en OPOFUENTE_TESSERACT_PATH no existe en este equipo.",
            )
        return Capability(
            id="ocr",
            label="OCR (Tesseract)",
            status=CapabilityStatus.CONFIGURED_UNVERIFIED,
            detail=(
                "Binario presente, pero la aplicación no lo llama: el OCR no está implementado y "
                "una imagen se queda pendiente con su aviso. Declararlo evita creer que un PDF "
                "escaneado se está leyendo."
            ),
        )

    def _llm(self) -> Capability:
        provider = self._settings.llm_provider
        if provider == "disabled":
            return Capability(
                id="llm",
                label="Modelo de lenguaje",
                status=CapabilityStatus.DISABLED,
                detail=(
                    "Sin proveedor: las respuestas se componen del propio corpus (extractivas) y "
                    "citan cada afirmación. Un modelo de lenguaje llegaría con la deuda DEBT-014."
                ),
            )
        # El destino se calcula **para este proveedor**, no con un booleano que mezclaba los dos
        # (DEBT-001): decir «los fragmentos saldrían del equipo» por el endpoint de embeddings sería
        # acusar al modelo de lenguaje de lo que hace otro.
        destino = self._settings.llm_destination
        extra = (
            " Los fragmentos que se le mandaran saldrían de este equipo."
            if sends_content_off_device(destino)
            else f" El endpoint configurado {destino.reason}."
        )
        return Capability(
            id="llm",
            label="Modelo de lenguaje",
            status=CapabilityStatus.CONFIGURED_UNVERIFIED,
            detail=(
                f"Proveedor {provider} configurado con modelo "
                f"{self._settings.llm_model or 'sin especificar'}, pero OpoFuente no lo usa para "
                f"responder: hoy responde con el corpus (extractivo).{extra}"
            ),
        )

    def _embeddings(self) -> Capability:
        provider = self._settings.embedding_provider
        if provider == "disabled":
            return Capability(
                id="embeddings",
                label="Embeddings",
                status=CapabilityStatus.DISABLED,
                detail=(
                    "Sin proveedor de embeddings decidido: la búsqueda es literal (FTS5) y cada "
                    "respuesta lo declara como degradación (DEBT-014)."
                ),
            )
        # Y aquí el suyo, que es lo que la deuda pedía: el bloque de embeddings informa de **su**
        # destino, no del que tenga el modelo de lenguaje.
        destino = self._settings.embeddings_destination
        extra = (
            " El texto que se mandara saldría de este equipo."
            if sends_content_off_device(destino)
            else f" El endpoint configurado {destino.reason}."
        )
        return Capability(
            id="embeddings",
            label="Embeddings",
            status=CapabilityStatus.CONFIGURED_UNVERIFIED,
            detail=(
                f"Proveedor {provider} configurado, pero sin índice vectorial construido ni "
                f"benchmark en español: la búsqueda sigue siendo literal (DEBT-014).{extra}"
            ),
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


class VectorIndexCapabilityProvider:
    """El índice vectorial: no existe, y se dice por qué en lugar de prometer un slice.

    S09 construyó la búsqueda **literal**: sin proveedor de embeddings decidido (el modelo se fija
    por ADR tras un benchmark en español) no hay vectores que indexar, y descargar un modelo al
    arrancar sin avisar está prohibido. Declararlo `planned` con un slice sería prometer una fecha
    que nadie ha decidido.
    """

    def provide(self) -> tuple[Capability, ...]:
        return (
            Capability(
                id="vector_index",
                label="Índice vectorial local",
                status=CapabilityStatus.UNAVAILABLE,
                detail=(
                    "Sin proveedor de embeddings no hay vectores que indexar: la búsqueda del "
                    "corpus es literal (FTS5) sobre el texto extraído (DEBT-014)."
                ),
            ),
        )


class SqliteCapabilityProvider:
    """Comprueba de verdad si el SQLite de este equipo soporta FTS5 y si el índice existe.

    La capacidad no se declara operativa por soportar FTS5: hace falta que el índice léxico de S09
    esté creado en esta base. Un SQLite con FTS5 y sin migrar no puede buscar nada, y eso hay que
    decirlo antes de que alguien busque y no encuentre.
    """

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def provide(self) -> tuple[Capability, ...]:
        try:
            with self._engine.connect() as connection:
                connection.execute(text("CREATE VIRTUAL TABLE temp.fts5_probe USING fts5(sample)"))
                connection.execute(text("DROP TABLE temp.fts5_probe"))
                creado = connection.execute(
                    text(
                        "SELECT count(*) FROM sqlite_master "
                        "WHERE name = 'evidence_fts' AND type = 'table'"
                    )
                ).scalar_one()
        except SQLAlchemyError as exc:
            return (
                Capability(
                    id="fts5",
                    label="Búsqueda literal (FTS5)",
                    status=CapabilityStatus.UNAVAILABLE,
                    detail=(
                        "El SQLite de este equipo no soporta FTS5 "
                        f"({type(exc).__name__}); la búsqueda literal no puede funcionar."
                    ),
                ),
            )
        if not creado:
            return (
                Capability(
                    id="fts5",
                    label="Búsqueda literal (FTS5)",
                    status=CapabilityStatus.UNAVAILABLE,
                    detail=(
                        "Este equipo soporta FTS5, pero el índice léxico no está creado en esta "
                        "base: la migración 0018 no se ha aplicado, así que no se puede buscar."
                    ),
                ),
            )
        return (
            Capability(
                id="fts5",
                label="Búsqueda literal (FTS5)",
                status=CapabilityStatus.ENABLED,
                detail=(
                    "Índice léxico comprobado: tabla externa sobre evidence_spans, ordenada por "
                    "bm25, con los disparadores que la mantienen al día; se rehace cuando haga "
                    "falta sin salir de SQLite."
                ),
            ),
        )
