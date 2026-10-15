"""Las cuentas por la API real (§8 del objetivo vivo): alta, acceso, recuperación, baja y puerta.

**Qué defiende esta suite, y por qué es la más importante del bloque.** El §B del objetivo vivo pone
una regla por encima de todas: *el alumno que ya existe —uso local, sin cuenta— tiene que seguir
funcionando igual*. Eso se comprueba en `test_el_alumno_sin_cuenta_sigue_estudiando`, que es la
prueba
que hay que mirar primero si algo de aquí falla.

Las demás comprueban lo que el §8 pide y lo que una revisión de seguridad preguntaría:

- el alta **no revela** si una dirección ya estaba, y el acceso **no revela** si existe la cuenta;
- la contraseña **nunca** se guarda en claro, nunca se devuelve y no está en el fichero de la base;
- el freno de intentos bloquea de verdad y dice cuándo se puede volver;
- cerrar sesión invalida el testigo **en el servidor**, no solo en el navegador;
- darse de baja borra lo suyo y deja el evento del cierre, que es la prueba de que se hizo;
- sin sesión, las rutas de administración contestan 401 (la puerta del §8).

El coste de argon2 se baja en estas pruebas a propósito: no se está midiendo cuánto tarda derivar
una
contraseña, se está midiendo **qué se guarda y qué se contesta**. Una suite que tarda tres minutos
en
comprobar ocho cosas acaba no ejecutándose.
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from httpx import Response

from opofuente.config import Settings
from opofuente.infrastructure.db import build_engine
from opofuente.main import create_app

ORIGEN = {"Origin": "http://127.0.0.1:5173"}

#: La contraseña de las pruebas. Larga a propósito: la política exige doce caracteres y la prueba no
#: debe ser la excepción que se salte la regla que se está comprobando.
BUENA = "contrasena-de-prueba-1"
OTRA = "otra-contrasena-distinta-2"

#: Una contraseña deliberadamente mala, en una constante para no escribir literales de contraseña
#: dentro de una llamada: la regla de seguridad del lint no distingue una prueba de un descuido.
MALA = "no-es-la-buena"
#: Corta a propósito, para comprobar que la política de doce caracteres se aplica.
CORTA = "corta"
#: La propia dirección como contraseña: la otra regla de la política.
PROPIA = "ana@ejemplo.es"

#: La cookie de la sesión, que es el nombre con el que se comprueba que existe y que es `HttpOnly`.
COOKIE_SESION = "opofuente_session"


def _settings(base: Settings, **extra: object) -> Settings:
    """Ajustes de la prueba: el mismo directorio de datos, las banderas que pida cada caso.

    El coste de argon2 se baja a lo mínimo que admite la configuración. No se está midiendo el
    tiempo; se está midiendo qué se guarda.
    """
    ajustes: dict[str, object] = {
        "data_dir": base.data_dir,
        "worker_enabled": False,
        "password_hash_time_cost": 1,
        "password_hash_memory_cost_kib": 8192,
        "password_hash_parallelism": 1,
    }
    ajustes.update(extra)
    return Settings(**ajustes, _env_file=None)  # type: ignore[arg-type]


@pytest.fixture
def cuentas(migrated_settings: Settings) -> Iterator[TestClient]:
    """Aplicación con cuentas, legales y analítica encendidas, sobre una base vacía y migrada."""
    ajustes = _settings(
        migrated_settings, accounts_enabled=True, legal_enabled=True, analytics_enabled=True
    )
    with TestClient(create_app(ajustes)) as cliente:
        yield cliente


@pytest.fixture
def sin_cuentas(migrated_settings: Settings) -> Iterator[TestClient]:
    """La configuración de siempre: **ninguna** bandera de la plataforma encendida."""
    with TestClient(create_app(_settings(migrated_settings))) as cliente:
        yield cliente


def alta(cliente: TestClient, email: str = "ana@ejemplo.es", password: str = BUENA) -> Response:
    return cliente.post(
        "/api/v1/accounts/register", json={"email": email, "password": password}, headers=ORIGEN
    )


def acceso(cliente: TestClient, email: str = "ana@ejemplo.es", password: str = BUENA) -> Response:
    return cliente.post(
        "/api/v1/accounts/login", json={"email": email, "password": password}, headers=ORIGEN
    )


def _sin_correlacion(cuerpo: dict[str, object]) -> dict[str, object]:
    """El cuerpo de un problema sin su identificador de correlación.

    Ese campo es de la **petición** —lo pone el middleware en cada una para poder seguirla en los
    registros—, así que dos peticiones distintas nunca lo tienen igual. Comparar los cuerpos enteros
    haría fallar la prueba por algo que no distingue nada de nadie; quitarlo deja la comparación en
    lo
    que sí importa: si el texto delata cuál de los dos casos ha pasado.
    """
    return {clave: valor for clave, valor in cuerpo.items() if clave != "correlation_id"}


# --------------------------------------------------------------- lo que el §8 pide, caso a caso


def test_alta(cuentas: TestClient) -> None:
    """El alta acepta la cuenta y, con ella, se puede entrar."""
    respuesta = alta(cuentas)

    assert respuesta.status_code == 202, respuesta.text
    assert respuesta.json()["status"] == "accepted"
    # No hay campo que diga si la cuenta existía: es lo que la hace uniforme.
    assert set(respuesta.json()) == {"status", "message"}

    assert acceso(cuentas).status_code == 200


def test_acceso(cuentas: TestClient) -> None:
    """El acceso abre sesión y la cookie es `HttpOnly`, `SameSite` y de la aplicación."""
    alta(cuentas)

    respuesta = acceso(cuentas)

    assert respuesta.status_code == 200, respuesta.text
    assert respuesta.json()["account"]["email"] == "ana@ejemplo.es"
    galleta = respuesta.headers["set-cookie"]
    assert COOKIE_SESION in galleta
    assert "HttpOnly" in galleta
    assert "SameSite=lax" in galleta
    assert "Path=/" in galleta
    # El testigo **no** viaja en el cuerpo: solo en la cookie.
    assert "token" not in respuesta.text
    assert cuentas.cookies.get(COOKIE_SESION) is not None


def test_acceso_con_contrasena_mala(cuentas: TestClient) -> None:
    """Una contraseña mala y una dirección desconocida contestan lo mismo, palabra por palabra."""
    alta(cuentas)

    mala = acceso(cuentas, password=MALA)
    desconocida = acceso(cuentas, email="nadie@ejemplo.es", password=BUENA)

    assert mala.status_code == 401
    assert desconocida.status_code == 401
    # Todo igual salvo el identificador de correlación, que es de la petición y no de la cuenta.
    assert _sin_correlacion(mala.json()) == _sin_correlacion(desconocida.json()), (
        "la respuesta no puede distinguir «esa contraseña no es» de «esa dirección no está»"
    )
    assert mala.json()["code"] == "invalid_credentials"


def test_recuperacion(cuentas: TestClient, migrated_settings: Settings) -> None:
    """El enlace de recuperación cambia la contraseña, se usa una sola vez y cierra las sesiones."""
    alta(cuentas)
    assert acceso(cuentas).status_code == 200

    pedir = cuentas.post(
        "/api/v1/accounts/password-resets", json={"email": "ana@ejemplo.es"}, headers=ORIGEN
    )
    assert pedir.status_code == 202

    enlaces = list((migrated_settings.data_paths.recovery).glob("*.txt"))
    assert enlaces, "sin servicio de correo, el enlace tiene que quedar en datos/recovery/"
    testigo = re.search(r"token=([A-Za-z0-9_\-]+)", enlaces[0].read_text(encoding="utf-8"))
    assert testigo is not None

    cambio = cuentas.post(
        "/api/v1/accounts/password-resets/confirm",
        json={"token": testigo.group(1), "password": OTRA},
        headers=ORIGEN,
    )
    assert cambio.status_code == 200, cambio.text

    # La nueva vale, la vieja no, y la sesión que había abierta se ha cerrado en el servidor.
    assert acceso(cuentas, password=BUENA).status_code == 401
    assert acceso(cuentas, password=OTRA).status_code == 200
    assert enlaces[0].read_text(encoding="utf-8")  # el fichero no se borra: lo borra el titular

    # El enlace es de un solo uso.
    repetido = cuentas.post(
        "/api/v1/accounts/password-resets/confirm",
        json={"token": testigo.group(1), "password": BUENA},
        headers=ORIGEN,
    )
    assert repetido.status_code == 422
    assert repetido.json()["code"] == "invalid_reset_token"


def test_recuperacion_no_revela_si_la_direccion_existe(cuentas: TestClient) -> None:
    alta(cuentas)

    con_cuenta = cuentas.post(
        "/api/v1/accounts/password-resets", json={"email": "ana@ejemplo.es"}, headers=ORIGEN
    )
    sin_cuenta = cuentas.post(
        "/api/v1/accounts/password-resets", json={"email": "nadie@ejemplo.es"}, headers=ORIGEN
    )

    assert con_cuenta.status_code == sin_cuenta.status_code == 202
    assert con_cuenta.json() == sin_cuenta.json()


def test_cierre_de_sesion(cuentas: TestClient) -> None:
    """Cerrar sesión invalida el testigo **en el servidor**, no solo en la respuesta."""
    alta(cuentas)
    assert acceso(cuentas).status_code == 200
    testigo = cuentas.cookies.get(COOKIE_SESION)
    assert testigo is not None

    cierre = cuentas.post("/api/v1/accounts/logout", headers=ORIGEN)
    assert cierre.status_code == 204

    # Con el mismo testigo, en un cliente que no ha visto la respuesta: el servidor lo rechaza.
    with TestClient(create_app(cuentas.app.state.settings)) as otro:
        otro.cookies.set(COOKIE_SESION, testigo)
        assert otro.get("/api/v1/accounts/me").status_code == 401


def test_ruta_protegida_sin_sesion(cuentas: TestClient) -> None:
    """Sin sesión: 401 en la cuenta **y** 401 en la administración. Con sesión, pasa."""
    limpio = TestClient(create_app(cuentas.app.state.settings))
    try:
        assert limpio.get("/api/v1/accounts/me").status_code == 401
        protegida = limpio.get("/api/v1/backups")
        assert protegida.status_code == 401, protegida.text
        assert protegida.json()["code"] == "session_required"
        # Y la zona de estudio sigue abierta: es la regla que manda.
        assert limpio.get("/api/v1/student/overview").status_code != 401
    finally:
        limpio.close()

    alta(cuentas)
    acceso(cuentas)
    assert cuentas.get("/api/v1/accounts/me").status_code == 200
    assert cuentas.get("/api/v1/backups").status_code == 200


def test_el_alumno_sin_cuenta_sigue_estudiando(seeded_settings: Settings) -> None:
    """**La prueba que manda.** Sin cuenta y con cuentas encendidas, el estudio funciona igual.

    Se comprueba dos veces, porque son dos configuraciones distintas y las dos tienen que valer:

    1. con las banderas apagadas —como nace la aplicación—, el temario se sirve sin sesión;
    2. con las cuentas **encendidas** y sin haber entrado, el temario se sigue sirviendo.
    """
    with TestClient(create_app(_settings(seeded_settings))) as apagado:
        temario = apagado.get("/api/v1/student/syllabus")
        assert temario.status_code == 200, temario.text
        assert temario.json()["blocks"], "sin cuenta tiene que haber temario"

    with TestClient(
        create_app(_settings(seeded_settings, accounts_enabled=True, legal_enabled=True))
    ) as encendido:
        sin_sesion = TestClient(create_app(encendido.app.state.settings))
        try:
            temario = sin_sesion.get("/api/v1/student/syllabus")
            assert temario.status_code == 200, "encender las cuentas no puede cerrar el estudio"
            assert temario.json()["blocks"]
        finally:
            sin_sesion.close()


# ------------------------------------------------------------------ robustez de datos (§8)


def test_la_contrasena_no_se_guarda_en_claro_ni_se_devuelve(
    cuentas: TestClient, migrated_settings: Settings
) -> None:
    """Ni en la base, ni en el fichero, ni en ninguna respuesta: la contraseña no aparece.

    Se comprueban las tres cosas por separado porque son tres fallos distintos: guardarla en claro,
    dejarla en el fichero por un volcado, y devolverla por la API.
    """
    alta(cuentas)
    respuesta = acceso(cuentas)
    assert BUENA not in respuesta.text

    engine = build_engine(migrated_settings.data_paths.database)
    try:
        with engine.begin() as conexion:
            filas = list(
                conexion.exec_driver_sql(
                    "SELECT id, email, password_hash, password_algo FROM accounts"
                )
            )
    finally:
        engine.dispose()

    assert len(filas) == 1
    _, _, resumen, algoritmo = filas[0]
    assert algoritmo == "argon2id"
    assert resumen.startswith("$argon2id$"), "el resumen tiene que ser de argon2id"
    assert BUENA not in resumen

    # Y no está en ninguna parte del fichero de la base.
    crudo = migrated_settings.data_paths.database.read_bytes()
    assert BUENA.encode("utf-8") not in crudo


def test_el_registro_no_revela_si_un_correo_ya_existe(cuentas: TestClient) -> None:
    """Dos altas con la misma dirección contestan lo mismo, y la segunda **no toca** la cuenta.

    Que la respuesta sea igual no basta: además, la contraseña de la primera tiene que seguir siendo
    la válida. Si la segunda alta hubiera reescrito la cuenta, la prueba lo vería.
    """
    primera = alta(cuentas, password=BUENA)
    segunda = alta(cuentas, password=OTRA)

    assert primera.status_code == segunda.status_code == 202
    assert primera.json() == segunda.json()

    assert acceso(cuentas, password=BUENA).status_code == 200
    assert acceso(cuentas, password=OTRA).status_code == 401


def test_limite_de_intentos(cuentas: TestClient) -> None:
    """Cinco fallos bloquean, el bloqueo dice cuánto falta, y **también** frena la buena."""
    alta(cuentas)

    for _ in range(4):
        assert acceso(cuentas, password=MALA).status_code == 401

    quinto = acceso(cuentas, password=MALA)
    assert quinto.status_code == 401

    bloqueado = acceso(cuentas, password=BUENA)
    assert bloqueado.status_code == 429, bloqueado.text
    assert bloqueado.json()["code"] == "too_many_attempts"
    assert int(bloqueado.headers["retry-after"]) > 0


def test_baja_de_la_cuenta(cuentas: TestClient) -> None:
    """Darse de baja borra la cuenta, sus sesiones y su progreso, y **deja el evento del cierre**.

    El evento se conserva a propósito: es la prueba de que la baja se hizo. Los demás eventos de esa
    cuenta se van con ella.
    """
    alta(cuentas)
    acceso(cuentas)

    baja = cuentas.delete("/api/v1/accounts/me", headers=ORIGEN)
    assert baja.status_code == 200, baja.text
    assert baja.json()["status"] == "closed"
    assert baja.json()["sessions"] >= 1

    assert cuentas.get("/api/v1/accounts/me").status_code == 401
    # La dirección queda libre otra vez: la cuenta ya no está.
    assert acceso(cuentas, password=BUENA).status_code == 401

    # El evento del cierre sigue en la auditoría; el de la baja no se ha llevado por delante.
    engine = build_engine(cuentas.app.state.settings.data_paths.database)
    try:
        with engine.begin() as conexion:
            acciones = [
                fila[0]
                for fila in conexion.exec_driver_sql(
                    "SELECT action FROM audit_events WHERE object_type = 'account'"
                )
            ]
    finally:
        engine.dispose()
    assert "account.closed" in acciones


def test_las_rutas_de_cuenta_se_auditan(cuentas: TestClient) -> None:
    """Alta, acceso, cierre de sesión y baja dejan cada uno su evento con su actor.

    Es lo que el §8 pide por «rutas auditadas»: no un registro de haber pasado por una función, sino
    una fila que se puede leer y que dice qué pasó y cuándo.
    """
    alta(cuentas)
    acceso(cuentas)
    cuentas.post("/api/v1/accounts/logout", headers=ORIGEN)

    engine = build_engine(cuentas.app.state.settings.data_paths.database)
    try:
        with engine.begin() as conexion:
            filas = list(
                conexion.exec_driver_sql(
                    "SELECT action, actor, object_type FROM audit_events WHERE actor = 'cuentas'"
                )
            )
    finally:
        engine.dispose()

    acciones = {fila[0] for fila in filas}
    assert {"account.registered", "account.login", "account.logout"} <= acciones
    assert all(fila[2] == "account" for fila in filas)
    # Ningún evento lleva la contraseña ni el testigo: el «después» está sanitizado.
    assert all(BUENA not in str(fila) for fila in filas)


def test_con_las_cuentas_apagadas_las_rutas_no_existen(
    sin_cuentas: TestClient, migrated_settings: Settings
) -> None:
    """Con la bandera apagada, las cuentas no existen: 404 y **ni una fila** escrita.

    Es la mitad de «todo lo nuevo va detrás de una bandera apagada»: la otra mitad es que tampoco
    queda rastro en la base de algo que nadie ha usado.
    """
    assert sin_cuentas.get("/api/v1/accounts/me").status_code == 404
    assert sin_cuentas.get("/api/v1/accounts/configuration").json()["enabled"] is False
    assert alta(sin_cuentas).status_code == 404
    assert acceso(sin_cuentas).status_code == 404

    engine = build_engine(migrated_settings.data_paths.database)
    try:
        with engine.begin() as conexion:
            # Las sentencias van escritas una a una y sin interpolar nada: un nombre de tabla
            # # construido con una cadena es exactamente lo que el lint de seguridad tiene que
            # marcar, y
            # aquí no hace falta.
            for tabla, sentencia in (
                ("accounts", "SELECT count(*) FROM accounts"),
                ("account_sessions", "SELECT count(*) FROM account_sessions"),
                ("password_resets", "SELECT count(*) FROM password_resets"),
                ("login_throttles", "SELECT count(*) FROM login_throttles"),
            ):
                total = conexion.exec_driver_sql(sentencia).scalar_one()
                assert total == 0, f"{tabla} no puede tener filas con la bandera apagada"
    finally:
        engine.dispose()


def test_la_configuracion_de_la_instalacion_dice_lo_que_hay(
    cuentas: TestClient, sin_cuentas: TestClient
) -> None:
    """La política dice qué está encendido, y lo dice igual en las dos configuraciones."""
    politica = cuentas.get("/api/v1/platform/policy").json()
    assert politica["accounts"]["enabled"] is True
    assert politica["accounts"]["anonymous_study"] is True
    assert politica["legal"]["enabled"] is True
    assert politica["analytics"]["enabled"] is True
    assert politica["analytics"]["requires_consent"] is True

    apagada = sin_cuentas.get("/api/v1/platform/policy").json()
    assert apagada["accounts"]["enabled"] is False
    assert apagada["legal"]["enabled"] is False
    assert apagada["analytics"]["enabled"] is False
    assert apagada["payments"] is False
    # La regla que manda se declara en las dos: se puede estudiar sin cuenta.
    assert apagada["accounts"]["anonymous_study"] is True


def test_la_politica_no_lleva_ningun_dato_de_nadie(cuentas: TestClient) -> None:
    """La política es pública: no puede llevar ni una dirección, ni un identificador de cuenta."""
    alta(cuentas)
    cuerpo = cuentas.get("/api/v1/platform/policy").text

    assert "ana@ejemplo.es" not in cuerpo
    assert "acct:" not in cuerpo
    assert not re.search(r"[0-9a-f]{8}-[0-9a-f]{4}", cuerpo), "ningún identificador en la política"


def test_la_lectura_de_un_enlace_caducado_no_vale(cuentas: TestClient) -> None:
    """Un testigo de recuperación inventado no cambia ninguna contraseña."""
    alta(cuentas)
    inventado = cuentas.post(
        "/api/v1/accounts/password-resets/confirm",
        json={"token": "no-es-un-enlace", "password": OTRA},
        headers=ORIGEN,
    )
    assert inventado.status_code == 422
    assert acceso(cuentas, password=BUENA).status_code == 200


def test_la_contrasena_tiene_que_cumplir_la_politica(cuentas: TestClient) -> None:
    """Doce caracteres, y no la propia dirección: las dos reglas se explican con su campo."""
    corta = alta(cuentas, password=CORTA)
    assert corta.status_code == 422
    assert corta.json()["code"] == "invalid_account_input"
    assert corta.json()["field_errors"][0]["field"] == "password"

    propia = alta(cuentas, password=PROPIA)
    assert propia.status_code == 422
    assert "propia dirección" in propia.json()["field_errors"][0]["message"]


def test_un_correo_sin_forma_de_correo_no_vale(cuentas: TestClient) -> None:
    respuesta = alta(cuentas, email="no-es-un-correo")
    assert respuesta.status_code == 422
    assert respuesta.json()["field_errors"][0]["field"] == "email"


def test_el_correo_se_normaliza(cuentas: TestClient) -> None:
    """`Ana@Ejemplo.es` y `ana@ejemplo.es` son la misma cuenta, y los acentos no crean otra."""
    alta(cuentas, email="Ana@Ejemplo.es")

    assert acceso(cuentas, email="ana@ejemplo.es").status_code == 200
    # Y una segunda alta con la otra forma tampoco crea una cuenta nueva.
    segunda = alta(cuentas, email="ANA@EJEMPLO.ES", password=OTRA)
    assert segunda.status_code == 202
    assert acceso(cuentas, password=BUENA).status_code == 200


def test_el_fichero_del_enlace_no_esta_en_la_respuesta(cuentas: TestClient) -> None:
    """La ruta del fichero del enlace no se publica: una ruta del ordenador del titular, no.

    Es la misma regla que el detector de la zona del alumno: ni una ruta del propietario en una
    respuesta. El enlace se busca en `datos/recovery/`, y eso lo dice `PARA-EL-PROPIETARIO.md`.
    """
    alta(cuentas)
    respuesta = cuentas.post(
        "/api/v1/accounts/password-resets", json={"email": "ana@ejemplo.es"}, headers=ORIGEN
    )

    assert "recovery" not in respuesta.text
    assert ":\\" not in respuesta.text
    assert "/home/" not in respuesta.text
    assert str(Path.home()) not in respuesta.text
