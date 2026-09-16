"""Pruebas de los extractores, por formato y con documentos sintéticos generados al vuelo.

Lo que se comprueba, formato a formato: que la **estructura** extraída es la esperada (páginas,
títulos, tabla), que la **calidad** se etiqueta con criterio, que los **avisos** dicen lo que se
descartó y que lo que no tiene extractor se **conserva** en lugar de inventarse.

Las pruebas negativas de seguridad (ZIP traversal, bombas, entidades externas) están en
`test_safe_inputs.py`; aquí se comprueba que los extractores las respetan.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from opofuente.config import Settings
from opofuente.domain.errors import UnsafeContentError
from opofuente.domain.extraction import (
    Quality,
    RepresentationKind,
    RepresentationStatus,
    SectionType,
    WarningCode,
    sections_are_consistent,
)
from opofuente.infrastructure.extractors import ExtractionPlan, ExtractorRegistry
from opofuente.infrastructure.extractors.base import detect_format
from opofuente_testing.synthetic_documents import (
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
    from opofuente_testing.synthetic_documents import build_zip

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
    """El anidamiento se decide con la profundidad persistida de la entrada, no con el nombre."""
    registro = ExtractorRegistry(Settings(max_zip_depth=1, _env_file=None))

    assert registro.nested_container_refusal(container_depth=0) is None, "el de fuera sí se expande"
    motivo = registro.nested_container_refusal(container_depth=1)
    assert motivo is not None
    assert "profundidad máxima 1" in motivo

    # Y con un límite mayor, el mismo contenedor anidado sí se expandiría.
    permisivo = ExtractorRegistry(Settings(max_zip_depth=2, _env_file=None))
    assert permisivo.nested_container_refusal(container_depth=1) is None


# --- el nombre original manda cuando el fichero vive en el almacén por hash (regresión S03) -------


#: Cada caso: cómo se llama el fichero de verdad, con qué contenido, y qué hay que decidir.
#: La ruta que se le pasa a `plan` es la del almacén (`<hash>`, sin extensión), que es el caso real.
@pytest.mark.parametrize(
    ("nombre", "contenido", "accion"),
    [
        ("programa.docm", b"contenido sintetico de un docm", "preserve"),
        ("notas.xlsm", b"contenido sintetico de un xlsm", "preserve"),
        ("locucion.mp3", b"ID3contenido sintetico", "preserve"),
        ("video.mp4", b"\x00\x00\x00\x18ftypmp42 sintetico", "preserve"),
        ("instalador.exe", b"MZ" + b"\x00" * 64, "refuse"),
        ("guion.ps1", b"Write-Output 'no se copia'", "refuse"),
    ],
)
def test_el_nombre_original_decide_igual_con_el_fichero_en_el_almacen(
    tmp_path: Path, nombre: str, contenido: bytes, accion: str
) -> None:
    """Un fichero guardado por hash no tiene extensión: la política sale del nombre de la entrada.

    Antes el registro miraba `path.suffix` de la ruta del almacén (el hash), así que un `.docm`
    acababa extrayéndose, un `.mp3` se trataba como binario y un `.exe` no se rechazaba por su
    nombre. Esta es la reproducción exacta de aquel fallo: la misma ruta, con y sin nombre.

    Se comprueba además que **sin** el nombre la decisión es otra, que es lo que demuestra que la
    prueba mide el arreglo y no otra cosa.
    """
    almacen = tmp_path / "sha256" / "ab" / "cd" / ("a" * 64)
    almacen.parent.mkdir(parents=True)
    almacen.write_bytes(contenido)

    registro = ExtractorRegistry(Settings(_env_file=None))
    sin_nombre = registro.plan(almacen)
    con_nombre = registro.plan(almacen, name=nombre)

    assert con_nombre.action == accion, f"{nombre} debería decidir {accion}"
    assert _decision(sin_nombre) != _decision(con_nombre), (
        f"{nombre}: sin el nombre original la decisión cambia, y eso es lo que se está probando"
    )


def _decision(plan: ExtractionPlan) -> tuple[str, str, str]:
    """Lo que identifica una decisión: qué se hace, por qué y con qué extractor."""
    return (plan.action, plan.reason, plan.extractor.name if plan.extractor else "")


def test_sin_el_nombre_original_un_markdown_pierde_secciones_y_un_json_su_vista_previa(
    tmp_path: Path,
) -> None:
    """Los otros dos casos del mismo fallo, donde cambia el extractor elegido y no la acción.

    Un `.md` guardado por hash se extrae igual (el contenido es texto), pero **sin secciones**: los
    encabezados Markdown se detectan por la extensión. Un `.json` guardado por hash se trata como
    texto plano en lugar de como estructura: la vista previa del JSON se pierde.
    """
    registro = ExtractorRegistry(Settings(_env_file=None))
    almacen = tmp_path / "sha256" / "ab" / "cd" / ("b" * 64)
    almacen.parent.mkdir(parents=True)

    almacen.write_bytes(b"# Tema 1\n\nTexto sintetico del tema.")
    con_nombre = registro.extract(almacen, plan=registro.plan(almacen, name="tema.md"))
    sin_nombre = registro.extract(almacen, plan=registro.plan(almacen))
    assert con_nombre.sections, "con el nombre original el Markdown deja sus encabezados"
    assert not sin_nombre.sections, "sin él, el mismo fichero no tiene secciones"

    almacen.write_bytes(b'{"temas": ["uno", "dos"]}')
    con_nombre = registro.plan(almacen, name="apuntes.json")
    sin_nombre = registro.plan(almacen)
    assert con_nombre.extractor is not None
    assert con_nombre.extractor.name == "json_preview"
    assert sin_nombre.extractor is not None
    assert sin_nombre.extractor.name == "plain_text", (
        "sin el nombre se pierde la vista de estructura"
    )


def test_un_ejecutable_con_nombre_inocente_se_rechaza_por_su_firma(tmp_path: Path) -> None:
    """Los bytes mandan: un `.txt` con cabecera `MZ` (PE) es un ejecutable y no se admite."""
    registro = ExtractorRegistry(Settings(_env_file=None))
    archivo = tmp_path / "apuntes.txt"
    archivo.write_bytes(b"MZ" + b"\x00" * 128)

    plan = registro.plan(archivo, name="apuntes.txt")

    assert plan.action == "refuse"
    assert "firma de ejecutable" in plan.reason
    assert registro.refusal_by_signature(archivo) is not None


def test_un_elf_se_reconoce_por_su_firma(tmp_path: Path) -> None:
    """La otra firma habitual en Binutils/Linux: `\\x7fELF`."""
    archivo = tmp_path / "binario.bin"
    archivo.write_bytes(b"\x7fELF" + b"\x00" * 64)

    plan = ExtractorRegistry(Settings(_env_file=None)).plan(archivo, name="binario.bin")

    assert plan.action == "refuse"
    assert "ELF" in plan.reason


# --- las secciones señalan siempre el texto que se guarda (regresión S03) -------------------------


#: Un documento sintético de cada familia que produce secciones, para comprobar la invariante.
def _fixtures_con_secciones(root: Path) -> list[tuple[str, Path]]:
    from opofuente_testing.synthetic_documents import build_zip

    build_zip(root / "paquete.zip", {"leeme.txt": b"Contenido sintetico del paquete."})
    return [
        ("pdf", build_text_pdf(root / "temario.pdf", pages=3)),
        ("pdf-cabecera-repetida", build_pdf_with_repeated_header(root / "repetido.pdf", pages=6)),
        ("docx", build_docx(root / "tema.docx")),
        ("html-con-titulo", build_html(root / "material.html")),
        ("markdown", _write(root / "apuntes.md", "# Tema 1\n\n## Apartado\n\nTexto sintetico.")),
        ("csv", build_csv(root / "preguntas.csv", rows=4)),
        ("json", build_json(root / "datos.json")),
        ("imagen", build_png(root / "escaneo.png")),
    ]


def _write(path: Path, content: str) -> Path:
    path.write_text(content, encoding="utf-8")
    return path


def test_las_secciones_caen_siempre_dentro_del_texto_guardado(tmp_path: Path) -> None:
    """Invariante de toda representación: `0 ≤ char_start ≤ char_end ≤ char_count`.

    Los extractores miden los tramos mientras construyen el texto, y después el texto se normaliza y
    se recorta. Antes, esos offsets se calculaban **antes** de normalizar y de truncar (y, en HTML,
    antes de anteponer el título), así que una sección podía señalar texto que no estaba en la
    representación: el fallo se reprodujo con una sección titulada «Encabezado real» cuyo rango
    apuntaba a `Titulo meta\n\nEn`.
    """
    registro = ExtractorRegistry(Settings(_env_file=None))
    for nombre, archivo in _fixtures_con_secciones(tmp_path):
        resultado = registro.extract(archivo)
        assert sections_are_consistent(resultado.text, resultado.sections), (
            f"{nombre}: alguna sección se sale del texto ({resultado.char_count} caracteres)"
        )
        for section in resultado.sections:
            # Y además el tramo tiene que ser el texto que dice ser: se compara con el corte real.
            fragmento = resultado.text[section.char_start : section.char_end]
            assert len(fragmento) == section.length, (
                f"{nombre}: el tramo {section.position} no cuadra"
            )


def test_las_secciones_se_ajustan_cuando_el_texto_se_recorta(tmp_path: Path) -> None:
    """Con el texto recortado por el límite, las secciones que ya no existen se descartan."""
    ajustes = Settings(max_representation_chars=1000, max_text_bytes=10_000, _env_file=None)
    largo = _write(
        tmp_path / "apuntes.md",
        "\n".join(
            f"## Apartado {index}\n\nTexto sintetico del apartado {index}." for index in range(80)
        ),
    )

    resultado = ExtractorRegistry(ajustes).extract(largo)

    assert WarningCode.TRUNCATED in resultado.warnings
    assert resultado.char_count == 1000
    assert sections_are_consistent(resultado.text, resultado.sections)
    assert resultado.sections, "quedan las secciones que sí entran en el texto recortado"
    assert all(section.char_end <= 1000 for section in resultado.sections)


def test_el_titulo_del_html_no_desplaza_las_secciones(tmp_path: Path) -> None:
    """El título se antepone al texto: los tramos tienen que contar con él desde el principio."""
    archivo = _write(
        tmp_path / "material.html",
        "<html><head><title>Titulo meta</title></head><body>"
        "<h1>Encabezado real</h1><p>Parrafo sintetico del documento.</p></body></html>",
    )

    resultado = ExtractorRegistry(Settings(_env_file=None)).extract(archivo)

    assert resultado.text.startswith("Titulo meta")
    primera = resultado.sections[0]
    assert primera.title == "Encabezado real"
    assert resultado.text[primera.char_start : primera.char_end] == "Encabezado real"


def test_la_normalizacion_unicode_no_desplaza_las_secciones(tmp_path: Path) -> None:
    """NFC puede **acortar** un tramo: medirlo antes de normalizar desplazaba los siguientes.

    Reproducción del fallo: un encabezado escrito con `e` + acento combinante (U+0301) mide un
    carácter más que su forma normalizada. Si el tramo se medía antes de normalizar, el título
    apuntaba a `rimera` y todas las secciones siguientes quedaban desplazadas. Lo que se comprueba
    aquí es que **el fragmento señalado es el que dice ser**, no solo que esté dentro del texto.
    """
    combinante = "Primera\u0301 parte"
    archivo = _write(
        tmp_path / "apuntes.md",
        f"# {combinante}\n\nTexto de la primera parte.\n\n## Segunda parte\n\nTexto de la segunda.",
    )

    resultado = ExtractorRegistry(Settings(_env_file=None)).extract(archivo)

    assert [section.title for section in resultado.sections] == [
        "Primerá parte",
        "Segunda parte",
    ]
    for section in resultado.sections:
        # El tramo de Markdown abarca la línea entera (`# Título\n`), así que lo que se comprueba es
        # que **contiene** su título tal cual: con el desplazamiento de un carácter, el tramo se
        # quedaba en `# Primerá par` y el título ya no cabía dentro.
        fragmento = resultado.text[section.char_start : section.char_end]
        assert section.title in fragmento, (
            f"la sección {section.position} apunta a {fragmento!r} y no contiene {section.title!r}"
        )
        assert resultado.text.index(section.title) == resultado.text.index(
            section.title, section.char_start, section.char_end
        ), "el título aparece antes del tramo que lo señala"


@pytest.mark.parametrize(
    ("caracter", "bytes_utf8"),
    [("á", 2), ("€", 3), ("😀", 4)],
)
def test_un_corte_de_bytes_no_parte_caracteres_utf8(
    tmp_path: Path, caracter: str, bytes_utf8: int
) -> None:
    """El tope de lectura cae donde caiga: nunca en mitad de un carácter.

    Si el corte partía un carácter de 2, 3 o 4 bytes, la decodificación UTF-8 fallaba y el bloque
    entero se reinterpretaba como Windows-1252: el texto salía corrupto y con una codificación
    informada que no era la suya.
    """
    relleno = "Texto sintetico. " * 80
    base = len(relleno.encode("utf-8"))
    assert base >= 1024, "el tope de configuración exige al menos un kibibyte"
    for desplazamiento in range(bytes_utf8):
        # El corte se coloca dentro del carácter: en su primer byte, en el segundo o en el tercero.
        ajustes = Settings(max_text_bytes=base + desplazamiento, _env_file=None)
        archivo = tmp_path / f"corte-{bytes_utf8}-{desplazamiento}.txt"
        archivo.write_text(relleno + caracter + " resto del material sintetico.", encoding="utf-8")

        resultado = ExtractorRegistry(ajustes).extract(archivo)

        assert WarningCode.TRUNCATED in resultado.warnings
        assert resultado.metadata["encoding"] == "utf-8", (
            f"el corte partió {caracter!r} y el texto se releyó como Windows-1252"
        )
        assert caracter not in resultado.text, "el carácter partido no se inventa a medias"
        assert "Texto sintetico." in resultado.text, "lo que sí cabía se lee entero"


@pytest.mark.parametrize("formato", ["html", "docx", "csv", "json"])
def test_cada_tramo_señala_su_contenido_con_unicode_combinante(
    tmp_path: Path, formato: str
) -> None:
    """Los tramos de HTML, DOCX, CSV y JSON también se miden sobre el texto normalizado.

    Es la reproducción exacta del fallo del propietario, pero en los extractores que construyen el
    texto por piezas: medir una pieza antes de normalizarla (NFC puede acortarla) desplazaba todo lo
    que venía después, así que una sección señalaba un contenido que no era el suyo aunque sus
    límites siguieran dentro del texto.
    """
    combinante = "Primera\u0301 parte"
    normalizado = "Primerá parte"
    siguiente = "Segunda parte"

    if formato == "html":
        archivo = _write(
            tmp_path / "material.html",
            f"<html><body><h1>{combinante}</h1><p>Texto de la primera parte.</p>"
            f"<h2>{siguiente}</h2><p>Texto de la segunda.</p></body></html>",
        )
    elif formato == "docx":
        import docx

        archivo = tmp_path / "tema.docx"
        documento = docx.Document()
        documento.add_heading(combinante, level=1)
        documento.add_paragraph("Texto de la primera parte.")
        documento.add_heading(siguiente, level=2)
        documento.add_paragraph("Texto de la segunda.")
        documento.save(str(archivo))
    elif formato == "csv":
        archivo = _write(
            tmp_path / "preguntas.csv",
            f"pregunta;opcion\n{combinante};A\nPregunta dos;B\n",
        )
    else:
        archivo = _write(
            tmp_path / "datos.json",
            json.dumps({"primera": combinante, "segunda": siguiente}, ensure_ascii=False),
        )

    resultado = ExtractorRegistry(Settings(_env_file=None)).extract(archivo)

    assert resultado.sections, f"{formato}: debería dejar tramos"
    for section in resultado.sections:
        fragmento = resultado.text[section.char_start : section.char_end]
        assert fragmento, f"{formato}: el tramo {section.position} señala texto vacío"
    # En HTML y DOCX los tramos son las piezas exactas: ahí se puede exigir igualdad.
    if formato in {"html", "docx"}:
        fragmentos = [resultado.text[s.char_start : s.char_end] for s in resultado.sections]
        assert fragmentos == [
            normalizado,
            "Texto de la primera parte.",
            siguiente,
            "Texto de la segunda.",
        ], f"{formato}: los tramos no coinciden con su contenido"
    else:
        # En CSV y JSON el tramo es todo el texto, pero el combinante tiene que estar normalizado
        # en el sitio que dice el tramo (no desplazado por haberlo medido antes).
        assert normalizado in resultado.text
        assert resultado.text.index(normalizado) < len(resultado.text)


def test_un_corte_que_ya_es_valido_no_pierde_ningun_byte(tmp_path: Path) -> None:
    """Si el bloque cortado ya decodifica como UTF-8, se conserva **entero**.

    Reproducción del fallo: el recorte empezaba probando `len(data) - 1`, así que siempre perdía un
    byte aunque el corte fuera perfectamente válido (1025 bytes ASCII con límite 1024 daban 1023).
    """
    from opofuente.infrastructure.extractors.base import read_bounded

    ascii_file = tmp_path / "ascii.txt"
    ascii_file.write_bytes(b"a" * 1025)

    data, truncated = read_bounded(ascii_file, max_bytes=1024)

    assert truncated is True
    assert len(data) == 1024, f"se perdieron {1024 - len(data)} bytes sin motivo"
    data.decode("utf-8")

    # Y con un fichero que cabe justo, no hay nada que recortar.
    justo = tmp_path / "justo.txt"
    justo.write_bytes(b"b" * 1024)
    completo, truncado = read_bounded(justo, max_bytes=1024)
    assert len(completo) == 1024
    assert truncado is False


@pytest.mark.parametrize("caracter", ["á", "€", "😀"])
def test_un_corte_que_parte_un_caracter_solo_retrocede_lo_necesario(
    tmp_path: Path, caracter: str
) -> None:
    """Si el corte parte un carácter, solo se retroceden sus bytes, no más."""
    from opofuente.infrastructure.extractors.base import read_bounded

    relleno = "Texto sintetico. " * 80
    base = len(relleno.encode("utf-8"))
    archivo = tmp_path / f"corte-{len(caracter.encode('utf-8'))}.txt"
    archivo.write_text(relleno + caracter + " resto del material.", encoding="utf-8")

    data, truncated = read_bounded(archivo, max_bytes=base + 1)

    assert truncated is True
    assert len(data) == base, "se retrocedió de más: el relleno cabía entero"
    assert data.decode("utf-8") == relleno


@pytest.mark.parametrize(
    ("nombre", "contenido", "esperado"),
    [
        # Byte 0xFF: nunca es válido en UTF-8. No se recorta nada: el contenido no es UTF-8 y
        # recortar el final no lo arreglaría (quien decodifica decide, avisando de la codificación).
        ("solo-0xff", b"\xff" + b"x" * 2048, 1024),
        # 0xFF en medio del bloque: el error no está al final, así que no se toca.
        ("0xff-en-medio", b"a" * 512 + b"\xff" + b"b" * 1024, 1024),
        # Continuación inválida al principio de una secuencia (0xC3 sin continuación válida).
        ("continuacion-invalida", b"a" * 1024 + b"\xc3\x28", 1024),
        # Secuencia que **no** se completa con lo que viene después (`\xe2\x82m` no es UTF-8
        # válido): el contenido no es UTF-8 en ninguna de sus interpretaciones, así que se conserva
        # entero y el extractor declarará la codificación que use.
        ("secuencia-invalida-al-final", b"a" * 1022 + b"\xe2\x82" + b"m", 1024),
        # Aquí sí hay una secuencia UTF-8 partida de verdad: el bloque acaba en `\xe2\x82` y lo que
        # viene después (`\xac`) la completa, así que el fichero es UTF-8 y se retira la parte
        # incompleta. Es la misma situación que comprueba, ya con el extractor entero, el test
        # `test_un_caracter_utf8_cortado_por_la_mitad_si_se_recorta`.
        ("secuencia-truncada-al-final", b"a" * 1022 + "€".encode() + b"resto.", 1022),
        # 0xFF como último byte del bloque: no es una secuencia truncada sino un byte inválido, así
        # que no se recorta (quitarlo no arreglaría la decodificación y perdería un byte real).
        ("0xff-al-final", b"a" * 1023 + b"\xff" + b"x", 1024),
        # Secuencias partidas por el tope **seguidas inmediatamente de otro carácter multibyte**:
        # solo cuenta la secuencia que cruza el límite, no lo que venga después. Si se miran bytes
        # de más, la segunda secuencia (incompleta) hace fallar la comprobación y el bloque se queda
        # con un byte suelto.
        (
            "corte-de-2-bytes-con-euro-despues",
            b"a" * 1023 + "é".encode() + "€".encode() + b"resto.",
            1023,
        ),
        (
            "corte-de-2-bytes-con-emoji-despues",
            b"a" * 1023 + "é".encode() + "😀".encode() + b"r.",
            1023,
        ),
        (
            "corte-de-3-bytes-con-euro-despues",
            b"a" * 1023 + "€".encode() + "€".encode() + b"resto.",
            1023,
        ),
        (
            "corte-de-4-bytes-con-euro-despues",
            b"a" * 1022 + "😀".encode() + "€".encode() + b"resto.",
            1022,
        ),
    ],
)
def test_los_bloques_que_no_son_utf8_no_se_recortan_por_el_final(
    tmp_path: Path, nombre: str, contenido: bytes, esperado: int
) -> None:
    """Solo se retrocede ante una secuencia **incompleta** al final, no ante cualquier error.

    Un 0xFF o una continuación inválida no son UTF-8 y recortar el final no lo arregla: lo honesto
    es entregar el bloque tal cual y que el extractor avise de la codificación que ha usado. Si se
    recortara a ciegas, además se perdería contenido que sí estaba.
    """
    from opofuente.infrastructure.extractors.base import read_bounded

    archivo = tmp_path / f"{nombre}.bin"
    archivo.write_bytes(contenido)

    data, truncated = read_bounded(archivo, max_bytes=1024)

    assert truncated is True
    assert len(data) == esperado, f"{nombre}: se devolvieron {len(data)} bytes"


def test_los_espacios_significativos_se_conservan_en_csv_y_json(tmp_path: Path) -> None:
    """CSV y JSON son datos: los espacios repetidos son contenido, no presentación.

    La regla del dominio lo dice expresamente (`normalise_text`: «no se colapsan espacios»). Con el
    colapso aplicado a todo, `Con  dos  espacios;A  B` se guardaba como `Con dos espacios;A B`,
    que es otro contenido.
    """
    registro = ExtractorRegistry(Settings(_env_file=None))

    csv_path = tmp_path / "preguntas.csv"
    csv_path.write_text("pregunta;opcion_a\nCon  dos  espacios;A  B\n", encoding="utf-8")
    csv_result = registro.extract(csv_path)
    assert "Con  dos  espacios;A  B" in csv_result.text, csv_result.text
    assert "Con dos espacios" not in csv_result.text

    json_path = tmp_path / "datos.json"
    json_path.write_text(
        json.dumps({"titulo": "Con  dos  espacios", "otro": "A  B"}, ensure_ascii=False),
        encoding="utf-8",
    )
    json_result = registro.extract(json_path)
    assert "Con  dos  espacios" in json_result.text, json_result.text
    assert "A  B" in json_result.text

    # HTML mantiene el colapso: ahí un bloque de espacios es presentación y el navegador lo muestra
    # como uno solo.
    html_path = tmp_path / "material.html"
    html_path.write_text("<html><body><p>Con  dos  espacios</p></body></html>", encoding="utf-8")
    html_result = registro.extract(html_path)
    assert "Con dos espacios" in html_result.text


def test_una_letra_cp1252_en_el_limite_no_se_recorta(tmp_path: Path) -> None:
    """Un `0xC3` en el límite es `Ã` en Windows-1252: no puede tratarse como UTF-8 partido.

    El recorte mira lo que viene **después** del corte: si esos bytes no completan la secuencia, ese
    byte no era UTF-8 y el bloque se conserva entero, de modo que el texto mantiene su `Ã` y la
    codificación se declara como CP-1252 en lugar de perder un carácter en silencio.
    """
    relleno = "a" * 1023
    archivo = tmp_path / "cp1252.txt"
    archivo.write_bytes(relleno.encode("cp1252") + "Ã".encode("cp1252") + b"resto del material.")

    resultado = ExtractorRegistry(
        Settings(max_text_bytes=1024, max_representation_chars=100_000, _env_file=None)
    ).extract(archivo)

    assert WarningCode.TRUNCATED in resultado.warnings
    assert resultado.metadata["encoding"] == "cp1252", "el byte 0xC3 no es UTF-8 partido"
    assert resultado.text.endswith("Ã"), f"se perdió la Ã: {resultado.text[-5:]!r}"
    assert len(resultado.text) == 1024


def test_un_caracter_utf8_cortado_por_la_mitad_si_se_recorta(tmp_path: Path) -> None:
    """Y si el corte parte una secuencia UTF-8 de verdad, sí se retira la parte incompleta.

    Es la otra cara del mismo caso: el fichero es UTF-8 y los bytes que siguen al corte completan el
    carácter, así que el bloque se recorta para no entregar una secuencia a medias.
    """
    archivo = tmp_path / "utf8.txt"
    archivo.write_bytes(b"a" * 1023 + "á".encode() + b"resto.")

    resultado = ExtractorRegistry(
        Settings(max_text_bytes=1024, max_representation_chars=100_000, _env_file=None)
    ).extract(archivo)

    assert resultado.metadata["encoding"] == "utf-8"
    assert len(resultado.text) == 1023, "el carácter partido no entra"
    assert resultado.text == "a" * 1023


@pytest.mark.parametrize("siguiente", ["€", "😀"])
def test_el_caracter_que_sigue_al_corte_no_estorba(tmp_path: Path, siguiente: str) -> None:
    """Tras el carácter partido viene **otro** multibyte: se mira solo la primera secuencia.

    Reproducción del fallo: la comprobación tomaba del `tail` los bytes que caben en una secuencia
    (`4 - len(parcial)`) en vez de los que le faltan a **esa** secuencia, así que al incluir el
    principio del `€` o del emoji la decodificación fallaba y el bloque se conservaba entero: el
    fichero —que es UTF-8— se leía como CP-1252 y el texto acababa con una `Ã` inventada.
    """
    archivo = tmp_path / "utf8-seguido.txt"
    archivo.write_bytes(b"a" * 1023 + "é".encode() + siguiente.encode() + b"resto del material.")

    resultado = ExtractorRegistry(
        Settings(max_text_bytes=1024, max_representation_chars=100_000, _env_file=None)
    ).extract(archivo)

    assert WarningCode.TRUNCATED in resultado.warnings
    assert resultado.metadata["encoding"] == "utf-8", (
        "el fichero es UTF-8: no hay que reinterpretarlo"
    )
    assert resultado.text == "a" * 1023, f"el carácter partido no entra: {resultado.text[-5:]!r}"


# --- lectura acotada por extractor (regresión S03) -----------------------------------------------


def test_un_fichero_de_texto_mas_grande_que_el_tope_se_lee_acotado(tmp_path: Path) -> None:
    """Un TXT enorme no se carga entero: se lee el principio, se avisa y el texto es utilizable."""
    ajustes = Settings(max_text_bytes=2048, max_representation_chars=100_000, _env_file=None)
    archivo = tmp_path / "apuntes.txt"
    archivo.write_text("Material sintetico de prueba. " * 5000, encoding="utf-8")
    assert archivo.stat().st_size > 2048

    resultado = ExtractorRegistry(ajustes).extract(archivo)

    assert WarningCode.TRUNCATED in resultado.warnings
    assert resultado.metadata["read_truncated"] is True
    assert len(resultado.text) <= 2048
    assert resultado.status is RepresentationStatus.EXTRACTED


def test_un_json_mas_grande_que_su_tope_se_declara_en_lugar_de_cargarse(
    tmp_path: Path,
) -> None:
    """El JSON hay que parsearlo entero: si no cabe en el tope, se dice y no se intenta.

    Antes se hacía `read_bytes()` y `json.loads` del fichero completo: un JSON válido de cientos de
    megabytes (permitido por el límite de ingesta) podía agotar la memoria del equipo.
    """
    ajustes = Settings(max_json_bytes=4096, max_representation_chars=100_000, _env_file=None)
    archivo = tmp_path / "datos.json"
    archivo.write_text(
        json.dumps({"temas": [f"Tema sintetico {index}" for index in range(2000)]}),
        encoding="utf-8",
    )
    assert archivo.stat().st_size > 4096

    resultado = ExtractorRegistry(ajustes).extract(archivo)

    assert resultado.status is RepresentationStatus.FAILED
    assert WarningCode.TOO_LARGE in resultado.warnings
    assert resultado.text == ""
    assert resultado.metadata["limit_bytes"] == 4096


def test_una_imagen_mas_grande_que_su_tope_se_conserva_sin_describir(tmp_path: Path) -> None:
    """Tampoco se decodifica una imagen enorme solo para saber cuánto mide."""
    ajustes = Settings(max_image_bytes=1024, _env_file=None)
    archivo = build_png(tmp_path / "grande.png", width=800, height=800)
    assert archivo.stat().st_size > 1024

    resultado = ExtractorRegistry(ajustes).extract(archivo)

    assert WarningCode.TOO_LARGE in resultado.warnings
    assert resultado.status is RepresentationStatus.PENDING, "se conserva y queda pendiente de OCR"
    assert resultado.ocr_candidate is True
