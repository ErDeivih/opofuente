"""Capa API: rutas, DTO, validación y códigos HTTP.

No contiene reglas de puntuación, clasificación ni acceso directo a datos.
"""

from __future__ import annotations

from fastapi import APIRouter

from opofuente.api.routes import classification, ingestion, profiles, system

api_router = APIRouter()
api_router.include_router(system.router)
api_router.include_router(profiles.router)
api_router.include_router(ingestion.router)
api_router.include_router(classification.router)

__all__ = ["api_router"]
