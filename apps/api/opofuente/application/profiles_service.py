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
from opofuente.domain.errors import InvalidStateError, NotFoundError
from opofuente.domain.profiles import (
    ConvocationStatus,
    Profile,
    validate_curriculum,
    validate_exam,
)

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

    def activate_convocation(self, convocation_id: str) -> ConvocationSummary:
        """Cambia la convocatoria vigente de una oposición.

        Se exige que la convocatoria se pueda usar de verdad: una convocatoria publicada (no en
        borrador ni archivada) y con programa sembrado. Una oposición con dos convocatorias —la de
        acceso libre de 2022 y la de estabilización, en Celador— necesita poder elegir con cuál se
        estudia, y la aplicación no debe dejar elegir una que no tenga temario que mostrar.
        """
        detail = self.get_convocation(convocation_id)
        status = detail.summary.status
        if status is ConvocationStatus.DRAFT:
            raise InvalidStateError(
                "la convocatoria está en borrador y todavía no se ha publicado: "
                "no se puede convertir en la vigente"
            )
        if status is ConvocationStatus.ARCHIVED:
            raise InvalidStateError(
                "la convocatoria está archivada: está marcada como no utilizable por la aplicación"
            )
        curriculum = self._repository.get_curriculum(convocation_id)
        if curriculum is None or not curriculum.nodes:
            raise InvalidStateError(
                "la convocatoria no tiene programa sembrado: no hay temario con el que trabajar"
            )
        activated = self._repository.activate_convocation(convocation_id, now=self._clock.now())
        if activated is None:  # pragma: no cover - se acaba de comprobar que existe
            raise NotFoundError("convocatoria", convocation_id)
        logger.info(
            "profiles.convocation_activated",
            extra={"event": "convocation_activated", "path": activated.code},
        )
        return activated

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
