"""Construye los fixtures de perfil desde las fuentes oficiales verificadas.

Por qué existe esta herramienta y no un JSON escrito a mano: el programa oficial y las reglas de
examen deben poder rastrearse hasta el documento descargado. Aquí se hace así:

1. se verifica el `sha256` de cada fuente contra `fixtures/profiles/manifest.json` (si el documento
   cambia, la herramienta falla y no se genera nada);
2. el **programa** se extrae automáticamente del documento oficial: en TAI del ANEXO V del BOE, en
   Guardia Civil del PDF oficial del temario;
3. cada valor de los **perfiles curados** (`*.profile.json`) lleva una cita literal de la fuente, y
   la herramienta comprueba que esa cita existe de verdad antes de escribir nada.

Una cifra sin cita no puede entrar en un fixture.

Uso:
    uv run python -m opofuente.tools.build_profile_fixtures             # escribe los fixtures
    uv run python -m opofuente.tools.build_profile_fixtures --check     # falla si hay diferencias
"""

from __future__ import annotations

import html
import json
import re
import sys
import unicodedata
import xml.etree.ElementTree as ET
from collections.abc import Iterable, Iterator, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pymupdf

from opofuente.config import project_root
from opofuente.domain.errors import InvariantViolationError

MANIFEST = Path("fixtures") / "profiles" / "manifest.json"
PROFILE_SUFFIX = ".profile.json"
CURRICULUM_SUFFIX = ".curriculum.json"

BULLET = "\uf0a7"
SUB_BULLET = "\uf0b7"
_IGNORED_PREFIXES = (
    "--- pagina",
    "TEMARIO DE LAS CONVOCATORIAS",
    "CENTROS DOCENTES",
    "DE LA GUARDIA CIVIL",
)
_WHITESPACE = re.compile(r"\s+")
_PARAGRAPH = re.compile(r"<p\b([^>]*)>(.*?)</p>", re.DOTALL | re.IGNORECASE)
_CLASS = re.compile(r'class="([^"]*)"')
#: Clases con las que los boletines marcan el encabezado de un anexo: el XML del BOE usa
#: `anexo_num`/`anexo` y el HTML del BOCYL, `aparienciaTitulo`.
_ANNEX_CLASSES = frozenset({"anexo_num", "anexo", "aparienciaTitulo"})
#: Raya del separador de los títulos de tema del BOCYL («Tema 1.<raya> …»). Se escribe escapada
#: porque la raya y el guion son caracteres distintos y el patrón admite los dos.
_EN_DASH = "\u2013"
_TOPIC = re.compile(rf"^Tema\s+(\d+)\.\s*[{_EN_DASH}-]\s*(.+)$")


def normalize(value: str) -> str:
    """Texto comparable: sin etiquetas HTML, sin entidades y con espacios colapsados."""
    without_tags = re.sub(r"<[^>]+>", " ", value)
    return _WHITESPACE.sub(" ", html.unescape(without_tags)).strip()


def slug(value: str) -> str:
    """Clave estable para un título: sin tildes, en minúsculas y con guiones."""
    decomposed = unicodedata.normalize("NFKD", value)
    ascii_only = "".join(char for char in decomposed if not unicodedata.combining(char))
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", ascii_only.lower())).strip("-")


# --------------------------------------------------------------------------- fuentes


@dataclass(frozen=True, slots=True)
class Source:
    id: str
    local_path: Path
    sha256: str
    role: str
    profile_code: str | None


def load_manifest(root: Path) -> list[Source]:
    manifest_path = root / MANIFEST
    if not manifest_path.is_file():
        raise InvariantViolationError(f"falta el manifiesto de fuentes: {MANIFEST}")
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    sources = [
        Source(
            id=entry["id"],
            local_path=root / entry["local_path"],
            sha256=entry["sha256"],
            role=entry["role"],
            profile_code=entry.get("profile_code"),
        )
        for entry in data["sources"]
    ]
    if not sources:
        raise InvariantViolationError("el manifiesto no declara ninguna fuente")
    return sources


