"""El consentimiento de las cookies y el inventario de datos, servidos (§9).

**Qué decide este servicio.** Tres cosas, y las tres son de la misma familia —decir la verdad sobre
los datos—:

1. **Qué se pregunta y con qué texto vigente.** La versión del texto va con la decisión: si el texto
   cambia en lo que pide, la decisión vieja deja de valer y se vuelve a preguntar.
2. **Qué se ha decidido**, leído de la cookie de quien navega. Sin cookie, `None`: «no ha decidido»
y
   «ha rechazado» son dos cosas distintas y el código no las mezcla, porque de esa diferencia
   depende
   que no se ponga ninguna cookie que no sea necesaria.
3. **La constancia agregada** de que se preguntó: cuántas decisiones se han tomado y con qué
   desenlace, **sin sujeto**. Es lo que permite demostrar que el aviso existía sin construir un
   registro de quién aceptó qué.
"""

from __future__ import annotations

from dataclasses import dataclass

from opofuente.application.account_models import ConsentSummary
from opofuente.application.ports import Clock, ConsentStore
from opofuente.config import Settings
from opofuente.domain.accounts import (
    CONSENT_POLICY_VERSION,
    CONSENT_PURPOSES,
    ESSENTIAL_PURPOSES,
    ConsentState,
    parse_consent,
    render_consent,
)
from opofuente.domain.errors import LegalDisabledError
from opofuente.domain.legal import (
    COOKIES,
    DATA_INVENTORY,
    LEGAL_DOCUMENTS,
    LEGAL_TEXT_UPDATED_ON,
    LEGAL_TEXT_VERSION,
    NEGATIVE_CLAIMS,
    OWNER_FIELDS_PENDING,
    CookieDeclaration,
    DataUse,
    LegalDocument,
    NegativeClaim,
)


@dataclass(frozen=True, slots=True)
class ConsentPolicyView:
    """Lo que la pantalla necesita para pedir el consentimiento sin inventarse nada."""

    policy_version: int
    text_version: int
    text_updated_on: str
    purposes: tuple[str, ...]
    essential: tuple[str, ...]
    cookies: tuple[CookieDeclaration, ...]
    analytics_available: bool
    legal_available: bool


class LegalService:
    """Los textos, el inventario y la decisión sobre las cookies."""

    def __init__(
        self,
        *,
        store: ConsentStore,
        clock: Clock,
        settings: Settings,
    ) -> None:
        self._store = store
        self._clock = clock
        self._settings = settings

    @property
    def enabled(self) -> bool:
        return self._settings.legal_enabled

    def require_enabled(self) -> None:
        """Corta si esta instalación no sirve los textos legales.

        Es lo que hace que la bandera signifique algo: con `OPOFUENTE_LEGAL_ENABLED=0` las rutas
        contestan 404 y no hay ninguna página legal que se pueda leer ni ninguna cookie de
        consentimiento que se pueda poner. O se sirve, o no se sirve: **no se sirve a medias**.
        """
        if not self.enabled:
            raise LegalDisabledError("esta instalación no sirve los textos legales")

    @property
    def documents(self) -> tuple[LegalDocument, ...]:
        return LEGAL_DOCUMENTS

    @property
    def inventory(self) -> tuple[DataUse, ...]:
        return DATA_INVENTORY

    @property
    def negative_claims(self) -> tuple[NegativeClaim, ...]:
        return NEGATIVE_CLAIMS

    @property
    def cookies(self) -> tuple[CookieDeclaration, ...]:
        return COOKIES

    @property
    def owner_fields_pending(self) -> tuple[str, ...]:
        return OWNER_FIELDS_PENDING

    @property
    def text_updated_on(self) -> str:
        return LEGAL_TEXT_UPDATED_ON

    @property
    def text_version(self) -> int:
        return LEGAL_TEXT_VERSION

    def policy(self) -> ConsentPolicyView:
        return ConsentPolicyView(
            policy_version=CONSENT_POLICY_VERSION,
            text_version=LEGAL_TEXT_VERSION,
            text_updated_on=LEGAL_TEXT_UPDATED_ON,
            purposes=CONSENT_PURPOSES,
            essential=tuple(sorted(ESSENTIAL_PURPOSES)),
            cookies=COOKIES,
            analytics_available=self._settings.analytics_enabled,
            legal_available=self._settings.legal_enabled,
        )

    def state(self, raw_cookie: str | None) -> ConsentState | None:
        """La decisión de quien navega, leída de su cookie. `None` es «sin decidir»."""
        return parse_consent(raw_cookie, now=self._clock.now())

    def decide(
        self,
        *,
        analytics: bool,
        preferences: bool,
        raw_cookie: str | None = None,
    ) -> ConsentState:
        """Guarda la decisión: en la cookie de quien la toma y, sin sujeto, en la base.

        La decisión **sustituye** a la anterior: aceptar después de haber rechazado no deja las dos;
        es lo que se espera de un botón que dice «guardar mi elección».

        Si el texto vigente no ha cambiado y la decisión es la misma que ya había, no se escribe
        otra
        fila de constancia: repetir la misma respuesta no es una decisión nueva.
        """
        ahora = self._clock.now()
        anterior = self.state(raw_cookie)
        estado = ConsentState(
            policy_version=CONSENT_POLICY_VERSION,
            analytics=analytics,
            preferences=preferences,
            decided_at=ahora,
        )
        repetida = (
            anterior is not None
            and anterior.policy_version == estado.policy_version
            and anterior.analytics == estado.analytics
            and anterior.preferences == estado.preferences
        )
        if not repetida:
            self._store.record_consent(
                now=ahora,
                policy_version=CONSENT_POLICY_VERSION,
                analytics=analytics,
                preferences=preferences,
            )
        return estado

    def render(self, state: ConsentState) -> str:
        return render_consent(state)

    def summary(self) -> ConsentSummary:
        return self._store.consent_summary()


__all__ = ["ConsentPolicyView", "LegalService"]
