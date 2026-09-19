"""Servicio de higiene y diagnóstico: qué ocupa, qué sobra y qué se puede retirar (DEBT-007).

Tres decisiones que se ven en el código y conviene saber por qué:

1. **medir no es retirar**: `report()` no borra nada. Devuelve la foto (uso por área y
candidatos con
   su motivo y su tamaño) y son las rutas de retirada las que borran, una por una y con lo que se
   pidió. Un «limpiar todo» sin foto es exactamente lo que el contrato prohíbe;
2. **lo ilegible se dice**: un área que no se puede medir aparece como no legible, no como vacía;
3. **lo referenciado no se toca**: los artefactos huérfanos salen de una consulta que comprueba
todas
   las referencias, y la retirada vuelve a comprobarlas antes de borrar la fila.
"""

from __future__ import annotations

import shutil
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from opofuente.config import DataPaths
from opofuente.domain.housekeeping import (
    AreaUsage,
    HousekeepingAction,
    HousekeepingCandidate,
    HousekeepingReport,
    human_bytes,
    is_within,
)
from opofuente.infrastructure.artifact_store import ArtifactStore
from opofuente.infrastructure.housekeeping_repository import (
    SqlAlchemyHousekeepingRepository,
    candidate_for_artifact,
)

#: Días que se conserva un trabajo terminado antes de poder retirarlo. No es un número sagrado: es
#: el que deja ver «qué pasó ayer» sin acumular un histórico entero de la cola.
DEFAULT_RETENTION_DAYS = 30

#: Áreas del árbol de datos que se miden, con el nombre que se enseña. El orden es el de la
#: pantalla: primero lo que ocupa de verdad (material), luego lo que se puede reconstruir.
MEASURED_AREAS: tuple[tuple[str, str], ...] = (
    ("artifacts", "Material copiado (por contenido)"),
    ("extracted", "Texto extraído y representaciones"),
    ("backups", "Copias de seguridad"),
    ("exports", "Exportaciones generadas"),
    ("logs", "Registros"),
)


@dataclass(frozen=True, slots=True)
class PurgeResult:
    """Lo que una retirada ha hecho de verdad: cuántas cosas y cuántos bytes."""

    action: HousekeepingAction
    removed: int
    freed_bytes: int
    skipped: tuple[str, ...]
    detail: str


