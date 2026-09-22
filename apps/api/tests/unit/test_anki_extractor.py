"""Pruebas del extractor de barajas de Anki (`.apkg`, `.colpkg`).

La baraja de prueba se **construye** (`opofuente_testing.synthetic_documents`): un contenedor
con una colección SQLite dentro, comprimida con zstd como la exporta Anki desde 2.1.50. No se
descarga ninguna baraja real ni se usa material del propietario.

Lo que se defiende:

- una baraja se lee como baraja, no se expande como un ZIP cualquiera;
- de cada tarjeta se conservan los nombres de campo que usa la propia baraja;
- una colección vacía, un contenedor sin colección y una comprimida que no se puede descomprimir se
  declaran, en lugar de devolver texto inventado;
- la media que no se extrae se avisa.
"""

from __future__ import annotations

import json
import sqlite3
import zipfile
from pathlib import Path

import pytest

from opofuente.domain.extraction import (
    Quality,
    RepresentationKind,
    RepresentationStatus,
    SectionType,
    WarningCode,
)
from opofuente.infrastructure.extractors.anki import AnkiExtractor
from opofuente.infrastructure.extractors.base import detect_format
from opofuente.infrastructure.safe_zip import ZipLimits
from opofuente_testing.synthetic_documents import (
    ANKI_FIELD_SEPARATOR,
    anki_collection_bytes,
    build_anki_deck,
)

LIMITS = ZipLimits(max_entries=100, max_uncompressed_bytes=10_000_000, max_ratio=1000)


def _extractor(*, max_chars: int = 100_000) -> AnkiExtractor:
    return AnkiExtractor(max_chars=max_chars, max_bytes=10_000_000, limits=LIMITS)


@pytest.fixture
def baraja_moderna(tmp_path: Path) -> Path:
    sqlite = tmp_path / "collection.sqlite"
    coleccion = anki_collection_bytes(
        sqlite,
        notes=[
            (1, 1, f"¿Quién aprueba la ley?{ANKI_FIELD_SEPARATOR}Las Cortes.", ""),
            (2, 1, f"¿Cuántos días?{ANKI_FIELD_SEPARATOR}Diez días <b>hábiles</b>.", "plazos"),
        ],
        decks={1: "Constitución::Título I"},
    )
    return build_anki_deck(tmp_path / "baraja.apkg", collection=coleccion)


def test_una_baraja_se_reconoce_por_su_contenido_y_no_como_un_zip(baraja_moderna: Path) -> None:
    detectado = detect_format(baraja_moderna, name="baraja.apkg")
    assert detectado.family == "anki"
    assert detectado.suffix == ".apkg"


def test_un_zip_normal_sigue_siendo_un_zip(tmp_path: Path) -> None:
    ruta = tmp_path / "cualquiera.zip"
    with zipfile.ZipFile(ruta, "w") as archive:
        archive.writestr("leeme.txt", "hola")
    assert detect_format(ruta, name="cualquiera.zip").family == "zip"


def test_lee_las_tarjetas_con_sus_nombres_de_campo(baraja_moderna: Path) -> None:
    resultado = _extractor().extract(baraja_moderna, detected=detect_format(baraja_moderna))

    assert resultado.status is RepresentationStatus.EXTRACTED
    assert resultado.kind is RepresentationKind.NATIVE_TEXT
    assert resultado.quality in {Quality.GOOD, Quality.USABLE_WITH_WARNINGS}
    assert resultado.metadata["cards"] == 2
    assert resultado.metadata["decks"] == 1
    assert resultado.metadata["container"] == "collection.anki21"

    # El nombre del mazo sale anidado como en Anki («::») y el HTML del campo se limpia.
    assert "TARJETA 1. Constitución::Título I · Básico" in resultado.text
    assert "Anverso: ¿Quién aprueba la ley?" in resultado.text
    assert "Reverso: Las Cortes." in resultado.text
    assert "Reverso: Diez días hábiles." in resultado.text
    assert "<b>" not in resultado.text
    assert "Etiquetas: plazos" in resultado.text


def test_cada_tarjeta_es_un_tramo_con_su_etiqueta(baraja_moderna: Path) -> None:
    resultado = _extractor().extract(baraja_moderna, detected=detect_format(baraja_moderna))

    assert len(resultado.sections) == 2
    primera = resultado.sections[0]
    assert primera.section_type is SectionType.QUESTION_BLOCK
    assert primera.label == "TARJETA 1. Constitución::Título I · Básico"
    # El tramo señala texto que existe de verdad en la representación.
    assert resultado.text[primera.char_start : primera.char_end].startswith(primera.label)


