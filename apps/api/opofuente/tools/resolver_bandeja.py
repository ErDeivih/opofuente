"""Resuelve solo lo que no necesita criterio y deja el resto listo para decidir en bloque (F31).

El §3 del cierre del objetivo, en un comando. La bandeja del motor tenía **868 incidencias abiertas
en 150 conjuntos**, y una parte grande de eso no es una pregunta para el propietario: es lo que una
regla puede cerrar sola. Lo que hace, en el orden que manda el documento:

1. **reclasifica** con las reglas del §2 de `AJUSTES-AL-OBJETIVO-CLAVES-Y-RITMO-2026-10.md` —las
   mismas del comando de F18, sin reescribirlas—, para que la etiqueta diga quién arregla cada cosa;
2. **resuelve** lo que no necesita criterio (`domain.notes_incidents.estado_resuelto`):
   - un **falso positivo** sale marcado `dismissed`. No se borra: el motor vuelve a comprobar los
     temas y un falso positivo ya descartado **no puede volver a entrar**;
   - una **pregunta mal importada** se va a `no_son_preguntas`: lo decidió una regla mecánica;
   - una incidencia con **clave derivada** —apuntes con cita y una respuesta independiente del
     coincidiendo en otra letra— pasa a `propuesta_lista`, que es lo que el propietario aprueba en
     bloque desde la bandeja;
3. **no toca una clave oficial**: una propuesta de un conjunto protegido no se propone siquiera. La
   clave de un examen oficial la decide el propietario y nadie más;
4. **cuenta la cifra**, en la base: cuántas entradas dependen de verdad de su criterio antes y
   después.

Todo lo que decide es **puro y sin modelo**: se puede volver a ejecutar sin gastar nada, y volver a
ejecutarlo **no cambia nada** (la segunda pasada no encuentra nada que resolver).

Uso:
    # ver qué haría (no escribe nada)
    uv run python -m opofuente.tools.resolver_bandeja
    # hacerlo, con copia verificada antes
    uv run python -m opofuente.tools.resolver_bandeja --aplicar

Códigos de salida: 0 bien · 1 fallo.
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from collections.abc import Sequence
from datetime import UTC, datetime

from opofuente.application.backup_service import BackupService
from opofuente.config import Settings, get_settings
from opofuente.domain.backup import DEFAULT_SCOPE
from opofuente.domain.errors import OpoFuenteError
from opofuente.domain.notes_incidents import (
    PATRON_REFERENCIA_PEGADA,
    Reclasificacion,
    ResolucionDeBandeja,
    categoria_reclasificada,
    detalle_reclasificado,
    es_falso_positivo,
    estado_resuelto,
    motivo_reclasificacion,
    regla_de_mala_importacion,
)
from opofuente.domain.topic_notes import CategoriaIncidencia
from opofuente.domain.tray import TraySet, agrupar
from opofuente.infrastructure.clock import SystemClock
from opofuente.infrastructure.db import build_engine, build_session_factory
from opofuente.infrastructure.notes_incident_repository import (
    IncidentEvidence,
    IncidentProposal,
    SqlAlchemyNotesIncidentRepository,
)

#: Quién firma esto en la auditoría. Es una decisión tomada con el documento delante, no la persona
#: ni la máquina, y por eso tiene su propio actor.
ACTOR = "f31:resolucion-de-bandeja"

#: La nota que deja la resolución en cada caso: una línea que explica qué regla la tocó.
NOTA_FALSO_POSITIVO = (
    "no era una incidencia: la letra de los apuntes está en la clave, así que no hay nada que "
    "decidir; queda descartada y no vuelve a entrar"
)
NOTA_MAL_IMPORTADA = (
    "la pregunta está mal importada y lo decidió una regla mecánica: va a «No son preguntas» sin "
    "pasar por el propietario"
)
NOTA_PROPUESTA = (
    "hay clave derivada: los apuntes con cita y una respuesta independiente del modelo coinciden "
    "otra letra. Se aprueba en bloque desde la bandeja del conjunto"
)


def _use_utf8_stdout() -> None:
    reconfigurar = getattr(sys.stdout, "reconfigure", None)
    if callable(reconfigurar):
        reconfigurar(encoding="utf-8")


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="opofuente.tools.resolver_bandeja",
        description="Resuelve lo que no necesita criterio y propone lo que se aprueba en bloque.",
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
        "--detalle",
        type=int,
        default=10,
        help="cuántas incidencias se enseñan una a una (por defecto 10)",
    )
    return parser.parse_args(list(argv))


def _protegidos(repositorio: SqlAlchemyNotesIncidentRepository) -> dict[str, TraySet]:
    """Los conjuntos de la bandeja, por identificador, para saber cuáles son oficiales."""
    return {fila.set_id: fila for fila in repositorio.tray_sets()}


def _propuestas_utiles(
    propuestas: Sequence[IncidentProposal], conjuntos: dict[str, TraySet]
) -> dict[str, IncidentProposal]:
    """Las propuestas que se pueden proponer: las de un conjunto que **no** está protegido.

    No es un filtro de adorno: proponer una clave para un examen oficial sería ofrecer un botón que
    la ruta va a rechazar, y la bandeja no ofrece lo que no se puede hacer.
    """
    utiles: dict[str, IncidentProposal] = {}
    for propuesta in propuestas:
        conjunto = conjuntos.get(propuesta.set_id)
        if conjunto is None or conjunto.es_oficial:
            continue
        utiles[propuesta.incident_id] = propuesta
    return utiles


def _decidir(
    evidencia: IncidentEvidence,
    *,
    fiabilidad: dict[str, str],
    tiene_propuesta: bool,
    ahora: datetime,
) -> tuple[Reclasificacion, ResolucionDeBandeja | None, str | None]:
    """La decisión para una incidencia: la categoría nueva y el estado que deja una regla.

    Devuelve también la regla mecánica que disparó, si la hubo, para poder contarla en el informe.
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
    frase = evidencia.frase_del_ancla if evidencia.phrase is None else None
    motivo = motivo_reclasificacion(
        destino,
        regla=regla,
        tiene_frase=evidencia.phrase is not None or evidencia.frase_del_ancla is not None,
    )
    reetiquetado = Reclasificacion(
        incident_id=evidencia.incident_id,
        categoria=destino,
        detalle=detalle_reclasificado(
            motivo=motivo, regla=regla, detalle=evidencia.detalle, fecha=ahora
        ),
        phrase=frase,
    )
    estado = estado_resuelto(categoria=destino, tiene_propuesta=tiene_propuesta)
    if estado is None:
        return reetiquetado, None, regla
    if destino is None:
        nota = NOTA_FALSO_POSITIVO
    elif destino is CategoriaIncidencia.PREGUNTA_MAL_IMPORTADA:
        nota = NOTA_MAL_IMPORTADA
    else:
        nota = NOTA_PROPUESTA
    return (
        reetiquetado,
        ResolucionDeBandeja(
            incident_id=evidencia.incident_id,
            status=estado,
            note=nota,
        ),
        regla,
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
        fiabilidad = incidencias.key_reliability().por_conjunto
        conjuntos = _protegidos(incidencias)
        propuestas = _propuestas_utiles(incidencias.proposals(), conjuntos)

        antes = agrupar(list(conjuntos.values()))
        print(f"incidencias en la bandeja: {len(evidencias)}")
        print(f"conjuntos con algo pendiente: {antes.filas}")
        print(
            "ENTRADAS DE DECISIÓN REAL (antes): "
            f"{antes.entradas_de_decision}  ·  propuestas: {len(propuestas)}"
        )

        reetiquetados: list[Reclasificacion] = []
        resoluciones: list[ResolucionDeBandeja] = []
        por_estado: Counter[str] = Counter()
        por_regla: Counter[str] = Counter()
        referencias_pegadas = 0
        for evidencia in evidencias:
            cambio, resolucion, regla = _decidir(
                evidencia,
                fiabilidad=fiabilidad,
                tiene_propuesta=evidencia.incident_id in propuestas,
                ahora=ahora,
            )
            if regla is not None:
                por_regla[regla] += 1
            if PATRON_REFERENCIA_PEGADA.search(evidencia.stem):
                referencias_pegadas += 1
            if cambio.categoria is not None and (
                evidencia.categoria is not cambio.categoria or cambio.phrase is not None
            ):
                # Un falso positivo **no** entra aquí: `reclassify` borra la fila cuando la
                # categoría es nula, y lo que hay que hacer con un falso positivo es descartarlo
                # —dejando la fila— para que el motor no lo traiga otra vez.
                reetiquetados.append(cambio)
            if resolucion is not None:
                resoluciones.append(resolucion)
                por_estado[resolucion.status.value] += 1

        print("\n--- lo que la resolución deja hecho ---")
        for estado, cuantas in por_estado.most_common():
            print(f"    {estado}: {cuantas}")
        print(f"    (sin tocar, esperando criterio: {len(evidencias) - len(resoluciones)})")
        print("\n--- reglas mecánicas que han disparado ---")
        for regla, cuantas in por_regla.most_common():
            print(f"    {regla}: {cuantas}")
        print(
            f"\nenunciados con la referencia del examen pegada: {referencias_pegadas} "
            "(se limpian, no son incidencia)"
        )
        print(f"\n--- reetiquetados: {len(reetiquetados)} ---")
        for cambio in reetiquetados[: max(args.detalle, 0)]:
            destino = (
                cambio.categoria.value if cambio.categoria is not None else "(fuera de la bandeja)"
            )
            print(f"    · {destino}")
        if len(reetiquetados) > args.detalle:
            print(f"    … y {len(reetiquetados) - args.detalle} más")

        if not args.aplicar:
            print("\nENSAYO: no se ha escrito nada. Con --aplicar se hace.")
            return 0

        if not args.sin_copia:
            servicio_copias = BackupService(
                paths=settings.data_paths,
                app_version="f31",
                clock=lambda: datetime.now(UTC),
                schema_revision=lambda: "0039_bandeja_por_conjunto",
            )
            copia = servicio_copias.create(
                scope=DEFAULT_SCOPE,
                note="antes de resolver la bandeja por regla y proponer en bloque (F31)",
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

        if reetiquetados:
            resumen_reclasificacion = incidencias.reclassify(reetiquetados, actor=ACTOR, now=ahora)
            print(
                f"reclasificadas: {resumen_reclasificacion.actualizadas} · "
                f"fuera de la bandeja: {resumen_reclasificacion.retiradas}"
            )
        if resoluciones:
            resumen = incidencias.resolve_by_rule(resoluciones, actor=ACTOR, now=ahora)
            print(
                f"resueltas por regla: {resumen.actualizadas} · "
                f"descartadas (falsos positivos): {resumen.retiradas}"
            )

        # La cifra, contada otra vez en la base: la de antes no se hereda.
        despues = agrupar(list(incidencias.tray_sets()))
        print(
            "\nENTRADAS DE DECISIÓN REAL (después): "
            f"{despues.entradas_de_decision}  ·  conjuntos: {despues.filas}  ·  "
            f"propuestas: {despues.propuestas}"
        )
        return 0
    except OpoFuenteError as error:
        print(f"No se ha podido resolver la bandeja: {error}", file=sys.stderr)
        return 1
    finally:
        engine.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
