"""Los textos legales, el consentimiento y los contadores (§9, §10 y §11) por la API real.

**La prueba que da valor a todo el §9** es `test_el_inventario_se_puede_comprobar_contra_la_base`:
el
inventario de datos no se cree, se **cruza** contra el esquema. Cada fila dice de qué tabla y de qué
columna habla, y aquí se comprueba que existen; y cada promesa de lo que **no** se recoge se
comprueba
buscando columnas con esos nombres. Si mañana alguien añade una columna de dirección de red para
depurar algo, esta prueba falla y la política de privacidad deja de poder mentir sin que nadie se
entere.

Las demás comprueban lo que el §9 y el §10 piden literalmente:

- antes de aceptar **no se pone ninguna cookie que no sea necesaria**;
- aceptar y rechazar se contestan **igual** —mismo cuerpo, misma cookie— porque rechazar tiene que
ser
  tan fácil como aceptar;
- la analítica **no cuenta nada sin permiso**, y lo comprueba el servidor, no la pantalla;
- lo que se cuenta **no tiene forma de llevar** un dato personal, porque no hay columna donde
ponerlo;
- los pagos son un hueco: contestan qué habría que contratar y no cobran nada.
"""

from __future__ import annotations

import json
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from opofuente.config import Settings
from opofuente.domain.legal import COOKIES, DATA_INVENTORY, NEGATIVE_CLAIMS
from opofuente.infrastructure.db import build_engine
from opofuente.main import create_app

ORIGEN = {"Origin": "http://127.0.0.1:5173"}

#: La cookie con la que se recuerda la decisión. Es la **única** que la API pone por el §9.
COOKIE_CONSENTIMIENTO = "opofuente_consent"

#: La cookie **no esencial** de la aplicación (el tamaño del texto de lectura). La pone la pantalla,
#: nunca el servidor, y solo con consentimiento: por eso se comprueba que la API no la pone aquí.
COOKIE_NO_ESENCIAL = "opofuente_prefs"


def _settings(base: Settings, **extra: object) -> Settings:
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
def legal(migrated_settings: Settings) -> Iterator[TestClient]:
    """Con el marco legal y la analítica encendidos, y las cuentas apagadas.

    Sin cuentas a propósito: el §9 tiene que funcionar en la instalación de un solo usuario, que es
    justo la que existe hoy. Una analítica que solo se pudiera consentir con cuenta sería una
    analítica que nunca se podría encender aquí.
    """
    with TestClient(
        create_app(_settings(migrated_settings, legal_enabled=True, analytics_enabled=True))
    ) as cliente:
        yield cliente


@pytest.fixture
def apagado(migrated_settings: Settings) -> Iterator[TestClient]:
    with TestClient(create_app(_settings(migrated_settings))) as cliente:
        yield cliente


# ------------------------------------------------------------------------------- §9: los textos


def test_con_la_bandera_apagada_no_se_sirve_ninguna_pagina_legal(apagado: TestClient) -> None:
    """Sin la bandera del §9, esto no existe: 404 y ni una cookie puesta."""
    assert apagado.get("/api/v1/legal/documents").status_code == 404
    assert apagado.get("/api/v1/legal/data-inventory").status_code == 404
    assert apagado.get("/api/v1/legal/cookies").status_code == 404
    assert apagado.post("/api/v1/legal/consent", json={}, headers=ORIGEN).status_code == 404


def test_los_tres_textos_estan_y_lo_dicen(legal: TestClient) -> None:
    """Aviso legal, privacidad y cookies: los tres, con texto y con lo que falta marcado."""
    cuerpo = legal.get("/api/v1/legal/documents").json()

    assert {documento["key"] for documento in cuerpo["documents"]} == {
        "aviso-legal",
        "privacidad",
        "cookies",
    }
    assert cuerpo["text_version"] >= 1
    assert cuerpo["owner_fields_pending"], "el titular tiene que saber qué le falta por rellenar"
    assert "[PENDIENTE:" in cuerpo["documents"][0]["body_markdown"], (
        "la marca de lo que falta tiene que estar en el texto, no solo en la respuesta"
    )
    for documento in cuerpo["documents"]:
        assert len(documento["body_markdown"]) > 500, documento["key"]
        assert documento["title"] and documento["summary"]


