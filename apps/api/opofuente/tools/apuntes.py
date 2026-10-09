"""Los apuntes de un tema, guiados por sus preguntas (pasos B-E del plan, los tres pilotos).

Es el comando del piloto: coge las preguntas **ya clasificadas** de un tema, escribe con el modelo
los
hechos que hay que saber, monta el esquema con los epígrafes oficiales, redacta cada apartado con
todos
sus hechos y el material del tema, y comprueba **pregunta a pregunta** que los apuntes la contestan.
Al final guarda el tema como versión (el mecanismo de versiones del dossier, que ya existía).

Uso:
    # ver lo que hay en un tema, sin llamar a nadie
    uv run python -m opofuente.tools.apuntes --tema IV.7 --listar
    # el indice por materias del tema, sin llamar a nadie (el esquema, antes de redactar)
    uv run python -m opofuente.tools.apuntes --tema IV.7 --esquema
    # escribir los apuntes del tema (llama al modelo)
    $env:DEEPSEEK_API_KEY = "…"
    uv run python -m opofuente.tools.apuntes --tema IV.7
    # escribir, pero no dar el tema por bueno si no pasa las comprobaciones de forma
    uv run python -m opofuente.tools.apuntes --tema IV.7 --exigir-calidad
    # los tres pilotos, de una vez
    uv run python -m opofuente.tools.apuntes --tema IV.7 --tema I.6 --tema I.1

La clave se lee de `DEEPSEEK_API_KEY`. **No** se escribe en ningún fichero del repositorio, ni en un
log, ni en este comando: si no está, el comando lo dice y para. Una corrida sin clave gastaría horas
de trabajo para nada.

Códigos de salida: 0 bien · 1 fallo al escribir los apuntes · 2 falta la clave · 3 el tema no pasa
las comprobaciones de forma (con `--exigir-calidad`, no se archiva la versión).
"""

from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Sequence

from opofuente.application.dossier_service import DossierService
from opofuente.application.topic_notes_models import TopicNotesReport
from opofuente.application.topic_notes_service import TopicNotesService
from opofuente.config import Settings, get_settings
from opofuente.domain.errors import OpoFuenteError
from opofuente.domain.topic_index import catalogo, indice_de
from opofuente.infrastructure.clock import SystemClock
from opofuente.infrastructure.db import build_engine, build_session_factory
from opofuente.infrastructure.dossier_repository import SqlAlchemyDossierRepository
from opofuente.infrastructure.topic_notes_client import (
    BASE_URL_POR_DEFECTO,
    MODELO_POR_DEFECTO,
    DeepSeekNotesModel,
)
from opofuente.infrastructure.topic_notes_repository import SqlAlchemyTopicNotesRepository

#: La variable de la que se lee la clave. Es lo único que se necesita configurar para escribir.
VARIABLE_DE_LA_CLAVE = "DEEPSEEK_API_KEY"

#: Los tres temas del piloto que fijó el propietario (`DECISIONES-Y-SIGUIENTE-TANDA` §6).
PILOTOS = ("IV.7", "I.6", "I.1")


