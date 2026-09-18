"""Exportación: Anki CSV y Markdown/Obsidian (06_QUESTIONS §8 y 08_API-CONTRACT §11).

Lo que se exporta y lo que no:

- **se exporta lo que la aplicación sabe**: la pregunta, sus opciones, la respuesta correcta **solo
  si la clave la cubre**, la explicación, las citas con su documento y su versión, la oposición, el
  tema y la procedencia. Si una pregunta no tiene respuesta conocida, se exporta **diciéndolo**: una
  tarjeta sin solución no se puede estudiar, y callarlo sería peor;
- **la procedencia viaja siempre**: conjunto, plantilla, versión del documento y origen (oficial,
  privada o generada). §8 lo pide para Anki y 09_SECURITY §8 lo pide para cualquier exportación;
- **el material restringido se avisa**: una pregunta cuya cita venga de material con derechos
  restringidos (o sin determinar) se exporta, pero con su aviso, porque exportar es sacar el
  material de la aplicación.

El renderizado es puro: no toca disco ni base. Así se puede probar letra a letra.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime

#: Separador del CSV. Se elige `;` porque el material es español y las comas y los puntos y coma son
#: parte de la prosa; con `,` habría que entrecomillar casi todo. Anki lo acepta como separador
#: explícito al importar, y el fichero lo declara en su primera línea.
CSV_DELIMITER = ";"

#: Cabecera del Anki CSV: son los campos que Anki pide al importar (y los que §8 enumera).
ANKI_FIELDS = (
    "pregunta",
    "opciones",
    "respuesta",
    "explicacion",
    "citas",
    "oposicion",
    "tema",
    "origen",
    "conjunto",
    "plantilla",
    "documentos",
)

#: Caracteres con los que una hoja de cálculo empieza a evaluar una fórmula. Se neutralizan con un
#: apóstrofo **solo** cuando encabezan la celda, y se avisa: el texto de una pregunta puede venir de
#: un PDF ajeno, y una exportación no es un sitio donde ejecutar lo que alguien escribió.
_FORMULA_STARTS = ("=", "+", "@", "\t", "\r")
_SIN_SOLUCION = "(sin respuesta conocida: la plantilla no la cubre)"


@dataclass(frozen=True, slots=True)
class ExportRow:
    """Una pregunta exportable, ya resuelta: nada de esto se decide al renderizar."""

    stable_key: str
    question: str
    options: tuple[tuple[str, str], ...]
    correct_option_keys: tuple[str, ...]
    explanation: str | None
    citations: tuple[str, ...]
    document_titles: tuple[str, ...]
    document_versions: tuple[str, ...]
    opposition: str | None
    topic: str | None
    origin_type: str
    set_title: str
    key_label: str | None
    #: `True` cuando la cita viene de material con derechos restringidos o sin determinar.
    restricted: bool = False


@dataclass(frozen=True, slots=True)
class ExportDocument:
    """El fichero exportado, antes de escribirlo."""

    filename: str
    content: str
    format: str
    item_count: int
    documents: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    provenance: dict[str, str] = field(default_factory=dict)


def _neutralizar(texto: str) -> tuple[str, bool]:
    """Devuelve el texto listo para una celda y si hubo que neutralizarlo."""
    if texto.startswith(_FORMULA_STARTS):
        return f"'{texto}", True
    # Un guion solo es fórmula si le sigue un número; «- no me acuerdo» es prosa.
    if texto.startswith("-") and len(texto) > 1 and texto[1].isdigit():
        return f"'{texto}", True
    return texto, False


def _celda(texto: str) -> tuple[str, bool]:
    """Una celda CSV entrecomillada como manda RFC 4180, con la fórmula neutralizada."""
    seguro, neutralizada = _neutralizar(texto)
    escapado = seguro.replace('"', '""')
    return f'"{escapado}"', neutralizada


def _texto_de_opciones(opciones: Sequence[tuple[str, str]]) -> str:
    return "\n".join(f"{clave.upper()}) {texto}" for clave, texto in opciones)


def _respuesta(row: ExportRow) -> str:
    if not row.correct_option_keys:
        return _SIN_SOLUCION
    return ", ".join(clave.upper() for clave in row.correct_option_keys)


def render_anki_csv(rows: Sequence[ExportRow]) -> tuple[str, tuple[str, ...]]:
    """CSV de Anki: pregunta, opciones, respuesta, explicación, citas, oposición, tema y origen.

    La primera línea es la cabecera con los nombres de los campos, que es lo que Anki enseña al
    importar para mapearlos.
    """
    lineas = [CSV_DELIMITER.join(ANKI_FIELDS)]
    neutralizadas = 0
    for row in rows:
        valores = (
            row.question,
            _texto_de_opciones(row.options),
            _respuesta(row),
            row.explanation or "",
            "\n".join(row.citations),
            row.opposition or "",
            row.topic or "",
            row.origin_type,
            row.set_title,
            row.key_label or "",
            "\n".join(
                f"{titulo} ({version})"
                for titulo, version in zip(row.document_titles, row.document_versions, strict=False)
            ),
        )
        celdas: list[str] = []
        for valor in valores:
            celda, neutralizada = _celda(valor)
            neutralizadas += 1 if neutralizada else 0
            celdas.append(celda)
        lineas.append(CSV_DELIMITER.join(celdas))
    avisos: tuple[str, ...] = ()
    if neutralizadas:
        avisos = (
            f"{neutralizadas} celda(s) empezaban por un carácter de fórmula y se han neutralizado "
            "con un apóstrofo para que una hoja de cálculo no las evalúe",
        )
    # LF explícito y sin BOM: el fichero lo leen Anki y cualquier editor de texto.
    return "\n".join(lineas) + "\n", avisos


def render_markdown(
    rows: Sequence[ExportRow], *, title: str, generated_at: datetime, version: str
) -> str:
    """Markdown para Obsidian: una ficha por pregunta, con sus citas y su procedencia."""
    cabecera = [
        "---",
        f"titulo: {title}",
        f"generado: {generated_at.isoformat()}",
        f"opofuente: {version}",
        f"preguntas: {len(rows)}",
        "---",
        "",
        f"# {title}",
        "",
        "> Exportado de OpoFuente. Cada pregunta lleva su procedencia y su cita; lo que no tiene "
        "respuesta conocida lo dice.",
        "",
    ]
    fichas: list[str] = []
    for indice, row in enumerate(rows, start=1):
        detalle = [
            f"## {indice}. {row.question}",
            "",
        ]
        if row.options:
            detalle.append("Opciones:")
            detalle.append("")
            detalle.extend(f"- **{clave.upper()})** {texto}" for clave, texto in row.options)
            detalle.append("")
        detalle.append(f"**Respuesta:** {_respuesta(row)}")
        detalle.append("")
        if row.explanation:
            detalle.extend([row.explanation, ""])
        if row.citations:
            detalle.append("Evidencia:")
            detalle.append("")
            detalle.extend(f"- {cita}" for cita in row.citations)
            detalle.append("")
        procedencia = [
            f"- procedencia: {row.origin_type}",
            f"- conjunto: {row.set_title}",
        ]
        if row.key_label:
            procedencia.append(f"- plantilla: {row.key_label}")
        if row.opposition:
            procedencia.append(f"- oposición: {row.opposition}")
        if row.topic:
            procedencia.append(f"- tema: {row.topic}")
        if row.document_titles or row.document_versions:
            procedencia.append(
                "- documentos: "
                + ", ".join(
                    f"{titulo} ({version})"
                    for titulo, version in zip(
                        row.document_titles, row.document_versions, strict=False
                    )
                )
            )
        if row.restricted:
            procedencia.append("- derechos: material restringido (revisa antes de compartirlo)")
        detalle.extend(procedencia)
        detalle.extend(["", "---", ""])
        fichas.append("\n".join(detalle))
    return "\n".join((*cabecera, *fichas))


def restricted_rows(rows: Sequence[ExportRow]) -> tuple[ExportRow, ...]:
    """Las preguntas cuya evidencia viene de material restringido o sin derechos determinados."""
    return tuple(row for row in rows if row.restricted)


def export_warnings(rows: Sequence[ExportRow]) -> tuple[str, ...]:
    """Lo que hay que decir **antes** de que alguien use el fichero fuera de aquí."""
    avisos: list[str] = []
    restringidas = restricted_rows(rows)
    if restringidas:
        avisos.append(
            f"{len(restringidas)} de {len(rows)} pregunta(s) citan material con derechos "
            "restringidos o sin determinar: al exportar sale de la aplicación, así que revísalo "
            "antes de compartirlo."
        )
    sin_solucion = [row for row in rows if not row.correct_option_keys]
    if sin_solucion:
        avisos.append(
            f"{len(sin_solucion)} pregunta(s) no tienen respuesta conocida (la plantilla no las "
            "cubre): se exportan diciéndolo, porque una tarjeta sin solución no se puede estudiar."
        )
    sin_cita = [row for row in rows if not row.citations]
    if sin_cita:
        avisos.append(
            f"{len(sin_cita)} pregunta(s) no citan ninguna evidencia: se puede estudiar con ellas, "
            "pero no se puede comprobar de dónde salen."
        )
    return tuple(avisos)


__all__ = [
    "ANKI_FIELDS",
    "CSV_DELIMITER",
    "ExportDocument",
    "ExportRow",
    "export_warnings",
    "render_anki_csv",
    "render_markdown",
    "restricted_rows",
]
