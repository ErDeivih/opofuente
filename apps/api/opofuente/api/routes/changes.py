"""Rutas de cambios, dependencias y derivados (08_API-CONTRACT §11, RF-09).

Las cuatro rutas de §11 —listar, leer, confirmar y ver lo afectado— y cuatro **añadidas** para poder
trabajar con lo que se genera a partir del material:

- `POST /derived-artifacts` crea un resumen extractivo de unas secciones (es lo que se invalida
  cuando el material cambia: sin poder crear un derivado, `needs_review` no se podría demostrar);
- `GET /derived-artifacts` y `GET /derived-artifacts/{id}` listan y leen derivados, con lo que
  dependen y por qué están pendientes;
- `POST /derived-artifacts/{id}/resolution` cierra la revisión.

`GET /change-sets/{id}/affected` es la **simulación** del cambio normativo: se calcula todo y no se
aplica nada; confirmar es lo que acepta la versión, sustituye la anterior y marca los derivados.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query

from opofuente.api.change_schemas import (
    AffectedSchema,
    ArtifactKindName,
    ArtifactReviewName,
    ChangeOutcomeSchema,
    ChangeSetSchema,
    ChangeStatusName,
    CreateSummarySchema,
    DependentKindName,
    DerivedArtifactSchema,
    ReviewArtifactSchema,
    SectionChangeKindName,
    SectionChangeSchema,
)
from opofuente.api.deps import ChangeServiceDep
from opofuente.api.error_responses import INGESTION_WRITE_ERRORS, RESOURCE_ERRORS
from opofuente.application.change_models import (
    AffectedView,
    ChangeOutcome,
    ChangeSetView,
    DerivedArtifactView,
    SectionChangeView,
)

router = APIRouter(tags=["cambios"])

#: Traducciones del texto guardado a los valores que declara el contrato. Se escriben como mapas
#: tipados en lugar de `cast`: si llega un valor que no está aquí, se ve en la primera prueba.
_ESTADOS: dict[str, ChangeStatusName] = {
    "proposed": "proposed",
    "confirmed": "confirmed",
    "discarded": "discarded",
}
_TIPOS_DEPENDIENTE: dict[str, DependentKindName] = {
    "derived_artifact": "derived_artifact",
    "question_version": "question_version",
    "rag_answer": "rag_answer",
}
_REVISIONES: dict[str, ArtifactReviewName] = {
    "pending": "pending",
    "reviewed": "reviewed",
    "discarded": "discarded",
}
_SECCIONES: dict[str, SectionChangeKindName] = {
    "added": "added",
    "removed": "removed",
    "changed": "changed",
    "unchanged": "unchanged",
}


def _section(view: SectionChangeView) -> SectionChangeSchema:
    tipo = _SECCIONES.get(view.kind, "unchanged")
    return SectionChangeSchema(label=view.label, kind=tipo, left=view.left, right=view.right)


def _affected(view: AffectedView) -> AffectedSchema:
    tipo = _TIPOS_DEPENDIENTE.get(view.kind, "derived_artifact")
    return AffectedSchema(
        kind=tipo,
        id=view.id,
        title=view.title,
        sections=list(view.sections),
        reason=view.reason,
        reviewable=view.reviewable,
    )


def _change(view: ChangeSetView) -> ChangeSetSchema:
    # El estado y el tipo llegan como texto desde la base; el contrato declara los valores
    # posibles y aquí se traducen sin inventar ninguno.
    estado = _ESTADOS.get(view.status, "proposed")
    return ChangeSetSchema(
        id=view.id,
        document_id=view.document_id,
        document_title=view.document_title,
        previous_version_id=view.previous_version_id,
        previous_version_label=view.previous_version_label,
        new_version_id=view.new_version_id,
        new_version_label=view.new_version_label,
        status=estado,
        created_at=view.created_at,
        confirmed_at=view.confirmed_at,
        discarded_at=view.discarded_at,
        reviewed_by=view.reviewed_by,
        sections=[_section(seccion) for seccion in view.sections],
        affected=[_affected(item) for item in view.affected],
        sections_changed=view.sections_changed,
        sections_added=view.sections_added,
        sections_removed=view.sections_removed,
        sections_unchanged=view.sections_unchanged,
        effect_note=view.effect_note,
        notes=list(view.notes),
    )


def _outcome(view: ChangeOutcome) -> ChangeOutcomeSchema:
    return ChangeOutcomeSchema(
        change=_change(view.change),
        applied=view.applied,
        reason=view.reason,
        marked=list(view.marked),
        superseded_version_id=view.superseded_version_id,
    )


def _artifact(view: DerivedArtifactView) -> DerivedArtifactSchema:
    # Hoy solo hay un tipo de derivado (resumen extractivo); el estado sí lo elige la revisión.
    tipo: ArtifactKindName = "summary"
    revision = _REVISIONES.get(view.review_status, "pending")
    return DerivedArtifactSchema(
        id=view.id,
        kind=tipo,
        title=view.title,
        content=view.content,
        document_version_id=view.document_version_id,
        document_id=view.document_id,
        document_title=view.document_title,
        generator=view.generator,
        prompt_template_version=view.prompt_template_version,
        model=view.model,
        review_status=revision,
        needs_review=view.needs_review,
        needs_review_reason=view.needs_review_reason,
        needs_review_at=view.needs_review_at,
        reviewed_at=view.reviewed_at,
        created_at=view.created_at,
        updated_at=view.updated_at,
        sections=list(view.sections),
    )


@router.get(
    "/change-sets",
    response_model=list[ChangeSetSchema],
    responses=RESOURCE_ERRORS,
    summary="Los cambios de versión propuestos, confirmados o descartados",
)
def list_change_sets(
    service: ChangeServiceDep,
    document_id: Annotated[str | None, Query()] = None,
    status: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
) -> list[ChangeSetSchema]:
    return [
        _change(vista)
        for vista in service.change_sets(document_id=document_id, status=status, limit=limit)
    ]


@router.get(
    "/change-sets/{change_id}",
    response_model=ChangeSetSchema,
    responses=RESOURCE_ERRORS,
    summary="Un cambio con su diff por sección y sus derivados afectados",
)
def get_change_set(change_id: str, service: ChangeServiceDep) -> ChangeSetSchema:
    return _change(service.change_set(change_id))


@router.get(
    "/change-sets/{change_id}/affected",
    response_model=ChangeSetSchema,
    responses=RESOURCE_ERRORS,
    summary="La simulación del cambio: qué se invalidaría, sin aplicar nada",
)
def get_change_set_affected(change_id: str, service: ChangeServiceDep) -> ChangeSetSchema:
    """Nada de lo que se ve aquí ha ocurrido todavía: el cambio se aplica al confirmarlo."""
    return _change(service.affected(change_id))


@router.post(
    "/change-sets/{change_id}/confirm",
    response_model=ChangeOutcomeSchema,
    responses=INGESTION_WRITE_ERRORS,
    summary="Confirma el cambio: acepta la versión, sustituye la anterior y marca derivados",
)
def confirm_change_set(change_id: str, service: ChangeServiceDep) -> ChangeOutcomeSchema:
    """La relación de versión la confirma una persona; la anterior no se borra."""
    return _outcome(service.confirm(change_id))


@router.post(
    "/change-sets/{change_id}/discard",
    response_model=ChangeOutcomeSchema,
    responses=INGESTION_WRITE_ERRORS,
    summary="Descarta la propuesta sin invalidar nada (ruta añadida a §11)",
)
def discard_change_set(change_id: str, service: ChangeServiceDep) -> ChangeOutcomeSchema:
    return _outcome(service.discard(change_id))


@router.post(
    "/derived-artifacts",
    response_model=DerivedArtifactSchema,
    status_code=201,
    responses=INGESTION_WRITE_ERRORS,
    summary="Crea un resumen extractivo de unas secciones (ruta añadida a §11)",
)
def create_derived_artifact(
    request: CreateSummarySchema, service: ChangeServiceDep
) -> DerivedArtifactSchema:
    """Sin modelo: junta los fragmentos de las secciones elegidas con su cita."""
    return _artifact(
        service.create_summary(
            document_version_id=request.document_version_id,
            section_ids=request.section_ids,
            title=request.title,
        )
    )


@router.get(
    "/derived-artifacts",
    response_model=list[DerivedArtifactSchema],
    responses=RESOURCE_ERRORS,
    summary="Los derivados del material y lo que está pendiente de revisar (añadida a §11)",
)
def list_derived_artifacts(
    service: ChangeServiceDep,
    document_version_id: Annotated[str | None, Query()] = None,
    needs_review: Annotated[bool | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 200,
) -> list[DerivedArtifactSchema]:
    return [
        _artifact(vista)
        for vista in service.artifacts(
            document_version_id=document_version_id, needs_review=needs_review, limit=limit
        )
    ]


@router.get(
    "/derived-artifacts/{artifact_id}",
    response_model=DerivedArtifactSchema,
    responses=RESOURCE_ERRORS,
    summary="Un derivado con sus secciones de origen (ruta añadida a §11)",
)
def get_derived_artifact(artifact_id: str, service: ChangeServiceDep) -> DerivedArtifactSchema:
    return _artifact(service.artifact(artifact_id))


@router.post(
    "/derived-artifacts/{artifact_id}/resolution",
    response_model=DerivedArtifactSchema,
    responses=INGESTION_WRITE_ERRORS,
    summary="Cierra la revisión de un derivado (ruta añadida a §11)",
)
def resolve_derived_artifact(
    artifact_id: str, request: ReviewArtifactSchema, service: ChangeServiceDep
) -> DerivedArtifactSchema:
    return _artifact(service.review_artifact(artifact_id, resolution=request.resolution))
