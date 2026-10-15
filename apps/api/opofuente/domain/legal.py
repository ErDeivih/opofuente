"""Los textos legales y el inventario de datos (§9 del objetivo vivo), como datos y no como
pantalla.

**Por qué esto vive en el servidor y no en la interfaz.** El §9 pide tres cosas que solo valen si
dicen la verdad: el aviso legal, la política de privacidad, la política de cookies y un apartado
**escrito y verificable** de qué datos se recogen, para qué y cuánto tiempo. Si el texto estuviera
escrito a mano dentro de un componente, la única forma de comprobar que sigue siendo cierto sería
leerlo; aquí el inventario es **una tabla de datos** que se sirve por la API y que se puede cruzar
contra el esquema real de la base (lo hace `apps/api/tests/integration/test_legal_api.py`). Un
inventario que se puede contradecir con el esquema es un inventario; uno que no, es publicidad.

**Lo que este módulo no hace.** No inventa la identidad del titular. Los documentos legales llevan
marcas `[PENDIENTE: …]` donde tiene que ir su nombre, su NIF y su dirección de contacto: son datos
que no se pueden deducir del código, y poner unos de mentira sería peor que dejar la marca a la
vista. La API lo declara (`owner_fields_pending`) para que la pantalla lo enseñe y para que nadie
publique esto creyendo que está acabado.
"""

from __future__ import annotations

from dataclasses import dataclass

#: Cuándo se escribió el texto vigente. Va en la respuesta y en la cookie de consentimiento: un
#: consentimiento vale para **lo que se aceptó**, así que si el texto cambia hay que volver a
#: preguntar.
LEGAL_TEXT_VERSION = 1
LEGAL_TEXT_UPDATED_ON = "2026-10-15"

#: Lo que hay que rellenar antes de publicar esto en internet. No se inventa: se declara.
OWNER_FIELDS_PENDING: tuple[str, ...] = (
    "nombre y apellidos o razón social del titular",
    "NIF del titular",
    "dirección de contacto del titular",
    "dirección de correo de contacto",
)

#: La marca que aparece en el texto donde falta un dato del titular. En mayúsculas y entre corchetes
#: para que no se pueda leer el documento por encima sin verla.
PENDING_MARK = "[PENDIENTE: {field}]"


def _pending(what: str) -> str:
    return PENDING_MARK.format(field=what)


@dataclass(frozen=True, slots=True)
class LegalDocument:
    """Un documento legal: su nombre corto (el de la dirección), su título y su texto."""

    key: str
    title: str
    summary: str
    body_markdown: str


@dataclass(frozen=True, slots=True)
class DataUse:
    """Un uso de datos: qué, para qué, dónde vive y cuánto tiempo, con su base jurídica.

    `tables` es lo que hace verificable la fila: son los nombres de tabla **reales**, y la prueba de
    integración comprueba que existen. `columns` se comprueba igual cuando la fila afirma algo sobre
    una columna concreta (por ejemplo, que la contraseña se guarda en un resumen argon2id).
    """

    what: str
    why: str
    where: str
    retention: str
    lawful_basis: str
    tables: tuple[str, ...] = ()
    columns: tuple[tuple[str, str], ...] = ()
    needs_account: bool = False
    needs_consent: str | None = None


@dataclass(frozen=True, slots=True)
class CookieDeclaration:
    """Una cookie, con lo que hay que poder decir de ella sin mirar el código."""

    name: str
    purpose: str
    essential: bool
    duration: str
    set_by: str
    purpose_key: str


@dataclass(frozen=True, slots=True)
class NegativeClaim:
    """Lo que **no** se recoge. Se declara para poder comprobarlo, no para prometerlo de palabra."""

    claim: str
    #: Patrones de nombre de columna que **no** pueden existir en las tablas citadas.
    forbidden_column_fragments: tuple[str, ...]
    tables: tuple[str, ...]


# ------------------------------------------------------------------------------- el inventario

