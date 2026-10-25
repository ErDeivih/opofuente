"""Las rutas de las tarjetas de repaso (M3).

**Tres rutas y ninguna de mas**: lo que vence, responder una tarjeta y el numero
que la cola ensena antes de empezar. **Generar tarjetas no es una ruta**: es una
accion que cuesta dinero si un dia usa el modelo, y se pide desde su herramienta.

**Por que el `answer` responde con la tarjeta y no con un `204`**: el alumno
necesita saber cuando vuelve la que acaba de contestar, y eso lo decide SM-2 en el
servidor. Devolverlo evita pedirla otra vez.
"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter
from pydantic import BaseModel, Field

from opofuente.api.deps import CardServiceDep
from opofuente.api.error_responses import RESOURCE_ERRORS
from opofuente.domain.errors import NotFoundError
from opofuente.domain.repaso import Respuesta
from opofuente.infrastructure.card_repository import CardView

router = APIRouter(tags=["tarjetas"])


def _schema(tarjeta: CardView) -> CardSchema:
    """Una tarjeta del repositorio, tal como viaja por la API."""
    return CardSchema(
        id=tarjeta.id,
        front=tarjeta.front,
        back=tarjeta.back,
        citation=tarjeta.citation,
        due_at=tarjeta.due_at,
        interval_days=tarjeta.interval_days,
        repetitions=tarjeta.repetitions,
    )


class CardSchema(BaseModel):
    """Una tarjeta tal como la pinta la pantalla de repaso."""

    id: str
    front: str
    back: str
    citation: str | None = None
    due_at: datetime
    interval_days: int
    repetitions: int


class DueFailureOptionSchema(BaseModel):
    """Una opción del fallo, con su letra y su texto."""

    key: str
    text: str


class DueFailureSchema(BaseModel):
    """**Una pregunta fallada que vence hoy** (fase «lo que ve el alumno», punto 3).

    **Lleva el enunciado y las opciones y NO la clave**: contestarla es lo que la saca de la cola, y
    la corrección la hace el servidor. **La explicación se sirve al corregir**, no antes.
    """

    question_version_id: str
    stem: str
    options: list[DueFailureOptionSchema]


class CardQueueSchema(BaseModel):
    """La cola del día: **tarjetas, fallos vencidos y el total**, que son tres cosas distintas."""

    tarjetas: list[CardSchema]
    #: **Los fallos vencidos**, entrelazados con las tarjetas y dentro del mismo tope.
    fallos: list[DueFailureSchema] = []
    total: int = Field(description="Cuántas vencen hoy, no cuántas caben en la pantalla")


class PendingSchema(BaseModel):
    """Solo el numero: lo que la cola ensena antes de empezar."""

    vencen: int


class AnswerCardSchema(BaseModel):
    """Lo que se responde a una tarjeta, con las cuatro opciones de SM-2."""

    respuesta: Respuesta


@router.get(
    "/cards/pending",
    response_model=PendingSchema,
    summary="Cuántas tarjetas vencen hoy (M3)",
)
def pending_cards(service: CardServiceDep) -> PendingSchema:
    """El número de vencidas, **sin traerlas**: la cola lo enseña antes de empezar."""
    return PendingSchema(vencen=service.vencen())


@router.get(
    "/cards/queue",
    response_model=CardQueueSchema,
    summary="La cola del día: las tarjetas que vencen (M3)",
)
def card_queue(service: CardServiceDep) -> CardQueueSchema:
    """Las tarjetas vencidas, entrelazadas y con el tope del día.

    **`total` es el de vencidas, no el de la página**: es lo que le queda al alumno,
    y contar solo lo que cabe en la pantalla mentiría hacia abajo.
    """
    tarjetas, fallos = service.cola_del_dia()
    return CardQueueSchema(
        tarjetas=[_schema(tarjeta) for tarjeta in tarjetas],
        fallos=[
            DueFailureSchema(
                question_version_id=fail.question_version_id,
                stem=fail.stem,
                options=[
                    DueFailureOptionSchema(key=clave, text=texto) for clave, texto in fail.options
                ],
            )
            for fail in fallos
        ],
        # **El total es el de la cola entera**, tarjetas y fallos: es lo que le queda al alumno, y
        # contar solo las tarjetas mentiría hacia abajo.
        total=service.vencen() + len(fallos),
    )


@router.post(
    "/cards/{card_id}/answer",
    response_model=CardSchema,
    responses=RESOURCE_ERRORS,
    summary="Responde una tarjeta y devuelve cuándo vuelve (M3)",
)
def answer_card(
    card_id: str,
    cuerpo: AnswerCardSchema,
    service: CardServiceDep,
) -> CardSchema:
    """Aplica SM-2 y devuelve la tarjeta **con su nueva fecha de vuelta**.

    **404 si no existe**: un `True`/`False` no le dice nada al alumno sobre qué
    pasó con la tarjeta que acaba de contestar.
    """
    if not service.responder(card_id, cuerpo.respuesta):
        raise NotFoundError("tarjeta", card_id)
    actual = service.una(card_id)
    if actual is None:
        raise NotFoundError("tarjeta", card_id)
    return _schema(actual)
