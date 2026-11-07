"""Rutas del temario común: índice, versiones, referencias, particularidades y avance (B-004).

`/convocations/{id}/curriculum` sigue devolviendo el **programa publicado** (no se rompe lo que ya
llama); este router añade el temario que se estudia. El temario efectivo de una convocatoria aplica
sus particularidades (omite, renombra, renumera) sin copiar el temario.
"""

from __future__ import annotations

from fastapi import APIRouter, Query

from opofuente.api.deps import CurriculumServiceDep
from opofuente.api.error_responses import RESOURCE_ERRORS, WRITE_ERRORS
from opofuente.api.profile_schemas import CurriculumNodeSchema
from opofuente.api.temario_schemas import (
    AdjustmentSchema,
    AppearanceSchema,
    BlockProgressSchema,
    ConvocationIdentitySchema,
    CurriculumDetailSchema,
    CurriculumIdentitySchema,
    CurriculumNodeDetailSchema,
    CurriculumReferenceSchema,
    CurriculumSummarySchema,
    CurriculumVersionSchema,
    NodeMaterialPageSchema,
    NodeMaterialSchema,
    NodeQuestionPageSchema,
    NodeQuestionSchema,
    ProgressSchema,
    StudyMarkSchema,
    TemarioSchema,
)
from opofuente.application.curriculum_models import (
    AdjustmentView,
    AppearanceView,
    BlockProgressView,
    ConvocationIdentityView,
    CurriculumDetailView,
    CurriculumIdentityView,
    CurriculumNodeDetailView,
    CurriculumSummaryView,
    CurriculumVersionView,
    NodeMaterialPage,
    NodeQuestionPage,
    ProgressView,
    StudyMarkView,
    TemarioView,
)
from opofuente.application.read_models import NodeView

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
        studied_at=node.studied_at,
    )


def _version(version: CurriculumVersionView) -> CurriculumVersionSchema:
    return CurriculumVersionSchema(
        code=version.code,
        version_no=version.version_no,
        title=version.title,
        status=version.status,
    )


def _version_or_none(version: CurriculumVersionView | None) -> CurriculumVersionSchema | None:
    return None if version is None else _version(version)


def _summary(item: CurriculumSummaryView) -> CurriculumSummarySchema:
    return CurriculumSummarySchema(
        code=item.code,
        name=item.name,
        kind=item.kind,
        group_code=item.group_code,
        family=item.family,
        versions=[_version(version) for version in item.versions],
        active_version=_version_or_none(item.active_version),
    )


def _block(block: BlockProgressView) -> BlockProgressSchema:
    return BlockProgressSchema(
        block_id=block.block_id,
        path=block.path,
        title=block.title,
        position=block.position,
        topics_total=block.topics_total,
        topics_studied=block.topics_studied,
        topics_with_activity=block.topics_with_activity,
        percent=block.percent,
    )


def _progress(progress: ProgressView) -> ProgressSchema:
    return ProgressSchema(
        curriculum_code=progress.curriculum_code,
        version_code=progress.version_code,
        blocks=[_block(block) for block in progress.blocks],
        topics_total=progress.topics_total,
        topics_studied=progress.topics_studied,
        topics_with_activity=progress.topics_with_activity,
        percent=progress.percent,
    )


def _adjustment(adjustment: AdjustmentView) -> AdjustmentSchema:
    return AdjustmentSchema(
        kind=adjustment.kind,
        weight=adjustment.weight,
        official_code_override=adjustment.official_code_override,
        title_override=adjustment.title_override,
        evidence_quote=adjustment.evidence_quote,
    )


def _appearance(appearance: AppearanceView) -> AppearanceSchema:
    return AppearanceSchema(
        convocation_id=appearance.convocation_id,
        convocation_code=appearance.convocation_code,
        convocation_title=appearance.convocation_title,
        convocation_status=appearance.convocation_status,
        official_url=appearance.official_url,
        role=appearance.role,
        source_reference=appearance.source_reference,
        omitted=appearance.omitted,
        adjustments=[_adjustment(adjustment) for adjustment in appearance.adjustments],
    )


