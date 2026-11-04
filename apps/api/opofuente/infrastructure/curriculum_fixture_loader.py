"""Carga del fixture del temario común.

El fixture se genera desde la fuente (`build_curriculum_fixtures.py`) y aquí se valida antes de
sembrarlo: forma (pydantic), coherencia (dominio) y **recuentos**. La validación de forma no basta:
un fixture con 4 bloques es JSON válido y, sin embargo, no es la v1 aprobada; por eso el cargador
compara los recuentos declarados con los nodos reales y con los que exige la publicación.

Si un fixture está mal formado, el error dice qué fichero y qué campo.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from opofuente.domain.curricula import (
    CommonCurriculum,
    CurriculumReference,
    CurriculumSource,
    count_common_nodes,
    publication_counts,
    validate_common_curriculum,
)
from opofuente.domain.errors import InvariantViolationError
from opofuente.domain.profiles import CurriculumNode, NodeType

COMMON_CURRICULUM_FIXTURE = Path("fixtures") / "curricula" / "informatica-c1.v1.json"


class NodeFixture(BaseModel):
    """Un nodo del temario en el fixture, con la cita de su bloque cuando la tiene."""

    model_config = ConfigDict(extra="forbid")

    node_type: NodeType
    official_code: str
    title: str
    position: int
    path: str
    depth: int
    description: str | None = None
    source_reference: str | None = None
    children: list[NodeFixture] = Field(default_factory=list)


class VersionFixture(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version_no: int
    code: str
    title: str


class SourceFixture(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document: str
    sha256: str
    transformations: list[str] = Field(default_factory=list)


class CountsFixture(BaseModel):
    model_config = ConfigDict(extra="forbid")

    blocks: int
    topics: int
    nodes: int


class ReferenceFixture(BaseModel):
    model_config = ConfigDict(extra="forbid")

    convocation_code: str
    role: str
    source_reference: str


class CommonCurriculumFixture(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    name: str
    group_code: str | None = None
    family: str | None = None
    version: VersionFixture
    generated_from: SourceFixture
    counts: CountsFixture
    nodes: list[NodeFixture]
    referenced_by: list[ReferenceFixture] = Field(default_factory=list)


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


def load_common_curriculum(path: Path | None = None) -> CommonCurriculum:
    """Lee y valida el fixture del temario común."""
    ruta = path or COMMON_CURRICULUM_FIXTURE
    try:
        data: Any = json.loads(ruta.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise InvariantViolationError(f"falta el fixture del temario común: {ruta}") from error
    except json.JSONDecodeError as error:
        raise InvariantViolationError(f"{ruta.name} no es JSON válido: {error}") from error

    try:
        fixture = CommonCurriculumFixture.model_validate(data)
    except ValidationError as error:
        raise InvariantViolationError(
            f"{ruta.name} no cumple el formato del temario común: {error}"
        ) from error

    curriculum = CommonCurriculum(
        code=fixture.code,
        name=fixture.name,
        group_code=fixture.group_code,
        family=fixture.family,
        version_no=fixture.version.version_no,
        version_code=fixture.version.code,
        title=fixture.version.title,
        nodes=_to_nodes(fixture.nodes),
        source=CurriculumSource(
            document=fixture.generated_from.document,
            sha256=fixture.generated_from.sha256,
        ),
        references=tuple(
            CurriculumReference(
                convocation_code=reference.convocation_code,
                role=reference.role,
                source_reference=reference.source_reference,
            )
            for reference in fixture.referenced_by
        ),
    )

    validate_common_curriculum(curriculum)

    reales = count_common_nodes(curriculum.nodes)
    declarados = {
        "blocks": fixture.counts.blocks,
        "topics": fixture.counts.topics,
        "nodes": fixture.counts.nodes,
    }
    if declarados != reales:
        raise InvariantViolationError(
            f"{curriculum.code}: el fixture declara {declarados} y contiene {reales}"
        )
    esperados = publication_counts(curriculum)
    if reales != esperados:
        raise InvariantViolationError(
            f"{curriculum.code}: la versión {curriculum.version_no} debe tener {esperados} "
            f"para publicarse y el fixture tiene {reales}"
        )
    return curriculum
