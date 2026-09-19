"""Archivo de copia: escribir, leer y comprobar el `.zip` con su manifiesto.

Un archivo de copia es un ZIP con `manifest.json` en la raíz y, debajo, las rutas **relativas** al
árbol de datos (`artifacts/…`, `extracted/…`, `database/opofuente.sqlite3`). El manifiesto va el
primero para poder decidir si la copia sirve **antes** de leer un solo byte de datos.

La base de datos **no** se copia como fichero suelto: se copia con la API de respaldo de SQLite, que
da una instantánea coherente aunque el programa esté escribiendo (con `-wal` activo, copiar el
fichero
a mano puede dar una base rota). Eso se hace en `snapshot_database`, y aquí solo se mete el
resultado.
"""

from __future__ import annotations

import hashlib
import shutil
import sqlite3
import zipfile
from collections.abc import Callable, Iterator
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from opofuente.domain.backup import (
    ARCHIVE_SUFFIX,
    BACKUP_FORMAT_VERSION,
    DEFAULT_SCOPE,
    EXCLUDED_SUFFIXES,
    EXCLUDED_TOP_LEVEL,
    MANIFEST_NAME,
    BackupEntry,
    BackupError,
    BackupManifest,
    BackupScope,
    is_inside,
    restore_source,
    rollback_directory,
    safe_relative_path,
)

#: Tamaño de bloque para hashear y copiar: se trabaja por trozos, nunca con el fichero entero en
#: memoria (el material puede ser grande y el equipo es un portátil).
CHUNK_BYTES = 1024 * 1024

#: Ruta, dentro del archivo, de la instantánea de la base de datos.
DATABASE_ENTRY = "database/opofuente.sqlite3"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as origen:
        while True:
            bloque = origen.read(CHUNK_BYTES)
            if not bloque:
                break
            digest.update(bloque)
    return digest.hexdigest()


def snapshot_database(source: Path, destination: Path) -> None:
    """Instantánea coherente de SQLite con la API de respaldo, no copiando el fichero.

    La instantánea es **lógicamente** idéntica (mismas tablas, mismas filas, mismo esquema) pero no
    necesariamente idéntica byte a byte: la API de respaldo reproduce las páginas y puede reordenar
    el espacio libre. Por eso lo que se comprueba de una base restaurada son sus datos, no su hash:
    el hash del manifiesto sirve para saber que **el archivo de la copia** llegó entero, que es otra
    cosa. Para que el fichero fuese byte a byte igual habría que copiarlo con la base cerrada, y eso
    no se puede hacer con la aplicación en marcha.

    Si la base no existe (instalación recién creada y todavía sin migrar) se escribe una base vacía
    como instantánea: es lo que hay, y decirlo es mejor que fallar la copia.
    """
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not source.is_file():
        sqlite3.connect(destination).close()
        return
    origen = sqlite3.connect(f"file:{source.as_posix()}?mode=ro", uri=True)
    try:
        destino = sqlite3.connect(destination)
        try:
            origen.backup(destino)
        finally:
            destino.close()
    finally:
        origen.close()


def iter_files(root: Path, scope: tuple[BackupScope, ...]) -> Iterator[tuple[str, Path]]:
    """Ficheros del árbol de datos que entran en la copia, con su ruta relativa posix.

    Se excluyen las copias mismas (`backups/`), los temporales (`tmp/`), los registros (`logs/`)
    y los
    restos de una operación interrumpida (`.part`, `-wal`, `-shm`): nada de eso es dato del
    usuario y
    copiarlo haría copias dentro de copias.
    """
    for parte in scope:
        base = root / parte.value
        if parte is BackupScope.DATABASE:
            continue
        if not base.is_dir():
            continue
        for ruta in sorted(base.rglob("*")):
            if not ruta.is_file():
                continue
            relativa = ruta.relative_to(root).as_posix()
            if any(relativa.endswith(sufijo) for sufijo in EXCLUDED_SUFFIXES):
                continue
            if relativa.split("/", 1)[0] in EXCLUDED_TOP_LEVEL:
                continue
            yield relativa, ruta