def _convocation(convocation: ConvocationIdentityView) -> ConvocationIdentitySchema:
    return ConvocationIdentitySchema(
        id=convocation.id,
        code=convocation.code,
        title=convocation.title,
        official_url=convocation.official_url,
        published_at=convocation.published_at,
        opposition_code=convocation.opposition_code,
        opposition_name=convocation.opposition_name,
        source_reference=convocation.source_reference,
    )


def _identity(curriculum: CurriculumIdentityView) -> CurriculumIdentitySchema:
    return CurriculumIdentitySchema(
        code=curriculum.code,
        name=curriculum.name,
        kind=curriculum.kind,
        version_code=curriculum.version_code,
        version_title=curriculum.version_title,
    )


def _detail(detail: CurriculumDetailView) -> CurriculumDetailSchema:
    return CurriculumDetailSchema(
        code=detail.code,
        name=detail.name,
        kind=detail.kind,
        group_code=detail.group_code,
        family=detail.family,
        versions=[_version(version) for version in detail.versions],
        active_version=_version_or_none(detail.active_version),
        counts=detail.counts,
        nodes=[_node(node) for node in detail.nodes],
        progress=None if detail.progress is None else _progress(detail.progress),
    )


@router.get(
    "/curricula",
    response_model=list[CurriculumSummarySchema],
    responses=RESOURCE_ERRORS,
    summary="Temarios disponibles (común y programas publicados)",
)
def list_curricula(
    service: CurriculumServiceDep,
    kind: str | None = Query(default=None, pattern="^(common|published)$"),
) -> list[CurriculumSummarySchema]:
    return [_summary(item) for item in service.list_curricula(kind=kind)]


@router.get(
    "/curricula/{curriculum_code}",
    response_model=CurriculumDetailSchema,
    responses=RESOURCE_ERRORS,
    summary="Temario con sus versiones y su árbol",
)
def get_curriculum(curriculum_code: str, service: CurriculumServiceDep) -> CurriculumDetailSchema:
    return _detail(service.get_curriculum(curriculum_code))


@router.get(
    "/curricula/{curriculum_code}/versions",
    response_model=list[CurriculumVersionSchema],
    responses=RESOURCE_ERRORS,
    summary="Versiones de un temario",
)
def list_curriculum_versions(
    curriculum_code: str, service: CurriculumServiceDep
) -> list[CurriculumVersionSchema]:
    return [_version(version) for version in service.list_versions(curriculum_code)]


@router.get(
    "/curricula/{curriculum_code}/progress",
    response_model=ProgressSchema,
    responses=RESOURCE_ERRORS,
    summary="Avance por bloque y total sobre el temario común",
)
def get_curriculum_progress(curriculum_code: str, service: CurriculumServiceDep) -> ProgressSchema:
    return _progress(service.get_progress(curriculum_code))


@router.get(
    "/convocations/{convocation_id}/temario",
    response_model=TemarioSchema,
    responses=RESOURCE_ERRORS,
    summary="Temario efectivo de la convocatoria, con sus particularidades",
)
def get_temario(convocation_id: str, service: CurriculumServiceDep) -> TemarioSchema:
    temario: TemarioView = service.get_temario(convocation_id)
    return TemarioSchema(
        convocation=_convocation(temario.convocation),
        curriculum=_identity(temario.curriculum),
        version=_version(temario.version),
        counts=temario.counts,
        nodes=[_node(node) for node in temario.nodes],
        omitted_topics=temario.omitted_topics,
    )


@router.get(
    "/convocations/{convocation_id}/references",
    response_model=list[CurriculumReferenceSchema],
    responses=RESOURCE_ERRORS,
    summary="Temarios que referencia una convocatoria, con su papel y su cita",
)
def list_references(
    convocation_id: str, service: CurriculumServiceDep
) -> list[CurriculumReferenceSchema]:
    return [
        CurriculumReferenceSchema(
            role=reference.role,
            curriculum_code=reference.curriculum_code,
            curriculum_name=reference.curriculum_name,
            curriculum_kind=reference.curriculum_kind,
            version_code=reference.version_code,
            version_no=reference.version_no,
            version_title=reference.version_title,
            source_reference=reference.source_reference,
        )
        for reference in service.list_references(convocation_id)
    ]


