"""Importación de convocatorias C1 que referencian el temario común (B-006).

Valida el fixture y delega la escritura; el informe dice cuántas se importaron, cuántas quedan por
confirmar y cuántas filas de la fuente se descartaron con su motivo.
"""

from __future__ import annotations

from opofuente.application.ports import Clock, ConvocatoriasRepository
from opofuente.application.read_models import ConvocatoriasSeedReport
from opofuente.domain.convocatorias_c1 import C1ConvocatoriasFixture, validate_c1_convocatorias


class ConvocatoriasService:
    def __init__(self, repository: ConvocatoriasRepository, clock: Clock) -> None:
        self._repository = repository
        self._clock = clock

    def seed(self, fixture: C1ConvocatoriasFixture) -> ConvocatoriasSeedReport:
        """Siembra idempotente de convocatorias C1 y sus referencias `primary`."""
        validate_c1_convocatorias(fixture)
        return self._repository.upsert_c1_convocatorias(fixture, now=self._clock.now())
