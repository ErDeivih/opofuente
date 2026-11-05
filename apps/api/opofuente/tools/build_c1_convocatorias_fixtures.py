"""Construye el fixture de convocatorias de informática C1 que referencian el temario común.

Fuentes (verificadas por sha256 contra `fixtures/curricula/manifest.json`):

- `fuentes/oposicionesinformatica/c1.txt`: 10 listados de convocatorias de informática C1 con su
  enlace. Es un agregador: **no** son bases oficiales, así que las convocatorias entran en
  `draft` («por confirmar») y su cita dice de dónde salen y cuándo se observaron.
- `minicerebro/convocatorias.csv`: inventario por administración, grupo y enlace. Solo se importan
  las filas con **grupo C1 explícito** y enlace oficial; el resto se descarta con su motivo escrito
  (no se convierte una bolsa o un portal en una convocatoria). La fila del TAI 2025 se descarta
  porque ya está sembrada como perfil propio (B-002), con su ref `primary`.

Nada se inventa: si la fuente no publica la fecha oficial se usa la **fecha de observación** y el
fixture lo dice en `published_at_note`; si no hay bases, la cita lo declara.

Uso:
    uv run python -m opofuente.tools.build_c1_convocatorias_fixtures
    uv run python -m opofuente.tools.build_c1_convocatorias_fixtures --check
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import re
import sys
import unicodedata
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from opofuente.config import project_root
from opofuente.domain.errors import InvariantViolationError

MANIFEST = Path("fixtures") / "curricula" / "manifest.json"
FIXTURE = Path("fixtures") / "curricula" / "convocatorias-c1.json"

_LISTADO_ENV = "OPOFUENTE_C1_LISTADO"
_CSV_ENV = "OPOFUENTE_CONVOCATORIAS_CSV"

_DATE = re.compile(r"(\d{2})/(\d{2})/(\d{4})")
_LAST_SEGMENT = re.compile(r",\s*([^,]+)$")

CRITERIA = (
    "Solo se importan convocatorias de informática C1: grupo C1 explícito en el inventario o "
    "listado de informática C1 en el agregador.",
    "Las filas de bolsas de empleo, portales o grupos distintos de C1 no se convierten en "
    "convocatorias: se descartan con su motivo.",
    "La convocatoria del TAI 2025 del inventario se descarta porque ya está sembrada como perfil "
    "propio (B-002) y su referencia primary ya existe.",
    "Si la fuente no publica la fecha oficial se usa la fecha de observación y se dice en el "
    "fixture; no se inventa una fecha de bases.",
    "Las entradas del agregador entran en draft (por confirmar) y su cita declara que no se han "
    "verificado bases oficiales; las del inventario con enlace oficial entran en archived "
    "(cerradas).",
)


@dataclass(frozen=True, slots=True)
class Source:
    id: str
    document: str
    local_path: Path
    sha256: str
    observed_at: str


@dataclass(frozen=True, slots=True)
class Convocatoria:
    code: str
    title: str
    administration: str | None
    territory: str | None
    official_url: str
    published_at: str
    published_at_note: str | None
    status: str
    source_reference: str
    source_id: str


def _slug(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value)
    ascii_only = "".join(char for char in decomposed if not unicodedata.combining(char))
    limpio = re.sub(r"[^a-z0-9]+", "-", ascii_only.lower()).strip("-")
    return limpio or "convocatoria"


def _load_manifest(root: Path) -> dict[str, Source]:
    ruta = root / MANIFEST
    if not ruta.is_file():
        raise InvariantViolationError(f"falta el manifiesto de fuentes: {MANIFEST}")
    data = json.loads(ruta.read_text(encoding="utf-8"))
    fuentes: dict[str, Source] = {}
    for entrada in data["sources"]:
        if "observed_at" not in entrada:
            continue
        fuentes[str(entrada["id"])] = Source(
            id=str(entrada["id"]),
            document=str(entrada["document"]),
            local_path=Path(str(entrada["local_path"])),
            sha256=str(entrada["sha256"]),
            observed_at=str(entrada["observed_at"]),
        )
    return fuentes


def _resolve(root: Path, source: Source, override: Path | None) -> Path:
    if override is not None:
        return override
    from_env = os.environ.get(_LISTADO_ENV if source.id == "c1-agregador" else _CSV_ENV)
    if from_env:
        return Path(from_env)
    return root / source.local_path


def _verify(path: Path, source: Source) -> str:
    if not path.is_file():
        raise InvariantViolationError(
            f"falta la fuente {source.id}: {path}. Copia {source.document} a {source.local_path} "
            "o define la variable de entorno correspondiente"
        )
    # `utf-8-sig`: el inventario puede venir con BOM; sin quitarlo, la primera columna
    # (`administracion`) no se encontraría y el código saldría como «c1-administracion-…».
    texto = path.read_text(encoding="utf-8-sig")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != source.sha256:
        raise InvariantViolationError(
            f"la fuente {source.id} no coincide con el manifiesto: {digest[:12]}… != "
            f"{source.sha256[:12]}…; si el listado cambió, revísalo y actualiza el manifiesto"
        )
    return texto


def _parse_listado(texto: str, source: Source) -> list[Convocatoria]:
    """Cada entrada del listado son dos líneas: el título y su enlace."""
    lineas = [linea.strip() for linea in texto.splitlines() if linea.strip()]
    convocatorias: list[Convocatoria] = []
    codigos: set[str] = set()
    indice = 0
    while indice < len(lineas):
        titulo = lineas[indice]
        if not titulo.startswith("- "):
            indice += 1
            continue
        if indice + 1 >= len(lineas):
            raise InvariantViolationError(f"{source.id}: la entrada {titulo!r} no tiene enlace")
        enlace = lineas[indice + 1]
        if not enlace.startswith("http"):
            raise InvariantViolationError(f"{source.id}: el enlace de {titulo!r} no es una URL")
        titulo = titulo[2:].strip()
        segmento = urlparse(enlace).path.strip("/").split("/")[-1] or "convocatoria"
        code = f"c1-{_slug(segmento)[:50]}"
        while code in codigos:
            code = f"{code}-2"
        codigos.add(code)
        coincidencia = _LAST_SEGMENT.search(titulo)
        territorio = coincidencia.group(1).strip() if coincidencia else None
        administracion = None
        if territorio is not None and ", " in titulo:
            administracion = titulo[: titulo.rfind(", ")].split(", ")[-1].strip()
        convocatorias.append(
            Convocatoria(
                code=code,
                title=titulo,
                administration=administracion,
                territory=territorio,
                official_url=enlace,
                published_at=source.observed_at,
                published_at_note=(
                    "fecha de observación del listado; la fuente no publica la fecha oficial"
                ),
                status="draft",
                source_reference=(
                    f"Listado de oposicionesinformatica.com observado el {source.observed_at}; "
                    "sin bases oficiales verificadas"
                ),
                source_id=source.id,
            )
        )
        indice += 2
    if not convocatorias:
        raise InvariantViolationError(f"{source.id}: el listado no tiene ninguna convocatoria")
    return convocatorias


def _parse_inventario(
    texto: str, source: Source
) -> tuple[list[Convocatoria], list[dict[str, Any]]]:
    """Importa solo filas de grupo C1 con enlace; el resto se descarta con su motivo."""
    filas = list(csv.DictReader(io.StringIO(texto), delimiter=";"))
    if not filas:
        raise InvariantViolationError(f"{source.id}: el inventario está vacío")
    convocatorias: list[Convocatoria] = []
    descartadas: list[dict[str, Any]] = []
    codigos: set[str] = set()
    for numero, fila in enumerate(filas, start=2):
        grupo = (fila.get("grupo") or "").strip()
        enlace = (fila.get("enlace") or "").strip()
        puesto = (fila.get("puesto") or "").strip()
        if grupo.upper() != "C1":
            descartadas.append(
                {
                    "source_id": source.id,
                    "row": numero,
                    "title": puesto or "(sin puesto)",
                    "reason": f"no es C1 (grupo={grupo or 'no consta'})",
                }
            )
            continue
        if not enlace.startswith("http"):
            descartadas.append(
                {
                    "source_id": source.id,
                    "row": numero,
                    "title": puesto,
                    "reason": "sin enlace oficial",
                }
            )
            continue
        if "Técnicos Auxiliares de Informática" in puesto:
            descartadas.append(
                {
                    "source_id": source.id,
                    "row": numero,
                    "title": puesto,
                    "reason": "ya está sembrada como convocatoria del perfil TAI 2025",
                }
            )
            continue

        administracion = (fila.get("administracion") or "").strip() or None
        territorio = None
        sufijo = re.search(r"-\s*(.+)$", puesto)
        if sufijo:
            territorio = sufijo.group(1).strip()
            territorio = territorio[:1].upper() + territorio[1:]
        code = f"c1-{_slug(f'{administracion or "administracion"} {territorio or ""}')[:55]}"
        while code in codigos:
            code = f"{code}-2"
        codigos.add(code)

        fecha = _DATE.search(fila.get("plazo") or "") or _DATE.search(fila.get("publicacion") or "")
        publicada = (
            f"{fecha.group(3)}-{fecha.group(2)}-{fecha.group(1)}" if fecha else (source.observed_at)
        )
        nota_fecha = (
            "fecha conocida según el inventario (columna de plazo/publicación); no consta la de "
            "las bases"
            if fecha
            else f"fecha de observación del inventario ({source.observed_at}); "
            "la fuente no publica la fecha en esta fila"
        )
        convocatorias.append(
            Convocatoria(
                code=code,
                title=puesto,
                administration=administracion,
                territory=territorio,
                official_url=enlace,
                published_at=publicada,
                published_at_note=nota_fecha,
                status="archived",
                source_reference=(
                    f"{fila.get('publicacion') or 'Boletín oficial'}; "
                    f"estado en la fuente: {fila.get('estado') or 'no consta'}"
                ),
                source_id=source.id,
            )
        )
    return convocatorias, descartadas


def _validar(items: list[Convocatoria]) -> None:
    codigos = [item.code for item in items]
    if len(codigos) != len(set(codigos)):
        raise InvariantViolationError("el fixture generaría códigos de convocatoria repetidos")
    for item in items:
        if len(item.code) > 64:
            raise InvariantViolationError(f"código de convocatoria demasiado largo: {item.code}")
        if item.status not in {"draft", "archived"}:
            raise InvariantViolationError(f"{item.code}: estado no válido ({item.status})")
        if not item.official_url.startswith("http"):
            raise InvariantViolationError(f"{item.code}: el enlace no es una URL")
        date.fromisoformat(item.published_at)
        if not item.source_reference.strip():
            raise InvariantViolationError(f"{item.code}: no tiene cita de procedencia")
        if not item.title.strip():
            raise InvariantViolationError(f"{item.code}: no tiene título")


def build_fixture(
    convocatorias: list[Convocatoria],
    descartadas: list[dict[str, Any]],
    fuentes: dict[str, Source],
) -> dict[str, Any]:
    return {
        "opposition": {
            "code": "informatica-c1",
            "name": "Informática C1",
            "description": (
                "Convocatorias de informática C1 que estudian el temario común. "
                "Las entradas en draft están pendientes de confirmar sus bases."
            ),
        },
        "generated_from": {
            "criteria": list(CRITERIA),
            "sources": [
                {
                    "id": source.id,
                    "document": source.document,
                    "sha256": source.sha256,
                    "observed_at": source.observed_at,
                }
                for source in fuentes.values()
            ],
        },
        "convocatorias": [
            {
                "code": item.code,
                "title": item.title,
                "administration": item.administration,
                "territory": item.territory,
                "group_code": "C1",
                "official_url": item.official_url,
                "published_at": item.published_at,
                "published_at_note": item.published_at_note,
                "status": item.status,
                "source_reference": item.source_reference,
                "source_id": item.source_id,
            }
            for item in convocatorias
        ],
        "discarded": descartadas,
    }


def render(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2) + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    check_only = "--check" in args
    root = project_root()
    fuentes = _load_manifest(root)
    try:
        listado = fuentes["c1-agregador"]
        inventario = fuentes["convocatorias-csv"]
    except KeyError as error:  # pragma: no cover - manifiesto incompleto
        raise InvariantViolationError(f"falta la fuente {error} en el manifiesto") from error

    ruta_listado = _resolve(root, listado, None)
    ruta_csv = _resolve(root, inventario, None)
    texto_listado = _verify(ruta_listado, listado)
    texto_csv = _verify(ruta_csv, inventario)

    convocatorias = _parse_listado(texto_listado, listado)
    del_inventario, descartadas = _parse_inventario(texto_csv, inventario)
    convocatorias.extend(del_inventario)
    _validar(convocatorias)
    contenido = render(build_fixture(convocatorias, descartadas, fuentes))
    destino = root / FIXTURE

    print(f"Fuentes verificadas: {ruta_listado.name}, {ruta_csv.name}")
    print(
        f"  {len(convocatorias)} convocatorias C1 ({len(descartadas)} filas descartadas del "
        f"inventario con su motivo)"
    )

    if check_only:
        if not destino.is_file() or destino.read_text(encoding="utf-8") != contenido:
            print(
                "El fixture de convocatorias C1 no coincide con sus fuentes. Ejecuta: "
                "uv run python -m opofuente.tools.build_c1_convocatorias_fixtures",
                file=sys.stderr,
            )
            return 1
        print("Fixture de convocatorias C1 sincronizado con sus fuentes.")
        return 0

    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(contenido, encoding="utf-8", newline="\n")
    print(f"Fixture escrito: {destino}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
