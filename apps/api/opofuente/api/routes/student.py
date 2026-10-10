"""Rutas de la zona del alumno (F2, `08_API-CONTRACT` §10 ampliado).

Cuatro rutas de **lectura** y cinco de **test**, y ninguna más. Lo que devuelven lo declaran
`student_schemas.py`, que no tiene campo para la evidencia, el conjunto, la clave, la versión ni la
ruta.

Lo que **no** está aquí todavía, y por qué:

- `GET /student/topics/{codigo}/notes`: los apuntes redactados ya existen (`topic_note_sections` y
  `question_note_anchors`, pasos B-E del plan de apuntes) y viajan dentro de la versión del tema,
  que es lo que sirve la ficha del programa. Lo que falta es la **pantalla de lectura** del alumno
  (capítulos por epígrafe, índice, buscador y «Ver en apuntes» al párrafo): es el paso 5 del plan y
  necesita su propio contrato, sin identificadores ni rutas de la trastienda.
- `GET /student/official-exams`: los exámenes oficiales del INAP necesitan su importación (D10 del
  objetivo) antes de poder listarse con su nota; listarlos hoy sería listar conjuntos internos.

El test en curso **sí** está: `POST /student/tests` y `POST /student/mock-exams` montan la sesión
por la composición declarada de `StudyService` (`compose`), y las cuatro rutas de
`/student/sessions/{id}` la leen, la arrancan, la contestan y la cierran. La pregunta viaja por su
**posición en la hoja de respuestas**, así que ningún identificador de pregunta sale de esta capa.
"""

from __future__ import annotations

from fastapi import APIRouter, Path, status

from opofuente.api.deps import StudentServiceDep
from opofuente.api.error_responses import RESOURCE_ERRORS
from opofuente.api.student_schemas import (
    StudentAnswerRequestSchema,
    StudentBlockProgressSchema,
    StudentCorrectionSchema,
    StudentEpigraphSchema,
    StudentMockExamRequestSchema,
    StudentOppositionSchema,
    StudentOptionSchema,
    StudentOverviewSchema,
    StudentPartScoreSchema,
    StudentProgressSchema,
    StudentQuestionSchema,
    StudentResultSchema,
    StudentRunSchema,
    StudentScoreSchema,
    StudentSessionSchema,
    StudentSheetRowSchema,
    StudentSyllabusSchema,
    StudentTestRequestSchema,
    StudentTopicProgressSchema,
    StudentTopicSchema,
)
from opofuente.application.student_models import (
    StudentAnswerRequest,
    StudentBlockProgressView,
    StudentMockExamRequest,
    StudentOppositionView,
    StudentOverviewView,
    StudentPartScoreView,
    StudentProgressView,
    StudentQuestionView,
    StudentResultView,
    StudentRunView,
    StudentScoreView,
    StudentSessionView,
    StudentTestRequest,
    StudentTopicProgressView,
    StudentTopicView,
)

router = APIRouter(prefix="/student", tags=["alumno"])


def _opposition(view: StudentOppositionView) -> StudentOppositionSchema:
    return StudentOppositionSchema(code=view.code, name=view.name)


def _score(view: StudentScoreView) -> StudentScoreSchema:
    return StudentScoreSchema(
        correct=view.correct,
        wrong=view.wrong,
        blank=view.blank,
        points=view.points,
        points_decimal=view.points_decimal,
        maximum=view.maximum,
        passed=view.passed,
    )


def _session(view: StudentSessionView) -> StudentSessionSchema:
    return StudentSessionSchema(
        id=view.id,
        mode=view.mode,  # type: ignore[arg-type]
        status=view.status,  # type: ignore[arg-type]
        title=view.title,
        total_questions=view.total_questions,
        answered_questions=view.answered_questions,
        time_limit_minutes=view.time_limit_minutes,
        started_at=view.started_at,
        finished_at=view.finished_at,
        created_at=view.created_at,
        result=None if view.result is None else _score(view.result),
        practical_case_origin=view.practical_case_origin,
    )


def _part(view: StudentPartScoreView) -> StudentPartScoreSchema:
    return StudentPartScoreSchema(
        part_code=view.part_code,
        part_name=view.part_name,
        kind=view.kind,
        correct=view.correct,
        wrong=view.wrong,
        blank=view.blank,
        score=view.score,
        score_decimal=view.score_decimal,
        score_max=view.score_max,
        pass_score=view.pass_score,
        passed=view.passed,
        verdict_note=view.verdict_note,
    )


