"""El generador de explicaciones, en seco: dice qué haría sin gastar (M1 de la fase 3).

**Por defecto no llama a nadie y no escribe nada**: recorre el camino entero —las preguntas con
ancla y clave servible, el texto de su apartado, los lotes y las cuatro comprobaciones— con el
doble, **a coste cero**, y dice qué habría pasado. Con `--de-verdad` llama al modelo y gasta.

La clave se lee de `DEEPSEEK_API_KEY` y no se escribe en ningún fichero.
"""

from __future__ import annotations

import argparse
import os
import sqlite3
import sys
from collections.abc import Sequence

from opofuente.application.explicaciones import PreguntaAExplicar, validar_lote
from opofuente.config import get_settings
from opofuente.infrastructure.explanation_client import DeepSeekExplanationProposer
from opofuente_testing.explanation_proposer import FakeExplanationProposer

#: Las preguntas que se pueden explicar: con apartado publicado y clave servible.
_CONSULTA = (
    "select a.question_version_id, v.stem, a.expected_letters, s.body_markdown, a.section_id "
    "from question_note_anchors a "
    "join question_versions v on v.id = a.question_version_id "
    "join topic_note_sections s on s.id = a.section_id "
    "where a.result = 'covered' and a.expected_letters is not null "
    "and length(a.expected_letters) > 0 and length(trim(s.body_markdown)) > 0 "
    "limit ?"
)


def _preguntas(limite: int) -> tuple[PreguntaAExplicar, ...]:
    """Las N primeras preguntas que se pueden explicar, con su ancla y su apartado."""
    base = sqlite3.connect(get_settings().data_paths.database)
    try:
        filas = base.execute(_CONSULTA, (limite,)).fetchall()
        preguntas: list[PreguntaAExplicar] = []
        for qid, stem, letras, cuerpo, seccion in filas:
            opciones = tuple(
                (str(clave), str(texto))
                for clave, texto in base.execute(
                    "select stable_key, text from option_versions where question_version_id = ?",
                    (qid,),
                )
            )
            preguntas.append(
                PreguntaAExplicar(
                    question_version_id=str(qid),
                    enunciado=str(stem),
                    opciones=opciones,
                    clave=tuple(x.strip().lower() for x in str(letras).split(",") if x.strip()),
                    apartado=str(cuerpo),
                    note_anchor_id=str(seccion),
                )
            )
        return tuple(preguntas)
    finally:
        base.close()


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limite", type=int, default=20, help="cuántas preguntas, por defecto 20")
    parser.add_argument(
        "--de-verdad",
        action="store_true",
        help="llama al modelo de verdad (gasta); sin esto usa el doble y no gasta nada",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.de_verdad:
        clave = os.environ.get("DEEPSEEK_API_KEY", "").strip()
        if not clave:
            print("sin DEEPSEEK_API_KEY no hay llamada: se para sin gastar")
            return 2
        proposer: object = DeepSeekExplanationProposer(api_key=clave)
    else:
        proposer = FakeExplanationProposer()
    preguntas = _preguntas(args.limite)
    print(f"preguntas con ancla y clave: {len(preguntas)}")
    salida = validar_lote(preguntas, proposer)  # type: ignore[arg-type]
    print(f"aceptadas: {len(salida.aceptadas)}")
    print(f"rechazadas: {len(salida.rechazadas)}")
    print(f"sin material: {len(salida.sin_material)}")
    if args.de_verdad:
        entrada, salida_tokens = proposer.ultimos_tokens  # type: ignore[attr-defined]
        print(f"tokens: entrada {entrada} · salida {salida_tokens}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
