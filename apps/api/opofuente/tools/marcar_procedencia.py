"""Marca de dónde sale cada conjunto que ya estaba en la base (`origin_scope`, D10).

**Qué hace y qué no.** Rellena hacia atrás la columna que añade la migración `0037`, **por la ruta
auditada** (`QuestionService.set_origin_scope`, la misma que usa la API y que deja su evento de
auditoría). No toca preguntas, claves, visibilidad ni ningún otro campo.

**Cómo decide, y por qué así.** La procedencia no está en ningún dato de la base: el material lo
reunió el propietario y los conjuntos se llaman como se llamaban los ficheros de los que salieron.
Lo único que se puede afirmar es lo que dice el **título**, así que la regla es esa y está escrita:

- lo que **es** un examen oficial de la Administración General del Estado —los del INAP y los de la
  Guardia Civil— es `age`;
- lo que nombra a **otra administración** (un ayuntamiento, una comunidad, una universidad, un
  parlamento autonómico) es `otra_administracion`, que es lo que lo deja fuera de un simulacro;
- **todo lo demás es `desconocida`**, y no es un cajón de sastre: es la respuesta honesta para el
  material del propietario cuya administración de origen no se puede afirmar. `desconocida` **no
  excluye de nada**, así que equivocarse por este lado no le quita material a nadie; decir `age` de
  un banco de origen dudoso sería afirmar lo que no se sabe.

**Ensayo por defecto.** Sin `--aplicar` no escribe nada y dice qué cambiaría, conjunto a conjunto.

Uso:
    uv run python -m opofuente.tools.marcar_procedencia
    uv run python -m opofuente.tools.marcar_procedencia --aplicar

Códigos de salida: 0 bien · 1 fallo.
"""

from __future__ import annotations

import argparse
import re
import sys
from collections.abc import Sequence

from opofuente.application.question_service import QuestionService
from opofuente.config import Settings, get_settings
from opofuente.domain.questions import OriginScope
from opofuente.infrastructure.clock import SystemClock
from opofuente.infrastructure.db import build_engine, build_session_factory
from opofuente.infrastructure.document_repository import SqlAlchemyDocumentRepository
from opofuente.infrastructure.question_repository import SqlAlchemyQuestionRepository
from opofuente.infrastructure.representation_store import RepresentationStore

#: Quién firma los cambios: el comando de esta tanda.
ACTOR = "f23:procedencia"

#: Reglas, en orden: la primera que casa decide. Cada una lleva su porqué, que va al informe y a la
#: auditoría, porque una clasificación sin motivo no se puede revisar.
REGLAS: tuple[tuple[str, str, str], ...] = (
    (
        r"(examen oficial INAP)|(Guardia Civil)",
        OriginScope.AGE.value,
        "es un examen oficial de la Administración General del Estado (INAP o Guardia Civil)",
    ),
    (
        r"examen completo, con su plantilla",
        OriginScope.AGE.value,
        "es un examen del INAP guardado como banco privado; su enunciado lo dice",
    ),
    (
        r"TAI_ejer_\w+_(libre|promo)_AGE_\d{4}",
        OriginScope.AGE.value,
        "el nombre del material declara que es un ejercicio de la AGE",
    ),
    (
        r"Ajuntament|Ayuntamiento|Concello|Deputaci|Diputaci|Cabildo|Comarca",
        OriginScope.OTRA_ADMINISTRACION.value,
        "es de una administración local",
    ),
    (
        r"Comunidad (de|Foral)|Junta de|Xunta de|Generalitat|Govern de|Parlamento de|"
        r"Cortes de|Principado de|Region de Murcia|Región de Murcia",
        OriginScope.OTRA_ADMINISTRACION.value,
        "es de una comunidad autónoma o de un parlamento autonómico",
    ),
    (
        r"Universidad|Universitat|UCA |UPNA|UCM|UGR",
        OriginScope.OTRA_ADMINISTRACION.value,
        "es de una universidad",
    ),
    (
        r"examenes-otras-administraciones",
        OriginScope.OTRA_ADMINISTRACION.value,
        "el material está guardado en la carpeta de exámenes de otras administraciones",
    ),
)

#: La regla por defecto, con su motivo.
POR_DEFECTO = (
    OriginScope.DESCONOCIDA.value,
    "el título no dice de qué administración sale: no se afirma lo que no se sabe",
)


def clasificar(titulo: str, set_type: str) -> tuple[str, str]:
    """De qué administración sale un conjunto, por su título y su tipo. Puro y comprobable."""
    if set_type == "official_exam" and "Guardia Civil" not in titulo:
        return OriginScope.AGE.value, "es un examen oficial del INAP"
    if set_type == "official_exam":
        return OriginScope.AGE.value, "es un examen oficial de la Guardia Civil (AGE)"
    for patron, ambito, motivo in REGLAS:
        if re.search(patron, titulo):
            return ambito, motivo
    return POR_DEFECTO


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Marca la procedencia de los conjuntos (D10).")
    parser.add_argument(
        "--aplicar", action="store_true", help="escribe de verdad (sin esto, solo dice qué haría)"
    )
    return parser.parse_args(list(argv))


def _use_utf8_stdout() -> None:
    for flujo in (sys.stdout, sys.stderr):
        reconfigure = getattr(flujo, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")


def main(argv: Sequence[str] | None = None) -> int:
    _use_utf8_stdout()
    args = parse_args(sys.argv[1:] if argv is None else argv)
    settings: Settings = get_settings()
    settings.data_paths.ensure_directories()
    engine = build_engine(settings.data_paths.database)
    try:
        session_factory = build_session_factory(engine)
        servicio = QuestionService(
            questions=SqlAlchemyQuestionRepository(session_factory),
            clock=SystemClock(),
            documents=SqlAlchemyDocumentRepository(
                session_factory, RepresentationStore(settings.data_paths)
            ),
        )
        paginas = servicio.sets(limit=1000)
        resumen: dict[str, int] = {}
        cambios = 0
        for vista in paginas.sets:
            ambito, motivo = clasificar(str(vista.title), str(vista.set_type))
            resumen[f"{ambito} → {motivo}"] = resumen.get(f"{ambito} → {motivo}", 0) + 1
            if str(vista.origin_scope) == ambito:
                continue
            cambios += 1
            print(
                f"  {vista.origin_scope:18s} → {ambito:18s} [{vista.set_type:14s}] "
                f"{str(vista.title)[:70]}"
            )
            print(f"      {motivo}")
            if args.aplicar:
                servicio.set_origin_scope(vista.id, ambito, actor=ACTOR)
        print("=" * 100)
        print(f"conjuntos: {paginas.total} · cambios: {cambios}")
        for etiqueta, cuantos in sorted(resumen.items(), key=lambda par: -par[1]):
            print(f"  {cuantos:5d}  {etiqueta}")
        if not args.aplicar:
            print("(ensayo: no se ha escrito nada; con --aplicar se aplica)")
        return 0
    finally:
        engine.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