def verify_sources(sources: Iterable[Source]) -> None:
    import hashlib

    missing: list[str] = []
    mismatch: list[str] = []
    for source in sources:
        if not source.local_path.is_file():
            missing.append(str(source.local_path))
            continue
        digest = hashlib.sha256(source.local_path.read_bytes()).hexdigest()
        if digest != source.sha256:
            mismatch.append(f"{source.local_path} ({digest[:12]}… != {source.sha256[:12]}…)")
    if missing:
        raise InvariantViolationError(
            "faltan fuentes locales; ejecuta scripts/fetch-sources.ps1: " + ", ".join(missing)
        )
    if mismatch:
        raise InvariantViolationError(
            "el documento descargado no coincide con el hash del manifiesto: " + "; ".join(mismatch)
        )


def xml_paragraphs(path: Path) -> list[tuple[str, str]]:
    """Pares (clase CSS, texto) de todos los párrafos del XML del BOE.

    `# noqa: S314`: se analiza XML de fuera, pero solo después de comprobar su `sha256` contra el
    manifiesto (`verify_sources`), así que a estas alturas el documento no es entrada no confiable.
    Los extractores que en S03 lean XML/HTML del usuario sí tendrán que defenderse (DEBT-004).
    """
    root = ET.parse(path).getroot()  # noqa: S314
    result: list[tuple[str, str]] = []
    for element in root.iter():
        if element.tag != "p":
            continue
        text = normalize("".join(element.itertext()))
        if text:
            result.append((element.get("class") or "", text))
    return result


def html_paragraphs(path: Path) -> list[tuple[str, str]]:
    """Pares (clase CSS, texto) de todos los párrafos de un documento HTML.

    El BOCYL publica cada párrafo del acto en su propio `<p>` y marca los encabezados de anexo con
    la clase `aparienciaTitulo`. Se analiza con expresiones regulares porque el HTML del boletín no
    es XML bien formado; el fichero ya está verificado por `sha256` contra el manifiesto.
    """
    raw = path.read_text(encoding="utf-8", errors="replace")
    result: list[tuple[str, str]] = []
    for match in _PARAGRAPH.finditer(raw):
        css = _CLASS.search(match.group(1))
        text = normalize(match.group(2))
        if text:
            result.append((css.group(1) if css else "", text))
    return result


def pdf_text(path: Path) -> str:
    # PyMuPDF no publica tipos: la llamada no se puede comprobar, pero el fichero ya está
    # verificado por sha256 contra el manifiesto antes de llegar aquí.
    with pymupdf.open(path) as document:
        return "\n".join(page.get_text() for page in document)


def annex_range(paragraphs: Sequence[tuple[str, str]], heading: str) -> tuple[int, int]:
    """Rango [inicio, fin) de un anexo identificado por su encabezado."""
    start = None
    for index, (css, text) in enumerate(paragraphs):
        if css in _ANNEX_CLASSES and text.upper() == heading.upper():
            start = index
            break
    if start is None:
        raise InvariantViolationError(f"no se encontró el anexo {heading!r} en el documento")
    end = len(paragraphs)
    for index in range(start + 1, len(paragraphs)):
        css, _text = paragraphs[index]
        if css in _ANNEX_CLASSES:
            end = index
            break
    return start, end


def bocyl_annex_range(paragraphs: Sequence[tuple[str, str]], heading: str) -> tuple[int, int]:
    """Rango [inicio, fin) de un anexo del BOCYL en HTML.

    Aquí no sirve cortar por clase CSS: en el BOCYL el encabezado del anexo y el título que lo
    sigue comparten la misma clase (`aparienciaTitulo`), así que el corte por clase dejaría el
    anexo vacío a la altura de su propio título. El anexo acaba donde empieza el siguiente.
    """
    start = None
    for index, (_css, text) in enumerate(paragraphs):
        if text.upper() == heading.upper():
            start = index
            break
    if start is None:
        raise InvariantViolationError(f"no se encontró el anexo {heading!r} en el documento")

    end = len(paragraphs)
    for index in range(start + 1, len(paragraphs)):
        _css, text = paragraphs[index]
        if text.upper().startswith("ANEXO "):
            end = index
            break
    return start, end


