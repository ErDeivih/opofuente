"""La exportación de un tema a PDF: cabecera, markdown y nombre de archivo, sin PyMuPDF.

La aplicación compone el documento y lo convierte a HTML; el renderizador es infraestructura. Aquí
se prueban las reglas que no dependen de la tecnología: que el documento se explique solo, que el
markdown se interprete como en pantalla y que el nombre del archivo no pueda llevar rutas.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime

from opofuente.application.topic_pdf import (
    TopicPdfChapter,
    TopicPdfDocument,
    TopicPdfSection,
    build_topic_pdf_html,
    markdown_to_html,
    texto_para_pdf,
    topic_pdf_filename,
)


def _documento(*, estado: str = "published", titulo: str = "Redes locales") -> TopicPdfDocument:
    return TopicPdfDocument(
        topic_code="IV.10",
        topic_title=titulo,
        block_code="IV",
        block_title="Redes y comunicaciones",
        opposition_code="tai-age",
        opposition_name="Técnico Auxiliar de Informática",
        state=estado,
        downloaded_at=datetime(2026, 10, 31, 9, 0, tzinfo=UTC),
        generated_at=datetime(2026, 10, 29, 18, 30, tzinfo=UTC),
        app_version="0.1.0",
        chapters=(
            TopicPdfChapter(
                code="IV.10.1",
                title="Fundamentos",
                position=1,
                sections=(
                    TopicPdfSection(
                        number=1,
                        title="Qué es una red",
                        body_markdown="## Capas\n\nEl modelo **TCP/IP** tiene *cuatro* capas.",
                    ),
                ),
            ),
        ),
    )


def test_el_markdown_se_interpreta_como_en_pantalla() -> None:
    html = markdown_to_html(
        "\n".join(
            [
                "## Las cuatro capas",
                "",
                "El modelo **TCP/IP** y `RFC 1122`.",
                "",
                "| Capa | Unidad |",
                "| --- | --- |",
                "| Transporte | Segmento |",
                "",
                "- Primero",
                "- Segundo",
                "",
                "1. Uno",
                "2. Dos",
                "",
                "> Una cita",
            ]
        )
    )

    assert "<h3>Las cuatro capas</h3>" in html
    assert "<strong>TCP/IP</strong>" in html
    assert "<code>RFC 1122</code>" in html
    assert "<table><thead><tr><th>Capa</th><th>Unidad</th></tr></thead>" in html
    assert "<td>Transporte</td><td>Segmento</td>" in html
    assert "<ul><li>Primero</li><li>Segundo</li></ul>" in html
    assert "<ol><li>Uno</li><li>Dos</li></ol>" in html
    assert "<blockquote>Una cita</blockquote>" in html


def test_el_html_del_apunte_se_escapa_antes_de_dar_formato() -> None:
    html = markdown_to_html("<script>alert('x')</script> y **negrita**")

    assert "<script>" not in html
    assert "&lt;script&gt;" in html
    assert "<strong>negrita</strong>" in html


def test_las_marcas_de_revision_no_viajan_al_pdf() -> None:
    html = markdown_to_html("Texto revisable <!-- revisar: comprobar la cita --> final")

    assert "revisar" not in html
    assert "comprobar la cita" not in html
    assert "Texto revisable" in html
    assert "final" in html


def test_la_cabecera_dice_de_donde_sale_el_texto_y_cuando_se_genero() -> None:
    html = build_topic_pdf_html(_documento())

    assert "IV.10 · Redes locales" in html
    assert "Técnico Auxiliar de Informática (tai-age)" in html
    assert "Bloque IV · Redes y comunicaciones" in html
    assert "Estado: Publicado" in html
    assert "Descargado el 31/10/2026" in html
    assert "Apuntes generados el 29/10/2026" in html
    assert "Este tema está en borrador" not in html


def test_un_documento_en_borrador_lo_advierte_en_la_cabecera() -> None:
    html = build_topic_pdf_html(_documento(estado="draft"))

    assert "Estado: Borrador: texto pendiente de revisión" in html
    assert "Este tema está en borrador" in html
    assert "no debe citarse como material oficial" in html


def test_todos_los_capitulos_entran_en_orden_con_su_titulo_y_su_codigo() -> None:
    documento = replace(
        _documento(),
        chapters=(
            TopicPdfChapter(code="IV.10.2", title="Cableado", position=2),
            TopicPdfChapter(code="IV.10.1", title="Fundamentos", position=1),
        ),
    )

    html = build_topic_pdf_html(documento)

    assert html.index("1. Fundamentos") < html.index("2. Cableado")
    assert "IV.10.1" in html
    assert "IV.10.2" in html


def test_el_nombre_del_archivo_es_ascii_y_no_lleva_rutas() -> None:
    nombre = topic_pdf_filename(_documento(titulo="Redes locales: cableado y fibra óptica"))

    assert nombre == "tema-iv-10-redes-locales-cableado-y-fibra-optica.pdf"
    assert "/" not in nombre
    assert "\\" not in nombre
    assert nombre.isascii()


def test_un_titulo_larguisimo_se_recorta_y_sigue_siendo_un_pdf() -> None:
    nombre = topic_pdf_filename(_documento(titulo="Tema " + "muy largo " * 40))

    assert nombre.startswith("tema-iv-10-")
    assert nombre.endswith(".pdf")
    assert len(nombre) <= len("tema-iv-10-.pdf") + 60


def test_un_titulo_sin_letras_no_deja_un_nombre_vacio() -> None:
    assert topic_pdf_filename(_documento(titulo="¿¡!?")) == "tema-iv-10-tema.pdf"


def test_el_texto_estampado_se_sustituye_por_su_equivalente_en_latin1() -> None:
    # Guion largo, puntos suspensivos, comillas tipográficas y guion medio: los cuatro se escriben
    # con escape para que el propio fichero de pruebas no dependa de cómo se guarde el editor.
    entrada = "BORRADOR \u2014 no oficial \u2026 \u201cRedes\u201d \u2013 \u00f1"

    salida = texto_para_pdf(entrada)

    assert salida == 'BORRADOR - no oficial ... "Redes" - \u00f1'
    salida.encode("latin-1")


def test_el_texto_estampado_siempre_se_puede_codificar_en_latin1() -> None:
    # Espacio duro, viñeta, ideogramas y flecha: lo que no se puede representar se marca con '?'.
    entrada = "Tema IV.10 · Redes\u00a0locales \u2022 \u65e5\u672c\u8a9e \u2192 50 %"

    salida = texto_para_pdf(entrada)

    salida.encode("latin-1")
    assert salida.startswith("Tema IV.10 · Redes locales - ")
    assert salida.endswith(" 50 %")
    assert "?" in salida


def test_las_letras_acentuadas_no_se_pierden_al_preparar_el_texto() -> None:
    assert texto_para_pdf("Técnico Auxiliar de Informática, ¿qué?") == (
        "Técnico Auxiliar de Informática, ¿qué?"
    )
