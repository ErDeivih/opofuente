"""Clasificación y revisión (S04): reglas puras, sin base de datos, sin red y sin LLM.

Todo lo que decide **qué se propone**, **qué se puede aceptar** y **qué cuenta como cobertura** vive
aquí, para poder probarlo sin motor de base de datos y para que la interfaz y la API no inventen
reglas por su cuenta.

Decisiones que la especificación deja abiertas y cómo se cierran (ver `docs/slices/S04.md`):

- **Vocabulario de autoridad.** `authority_tier` aparece en el manifiesto de fuentes con el valor
  `A`
  y la invariante 8 del modelo dice que «un contenido generado nunca es autoridad A/B», pero la
  especificación no enumera el resto de niveles. Se fijan cinco: `A` organismo convocante o
  publicación oficial, `B` otra administración pública, `C` tercero identificable (editorial,
  academia, autor con nombre), `D` origen comunitario o anónimo, y `unknown` cuando no consta.
- **Vocabulario de derechos.** Se reutiliza el del manifiesto de fuentes
  (`reuse_with_conditions`, `private_use_only`, `rights_document`) y se añade `unknown`, que es el
  valor conservador por defecto y no se puede presentar como permiso.
- **Ejes críticos.** `authority` y `rights` requieren confirmación explícita **siempre** (04 §8):
  una propuesta con confianza altísima no se aplica sola, va a la cola de revisión. El resto de ejes
  puede
  quedar `auto_applied_provisional`, que es visible y reversible.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from opofuente.domain.extraction import Quality


class SubjectType(StrEnum):
    """Sobre qué se clasifica. En S04 no hay documentos lógicos todavía: eso es S05."""

    ARTIFACT = "artifact"
    REPRESENTATION = "representation"


class Axis(StrEnum):
    """Ejes de clasificación (03_DATA-MODEL §5 y 04_INGESTION §6-§7)."""

    DOCUMENT_TYPE = "document_type"
    OPPOSITION = "opposition"
    TOPIC = "topic"
    AUTHORITY = "authority"
    RIGHTS = "rights"


#: Ejes que **siempre** exigen confirmación explícita: la aplicación no otorga autoridad ni
#: derechos por su cuenta (04 §8, D006). `answer`, `supersedes` y «publicar un derivado
#: generado» son críticos
#: también, pero pertenecen a slices posteriores: aquí solo existen estos dos.
CRITICAL_AXES: frozenset[Axis] = frozenset({Axis.AUTHORITY, Axis.RIGHTS})


class DocumentType(StrEnum):
    """Tipos documentales del MVP (04 §6). `unknown` es un resultado válido, no un fallo."""

    CONVOCATION = "convocation"
    CURRICULUM = "curriculum"
    LAW_OR_REGULATION = "law_or_regulation"
    OFFICIAL_TECHNICAL = "official_technical"
    PRIVATE_SYLLABUS = "private_syllabus"
    PERSONAL_NOTES = "personal_notes"
    OFFICIAL_EXAM = "official_exam"
    ANSWER_KEY = "answer_key"
    PRIVATE_QUESTION_BANK = "private_question_bank"
    PRACTICAL_CASE = "practical_case"
    FLASHCARDS = "flashcards"
    COMMUNITY_MATERIAL = "community_material"
    UNKNOWN = "unknown"


class AuthorityTier(StrEnum):
    """Nivel de autoridad de la fuente o del documento (ver la decisión de arriba)."""

    A = "A"
    B = "B"
    C = "C"
    D = "D"
    UNKNOWN = "unknown"


class RightsStatus(StrEnum):
    """Estado de derechos del material; `UNKNOWN` es el valor conservador y nunca un permiso."""

    REUSE_WITH_CONDITIONS = "reuse_with_conditions"
    PRIVATE_USE_ONLY = "private_use_only"
    RIGHTS_DOCUMENT = "rights_document"
    UNKNOWN = "unknown"


#: Cómo se dice cada valor de los vocabularios cerrados cuando hay que enseñarlo o contarlo.
#:
#: Vive en el dominio porque lo usan el repositorio (para etiquetar una propuesta) y el resumen de
#: preparación (para contar el material por papel). Dos tablas de etiquetas serían dos verdades: la
#: pantalla podría decir «Temario» donde el informe dice «Temario o programa».
DOCUMENT_TYPE_LABELS: dict[str, str] = {
    DocumentType.CONVOCATION.value: "Convocatoria",
    DocumentType.CURRICULUM.value: "Temario o programa",
    DocumentType.LAW_OR_REGULATION.value: "Norma legal",
    DocumentType.OFFICIAL_TECHNICAL.value: "Documentación técnica oficial",
    DocumentType.PRIVATE_SYLLABUS.value: "Temario particular",
    DocumentType.PERSONAL_NOTES.value: "Apuntes personales",
    DocumentType.OFFICIAL_EXAM.value: "Examen oficial",
    DocumentType.ANSWER_KEY.value: "Plantilla de respuestas",
    DocumentType.PRIVATE_QUESTION_BANK.value: "Banco de preguntas privado",
    DocumentType.PRACTICAL_CASE.value: "Caso práctico",
    DocumentType.FLASHCARDS.value: "Tarjetas de repaso",
    DocumentType.COMMUNITY_MATERIAL.value: "Material de la comunidad",
    DocumentType.UNKNOWN.value: "Sin determinar",
}

AUTHORITY_LABELS: dict[str, str] = {
    AuthorityTier.A.value: "Publicación oficial",
    AuthorityTier.B.value: "Administración pública",
    AuthorityTier.C.value: "Tercero identificable",
    AuthorityTier.D.value: "Origen comunitario o anónimo",
    AuthorityTier.UNKNOWN.value: "Sin determinar",
}

RIGHTS_LABELS: dict[str, str] = {
    RightsStatus.REUSE_WITH_CONDITIONS.value: "Reutilización con condiciones",
    RightsStatus.PRIVATE_USE_ONLY.value: "Solo uso privado",
    RightsStatus.RIGHTS_DOCUMENT.value: "Documento de condiciones de uso",
    RightsStatus.UNKNOWN.value: "Derechos sin determinar",
}


class ProposalStatus(StrEnum):
    """Estados de una propuesta de clasificación (03_DATA-MODEL §5)."""

    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"
    AUTO_APPLIED_PROVISIONAL = "auto_applied_provisional"


class CoverageType(StrEnum):
    """Cuánto cubre el material del nodo: aviso < parte < todo (ver `docs/slices/S04.md`)."""

    MENTION = "mention"
    PARTIAL = "partial"
    COMPLETE = "complete"


class MappingStatus(StrEnum):
    """Un mapeo provisional **no** cuenta como cobertura aceptada (11_IMPLEMENTATION-SLICES S05)."""

    PROVISIONAL = "provisional"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class Band(StrEnum):
    """Bandas de confianza configurables (04 §8). Sin calibrar hasta tener muestra (Q005)."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass(frozen=True, slots=True)