def test_un_texto_por_su_nombre_y_404_si_no_existe(legal: TestClient) -> None:
    assert legal.get("/api/v1/legal/documents/privacidad").json()["key"] == "privacidad"
    assert legal.get("/api/v1/legal/documents/no-existe").status_code == 404


def test_el_inventario_se_puede_comprobar_contra_la_base(
    legal: TestClient, migrated_settings: Settings
) -> None:
    """**La prueba que hace verificable el §9.** El inventario, cruzado contra el esquema real.

    Dos direcciones: lo que dice que se guarda tiene que existir, y lo que dice que no se guarda no
    puede existir. Una política de privacidad que no se puede comprobar es publicidad.
    """
    inventario = legal.get("/api/v1/legal/data-inventory").json()
    assert len(inventario["uses"]) == len(DATA_INVENTORY)
    assert len(inventario["not_collected"]) == len(NEGATIVE_CLAIMS)

    engine = build_engine(migrated_settings.data_paths.database)
    try:
        with engine.begin() as conexion:
            tablas = {
                fila[0]
                for fila in conexion.exec_driver_sql(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                )
            }
            # 1) Lo que se declara guardado existe de verdad.
            for uso in DATA_INVENTORY:
                for tabla in uso.tables:
                    assert tabla in tablas, f"el inventario declara {tabla}, que no existe"
                for tabla, columna in uso.columns:
                    if tabla not in tablas:
                        # `accounts` no existe si la migración no la trajo: entonces la fila
                        # declararía algo que no hay, y eso también es un fallo.
                        pytest.fail(f"el inventario declara {tabla}.{columna}, y {tabla} no existe")
                    columnas = {
                        fila[1] for fila in conexion.exec_driver_sql(f"PRAGMA table_info({tabla})")
                    }
                    assert columna in columnas, f"el inventario declara {tabla}.{columna}"

            # 2) Lo que se declara **no** recogido no puede estar en el esquema.
            for promesa in NEGATIVE_CLAIMS:
                for tabla in promesa.tables:
                    if tabla not in tablas:
                        continue
                    columnas = [
                        fila[1] for fila in conexion.exec_driver_sql(f"PRAGMA table_info({tabla})")
                    ]
                    for columna in columnas:
                        for fragmento in promesa.forbidden_column_fragments:
                            assert fragmento not in columna.lower(), (
                                f"«{promesa.claim}» y sin embargo {tabla}.{columna} existe"
                            )
    finally:
        engine.dispose()


def test_las_cookies_declaradas_son_las_que_hay(legal: TestClient) -> None:
    """La tabla de cookies no puede declarar una cookie que nadie pone ni olvidar una que sí."""
    declaradas = {cookie["name"] for cookie in legal.get("/api/v1/legal/cookies").json()["cookies"]}
    assert declaradas == {cookie.name for cookie in COOKIES}
    assert COOKIE_CONSENTIMIENTO in declaradas
    assert COOKIE_NO_ESENCIAL in declaradas


# ------------------------------------------------------------------- §9: el consentimiento


def test_antes_de_aceptar_no_se_pone_ninguna_cookie_no_esencial(legal: TestClient) -> None:
    """**La prueba del §9.** Navegar sin decidir no pone nada no esencial, y la API lo dice.

    Se comprueban las dos mitades: que la API no pone la cookie no esencial en ninguna de las rutas
    del §9, y que sin decisión no hay ninguna cookie de consentimiento que valga (el estado es
    `null`, que es distinto de «ha rechazado»).
    """
    for ruta in (
        "/api/v1/legal/documents",
        "/api/v1/legal/cookies",
        "/api/v1/legal/data-inventory",
    ):
        respuesta = legal.get(ruta)
        galletas = respuesta.headers.get_list("set-cookie")
        assert not galletas, f"{ruta} no puede poner ninguna cookie antes de decidir: {galletas}"

    assert legal.get("/api/v1/legal/consent").json() is None
    assert legal.cookies.get(COOKIE_NO_ESENCIAL) is None


