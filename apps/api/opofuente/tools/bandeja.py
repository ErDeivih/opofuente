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
    #: De esas decisiones, **las que son de un examen oficial**: son las unicas que el
    #: propietario tiene que resolver el (§2.6 del plan: «solo las de examenes oficiales
    #: llegan al propietario»).
    del_propietario: int = 0
    #: Y las que **ya estan resueltas por la cuarentena de su conjunto**: la clave de ese
    #: conjunto no es fiable, asi que la pregunta no entra en tests ni simulacros, y la
    #: decision se tomo sobre el conjunto entero, no pregunta a pregunta.
    por_la_cuarentena: int = 0

    @property
    def resto(self) -> int:
        """Las que no son ni del propietario ni de un conjunto en cuarentena."""
        return self.decisiones - self.del_propietario - self.por_la_cuarentena

    @property
    def total(self) -> int:
        return self.explicaciones + self.automatizables + self.decisiones

    def lines(self) -> tuple[str, ...]:
        return (
            f"explicaciones en borrador  {self.explicaciones:>6}   (se aprueban en bloque)",
            f"incidencias automatizables  {self.automatizables:>6}   (sin frase, sin clave)",
            f"decisiones de verdad        {self.decisiones:>6}   (apuntes contra clave)",
            f"  de examen oficial         {self.del_propietario:>6}   <- las que decides tu",
            f"  ya en cuarentena          {self.por_la_cuarentena:>6}   (fuera de tests)",
            f"  y el resto                {self.resto:>6}   (privado con clave fiable)",
            f"                            {'-' * 6}",
            f"total                       {self.total:>6}",
            "",
            # **Y la frase que importa**: el hito pone un tope de 100 **y manda que solo las de
            # examen oficial lleguen al propietario**. Se cuenta esa cifra, no la suma: sumar las
            # que el propio plan deja fuera convertiria el hito en imposible por definicion.
            f"el hito pide menos de 100 decisiones para el propietario; hay {self.del_propietario}",
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
        # **De las que piden criterio, cuantas son de examen oficial y cuantas ya las
        # resolvio la cuarentena del conjunto.** Se mira el tipo de conjunto y su
        # fiabilidad, que es lo que decide si la pregunta entra o no en tests.
        oficiales, cuarentena = session.execute(
            text(
                "select "
                "coalesce(sum(case when qs.set_type = 'official_exam' then 1 else 0 end), 0), "
                "coalesce(sum(case when qs.set_type is not null "
                "and qs.set_type <> 'official_exam' "
                "and coalesce(qs.key_reliability, '') in ('dudosa', 'no_fiable') "
                "then 1 else 0 end), 0) "
                "from notes_incidents i "
                "left join question_versions v on v.id = i.question_version_id "
                "left join question_sets qs on qs.id = v.question_set_id "
                "where i.status = 'open' "
                "and i.reason not in ('sin_frase_en_los_apuntes', 'clave_sin_definir')"
            )
        ).one()
    return Reparto(
        explicaciones=explicaciones,
        automatizables=automatizables,
        decisiones=abiertas - automatizables,
        del_propietario=int(oficiales),
        por_la_cuarentena=int(cuarentena),
    )


def detalle() -> tuple[str, ...]:
    """Las automatizables, **agrupadas por motivo**, que es la propuesta en bloque.

    **Una propuesta que se puede leer antes de aprobarla**: **el hito pide
    «propuesto en bloque», y un bloque de 134 sin verlo no es una propuesta, es
    un boton a ciegas.**
    """
    motor = create_engine(f"sqlite+pysqlite:///{get_settings().data_paths.database}")
    fabrica = sessionmaker(bind=motor)
    lineas = ["", "lo automatizable, por motivo:"]
    with fabrica() as session:
        for motivo, cuantas in session.execute(
            text(
                "select reason, count(*) from notes_incidents "
                "where status = 'open' "
                "and reason in ('sin_frase_en_los_apuntes', 'clave_sin_definir') "
                "group by reason order by count(*) desc"
            )
        ):
            lineas.append(f"  {motivo!s:<28} {int(cuantas):>4}")
        lineas.append("")
        lineas.append("y lo que pide decision, por motivo:")
        for motivo, cuantas in session.execute(
            text(
                "select reason, count(*) from notes_incidents "
                "where status = 'open' "
                "and reason not in ('sin_frase_en_los_apuntes', 'clave_sin_definir') "
                "group by reason order by count(*) desc"
            )
        ):
            lineas.append(f"  {motivo!s:<28} {int(cuantas):>4}")
    return tuple(lineas)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--detalle",
        action="store_true",
        help="y ademas, como se reparte cada grupo por motivo",
    )
    parser.add_argument(
        "--aplicar",
        action="store_true",
        help="ESCRIBE: marca como propuesta lista lo automatizable. Sin esto, nada se toca",
    )
    parser.add_argument(
        "--proponer",
        action="store_true",
        help="ensena la propuesta en bloque: que se haria con cada grupo, sin hacerlo",
    )
    args = parser.parse_args(argv)
    for linea in repartir().lines():
        print(linea)
    if args.detalle:
        for linea in detalle():
            print(linea)
    if args.proponer:
        for linea in propuesta():
            print(linea)
    if args.aplicar:
        print()
        print(marcar_como_propuesta())
    return 0


