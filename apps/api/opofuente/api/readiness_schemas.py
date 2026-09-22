"""Esquemas del resumen de preparación y de lo que espera a una persona (S12.6).

Las frases (`detail`) las compone el servidor y la interfaz las enseña tal cual: el mismo texto que
viaja en la respuesta es el que se lee en Inicio, así que no hay dos versiones de la misma cifra.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from opofuente.application.readiness_models import (
    PendingActionsView,
    PendingActionView,
    ReadinessStepView,
    StepStatus,
    StudyReadinessView,
)


class StudyReadinessStepSchema(BaseModel):
    """Un paso hacia poder estudiar: qué es, cómo está y por dónde se resuelve."""

    key: str
    title: str
    status: StepStatus
    detail: str
    count: int
    action_href: str
    action_label: str


class StudyReadinessSchema(BaseModel):
    """Si esta oposición se puede estudiar ya, paso a paso, y qué falta si falta algo."""

    opposition_id: str
    opposition_name: str
    convocation_code: str | None = None
    ready: bool
    steps: list[StudyReadinessStepSchema]
    missing: list[str] = Field(
        default_factory=list,
        description="Una frase por paso que no está listo, tal y como se enseña.",
    )


class PendingActionSchema(BaseModel):
    """Algo que espera a una persona, con la cifra y la pantalla donde se resuelve."""

    key: str
    title: str
    detail: str
    count: int
    href: str
    label: str


class PendingActionsSchema(BaseModel):
    """Todo lo que espera a una persona ahora mismo, ya ordenado."""

    actions: list[PendingActionSchema]
    total: int


def step(step: ReadinessStepView) -> StudyReadinessStepSchema:
    return StudyReadinessStepSchema(
        key=step.key,
        title=step.title,
        status=step.status,
        detail=step.detail,
        count=step.count,
        action_href=step.action_href,
        action_label=step.action_label,
    )


def readiness(view: StudyReadinessView) -> StudyReadinessSchema:
    return StudyReadinessSchema(
        opposition_id=view.opposition_id,
        opposition_name=view.opposition_name,
        convocation_code=view.convocation_code,
        ready=view.ready,
        steps=[step(paso) for paso in view.steps],
        missing=list(view.missing),
    )


def action(view: PendingActionView) -> PendingActionSchema:
    return PendingActionSchema(
        key=view.key,
        title=view.title,
        detail=view.detail,
        count=view.count,
        href=view.href,
        label=view.label,
    )


def pending_actions(view: PendingActionsView) -> PendingActionsSchema:
    return PendingActionsSchema(
        actions=[action(accion) for accion in view.actions],
        total=view.total,
    )


__all__ = [
    "PendingActionSchema",
    "PendingActionsSchema",
    "StudyReadinessSchema",
    "StudyReadinessStepSchema",
    "action",
    "pending_actions",
    "readiness",
    "step",
]
