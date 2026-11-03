"""ZIP seguro: inspección y extracción a un temporal aislado (DEBT-004, 09_SECURITY §3).

Un ZIP es entrada no confiable y puede ser tres ataques a la vez: **traversal** (miembros con `..`,
rutas absolutas o letra de unidad que escriben fuera del destino), **bomba** (mucho contenido
comprimido, o una proporción de expansión absurda) y **enlace** (un miembro marcado como symlink que
apunta fuera al extraerlo).

Aquí se inspecciona **antes** de extraer nada y se extrae con tres defensas más:

- cada miembro se escribe con `resolve_within`, comprobando la ruta resuelta;
- se lee por trozos contando bytes, así que una cabecera que mienta sobre el tamaño no cuela;
- los directorios se crean, pero los enlaces y las entradas raras no se extraen.

El ZIP no se «abre» ni se ejecuta: solo se leen sus bytes.
"""

from __future__ import annotations

import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from opofuente.domain.errors import UnsafeContentError
from opofuente.infrastructure.safe_paths import resolve_within

CHUNK_BYTES = 1024 * 1024

#: Entradas que generan los sistemas al comprimir y no son material del usuario.
JUNK_PREFIXES = ("__MACOSX/",)
JUNK_NAMES = frozenset({".DS_Store", "Thumbs.db", "desktop.ini"})

#: Nombres de dispositivo reservados de Windows (sin extensión y con ella: `NUL.txt` también lo es).
RESERVED_DEVICE_NAMES = frozenset(
    {
        "CON",
        "PRN",
        "AUX",
        "NUL",
        "COM1",
        "COM2",
        "COM3",
        "COM4",
        "COM5",
        "COM6",
        "COM7",
        "COM8",
        "COM9",
        "LPT1",
        "LPT2",
        "LPT3",
        "LPT4",
        "LPT5",
        "LPT6",
        "LPT7",
        "LPT8",
        "LPT9",
    }
)


@dataclass(frozen=True, slots=True)
class ZipLimits:
    """Límites de un ZIP. Los valores salen de la configuración, no de aquí."""

    max_entries: int
    max_uncompressed_bytes: int
    max_ratio: int


@dataclass(frozen=True, slots=True)
class ZipMember:
    name: str
    size_bytes: int
    compressed_bytes: int
    is_directory: bool


@dataclass(frozen=True, slots=True)
class ZipInspection:
    """Resultado de inspeccionar un ZIP sin extraerlo."""

    members: tuple[ZipMember, ...]
    total_uncompressed_bytes: int
    total_compressed_bytes: int
    skipped_junk: int

    @property
    def ratio(self) -> float:
        if self.total_compressed_bytes == 0:
            return float(self.total_uncompressed_bytes)
        return self.total_uncompressed_bytes / self.total_compressed_bytes

    @property
    def file_count(self) -> int:
        return sum(1 for member in self.members if not member.is_directory)


def _is_junk(name: str) -> bool:
    if name.startswith(JUNK_PREFIXES):
        return True
    return PurePosixPath(name).name in JUNK_NAMES


def _member_name(info: zipfile.ZipInfo) -> str:
    """Nombre del miembro con `/` como separador, venga del sistema que venga.

    `zipfile` solo sustituye `\\` por `/` cuando el anfitrión es Windows, así que el mismo ZIP se
    juzgaba de dos formas distintas según dónde corriera la puerta. Se normaliza aquí, una sola vez
    y al estilo del sistema donde vive el producto: `..\\x.txt` se juzga como `../x.txt` (traversal)
    y `apuntes\\tema.txt` como `apuntes/tema.txt`, que es lo que Windows escribiría al expandirlo.

    `check_member_name` sigue viendo el nombre tal cual se le pase: su contrato es la cadena cruda
    y así lo fijan sus pruebas directas.
    """
    return info.filename.replace("\\", "/")