def test_aceptar_y_rechazar_cuestan_lo_mismo(legal: TestClient) -> None:
    """Mismo cuerpo, misma cookie de vuelta: el rechazo no es un camino de segunda.

    Se comprueba la forma —no el contenido— porque es ahí donde se hace la trampa de verdad: en la
    que el botón de aceptar guarda y el de rechazar no.
    """
    aceptar = legal.post(
        "/api/v1/legal/consent", json={"analytics": True, "preferences": True}, headers=ORIGEN
    )
    galleta_aceptar = aceptar.headers["set-cookie"]
    assert aceptar.status_code == 200
    assert aceptar.json()["analytics"] is True
    assert COOKIE_CONSENTIMIENTO in galleta_aceptar
    assert "Max-Age=" in galleta_aceptar
    # No es `HttpOnly`: el servidor tiene que poder leerla y la página también.
    assert "HttpOnly" not in galleta_aceptar

    rechazar = legal.post(
        "/api/v1/legal/consent", json={"analytics": False, "preferences": False}, headers=ORIGEN
    )
    galleta_rechazar = rechazar.headers["set-cookie"]
    assert rechazar.status_code == 200
    assert rechazar.json()["analytics"] is False
    assert COOKIE_CONSENTIMIENTO in galleta_rechazar

    # Las dos respuestas tienen los mismos campos...
    assert set(rechazar.json()) == set(aceptar.json())
    # ...y las dos cookies, la misma forma: solo cambian los dos dígitos de los fines.
    assert _forma(galleta_aceptar) == _forma(galleta_rechazar)


def _forma(galleta: str) -> str:
    """La forma de la cookie sin el valor: sirve para comparar dos decisiones entre sí."""
    primero = galleta.split(";")[0]
    return "=".join(primero.split("=")[:-1])


def test_la_decision_se_recuerda_y_sustituye(legal: TestClient) -> None:
    """Decidir dos veces deja la segunda, y la lectura devuelve lo que se decidió."""
    legal.post(
        "/api/v1/legal/consent", json={"analytics": True, "preferences": False}, headers=ORIGEN
    )
    assert legal.get("/api/v1/legal/consent").json()["analytics"] is True

    legal.post(
        "/api/v1/legal/consent", json={"analytics": False, "preferences": True}, headers=ORIGEN
    )
    estado = legal.get("/api/v1/legal/consent").json()
    assert estado["analytics"] is False
    assert estado["preferences"] is True
    assert estado["necessary"] is True, "lo necesario no se puede apagar"


def test_la_constancia_no_dice_quien_decidio(legal: TestClient) -> None:
    """Se guarda que hubo decisiones, no de quién: el resumen es agregado por construcción."""
    legal.post(
        "/api/v1/legal/consent", json={"analytics": True, "preferences": True}, headers=ORIGEN
    )
    legal.post(
        "/api/v1/legal/consent", json={"analytics": False, "preferences": False}, headers=ORIGEN
    )

    resumen = legal.get("/api/v1/legal/consent/summary").json()
    assert resumen["total"] == 2
    assert resumen["with_analytics"] == 1
    assert resumen["with_preferences"] == 1
    assert set(resumen) == {
        "total",
        "with_analytics",
        "with_preferences",
        "policy_version",
        "since",
    }


def test_decidir_lo_mismo_dos_veces_no_es_dos_decisiones(legal: TestClient) -> None:
    """Repetir la misma respuesta no apila constancias: no es una decisión nueva."""
    for _ in range(3):
        legal.post(
            "/api/v1/legal/consent", json={"analytics": False, "preferences": False}, headers=ORIGEN
        )
    assert legal.get("/api/v1/legal/consent/summary").json()["total"] == 1


# ------------------------------------------------------------------------- §10: la analítica


