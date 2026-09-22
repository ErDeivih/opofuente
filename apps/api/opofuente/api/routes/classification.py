"""Rutas de clasificación y revisión (contrato de la API §3, §6 y §7).

Cada decisión es explícita y auditable: aceptar, rechazar y deshacer escriben su evento con el
antes/después sanitizado. Una decisión que no se puede aplicar (transición inválida, nodo ausente)
responde 409 con el motivo, en lugar de aceptar en silencio algo que no se ha aplicado.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query

from opofuente.api.classification_schemas import (
    AcceptedClassificationSchema,
    AcceptedValueSchema,
    AlternativeSchema,
    BulkDecisionRequestSchema,
    BulkDecisionResponseSchema,
    CoverageNodeSchema,
    CoverageSchema,
    DecisionOutcomeSchema,
    DecisionRequestSchema,
    DuplicateClusterSchema,
    DuplicateMemberSchema,
    MappingSchema,
    ProposalPageSchema,
    ProposalSchema,
    ResolveDuplicateRequestSchema,
    ReviewGroupSchema,
    mapping_schema,
)
from opofuente.api.deps import ClassificationServiceDep, JobServiceDep
from opofuente.api.error_responses import INGESTION_WRITE_ERRORS, RESOURCE_ERRORS
from opofuente.api.ingestion_schemas import JobSchema
from opofuente.application.read_models import (
    BulkDecisionResult,
    DecisionOutcome,
    DuplicateClusterView,
    DuplicateMemberView,
    JobView,
    MappingView,
    NodeCoverageView,
    ProposalPage,
    ProposalView,
    ReviewGroupView,
)
from opofuente.domain.classification import CoverageType
from opofuente.domain.errors import ClassificationConflictError, NotFoundError

router = APIRouter(tags=["clasificación"])


def _proposal(view: ProposalView) -> ProposalSchema:
    return ProposalSchema(
        id=view.id,
        subject_type=view.subject_type,  # type: ignore[arg-type]
        subject_id=view.subject_id,
        subject_label=view.subject_label,
        axis=view.axis,  # type: ignore[arg-type]
        proposed_value=view.proposed_value,
        value_label=view.value_label,
        confidence=view.confidence,
        band=view.band,  # type: ignore[arg-type]
        is_critical=view.is_critical,
        status=view.status,  # type: ignore[arg-type]
        engine_name=view.engine_name,
        engine_version=view.engine_version,
        alternatives=[
            AlternativeSchema(value=alternativa.value, confidence=alternativa.confidence)
            for alternativa in view.alternatives
        ],
        evidence=list(view.evidence),
        created_at=view.created_at,
        decided_at=view.decided_at,
        decision_note=view.decision_note,
    )


def _page(page: ProposalPage) -> ProposalPageSchema:
    return ProposalPageSchema(
        proposals=[_proposal(view) for view in page.proposals],
        total=page.total,
        limit=page.limit,
        offset=page.offset,
    )


def _group(view: ReviewGroupView) -> ReviewGroupSchema:
    return ReviewGroupSchema(
        key=view.key,
        subject_type=view.subject_type,
        axis=view.axis,
        proposed_value=view.proposed_value,
        label=view.label,
        proposal_ids=list(view.proposal_ids),
        size=view.size,
        min_confidence=view.min_confidence,
        max_confidence=view.max_confidence,
        is_critical=view.is_critical,
    )


def _outcome(result: DecisionOutcome) -> DecisionOutcomeSchema:
    return DecisionOutcomeSchema(
        proposal_id=result.proposal_id,
        status=result.status,
        applied=result.applied,
        mapping_id=result.mapping_id,
        audit_event_id=result.audit_event_id,
        reason=result.reason,
    )


def _mapping(view: MappingView) -> MappingSchema:
    """Un mapeo, en el formato único del contrato: el mismo lo sirva quien lo sirva."""
    return mapping_schema(view)


def _member(miembro: DuplicateMemberView) -> DuplicateMemberSchema:
    return DuplicateMemberSchema(
        subject_type=miembro.subject_type,
        subject_id=miembro.subject_id,
        subject_label=miembro.subject_label,
        similarity=miembro.similarity,
        is_representative=miembro.is_representative,
    )


def _cluster(view: DuplicateClusterView) -> DuplicateClusterSchema:
    return DuplicateClusterSchema(
        id=view.id,
        kind=view.kind,  # type: ignore[arg-type]
        relation=view.relation,  # type: ignore[arg-type]
        signature=view.signature,
        status=view.status,  # type: ignore[arg-type]
        members=[_member(miembro) for miembro in view.members],
        created_at=view.created_at,
        resolved_at=view.resolved_at,
        resolution_note=view.resolution_note,
    )


def _assert_applied(result: DecisionOutcome) -> DecisionOutcome:
    """Una decisión que no se aplicó es un conflicto, y se dice por qué (409)."""
    if not result.applied:
        raise ClassificationConflictError(result.reason or "La decisión no se pudo aplicar")
    return result


@router.get(
    "/classification-proposals",
    response_model=ProposalPageSchema,
    responses=RESOURCE_ERRORS,
    summary="Propuestas de clasificación, con su banda y su evidencia",
)
def list_proposals(
    service: ClassificationServiceDep,
    subject_type: Annotated[str | None, Query()] = None,
    subject_id: Annotated[str | None, Query()] = None,
    axis: Annotated[str | None, Query()] = None,
    status: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ProposalPageSchema:
    return _page(
        service.list_proposals(
            subject_type=subject_type,
            subject_id=subject_id,
            axis=axis,
            status=status,
            limit=limit,
            offset=offset,
        )
    )


@router.get(
    "/classification-proposals/{proposal_id}",
    response_model=ProposalSchema,
    responses=RESOURCE_ERRORS,
    summary="Una propuesta concreta",
)
def get_proposal(proposal_id: str, service: ClassificationServiceDep) -> ProposalSchema:
    view = service.get_proposal(proposal_id)
    if view is None:
        raise NotFoundError("propuesta", proposal_id)
    return _proposal(view)


@router.post(
    "/classification-proposals/{proposal_id}/accept",
    response_model=DecisionOutcomeSchema,
    responses=INGESTION_WRITE_ERRORS,
    summary="Acepta una propuesta (y crea el mapeo si es de tema)",
)
def accept_proposal(
    proposal_id: str, request: DecisionRequestSchema, service: ClassificationServiceDep
) -> DecisionOutcomeSchema:
    resultado = service.decide(
        proposal_id,
        decision="accepted",
        note=request.note,
        override_value=request.override_value,
        coverage_type=CoverageType(request.coverage_type),
    )
    return _outcome(_assert_applied(resultado))


@router.post(
    "/classification-proposals/{proposal_id}/reject",
    response_model=DecisionOutcomeSchema,
    responses=INGESTION_WRITE_ERRORS,
    summary="Rechaza una propuesta (y retira el mapeo que hubiera salido de ella)",
)
def reject_proposal(
    proposal_id: str, request: DecisionRequestSchema, service: ClassificationServiceDep
) -> DecisionOutcomeSchema:
    resultado = service.decide(
        proposal_id,
        decision="rejected",
        note=request.note,
        override_value=request.override_value,
        coverage_type=CoverageType(request.coverage_type),
    )
    return _outcome(_assert_applied(resultado))


@router.post(
    "/classification-proposals/bulk-decision",
    response_model=BulkDecisionResponseSchema,
    responses=INGESTION_WRITE_ERRORS,
    summary="Decide en lote, con excepciones: nunca es todo-o-nada",
)
def bulk_decision(
    request: BulkDecisionRequestSchema, service: ClassificationServiceDep
) -> BulkDecisionResponseSchema:
    resultado: BulkDecisionResult = service.bulk_decide(
        request.proposal_ids,
        decision=request.decision,
        note=request.note,
        overrides=request.overrides,
        excluded=request.excluded,
    )
    return BulkDecisionResponseSchema(
        outcomes=[_outcome(outcome) for outcome in resultado.outcomes],
        applied=resultado.applied,
        conflicts=resultado.conflicts,
        requested=resultado.requested,
        excluded=list(resultado.excluded),
    )


@router.post(
    "/classification-decisions/{decision_id}/undo",
    response_model=DecisionOutcomeSchema,
    responses=INGESTION_WRITE_ERRORS,
    summary="Deshace una decisión y devuelve la propuesta a la cola",
)
def undo_decision(decision_id: str, service: ClassificationServiceDep) -> DecisionOutcomeSchema:
    """Deshace la última decisión de una propuesta.

    `{decision_id}` es el identificador de la decisión que devuelve la propia respuesta de decidir
    (`audit_event_id`). También se admite el identificador de la propuesta: la interfaz trabaja con
    propuestas y la API no le obliga a recordar la traza de auditoría para deshacer.
    """
    return _outcome(_assert_applied(service.undo(decision_id)))


@router.get(
    "/review-groups",
    response_model=list[ReviewGroupSchema],
    responses=RESOURCE_ERRORS,
    summary="Grupos de revisión: propuestas pendientes agrupadas por eje y valor",
)
def review_groups(service: ClassificationServiceDep) -> list[ReviewGroupSchema]:
    return [_group(grupo) for grupo in service.review_groups()]


@router.get(
    "/curriculum-nodes/{node_id}/coverage",
    response_model=CoverageSchema,
    responses=RESOURCE_ERRORS,
    summary="Cobertura de un nodo y de su subárbol (provisional y aceptada, separadas)",
)
def node_coverage(node_id: str, service: ClassificationServiceDep) -> CoverageSchema:
    view: NodeCoverageView | None = service.node_coverage(node_id)
    if view is None:
        raise NotFoundError("nodo del programa", node_id)
    return CoverageSchema(
        node_id=view.node_id,
        path=view.path,
        title=view.title,
        provisional=view.provisional,
        accepted=view.accepted,
        unclassified_subjects=view.unclassified_subjects,
        materials_total=view.materials_total,
        subtree=[
            CoverageNodeSchema(
                node_id=nodo.node_id,
                path=nodo.path,
                title=nodo.title,
                depth=nodo.depth,
                provisional=nodo.provisional,
                accepted=nodo.accepted,
                materials=list(nodo.materials),
            )
            for nodo in view.subtree
        ],
    )


@router.get(
    "/mappings",
    response_model=list[MappingSchema],
    responses=RESOURCE_ERRORS,
    summary="Mapeos de programa de un sujeto",
)
def list_mappings(
    service: ClassificationServiceDep,
    subject_type: Annotated[str | None, Query()] = None,
    subject_id: Annotated[str | None, Query()] = None,
) -> list[MappingSchema]:
    return [
        _mapping(mapeo)
        for mapeo in service.mappings(subject_type=subject_type, subject_id=subject_id)
    ]


@router.delete(
    "/curriculum-mappings/{mapping_id}",
    status_code=204,
    responses=INGESTION_WRITE_ERRORS,
    summary="Retira un mapeo (queda auditado)",
)
def delete_mapping(mapping_id: str, service: ClassificationServiceDep) -> None:
    if not service.delete_mapping(mapping_id):
        raise NotFoundError("mapeo", mapping_id)


@router.get(
    "/duplicate-clusters",
    response_model=list[DuplicateClusterSchema],
    responses=RESOURCE_ERRORS,
    summary="Grupos de material repetido o muy parecido",
)
def list_duplicate_clusters(
    service: ClassificationServiceDep, status: Annotated[str | None, Query()] = None
) -> list[DuplicateClusterSchema]:
    return [_cluster(view) for view in service.list_duplicate_clusters(status=status)]


@router.post(
    "/duplicate-clusters/{cluster_id}/resolve",
    response_model=DuplicateClusterSchema,
    responses=INGESTION_WRITE_ERRORS,
    summary="Resuelve un grupo de duplicados (nunca borra nada por sí solo)",
)
def resolve_duplicate_cluster(
    cluster_id: str, request: ResolveDuplicateRequestSchema, service: ClassificationServiceDep
) -> DuplicateClusterSchema:
    view = service.resolve_duplicate_cluster(
        cluster_id, relation=request.relation, note=request.note
    )
    if view is None:
        raise NotFoundError("grupo de duplicados", cluster_id)
    return _cluster(view)


@router.get(
    "/classification/{subject_type}/{subject_id}",
    response_model=AcceptedClassificationSchema,
    responses=RESOURCE_ERRORS,
    summary="Clasificación vigente de un material (lo aceptado y lo provisional)",
)
def accepted_classification(
    subject_type: str, subject_id: str, service: ClassificationServiceDep
) -> AcceptedClassificationSchema:
    """Lo que consta de un material: hace que aceptar una propuesta **se note** en el producto.

    Devuelve solo lo decidido —lo aceptado por el usuario y lo aplicado provisionalmente por banda
    alta— con su etiqueta legible y separado, porque «provisional» significa «revisable».
    """
    view = service.accepted_classification(subject_type=subject_type, subject_id=subject_id)
    return AcceptedClassificationSchema(
        subject_type=view.subject_type,
        subject_id=view.subject_id,
        subject_label=view.subject_label,
        pending_review=view.pending_review,
        values=[
            AcceptedValueSchema(
                axis=valor.axis,
                value=valor.value,
                value_label=valor.value_label,
                status=valor.status,  # type: ignore[arg-type]
                confidence=valor.confidence,
                is_critical=valor.is_critical,
                decided_at=valor.decided_at,
            )
            for valor in view.values
        ],
    )


def _job(job: JobView) -> JobSchema:
    """El trabajo encolado, con la misma forma que sirve la API de ingestión: es el mismo."""
    return JobSchema(
        id=job.id,
        job_type=job.job_type,
        status=job.status,
        progress=job.progress,
        attempts=job.attempts,
        max_attempts=job.max_attempts,
        created_at=job.created_at,
        updated_at=job.updated_at,
        step=job.step,
        error_code=job.error_code,
        error_message=job.error_message,
        started_at=job.started_at,
        finished_at=job.finished_at,
        cancel_requested=job.cancel_requested,
    )


@router.post(
    "/classification-runs",
    response_model=JobSchema,
    status_code=202,
    responses=INGESTION_WRITE_ERRORS,
    summary="Encola una pasada de clasificación del corpus (idempotente)",
)
def run_classification(service: ClassificationServiceDep, jobs: JobServiceDep) -> JobSchema:
    """Clasificar dejó de ser una petición larga: se **encola** y se sigue por su trabajo.

    Con el material real del propietario una pasada tarda 46,7 segundos: tener eso dentro de una
    petición dejaba el botón bloqueado sin decir en qué iba (DEBT-024). Ahora responde **202** con
    el trabajo recién encolado —su `step` dirá el resumen al terminar— y la pantalla lo sigue.

    Si ya hay una pasada viva, devuelve **esa**: pulsar dos veces no clasifica dos veces.
    """
    trabajo = service.enqueue_run()
    return _job(jobs.get_job(trabajo.id))
