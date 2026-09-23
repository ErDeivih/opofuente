"""Rutas de perfiles: oposiciones, convocatorias, programa y reglas de examen (08_API-CONTRACT §3).

Solo lectura salvo dos rutas de escritura: `POST /oppositions/{id}/activate`, que elige la oposición
activa, y `POST /convocations/{id}/activate`, que elige la convocatoria vigente de esa oposición (y
por tanto es también la primera ruta de escritura del proyecto: sobre ellas actúa la comprobación de
Origin).

La cobertura de un nodo **no** vive aquí: se calcula en `GET /curriculum-nodes/{id}/coverage`
(dominio de clasificación y revisión, S04) a partir de los mapeos aceptados, y esta respuesta no la
duplica para no dar dos cifras distintas de lo mismo.
"""

from __future__ import annotations

from fastapi import APIRouter

from opofuente.api.deps import ProfilesServiceDep
from opofuente.api.error_responses import (
    ACTIVATION_ERRORS,
    BASE_ERRORS,
    RESOURCE_ERRORS,
    WRITE_ERRORS,
)
from opofuente.api.profile_schemas import (
    ActiveConvocationSchema,
    ConvocationDetailSchema,
    ConvocationReferenceSchema,
    CurriculumNodeDetailSchema,
    CurriculumNodeSchema,
    CurriculumSchema,
    ExamPartSchema,
    ExamRuleSchema,
    OppositionDetailSchema,
    OppositionSchema,
)
from opofuente.application.read_models import (
    ConvocationDetail,
    ConvocationSummary,
    CurriculumView,
    NodeDetail,
    NodeView,
    OppositionSummary,
)

router = APIRouter()


def _node(node: NodeView) -> CurriculumNodeSchema:
    return CurriculumNodeSchema(
        id=node.id,
        node_type=node.node_type,
        official_code=node.official_code,
        title=node.title,
        description=node.description,
        position=node.position,
        path=node.path,
        depth=node.depth,
        children=[_node(child) for child in node.children],
    )


def _convocation_reference(summary: ConvocationSummary) -> ConvocationReferenceSchema:
    return ConvocationReferenceSchema(
        id=summary.id,
        code=summary.code,
        title=summary.title,
        official_url=summary.official_url,
        published_at=summary.published_at,
        exam_date=summary.exam_date,
        status=summary.status,
    )


def _opposition(summary: OppositionSummary) -> OppositionSchema:
    active = None
    if (
        summary.convocation_id
        and summary.convocation_code
        and summary.convocation_status
        and summary.convocation_published_at
    ):
        active = ActiveConvocationSchema(
            id=summary.convocation_id,
            code=summary.convocation_code,
            published_at=summary.convocation_published_at,
            status=summary.convocation_status,
        )
    return OppositionSchema(
        id=summary.id,
        code=summary.code,
        name=summary.name,
        description=summary.description,
        active=summary.active,
        active_convocation=active,
    )


@router.get(
    "/oppositions",
    response_model=list[OppositionSchema],
    responses=BASE_ERRORS,
    summary="Oposiciones disponibles y su convocatoria activa",
)
def list_oppositions(service: ProfilesServiceDep) -> list[OppositionSchema]:
    return [_opposition(summary) for summary in service.list_oppositions()]


@router.get(
    "/oppositions/{opposition_id}",
    response_model=OppositionDetailSchema,
    responses=RESOURCE_ERRORS,
    summary="Detalle de una oposición con sus convocatorias",
)
def get_opposition(opposition_id: str, service: ProfilesServiceDep) -> OppositionDetailSchema:
    detail = service.get_opposition(opposition_id)
    return OppositionDetailSchema(
        opposition=_opposition(detail.opposition),
        convocations=[_convocation_reference(row) for row in detail.convocations],
    )


@router.post(
    "/oppositions/{opposition_id}/activate",
    response_model=OppositionSchema,
    responses=WRITE_ERRORS,
    summary="Activa una oposición (desactiva el resto)",
)
def activate_opposition(opposition_id: str, service: ProfilesServiceDep) -> OppositionSchema:
    return _opposition(service.activate_opposition(opposition_id))


