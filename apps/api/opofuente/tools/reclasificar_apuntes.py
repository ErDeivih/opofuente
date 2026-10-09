"""Saca de un tema lo que no es suyo: las preguntas mal clasificadas, a la cola de clasificación.

Es el paso 5 del encargo del propietario para IV.7, y hace tres cosas, en este orden:

1. **copia de seguridad** del árbol de datos con el mecanismo del repositorio (`BackupService`), y
   se dice su identificador antes de escribir nada;
2. **mueve las preguntas** que no son de ninguna materia del tema: cada una va a la **cola de
   clasificación** con su **propuesta de tema** (`status="provisional"`, que es lo que se despacha
   en `/admin/clasificacion`), o se declara **fuera de temario** con su motivo (`enunciado_roto`
   para un enunciado que no es una pregunta contestable, `otra_administracion` para la normativa de
   otra administración). Por los dos caminos se retiran los mapeos que la pregunta tuviera, así que
   deja de contar en este tema;
3. **se lleva sus datos**: los hechos del tema que salieron de esas preguntas se borran, con su
   evento de auditoría (`topic_fact.forgotten`) y el actor identificable.

Nada de esto se hace por SQL a mano: las preguntas entran por `QuestionService.apply_topic_batch`
(el mismo camino de escritura que la ruta `POST /api/v1/questions/topics/bulk`, con su auditoría) y
los hechos por `TopicNotesRepository.forget_facts`, que también audita.

Uso:
    # ver qué haría, sin escribir y sin copia
    uv run python -m opofuente.tools.reclasificar_apuntes --tema IV.7
    # hacerlo (copia de seguridad primero)
    uv run python -m opofuente.tools.reclasificar_apuntes --tema IV.7 --aplicar

Códigos de salida: 0 bien · 1 fallo · 2 falta la clave de decisión (una pregunta sin destino
declarado): **no se escribe nada a medias**.
"""

from __future__ import annotations

import argparse
import re
import sys
from collections.abc import Sequence
from dataclasses import replace
from datetime import UTC, datetime

from sqlalchemy import select

from opofuente.application.backup_service import BackupService
from opofuente.application.question_models import TopicAssignmentRequest
from opofuente.application.question_service import QuestionService
from opofuente.config import Settings, get_settings
from opofuente.domain.backup import DEFAULT_SCOPE
from opofuente.domain.errors import OpoFuenteError
from opofuente.domain.rag import normalise
from opofuente.domain.topic_classification import OutOfSyllabus
from opofuente.domain.topic_index import catalogo, indice_de
from opofuente.infrastructure.clock import SystemClock
from opofuente.infrastructure.db import build_engine, build_session_factory
from opofuente.infrastructure.db_models import CurriculumNodeRecord
from opofuente.infrastructure.document_repository import SqlAlchemyDocumentRepository
from opofuente.infrastructure.question_repository import SqlAlchemyQuestionRepository
from opofuente.infrastructure.representation_store import RepresentationStore
from opofuente.infrastructure.topic_notes_repository import SqlAlchemyTopicNotesRepository

#: Quién firma esto en la auditoría. Se distingue de la máquina (`llm:deepseek-flash`) y de la
#: persona (`local`): es una decisión tomada con el encargo del propietario delante.
ACTOR = "f9:reclasificacion-iv7"

#: El destino de cada pregunta que no es de ninguna materia del tema, por **lo que dice su
#: enunciado**. Se escribe a mano y se lee: es la decisión que el propietario quiere ver.
#:
#: - `propone` es la ruta de un **tema del programa** al que la pregunta pertenece de verdad. Va
#:   como propuesta (`provisional`), que es lo que aparece en la cola del panel para confirmarla;
#: - `fuera` es un motivo de fuera de temario: no hay tema al que mandarla.
#:
#: Una pregunta que no case con ninguna regla **para la corrida con código 2**: inventarle un
#: destino sería exactamente lo que no se puede hacer.
_REGLAS: tuple[tuple[str, tuple[str, ...], str], ...] = (
    # --- otros bloques del programa, con su propuesta de tema --------------------------------
    (
        "propone",
        (r"integridad referencial", r"integridad de la entidad", r"modelo relacional de datos"),
        "III.1",
    ),
    (
        "propone",
        (r"diagramas? de flujo de datos", r"metrica v3", r"el flujo de datos representa"),
        "III.9",
    ),
    ("propone", (r"acoplamiento de marca", r"stamp coupling"), "III.4"),
    ("propone", (r"\bhba\b", r"host bus adapter"), "II.2"),
    ("propone", (r"\bmdm\b", r"dispositivos moviles"), "II.2"),
    ("propone", (r"\bdect\b", r"telefonia inalambrica"), "IV.6"),
    (
        "propone",
        (r"hkey_classes_root", r"extension de fichero", r"registro de windows"),
        "II.4",
    ),
    # --- lo que no es de este temario ni de otro: fuera, con su motivo ------------------------
    (
        "fuera",
        (r"consejo de seguridad nacional", r"real decreto 43/2021"),
        OutOfSyllabus.OTRA_ADMINISTRACION.value,
    ),
    (
        "fuera",
        (
            r"network time protocol",
            r"microsoft sql server",
            r"certificate management protocol",
            r"discard protocol",
            r"quick mail transfer protocol",
            r"remote desktop protocol",
            r"cual de las siguientes afirmaciones es correcta",
            r"cual de las siguientes respuestas es la correcta",
            r"cual de las siguientes afirmaciones es verdadera",
            r"indique la respuesta incorrecta",
        ),
        OutOfSyllabus.ENUNCIADO_ROTO.value,
    ),
)