DATA_INVENTORY: tuple[DataUse, ...] = (
    DataUse(
        what="Tu dirección de correo.",
        why="Identificar tu cuenta y poder recuperar el acceso desde otro sitio.",
        where="La base de datos de la aplicación, en la tabla de cuentas.",
        retention="Mientras la cuenta exista. Se borra al cerrar la cuenta.",
        lawful_basis="Ejecución de un contrato (art. 6.1.b del RGPD): sin ella no hay cuenta.",
        tables=("accounts",),
        columns=(("accounts", "email_normalized"),),
        needs_account=True,
    ),
    DataUse(
        what="Tu contraseña, guardada como resumen irreversible (argon2id).",
        why="Comprobar que eres tú sin poder leer tu contraseña ni devolverla.",
        where="La base de datos, en la tabla de cuentas. Nunca en claro y nunca en una respuesta.",
        retention="Mientras la cuenta exista.",
        lawful_basis="Ejecución de un contrato (art. 6.1.b del RGPD).",
        tables=("accounts",),
        columns=(("accounts", "password_hash"), ("accounts", "password_algo")),
        needs_account=True,
    ),
    DataUse(
        what="Tus sesiones abiertas: un resumen del testigo de sesión y las fechas de uso.",
        why="Mantener la sesión abierta y poder cerrarla desde la propia aplicación.",
        where="La base de datos, en la tabla de sesiones de cuenta; el cookie en tu navegador.",
        retention="Treinta días sin usarla. Se borra al cerrar sesión.",
        lawful_basis="Ejecución de un contrato (art. 6.1.b del RGPD).",
        tables=("account_sessions",),
        needs_account=True,
    ),
    DataUse(
        what="Los enlaces de recuperación: un resumen del testigo y su caducidad.",
        why="Poder cambiar la contraseña cuando no te acuerdas de ella.",
        where="La base de datos, en la tabla de recuperaciones.",
        retention="Una hora desde que se piden; el usado se marca y deja de valer.",
        lawful_basis="Ejecución de un contrato (art. 6.1.b del RGPD).",
        tables=("password_resets",),
        needs_account=True,
    ),
    DataUse(
        what="Un resumen del correo y el número de intentos fallidos seguidos.",
        why="Evitar que se prueben contraseñas a la fuerza contra tu cuenta.",
        where="La base de datos, en la tabla del freno de intentos. No se guarda qué se probó.",
        retention="Quince minutos; se borra en cuanto se acierta la contraseña.",
        lawful_basis="Interés legítimo (art. 6.1.f del RGPD): proteger la cuenta.",
        tables=("login_throttles",),
    ),
    DataUse(
        what="Tu decisión sobre las cookies (aceptado o rechazado, por fin, y cuándo).",
        why="Recordar qué aceptaste y poder demostrar que se te preguntó.",
        where="Tu navegador, en una cookie propia, y una fila sin identificador en la base.",
        retention="Seis meses, y luego se vuelve a preguntar.",
        lawful_basis="Obligación legal (art. 6.1.c del RGPD) y consentimiento (art. 6.1.a).",
        tables=("consent_records",),
    ),
    DataUse(
        what="El tamaño de texto con el que lees los apuntes.",
        why="No volver a elegirlo cada vez que entras.",
        where="Solo tu navegador, en una cookie propia. No llega al servidor.",
        retention="Doce meses o hasta que borres las cookies.",
        lawful_basis="Consentimiento (art. 6.1.a del RGPD).",
        needs_consent="preferences",
    ),
    DataUse(
        what="Contadores de uso: qué pantalla se abre y qué acción se pulsa, contados por día.",
        why="Saber qué pantallas se usan de verdad, para arreglar las que no.",
        where="La base de datos, en la tabla de contadores: sin cuenta, sin sesión y sin ningún "
        "identificador que permita seguir a una persona.",
        retention="Doce meses.",
        lawful_basis="Consentimiento (art. 6.1.a del RGPD).",
        tables=("analytics_events",),
        needs_consent="analytics",
    ),
    DataUse(
        what="Tu progreso de estudio: tests, respuestas y fallos.",
        why="Que veas tu progreso, tus fallos y tus simulacros.",
        where="La base de datos de la aplicación, en las tablas del estudio.",
        retention=(
            "Sin cuenta, vive en este ordenador y no sale de él. Con cuenta, hoy se guarda igual, "
            "sin separarse por cuenta: lo que se borra al cerrar la cuenta son la cuenta, sus "
            "sesiones, sus enlaces y su auditoría. Separar el progreso de cada cuenta está "
            "pendiente y no se promete hasta que esté."
        ),
        lawful_basis="Ejecución de un contrato (art. 6.1.b del RGPD).",
        tables=(
            "study_sessions",
            "session_questions",
            "attempts",
            "learning_errors",
            "review_items",
        ),
        needs_account=True,
    ),
    DataUse(
        what="Los eventos de tu cuenta: alta, acceso, cierre de sesión y baja.",
        why="Poder demostrar que el alta, el acceso y la baja ocurrieron, y cuándo.",
        where=(
            "La base de datos, en la tabla de auditoría. No llevan ni la dirección ni la "
            "contraseña."
        ),
        retention=(
            "El de la baja se conserva —es la prueba de que se hizo—; los demás se borran con la "
            "cuenta."
        ),
        lawful_basis="Interés legítimo (art. 6.1.f del RGPD): seguridad y trazabilidad.",
        tables=("audit_events",),
        needs_account=True,
    ),
)

