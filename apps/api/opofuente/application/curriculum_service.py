"""Casos de uso del temario común (B-002).

La capa API y las herramientas piden aquí; el repositorio guarda. El servicio comprueba que el
temario es coherente antes de escribir nada y devuelve el informe de la siembra: qué se creó, qué se
actualizó, si quedó publicado y con qué recuentos. `seed_profiles --check` usa ese informe para
fallar cuando hay cambios pendientes, igual que con los perfiles.
"""

from __future__ import annotations

from opofuente.application.ports import Clock, CurriculumRepository
from opofuente.application.read_models import CurriculumSeedReport
from opofuente.domain.curricula import CommonCurriculum, validate_common_curriculum


class CurriculaService:
    def __init__(self, repository: CurriculumRepository, clock: Clock) -> None:
        self._repository = repository
        self._clock = clock

    def seed(self, curriculum: CommonCurriculum) -> CurriculumSeedReport:
        """Siembra idempotente del temario común y de sus referencias."""
        # Se vuelve a validar aquí: la siembra no debe aceptar un temario incoherente aunque venga
        # de un fixture ya construido (mismo criterio que con los perfiles).
        validate_common_curriculum(curriculum)
        return self._repository.upsert_common_curriculum(curriculum, now=self._clock.now())
