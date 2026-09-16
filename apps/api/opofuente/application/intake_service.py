"""Entradas directas de S03: ficheros subidos, texto pegado y URL descargada (04_INGESTION §2).

Las tres crean un lote de importación con sus entradas **ya copiadas** (`hashed`), porque aquí
no hay nada que inventariar: el usuario ya eligió qué entra. A partir de ahí el lote sigue el
mismo camino que una carpeta: se encola la extracción y el worker lo cierra.

Reglas que se aplican en las tres:

- nada se guarda con el nombre que traía: el destino sale del hash y el nombre original queda como
  metadato saneado (`safe_display_name`);
- el texto pegado y lo descargado se escriben primero en `data/tmp` y después al almacén, con el
  mismo `store_file` (temporal + fsync + `os.replace`);
- cada entrada deja su origen con su tipo (`paste`, `url`, `file`), y en la URL se guardan la
  dirección final y la cadena de redirecciones que se siguieron;
- un fallo de descarga o un contenido rechazado por seguridad **no** crea el lote a medias: se
  propaga el error y el usuario ve el motivo.
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO
from uuid import uuid4

from opofuente.application.ports import Clock, IngestionRepository, JobQueue
from opofuente.application.read_models import BatchView
from opofuente.application.storage_policy import refusal_message
from opofuente.domain.artifacts import OriginType, media_type_for
from opofuente.domain.errors import (
    InvalidSourceError,
    NotFoundError,
    UnsafeContentError,
)
from opofuente.domain.ingestion import (
    BatchKind,
    BatchMode,
    BatchStatus,
    DiscoveredEntry,
    ItemStatus,
)
from opofuente.domain.jobs import JobType
from opofuente.infrastructure.artifact_store import ArtifactStore
from opofuente.infrastructure.safe_paths import resolve_within, safe_display_name
from opofuente.infrastructure.url_guard import (
    FetchResult,
    UrlLimits,
    display_url,
    fetch_url,
    url_limits_from_settings,
)

logger = logging.getLogger(__name__)

#: Cómo se descarga una URL. Se inyecta en las pruebas para no salir a la red.
UrlFetcher = Callable[..., FetchResult]


@dataclass(frozen=True, slots=True)
class IntakeFile:
    """Un fichero que entra subido: su nombre visible y los bytes ya escritos en un temporal."""

    name: str
    path: Path


class IntakeService:
    """Crea lotes a partir de ficheros subidos, texto pegado o una URL descargada."""

    def __init__(
        self,
        *,
        repository: IngestionRepository,
        jobs: JobQueue,
        store: ArtifactStore,
        clock: Clock,
        data_root: Path,
        max_file_bytes: int,
        max_paste_bytes: int | None = None,
        url_limits: UrlLimits | None = None,
        url_fetcher: UrlFetcher | None = None,
    ) -> None:
        self._repository = repository
        self.jobs = jobs
        self._store = store
        self._clock = clock
        self._data_root = data_root
        self._max_file_bytes = max_file_bytes
        # Un pegado no tiene por qué pasar por el límite de un fichero subido, pero tampoco puede
        # ser ilimitado: sin tope, pegar media biblioteca crearía un lote gigante de una vez.
        self._max_paste_bytes = max_paste_bytes or max_file_bytes
        self._url_limits = url_limits
        self._fetcher = url_fetcher or fetch_url

    # ------------------------------------------------------------------ ficheros

    def stage_uploads(self, uploads: Sequence[tuple[str, BinaryIO]]) -> tuple[IntakeFile, ...]:
        """Escribe lo subido en temporales, con tope de tamaño, y descarta lo que no se admite.

        Se hace en dos pasos a propósito: así la API no tiene que conocer rutas y el almacén recibe
        siempre un fichero del disco (que es como se calcula el hash por trozos).

        Cada temporal se borra si su escritura falla (límite superado, disco lleno, error de
        lectura): antes el temporal en curso no entraba en `preparados` hasta terminar de
        escribirse, así que un fichero demasiado grande dejaba su `.part` en `data/tmp`.
        """
        if not uploads:
            raise InvalidSourceError("no has seleccionado ningún fichero")
        preparados: list[IntakeFile] = []
        try:
            for nombre, flujo in uploads:
                temporal = self._temp_path("subida")
                try:
                    self._write_upload(nombre, flujo, temporal)
                except Exception:
                    temporal.unlink(missing_ok=True)
                    raise
                preparados.append(IntakeFile(name=nombre, path=temporal))
        except Exception:
            for item in preparados:
                item.path.unlink(missing_ok=True)
            raise
        return tuple(preparados)

    def _write_upload(self, nombre: str, flujo: BinaryIO, temporal: Path) -> None:
        """Vuelca una subida al temporal y rechaza lo que no debe llegar al almacén.

        El ejecutable se rechaza **aquí**, antes de copiarlo: si se copiara primero y se rechazara
        después, el binario ya estaría en el almacén y el lote tendría una entrada fallida que no
        debía existir. La política es la común (`storage_policy`): primero por el nombre —para no
        escribir nada— y después por la firma del fichero ya escrito.
        """
        por_nombre = refusal_message(name=nombre)
        if por_nombre is not None:
            raise UnsafeContentError(por_nombre)
        escrito = 0
        with temporal.open("wb") as destino:
            while True:
                trozo = flujo.read(1024 * 1024)
                if not trozo:
                    break
                escrito += len(trozo)
                if escrito > self._max_file_bytes:
                    raise UnsafeContentError(
                        f"el fichero {safe_display_name(nombre)!r} supera el límite de "
                        f"{self._max_file_bytes} bytes"
                    )
                destino.write(trozo)
        # La firma solo se puede mirar con el fichero ya escrito: un `.dat` con cabecera PE no pasa.
        por_firma = refusal_message(name=nombre, path=temporal)
        if por_firma is not None:
            raise UnsafeContentError(por_firma)

    def ingest_files(self, files: Sequence[IntakeFile]) -> BatchView:
        """Copia al almacén los ficheros que el usuario ha soltado o seleccionado."""
        if not files:
            raise InvalidSourceError("no has seleccionado ningún fichero")
        # Todo se comprueba **antes** de crear el lote: si algo no se admite, no queda ni lote ni
        # artefacto por el camino.
        for item in files:
            if not item.path.is_file():
                raise InvalidSourceError("uno de los ficheros ya no está disponible")
            motivo = refusal_message(name=item.name, path=item.path)
            if motivo is not None:
                raise UnsafeContentError(motivo)
        now = self._clock.now()
        batch_id = self._repository.create_batch(
            kind=BatchKind.IMPORT,
            mode=BatchMode.COPY,
            source_path_display=f"{len(files)} fichero(s) seleccionados",
            now=now,
            status=BatchStatus.QUEUED,
        )
        try:
            for item in files:
                nombre = safe_display_name(item.name)
                self._store_one(
                    batch_id,
                    display_location=nombre,
                    original_name=item.name,
                    origin_type=OriginType.FILE,
                    source_path_display=None,
                    source=item.path,
                )
        except Exception as error:
            # Un fallo a mitad deja el lote cerrado y con su motivo: si se quedara en `queued`, no
            # habría ni trabajo ni entrada que lo cerrara y el usuario vería un lote colgado para
            # siempre (pasaba con un fallo de disco al copiar).
            self._close_failed(batch_id, error)
            raise
        finally:
            # Los temporales de la subida solo viven hasta que el contenido está en el almacén: se
            # borran siempre, también si la copia falla a mitad. Sin esto, cada subida dejaba su
            # `.part` en `data/tmp` para siempre (lo encontró la prueba manual de S03).
            for item in files:
                item.path.unlink(missing_ok=True)
        return self._close_intake(batch_id)

    # ------------------------------------------------------------------ texto pegado

    def ingest_paste(self, text: str, *, title: str | None = None) -> BatchView:
        """Guarda el texto pegado como un artefacto propio, con su origen `paste`.

        El texto pegado no pasa por la política de contenido: lo escribe OpoFuente y no trae firma
        que inspeccionar. Lo que sí tiene es tope de tamaño y validación previa (vacío, límite).
        """
        contenido = text.strip()
        if not contenido:
            raise InvalidSourceError("no hay texto que guardar")
        tamano = len(contenido.encode("utf-8"))
        if tamano > self._max_paste_bytes:
            raise InvalidSourceError(
                f"el texto pegado ocupa {tamano} bytes y el límite es {self._max_paste_bytes}"
            )
        now = self._clock.now()
        etiqueta = safe_display_name(title) if title else "texto pegado"

        # El temporal se escribe **antes** de crear el lote: si el disco falla aquí, no hay nada que
        # cerrar y no queda un lote en `queued` sin entradas ni trabajo que lo cierre (el usuario
        # veía un lote colgado para siempre).
        temporal = self._temp_path("paste")
        try:
            temporal.write_text(contenido, encoding="utf-8", newline="\n")
        except OSError:
            temporal.unlink(missing_ok=True)
            raise

        batch_id = self._repository.create_batch(
            kind=BatchKind.IMPORT,
            mode=BatchMode.COPY,
            source_path_display=etiqueta,
            now=now,
            status=BatchStatus.QUEUED,
        )
        try:
            self._store_one(
                batch_id,
                display_location=etiqueta,
                original_name=etiqueta,
                origin_type=OriginType.PASTE,
                source_path_display=None,
                source=temporal,
            )
        except Exception as error:
            self._close_failed(batch_id, error)
            raise
        finally:
            temporal.unlink(missing_ok=True)
        return self._close_intake(batch_id)

    # ------------------------------------------------------------------ URL

    def ingest_url(self, url: str) -> BatchView:
        """Descarga una URL con la guarda de red y guarda lo descargado como artefacto.

        Lo descargado pasa por la **misma** política de contenido que una subida o una carpeta: un
        ejecutable servido por URL con nombre inocente se rechaza antes de crear el lote y antes de
        copiarlo al almacén. Antes esta vía no lo comprobaba y el binario entraba.
        """
        limits = self._url_limits or url_limits_from_settings(
            timeout_seconds=20.0, max_bytes=64 * 1024 * 1024, max_redirects=5
        )
        temporal = self._temp_path("url")
        try:
            descarga: FetchResult = self._fetcher(url, destination=temporal, limits=limits)
            nombre = _name_from_url(descarga.final_url, descarga.content_type)
            motivo = refusal_message(name=nombre, path=temporal)
            if motivo is not None:
                raise UnsafeContentError(motivo)
            now = self._clock.now()
            batch_id = self._repository.create_batch(
                kind=BatchKind.IMPORT,
                mode=BatchMode.COPY,
                # Se muestra la URL que pidió el usuario (la final queda en el origen): es lo que
                # identifica el lote para quien lo pidió, y sin cadena de consulta.
                source_path_display=_display_url(url),
                now=now,
                status=BatchStatus.QUEUED,
            )
            # La URL final se guarda **sin cadena de consulta ni fragmento**: una descarga puede
            # acabar en una dirección con un token, y ese valor viaja a la API y a la interfaz como
            # procedencia del texto. Lo que se muestra es el sitio, no el secreto que llevaba.
            final_visible = display_url(descarga.final_url)
            try:
                self._store_one(
                    batch_id,
                    display_location=final_visible,
                    original_name=nombre,
                    origin_type=OriginType.URL,
                    source_path_display=final_visible,
                    source=temporal,
                )
            except Exception as error:
                self._close_failed(batch_id, error)
                raise
        finally:
            temporal.unlink(missing_ok=True)
        logger.info(
            "intake.url_stored",
            extra={
                "event": "intake_url",
                "status_code": len(descarga.redirects),
            },
        )
        return self._close_intake(batch_id)

    # ------------------------------------------------------------------ apoyo

    def _temp_path(self, prefijo: str) -> Path:
        """Fichero temporal dentro del directorio de datos (nunca fuera)."""
        tmp = resolve_within(self._data_root, self._data_root / "tmp")
        tmp.mkdir(parents=True, exist_ok=True)
        return resolve_within(tmp, tmp / f"{prefijo}-{uuid4().hex}.part")

    def _store_one(
        self,
        batch_id: str,
        *,
        display_location: str,
        original_name: str,
        origin_type: OriginType,
        source_path_display: str | None,
        source: Path,
    ) -> None:
        """Copia un fichero al almacén y le crea su entrada en el lote."""
        stat = source.stat()
        stored = self._store.store_file(source)
        artifact_id, _created = self._repository.register_artifact(
            digest=stored.sha256,
            size_bytes=stored.size_bytes,
            media_type=media_type_for(original_name),
            storage_key=stored.storage_key,
            origin_type=origin_type,
            display_location=display_location,
            original_name=safe_display_name(original_name),
            source_path_display=source_path_display,
            file_mtime=None,
            now=self._clock.now(),
        )
        relativo = self._unique_path(batch_id, safe_display_name(original_name))
        self._repository.add_entries(
            batch_id,
            (
                DiscoveredEntry(
                    relative_path=relativo,
                    original_name=safe_display_name(original_name),
                    size_bytes=stat.st_size,
                    mtime=None,
                    media_type=media_type_for(original_name),
                    status=ItemStatus.HASHED,
                    # La procedencia se guarda en la **entrada**, no solo en el artefacto: unos
                    # mismos bytes pueden entrar como fichero, como texto pegado y como URL, y cada
                    # entrada tiene la suya. `display_location` ya viene saneado por su vía (nombre
                    # de fichero saneado, título saneado o URL sin cadena de consulta): volver a
                    # sanearlo aquí destrozaría una URL (`https:__ejemplo.test_x`).
                    origin_type=origin_type.value,
                    origin_display=display_location,
                ),
            ),
            status=ItemStatus.HASHED,
        )
        item_id = self._repository.item_id_for(batch_id, relativo)
        if item_id is None:  # pragma: no cover - se acaba de añadir
            raise NotFoundError("entrada del lote", relativo)
        self._repository.mark_item(item_id, ItemStatus.HASHED, artifact_id=artifact_id)

    def _unique_path(self, batch_id: str, base: str) -> str:
        """Dos ficheros con el mismo nombre en un lote no pueden pisarse.

        El nombre original es metadato y la identidad del contenido es el hash, así que aquí solo
        hay que evitar que dos entradas del mismo lote compartan ruta: la segunda pasa a
        `nombre (2)`.
        """
        if self._repository.item_id_for(batch_id, base) is None:
            return base
        sufijo = 2
        while True:
            candidate = _with_suffix(base, sufijo)
            if self._repository.item_id_for(batch_id, candidate) is None:
                return candidate
            sufijo += 1

    def _close_intake(self, batch_id: str) -> BatchView:
        """Cuenta lo que ha entrado, deja el lote encolado y pide su extracción.

        El trabajo de extracción se guarda **en el lote** (`set_job`): es el que la interfaz
        consulta para el progreso, y el que se cancela cuando el usuario cancela. Sin ese enlace, el
        lote apuntaba a un trabajo viejo (o a ninguno) y la pantalla mostraba un progreso que no era
        el de su trabajo.
        """
        self._repository.set_counters(batch_id, self._repository.summarize_import(batch_id))
        pending = self._repository.pending_extraction_count(batch_id)
        if pending:
            job, _created = self.jobs.enqueue(
                job_type=JobType.EXTRACT_ARTIFACT,
                payload={"batch_id": batch_id},
                now=self._clock.now(),
                idempotency_key=f"extract_batch:{batch_id}:0",
            )
            self._repository.set_job(batch_id, job.id)
        else:  # pragma: no cover - sin entradas copiadas no hay lote que cerrar
            self._repository.set_status(batch_id, BatchStatus.SUCCEEDED, now=self._clock.now())
        view = self._repository.get_batch(batch_id)
        if view is None:  # pragma: no cover - se acaba de crear
            raise NotFoundError("lote", batch_id)
        return view

    def _close_failed(self, batch_id: str, error: Exception) -> None:
        """Cierra el lote como `failed` con su motivo, cuando falla la copia de lo que entra.

        Un lote que se queda en `queued` sin entradas ni trabajos es un lote huérfano: nadie lo va a
        cerrar y el usuario lo ve colgado. Se cuentan las entradas reales (las que sí entraron) y se
        guarda un motivo saneado.
        """
        self._repository.set_counters(batch_id, self._repository.summarize_import(batch_id))
        self._repository.set_status(
            batch_id,
            BatchStatus.FAILED,
            now=self._clock.now(),
            error_summary=_safe_error_summary(error),
        )
        logger.error(
            "intake.store_failed",
            extra={
                "event": "intake_store_failed",
                "error_type": type(error).__name__,
                "job_id": batch_id,
            },
        )


def _safe_error_summary(error: Exception) -> str:
    """Motivo del fallo para el informe: sin trazas y sin rutas del usuario."""
    from opofuente.infrastructure.safe_paths import redact_paths

    detail = redact_paths(str(error).strip().replace("\n", " "))
    if len(detail) > 160:
        detail = detail[:160] + "…"
    return f"{type(error).__name__}: {detail}" if detail else type(error).__name__


def _with_suffix(name: str, index: int) -> str:
    """`tema.pdf` + 2 → `tema (2).pdf`, conservando la extensión."""
    sufijo = Path(name).suffix
    if sufijo:
        return f"{name[: -len(sufijo)]} ({index}){sufijo}"
    return f"{name} ({index})"


def _display_url(url: str) -> str:
    """URL para mostrar en el lote, sin cadena de consulta (puede llevar tokens)."""
    return display_url(url)


def _name_from_url(url: str, content_type: str | None) -> str:
    """Nombre para el artefacto: el último tramo de la URL o uno genérico por tipo."""
    from urllib.parse import unquote, urlsplit

    ultimo = unquote(urlsplit(url).path.rstrip("/").rsplit("/", 1)[-1])
    if ultimo:
        return ultimo
    if content_type:
        principal = content_type.split(";")[0].strip().lower()
        if principal == "application/pdf":
            return "descarga.pdf"
        if principal.startswith("text/html"):
            return "descarga.html"
        if principal.startswith("text/"):
            return "descarga.txt"
    return "descarga.bin"
