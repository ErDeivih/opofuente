"""Cambios e invalidación selectiva (S11; RF-09 y la demo D de `16_TRACEABILITY`).

Tres reglas, y la tercera es la que más importa:

1. **un cambio se propone, no se aplica**: cuando aparece una versión nueva se calcula el diff por
   sección y **qué depende de lo que cambió**, y no se toca nada hasta que una persona confirma
   (`07_UI-UX` §10). Esa propuesta **es** la simulación del cambio normativo: se puede mirar entera,
   con sus derivados afectados, sin ninguna consecuencia;
2. **solo se invalida lo que depende de lo que cambió**: un derivado se marca `needs_review` si
   alguno de sus insumos está en una sección que cambió o se quitó. Si solo depende de secciones
   intactas, **no se toca**. La dependencia son aristas escritas al crear el derivado, no una
   semejanza que alguien calcule después (§8: «no se infieren después»);
3. **la aplicación no interpreta el efecto jurídico**: describe qué texto cambió y qué depende de
   él, y dice expresamente que no decide si una norma sigue vigente, si algo deja de ser válido ni
   qué hay que hacer con el material. Eso lo decide una persona (RF-09).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum

from opofuente.domain.errors import InvalidStateError

# --- vocabularios (los mismos que la migración 0020) ---------------------------------------------


class ChangeStatus(StrEnum):
    """Estado de un conjunto de cambios: propuesto, confirmado o descartado."""

    PROPOSED = "proposed"
    CONFIRMED = "confirmed"
    DISCARDED = "discarded"


class SectionChangeKind(StrEnum):
    """Qué le pasó a una sección entre dos versiones (el vocabulario del diff de S05)."""

    ADDED = "added"
    REMOVED = "removed"
    CHANGED = "changed"
    UNCHANGED = "unchanged"


class ArtifactKind(StrEnum):
    """Qué tipo de derivado es. Hoy solo se generan resúmenes extractivos."""

    SUMMARY = "summary"


class ArtifactReview(StrEnum):
    """Estado de revisión de un derivado."""

    PENDING = "pending"
    REVIEWED = "reviewed"
    DISCARDED = "discarded"


class EdgeSource(StrEnum):
    """De qué depende algo: lo que puede cambiar."""

    DOCUMENT_VERSION = "document_version"
    DOCUMENT_SECTION = "document_section"
    EVIDENCE_SPAN = "evidence_span"


class EdgeTarget(StrEnum):
    """Qué depende: lo que hay que revisar cuando su fuente cambia."""

    DERIVED_ARTIFACT = "derived_artifact"
    QUESTION_VERSION = "question_version"
    RAG_ANSWER = "rag_answer"


# --- lo que dice la aplicación del efecto de un cambio -------------------------------------------

#: Lo que OpoFuente **no** decide. Viaja en cada conjunto de cambios y se enseña antes de confirmar:
#: describir un cambio de texto no es interpretar una norma, y confundirlas sería lo peligroso.
LEGAL_EFFECT_NOTE = (
    "OpoFuente describe qué texto cambió y qué depende de él. No decide si una norma sigue "
    "vigente, si algo deja de ser válido ni qué hay que hacer con el material: eso lo decide una "
    "persona."
)

#: Lo que se puede hacer con un derivado marcado, dicho en una frase (para la interfaz).
REVIEW_ACTIONS = (
    "«sigue valiendo» deja el derivado como estaba y cierra la revisión",
    "«descartar» lo aparta: no se borra, deja de usarse",
)


@dataclass(frozen=True, slots=True)
class Dependent:
    """Algo que depende de una sección: un derivado, una pregunta o una respuesta guardada."""

    kind: EdgeTarget
    id: str
    title: str
    #: Solo los derivados se marcan `needs_review`: una respuesta guardada es historia de lo que se
    #: respondió con el corpus de entonces, y no se reescribe (misma regla que en S09).
    reviewable: bool = True


@dataclass(frozen=True, slots=True)
class SectionChange:
    """Una sección del diff: su etiqueta y qué le pasó."""

    label: str
    kind: SectionChangeKind


@dataclass(frozen=True, slots=True)
class AffectedItem:
    """Un dependiente afectado, con la razón por la que lo está."""

    kind: EdgeTarget
    id: str
    title: str
    sections: tuple[str, ...]
    reason: str
    reviewable: bool


@dataclass(frozen=True, slots=True)
class ChangeAssessment:
    """El resultado de valorar un cambio: qué se tocó y qué queda pendiente de revisar."""

    sections: tuple[SectionChange, ...] = ()
    affected: tuple[AffectedItem, ...] = ()
    note: str = LEGAL_EFFECT_NOTE
    extra_notes: tuple[str, ...] = ()

    @property
    def changed(self) -> int:
        return sum(1 for seccion in self.sections if seccion.kind is SectionChangeKind.CHANGED)

    @property
    def added(self) -> int:
        return sum(1 for seccion in self.sections if seccion.kind is SectionChangeKind.ADDED)

    @property
    def removed(self) -> int:
        return sum(1 for seccion in self.sections if seccion.kind is SectionChangeKind.REMOVED)

    @property
    def unchanged(self) -> int:
        return sum(1 for seccion in self.sections if seccion.kind is SectionChangeKind.UNCHANGED)

    @property
    def has_changes(self) -> bool:
        return self.changed + self.added + self.removed > 0

    @property
    def reviewable(self) -> tuple[AffectedItem, ...]:
        return tuple(item for item in self.affected if item.reviewable)


def _motivo(kind: SectionChangeKind, label: str) -> str:
    if kind is SectionChangeKind.CHANGED:
        return f"depende de «{label}», que ha cambiado"
    if kind is SectionChangeKind.REMOVED:
        return f"depende de «{label}», que ya no está en la versión nueva"
    # Solo se llama con secciones cambiadas o quitadas; `added` y `unchanged` no invalidan nada.
    return f"depende de «{label}»"


@dataclass
class _Acumulado:
    """Lo que se va juntando por dependiente mientras se recorre el diff."""

    kind: EdgeTarget
    id: str
    title: str
    reviewable: bool
    sections: list[str] = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)


def assess_change(
    *,
    sections: Sequence[SectionChange],
    dependents: Mapping[str, Sequence[Dependent]],
) -> ChangeAssessment:
    """Decide qué queda pendiente de revisar y por qué, sin tocar nada.

    Un dependiente se marca si **alguno** de sus insumos está en una sección que cambió o se quitó.
    Una sección nueva no invalida nada por sí sola: nadie dependía de ella porque no existía. Las
    secciones intactas tampoco: es la mitad del criterio de aceptación del slice («solo derivados
    dependientes se invalidan») y por eso se comprueba con una prueba que mira los dos lados.
    """
    acumulado: dict[tuple[str, str], _Acumulado] = {}
    for seccion in sections:
        if seccion.kind in (SectionChangeKind.UNCHANGED, SectionChangeKind.ADDED):
            continue
        for dependiente in dependents.get(seccion.label, ()):
            entrada = acumulado.setdefault(
                (dependiente.kind.value, dependiente.id),
                _Acumulado(
                    kind=dependiente.kind,
                    id=dependiente.id,
                    title=dependiente.title,
                    reviewable=dependiente.reviewable,
                ),
            )
            if seccion.label not in entrada.sections:
                entrada.sections.append(seccion.label)
            motivo = _motivo(seccion.kind, seccion.label)
            if motivo not in entrada.reasons:
                entrada.reasons.append(motivo)

    afectados = tuple(
        AffectedItem(
            kind=entrada.kind,
            id=entrada.id,
            title=entrada.title,
            sections=tuple(entrada.sections),
            reason="; ".join(entrada.reasons),
            reviewable=entrada.reviewable,
        )
        for entrada in acumulado.values()
    )

    notas: list[str] = []
    if afectados and not any(item.reviewable for item in afectados):
        notas.append(
            "Nada de lo afectado se puede revisar aquí: lo que depende de estas secciones son "
            "respuestas guardadas, que forman parte de lo que se respondió y no se reescriben."
        )
    if not afectados and sections:
        notas.append(
            "Ningún derivado depende de lo que ha cambiado: el cambio de texto no obliga a revisar "
            "nada de lo que hay guardado."
        )
    return ChangeAssessment(sections=tuple(sections), affected=afectados, extra_notes=tuple(notas))


def assert_can_confirm(status: ChangeStatus) -> None:
    """Un conjunto de cambios solo se confirma una vez, y solo mientras está propuesto."""
    if status is ChangeStatus.CONFIRMED:
        raise InvalidStateError(
            "este cambio ya está confirmado: confirmarlo otra vez volvería a marcar los derivados"
        )
    if status is ChangeStatus.DISCARDED:
        raise InvalidStateError(
            "este cambio se descartó: para volver a proponerlo hay que promover otra versión"
        )


def assert_can_review(*, needs_review: bool) -> None:
    """Solo se revisa lo que está pendiente: revisar lo que no lo está no dice nada."""
    if not needs_review:
        raise InvalidStateError("este derivado no está pendiente de revisión")


__all__ = [
    "LEGAL_EFFECT_NOTE",
    "REVIEW_ACTIONS",
    "AffectedItem",
    "ArtifactKind",
    "ArtifactReview",
    "ChangeAssessment",
    "ChangeStatus",
    "Dependent",
    "EdgeSource",
    "EdgeTarget",
    "SectionChange",
    "SectionChangeKind",
    "assert_can_confirm",
    "assert_can_review",
    "assess_change",
]