class ConfidenceBands:
    """Tres bandas: autoaplicable, cola de revisión y sin asignar.

    Los umbrales son configurables y **no** están calibrados: la especificación prohíbe fijarlos
    antes
    de tener un conjunto etiquetado (04 §8) y Q005 deja la calibración para la muestra real.
    """

    high: float = 0.75
    medium: float = 0.45

    def __post_init__(self) -> None:
        if not 0.0 <= self.medium <= self.high <= 1.0:
            raise ValueError("Las bandas deben cumplir 0 <= media <= alta <= 1")

    def band_for(self, confidence: float, *, axis: Axis) -> Band:
        """Banda de una propuesta. Un eje crítico **nunca** llega a la banda alta."""
        if not 0.0 <= confidence <= 1.0:
            raise ValueError("La confianza debe estar entre 0 y 1")
        if confidence < self.medium:
            return Band.LOW
        if axis in CRITICAL_AXES:
            return Band.MEDIUM
        return Band.HIGH if confidence >= self.high else Band.MEDIUM

    def decides_itself(self, confidence: float, *, axis: Axis) -> bool:
        """¿La propuesta se puede aplicar provisionalmente sola? Nunca en un eje crítico."""
        return self.band_for(confidence, axis=axis) is Band.HIGH


@dataclass(frozen=True, slots=True)
class Alternative:
    """Alternativa que el motor barajó: se guarda para que la revisión sea útil."""

    value: str
    confidence: float


@dataclass(frozen=True, slots=True)
class Proposal:
    """Una propuesta de clasificación, con su motor, su evidencia y sus alternativas.

    No es un hecho: hasta que se acepta, no cambia nada del material. `evidence` son referencias
    breves y **citables** (fragmento, sección, identificador), nunca el documento entero.
    """

    id: str
    subject_type: SubjectType
    subject_id: str
    axis: Axis
    proposed_value: str
    confidence: float
    engine_name: str
    engine_version: str
    alternatives: tuple[Alternative, ...] = ()
    evidence: tuple[str, ...] = ()
    status: ProposalStatus = ProposalStatus.PENDING
    decided_at: object | None = None
    decision_note: str | None = None

    def __post_init__(self) -> None:
        if not self.subject_id:
            raise ValueError("Una propuesta necesita sujeto")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("La confianza debe estar entre 0 y 1")
        if not value_matches_axis(self.axis, self.proposed_value):
            raise ValueError(
                f"«{self.proposed_value}» no es un valor válido para el eje {self.axis.value}"
            )

    @property
    def is_critical(self) -> bool:
        return self.axis in CRITICAL_AXES


