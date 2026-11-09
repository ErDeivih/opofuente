"""Genera `apps/web/demo/data.json` para la demo estática de GitHub Pages.

No necesita base de datos ni API: lee el fixture del temario común y los dos temas de demo
(`fixtures/demo/tema-*.json`) y escribe un JSON que la demo cliente empaqueta. Solo entran datos
propios o sintéticos: **ningún** perfil de Guardia Civil ni Celador, ni material del corpus real.

Uso:
    uv run python -m opofuente.tools.build_static_demo
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from opofuente.config import project_root

CURRICULUM_FIXTURE = Path("fixtures") / "curricula" / "informatica-c1.v1.json"
DEMO_TOPICS = (
    Path("fixtures") / "demo" / "tema-i1.json",
    Path("fixtures") / "demo" / "tema-ii13.json",
)
SALIDA = Path("apps") / "web" / "demo" / "data.json"


def build_static_demo(*, out: Path, root: Path | None = None) -> dict[str, int]:
    base = root or project_root()
    curriculum = json.loads((base / CURRICULUM_FIXTURE).read_text(encoding="utf-8"))

    # Apuntes largos para los temas que la demo enseña completos; el resto usa la descripción del
    # fixture (una línea), que es lo que ya tiene el temario común.
    temas_demo: dict[str, Any] = {}
    for fixture_path in DEMO_TOPICS:
        fixture = json.loads((base / fixture_path).read_text(encoding="utf-8"))
        temas_demo[str(fixture["node_path"])] = fixture

    bloques = []
    total_temas = 0
    for bloque in curriculum["nodes"]:
        if bloque.get("node_type") != "block":
            continue
        temas = []
        for tema in bloque.get("children", []):
            if tema.get("node_type") != "topic":
                continue
            total_temas += 1
            demo = temas_demo.get(str(tema["path"]))
            temas.append(
                {
                    "path": tema["path"],
                    "title": tema["title"],
                    "apuntes": str(demo["apuntes"]) if demo else str(tema.get("description") or ""),
                    "practica": str(tema["path"]) in temas_demo,
                }
            )
        bloques.append({"path": bloque["path"], "title": bloque["title"], "temas": temas})

    practicas = []
    for path, fixture in temas_demo.items():
        preguntas = [
            {
                "stem": pregunta["stem"],
                "options": [
                    {"key": chr(ord("a") + indice), "text": texto}
                    for indice, texto in enumerate(pregunta["options"])
                ],
                "correct": pregunta["correct"],
                "explanation": pregunta["explanation"],
            }
            for pregunta in fixture["questions"]
        ]
        practicas.append(
            {
                "slug": path.lower().replace(".", "-"),
                "tema_path": path,
                "title": f"Práctica · {fixture['title']}",
                "questions": preguntas,
            }
        )

    data = {
        "title": "OpoFuente — demo estática",
        "warning": (
            "Demo estática: los datos están empaquetados y tus respuestas se guardan solo en este "
            "navegador. No hay servidor, no se envía nada y no hay cuenta."
        ),
        "curriculum": {
            "code": curriculum["code"],
            "name": curriculum["name"],
            "blocks": bloques,
        },
        "practices": practicas,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "blocks": len(bloques),
        "topics": total_temas,
        "practices": len(practicas),
        "questions": sum(len(practica["questions"]) for practica in practicas),
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=project_root() / SALIDA)
    args = parser.parse_args(list(argv) if argv is not None else None)
    counts = build_static_demo(out=args.out)
    print(json.dumps({"out": str(args.out), **counts}, ensure_ascii=False))
    if counts["blocks"] != 5 or counts["topics"] != 40 or counts["practices"] < 2:
        print("La demo estática no tiene el temario y las prácticas esperadas.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
