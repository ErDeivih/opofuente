"""Copia de seguridad, verificación y restauración (09_SECURITY-PRIVACY-AND-RIGHTS §10).

Tres reglas gobiernan todo lo de aquí, y las tres vienen del contrato:

1. **Una copia se valida sin escribir nada.** Antes de tocar un solo fichero de la instalación se
   comprueba el manifiesto, la versión de esquema y el hash de cada entrada: una copia corrupta se
   declara corrupta, no se restaura a medias.
2. **La restauración es atómica y reversible.** Se restaura en un directorio temporal, se prepara un
   punto de retorno (`<nombre>.restore-old`) y solo entonces se intercambia. Si algo falla entre
   medias, se vuelve a dejar la instalación anterior en su sitio: un fallo de restauración **no**
   deja al usuario sin datos.
3. **Nada de borrados a ciegas.** El intercambio mueve directorios a un punto de retorno con nombre
   fijo y comprobado; no se borra ninguna ruta construida a partir de datos de la copia. Lo que se
   retira del árbol de datos tiene que estar **dentro** del árbol de datos.

Este módulo no sabe nada de HTTP ni de SQLite: recibe un manifiesto, unos ficheros y un sistema de
archivos, y devuelve una decisión. Esa es la parte que se puede probar sin arrancar nada.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path, PurePosixPath
from typing import Any

#: Versión del **formato** del manifiesto, no de la aplicación ni del esquema. Cambiarla significa
#: que una copia hecha con una versión anterior necesita conversión para poder restaurarse.
BACKUP_FORMAT_VERSION = 1

#: Nombre del manifiesto dentro del archivo y del fichero suelto junto a él.
MANIFEST_NAME = "manifest.json"

#: Extensiones de los archivos de copia.
ARCHIVE_SUFFIX = ".zip"

#: Sufijo del punto de retorno que se prepara durante una restauración.
ROLLBACK_SUFFIX = ".restore-old"

#: Extensiones que **no** entran en una copia aunque estén en el árbol de datos: no son datos del
#: usuario y se reconstruyen solas.
EXCLUDED_SUFFIXES = (".part", "-wal", "-shm")

#: Directorios del árbol de datos que no se copian: las copias mismas (no se copia una copia dentro
#: de otra), los temporales y los registros (se regeneran y no son datos).
EXCLUDED_TOP_LEVEL = ("backups", "tmp", "logs")


class BackupScope(StrEnum):
    """Qué entra en una copia. El contrato pide DB, artefactos, representaciones y configuración."""

    DATABASE = "database"
    ARTIFACTS = "artifacts"
    EXTRACTED = "extracted"
    FIXTURES = "fixtures"


#: Alcance por defecto: todo lo que hace falta para reproducir la instalación.
DEFAULT_SCOPE: tuple[BackupScope, ...] = (
    BackupScope.DATABASE,
    BackupScope.ARTIFACTS,
    BackupScope.EXTRACTED,
    BackupScope.FIXTURES,
)

#: Entradas de primer nivel del árbol de datos que una restauración **sí** sustituye. Todo lo demás
#: (copias, temporales, registros, índice vectorial) se queda como está: el índice se reconstruye,
#: las copias no se pisan entre sí al restaurar y el árbol de temporales es **zona de paso**, no
#: estado: restaurarlo mezclaría restos de una operación interrumpida con los de la copia.
RESTORE_TARGETS: tuple[str, ...] = ("opofuente.sqlite3", "artifacts", "extracted")

#: Dónde vive cada entrada de `RESTORE_TARGETS` **dentro** de la copia. La base se guarda bajo
#: `database/` para que el alcance quede explícito en el manifiesto, así que su ruta en el archivo
#: no coincide con la del árbol de datos y hay que traducirla; sin esta tabla, restaurar dejaba la
#: base sin colocar (y la instalación sin datos) mientras decía que había ido bien.
RESTORE_ARCHIVE_PATH: dict[str, str] = {"opofuente.sqlite3": "database/opofuente.sqlite3"}


def restore_source(restored: Path, name: str) -> Path:
    """Ruta de una entrada del árbol de datos **dentro** de la copia extraída."""
    return restored / RESTORE_ARCHIVE_PATH.get(name, name)


class BackupError(Exception):
    """La copia no se puede hacer, no se puede leer o no se puede restaurar, con el motivo."""


@dataclass(frozen=True, slots=True)
class BackupEntry:
    """Un fichero dentro de la copia, con lo necesario para comprobar que llegó entero."""

    path: str
    size_bytes: int
    sha256: str


@dataclass(frozen=True, slots=True)
class BackupManifest:
    """Lo que la copia dice de sí misma.

    `schema_revision` es la revisión de Alembic con la que se hizo: es lo que permite decidir si una
    copia se puede restaurar en el código actual o necesita migración.
    """

    id: str
    created_at: str
    app_version: str
    schema_revision: str
    format_version: int
    scope: tuple[str, ...]
    entries: tuple[BackupEntry, ...] = field(default_factory=tuple)
    note: str | None = None

    @property
    def total_bytes(self) -> int:
        return sum(entrada.size_bytes for entrada in self.entries)

    def to_json(self) -> str:
        return json.dumps(
            {
                "id": self.id,
                "created_at": self.created_at,
                "app_version": self.app_version,
                "schema_revision": self.schema_revision,
                "format_version": self.format_version,
                "scope": list(self.scope),
                "note": self.note,
                "entries": [
                    {
                        "path": entrada.path,
                        "size_bytes": entrada.size_bytes,
                        "sha256": entrada.sha256,
                    }
                    for entrada in self.entries
                ],
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )

    @classmethod
    def from_json(cls, payload: str) -> BackupManifest:
        """Lee un manifiesto y **rechaza** lo que no cumple el formato, en lugar de rellenarlo."""
        try:
            datos: Any = json.loads(payload)
        except json.JSONDecodeError as error:
            raise BackupError(f"el manifiesto no es JSON válido: {error}") from error
        if not isinstance(datos, dict):
            raise BackupError("el manifiesto no es un objeto")
        faltan = [
            clave
            for clave in (
                "id",
                "created_at",
                "schema_revision",
                "format_version",
                "scope",
                "entries",
            )
            if clave not in datos
        ]
        if faltan:
            raise BackupError(f"al manifiesto le faltan campos: {', '.join(sorted(faltan))}")
        if not isinstance(datos["entries"], list):
            raise BackupError("«entries» no es una lista")
        entradas: list[BackupEntry] = []
        for fila in datos["entries"]:
            if not isinstance(fila, dict) or not {"path", "size_bytes", "sha256"} <= set(fila):
                raise BackupError("una entrada del manifiesto está incompleta")
            entradas.append(
                BackupEntry(
                    path=str(fila["path"]),
                    size_bytes=int(fila["size_bytes"]),
                    sha256=str(fila["sha256"]),
                )
            )
        return cls(
            id=str(datos["id"]),
            created_at=str(datos["created_at"]),
            app_version=str(datos.get("app_version", "")),
            schema_revision=str(datos["schema_revision"]),
            format_version=int(datos["format_version"]),
            scope=tuple(str(valor) for valor in datos["scope"]),
            entries=tuple(entradas),
            note=None if datos.get("note") is None else str(datos["note"]),
        )


def safe_relative_path(raw: str) -> PurePosixPath:
    """Ruta relativa de una entrada, o error.

    Una copia es una entrada de datos **no confiable** hasta que se valida: si un manifiesto pudiera
    traer `../` o una ruta absoluta, restaurarlo escribiría fuera del destino. Aquí se rechaza antes
    de construir ninguna ruta.
    """
    if not raw or raw.strip() != raw:
        raise BackupError("una entrada tiene una ruta vacía o con espacios sobrantes")
    normalizada = raw.replace("\\", "/")
    ruta = PurePosixPath(normalizada)
    if ruta.is_absolute() or normalizada.startswith("/"):
        raise BackupError(f"la entrada «{raw}» es una ruta absoluta")
    if any(parte in ("..", "") for parte in ruta.parts):
        raise BackupError(f"la entrada «{raw}» sale del destino")
    if ":" in ruta.parts[0]:
        raise BackupError(f"la entrada «{raw}» usa una unidad de Windows")
    return ruta


def is_restorable(manifest: BackupManifest, *, current_revision: str) -> tuple[bool, str]:
    """¿Se puede restaurar esta copia con el código actual? Con el motivo, siempre.

    Dos comprobaciones, y ninguna rellena lo que falta:

    - el **formato** del manifiesto tiene que ser el que este código entiende;
    - la **revisión de esquema** de la copia no puede ser más nueva que la del código: restaurar el
      futuro sobre el presente dejaría tablas que el programa no sabe leer.
    """
    if manifest.format_version != BACKUP_FORMAT_VERSION:
        return False, (
            f"la copia usa el formato {manifest.format_version} y este programa entiende el "
            f"{BACKUP_FORMAT_VERSION}"
        )
    if manifest.schema_revision == current_revision:
        return True, f"la copia está en la revisión de esquema actual ({current_revision})"
    if manifest.schema_revision > current_revision:
        return False, (
            f"la copia es de una revisión más nueva ({manifest.schema_revision}) que la del "
            f"programa ({current_revision}): actualiza el programa antes de restaurarla"
        )
    return True, (
        f"la copia es de la revisión {manifest.schema_revision} y el programa está en "
        f"{current_revision}: al restaurar se aplicarán las migraciones que falten"
    )


def validate_entries(manifest: BackupManifest) -> None:
    """Comprueba la coherencia interna del manifiesto: rutas seguras, sin duplicados y con hash."""
    vistas: set[str] = set()
    for entrada in manifest.entries:
        safe_relative_path(entrada.path)
        if entrada.path in vistas:
            raise BackupError(f"la entrada «{entrada.path}» está dos veces en el manifiesto")
        vistas.add(entrada.path)
        if entrada.size_bytes < 0:
            raise BackupError(f"la entrada «{entrada.path}» declara un tamaño negativo")
        if len(entrada.sha256) != 64:
            raise BackupError(f"la entrada «{entrada.path}» no trae un sha256 de 64 caracteres")


def missing_scope(manifest: BackupManifest, scope: tuple[BackupScope, ...]) -> tuple[str, ...]:
    """Qué parte del alcance pedido **no** trae la copia: una copia parcial se dice, no se
    supone."""
    faltan: list[str] = []
    for parte in scope:
        if parte.value not in manifest.scope:
            faltan.append(parte.value)
            continue
        if not any(entrada.path.startswith(f"{parte.value}/") for entrada in manifest.entries):
            faltan.append(parte.value)
    return tuple(faltan)


def rollback_directory(target: Path) -> Path:
    """Punto de retorno de un directorio: `<ruta>.restore-old`, sin construirlo desde la copia."""
    return target.with_name(target.name + ROLLBACK_SUFFIX)


def is_inside(root: Path, candidate: Path) -> bool:
    """¿Está `candidate` dentro de `root`? Se compara resolviendo, no por texto.

    Es la guarda que impide que un intercambio de directorios toque algo que no es del árbol de
    datos.
    """
    try:
        candidato = candidate.resolve()
        raiz = root.resolve()
    except OSError:
        return False
    return candidato == raiz or raiz in candidato.parents


__all__ = [
    "ARCHIVE_SUFFIX",
    "BACKUP_FORMAT_VERSION",
    "DEFAULT_SCOPE",
    "EXCLUDED_SUFFIXES",
    "EXCLUDED_TOP_LEVEL",
    "MANIFEST_NAME",
    "RESTORE_ARCHIVE_PATH",
    "RESTORE_TARGETS",
    "ROLLBACK_SUFFIX",
    "BackupEntry",
    "BackupError",
    "BackupManifest",
    "BackupScope",
    "is_inside",
    "is_restorable",
    "missing_scope",
    "restore_source",
    "rollback_directory",
    "safe_relative_path",
    "validate_entries",
]