def value_matches_axis(axis: Axis, value: str) -> bool:
    """¿El valor propuesto pertenece al vocabulario del eje?

    Los ejes `opposition` y `topic` se validan contra datos reales (perfiles y nodos sembrados), no
    contra una lista fija: por eso aquí solo se comprueba que no vengan vacíos.
    """
    if not value:
        return False
    if axis is Axis.DOCUMENT_TYPE:
        return value in {item.value for item in DocumentType}
    if axis is Axis.AUTHORITY:
        return value in {item.value for item in AuthorityTier}
    if axis is Axis.RIGHTS:
        return value in {item.value for item in RightsStatus}
    return True


_ALLOWED_DECISIONS: dict[ProposalStatus, frozenset[ProposalStatus]] = {
    ProposalStatus.PENDING: frozenset(
        {
            ProposalStatus.ACCEPTED,
            ProposalStatus.REJECTED,
            ProposalStatus.SUPERSEDED,
            ProposalStatus.AUTO_APPLIED_PROVISIONAL,
        }
    ),
    ProposalStatus.AUTO_APPLIED_PROVISIONAL: frozenset(
        {ProposalStatus.ACCEPTED, ProposalStatus.REJECTED, ProposalStatus.SUPERSEDED}
    ),
    ProposalStatus.ACCEPTED: frozenset({ProposalStatus.SUPERSEDED}),
    ProposalStatus.REJECTED: frozenset({ProposalStatus.SUPERSEDED}),
    ProposalStatus.SUPERSEDED: frozenset(),
}

#: Estados desde los que se puede «deshacer» una decisión y volver a la cola.
UNDOABLE_STATUSES: frozenset[ProposalStatus] = frozenset(
    {
        ProposalStatus.ACCEPTED,
        ProposalStatus.REJECTED,
        ProposalStatus.AUTO_APPLIED_PROVISIONAL,
    }
)


def decision_allowed(current: ProposalStatus, new: ProposalStatus) -> bool:
    """¿Se puede pasar de `current` a `new`?"""
    return new in _ALLOWED_DECISIONS[current]


def can_undo(status: ProposalStatus) -> bool:
    """¿Hay algo que deshacer? Una propuesta pendiente o sustituida no tiene nada que revertir."""
    return status in UNDOABLE_STATUSES


def coverage_counts_as_accepted(quality: Quality | None, mapping_status: MappingStatus) -> bool:
    """¿Este mapeo cuenta como **cobertura aceptada**?

    Solo si alguien lo aceptó explícitamente **y** el texto que lo respalda es utilizable: una
    fuente
    pobre o candidata no puede sostener una cobertura aceptada (11_IMPLEMENTATION-SLICES S05). Un
    mapeo provisional cuenta como cobertura provisional, nunca como aceptada.
    """
    if mapping_status is not MappingStatus.ACCEPTED:
        return False
    return quality in {Quality.GOOD, Quality.USABLE_WITH_WARNINGS}


@dataclass(frozen=True, slots=True)
class ReviewGroup:
    """Grupo de revisión: propuestas que se pueden decidir juntas por un criterio explicable."""

    key: str
    label: str
    subject_type: SubjectType
    axis: Axis
    proposed_value: str
    proposal_ids: tuple[str, ...] = field(default_factory=tuple)

    @property
    def size(self) -> int:
        return len(self.proposal_ids)


def group_key(subject_type: SubjectType, axis: Axis, value: str) -> str:
    """Clave determinista de un grupo: mismo sujeto, eje y valor propuesto, mismo grupo."""
    return f"{subject_type.value}:{axis.value}:{value}"


@dataclass(frozen=True, slots=True)
class TopicCandidate:
    """Nodo del programa que un motor puede proponer como tema."""

    node_id: str
    path: str
    title: str
    depth: int


@dataclass(frozen=True, slots=True)
class ProfileCandidate:
    """Perfil activo con los nodos de su convocatoria: lo que un motor necesita para el tema."""

    opposition_code: str
    opposition_name: str
    convocation_code: str
    topics: tuple[TopicCandidate, ...] = ()


@dataclass(frozen=True, slots=True)
class ClassificationSubject:
    """Todo lo que un motor puede mirar de un sujeto. Ni ficheros, ni base de datos, ni red.

    `text` es un **extracto acotado** de la representación (la aplicación decide el tope): no
    recibe el documento entero. `origin_display` es la procedencia visible y ya saneada (la URL sin
    cadena de consulta o la etiqueta del pegado), nunca la ruta privada del usuario.
    """

    subject_type: SubjectType
    subject_id: str
    text: str = ""
    original_name: str | None = None
    media_type: str | None = None
    origin_type: str | None = None
    origin_display: str | None = None
    profiles: tuple[ProfileCandidate, ...] = ()

    @property
    def label(self) -> str:
        """Nombre con el que se presenta el sujeto: el fichero si consta, el id si no."""
        return self.original_name or self.origin_display or self.subject_id
