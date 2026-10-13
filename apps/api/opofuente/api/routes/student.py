"""Rutas de la zona del alumno (F2, `08_API-CONTRACT` §10 ampliado).

Cinco rutas de **lectura** y seis de **escritura**, y ninguna más. Lo que devuelven lo declaran
`student_schemas.py`, que no tiene campo para la evidencia, el conjunto, la clave, la versión ni la
ruta.

Lo que **no** está aquí todavía, y por qué:

- `GET /student/official-exams`: los exámenes oficiales del INAP necesitan su importación (D10 del
  objetivo) antes de poder listarse con su nota; listarlos hoy sería listar conjuntos internos.

Los **apuntes del tema** sí están desde F13: `GET /student/topics/{codigo}/notes` sirve el texto con
su estado (publicado, borrador o sin escribir) y **sin** ningún identificador de pregunta —lo que
viaja es el recuento de preguntas que contesta cada apartado—, y `POST
/student/topics/{codigo}/reports` guarda el aviso «esto está mal» por la ruta auditada (decisión
D2).

El test en curso **sí** está: `POST /student/tests` y `POST /student/mock-exams` montan la sesión
por la composición declarada de `StudyService` (`compose`), y las cuatro rutas de
`/student/sessions/{id}` la leen, la arrancan, la contestan y la cierran. La pregunta viaja por su
**posición en la hoja de respuestas**, así que ningún identificador de pregunta sale de esta capa.
"""

from __future__ import annotations

from fastapi import APIRouter, Path, status

from opofuente.api.deps import StudentServiceDep
from opofuente.api.error_responses import RESOURCE_ERRORS, WRITE_ERRORS
from opofuente.api.student_schemas import (
    StudentAnswerRequestSchema,
    StudentBlockProgressSchema,
    StudentCorrectionSchema,
    StudentEpigraphSchema,
    StudentMistakeSchema,
    StudentMistakesSchema,
    StudentMistakeTopicSchema,
    StudentMockCaseBlockSchema,
    StudentMockCaseTopicSchema,
    StudentMockExamPartSchema,
    StudentMockExamPlanSchema,
    StudentMockExamRequestSchema,
    StudentMockExamVariantSchema,
    StudentNoteSectionSchema,
    StudentNotesSchema,
    StudentOfficialExamSchema,
    StudentOfficialExamsSchema,
    StudentOppositionSchema,
    StudentOptionSchema,
    StudentOverviewSchema,
    StudentPartScoreSchema,
    StudentProgressSchema,
    StudentQuestionSchema,
    StudentReportRequestSchema,
    StudentReportSchema,
    StudentResultQuestionSchema,
    StudentResultSchema,
    StudentResultTopicSchema,
    StudentRunSchema,
    StudentScoreSchema,
    StudentSessionResultSchema,
    StudentSessionSchema,
    StudentSheetRowSchema,
    StudentSyllabusSchema,
    StudentTestRequestSchema,
    StudentTopicProgressSchema,
    StudentTopicRefSchema,
    StudentTopicSchema,
)
from opofuente.application.student_models import (
    StudentAnswerRequest,
    StudentBlockProgressView,
    StudentMistakesView,
    StudentMistakeTopicView,
    StudentMistakeView,
    StudentMockCaseBlockView,
    StudentMockExamPartView,
    StudentMockExamPlanView,
    StudentMockExamRequest,
    StudentMockExamVariantView,
    StudentNotesView,
    StudentOfficialExamsView,
    StudentOfficialExamView,
    StudentOppositionView,
    StudentOverviewView,
    StudentPartScoreView,
    StudentProgressView,
    StudentQuestionView,
    StudentReportView,
    StudentResultQuestionView,
    StudentResultTopicView,
    StudentResultView,
    StudentRunView,
    StudentScoreView,
    StudentSessionResultView,
    StudentSessionView,
    StudentTestRequest,
    StudentTopicProgressView,
    StudentTopicRefView,
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
        key_in_review=view.key_in_review,
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
        keys_in_review=view.keys_in_review,
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
        notes_state=view.notes_state,  # type: ignore[arg-type]
    )


def _notes(view: StudentNotesView) -> StudentNotesSchema:
    return StudentNotesSchema(
        code=view.code,
        state=view.state,  # type: ignore[arg-type]
        generated_at=view.generated_at,
        sections=[
            StudentNoteSectionSchema(
                number=apartado.number,
                key=apartado.key,
                title=apartado.title,
                epigraph_code=apartado.epigraph_code,
                anchor=apartado.anchor,
                body_markdown=apartado.body_markdown,
                questions_covered=apartado.questions_covered,
            )
            for apartado in view.sections
        ],
    )


