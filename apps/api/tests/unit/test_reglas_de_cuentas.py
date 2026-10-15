"""Las reglas de las cuentas y del consentimiento, sin base de datos ni framework (§8 y §9).

Estas pruebas son las que se pueden leer para entender **qué** se decidió, porque no montan nada:
son
funciones puras. Las de integración comprueban que la fontanería las respeta; estas, que las reglas
son las que dicen ser.

Lo que se defiende aquí, en una línea cada una:

- un correo se normaliza —minúsculas, sin espacios y **sin acentos sueltos**— porque si no, la misma
  persona se registra dos veces;
- una contraseña de menos de doce caracteres no vale, y la propia dirección tampoco;
- el freno reinicia su ventana, y a los cinco fallos bloquea quince minutos;
- el consentimiento **falla cerrado**: lo que no se entiende o no se ha decidido no enciende nada;
- la analítica solo admite etiquetas de su lista: no hay ninguna forma de contar texto libre.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from opofuente.domain.accounts import (
    CONSENT_POLICY_VERSION,
    LOGIN_LOCK,
    LOGIN_WINDOW,
    MAX_LOGIN_FAILURES,
    ConsentState,
    ThrottleState,
    hash_token,
    is_account_owner,
    normalize_email,
    owner_id_for_email,
    parse_consent,
    pseudonym,
    render_consent,
    token_matches,
    validate_password,
    without_accents,
)
from opofuente.domain.analytics import ACTION, PAGE_VIEW, is_valid_event
from opofuente.domain.errors import InvalidAccountInputError

AHORA = datetime(2026, 10, 15, 12, 0, tzinfo=UTC)


# ------------------------------------------------------------------------------- el correo


def test_el_correo_se_normaliza() -> None:
    assert normalize_email("  Ana@Ejemplo.ES ") == "ana@ejemplo.es"


def test_los_acentos_no_crean_una_cuenta_distinta() -> None:
    """«José@ejemplo.es» y «jose@ejemplo.es» son la misma persona, y tienen que ser la misma cuenta.

    Es el fallo que esta regla evita: con la tilde suelta, `jose'` y `jose` no son lo mismo y la
    misma persona puede registrarse dos veces con lo que parece el mismo correo.
    """
    assert normalize_email("José@Ejemplo.es") == "jose@ejemplo.es"
    assert without_accents("jose\u0301@ejemplo.es") == "jose@ejemplo.es"


@pytest.mark.parametrize("malo", ["", "   ", "no-es-un-correo", "a@b", "@ejemplo.es", "a@.es"])
def test_un_correo_sin_forma_de_correo_no_vale(malo: str) -> None:
    with pytest.raises(InvalidAccountInputError) as error:
        normalize_email(malo)
    assert error.value.field == "email"


# -------------------------------------------------------------------------- la contraseña


def test_la_contrasena_tiene_minimo_y_tope() -> None:
    validate_password("contrasena-larga", email="ana@ejemplo.es")

    with pytest.raises(InvalidAccountInputError):
        validate_password("corta", email="ana@ejemplo.es")
    with pytest.raises(InvalidAccountInputError):
        validate_password("x" * 300, email="ana@ejemplo.es")


def test_la_propia_direccion_no_es_una_contrasena() -> None:
    with pytest.raises(InvalidAccountInputError) as error:
        validate_password("ana@ejemplo.es", email="Ana@Ejemplo.es")
    assert error.value.field == "password"


# --------------------------------------------------------------------------------- el freno


def test_el_freno_cuenta_y_bloquea() -> None:
    estado = ThrottleState()
    for _ in range(MAX_LOGIN_FAILURES - 1):
        estado = estado.register_failure(AHORA)
    assert not estado.is_locked(AHORA), "cuatro fallos no bloquean"

    estado = estado.register_failure(AHORA)
    assert estado.is_locked(AHORA)
    assert estado.seconds_until_unlock(AHORA) == int(LOGIN_LOCK.total_seconds())


def test_el_freno_reinicia_su_ventana() -> None:
    """Cinco fallos repartidos en tres días no bloquean: quien no se acuerda no es un ataque."""
    estado = ThrottleState().register_failure(AHORA)
    estado = estado.register_failure(AHORA + LOGIN_WINDOW + timedelta(minutes=1))
    assert estado.failures == 1


def test_un_acierto_limpia_el_freno() -> None:
    estado = ThrottleState()
    for _ in range(MAX_LOGIN_FAILURES):
        estado = estado.register_failure(AHORA)
    assert estado.register_success().failures == 0
    assert not estado.register_success().is_locked(AHORA)


# --------------------------------------------------------------------------- el testigo


def test_el_testigo_se_guarda_como_resumen_y_se_compara() -> None:
    testigo = "un-testigo-cualquiera"
    resumen = hash_token(testigo)

    assert testigo not in resumen
    assert len(resumen) == 64
    assert token_matches(testigo, resumen)
    assert not token_matches("otro", resumen)


def test_el_dueno_de_una_cuenta_no_lleva_la_direccion() -> None:
    dueno = owner_id_for_email("ana@ejemplo.es")

    assert is_account_owner(dueno)
    assert "ana" not in dueno and "ejemplo" not in dueno
    assert dueno == f"acct:{pseudonym('ana@ejemplo.es')[:32]}"
    assert len(dueno) <= 64, "la columna es String(64)"
    # Y dos cuentas distintas no comparten dueño.
    assert dueno != owner_id_for_email("otra@ejemplo.es")


# ------------------------------------------------------------------- el consentimiento


def test_el_consentimiento_va_y_vuelve() -> None:
    estado = ConsentState(
        policy_version=CONSENT_POLICY_VERSION,
        analytics=True,
        preferences=False,
        decided_at=AHORA,
    )
    valor = render_consent(estado)

    assert valor.startswith(f"v{CONSENT_POLICY_VERSION}.")
    assert parse_consent(valor, now=AHORA) == estado


def test_sin_cookie_no_hay_decision_y_eso_no_es_rechazar() -> None:
    """`None` es «no ha decidido»; un estado con los dos fines en falso es «ha rechazado»."""
    assert parse_consent(None, now=AHORA) is None
    assert parse_consent("", now=AHORA) is None
    rechazo = parse_consent("v1.a0.p0.t0", now=AHORA)
    assert rechazo is not None
    assert rechazo.analytics is False


@pytest.mark.parametrize(
    "basura",
    [
        "v1.a1",
        "a1.p1",
        "v2.a1.p1.t99999999999999999999",
        "lo que sea",
        "v1.a2.p1.t0",
        "V1.A1.P1.T0",
    ],
)
def test_lo_que_no_se_entiende_no_enciende_nada(basura: str) -> None:
    """Falla cerrado: una cookie que no se entiende es una cookie sin permiso."""
    estado = parse_consent(basura, now=AHORA)
    assert estado is None or not estado.grants("analytics")


def test_lo_necesario_nunca_se_apaga_y_lo_desconocido_no_se_concede() -> None:
    estado = ConsentState(policy_version=1, analytics=False, preferences=False, decided_at=AHORA)
    assert estado.grants("necessary") is True
    assert estado.grants("analytics") is False
    assert estado.grants("publicidad") is False, "un fin que no existe no está concedido"


def test_una_decision_caduca_y_hay_que_volver_a_preguntar() -> None:
    vieja = ConsentState(
        policy_version=CONSENT_POLICY_VERSION,
        analytics=True,
        preferences=True,
        decided_at=AHORA - timedelta(days=365),
    )
    assert vieja.has_expired(AHORA)
    assert not vieja.is_current(policy_version=CONSENT_POLICY_VERSION, now=AHORA)


def test_un_texto_nuevo_invalida_la_decision_vieja() -> None:
    estado = ConsentState(policy_version=1, analytics=True, preferences=True, decided_at=AHORA)
    assert not estado.is_current(policy_version=2, now=AHORA)


# --------------------------------------------------------------------------- la analítica


def test_solo_se_cuentan_las_etiquetas_conocidas() -> None:
    assert is_valid_event(PAGE_VIEW, "inicio")
    assert is_valid_event(ACTION, "test_iniciado")

    assert not is_valid_event(PAGE_VIEW, "El tema IV.7 se me da fatal")
    assert not is_valid_event(PAGE_VIEW, "IV.7")
    assert not is_valid_event("click", "inicio")
    assert not is_valid_event(PAGE_VIEW, "inicio "), "los espacios también cambian la etiqueta"
    assert not is_valid_event(PAGE_VIEW, "x" * 60)
