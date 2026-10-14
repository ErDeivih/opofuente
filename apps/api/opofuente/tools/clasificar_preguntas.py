"""Clasifica por tema y epígrafe las preguntas que no tienen tema (F4, paso A del plan de apuntes).

Es el comando del piloto: selecciona las preguntas **sin tema** de una oposición, agrupadas por
banco (su conjunto de origen) y de mayor a menor, pregunta al modelo en lotes y escribe el resultado
por el **servicio** del banco de preguntas —el mismo que usa la ruta auditada—, dejando la confianza
y el motivo en la auditoría.

Uso:
    # ver los bancos y lo que les falta, sin llamar a nadie
    uv run python -m opofuente.tools.clasificar_preguntas --listar
    # los DOS primeros bancos, sin escribir nada
    $env:DEEPSEEK_API_KEY = "…"
    uv run python -m opofuente.tools.clasificar_preguntas --bancos 2 --dry-run

La clave se lee de `DEEPSEEK_API_KEY`. **No** se escribe en ningún fichero del repositorio, ni en un
log, ni en este comando: si no está, el comando lo dice y para. Un clasificador que se inventa la
clave (o que sigue sin ella y marca todo como «sin propuesta») estaría gastando una corrida entera
para nada.

Códigos de salida: 0 bien · 1 fallo al clasificar · 2 falta la clave (o el temario).
"""

from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Sequence

from opofuente.application.question_service import QuestionService
from opofuente.application.topic_classification_models import BankToClassify
from opofuente.application.topic_classification_service import (
    LOTE_POR_DEFECTO,
    TopicClassificationService,
)
from opofuente.config import Settings, get_settings
from opofuente.domain.errors import OpoFuenteError
from opofuente.infrastructure.clock import SystemClock
from opofuente.infrastructure.db import build_engine, build_session_factory
from opofuente.infrastructure.document_repository import SqlAlchemyDocumentRepository
from opofuente.infrastructure.profile_repository import SqlAlchemyProfileRepository
from opofuente.infrastructure.question_repository import SqlAlchemyQuestionRepository
from opofuente.infrastructure.representation_store import RepresentationStore
from opofuente.infrastructure.run_lock import ClassificationRunLock, current_run
from opofuente.infrastructure.topic_classification_client import (
    BASE_URL_POR_DEFECTO,
    MODELO_POR_DEFECTO,
    DeepSeekTopicProposer,
)
from opofuente.infrastructure.topic_classification_repository import (
    SqlAlchemyTopicClassificationRepository,
)

#: La variable de la que se lee la clave. Es lo único que se necesita configurar para clasificar.
VARIABLE_DE_LA_CLAVE = "DEEPSEEK_API_KEY"


def _use_utf8_stdout() -> None:
    """El informe lleva acentos y comillas angulares: en Windows, redirigido a un fichero, saldría
    en la codificación local y no se podría comparar entre máquinas."""
    reconfigurar = getattr(sys.stdout, "reconfigure", None)
    if callable(reconfigurar):
        reconfigurar(encoding="utf-8")


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    """Las opciones del comando, con los valores por defecto en su ayuda."""
    parser = argparse.ArgumentParser(
        prog="opofuente.tools.clasificar_preguntas",
        description="Clasifica por tema y epígrafe las preguntas sin tema, por bancos.",
    )
    parser.add_argument(
        "--oposicion",
        default=None,
        help="código de la oposición (por defecto, la del alumno en la configuración)",
    )
    parser.add_argument(
        "--bancos",
        type=int,
        default=None,
        metavar="N",
        help="clasifica solo los N bancos con más preguntas sin tema",
    )
    parser.add_argument(
        "--limite",
        type=int,
        default=None,
        metavar="N",
        help="clasifica como mucho N preguntas en total",
    )
    parser.add_argument(
        "--lote",
        type=int,
        default=LOTE_POR_DEFECTO,
        metavar="N",
        help=f"preguntas por llamada al modelo (por defecto {LOTE_POR_DEFECTO})",
    )
    parser.add_argument(
        "--dry-run",
        "--seco",
        dest="dry_run",
        action="store_true",
        help="llama al modelo y dice lo que haría, pero no escribe nada",
    )
    parser.add_argument(
        "--listar",
        action="store_true",
        help="enseña los bancos y lo que les falta, sin llamar al modelo ni escribir",
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
        "--tiempo",
        type=float,
        default=120.0,
        metavar="SEGUNDOS",
        help="tiempo máximo por llamada (por defecto 120)",
    )
    return parser.parse_args(list(argv))


