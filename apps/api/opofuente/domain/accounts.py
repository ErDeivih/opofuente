"""Cuentas, sesiones y consentimiento (§8 y §9 del objetivo vivo): las reglas, sin base de datos.

**Qué decide este módulo y qué no.** Aquí están las **reglas** —qué es un correo, qué contraseña se
admite, cuándo se bloquea la insistencia, cómo se codifica el consentimiento y a qué dueño apunta
una cuenta— y **nada más**: no abre la base, no firma cookies, no sabe que existe HTTP. Se escribe
así porque son las reglas que hay que poder probar **sin levantar la aplicación entera**, y porque
eldía que la plataforma se despliegue fuera de este ordenador lo que viaja es esto, no el taller.

**La regla que manda por encima de todo** (encabezado del §B del objetivo): el alumno que ya existe
tiene que seguir estudiando igual. Por eso aquí conviven las dos cosas sin contradecirse:

- el dueño de quien **no** tiene cuenta es `OWNER_ID_LOCAL` (`'local'`), que es el valor con el que
  la aplicación lleva escribiendo desde el primer día (migración 0027);
- el dueño de una cuenta es `acct:<id>`, de modo que dos cuentas no comparten progreso.

Ninguna de las dos rutas es la de antes «adaptada»: la de antes es una de las dos, intacta.
"""

from __future__ import annotations

import hashlib
import re
import secrets
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum

from opofuente.domain.errors import InvalidAccountInputError
from opofuente.domain.study import OWNER_ID_LOCAL

# --------------------------------------------------------------------------- nombres del navegador

#: La cookie de la sesión. `HttpOnly`: el JavaScript de la página no la lee (ni falta que le hace).
SESSION_COOKIE_NAME = "opofuente_session"

#: La cookie con **la decisión sobre las cookies**. No lleva ningún identificador —solo qué se ha
#: aceptado y con qué texto vigente— y por eso se puede leer desde el servidor sin convertirla en un
#: dato personal. Es la que hace que «rechazar» sea de verdad una decisión guardada.
CONSENT_COOKIE_NAME = "opofuente_consent"

#: La cookie **no esencial** de la aplicación: el tamaño del texto con el que se leen los apuntes.
#: Es la que se usa para poder demostrar que antes de aceptar no se pone ninguna, y no se pone nunca
#: sin consentimiento para preferencias.
PREFERENCE_COOKIE_NAME = "opofuente_prefs"

# ----------------------------------------------------------------------------------- la contraseña

#: Doce caracteres: el mínimo que recomienda el NIST para una contraseña sin otras exigencias. No se
#: pide mayúscula, ni número, ni símbolo: exigirlos produce `Verano2026!` y no contraseñas mejores.
MIN_PASSWORD_LENGTH = 12

#: Un tope alto pero real: sin él, una petición con un cuerpo de un megabyte haría trabajar al
#: derivador de claves hasta agotar el proceso (el coste de argon2 crece con la entrada).
MAX_PASSWORD_LENGTH = 256

MAX_EMAIL_LENGTH = 254

#: La forma de un correo, sin ambigüedad: algo, una arroba, un dominio con al menos un punto.
_EMAIL = re.compile(r"^[^@\s]+@[^@\s.]+(?:\.[^@\s.]+)+$")


def normalize_email(raw: str) -> str:
    """La forma canónica de una dirección: sin espacios, minúsculas y sin acentos.

    Se normaliza porque `Ana@Ejemplo.es` y `ana@ejemplo.es` son la misma cuenta para cualquiera que
    las escriba, y tratarlas como dos permite registrarse dos veces con el mismo correo. Los acentos
    se quitan por la misma razón práctica: el teclado de un móvil los añade solo.

    Lanza `InvalidAccountInputError` si lo que llega no es una dirección: es entrada inválida, con
    su campo, y se contesta como tal.
    """
    limpio = without_accents(raw).strip().lower()
    if not limpio:
        raise InvalidAccountInputError("escribe tu dirección de correo", field="email")
    if len(limpio) > MAX_EMAIL_LENGTH:
        raise InvalidAccountInputError("la dirección de correo es demasiado larga", field="email")
    if not _EMAIL.match(limpio):
        raise InvalidAccountInputError(
            "esa dirección de correo no tiene forma de correo", field="email"
        )
    return limpio


