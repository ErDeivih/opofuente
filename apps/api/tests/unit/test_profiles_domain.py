"""Pruebas unitarias del dominio de perfiles: programa y reglas de examen."""

from __future__ import annotations

import pytest

from opofuente.domain.errors import InvariantViolationError
from opofuente.domain.profiles import (
    CurriculumNode,
    ExamPart,
    ExamRule,
    NodeType,
    PartFormat,
    PartKind,
    RuleKind,
    count_by_type,
    flatten,
    validate_curriculum,
    validate_exam,
)


def _block(code: str, position: int, children: tuple[CurriculumNode, ...] = ()) -> CurriculumNode:
    return CurriculumNode(
        node_type=NodeType.BLOCK,
        official_code=code,
        title=f"Bloque {code}",
        position=position,
        path=code,
        depth=0,
        children=children,
    )


def _topic(block_code: str, position: int) -> CurriculumNode:
    return CurriculumNode(
        node_type=NodeType.TOPIC,
        official_code=str(position),
        title=f"Tema {position}",
        position=position,
        path=f"{block_code}.{position}",
        depth=1,
    )


def _part(code: str, **overrides: object) -> ExamPart:
    base: dict[str, object] = {
        "code": code,
        "name": code,
        "kind": PartKind.TEST,
        "format": PartFormat.SINGLE_CHOICE,
        "position": 1,
        "ordinary_items": 10,
        "evidence_quote": "cita",
    }
    base.update(overrides)
    return ExamPart(**base)


def _rule(code: str, **overrides: object) -> ExamRule:
    base: dict[str, object] = {
        "code": code,
        "kind": RuleKind.BOOLEAN,
        "value_text": "true",
        "description": "descripción",
        "evidence_quote": "cita",
    }
    base.update(overrides)
    return ExamRule(**base)


def test_arbol_valido_se_acepta() -> None:
    nodes = (_block("I", 1, (_topic("I", 1), _topic("I", 2))), _block("II", 2, (_topic("II", 1),)))
    validate_curriculum("demo", nodes)
    assert count_by_type(nodes) == {NodeType.BLOCK: 2, NodeType.TOPIC: 3, NodeType.EPIGRAPH: 0}
    assert [node.path for node, _parent in flatten(nodes)] == ["I", "I.1", "I.2", "II", "II.1"]


def test_programa_vacio_falla() -> None:
    with pytest.raises(InvariantViolationError):
        validate_curriculum("demo", ())


def test_rutas_repetidas_fallan() -> None:
    nodes = (_block("I", 1, (_topic("I", 1), _topic("I", 1))),)
    with pytest.raises(InvariantViolationError):
        validate_curriculum("demo", nodes)


def test_posiciones_no_consecutivas_fallan() -> None:
    nodes = (_block("I", 1), _block("II", 3))
    with pytest.raises(InvariantViolationError):
        validate_curriculum("demo", nodes)


def test_ruta_que_no_cuelga_de_su_padre_falla() -> None:
    malo = CurriculumNode(
        node_type=NodeType.TOPIC,
        official_code="1",
        title="Tema",
        position=1,
        path="II.1",
        depth=1,
    )
    with pytest.raises(InvariantViolationError):
        validate_curriculum("demo", (_block("I", 1, (malo,)),))


def test_epigrafe_con_hijos_falla() -> None:
    """Un epígrafe es hoja: el modelo solo distingue bloque, tema y epígrafe."""
    epigrafe_con_hijo = CurriculumNode(
        node_type=NodeType.EPIGRAPH,
        official_code="1",
        title="Epígrafe",
        position=1,
        path="I.1.1",
        depth=2,
        children=(
            CurriculumNode(
                node_type=NodeType.EPIGRAPH,
                official_code="1",
                title="Subepígrafe",
                position=1,
                path="I.1.1.1",
                depth=3,
            ),
        ),
    )
    arbol = (
        CurriculumNode(
            node_type=NodeType.BLOCK,
            official_code="I",
            title="Bloque",
            position=1,
            path="I",
            depth=0,
            children=(
                CurriculumNode(
                    node_type=NodeType.TOPIC,
                    official_code="1",
                    title="Tema",
                    position=1,
                    path="I.1",
                    depth=1,
                    children=(epigrafe_con_hijo,),
                ),
            ),
        ),
    )
    with pytest.raises(InvariantViolationError):
        validate_curriculum("demo", arbol)


def test_examen_valido_se_acepta() -> None:
    parts = (
        _part("grupo", kind=PartKind.GROUP, format=None, ordinary_items=None),
        _part("p1", parent_code="grupo", score_min=0, score_max=50, pass_score=25),
    )
    validate_exam("demo", parts, (_rule("r1"),))


def test_examen_sin_partes_falla() -> None:
    with pytest.raises(InvariantViolationError):
        validate_exam("demo", (), ())


def test_parte_que_cuelga_de_un_padre_inexistente_falla() -> None:
    with pytest.raises(InvariantViolationError):
        validate_exam("demo", (_part("p1", parent_code="nada"),), ())


def test_agrupacion_sin_pruebas_falla() -> None:
    parts = (_part("grupo", kind=PartKind.GROUP, format=None, ordinary_items=None),)
    with pytest.raises(InvariantViolationError):
        validate_exam("demo", parts, ())


def test_prueba_sin_formato_falla() -> None:
    with pytest.raises(InvariantViolationError):
        validate_exam("demo", (_part("p1", format=None),), ())


def test_minimo_fuera_de_rango_falla() -> None:
    parts = (
        _part("grupo", kind=PartKind.GROUP, format=None, ordinary_items=None),
        _part("p1", parent_code="grupo", score_min=0, score_max=50, pass_score=80),
    )
    with pytest.raises(InvariantViolationError):
        validate_exam("demo", parts, ())


def test_cita_obligatoria_en_partes_y_reglas() -> None:
    parts = (
        _part("grupo", kind=PartKind.GROUP, format=None, ordinary_items=None, evidence_quote=""),
        _part("p1", parent_code="grupo"),
    )
    with pytest.raises(InvariantViolationError):
        validate_exam("demo", parts, ())
    with pytest.raises(InvariantViolationError):
        validate_exam("demo", (_part("p1", parent_code=None),), (_rule("r1", evidence_quote=""),))


def test_regla_booleana_con_valor_invalido_falla() -> None:
    with pytest.raises(InvariantViolationError):
        validate_exam("demo", (_part("p1", parent_code=None),), (_rule("r1", value_text="quizá"),))
