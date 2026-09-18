"""Pruebas unitarias del renderizado de exportaciones (06_QUESTIONS §8).

Lo que se prueba aquí es el texto que sale del fichero: que el CSV sea un CSV de verdad (se lee con
el lector de CSV de Python, no a ojo), que una celda que parece una fórmula se neutralice, que la
procedencia viaje y que lo que no tiene respuesta lo diga en lugar de salir en blanco.
"""

from __future__ import annotations

import csv
import io
from datetime import UTC, datetime

from opofuente.domain.export import (
    ANKI_FIELDS,
    CSV_DELIMITER,
    ExportRow,
    export_warnings,
    render_anki_csv,
    render_markdown,
    restricted_rows,
)

MOMENTO = datetime(2026, 9, 18, 12, 0, tzinfo=UTC)


def _fila(**cambios: object) -> ExportRow:
    base = {
        "stable_key": "q001",
        "question": "El plazo del procedimiento es de diez dias habiles:",
        "options": (("a", "Verdadero"), ("b", "Falso")),
        "correct_option_keys": ("a",),
        "explanation": "Lo dice el articulo 5",
        "citations": ("Temario, pag. 12",),
        "document_titles": ("Temario oficial",),
        "document_versions": ("ver-1",),
        "opposition": "Tecnicos Auxiliares de Informatica",
        "topic": "Plazos",
        "origin_type": "private",
        "set_title": "Examen de prueba",
        "key_label": "plantilla v1",
        "restricted": False,
    }
    base.update(cambios)
    return ExportRow(**base)  # type: ignore[arg-type]


def _leer_csv(contenido: str) -> list[list[str]]:
    """El CSV leído como CSV: si el lector no lo entiende, el fichero no vale para Anki."""
    return list(csv.reader(io.StringIO(contenido), delimiter=CSV_DELIMITER))


def test_el_csv_lleva_cabecera_separador_y_la_procedencia_de_cada_pregunta() -> None:
    contenido, avisos = render_anki_csv([_fila()])

    filas = _leer_csv(contenido)
    assert filas[0] == list(ANKI_FIELDS)
    assert len(filas) == 2, "una pregunta, un registro"
    assert len(filas[1]) == len(ANKI_FIELDS)
    assert avisos == ()

    campos = dict(zip(ANKI_FIELDS, filas[1], strict=True))
    assert campos["pregunta"] == "El plazo del procedimiento es de diez dias habiles:"
    assert campos["opciones"] == "A) Verdadero\nB) Falso"
    assert campos["respuesta"] == "A"
    assert campos["explicacion"] == "Lo dice el articulo 5"
    assert campos["citas"] == "Temario, pag. 12"
    assert campos["oposicion"] == "Tecnicos Auxiliares de Informatica"
    assert campos["tema"] == "Plazos"
    assert campos["origen"] == "private"
    assert campos["conjunto"] == "Examen de prueba"
    assert campos["plantilla"] == "plantilla v1"
    assert campos["documentos"] == "Temario oficial (ver-1)"


def test_una_celda_con_comillas_y_saltos_de_linea_no_rompe_el_csv() -> None:
    contenido, _ = render_anki_csv(
        [_fila(question='Dijo "el plazo" y añadió:\nque era de diez días')]
    )
    filas = _leer_csv(contenido)
    assert len(filas) == 2, "un salto dentro de la celda no crea un registro nuevo"
    campos = dict(zip(ANKI_FIELDS, filas[1], strict=True))
    assert campos["pregunta"] == 'Dijo "el plazo" y añadió:\nque era de diez días'


def test_una_celda_que_parece_una_formula_se_neutraliza_y_se_avisa() -> None:
    contenido, avisos = render_anki_csv(
        [_fila(question='=HYPERLINK("http://x","pulsa")'), _fila(stable_key="q002")]
    )
    assert "'=HYPERLINK" in contenido
    assert avisos and "neutralizado" in avisos[0]
    # Un guion seguido de texto es prosa, no una fórmula: no se toca.
    prosa, avisos_prosa = render_anki_csv([_fila(question="- no me acuerdo del plazo")])
    assert "- no me acuerdo del plazo" in prosa
    assert avisos_prosa == ()


def test_una_pregunta_sin_respuesta_conocida_lo_dice_en_el_fichero() -> None:
    contenido, _ = render_anki_csv([_fila(correct_option_keys=())])
    assert "sin respuesta conocida" in contenido
    avisos = export_warnings([_fila(correct_option_keys=())])
    assert any("no tienen respuesta conocida" in aviso for aviso in avisos)


def test_el_markdown_lleva_la_ficha_la_cita_y_la_procedencia() -> None:
    contenido = render_markdown(
        [_fila()], title="Repaso de plazos", generated_at=MOMENTO, version="0.0.0-test"
    )
    assert contenido.startswith("---\n")
    assert "titulo: Repaso de plazos" in contenido
    assert "opofuente: 0.0.0-test" in contenido
    assert "## 1. El plazo del procedimiento" in contenido
    assert "- **A)** Verdadero" in contenido
    assert "**Respuesta:** A" in contenido
    assert "Evidencia:" in contenido
    assert "- Temario, pag. 12" in contenido
    assert "- tema: Plazos" in contenido
    assert "- documentos: Temario oficial (ver-1)" in contenido
    # La respuesta correcta nunca se enseña como una opción marcada: la ficha la dice aparte.
    assert "sin respuesta conocida" not in contenido


def test_el_material_restringido_se_marca_en_la_ficha_y_se_avisa() -> None:
    filas = [_fila(restricted=True), _fila(stable_key="q002")]
    contenido = render_markdown(filas, title="Banco", generated_at=MOMENTO, version="0.0.0-test")
    assert "derechos: material restringido" in contenido
    assert len(restricted_rows(filas)) == 1
    avisos = export_warnings(filas)
    assert any("derechos restringidos" in aviso for aviso in avisos)


def test_una_pregunta_sin_cita_se_avisa_porque_no_se_puede_comprobar() -> None:
    avisos = export_warnings([_fila(citations=(), document_titles=(), document_versions=())])
    assert any("no citan ninguna evidencia" in aviso for aviso in avisos)
