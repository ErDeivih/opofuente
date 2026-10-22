"""`opofuente notes verify` — la comprobacion semanal de los apuntes (M7).

**Que hace**: recorre los temas que ya tienen apuntes, **les pasa la misma
revision de forma que se les pasa al escribirlos**, y **avisa de los que han
dejado de pasar el liston**. **No escribe nada y no llama al modelo.**

**Por que existe, y no basta con revisarlos al escribirlos**: **un tema que
paso el liston hace tres meses puede no pasarlo hoy**, **porque el liston
depende de los hechos, y los hechos cambian cuando cambia la clave o la
norma**. **Sin esta comprobacion nadie se entera hasta que un alumno se
queja**, **y eso es exactamente lo que el hito llama «calidad continua».**

**La salida, y su codigo**: **`0` si todos pasan**, **`1` si alguno ha
bajado**, **`2` si no hay nada que revisar**. **Un comando que se ejecuta
desde una tarea programada tiene que poder distinguir «todo bien» de «nada
mirado»**: **lo segundo no es lo primero.**

**`--all` revisa todos los temas con apuntes**; **sin `--all`, solo los que
tienen material publicado**, **que son los que un alumno puede estar
leyendo ahora mismo.**
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from opofuente.config import get_settings
from opofuente.domain.notes_quality import revisar_apuntes
from opofuente.infrastructure.topic_notes_repository import (
    SqlAlchemyTopicNotesRepository,
)

#: La consulta de los temas a revisar, **sin una sola coma interpolada**.
#: `:todos` y `:tope` van como parametros: **un `--limite` metido en el SQL
#: con un f-string es una inyeccion esperando un numero raro**, y aunque hoy
#: solo lo llame una persona, la costumbre es la que se copia despues.
TEMAS = """
    select n.id, n.official_code
    from curriculum_nodes n
    where exists (
        select 1 from topic_note_sections s
        where s.curriculum_node_id = n.id
    )
      and (
        :todos = 1
        or exists (
            select 1
            from question_note_anchors a
            join question_versions v on v.id = a.question_version_id
            join question_sets cs on cs.id = v.question_set_id
            where a.curriculum_node_id = n.id
              and cs.distribution = 'public'
        )
      )
    order by n.official_code
    limit :tope
"""


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="comando", required=True)
    verificar = sub.add_parser(
        "verify",
        help="revisa los apuntes y avisa de los que han bajado del liston",
    )
    verificar.add_argument(
        "--all",
        action="store_true",
        help="todos los temas con apuntes, no solo los que tienen material publicado",
    )
    verificar.add_argument("--limite", type=int, default=0, help="como mucho N temas (0 = todos)")
    return parser


def _temas(*, todos: bool, limite: int) -> list[tuple[str, str]]:
    """Los temas que hay que revisar, **por su id y su codigo**.

    **Con `--all`, todos los que tienen algun apartado escrito.** **Sin
    `--all`, solo los que tienen material publicado**: **revisar un tema que
    nadie puede leer es trabajo que no cambia nada.**
    """
    motor = create_engine(f"sqlite+pysqlite:///{get_settings().data_paths.database}")
    fabrica = sessionmaker(bind=motor)
    with fabrica() as session:
        filas = session.execute(
            text(TEMAS),
            {"todos": 1 if todos else 0, "tope": limite if limite > 0 else -1},
        ).all()
    return [(str(fila[0]), str(fila[1])) for fila in filas]


def verificar(*, todos: bool, limite: int) -> int:
    """La revision, tema a tema, y el veredicto global."""
    motor = create_engine(f"sqlite+pysqlite:///{get_settings().data_paths.database}")
    notas = SqlAlchemyTopicNotesRepository(sessionmaker(bind=motor))
    temas = _temas(todos=todos, limite=limite)
    if not temas:
        print("no hay temas que revisar")
        return 2

    bajados: list[tuple[str, tuple[str, ...]]] = []
    for node_id, codigo in temas:
        revision = revisar_apuntes(notas.sections(node_id), notas.facts(node_id))
        if revision.pasa:
            print(f"  {codigo}: pasa · {revision.palabras} palabras")
            continue
        bajados.append((codigo, revision.lines()))

    if not bajados:
        print(f"\n{len(temas)} tema(s) revisado(s) · todos pasan el liston")
        return 0

    print(f"\n{len(bajados)} de {len(temas)} han bajado del liston:")
    for codigo, lineas in bajados:
        print(f"  {codigo}:")
        for linea in lineas:
            print(f"    {linea.strip()}")
    return 1


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.comando == "verify":
        return verificar(todos=bool(args.all), limite=int(args.limite))
    return 2


if __name__ == "__main__":
    sys.exit(main())
