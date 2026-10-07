"""Rutas de la zona del alumno (F2, `08_API-CONTRACT` §10 ampliado).

Cuatro rutas de **lectura**, y ninguna más: `overview`, `syllabus`, `topics/{codigo}` y `progress`.
Lo que devuelven lo declaran `student_schemas.py`, que no tiene campo para la evidencia, el
conjunto, la clave, la versión ni la ruta.

Lo que **no** está aquí todavía, y por qué:

- `POST /student/tests` y `POST /student/mock-exams`: montar un test de varios bloques, o un
  simulacro con elección de bloque, exige una composición que `StudyService` no sabe hacer hoy. Ese
  servicio compone **por conjunto de preguntas** (`sources`) o por **un** tema
  (`curriculum_node_id`), y del simulacro coge la parte entera de un solo conjunto tal como se
  publica. Escribir aquí la composición —elegir preguntas por bloque, congelar su clave y su
  posición, aplicar la penalización— duplicaría la parte más delicada del servicio de estudio y
  dejaría dos verdades sobre cómo se corrige una sesión. Necesita un cambio en `StudyService`
  (composición por varios temas, por bloque o sobre un fondo común del programa), y eso es una
  decisión de diseño del arquitecto, no de esta capa.
- `GET /student/official-exams`: hoy los exámenes oficiales solo se listan por conjunto de preguntas
  con su identificador a la vista, que es justo lo que esta capa no puede enseñar.
- `GET /student/topics/{codigo}/notes`: depende de `topic_notes`, que todavía no existe (F4).
"""

from __future__ import annotations

from fastapi import APIRouter, Path

from opofuente.api.deps import StudentServiceDep
from opofuente.api.error_responses import RESOURCE_ERRORS
from opofuente.api.student_schemas import (
    StudentBlockProgressSchema,
    StudentEpigraphSchema,
    StudentOppositionSchema,
    StudentOverviewSchema,
    StudentProgressSchema,
    StudentScoreSchema,
    StudentSessionSchema,
    StudentSyllabusSchema,
    StudentTopicProgressSchema,
    StudentTopicSchema,
)
from opofuente.application.student_models import (
    StudentBlockProgressView,
    StudentOppositionView,
    StudentOverviewView,
    StudentProgressView,
    StudentScoreView,
    StudentSessionView,
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
