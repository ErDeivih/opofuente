"""Casos de uso del temario común para la API (B-004/B-005).

La capa API pide aquí y traduce a DTO; el repositorio lee la base. El servicio solo decide qué es
«no encontrado» y no repite reglas que ya viven en el modelo.
"""

from __future__ import annotations

from opofuente.application.curriculum_models import (
    CurriculumDetailView,
    CurriculumNodeDetailView,
    CurriculumSummaryView,
    CurriculumVersionView,
    ProgressView,
    ReferenceView,
    StudyMarkView,
    TemarioView,
)
from opofuente.application.ports import Clock, CurriculumReadRepository
from opofuente.domain.errors import NotFoundError


class CurriculumReadService:
    def __init__(self, repository: CurriculumReadRepository, clock: Clock) -> None:
        self._repository = repository
        self._clock = clock

    def list_curricula(self, *, kind: str | None = None) -> tuple[CurriculumSummaryView, ...]:
        return self._repository.list_curricula(kind=kind)

    def get_curriculum(self, code: str) -> CurriculumDetailView:
        vista = self._repository.get_curriculum(code)
        if vista is None:
            raise NotFoundError("temario", code)
        return vista

    def list_versions(self, code: str) -> tuple[CurriculumVersionView, ...]:
        versiones = self._repository.list_versions(code)
        if versiones is None:
            raise NotFoundError("temario", code)
        return versiones

    def get_progress(self, code: str) -> ProgressView:
        avance = self._repository.get_progress(code)
        if avance is None:
            raise NotFoundError("temario", code)
        return avance

    def list_references(self, convocation_id: str) -> tuple[ReferenceView, ...]:
        referencias = self._repository.list_references(convocation_id)
        if referencias is None:
            raise NotFoundError("convocatoria", convocation_id)
        return referencias

    def get_temario(self, convocation_id: str) -> TemarioView:
        temario = self._repository.get_temario(convocation_id)
        if temario is None:
            raise NotFoundError("temario de la convocatoria", convocation_id)
        return temario

    def get_node(
        self, node_id: str, *, convocation_id: str | None = None
    ) -> CurriculumNodeDetailView:
        detalle = self._repository.get_node(node_id, convocation_id=convocation_id)
        if detalle is None:
            raise NotFoundError("nodo del temario", node_id)
        return detalle

    def mark_studied(self, node_id: str) -> StudyMarkView:
        marca = self._repository.mark_studied(node_id, now=self._clock.now())
        if marca is None:
            raise NotFoundError("nodo del temario", node_id)
        return marca

    def unmark_studied(self, node_id: str) -> bool:
        resultado = self._repository.unmark_studied(node_id)
        if resultado is None:
            raise NotFoundError("nodo del temario", node_id)
        return resultado