def source_text(source_id: str, cache: dict[str, str], sources: dict[str, Source]) -> str:
    """Texto normalizado de una fuente, para verificar citas."""
    if source_id in cache:
        return cache[source_id]
    source = sources.get(source_id)
    if source is None:
        raise InvariantViolationError(
            f"cita a una fuente que no está en el manifiesto: {source_id}"
        )

    suffix = source.local_path.suffix.lower()
    if suffix == ".xml":
        paragraphs = xml_paragraphs(source.local_path)
        if source_id.startswith("tai"):
            # En TAI el programa y las reglas están en el ANEXO V; el resto del BOE convoca a
            # otros cuerpos y no debe poder «validar» una cita por casualidad.
            start, end = annex_range(paragraphs, "ANEXO V")
            text = normalize(" ".join(value for _css, value in paragraphs[start:end]))
        else:
            text = normalize(" ".join(value for _css, value in paragraphs))
    elif suffix == ".pdf":
        text = normalize(pdf_text(source.local_path))
    else:
        text = normalize(source.local_path.read_text(encoding="utf-8", errors="replace"))

    cache[source_id] = text
    return text


def verify_quotes(
    node: Any,
    path: str,
    *,
    cache: dict[str, str],
    sources: dict[str, Source],
    checked: list[str],
) -> None:
    """Comprueba recursivamente que toda cita de evidencia existe en su fuente."""
    if isinstance(node, dict):
        evidence = node.get("evidence")
        if isinstance(evidence, dict):
            source_id = evidence.get("source_id")
            quote = normalize(str(evidence.get("quote", "")))
            if not source_id or not quote:
                raise InvariantViolationError(f"{path}: evidencia incompleta ({evidence!r})")
            if quote not in source_text(source_id, cache, sources):
                raise InvariantViolationError(
                    f"{path}: la cita no aparece literalmente en {source_id}: {quote[:80]!r}"
                )
            checked.append(f"{path} -> {source_id}")
        for key, value in node.items():
            verify_quotes(value, f"{path}.{key}", cache=cache, sources=sources, checked=checked)
    elif isinstance(node, list):
        for index, value in enumerate(node):
            verify_quotes(value, f"{path}[{index}]", cache=cache, sources=sources, checked=checked)


# --------------------------------------------------------------------------- programas


def tai_curriculum(path: Path) -> list[dict[str, Any]]:
    paragraphs = xml_paragraphs(path)
    start, end = annex_range(paragraphs, "ANEXO V")
    section = paragraphs[start:end]

    program_start = None
    for index, (_css, text) in enumerate(section):
        if text.startswith("3. Programa."):
            program_start = index
            break
    if program_start is None:
        raise InvariantViolationError("no se encontró el apartado «3. Programa.» en el ANEXO V")

    blocks: list[dict[str, Any]] = []
    for css, text in section[program_start + 1 :]:
        block_match = re.match(r"^([IVX]+)\.\s+(.+)$", text) if css == "centro_cursiva" else None
        if block_match:
            blocks.append(
                {
                    "node_type": "block",
                    "official_code": block_match.group(1),
                    "title": block_match.group(2).strip(),
                    "position": len(blocks) + 1,
                    "path": block_match.group(1),
                    "depth": 0,
                    "children": [],
                }
            )
            continue
        topic_match = re.match(r"^(\d+)\.\s+(.+)$", text)
        if topic_match and blocks:
            block = blocks[-1]
            position = len(block["children"]) + 1
            block["children"].append(
                {
                    "node_type": "topic",
                    "official_code": topic_match.group(1),
                    "title": topic_match.group(2).strip(),
                    "position": position,
                    "path": f"{block['official_code']}.{position}",
                    "depth": 1,
                    "children": [],
                }
            )
    return blocks