#: Lo que **no** se recoge. Cada una se comprueba contra el esquema: si algún día alguien añade una
#: columna de dirección IP, la prueba de integración falla y este texto deja de poder mentir.
NEGATIVE_CLAIMS: tuple[NegativeClaim, ...] = (
    NegativeClaim(
        claim="No se guarda tu dirección IP, ni al entrar ni al estudiar.",
        forbidden_column_fragments=("ip", "remote_addr", "client_address"),
        tables=(
            "accounts",
            "account_sessions",
            "password_resets",
            "login_throttles",
            "consent_records",
            "analytics_events",
        ),
    ),
    NegativeClaim(
        claim="No se guarda tu navegador ni tu sistema operativo.",
        forbidden_column_fragments=("user_agent", "browser", "platform", "os_"),
        tables=(
            "accounts",
            "account_sessions",
            "password_resets",
            "login_throttles",
            "consent_records",
            "analytics_events",
        ),
    ),
    NegativeClaim(
        claim="Ninguna contraseña se guarda en claro ni se devuelve por la API.",
        forbidden_column_fragments=("password_plain", "plain_password", "password_text"),
        tables=("accounts",),
    ),
    NegativeClaim(
        claim="No hay ningún identificador de terceros: los contadores no los pone nadie de fuera.",
        forbidden_column_fragments=("third_party", "ga_id", "client_id", "visitor_id", "cookie_id"),
        tables=("analytics_events", "consent_records"),
    ),
)

COOKIES: tuple[CookieDeclaration, ...] = (
    CookieDeclaration(
        name="opofuente_session",
        purpose="Mantener la sesión abierta mientras estudias, cuando las cuentas están activadas.",
        essential=True,
        duration="30 días desde el último uso",
        set_by="Esta aplicación",
        purpose_key="necessary",
    ),
    CookieDeclaration(
        name="opofuente_consent",
        purpose=(
            "Recordar si has aceptado o rechazado, para no volver a preguntarte en cada página."
        ),
        essential=True,
        duration="6 meses",
        set_by="Esta aplicación",
        purpose_key="necessary",
    ),
    CookieDeclaration(
        name="opofuente_prefs",
        purpose="Recordar el tamaño de texto con el que lees los apuntes. Solo se pone si aceptas "
        "las cookies de preferencias.",
        essential=False,
        duration="12 meses",
        set_by="Esta aplicación",
        purpose_key="preferences",
    ),
)


# ---------------------------------------------------------------------------------- los textos

