"""Capa API: rutas, DTO, validación y códigos HTTP.

No contiene reglas de puntuación, clasificación ni acceso directo a datos.
"""

from __future__ import annotations

from fastapi import APIRouter

from opofuente.api.routes import (
    backups,
    changes,
    classification,
    dossier,
    exports,
    housekeeping,
    ingestion,
    library,
    notes_incidents,
    notes_reports,
    profiles,
    question_file,
    questions,
    readiness,
    reviews,
    search,
    student,
    study,
    system,
)

api_router = APIRouter()
api_router.include_router(system.router)
api_router.include_router(profiles.router)
api_router.include_router(ingestion.router)
api_router.include_router(classification.router)
api_router.include_router(library.router)
api_router.include_router(questions.router)
api_router.include_router(study.router)
api_router.include_router(search.router)
api_router.include_router(reviews.router)
api_router.include_router(exports.router)
api_router.include_router(changes.router)
api_router.include_router(backups.router)
api_router.include_router(housekeeping.router)
api_router.include_router(readiness.router)
# El dossier va al final: sus rutas cuelgan de `/curriculum-nodes/{node_id}` y no deben quedar
# detrás
# de una ruta con parámetro que las tape (ADR-018).
api_router.include_router(dossier.router)
# La zona del alumno (F2) va **después** del dossier por el mismo motivo y por uno propio: todas sus
# rutas cuelgan de `/student/*`, y ninguna otra ruta del contrato empieza por ahí, así que no puede
# tapar a nadie ni quedar tapada.
api_router.include_router(student.router)
# La bandeja de avisos del alumno (F13) es del propietario y cuelga de `/notes-reports`, un prefijo
# que no comparte con nadie: va al final, con las demás rutas que no pueden quedar tapadas.
api_router.include_router(notes_reports.router)
# La bandeja del motor (F18) cuelga de `/notes-incidents`, otro prefijo que no comparte con nadie:
# va
# al final por el mismo motivo que la del alumno.
api_router.include_router(notes_incidents.router)
# La ficha de pregunta (F20) cuelga de `/question-files`, un prefijo que no comparte con nadie: va
# al final por el mismo motivo que las dos bandejas. Es la pantalla que faltaba detrás de los
# enlaces que la bandeja del motor y el banco ya usaban (`/admin/preguntas?pregunta=<id>`).
api_router.include_router(question_file.router)

__all__ = ["api_router"]
