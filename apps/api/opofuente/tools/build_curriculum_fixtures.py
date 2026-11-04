"""Construye el fixture del temario común v1 desde su fuente verificada.

Por qué existe esta herramienta y no un JSON escrito a mano (mismo criterio que
`build_profile_fixtures.py`, ADR-006):

1. la fuente es `minicerebro/temario-c1.md`, del espacio de contenido de `ESPECIFICACION.md` §2;
2. antes de leerla se comprueba su `sha256` contra `fixtures/curricula/manifest.json`: si el
   documento cambia, la herramienta falla y **no genera nada**;
3. el árbol se extrae del propio documento: los 5 bloques (`## BLOQUE <romano> — …`) y sus 40 temas
   numerados; el texto de cada tema se conserva íntegro (solo se quita la marca de énfasis de
   Markdown y se unen las líneas partidas);
4. se comprueban los recuentos aprobados (5 bloques / 40 temas / 45 nodos), que la numeración sea
   1-40 y que las rutas sean `I.1`…`V.40`, sin perder ni inventar ningún tema.

La referencia `primary` del TAI 2025 no se deduce del documento: es la decisión de producto O1
(aprobada con la especificación) y viaja en el fixture con su cita de las bases.

Uso:
    uv run python -m opofuente.tools.build_curriculum_fixtures            # escribe el fixture
    uv run python -m opofuente.tools.build_curriculum_fixtures --check    # falla si hay diferencias

La fuente se busca, por este orden, en `--source <ruta>`, en la variable `OPOFUENTE_TEMARIO_C1` o en
la ruta local declarada en el manifiesto (`data/sources/…`, ignorada por git).
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from opofuente.config import project_root
from opofuente.domain.curricula import V1_BLOCKS, V1_NODES, V1_TOPICS
from opofuente.domain.errors import InvariantViolationError

MANIFEST = Path("fixtures") / "curricula" / "manifest.json"
FIXTURE = Path("fixtures") / "curricula" / "informatica-c1.v1.json"
SOURCE_ENV = "OPOFUENTE_TEMARIO_C1"

_BLOCK = re.compile(
    r"^##\s+BLOQUE\s+([IVXLCDM]+)\s*[\u2014\u2013-]\s*(.+?)\s*"
    r"\(temas\s+(\d+)[-\u2013](\d+)\)\s*$"
)
_TOPIC = re.compile(r"^(\d+)\.\s+(.*)$")
_WHITESPACE = re.compile(r"\s+")

TRANSFORMATIONS = (
    "El temario fuente es un documento de trabajo: agrupa 5 bloques y 40 temas numerados 1-40.",
    "Los bloques son los encabezados «## BLOQUE <romano> — <título> (temas a-b)»: el título del "
    "nodo es el nombre del bloque y el sufijo del rango se usa para comprobar su contenido.",
    "Los temas son los párrafos numerados que cuelgan de cada bloque; se une el texto partido en "
    "varias líneas y se quita la marca de énfasis de Markdown (**). No se resume ni se recorta "
    "ninguna palabra.",
    "El número que publica la fuente es el official_code del tema y la ruta es <bloque>.<número> "
    "(I.1 … V.40), como fija ESPECIFICACION §5.4.",
    "La referencia primary del TAI 2025 es la decisión de producto O1, no se deduce del documento; "
    "se guarda con su cita de las bases.",
)


@dataclass(frozen=True, slots=True)
class Source:
    id: str
    document: str
    local_path: Path
    sha256: str


@dataclass(frozen=True, slots=True)
class BlockSource:
    roman: str
    title: str
    first_topic: int
    last_topic: int


def _load_manifest(root: Path) -> Source:
    ruta = root / MANIFEST
    if not ruta.is_file():
        raise InvariantViolationError(f"falta el manifiesto de fuentes: {MANIFEST}")
    data = json.loads(ruta.read_text(encoding="utf-8"))
    sources = data["sources"]
    if len(sources) != 1:
        raise InvariantViolationError(
            f"{MANIFEST}: se esperaba una fuente para el temario común y hay {len(sources)}"
        )
    entrada = sources[0]
    return Source(
        id=entrada["id"],
        document=entrada["document"],
        local_path=Path(entrada["local_path"]),
        sha256=entrada["sha256"],
    )


def _resolve_source(root: Path, source: Source, override: Path | None) -> Path:
    if override is not None:
        return override
    from_env = os.environ.get(SOURCE_ENV)
    if from_env:
        return Path(from_env)
    return root / source.local_path


def _verify_source(path: Path, source: Source) -> None:
    if not path.is_file():
        raise InvariantViolationError(
            f"falta la fuente del temario común: {path}. Copia minicerebro/temario-c1.md a "
            f"{source.local_path} o define {SOURCE_ENV} con su ruta"
        )
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != source.sha256:
        raise InvariantViolationError(
            f"la fuente del temario no coincide con el manifiesto: {digest[:12]}… != "
            f"{source.sha256[:12]}…; si el documento cambió, revisa el temario y actualiza el "
            "manifiesto a mano"
        )


def parse_blocks(markdown: str) -> list[tuple[BlockSource, list[tuple[int, str]]]]:
    """Devuelve cada bloque con sus temas (número y texto completo), sin perder líneas."""
    bloques: list[tuple[BlockSource, list[tuple[int, str]]]] = []
    actual: BlockSource | None = None
    temas: list[tuple[int, str]] = []
    pendiente: tuple[int, list[str]] | None = None

    def cerrar_tema() -> None:
        nonlocal pendiente
        if pendiente is not None:
            numero, partes = pendiente
            texto = _WHITESPACE.sub(" ", " ".join(partes)).replace("**", "").strip()
            if not texto:
                raise InvariantViolationError(f"el tema {numero} del temario fuente está vacío")
            temas.append((numero, texto))
            pendiente = None

    for linea_cruda in markdown.splitlines():
        linea = linea_cruda.strip()
        if not linea:
            cerrar_tema()
            continue
        if linea.startswith("## "):
            cerrar_tema()
            coincidencia = _BLOCK.match(linea)
            if coincidencia is None:
                # Cualquier otro encabezado de nivel 2 termina el temario (leyes, plan de estudio…).
                if actual is not None:
                    break
                continue
            if actual is not None:
                bloques.append((actual, temas))
            actual = BlockSource(
                roman=coincidencia.group(1),
                title=coincidencia.group(2).strip(),
                first_topic=int(coincidencia.group(3)),
                last_topic=int(coincidencia.group(4)),
            )
            temas = []
            continue
        if linea == "---":
            cerrar_tema()
            if actual is not None:
                break
            continue
        coincidencia_tema = _TOPIC.match(linea)
        if actual is not None and coincidencia_tema is not None:
            # Un tema empieza con «N. » a principio de línea; si había uno abierto, sus líneas
            # partidas ya se acumularon y aquí termina.
            cerrar_tema()
            numero = int(coincidencia_tema.group(1))
            pendiente = (numero, [coincidencia_tema.group(2).strip()])
            continue
        if pendiente is not None:
            pendiente[1].append(linea)
            continue
        if actual is not None:
            raise InvariantViolationError(
                f"texto suelto en el temario fuente, fuera de un tema: {linea[:80]!r}"
            )

    cerrar_tema()
    if actual is not None:
        bloques.append((actual, temas))
    return bloques


def build_nodes(
    bloques: list[tuple[BlockSource, list[tuple[int, str]]]], document: str
) -> list[dict[str, Any]]:
    """Convierte los bloques leídos en el árbol de nodos del fixture."""
    if len(bloques) != V1_BLOCKS:
        raise InvariantViolationError(
            f"el temario fuente tiene {len(bloques)} bloques y la v1 aprobada tiene {V1_BLOCKS}"
        )
    nodos: list[dict[str, Any]] = []
    total_temas = 0
    for posicion, (bloque, temas) in enumerate(bloques, start=1):
        esperados = list(range(bloque.first_topic, bloque.last_topic + 1))
        numeros = [numero for numero, _texto in temas]
        if numeros != esperados:
            raise InvariantViolationError(
                f"BLOQUE {bloque.roman}: se esperaban los temas {esperados} y hay {numeros}"
            )
        hijos: list[dict[str, Any]] = []
        for posicion_tema, (numero, texto) in enumerate(temas, start=1):
            hijos.append(
                {
                    "node_type": "topic",
                    "official_code": str(numero),
                    "title": texto,
                    "position": posicion_tema,
                    "path": f"{bloque.roman}.{numero}",
                    "depth": 1,
                    "children": [],
                }
            )
        total_temas += len(hijos)
        nodos.append(
            {
                "node_type": "block",
                "official_code": bloque.roman,
                "title": bloque.title,
                "position": posicion,
                "path": bloque.roman,
                "depth": 0,
                "source_reference": (
                    f"{document}, BLOQUE {bloque.roman} — {bloque.title} "
                    f"(temas {bloque.first_topic}-{bloque.last_topic})"
                ),
                "children": hijos,
            }
        )

    total_nodos = len(nodos) + total_temas
    if (len(nodos), total_temas, total_nodos) != (V1_BLOCKS, V1_TOPICS, V1_NODES):
        raise InvariantViolationError(
            f"el temario fuente da {len(nodos)} bloques / {total_temas} temas / "
            f"{total_nodos} nodos y la v1 aprobada es {V1_BLOCKS}/{V1_TOPICS}/{V1_NODES}"
        )
    rutas = [str(nodo["path"]) for bloque in nodos for nodo in (bloque, *bloque["children"])]
    if len(rutas) != len(set(rutas)):
        raise InvariantViolationError("el temario fuente genera rutas repetidas")
    return nodos


def build_fixture(nodes: list[dict[str, Any]], source: Source) -> dict[str, Any]:
    return {
        "code": "informatica-c1",
        "name": "Temario común de informática C1",
        "group_code": "C1",
        "family": "informatica",
        "version": {
            "version_no": 1,
            "code": "informatica-c1-v1",
            "title": "Temario común de informática C1",
        },
        "generated_from": {
            "document": source.document,
            "sha256": source.sha256,
            "transformations": list(TRANSFORMATIONS),
        },
        "counts": {"blocks": V1_BLOCKS, "topics": V1_TOPICS, "nodes": V1_NODES},
        "nodes": nodes,
        "referenced_by": [
            {
                "convocation_code": "tai-age-2025",
                "role": "primary",
                # Cita del ANEXO V del BOE-A-2025-26262, que es donde las bases publican el
                # programa del TAI (ESPECIFICACION §7 O1).
                "source_reference": "ANEXO V, apartado 3",
            }
        ],
    }


def render(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2) + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    check_only = "--check" in args
    source_override: Path | None = None
    if "--source" in args:
        indice = args.index("--source")
        try:
            source_override = Path(args[indice + 1])
        except IndexError as error:
            raise InvariantViolationError("--source necesita una ruta") from error

    root = project_root()
    source = _load_manifest(root)
    ruta_fuente = _resolve_source(root, source, source_override)
    _verify_source(ruta_fuente, source)

    bloques = parse_blocks(ruta_fuente.read_text(encoding="utf-8"))
    nodos = build_nodes(bloques, source.document)
    contenido = render(build_fixture(nodos, source))
    destino = root / FIXTURE

    print(f"Fuente verificada por sha256: {ruta_fuente}")
    print(
        f"  {V1_BLOCKS} bloques, {V1_TOPICS} temas, {V1_NODES} nodos "
        f"(rutas {nodos[0]['children'][0]['path']} … {nodos[-1]['children'][-1]['path']})"
    )

    if check_only:
        if not destino.is_file() or destino.read_text(encoding="utf-8") != contenido:
            print(
                "El fixture del temario común no coincide con su fuente. Ejecuta: "
                "uv run python -m opofuente.tools.build_curriculum_fixtures",
                file=sys.stderr,
            )
            return 1
        print("Fixture del temario común sincronizado con su fuente.")
        return 0

    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(contenido, encoding="utf-8", newline="\n")
    print(f"Fixture escrito: {destino}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
