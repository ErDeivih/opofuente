"""El generador de explicaciones (M1 de la fase 3).

**Por defecto no llama a nadie y no escribe nada**: recorre el camino entero —las preguntas
con ancla y clave servible, el texto de su apartado, los lotes y las comprobaciones— con el
doble, **a coste cero**, y dice qué habría pasado. Con `--de-verdad` llama al modelo y
gasta; con `--guardar` escribe las aceptadas.

La clave se lee de `DEEPSEEK_API_KEY` y no se escribe en ningún fichero.
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
from collections.abc import Sequence

from opofuente.application.explicaciones import PreguntaAExplicar, validar_lote
from opofuente.application.question_service import QuestionService
from opofuente.config import get_settings
from opofuente.domain.questions import Origin
from opofuente.infrastructure.clock import SystemClock
from opofuente.infrastructure.db import build_engine, build_session_factory
from opofuente.infrastructure.document_repository import SqlAlchemyDocumentRepository
from opofuente.infrastructure.explanation_client import DeepSeekExplanationProposer
from opofuente.infrastructure.question_repository import SqlAlchemyQuestionRepository
from opofuente.infrastructure.representation_store import RepresentationStore
from opofuente_testing.explanation_proposer import FakeExplanationProposer

#: Las preguntas que se pueden explicar: con apartado publicado y clave servible.
_CONSULTA = (
    "select a.question_version_id, v.stem, a.expected_letters, s.body_markdown, a.section_id "
    "from question_note_anchors a "
    "join question_versions v on v.id = a.question_version_id "
    "join topic_note_sections s on s.id = a.section_id "
    "where a.result = 'covered' and a.expected_letters is not null "
    "and length(a.expected_letters) > 2 and length(trim(s.body_markdown)) > 0 "
    "limit ?"
)


def _preguntas(limite: int) -> tuple[PreguntaAExplicar, ...]:
    """Las N primeras preguntas que se pueden explicar, con su ancla y su apartado."""
    base = sqlite3.connect(get_settings().data_paths.database)
    try:
        filas = base.execute(_CONSULTA, (limite,)).fetchall()
        preguntas: list[PreguntaAExplicar] = []
        for qid, stem, letras, cuerpo, seccion in filas:
            clave = tuple(
                str(elemento).strip().lower()
                for elemento in json.loads(str(letras))
                if str(elemento).strip()
            )
            if not clave:
                continue
            opciones = tuple(
                (str(letra), str(texto))
                for letra, texto in base.execute(
                    "select stable_key, text from option_versions where question_version_id = ?",
                    (qid,),
                )
            )
            preguntas.append(
                PreguntaAExplicar(
                    question_version_id=str(qid),
                    enunciado=str(stem),
                    opciones=opciones,
                    clave=clave,
                    apartado=str(cuerpo),
                    note_anchor_id=str(seccion),
                )
            )
        return tuple(preguntas)
    finally:
        base.close()


def _servicio() -> QuestionService:
    """El servicio de preguntas, para guardar lo que el modelo escriba."""
    settings = get_settings()
    engine = build_engine(settings.data_paths.database)
    session_factory = build_session_factory(engine)
    return QuestionService(
        questions=SqlAlchemyQuestionRepository(session_factory),
        clock=SystemClock(),
        documents=SqlAlchemyDocumentRepository(
            session_factory, RepresentationStore(settings.data_paths)
        ),
    )


def _guardar(aceptadas: Sequence[object], *, modelo: str) -> int:
    """Escribe las aceptadas en la base, **con su cita y su anclaje**.

    **Devuelve cuántas entraron de verdad**: el servicio puede decir que no si la pregunta
    desapareció entre la lectura y la escritura, y contarlas como guardadas sería mentir en la
    cifra del hito.
    """
    servicio = _servicio()
    guardadas = 0
    for propuesta in aceptadas:
        vista = servicio.set_explanation(
            propuesta.question_version_id,  # type: ignore[attr-defined]
            text=propuesta.texto,  # type: ignore[attr-defined]
            origin=Origin.GENERATED,
            citation=propuesta.cita,  # type: ignore[attr-defined]
            model_name=modelo,
        )
        if vista is not None:
            guardadas = guardadas + 1
    return guardadas


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limite", type=int, default=20, help="cuántas preguntas, por defecto 20")
    parser.add_argument(
        "--desde",
        type=int,
        default=0,
        help="se salta las primeras N: es lo que permite reanudar una corrida cortada",
    )
    parser.add_argument(
        "--de-verdad",
        action="store_true",
        help="llama al modelo de verdad (gasta); sin esto usa el doble y no gasta nada",
    )
    parser.add_argument(
        "--guardar",
        action="store_true",
        help="escribe las aceptadas en la base (solo tiene sentido con --de-verdad)",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.de_verdad:
        clave = os.environ.get("DEEPSEEK_API_KEY", "").strip()
        if not clave:
            print("sin DEEPSEEK_API_KEY no hay llamada: se para sin gastar")
            return 2
        proposer: object = DeepSeekExplanationProposer(api_key=clave)
    else:
        proposer = FakeExplanationProposer()
    preguntas = _preguntas(args.limite + args.desde)
    if not preguntas:
        print("no hay preguntas con ancla y clave servible")
        return 0
    desde = min(args.desde, len(preguntas))
    preguntas = preguntas[desde:]
    print(f"preguntas con ancla y clave: {len(preguntas)} (desde la {desde + 1})")
    salida = validar_lote(preguntas, proposer)  # type: ignore[arg-type]
    print(f"aceptadas: {len(salida.aceptadas)}")
    print(f"rechazadas: {len(salida.rechazadas)}")
    for ident, motivos in salida.rechazadas[:5]:
        print(f"  {ident}: {'; '.join(motivos)}")
    print(f"sin material: {len(salida.sin_material)}")
    if args.de_verdad:
        entrada, salida_tokens = proposer.ultimos_tokens  # type: ignore[attr-defined]
        print(f"tokens: entrada {entrada} · salida {salida_tokens}")
    if args.guardar:
        if not args.de_verdad:
            print("sin --de-verdad no se guarda nada: el doble escribe explicaciones de mentira")
            return 2
        modelo = proposer.version  # type: ignore[attr-defined]
        print(f"guardadas: {_guardar(salida.aceptadas, modelo=modelo)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
