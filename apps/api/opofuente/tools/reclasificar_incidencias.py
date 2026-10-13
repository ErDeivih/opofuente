"""Reclasifica la bandeja del motor: el §2 de `AJUSTES-AL-OBJETIVO-CLAVES-Y-RITMO-2026-10.md`.

El motor ponía la categoría `norma_cambiada` a **toda** pregunta con un hecho dudoso, **antes** de
mirar si la letra de los apuntes coincidía con la clave. De las 291 que lo decían, 23 no eran ni
incidencias y 146 eran de conjuntos con la clave en cuarentena. Esto las vuelve a clasificar con las
reglas del §2, **en su orden**, y saca de la bandeja lo que no era una incidencia.

Lo que hace, en orden:

1. **lee** la bandeja con lo que hace falta para decidir: la pregunta, sus opciones, la comprobación
   de los apuntes (letra, letras esperadas, desenlace y la frase que demuestra) y la fiabilidad de
   la
   clave de su conjunto;
2. **decide** con el dominio (`regla_de_mala_importacion`, `es_falso_positivo`,
   `categoria_reclasificada`): mecánica, sin modelo y sin red;
3. **escribe** por `SqlAlchemyNotesIncidentRepository.reclassify`, que deja un evento de auditoría
por
   incidencia en **una sola transacción** — y, si se pide, saca del temario las preguntas mal
   importadas que ninguna regla puede reparar, por el mismo camino auditado que usa el panel
   (`QuestionService.apply_topic_batch`, con `enunciado_roto`).

**Ensayo por defecto**: sin `--aplicar` no escribe nada. Con `--aplicar` hace **copia verificada**
antes de tocar la bandeja, salvo que se diga `--sin-copia`, que solo vale cuando ya se trabaja sobre
una copia de la base.

Uso:
    # ver qué haría (no escribe nada)
    uv run python -m opofuente.tools.reclasificar_incidencias
    # hacerlo, con copia verificada antes
    uv run python -m opofuente.tools.reclasificar_incidencias --aplicar
    # hacerlo además sacando del temario lo que no se puede reparar
    uv run python -m opofuente.tools.reclasificar_incidencias --aplicar --excluir-no-reparables

Códigos de salida: 0 bien · 1 fallo.
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from collections.abc import Sequence
from datetime import UTC, datetime

from opofuente.application.backup_service import BackupService
from opofuente.application.question_models import TopicAssignmentRequest
from opofuente.application.question_service import QuestionService
from opofuente.config import Settings, get_settings
from opofuente.domain.backup import DEFAULT_SCOPE
from opofuente.domain.errors import OpoFuenteError
from opofuente.domain.notes_incidents import (
    PATRON_REFERENCIA_PEGADA,
    REGLA_MENOS_DE_TRES_OPCIONES,
    Reclasificacion,
    categoria_reclasificada,
    detalle_reclasificado,
    es_falso_positivo,
    motivo_reclasificacion,
    regla_de_mala_importacion,
)
from opofuente.domain.topic_classification import OutOfSyllabus
from opofuente.infrastructure.clock import SystemClock
from opofuente.infrastructure.db import build_engine, build_session_factory
from opofuente.infrastructure.document_repository import SqlAlchemyDocumentRepository
from opofuente.infrastructure.notes_incident_repository import (
    IncidentEvidence,
    SqlAlchemyNotesIncidentRepository,
)
from opofuente.infrastructure.question_repository import SqlAlchemyQuestionRepository
from opofuente.infrastructure.representation_store import RepresentationStore

#: Quién firma esto en la auditoría. Se distingue de la máquina (`llm:deepseek-flash`) y de la
#: persona (`local`): es una decisión tomada con el documento de ajustes delante.
ACTOR = "f18:reclasificacion-incidencias"

#: Por qué se saca del temario una pregunta mal importada que ninguna regla puede reparar.
MOTIVO_EXCLUSION = (
    "la pregunta no se puede contestar: le faltan opciones y ninguna regla puede inventarse "
    "las que no están (reclasificación de incidencias, §2)"
)


def _use_utf8_stdout() -> None:
    reconfigurar = getattr(sys.stdout, "reconfigure", None)
    if callable(reconfigurar):
        reconfigurar(encoding="utf-8")


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="opofuente.tools.reclasificar_incidencias",
        description="Vuelve a clasificar las incidencias del motor (§2 del documento de ajustes).",
    )
    parser.add_argument(
        "--aplicar",
        action="store_true",
        help="escribe los cambios (copia verificada antes); sin esto solo lo enseña",
    )
    parser.add_argument(
        "--sin-copia",
        action="store_true",
        help="no hace copia antes de escribir: solo vale si ya se trabaja sobre una copia",
    )
    parser.add_argument(
        "--excluir-no-reparables",
        action="store_true",
        help=(
            "saca del temario, con `enunciado_roto`, las preguntas mal importadas que ninguna "
            "regla puede reparar (las que no llegan a tres opciones)"
        ),
    )
    parser.add_argument(
        "--detalle",
        type=int,
        default=12,
        help="cuántas incidencias se enseñan una a una (por defecto 12)",
    )
    return parser.parse_args(list(argv))


def _decidir(
    evidencia: IncidentEvidence, fiabilidad: dict[str, str], ahora: datetime
) -> tuple[Reclasificacion, str | None, str]:
    """La decisión para una incidencia: el cambio, la regla mecánica y el porqué.

    Devuelve también la regla mecánica (o `None`) porque el comando la necesita para dos cosas:
    sacar
    del temario las que no se pueden reparar y contar cuántas caen por cada regla.
    """
    regla = regla_de_mala_importacion(evidencia.opciones, evidencia.question_type)
    falso = es_falso_positivo(
        letra=evidencia.letra, esperadas=evidencia.esperadas, resultado=evidencia.resultado
    )
    destino = categoria_reclasificada(
        actual=evidencia.categoria,
        motivo=evidencia.motivo,
        regla_mal_importada=regla,
        conjunto_en_cuarentena=fiabilidad.get(evidencia.question_set_id) == "no_fiable",
        falso_positivo=falso,
        tiene_frase=evidencia.phrase is not None or evidencia.frase_del_ancla is not None,
    )
    # La frase que demuestra la contradicción: se copia a la incidencia solo si el motor la verificó
    # y
    # la incidencia no la tenía (el motor solo la guardaba para los conflictos de letra).
    frase = evidencia.frase_del_ancla if evidencia.phrase is None else None
    motivo = motivo_reclasificacion(
        destino,
        regla=regla,
        tiene_frase=evidencia.phrase is not None or evidencia.frase_del_ancla is not None,
    )
    return (
        Reclasificacion(
            incident_id=evidencia.incident_id,
            categoria=destino,
            detalle=detalle_reclasificado(
                motivo=motivo, regla=regla, detalle=evidencia.detalle, fecha=ahora
            ),
            phrase=frase,
        ),
        regla,
        motivo,
    )


def main(argv: Sequence[str] | None = None) -> int:
    _use_utf8_stdout()
    args = parse_args(sys.argv[1:] if argv is None else argv)
    settings: Settings = get_settings()
    settings.data_paths.ensure_directories()
    engine = build_engine(settings.data_paths.database)
    try:
        session_factory = build_session_factory(engine)
        incidencias = SqlAlchemyNotesIncidentRepository(session_factory)
        ahora = SystemClock().now()

        evidencias = incidencias.reclassification_evidence()
        fiabilidad = incidencias.key_reliability()
        print(f"incidencias en la bandeja: {len(evidencias)}")
        print(f"fiabilidad de las claves: {fiabilidad.fuente}")
        print(
            f"    conjuntos en cuarentena: {
                sum(1 for v in fiabilidad.por_conjunto.values() if v == 'no_fiable')
            }"
        )

        # --- la decisión, sin escribir nada ---
        cambios: list[Reclasificacion] = []
        motivos: dict[str, str] = {}
        reglas: dict[str, str | None] = {}
        por_categoria: Counter[str] = Counter()
        por_regla: Counter[str] = Counter()
        referencias_pegadas = 0
        for evidencia in evidencias:
            cambio, regla, motivo = _decidir(evidencia, fiabilidad.por_conjunto, ahora)
            clave = (
                cambio.categoria.value
                if cambio.categoria is not None
                else "(fuera: no era una incidencia)"
            )
            por_categoria[clave] += 1
            if regla is not None:
                por_regla[regla] += 1
            # La referencia del examen pegada al enunciado («2011 Universidad…») **no** es una mala
            # importación: se limpia. Se cuenta para poder decir cuántas quedan por limpiar, porque
            # limpiar un enunciado es escribir una versión nueva de la pregunta y eso no lo hace
            # este comando.
            if PATRON_REFERENCIA_PEGADA.search(evidencia.stem):
                referencias_pegadas += 1
            if evidencia.categoria is cambio.categoria and cambio.phrase is None:
                continue
            cambios.append(cambio)
            motivos[evidencia.incident_id] = motivo
            reglas[evidencia.incident_id] = regla

        print(f"\n--- la bandeja como queda ({len(evidencias)} incidencias) ---")
        for categoria, cuantas in por_categoria.most_common():
            print(f"    {categoria}: {cuantas}")
        print(f"\n--- cambios a escribir: {len(cambios)} ---")
        for cambio in cambios[: max(args.detalle, 0)]:
            destino = (
                cambio.categoria.value if cambio.categoria is not None else "(fuera de la bandeja)"
            )
            print(f"    · {destino}: {motivos[cambio.incident_id]}")
        if len(cambios) > args.detalle:
            print(f"    … y {len(cambios) - args.detalle} más")
        print("\n--- reglas mecánicas que han disparado ---")
        for regla, cuantas in por_regla.most_common():
            print(f"    {regla}: {cuantas}")
        print(
            f"\nenunciados con la referencia del examen pegada: {referencias_pegadas} "
            "(se limpian, no son incidencia; la limpieza no la hace este comando)"
        )

        # Las que ninguna regla puede reparar: no llegan a tres opciones.
        a_excluir = [
            evidencia
            for evidencia in evidencias
            if reglas.get(evidencia.incident_id) == REGLA_MENOS_DE_TRES_OPCIONES
        ]
        print(f"preguntas mal importadas que ninguna regla puede reparar: {len(a_excluir)}")

        if not args.aplicar:
            print("\nENSAYO: no se ha escrito nada. Con --aplicar se hace.")
            return 0

        # --- la copia, antes de tocar la bandeja ---
        if not args.sin_copia:
            servicio_copias = BackupService(
                paths=settings.data_paths,
                app_version="f18",
                clock=lambda: datetime.now(UTC),
                # La revisión se declara con la que este comando espera: no se migra nada, solo se
                # copia, y la copia tiene que decir sobre qué esquema se hizo.
                schema_revision=lambda: "0035_incidencias_despachables",
            )
            copia = servicio_copias.create(
                scope=DEFAULT_SCOPE,
                note="antes de reclasificar las incidencias del motor (§2, f18)",
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

        resumen = incidencias.reclassify(cambios, actor=ACTOR, now=ahora)
        print(
            f"reclasificadas: {resumen.actualizadas} · fuera de la bandeja: {resumen.retiradas} · "
            f"total: {resumen.total}"
        )

        # --- y las que no se pueden reparar, fuera del temario ------------------------------
        if args.excluir_no_reparables and a_excluir:
            servicio = QuestionService(
                questions=SqlAlchemyQuestionRepository(session_factory),
                clock=SystemClock(),
                documents=SqlAlchemyDocumentRepository(
                    session_factory, RepresentationStore(settings.data_paths)
                ),
            )
            lote = servicio.apply_topic_batch(
                [
                    TopicAssignmentRequest(
                        question_version_id=evidencia.question_version_id,
                        exclusion_reason=OutOfSyllabus.ENUNCIADO_ROTO,
                        reason=MOTIVO_EXCLUSION,
                        retire_others=True,
                    )
                    for evidencia in a_excluir
                ],
                actor=ACTOR,
            )
            desenlaces: Counter[str] = Counter()
            for resultado in lote.rows:
                desenlaces[resultado.outcome] += 1
            print(f"sacadas del temario (enunciado_roto): {dict(desenlaces)}")
            errores = [resultado for resultado in lote.rows if resultado.outcome == "error"]
            for resultado in errores[:10]:
                print(
                    f"    · ERROR {resultado.question_version_id}: {resultado.detail}",
                    file=sys.stderr,
                )
            if errores:
                return 1
        elif a_excluir:
            print(
                f"{len(a_excluir)} pregunta(s) sin reparar se quedan en el temario: "
                "se sacan con --excluir-no-reparables"
            )
        return 0
    except OpoFuenteError as error:
        print(f"No se ha podido reclasificar: {error}", file=sys.stderr)
        return 1
    finally:
        engine.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