def test_la_analitica_no_cuenta_nada_sin_permiso(legal: TestClient) -> None:
    """**El §10 comprobado por el servidor**: sin consentimiento, el suceso se rechaza con 403."""
    sin_decidir = legal.post(
        "/api/v1/analytics/events", json={"name": "page_view", "label": "inicio"}, headers=ORIGEN
    )
    assert sin_decidir.status_code == 403
    assert sin_decidir.json()["code"] == "consent_required"

    # Rechazando explícitamente, tampoco.
    legal.post("/api/v1/legal/consent", json={"analytics": False}, headers=ORIGEN)
    rechazado = legal.post(
        "/api/v1/analytics/events", json={"name": "page_view", "label": "inicio"}, headers=ORIGEN
    )
    assert rechazado.status_code == 403

    # Y con permiso, sí.
    legal.post("/api/v1/legal/consent", json={"analytics": True}, headers=ORIGEN)
    contado = legal.post(
        "/api/v1/analytics/events", json={"name": "page_view", "label": "inicio"}, headers=ORIGEN
    )
    assert contado.status_code == 202, contado.text
    assert contado.json()["recorded"] is True


def test_no_se_puede_contar_lo_que_no_esta_en_la_lista(legal: TestClient) -> None:
    """No hay texto libre: una etiqueta que no está en el vocabulario se rechaza.

    Es lo que convierte el esquema en una garantía. Si se pudiera mandar cualquier cadena, alguien
    podría contar el enunciado de una pregunta o el nombre de un tema sin tocar la base.
    """
    legal.post("/api/v1/legal/consent", json={"analytics": True}, headers=ORIGEN)

    libre = legal.post(
        "/api/v1/analytics/events",
        json={"name": "page_view", "label": "El tema IV.7 se me da fatal"},
        headers=ORIGEN,
    )
    assert libre.status_code == 409
    assert "lista" in libre.json()["detail"]

    tipo_raro = legal.post(
        "/api/v1/analytics/events", json={"name": "click", "label": "inicio"}, headers=ORIGEN
    )
    assert tipo_raro.status_code == 409


def test_lo_contado_no_tiene_sujeto(legal: TestClient, migrated_settings: Settings) -> None:
    """La tabla de contadores **no tiene ninguna columna** donde quepa una persona."""
    legal.post("/api/v1/legal/consent", json={"analytics": True}, headers=ORIGEN)
    legal.post(
        "/api/v1/analytics/events", json={"name": "page_view", "label": "temario"}, headers=ORIGEN
    )

    engine = build_engine(migrated_settings.data_paths.database)
    try:
        with engine.begin() as conexion:
            columnas = [
                fila[1] for fila in conexion.exec_driver_sql("PRAGMA table_info(analytics_events)")
            ]
            fila = conexion.exec_driver_sql(
                "SELECT occurred_on, name, label FROM analytics_events"
            ).one()
    finally:
        engine.dispose()

    assert set(columnas) == {"id", "occurred_on", "name", "label", "recorded_at"}
    for prohibida in ("account", "session", "owner", "ip", "user_agent", "email"):
        assert not any(prohibida in columna for columna in columnas), prohibida
    assert fila[1] == "page_view"
    assert fila[2] == "temario"
    # El día, no la hora: la hora exacta, repetida, empieza a parecerse a un identificador.
    assert len(fila[0]) == 10


def test_el_resumen_va_agregado(legal: TestClient) -> None:
    legal.post("/api/v1/legal/consent", json={"analytics": True}, headers=ORIGEN)
    for etiqueta in ("inicio", "inicio", "temario"):
        legal.post(
            "/api/v1/analytics/events",
            json={"name": "page_view", "label": etiqueta},
            headers=ORIGEN,
        )

    resumen = legal.get("/api/v1/analytics/summary").json()
    assert resumen["enabled"] is True
    assert resumen["requires_consent"] is True
    assert resumen["retention_days"] == 365
    contadores = {(fila["name"], fila["label"]): fila["total"] for fila in resumen["counts"]}
    assert contadores[("page_view", "inicio")] == 2
    assert contadores[("page_view", "temario")] == 1
    assert resumen["days"], "el resumen tiene que decir también por día"


def test_con_la_analitica_apagada_no_se_cuenta_nada(apagado: TestClient) -> None:
    """Aunque alguien acepte, sin la bandera no hay analítica: 409 y ni una fila."""
    respuesta = apagado.post(
        "/api/v1/analytics/events", json={"name": "page_view", "label": "inicio"}, headers=ORIGEN
    )
    assert respuesta.status_code == 409
    assert "no tiene analítica" in respuesta.json()["detail"]


