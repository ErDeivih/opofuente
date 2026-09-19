"""Baseline de rendimiento local: mide lo que el usuario nota, con números de verdad.

No es un banco de pruebas de laboratorio ni pretende serlo. Mide cinco operaciones sobre un corpus
**sintético** generado aquí mismo, para que una regresión futura se pueda comparar con algo y no con
una impresión.

Por qué estas cinco:

1. **copia de seguridad**: es la operación que más disco y tiempo mueve de golpe;
2. **restauración completa**: el camino más largo (validar, extraer, intercambiar, migrar);
3. **búsqueda léxica**: la interacción más repetida;
4. **rehacer el índice**: el que más crece con el corpus;
5. **foto de higiene**: recorre el almacén entero midiendo tamaños.

Se ejecuta a mano, no en las puertas: las puertas comprueban corrección, y un umbral de tiempo en CI
es la forma más rápida de tener una puerta que falla por el portátil y no por el código.

    uv run python -m opofuente.tools.benchmark --documents 200 --sessions 50
"""

from __future__ import annotations

import argparse
import shutil
import sys
import tempfile
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from opofuente.application.backup_service import BackupService
from opofuente.application.housekeeping_service import HousekeepingService
from opofuente.application.search_service import SearchRequest, SearchService
from opofuente.config import Settings
from opofuente.domain.rag import SearchFilters
from opofuente.infrastructure.artifact_store import ArtifactStore
from opofuente.infrastructure.db import build_engine, build_session_factory
from opofuente.infrastructure.housekeeping_repository import SqlAlchemyHousekeepingRepository
from opofuente.infrastructure.migrations import run_migrations, script_head
from opofuente.infrastructure.search_repository import SqlAlchemySearchRepository

AHORA = datetime(2026, 9, 19, 12, 0, tzinfo=UTC)


class _Reloj:
    """Reloj fijo: el baseline mide rendimiento, y una fecha que cambia no aporta nada aquí."""

    def now(self) -> datetime:
        return AHORA


@dataclass(frozen=True, slots=True)
class Measurement:
    """Una medida: qué se ha hecho, cuánto ha tardado y con qué tamaño de corpus."""

    name: str
    seconds: float
    detail: str


def _corpus(settings: Settings, *, documents: int) -> int:
    """Corpus sintético: documentos con sus fragmentos y sus citas.

    Se inserta con SQL directo porque lo que se mide es el rendimiento de las operaciones, no el
    de la importación (que ya tiene sus propias pruebas de tiempo en el bucle de la bandeja).
    """
    run_migrations(settings, revision="head")
    paths = settings.data_paths
    engine = build_engine(paths.database)
    fragmentos = 0
    try:
        with engine.begin() as conexion:
            for indice in range(documents):
                sha = f"{indice:064d}"
                artifact = f"art-{indice}"
                version = f"ver-{indice}"
                # Un fichero de verdad en el almacén: la copia lo va a leer.
                ruta = paths.artifacts / "sha256" / sha[:2] / sha[2:4] / sha
                ruta.parent.mkdir(parents=True, exist_ok=True)
                contenido = (f"Documento sintetico {indice}. " * 200).encode()
                ruta.write_bytes(contenido)
                conexion.exec_driver_sql(
                    "INSERT INTO source_artifacts (id, sha256, size_bytes, media_type, "
                    "storage_key, first_seen_at) VALUES (?, ?, ?, 'text/plain', ?, ?)",
                    (
                        artifact,
                        sha,
                        len(contenido),
                        f"sha256/{sha[:2]}/{sha[2:4]}/{sha}",
                        AHORA.isoformat(),
                    ),
                )
                conexion.exec_driver_sql(
                    "INSERT INTO artifact_origins (id, artifact_id, origin_type, display_location, "
                    "accessed_at) VALUES (?, ?, 'file', ?, ?)",
                    (f"ori-{indice}", artifact, f"carpeta/doc-{indice}.txt", AHORA.isoformat()),
                )
                conexion.exec_driver_sql(
                    "INSERT INTO extracted_representations (id, artifact_id, extractor_name, "
                    "extractor_version, kind, status, quality, char_count, created_at) VALUES "
                    "(?, ?, 'text', '1', 'plain_text', 'extracted', 'good', ?, ?)",
                    (f"rep-{indice}", artifact, len(contenido), AHORA.isoformat()),
                )
                conexion.exec_driver_sql(
                    "INSERT INTO logical_documents (id, canonical_title, document_type, "
                    "authority_tier, owner_scope, created_at, updated_at) VALUES "
                    "(?, ?, 'curriculum', 'A', 'private_user', ?, ?)",
                    (
                        f"doc-{indice}",
                        f"Tema sintetico {indice}",
                        AHORA.isoformat(),
                        AHORA.isoformat(),
                    ),
                )
                conexion.exec_driver_sql(
                    "INSERT INTO document_versions (id, logical_document_id, artifact_id, "
                    "representation_id, status, approved_at, language, created_at) VALUES "
                    "(?, ?, ?, ?, 'accepted', ?, 'es', ?)",
                    (
                        version,
                        f"doc-{indice}",
                        artifact,
                        f"rep-{indice}",
                        AHORA.isoformat(),
                        AHORA.isoformat(),
                    ),
                )
                for fragmento in range(5):
                    conexion.exec_driver_sql(
                        "INSERT INTO evidence_spans (id, document_version_id, ordinal, page, "
                        "citation_label, quality, index_status, text, normalized_text, created_at) "
                        "VALUES (?, ?, ?, ?, ?, 'good', 'indexed', ?, ?, ?)",
                        (
                            f"span-{indice}-{fragmento}",
                            version,
                            fragmento + 1,
                            fragmento + 1,
                            f"Tema {indice}, pag. {fragmento + 1}",
                            f"El plazo de alegaciones del procedimiento {indice} es de "
                            f"{fragmento + 10} dias habiles.",
                            f"el plazo de alegaciones del procedimiento {indice} es de "
                            f"{fragmento + 10} dias habiles.",
                            AHORA.isoformat(),
                        ),
                    )
                    fragmentos += 1
    finally:
        engine.dispose()
    return fragmentos