class HousekeepingService:
    """Mide el almacén, propone lo que sobra y lo retira cuando se lo piden."""

    def __init__(
        self,
        *,
        paths: DataPaths,
        artifacts: ArtifactStore,
        repository: SqlAlchemyHousekeepingRepository,
        clock: Callable[[], datetime],
        retention_days: int = DEFAULT_RETENTION_DAYS,
    ) -> None:
        self._paths = paths
        self._artifacts = artifacts
        self._repository = repository
        self._clock = clock
        self._retention_days = retention_days

    # ------------------------------------------------------------------ medir

    def report(self) -> HousekeepingReport:
        """Foto del almacén: uso por área y todo lo que se puede retirar, con su motivo."""
        ahora = self._clock()
        candidatos: list[HousekeepingCandidate] = []

        for identificador, storage_key in self._repository.orphan_artifacts():
            tamano = 0
            try:
                ruta = self._artifacts.path_for_key(storage_key)
                if ruta.is_file():
                    tamano = ruta.stat().st_size
            except OSError:
                tamano = 0
            candidatos.append(candidate_for_artifact(identificador, storage_key, tamano))

        candidatos.extend(self._stale_temps())
        candidatos.extend(self._old_jobs(ahora))

        return HousekeepingReport(
            usage=self._usage(),
            candidates=tuple(candidatos),
            retention_days=self._retention_days,
        )

    def _usage(self) -> tuple[AreaUsage, ...]:
        areas: list[AreaUsage] = []
        for nombre, etiqueta in MEASURED_AREAS:
            area = self._paths.root / nombre
            if not area.exists():
                areas.append(
                    AreaUsage(
                        area=nombre,
                        path_display=nombre,
                        size_bytes=0,
                        file_count=0,
                        note="no existe todavía",
                    )
                )
                continue
            try:
                total = 0
                ficheros = 0
                for ruta in area.rglob("*"):
                    if ruta.is_file():
                        total += ruta.stat().st_size
                        ficheros += 1
                areas.append(
                    AreaUsage(
                        area=nombre,
                        path_display=nombre,
                        size_bytes=total,
                        file_count=ficheros,
                        note=etiqueta,
                    )
                )
            except OSError as error:
                areas.append(
                    AreaUsage(
                        area=nombre,
                        path_display=nombre,
                        size_bytes=0,
                        file_count=0,
                        readable=False,
                        note=f"no se ha podido medir ({type(error).__name__})",
                    )
                )
        return tuple(areas)

    def _stale_temps(self) -> tuple[HousekeepingCandidate, ...]:
        """Restos de una operación interrumpida: `.part` sueltos y árboles de trabajo huérfanos.

        Solo se mira el árbol de temporales y **solo** dentro de él (`is_within`): retirar por
        una ruta
        construida sin comprobar es lo que el contrato prohíbe.
        """
        temporales = self._paths.tmp
        if not temporales.is_dir():
            return ()
        candidatos: list[HousekeepingCandidate] = []
        for ruta in sorted(temporales.iterdir()):
            if not is_within(self._paths.root, ruta):
                continue
            try:
                if ruta.is_dir():
                    tamano = sum(f.stat().st_size for f in ruta.rglob("*") if f.is_file())
                    candidatos.append(
                        HousekeepingCandidate(
                            action=HousekeepingAction.STALE_TEMP,
                            reference=ruta.name,
                            detail=(
                                "árbol de trabajo de una operación interrumpida: "
                                f"{human_bytes(tamano)}"
                            ),
                            size_bytes=tamano,
                            relative_path=f"tmp/{ruta.name}",
                        )
                    )
                elif ruta.name.endswith(".part"):
                    tamano = ruta.stat().st_size
                    candidatos.append(
                        HousekeepingCandidate(
                            action=HousekeepingAction.STALE_TEMP,
                            reference=ruta.name,
                            detail=(
                                f"fichero temporal de una copia interrumpida: {human_bytes(tamano)}"
                            ),
                            size_bytes=tamano,
                            relative_path=f"tmp/{ruta.name}",
                        )
                    )
            except OSError:
                continue
        return tuple(candidatos)

    def _old_jobs(self, ahora: datetime) -> tuple[HousekeepingCandidate, ...]:
        return tuple(
            HousekeepingCandidate(
                action=HousekeepingAction.OLD_JOB,
                reference=identificador,
                detail=(
                    f"trabajo en estado «{estado}» de hace más de {self._retention_days} días: "
                    "no se va a volver a ejecutar"
                ),
                size_bytes=0,
            )
            for identificador, estado in self._repository.old_jobs(
                older_than_days=self._retention_days, now=ahora
            )
        )

    # ------------------------------------------------------------------ retirar

    def purge_temps(self, *, references: tuple[str, ...] | None = None) -> PurgeResult:
        """Retira temporales, comprobando que cada ruta está **dentro** del árbol de datos."""
        candidatos = self._stale_temps()
        elegidos = (
            candidatos
            if references is None
            else tuple(c for c in candidatos if c.reference in set(references))
        )
        retirados = 0
        liberado = 0
        saltados: list[str] = []
        for candidato in elegidos:
            ruta = self._paths.root / (candidato.relative_path or "")
            if not ruta.exists():
                saltados.append(candidato.reference)
                continue
            if not is_within(self._paths.root, ruta):
                saltados.append(candidato.reference)
                continue
            try:
                if ruta.is_dir():
                    shutil.rmtree(ruta)
                else:
                    ruta.unlink()
            except OSError:
                saltados.append(candidato.reference)
                continue
            retirados += 1
            liberado += candidato.size_bytes
        return PurgeResult(
            action=HousekeepingAction.STALE_TEMP,
            removed=retirados,
            freed_bytes=liberado,
            skipped=tuple(saltados),
            detail=(
                f"{retirados} temporal(es) retirados y {human_bytes(liberado)} liberados"
                if retirados
                else "no había temporales que retirar"
            ),
        )

    def purge_orphan_artifacts(self, *, identifiers: tuple[str, ...] | None = None) -> PurgeResult:
        """Retira artefactos huérfanos: borra el fichero del almacén y después su fila.

        El orden importa y es al revés del que parece: primero el **fichero** y luego la fila. Si se
        borrara la fila primero y el borrado del fichero fallara, quedaría un fichero que nadie sabe
        que existe (basura invisible); al revés, lo peor que puede pasar es una fila sin
        fichero, que
        la comprobación de integridad **detecta y dice**.
        """
        candidatos = {
            candidato.reference: candidato
            for candidato in self.report().candidates
            if candidato.action is HousekeepingAction.ORPHAN_ARTIFACT
        }
        elegidos = (
            tuple(candidatos.values())
            if identifiers is None
            else tuple(c for clave, c in candidatos.items() if clave in set(identifiers))
        )
        retirados = 0
        liberado = 0
        saltados: list[str] = []
        for candidato in elegidos:
            ruta: Path | None = None
            if candidato.relative_path:
                try:
                    ruta = self._artifacts.path_for_key(candidato.relative_path)
                except OSError:
                    ruta = None
            tamano = candidato.size_bytes
            # Primero el fichero; si no se puede retirar, la fila **no** se toca.
            if ruta is not None and ruta.exists():
                try:
                    ruta.unlink()
                except OSError:
                    saltados.append(candidato.reference)
                    continue
            if self._repository.delete_artifacts((candidato.reference,)) == 0:
                # La fila ya no era huérfana (alguien la promocionó): se dice, no se esconde.
                saltados.append(candidato.reference)
                continue
            retirados += 1
            liberado += tamano
        return PurgeResult(
            action=HousekeepingAction.ORPHAN_ARTIFACT,
            removed=retirados,
            freed_bytes=liberado,
            skipped=tuple(saltados),
            detail=(
                f"{retirados} artefacto(s) sin uso retirados y {human_bytes(liberado)} liberados"
                if retirados
                else "no había artefactos sin uso que retirar"
            ),
        )

    def purge_old_jobs(self, *, identifiers: tuple[str, ...] | None = None) -> PurgeResult:
        """Retira trabajos terminados y antiguos. No borra ficheros: solo filas de la cola."""
        candidatos = {candidato.reference: candidato for candidato in self._old_jobs(self._clock())}
        elegidos = (
            tuple(candidatos)
            if identifiers is None
            else tuple(clave for clave in candidatos if clave in set(identifiers))
        )
        retirados = self._repository.delete_jobs(elegidos)
        return PurgeResult(
            action=HousekeepingAction.OLD_JOB,
            removed=retirados,
            freed_bytes=0,
            skipped=(),
            detail=(
                f"{retirados} trabajo(s) terminados y antiguos retirados del historial"
                if retirados
                else "no había trabajos que retirar"
            ),
        )


__all__ = [
    "DEFAULT_RETENTION_DAYS",
    "MEASURED_AREAS",
    "HousekeepingService",
    "PurgeResult",
]
