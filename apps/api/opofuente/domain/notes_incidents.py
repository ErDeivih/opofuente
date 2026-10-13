"""La bandeja del motor: lo que el sistema no ha podido resolver solo (F18, §4.1 del objetivo).

Esto **no** es la bandeja del alumno. `notes_reports` (migración `0033`) guarda lo que dice una
persona que está leyendo los apuntes: «en este apartado hay un error». Aquí es lo contrario: nadie
la ha mirado todavía. La escribió una **comprobación** —el motor de apuntes, al enfrentar el tema
con las preguntas de su banco— y lo que dejó dentro es lo que no se pudo cerrar solo:

- a quién le toca arreglarlo (`category`, el vocabulario del §2.1.4 del objetivo);
- qué pasó exactamente (`reason`, `detail`, y la `phrase` verificada cuando la hay);
- dónde (el `anchor` del apartado del que habla) y de qué pregunta (su versión del banco).

Y, desde la migración `0035`, **qué se ha decidido**: `status`, la nota de lo que se ha hecho y
cuándo se cerró. Los estados son los cuatro que esta aplicación ya usa para despachar una bandeja
—los mismos de `notes_reports`: `open`, `in_progress`, `reviewed`, `dismissed`— porque el trabajo es
el mismo: alguien mira, decide y lo deja escrito. `dismissed` no es un adorno: el motor **se
equivoca** (una clave que contradice la norma puede estar bien y ser los apuntes los que sobran) y
sin él esa incidencia no se podría cerrar nunca.

Dos reglas viven aquí y no en la ruta, porque son del dominio:

1. **qué cuenta como despachada lo decide el dominio** (`reviewed_at_for`): cerrar deja fecha y
   reabrir la borra, igual que en la bandeja del alumno. Si lo decidiera la pantalla, la bandeja
   podría enseñar «resuelto el 12-oct» con la incidencia pendiente;
2. **la nota es de una línea y se normaliza antes de tocar la base**: es la misma regla que la del
   aviso del alumno, y por eso se reutiliza tal cual en vez de escribir otra parecida.

Y desde el §2 de `AJUSTES-AL-OBJETIVO-CLAVES-Y-RITMO-2026-10.md`, aquí viven también **las reglas de
la reclasificación** (`regla_de_mala_importacion`, `es_falso_positivo`, `categoria_reclasificada`).
Están aquí y no en el comando que las ejecuta porque son del dominio: qué es una pregunta mal
importada, cuándo una incidencia de clave es un falso positivo y en qué categoría acaba cada una son
decisiones que hay que poder probar sin base de datos y sin modelo. El comando solo las aplica.

Por qué hubo que reclasificar: la categoría `norma_cambiada` la ponía el motor a **toda** pregunta
con un hecho dudoso, **antes** de mirar si la letra de los apuntes coincidía con la clave
(`topic_notes_service.py` pasa `clave_dudosa=True` y `domain/topic_notes.py` devuelve el motivo sin
comparar letras). Medido en la copia de la base real el 13 de octubre de 2026: de las 291 que decían
«norma cambiada», **23 no eran ni incidencias** (la letra de los apuntes está en la clave), 146 eran
de conjuntos con la clave en cuarentena y 13 eran preguntas mal importadas.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum

from opofuente.domain.notes_reports import normalise_note
from opofuente.domain.topic_notes import CategoriaIncidencia, Motivo


class IncidentStatus(StrEnum):
    """En qué punto está una incidencia del motor.

    Es el vocabulario de bandeja que la aplicación ya tenía (`notes_reports`, migraciones `0033` y
    `0034`). `open` es lo que espera al propietario; `in_progress` es «lo he visto y estoy en ello»;
    y `reviewed` y `dismissed` son las dos salidas, que significan cosas distintas: **resuelto** es
    «he hecho lo que pedía su categoría» (añadir material, revisar la clave, reescribir la pregunta,
    comprobar la norma) y **descartado** es «el motor se equivoca».

    Se declara aquí, y no se importa del aviso del alumno, porque son dos ciclos de vida distintos
    en dos tablas distintas, cada una con su `CHECK`: si mañana una bandeja necesita un estado más,
    no tiene por qué cambiar la otra.
    """

    OPEN = "open"
    IN_PROGRESS = "in_progress"
    REVIEWED = "reviewed"
    DISMISSED = "dismissed"


class IncidentCoverage(StrEnum):
    """El desenlace que la bandeja enseña: una **duda** o un **conflicto** de letra.

    No es todo `Coverage` (`domain.topic_notes`). Una fila de `notes_incidents` solo puede ser una
    de estas dos —lo dice el `CHECK` de la tabla desde `0031`, y el motor nunca deja aquí una
    pregunta cubierta—, y declarar exactamente los dos valores que caben es lo que permite que el
    contrato publique dos y que la pantalla no tenga que defenderse de los otros.
    """

    DUDOSA = "doubtful"
    CONFLICTO = "conflict"


#: Los estados con los que una incidencia está **cerrada**: nadie tiene que volver a mirarla.
CLOSED_STATUSES: frozenset[IncidentStatus] = frozenset(
    {IncidentStatus.REVIEWED, IncidentStatus.DISMISSED}
)


def reviewed_at_for(status: IncidentStatus, now: datetime) -> datetime | None:
    """Cuándo se despachó una incidencia que pasa a `status`.

    Cerrarla deja la fecha; reabrirla (o ponerla en curso) la **borra**, porque la columna dice
    cuándo se despachó y una incidencia abierta con fecha de revisión es una traza que miente.
    """
    return now if status in CLOSED_STATUSES else None


@dataclass(frozen=True, slots=True)
class NotesIncident:
    """Una incidencia del motor, tal como se guarda y tal como se lee en la bandeja.

    Lo que **no** se guarda y se resuelve al leer: el título del tema, el del apartado, el enunciado
    de la pregunta y el material del que salió. Son cuatro cosas que cambian debajo de la incidencia
    —los apuntes se reescriben, una pregunta se corrige, un documento se sustituye— y guardar una
    copia dentro de la incidencia dejaría dos versiones de lo mismo, una de ellas vieja.

    `section_title` y `anchor` quedan vacíos cuando la pregunta **no se pudo situar en ninguna
    materia**: eso no es un dato que falte, es el hallazgo (la pregunta hay que reescribirla o
    asignarle un tema), y la pantalla lo tiene que decir en vez de mandar a un ancla que no está.
    """

    id: str
    node_id: str
    question_version_id: str
    group_signature: str
    category: CategoriaIncidencia
    reason: Motivo
    #: `doubtful` o `conflict`. Es el desenlace que la bandeja enseña: un conflicto de letra es un
    #: conflicto, no una duda.
    coverage: IncidentCoverage
    detail: str
    attempts: int
    created_at: datetime
    status: IncidentStatus
    reviewed_at: datetime | None = None
    resolution_note: str | None = None
    #: La cita **verificada** de los apuntes, cuando la hay. La tienen los conflictos de letra: es
    #: la frase que sostiene otra opción que la clave. Sin ella la incidencia sigue siendo válida
    #: (hay huecos que no la tienen porque el dato no está escrito en ninguna parte).
    phrase: str | None = None
    section_key: str = ""
    anchor: str = ""
    section_title: str | None = None
    topic_code: str = ""
    topic_title: str = ""
    #: El enunciado de la pregunta que la provoca. Es lo que permite juzgar sin abrir nada más.
    stem: str = ""
    #: De dónde salió la pregunta: el banco o el examen que la trajo.
    set_title: str = ""
    #: El material del que salió la pregunta y **el estado de su versión**. Es la otra mitad de la
    #: contradicción cuando la categoría es «norma cambiada»: la clave viene de aquí y los apuntes
    #: dicen otra cosa. Su estado importa —una versión `superseded` es material que ya se sustituyó—
    #: y por eso viaja con el enlace.
    source_document_id: str | None = None
    source_document_title: str | None = None
    source_document_type: str | None = None
    source_version_status: str | None = None
    source_version_label: str | None = None


@dataclass(frozen=True, slots=True)
class IncidentFilter:
    """Lo que se puede pedir al listar la bandeja: por categoría, por estado, por tema y por texto.

    `q` busca en el enunciado de la pregunta, en el motivo, en la frase verificada y en el título
    del apartado: entre 453 incidencias, esas cuatro cosas son las que permiten encontrar la que se
    tiene en la cabeza sin recorrerlas. Los filtros se combinan, no se excluyen.
    """

    category: CategoriaIncidencia | None = None
    status: IncidentStatus | None = None
    topic_code: str | None = None
    q: str | None = None
    limit: int = field(default=200)


# --------------------------------------------------------------- la reclasificación (§2 de AJUSTES)

#: Las reglas mecánicas de una pregunta mal importada, en el orden en que se comprueban. Son de
#: **forma**, no de contenido: no hace falta el modelo para ver que a una pregunta le faltan
#: opciones
#: o que dos opciones están fundidas en una.
REGLA_MENOS_DE_TRES_OPCIONES = "menos_de_tres_opciones"
REGLA_OPCION_CON_PATRON_DE_OTRA = "opcion_con_patron_de_otra"
REGLA_OPCIONES_DUPLICADAS = "opciones_duplicadas"
REGLA_OPCION_TRUNCADA = "opcion_truncada"

#: Qué se le dice al propietario de cada regla. Es lo que va en el `detail` de la incidencia.
TEXTO_DE_REGLA_MAL_IMPORTADA: dict[str, str] = {
    REGLA_MENOS_DE_TRES_OPCIONES: (
        "la pregunta no tiene al menos tres opciones con texto: no se puede contestar elegando "
        "entre las que hay, y ninguna regla puede inventarse las que faltan"
    ),
    REGLA_OPCION_CON_PATRON_DE_OTRA: (
        "una de las opciones lleva dentro el patrón de otra («b)», «c)»…) porque dos opciones "
        "quedaron fundidas al extraerlas: se puede reparar partiéndola"
    ),
    REGLA_OPCIONES_DUPLICADAS: (
        "dos opciones dicen lo mismo: una de las dos es un resto de la extracción"
    ),
    REGLA_OPCION_TRUNCADA: (
        "una opción es el principio de otra: la extracción cortó el texto a media frase"
    ),
}

#: Dos opciones más cortas que esto no se miran por truncamiento. Un número puede ser prefijo de
#: otro sin que nada esté roto —el puerto 25 lo es de 2525—, y sin esta guarda la regla marcaba
#: preguntas de puertos que están perfectas. Medido en la copia: 5 marcas, 4 de ellas falsas.
LARGO_MINIMO_TRUNCADO = 15

#: El patrón de una opción dentro de otra: `a)`, `b)`, `3 c)`… en mitad del texto.
_PATRON_DE_OPCION = re.compile(r"\b\d?[a-dA-D]\)")

#: La referencia del examen pegada al enunciado («2011 Universidad Internacional de Andalucía…»).
PATRON_REFERENCIA_PEGADA = re.compile(
    r"(19|20)\d{2}\s+"
    r"(Cuerpo|Escala|Administraci|Ayuntamiento|Comunidad|Junta|Ministerio|Test|T\u00e9cnico|"
    r"Universidad|Diputaci|Gobierno|Servicio)",
    re.IGNORECASE,
)

#: El tipo de pregunta que **no** admite el juicio de «menos de tres opciones»: una de verdadero o
#: falso tiene dos a propósito, y una de referencia libre puede no tener ninguna.
TIPOS_CON_DOS_OPCIONES: frozenset[str] = frozenset({"true_false", "free_text_reference"})

#: La regla de discrepancia del §1 del documento de ajustes: por debajo de estas comprobaciones un
#: conjunto no se juzga —con dos preguntas no se puede decir que una clave sea mala— y por encima
#: del
#: umbral pasa a cuarentena.
MINIMO_COMPROBADO = 15
UMBRAL_NO_FIABLE = 0.30
UMBRAL_DUDOSA = 0.15


def fiabilidad_por_discrepancia(discrepancias: int, comprobadas: int) -> str | None:
    """El estado de fiabilidad de un conjunto según su discrepancia notas↔clave (§1).

    `None` es «no se juzga»: menos de `MINIMO_COMPROBADO` preguntas comprobadas no son una muestra.
    Es la regla del §1 escrita aquí **solo como respaldo** para poder ejecutar y medir la
    reclasificación antes de que exista la columna `key_reliability`; cuando exista, manda la
    columna
    y esta función no se usa (lo dice el comando, para que no haya dos verdades).
    """
    if comprobadas < MINIMO_COMPROBADO:
        return None
    tasa = discrepancias / comprobadas
    if tasa > UMBRAL_NO_FIABLE:
        return "no_fiable"
    if tasa >= UMBRAL_DUDOSA:
        return "dudosa"
    return "fiable"


def regla_de_mala_importacion(textos: Sequence[str], tipo: str) -> str | None:
    """La primera regla mecánica que casa con esta pregunta, o `None` si no es una mala importación.

    Es **mecánica a propósito**: nada de modelo, nada de red, y por eso se puede ejecutar entera y
    volver a ejecutarla sin gastar nada. El orden importa y es el del §2: primero lo que hace que la
    pregunta no se pueda contestar (faltan opciones), después lo que sí se puede reparar con una
    regla (dos opciones fundidas, repetidas o cortadas).
    """
    con_texto = [texto for texto in textos if texto.strip()]
    if tipo not in TIPOS_CON_DOS_OPCIONES and len(con_texto) < 3:
        return REGLA_MENOS_DE_TRES_OPCIONES
    # El patrón se busca **a partir del segundo carácter**: una opción puede empezar por «a)» sin
    # que
    # eso signifique nada (es su propio rótulo), y lo que delata la fusión es encontrarlo dentro.
    if any(_PATRON_DE_OPCION.search(texto[1:]) for texto in con_texto):
        return REGLA_OPCION_CON_PATRON_DE_OTRA
    normalizadas = [re.sub(r"\s+", " ", texto.strip().lower()) for texto in con_texto]
    if len(set(normalizadas)) != len(normalizadas):
        return REGLA_OPCIONES_DUPLICADAS
    for una in normalizadas:
        for otra in normalizadas:
            if una != otra and len(una) >= LARGO_MINIMO_TRUNCADO and otra.startswith(una):
                return REGLA_OPCION_TRUNCADA
    return None


def es_falso_positivo(
    *, letra: str | None, esperadas: Sequence[str], resultado: str | None
) -> bool:
    """¿Esta incidencia de clave es un falso positivo del motor?

    El motor marcaba la incidencia por un hecho dudoso **antes** de comparar letras, así que dejaba
    en la bandeja preguntas en las que la letra de los apuntes **está** en la clave: no hay nada que
    mirar. También cuenta la comprobación que ya está marcada como `covered`: el motor la habría
    borrado en la corrida siguiente y la fila es un resto.

    Sin letra no se puede decir nada: no es un falso positivo, es una incidencia sin comprobación.
    """
    if resultado == "covered":
        return True
    if letra is None or not esperadas:
        return False
    return letra.strip().lower() in {cual.strip().lower() for cual in esperadas}


def categoria_reclasificada(
    *,
    actual: CategoriaIncidencia,
    motivo: Motivo,
    regla_mal_importada: str | None,
    conjunto_en_cuarentena: bool,
    falso_positivo: bool,
    tiene_frase: bool,
    norma_citada: bool = False,
) -> CategoriaIncidencia | None:
    """En qué categoría acaba una incidencia al reclasificarla, o `None` si sale de la bandeja.

    El orden es el que manda el §2 de `AJUSTES-AL-OBJETIVO-CLAVES-Y-RITMO-2026-10.md` y no se puede
    cambiar sin cambiar el significado de las cifras:

    1. **`pregunta_mal_importada`**: la pregunta está rota por su forma, y eso se ve antes de mirar
    la
       clave. Se comprueba lo primero porque una pregunta mal importada no puede tener una clave
       sospechosa: no hay pregunta que juzgar;
    2. **`clave_no_fiable`**: la pregunta es de un conjunto con la clave en cuarentena (>30 % de
       discrepancias con los apuntes, §1). Su clave no se usa para nada hasta que se arregle, así
       que
       lo que diga de los apuntes no es una incidencia de los apuntes;
    3. **`clave_sospechosa`**: conjunto fiable cuya clave contradice lo que dicen los apuntes. La
       frase que lo demuestra viaja con la incidencia cuando el motor la verificó
       (`tiene_frase`); sin ella la incidencia sigue siendo la misma —la letra de los apuntes no
       está
       en la clave— y la pantalla lo dice, porque un «sospechosa» sin la cita es una sospecha más
       débil;
    4. **`norma_cambiada`**: **solo** con la cita de la norma vigente y su versión o fecha. Esa
       evidencia no está en los datos de hoy —la escribe una pasada del modelo que este bloque no
       ejecuta—, así que ninguna incidencia se queda aquí: sin la cita, una clave que contradice los
       apuntes es una clave sospechosa, que es lo que se puede afirmar. El parámetro existe para que
       la pasada que sí la tenga no tenga que reescribir esta regla;
    5. **`hueco_sin_material`** y **`pregunta_ambigua`**, como estaban: un hueco es que falte texto
    y
       una pregunta ambigua es que no haya clave con la que juzgarla, y ninguna de las dos se
       arregla
       mirando la clave.

    Un **falso positivo** no llega aquí: sale de la bandeja antes de preguntar nada.
    """
    if falso_positivo:
        return None
    if regla_mal_importada is not None:
        return CategoriaIncidencia.PREGUNTA_MAL_IMPORTADA
    if conjunto_en_cuarentena:
        return CategoriaIncidencia.CLAVE_NO_FIABLE
    if actual in (
        CategoriaIncidencia.HUECO_SIN_MATERIAL,
        CategoriaIncidencia.PREGUNTA_AMBIGUA,
    ) and motivo in (Motivo.SIN_FRASE_EN_LOS_APUNTES, Motivo.SIN_MATERIA_EN_EL_INDICE):
        return actual
    if norma_citada:
        return CategoriaIncidencia.NORMA_CAMBIADA
    if tiene_frase or motivo in (Motivo.LETRA_NO_COINCIDE, Motivo.CLAVE_CONTRADICE_LA_NORMA):
        return CategoriaIncidencia.CLAVE_SOSPECHOSA
    return actual


#: Con lo que empieza el detalle de una incidencia reclasificada. Sirve para dos cosas: que el
#: propietario vea **por qué** cambió de categoría, y poder volver a ejecutar la reclasificación sin
#: apilar una cabecera sobre otra.
MARCA_DE_RECLASIFICACION = "reclasificada:"

#: La línea que dice qué regla mecánica disparó. También es cabecera: se reescribe, no se apila.
PREFIJO_DE_REGLA = "regla mecánica:"

#: Por qué una incidencia sale de la bandeja: no es que cambie de categoría, es que no era una
#: incidencia. Es el texto que queda en su lugar en la auditoría.
MOTIVO_FALSO_POSITIVO = (
    "no era una incidencia: la letra que dan los apuntes está en la clave de la pregunta, así que "
    "no hay nada que decidir"
)


def motivo_reclasificacion(
    destino: CategoriaIncidencia | None, *, regla: str | None = None, tiene_frase: bool = False
) -> str:
    """La frase que explica el cambio de categoría, la que el propietario lee.

    Es una línea por caso y no una plantilla: cada categoría se cambia por un motivo distinto, y el
    propietario necesita saber **cuál** para no tener que deducirlo del detalle del motor.
    """
    if destino is None:
        return MOTIVO_FALSO_POSITIVO
    if destino is CategoriaIncidencia.PREGUNTA_MAL_IMPORTADA:
        return TEXTO_DE_REGLA_MAL_IMPORTADA.get(regla or "", "la pregunta está mal importada")
    if destino is CategoriaIncidencia.CLAVE_NO_FIABLE:
        return (
            "la clave es de un conjunto en cuarentena: no se usa para corregir ni cuenta para la "
            "cobertura, así que lo que digan los apuntes no es una incidencia de los apuntes"
        )
    if destino is CategoriaIncidencia.CLAVE_SOSPECHOSA:
        if tiene_frase:
            return "la clave contradice lo que dicen los apuntes, y está la frase que lo demuestra"
        return (
            "la clave contradice lo que dicen los apuntes (la letra no está en la clave); no "
            "consta la frase que lo demuestra, así que hay que abrir la pregunta"
        )
    if destino is CategoriaIncidencia.NORMA_CAMBIADA:
        return "el modelo cita la norma vigente y la versión o fecha que cambia la respuesta"
    return (
        f"la incidencia se queda en {destino.value}: no la toca ninguna regla de la reclasificación"
    )


def detalle_reclasificado(
    *, motivo: str, detalle: str, fecha: datetime, regla: str | None = None
) -> str:
    """El detalle de una incidencia reclasificada: la cabecera con el porqué y **lo que dijo el
    motor**.

    Lo que escribió la corrida **no se tira**: se queda debajo. La cabecera se sustituye, no se
    acumula, así que ejecutar dos veces la reclasificación deja el mismo texto que ejecutarla una:
    se saltan **todas** las líneas de cabecera que ya hubiera (la marca y la regla), no solo la
    primera.
    """
    lineas = detalle.split("\n")
    inicio = 0
    while inicio < len(lineas) and (
        lineas[inicio].startswith(MARCA_DE_RECLASIFICACION)
        or lineas[inicio].startswith(PREFIJO_DE_REGLA)
    ):
        inicio += 1
    limpio = "\n".join(lineas[inicio:]).strip()
    partes = [f"{MARCA_DE_RECLASIFICACION} {fecha.date().isoformat()} · {motivo}"]
    if regla is not None:
        partes.append(f"{PREFIJO_DE_REGLA} {regla}")
    return "\n".join([*partes, limpio]).strip()


@dataclass(frozen=True, slots=True)
class Reclasificacion:
    """Un cambio de categoría decidido por la reclasificación (§2 de AJUSTES).

    `categoria` es `None` cuando la incidencia **sale de la bandeja**: es lo que pasa con un falso
    positivo, que no es que cambie de categoría, es que no era una incidencia. `phrase` viaja solo
    cuando el motor verificó la frase que demuestra la contradicción y la incidencia no la tenía.
    """

    incident_id: str
    categoria: CategoriaIncidencia | None
    detalle: str
    phrase: str | None = None


__all__ = [
    "CLOSED_STATUSES",
    "LARGO_MINIMO_TRUNCADO",
    "MARCA_DE_RECLASIFICACION",
    "MINIMO_COMPROBADO",
    "MOTIVO_FALSO_POSITIVO",
    "PATRON_REFERENCIA_PEGADA",
    "REGLA_MENOS_DE_TRES_OPCIONES",
    "REGLA_OPCIONES_DUPLICADAS",
    "REGLA_OPCION_CON_PATRON_DE_OTRA",
    "REGLA_OPCION_TRUNCADA",
    "TEXTO_DE_REGLA_MAL_IMPORTADA",
    "TIPOS_CON_DOS_OPCIONES",
    "UMBRAL_DUDOSA",
    "UMBRAL_NO_FIABLE",
    "IncidentCoverage",
    "IncidentFilter",
    "IncidentStatus",
    "NotesIncident",
    "Reclasificacion",
    "categoria_reclasificada",
    "detalle_reclasificado",
    "es_falso_positivo",
    "fiabilidad_por_discrepancia",
    "motivo_reclasificacion",
    "normalise_note",
    "regla_de_mala_importacion",
    "reviewed_at_for",
]