def without_accents(raw: str) -> str:
    """Quita los acentos de una cadena.

    Se hace con `unicodedata` de la biblioteca estándar, en **dos pasos** y no en uno: la
    descomposición `NFKD` separa la letra de su tilde, y hay que quitar después la tilde suelta
    (categoría `Mn`). Quedarse en el primer paso deja `jose'@…`, que se parece a `jose@…` y no es
    igual —y esa diferencia es exactamente la que permite registrarse dos veces con el mismo
    correo—.
    """
    return "".join(
        letra for letra in unicodedata.normalize("NFKD", raw) if not unicodedata.combining(letra)
    )


def validate_password(password: str, *, email: str) -> None:
    """Comprueba que la contraseña se puede admitir, y explica por qué no si no.

    Tres reglas, y las tres tienen motivo: la longitud mínima, el tope (para que el derivador no se
    convierta en la forma barata de tumbar el proceso) y que no sea la propia dirección, que es la
    contraseña que más se repite cuando alguien tiene prisa.
    """
    if len(password) < MIN_PASSWORD_LENGTH:
        raise InvalidAccountInputError(
            f"la contraseña necesita al menos {MIN_PASSWORD_LENGTH} caracteres", field="password"
        )
    if len(password) > MAX_PASSWORD_LENGTH:
        raise InvalidAccountInputError(
            f"la contraseña no puede pasar de {MAX_PASSWORD_LENGTH} caracteres", field="password"
        )
    if password.strip() == "":
        raise InvalidAccountInputError("la contraseña no puede ser solo espacios", field="password")
    if password.strip().lower() == email.strip().lower():
        raise InvalidAccountInputError(
            "la contraseña no puede ser tu propia dirección de correo", field="password"
        )


# ------------------------------------------------------------------------------------- los intentos

#: Insistencias toleradas dentro de la ventana antes de bloquear.
MAX_LOGIN_FAILURES = 5
#: La ventana en la que se cuentan: cinco fallos repartidos en un mes no son un ataque.
LOGIN_WINDOW = timedelta(minutes=15)
#: Lo que dura el bloqueo. Corto a propósito: quien se equivoca de verdad no se queda fuera una
#: tarde.
LOGIN_LOCK = timedelta(minutes=15)


@dataclass(frozen=True, slots=True)
class ThrottleState:
    """Cuántas veces se ha fallado con una cuenta y hasta cuándo está bloqueada.

    No guarda la contraseña probada ni desde dónde se probó: solo el número de fallos de la ventana
    en curso y, si toca, el final del bloqueo. Es lo mínimo para poder frenar la insistencia sin
    construir un registro de quién intenta qué.
    """

    failures: int = 0
    window_started_at: datetime | None = None
    locked_until: datetime | None = None

    def is_locked(self, now: datetime) -> bool:
        return self.locked_until is not None and self.locked_until > now

    def seconds_until_unlock(self, now: datetime) -> int:
        if self.locked_until is None:
            return 0
        return max(0, int((self.locked_until - now).total_seconds()))

    def register_failure(self, now: datetime) -> ThrottleState:
        """Un fallo más, y bloqueo si se ha pasado de la cuenta.

        La ventana se reinicia sola cuando ha pasado: si no, cinco fallos sueltos en tres días
        bloquearían a quien simplemente no se acuerda de la contraseña.
        """
        if self.window_started_at is None or now - self.window_started_at > LOGIN_WINDOW:
            return ThrottleState(failures=1, window_started_at=now, locked_until=None)
        fallos = self.failures + 1
        if fallos >= MAX_LOGIN_FAILURES:
            return ThrottleState(
                failures=fallos,
                window_started_at=self.window_started_at,
                locked_until=now + LOGIN_LOCK,
            )
        return ThrottleState(
            failures=fallos, window_started_at=self.window_started_at, locked_until=None
        )

    def register_success(self, *, window_started_at: datetime | None = None) -> ThrottleState:
        """Un acierto limpia la cuenta de fallos: es lo que hace inofensivo equivocarse una vez."""
        return ThrottleState(failures=0, window_started_at=window_started_at, locked_until=None)


# ------------------------------------------------------------------------------------ la sesión

#: Cuánto dura una sesión sin volver a entrar. Treinta días: es una aplicación de estudio, no un
#: banco.
SESSION_TTL = timedelta(hours=720)

#: Cuánto vale un enlace de recuperación. Una hora: lo que se tarda en mirar el correo.
RESET_TTL = timedelta(minutes=60)

#: Entropía de los dos testigos (sesión y recuperación). 32 bytes = 256 bits: no se adivinan.
TOKEN_BYTES = 32


