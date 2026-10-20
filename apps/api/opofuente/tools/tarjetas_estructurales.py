"""Las tarjetas que salen de una forma regular, sin modelo (M3 de la fase 3).

**No escribe nada y no llama a nadie**: lee los hechos de la copia, pasa cada uno por
`tarjeta_estructural` y dice **cuántas tarjetas salen y cuántos hechos no encajan**. La cifra es
el dato que el hito pide, y sirve para decidir si la vía sin modelo basta.

Uso:

    uv run python -m opofuente.tools.tarjetas_estructurales
    uv run python -m opofuente.tools.tarjetas_estructurales --muestra 5
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
from collections.abc import Sequence

from opofuente.config import get_settings
from opofuente.domain.tarjetas import tarjeta_estructural

_CONSULTA = "select kind, text from topic_facts where doubtful = 0"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--muestra",
        type=int,
        default=0,
        help="cuántas tarjetas enseñar por la salida (por defecto 0)",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    base = sqlite3.connect(get_settings().data_paths.database)
    try:
        hechos = base.execute(_CONSULTA).fetchall()
    finally:
        base.close()
    tarjetas = [t for t in (tarjeta_estructural(texto) for _, texto in hechos) if t is not None]
    print(f"hechos no dudosos: {len(hechos)}")
    print(f"tarjetas por plantilla: {len(tarjetas)}")
    fuera = len(hechos) - len(tarjetas)
    print(f"sin plantilla (a la bandeja): {fuera}")
    if tarjetas:
        porcentaje = 100 * len(tarjetas) / len(hechos)
        print(f"proporcion: {porcentaje:.1f} %")
    for tarjeta in tarjetas[: args.muestra]:
        print(f"  · {tarjeta.anverso} -> {tarjeta.reverso}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
