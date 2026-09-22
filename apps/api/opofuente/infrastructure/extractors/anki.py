"""Extractor de barajas de Anki (`.apkg`, `.colpkg`).

Una baraja de Anki es un contenedor **ZIP** con una **base de datos SQLite** dentro y los ficheros
de media numerados. Este extractor lo lee como lo que es, sin expandirlo como si fuera un ZIP
cualquiera (que es lo que pasaría si se tratara como `.zip`: se perderían las tarjetas y quedarían
sueltos un SQLite y unas imágenes).

Lo que hace, en orden:

1. inspecciona el contenedor con las mismas guardas que un ZIP (`safe_zip`): nombres, enlaces,
   bombas y límites de tamaño;
2. saca **la colección** (`collection.anki21b`, `collection.anki21` o `collection.anki2`), que desde
   Anki 2.1.50 viene comprimida con **zstd** — de ahí la dependencia (ADR-016);
3. la abre como SQLite **en solo lectura** y lee las notas con el nombre de cada campo y el mazo al
   que pertenecen;
4. escribe **un tramo por tarjeta**, con los nombres de campo que usa la propia baraja (anverso,
   reverso, lo que sea): no se inventa cuál es la pregunta y cuál la respuesta;
5. **declara la media que no extrae** y avisa de ella, en vez de callarse que la baraja traía
   imágenes o audio.

Lo que **no** hace: convertir una tarjeta en una pregunta corregible. El modelo tiene el tipo
`free_text_reference` y **no tiene dónde guardar la respuesta de referencia**, así que una tarjeta
entra como material estudiable y citable, no como pregunta (ADR-016 y DEBT-023).
"""

from __future__ import annotations

import json
import re
import sqlite3
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import zstandard

from opofuente.domain.errors import UnsafeContentError
from opofuente.domain.extraction import (
    ExtractedSection,
    ExtractionResult,
    ExtractorRef,
    Quality,
    RepresentationKind,
    RepresentationStatus,
    SectionType,
    WarningCode,
    clamp_sections,
    measure_quality,
    merge_warnings,
    normalise_text,
    truncate_text,
)
from opofuente.infrastructure.extractors.base import DetectedFormat
from opofuente.infrastructure.safe_zip import ZipLimits, inspect_zip, write_single_entry

EXTRACTOR_NAME = "anki_apkg"
EXTRACTOR_VERSION = "1"

#: Miembros donde Anki guarda la colección, del formato más nuevo al más viejo.
_COLLECTION_NAMES = ("collection.anki21b", "collection.anki21", "collection.anki2")

#: Cabecera de un flujo zstd. Anki comprime la colección con zstd desde 2.1.50.
_ZSTD_MAGIC = b"\x28\xb5\x2f\xfd"

#: Separador de campos dentro de `notes.flds` (unidad de separación, 0x1f).
_FIELD_SEPARATOR = "\x1f"

#: Miembros del contenedor que no son media.
_NOT_MEDIA = frozenset(
    {"collection.anki2", "collection.anki21", "collection.anki21b", "media", "meta"}
)

#: Etiquetas HTML: Anki guarda los campos con marcado.
_TAGS = re.compile(r"<[^>]+>")

#: Espacios de más que deja quitar las etiquetas, y el hueco delante de un signo de puntuación.
_SPACES = re.compile(r"[ \t]{2,}")
_SPACE_BEFORE_PUNCTUATION = re.compile(r"\s+([.,;:!?)\]}])")

_ENTITIES = (
    ("&nbsp;", " "),
    ("&amp;", "&"),
    ("&lt;", "<"),
    ("&gt;", ">"),
    ("&quot;", '"'),
    ("&#39;", "'"),
)


@dataclass(frozen=True, slots=True)
class _NoteType:
    """Tipo de nota: su nombre y los nombres de sus campos, en orden."""

    name: str
    fields: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class _Note:
    note_id: int
    note_type_id: int
    fields: tuple[str, ...]
    tags: tuple[str, ...]
    deck_id: int | None


@dataclass(frozen=True, slots=True)
class _Card:
    """Una tarjeta ya escrita: su título y el texto de sus campos."""

    title: str
    body: str