def gc_curriculum(path: Path) -> list[dict[str, Any]]:
    """Programa de Guardia Civil desde el PDF oficial del temario.

    El PDF usa dos niveles de viñeta: el epígrafe y, dentro de él, subniveles. El modelo de
    programa de OpoFuente solo distingue bloque, tema y epígrafe, así que los subniveles se
    conservan **dentro** del epígrafe separados por «; » en lugar de perderlos o inventar un
    cuarto nivel.
    """
    lines = [line.rstrip() for line in pdf_text(path).splitlines()]
    topics: list[dict[str, Any]] = []
    topic: dict[str, Any] | None = None
    block: dict[str, Any] | None = None
    chunks: list[list[str]] = []
    pending_epigraph = False

    def flush_epigraph() -> None:
        nonlocal chunks, pending_epigraph
        if block is not None and chunks:
            text = "; ".join(
                normalize(" ".join(chunk)) for chunk in chunks if normalize(" ".join(chunk))
            )
            if text:
                position = len(block["children"]) + 1
                block["children"].append(
                    {
                        "node_type": "epigraph",
                        "official_code": str(position),
                        "title": text,
                        "position": position,
                        "path": f"{block['path']}.{position}",
                        "depth": 2,
                        "children": [],
                    }
                )
        chunks = []
        pending_epigraph = False

    for raw in lines:
        stripped = raw.strip()
        if not stripped or _WHITESPACE.fullmatch(stripped):
            continue
        if stripped.isdigit() or stripped.startswith(_IGNORED_PREFIXES):
            continue

        topic_match = re.match(r"^o?\s*TEMA\s+(\d+)\s*\.-\s*(.+)$", stripped, re.IGNORECASE)
        if topic_match:
            flush_epigraph()
            position = int(topic_match.group(1))
            topic = {
                "node_type": "topic",
                "official_code": str(position),
                "title": topic_match.group(2).strip().rstrip("."),
                "position": position,
                "path": str(position),
                "depth": 0,
                "children": [],
            }
            topics.append(topic)
            block = None
            continue

        if topic is None:
            continue

        if re.match(r"^Bloque\b", stripped, re.IGNORECASE):
            flush_epigraph()
            position = len(topic["children"]) + 1
            block = {
                "node_type": "block",
                "official_code": str(position),
                "title": stripped,
                "position": position,
                "path": f"{topic['path']}.{position}",
                "depth": 1,
                "children": [],
            }
            topic["children"].append(block)
            continue

        if stripped == BULLET:  # viñeta de primer nivel: nuevo epígrafe
            flush_epigraph()
            pending_epigraph = True
            chunks = [[]]
            continue

        if stripped == SUB_BULLET:  # viñeta de segundo nivel: subnivel del epígrafe actual
            if chunks and chunks[-1]:
                chunks.append([])
            continue

        if stripped == "o":
            continue

        if (pending_epigraph and chunks) or (block is not None and chunks):
            chunks[-1].append(stripped)
        # Texto suelto sin viñeta ni bloque (encabezados de página) se ignora.

    flush_epigraph()
    return topics


def celador_curriculum(path: Path) -> list[dict[str, Any]]:
    """Programa de Celador/a del SACYL desde el ANEXO II de la orden publicada en el BOCYL.

    El programa oficial son dieciséis temas y nada más: el BOCYL publica cada tema en un párrafo
    que empieza por «Tema» y su número, y no hay bloques ni epígrafes. Por eso los temas cuelgan de
    la raíz y el texto de cada tema se conserva íntegro como título del nodo.
    """
    paragraphs = html_paragraphs(path)
    start, end = bocyl_annex_range(paragraphs, "ANEXO II")

    topics: list[dict[str, Any]] = []
    for _css, text in paragraphs[start + 1 : end]:
        match = _TOPIC.match(text)
        if not match:
            continue
        position = int(match.group(1))
        topics.append(
            {
                "node_type": "topic",
                "official_code": str(position),
                "title": match.group(2).strip(),
                "position": position,
                "path": str(position),
                "depth": 0,
                "children": [],
            }
        )
    return topics


CURRICULUM_BUILDERS = {
    "tai-age-2025": ("tai-boe-convocatoria-xml", "ANEXO V (apartado 3. Programa)", tai_curriculum),
    "gc-cabos-guardias-2026": (
        "gc-temario-oficial-pdf",
        "temario oficial completo",
        gc_curriculum,
    ),
    "celador-sacyl-2022": (
        "celador-2022-bocyl-orden-html",
        "ANEXO II (PROGRAMA)",
        celador_curriculum,
    ),
}

