"""Rutas de errores, repaso y dominio (08_API-CONTRACT §10).

Las cuatro rutas de §10 —clasificar el error de un intento, la cola de hoy, completar y aplazar un
repaso— y dos **añadidas** para poder enseñar lo que el producto promete en la pantalla de Errores:

- `GET /learning-errors` agrupa los fallos por concepto (la vista `Conceptos` de 07_UI-UX §9), y sin
  ella esa vista tendría que agrupar el cliente con su propia regla, que es como tener dos verdades;
- `GET /learning-errors/{id}` da el historial de un error concreto, que es lo que §9 pide enseñar.

Ninguna de las dos decide nada: las dos leen lo que ya está guardado. Quedan señaladas para su
ratificación, como las demás rutas añadidas de los slices anteriores.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Annotated

from fastapi import APIRouter, Query

from opofuente.api.deps import ProfilesServiceDep, ReviewServiceDep
from opofuente.api.error_responses import INGESTION_WRITE_ERRORS, RESOURCE_ERRORS
from opofuente.api.review_schemas import (
    CompleteReviewSchema,
    ConceptGroupSchema,
    ConceptSchema,
    DueItemSchema,
    DueOptionSchema,
    ErrorClassificationSchema,
    ErrorDetailSchema,
    ErrorSchema,
    MasteryProgramSchema,
    NodeMasterySchema,
    ResolveErrorSchema,
    ReviewEventSchema,
    ReviewItemSchema,
    ReviewQueueSchema,
    ReviewStatsSchema,
    SnoozeReviewSchema,
)
from opofuente.application.profiles_service import ProfilesService
from opofuente.application.read_models import NodeView, OppositionDetail
from opofuente.application.review_models import (
    ConceptGroupView,
    ConceptSummaryView,
    DueItemView,
    ErrorDetailView,
    ErrorView,
    ReviewEventView,
    ReviewItemView,
    ReviewQueueView,
    ReviewStatsView,
)
from opofuente.domain.errors import NotFoundError
from opofuente.domain.review import MIN_INTENTOS_DOMINIO, ErrorCause, Mastery, ReviewOutcome
from opofuente.domain.study import Confidence

router = APIRouter(tags=["errores y repaso"])


def _item(view: ReviewItemView) -> ReviewItemSchema:
    return ReviewItemSchema(
        id=view.id,
        question_version_id=view.question_version_id,
        opposition_id=view.opposition_id,
        learning_error_id=view.learning_error_id,
        due_at=view.due_at,
        interval_days=view.interval_days,
        repetitions=view.repetitions,
        lapses=view.lapses,
        last_reviewed_at=view.last_reviewed_at,
        last_reason=view.last_reason,
        created_at=view.created_at,
        updated_at=view.updated_at,
    )


def _event(view: ReviewEventView) -> ReviewEventSchema:
    return ReviewEventSchema(
        id=view.id,
        kind=view.kind,  # type: ignore[arg-type]
        outcome=None if view.outcome is None else view.outcome.value,
        confidence=view.confidence,  # type: ignore[arg-type]
        cause=None if view.cause is None else view.cause.value,
        note=view.note,
        previous_due_at=view.previous_due_at,
        due_at=view.due_at,
        previous_interval_days=view.previous_interval_days,
        interval_days=view.interval_days,
        repetitions=view.repetitions,
        reason=view.reason,
        occurred_at=view.occurred_at,
    )


def _due(view: DueItemView) -> DueItemSchema:
    return DueItemSchema(
        review=_item(view.item),
        question_version_id=view.question_version_id,
        question_set_id=view.question_set_id,
        stable_key=view.stable_key,
        stem=view.stem,
        part_code=view.part_code,
        is_reserve=view.is_reserve,
        origin_type=view.origin_type,
        overdue_days=view.overdue_days,
        explanation=view.explanation,
        options=[DueOptionSchema(stable_key=clave, text=texto) for clave, texto in view.options],
        session_id=view.session_id,
    )


def _stats(view: ReviewStatsView) -> ReviewStatsSchema:
    return ReviewStatsSchema(
        active=view.active,
        due=view.due,
        next_due_at=view.next_due_at,
        lapses=view.lapses,
    )


def _error(view: ErrorView) -> ErrorSchema:
    return ErrorSchema(
        id=view.id,
        attempt_id=view.attempt_id,
        question_version_id=view.question_version_id,
        stable_key=view.stable_key,
        stem=view.stem,
        session_id=view.session_id,
        part_code=view.part_code,
        curriculum_node_id=view.curriculum_node_id,
        node_title=view.node_title,
        concept_label=view.concept_label,
        cause=view.cause.value,
        user_note=view.user_note,
        status=view.status,  # type: ignore[arg-type]
        occurrences=view.occurrences,
        first_seen_at=view.first_seen_at,
        last_seen_at=view.last_seen_at,
        resolved_at=view.resolved_at,
    )


def _detail(view: ErrorDetailView) -> ErrorDetailSchema:
    return ErrorDetailSchema(
        error=_error(view.error),
        chosen_option_keys=list(view.chosen_option_keys),
        confidence=view.confidence,  # type: ignore[arg-type]
        answered_at=view.answered_at,
        review=None if view.review is None else _item(view.review),
        events=[_event(evento) for evento in view.events],
    )


def _concept(view: ConceptSummaryView) -> ConceptSchema:
    return ConceptSchema(
        key=view.key,
        label=view.label,
        node_id=view.node_id,
        open_count=view.open_count,
        resolved_count=view.resolved_count,
        occurrences=view.occurrences,
        last_seen_at=view.last_seen_at,
        errors=[_error(error) for error in view.errors],
    )


def _concepts(view: ConceptGroupView) -> ConceptGroupSchema:
    return ConceptGroupSchema(
        groups=[_concept(grupo) for grupo in view.groups],
        total_errors=view.total_errors,
        open_errors=view.open_errors,
    )


def _queue(view: ReviewQueueView) -> ReviewQueueSchema:
    return ReviewQueueSchema(
        items=[_due(item) for item in view.items],
        stats=_stats(view.stats),
        concepts=[_concept(concepto) for concepto in view.concepts],
        notes=list(view.notes),
    )


@router.post(
    "/attempts/{attempt_id}/error-classification",
    response_model=ErrorSchema,
    responses=INGESTION_WRITE_ERRORS,
    summary="Declara por qué se ha fallado (causa, concepto y nota)",
)
def classify_error(
    attempt_id: str, request: ErrorClassificationSchema, service: ReviewServiceDep
) -> ErrorSchema:
    """Sin causa no hay error: lo que se declara aquí es lo que la persona dice de su fallo."""
    return _error(
        service.classify(
            attempt_id,
            cause=ErrorCause(request.cause),
            concept_label=request.concept_label,
            curriculum_node_id=request.curriculum_node_id,
            note=request.note,
        )
    )


@router.get(
    "/reviews/due",
    response_model=ReviewQueueSchema,
    responses=RESOURCE_ERRORS,
    summary="Lo que toca repasar hoy, con su motivo",
)
def due_reviews(
    service: ReviewServiceDep,
    opposition_id: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> ReviewQueueSchema:
    return _queue(service.queue(opposition_id=opposition_id, limit=limit))


@router.post(
    "/reviews/{review_id}/complete",
    response_model=ReviewItemSchema,
    responses=INGESTION_WRITE_ERRORS,
    summary="Declara el resultado de un repaso hecho y lo reprograma",
)
def complete_review(
    review_id: str, request: CompleteReviewSchema, service: ReviewServiceDep
) -> ReviewItemSchema:
    return _item(
        service.complete(
            review_id,
            outcome=ReviewOutcome(request.outcome),
            confidence=None if request.confidence is None else Confidence(request.confidence),
            cause=None if request.cause is None else ErrorCause(request.cause),
            note=request.note,
        )
    )


@router.post(
    "/reviews/{review_id}/snooze",
    response_model=ReviewItemSchema,
    responses=INGESTION_WRITE_ERRORS,
    summary="Aplaza un repaso sin contarlo como repasado",
)
def snooze_review(
    review_id: str, request: SnoozeReviewSchema, service: ReviewServiceDep
) -> ReviewItemSchema:
    return _item(service.snooze(review_id, days=request.days))


@router.get(
    "/reviews/{review_id}",
    response_model=ReviewItemSchema,
    responses=RESOURCE_ERRORS,
    summary="El estado de un repaso (ruta añadida a §10)",
)
def get_review(review_id: str, service: ReviewServiceDep) -> ReviewItemSchema:
    return _item(service.item(review_id))


@router.get(
    "/reviews/{review_id}/history",
    response_model=list[ReviewEventSchema],
    responses=RESOURCE_ERRORS,
    summary="El historial de un repaso, del cambio más reciente al más antiguo (añadida a §10)",
)
def get_review_history(review_id: str, service: ReviewServiceDep) -> list[ReviewEventSchema]:
    """Lo que ha movido la fecha de un repaso: sin esto, una fecha no se puede explicar."""
    return [_event(evento) for evento in service.history(review_id)]


@router.get(
    "/learning-errors",
    response_model=ConceptGroupSchema,
    responses=RESOURCE_ERRORS,
    summary="Los fallos agrupados por concepto (ruta añadida a §10)",
)
def list_learning_errors(
    service: ReviewServiceDep,
    opposition_id: Annotated[str | None, Query()] = None,
) -> ConceptGroupSchema:
    return _concepts(service.concepts(opposition_id=opposition_id))


@router.get(
    "/learning-errors/{error_id}",
    response_model=ErrorDetailSchema,
    responses=RESOURCE_ERRORS,
    summary="Un fallo con su intento, su repaso y su historial (ruta añadida a §10)",
)
def get_learning_error(error_id: str, service: ReviewServiceDep) -> ErrorDetailSchema:
    return _detail(service.error(error_id))


@router.get(
    "/reviews/mastery",
    response_model=MasteryProgramSchema,
    responses=RESOURCE_ERRORS,
    summary="El dominio estimado de cada nodo del programa (ruta añadida a §10)",
)
def program_mastery(
    service: ReviewServiceDep,
    profiles: ProfilesServiceDep,
    opposition_id: Annotated[str | None, Query()] = None,
) -> MasteryProgramSchema:
    """Lo que la aplicación puede decir del dominio de cada tema, sin inventar un porcentaje.

    Los nodos sin intentos se declaran «sin datos» y los que tienen pocos, «evidencia insuficiente»:
    07_UI-UX §5 pide enseñar esa columna, y aquí se calcula con la misma regla para todos.
    """
    oposicion = _oposicion(profiles, opposition_id)
    convocatoria_id = oposicion.opposition.convocation_id
    if convocatoria_id is None:
        raise NotFoundError("convocatoria activa", oposicion.opposition.code)
    curriculum = profiles.get_curriculum(convocatoria_id)
    nodos = _aplanar(curriculum.nodes)
    estimaciones = service.mastery([nodo.id for nodo in nodos])
    fichas = [_mastery(nodo.id, estimaciones[nodo.id]) for nodo in nodos]
    con_estimacion = sum(1 for ficha in fichas if ficha.has_estimate)
    sin_datos = sum(1 for ficha in fichas if ficha.attempts == 0)
    return MasteryProgramSchema(
        opposition_id=oposicion.opposition.id,
        convocation_id=convocatoria_id,
        nodes=fichas,
        nodes_total=len(fichas),
        nodes_with_estimate=con_estimacion,
        nodes_insufficient=len(fichas) - con_estimacion - sin_datos,
        nodes_without_data=sin_datos,
        note=(
            "El dominio se estima por tema con los intentos de las preguntas **asignadas** a ese "
            "tema. Un tema sin preguntas asignadas no tiene datos, y con menos de "
            f"{MIN_INTENTOS_DOMINIO} intentos recientes se dice «evidencia insuficiente» en lugar "
            "de un porcentaje."
        ),
    )


def _oposicion(profiles: ProfilesService, opposition_id: str | None) -> OppositionDetail:
    if opposition_id is not None:
        return profiles.get_opposition(opposition_id)
    for candidata in profiles.list_oppositions():
        if candidata.active:
            return profiles.get_opposition(candidata.id)
    raise NotFoundError("oposición activa", "(ninguna)")


def _aplanar(nodos: Sequence[NodeView]) -> list[NodeView]:
    return [nodo for raiz in nodos for nodo in (raiz, *_aplanar(raiz.children))]


def _mastery(node_id: str, mastery: Mastery) -> NodeMasterySchema:
    return NodeMasterySchema(
        curriculum_node_id=node_id,
        level=mastery.level.value,
        attempts=mastery.attempts,
        correct=mastery.correct,
        recent_attempts=mastery.recent_attempts,
        accuracy=mastery.accuracy,
        explanation=mastery.explanation,
        has_estimate=mastery.has_estimate,
    )


@router.post(
    "/learning-errors/{error_id}/resolution",
    response_model=ErrorSchema,
    responses=INGESTION_WRITE_ERRORS,
    summary="Resuelve un error o lo vuelve a abrir (ruta añadida a §10)",
)
def resolve_learning_error(
    error_id: str, request: ResolveErrorSchema, service: ReviewServiceDep
) -> ErrorSchema:
    """Resolver un error es una decisión de quien estudia, y **no** detiene su repaso."""
    if request.resolved:
        return _error(service.resolve_error(error_id, note=request.note))
    return _error(service.reopen_error(error_id))