def check_member_name(name: str) -> None:
    """Rechaza nombres que escapan del destino o que no son rutas normales **en Windows**.

    Es pública a propósito: es una de las defensas del módulo y las pruebas la ejercitan
    directamente, sin tener que construir un ZIP que burle la normalización de `zipfile`.

    Además del traversal y de la ruta absoluta se rechazan los nombres que NTFS interpreta de forma
    especial, porque un ZIP que se expande en Windows puede acabar escribiendo donde no debe:

    - `archivo.txt:flujo` → flujo alternativo de datos (`ADS`): el fichero visible queda vacío y el
      contenido va a un flujo oculto que se ejecuta o se lee por otra vía;
    - `CON`, `NUL`, `COM1`… → nombres de dispositivo reservados: escribir en ellos no crea un
      fichero, va al dispositivo (o falla de formas raras);
    - segmentos que terminan en punto o espacio → Windows los recorta al crear el fichero, así que
      dos miembros distintos pueden acabar siendo el mismo;
    - caracteres de control → no son material y rompen herramientas.
    """
    if not name or name.strip() != name:
        raise UnsafeContentError("el ZIP trae un miembro con nombre vacío o con espacios raros")
    if "\\" in name:
        raise UnsafeContentError(
            "el ZIP trae un miembro con barra invertida: no se admiten rutas de Windows"
        )
    if any(ord(character) < 32 or ord(character) == 127 for character in name):
        raise UnsafeContentError("el ZIP trae un miembro con caracteres de control")
    if ":" in name:
        # Cubre la letra de unidad (`C:`) y el flujo alternativo de datos (`archivo.txt:flujo`).
        raise UnsafeContentError(
            "el ZIP trae un miembro con dos puntos: unidad o flujo alternativo de datos"
        )
    pure = PurePosixPath(name)
    if pure.is_absolute():
        raise UnsafeContentError("el ZIP trae un miembro con ruta absoluta")
    for part in pure.parts:
        if part == "..":
            raise UnsafeContentError("el ZIP trae un miembro que sale de la carpeta (..)")
        if part != part.rstrip(". "):
            raise UnsafeContentError(
                f"el ZIP trae un miembro cuyo nombre acaba en punto o espacio ({part!r}): "
                "Windows lo recortaría y dos entradas podrían acabar siendo la misma"
            )
        if _is_reserved_device_name(part):
            raise UnsafeContentError(
                f"el ZIP trae un miembro con nombre de dispositivo reservado ({part!r})"
            )


def _is_reserved_device_name(part: str) -> bool:
    """¿Es un nombre de dispositivo de Windows (`CON`, `NUL`, `COM1`…), con o sin extensión?"""
    base = part.split(".", 1)[0].strip().upper()
    if base in RESERVED_DEVICE_NAMES:
        return True
    # `COM0` y `LPT0` no son dispositivos, pero no se gana nada admitiéndolos y sí se complica la
    # regla: se rechazan igual que los numerados de verdad.
    return len(base) == 4 and base[:3] in {"COM", "LPT"} and base[3].isdigit()


def _check_unique_names(members: list[ZipMember]) -> None:
    """Dos miembros no pueden diferir solo en mayúsculas: en Windows son el mismo fichero.

    Un ZIP con `Tema.txt` y `tema.txt` se expandiría en una sola entrada escrita dos veces, y el
    resultado dependería del orden: una sobrescritura silenciosa.
    """
    seen: dict[str, str] = {}
    for member in members:
        key = member.name.casefold()
        previous = seen.get(key)
        if previous is not None:
            raise UnsafeContentError(
                f"el ZIP trae dos entradas que solo difieren en mayúsculas ({previous!r} y "
                f"{member.name!r}): en Windows son el mismo fichero"
            )
        seen[key] = member.name


def _check_symlink(info: zipfile.ZipInfo) -> None:
    """Un miembro marcado como enlace simbólico no se extrae: podría apuntar fuera."""
    mode = info.external_attr >> 16
    if mode and (mode & 0o170000) == 0o120000:
        raise UnsafeContentError("el ZIP trae un enlace simbólico: no se extraen enlaces")