def _report(view: StudentReportView) -> StudentReportSchema:
    return StudentReportSchema(
        section_key=view.section_key,
        reason=view.reason,
        status=view.status,  # type: ignore[arg-type]
        created_at=view.created_at,
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


def _topic_ref(view: StudentTopicRefView) -> StudentTopicRefSchema:
    return StudentTopicRefSchema(code=view.code, title=view.title)


def _result_question(view: StudentResultQuestionView) -> StudentResultQuestionSchema:
    return StudentResultQuestionSchema(
        position=view.position,
        is_reserve=view.is_reserve,
        part_code=view.part_code,
        part_name=view.part_name,
        stem=view.stem,
        options=[StudentOptionSchema(key=opcion.key, text=opcion.text) for opcion in view.options],
        chosen=list(view.chosen_option_keys),
        correct=list(view.correct_option_keys),
        outcome=view.outcome,  # type: ignore[arg-type]
        elapsed_ms=view.elapsed_ms,
        topics=[_topic_ref(tema) for tema in view.topics],
        key_in_review=view.key_in_review,
    )


def _result_topic(view: StudentResultTopicView) -> StudentResultTopicSchema:
    return StudentResultTopicSchema(
        code=view.code,
        title=view.title,
        correct=view.correct,
        wrong=view.wrong,
        blank=view.blank,
        graded=view.graded,
        accuracy=view.accuracy,
    )


def _session_result(view: StudentSessionResultView) -> StudentSessionResultSchema:
    return StudentSessionResultSchema(
        session=_session(view.session),
        parts=[_part(parte) for parte in view.parts],
        total=_part(view.total),
        official_available=view.official_available,
        official_note=view.official_note,
        duration_seconds=view.duration_seconds,
        questions=[_result_question(pregunta) for pregunta in view.questions],
        topics=[_result_topic(tema) for tema in view.topics],
    )


def _mock_part(view: StudentMockExamPartView) -> StudentMockExamPartSchema:
    return StudentMockExamPartSchema(
        code=view.code,
        name=view.name,
        ordinary_items=view.ordinary_items,
        reserve_items=view.reserve_items,
        score_max=view.score_max,
        pass_score=view.pass_score,
        penalty=view.penalty,
        time_minutes=view.time_minutes,
    )


def _mock_variant(view: StudentMockExamVariantView) -> StudentMockExamVariantSchema:
    return StudentMockExamVariantSchema(
        variant=view.variant,  # type: ignore[arg-type]
        title=view.title,
        time_limit_minutes=view.time_limit_minutes,
        parts=[_mock_part(parte) for parte in view.parts],
        note=view.note,
    )


def _mock_case_block(view: StudentMockCaseBlockView) -> StudentMockCaseBlockSchema:
    return StudentMockCaseBlockSchema(
        code=view.code,
        title=view.title,
        topics=[
            StudentMockCaseTopicSchema(
                code=tema.code,
                title=tema.title,
                available_questions=tema.available_questions,
            )
            for tema in view.topics
        ],
    )


def _mock_plan(view: StudentMockExamPlanView) -> StudentMockExamPlanSchema:
    return StudentMockExamPlanSchema(
        opposition=_opposition(view.opposition),
        full=_mock_variant(view.full),
        short=_mock_variant(view.short),
        case_blocks=[_mock_case_block(bloque) for bloque in view.case_blocks],
    )


def _official_exam(view: StudentOfficialExamView) -> StudentOfficialExamSchema:
    return StudentOfficialExamSchema(
        position=view.position,
        title=view.title,
        held_at=view.held_at,
        questions=view.questions,
        ready=view.ready,
    )


def _official_exams(view: StudentOfficialExamsView) -> StudentOfficialExamsSchema:
    return StudentOfficialExamsSchema(exams=[_official_exam(examen) for examen in view.exams])


def _mistake(view: StudentMistakeView) -> StudentMistakeSchema:
    return StudentMistakeSchema(
        stem=view.stem,
        topics=[_topic_ref(tema) for tema in view.topics],
        last_failed_at=view.last_failed_at,
        times_failed=view.times_failed,
        due=view.due,
    )


def _mistake_topic(view: StudentMistakeTopicView) -> StudentMistakeTopicSchema:
    return StudentMistakeTopicSchema(
        code=view.code,
        title=view.title,
        failed=view.failed,
        due=view.due,
    )


def _mistakes(view: StudentMistakesView) -> StudentMistakesSchema:
    return StudentMistakesSchema(
        total=view.total,
        due_total=view.due_total,
        questions=[_mistake(fallo) for fallo in view.questions],
        topics=[_mistake_topic(tema) for tema in view.topics],
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
    "/topics/{codigo}/notes",
    response_model=StudentNotesSchema,
    responses=RESOURCE_ERRORS,
    summary="Los apuntes de un tema: su texto en orden de lectura y si están en borrador",
)
def student_topic_notes(
    service: StudentServiceDep,
    codigo: str = Path(
        description="Código legible del tema, como `IV.10` (también se acepta `IV-10`).",
        examples=["IV.10"],
    ),
) -> StudentNotesSchema:
    """Los apuntes del tema, tal como se leen.

    Un tema **en borrador se sirve igual** que uno publicado: el estado viaja con el texto
    (`draft`) y la pantalla lo dice. No se esconden apuntes por no haber pasado una puerta —para eso
    está la marca— y un tema sin apuntes devuelve su estado y una lista vacía, no un 404: el tema
    existe y lo que falta es el texto.
    """
    return _notes(service.notes(codigo))


@router.post(
    "/topics/{codigo}/reports",
    response_model=StudentReportSchema,
    status_code=status.HTTP_201_CREATED,
    responses=WRITE_ERRORS,
    summary="Avisa de que un apartado de los apuntes está mal («esto está mal»)",
)
def student_report_notes(
    service: StudentServiceDep,
    request: StudentReportRequestSchema,
    codigo: str = Path(description="Código legible del tema, como `IV.10`.", examples=["IV.10"]),
) -> StudentReportSchema:
    """Guarda el aviso del alumno sobre un apartado de los apuntes (decisión D2).

    No es un registro de pantalla: entra en `notes_reports` y **en la auditoría**, en la misma
    transacción, y es lo que el propietario verá en su bandeja. El motivo es obligatorio y de una
    línea; el apartado se identifica por su clave y el anclaje lo pone el servidor.
    """
    return _report(service.report(codigo, request.section_key, request.reason))


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
        tests_finished=view.tests_finished,
    )


