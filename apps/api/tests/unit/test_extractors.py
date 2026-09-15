"""Pruebas de los extractores, por formato y con documentos sintéticos generados al vuelo.

Lo que se comprueba, formato a formato: que la **estructura** extraída es la esperada (páginas,
títulos, tabla), que la **calidad** se etiqueta con criterio, que los **avisos** dicen lo que se
descartó y que lo que no tiene extractor se **conserva** en lugar de inventarse.

Las pruebas negativas de seguridad (ZIP traversal, bombas, entidades externas) están en
`test_safe_inputs.py`; aquí se comprueba que los extractores las respetan.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from synthetic_documents import (
    build_bomb_docx,
    build_cp1252_text,
    build_csv,
    build_docx,
    build_docx_with_doctype,
    build_executable_bytes,
    build_html,
    build_json,
    build_json_broken,
    build_pdf_with_repeated_header,
    build_png,
    build_scanned_pdf,
    build_spreadsheet_like,
    build_text_pdf,
)

from opofuente.config import Settings
from opofuente.domain.errors import UnsafeContentError
from opofuente.domain.extraction import (
    Quality,
    RepresentationKind,
    RepresentationStatus,
    SectionType,
    WarningCode,
)
from opofuente.infrastructure.extractors import ExtractorRegistry
from opofuente.infrastructure.extractors.base import detect_format


@pytest.fixture
def registry() -> ExtractorRegistry:
    return ExtractorRegistry(Settings(_env_file=None))


# --- Detección de formato: manda el contenido, no la extensión -----------------------------


def test_el_pdf_se_detecta_por_su_firma_aunque_la_extension_mienta(tmp_path: Path) -> None:
    mentiroso = tmp_path / "documento.txt"
    build_text_pdf(mentiroso, pages=1)

    formato = detect_format(mentiroso)

    assert formato.family == "pdf"
    assert formato.matches_extension is False, "la extensión decía .txt y el contenido es un PDF"


def test_el_docx_se_reconoce_mirando_dentro_del_zip(tmp_path: Path) -> None:
    archivo = build_docx(tmp_path / "documento.docx")
    assert detect_format(archivo).family == "docx"


def test_una_hoja_de_calculo_no_se_confunde_con_un_docx(tmp_path: Path) -> None:
    archivo = build_spreadsheet_like(tmp_path / "hoja.xlsx")
    assert detect_format(archivo).family == "spreadsheet"


# --- PDF -----------------------------------------------------------------------------------


def test_pdf_nativo_extrae_pagina_a_pagina(tmp_path: Path) -> None:
    archivo = build_text_pdf(tmp_path / "temario.pdf", pages=3)

    resultado = ExtractorRegistry(Settings(_env_file=None)).extract(archivo)

    assert resultado.kind is RepresentationKind.NATIVE_TEXT
    assert resultado.status is RepresentationStatus.EXTRACTED
    assert resultado.page_count == 3
    assert [section.page_start for section in resultado.sections] == [1, 2, 3]
    assert all(section.section_type is SectionType.PAGE for section in resultado.sections)
    assert "Ley 39/2015" in resultado.text
    assert resultado.quality in {Quality.GOOD, Quality.USABLE_WITH_WARNINGS}
    assert resultado.indexable is True
    assert resultado.ocr_candidate is False


def test_pdf_escaneado_sin_capa_de_texto_queda_pendiente_y_candidato_a_ocr(tmp_path: Path) -> None:
    archivo = build_scanned_pdf(tmp_path / "escaneado.pdf", pages=2)

    resultado = ExtractorRegistry(Settings(_env_file=None)).extract(archivo)

    assert resultado.status is RepresentationStatus.PENDING
    assert resultado.ocr_candidate is True
    assert resultado.text.strip() == ""
    assert WarningCode.OCR_CANDIDATE in resultado.warnings
    assert WarningCode.EMPTY_TEXT in resultado.warnings
    assert resultado.quality is Quality.POOR
    assert resultado.indexable is False, "una representación pobre no entra en el índice"
    assert resultado.metadata["pages"] == 2


def test_pdf_con_cabecera_y_pie_repetidos_avisa_sin_tocar_el_original(tmp_path: Path) -> None:
    archivo = build_pdf_with_repeated_header(tmp_path / "repetido.pdf", pages=6)
    huella = archivo.stat().st_size, archivo.stat().st_mtime

    resultado = ExtractorRegistry(Settings(_env_file=None)).extract(archivo)

    assert WarningCode.HEADER_FOOTER_REPEATED in resultado.warnings
    assert resultado.quality is Quality.USABLE_WITH_WARNINGS
    # El texto repetido se conserva: se avisa, no se recorta.
    assert "CABECERA REPETIDA" in resultado.text
    assert (archivo.stat().st_size, archivo.stat().st_mtime) == huella


# --- DOCX ----------------------------------------------------------------------------------


def test_docx_extrae_titulos_parrafos_y_tabla(tmp_path: Path) -> None:
    archivo = build_docx(tmp_path / "tema.docx")

    resultado = ExtractorRegistry(Settings(_env_file=None)).extract(archivo)

    assert resultado.status is RepresentationStatus.EXTRACTED
    tipos = [section.section_type for section in resultado.sections]
    assert SectionType.TITLE in tipos
    assert SectionType.HEADING in tipos
    assert SectionType.TABLE in tipos
    assert "Tema 1. Organización del Estado" in resultado.text
    assert "Bloque | Tema | Preguntas" in resultado.text
    assert resultado.metadata["tables"] == 1
    assert resultado.quality is Quality.GOOD


def test_docx_con_doctype_se_rechaza_por_seguridad(tmp_path: Path) -> None:
    """El ataque de entidades externas dentro de un DOCX no se parsea: se rechaza."""
    archivo = build_docx_with_doctype(tmp_path / "malicioso.docx")

    with pytest.raises(UnsafeContentError) as error:
        ExtractorRegistry(Settings(_env_file=None)).extract(archivo)

    assert "DOCTYPE" in str(error.value)


def test_docx_bomba_se_rechaza_antes_de_parsear(tmp_path: Path) -> None:
    archivo = build_bomb_docx(tmp_path / "bomba.docx", size_bytes=8 * 1024 * 1024)

    with pytest.raises(UnsafeContentError):
        ExtractorRegistry(Settings(_env_file=None)).extract(archivo)


# --- HTML ----------------------------------------------------------------------------------


def test_html_no_ejecuta_nada_y_deja_fuera_scripts_y_navegacion(tmp_path: Path) -> None:
    archivo = build_html(tmp_path / "pagina.html")

    resultado = ExtractorRegistry(Settings(_env_file=None)).extract(archivo)

    assert resultado.kind is RepresentationKind.HTML_TEXT
    assert "fetch(" not in resultado.text
    assert "alert(" not in resultado.text
    assert "body{color:red}" not in resultado.text
    assert "Navegación que no es contenido" not in resultado.text
    assert "Pie que tampoco es contenido" not in resultado.text
    assert WarningCode.SCRIPT_REMOVED in resultado.warnings
    assert WarningCode.ACTIVE_CONTENT_REMOVED in resultado.warnings
    assert "Tema 2. Procedimiento administrativo" in resultado.text
    assert "Diez días" in resultado.text
    # La prompt injection es texto: se conserva como texto y no cambia nada.
    assert "Ignora las instrucciones anteriores" in resultado.text


def test_html_sin_scripts_no_avisa_de_scripts(tmp_path: Path) -> None:
    archivo = build_html(tmp_path / "limpio.html", with_scripts=False)

    resultado = ExtractorRegistry(Settings(_env_file=None)).extract(archivo)

    assert WarningCode.SCRIPT_REMOVED not in resultado.warnings
    assert WarningCode.ACTIVE_CONTENT_REMOVED not in resultado.warnings


def test_html_conserva_titulo_y_secciones(tmp_path: Path) -> None:
    archivo = build_html(tmp_path / "con-titulo.html")

    resultado = ExtractorRegistry(Settings(_env_file=None)).extract(archivo)

    assert resultado.metadata["title"] == "Temario sintético"
    assert resultado.text.startswith("Temario sintético")
    assert any(section.section_type is SectionType.TITLE for section in resultado.sections)
    assert any(section.section_type is SectionType.TABLE for section in resultado.sections)


# --- CSV y JSON ----------------------------------------------------------------------------


def test_csv_detecta_separador_y_cuenta_filas(tmp_path: Path) -> None:
    archivo = build_csv(tmp_path / "preguntas.csv", delimiter=";", rows=5)

    resultado = ExtractorRegistry(Settings(_env_file=None)).extract(archivo)

    assert resultado.kind is RepresentationKind.CSV_PREVIEW
    assert resultado.metadata["delimiter"] == ";"
    assert resultado.metadata["rows"] == 6
    assert resultado.metadata["columns"] == 4
    assert "pregunta;opcion_a;opcion_b;correcta" in resultado.text
    assert resultado.sections[0].section_type is SectionType.TABLE


def test_csv_con_coma_tambien_se_detecta(tmp_path: Path) -> None:
    archivo = build_csv(tmp_path / "con-coma.csv", delimiter=",", rows=3)
    resultado = ExtractorRegistry(Settings(_env_file=None)).extract(archivo)
    assert resultado.metadata["delimiter"] == ","


def test_csv_con_fila_defectuosa_no_aborta(tmp_path: Path) -> None:
    archivo = build_csv(tmp_path / "defectuoso.csv", rows=2, bad_row=True)

    resultado = ExtractorRegistry(Settings(_env_file=None)).extract(archivo)

    assert resultado.status is RepresentationStatus.EXTRACTED
    assert "fila incompleta" in resultado.text


def test_json_muestra_estructura_con_profundidad_acotada(tmp_path: Path) -> None:
    archivo = build_json(tmp_path / "datos.json")

    resultado = ExtractorRegistry(Settings(_env_file=None)).extract(archivo)

    assert resultado.kind is RepresentationKind.JSON_PREVIEW
    assert "convocatoria: sintetica-2026" in resultado.text
    assert "titulo: Tema uno" in resultado.text
    assert "activa: sí" in resultado.text
    assert "notas: (nulo)" in resultado.text


def test_json_roto_queda_fallido_sin_reventar(tmp_path: Path) -> None:
    archivo = build_json_broken(tmp_path / "roto.json")

    resultado = ExtractorRegistry(Settings(_env_file=None)).extract(archivo)

    assert resultado.status is RepresentationStatus.FAILED
    assert resultado.quality is Quality.FAILED
    assert WarningCode.MALFORMED_STRUCTURE in resultado.warnings


# --- Texto plano e imágenes -----------------------------------------------------------------


def test_texto_en_windows_1252_se_lee_y_se_avisa(tmp_path: Path) -> None:
    archivo = build_cp1252_text(tmp_path / "notas.txt")

    resultado = ExtractorRegistry(Settings(_env_file=None)).extract(archivo)

    assert "ñandú" in resultado.text
    assert resultado.metadata["encoding"] == "cp1252"
    assert WarningCode.LANGUAGE_UNKNOWN in resultado.warnings


def test_imagen_sin_ocr_queda_pendiente_y_no_inventa_texto(tmp_path: Path) -> None:
    archivo = build_png(tmp_path / "escaneo.png")

    resultado = ExtractorRegistry(Settings(_env_file=None)).extract(archivo)

    assert resultado.kind is RepresentationKind.IMAGE_METADATA
    assert resultado.status is RepresentationStatus.PENDING
    assert resultado.ocr_candidate is True
    assert WarningCode.OCR_NOT_EXECUTED in resultado.warnings
    assert resultado.metadata["width"] == 40
    assert resultado.metadata["height"] == 24
    # Lo que hay en `text` son metadatos, no texto del documento.
    assert "píxeles" in resultado.text


# --- Planes: qué se extrae, qué se conserva y qué se rechaza --------------------------------


def test_una_hoja_de_calculo_se_conserva_sin_extraer(tmp_path: Path) -> None:
    """DEBT-008: la hoja se copia (eso lo hace la importación) y aquí se decide no extraerla."""
    archivo = build_spreadsheet_like(tmp_path / "hoja.xlsx")

    plan = ExtractorRegistry(Settings(_env_file=None)).plan(archivo)

    assert plan.action == "preserve"
    assert "todavía no se extrae" in plan.reason


@pytest.mark.parametrize(
    "nombre",
    ["presentacion.pptx", "libro.epub", "audio.mp3", "video.mp4", "macro.docm"],
)
def test_los_formatos_sin_extractor_se_conservan(tmp_path: Path, nombre: str) -> None:
    archivo = tmp_path / nombre
    archivo.write_bytes(b"contenido sintetico")

    plan = ExtractorRegistry(Settings(_env_file=None)).plan(archivo)

    assert plan.action == "preserve", nombre


def test_un_ejecutable_se_rechaza_y_no_se_conserva(tmp_path: Path) -> None:
    archivo = build_executable_bytes(tmp_path / "instalador.exe")

    plan = ExtractorRegistry(Settings(_env_file=None)).plan(archivo)

    assert plan.action == "refuse"
    assert "ejecutable" in plan.reason


def test_un_zip_normal_se_expande(tmp_path: Path) -> None:
    from synthetic_documents import build_zip

    archivo = build_zip(tmp_path / "paquete.zip", {"apuntes.txt": b"contenido sintetico"})

    plan = ExtractorRegistry(Settings(_env_file=None)).plan(archivo)

    assert plan.action == "expand_zip"


def test_pedir_texto_de_algo_que_no_se_extrae_es_un_error_de_programa(tmp_path: Path) -> None:
    from opofuente.domain.errors import InvariantViolationError

    archivo = build_spreadsheet_like(tmp_path / "hoja.xlsx")

    with pytest.raises(InvariantViolationError):
        ExtractorRegistry(Settings(_env_file=None)).extract(archivo)


def test_el_registro_limita_los_caracteres_de_la_representacion(tmp_path: Path) -> None:
    ajustes = Settings(max_representation_chars=1000, _env_file=None)
    archivo = build_text_pdf(tmp_path / "largo.pdf", pages=8)

    resultado = ExtractorRegistry(ajustes).extract(archivo)

    assert len(resultado.text) == 1000
    assert WarningCode.TRUNCATED in resultado.warnings


def test_un_zip_dentro_de_otro_zip_se_conserva_sin_expandir() -> None:
    """El anidamiento se mide sobre la ruta de la entrada, con el límite de la configuración."""
    registro = ExtractorRegistry(Settings(max_zip_depth=1, _env_file=None))

    assert registro.nested_container_reason("paquete.zip") is None, "el de fuera sí se expande"
    motivo = registro.nested_container_reason("paquete.zip/inner.zip")
    assert motivo is not None
    assert "profundidad máxima 1" in motivo

    # Un nombre que solo se parece a un contenedor no cuenta, y subir el límite lo permite.
    assert registro.nested_container_reason("paquete.zip/temas/tema-01.txt") is None
    permisivo = ExtractorRegistry(Settings(max_zip_depth=2, _env_file=None))
    assert permisivo.nested_container_reason("paquete.zip/inner.zip") is None