def test_la_media_que_no_se_extrae_se_avisa(tmp_path: Path) -> None:
    ruta = build_anki_deck(tmp_path / "con-media.apkg", cards=[("Anverso", "Reverso")])
    sqlite = tmp_path / "otra.sqlite"
    con_media = build_anki_deck(
        tmp_path / "con-media2.apkg",
        cards=[],
        collection=anki_collection_bytes(
            sqlite, notes=[(1, 1, f"Anverso{ANKI_FIELD_SEPARATOR}Reverso", "")], decks={1: "Mazo"}
        ),
        media=2,
    )

    resultado = _extractor().extract(con_media, detected=detect_format(con_media))

    assert WarningCode.MEDIA_NOT_EXTRACTED in resultado.warnings
    assert resultado.metadata["media_files"] == 2
    # La misma baraja sin media no lleva ese aviso.
    sin_media = _extractor().extract(ruta, detected=detect_format(ruta))
    assert WarningCode.MEDIA_NOT_EXTRACTED not in sin_media.warnings


def test_una_baraja_sin_tarjetas_lo_dice_en_lugar_de_devolver_texto(tmp_path: Path) -> None:
    ruta = build_anki_deck(
        tmp_path / "vacia.apkg",
        cards=[],
        collection=anki_collection_bytes(tmp_path / "vacia.sqlite", notes=[], decks={1: "Mazo"}),
    )

    resultado = _extractor().extract(ruta, detected=detect_format(ruta))

    assert resultado.status is RepresentationStatus.EMPTY
    assert resultado.text == ""
    assert WarningCode.EMPTY_TEXT in resultado.warnings
    assert resultado.metadata["cards"] == 0


def test_un_contenedor_sin_coleccion_no_inventa_tarjetas(tmp_path: Path) -> None:
    ruta = tmp_path / "falso.apkg"
    with zipfile.ZipFile(ruta, "w") as archive:
        archive.writestr("otra-cosa.txt", "no soy una baraja")

    resultado = _extractor().extract(ruta, detected=detect_format(ruta))

    assert resultado.status is RepresentationStatus.FAILED
    assert "colección" in str(resultado.metadata["reason"])


def test_una_coleccion_corrupta_no_revienta_la_extraccion(tmp_path: Path) -> None:
    ruta = build_anki_deck(
        tmp_path / "rota.apkg", cards=[], collection=b"no soy sqlite", compressed=False
    )

    resultado = _extractor().extract(ruta, detected=detect_format(ruta))

    assert resultado.status is RepresentationStatus.FAILED
    assert WarningCode.EXTRACTOR_FAILED in resultado.warnings


def test_una_coleccion_antigua_lee_sus_tipos_de_nota(tmp_path: Path) -> None:
    """Antes de 2.1.28 los tipos y los mazos viven en JSON dentro de la tabla `col`."""
    sqlite = tmp_path / "collection.sqlite"
    conexion = sqlite3.connect(sqlite)
    try:
        conexion.executescript(
            """
            create table col (id integer primary key, models text, decks text);
            create table notes (
                id integer primary key, guid text, mid integer, mod integer, usn integer,
                tags text, flds text, sfld text, csum integer, flags integer, data text
            );
            create table cards (id integer primary key, nid integer, did integer);
            """
        )
        conexion.execute(
            "insert into col values (1, ?, ?)",
            (
                json.dumps(
                    {
                        "7": {
                            "name": "Básico antiguo",
                            "flds": [{"name": "Pregunta"}, {"name": "Respuesta"}],
                        }
                    }
                ),
                json.dumps({"3": {"name": "Mazo antiguo"}}),
            ),
        )
        conexion.execute(
            "insert into notes values (5, 'g', 7, 0, 0, '', ?, '', 0, 0, '')",
            (f"¿Qué dice?{ANKI_FIELD_SEPARATOR}Lo que dice.",),
        )
        conexion.execute("insert into cards values (50, 5, 3)")
        conexion.commit()
    finally:
        conexion.close()

    ruta = build_anki_deck(
        tmp_path / "antigua.apkg",
        cards=[],
        collection=sqlite.read_bytes(),
        member="collection.anki2",
        compressed=False,
    )
    resultado = _extractor().extract(ruta, detected=detect_format(ruta))

    assert resultado.status is RepresentationStatus.EXTRACTED
    assert "TARJETA 1. Mazo antiguo · Básico antiguo" in resultado.text
    assert "Pregunta: ¿Qué dice?" in resultado.text
    assert "Respuesta: Lo que dice." in resultado.text


def test_el_texto_se_recorta_y_se_dice(tmp_path: Path) -> None:
    ruta = build_anki_deck(
        tmp_path / "larga.apkg",
        cards=[],
        collection=anki_collection_bytes(
            tmp_path / "larga.sqlite",
            notes=[
                (numero, 1, f"Pregunta {numero}{ANKI_FIELD_SEPARATOR}Respuesta {numero}", "")
                for numero in range(1, 40)
            ],
            decks={1: "Mazo"},
        ),
    )

    resultado = _extractor(max_chars=200).extract(ruta, detected=detect_format(ruta))

    assert len(resultado.text) <= 200
    assert WarningCode.TRUNCATED in resultado.warnings
    # Los tramos se ajustan al texto recortado: ninguno señala texto que ya no está.
    for seccion in resultado.sections:
        assert seccion.char_end <= len(resultado.text)
