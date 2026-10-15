"""La analítica propia: contar sin permiso, no; contar con identificadores, tampoco (§10).

**Las dos condiciones, comprobadas en el servidor.** Un suceso se cuenta solo si se cumplen las dos:

1. la analítica está encendida en esta instalación (`OPOFUENTE_ANALYTICS_ENABLED=1`);
2. quien navega ha **aceptado** la analítica, y eso se lee de su cookie de consentimiento en la
   propia petición.

La segunda no se puede delegar en la pantalla. Una pantalla que decide si manda el suceso es una
promesa; que el servidor conteste que no cuando falta el permiso es un hecho. Y como el esquema no
tiene ni cuenta, ni sesión, ni dirección, ni texto libre, lo que se cuenta no puede convertirse en
un
dato personal ni por descuido: la etiqueta sale de una lista cerrada o se rechaza.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from opofuente.application.account_models import CountByLabel
from opofuente.application.ports import AnalyticsStore, Clock
from opofuente.config import Settings
from opofuente.domain.accounts import ConsentState
from opofuente.domain.analytics import RETENTION_DAYS, AnalyticsEvent, is_valid_event
from opofuente.domain.errors import ConsentRequiredError, UnsupportedError


class AnalyticsService:
    """Cuenta pantallas y acciones, agregadas y sin identificadores."""

    def __init__(
        self,
        *,
        store: AnalyticsStore,
        clock: Clock,
        settings: Settings,
    ) -> None:
        self._store = store
        self._clock = clock
        self._settings = settings

    @property
    def enabled(self) -> bool:
        return self._settings.analytics_enabled

    @property
    def retention_days(self) -> int:
        return RETENTION_DAYS

    @property
    def requires_consent(self) -> bool:
        """Siempre. Se declara para que la interfaz no tenga que saberlo por su cuenta."""
        return True

    def record(self, *, name: str, label: str, consent: ConsentState | None) -> AnalyticsEvent:
        """Cuenta un suceso, o explica por qué no.

        El orden de las comprobaciones importa para el mensaje: primero si la función está encendida
        —si no, esto no existe— y después si hay permiso. Al revés, a quien no ha aceptado se le
        diría «no existe» de algo que sí existe y que puede activar aceptando.
        """
        if not self.enabled:
            raise UnsupportedError(
                "esta instalación no tiene analítica: no se cuenta nada y no hay nada que enviar"
            )
        if not is_valid_event(name, label):
            raise UnsupportedError(
                "ese suceso no está en la lista de lo que se cuenta: solo se cuentan pantallas y "
                "acciones conocidas, sin texto libre"
            )
        if consent is None or not consent.grants("analytics"):
            raise ConsentRequiredError(
                "no se cuenta nada sin tu permiso: acepta la analítica si quieres que se cuente"
            )
        ahora = self._clock.now()
        evento = AnalyticsEvent(day=ahora.date().isoformat(), name=name, label=label)
        self._store.record(evento, now=ahora)
        return evento

    def summary(self, *, days: int = 30) -> list[CountByLabel]:
        return self._store.summary(days=days)

    def totals_by_day(self, *, days: int = 30) -> list[tuple[str, int]]:
        return self._store.totals_by_day(days=days)

    def purge(self, *, days: int = RETENTION_DAYS) -> int:
        """Tira lo que pasa del plazo declarado en el inventario de datos.

        Es lo que hace verdad el «doce meses»: sin esto, la frase sería una promesa sobre filas que
        nadie borra nunca.
        """
        limite = (datetime.now(UTC) - timedelta(days=days)).date().isoformat()
        return self._store.purge_older_than(day=limite)


__all__ = ["AnalyticsService"]