class AnkiExtractor:
    """Texto de una baraja de Anki: una tarjeta por tramo, con sus nombres de campo."""

    name = EXTRACTOR_NAME
    version = EXTRACTOR_VERSION

    def __init__(self, *, max_chars: int, max_bytes: int, limits: ZipLimits) -> None:
        self._max_chars = max_chars
        self._max_bytes = max_bytes
        self._limits = limits

    def extract(self, path: Path, *, detected: DetectedFormat) -> ExtractionResult:
        try:
            inspection = inspect_zip(path, limits=self._limits)
        except UnsafeContentError as error:
            return _failed(str(error))

        members = [member for member in inspection.members if not member.is_directory]
        coleccion = _collection_member([member.name for member in members])
        if coleccion is None:
            return _failed("el contenedor no trae ninguna colección de Anki dentro")
        media = [
            member.name
            for member in members
            if member.name.lower() not in _NOT_MEDIA and member.name != coleccion
        ]

        with tempfile.TemporaryDirectory(prefix="opofuente-anki-") as carpeta:
            destino = Path(carpeta) / "collection.sqlite"
            try:
                self._write_collection(path, coleccion, destino)
            except UnsafeContentError as error:
                return _failed(str(error))
            except (zipfile.BadZipFile, OSError) as error:
                return _failed(f"la colección no se pudo leer ({type(error).__name__})")

            try:
                notas, mazos, tipos = _read_notes(destino)
            except sqlite3.DatabaseError as error:
                return _failed(f"la colección no es una base de datos legible ({error})")

        tarjetas = _cards(notas, mazos, tipos)
        if not tarjetas:
            return ExtractionResult(
                kind=RepresentationKind.NATIVE_TEXT,
                status=RepresentationStatus.EMPTY,
                text="",
                extractor=ExtractorRef(self.name, self.version),
                quality=Quality.POOR,
                warnings=(WarningCode.EMPTY_TEXT,),
                metadata={
                    "cards": 0,
                    "decks": len(mazos),
                    "note_types": len(tipos),
                    "media_files": len(media),
                    "container": coleccion,
                },
            )

        cuerpo = "\n\n".join(f"{tarjeta.title}\n{tarjeta.body}" for tarjeta in tarjetas)
        texto, truncation = truncate_text(cuerpo, max_chars=self._max_chars)
        secciones = clamp_sections(_sections(tarjetas), char_count=len(texto))
        calidad = measure_quality(texto, kind=RepresentationKind.NATIVE_TEXT)

        # La media no se extrae: ni se convierte en artefactos ni se analiza. Se dice.
        avisos: list[WarningCode] = [WarningCode.MEDIA_NOT_EXTRACTED] if media else []
        return ExtractionResult(
            kind=RepresentationKind.NATIVE_TEXT,
            status=RepresentationStatus.EXTRACTED,
            text=texto,
            extractor=ExtractorRef(self.name, self.version),
            sections=secciones,
            quality=calidad.quality,
            warnings=merge_warnings(tuple(avisos), truncation, calidad.warnings),
            metadata={
                "cards": len(tarjetas),
                "cards_written": len(secciones),
                "decks": len(mazos),
                "note_types": len(tipos),
                "media_files": len(media),
                "container": coleccion,
            },
        )

    def _write_collection(self, path: Path, member: str, destino: Path) -> None:
        """Deja la colección como SQLite legible, descomprimiéndola si venía con zstd."""
        crudo = destino.with_suffix(".bin")
        with zipfile.ZipFile(path) as archive:
            info = next((item for item in archive.infolist() if item.filename == member), None)
            if info is None:
                raise UnsafeContentError(f"el contenedor no trae {member}")
            write_single_entry(archive, info, crudo, max_bytes=self._max_bytes)

        datos = crudo.read_bytes()
        crudo.unlink(missing_ok=True)
        if datos.startswith(_ZSTD_MAGIC):
            datos = _decompress_zstd(datos, max_bytes=self._max_bytes)
        destino.write_bytes(datos)