def new_token() -> str:
    """Un testigo nuevo, del generador criptográfico del sistema (nunca `random`)."""
    return secrets.token_urlsafe(TOKEN_BYTES)


def pseudonym(value: str) -> str:
    """El resumen con el que se identifica algo **sin guardarlo**.

    Se usa para el freno de intentos: la fila se identifica por el resumen de la dirección
    normalizada y no por la dirección. Es lo que permite contar las insistencias sin construir un
    registro de
    quién las hizo, que es la mitad del motivo por el que el freno existe.
    """
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def hash_token(token: str) -> str:
    """El testigo **como se guarda**: un resumen, nunca el testigo.

    Se guarda el resumen y no el valor por lo mismo que la contraseña: quien lea la base no puede
    suplantar a nadie con lo que hay dentro. No hace falta un derivador lento aquí —el testigo ya
    tiene 256 bits de entropía y no se puede probar por diccionario— y por eso es un SHA-256 y no
    argon2.
    """
    return pseudonym(token)


def token_matches(token: str, stored_hash: str) -> bool:
    """Compara en tiempo constante: una comparación que corta al primer byte distinto filtra."""
    return secrets.compare_digest(hash_token(token), stored_hash)


# ---------------------------------------------------------------------------------- el dueño

#: Prefijo del dueño de una cuenta. `owner_id` es `String(64)` desde la migración 0027, así que
#: `acct:` más un resumen de 32 caracteres cabe con holgura.
ACCOUNT_OWNER_PREFIX = "acct:"


def owner_id_for_email(email_normalized: str) -> str:
    """A qué `owner_id` apunta el progreso de una cuenta.

    Es la costura que la migración 0027 dejó preparada: `study_sessions`, `session_questions`,
    `attempts`, `learning_errors`, `review_items` y `notes_reports` ya filtran por `owner_id`, así
    que separar el progreso de dos cuentas no exige tocar el modelo del estudio.

    Se calcula desde el **resumen de la dirección** y no desde el identificador de la fila porque el
    dueño tiene que existir **antes** de escribir la cuenta: `owner_id` es `NOT NULL` y la cuenta se
    crea en una sola escritura. La dirección normalizada es única, así que el resumen también lo es:
    dos cuentas no pueden compartir dueño. Y va el resumen y no la dirección para que el progreso no
    lleve la dirección dentro.
    """
    return f"{ACCOUNT_OWNER_PREFIX}{pseudonym(email_normalized)[:32]}"


def is_account_owner(owner_id: str) -> bool:
    """¿Este dueño es una cuenta, o es el de quien estudia sin cuenta?"""
    return owner_id.startswith(ACCOUNT_OWNER_PREFIX)


def anonymous_owner_id() -> str:
    """El dueño de quien estudia sin cuenta: exactamente el de siempre."""
    return OWNER_ID_LOCAL


# ------------------------------------------------------------------------------- el consentimiento

#: El texto vigente del aviso de cookies. Sube cuando cambia **lo que se pide**, no cuando se
# # corrige#: una coma: un consentimiento vale para lo que se aceptó, y si se pide otra cosa hay que
# volver a
#: preguntar (por eso el consentimiento caduca con el texto).
CONSENT_POLICY_VERSION = 1

#: Cuánto vale una decisión antes de volver a preguntar. Seis meses: lo que tarda en cambiar el
#: criterio de quien la tomó, según el propio considerando 32 del RGPD.
CONSENT_VALIDITY = timedelta(days=180)

#: Los fines, con el nombre que usan la interfaz, la cookie y la analítica. El orden importa para la
#: interfaz: lo necesario primero, y lo demás en el orden en el que se presenta.
CONSENT_PURPOSES: tuple[str, ...] = ("necessary", "preferences", "analytics")

#: Los que **no** se pueden desactivar: sin ellos la aplicación no funciona (la sesión) o no se
# # puede#: recordar la propia decisión (esta cookie). Se declaran para que la interfaz no los pinte
# como una
#: casilla que se puede apagar.
ESSENTIAL_PURPOSES: frozenset[str] = frozenset({"necessary"})


