"""XML endurecido para entrada no confiable (DEBT-004).

Todo XML que llega de fuera (dentro de un DOCX, un PPTX o un fichero suelto) pasa por aquí:

- **sin entidades externas**: `resolve_entities=False` y `load_dtd=False`, así que un `DOCTYPE` con
  una entidad que apunte a un fichero local o a una URL no se resuelve nunca;
- **sin red**: `no_network=True` (además es el valor por defecto de lxml);
- **sin árboles gigantes**: `huge_tree=False`, que limita la profundidad y el efecto de una
  «billion laughs»;
- **con tope de tamaño**: se lee como mucho `max_bytes` antes de parsear, para no cargar en memoria
  lo que no se va a aceptar.

Lo que devuelve es un `Element` de lxml ya parseado. El XML no se ejecuta: parsear no ejecuta nada.
"""

from __future__ import annotations

from io import BytesIO
from typing import Final

from lxml import etree

from opofuente.domain.errors import UnsafeContentError

#: Tamaño máximo de un documento XML que se acepta parsear (8 MiB): `word/document.xml` de un DOCX
#: real ronda unos cientos de KiB, así que este tope no molesta y evita sorpresas.
DEFAULT_MAX_XML_BYTES: Final = 8 * 1024 * 1024

#: Etiquetas cuyo contenido se descarta siempre: no aportan texto y a veces traen datos ocultos.
DROPPED_TAGS: Final = frozenset({"script", "style", "head", "meta", "link", "iframe", "object"})


def hardened_parser() -> etree.XMLParser:
    """Parser XML sin resolución de entidades, sin red y sin árboles enormes."""
    return etree.XMLParser(
        resolve_entities=False,
        load_dtd=False,
        no_network=True,
        huge_tree=False,
        recover=False,
        remove_blank_text=False,
    )


def parse_xml_bytes(data: bytes, *, max_bytes: int = DEFAULT_MAX_XML_BYTES) -> etree._Element:
    """Parsea XML no confiable con el parser endurecido.

    Lanza `UnsafeContentError` si el documento excede el tamaño, si trae un `DOCTYPE` (la vía
    habitual de las entidades externas) o si el parser lo rechaza.
    """
    if len(data) > max_bytes:
        raise UnsafeContentError(f"el XML supera el límite de {max_bytes} bytes y no se parsea")
    prefix = data[:4096].lstrip()
    if prefix.startswith(b"<?xml") and b"<!DOCTYPE" in data[:4096]:
        raise UnsafeContentError("el XML trae un DOCTYPE: no se admiten entidades externas")
    if prefix.startswith(b"<!DOCTYPE"):
        raise UnsafeContentError("el XML trae un DOCTYPE: no se admiten entidades externas")

    parser = hardened_parser()
    try:
        return etree.parse(BytesIO(data), parser).getroot()
    except etree.XMLSyntaxError as error:
        raise UnsafeContentError(f"el XML no se pudo parsear ({error.msg})") from error
    except ValueError as error:  # pragma: no cover - lxml lanza esto en casos extremos
        raise UnsafeContentError("el XML no se pudo parsear") from error


def element_text(element: etree._Element, *, skip_tags: frozenset[str] = DROPPED_TAGS) -> str:
    """Texto de un elemento, saltando las etiquetas que nunca aportan contenido visible.

    Se usa `itertext` sobre los hijos permitidos: no se ejecuta nada y no se sigue ninguna
    referencia externa (el parser ya lo impide).
    """
    parts: list[str] = []
    for node in element.iter():
        tag = node.tag
        # En lxml, los comentarios y las instrucciones de procesado tienen una etiqueta que es una
        # función, no una cadena: no son texto y se saltan.
        if callable(tag):
            continue
        if tag.split("}")[-1].lower() in skip_tags:
            continue
        for text in node.itertext():
            value = text.decode("utf-8", errors="replace") if isinstance(text, bytes) else text
            if value.strip():
                parts.append(value)
    return "\n".join(parts)