def _failed(reason: str) -> ExtractionResult:
    return ExtractionResult(
        kind=RepresentationKind.NATIVE_TEXT,
        status=RepresentationStatus.FAILED,
        text="",
        extractor=ExtractorRef(EXTRACTOR_NAME, EXTRACTOR_VERSION),
        quality=Quality.FAILED,
        warnings=(WarningCode.EXTRACTOR_FAILED,),
        metadata={"reason": reason},
    )


def _collection_member(names: list[str]) -> str | None:
    por_nombre = {name.lower(): name for name in names}
    for candidato in _COLLECTION_NAMES:
        if candidato in por_nombre:
            return por_nombre[candidato]
    return None


def _decompress_zstd(datos: bytes, *, max_bytes: int) -> bytes:
    """Descomprime acotando la salida: una colección no puede llenar la memoria."""
    try:
        return zstandard.ZstdDecompressor().decompress(datos, max_output_size=max_bytes)
    except zstandard.ZstdError as error:
        raise UnsafeContentError(
            f"la colección comprimida no se pudo descomprimir ({error})"
        ) from error


def _read_notes(
    sqlite: Path,
) -> tuple[list[_Note], dict[int, str], dict[int, _NoteType]]:
    """Lee notas, mazos y tipos de nota de una colección, moderna o antigua."""
    conexion = sqlite3.connect(f"file:{sqlite.as_posix()}?mode=ro", uri=True)
    try:
        conexion.row_factory = sqlite3.Row
        tablas = {
            str(fila[0])
            for fila in conexion.execute("select name from sqlite_master where type = 'table'")
        }
        if "notetypes" in tablas:
            tipos, mazos = _modern_types_and_decks(conexion)
        else:
            tipos, mazos = _legacy_types_and_decks(conexion)
        mazo_por_nota = _deck_by_note(conexion) if "cards" in tablas else {}
        notas = [
            _Note(
                note_id=int(fila["id"]),
                note_type_id=int(fila["mid"]),
                fields=tuple(str(fila["flds"] or "").split(_FIELD_SEPARATOR)),
                tags=tuple(
                    etiqueta for etiqueta in str(fila["tags"] or "").split() if etiqueta.strip()
                ),
                deck_id=mazo_por_nota.get(int(fila["id"])),
            )
            for fila in conexion.execute("select id, mid, flds, tags from notes order by id")
        ]
        return notas, mazos, tipos
    finally:
        conexion.close()


def _modern_types_and_decks(
    conexion: sqlite3.Connection,
) -> tuple[dict[int, _NoteType], dict[int, str]]:
    tipos: dict[int, _NoteType] = {}
    for fila in conexion.execute("select id, name, config from notetypes"):
        config = _json(fila["config"])
        campos = config.get("flds") if isinstance(config, dict) else None
        nombres: list[str] = []
        if isinstance(campos, list):
            for campo in campos:
                if isinstance(campo, dict) and isinstance(campo.get("name"), str):
                    nombres.append(str(campo["name"]))
        tipos[int(fila["id"])] = _NoteType(str(fila["name"] or ""), tuple(nombres))

    mazos: dict[int, str] = {}
    for fila in conexion.execute("select id, name from decks"):
        # En una colección moderna el nombre del mazo es JSON (`"name"`); una creada a mano puede
        # traerlo en texto plano, así que se admiten las dos formas en lugar de fallar por una.
        bruto = fila["name"]
        nombre = bruto
        if isinstance(bruto, str) and bruto.startswith("{"):
            cargado = _json(bruto)
            if isinstance(cargado, dict) and isinstance(cargado.get("name"), str):
                nombre = cargado["name"]
        mazos[int(fila["id"])] = str(nombre or "").replace("\x1f", "::")
    return tipos, mazos