def _use_utf8_stdout() -> None:
    """El informe lleva acentos y comillas angulares: en Windows, redirigido, saldría en la
    codificación local y no se podría comparar entre máquinas."""
    reconfigurar = getattr(sys.stdout, "reconfigure", None)
    if callable(reconfigurar):
        reconfigurar(encoding="utf-8")


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    """Las opciones del comando, con los valores por defecto en su ayuda."""
    parser = argparse.ArgumentParser(
        prog="opofuente.tools.apuntes",
        description="Escribe los apuntes de un tema a partir de sus preguntas y los comprueba.",
    )
    parser.add_argument(
        "--tema",
        action="append",
        default=None,
        metavar="CODIGO",
        help=f"tema del programa, repetible (por defecto, los pilotos: {', '.join(PILOTOS)})",
    )
    parser.add_argument(
        "--listar",
        action="store_true",
        help="enseña lo que hay en el tema (preguntas, hechos y apartados) sin llamar al modelo",
    )
    parser.add_argument(
        "--esquema",
        action="store_true",
        help=(
            "enseña el índice por materias del tema (el esquema antes de redactar): qué apartados "
            "tendrá y qué hechos van en cada uno, sin llamar al modelo"
        ),
    )
    parser.add_argument(
        "--exigir-calidad",
        dest="exigir_calidad",
        action="store_true",
        help=(
            "no da el tema por bueno si no pasa las comprobaciones de forma (encabezados "
            "repetidos, marcas internas, tablas sin cabecera, párrafos repetidos y extensión): no "
            "archiva la versión y sale con código 3"
        ),
    )
    parser.add_argument(
        "--dry-run",
        "--seco",
        dest="dry_run",
        action="store_true",
        help="llama al modelo y dice lo que haría, pero no escribe nada",
    )
    parser.add_argument(
        "--limite",
        type=int,
        default=None,
        metavar="N",
        help="como mucho N grupos de preguntas (para probar sin gastar en el tema entero)",
    )
    parser.add_argument(
        "--sin-version",
        dest="version",
        action="store_false",
        help="no guarda el tema como versión al terminar",
    )
    parser.add_argument(
        "--modelo", default=MODELO_POR_DEFECTO, help=f"modelo (por defecto {MODELO_POR_DEFECTO})"
    )
    parser.add_argument(
        "--base-url",
        default=BASE_URL_POR_DEFECTO,
        help=f"endpoint del modelo (por defecto {BASE_URL_POR_DEFECTO})",
    )
    parser.add_argument(
        "--paralelo",
        type=int,
        default=4,
        metavar="N",
        help="llamadas al modelo a la vez (por defecto 4; 1 es secuencial)",
    )
    parser.add_argument(
        "--tiempo",
        type=float,
        default=300.0,
        metavar="SEGUNDOS",
        help="tiempo máximo por llamada (por defecto 300)",
    )
    return parser.parse_args(list(argv))


def main(argv: Sequence[str] | None = None) -> int:
    _use_utf8_stdout()
    args = parse_args(sys.argv[1:] if argv is None else argv)
    settings: Settings = get_settings()
    settings.data_paths.ensure_directories()
    temas: list[str] = list(args.tema) if args.tema else list(PILOTOS)

    engine = build_engine(settings.data_paths.database)
    try:
        session_factory = build_session_factory(engine)
        notas = SqlAlchemyTopicNotesRepository(session_factory)
        dossier_service = DossierService(
            repository=SqlAlchemyDossierRepository(session_factory),
            clock=SystemClock(),
            notes=notas,
        )
        if args.listar:
            # Sin clave y sin modelo: ver lo que hay no cuesta nada y es lo primero que se mira.
            for tema in temas:
                print("\n".join(_listar(notas, tema)))
            return 0
        if args.esquema:
            # El esquema antes de redactar: tampoco llama a nadie ni necesita clave.
            for tema in temas:
                print("\n".join(_esquema(notas, tema)))
                print()
            return 0

        api_key = os.environ.get(VARIABLE_DE_LA_CLAVE, "")
        if not api_key.strip():
            print(
                f"Falta la variable de entorno {VARIABLE_DE_LA_CLAVE}: sin clave no se escriben "
                "apuntes. Se lee del entorno y no se guarda en ningún sitio.",
                file=sys.stderr,
            )
            return 2

        servicio = TopicNotesService(
            repository=notas,
            dossier=SqlAlchemyDossierRepository(session_factory),
            model=DeepSeekNotesModel(
                api_key=api_key,
                model=args.modelo,
                base_url=args.base_url,
                timeout_seconds=args.tiempo,
            ),
            workers=max(1, args.paralelo),
        )
        reloj = SystemClock()
        if args.dry_run:
            print("ENSAYO: se llama al modelo y NO se escribe nada.\n")
        total = 0.0
        sin_calidad: list[str] = []
        for tema in temas:
            informe = servicio.run(
                tema,
                now=reloj.now(),
                dry_run=args.dry_run,
                limite_grupos=args.limite,
            )
            pasa = informe.revision is None or informe.revision.pasa
            if args.version and not args.dry_run and (pasa or not args.exigir_calidad):
                archivado = dossier_service.archive(informe.node_id)
                if archivado is not None:
                    informe.version_created = archivado[1]
            if not pasa:
                sin_calidad.append(informe.topic_code)
            print("\n".join(informe.lines()))
            print()
            total += informe.estimated_cost_usd
        if len(temas) > 1:
            print(f"Coste estimado de los {len(temas)} temas: {total:.4f} $ (precios de valle).")
        if sin_calidad:
            print(
                "NO pasan las comprobaciones de forma: "
                + ", ".join(sin_calidad)
                + (
                    ". No se ha archivado la versión: un tema con encabezados repetidos, marcas "
                    "internas, tablas sin cabecera, párrafos repetidos o extensión de sobra no se "
                    "da por bueno."
                    if args.exigir_calidad
                    else ". Se archiva igual porque no se pidió --exigir-calidad."
                ),
                file=sys.stderr,
            )
            if args.exigir_calidad:
                return 3
        return 0
    except OpoFuenteError as error:
        print(f"No se han podido escribir los apuntes: {error}", file=sys.stderr)
        return 1
    finally:
        engine.dispose()