# --------------------------------------------------------------------------- §11: los pagos


def test_los_pagos_son_un_hueco_con_la_propuesta_escrita(legal: TestClient) -> None:
    """El §11: la bandera apagada, la propuesta escrita y **nada contratado**."""
    cuerpo = legal.get("/api/v1/payments/plans").json()

    assert cuerpo["enabled"] is False
    assert cuerpo["provider"] == "ninguna (bandera apagada)"
    assert "No hay ninguna pasarela integrada" in cuerpo["notice"]
    assert "no se han podido comprobar" in cuerpo["notice"], (
        "una comisión que no se ha medido se declara sin verificar, no se inventa"
    )

    # La propuesta: qué pasarela, por qué, qué contratar y qué datos saldrían.
    nombres = [pasarela["name"] for pasarela in cuerpo["gateways"]]
    assert nombres[0] == "Stripe", "la recomendada va primera"
    recomendadas = [p for p in cuerpo["gateways"] if p["recommended"]]
    assert len(recomendadas) == 1
    stripe = recomendadas[0]
    assert stripe["why"]
    assert stripe["what_to_contract"], "hay que decir qué se contrata"
    assert stripe["costs"] and all(not linea["verified"] for linea in stripe["costs"])
    assert stripe["price_page"].startswith("https://")
    assert "Dirección de correo." in stripe["personal_data_to_third_party"]
    assert any(
        "medio de pago" in linea.lower() for linea in stripe["personal_data_to_third_party"]
    ), "hay que decir que los datos del medio de pago los recoge la pasarela, no la aplicación"

    assert [plan["key"] for plan in cuerpo["plans"]] == ["free", "account", "paid"]
    assert all(plan["price"] == "sin decidir" or plan["price"] == "0" for plan in cuerpo["plans"])


def test_la_pasarela_esta_declarada_en_la_politica_de_privacidad(legal: TestClient) -> None:
    """Lo que el §11 pide que entre en privacidad, entra: los datos que irían a un tercero."""
    privacidad = legal.get("/api/v1/legal/documents/privacidad").json()["body_markdown"]

    assert "Terceros" in privacidad
    assert "Hoy no hay ninguno" in privacidad
    assert "pasarela de pago" in privacidad
    assert "datos de la tarjeta" in privacidad
    assert "servicio de correo" in privacidad


def test_nada_de_la_plataforma_llama_a_ningun_tercero(legal: TestClient) -> None:
    """Las respuestas del §9, §10 y §11 no llevan ni una dirección de fuera.

    Se comprueba sobre el JSON tal cual se sirve: si algún día alguien enchufara una analítica de
    terceros, su dominio aparecería aquí y esta prueba lo vería antes que el propietario. Y las
    únicas direcciones que se publican son las páginas de precios de la propuesta de pagos, que hay
    que poder comprobar antes de contratar.
    """
    for ruta in (
        "/api/v1/legal/documents",
        "/api/v1/legal/cookies",
        "/api/v1/legal/data-inventory",
        "/api/v1/platform/policy",
    ):
        cuerpo = json.dumps(legal.get(ruta).json(), ensure_ascii=False)
        for ajeno in ("google-analytics", "googletagmanager", "doubleclick", "facebook", "hotjar"):
            assert ajeno not in cuerpo, f"{ruta} nombra a un tercero: {ajeno}"
        assert "http://" not in cuerpo and "https://" not in cuerpo, (
            f"{ruta} no tiene por qué publicar ninguna dirección"
        )

    pagos = json.dumps(legal.get("/api/v1/payments/plans").json(), ensure_ascii=False)
    urls = [trozo for trozo in pagos.split('"') if trozo.startswith("http")]
    assert urls, "la propuesta de pagos tiene que citar de dónde salen sus cifras"
    for url in urls:
        assert url.startswith("https://"), url
        assert any(dominio in url for dominio in ("stripe.com", "paddle.com", "pagos.redsys.es")), (
            url
        )
