"""Servicio de copia, verificación y restauración (08_API-CONTRACT §11, 09_SECURITY §10).

El contrato fija el orden de una restauración y aquí se sigue tal cual, porque cada paso existe para
evitar un destrozo concreto:

1. **validar sin escribir**: se lee el manifiesto, se comprueban las rutas y se hashea el contenido.
   Una copia corrupta se declara corrupta **antes** de tocar nada.
2. **comprobar espacio y versión**: sin sitio no se empieza; con una revisión de esquema más nueva
   que el programa, se para y se dice que hay que actualizar primero.
3. **copia previa automática**: antes de sustituir nada se hace una copia de lo que hay. Es la red
   de seguridad del usuario y no es opcional.
4. **restaurar a temporal**: se extrae al árbol de temporales, nunca encima de los datos.
5. **intercambio atómico**, con deshacer si algo falla (ver `swap_restored`).
6. **migración y comprobación**: la base restaurada se lleva a la revisión del código.
7. **recuperación manual si falla**: los puntos de retorno se quedan donde están y se dicen sus
rutas.
"""

from __future__ import annotations

import shutil
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from opofuente.config import DataPaths
from opofuente.domain.backup import (
    DEFAULT_SCOPE,
    RESTORE_TARGETS,
    BackupError,
    BackupManifest,
    BackupScope,
    is_restorable,
    missing_scope,
    validate_entries,
)
from opofuente.infrastructure.backup_archive import (
    archive_path,
    discard_rollback,
    extract_archive,
    free_bytes,
    new_backup_id,
    read_manifest,
    safe_backup_id,
    snapshot_database,
    swap_restored,
    verify_archive,
    write_archive,
)


@dataclass(frozen=True, slots=True)
class BackupView:
    """Una copia tal como se enseña: identidad, tamaño y si se puede restaurar aquí y ahora."""

    id: str
    created_at: str
    app_version: str
    schema_revision: str
    scope: tuple[str, ...]
    size_bytes: int
    file_count: int
    note: str | None
    restorable: bool
    restorable_reason: str


@dataclass(frozen=True, slots=True)
class VerificationView:
    """Resultado de verificar una copia: lo que se ha mirado y lo que no cuadra."""

    backup: BackupView
    verified: bool
    problems: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class RestorePreview:
    """Lo que una restauración haría, **antes** de hacerlo."""

    backup: BackupView
    can_restore: bool
    blockers: tuple[str, ...]
    missing_scope: tuple[str, ...]
    free_bytes: int
    needed_bytes: int
    targets: tuple[str, ...]
    previous_backup_note: str


@dataclass(frozen=True, slots=True)
class RestoreResult:
    """Lo que una restauración ha hecho, con lo necesario para entenderla y deshacerla a mano."""

    backup_id: str
    previous_backup_id: str
    restored: tuple[str, ...]
    rollback_paths: tuple[str, ...]
    schema_revision: str
    health_ok: bool
    health_detail: str