def _esquema(notas: SqlAlchemyTopicNotesRepository, code: str) -> tuple[str, ...]:
    """El índice por materias del tema: el esquema antes de redactar, sin llamar a nadie.

    Es el paso C del plan tal como lo pidió el propietario: ver el árbol de apartados antes de que
    se escriba nada. Los hechos y las preguntas salen de la base; el reparto, del catálogo del tema.
    """
    node_id = notas.node_id(code)
    if node_id is None:
        return (f"[{code}] no existe ese tema en el programa",)
    nodo = notas.node(node_id)
    if nodo is None:
        return (f"[{code}] no es un tema del programa",)
    if catalogo(code) is None:
        return (
            f"[{code}] todavía no tiene catálogo de materias: el índice de este tema está sin "
            "definir (se define antes de redactar, no se inventa)",
        )
    try:
        indice = indice_de(
            topic_code=code,
            topic_title=nodo.title,
            epigraphs=nodo.epigraphs,
            hechos=notas.facts(node_id),
            grupos=notas.question_groups(node_id),
        )
    except (KeyError, ValueError) as error:
        return (f"[{code}] el catálogo de materias no cuadra con el temario: {error}",)
    return indice.lines()


def _listar(notas: SqlAlchemyTopicNotesRepository, code: str) -> tuple[str, ...]:
    """Lo que hay en un tema hoy: sus preguntas, sus hechos y sus apartados."""
    node_id = notas.node_id(code)
    if node_id is None:
        return (f"[{code}] no existe ese tema en el programa",)
    nodo = notas.node(node_id)
    grupos = notas.question_groups(node_id)
    hechos = notas.facts(node_id)
    apartados = notas.sections(node_id)
    comprobadas = notas.checks(node_id)
    lineas = [
        f"[{code}] {'' if nodo is None else nodo.title}",
        f"    {len(nodo.epigraphs) if nodo else 0} epígrafe(s) · "
        f"{len(grupos)} grupo(s) de preguntas "
        f"({sum(len(grupo.questions) for grupo in grupos)} preguntas)",
        f"    hechos guardados: {len(hechos)} · apartados: {len(apartados)} · "
        f"comprobaciones: {len(comprobadas)}",
    ]
    for apartado in apartados:
        lineas.append(
            f"      · {apartado.key} · {apartado.title[:60]} · "
            f"{len(apartado.facts)} hecho(s) · {len(apartado.body_markdown)} caracteres"
        )
    return tuple(lineas)


def _resumen(informes: Sequence[TopicNotesReport]) -> tuple[str, ...]:
    """La última línea del comando cuando se escriben varios temas."""
    return tuple(
        f"[{informe.topic_code}] {informe.coverage.covered} cubiertas de "
        f"{informe.coverage.groups} · {informe.estimated_cost_usd:.4f} $"
        for informe in informes
    )


if __name__ == "__main__":
    raise SystemExit(main())