_AVISO_LEGAL = f"""\
## Quién es el titular de este sitio

- Titular: {_pending("nombre y apellidos o razón social")}
- NIF: {_pending("NIF del titular")}
- Dirección de contacto: {_pending("dirección de contacto del titular")}
- Correo de contacto: {_pending("dirección de correo de contacto")}

## Qué es este sitio

Una aplicación de estudio para preparar las pruebas de Técnico Auxiliar de Informática. **No es una
academia oficial y no tiene ninguna relación con el Instituto Nacional de Administración Pública ni
con ningún organismo público.** Las preguntas de convocatorias anteriores proceden de las
publicaciones oficiales de la Administración; el resto del material se ha redactado para esta
aplicación o procede de normativa y documentación técnica de origen público.

## Para qué sirve

Estudiar: leer los temas, practicar con preguntas, hacer simulacros y ver el propio progreso. El uso
es personal.

## Qué no se garantiza

El temario de una convocatoria lo fija la convocatoria. Esta aplicación reproduce el programa de la
última que se ha cargado, con la fecha que aparece en el propio temario. Comprueba siempre la
convocatoria oficial antes de fiarte de un plazo o de un número de preguntas.

## Quién responde de qué

El titular responde del funcionamiento de la aplicación y de sus textos. No responde del uso que se
haga de los datos que se aprenden con ella, ni de las decisiones que se tomen en una prueba oficial.

## Propiedad del contenido

Los textos legales (leyes, reglamentos y sus artículos) no tienen protección de propiedad
intelectual y se citan tal cual. La redacción de los temas, las preguntas propias y las
explicaciones son de esta aplicación. No se ofrece material de academias ni de bancos de preguntas
de pago.

## Enlaces

Los enlaces a sedes oficiales llevan a las páginas de la Administración. Esta aplicación no
responde de lo que publiquen esas páginas.
"""

_PRIVACIDAD = f"""\
## Quién trata tus datos

- Responsable: {_pending("nombre y apellidos o razón social")}
- NIF: {_pending("NIF del titular")}
- Correo para ejercer tus derechos: {_pending("dirección de correo de contacto")}

## Qué datos se recogen, para qué y cuánto tiempo

Está en la tabla «Qué datos se recogen» de esta misma aplicación, con una fila por dato, el motivo,
dónde vive y cuánto se guarda. Esa tabla se genera desde la misma descripción que usa el programa,
así que no puede decir una cosa distinta de la que hace.

En resumen: **sin cuenta**, la aplicación no recoge ningún dato tuyo — estudiar sin cuenta no manda
nada a ningún sitio; el progreso se queda en este ordenador. **Con cuenta**, se recogen la dirección
de correo que escribes, un resumen irreversible de tu contraseña, tus sesiones abiertas, tu
progreso de estudio y los eventos de tu cuenta (alta, acceso y baja).

## Para qué no se usan

- No se usan para publicidad.
- No se venden ni se ceden a nadie.
- No se usan para elaborar perfiles ni para tomar decisiones automatizadas sobre ti.
- No se envían a ningún servicio de fuera mientras no contrates uno: ver «Terceros», más abajo.

## Dónde están

En el ordenador del titular, en la base de datos de la aplicación. La aplicación escucha solo en la
dirección local de este equipo y no publica nada por su cuenta.

## Terceros

**Hoy no hay ninguno.** No hay ningún servicio contratado que reciba tus datos: ni analítica de
terceros, ni correo, ni pasarela de pagos. Si algún día se contrata alguno, esta página dirá cuál y
qué datos recibe **antes** de que empiece a funcionar, y se volverá a pedir tu consentimiento.

Si se contratara una pasarela de pago, lo que viajaría a ese tercero sería: tu dirección de correo,
tu nombre y dirección de facturación, tu número de identificación fiscal si pides factura y los
datos
de tu medio de pago. Los datos de la tarjeta **no pasan por esta aplicación** en ningún caso: los
recoge la pasarela.

Si se contratara un servicio de correo, lo que viajaría sería tu dirección de correo y el contenido
del aviso que se te mande (por ejemplo, el enlace para cambiar la contraseña).

## Tus derechos

Puedes pedir el acceso, la corrección, el borrado, la limitación y la portabilidad de tus datos, y
oponerte a su tratamiento, escribiendo a la dirección de contacto del titular. También puedes
**cerrar la cuenta desde la propia aplicación**, en la pantalla de tu cuenta: cerrar la cuenta borra
la cuenta, sus sesiones y tu progreso, y deja constancia del cierre en la auditoría.

Si crees que no se te ha atendido bien, puedes reclamar ante la Agencia Española de Protección de
Datos.

## Menores

Esta aplicación no está dirigida a menores de catorce años.

## Cambios

Cuando este texto cambie de forma sustancial se volverá a preguntar tu consentimiento. La fecha del
texto vigente aparece al principio de esta página.
"""