def _question(view: StudentQuestionView) -> StudentQuestionSchema:
    return StudentQuestionSchema(
        position=view.position,
        is_reserve=view.is_reserve,
        stem=view.stem,
        question_type=view.question_type,
        options=[StudentOptionSchema(key=opcion.key, text=opcion.text) for opcion in view.options],
        answered=view.answered,
        chosen=list(view.chosen_option_keys),
        confidence=view.confidence,  # type: ignore[arg-type]
        correction=(
            None
            if view.correction is None
            else StudentCorrectionSchema(
                outcome=view.correction.outcome,  # type: ignore[arg-type]
                correct=list(view.correction.correct_option_keys),
                reason=view.correction.reason,
            )
        ),
    )


def _run(view: StudentRunView) -> StudentRunSchema:
    return StudentRunSchema(
        session=_session(view.session),
        total=view.total,
        answered=view.answered,
        pending=view.pending,
        finished=view.finished,
        position=view.position,
        question=None if view.question is None else _question(view.question),
        sheet=[
            StudentSheetRowSchema(
                position=fila.position,
                answered=fila.answered,
                chosen=list(fila.chosen_option_keys),
                confidence=fila.confidence,  # type: ignore[arg-type]
                outcome=fila.outcome,  # type: ignore[arg-type]
                correct=list(fila.correct_option_keys),
            )
            for fila in view.sheet
        ],
    )


def _topic_progress(view: StudentTopicProgressView) -> StudentTopicProgressSchema:
    return StudentTopicProgressSchema(
        code=view.code,
        number=view.number,
        title=view.title,
        available_questions=view.available_questions,
        answered=view.answered,
        correct=view.correct,
        accuracy=view.accuracy,
        due_reviews=view.due_reviews,
    )


def _block(view: StudentBlockProgressView) -> StudentBlockProgressSchema:
    return StudentBlockProgressSchema(
        code=view.code,
        title=view.title,
        position=view.position,
        available_questions=view.available_questions,
        answered=view.answered,
        correct=view.correct,
        accuracy=view.accuracy,
        due_reviews=view.due_reviews,
        topics=[_topic_progress(tema) for tema in view.topics],
    )


@router.get(
    "/overview",
    response_model=StudentOverviewSchema,
    responses=RESOURCE_ERRORS,
    summary="Inicio: el test a medias, los fallos vencidos y el progreso por bloque",
)
def student_overview(service: StudentServiceDep) -> StudentOverviewSchema:
    """Lo que se pinta al entrar. La oposición la pone la configuración, no la petición.

    No hay parámetro de oposición **a propósito**: la zona del alumno sirve un solo cuerpo
    (`OPOFUENTE_STUDENT_OPPOSITION`) y el filtro vive en el servidor, así que no existe forma de
    pedir el progreso de otro desde aquí.
    """
    view: StudentOverviewView = service.overview()
    return StudentOverviewSchema(
        opposition=_opposition(view.opposition),
        in_progress=None if view.in_progress is None else _session(view.in_progress),
        due_reviews=view.due_reviews,
        blocks=[_block(bloque) for bloque in view.blocks],
        recent_tests=[_session(sesion) for sesion in view.recent_tests],
    )


@router.get(
    "/syllabus",
    response_model=StudentSyllabusSchema,
    responses=RESOURCE_ERRORS,
    summary="El temario: bloques y temas en orden numérico, con lo disponible y el acierto",
)
def student_syllabus(service: StudentServiceDep) -> StudentSyllabusSchema:
    """El temario completo. El orden es el de la consulta del programa, que ya es numérico.

    Aquí no se reordena nada: el orden se arregla en la consulta (`curriculum_order`, pieza 1 de F1)
    y esa misma consulta la usa el panel. Reordenar otra vez en esta capa sería tener dos órdenes
    que pueden divergir, y por eso `IV.1` sale antes que `IV.10` sin que nadie lo toque aquí.
    """
    bloques = service.syllabus()
    return StudentSyllabusSchema(
        opposition=_opposition(service.opposition_view()),
        blocks=[_block(bloque) for bloque in bloques],
    )


@router.get(
    "/topics/{codigo}",
    response_model=StudentTopicSchema,
    responses=RESOURCE_ERRORS,
    summary="Un tema por su código legible (IV.10): título, epígrafes, recuentos y progreso",
)
def student_topic(
    service: StudentServiceDep,
    codigo: str = Path(
        description="Código legible del tema, como `IV.10` (también se acepta `IV-10`).",
        examples=["IV.10"],
    ),
) -> StudentTopicSchema:
    """Un tema por su código. **Nunca** por su identificador: los UUID no se enseñan al alumno."""
    view: StudentTopicView = service.topic(codigo)
    return StudentTopicSchema(
        code=view.code,
        number=view.number,
        title=view.title,
        description=view.description,
        block_code=view.block_code,
        block_title=view.block_title,
        epigraphs=[
            StudentEpigraphSchema(code=epigrafe.code, title=epigrafe.title)
            for epigrafe in view.epigraphs
        ],
        progress=None if view.progress is None else _topic_progress(view.progress),
    )