class BackupService:
    """Copia, verifica y restaura el árbol de datos local."""

    def __init__(
        self,
        *,
        paths: DataPaths,
        app_version: str,
        clock: Callable[[], datetime],
        schema_revision: Callable[[], str],
        migrate: Callable[[], None] | None = None,
        health: Callable[[], tuple[bool, str]] | None = None,
    ) -> None:
        self._paths = paths
        self._app_version = app_version
        self._clock = clock
        self._schema_revision = schema_revision
        self._migrate = migrate
        self._health = health

    # ------------------------------------------------------------------ copia

    def create(
        self,
        *,
        scope: tuple[BackupScope, ...] = DEFAULT_SCOPE,
        note: str | None = None,
        progress: Callable[[str, int, int], None] | None = None,
    ) -> BackupView:
        """Hace una copia y devuelve su ficha. La base se copia con la API de respaldo de SQLite."""
        ahora = self._clock()
        identificador = new_backup_id(ahora)
        destino = archive_path(self._paths.backups, identificador)
        # La instantánea va en **su** directorio dentro de temporales: así no comparte sitio con los
        # restos de una operación interrumpida y se puede retirar entera sin tocar nada más.
        instantanea_dir = self._paths.tmp / f"snapshot-{identificador}"
        instantanea = instantanea_dir / "opofuente.sqlite3"
        try:
            snapshot_database(self._paths.database, instantanea)
            manifiesto = write_archive(
                root=self._paths.root,
                destination=destino,
                backup_id=identificador,
                created_at=ahora,
                app_version=self._app_version,
                schema_revision=self._schema_revision(),
                scope=scope,
                note=note,
                database=instantanea,
                progress=progress,
            )
        except OSError as error:
            destino.unlink(missing_ok=True)
            raise BackupError(f"la copia no se pudo escribir: {error}") from error
        finally:
            shutil.rmtree(instantanea_dir, ignore_errors=True)
        return self._view(manifiesto, size_bytes=destino.stat().st_size)

    def list(self) -> tuple[BackupView, ...]:
        """Las copias que hay, de la más nueva a la más antigua.

        Una copia ilegible **no** se esconde: si su manifiesto no se puede leer, aparece con el
        motivo
        y marcada como no restaurable, en lugar de desaparecer de la lista como si no existiera.
        """
        vistas: list[BackupView] = []
        if not self._paths.backups.is_dir():
            return ()
        for archivo in sorted(self._paths.backups.glob("*.zip"), reverse=True):
            try:
                manifiesto = read_manifest(archivo)
                vistas.append(self._view(manifiesto, size_bytes=archivo.stat().st_size))
            except BackupError as error:
                vistas.append(
                    BackupView(
                        id=archivo.stem,
                        created_at="",
                        app_version="",
                        schema_revision="",
                        scope=(),
                        size_bytes=archivo.stat().st_size,
                        file_count=0,
                        note=None,
                        restorable=False,
                        restorable_reason=str(error),
                    )
                )
        return tuple(vistas)

    def get(self, backup_id: str) -> BackupView | None:
        archivo = archive_path(self._paths.backups, safe_backup_id(backup_id))
        if not archivo.is_file():
            return None
        try:
            manifiesto = read_manifest(archivo)
        except BackupError:
            return None
        return self._view(manifiesto, size_bytes=archivo.stat().st_size)

    def verify(self, backup_id: str) -> VerificationView | None:
        """Verifica hash y tamaño de cada entrada. Devuelve `None` si la copia no existe."""
        archivo = archive_path(self._paths.backups, safe_backup_id(backup_id))
        if not archivo.is_file():
            return None
        manifiesto, problemas = verify_archive(archivo)
        vista = self._view(manifiesto, size_bytes=archivo.stat().st_size)
        return VerificationView(backup=vista, verified=not problemas, problems=problemas)

    # ------------------------------------------------------------------ restauración

    def preview(self, backup_id: str) -> RestorePreview | None:
        """Paso 1 y 2: valida la copia y comprueba espacio y versión, sin escribir nada."""
        identificador = safe_backup_id(backup_id)
        archivo = archive_path(self._paths.backups, identificador)
        if not archivo.is_file():
            return None
        manifiesto = read_manifest(archivo)
        validate_entries(manifiesto)
        vista = self._view(manifiesto, size_bytes=archivo.stat().st_size)
        bloqueos: list[str] = []
        puede, motivo = is_restorable(manifiesto, current_revision=self._schema_revision())
        if not puede:
            bloqueos.append(motivo)
        faltan = missing_scope(manifiesto, DEFAULT_SCOPE)
        if "database" in faltan:
            bloqueos.append("la copia no trae la base de datos: sin ella no hay nada que restaurar")
        libre = free_bytes(self._paths.root)
        necesario = manifiesto.total_bytes * 2
        if libre >= 0 and libre < necesario:
            bloqueos.append(f"no hay espacio: hacen falta unos {necesario} bytes y quedan {libre}")
        return RestorePreview(
            backup=vista,
            can_restore=not bloqueos,
            blockers=tuple(bloqueos),
            missing_scope=faltan,
            free_bytes=libre,
            needed_bytes=necesario,
            targets=RESTORE_TARGETS,
            previous_backup_note=(
                "Antes de restaurar se hará una copia automática de lo que hay ahora."
            ),
        )

    def restore(self, backup_id: str, *, keep_rollback: bool = False) -> RestoreResult:
        """Restaura **de verdad**, en el orden del contrato, con deshacer si algo falla."""
        identificador = safe_backup_id(backup_id)
        archivo = archive_path(self._paths.backups, identificador)
        if not archivo.is_file():
            raise BackupError(f"no existe la copia {identificador}")
        vista_previa = self.preview(identificador)
        if vista_previa is None:
            raise BackupError(f"no existe la copia {identificador}")
        if not vista_previa.can_restore:
            raise BackupError("la copia no se puede restaurar: " + "; ".join(vista_previa.blockers))
        _, problemas = verify_archive(archivo)
        if problemas:
            raise BackupError("la copia no ha pasado la verificación: " + "; ".join(problemas[:3]))

        # 3. Copia previa automática: la red de seguridad del usuario.
        previa = self.create(note=f"copia automática previa a restaurar {identificador}")

        # 4. Extracción a temporal: nunca encima de los datos.
        temporal = self._paths.tmp / f"restore-{identificador}"
        if temporal.exists():
            shutil.rmtree(temporal, ignore_errors=True)
        manifiesto = read_manifest(archivo)
        extraidos = extract_archive(archivo, temporal)

        # 5. Comprobación que evita el fallo silencioso: **todo** lo que la copia dice traer tiene
        #    que estar extraído, y la base tiene que estar entre ello. Sin esto, una extracción
        #    incompleta restauraría «bien» dejando la instalación sin datos.
        escritos = set(extraidos)
        faltan_en_la_copia = [
            entrada.path for entrada in manifiesto.entries if entrada.path not in escritos
        ]
        if "database/opofuente.sqlite3" not in escritos:
            faltan_en_la_copia.append("database/opofuente.sqlite3")
        if faltan_en_la_copia:
            shutil.rmtree(temporal, ignore_errors=True)
            raise BackupError(
                "la copia no trae lo necesario para restaurar: " + ", ".join(faltan_en_la_copia[:5])
            )
        # 6. Intercambio atómico.
        try:
            puntos = swap_restored(
                root=self._paths.root, restored=temporal, targets=RESTORE_TARGETS
            )
        finally:
            shutil.rmtree(temporal, ignore_errors=True)

        # 6. Migración y comprobación.
        revision = ""
        sano = True
        detalle = "sin comprobación configurada"
        try:
            if self._migrate is not None:
                self._migrate()
            revision = self._schema_revision()
            if self._health is not None:
                sano, detalle = self._health()
            else:
                detalle = "la base restaurada se ha migrado hasta la revisión del programa"
        except Exception as error:
            # Se informa en lugar de esconderlo: es un fallo de restauración y el usuario tiene que
            # saber dónde quedaron los puntos de retorno para poder deshacerlo a mano.
            sano = False
            detalle = (
                f"la restauración se hizo, pero la comprobación posterior falló ({error}). "
                f"Puntos de retorno: {', '.join(puntos) or 'ninguno'}"
            )
            return RestoreResult(
                backup_id=identificador,
                previous_backup_id=previa.id,
                restored=tuple(extraidos),
                rollback_paths=puntos,
                schema_revision=revision,
                health_ok=False,
                health_detail=detalle,
            )

        # 7. Solo si todo ha ido bien se retiran los puntos de retorno. Si no, quedan para deshacer.
        if not keep_rollback and sano:
            discard_rollback(self._paths.root, RESTORE_TARGETS)
            puntos = ()
        return RestoreResult(
            backup_id=identificador,
            previous_backup_id=previa.id,
            restored=tuple(extraidos),
            rollback_paths=puntos,
            schema_revision=revision,
            health_ok=sano,
            health_detail=detalle,
        )

    # ------------------------------------------------------------------ piezas

    def _view(self, manifiesto: BackupManifest, *, size_bytes: int) -> BackupView:
        puede, motivo = is_restorable(manifiesto, current_revision=self._schema_revision())
        return BackupView(
            id=manifiesto.id,
            created_at=manifiesto.created_at,
            app_version=manifiesto.app_version,
            schema_revision=manifiesto.schema_revision,
            scope=manifiesto.scope,
            size_bytes=size_bytes,
            file_count=len(manifiesto.entries),
            note=manifiesto.note,
            restorable=puede,
            restorable_reason=motivo,
        )


__all__ = [
    "BackupService",
    "BackupView",
    "RestorePreview",
    "RestoreResult",
    "VerificationView",
]