def write_archive(
    *,
    root: Path,
    destination: Path,
    backup_id: str,
    created_at: datetime,
    app_version: str,
    schema_revision: str,
    scope: tuple[BackupScope, ...] = DEFAULT_SCOPE,
    note: str | None = None,
    database: Path | None = None,
    progress: Callable[[str, int, int], None] | None = None,
) -> BackupManifest:
    """Escribe la copia y devuelve su manifiesto, con el hash real de cada entrada.

    El manifiesto se construye **mientras** se escribe: cada entrada se hashea al vuelo, así que el
    hash del manifiesto es el del contenido que de verdad ha entrado, no el que se esperaba.
    """
    entradas: list[BackupEntry] = []
    destination.parent.mkdir(parents=True, exist_ok=True)
    ficheros = list(iter_files(root, scope))
    total = len(ficheros)
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archivo:
        # 1. La base de datos, si el alcance la incluye y hay instantánea preparada.
        if BackupScope.DATABASE in scope:
            origen_bd = database if database is not None else root / "opofuente.sqlite3"
            digest = hashlib.sha256()
            tamano = 0
            if origen_bd.is_file():
                with (
                    archivo.open(DATABASE_ENTRY, "w") as destino,
                    origen_bd.open("rb") as fuente,
                ):
                    while True:
                        bloque = fuente.read(CHUNK_BYTES)
                        if not bloque:
                            break
                        digest.update(bloque)
                        tamano += len(bloque)
                        destino.write(bloque)
            entradas.append(
                BackupEntry(path=DATABASE_ENTRY, size_bytes=tamano, sha256=digest.hexdigest())
            )
        # 2. El material, por trozos, hasheando lo que se escribe.
        for indice, (relativa, ruta) in enumerate(ficheros, start=1):
            digest = hashlib.sha256()
            tamano = 0
            with archivo.open(relativa, "w") as destino, ruta.open("rb") as fuente:
                while True:
                    bloque = fuente.read(CHUNK_BYTES)
                    if not bloque:
                        break
                    digest.update(bloque)
                    tamano += len(bloque)
                    destino.write(bloque)
            entradas.append(
                BackupEntry(path=relativa, size_bytes=tamano, sha256=digest.hexdigest())
            )
            if progress is not None:
                progress(relativa, indice, total)

        manifiesto = BackupManifest(
            id=backup_id,
            created_at=created_at.isoformat(),
            app_version=app_version,
            schema_revision=schema_revision,
            format_version=BACKUP_FORMAT_VERSION,
            scope=tuple(parte.value for parte in scope),
            entries=tuple(entradas),
            note=note,
        )
        archivo.writestr(MANIFEST_NAME, manifiesto.to_json())
    return manifiesto


def read_manifest(archive: Path) -> BackupManifest:
    """Manifiesto del archivo, sin leer el contenido de los datos."""
    if not archive.is_file():
        raise BackupError(f"no existe la copia {archive.name}")
    try:
        with zipfile.ZipFile(archive) as archivo, archivo.open(MANIFEST_NAME) as fichero:
            return BackupManifest.from_json(fichero.read().decode("utf-8"))
    except KeyError as error:
        raise BackupError("la copia no trae manifiesto") from error
    except zipfile.BadZipFile as error:
        raise BackupError("la copia no es un archivo legible") from error


def verify_archive(archive: Path) -> tuple[BackupManifest, tuple[str, ...]]:
    """Comprueba hash y tamaño de **cada** entrada sin escribir nada, y devuelve los problemas.

    Devuelve el manifiesto y la lista de problemas en lugar de lanzar en el primer fallo: quien
    verifica
    quiere saber todo lo que está mal, no la primera línea.
    """
    manifiesto = read_manifest(archive)
    problemas: list[str] = []
    try:
        with zipfile.ZipFile(archive) as archivo:
            presentes = set(archivo.namelist())
            for entrada in manifiesto.entries:
                if entrada.path not in presentes:
                    problemas.append(f"falta «{entrada.path}»")
                    continue
                digest = hashlib.sha256()
                tamano = 0
                with archivo.open(entrada.path) as fichero:
                    while True:
                        bloque = fichero.read(CHUNK_BYTES)
                        if not bloque:
                            break
                        digest.update(bloque)
                        tamano += len(bloque)
                if tamano != entrada.size_bytes:
                    problemas.append(
                        f"«{entrada.path}» mide {tamano} bytes y el manifiesto dice "
                        f"{entrada.size_bytes}"
                    )
                if digest.hexdigest() != entrada.sha256:
                    problemas.append(f"«{entrada.path}» no coincide con su hash")
            sobrantes = (
                presentes - {entrada.path for entrada in manifiesto.entries} - {MANIFEST_NAME}
            )
            for sobrante in sorted(sobrantes):
                problemas.append(f"«{sobrante}» está en la copia y no en el manifiesto")
    except zipfile.BadZipFile as error:
        raise BackupError("la copia no es un archivo legible") from error
    return manifiesto, tuple(problemas)


def extract_archive(archive: Path, destination: Path) -> tuple[str, ...]:
    """Extrae la copia en `destination`, entrada por entrada y con la ruta ya validada.

    No se usa `extractall`: extraer un ZIP es el punto donde una ruta maliciosa se convierte en
    escritura fuera del destino, así que cada entrada se valida y se escribe a mano.
    """
    manifiesto = read_manifest(archive)
    destination.mkdir(parents=True, exist_ok=True)
    escritos: list[str] = []
    with zipfile.ZipFile(archive) as archivo:
        for entrada in manifiesto.entries:
            relativa = safe_relative_path(entrada.path)
            salida = destination.joinpath(*relativa.parts)
            salida.parent.mkdir(parents=True, exist_ok=True)
            with archivo.open(entrada.path) as origen, salida.open("wb") as destino:
                while True:
                    bloque = origen.read(CHUNK_BYTES)
                    if not bloque:
                        break
                    destino.write(bloque)
            escritos.append(entrada.path)
    return tuple(escritos)