_COOKIES = """\
## Qué es una cookie

Un fichero pequeño que el navegador guarda cuando una página se lo pide. Sirve, por ejemplo, para
que no tengas que volver a entrar en cada pantalla.

## Qué se pone en esta aplicación

La tabla «Cookies» de esta página las lista una a una, con su finalidad, cuánto duran y si son
necesarias. Se resume así:

- **Necesarias**: las que hacen que la aplicación funcione. En concreto, la de la sesión —solo si
  las cuentas están activadas— y la que guarda tu decisión sobre esta misma pregunta. Sin la
  segunda, la aplicación no podría recordar que ya te preguntó.
- **Preferencias**: una sola, la del tamaño del texto de lectura. **No se pone hasta que aceptas.**

## Antes de aceptar no se pone ninguna que no sea necesaria

Mientras no tomes una decisión, **no se pone ninguna cookie de preferencias**. Se puede comprobar en
la propia aplicación y en sus pruebas: se navega sin aceptar y se mira qué cookies hay.

## Aceptar y rechazar cuestan lo mismo

Los dos botones están en el mismo sitio, con el mismo tamaño y el mismo número de pulsaciones. Se
puede rechazar sin dar ninguna explicación y sin perder ninguna función de estudio: la aplicación
funciona igual, solo que no recuerda el tamaño de texto que elegiste.

## Cómo cambiar de idea

Vuelve a abrir «Cookies», en el pie de cualquier pantalla, y elige otra vez. La decisión nueva
sustituye a la anterior. También puedes borrar las cookies de este sitio desde tu navegador: al
volver, se te preguntará de nuevo.

## Analítica

Si aceptas la analítica, se cuentan las pantallas que se abren y las acciones que se pulsan **por
día y en total**, sin cuenta, sin sesión y sin ningún identificador que permita seguir a una
persona. No hay ningún servicio de analítica de fuera implicado. Si no aceptas, no se cuenta nada.
"""

LEGAL_DOCUMENTS: tuple[LegalDocument, ...] = (
    LegalDocument(
        key="aviso-legal",
        title="Aviso legal",
        summary="Quién está detrás de esta aplicación, qué es y qué no es.",
        body_markdown=_AVISO_LEGAL,
    ),
    LegalDocument(
        key="privacidad",
        title="Privacidad",
        summary="Qué datos se recogen, para qué, dónde están y cuánto tiempo se guardan.",
        body_markdown=_PRIVACIDAD,
    ),
    LegalDocument(
        key="cookies",
        title="Cookies",
        summary="Qué cookies se ponen, cuáles son necesarias y cómo cambiar de idea.",
        body_markdown=_COOKIES,
    ),
)


def document(key: str) -> LegalDocument | None:
    """Un documento por su nombre corto (el que va en la dirección)."""
    for candidato in LEGAL_DOCUMENTS:
        if candidato.key == key:
            return candidato
    return None


def any_data_use_needs_consent(purpose: str) -> bool:
    """¿Algún uso de datos declarado depende de este consentimiento? Lo usa la analítica."""
    return any(uso.needs_consent == purpose for uso in DATA_INVENTORY)


__all__ = [
    "COOKIES",
    "DATA_INVENTORY",
    "LEGAL_DOCUMENTS",
    "LEGAL_TEXT_UPDATED_ON",
    "LEGAL_TEXT_VERSION",
    "NEGATIVE_CLAIMS",
    "OWNER_FIELDS_PENDING",
    "PENDING_MARK",
    "CookieDeclaration",
    "DataUse",
    "LegalDocument",
    "NegativeClaim",
    "any_data_use_needs_consent",
    "document",
]
