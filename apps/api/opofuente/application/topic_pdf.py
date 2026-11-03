"""El documento que se exporta como PDF: **qué** lleva un tema, sin decir cómo se pinta.

Esta capa es pura a propósito: compone la cabecera de procedencia, decide qué texto entra y cómo se
convierte el markdown de los apuntes a la estructura que entenderá el renderizador. El renderizador
—PyMuPDF— vive en `infrastructure/topic_pdf.py`, igual que el resto de integraciones: la aplicación
no conoce la tecnología que produce los bytes.

Tres reglas de la exportación, y las tres son del encargo:

1. **Se exporta un tema entero**, con todos sus capítulos en orden de lectura, no solo el que la
   pantalla tenga abierto.
2. **La cabecera dice de dónde sale**: oposición, bloque, tema, fecha de generación, estado y, si
   está en borrador, que no es oficial. Un PDF descargado va a vivir fuera de la aplicación y tiene
   que poder explicarse solo.
3. **El markdown se interpreta igual que en pantalla** (`notesMarkdownParser.ts`): títulos, listas,
   tablas, citas y negrita/cursiva/código en línea. Lo que el alumno lee en la web y lo que imprime
   no pueden contar cosas distintas. Las marcas `<!-- revisar: … -->` no viajan: el estado del tema
   ya avisa de que hay texto pendiente, y esas notas son para quien revisa, no para el alumno.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from datetime import datetime
from html import escape

#: Lo que el alumno ve para cada estado de los apuntes. `none` no se exporta: sin texto no hay PDF.
ETIQUETAS_DE_ESTADO: dict[str, str] = {
    "draft": "Borrador: texto pendiente de revisión",
    "published": "Publicado",
}

_AVISO_BORRADOR = (
    "Este tema está en borrador: su texto aún no se ha revisado y no debe citarse como material "
    "oficial."
)

_REVISION = re.compile(r"<!--\s*revisar:.*?-->", re.DOTALL)
_TITULO = re.compile(r"^(#{2,6})\s+(.*)$")
_VINETA = re.compile(r"^[-*]\s+(.*)$")
_NUMERADA = re.compile(r"^[0-9]+[.)]\s+(.*)$")
_CITA = re.compile(r"^>\s?(.*)$")
_SEPARADOR_DE_TABLA = re.compile(r"^:?-{3,}:?$")

_NEGRITA = re.compile(r"\*\*(.+?)\*\*")
_CURSIVA = re.compile(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)")
_CODIGO = re.compile(r"`([^`]+)`")


@dataclass(frozen=True, slots=True)
class TopicPdfSection:
    """Un apartado tal y como entra en el PDF: su número, su título y su markdown."""

    number: int
    title: str
    body_markdown: str


@dataclass(frozen=True, slots=True)
class TopicPdfChapter:
    """Un capítulo del tema (un epígrafe oficial) con sus apartados."""

    code: str
    title: str
    position: int
    sections: tuple[TopicPdfSection, ...] = ()


@dataclass(frozen=True, slots=True)
class TopicPdfDocument:
    """Todo lo que necesita la portada y el cuerpo de la exportación.

    `state` es el estado de los apuntes (`draft` o `published`). `generated_at` es cuándo se
    escribieron los apuntes y `downloaded_at` cuándo se descarga el PDF: las dos fechas importan y
    no son la misma.
    """

    topic_code: str
    topic_title: str
    block_code: str
    block_title: str
    opposition_code: str
    opposition_name: str
    state: str
    downloaded_at: datetime
    generated_at: datetime | None = None
    app_version: str = ""
    chapters: tuple[TopicPdfChapter, ...] = ()


#: PyMuPDF dibuja la cabecera y el pie con la fuente base `helv`, que solo codifica Latin-1: lo que
#: quede fuera de ese repertorio se imprime como un signo de interrogación. Los caracteres
#: tipográficos habituales en unos apuntes se sustituyen por su equivalente visible.
_EQUIVALENTES_LATIN1: dict[str, str] = {
    "\u2014": "-",  # guion largo
    "\u2013": "-",  # guion medio
    "\u2212": "-",  # signo menos
    "\u2026": "...",  # puntos suspensivos
    "\u201c": '"',
    "\u201d": '"',
    "\u201e": '"',
    "\u2018": "'",
    "\u2019": "'",
    "\u00ab": '"',
    "\u00bb": '"',
    "\u2022": "-",  # viñeta
    "\u2027": "-",
    "\u00a0": " ",
    "\u202f": " ",
    "\u2009": " ",
    "\u200b": "",
    "\ufeff": "",
    "\u20ac": "EUR",
}


def _en_latin1(caracter: str) -> bool:
    try:
        caracter.encode("latin-1")
    except UnicodeEncodeError:
        return False
    return True


def texto_para_pdf(texto: str) -> str:
    """Deja el texto en lo que la fuente base del PDF puede dibujar de verdad.

    La cabecera y el pie se estampan con `insert_text` y la fuente `helv`, que codifica en Latin-1.
    Se conservan las letras acentuadas del castellano (están en Latin-1) y solo se sustituye lo que
    no cabe: primero por su equivalente tipográfico, después por su letra base sin diacríticos y, si
    tampoco, por `?`. Es mejor un guion o un `?` explícito que un carácter perdido en cada página.
    """

    piezas: list[str] = []
    for caracter in texto:
        equivalente = _EQUIVALENTES_LATIN1.get(caracter)
        if equivalente is not None:
            piezas.append(equivalente)
            continue
        if _en_latin1(caracter):
            piezas.append(caracter)
            continue
        base = "".join(
            letra
            for letra in unicodedata.normalize("NFKD", caracter)
            if not unicodedata.combining(letra) and _en_latin1(letra)
        )
        piezas.append(base or "?")
    return "".join(piezas)


def _en_linea(texto: str) -> str:
    """Negrita, cursiva y código **después** de escapar: el texto viene de fuera y no es HTML."""

    escapado = escape(texto, quote=False)
    escapado = _CODIGO.sub(r"<code>\1</code>", escapado)
    escapado = _NEGRITA.sub(r"<strong>\1</strong>", escapado)
    return _CURSIVA.sub(r"<em>\1</em>", escapado)


def _celdas(linea: str) -> list[str]:
    despojada = linea.strip()
    if despojada.startswith("|"):
        despojada = despojada[1:]
    if despojada.endswith("|"):
        despojada = despojada[:-1]
    return [celda.strip() for celda in despojada.split("|")]


def markdown_to_html(markdown: str) -> str:
    """Convierte el markdown de los apuntes en el subconjunto de HTML que usa el PDF.

    Se interpreta solo lo que el parser de la web ya interpreta. Cualquier otro marcado se queda
    como texto: es preferible un asterisco visible a un enlace inventado.
    """

    lineas = _REVISION.sub("", markdown).splitlines()
    salida: list[str] = []
    parrafo: list[str] = []
    lista: list[str] = []
    lista_ordenada = False
    tabla: list[list[str]] = []

    def cerrar_parrafo() -> None:
        if parrafo:
            salida.append(f"<p>{_en_linea(' '.join(parrafo))}</p>")
            parrafo.clear()

    def cerrar_lista() -> None:
        nonlocal lista_ordenada
        if lista:
            etiqueta = "ol" if lista_ordenada else "ul"
            elementos = "".join(f"<li>{_en_linea(item)}</li>" for item in lista)
            salida.append(f"<{etiqueta}>{elementos}</{etiqueta}>")
            lista.clear()

    def cerrar_tabla() -> None:
        if not tabla:
            return
        filas = list(tabla)
        tabla.clear()
        cabecera, *cuerpo = filas
        columnas = "".join(f"<th>{_en_linea(celda)}</th>" for celda in cabecera)
        html = [f"<table><thead><tr>{columnas}</tr></thead>"]
        if cuerpo:
            html.append("<tbody>")
            for fila in cuerpo:
                celdas = "".join(f"<td>{_en_linea(celda)}</td>" for celda in fila)
                html.append(f"<tr>{celdas}</tr>")
            html.append("</tbody>")
        html.append("</table>")
        salida.append("".join(html))

    def cerrar_todo() -> None:
        cerrar_parrafo()
        cerrar_lista()
        cerrar_tabla()

    for linea in lineas:
        despojada = linea.strip()
        if not despojada:
            cerrar_todo()
            continue

        if despojada.startswith("|"):
            cerrar_parrafo()
            cerrar_lista()
            celdas = _celdas(despojada)
            if all(_SEPARADOR_DE_TABLA.match(celda) for celda in celdas):
                continue
            tabla.append(celdas)
            continue

        if tabla:
            cerrar_tabla()

        titulo = _TITULO.match(despojada)
        if titulo:
            cerrar_todo()
            nivel = min(len(titulo.group(1)) + 1, 4)
            salida.append(f"<h{nivel}>{_en_linea(titulo.group(2))}</h{nivel}>")
            continue

        cita = _CITA.match(despojada)
        if cita:
            cerrar_parrafo()
            cerrar_lista()
            salida.append(f"<blockquote>{_en_linea(cita.group(1))}</blockquote>")
            continue

        vineta = _VINETA.match(despojada)
        if vineta:
            cerrar_parrafo()
            if lista_ordenada:
                cerrar_lista()
            lista_ordenada = False
            lista.append(vineta.group(1))
            continue

        numerada = _NUMERADA.match(despojada)
        if numerada:
            cerrar_parrafo()
            if lista and not lista_ordenada:
                cerrar_lista()
            lista_ordenada = True
            lista.append(numerada.group(1))
            continue

        if lista:
            cerrar_lista()
        parrafo.append(despojada)

    cerrar_todo()
    return "\n".join(salida)


#: Estilo del documento. PyMuPDF no es un navegador: se queda en lo que entiende (tipografías,
#: márgenes, bordes y tablas) y no se usan rejillas ni posicionamiento.
PDF_CSS = """
body { font-family: sans-serif; font-size: 10.5pt; color: #1a1a1a; }
h1 { font-size: 19pt; margin: 0 0 4pt 0; }
h2 { font-size: 14.5pt; margin: 16pt 0 4pt 0; }
h3 { font-size: 12pt; margin: 11pt 0 3pt 0; }
h4 { font-size: 11pt; margin: 9pt 0 2pt 0; }
p { margin: 0 0 6pt 0; }
ul, ol { margin: 0 0 6pt 12pt; }
li { margin: 0 0 2pt 0; }
blockquote { margin: 0 0 6pt 8pt; color: #444444; }
table { border-collapse: collapse; margin: 4pt 0 8pt 0; }
th, td { border: 1px solid #b8b8b8; padding: 3pt 5pt; font-size: 9.5pt; }
th { background-color: #eeeeee; text-align: left; }
code { font-family: monospace; font-size: 9.5pt; }
.meta { color: #555555; font-size: 9pt; margin: 0 0 2pt 0; }
.code { color: #666666; font-size: 10pt; }
.aviso { color: #8a4b00; font-size: 9pt; margin: 6pt 0 0 0; }
.capitulo { margin: 0 0 10pt 0; }
"""


def _etiqueta_de_estado(estado: str) -> str:
    """El estado tal y como se lee en la cabecera; un estado desconocido no se inventa."""

    return ETIQUETAS_DE_ESTADO.get(estado, estado)


def build_topic_pdf_html(document: TopicPdfDocument) -> str:
    """Compone el HTML del documento: portada, aviso de estado y todos los capítulos."""

    partes: list[str] = [
        f"<h1>{escape(document.topic_code, quote=False)} · "
        f"{escape(document.topic_title, quote=False)}</h1>",
        f'<p class="meta">{escape(document.opposition_name, quote=False)} '
        f"({escape(document.opposition_code, quote=False)})</p>",
        f'<p class="meta">Bloque {escape(document.block_code, quote=False)} · '
        f"{escape(document.block_title, quote=False)}</p>",
        f'<p class="meta">Estado: {escape(_etiqueta_de_estado(document.state), quote=False)}'
        f" · Descargado el {document.downloaded_at:%d/%m/%Y}</p>",
    ]
    if document.generated_at is not None:
        partes.append(f'<p class="meta">Apuntes generados el {document.generated_at:%d/%m/%Y}</p>')
    if document.state == "draft":
        partes.append(f'<p class="aviso">{escape(_AVISO_BORRADOR, quote=False)}</p>')

    for capitulo in sorted(document.chapters, key=lambda capitulo: capitulo.position):
        partes.append('<div class="capitulo">')
        partes.append(
            f"<h2>{capitulo.position}. {escape(capitulo.title, quote=False)} "
            f'<span class="code">{escape(capitulo.code, quote=False)}</span></h2>'
        )
        for seccion in capitulo.sections:
            partes.append(f"<h3>{seccion.number}. {escape(seccion.title, quote=False)}</h3>")
            partes.append(markdown_to_html(seccion.body_markdown))
        partes.append("</div>")

    return "\n".join(partes)


def _slug(texto: str) -> str:
    """ASCII, minúsculas y guiones: un nombre de archivo que cualquier navegador guarda igual."""

    normalizado = unicodedata.normalize("NFKD", texto)
    ascii_texto = normalizado.encode("ascii", "ignore").decode("ascii").lower()
    limpio = re.sub(r"[^a-z0-9]+", "-", ascii_texto).strip("-")
    return limpio[:60].rstrip("-") or "tema"


def topic_pdf_filename(document: TopicPdfDocument) -> str:
    """`tema-IV.10-redes-locales.pdf`, sin rutas ni caracteres que el sistema tenga que escapar."""

    codigo = _slug(document.topic_code)
    titulo = _slug(document.topic_title)
    return f"tema-{codigo}-{titulo}.pdf"
