"""El canje de una invitacion, por HTTP (M8).

**Que hace**: recibe el token del enlace y la contrasena que quiere poner la
persona invitada, **y crea la cuenta**.

**Y las dos decisiones que estan en el codigo:**

1. **el canje responde `400` con su motivo y no `401`**: **aqui no hay sesion
   que autenticar**, **lo que falla es el enlace** —caducado, usado o de otra
   direccion—, **y eso es una peticion mal formada, no una falta de permiso**;
2. **el mensaje no distingue «no existe» de «estaba mal»**, **que ya lo decide
   `canjear`**: **confirmar que un enlace existe a quien no lo tiene es regalar
   media invitacion.**
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from opofuente.api.error_responses import WRITE_ERRORS
from opofuente.tools.canjear import MINIMO, canjear

router = APIRouter(tags=["invitaciones"])


class CanjeSchema(BaseModel):
    """Lo que manda la pantalla: el token del enlace y la contrasena nueva."""

    token: str = Field(min_length=1)
    correo: str = Field(min_length=3)
    contrasena: str = Field(min_length=MINIMO)


class CanjeResultadoSchema(BaseModel):
    creada: bool
    motivo: str


@router.post(
    "/invitations/accept",
    response_model=CanjeResultadoSchema,
    responses=WRITE_ERRORS,
    summary="Canjea una invitacion y crea la cuenta (M8)",
)
def accept_invitation(cuerpo: CanjeSchema) -> CanjeResultadoSchema:
    """**Un solo uso, con caducidad y para una direccion**: lo comprueba `canjear`.

    **La contrasena entra por el cuerpo y no se registra en ningun sitio**:
    **el log de una peticion no es lugar para un secreto.**
    """
    bien, motivo = canjear(cuerpo.token, cuerpo.correo, cuerpo.contrasena)
    if not bien:
        # **400 y no 401**: no es que falte permiso, es que el enlace no vale.
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=motivo)
    return CanjeResultadoSchema(creada=True, motivo=motivo)