@router.get(
    "/oppositions/{opposition_id}/convocations",
    response_model=list[ConvocationReferenceSchema],
    responses=RESOURCE_ERRORS,
    summary="Convocatorias de una oposición",
)
def list_convocations(
    opposition_id: str, service: ProfilesServiceDep
) -> list[ConvocationReferenceSchema]:
    return [_convocation_reference(row) for row in service.list_convocations(opposition_id)]


@router.post(
    "/convocations/{convocation_id}/activate",
    response_model=ConvocationReferenceSchema,
    responses=ACTIVATION_ERRORS,
    summary="Convierte una convocatoria en la vigente de su oposición",
)
def activate_convocation(
    convocation_id: str, service: ProfilesServiceDep
) -> ConvocationReferenceSchema:
    """Elige con qué convocatoria trabaja la aplicación.

    La vigente anterior queda «superada» (sigue visible y se puede volver a ella). Se rechaza con
    409 si la convocatoria está en borrador, archivada o no tiene programa sembrado: la aplicación
    no ofrece como vigente algo que no puede mostrar.
    """
    return _convocation_reference(service.activate_convocation(convocation_id))


@router.get(
    "/convocations/{convocation_id}",
    response_model=ConvocationDetailSchema,
    responses=RESOURCE_ERRORS,
    summary="Convocatoria con sus partes y sus reglas de examen",
)
def get_convocation(convocation_id: str, service: ProfilesServiceDep) -> ConvocationDetailSchema:
    detail: ConvocationDetail = service.get_convocation(convocation_id)
    return ConvocationDetailSchema(
        id=detail.summary.id,
        code=detail.summary.code,
        title=detail.summary.title,
        official_url=detail.summary.official_url,
        published_at=detail.summary.published_at,
        exam_date=detail.summary.exam_date,
        exam_date_note=detail.exam_date_note,
        status=detail.summary.status,
        source_reference=detail.source_reference,
        opposition_id=detail.summary.opposition_id,
        opposition_code=detail.opposition_code,
        opposition_name=detail.opposition_name,
        parts=[
            ExamPartSchema(
                code=part.code,
                name=part.name,
                kind=part.kind,
                format=part.format,
                position=part.position,
                parent_code=part.parent_code,
                ordinary_items=part.ordinary_items,
                reserve_items=part.reserve_items,
                options_per_question=part.options_per_question,
                score_min=part.score_min,
                score_max=part.score_max,
                pass_score=part.pass_score,
                wrong_penalty_fraction=part.wrong_penalty_fraction,
                fail_if_errors_gte=part.fail_if_errors_gte,
                time_minutes=part.time_minutes,
                structure_note=part.structure_note,
                notes=part.notes,
                evidence_quote=part.evidence_quote,
            )
            for part in detail.parts
        ],
        rules=[
            ExamRuleSchema(
                code=rule.code,
                kind=rule.kind,
                value_text=rule.value_text,
                description=rule.description,
                evidence_quote=rule.evidence_quote,
            )
            for rule in detail.rules
        ],
    )


@router.get(
    "/convocations/{convocation_id}/curriculum",
    response_model=CurriculumSchema,
    responses=RESOURCE_ERRORS,
    summary="Árbol del programa oficial",
)
def get_curriculum(convocation_id: str, service: ProfilesServiceDep) -> CurriculumSchema:
    view: CurriculumView = service.get_curriculum(convocation_id)
    return CurriculumSchema(
        convocation_id=view.convocation_id,
        convocation_code=view.convocation_code,
        opposition_code=view.opposition_code,
        counts=view.counts,
        nodes=[_node(node) for node in view.nodes],
    )


@router.get(
    "/curriculum-nodes/{node_id}",
    response_model=CurriculumNodeDetailSchema,
    responses=RESOURCE_ERRORS,
    summary="Nodo del programa con su procedencia",
)
def get_curriculum_node(node_id: str, service: ProfilesServiceDep) -> CurriculumNodeDetailSchema:
    detail: NodeDetail = service.get_node(node_id)
    return CurriculumNodeDetailSchema(
        node=_node(detail.node),
        convocation_id=detail.convocation_id,
        convocation_code=detail.convocation_code,
        convocation_title=detail.convocation_title,
        official_url=detail.official_url,
        published_at=detail.published_at,
        opposition_code=detail.opposition_code,
        opposition_name=detail.opposition_name,
        source_reference=detail.source_reference,
        ancestors=[_node(ancestor) for ancestor in detail.ancestors],
    )
