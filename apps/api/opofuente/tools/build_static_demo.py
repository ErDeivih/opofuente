"""Genera `apps/web/demo/data.json` para la demo estática de GitHub Pages.

No necesita base de datos ni API: lee el fixture del temario común y los ficheros de tema de
`fixtures/demo/` (esquema en `fixtures/demo/README.md`) y escribe el JSON que la demo cliente
empaqueta. Solo entran datos propios o sintéticos: **ningún** perfil de Guardia Civil ni Celador, ni
material del corpus real.

Estados por tema:
- `completo`: al menos 3 secciones y 10 preguntas.
- `con_preguntas`: 10 preguntas pero menos de 3 secciones.
- `pendiente`: no hay fichero; la demo lo dirá «en preparación».

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
DIR_TEMAS = Path("fixtures") / "demo" / "temas"
DIR_LEGACY = Path("fixtures") / "demo"
SALIDA = Path("apps") / "web" / "demo" / "data.json"

MIN_SECCIONES = 3
MIN_PREGUNTAS = 10
LETRAS = frozenset("abcd")


def _cargar_temas(base: Path) -> dict[str, dict[str, Any]]:
    """Carga los ficheros de tema (nuevo directorio y los dos legacy) y los valida."""
    ficheros = sorted((base / DIR_TEMAS).glob("*.json")) if (base / DIR_TEMAS).is_dir() else []
    ficheros += sorted((base / DIR_LEGACY).glob("tema-*.json"))
    temas: dict[str, dict[str, Any]] = {}
    for fichero in ficheros:
        data = json.loads(fichero.read_text(encoding="utf-8"))
        path = str(data["node_path"])
        if path in temas:
            raise RuntimeError(f"hay dos ficheros para el tema {path}")
        sections = data.get("sections")
        questions = data.get("questions")
        if not isinstance(sections, list) or not isinstance(questions, list):
            raise RuntimeError(f"{fichero.name}: faltan `sections` o `questions`")
        for section in sections:
            if not isinstance(section, dict) or "heading" not in section:
                raise RuntimeError(f"{fichero.name}: sección sin `heading`")
            if "body" not in section and "table" not in section:
                raise RuntimeError(f"{fichero.name}: sección vacía ({section.get('heading')})")
        for pregunta in questions:
            if not isinstance(pregunta, dict):
                raise RuntimeError(f"{fichero.name}: pregunta mal formada")
            opciones = pregunta.get("options")
            if not isinstance(opciones, list) or len(opciones) != 4:
                raise RuntimeError(f"{fichero.name}: «{pregunta.get('stem')}» no tiene 4 opciones")
            if pregunta.get("correct") not in LETRAS:
                raise RuntimeError(f"{fichero.name}: «{pregunta.get('stem')}» sin letra correcta")
            if not str(pregunta.get("explanation") or "").strip():
                raise RuntimeError(f"{fichero.name}: «{pregunta.get('stem')}» sin explicación")
        data["source"] = data.get("source") or {"label": "Apuntes propios de la demo", "url": ""}
        temas[path] = data
    return temas


def _estado(sections: int, questions: int) -> str:
    if sections >= MIN_SECCIONES and questions >= MIN_PREGUNTAS:
        return "completo"
    if questions >= MIN_PREGUNTAS:
        return "con_preguntas"
    return "pendiente"


def _slug(path: str) -> str:
    return path.lower().replace(".", "-")


def build_static_demo(*, out: Path, root: Path | None = None) -> dict[str, int]:
    base = root or project_root()
    curriculum = json.loads((base / CURRICULUM_FIXTURE).read_text(encoding="utf-8"))
    temas = _cargar_temas(base)

    bloques = []
    total_temas = 0
    completos = 0
    con_preguntas = 0
    pendientes = 0
    for bloque in curriculum["nodes"]:
        if bloque.get("node_type") != "block":
            continue
        topics = []
        for tema in bloque.get("children", []):
            if tema.get("node_type") != "topic":
                continue
            total_temas += 1
            path = str(tema["path"])
            completo = temas.get(path)
            secciones = len(completo.get("sections", [])) if completo else 0
            preguntas = len(completo.get("questions", [])) if completo else 0
            estado = _estado(secciones, preguntas)
            if estado == "completo":
                completos += 1
            elif estado == "con_preguntas":
                con_preguntas += 1
            else:
                pendientes += 1
            topics.append(
                {
                    "path": path,
                    "title": tema["title"],
                    "status": estado,
                    "sectionCount": secciones,
                    "questionCount": preguntas,
                }
            )
        bloques.append({"path": bloque["path"], "title": bloque["title"], "topics": topics})

    if total_temas != 40:
        raise RuntimeError(f"el temario debería tener 40 temas, tiene {total_temas}")

    # Contenido completo por tema (solo los que tienen fichero) y prácticas.
    contenido: dict[str, Any] = {}
    practicas = []
    for path, tema in sorted(temas.items()):
        secciones = len(tema["sections"])
        preguntas = tema["questions"]
        estado = _estado(secciones, len(preguntas))
        contenido[path] = {
            "path": path,
            "title": tema["title"],
            "status": estado,
            "source": tema["source"],
            "sections": tema["sections"],
        }
        if len(preguntas) >= MIN_PREGUNTAS:
            slug = _slug(path)
            contenido[path]["practiceSlug"] = slug
            practicas.append(
                {
                    "slug": slug,
                    "tema_path": path,
                    "title": f"Práctica · {tema['title']}",
                    "questions": [
                        {
                            "stem": pregunta["stem"],
                            "options": [
                                {"key": chr(ord("a") + indice), "text": opcion}
                                for indice, opcion in enumerate(pregunta["options"])
                            ],
                            "correct": pregunta["correct"],
                            "explanation": pregunta["explanation"],
                        }
                        for pregunta in preguntas
                    ],
                }
            )

    total_preguntas = sum(len(practica["questions"]) for practica in practicas)
    # «Con preguntas» cuenta los temas que ya tienen práctica (los completos hoy); «pendiente» es no
    # tener contenido. Son dos lecturas distintas del progreso y la demo las explica juntas.
    temas_con_preguntas = sum(
        1 for tema in temas.values() if len(tema["questions"]) >= MIN_PREGUNTAS
    )
    data = {
        "title": "OpoFuente — demo estática",
        "warning": (
            "Demo estática: el contenido va empaquetado y tus respuestas se guardan solo en este "
            "navegador. No hay servidor, no se envía nada y no hay cuenta."
        ),
        "curriculum": {
            "code": curriculum["code"],
            "name": curriculum["name"],
            "blocks": bloques,
        },
        "topics": contenido,
        "practices": practicas,
        "progress": {
            "total": total_temas,
            "complete": completos,
            "withQuestions": temas_con_preguntas,
            "pending": pendientes,
            "questions": total_preguntas,
        },
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "blocks": len(bloques),
        "topics": total_temas,
        "complete": completos,
        "withQuestions": temas_con_preguntas,
        "pending": pendientes,
        "practices": len(practicas),
        "questions": total_preguntas,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=project_root() / SALIDA)
    args = parser.parse_args(list(argv) if argv is not None else None)
    counts = build_static_demo(out=args.out)
    print(json.dumps({"out": str(args.out), **counts}, ensure_ascii=False))
    if counts["blocks"] != 5 or counts["topics"] != 40:
        print("La demo estática no tiene el temario esperado.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
