"""Capa API: rutas, DTO, validación y códigos HTTP.

No contiene reglas de puntuación, clasificación ni acceso directo a datos.
"""

from __future__ import annotations

from fastapi import APIRouter

from opofuente.api.routes import (
    backups,
    changes,
    classification,
    exports,
    housekeeping,
    ingestion,
    library,
    profiles,
    questions,
    readiness,
    reviews,
    search,
    study,
    system,
    telemetry,
    temario,
)

api_router = APIRouter()
api_router.include_router(system.router)
api_router.include_router(profiles.router)
api_router.include_router(temario.router)
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
api_router.include_router(telemetry.router)

__all__ = ["api_router"]
