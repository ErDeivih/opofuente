"""Construye una base SQLite de demostración, pequeña y sin material de terceros restringido.

Se usa para desplegar una *demo* pública sin tocar el corpus real del propietario. La base se
genera desde los fixtures del repositorio, no desde `data/`:

- siembra **solo el perfil TAI AGE 2025** (BOE, reutilizable con su cita) y deja fuera los perfiles
  de Guardia Civil y Celador, cuyo uso es privado (DEBT-003);
- siembra el **temario común C1** (5 bloques / 40 temas) y las convocatorias C1 que lo referencian;
- crea un conjunto de preguntas **sintético**: una pregunta por tema del temario común, generada a
  partir de los títulos del propio fixture, con su clave activa. No copia ni inventa contenido
  doctrinal: es un banco de demostración para que la pantalla del banco de preguntas se pueda ver.

La base resultante es la que el Dockerfile empaqueta en la imagen. El contenedor la copia a su
volumen efímero al arrancar si no existe.

Uso:
    uv run python -m opofuente.tools.build_demo_database --out data/demo/opofuente-demo.sqlite3
"""

from __future__ import annotations

import argparse
import json
import shutil
import sqlite3
import sys
from collections.abc import Sequence
from pathlib import Path

from sqlalchemy import text

from opofuente.application.convocatorias_service import ConvocatoriasService
from opofuente.application.curriculum_service import CurriculaService
from opofuente.application.profiles_service import ProfilesService
from opofuente.application.question_service import QuestionService
from opofuente.config import Settings, project_root
from opofuente.infrastructure.clock import SystemClock
from opofuente.infrastructure.convocatorias_fixture_loader import (
    C1_CONVOCATORIAS_FIXTURE,
    load_c1_convocatorias,
)
from opofuente.infrastructure.convocatorias_repository import SqlAlchemyConvocatoriasRepository
from opofuente.infrastructure.curriculum_fixture_loader import (
    COMMON_CURRICULUM_FIXTURE,
    load_common_curriculum,
)
from opofuente.infrastructure.curriculum_repository import SqlAlchemyCurriculumRepository
from opofuente.infrastructure.db import build_engine, build_session_factory
from opofuente.infrastructure.document_repository import SqlAlchemyDocumentRepository
from opofuente.infrastructure.fixture_loader import load_profiles
from opofuente.infrastructure.migrations import run_migrations
from opofuente.infrastructure.profile_repository import SqlAlchemyProfileRepository
from opofuente.infrastructure.question_repository import SqlAlchemyQuestionRepository
from opofuente.infrastructure.representation_store import RepresentationStore

#: Perfil que sí se publica en la demo: temario del BOE, reutilizable citando la fuente.
DEMO_PROFILE_CODE = "tai-age"

#: Conjunto de preguntas de la demo (el título lo dice para que nadie lo confunda con un examen).
DEMO_SET_TITLE = "Banco de demostración (datos sintéticos)"

DEMO_DB_NAME = "opofuente-demo.sqlite3"


def _demo_csv(curriculum_json: Path) -> str:
    """Una pregunta por tema del temario común, con su bloque como respuesta correcta.

    No es contenido doctrinal: es una pregunta de demostración generada del propio fixture, para
    que el banco tenga filas y el mapeo pregunta→tema se pueda ver. La respuesta correcta rota de
    posición para que la plantilla no sea trivial.
    """
    data = json.loads(curriculum_json.read_text(encoding="utf-8"))
    blocks = [node for node in data["nodes"] if node["node_type"] == "block"]
    if len(blocks) != 5:
        raise RuntimeError(f"el fixture del temario debería tener 5 bloques, tiene {len(blocks)}")
    labels = [f"Bloque {block['path']}" for block in blocks]
    lines = ["stem;option_a;option_b;option_c;option_d;correct;explanation;topic"]
    for block in blocks:
        for topic in block.get("children", []):
            if topic["node_type"] != "topic":
                continue
            distractores = [label for label in labels if label != f"Bloque {block['path']}"]
            correcta = f"Bloque {block['path']}"
            posicion = int(topic["official_code"]) % 4
            opciones = distractores[:3]
            opciones.insert(posicion, correcta)
            letra = chr(ord("a") + posicion)
            title = str(topic["title"]).replace(";", ",").replace('"', "")
            stem = f"Demostración: ¿a qué bloque del temario común pertenece el tema «{title}»?"
            explanation = (
                f"El tema {topic['path']} del temario común está en el bloque {block['path']}."
            )
            lines.append(";".join([stem, *opciones, letra, explanation, topic["path"]]))
    return "\n".join(lines) + "\n"


