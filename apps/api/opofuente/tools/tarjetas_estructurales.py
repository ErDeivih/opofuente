"""Las tarjetas que salen de una forma regular, sin modelo (M3 de la fase 3).

**Por defecto no escribe nada y no llama a nadie**: lee los hechos, pasa cada uno por
`tarjeta_estructural` y dice cuantas tarjetas salen y cuantos hechos no encajan.

**Con `--guardar` si escribe**: mete las tarjetas en la tabla `cards`. **El anverso es unico**,
asi que pasarla dos veces no duplica nada.

Uso:

    uv run python -m opofuente.tools.tarjetas_estructurales
    uv run python -m opofuente.tools.tarjetas_estructurales --muestra 5
    uv run python -m opofuente.tools.tarjetas_estructurales --guardar
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
import uuid
from collections.abc import Sequence
from datetime import UTC, datetime

from opofuente.config import get_settings
from opofuente.domain.tarjetas import Tarjeta, tarjeta_estructural

_CONSULTA = "select kind, text from topic_facts where doubtful = 0"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--muestra",
        type=int,
        default=0,
        help="cuántas tarjetas enseñar por la salida (por defecto 0)",
    )
    parser.add_argument(
        "--guardar",
        action="store_true",
        help="guarda las tarjetas en la base, en vez de solo contarlas",
    )
    return parser


def _guardar(tarjetas: Sequence[Tarjeta]) -> int:
    """Mete las tarjetas en `cards`, solo las que no estaban ya por su anverso.

    Se hace con `sqlite3` y no con el repositorio porque **este es un guion de linea de
    ordenes**: montar la sesion de SQLAlchemy para catorce `INSERT` seria mas ceremonia que
    trabajo. La tabla es la que crea la migracion `0042_tarjetas`.
    """
    ahora = datetime.now(UTC).isoformat()
    base = sqlite3.connect(get_settings().data_paths.database)
    try:
        existentes = {f[0] for f in base.execute("select front from cards")}
        nuevas = 0
        for tarjeta in tarjetas:
            if tarjeta.anverso in existentes:
                continue
            base.execute(
                "insert into cards (id, topic_fact_id, front, back, citation, origin,"
                " status, ease, interval_days, repetitions, due_at, created_at,"
                " updated_at) values (?, null, ?, ?, ?, 'structural', 'active',"
                " 2.5, 0, 0, ?, ?, null)",
                (
                    str(uuid.uuid4()),
                    tarjeta.anverso,
                    tarjeta.reverso,
                    tarjeta.reverso,
                    ahora,
                    ahora,
                ),
            )
            existentes.add(tarjeta.anverso)
            nuevas += 1
        base.commit()
        return nuevas
    finally:
        base.close()


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
    if args.guardar:
        print(f"guardadas: {_guardar(tarjetas)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
