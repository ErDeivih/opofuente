"""El renderizador del PDF, ejecutado de verdad contra la PyMuPDF instalada.

`test_topic_pdf.py` prueba el documento y el markdown sin abrir la librería. Aquí se pide el PDF
real: que se pueda abrir, que el texto llegue a la página, que la paginación cuadre en un tema de
varias páginas, que el borrador se anuncie y que un cuerpo que no cabe se corte en vez de girar
para siempre. Nada de esto escribe en disco: los bytes salen de memoria.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime

import pymupdf
import pytest

from opofuente.application.topic_pdf import (
    TopicPdfChapter,
    TopicPdfDocument,
    TopicPdfSection,
)
from opofuente.infrastructure import topic_pdf as renderizador
from opofuente.infrastructure.topic_pdf import (
    MAX_PAGINAS,
    CuerpoDemasiadoLargoError,
    render_topic_pdf,
)


def _documento(
    *,
    estado: str = "published",
    titulo: str = "Redes locales",
    capitulos: tuple[TopicPdfChapter, ...] | None = None,
) -> TopicPdfDocument:
    if capitulos is None:
        capitulos = (
            TopicPdfChapter(
                code="IV.10.1",
                title="Fundamentos",
                position=1,
                sections=(
                    TopicPdfSection(
                        number=1,
                        title="Qué es una red",
                        body_markdown="El modelo **TCP/IP** tiene *cuatro* capas.",
                    ),
                ),
            ),
        )
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
        chapters=capitulos,
    )


def _abrir(pdf: bytes) -> pymupdf.Document:
    return pymupdf.open(stream=pdf, filetype="pdf")


def _texto_completo(pdf: bytes) -> str:
    documento = _abrir(pdf)
    try:
        return "\n".join(pagina.get_text() for pagina in documento)
    finally:
        documento.close()


def test_el_pdf_se_abre_y_lleva_el_texto_a_la_pagina() -> None:
    pdf = render_topic_pdf(_documento())

    assert pdf.startswith(b"%PDF")
    documento = _abrir(pdf)
    try:
        assert documento.page_count == 1
    finally:
        documento.close()

    texto = _texto_completo(pdf)
    assert "Tema IV.10 · Redes locales" in texto
    assert "Publicado" in texto
    assert "OpoFuente v0.1.0 · generado el 31/10/2026" in texto
    assert "página 1 de 1" in texto
    assert "Qué es una red" in texto
    assert "TCP/IP" in texto


def test_un_tema_en_borrador_lo_advierte_en_la_cabecera_y_en_el_pie() -> None:
    texto = _texto_completo(render_topic_pdf(_documento(estado="draft")))

    assert "BORRADOR - no oficial" in texto
    assert "pendiente de revisión" in texto


def test_los_metadatos_dicen_que_es_y_de_donde_sale() -> None:
    documento = _abrir(render_topic_pdf(_documento()))
    try:
        metadatos = documento.metadata
    finally:
        documento.close()

    assert metadatos["title"] == "Tema IV.10 · Redes locales"
    assert metadatos["author"] == "OpoFuente"
    assert metadatos["subject"] == "Apuntes del temario"
    assert metadatos["producer"] == "OpoFuente"


def test_un_tema_largo_ocupa_varias_paginas_y_no_pierde_el_final() -> None:
    relleno = "texto de relleno " * 12
    secciones = tuple(
        TopicPdfSection(
            number=indice,
            title=f"Epígrafe {indice}",
            body_markdown="\n\n".join(f"Párrafo {indice}.{n} {relleno}" for n in range(4)),
        )
        for indice in range(1, 41)
    )
    documento = _documento(
        capitulos=(
            TopicPdfChapter(code="IV.10.1", title="Fundamentos", position=1, sections=secciones),
        ),
    )

    pdf = render_topic_pdf(documento)
    abierto = _abrir(pdf)
    try:
        total = abierto.page_count
        textos = [pagina.get_text() for pagina in abierto]
    finally:
        abierto.close()

    assert total > 1
    for numero, texto in enumerate(textos, start=1):
        assert f"página {numero} de {total}" in texto
    assert "Epígrafe 40" in textos[-1]


def test_un_documento_sin_capitulos_sigue_siendo_un_pdf_de_una_pagina() -> None:
    pdf = render_topic_pdf(_documento(capitulos=()))

    abierto = _abrir(pdf)
    try:
        assert abierto.page_count == 1
    finally:
        abierto.close()
    assert "página 1 de 1" in _texto_completo(pdf)


def test_un_titulo_que_la_fuente_base_no_dibuja_no_rompe_la_descarga() -> None:
    pdf = render_topic_pdf(_documento(titulo="Tema IV.10 · 🚀 \u65e5\u672c\u8a9e"))

    texto = _texto_completo(pdf)
    assert "Tema IV.10" in texto
    assert "página 1 de 1" in texto


class _HistoriaQueNoTermina:
    def __init__(self) -> None:
        self.veces = 0

    def place(self, where: object) -> tuple[bool, float]:
        self.veces += 1
        return True, 0.0

    def draw(self, device: object) -> None:
        return None


class _EscritorQueCuentaPaginas:
    def __init__(self) -> None:
        self.paginas = 0

    def begin_page(self, rect: object) -> object:
        self.paginas += 1
        return object()

    def end_page(self) -> None:
        return None


def test_un_cuerpo_que_nunca_termina_se_corta_en_vez_de_girar_para_siempre() -> None:
    historia = _HistoriaQueNoTermina()
    escritor = _EscritorQueCuentaPaginas()

    with pytest.raises(CuerpoDemasiadoLargoError):
        renderizador._maquetar_cuerpo(historia, escritor, pymupdf.Rect(0, 0, 100, 100))

    assert historia.veces == MAX_PAGINAS
    assert escritor.paginas == MAX_PAGINAS


def test_un_cuerpo_que_termina_a_la_primera_no_crea_paginas_de_mas() -> None:
    class _HistoriaCorta:
        def place(self, where: object) -> tuple[bool, float]:
            return False, 1.0

        def draw(self, device: object) -> None:
            return None

    escritor = _EscritorQueCuentaPaginas()

    renderizador._maquetar_cuerpo(_HistoriaCorta(), escritor, pymupdf.Rect(0, 0, 100, 100))

    assert escritor.paginas == 1


def test_el_tope_de_paginas_deja_margen_sobre_un_temario_real() -> None:
    # 40 epígrafes de cuatro párrafos caben de sobra: el tope solo tiene que atrapar lo patológico.
    assert MAX_PAGINAS >= 100


def test_el_reparto_del_documento_se_respeta_en_el_pdf() -> None:
    documento = replace(
        _documento(),
        chapters=(
            TopicPdfChapter(
                code="IV.10.2",
                title="Cableado",
                position=2,
                sections=(
                    TopicPdfSection(number=2, title="Par trenzado", body_markdown="Categoría 6."),
                ),
            ),
            TopicPdfChapter(
                code="IV.10.1",
                title="Fundamentos",
                position=1,
                sections=(
                    TopicPdfSection(number=1, title="Qué es una red", body_markdown="Nodos."),
                ),
            ),
        ),
    )

    texto = _texto_completo(render_topic_pdf(documento))

    assert texto.index("Fundamentos") < texto.index("Cableado")
    assert "Par trenzado" in texto
