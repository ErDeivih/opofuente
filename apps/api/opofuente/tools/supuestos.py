"""Genera supuestos practicos con el modelo y los guarda (M5).

**Que hace**: recorre los apartados de los bloques III y IV, **pide un
supuesto a cada uno**, lo comprueba con el segundo modelo, **y guarda los
que pasan el 90 %** hasta tener seis por bloque.

**Y una cosa que hay que decir porque no es obvia**: **las veinticinco
preguntas del supuesto se dan de alta como preguntas del banco antes de
guardar el supuesto**. **Un supuesto apunta a preguntas, no a texto**: si
el modelo escribe veinticinco preguntas y no se guardan como preguntas, el
supuesto queda sin nada a lo que apuntar. **Se crean en un conjunto propio,
`origin = generated`, para que no se confundan con el banco real.**

**El gasto se cuenta y se dice**: **el tope del hito son 6 $**, y la
herramienta se para si lo alcanza.
"""

from __future__ import annotations

import argparse
import os
import sys
import uuid
from collections.abc import Sequence
from datetime import UTC, datetime

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from opofuente.application.practical_case_service import PracticalCaseService
from opofuente.config import get_settings
from opofuente.domain.practical_case import SupuestoPropuesto
from opofuente.infrastructure.db_models import (
    OptionVersionRecord,
    QuestionSetRecord,
    QuestionVersionRecord,
)
from opofuente.infrastructure.practical_case_client import PracticalCaseClient
from opofuente.infrastructure.practical_case_repository import (
    SqlAlchemyPracticalCaseRepository,
)

#: Los bloques donde vive el supuesto.
BLOQUES = ("III", "IV")

#: El tope de gasto del hito, en dolares.
TOPE = 6.0

#: Lo que cuesta cada intento: dos llamadas de unas cuatrocientas palabras
#: a la cifra medida en M1 (0,000024 $ por pregunta).
COSTE_POR_INTENTO = 0.06


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--por-bloque", type=int, default=6, help="cuantos supuestos por bloque (6)"
    )
    parser.add_argument("--guardar", action="store_true", help="guarda los aceptados en la base")
    parser.add_argument(
        "--limite", type=int, default=40, help="cuantos apartados mirar por bloque (40)"
    )
    return parser


def _fabrica() -> tuple[object, sessionmaker[Session]]:
    motor = create_engine(f"sqlite+pysqlite:///{get_settings().data_paths.database}")
    return motor, sessionmaker(bind=motor)


def _oposicion(fabrica: sessionmaker[Session]) -> str:
    """La oposicion de TAI, **por su codigo y no por ser la primera**.

    **Un supuesto de TAI tiene que colgar de TAI**: **elegir «la primera»
    funcionaria hoy con tres filas y apuntaria al examen equivocado el dia que
    haya cuatro.**
    """
    with fabrica() as session:
        fila = session.execute(
            text(
                "select id from oppositions where code like '%tai%' "
                "or name like '%Tecnicos Auxiliares%' limit 1"
            )
        ).first()
    if fila is None:
        raise SystemExit("no hay oposicion de TAI en esta base")
    return str(fila[0])


def _apartados(limite: int, fabrica: sessionmaker[Session]) -> dict[str, list[tuple[str, str]]]:
    """Los apartados de cada bloque, **por su codigo y con su texto**.

    **Un apartado es un tema con notas**: los que no las tienen no sirven
    para escribir un caso sobre ellos.
    """
    salida: dict[str, list[tuple[str, str]]] = {bloque: [] for bloque in BLOQUES}
    with fabrica() as session:
        for fila in session.execute(
            text(
                """
                -- **Se filtra por `path` y no por `official_code`**: en la base real el
                -- `official_code` de un tema es su numero («1», «2») y la ruta es la que
                -- dice el bloque («III.1»). **Filtrando por el codigo oficial salian CERO
                -- apartados y el generador decia que no habia material**, cuando habia
                -- dieciseis temas con notas.
                -- **Y se juntan las secciones del tema**: un tema con notas tiene varias,
                -- y el modelo necesita el texto entero para escribir el caso.
                select n.path, group_concat(s.body_markdown, char(10) || char(10))
                from curriculum_nodes n
                join topic_note_sections s on s.curriculum_node_id = n.id
                where n.path like 'III%' or n.path like 'IV%'
                group by n.path
                order by n.path
                """
            )
        ):
            codigo = str(fila[0])
            bloque = "III" if codigo.startswith("III") else "IV"
            if len(salida[bloque]) < limite:
                salida[bloque].append((codigo, str(fila[1])))
    return salida