def build_demo_database(*, out: Path, workdir: Path) -> dict[str, int]:
    """Genera la base de demo y devuelve los recuentos que se pueden comprobar en el log."""
    if workdir.exists():
        shutil.rmtree(workdir)
    workdir.mkdir(parents=True)

    settings = Settings(data_dir=workdir)
    settings.data_paths.ensure_directories()
    run_migrations(settings, revision="head")

    root = project_root()
    engine = build_engine(settings.data_paths.database)
    try:
        sessions = build_session_factory(engine)
        perfiles = [
            profile
            for profile in load_profiles(root / "fixtures" / "profiles")
            if profile.opposition.code == DEMO_PROFILE_CODE
        ]
        if len(perfiles) != 1:
            raise RuntimeError(
                f"se esperaba un único perfil {DEMO_PROFILE_CODE}, hay {len(perfiles)}"
            )
        ProfilesService(SqlAlchemyProfileRepository(sessions), SystemClock()).seed(perfiles)
        CurriculaService(SqlAlchemyCurriculumRepository(sessions), SystemClock()).seed(
            load_common_curriculum(root / COMMON_CURRICULUM_FIXTURE)
        )
        ConvocatoriasService(SqlAlchemyConvocatoriasRepository(sessions), SystemClock()).seed(
            load_c1_convocatorias(root / C1_CONVOCATORIAS_FIXTURE)
        )

        with sessions() as session:
            opposition_id = session.execute(
                text("SELECT id FROM oppositions WHERE code = :code"),
                {"code": DEMO_PROFILE_CODE},
            ).scalar_one()

        repositorio = SqlAlchemyQuestionRepository(sessions)
        servicio = QuestionService(
            repositorio,
            SystemClock(),
            SqlAlchemyDocumentRepository(sessions, RepresentationStore(settings.data_paths)),
        )
        conjunto = servicio.create_set(
            DEMO_SET_TITLE,
            opposition_id=opposition_id,
            set_type="private_bank",
            model_code="A",
        )
        informe = servicio.import_from_csv(conjunto.id, _demo_csv(root / COMMON_CURRICULUM_FIXTURE))
        claves = servicio.keys(conjunto.id)
        if not claves:
            raise RuntimeError("la importación de demostración no creó ninguna clave")
        servicio.activate_key(claves[0].id)
        # Un banco de demo que se queda en «borrador» da la impresión de estar a medias; se
        # confirma en el propio fixture de demostración (no es una decisión sobre datos reales).
        repositorio.set_status(conjunto.id, "confirmed", now=SystemClock().now(), actor="demo")
    finally:
        engine.dispose()

    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        out.unlink()
    origen = sqlite3.connect(settings.data_paths.database)
    destino = sqlite3.connect(out)
    try:
        origen.backup(destino)
    finally:
        destino.close()
        origen.close()

    comprobacion = sqlite3.connect(out)
    try:

        def cuenta(sql: str) -> int:
            return int(comprobacion.execute(sql).fetchone()[0])

        counts = {
            "curriculum_nodes": cuenta("SELECT count(*) FROM curriculum_nodes"),
            "question_sets": cuenta("SELECT count(*) FROM question_sets"),
            "questions": cuenta("SELECT count(*) FROM question_versions"),
            "answer_keys": cuenta("SELECT count(*) FROM answer_key_entries"),
            "imported": int(informe.created),
        }
    finally:
        comprobacion.close()

    shutil.rmtree(workdir, ignore_errors=True)
    return counts


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        type=Path,
        default=project_root() / "data" / "demo" / DEMO_DB_NAME,
        help="fichero SQLite de salida",
    )
    parser.add_argument(
        "--workdir",
        type=Path,
        default=project_root() / ".demo-tmp",
        help="directorio de trabajo temporal (se borra al terminar)",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)
    counts = build_demo_database(out=args.out, workdir=args.workdir)
    print(json.dumps({"out": str(args.out), **counts}, ensure_ascii=False))
    if counts["curriculum_nodes"] < 45 or counts["questions"] < 40:
        print("La base de demo no tiene el temario y las preguntas esperadas.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
