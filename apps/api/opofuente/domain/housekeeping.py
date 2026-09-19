"""Higiene del almacén: qué ocupa, qué sobra y qué se puede retirar sin romper nada (DEBT-007).

El almacén crece por diseño —cada copia de material es un artefacto por contenido— y hasta S12 no
había **ninguna** forma de mirarlo ni de retirar lo que ya no sostiene nada. Este módulo define las
dos preguntas que la aplicación tiene que poder contestar:

1. **¿qué hay?** uso por área del árbol de datos, con lo que no se puede calcular dicho como tal;
2. **¿qué sobra?** artefactos sin origen ni versión, temporales de una operación interrumpida y
   trabajos ya terminados que nadie va a volver a mirar.

Y una regla que es la razón de que esto no sea un `rm -rf` con interfaz: **nada se retira en seco.**
Todo lo que este módulo propone retirar se comprueba antes contra las referencias reales (orígenes,
versiones de documento, representaciones, evidencias) y, si algo está referenciado, no se
propone. Lo
que se propone retirar se dice con su motivo y su tamaño, y la retirada es cosa de quien lo pide.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path


class HousekeepingAction(StrEnum):
    """Las tres cosas que se pueden retirar, cada una con su comprobación."""

    ORPHAN_ARTIFACT = "orphan_artifact"
    """Fichero del almacén que no tiene ni origen, ni versión de documento, ni representación."""
    STALE_TEMP = "stale_temp"
    """Resto de una operación interrumpida (`.part`) o árbol de trabajo huérfano."""
    OLD_JOB = "old_job"
    """Trabajo en estado terminal, anterior al periodo de retención."""


@dataclass(frozen=True, slots=True)
class AreaUsage:
    """Lo que ocupa un área del árbol de datos, con su recuento de ficheros.

    `size_bytes` es `0` y `readable` es `False` cuando no se ha podido medir: un área ilegible se
    declara ilegible en lugar de aparecer como vacía, que sería una mentira cómoda.
    """

    area: str
    path_display: str
    size_bytes: int
    file_count: int
    readable: bool = True
    note: str | None = None


@dataclass(frozen=True, slots=True)
class HousekeepingCandidate:
    """Algo que se puede retirar, con lo necesario para decidirlo sin abrir nada más."""

    action: HousekeepingAction
    reference: str
    detail: str
    size_bytes: int
    #: Ruta relativa al árbol de datos para lo que vive en disco; vacío para lo que vive en la base.
    relative_path: str | None = None

    @property
    def display(self) -> str:
        return self.relative_path or self.reference


@dataclass(frozen=True, slots=True)
class HousekeepingReport:
    """Lo que hay y lo que sobra. Es la foto que se enseña antes de tocar nada."""

    usage: tuple[AreaUsage, ...]
    candidates: tuple[HousekeepingCandidate, ...]
    retention_days: int

    @property
    def total_bytes(self) -> int:
        return sum(area.size_bytes for area in self.usage)

    @property
    def reclaimable_bytes(self) -> int:
        return sum(candidato.size_bytes for candidato in self.candidates)

    def by_action(self, action: HousekeepingAction) -> tuple[HousekeepingCandidate, ...]:
        return tuple(candidato for candidato in self.candidates if candidato.action is action)


def human_bytes(value: int) -> str:
    """Tamaño legible. Se usa en los mensajes del servidor para no dar cifras crudas al usuario."""
    if value < 0:
        return "desconocido"
    unidades = ("B", "KiB", "MiB", "GiB", "TiB")
    tamano = float(value)
    for unidad in unidades:
        if tamano < 1024 or unidad == unidades[-1]:
            return f"{tamano:.0f} {unidad}" if unidad == "B" else f"{tamano:.1f} {unidad}"
        tamano /= 1024
    return f"{tamano:.1f} TiB"


def is_within(root: Path, candidate: Path) -> bool:
    """¿Está `candidate` dentro de `root`? La misma guarda que usa la restauración, aquí para poder
    retirar temporales sin tocar nada que no sea del árbol de datos."""
    try:
        objetivo = candidate.resolve()
        raiz = root.resolve()
    except OSError:
        return False
    return objetivo == raiz or raiz in objetivo.parents


__all__ = [
    "AreaUsage",
    "HousekeepingAction",
    "HousekeepingCandidate",
    "HousekeepingReport",
    "human_bytes",
    "is_within",
]
