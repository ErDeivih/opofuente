"""Renderiza a PDF un `TopicPdfDocument` con PyMuPDF, en memoria y sin tocar el disco.

El reparto es el mismo que en el resto de integraciones: la aplicación decide qué se cuenta
(`application/topic_pdf.py`), y aquí se decide cómo se pinta. La descarga no escribe un archivo
temporal: se compone en un `BytesIO`, se sella la cabecera y el pie de cada página y se
devuelven los bytes para que la ruta los entregue.

La cabecera y el pie se estampan **después** de maquetar el cuerpo, porque el «página N de M» no se
puede saber hasta que están todas. Por eso el cuerpo reserva arriba y abajo el hueco que ocupan.
"""

from __future__ import annotations

import io
from typing import Any, Protocol

import pymupdf

from opofuente.application.topic_pdf import (
    PDF_CSS,
    TopicPdfDocument,
    build_topic_pdf_html,
    texto_para_pdf,
)

#: A4 en puntos (595 × 842).
PAGE = pymupdf.paper_rect("a4")

#: Márgenes. El superior y el inferior dejan sitio a la cabecera y al pie estampados.
MARGEN_LATERAL = 46
MARGEN_SUPERIOR = 64
MARGEN_INFERIOR = 58

#: Cuerpo de letra de la cabecera y el pie, en gris para que no compitan con el texto.
_PIE_TAMANO = 7.5
_PIE_COLOR = (0.35, 0.35, 0.35)
_FUENTE = "helv"

#: Tope de páginas del cuerpo. Un temario real no se acerca; el tope existe para que un HTML
#: patológico (una tabla o una palabra que no cabe en una página) no deje el bucle creando páginas
#: para siempre y agote memoria y CPU dentro de una descarga.
MAX_PAGINAS = 200


class CuerpoDemasiadoLargoError(RuntimeError):
    """El cuerpo no cabe en `MAX_PAGINAS`: se corta con un error explícito, no con un bucle."""


class _Historia(Protocol):
    """Lo que hace falta de `pymupdf.Story` para volcarla en páginas."""

    def place(self, where: Any) -> tuple[bool, float]: ...

    def draw(self, device: Any) -> None: ...


class _Escritor(Protocol):
    """Lo que hace falta de `pymupdf.DocumentWriter` para encadenar páginas."""

    def begin_page(self, rect: Any) -> Any: ...

    def end_page(self) -> None: ...


def _maquetar_cuerpo(story: _Historia, writer: _Escritor, cuerpo: pymupdf.Rect) -> None:
    """Vuelca la historia en páginas hasta que no quede contenido.

    `Story.place` devuelve si queda contenido por colocar, pero nada garantiza que cada página
    consuma algo: por eso se cuenta y se corta. Se acepta cualquier objeto con `place` y `draw` para
    poder probar el corte sin generar un PDF real.
    """

    for _ in range(MAX_PAGINAS):
        device = writer.begin_page(PAGE)
        mas, _ = story.place(cuerpo)
        story.draw(device)
        writer.end_page()
        if not mas:
            return
    raise CuerpoDemasiadoLargoError(
        f"El tema no cabe en {MAX_PAGINAS} páginas: no se genera un PDF incompleto."
    )


def _recortar(texto: str, limite: int) -> str:
    """Un título largo no puede empujar el pie fuera de la página.

    Se sanea antes de medir y se recorta con tres puntos ASCII: los puntos suspensivos tipográficos
    no existen en la fuente base y acabarían impresos como un signo de interrogación.
    """

    limpio = " ".join(texto_para_pdf(texto).split())
    if len(limpio) <= limite:
        return limpio
    return limpio[: max(limite - 3, 0)].rstrip() + "..."


def _ancho(texto: str, tamano: float) -> float:
    return pymupdf.get_text_length(texto, fontname=_FUENTE, fontsize=tamano)


def _estampar(documento: pymupdf.Document, topic_pdf: TopicPdfDocument) -> None:
    """Cabecera y pie en cada página.

    La procedencia va a la izquierda; el estado y la paginación, a la derecha.
    """

    total = documento.page_count
    izquierda = _recortar(f"Tema {topic_pdf.topic_code} · {topic_pdf.topic_title}", 70)
    estado = texto_para_pdf("BORRADOR — no oficial" if topic_pdf.state == "draft" else "Publicado")
    generado = topic_pdf.downloaded_at.strftime("%d/%m/%Y")
    pie_izquierda = "OpoFuente"
    if topic_pdf.app_version:
        pie_izquierda = f"OpoFuente v{topic_pdf.app_version}"
    pie_izquierda = texto_para_pdf(f"{pie_izquierda} · generado el {generado}")

    for indice, pagina in enumerate(documento, start=1):
        ancho = pagina.rect.width
        pagina.insert_text(
            (MARGEN_LATERAL, 36),
            izquierda,
            fontname=_FUENTE,
            fontsize=_PIE_TAMANO,
            color=_PIE_COLOR,
        )
        pagina.insert_text(
            (ancho - MARGEN_LATERAL - _ancho(estado, _PIE_TAMANO), 36),
            estado,
            fontname=_FUENTE,
            fontsize=_PIE_TAMANO,
            color=_PIE_COLOR,
        )
        pagina.insert_text(
            (MARGEN_LATERAL, pagina.rect.height - 30),
            pie_izquierda,
            fontname=_FUENTE,
            fontsize=_PIE_TAMANO,
            color=_PIE_COLOR,
        )
        paginacion = texto_para_pdf(f"página {indice} de {total}")
        pagina.insert_text(
            (ancho - MARGEN_LATERAL - _ancho(paginacion, _PIE_TAMANO), pagina.rect.height - 30),
            paginacion,
            fontname=_FUENTE,
            fontsize=_PIE_TAMANO,
            color=_PIE_COLOR,
        )


def render_topic_pdf(topic_pdf: TopicPdfDocument) -> bytes:
    """Devuelve el PDF completo del tema, con cabecera, pie y metadatos."""

    html = build_topic_pdf_html(topic_pdf)
    story = pymupdf.Story(html=html, user_css=PDF_CSS)
    cuerpo = pymupdf.Rect(
        MARGEN_LATERAL,
        MARGEN_SUPERIOR,
        PAGE.width - MARGEN_LATERAL,
        PAGE.height - MARGEN_INFERIOR,
    )

    buffer = io.BytesIO()
    writer = pymupdf.DocumentWriter(buffer)
    _maquetar_cuerpo(story, writer, cuerpo)
    writer.close()

    documento = pymupdf.open(stream=buffer.getvalue(), filetype="pdf")
    try:
        _estampar(documento, topic_pdf)
        documento.set_metadata(
            {
                "title": f"Tema {topic_pdf.topic_code} · {topic_pdf.topic_title}",
                "author": "OpoFuente",
                "subject": "Apuntes del temario",
                "creator": "OpoFuente",
                "producer": "OpoFuente",
            }
        )
        return documento.tobytes(garbage=4, deflate=True)
    finally:
        documento.close()
