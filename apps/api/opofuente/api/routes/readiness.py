"""Rutas del resumen de preparación y de lo que espera a una persona (S12.6).

Dos rutas de solo lectura, y las dos existen por la misma pregunta del propietario: «¿ya puedo
estudiar con lo que he soltado, o me falta algo?». La primera responde por oposición (material por
papel, preguntas por tema y claves activas); la segunda dice qué espera todavía una decisión humana,
que es lo único que la aplicación no puede hacer sola (ADR-017).

No hay ruta de escritura: este resumen no cambia nada, solo cuenta lo que hay.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from opofuente.api.deps import ReadinessServiceDep
from opofuente.api.error_responses import BASE_ERRORS, RESOURCE_ERRORS
from opofuente.api.readiness_schemas import (
    PendingActionsSchema,
    StudyReadinessSchema,
    pending_actions,
    readiness,
)

router = APIRouter()


@router.get(
    "/oppositions/{opposition_id}/readiness",
    response_model=StudyReadinessSchema,
    responses={**BASE_ERRORS, **RESOURCE_ERRORS},
    summary="¿Está esta oposición lista para estudiar, y qué falta?",
    tags=["perfiles"],
)
def get_readiness(opposition_id: str, service: ReadinessServiceDep) -> StudyReadinessSchema:
    """Material por papel, preguntas por tema y claves activas, con lo que falta en palabras."""
    vista = service.readiness(opposition_id)
    if vista is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"la oposición «{opposition_id}» no existe",
        )
    return readiness(vista)


@router.get(
    "/pending-actions",
    response_model=PendingActionsSchema,
    responses=BASE_ERRORS,
    summary="Lo que sigue esperando una decisión de una persona",
    tags=["sistema"],
)
def get_pending_actions(service: ReadinessServiceDep) -> PendingActionsSchema:
    """Incidencias de importación, propuestas de clasificación, cambios y material sin aceptar."""
    return pending_actions(service.pending_actions())
