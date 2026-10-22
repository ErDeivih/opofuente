"""Que hay en la bandeja del propietario, y que de eso es automatizable (M7).

**Que hace**: cuenta lo que espera una decision y **lo parte en dos**:

- **lo automatizable**: **incidencias que no piden un criterio** —una pregunta sin
  clave, un apartado sin la frase que lo sostiene—, **que se pueden proponer en
  bloque**;
- **lo que pide una decision**: **contradicciones entre los apuntes y la clave**,
  **que piden leer dos textos y decidir cual vale**.

**Por que existe**: **el punto 3 de M7 pide «bandeja por debajo de 100 decisiones
reales, con todo lo automatizable propuesto en bloque»**, **y hoy las dos cosas se
cuentan juntas**: **2.529 en un solo numero no dice si el trabajo es de una tarde o
de un mes**.

**No escribe nada y no llama a nadie.** **Solo cuenta y separa.**
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from dataclasses import dataclass

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from opofuente.config import get_settings

#: Los motivos que **no piden criterio**: se pueden proponer en bloque y que una
#: persona los apruebe de una vez.
AUTOMATIZABLES = ("sin_frase_en_los_apuntes", "clave_sin_definir")


@dataclass(frozen=True, slots=True)
class Reparto:
    """La bandeja, partida en lo que se puede proponer y lo que hay que decidir."""

    explicaciones: int
    automatizables: int
    decisiones: int

    @property
    def total(self) -> int:
        return self.explicaciones + self.automatizables + self.decisiones

    def lines(self) -> tuple[str, ...]:
        return (
            f"explicaciones en borrador  {self.explicaciones:>6}   (se aprueban en bloque)",
            f"incidencias automatizables  {self.automatizables:>6}   (sin frase, sin clave)",
            f"decisiones de verdad        {self.decisiones:>6}   (apuntes contra clave)",
            f"                            {'-' * 6}",
            f"total                       {self.total:>6}",
            "",
            # **Y la frase que importa**: el hito pone un tope de 100 y lo que hay
            # es otra cosa; decir «no se cumple» sin decir cuanto falta no sirve.
            f"el hito pide menos de 100 decisiones reales; hay {self.decisiones}",
        )


def repartir() -> Reparto:
    """Cuenta y separa, **leyendo lo que hay**."""
    motor = create_engine(f"sqlite+pysqlite:///{get_settings().data_paths.database}")
    fabrica = sessionmaker(bind=motor)
    with fabrica() as session:
        explicaciones = int(
            session.execute(
                text(
                    "select count(*) from question_explanations "
                    "where origin = 'generated' and status = 'draft'"
                )
            ).scalar_one()
        )
        # **Un solo recorrido con un `in`**: dos consultas seguidas para lo mismo
        # es como se acaba contando dos veces la que se solapa.
        automatizables = int(
            session.execute(
                text(
                    "select count(*) from notes_incidents "
                    "where status = 'open' and reason in :motivos"
                ).bindparams(motivos=AUTOMATIZABLES)
                if False
                else text(
                    "select count(*) from notes_incidents "
                    "where status = 'open' "
                    "and reason in ('sin_frase_en_los_apuntes', 'clave_sin_definir')"
                )
            ).scalar_one()
        )
        abiertas = int(
            session.execute(
                text("select count(*) from notes_incidents where status = 'open'")
            ).scalar_one()
        )
    return Reparto(
        explicaciones=explicaciones,
        automatizables=automatizables,
        decisiones=abiertas - automatizables,
    )


def main(argv: Sequence[str] | None = None) -> int:
    argparse.ArgumentParser(description=__doc__).parse_args(argv)
    for linea in repartir().lines():
        print(linea)
    return 0


if __name__ == "__main__":
    sys.exit(main())
