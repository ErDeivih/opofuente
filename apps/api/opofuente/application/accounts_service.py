"""Cuentas y sesiones: las reglas de verdad, con la base y el reloj detrás de puertos (§8).

**Las cinco decisiones que se ven aquí, y por qué.**

1. **El alta contesta lo mismo siempre.** Si la dirección ya está, no se escribe nada y se contesta
   igual que si fuera nueva. La respuesta no dice «ya existe» ni «creada»: decir cuál de las dos es,
   es decir quién tiene cuenta en esta aplicación, y eso no se le cuenta a quien no ha demostrado
   ser nadie. Por eso el resultado lleva un `created` que **no viaja** en la respuesta: es para la
   auditoría y para las pruebas.
2. **El acceso contesta lo mismo para una dirección desconocida y para una contraseña mala**, y
   además tarda lo mismo: cuando no hay cuenta se comprueba igualmente contra un resumen de mentira.
   Sin eso, medir el tiempo de la respuesta diría qué direcciones existen aunque el texto no lo
   diga.3. **El freno cuenta los dos casos.** Cinco fallos seguidos con la misma dirección bloquean
   quince
   minutos, exista la cuenta o no: un freno que solo contara las direcciones conocidas sería, otra
   vez, una forma de averiguar cuáles lo son.
4. **Cambiar la contraseña cierra las demás sesiones.** Si no, quien hubiera entrado antes seguiría
   dentro y el cambio no serviría para echarlo.
5. **La baja borra.** Cuenta, sesiones, enlaces y el progreso firmado con su dueño; y deja el evento
   del cierre, que es la única prueba de que se hizo.

**Lo que no hace.** No envía correo: no hay servicio contratado y no se simula. El enlace de
recuperación se deja donde el titular puede leerlo, y esa decisión está escrita en
`PARA-EL-PROPIETARIO.md` con lo que habría que contratar para que deje de hacer falta.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import NoReturn

from opofuente.application.account_models import (
    Account,
    AccountAuditEntry,
    ConsentSummary,
    LoginOutcome,
    RegisterOutcome,
    ResetRequestOutcome,
    SessionCookie,
    SessionUser,
    SessionView,
)
from opofuente.application.ports import AccountStore, Clock, PasswordHasher
from opofuente.config import Settings
from opofuente.domain.accounts import (
    LOGIN_WINDOW,
    RESET_TTL,
    SESSION_COOKIE_NAME,
    AccountEventKind,
    ConsentState,
    ThrottleState,
    hash_token,
    new_token,
    normalize_email,
    owner_id_for_email,
    pseudonym,
    validate_password,
)
from opofuente.domain.errors import (
    AccountsDisabledError,
    InvalidAccountInputError,
    InvalidCredentialsError,
    TooManyAttemptsError,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class MaintenanceReport:
    """Lo que ha limpiado la puesta al día. Se devuelve para poder decirlo, no para guardarlo."""

    expired_sessions: int
    expired_resets: int
    stale_throttles: int


class AccountsService:
    """Alta, acceso, recuperación, cierre de sesión y baja, con su auditoría."""

    def __init__(
        self,
        *,
        store: AccountStore,
        hasher: PasswordHasher,
        clock: Clock,
        settings: Settings,
    ) -> None:
        self._store = store
        self._hasher = hasher
        self._clock = clock
        self._settings = settings
        # El resumen de mentira se calcula **la primera vez que hace falta**, no al construir el
        # servicio: con las cuentas apagadas nadie comprueba ninguna contraseña, y pagar una
        # derivación de memoria en cada arranque por algo que no se va a usar es un peaje tonto.
        self._decoy: str | None = None

    def _decoy_hash(self) -> str:
        """Un resumen de mentira, para gastar el mismo tiempo cuando la dirección no existe."""
        if self._decoy is None:
            self._decoy = self._hasher.hash(new_token())
        return self._decoy

    # ------------------------------------------------------------------ lo que se puede

    @property
    def enabled(self) -> bool:
        return self._settings.accounts_enabled

    @property
    def session_cookie(self) -> SessionCookie:
        return SessionCookie(
            name=SESSION_COOKIE_NAME,
            max_age=self._settings.session_ttl_hours * 3600,
            same_site=self._settings.session_cookie_same_site,
            secure=self._settings.session_cookie_secure,
        )

    # --------------------------------------------------------------------------- alta

    def register(self, *, email: str, password: str) -> RegisterOutcome:
        """Da de alta una cuenta, o no hace nada si la dirección ya la tiene.

        **Lo que devuelve es lo que se sabe, no lo que se contesta.** La respuesta de la API es la
        misma en los dos casos (ver el encabezado del módulo); este resultado existe para que la
        auditoría registre lo que pasó de verdad y para que las pruebas puedan comprobarlo.
        """
        self._require_enabled()
        normalizada = normalize_email(email)
        validate_password(password, email=normalizada)
        ahora = self._clock.now()
        existente = self._store.account_with_secret(normalizada)
        if existente is not None:
            # Se apunta el intento —sin la contraseña— y no se toca la cuenta que ya estaba.
            self._store.write_event(
                kind=AccountEventKind.REGISTERED,
                account_id=existente.account.id,
                occurred_at=ahora,
                detail={"outcome": "already_registered"},
            )
            return RegisterOutcome(created=False, account=None)

        cuenta = self._store.create_account(
            email=email.strip(),
            email_normalized=normalizada,
            password_hash=self._hasher.hash(password),
            password_algo=self._hasher.algorithm,
            owner_id=owner_id_for_email(normalizada),
            now=ahora,
        )
        self._store.write_event(
            kind=AccountEventKind.REGISTERED,
            account_id=cuenta.id,
            occurred_at=ahora,
            detail={"outcome": "created"},
        )
        return RegisterOutcome(created=True, account=cuenta)

    # ------------------------------------------------------------------------- acceso

    def login(self, *, email: str, password: str) -> LoginOutcome:
        """Comprueba la contraseña y abre sesión. Lanza si no vale o si toca esperar."""
        self._require_enabled()
        normalizada = normalize_email(email)
        ahora = self._clock.now()
        clave_freno = pseudonym(normalizada)
        # La puesta al día va antes de contar: si no, las filas de hace un mes seguirían bloqueando.
        self._store.purge_stale_throttles(now=ahora, before=ahora - LOGIN_WINDOW)
        estado = self._store.throttle(clave_freno)
        if estado.is_locked(ahora):
            self._store.write_event(
                kind=AccountEventKind.LOGIN_THROTTLED,
                account_id=clave_freno,
                occurred_at=ahora,
                detail={"retry_after_seconds": estado.seconds_until_unlock(ahora)},
            )
            raise TooManyAttemptsError(retry_after_seconds=estado.seconds_until_unlock(ahora))

        encontrada = self._store.account_with_secret(normalizada)
        if encontrada is None:
            # Se gasta el mismo tiempo que si existiera.
            self._hasher.verify(password, self._decoy_hash())
            self._raise_bad_credentials(clave_freno, estado, ahora, existe=False)
        if not self._hasher.verify(password, encontrada.password_hash):
            self._raise_bad_credentials(clave_freno, estado, ahora, existe=True)

        # Acierto: el freno se borra, no se reinicia. No queda ni el rastro de que se falló.
        self._store.clear_throttle(clave_freno)
        if self._hasher.needs_rehash(encontrada.password_hash):
            # Es el único momento en el que la contraseña está en claro y a mano: se aprovecha.
            self._store.set_password(
                account_id=encontrada.account.id,
                password_hash=self._hasher.hash(password),
                now=ahora,
            )
        testigo = new_token()
        caduca = ahora + self._settings.session_ttl
        self._store.create_session(
            account_id=encontrada.account.id,
            owner_id=encontrada.account.owner_id,
            token_hash=hash_token(testigo),
            now=ahora,
            expires_at=caduca,
        )
        self._store.write_event(
            kind=AccountEventKind.LOGIN,
            account_id=encontrada.account.id,
            occurred_at=ahora,
            detail={"outcome": "ok"},
        )
        return LoginOutcome(account=encontrada.account, session_token=testigo, expires_at=caduca)

    def _raise_bad_credentials(
        self, clave_freno: str, estado: ThrottleState, ahora: datetime, *, existe: bool
    ) -> NoReturn:
        """Cuenta un fallo, lo apunta y corta. Siempre con el mismo error hacia fuera."""
        nuevo = estado.register_failure(ahora)
        self._store.save_throttle(clave_freno, nuevo, now=ahora)
        self._store.write_event(
            kind=AccountEventKind.LOGIN_FAILED,
            account_id=clave_freno,
            occurred_at=ahora,
            detail={
                "outcome": "bad_credentials",
                "account_exists": existe,
                "failures": nuevo.failures,
            },
        )
        raise InvalidCredentialsError

    # ------------------------------------------------------------------------ sesión

    def resolve(self, token: str | None) -> SessionUser | None:
        """Quién está al otro lado, a partir del testigo de la cookie. `None` si no hay nadie.

        Además de resolver, **alarga** la sesión: quien estudia todos los días no tiene que volver a
        entrar, que es lo que se espera de una aplicación de estudio.
        """
        if not token or not self.enabled:
            return None
        ahora = self._clock.now()
        encontrada = self._store.live_session(hash_token(token), now=ahora)
        if encontrada is None:
            return None
        cuenta, sesion_id = encontrada
        self._store.touch_session(
            sesion_id, now=ahora, expires_at=ahora + self._settings.session_ttl
        )
        return SessionUser(account=cuenta, session_id=sesion_id, owner_id=cuenta.owner_id)

    def is_live(self, token: str | None) -> bool:
        """¿Esta cookie es de una sesión viva? **No alarga nada**: es la pregunta de la puerta.

        Existe aparte de `resolve` porque la puerta de las rutas se ejecuta en cada petición y no
        tiene por qué escribir en la base para contestar sí o no.
        """
        if not token or not self.enabled:
            return False
        return self._store.live_session(hash_token(token), now=self._clock.now()) is not None

    def logout(self, token: str | None) -> bool:
        """Cierra la sesión de esta pestaña. Devuelve si había algo que cerrar."""
        self._require_enabled()
        if not token:
            return False
        ahora = self._clock.now()
        encontrada = self._store.live_session(hash_token(token), now=ahora)
        if encontrada is None:
            return False
        cuenta, sesion_id = encontrada
        self._store.revoke_session(sesion_id, now=ahora)
        self._store.write_event(
            kind=AccountEventKind.LOGOUT,
            account_id=cuenta.id,
            occurred_at=ahora,
            detail={"outcome": "closed"},
        )
        return True

    def sessions(self, token: str | None) -> list[SessionView]:
        usuario = self._require_session(token)
        return self._store.sessions_for(
            usuario.account.id, now=self._clock.now(), current_id=usuario.session_id
        )

    def revoke(self, token: str | None, session_id: str) -> bool:
        """Cierra otra sesión de la misma cuenta. Nunca la que se está usando."""
        usuario = self._require_session(token)
        if session_id == usuario.session_id:
            # Cerrar la sesión desde la que se pide dejaría a quien lo pide fuera sin querer.
            return False
        ahora = self._clock.now()
        cerrada = self._store.revoke_session(session_id, now=ahora)
        if cerrada:
            self._store.write_event(
                kind=AccountEventKind.LOGOUT,
                account_id=usuario.account.id,
                occurred_at=ahora,
                detail={"outcome": "closed_other"},
            )
        return cerrada

    def history(self, token: str | None) -> list[AccountAuditEntry]:
        usuario = self._require_session(token)
        return self._store.events_for(usuario.account.id)

    # ------------------------------------------------------------------- recuperación

    def request_reset(self, *, email: str) -> ResetRequestOutcome:
        """Crea un enlace de recuperación. **La respuesta no dice si la cuenta existe.**

        Sin servicio de correo contratado, el enlace se deja en `datos/recovery/` para que lo lea el
        titular: es la única forma de que la recuperación funcione de verdad hoy sin contratar
        nada, y está declarado en la política de privacidad y en `PARA-EL-PROPIETARIO.md`.
        """
        self._require_enabled()
        normalizada = normalize_email(email)
        ahora = self._clock.now()
        self._store.purge_expired_resets(now=ahora)
        encontrada = self._store.account_with_secret(normalizada)
        if encontrada is None:
            self._store.write_event(
                kind=AccountEventKind.RESET_REQUESTED,
                account_id=pseudonym(normalizada),
                occurred_at=ahora,
                detail={"outcome": "unknown_address"},
            )
            return ResetRequestOutcome(token=None, account=None, expires_at=None)

        testigo = new_token()
        caduca = ahora + RESET_TTL
        self._store.create_reset(
            account_id=encontrada.account.id,
            token_hash=hash_token(testigo),
            now=ahora,
            expires_at=caduca,
        )
        self._deliver_reset_link(encontrada.account, testigo)
        self._store.write_event(
            kind=AccountEventKind.RESET_REQUESTED,
            account_id=encontrada.account.id,
            occurred_at=ahora,
            detail={"outcome": "created", "delivery": self.delivery_channel},
        )
        return ResetRequestOutcome(token=testigo, account=encontrada.account, expires_at=caduca)

    def confirm_reset(self, *, token: str, password: str) -> Account:
        """Cambia la contraseña con un enlace de recuperación y cierra las demás sesiones."""
        self._require_enabled()
        ahora = self._clock.now()
        encontrado = self._store.live_reset(hash_token(token), now=ahora)
        if encontrado is None:
            raise InvalidAccountInputError(
                "ese enlace de recuperación ya no vale: pide uno nuevo",
                field="token",
                code="invalid_reset_token",
            )
        cuenta, reset_id = encontrado
        validate_password(password, email=cuenta.email.lower())
        self._store.set_password(
            account_id=cuenta.id, password_hash=self._hasher.hash(password), now=ahora
        )
        self._store.mark_reset_used(reset_id, now=ahora)
        cerradas = self._store.revoke_all_sessions(cuenta.id, now=ahora)
        self._store.write_event(
            kind=AccountEventKind.RESET_COMPLETED,
            account_id=cuenta.id,
            occurred_at=ahora,
            detail={"outcome": "changed", "sessions_closed": cerradas},
        )
        return self._store.account_by_id(cuenta.id) or cuenta

    @property
    def delivery_channel(self) -> str:
        """Por dónde sale el enlace de recuperación. Hoy, por un fichero que lee el titular."""
        return "correo" if self._settings.mail_enabled else "fichero_local"

    @property
    def recovery_directory(self) -> str:
        """Dónde buscar el enlace. Se dice en la respuesta para que no haya que adivinarlo."""
        return str(self._settings.data_paths.recovery)

    def _deliver_reset_link(self, account: Account, token: str) -> None:
        """Deja el enlace donde el titular pueda leerlo mientras no haya correo contratado.

        **No se registra en el log y no viaja en ninguna respuesta**: las dos cosas están prohibidas
        por las reglas del proyecto («secretos nunca en repo, logs, DB, frontend o respuestas»). El
        fichero vive en el árbol de datos, en la misma unidad que la base, y solo lo puede leer
        quien ya puede leer la base.
        """
        carpeta = self._settings.data_paths.recovery
        try:
            carpeta.mkdir(parents=True, exist_ok=True)
        except OSError:
            logger.warning(
                "opofuente.recovery_directory_unavailable",
                extra={"event": "recovery_directory_unavailable"},
            )
            return
        enlace = f"{self._settings.web_base_url}/recuperar?token={token}"
        marca = pseudonym(account.email_normalized)[:12]
        nombre = f"{marca}-{int(self._clock.now().timestamp())}.txt"
        contenido = (
            "Enlace de recuperación de OpoFuente\n"
            "==================================\n\n"
            f"Cuenta: {account.email}\n"
            f"Enlace: {enlace}\n\n"
            "Se puede usar una sola vez y caduca en una hora.\n"
            "No hay ningún servicio de correo contratado, así que este enlace no se manda a\n"
            "ninguna parte: se deja aquí para que lo lea el titular. Cuando se use, o cuando\n"
            "caduque, este fichero se puede borrar.\n"
        )
        try:
            (carpeta / nombre).write_text(contenido, encoding="utf-8")
        except OSError:
            logger.warning(
                "opofuente.recovery_link_not_written",
                extra={"event": "recovery_link_not_written"},
            )

    # ------------------------------------------------------------------------- baja

    def close(self, token: str | None) -> dict[str, int]:
        """Cierra la cuenta: borra lo suyo y deja constancia.

        El evento del cierre se escribe **antes** de borrar y se conserva a propósito
        (`keep_audit_event_id`): es lo único que queda de que la baja se hizo, y sin él «he borrado
        mi cuenta» sería una promesa sin rastro. Lo demás de esa cuenta —incluidos sus otros
        eventos—
        se va con ella.
        """
        usuario = self._require_session(token)
        evento = self._store.write_event(
            kind=AccountEventKind.CLOSED,
            account_id=usuario.account.id,
            occurred_at=self._clock.now(),
            detail={"outcome": "closed"},
        )
        return self._store.close_account(usuario.account.id, keep_audit_event_id=evento)

    # --------------------------------------------------------------------- mantenimiento

    def maintenance(self) -> MaintenanceReport:
        """Tira lo caducado. Es lo que hace verdad el «caduca a los treinta días» del inventario."""
        ahora = self._clock.now()
        return MaintenanceReport(
            expired_sessions=self._store.purge_expired_sessions(now=ahora),
            expired_resets=self._store.purge_expired_resets(now=ahora),
            stale_throttles=self._store.purge_stale_throttles(
                now=ahora, before=ahora - LOGIN_WINDOW
            ),
        )

    def consent_summary(self) -> ConsentSummary:
        return self._store.consent_summary()

    def record_consent(self, state: ConsentState) -> None:
        """Deja constancia de una decisión sobre las cookies, **sin sujeto**.

        Se guarda para poder demostrar que se preguntó y que hubo respuestas. No se guarda quién:
        eso vive en la cookie de su navegador, que es donde tiene que estar.
        """
        self._store.record_consent(
            now=self._clock.now(),
            policy_version=state.policy_version,
            analytics=state.analytics,
            preferences=state.preferences,
        )

    # ------------------------------------------------------------------------ utilidades

    def require_enabled(self) -> None:
        """Corta si esta instalación no tiene cuentas. La ruta lo traduce a 404.

        Es público porque la ruta tiene que poder preguntarlo **antes** de leer nada: con las
        cuentas
        apagadas, `/accounts/me` no es «no has entrado», es «esto no existe», y las dos cosas se
        contestan distinto (404 frente a 401) para que nadie confunda una función apagada con una
        sesión que falta.
        """
        if not self.enabled:
            raise AccountsDisabledError("las cuentas están apagadas en esta instalación")

    def _require_enabled(self) -> None:
        self.require_enabled()

    def _require_session(self, token: str | None) -> SessionUser:
        usuario = self.resolve(token)
        if usuario is None:
            raise InvalidCredentialsError("esta operación necesita una sesión abierta")
        return usuario


__all__ = ["AccountsService", "MaintenanceReport"]