def _banks_to_show(bancos: Sequence[BankToClassify]) -> str:
    """Los bancos en texto, numerados para poder decir «los dos primeros» sin ambigüedad."""
    if not bancos:
        return "No hay ningún banco con preguntas sin tema."
    lineas = [f"{len(bancos)} banco(s) con preguntas sin tema, de mayor a menor:"]
    for posicion, banco in enumerate(bancos, start=1):
        lineas.append(f"  {posicion:>3}. {banco.pending:>5} sin tema · {banco.title}")
    return "\n".join(lineas)


def main(argv: Sequence[str] | None = None) -> int:
    _use_utf8_stdout()
    args = parse_args(sys.argv[1:] if argv is None else argv)
    settings: Settings = get_settings()
    code = args.oposicion or settings.student_opposition
    settings.data_paths.ensure_directories()

    engine = build_engine(settings.data_paths.database)
    try:
        session_factory = build_session_factory(engine)
        classification = SqlAlchemyTopicClassificationRepository(session_factory)
        profiles = SqlAlchemyProfileRepository(session_factory)
        question_service = QuestionService(
            questions=SqlAlchemyQuestionRepository(session_factory),
            clock=SystemClock(),
            documents=SqlAlchemyDocumentRepository(
                session_factory, RepresentationStore(settings.data_paths)
            ),
        )
        if args.listar:
            # Sin clave y sin modelo: ver lo que hay no cuesta nada y es lo primero que se mira.
            oposicion_id = _opposition_id(profiles, code)
            print(_banks_to_show(classification.banks(oposicion_id, limit=args.bancos)))
            # Si hay una corrida en curso se dice aquí: es la respuesta a «¿por qué no arranca?»
            # antes de intentarlo siquiera.
            en_curso = current_run(session_factory)
            if en_curso is not None:
                print(
                    f"\nAVISO: hay una clasificación en curso desde "
                    f"{en_curso.get('iniciada', en_curso.get('marca', '?'))} "
                    f"(oposición «{en_curso.get('oposicion', 'desconocida')}»). Otra corrida se "
                    "negará a arrancar hasta que termine."
                )
            return 0

        api_key = os.environ.get(VARIABLE_DE_LA_CLAVE, "")
        if not api_key.strip():
            print(
                f"Falta la variable de entorno {VARIABLE_DE_LA_CLAVE}: sin clave no se clasifica "
                "nada. Se lee del entorno y no se guarda en ningún sitio.",
                file=sys.stderr,
            )
            return 2

        service = TopicClassificationService(
            classification=classification,
            profiles=profiles,
            questions=question_service,
            proposer=DeepSeekTopicProposer(
                api_key=api_key,
                model=args.modelo,
                base_url=args.base_url,
                timeout_seconds=args.tiempo,
            ),
            # La marca de corrida: dos clasificaciones a la vez sobre la misma base se pisan y
            # dejan preguntas con dos temas propuestos. La segunda se niega y lo dice.
            lock=ClassificationRunLock(session_factory, opposition_code=code),
            batch_size=args.lote,
        )
        if args.dry_run:
            print("ENSAYO: se llama al modelo y NO se escribe nada.\n")
        report = service.run(code, banks=args.bancos, limit=args.limite, dry_run=args.dry_run)
        print("\n".join(report.lines()))
        return 0
    except OpoFuenteError as error:
        print(f"No se ha podido clasificar: {error}", file=sys.stderr)
        return 1
    finally:
        engine.dispose()


def _opposition_id(profiles: SqlAlchemyProfileRepository, code: str) -> str:
    """El identificador de la oposición por su código, para poder contar sin montar el servicio."""
    for oposicion in profiles.list_oppositions():
        if oposicion.code == code:
            return oposicion.id
    raise OpoFuenteError(f"no hay ninguna oposición con el código «{code}»")


if __name__ == "__main__":
    raise SystemExit(main())
