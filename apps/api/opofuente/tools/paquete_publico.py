"""El paquete de contenido publico: exportarlo y volver a meterlo (M8).

**Que es**: un unico fichero JSON con el material que se puede repartir â€”los
conjuntos `distribution = public`, sus preguntas, sus claves, los apuntes,
las explicaciones generadas y las tarjetasâ€” **con sus identificadores tal
cual**, para que al importarlo en otra instalacion quede lo mismo.

**Y de donde sale la lista de lo que viaja**: **una lista blanca escrita a
mano, tabla por tabla, con su sentencia**. **No es una lista negra** â€”Â«todo
menos estasÂ»â€” **porque una tabla nueva entraria sola**: **si manana aparece
una tabla con datos de una persona, una lista negra se la lleva y una blanca
no**.

**Lo que NUNCA viaja, y por eso no esta en la lista**: **usuarios, sesiones,
intentos, resultados, avisos, incidencias, planes de estudio y todo lo que es
de una persona concreta.** **Y de las explicaciones, solo las `generated`**:
**las `private` son del propietario y no se reparten.**

**La importacion es idempotente**: **`insert ... or replace` por clave
primaria**, **asi que importar dos veces el mismo paquete deja la base igual
que importarlo una**.

**Y las sentencias son constantes, una por tabla, sin construir nada**: **el
paquete es un fichero que puede venir de cualquier sitio, y el importador no
monta una sola sentencia con lo que trae.** **Lo unico que se lee del paquete
son los nombres de tabla y columna, y los dos se comprueban contra la base
antes de usarlos.**
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import Date, DateTime, MetaData, Table, create_engine, event, text
from sqlalchemy.orm import Session, sessionmaker

from opofuente.config import get_settings

#: La version del formato. **Un importador viejo tiene que poder decir Â«esto no
#: lo se leerÂ»** en vez de meter medio paquete.
FORMATO = 1

#: **La lista blanca**: la tabla y la sentencia que saca sus filas.
#: **Cada sentencia es un literal completo**, partido en trozos contiguos solo
#: para que quepa en la linea. **No hay ni un `+` ni un f-string**.
VIAJAN: tuple[tuple[str, str], ...] = (
    ("oppositions", "select * from oppositions"),
    ("curriculum_nodes", "select * from curriculum_nodes"),
    (
        "question_sets",
        "select * from question_sets where distribution = 'public'",
    ),
    (
        "question_versions",
        "select * from question_versions where question_set_id in "
        "(select id from question_sets where distribution = 'public')",
    ),
    (
        "option_versions",
        "select * from option_versions where question_version_id in "
        "(select id from question_versions where question_set_id in "
        "(select id from question_sets where distribution = 'public'))",
    ),
    (
        "answer_key_entries",
        "select * from answer_key_entries where question_version_id in "
        "(select id from question_versions where question_set_id in "
        "(select id from question_sets where distribution = 'public'))",
    ),
    (
        "question_note_anchors",
        "select * from question_note_anchors where question_version_id in "
        "(select id from question_versions where question_set_id in "
        "(select id from question_sets where distribution = 'public'))",
    ),
    (
        "question_explanations",
        "select * from question_explanations where origin <> 'private'",
    ),
    ("topic_note_sections", "select * from topic_note_sections"),
    ("topic_facts", "select * from topic_facts"),
    ("cards", "select * from cards"),
    ("exam_rules", "select * from exam_rules"),
    ("exam_parts", "select * from exam_parts"),
)

#: Lo que **no puede aparecer** en un paquete, y se comprueba.
PROHIBIDAS: tuple[str, ...] = (
    "users",
    "study_sessions",
    "session_questions",
    "attempts",
    "attempt_evaluations",
    "notes_reports",
    "notes_incidents",
    "study_plans",
    "question_issue_reports",
    "password_resets",
    "login_throttles",
)


@dataclass
class Paquete:
    """Lo que se escribe en el fichero."""

    formato: int = FORMATO
    creado: str = ""
    tablas: dict[str, list[dict[str, Any]]] = field(default_factory=dict)

    def resumen(self) -> str:
        filas = sum(len(v) for v in self.tablas.values())
        detalle = " Â· ".join(f"{k} {len(v)}" for k, v in self.tablas.items() if v)
        return f"{len(self.tablas)} tabla(s) Â· {filas} fila(s)\n    {detalle}"


def _fabrica() -> sessionmaker[Session]:
    """El motor, **con tiempo de espera**: una base ocupada un segundo no es un
    error, es una base ocupada un segundo.

    **Sin `timeout`, SQLite se rinde al instante y contesta lo primero que
    puede** â€”que puede ser Â«no existe la tablaÂ», que es mentiraâ€”. **Con
    treinta segundos, espera, y si sigue ocupada lo dice de verdad.**
    """
    motor = create_engine(
        f"sqlite+pysqlite:///{get_settings().data_paths.database}",
        connect_args={"timeout": 30},
    )

    # **WAL, y no es un detalle (M8)**: en el modo por defecto, **leer bloquea a
    # escribir**. El instalador revisa el paquete â€”solo leeâ€” y luego lo importa
    # â€”escribeâ€”, **y con el diario clasico el segundo se queda esperando al
    # primero hasta rendirse con `database is locked`**. Con WAL, leer no
    # bloquea a escribir, **y el mismo instalador pasa**.
    @event.listens_for(motor, "connect")
    def _wal(conexion: Any, _registro: Any) -> None:
        conexion.execute("PRAGMA journal_mode=WAL")

    return sessionmaker(bind=motor)


def _columnas(session: Session, tabla: str) -> list[str]:
    """Las columnas de una tabla, **preguntandoselas a la base**."""
    filas = session.execute(text(f"pragma table_info({tabla})")).all()
    return [str(fila[1]) for fila in filas]


def _texto(valor: Any) -> Any:
    """Como se escribe un valor en el JSON: **las fechas en ISO, no con `str`**.

    **`str(datetime)` da `2026-10-22 14:02:40` y `isoformat()` da
    `2026-10-22T14:02:40`**: los dos se leen, **pero solo uno vuelve igual**.
    **La ida y vuelta del hito compara los ficheros, y con `str` la segunda
    exportacion sale distinta de la primera por un guion.**
    """
    if isinstance(valor, (datetime, date)):
        return valor.isoformat()
    return str(valor)


def _valor(tipo: Any, valor: Any) -> Any:
    """El valor del paquete, **puesto en el tipo que la columna espera**.

    **Un JSON no tiene fechas**: al exportar se escriben como texto ISO, y al
    importar hay que devolverlas a `datetime` **o la base las rechaza**.
    **Se mira el tipo de la columna, no el aspecto del texto**: adivinar por la
    forma acierta casi siempre, y ese Â«casiÂ» es un `TypeError` en la primera
    tabla con una fecha.
    """
    if valor is None:
        return None
    if isinstance(tipo, (DateTime, Date)) and isinstance(valor, str):
        try:
            return datetime.fromisoformat(valor)
        except ValueError:
            return valor
    return valor


def exportar(destino: Path) -> Paquete:
    """Escribe el paquete con el material publico."""
    fabrica = _fabrica()
    paquete = Paquete(formato=FORMATO, creado=datetime.now(UTC).isoformat(), tablas={})
    with fabrica() as session:
        for tabla, sentencia in VIAJAN:
            columnas = _columnas(session, tabla)
            if not columnas:
                continue
            filas = session.execute(text(sentencia)).all()
            paquete.tablas[tabla] = [dict(zip(columnas, fila, strict=True)) for fila in filas]
    destino.write_text(
        json.dumps(paquete.__dict__, ensure_ascii=False, default=_texto),
        encoding="utf-8",
    )
    return paquete


def revisar(ruta: Path) -> tuple[bool, tuple[str, ...]]:
    """**La prueba del hito**: que dentro no haya nada de una persona."""
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    tablas = datos.get("tablas", {})
    problemas: list[str] = []
    for prohibida in PROHIBIDAS:
        if tablas.get(prohibida):
            problemas.append(f"viene la tabla {prohibida} con {len(tablas[prohibida])} filas")
    privadas = [
        fila
        for fila in tablas.get("question_explanations", [])
        if str(fila.get("origin")) == "private"
    ]
    if privadas:
        problemas.append(f"vienen {len(privadas)} explicaciones privadas")
    return (not problemas, tuple(problemas))


def importar(ruta: Path) -> dict[str, int]:
    """Mete el paquete, **y dos veces seguidas deja lo mismo**."""
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    if int(datos.get("formato", 0)) != FORMATO:
        raise SystemExit(f"el paquete es formato {datos.get('formato')} y esto lee {FORMATO}")
    permitidas = {tabla for tabla, _ in VIAJAN}
    fabrica = _fabrica()
    metidas: dict[str, int] = {}
    with fabrica() as session:
        bind = session.get_bind()
        for tabla, filas in datos.get("tablas", {}).items():
            if not filas:
                metidas[tabla] = 0
                continue
            if tabla not in permitidas:
                raise SystemExit(f"el paquete trae una tabla que no viaja: {tabla}")
            columnas = list(filas[0].keys())
            reales = set(_columnas(session, tabla))
            sobran = {str(columna) for columna in columnas} - reales
            if sobran:
                raise SystemExit(f"la tabla {tabla} no tiene esas columnas: {sorted(sobran)}")
            tabla_orm = Table(tabla, MetaData(), autoload_with=bind)
            preparadas = [
                {
                    columna: _valor(tabla_orm.columns[columna].type, valor)
                    for columna, valor in fila.items()
                }
                for fila in filas
            ]
            session.execute(tabla_orm.insert().prefix_with("OR REPLACE"), preparadas)
            metidas[tabla] = len(filas)
        session.commit()
    return metidas


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="comando", required=True)
    exportar_p = sub.add_parser("exportar", help="escribe el paquete publico")
    exportar_p.add_argument("--salida", required=True, type=Path)
    revisar_p = sub.add_parser("revisar", help="comprueba que no lleva nada de una persona")
    revisar_p.add_argument("--paquete", required=True, type=Path)
    importar_p = sub.add_parser("importar", help="mete el paquete, o lo actualiza")
    importar_p.add_argument("--paquete", required=True, type=Path)
    args = parser.parse_args(argv)

    if args.comando == "exportar":
        paquete = exportar(args.salida)
        print(f"paquete escrito en {args.salida}")
        print(f"  {paquete.resumen()}")
        return 0
    if args.comando == "revisar":
        bien, problemas = revisar(args.paquete)
        if bien:
            print("el paquete no lleva nada de una persona")
            return 0
        print("el paquete NO se puede repartir:")
        for problema in problemas:
            print(f"  - {problema}")
        return 1
    if args.comando == "importar":
        metidas = importar(args.paquete)
        total = sum(metidas.values())
        print(f"importadas {total} fila(s) en {len(metidas)} tabla(s)")
        for tabla, cuantas in metidas.items():
            print(f"  {tabla}: {cuantas}")
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
