"""Perfiles de oposición: oposiciones, convocatorias, programa y reglas de examen.

Capa de dominio: sin FastAPI, sin SQLAlchemy y sin acceso a disco. Las reglas que se comprueban
aquí son las que el slice exige (una sola convocatoria activa por oposición, programa con
posiciones y rutas coherentes, partes de examen con referencias válidas) y se comprueban también
en la base de datos mediante restricciones.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import StrEnum

from opofuente.domain.errors import InvariantViolationError

MAX_DEPTH = 2


class ConvocationStatus(StrEnum):
    """Estado de una convocatoria publicada.

    `active` no significa «la última que ha salido» sino **la que la aplicación usa para trabajar**:
    es la que resuelven Programa, Estudio, Repaso y Banco, y solo puede haber una por oposición (lo
    garantiza un índice único parcial). Los demás estados describen por qué una convocatoria no es
    esa:

    - `draft`: todavía no se ha publicado. Nadie la ha convocado, así que no es utilizable.
    - `available`: está publicada, es utilizable y **no es la vigente**. Es el caso de una oposición
      con dos procesos vivos a la vez —Celador tiene la convocatoria ordinaria de acceso libre y el
      proceso de estabilización de la Ley 20/2021—: ninguna sustituye a la otra, las dos se pueden
      estudiar y solo una se elige para trabajar.
    - `superseded`: otra convocatoria del **mismo proceso** la ha reemplazado (una orden corregida,
      una republicación). No es lo mismo que `available`: aquí sí hay un acto posterior que la deja
      atrás.
    - `archived`: la aplicación no debe usar esta convocatoria.
    """

    DRAFT = "draft"
    ACTIVE = "active"
    AVAILABLE = "available"
    SUPERSEDED = "superseded"
    ARCHIVED = "archived"


class NodeType(StrEnum):
    """Nivel estructural del programa dentro de una convocatoria.

    Los perfiles oficiales no tienen la misma forma: TAI publica cuatro bloques con temas, y
    Guardia Civil publica veinticinco temas con bloques internos y epígrafes. El tipo describe el
    nivel, y cada convocatoria define su jerarquía (ver ADR-005).
    """

    BLOCK = "block"
    TOPIC = "topic"
    EPIGRAPH = "epigraph"


class PartKind(StrEnum):
    GROUP = "group"
    TEST = "test"


class PartFormat(StrEnum):
    SINGLE_CHOICE = "single_choice"
    MULTI_MARK_ERROR = "multi_mark_error"
    PSYCHOTECHNICAL = "psychotechnical"


class RuleKind(StrEnum):
    BOOLEAN = "boolean"
    INTEGER = "integer"
    FRACTION = "fraction"
    TEXT = "text"


@dataclass(frozen=True, slots=True)
class ExamPart:
    """Parte o agrupación de partes del examen, tal como la publica la convocatoria.

    Todo campo numérico puede ser nulo: si la convocatoria no publica un dato (por ejemplo,
    cuántas alternativas tiene cada pregunta), se deja vacío en lugar de suponerlo.
    """

    code: str
    name: str
    kind: PartKind
    position: int
    evidence_quote: str
    parent_code: str | None = None
    format: PartFormat | None = None
    ordinary_items: int | None = None
    reserve_items: int | None = None
    options_per_question: int | None = None
    score_min: float | None = None
    score_max: float | None = None
    pass_score: float | None = None
    wrong_penalty_fraction: float | None = None
    fail_if_errors_gte: int | None = None
    time_minutes: int | None = None
    structure_note: str | None = None
    notes: str | None = None


@dataclass(frozen=True, slots=True)
class ExamRule:
    """Regla transversal del examen (fórmula, penalización, umbral, desempate)."""

    code: str
    kind: RuleKind
    value_text: str
    description: str
    evidence_quote: str


@dataclass(frozen=True, slots=True)
class CurriculumNode:
    node_type: NodeType
    official_code: str
    title: str
    position: int
    path: str
    depth: int
    children: tuple[CurriculumNode, ...] = ()
    description: str | None = None


@dataclass(frozen=True, slots=True)
class Convocation:
    code: str
    title: str
    official_url: str
    published_at: date
    status: ConvocationStatus
    source_reference: str | None = None
    exam_date: date | None = None
    source_note: str | None = None


@dataclass(frozen=True, slots=True)
class Opposition:
    code: str
    name: str
    description: str | None = None
    active: bool = False


@dataclass(frozen=True, slots=True)
class Profile:
    """Perfil completo que se siembra desde un fixture: oposición, convocatoria, programa y
    reglas de examen."""

    opposition: Opposition
    convocation: Convocation
    curriculum: tuple[CurriculumNode, ...]
    parts: tuple[ExamPart, ...]
    rules: tuple[ExamRule, ...]


def flatten(nodes: tuple[CurriculumNode, ...]) -> tuple[tuple[CurriculumNode, str | None], ...]:
    """Recorre el árbol en preorden devolviendo cada nodo con la ruta de su padre."""
    result: list[tuple[CurriculumNode, str | None]] = []

    def visit(children: tuple[CurriculumNode, ...], parent_path: str | None) -> None:
        for node in children:
            result.append((node, parent_path))
            visit(node.children, node.path)

    visit(nodes, None)
    return tuple(result)


def count_by_type(nodes: tuple[CurriculumNode, ...]) -> dict[NodeType, int]:
    counts = dict.fromkeys(NodeType, 0)
    for node, _parent in flatten(nodes):
        counts[node.node_type] += 1
    return counts


def validate_curriculum(profile_code: str, nodes: tuple[CurriculumNode, ...]) -> None:
    """Comprueba que el árbol del programa es coherente antes de guardarlo."""
    if not nodes:
        raise InvariantViolationError(f"{profile_code}: el programa no tiene ningún nodo")

    paths: set[str] = set()
    for node, parent_path in flatten(nodes):
        if not node.title.strip():
            raise InvariantViolationError(f"{profile_code}: nodo sin título en {node.path}")
        if node.path in paths:
            raise InvariantViolationError(f"{profile_code}: ruta repetida {node.path}")
        paths.add(node.path)
        if node.depth > MAX_DEPTH:
            raise InvariantViolationError(
                f"{profile_code}: profundidad {node.depth} mayor que {MAX_DEPTH} en {node.path}"
            )
        if node.node_type is NodeType.EPIGRAPH and node.children:
            raise InvariantViolationError(
                f"{profile_code}: un epígrafe no puede tener hijos ({node.path})"
            )
        expected_parent = parent_path
        actual_parent = node.path.rsplit(".", 1)[0] if "." in node.path else None
        if actual_parent != expected_parent:
            raise InvariantViolationError(
                f"{profile_code}: la ruta {node.path} no cuelga de {expected_parent}"
            )

    for parent_path in {parent for _node, parent in flatten(nodes)}:
        siblings = [
            node
            for node, parent in flatten(nodes)
            if parent == parent_path or (parent_path is None and parent is None)
        ]
        positions = sorted(node.position for node in siblings)
        if positions != list(range(1, len(siblings) + 1)):
            raise InvariantViolationError(
                f"{profile_code}: posiciones no consecutivas en {parent_path or 'raíz'}: "
                f"{positions}"
            )


def validate_exam(
    profile_code: str, parts: tuple[ExamPart, ...], rules: tuple[ExamRule, ...]
) -> None:
    """Comprueba coherencia de partes y reglas antes de guardarlas."""
    if not parts:
        raise InvariantViolationError(f"{profile_code}: el examen no tiene ninguna parte")

    codes = [part.code for part in parts]
    if len(codes) != len(set(codes)):
        raise InvariantViolationError(f"{profile_code}: códigos de parte repetidos")

    rule_codes = [rule.code for rule in rules]
    if len(rule_codes) != len(set(rule_codes)):
        raise InvariantViolationError(f"{profile_code}: códigos de regla repetidos")

    for part in parts:
        if not part.evidence_quote.strip():
            raise InvariantViolationError(f"{profile_code}: la parte {part.code} no cita su fuente")
        if part.parent_code is not None and part.parent_code not in codes:
            raise InvariantViolationError(
                f"{profile_code}: la parte {part.code} cuelga de {part.parent_code}, que no existe"
            )
        if part.kind is PartKind.GROUP:
            if part.format is not None:
                raise InvariantViolationError(
                    f"{profile_code}: la agrupación {part.code} no puede tener formato"
                )
            if not any(other.parent_code == part.code for other in parts):
                raise InvariantViolationError(
                    f"{profile_code}: la agrupación {part.code} no agrupa ninguna prueba"
                )
        else:
            if part.format is None:
                raise InvariantViolationError(
                    f"{profile_code}: la prueba {part.code} no tiene formato"
                )
            if part.ordinary_items is None and part.score_max is None:
                raise InvariantViolationError(
                    f"{profile_code}: la prueba {part.code} no declara preguntas ni puntuación"
                )
            if (
                part.pass_score is not None
                and part.score_min is not None
                and part.score_max is not None
                and not part.score_min <= part.pass_score <= part.score_max
            ):
                raise InvariantViolationError(
                    f"{profile_code}: el mínimo de {part.code} queda fuera de su rango "
                    "de puntuación"
                )

    for rule in rules:
        if not rule.evidence_quote.strip():
            raise InvariantViolationError(f"{profile_code}: la regla {rule.code} no cita su fuente")
        if rule.kind is RuleKind.BOOLEAN and rule.value_text.lower() not in {"true", "false"}:
            raise InvariantViolationError(
                f"{profile_code}: la regla booleana {rule.code} no vale true ni false"
            )
