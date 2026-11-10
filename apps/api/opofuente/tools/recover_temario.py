"""Recupera el temario TAI que ya existe en disco y lo convierte a Markdown estructurado.

**No reescribe nada**: lee los apuntes ya generados en `F:\\OpoFuente\\APUNTES`, sus resúmenes y el
banco de preguntas por tema, y los consolida en `data/temario-recuperado/` (ignorado por git) con:
- un Markdown por tema con front-matter (bloque, título, fichero original, derechos);
- 10 preguntas por tema extraídas del banco (con respuesta y fuente);
- un manifiesto con el inventario y lo que falta respecto a los 33 temas TAI;
- imágenes extraídas de los PDFs de `1. TAI_2026` cuando se pueden sacar.

El material es **privado**: viene en parte de temarios de academia y fuentes de terceros. No se
publica en la demo de GitHub Pages; este comando solo lo consolida en local.

Uso:
    uv run python -m opofuente.tools.recover_temario
    uv run python -m opofuente.tools.recover_temario --source-root F:\\OpoFuente \
        --out data/temario-recuperado
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from opofuente.config import project_root

ROMANOS = {1: "I", 2: "II", 3: "III", 4: "IV"}
BLOQUES_OFICIALES = {1: 9, 2: 5, 3: 9, 4: 10}
APUNTE_GLOB = re.compile(r"^(?P<bloque>\d)\.(?P<numero>\d+) .+\.md$")
PREGUNTA_RE = re.compile(r"^\*\*(?P<numero>\d+)\.\s+(?P<stem>.+?)\*\*\s*$")
OPCION_RE = re.compile(
    r"^-\s+(?P<letra>[a-d])\)\s+(?P<texto>.+?)(?P<correcta>\s+⟵\s+\*\*correcta\*\*)?\s*$"
)
FUENTE_RE = re.compile(r"<sub>(?P<fuente>.+?)</sub>", re.S)
RESUMEN_RE = re.compile(r"^\*\*Bloque\s+(?P<bloque>\d)\.", re.M)


@dataclass(frozen=True)
class Pregunta:
    stem: str
    opciones: tuple[tuple[str, str], ...]
    correcta: str | None
    fuente: str

    def to_dict(self) -> dict[str, Any]:
        respuesta = next((texto for letra, texto in self.opciones if letra == self.correcta), None)
        return {
            "pregunta": self.stem,
            "opciones": [{"letra": letra, "texto": texto} for letra, texto in self.opciones],
            "correcta": self.correcta,
            "respuesta": respuesta,
            "explicacion": (
                f"Respuesta correcta: {respuesta}. Fuente: {self.fuente}"
                if respuesta is not None
                else f"Sin respuesta marcada en el material. Fuente: {self.fuente}"
            ),
            "fuente": self.fuente,
        }


@dataclass
class Tema:
    tema_id: str
    bloque: int
    numero: int
    titulo: str
    apunte: Path
    resumen: Path | None
    banco: Path | None
    caracteres: int = 0
    apartados: int = 0
    tablas: int = 0
    preguntas: list[Pregunta] = field(default_factory=list)
    fuentes: list[str] = field(default_factory=list)


def parse_apunte(path: Path) -> tuple[str, int, int, list[str]]:
    """Título, número de apartados, tablas y fuentes citadas de un apunte ya escrito."""
    texto = path.read_text(encoding="utf-8")
    titulo = ""
    for linea in texto.splitlines():
        if linea.startswith("# "):
            titulo = linea[2:].strip()
            break
    apartados = len(re.findall(r"^#{2,4} ", texto, flags=re.M))
    tablas = len(re.findall(r"^\|.+\|\s*$", texto, flags=re.M))
    urls = re.findall(r"https?://[^\s)>\]]+", texto)
    rutas = re.findall(r"`([^`]+\.(?:pdf|docx|md|html?|txt))`", texto)
    fuentes = list(dict.fromkeys([*urls[:5], *rutas]))
    return titulo, apartados, tablas, fuentes


def parse_question_bank(path: Path) -> list[Pregunta]:
    """Extrae las preguntas con opciones y marca de correcta de un banco por tema."""
    texto = path.read_text(encoding="utf-8")
    lineas = texto.splitlines()
    preguntas: list[Pregunta] = []
    actual: dict[str, Any] | None = None
    for linea in lineas:
        coincidencia = PREGUNTA_RE.match(linea)
        if coincidencia is not None:
            if actual is not None:
                preguntas.append(_cerrar_pregunta(actual))
            actual = {"stem": coincidencia.group("stem").strip(), "opciones": [], "fuente": ""}
            continue
        if actual is None:
            continue
        opcion = OPCION_RE.match(linea)
        if opcion is not None:
            actual["opciones"].append(
                (
                    opcion.group("letra"),
                    opcion.group("texto").strip(),
                    opcion.group("correcta") is not None,
                )
            )
            continue
        fuente = FUENTE_RE.search(linea)
        if fuente is not None and actual["fuente"] == "":
            actual["fuente"] = " ".join(fuente.group("fuente").split())
    if actual is not None:
        preguntas.append(_cerrar_pregunta(actual))
    return [pregunta for pregunta in preguntas if len(pregunta.opciones) >= 2]


def _cerrar_pregunta(actual: dict[str, Any]) -> Pregunta:
    opciones = tuple((letra, texto) for letra, texto, _ in actual["opciones"])
    correcta = next((letra for letra, _, es_correcta in actual["opciones"] if es_correcta), None)
    return Pregunta(
        stem=str(actual["stem"]), opciones=opciones, correcta=correcta, fuente=str(actual["fuente"])
    )


def seleccionar(preguntas: list[Pregunta], cantidad: int = 10) -> list[Pregunta]:
    """Prefiere preguntas con respuesta, con 4 opciones y sin enunciados repetidos."""
    ordenadas = sorted(
        preguntas,
        key=lambda pregunta: (
            pregunta.correcta is None,
            len(pregunta.opciones) != 4,
        ),
    )
    vistas: set[str] = set()
    elegidas: list[Pregunta] = []
    for pregunta in ordenadas:
        if pregunta.stem in vistas:
            continue
        vistas.add(pregunta.stem)
        elegidas.append(pregunta)
        if len(elegidas) == cantidad:
            break
    return elegidas


def _temas_de_apuntes(root: Path) -> dict[str, Tema]:
    temas: dict[str, Tema] = {}
    for path in sorted((root / "APUNTES").glob("*.md")):
        coincidencia = APUNTE_GLOB.match(path.name)
        if coincidencia is None:
            continue
        bloque = int(coincidencia.group("bloque"))
        numero = int(coincidencia.group("numero"))
        tema_id = f"{ROMANOS[bloque]}.{numero}"
        titulo, apartados, tablas, fuentes = parse_apunte(path)
        resumen = root / "RESUMENES" / f"{bloque}.{numero}.md"
        banco = root / "BANCO" / "por-tema-de-la-app" / "TAI" / f"{tema_id}.md"
        temas[tema_id] = Tema(
            tema_id=tema_id,
            bloque=bloque,
            numero=numero,
            titulo=titulo,
            apunte=path,
            resumen=resumen if resumen.is_file() else None,
            banco=banco if banco.is_file() else None,
            caracteres=len(path.read_text(encoding="utf-8")),
            apartados=apartados,
            tablas=tablas,
            fuentes=fuentes,
        )
    return temas


def _extraer_imagenes(roots: list[Path], destino: Path) -> dict[str, int]:
    """Extrae imágenes raster de los PDFs de los temarios TAI (si PyMuPDF está disponible)."""
    pdfs: list[Path] = []
    for root in roots:
        if root.is_dir():
            pdfs.extend(sorted(root.glob("BLOQUE */*.pdf")))
    if not pdfs:
        return {}
    try:
        import pymupdf
    except ImportError:  # pragma: no cover - PyMuPDF es dependencia de producción
        return {}
    resultado: dict[str, int] = {}
    for pdf in pdfs:
        carpeta = (
            destino / pdf.parent.name.replace(" ", "-").lower() / pdf.stem.replace(" ", "-").lower()
        )
        carpeta.mkdir(parents=True, exist_ok=True)
        extraidas = 0
        documento: Any = pymupdf.open(pdf)
        try:
            for pagina in documento:
                for indice, imagen in enumerate(pagina.get_images(full=True)):
                    xref = imagen[0]
                    datos = documento.extract_image(xref)
                    if datos is None or len(datos["image"]) < 5000:
                        continue
                    extension = datos["ext"]
                    archivo = carpeta / f"p{pagina.number + 1:03d}-{indice + 1}.{extension}"
                    archivo.write_bytes(datos["image"])
                    extraidas += 1
                    if extraidas >= 120:
                        break
                if extraidas >= 120:
                    break
        finally:
            documento.close()
        resultado[str(pdf)] = extraidas
    return resultado


def recover(
    *,
    source_root: Path,
    out: Path,
    extract_images: bool = True,
    images_roots: Sequence[Path] | None = None,
) -> dict[str, Any]:
    temas = _temas_de_apuntes(source_root)
    if not temas:
        raise RuntimeError(f"no se encontraron apuntes en {source_root / 'APUNTES'}")

    if out.exists():
        shutil.rmtree(out)
    (out / "temas").mkdir(parents=True)
    (out / "preguntas").mkdir(parents=True)

    catalogo: list[dict[str, Any]] = []
    faltan: list[str] = []
    for bloque, esperados in BLOQUES_OFICIALES.items():
        for numero in range(1, esperados + 1):
            tema_id = f"{ROMANOS[bloque]}.{numero}"
            if tema_id not in temas:
                faltan.append(tema_id)

    for _tema_id, tema in sorted(temas.items(), key=lambda item: (item[1].bloque, item[1].numero)):
        preguntas = seleccionar(parse_question_bank(tema.banco)) if tema.banco else []
        tema.preguntas = preguntas
        cuerpo = tema.apunte.read_text(encoding="utf-8")
        front_matter = "\n".join(
            [
                "---",
                f"tema: {tema.tema_id}",
                f"bloque: {ROMANOS[tema.bloque]}",
                f"titulo: {tema.titulo.replace(chr(10), ' ')}",
                f"origen: {tema.apunte}",
                f"resumen: {tema.resumen if tema.resumen is not None else ''}",
                f"banco: {tema.banco if tema.banco is not None else ''}",
                "derechos: privado; material de terceros, no publicar",
                "---",
                "",
            ]
        )
        (out / "temas" / f"{tema.tema_id}.md").write_text(front_matter + cuerpo, encoding="utf-8")
        (out / "preguntas" / f"{tema.tema_id}.json").write_text(
            json.dumps([pregunta.to_dict() for pregunta in preguntas], ensure_ascii=False, indent=2)
            + "\n",
            encoding="utf-8",
        )
        catalogo.append(
            {
                "tema": tema.tema_id,
                "bloque": ROMANOS[tema.bloque],
                "titulo": tema.titulo,
                "apunte": str(tema.apunte),
                "resumen": str(tema.resumen) if tema.resumen is not None else None,
                "banco": str(tema.banco) if tema.banco is not None else None,
                "caracteres": tema.caracteres,
                "apartados": tema.apartados,
                "tablas": tema.tablas,
                "preguntas_banco": len(tema.preguntas),
                "con_respuesta": sum(
                    1 for pregunta in tema.preguntas if pregunta.correcta is not None
                ),
                "fuentes_citadas": tema.fuentes[:10],
            }
        )

    raices_imagenes = (
        list(images_roots)
        if images_roots is not None
        else [
            source_root / "1. TAI_2026",
            Path.home() / "OneDrive" / "Escritorio" / "1. TAI_2026",
        ]
    )
    imagenes = _extraer_imagenes(raices_imagenes, out / "imagenes") if extract_images else {}
    manifiesto = {
        "generado": datetime.now(UTC).isoformat(),
        "origen": str(source_root),
        "derechos": (
            "Privado. Material de terceros (academia, internet, biblioteca propia); no publicar."
        ),
        "resumen": {
            "temas_recuperados": len(temas),
            "temas_oficiales": sum(BLOQUES_OFICIALES.values()),
            "faltan": faltan,
            "preguntas_totales": sum(len(tema.preguntas) for tema in temas.values()),
            "temas_con_10_preguntas": sum(
                1 for tema in temas.values() if len(tema.preguntas) >= 10
            ),
            "imagenes_extraidas": sum(imagenes.values()),
        },
        "temas": catalogo,
        "imagenes": imagenes,
    }
    (out / "manifest.json").write_text(
        json.dumps(manifiesto, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (out / "README.md").write_text(
        "# Temario TAI recuperado (privado)\n\n"
        "Consolidado desde `F:\\OpoFuente\\APUNTES`, `RESUMENES` y el banco por tema. "
        "**No se publica**:\n"
        "parte del material viene de temarios de academia y fuentes de terceros.\n\n"
        "- `temas/<I.1…>.md`: apunte completo con front-matter y sus fuentes citadas.\n"
        "- `preguntas/<I.1…>.json`: 10 preguntas por tema con respuesta y origen.\n"
        "- `imagenes/`: imágenes extraídas de los PDFs de `1. TAI_2026`.\n"
        "- `manifest.json`: inventario, recuentos y temas que faltan.\n\n"
        "Regenerar: `uv run python -m opofuente.tools.recover_temario`.\n",
        encoding="utf-8",
    )
    return manifiesto


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source-root",
        type=Path,
        default=Path(r"F:\OpoFuente"),
        help="raíz con APUNTES, RESUMENES, BANCO y 1. TAI_2026",
    )
    parser.add_argument("--out", type=Path, default=project_root() / "data" / "temario-recuperado")
    parser.add_argument(
        "--sin-imagenes", action="store_true", help="no extrae imágenes de los PDFs"
    )
    args = parser.parse_args(list(argv) if argv is not None else None)
    try:
        manifiesto = recover(
            source_root=args.source_root, out=args.out, extract_images=not args.sin_imagenes
        )
    except RuntimeError as error:
        print(str(error), file=sys.stderr)
        return 1
    print(json.dumps({"out": str(args.out), **manifiesto["resumen"]}, ensure_ascii=False))
    if manifiesto["resumen"]["faltan"]:
        print(f"Faltan temas: {', '.join(manifiesto['resumen']['faltan'])}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