# --- el simulacro: qué va a caer antes de montarlo ------------------------------------------------


@router.get(
    "/mock-exams",
    response_model=StudentMockExamPlanSchema,
    responses=RESOURCE_ERRORS,
    summary="El simulacro antes de montarlo: sus variantes, sus partes y el bloque del supuesto",
)
def student_mock_exam_plan(service: StudentServiceDep) -> StudentMockExamPlanSchema:
    """Qué va a caer en el simulacro, leído del perfil del examen.

    Es la ruta que hace que se pueda elegir **sabiendo qué se elige**: cuántas preguntas tiene cada
    parte, cuántas de reserva, cuánto dura, con qué se corrige (la penalización publicada) y qué
    temas entran en cada uno de los dos bloques del supuesto. Nada de esto se escribe a mano en la
    pantalla: sale de la convocatoria, y lo que la convocatoria no publica viaja como `null`.
    """
    return _mock_plan(service.mock_exam_plan())


# --- los exámenes oficiales importados ------------------------------------------------------------


@router.get(
    "/official-exams",
    response_model=StudentOfficialExamsSchema,
    responses=RESOURCE_ERRORS,
    summary="Los exámenes oficiales importados (hoy, ninguno: la lista vacía se dice)",
)
def student_official_exams(service: StudentServiceDep) -> StudentOfficialExamsSchema:
    """Los exámenes oficiales que hay importados de esta oposición.

    Una lista vacía es un **estado**, no un error: quiere decir que todavía no se ha importado
    ninguno, y la pantalla lo dice con esas palabras en vez de quedarse en blanco o de enseñar otra
    cosa con el nombre de «examen oficial».
    """
    return _official_exams(service.official_exams())


@router.post(
    "/official-exams/{posicion}/sessions",
    response_model=StudentSessionSchema,
    status_code=status.HTTP_201_CREATED,
    responses=RESOURCE_ERRORS,
    summary="Monta el examen oficial que ocupa esa posición de la lista",
)
def student_create_official_exam(
    service: StudentServiceDep,
    posicion: int = Path(
        ge=1,
        description="Su sitio en la lista de exámenes oficiales (el primero, el segundo).",
    ),
) -> StudentSessionSchema:
    """El examen se pide por su **sitio en la lista**, no por un identificador.

    Es la misma regla que la hoja de respuestas: lo que el alumno tiene delante es la fila, y por
    eso
    la fila es la dirección. Así la zona del alumno sigue sin enseñar de dónde salen las preguntas.
    """
    return _session(service.create_official_exam(posicion))


# --- los fallos: tus preguntas falladas, con su tema ----------------------------------------------


@router.get(
    "/mistakes",
    response_model=StudentMistakesSchema,
    responses=RESOURCE_ERRORS,
    summary="Las preguntas que fallaste la última vez, con su tema, su fecha y cuántas veces",
)
def student_mistakes(service: StudentServiceDep) -> StudentMistakesSchema:
    """Los fallos, y de aquí sale un test.

    Cada fila dice **de qué tema** era la pregunta —el dato que convierte la lista en algo que se
    puede usar— y el reparto por tema es lo que permite pedir un test solo con los fallos de un
    tema. Ese test lo compone el motor con el filtro de falladas, sobre los intentos de verdad: esta
    lista es para mirar, no la fuente de la composición.
    """
    return _mistakes(service.mistakes())


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


@router.get(
    "/sessions/{sesion}/result",
    response_model=StudentSessionResultSchema,
    responses=RESOURCE_ERRORS,
    summary="El resultado de un test terminado: la nota por parte, el tiempo y pregunta a pregunta",
)
def student_session_result(
    service: StudentServiceDep, sesion: str = Path()
) -> StudentSessionResultSchema:
    """El resultado entero de un test terminado, con lo que hace falta para repasar.

    Cada pregunta con tus opciones, lo que marcaste, cuál era la correcta y **de qué tema era**, más
    el desglose por tema. Es la pantalla que contesta a «qué he fallado y por dónde lo repaso», que
    es
    para lo que sirve un resultado; de un test sin terminar, el motor dice que no hay resultado y la
    respuesta lo repite en lugar de enseñar medio resultado.
    """
    return _session_result(service.result(sesion))