def _measure(name: str, accion: Callable[[], str]) -> Measurement:
    inicio = time.perf_counter()
    detalle = accion()
    return Measurement(name=name, seconds=time.perf_counter() - inicio, detail=detalle)


def run(*, documents: int) -> list[Measurement]:
    raiz = Path(tempfile.mkdtemp(prefix="opofuente-bench-"))
    settings = Settings(data_dir=raiz / "datos")
    settings.data_paths.ensure_directories()
    try:
        fragmentos = _corpus(settings, documents=documents)
        engine = build_engine(settings.data_paths.database)
        session_factory = build_session_factory(engine)
        busqueda = SearchService(
            search=SqlAlchemySearchRepository(session_factory),
            clock=_Reloj(),
        )
        copias = BackupService(
            paths=settings.data_paths,
            app_version="0.0.0-bench",
            clock=lambda: AHORA,
            schema_revision=lambda: script_head(settings) or "desconocida",
            migrate=lambda: run_migrations(settings, revision="head"),
        )
        higiene = HousekeepingService(
            paths=settings.data_paths,
            artifacts=ArtifactStore(settings.data_paths),
            repository=SqlAlchemyHousekeepingRepository(session_factory),
            clock=lambda: AHORA,
        )

        medidas: list[Measurement] = []
        estado: dict[str, str] = {}

        def hacer_copia() -> str:
            vista = copias.create(note="benchmark")
            estado["copia"] = vista.id
            return f"{vista.file_count} ficheros, {vista.size_bytes} bytes"

        medidas.append(_measure("copia de seguridad", hacer_copia))

        def restaurar() -> str:
            resultado = copias.restore(estado["copia"])
            salud = "ok" if resultado.health_ok else "fallo"
            return f"{len(resultado.restored)} entradas restauradas, salud={salud}"

        medidas.append(_measure("restauración completa", restaurar))

        def buscar() -> str:
            resultado = busqueda.search_only(
                SearchRequest(query="plazo de alegaciones", filters=_filtros())
            )
            return f"{len(resultado.hits)} fragmentos entregados de {resultado.total}"

        medidas.append(_measure("búsqueda léxica", buscar))

        medidas.append(
            _measure("rehacer el índice", lambda: f"{busqueda.rebuild()} fragmentos indexados")
        )
        medidas.append(
            _measure(
                "foto de higiene",
                lambda: (
                    f"{len(higiene.report().candidates)} candidatos, "
                    f"{higiene.report().total_bytes} bytes medidos"
                ),
            )
        )
        estado["fragmentos"] = str(fragmentos)
        engine.dispose()
        return medidas
    finally:
        shutil.rmtree(raiz, ignore_errors=True)


def _filtros() -> SearchFilters:
    return SearchFilters(limit=10)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Baseline de rendimiento local de OpoFuente")
    parser.add_argument(
        "--documents", type=int, default=200, help="documentos del corpus sintético"
    )
    parser.add_argument("--sessions", type=int, default=50, help="sesiones de estudio")
    argumentos = parser.parse_args(argv)

    medidas = run(documents=argumentos.documents)
    print(f"Corpus sintético: {argumentos.documents} documentos")
    print()
    for medida in medidas:
        print(f"{medida.name:>.26}: {medida.seconds:7.3f} s  ({medida.detail})")
    total = sum(medida.seconds for medida in medidas)
    print()
    print(f"{'total':>26}: {total:7.3f} s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
