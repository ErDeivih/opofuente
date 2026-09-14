"""Carga de los fixtures de perfil.

Lee el manifiesto, el perfil curado y el programa generado, y los convierte en objetos de
dominio. La validación de forma la hace pydantic; la de coherencia, el dominio. Si un fixture
está mal formado, la siembra falla con un mensaje que dice qué fichero y qué campo.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from datetime import date
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from opofuente.domain.errors import InvariantViolationError
from opofuente.domain.profiles import (
    Convocation,
    ConvocationStatus,
    CurriculumNode,
    ExamPart,
    ExamRule,
    NodeType,
    Opposition,
    PartFormat,
    PartKind,
    Profile,
    RuleKind,
    validate_curriculum,
    validate_exam,
)

MANIFEST_NAME = "manifest.json"
PROFILE_SUFFIX = ".profile.json"
CURRICULUM_SUFFIX = ".curriculum.json"


class NodeFixture(BaseModel):
    model_config = ConfigDict(extra="forbid")

    node_type: NodeType
    official_code: str
    title: str
    position: int
    path: str
    depth: int
    description: str | None = None
    children: list[NodeFixture] = Field(default_factory=list)


class EvidenceFixture(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_id: str
    quote: str


class PartFixture(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    name: str
    kind: PartKind
    position: int
    evidence: EvidenceFixture
    format: PartFormat | None = None
    parent_code: str | None = None
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


class RuleFixture(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    kind: RuleKind
    value_text: str
    description: str
    evidence: EvidenceFixture


class OppositionFixture(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    name: str
    description: str | None = None
    active: bool = False


class ConvocationFixture(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    title: str
    official_url: str
    published_at: date
    status: ConvocationStatus
    source_id: str
    exam_date: date | None = None
    exam_date_note: str | None = None
    source_identifier: str | None = None
    source_location: str | None = None


class ExamFixture(BaseModel):
    model_config = ConfigDict(extra="forbid")

    parts: list[PartFixture]
    rules: list[RuleFixture]


class ProfileFixture(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    source_manifest: str | None = None
    opposition: OppositionFixture
    convocation: ConvocationFixture
    exam: ExamFixture


class CurriculumFixture(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    generated_from: dict[str, Any]
    transformations: list[str] = Field(default_factory=list)
    counts: dict[str, int]
    nodes: list[NodeFixture]


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise InvariantViolationError(f"falta el fixture {path.name}") from error
    except json.JSONDecodeError as error:
        raise InvariantViolationError(f"{path.name} no es JSON válido: {error}") from error


def _load_model(path: Path, model: type[Any]) -> Any:
    try:
        return model.model_validate(_read_json(path))
    except ValidationError as error:
        raise InvariantViolationError(f"{path.name} no cumple el formato: {error}") from error


def _to_nodes(items: list[NodeFixture]) -> tuple[CurriculumNode, ...]:
    return tuple(
        CurriculumNode(
            node_type=item.node_type,
            official_code=item.official_code,
            title=item.title,
            description=item.description,
            position=item.position,
            path=item.path,
            depth=item.depth,
            children=_to_nodes(item.children),
        )
        for item in items
    )


def _to_part(item: PartFixture) -> ExamPart:
    return ExamPart(
        code=item.code,
        name=item.name,
        kind=item.kind,
        format=item.format,
        position=item.position,
        parent_code=item.parent_code,
        ordinary_items=item.ordinary_items,
        reserve_items=item.reserve_items,
        options_per_question=item.options_per_question,
        score_min=item.score_min,
        score_max=item.score_max,
        pass_score=item.pass_score,
        wrong_penalty_fraction=item.wrong_penalty_fraction,
        fail_if_errors_gte=item.fail_if_errors_gte,
        time_minutes=item.time_minutes,
        structure_note=item.structure_note,
        notes=item.notes,
        evidence_quote=item.evidence.quote,
    )


def _to_rule(item: RuleFixture) -> ExamRule:
    return ExamRule(
        code=item.code,
        kind=item.kind,
        value_text=item.value_text,
        description=item.description,
        evidence_quote=item.evidence.quote,
    )


def _source_reference(convocation: ConvocationFixture) -> str | None:
    parts = [part for part in (convocation.source_identifier, convocation.source_location) if part]
    return " · ".join(parts) if parts else None


def load_profiles(directory: Path | None = None) -> tuple[Profile, ...]:
    """Carga todos los perfiles disponibles en el directorio de fixtures."""
    base = directory or Path("fixtures") / "profiles"
    if not base.is_dir():
        raise InvariantViolationError(f"no existe el directorio de fixtures: {base}")
    if not (base / MANIFEST_NAME).is_file():
        raise InvariantViolationError(f"falta {MANIFEST_NAME} en {base}")

    profiles: list[Profile] = []
    for profile_path in sorted(base.glob(f"*{PROFILE_SUFFIX}")):
        fixture: ProfileFixture = _load_model(profile_path, ProfileFixture)
        curriculum_path = base / f"{fixture.code}{CURRICULUM_SUFFIX}"
        curriculum: CurriculumFixture = _load_model(curriculum_path, CurriculumFixture)
        if curriculum.code != fixture.code:
            raise InvariantViolationError(
                f"{curriculum_path.name} no corresponde al perfil {fixture.code}"
            )

        nodes = _to_nodes(curriculum.nodes)
        parts = tuple(_to_part(item) for item in fixture.exam.parts)
        rules = tuple(_to_rule(item) for item in fixture.exam.rules)

        validate_curriculum(fixture.code, nodes)
        validate_exam(fixture.code, parts, rules)

        declared = _declared_counts(fixture.code, curriculum.counts)
        actual: dict[NodeType, int] = {}
        for node, _parent in _walk(nodes):
            actual[node.node_type] = actual.get(node.node_type, 0) + 1
        normalized = {node_type: actual.get(node_type, 0) for node_type in NodeType}
        if declared != normalized:
            raise InvariantViolationError(
                f"{fixture.code}: el programa declara {declared} y contiene {normalized}"
            )

        profiles.append(
            Profile(
                opposition=Opposition(
                    code=fixture.opposition.code,
                    name=fixture.opposition.name,
                    description=fixture.opposition.description,
                    active=fixture.opposition.active,
                ),
                convocation=Convocation(
                    code=fixture.convocation.code,
                    title=fixture.convocation.title,
                    official_url=fixture.convocation.official_url,
                    published_at=fixture.convocation.published_at,
                    exam_date=fixture.convocation.exam_date,
                    status=fixture.convocation.status,
                    source_reference=_source_reference(fixture.convocation),
                    source_note=fixture.convocation.exam_date_note,
                ),
                curriculum=nodes,
                parts=parts,
                rules=rules,
            )
        )

    if not profiles:
        raise InvariantViolationError(f"no hay ningún perfil en {base}")
    return tuple(profiles)


def _walk(nodes: tuple[CurriculumNode, ...]) -> Iterator[tuple[CurriculumNode, None]]:
    for node in nodes:
        yield node, None
        yield from _walk(node.children)


#: Los fixtures declaran sus recuentos en plural («blocks»), porque se leen como resumen humano.
_COUNT_KEYS: dict[str, NodeType] = {
    "blocks": NodeType.BLOCK,
    "topics": NodeType.TOPIC,
    "epigraphs": NodeType.EPIGRAPH,
}


def _declared_counts(profile_code: str, counts: dict[str, int]) -> dict[NodeType, int]:
    unknown = set(counts) - set(_COUNT_KEYS)
    if unknown:
        raise InvariantViolationError(
            f"{profile_code}: recuentos desconocidos en el fixture: {sorted(unknown)}"
        )
    declared = {_COUNT_KEYS[key]: value for key, value in counts.items()}
    return {node_type: declared.get(node_type, 0) for node_type in NodeType}