@router.get(
    "/curriculum-nodes/{node_id}",
    response_model=CurriculumNodeDetailSchema,
    responses=RESOURCE_ERRORS,
    summary="Nodo del temario con su ficha, sus convocatorias y sus particularidades",
)
def get_curriculum_node(
    node_id: str,
    service: CurriculumServiceDep,
    convocation_id: str | None = Query(default=None),
) -> CurriculumNodeDetailSchema:
    detail: CurriculumNodeDetailView = service.get_node(node_id, convocation_id=convocation_id)
    return CurriculumNodeDetailSchema(
        node=_node(detail.node),
        curriculum=_identity(detail.curriculum),
        convocation=None if detail.convocation is None else _convocation(detail.convocation),
        appears_in=[_appearance(appearance) for appearance in detail.appears_in],
        particularities=[_adjustment(particularity) for particularity in detail.particularities],
        studied_at=detail.studied_at,
        ancestors=[_node(ancestor) for ancestor in detail.ancestors],
    )


@router.get(
    "/curriculum-nodes/{node_id}/questions",
    response_model=NodeQuestionPageSchema,
    responses=RESOURCE_ERRORS,
    summary="Preguntas del banco catalogadas en el tema (sin clave)",
)
def get_node_questions(
    node_id: str,
    service: CurriculumServiceDep,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> NodeQuestionPageSchema:
    pagina: NodeQuestionPage = service.node_questions(node_id, limit=limit, offset=offset)
    return NodeQuestionPageSchema(
        node_id=pagina.node_id,
        total=pagina.total,
        limit=pagina.limit,
        offset=pagina.offset,
        questions=[
            NodeQuestionSchema(
                id=pregunta.id,
                question_set_id=pregunta.question_set_id,
                set_title=pregunta.set_title,
                stable_key=pregunta.stable_key,
                stem=pregunta.stem,
                question_type=pregunta.question_type,
                origin_type=pregunta.origin_type,
                position=pregunta.position,
                is_reserve=pregunta.is_reserve,
            )
            for pregunta in pagina.questions
        ],
    )


@router.get(
    "/curriculum-nodes/{node_id}/materials",
    response_model=NodeMaterialPageSchema,
    responses=RESOURCE_ERRORS,
    summary="Material de la biblioteca catalogado en el tema, con su cita",
)
def get_node_materials(
    node_id: str,
    service: CurriculumServiceDep,
    limit: int = Query(default=20, ge=1, le=100),
) -> NodeMaterialPageSchema:
    pagina: NodeMaterialPage = service.node_materials(node_id, limit=limit)
    return NodeMaterialPageSchema(
        node_id=pagina.node_id,
        total=pagina.total,
        materials=[
            NodeMaterialSchema(
                subject_type=material.subject_type,
                subject_id=material.subject_id,
                document_id=material.document_id,
                document_version_id=material.document_version_id,
                title=material.title,
                section_title=material.section_title,
                page=material.page,
                citation_label=material.citation_label,
                excerpt=material.excerpt,
                coverage_type=material.coverage_type,
            )
            for material in pagina.materials
        ],
    )


@router.post(
    "/curriculum-nodes/{node_id}/studied",
    response_model=StudyMarkSchema,
    responses=WRITE_ERRORS,
    summary="Marca un tema como estudiado (con su fecha)",
)
def mark_node_studied(node_id: str, service: CurriculumServiceDep) -> StudyMarkSchema:
    mark: StudyMarkView = service.mark_studied(node_id)
    return StudyMarkSchema(node_id=mark.node_id, studied_at=mark.studied_at)


@router.delete(
    "/curriculum-nodes/{node_id}/studied",
    status_code=204,
    responses=WRITE_ERRORS,
    summary="Retira la marca de estudiado",
)
def unmark_node_studied(node_id: str, service: CurriculumServiceDep) -> None:
    service.unmark_studied(node_id)