def _dar_de_alta(
    *,
    fabrica: sessionmaker[Session],
    supuesto: SupuestoPropuesto,
    case_id: str,
    opposition_id: str,
    aciertos: int = 0,
) -> tuple[str, ...]:
    """Crea las preguntas del supuesto en el banco y devuelve sus ids.

    **Se crean en un conjunto propio** —`origin = generated`— **para que no
    se confundan con el banco real**: un supuesto generado no es material
    del propietario.
    """
    ahora = datetime.now(UTC)
    ids: list[str] = []
    with fabrica() as session:
        conjunto_id = str(uuid.uuid4())
        session.add(
            # **Los cinco valores no son relleno: son la ficha del conjunto.**
            # Un supuesto generado es `generated_batch`, `draft` —nadie lo ha
            # revisado—, `personal` —no se publica por existir—, `age` —es de esta
            # administracion—, **y su fiabilidad es la que acaba de medir el
            # segundo modelo**: si coincidio en todo, `fiable`.
            QuestionSetRecord(
                id=conjunto_id,
                title=f"Supuesto {supuesto.block} generado {case_id[:8]}",
                set_type="generated_batch",
                status="draft",
                distribution="personal",
                origin_scope="age",
                opposition_id=opposition_id,
                key_reliability="fiable" if aciertos >= 25 else "dudosa",
                created_at=ahora,
                updated_at=ahora,
            )
        )
        for posicion, pregunta in enumerate(supuesto.preguntas, start=1):
            version_id = str(uuid.uuid4())
            session.add(
                QuestionVersionRecord(
                    id=version_id,
                    question_set_id=conjunto_id,
                    stable_key=f"supuesto-{case_id[:8]}-{posicion:02d}",
                    version_no=1,
                    stem=pregunta.enunciado,
                    question_type="single_choice",
                    position=posicion,
                    is_reserve=posicion > 20,
                    status="complete",
                    origin_type="generated",
                    created_at=ahora,
                )
            )
            for orden, (letra, texto) in enumerate(pregunta.opciones, start=1):
                session.add(
                    # **`position` es obligatoria** y no es la letra: es el orden
                    # en que las opciones se enseñan, y sin ella la base rechaza
                    # la fila (lo dijo: `NOT NULL constraint failed`).
                    OptionVersionRecord(
                        id=str(uuid.uuid4()),
                        question_version_id=version_id,
                        stable_key=letra,
                        text=texto,
                        position=orden,
                    )
                )
            ids.append(version_id)
        session.commit()
    return tuple(ids)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    clave = os.environ.get("DEEPSEEK_API_KEY", "").strip()
    if not clave:
        print("sin DEEPSEEK_API_KEY no hay supuestos: se para sin gastar")
        return 2

    servicio = PracticalCaseService(PracticalCaseClient(api_key=clave))
    _motor, fabrica = _fabrica()
    repositorio = SqlAlchemyPracticalCaseRepository(fabrica)

    oposicion = _oposicion(fabrica)
    apartados = _apartados(args.limite, fabrica)
    gastado = 0.0
    for bloque in BLOQUES:
        aceptados = 0
        print(f"--- bloque {bloque}: {len(apartados[bloque])} apartados con notas")
        for codigo, cuerpo in apartados[bloque]:
            if aceptados >= args.por_bloque:
                break
            if gastado + COSTE_POR_INTENTO > TOPE:
                print(f"  tope de {TOPE} $ alcanzado: se para")
                return 3
            gastado += COSTE_POR_INTENTO
            intento = servicio.intentar(block=bloque, apartado=cuerpo)
            if not intento.aceptado:
                motivo = (
                    intento.veredicto.problemas[0] if intento.veredicto.problemas else "sin motivo"
                )
                print(f"  {codigo}: descartado · {motivo[:70]}")
                continue
            print(f"  {codigo}: ACEPTADO · {intento.aciertos}/25 coinciden")
            if args.guardar and intento.supuesto is not None:
                case_id = str(uuid.uuid4())
                ids = _dar_de_alta(
                    fabrica=fabrica,
                    supuesto=intento.supuesto,
                    case_id=case_id,
                    opposition_id=oposicion,
                )
                guardado = repositorio.guardar(
                    case_id=case_id,
                    supuesto=intento.supuesto,
                    origin="generated",
                    pregunta_ids=ids,
                )
                print(f"    guardado: {guardado is not None} · {len(ids)} preguntas")
            aceptados += 1

    print(f"\ngastado: {gastado:.2f} $ de {TOPE} $")
    for bloque in BLOQUES:
        print(f"  bloque {bloque}: {repositorio.contar(block=bloque)} guardados")
    return 0


if __name__ == "__main__":
    sys.exit(main())