def new_backup_id(now: datetime) -> str:
    """Identificador de copia: fecha legible y sufijo corto para no chocar dos copias del mismo
    día."""
    return f"{now.strftime('%Y%m%d-%H%M%S')}-{uuid4().hex[:6]}"


def archive_name(backup_id: str) -> str:
    return f"{backup_id}{ARCHIVE_SUFFIX}"


def archive_path(backups_dir: Path, backup_id: str) -> Path:
    return backups_dir / archive_name(safe_backup_id(backup_id))


def safe_backup_id(raw: str) -> str:
    """Valida el id de una copia antes de construir una ruta con él.

    Un id llega de la URL, así que no puede contener separadores, puntos suspensivos ni unidad de
    Windows: construir una ruta con él sin comprobarlo es exactamente el `rm -rf` sobre rutas
    construidas que el contrato prohíbe.
    """
    if not raw or len(raw) > 64 or raw != raw.strip():
        raise BackupError("el identificador de la copia no es válido")
    permitidos = set("0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ-_")
    if any(caracter not in permitidos for caracter in raw):
        raise BackupError("el identificador de la copia tiene caracteres no permitidos")
    return raw


def free_bytes(path: Path) -> int:
    """Espacio libre en la unidad donde vive `path`, subiendo hasta el primer ancestro existente."""
    candidato = path
    while not candidato.exists() and candidato.parent != candidato:
        candidato = candidato.parent
    try:
        return shutil.disk_usage(candidato).free
    except OSError:
        # Sin dato de espacio no se bloquea una restauración: se dice que no se ha podido comprobar.
        return -1


def swap_restored(
    *,
    root: Path,
    restored: Path,
    targets: tuple[str, ...],
) -> tuple[str, ...]:
    """Sustituye las entradas de `targets` por las de `restored`, de forma reversible.

    El intercambio se hace **moviendo**, nunca copiando encima y nunca borrando:
    cada entrada actual se aparta a `<nombre>.restore-old`, la nueva ocupa su sitio y, si algo
    falla a
    mitad, se deshacen los movimientos ya hechos y se devuelve el error. Un fallo de
    restauración tiene
    que dejar la instalación anterior utilizable, no a medias.

    Devuelve las rutas de los puntos de retorno que han quedado (para que quien llama pueda
    borrarlos
    cuando todo ha ido bien).
    """
    movidos: list[tuple[Path, Path]] = []  # (punto de retorno, ruta original)
    anteriores: list[tuple[Path, Path]] = []  # (ruta nueva, punto de retorno)
    try:
        for nombre in targets:
            destino = root / nombre
            if not is_inside(root, destino):
                raise BackupError(f"«{nombre}» no está dentro del árbol de datos")
            if not destino.exists():
                continue
            retorno = rollback_directory(destino)
            if retorno.exists():
                # Un punto de retorno de un intento anterior: se retira antes de volver a
                # usarlo. Está
                # dentro del árbol de datos por construcción, así que no es un borrado a ciegas.
                if retorno.is_dir():
                    shutil.rmtree(retorno)
                else:
                    retorno.unlink()
            destino.rename(retorno)
            movidos.append((retorno, destino))
        for nombre in targets:
            destino = root / nombre
            origen = restore_source(restored, nombre)
            if not origen.exists():
                continue
            destino.parent.mkdir(parents=True, exist_ok=True)
            origen.rename(destino)
            anteriores.append((destino, rollback_directory(destino)))
    except OSError as error:
        # Deshacer: lo nuevo que ya se movió vuelve a su punto de retorno y lo viejo vuelve a su
        # sitio.
        for colocado, _ in anteriores:
            if colocado.exists():
                shutil.rmtree(colocado, ignore_errors=True)
        for retorno, original in reversed(movidos):
            if retorno.exists() and not original.exists():
                retorno.rename(original)
        raise BackupError(
            f"la restauración no se pudo completar y se ha deshecho: {error}"
        ) from error
    return tuple(str(retorno) for retorno, _ in movidos)


def discard_rollback(root: Path, targets: tuple[str, ...]) -> None:
    """Retira los puntos de retorno de una restauración que ya terminó bien."""
    for nombre in targets:
        retorno = rollback_directory(root / nombre)
        if not retorno.exists():
            continue
        if not is_inside(root, retorno):
            raise BackupError(
                f"el punto de retorno de «{nombre}» no está dentro del árbol de datos"
            )
        if retorno.is_dir():
            shutil.rmtree(retorno)
        else:
            retorno.unlink()


__all__ = [
    "CHUNK_BYTES",
    "DATABASE_ENTRY",
    "archive_name",
    "archive_path",
    "discard_rollback",
    "extract_archive",
    "free_bytes",
    "iter_files",
    "new_backup_id",
    "read_manifest",
    "safe_backup_id",
    "sha256_file",
    "snapshot_database",
    "swap_restored",
    "verify_archive",
    "write_archive",
]
