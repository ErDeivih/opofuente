"""Casos de uso de perfiles: consultar convocatorias y programa, activar y sembrar.

La capa API no consulta la base de datos ni decide reglas: pide aquí y traduce a DTO.
"""

from __future__ import annotations

import logging
from collections.abc import Iterable, Sequence

from opofuente.application.ports import Clock, ProfileRepository
from opofuente.application.read_models import (
    ConvocationDetail,
    ConvocationSummary,
    CurriculumView,
    NodeDetail,
    OppositionDetail,
    OppositionSummary,
    SeedReport,
)
from opofuente.domain.errors import NotFoundError
from opofuente.domain.profiles import Profile, validate_curriculum, validate_exam

logger = logging.getLogger(__name__)


class ProfilesService:
    def __init__(self, repository: ProfileRepository, clock: Clock) -> None:
        self._repository = repository
        self._clock = clock

    def list_oppositions(self) -> Sequence[OppositionSummary]:
        return self._repository.list_oppositions()

    def get_opposition(self, opposition_id: str) -> OppositionDetail:
        detail = self._repository.get_opposition(opposition_id)
        if detail is None:
            raise NotFoundError("oposición", opposition_id)
        return detail

    def activate_opposition(self, opposition_id: str) -> OppositionSummary:
        activated = self._repository.activate_opposition(opposition_id, now=self._clock.now())
        if activated is None:
            raise NotFoundError("oposición", opposition_id)
        logger.info(
            "profiles.opposition_activated",
            extra={"event": "opposition_activated", "path": activated.code},
        )
        return activated

    def list_convocations(self, opposition_id: str) -> Sequence[ConvocationSummary]:
        if self._repository.get_opposition(opposition_id) is None:
            raise NotFoundError("oposición", opposition_id)
        return self._repository.list_convocations(opposition_id)

    def get_convocation(self, convocation_id: str) -> ConvocationDetail:
        detail = self._repository.get_convocation(convocation_id)
        if detail is None:
            raise NotFoundError("convocatoria", convocation_id)
        return detail

    def get_curriculum(self, convocation_id: str) -> CurriculumView:
        view = self._repository.get_curriculum(convocation_id)
        if view is None:
            raise NotFoundError("convocatoria", convocation_id)
        return view

    def get_node(self, node_id: str) -> NodeDetail:
        detail = self._repository.get_node(node_id)
        if detail is None:
            raise NotFoundError("nodo de programa", node_id)
        return detail

    def seed(self, profiles: Iterable[Profile]) -> SeedReport:
        """Siembra idempotente de perfiles oficiales."""
        outcomes = []
        for profile in profiles:
            # Se vuelve a validar aquí: la siembra no debe aceptar un perfil incoherente aunque
            # venga de un fixture ya construido.
            validate_curriculum(profile.convocation.code, profile.curriculum)
            validate_exam(profile.convocation.code, profile.parts, profile.rules)
            outcomes.append(self._repository.upsert_profile(profile, now=self._clock.now()))
        report = SeedReport(profiles=tuple(outcomes))
        logger.info(
            "profiles.seeded",
            extra={"event": "profiles_seeded", "revision": report.summary()},
        )
        return report