@dataclass(frozen=True, slots=True)
class ConsentState:
    """Lo que alguien ha decidido sobre las cookies, y con qué texto lo decidió."""

    policy_version: int
    analytics: bool
    preferences: bool
    decided_at: datetime

    @property
    def necessary(self) -> bool:
        return True

    def grants(self, purpose: str) -> bool:
        """¿Está concedido este fin? Un fin desconocido **no** está concedido (falla cerrado)."""
        if purpose == "necessary":
            return True
        if purpose == "analytics":
            return self.analytics
        if purpose == "preferences":
            return self.preferences
        return False

    @property
    def decided_epoch(self) -> int:
        return int(self.decided_at.timestamp())

    def has_expired(self, now: datetime) -> bool:
        """Una decisión vieja no vale: hay que volver a preguntar."""
        return now - self.decided_at > CONSENT_VALIDITY

    def is_current(self, *, policy_version: int, now: datetime) -> bool:
        return self.policy_version == policy_version and not self.has_expired(now)


def render_consent(state: ConsentState) -> str:
    """El valor de la cookie: `v1.a1.p0.t1730000000`.

    Un formato propio, corto y sin ambigüedad, con el número de texto delante: si el día de mañana
    cambia la forma, una cookie vieja se rechaza en lugar de interpretarse mal.
    """
    return (
        f"v{state.policy_version}"
        f".a{1 if state.analytics else 0}"
        f".p{1 if state.preferences else 0}"
        f".t{state.decided_epoch}"
    )


_CONSENT_VALUE = re.compile(
    r"^v(?P<version>\d+)\.a(?P<analytics>[01])\.p(?P<prefs>[01])\.t(?P<at>\d+)$"
)


def parse_consent(raw: str | None, *, now: datetime) -> ConsentState | None:
    """Lee la cookie de consentimiento. `None` significa **sin decisión**, y sin decisión no se
    enciende nada: es la única forma de que «rechazar» y «no haber elegido» no se confundan."""
    if not raw:
        return None
    encontrado = _CONSENT_VALUE.match(raw.strip())
    if encontrado is None:
        return None
    try:
        decidido = datetime.fromtimestamp(int(encontrado.group("at")), tz=now.tzinfo)
    except (OverflowError, OSError, ValueError):
        return None
    return ConsentState(
        policy_version=int(encontrado.group("version")),
        analytics=encontrado.group("analytics") == "1",
        preferences=encontrado.group("prefs") == "1",
        decided_at=decidido,
    )


# -------------------------------------------------------------------------- los eventos auditados


class AccountEventKind(StrEnum):
    """Lo que se escribe en la auditoría por cada movimiento de una cuenta.

    Un solo vocabulario para las cuatro cosas que el §8 pide poder auditar —alta, acceso, baja y
    recuperación— y para lo que sale mal (un fallo de contraseña o una insistencia bloqueada),
    porque «nadie intentó entrar» y «alguien lo intentó y no pudo» son dos hechos distintos y solo
    uno de
    los dos hay que mirar.
    """

    REGISTERED = "account.registered"
    LOGIN = "account.login"
    LOGIN_FAILED = "account.login_failed"
    LOGIN_THROTTLED = "account.login_throttled"
    LOGOUT = "account.logout"
    RESET_REQUESTED = "account.password_reset_requested"
    RESET_COMPLETED = "account.password_reset_completed"
    CLOSED = "account.closed"


#: El actor con el que se firman los eventos de cuenta en `audit_events` (`actor` es `String(32)`).
ACCOUNT_AUDIT_ACTOR = "cuentas"


__all__ = [
    "ACCOUNT_AUDIT_ACTOR",
    "ACCOUNT_OWNER_PREFIX",
    "CONSENT_COOKIE_NAME",
    "CONSENT_POLICY_VERSION",
    "CONSENT_PURPOSES",
    "CONSENT_VALIDITY",
    "ESSENTIAL_PURPOSES",
    "LOGIN_LOCK",
    "LOGIN_WINDOW",
    "MAX_EMAIL_LENGTH",
    "MAX_LOGIN_FAILURES",
    "MAX_PASSWORD_LENGTH",
    "MIN_PASSWORD_LENGTH",
    "PREFERENCE_COOKIE_NAME",
    "RESET_TTL",
    "SESSION_COOKIE_NAME",
    "SESSION_TTL",
    "TOKEN_BYTES",
    "AccountEventKind",
    "ConsentState",
    "ThrottleState",
    "anonymous_owner_id",
    "hash_token",
    "is_account_owner",
    "new_token",
    "normalize_email",
    "owner_id_for_email",
    "parse_consent",
    "pseudonym",
    "render_consent",
    "token_matches",
    "validate_password",
    "without_accents",
]