#: Qué se ha hecho con el texto oficial para convertirlo en árbol. Se registra para que nadie
#: tenga que adivinar si el fixture es literal o transformado.
TRANSFORMATIONS: dict[str, list[str]] = {
    "tai-age-2025": [
        "Solo se usa el ANEXO V del BOE; los demás anexos convocan otros cuerpos.",
        "Los bloques son los encabezados «I.» a «IV.» del apartado «3. Programa.» y los temas son "
        "los párrafos numerados que cuelgan de cada bloque. El programa de TAI no publica "
        "epígrafes: el texto de cada tema se conserva íntegro como título del nodo.",
    ],
    "gc-cabos-guardias-2026": [
        "Los temas son los veinticinco «TEMA n.-» del PDF oficial del temario.",
        "Dentro de cada tema, los «Bloque ...» del documento son nodos de tipo bloque.",
        "Los epígrafes son las viñetas de primer nivel del PDF.",
        "Las viñetas de segundo nivel se conservan dentro del epígrafe separadas por «; », porque "
        "el programa de OpoFuente solo distingue bloque, tema y epígrafe.",
        "Se unen las líneas partidas por el salto de página del PDF; no se cambia ni se resume "
        "ninguna palabra del texto oficial.",
    ],
    "celador-sacyl-2022": [
        "Solo se usa el ANEXO II (PROGRAMA) de la orden; los demás anexos son las plazas, el "
        "baremo de méritos y los modelos de solicitud.",
        "Los temas son los dieciséis párrafos que empiezan por «Tema» y su número, en el orden en "
        "que se publican.",
        "El programa oficial no publica bloques ni epígrafes: los dieciséis temas cuelgan de la "
        "raíz y el recuento de bloques y epígrafes del fixture es cero, no se rellena.",
        "El texto de cada tema se conserva íntegro como título del nodo: no se resume ni "
        "se recorta.",
    ],
}


def count_nodes(nodes: Sequence[dict[str, Any]], kind: str) -> int:
    return sum(
        count_nodes(node["children"], kind) + (1 if node["node_type"] == kind else 0)
        for node in nodes
    )


def walk(nodes: Sequence[dict[str, Any]]) -> Iterator[dict[str, Any]]:
    for node in nodes:
        yield node
        yield from walk(node["children"])


def build_curriculum(profile_code: str, sources: dict[str, Source]) -> dict[str, Any]:
    source_id, location, builder = CURRICULUM_BUILDERS[profile_code]
    source = sources[source_id]
    nodes = builder(source.local_path)
    paths = [node["path"] for node in walk(nodes)]
    if len(paths) != len(set(paths)):
        raise InvariantViolationError(f"{profile_code}: hay rutas de programa repetidas")

    return {
        "code": profile_code,
        "generated_from": {
            "source_id": source_id,
            "sha256": source.sha256,
            "location": location,
            "role": source.role,
        },
        "transformations": TRANSFORMATIONS[profile_code],
        "counts": {
            "blocks": count_nodes(nodes, "block"),
            "topics": count_nodes(nodes, "topic"),
            "epigraphs": count_nodes(nodes, "epigraph"),
        },
        "nodes": nodes,
    }


# --------------------------------------------------------------------------- salida


def render(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2) + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    check_only = "--check" in args
    root = project_root()

    sources_list = load_manifest(root)
    sources = {source.id: source for source in sources_list}
    verify_sources(sources_list)
    print(f"Fuentes verificadas por sha256: {len(sources_list)}")

    cache: dict[str, str] = {}
    checked: list[str] = []
    profiles_dir = root / "fixtures" / "profiles"
    outputs: list[tuple[Path, str]] = []

    for profile_path in sorted(profiles_dir.glob(f"*{PROFILE_SUFFIX}")):
        profile = json.loads(profile_path.read_text(encoding="utf-8"))
        code = profile["code"]
        verify_quotes(profile, code, cache=cache, sources=sources, checked=checked)

        curriculum = build_curriculum(code, sources)
        counts = curriculum["counts"]
        print(
            f"  {code}: {counts['blocks']} bloques, {counts['topics']} temas, "
            f"{counts['epigraphs']} epígrafes, {len(profile['exam']['rules'])} reglas"
        )
        outputs.append((profiles_dir / f"{code}{CURRICULUM_SUFFIX}", render(curriculum)))

    print(f"Citas verificadas contra su fuente: {len(checked)}")

    if check_only:
        stale = [
            target.name
            for target, content in outputs
            if not target.is_file() or target.read_text(encoding="utf-8") != content
        ]
        if stale:
            print(
                "Los fixtures de programa no coinciden con las fuentes. Ejecuta: "
                "uv run python -m opofuente.tools.build_profile_fixtures",
                file=sys.stderr,
            )
            print(f"  desincronizados: {', '.join(stale)}", file=sys.stderr)
            return 1
        print("Fixtures de programa sincronizados con las fuentes oficiales.")
        return 0

    for target, content in outputs:
        target.write_text(content, encoding="utf-8", newline="\n")
    print(f"Fixtures escritos: {', '.join(target.name for target, _ in outputs)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