@router.get(
    "/progress",
    response_model=StudentProgressSchema,
    responses=RESOURCE_ERRORS,
    summary="Acierto por bloque y por tema, los cinco más flojos e historial de tests",
)
def student_progress(service: StudentServiceDep) -> StudentProgressSchema:
    view: StudentProgressView = service.progress()
    return StudentProgressSchema(
        opposition=_opposition(view.opposition),
        blocks=[_block(bloque) for bloque in view.blocks],
        weakest_topics=[_topic_progress(tema) for tema in view.weakest_topics],
        history=[_session(sesion) for sesion in view.history],
    )


# --- el test: montarlo, correrlo y cerrarlo ------------------------------------------------------


@router.post(
    "/tests",
    response_model=StudentSessionSchema,
    status_code=status.HTTP_201_CREATED,
    responses=RESOURCE_ERRORS,
    summary="Monta un test de varios temas (los que elija el alumno)",
)
def student_create_test(
    service: StudentServiceDep, request: StudentTestRequestSchema
) -> StudentSessionSchema:
    """Un test de los temas elegidos, por la composición declarada del servicio de estudio.

    Si en esos temas no hay tantas preguntas como se piden, la sesión se monta con las que haya: un
    test de 50 con 30 disponibles es un test de 30, no un error que deja al alumno sin estudiar.
    """
    view: StudentSessionView = service.create_test(
        StudentTestRequest(
            nodes=tuple(request.nodes),
            count=request.count,
            filter=request.filter,
            feedback=request.feedback,
            timed=request.timed,
            owner_id=service.owner_id,
        )
    )
    return _session(view)


@router.post(
    "/mock-exams",
    response_model=StudentSessionSchema,
    status_code=status.HTTP_201_CREATED,
    responses=RESOURCE_ERRORS,
    summary="Monta el simulacro con el perfil del examen y el bloque elegido para el supuesto",
)
def student_create_mock_exam(
    service: StudentServiceDep, request: StudentMockExamRequestSchema
) -> StudentSessionSchema:
    """El simulacro del perfil: 80 + 5 y el supuesto de 20 + 5 del bloque III o del IV.

    Los dos supuestos son excluyentes y se monta el elegido. Si sus preguntas salen de los temas del
    bloque, la sesión lo dice (`practical_case_origin`).
    """
    view: StudentSessionView = service.create_mock_exam(
        StudentMockExamRequest(
            variant=request.variant,
            case_block=request.case_block,
            owner_id=service.owner_id,
        )
    )
    return _session(view)


@router.get(
    "/sessions/{sesion}",
    response_model=StudentRunSchema,
    responses=RESOURCE_ERRORS,
    summary="El test en curso: la pregunta que toca y la hoja de respuestas entera",
)
def student_session(
    service: StudentServiceDep,
    sesion: str = Path(description="Identificador de la sesión, el que devolvió al montarla."),
) -> StudentRunSchema:
    return _run(service.run(sesion))


@router.post(
    "/sessions/{sesion}/start",
    response_model=StudentRunSchema,
    responses=RESOURCE_ERRORS,
    summary="Arranca el test (arrancar uno que ya corre no cambia nada)",
)
def student_start(service: StudentServiceDep, sesion: str = Path()) -> StudentRunSchema:
    return _run(service.start(sesion))


@router.post(
    "/sessions/{sesion}/answers",
    response_model=StudentRunSchema,
    responses=RESOURCE_ERRORS,
    summary="Contesta la pregunta de una fila de la hoja y devuelve el test como queda",
)
def student_answer(
    service: StudentServiceDep,
    request: StudentAnswerRequestSchema,
    sesion: str = Path(),
) -> StudentRunSchema:
    """La respuesta se pide por la **fila** de la hoja de respuestas, no por un identificador.

    Es lo que el alumno tiene delante, y así la capa no tiene que enseñar ningún identificador de
    pregunta. La corrección solo vuelve cuando el modo la permite (`can_show_correction`).
    """
    return _run(
        service.answer(
            sesion,
            StudentAnswerRequest(
                position=request.position,
                chosen_option_keys=tuple(request.chosen),
                elapsed_ms=request.elapsed_ms,
                confidence=request.confidence,
            ),
        )
    )


@router.post(
    "/sessions/{sesion}/finish",
    response_model=StudentResultSchema,
    responses=RESOURCE_ERRORS,
    summary="Termina el test y devuelve el resultado con la nota de cada parte",
)
def student_finish(service: StudentServiceDep, sesion: str = Path()) -> StudentResultSchema:
    view: StudentResultView = service.finish(sesion)
    return StudentResultSchema(
        session=_session(view.session),
        parts=[_part(parte) for parte in view.parts],
        total=_part(view.total),
        official_available=view.official_available,
        official_note=view.official_note,
    )
