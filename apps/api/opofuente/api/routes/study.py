"""Rutas de estudio (08_API-CONTRACT §10).

Las rutas de esta sección son las que **no** pueden filtrar la solución: la pregunta de la sesión se
sirve con `SessionQuestionSchema`, que no tiene ningún campo de clave, y la corrección viaja en su
propio esquema. El servicio decide cuándo se construye; aquí solo se traduce.

De §10 quedan fuera las rutas de errores y repaso (`POST /attempts/{id}/error-classification`,
`GET /reviews/due`, `POST /reviews/{id}/complete` y `POST /reviews/{id}/snooze`): son de S10 y no se
declaran hasta que existan.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query

from opofuente.api.deps import StudyServiceDep
from opofuente.api.error_responses import INGESTION_WRITE_ERRORS, RESOURCE_ERRORS
from opofuente.api.question_schemas import OptionSchema, QuestionEvidenceSchema
from opofuente.api.study_schemas import (
    AnswerOutcomeSchema,
    AnswerRequestSchema,
    AttemptSchema,
    BulkRecalculationSchema,
    CorrectionSchema,
    CreateSessionSchema,
    CurrentQuestionSchema,
    DiagnosticReadingSchema,
    DiagnosticTopicSchema,
    IntervalSchema,
    NavigateRequestSchema,
    OutdatedSessionsSchema,
    PartScoreSchema,
    RecalculationSchema,
    ReviewSchema,
    ScoreSchema,
    SessionConfigurationSchema,
    SessionPageSchema,
    SessionQuestionSchema,
    SessionRecalculationSchema,
    SessionResultSchema,
    SessionSchema,
    SessionSourceSchema,
    SubstitutionSchema,
)
from opofuente.application.study_models import (
    AttemptView,
    CorrectionView,
    PartScoreView,
    RecalculationView,
    ReviewView,
    ScoreView,
    SessionPage,
    SessionQuestionView,
    SessionResultView,
    SessionView,
)
from opofuente.application.study_service import (
    AnswerInput,
    CreateSessionInput,
    CurrentQuestionView,
    SourceInput,
)
from opofuente.domain.study import Confidence, Feedback, SessionMode

router = APIRouter(tags=["estudio"])

#: Cuántas sesiones se devuelven de una vez si la petición no dice otra cosa.
DEFAULT_LIMIT = 50


def _score(view: ScoreView) -> ScoreSchema:
    return ScoreSchema(
        numerator=view.numerator,
        denominator=view.denominator,
        fraction=view.fraction,
        decimal=view.decimal,
    )


def _correction(view: CorrectionView) -> CorrectionSchema:
    return CorrectionSchema(
        outcome=view.outcome,  # type: ignore[arg-type]
        correct_option_keys=list(view.correct_option_keys),
        score=_score(view.score),
        reason=view.reason,
        explanation=view.explanation,
        evidence=[
            QuestionEvidenceSchema(
                span_id=cita.span_id,
                role=cita.role,  # type: ignore[arg-type]
                status=cita.status,  # type: ignore[arg-type]
                claim=cita.claim,
                text=cita.text,
                page=cita.page,
                citation_label=cita.citation_label,
                document_version_id=cita.document_version_id,
                section_id=cita.section_id,
            )
            for cita in view.evidence
        ],
    )


def _question(view: SessionQuestionView) -> SessionQuestionSchema:
    return SessionQuestionSchema(
        session_question_id=view.session_question_id,
        question_version_id=view.question_version_id,
        stable_key=view.stable_key,
        position=view.position,
        part_code=view.part_code,
        is_reserve=view.is_reserve,
        reserve_order=view.reserve_order,
        stem=view.stem,
        question_type=view.question_type,
        origin_type=view.origin_type,
        options=[
            OptionSchema(
                id=opcion.id,
                stable_key=opcion.stable_key,
                label=opcion.label,
                text=opcion.text,
                position=opcion.position,
            )
            for opcion in view.options
        ],
        answered=view.answered,
        chosen_option_keys=list(view.chosen_option_keys),
        elapsed_ms=view.elapsed_ms,
        confidence=view.confidence.value if view.confidence is not None else None,
        correction=None if view.correction is None else _correction(view.correction),
    )


def _attempt(view: AttemptView) -> AttemptSchema:
    return AttemptSchema(
        id=view.id,
        session_question_id=view.session_question_id,
        question_version_id=view.question_version_id,
        chosen_option_keys=list(view.chosen_option_keys),
        elapsed_ms=view.elapsed_ms,
        confidence=view.confidence.value if view.confidence is not None else None,
        client_sequence=view.client_sequence,
        answered_at=view.answered_at,
        outcome=view.outcome,  # type: ignore[arg-type]
        score=None if view.score is None else _score(view.score),
        reason=view.reason,
    )


def _part(view: PartScoreView) -> PartScoreSchema:
    return PartScoreSchema(
        part_code=view.part_code,
        part_name=view.part_name,
        ordinary_items=view.ordinary_items,
        score_min=view.score_min,
        score_max=view.score_max,
        pass_score=view.pass_score,
        penalty=None if view.penalty is None else _score(view.penalty),
        kind=view.kind,  # type: ignore[arg-type]
        correct=view.correct,
        wrong=view.wrong,
        blank=view.blank,
        annulled=view.annulled,
        excluded=view.excluded,
        conflicting=view.conflicting,
        reserves_used=view.reserves_used,
        unused_reserves=view.unused_reserves,
        score=_score(view.score),
        passed=view.passed,
        verdict_note=view.verdict_note,
        official_available=view.official_available,
    )


def _result(view: SessionResultView) -> SessionResultSchema:
    return SessionResultSchema(
        session_id=view.session_id,
        mode=view.mode.value,
        answer_key_version_id=view.answer_key_version_id,
        key_label=view.key_label,
        parts=[_part(parte) for parte in view.parts],
        total=_part(view.total),
        substitutions=[
            SubstitutionSchema(
                annulled_question_version_id=sustitucion.annulled_question_version_id,
                reserve_question_version_id=sustitucion.reserve_question_version_id,
            )
            for sustitucion in view.substitutions
        ],
        unfinished=view.unfinished,
        official_available=view.official_available,
        official_note=view.official_note,
        calculated_at=view.calculated_at,
        recalculation=(None if view.recalculation is None else _recalculation(view.recalculation)),
    )


def _recalculation(view: RecalculationView) -> RecalculationSchema:
    return RecalculationSchema(
        previous_total=_score(view.previous_total),
        previous_parts=[_part(parte) for parte in view.previous_parts],
        previous_key_label=view.previous_key_label,
        recalculated_at=view.recalculated_at,
        changed=view.changed,
        note=view.note,
    )


def _session(view: SessionView) -> SessionSchema:
    return SessionSchema(
        id=view.id,
        mode=view.mode.value,
        status=view.status.value,
        feedback=view.feedback.value,
        opposition_id=view.opposition_id,
        convocation_version_id=view.convocation_version_id,
        question_set_id=view.question_set_id,
        answer_key_version_id=view.answer_key_version_id,
        key_label=view.key_label,
        configuration=SessionConfigurationSchema(
            mode=view.configuration.mode.value,
            feedback=view.configuration.feedback.value,
            time_limit_minutes=view.configuration.time_limit_minutes,
            shuffle=view.configuration.shuffle,
            note=view.configuration.note,
            sources=[
                SessionSourceSchema(
                    question_set_id=fuente.question_set_id,
                    part_code=fuente.part_code or "",
                    count=fuente.count,
                    include_reserves=fuente.include_reserves,
                )
                for fuente in view.configuration.sources
            ],
        ),
        time_limit_minutes=view.time_limit_minutes,
        total_questions=view.total_questions,
        answered_questions=view.answered_questions,
        started_at=view.started_at,
        finished_at=view.finished_at,
        created_at=view.created_at,
        result=None if view.result is None else _result(view.result),
    )


def _page(view: SessionPage) -> SessionPageSchema:
    return SessionPageSchema(
        sessions=[_session(sesion) for sesion in view.sessions],
        total=view.total,
        limit=view.limit,
        offset=view.offset,
    )


def _current(view: CurrentQuestionView) -> CurrentQuestionSchema:
    return CurrentQuestionSchema(
        session=_session(view.session),
        question=None if view.question is None else _question(view.question),
        answered=view.answered,
        total=view.total,
        pending=view.pending,
        finished=view.finished,
    )


def _review(view: ReviewView) -> ReviewSchema:
    return ReviewSchema(
        session=_session(view.session),
        entries=[_question(entrada) for entrada in view.entries],
        partial=view.partial,
        note=view.note,
        pending=view.pending,
        unanswered=view.unanswered,
    )


def _create_input(request: CreateSessionSchema) -> CreateSessionInput:
    return CreateSessionInput(
        opposition_id=request.opposition_id,
        mode=SessionMode(request.mode),
        sources=tuple(
            SourceInput(
                question_set_id=fuente.question_set_id,
                part_code=fuente.part_code,
                count=fuente.count,
                include_reserves=fuente.include_reserves,
            )
            for fuente in request.sources
        ),
        convocation_version_id=request.convocation_version_id,
        feedback=None if request.feedback is None else Feedback(request.feedback),
        shuffle=request.shuffle,
        time_limit_minutes=request.time_limit_minutes,
        review_limit=request.review_limit,
        block_node_id=request.block_node_id,
    )


@router.get(
    "/study-sessions",
    response_model=SessionPageSchema,
    responses=RESOURCE_ERRORS,
    summary="Sesiones de estudio de una oposición (ruta añadida a §10)",
)
def list_study_sessions(
    service: StudyServiceDep,
    opposition_id: Annotated[str | None, Query()] = None,
    status: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = DEFAULT_LIMIT,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> SessionPageSchema:
    """Ruta **añadida** al contrato §10: Inicio necesita saber qué hay para continuar.

    Sin ella, «Continuar estudiando» no tendría de dónde leer, y el producto promete esa tarjeta.
    """
    return _page(
        service.list_sessions(
            opposition_id=opposition_id, status=status, limit=limit, offset=offset
        )
    )


@router.post(
    "/study-sessions",
    response_model=SessionSchema,
    status_code=201,
    responses=INGESTION_WRITE_ERRORS,
    summary="Crea una sesión de estudio con su composición congelada",
)
def create_study_session(request: CreateSessionSchema, service: StudyServiceDep) -> SessionSchema:
    """Monta la sesión. Si falta material, clave activa o la parte no se corrige aquí, lo dice."""
    return _session(service.create_session(_create_input(request)))


@router.get(
    "/study-sessions/{session_id}",
    response_model=SessionSchema,
    responses=RESOURCE_ERRORS,
    summary="Una sesión con su configuración y su progreso",
)
def get_study_session(session_id: str, service: StudyServiceDep) -> SessionSchema:
    return _session(service.session(session_id))


@router.post(
    "/study-sessions/{session_id}/start",
    response_model=SessionSchema,
    responses=RESOURCE_ERRORS,
    summary="Inicia la sesión (congela el reloj)",
)
def start_study_session(session_id: str, service: StudyServiceDep) -> SessionSchema:
    return _session(service.start(session_id))


@router.get(
    "/study-sessions/{session_id}/current-question",
    response_model=CurrentQuestionSchema,
    responses=RESOURCE_ERRORS,
    summary="La pregunta que toca ahora, sin solución",
)
def current_question(session_id: str, service: StudyServiceDep) -> CurrentQuestionSchema:
    return _current(service.current_question(session_id))


@router.post(
    "/study-sessions/{session_id}/navigate",
    response_model=CurrentQuestionSchema,
    responses=RESOURCE_ERRORS,
    summary="Mueve el puntero: a una posición o al siguiente/anterior",
)
def navigate(
    session_id: str, request: NavigateRequestSchema, service: StudyServiceDep
) -> CurrentQuestionSchema:
    return _current(
        service.navigate(session_id, position=request.position, direction=request.direction)
    )


@router.post(
    "/study-sessions/{session_id}/answers",
    response_model=AnswerOutcomeSchema,
    status_code=201,
    responses=INGESTION_WRITE_ERRORS,
    summary="Registra una respuesta y la corrige con la clave congelada",
)
def answer(
    session_id: str, request: AnswerRequestSchema, service: StudyServiceDep
) -> AnswerOutcomeSchema:
    """Registra el intento **una sola vez**: reenviar lo mismo no crea otro y cambiarlo es 409."""
    resultado = service.answer(
        session_id,
        AnswerInput(
            question_version_id=request.question_version_id,
            chosen_option_keys=tuple(request.chosen_option_keys),
            elapsed_ms=request.elapsed_ms,
            confidence=None if request.confidence is None else Confidence(request.confidence),
            client_sequence=request.client_sequence,
        ),
    )
    return AnswerOutcomeSchema(
        saved=resultado.saved,
        already_answered=resultado.already_answered,
        attempt=_attempt(resultado.attempt),
        session=_session(resultado.session),
        question=_question(resultado.question),
        correction=None if resultado.correction is None else _correction(resultado.correction),
    )


@router.post(
    "/study-sessions/{session_id}/finish",
    response_model=SessionResultSchema,
    responses=RESOURCE_ERRORS,
    summary="Termina la sesión y calcula el resultado",
)
def finish_study_session(session_id: str, service: StudyServiceDep) -> SessionResultSchema:
    return _result(service.finish(session_id))


@router.get(
    "/study-sessions/{session_id}/result",
    response_model=SessionResultSchema,
    responses=RESOURCE_ERRORS,
    summary="El resultado de una sesión terminada",
)
def study_result(session_id: str, service: StudyServiceDep) -> SessionResultSchema:
    return _result(service.result(session_id))


@router.get(
    "/study-sessions/{session_id}/review",
    response_model=ReviewSchema,
    responses=RESOURCE_ERRORS,
    summary="La revisión: cada pregunta con lo que se marcó y su corrección",
)
def study_review(session_id: str, service: StudyServiceDep) -> ReviewSchema:
    return _review(service.review(session_id))


@router.get(
    "/study-sessions/{session_id}/diagnostic",
    response_model=DiagnosticReadingSchema,
    responses=RESOURCE_ERRORS,
    summary="La lectura por temas de un diagnóstico (ruta añadida: DEBT-012)",
)
def diagnostic_reading(session_id: str, service: StudyServiceDep) -> DiagnosticReadingSchema:
    """Qué dice la muestra de un diagnóstico, tema por tema y con su intervalo.

    Ruta **añadida** al contrato §10 y registrada en ADR-013. Va aparte del resultado porque no es
    lo
    mismo: el resultado dice la puntuación directa de la muestra —que no es una nota— y esta lectura
    dice, por tema, qué se contestó y con qué incertidumbre. Mezclarlas invitaría a leer el
    intervalo
    como una calificación.
    """
    lectura = service.diagnostic_reading(session_id)
    return DiagnosticReadingSchema(
        session_id=session_id,
        mode="diagnostic",
        sample_size=lectura.sample_size,
        answered=lectura.answered,
        detail=lectura.detail,
        topics=[
            DiagnosticTopicSchema(
                node_id=ficha.node_id,
                title=ficha.title,
                answered=ficha.answered,
                correct=ficha.correct,
                interval=(
                    None
                    if ficha.interval is None
                    else IntervalSchema(
                        low=ficha.interval.low,
                        high=ficha.interval.high,
                        confidence=ficha.interval.confidence,
                        width=ficha.interval.width,
                    )
                ),
                note=ficha.note,
            )
            for ficha in lectura.topics
        ],
    )


@router.post(
    "/study-sessions/{session_id}/recalculate",
    response_model=SessionResultSchema,
    responses=RESOURCE_ERRORS,
    summary="Recalcula la sesión con la clave activa ahora (ruta añadida a §10)",
)
def recalculate_study_session(session_id: str, service: StudyServiceDep) -> SessionResultSchema:
    """Ruta **añadida** al contrato §10 para S08.

    Una clave corregida no cambia sola lo que ya se corrigió: recalcular es una acción explícita que
    crea evaluaciones nuevas, conserva el resultado anterior y explica de dónde a dónde cambió.
    """
    return _result(service.recalculate(session_id))


@router.get(
    "/question-sets/{set_id}/outdated-sessions",
    response_model=OutdatedSessionsSchema,
    responses=RESOURCE_ERRORS,
    summary="Sesiones terminadas sin corregir con la plantilla activa (ruta añadida: DEBT-013)",
)
def outdated_sessions(set_id: str, service: StudyServiceDep) -> OutdatedSessionsSchema:
    """Cuántas sesiones quedan desactualizadas tras activar una plantilla nueva.

    Es la lectura que faltaba: `POST /question-sets/{set_id}/recalculate-sessions` dice qué cambió
    **después** de recalcular, y esto dice qué hace falta **antes**. Activar una clave corregida sin
    recalcular no cambiaba ninguna nota y no se notaba en ninguna pantalla.
    """
    vista = service.outdated_sessions(set_id)
    return OutdatedSessionsSchema(
        question_set_id=vista.question_set_id,
        key_version=vista.key_version,
        key_id=vista.key_id,
        finished=vista.finished,
        up_to_date=vista.up_to_date,
        outdated=vista.outdated,
        without_evaluation=vista.without_evaluation,
        outdated_session_ids=list(vista.outdated_session_ids),
        detail=vista.detail,
    )


@router.post(
    "/question-sets/{set_id}/recalculate-sessions",
    response_model=BulkRecalculationSchema,
    responses=INGESTION_WRITE_ERRORS,
    summary="Recalcula en bloque las sesiones terminadas de un conjunto (DEBT-013)",
)
def recalculate_set(set_id: str, service: StudyServiceDep) -> BulkRecalculationSchema:
    """Corregir una clave y recalcular **todas** las sesiones afectadas de una vez.

    Va aquí y no en `/study-sessions/{id}/recalculate` porque el ámbito es el **conjunto**: lo que
    se corrige es su plantilla, y lo que hay que arreglar son las sesiones que se corrigieron con
    ella. El informe dice sesión por sesión qué cambió y cuánto: un «hecho» sin números no se puede
    comprobar.
    """
    vista = service.recalculate_set(set_id)
    return BulkRecalculationSchema(
        question_set_id=vista.question_set_id,
        key_version=vista.key_version,
        changed=vista.changed,
        detail=vista.detail,
        sessions=[
            SessionRecalculationSchema(
                session_id=cambio.session_id,
                previous_total=cambio.previous_total,
                new_total=cambio.new_total,
                previous_key_label=cambio.previous_key_label,
                new_key_label=cambio.new_key_label,
                changed=cambio.changed,
            )
            for cambio in vista.sessions
        ],
    )