def _legacy_types_and_decks(
    conexion: sqlite3.Connection,
) -> tuple[dict[int, _NoteType], dict[int, str]]:
    """Colecciones anteriores a 2.1.28: los tipos y los mazos viven en JSON dentro de `col`."""
    fila = conexion.execute("select models, decks from col limit 1").fetchone()
    modelos = _json(fila["models"]) if fila is not None else None
    barajas = _json(fila["decks"]) if fila is not None else None

    tipos: dict[int, _NoteType] = {}
    if isinstance(modelos, dict):
        for clave, valor in modelos.items():
            if not isinstance(valor, dict):
                continue
            campos = valor.get("flds")
            nombres: tuple[str, ...] = ()
            if isinstance(campos, list):
                nombres = tuple(
                    str(campo["name"])
                    for campo in campos
                    if isinstance(campo, dict) and "name" in campo
                )
            tipos[int(clave)] = _NoteType(str(valor.get("name", "")), nombres)

    mazos: dict[int, str] = {}
    if isinstance(barajas, dict):
        for clave, valor in barajas.items():
            if isinstance(valor, dict):
                mazos[int(clave)] = str(valor.get("name", "")).replace("\x1f", "::")
    return tipos, mazos


def _deck_by_note(conexion: sqlite3.Connection) -> dict[int, int]:
    """Mazo de cada nota: si una nota está en varios, se queda con el primero por identificador."""
    mazos: dict[int, int] = {}
    for fila in conexion.execute("select nid, did from cards order by nid, id"):
        mazos.setdefault(int(fila["nid"]), int(fila["did"]))
    return mazos


def _json(valor: Any) -> Any:
    if not isinstance(valor, (str, bytes)):
        return None
    try:
        return json.loads(valor)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None


def _field_name(tipos: dict[int, _NoteType], tipo_id: int, posicion: int) -> str:
    tipo = tipos.get(tipo_id)
    if tipo is not None and posicion < len(tipo.fields):
        return tipo.fields[posicion]
    return f"campo {posicion + 1}"


def _card_title(nota: _Note, mazos: dict[int, str], tipos: dict[int, _NoteType]) -> str:
    tipo = tipos.get(nota.note_type_id)
    nombre_tipo = tipo.name if tipo is not None and tipo.name else "tipo de nota sin nombre"
    mazo = mazos.get(nota.deck_id) if nota.deck_id is not None else None
    return f"{mazo or 'sin mazo'} · {nombre_tipo}"


def _cards(notas: list[_Note], mazos: dict[int, str], tipos: dict[int, _NoteType]) -> list[_Card]:
    """Una tarjeta por nota, con los nombres de campo de su propio tipo de nota."""
    tarjetas: list[_Card] = []
    for numero, nota in enumerate(notas, start=1):
        lineas: list[str] = []
        for posicion, valor in enumerate(nota.fields):
            texto = _plain(valor)
            if texto:
                lineas.append(f"{_field_name(tipos, nota.note_type_id, posicion)}: {texto}")
        if nota.tags:
            lineas.append(f"Etiquetas: {', '.join(nota.tags)}")
        tarjetas.append(
            _Card(
                title=f"TARJETA {numero}. {_card_title(nota, mazos, tipos)}",
                body="\n".join(lineas),
            )
        )
    return tarjetas


def _sections(tarjetas: list[_Card]) -> tuple[ExtractedSection, ...]:
    """Un tramo por tarjeta: la cita de una tarjeta es la tarjeta, no la baraja entera."""
    secciones: list[ExtractedSection] = []
    offset = 0
    for numero, tarjeta in enumerate(tarjetas, start=1):
        cuerpo = f"{tarjeta.title}\n{tarjeta.body}"
        secciones.append(
            ExtractedSection(
                section_type=SectionType.QUESTION_BLOCK,
                position=numero,
                char_start=offset,
                char_end=offset + len(cuerpo),
                label=tarjeta.title,
            )
        )
        offset += len(cuerpo) + 2  # los bloques se unen con una línea en blanco
    return tuple(secciones)


def _plain(valor: str) -> str:
    """Quita el marcado HTML que Anki guarda en los campos, sin perder el texto.

    Los campos de una baraja son HTML (`<b>hábiles</b>.`, `<br>`, `&nbsp;`). Se quitan las etiquetas
    y se arregla lo que dejan: espacios de más y el espacio que queda delante de un signo de
    puntuación, que es como se lee el campo y no como se guarda.
    """
    texto = _TAGS.sub(" ", valor)
    for origen, destino in _ENTITIES:
        texto = texto.replace(origen, destino)
    texto = _SPACES.sub(" ", texto)
    texto = _SPACE_BEFORE_PUNCTUATION.sub(r"\1", texto)
    return normalise_text(texto)
