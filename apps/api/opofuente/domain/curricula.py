"""Temario común: identidad, edición, procedencia y referencias de las convocatorias.

El temario común es **uno** (`ESPECIFICACION.md` §5). Este módulo describe su forma de dominio —sin
SQLAlchemy, sin acceso a disco y sin FastAPI— y las comprobaciones que un fixture debe cumplir antes
de sembrarse:

- la v1 tiene **5 bloques, 40 temas y 45 nodos**, con rutas `I.1`…`V.40` y la numeración 1-40 de la
  fuente (`§5.4`);
- solo cuelgan temas de bloques: la v1 no publica epígrafes;
- las rutas son únicas y jerárquicas (se reutiliza la validación del programa de perfiles);
- cada referencia apunta a una convocatoria con un papel del modelo (`primary`, `official`,
  `complementary`) y una cita de las bases.

La publicación no se decide aquí: la decide la siembra cuando el recuento real cuadra con el
declarado, para no afirmar que el temario está completo cuando no lo está.
"""

from __future__ import annotations

from dataclasses import dataclass

from opofuente.domain.errors import InvariantViolationError
from opofuente.domain.profiles import CurriculumNode, NodeType, count_by_type, validate_curriculum

#: Recuento de la v1 que publica `temario-c1.md` (ESPECIFICACION §5.4 y §6.7).
V1_BLOCKS = 5
V1_TOPICS = 40
V1_NODES = 45

#: Papeles que puede tener una referencia de convocatoria a un temario (§5.5).
CURRICULUM_REFERENCE_ROLES = ("primary", "official", "complementary")


@dataclass(frozen=True, slots=True)
class CurriculumSource:
    """De dónde sale esta edición: el documento y su huella."""

    document: str
    sha256: str


@dataclass(frozen=True, slots=True)
class CurriculumReference:
    """Una convocatoria que referencia el temario, con su papel y su cita de bases."""

    convocation_code: str
    role: str
    source_reference: str


@dataclass(frozen=True, slots=True)
class CommonCurriculum:
    """El temario común con su edición y sus referencias, tal y como viene del fixture."""

    code: str
    name: str
    group_code: str | None
    family: str | None
    version_no: int
    version_code: str
    title: str
    nodes: tuple[CurriculumNode, ...]
    source: CurriculumSource
    references: tuple[CurriculumReference, ...] = ()


def count_common_nodes(nodes: tuple[CurriculumNode, ...]) -> dict[str, int]:
    """Recuento por tipo de nodo, con las tres claves siempre presentes."""
    counts = count_by_type(nodes)
    return {
        "blocks": counts[NodeType.BLOCK],
        "topics": counts[NodeType.TOPIC],
        "nodes": sum(counts.values()),
    }


def publication_counts(curriculum: CommonCurriculum) -> dict[str, int]:
    """Recuento que tiene que cuadrar para publicar esta edición.

    No sirve el recuento del propio fixture: un temario incompleto es coherente consigo mismo y
    publicarlo afirmaría que está completo. Para la v1 del temario común el contrato es explícito
    (`ESPECIFICACION.md` §5.4 y §6.7): 5 bloques, 40 temas y 45 nodos.
    """
    if curriculum.code == "informatica-c1" and curriculum.version_no == 1:
        return {"blocks": V1_BLOCKS, "topics": V1_TOPICS, "nodes": V1_NODES}
    raise InvariantViolationError(
        f"{curriculum.code}: no hay recuento de publicación definido para la versión "
        f"{curriculum.version_no}; defínelo antes de sembrarla"
    )


def validate_common_curriculum(curriculum: CommonCurriculum) -> None:
    """Comprueba la coherencia del temario antes de que nadie lo siembre.

    No exige que sea la v1 completa: un fixture incompleto es válido como dato (se quedará en
    borrador), pero no puede tener rutas rotas, tipos incoherentes ni referencias inventadas.
    """
    if not curriculum.code.strip():
        raise InvariantViolationError("el temario común no tiene código")
    if not curriculum.version_code.strip():
        raise InvariantViolationError(f"{curriculum.code}: la versión no tiene código")
    if curriculum.version_no < 1:
        raise InvariantViolationError(f"{curriculum.code}: número de versión inválido")
    if not curriculum.title.strip():
        raise InvariantViolationError(f"{curriculum.code}: la versión no tiene título")
    if not curriculum.nodes:
        raise InvariantViolationError(f"{curriculum.code}: el temario no tiene ningún nodo")

    # Se reutiliza la validación del programa de perfiles: títulos, posiciones consecutivas,
    # profundidad, jerarquía de rutas y epígrafes sin hijos.
    validate_curriculum(curriculum.code, curriculum.nodes)

    for node in curriculum.nodes:
        if node.node_type is not NodeType.BLOCK:
            raise InvariantViolationError(
                f"{curriculum.code}: la raíz del temario debe ser un bloque, no {node.node_type}"
            )
        if node.depth != 0:
            raise InvariantViolationError(
                f"{curriculum.code}: el bloque {node.path} no está en la raíz"
            )
        for child in node.children:
            if child.node_type is not NodeType.TOPIC:
                raise InvariantViolationError(
                    f"{curriculum.code}: {child.path} cuelga de un bloque y no es un tema"
                )
            if child.children:
                raise InvariantViolationError(
                    f"{curriculum.code}: el tema {child.path} no puede tener hijos"
                )

    if len(curriculum.source.sha256) != 64:
        raise InvariantViolationError(
            f"{curriculum.code}: el sha256 de la fuente no tiene 64 caracteres"
        )
    for reference in curriculum.references:
        if reference.role not in CURRICULUM_REFERENCE_ROLES:
            raise InvariantViolationError(
                f"{curriculum.code}: papel de referencia desconocido: {reference.role}"
            )
        if not reference.convocation_code.strip():
            raise InvariantViolationError(f"{curriculum.code}: referencia sin convocatoria")
        if not reference.source_reference.strip():
            raise InvariantViolationError(
                f"{curriculum.code}: la referencia de {reference.convocation_code} "
                "no cita las bases"
            )
