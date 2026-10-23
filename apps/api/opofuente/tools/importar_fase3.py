"""Pasa a la base real lo generado de verdad en la copia (fase 3, §2.1.4).

**Que pasa, y que no:**

- **las 1.609 explicaciones generadas**, que siguen en borrador;
- **las 9 tarjetas**, que son propias del proyecto;
- **y nada de lo que crearon los recorridos**: sesiones, intentos, respuestas,
  planes de prueba ni avisos. Eso se queda en la copia.

**Y antes de escribir una fila comprueba que aquello a lo que apunta existe en
la real**: **una explicacion que apunte a una pregunta que no esta seria una
fila huerfana**, y el plan lo pide expresamente.

**Es idempotente**: **`insert or replace` por clave primaria**, asi que pasarlo
dos veces deja lo mismo.

**Y por defecto no escribe**: **`--aplicar` es obligatorio para que toque nada.**

**Las sentencias son literales y no se construyen**: la comprobacion va fila a
fila con consultas parametrizadas, **que sobre una clave primaria es lo mismo de
rapido y no hay una sola coma interpolada con datos en el fichero**.
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from opofuente.config import get_settings

#: Las dos tablas que viajan, **con su sentencia literal y sus columnas**.
EXPLICACIONES = (
    "select id, question_version_id, option_stable_key, text, origin, status, "
    "model_name, prompt_template_version, created_at, citation, note_anchor_id "
    "from question_explanations where origin = 'generated'"
)
TARJETAS = (
    "select id, topic_fact_id, front, back, citation, origin, status, ease, "
    "interval_days, repetitions, due_at, created_at, updated_at from cards"
)

#: Los dos `insert`, **literales**: `ruff` no admite una sentencia montada, y
#: tiene razon de fondo aunque aqui las columnas sean constantes.
INSERT_EXPLICACIONES = (
    "insert or replace into question_explanations "
    "(id, question_version_id, option_stable_key, text, origin, status, "
    "model_name, prompt_template_version, created_at, citation, note_anchor_id) "
    "values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
)
INSERT_TARJETAS = (
    "insert or replace into cards "
    "(id, topic_fact_id, front, back, citation, origin, status, ease, "
    "interval_days, repetitions, due_at, created_at, updated_at) "
    "values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
)


@dataclass(frozen=True, slots=True)
class Recuento:
    """Lo que se ha visto y lo que se puede pasar."""

    tabla: str
    filas: int
    huerfanas: int
    ya_estaban: int

    def linea(self) -> str:
        a_insertar = self.filas - self.huerfanas - self.ya_estaban
        return (
            f"{self.tabla}: {self.filas} en la copia · "
            f"{self.huerfanas} huerfanas · {self.ya_estaban} ya estaban · "
            f"{a_insertar} por pasar"
        )


def _cuenta(
    real: sqlite3.Connection,
    pregunta: str,
    filas: Sequence[tuple[object, ...]],
    indice: int,
) -> int:
    """Cuantas de esas filas cumplen la pregunta parametrizada.

    **Fila a fila y parametrizado**: sobre la clave primaria de
    `question_versions` o de `topic_facts` son mil seiscientas busquedas
    indexadas, **y a cambio no hay una sola sentencia construida**.
    """
    total = 0
    for fila in filas:
        valor = fila[indice]
        # **Un nulo no es una referencia rota**: una tarjeta sin hecho asociado
        # no apunta a nada, y eso no la invalida.
        if valor is None or real.execute(pregunta, (valor,)).fetchone():
            total += 1
    return total


def revisar(origen: Path, destino: Path) -> list[Recuento]:
    """Cuenta lo que se pasaria, **sin escribir nada**."""
    copia = sqlite3.connect(f"file:{origen}?mode=ro", uri=True)
    real = sqlite3.connect(f"file:{destino}?mode=ro", uri=True)
    try:
        explicaciones = copia.execute(EXPLICACIONES).fetchall()
        tarjetas = copia.execute(TARJETAS).fetchall()
        con_pregunta = _cuenta(
            real,
            "select 1 from question_versions where id = ?",
            explicaciones,
            1,
        )
        con_hecho = _cuenta(real, "select 1 from topic_facts where id = ?", tarjetas, 1)
        return [
            Recuento(
                tabla="question_explanations",
                filas=len(explicaciones),
                huerfanas=len(explicaciones) - con_pregunta,
                ya_estaban=_cuenta(
                    real,
                    "select 1 from question_explanations where id = ?",
                    explicaciones,
                    0,
                ),
            ),
            Recuento(
                tabla="cards",
                filas=len(tarjetas),
                huerfanas=len(tarjetas) - con_hecho,
                ya_estaban=_cuenta(real, "select 1 from cards where id = ?", tarjetas, 0),
            ),
        ]
    finally:
        copia.close()
        real.close()


def _validas(
    real: sqlite3.Connection,
    pregunta: str,
    filas: Sequence[tuple[object, ...]],
) -> list[tuple[object, ...]]:
    """Las filas cuya referencia existe en la real.

    **Las huerfanas se quedan fuera**: pasar una fila que apunta a algo que no
    existe es dejar basura en la base del propietario, **y despues nadie sabe de
    donde salio**.
    """
    salida = []
    for fila in filas:
        valor = fila[1]
        if valor is None or real.execute(pregunta, (valor,)).fetchone():
            salida.append(fila)
    return salida


def aplicar(origen: Path, destino: Path) -> list[Recuento]:
    """Pasa las filas **en una transaccion y comprobando cada referencia**."""
    recuentos = revisar(origen, destino)
    copia = sqlite3.connect(f"file:{origen}?mode=ro", uri=True)
    real = sqlite3.connect(destino)
    try:
        explicaciones = _validas(
            real,
            "select 1 from question_versions where id = ?",
            copia.execute(EXPLICACIONES).fetchall(),
        )
        real.executemany(INSERT_EXPLICACIONES, explicaciones)
        tarjetas = _validas(
            real,
            "select 1 from topic_facts where id = ?",
            copia.execute(TARJETAS).fetchall(),
        )
        real.executemany(INSERT_TARJETAS, tarjetas)
        real.commit()
    finally:
        copia.close()
        real.close()
    return recuentos


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--origen", required=True, type=Path)
    parser.add_argument("--aplicar", action="store_true", help="escribe; sin esto solo cuenta")
    args = parser.parse_args(argv)

    destino = get_settings().data_paths.database
    print(f"origen : {args.origen}")
    print(f"destino: {destino}")
    recuentos = aplicar(args.origen, destino) if args.aplicar else revisar(args.origen, destino)
    for recuento in recuentos:
        print(f"  {recuento.linea()}")
    if not args.aplicar:
        print("\nno se ha escrito nada: añade --aplicar para pasarlo")
    return 0


if __name__ == "__main__":
    sys.exit(main())
