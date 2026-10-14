"""Repara, una a una y por la ruta auditada, las preguntas que una regla puede arreglar (F20).

Es la mitad de la ficha de pregunta que no se puede hacer a mano sin aburrirse: el bloque del panel
dejó **once** preguntas señaladas como «mal importadas» que una regla puede reparar y **veintiún**
enunciados con la referencia del examen pegada. Repararlas es escribir una versión nueva de cada
una, y
eso se hace por el mismo camino que usa la pantalla (`QuestionFileService.repair` → el repositorio
de la
ficha), con su evento de auditoría, su motivo y su actor.

**Ensayo por defecto**: sin `--aplicar` no escribe nada y dice qué haría. Con `--aplicar` hace
**copia verificada** antes de tocar nada, salvo que se diga `--sin-copia`, que solo vale cuando ya
se
trabaja sobre una copia de la base.

**Idempotente**: una pregunta reparada deja de estar señalada (su incidencia pasa a `reviewed`) y su
enunciado deja de llevar la referencia, así que volver a pasar el comando no escribe nada la segunda
vez. Eso se comprueba en su prueba.

Lo que el comando **no** hace, y lo dice con números: reparar lo que ninguna regla puede reparar. De
las once, la mayoría no son ni malas importaciones —una opción que menciona a otra («… indicado en
la
opción c)») está bien escrita— y las demás son restos que ninguna regla puede reconstruir. Cada una
sale
con su motivo, agrupado, para que el propietario sepa qué le queda y por qué.

Uso:
    # ver qué haría (no escribe nada)
    uv run python -m opofuente.tools.reparar_preguntas
    # hacerlo, con copia verificada antes
    uv run python -m opofuente.tools.reparar_preguntas --aplicar
    # hacerlo sobre una copia, sin copia de seguridad
    uv run python -m opofuente.tools.reparar_preguntas --aplicar --sin-copia

Códigos de salida: 0 bien · 1 fallo.
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from collections.abc import Sequence
from datetime import UTC, datetime

from sqlalchemy import select

from opofuente.application.backup_service import BackupService
from opofuente.application.notes_incident_service import NotesIncidentsService
from opofuente.application.question_file_service import (
    ACTOR_REPARACION,
    QuestionFileService,
)
from opofuente.application.question_service import QuestionService
from opofuente.config import Settings, get_settings
from opofuente.domain.backup import DEFAULT_SCOPE
from opofuente.domain.errors import OpoFuenteError
from opofuente.domain.notes_incidents import PATRON_REFERENCIA_PEGADA, IncidentStatus
from opofuente.domain.notes_reports import normalise_note
from opofuente.domain.question_file import (
    REGLA_OPCION_FUNDIDA,
    REGLA_REFERENCIA_DEL_EXAMEN,
    Reparacion,
    motivo_de_no_reparar,
    reparacion_disponible,
)
from opofuente.infrastructure.clock import SystemClock
from opofuente.infrastructure.db import build_engine, build_session_factory
from opofuente.infrastructure.db_models import (
    NotesIncidentRecord,
    OptionVersionRecord,
    QuestionVersionRecord,
)
from opofuente.infrastructure.document_repository import SqlAlchemyDocumentRepository
from opofuente.infrastructure.notes_incident_repository import (
    SqlAlchemyNotesIncidentRepository,
)
from opofuente.infrastructure.question_file_repository import (
    SqlAlchemyQuestionFileRepository,
)
from opofuente.infrastructure.question_repository import SqlAlchemyQuestionRepository
from opofuente.infrastructure.representation_store import RepresentationStore

#: El motivo con el que se firma cada reparación. Va al `note` de la versión nueva y a la nota con
#: la
#: que se despacha la incidencia, y es lo que hace que las dos cosas se puedan leer juntas después.
MOTIVO = "reparación por regla mecánica del §2 (f20: referencia del examen y opciones fundidas)"

#: Lo mínimo que hay que contar para decidir: cuántas se repara y cuántas no, por qué regla y por
#: qué
#: motivo. El detalle largo va con `--detalle`.
DETALLE_POR_DEFECTO = 12


def _use_utf8_stdout() -> None:
    reconfigurar = getattr(sys.stdout, "reconfigure", None)
    if callable(reconfigurar):
        reconfigurar(encoding="utf-8")


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="opofuente.tools.reparar_preguntas",
        description="Repara por regla las preguntas que el §2 manda limpiar (F20).",
    )
    parser.add_argument(
        "--aplicar",
        action="store_true",
        help="escribe las reparaciones (copia verificada antes); sin esto solo lo enseña",
    )
    parser.add_argument(
        "--sin-copia",
        action="store_true",
        help="no hace copia antes de escribir: solo vale si ya se trabaja sobre una copia",
    )
    parser.add_argument(
        "--detalle",
        type=int,
        default=DETALLE_POR_DEFECTO,
        help=f"cuántas reparaciones se enseñan una a una (por defecto {DETALLE_POR_DEFECTO})",
    )
    parser.add_argument(
        "--solo",
        choices=(REGLA_REFERENCIA_DEL_EXAMEN, REGLA_OPCION_FUNDIDA),
        default=None,
        help="repara solo esta regla; sin esto, las dos",
    )
    return parser.parse_args(list(argv))


class _Candidata:
    """Una pregunta que hay que mirar: su identificador, su enunciado y sus opciones."""

    def __init__(
        self,
        *,
        question_version_id: str,
        stem: str,
        opciones: tuple[str, ...],
        tipo: str,
        en_bandeja: bool,
    ) -> None:
        self.question_version_id = question_version_id
        self.stem = stem
        self.opciones = opciones
        self.tipo = tipo
        #: `True` cuando además tiene una incidencia abierta de la bandeja del motor.
        self.en_bandeja = en_bandeja


def _candidatas(settings: Settings) -> tuple[_Candidata, ...]:
    """Las preguntas que hay que mirar: las señaladas por el motor y las que traen la referencia.

        Dos fuentes y una sola lista, sin duplicados: la bandeja del motor (las once «mal
        importadas»
    que el
        bloque del panel dejó escritas) y todas las preguntas cuyo enunciado todavía lleva la
        referencia
    del
        examen pegada (las veintiuna, que son las que hay que **limpiar**, no una incidencia). Una
    pregunta
        puede estar en las dos —la del JCL lo está— y se mira una vez.

        La referencia se busca recorriendo los enunciados en vez de con un `LIKE` sobre el año: el
        año
        aparece también en preguntas que hablan de un examen **en medio**, y quién decide qué es una
        referencia pegada es la guarda del dominio, que se prueba aparte.
    """
    engine = build_engine(settings.data_paths.database)
    try:
        with build_session_factory(engine)() as session:
            en_bandeja = {
                str(identificador)
                for identificador in session.execute(
                    select(NotesIncidentRecord.question_version_id).where(
                        NotesIncidentRecord.category == "pregunta_mal_importada"
                    )
                ).scalars()
            }
            vigentes = (
                session.execute(
                    select(QuestionVersionRecord).where(
                        QuestionVersionRecord.status != "superseded"
                    )
                )
                .scalars()
                .all()
            )
            mirar = {
                str(fila.id): fila
                for fila in vigentes
                if str(fila.id) in en_bandeja
                or PATRON_REFERENCIA_PEGADA.search(str(fila.stem) or "")
            }
            opciones: dict[str, list[str]] = {}
            if mirar:
                for pregunta_id, texto in session.execute(
                    select(OptionVersionRecord.question_version_id, OptionVersionRecord.text)
                    .where(OptionVersionRecord.question_version_id.in_(sorted(mirar)))
                    .order_by(OptionVersionRecord.question_version_id, OptionVersionRecord.position)
                ):
                    opciones.setdefault(str(pregunta_id), []).append(str(texto))
    finally:
        engine.dispose()
    return tuple(
        _Candidata(
            question_version_id=identificador,
            stem=str(fila.stem),
            opciones=tuple(opciones.get(identificador, ())),
            tipo=str(fila.question_type),
            en_bandeja=identificador in en_bandeja,
        )
        for identificador, fila in sorted(mirar.items())
    )


def main(argv: Sequence[str] | None = None) -> int:
    _use_utf8_stdout()
    args = parse_args(sys.argv[1:] if argv is None else argv)
    settings: Settings = get_settings()
    settings.data_paths.ensure_directories()
    engine = build_engine(settings.data_paths.database)
    try:
        session_factory = build_session_factory(engine)
        bandeja = NotesIncidentsService(
            SqlAlchemyNotesIncidentRepository(session_factory), clock=SystemClock()
        )
        servicio = QuestionFileService(
            questions=QuestionService(
                questions=SqlAlchemyQuestionRepository(session_factory),
                clock=SystemClock(),
                documents=SqlAlchemyDocumentRepository(
                    session_factory, RepresentationStore(settings.data_paths)
                ),
            ),
            files=SqlAlchemyQuestionFileRepository(session_factory),
            clock=SystemClock(),
        )

        candidatas = _candidatas(settings)
        reparables: list[tuple[_Candidata, Reparacion]] = []
        sin_reparacion: list[tuple[_Candidata, str]] = []
        for candidata in candidatas:
            reparacion = reparacion_disponible(
                stem=candidata.stem, opciones=candidata.opciones, tipo=candidata.tipo
            )
            if reparacion is None:
                continue
            if args.solo is not None and args.solo not in reparacion.reglas:
                continue
            reparables.append((candidata, reparacion))

        print(f"preguntas miradas: {len(candidatas)}")
        print(
            "  · de la bandeja del motor («mal importadas»): "
            f"{sum(1 for candidata in candidatas if candidata.en_bandeja)}"
        )
        con_referencia = sum(
            1 for candidata in candidatas if PATRON_REFERENCIA_PEGADA.search(candidata.stem)
        )
        print(f"  · con la referencia del examen pegada al enunciado: {con_referencia}")
        print(f"\n--- reparables por una regla: {len(reparables)} ---")
        por_regla: Counter[str] = Counter()
        for _candidata, reparacion in reparables:
            por_regla.update(reparacion.reglas)
        for regla, cuantas in por_regla.most_common():
            print(f"    {regla}: {cuantas}")
        for candidata, reparacion in reparables[: max(args.detalle, 0)]:
            reglas = "+".join(reparacion.reglas)
            print(f"    · {candidata.question_version_id} [{reglas}] {candidata.stem[:70]!r}")
            if reparacion.opciones is not None:
                print(f"      opciones nuevas: {list(reparacion.opciones)}")

        # Lo que se queda: las de la bandeja que ninguna regla repara, con su motivo agrupado. Es la
        # mitad del resultado y por eso sale siempre, aunque no se aplique nada.
        motivos: Counter[str] = Counter()
        for candidata in candidatas:
            if not candidata.en_bandeja:
                continue
            if any(candidata is elegida for elegida, _ in reparables):
                continue
            motivo = motivo_de_no_reparar(
                stem=candidata.stem, opciones=candidata.opciones, tipo=candidata.tipo
            )
            sin_reparacion.append((candidata, motivo or "no la toca ninguna regla"))
            motivos[motivo or "no la toca ninguna regla"] += 1
        print(f"\n--- de la bandeja, sin reparación posible: {len(sin_reparacion)} ---")
        for motivo, cuantas in motivos.most_common():
            print(f"    {cuantas:3d}  {motivo}")

        if not args.aplicar:
            print("\nENSAYO: no se ha escrito nada. Con --aplicar se hace.")
            return 0

        # --- la copia, antes de tocar la base ---
        if not args.sin_copia:
            servicio_copias = BackupService(
                paths=settings.data_paths,
                app_version="f20",
                clock=lambda: datetime.now(UTC),
                schema_revision=lambda: "0035_incidencias_despachables",
            )
            copia = servicio_copias.create(
                scope=DEFAULT_SCOPE,
                note="antes de reparar las preguntas del §2 (f20, ficha de pregunta)",
            )
            verificacion = servicio_copias.verify(copia.id)
            print(
                f"\ncopia de seguridad: {copia.id} · {copia.size_bytes} bytes · "
                f"verificada: {None if verificacion is None else verificacion.verified}"
            )
            if verificacion is None or not verificacion.verified:
                print("la copia NO verifica: no se escribe nada.", file=sys.stderr)
                return 1
        else:
            print("\n--sin-copia: se escribe sobre los datos que hay (solo vale sobre una copia).")

        reparadas = 0
        despachadas = 0
        movidos = Counter[str]()
        fallos: list[tuple[str, str]] = []
        for candidata, _reparacion in reparables:
            incidencias = servicio.incident_ids_of(candidata.question_version_id)
            try:
                resultado = servicio.repair(
                    candidata.question_version_id,
                    note=MOTIVO,
                    actor=ACTOR_REPARACION,
                )
            except OpoFuenteError as error:
                fallos.append((candidata.question_version_id, str(error)))
                continue
            # Las incidencias de la pregunta se despachan como resueltas **por la ruta auditada de
            # la bandeja** (la misma que usa el botón de la pantalla): una bandeja que siguiera
            # enseñando una pregunta ya reparada estaría mintiendo, y dejarla abierta apuntando a la
            # versión sustituida obligaría al propietario a cerrarla a mano una por una.
            for incidencia_id in incidencias:
                bandeja.update_incident(
                    incidencia_id,
                    status=IncidentStatus.REVIEWED,
                    note=normalise_note(
                        f"reparada: se escribió la versión {resultado.file.version_no} "
                        f"de la pregunta ({', '.join(resultado.reglas)})"
                    ),
                    actor=ACTOR_REPARACION,
                )
                despachadas += 1
            reparadas += 1
            movidos.update(
                {
                    "temas": resultado.moved_topics,
                    "anclas": resultado.moved_anchors,
                }
            )
            print(
                f"    reparada {candidata.question_version_id} → "
                f"{resultado.new_question_version_id} v{resultado.file.version_no} "
                f"[{'+'.join(resultado.reglas)}]"
            )
        print(
            f"\nreparadas: {reparadas} de {len(reparables)} · "
            f"temas movidos: {movidos['temas']} · anclas movidas: {movidos['anclas']} · "
            f"incidencias despachadas: {despachadas} · fallos: {len(fallos)}"
        )
        for identificador, motivo in fallos[:10]:
            print(f"    · FALLO {identificador}: {motivo}", file=sys.stderr)
        return 1 if fallos else 0
    except OpoFuenteError as error:
        print(f"No se ha podido reparar: {error}", file=sys.stderr)
        return 1
    finally:
        engine.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