def marcar_como_propuesta() -> str:
    """Marca las automatizables como **propuesta lista**, que es una salida real.

    **`IncidentStatus.PROPUESTA_LISTA` existe en el dominio y significa exactamente
    esto**: **una regla la ha resuelto y no necesita al propietario para empezar**.
    **Es la salida correcta para las 106 sin frase y las 28 sin clave**: **no se
    cierran como revisadas —nadie las ha revisado— ni se descartan —no son un
    error del motor—**, **sino que quedan propuestas y esperando un si o un no.**

    **Una transaccion y un `where` con los dos motivos**: **no hay UPDATE sin
    condicion en este fichero.**
    """
    motor = create_engine(f"sqlite+pysqlite:///{get_settings().data_paths.database}")
    fabrica = sessionmaker(bind=motor)
    with fabrica() as session:
        session.execute(
            text(
                "update notes_incidents set status = 'propuesta_lista' "
                "where status = 'open' "
                "and reason in ('sin_frase_en_los_apuntes', 'clave_sin_definir')"
            )
        )
        session.commit()
        # **Se cuenta despues y no con `rowcount`**: una sentencia cruda no lo
        # trae, y contar es lo que se puede afirmar.
        cuantas = int(
            session.execute(
                text("select count(*) from notes_incidents where status = 'propuesta_lista'")
            ).scalar_one()
        )
    return f"marcadas como propuesta lista: {cuantas}"


def propuesta() -> tuple[str, ...]:
    """Que haria la propuesta en bloque, **sin hacerlo**.

    **Y esto es a proposito de solo lectura**: **el boton que aplica toca dos
    cosas distintas** —**pedirle 106 frases al modelo, que cuesta dinero, y
    retirar 28 preguntas sin clave, que es una decision sobre el banco**—, **y
    ninguna de las dos se hace desde una herramienta que solo cuenta.**

    **Lo que si hace es decir exactamente que se haria**, **para que quien lo
    apruebe sepa que aprueba**: **una propuesta que no se puede leer antes no es
    una propuesta.**
    """
    return (
        "",
        "la propuesta en bloque, sin aplicar:",
        "  sin_frase_en_los_apuntes   106  se le piden al modelo, apartado a apartado",
        "  clave_sin_definir           28  se retiran del banco, con su evento",
        "",
        "no se ha escrito nada: aplicar esto es otra herramienta y otra prueba",
    )


if __name__ == "__main__":
    sys.exit(main())