def _use_utf8_stdout() -> None:
    reconfigurar = getattr(sys.stdout, "reconfigure", None)
    if callable(reconfigurar):
        reconfigurar(encoding="utf-8")


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="opofuente.tools.reclasificar_apuntes",
        description="Saca de un tema las preguntas mal clasificadas y se lleva sus hechos.",
    )
    parser.add_argument("--tema", default="IV.7", help="tema del programa (por defecto IV.7)")
    parser.add_argument(
        "--aplicar",
        action="store_true",
        help="escribe los cambios (hace copia de seguridad antes); sin esto solo lo enseña",
    )
    return parser.parse_args(list(argv))


def _destino(limpio: str) -> tuple[str, str] | None:
    for modo, patrones, valor in _REGLAS:
        if any(re.search(patron, limpio) for patron in patrones):
            return modo, valor
    return None


def main(argv: Sequence[str] | None = None) -> int:
    _use_utf8_stdout()
    args = parse_args(sys.argv[1:] if argv is None else argv)
    settings: Settings = get_settings()
    settings.data_paths.ensure_directories()
    engine = build_engine(settings.data_paths.database)
    try:
        session_factory = build_session_factory(engine)
        notas = SqlAlchemyTopicNotesRepository(session_factory)
        node_id = notas.node_id(args.tema)
        if node_id is None:
            print(f"[{args.tema}] no existe ese tema en el programa", file=sys.stderr)
            return 1
        nodo = notas.node(node_id)
        if nodo is None:
            print(f"[{args.tema}] no es un tema del programa", file=sys.stderr)
            return 1
        if catalogo(args.tema) is None:
            print(
                f"[{args.tema}] no tiene catálogo de materias: no hay nada que sacar de aquí "
                "(el catálogo es el que dice qué es del tema y qué no)",
                file=sys.stderr,
            )
            return 1
        indice = indice_de(
            topic_code=nodo.code,
            topic_title=nodo.title,
            epigraphs=nodo.epigraphs,
            hechos=notas.facts(node_id),
            grupos=notas.question_groups(node_id),
        )

        # --- el destino de cada pregunta que no es de ninguna materia del tema ---------------
        filas: list[TopicAssignmentRequest] = []
        sin_destino: list[str] = []
        for grupo in indice.grupos_sin_materia:
            limpio = normalise(grupo.representative.stem)
            destino = _destino(limpio)
            if destino is None:
                sin_destino.append(grupo.representative.stem)
                continue
            modo, valor = destino
            for pregunta in grupo.questions:
                if modo == "propone":
                    filas.append(
                        TopicAssignmentRequest(
                            question_version_id=pregunta.question_version_id,
                            curriculum_node_id=valor,
                            status="provisional",
                            confidence=0.0,
                            reason=(
                                "propuesta de tema: la pregunta se clasificó en "
                                f"{args.tema} y su bloque es {valor}"
                            ),
                            retire_others=True,
                        )
                    )
                else:
                    filas.append(
                        TopicAssignmentRequest(
                            question_version_id=pregunta.question_version_id,
                            exclusion_reason=OutOfSyllabus(valor),
                            reason="la pregunta no es de este temario: se retira del tema",
                            retire_others=True,
                        )
                    )

        print(f"[{args.tema}] {len(indice.grupos_sin_materia)} grupo(s) sin materia del tema")
        print(f"    a mover: {len(filas)} pregunta(s)")
        propuestas = sum(1 for fila in filas if fila.curriculum_node_id is not None)
        excluidas = len(filas) - propuestas
        print(
            f"    {propuestas} van a la cola con propuesta de tema · {excluidas} fuera de temario"
        )
        print(f"    hechos que se van con ellas: {len(indice.sin_materia)}")
        if sin_destino:
            print(
                f"    SIN DESTINO DECLARADO: {len(sin_destino)} grupo(s). No se escribe nada.",
                file=sys.stderr,
            )
            for stem in sin_destino:
                print(f"      · {stem[:100]}", file=sys.stderr)
            return 2
        if not args.aplicar:
            print("\nENSAYO: se llama a todo menos a la escritura. Con --aplicar se hace.")
            for peticion in filas:
                where = peticion.curriculum_node_id or f"fuera:{peticion.exclusion_reason}"
                print(f"      · {peticion.question_version_id} -> {where}")
            return 0

        # --- el destino tiene que existir y ser un tema --------------------------------------
        # La tabla de reglas escribe **rutas** (`III.1`) porque es lo que se lee; la asignación
        # necesita el **identificador** del nodo. Se traduce aquí, y si una ruta no existe no se
        # escribe nada: una propuesta a un nodo que no está sería una fila con `error` y la pregunta
        # se quedaría donde estaba, que es lo que ha pasado en la primera pasada de esta corrida.
        with session_factory() as session:
            identificador = {
                str(fila[0]): str(fila[1])
                for fila in session.execute(
                    select(CurriculumNodeRecord.path, CurriculumNodeRecord.id).where(
                        CurriculumNodeRecord.node_type == "topic"
                    )
                )
            }
        faltan = sorted(
            {
                peticion.curriculum_node_id
                for peticion in filas
                if peticion.curriculum_node_id is not None
                and peticion.curriculum_node_id not in identificador
            }
        )
        if faltan:
            print(f"estos temas propuestos no están en el programa: {faltan}", file=sys.stderr)
            return 1
        filas = [
            replace(peticion, curriculum_node_id=identificador[peticion.curriculum_node_id])
            if peticion.curriculum_node_id is not None
            else peticion
            for peticion in filas
        ]

        # --- 1. la copia de seguridad, antes de tocar nada -----------------------------------
        servicio_copias = BackupService(
            paths=settings.data_paths,
            app_version="f9",
            clock=lambda: datetime.now(UTC),
            schema_revision=lambda: "0030_ancla_en_conflicto",
        )
        copia = servicio_copias.create(
            scope=DEFAULT_SCOPE,
            note=f"antes de sacar de {args.tema} las preguntas mal clasificadas (f9)",
        )
        print(
            f"\ncopia de seguridad: {copia.id} · {copia.size_bytes} bytes · "
            f"{copia.file_count} fichero(s)"
        )
        verificacion = servicio_copias.verify(copia.id)
        print(f"    verificada: {None if verificacion is None else verificacion.verified}")

        # --- 2. las preguntas, por el mismo camino que la ruta por lotes ---------------------
        servicio = QuestionService(
            questions=SqlAlchemyQuestionRepository(session_factory),
            clock=SystemClock(),
            documents=SqlAlchemyDocumentRepository(
                session_factory, RepresentationStore(settings.data_paths)
            ),
        )
        lote = servicio.apply_topic_batch(filas, actor=ACTOR)
        desenlaces: dict[str, int] = {}
        for resultado in lote.rows:
            desenlaces[resultado.outcome] = desenlaces.get(resultado.outcome, 0) + 1
        print(f"    preguntas: {desenlaces}")
        errores = [resultado for resultado in lote.rows if resultado.outcome == "error"]
        for resultado in errores[:10]:
            print(
                f"      · ERROR {resultado.question_version_id}: {resultado.detail}",
                file=sys.stderr,
            )

        # --- 3. sus datos se van con ellas ----------------------------------------------------
        borrados = notas.forget_facts(
            node_id,
            [hecho.fact_id for hecho in indice.sin_materia if hecho.fact_id],
            actor=ACTOR,
            reason=(
                f"los hechos de las preguntas que salen de {args.tema}: se van con ellas a la cola "
                "de clasificación"
            ),
            now=SystemClock().now(),
        )
        print(f"    hechos borrados (con su evento): {borrados}")
        return 0 if not errores else 1
    except OpoFuenteError as error:
        print(f"No se ha podido reclasificar: {error}", file=sys.stderr)
        return 1
    finally:
        engine.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