def inspect_zip(path: Path, *, limits: ZipLimits, depth: int = 0) -> ZipInspection:
    """Inspecciona el ZIP y comprueba los límites. No extrae nada.

    `depth` cuenta los ZIP ya anidados que se están expandiendo; el llamante decide el máximo.
    """
    try:
        with zipfile.ZipFile(path) as archive:
            infos = archive.infolist()
    except zipfile.BadZipFile as error:
        raise UnsafeContentError("el ZIP está corrupto o no es un ZIP") from error
    except OSError as error:
        raise UnsafeContentError(f"el ZIP no se pudo leer ({type(error).__name__})") from error

    members: list[ZipMember] = []
    skipped = 0
    total_uncompressed = 0
    total_compressed = 0
    for info in infos:
        name = _member_name(info)
        if _is_junk(name):
            skipped += 1
            continue
        check_member_name(name)
        _check_symlink(info)
        is_directory = name.endswith("/")
        members.append(
            ZipMember(
                name=name.rstrip("/") if is_directory else name,
                size_bytes=int(info.file_size),
                compressed_bytes=int(info.compress_size),
                is_directory=is_directory,
            )
        )
        total_uncompressed += int(info.file_size)
        total_compressed += int(info.compress_size)

    if len(members) > limits.max_entries:
        raise UnsafeContentError(
            f"el ZIP trae {len(members)} entradas y el límite es {limits.max_entries}"
        )
    _check_unique_names(members)
    if total_uncompressed > limits.max_uncompressed_bytes:
        raise UnsafeContentError(
            "el ZIP descomprime "
            f"{total_uncompressed} bytes y el límite es {limits.max_uncompressed_bytes}"
        )
    compressed = max(total_compressed, 1)
    if total_uncompressed / compressed > limits.max_ratio:
        raise UnsafeContentError(
            f"el ZIP declara una expansión de {total_uncompressed // compressed}:1 "
            f"y el límite es {limits.max_ratio}:1"
        )
    return ZipInspection(
        members=tuple(members),
        total_uncompressed_bytes=total_uncompressed,
        total_compressed_bytes=total_compressed,
        skipped_junk=skipped,
    )


def extract_zip_safely(
    path: Path,
    destination: Path,
    *,
    limits: ZipLimits,
    max_bytes_per_member: int | None = None,
) -> tuple[Path, ...]:
    """Extrae el ZIP en `destination` y devuelve los ficheros escritos, en orden.

    Comprueba los límites primero (`inspect_zip`) y vuelve a comprobar cada miembro al escribirlo:
    la ruta resuelta tiene que quedar dentro del destino, y el número de bytes leídos no puede pasar
    del tope indicado aunque la cabecera mienta.
    """
    inspect_zip(path, limits=limits)
    destination.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    allowed = (
        max_bytes_per_member if max_bytes_per_member is not None else limits.max_uncompressed_bytes
    )
    try:
        with zipfile.ZipFile(path) as archive:
            for info in archive.infolist():
                name = _member_name(info)
                if _is_junk(name):
                    continue
                target = resolve_within(destination, destination / name)
                if name.endswith("/"):
                    target.mkdir(parents=True, exist_ok=True)
                    continue
                write_single_entry(archive, info, target, max_bytes=allowed)
                written.append(target)
    except zipfile.BadZipFile as error:  # pragma: no cover - ya se comprobó al inspeccionar
        raise UnsafeContentError("el ZIP está corrupto o no es un ZIP") from error
    return tuple(written)


def write_single_entry(
    archive: zipfile.ZipFile, info: zipfile.ZipInfo, target: Path, *, max_bytes: int
) -> None:
    """Escribe un miembro contando bytes: una cabecera que mienta no puede llenar el disco."""
    target.parent.mkdir(parents=True, exist_ok=True)
    written = 0
    with archive.open(info, "r") as source, target.open("wb") as sink:
        while True:
            chunk = source.read(CHUNK_BYTES)
            if not chunk:
                break
            written += len(chunk)
            if written > max_bytes:
                sink.close()
                target.unlink(missing_ok=True)
                raise UnsafeContentError(
                    f"el miembro {info.filename!r} supera el límite de {max_bytes} bytes al leerse"
                )
            sink.write(chunk)
