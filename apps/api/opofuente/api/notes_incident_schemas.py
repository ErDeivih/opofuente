"""Contrato de la bandeja del motor (F18, §4.1 del objetivo).

Es la bandeja que faltaba: la que **escribe el motor** cuando comprueba un tema contra las preguntas
de su banco y no puede cerrar lo que encuentra. La del alumno (`notes_report_schemas`) es una
persona
leyendo; esta es una comprobación que dejó constancia, y por eso lo que viaja es distinto: la
categoría (quién lo arregla), el motivo, la **frase verificada** cuando la hay y —lo que permite
actuar— la pregunta que lo provoca, el apartado del que habla y el material del que salió.

Dos textos viajan calculados por el servidor y **no** los escribe la pantalla: `category_help` sale
del vocabulario del dominio (`TEXTO_DE_CATEGORIA`, y `TEXTO_SIN_MATERIA` para la pregunta que no se
pudo situar). Si los escribiera la interfaz habría dos versiones de lo mismo, y la que se queda
vieja
es siempre la que nadie lee.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from opofuente.domain.notes_reports import MAX_REASON_CHARS

#: La categoría con la que una incidencia entra en la bandeja: quién tiene que arreglarla.
IncidentCategoryName = Literal[
    "hueco_sin_material",
    "clave_sospechosa",
    "pregunta_ambigua",
    "norma_cambiada",
    "pregunta_mal_importada",
    "clave_no_fiable",
]

#: Qué pasó exactamente. Es el vocabulario de `domain.topic_notes.Motivo`.
IncidentReasonName = Literal[
    "sin_frase_en_los_apuntes",
    "letra_no_coincide",
    "clave_contradice_la_norma",
    "clave_sin_definir",
    "sin_materia_en_el_indice",
]

#: El desenlace de la comprobación: una duda o un conflicto de letra.
IncidentCoverageName = Literal["doubtful", "conflict"]

#: En qué punto está la incidencia. Es el vocabulario de bandeja que la aplicación ya tenía, más los
#: dos estados que añade la resolución automática (F31): `propuesta_lista` (una regla la resolvió y
#: espera aprobación en bloque) y `no_son_preguntas` (una regla mecánica la sacó de la bandeja).
IncidentStatusName = Literal[
    "open",
    "in_progress",
    "reviewed",
    "dismissed",
    "propuesta_lista",
    "no_son_preguntas",
]

#: Dónde se enseña un conjunto en la bandeja agrupada. Lo **oficial** va aparte y arriba.
TraySectionName = Literal["oficial", "resto"]

#: Las tres acciones en bloque del §2.1 del cierre del objetivo. Vocabulario cerrado: la ruta
#: rechaza cualquier otra cosa antes de tocar la base.
TrayActionName = Literal["aceptar_derivadas", "dejar_fuera", "no_son_preguntas"]


class NotesIncidentSchema(BaseModel):
    """Una incidencia del motor, con lo que hace falta para juzgarla y para ir a mirarla.

    Cuatro bloques, y cada uno existe por algo:

    1. **qué es**: la categoría, el motivo y el texto del dominio que explica por qué el motor la
       señaló (`category_help`), más el detalle que escribió la corrida (`detail`) y la frase
       verificada (`phrase`) cuando la hay;
    2. **dónde**: el tema, el apartado del que habla (`anchor` y `section_title`) y —lo que permite
       juzgarla sin abrir nada— el enunciado de la pregunta (`stem`). `section_title` es nulo cuando
       la pregunta **no se pudo situar en ninguna materia**: eso no es un dato que falte, es el
       hallazgo, y la pantalla lo dice en vez de mandar a un ancla que no está;
    3. **de dónde sale la clave**: el conjunto del que es la pregunta (`set_title`) y el material
    con
       su versión y su estado (`source_*`). Cuando la categoría es «norma cambiada», la
       contradicción
       tiene dos mitades y esta es la segunda;
    4. **cómo acabó**: el estado, la nota de lo que se hizo y cuándo se cerró.
    """

    id: str
    topic_code: str
    topic_title: str
    category: IncidentCategoryName
    category_help: str
    reason: IncidentReasonName
    coverage: IncidentCoverageName
    detail: str
    phrase: str | None = None
    attempts: int
    anchor: str
    section_title: str | None = None
    question_version_id: str
    stem: str
    set_title: str
    source_document_id: str | None = None
    source_document_title: str | None = None
    source_document_type: str | None = None
    source_version_status: str | None = None
    source_version_label: str | None = None
    status: IncidentStatusName
    created_at: datetime
    reviewed_at: datetime | None = None
    resolution_note: str | None = None


class NotesIncidentListSchema(BaseModel):
    """Las incidencias de una página, con **las cuatro cifras** de la bandeja.

    Los recuentos van aparte de la lista aunque se puedan contar de ella, y son de la **bandeja
    entera**, no del filtro: `total` es lo que devuelve el filtro (contado en la base), y
    `totals_by_category` las cuatro categorías con su número real. Es lo que permite que la pantalla
    diga «291 de norma cambiada» sin leerse las 453, y sin heredar la cifra de ningún documento.

    Los cuatro estados salen siempre, con cero incluido: un botón de filtro que desaparece cuando su
    número es cero obliga a la pantalla a inventarse la ausencia.
    """

    pending: int = Field(ge=0, description="Incidencias en `open`, con independencia del filtro.")
    in_progress: int = Field(ge=0, description="Incidencias que el propietario tiene en la mano.")
    reviewed: int = Field(ge=0, description="Incidencias ya resueltas.")
    dismissed: int = Field(ge=0, description="Incidencias descartadas: el motor se equivocaba.")
    total: int = Field(ge=0, description="Incidencias que devuelve el filtro, contadas en la base.")
    totals_by_category: dict[str, int] = Field(default_factory=dict)
    incidents: list[NotesIncidentSchema]


class NotesIncidentUpdateSchema(BaseModel):
    """Lo único que se puede cambiar de una incidencia: en qué punto está y qué se ha hecho.

    No hay ruta para editarla ni para borrarla. La incidencia la escribió una comprobación y lo que
    la resuelve es otra cosa: añadir material, revisar una clave, reescribir una pregunta o
    comprobar la norma. Lo que el propietario decide aquí es **qué ha hecho con ella**, y eso se
    escribe.

    `note` es potestativa, como en el aviso del alumno: hay incidencias que se cierran sin nada que
    escribir. Cuando viene, es **una línea** y sustituye a la que hubiera; cuando no viene, la que
    hubiera se queda.
    """

    model_config = ConfigDict(extra="forbid")

    status: IncidentStatusName
    note: str | None = Field(default=None, max_length=MAX_REASON_CHARS)
    actor: str | None = Field(default=None, min_length=1, max_length=64)

    @field_validator("note")
    @classmethod
    def _una_linea(cls, valor: str | None) -> str | None:
        """La nota viaja en una línea: los saltos se quitan aquí, no en la pantalla."""
        return None if valor is None else " ".join(valor.split())


class TraySetSchema(BaseModel):
    """Una **fila** de la bandeja: un conjunto y lo que espera dentro.

    Es la pieza que hace trabajable una bandeja de cientos de filas. `pendientes` cuenta por
    categoría lo que espera criterio; `propuestas` lo que ya está resuelto por regla y solo falta
    aprobar en bloque. `resumen` es el título de la fila —«50 claves sospechosas»—, calculado por el
    dominio para que la pantalla no tenga que componerlo y no haya dos versiones del mismo texto.

    `acciones` viaja **calculado**: los conjuntos oficiales llegan con la lista vacía, porque su
    clave no se toca y sus incidencias las decide el propietario una a una. La pantalla no tiene que
    saberse la regla; la lee.
    """

    set_id: str
    title: str
    section: TraySectionName
    origin_scope: str
    key_reliability: str
    official: bool
    pendientes: dict[str, int] = Field(default_factory=dict)
    total_pendiente: int = Field(ge=0)
    propuestas: int = Field(ge=0)
    entradas_de_decision: int = Field(ge=0)
    resumen: str
    acciones: list[TrayActionName] = Field(default_factory=list)


class TraySchema(BaseModel):
    """Una **hoja** de la bandeja, en dos secciones, con **la cifra** de la medida de éxito (§2.4).

    `entradas_de_decision` no es el número de incidencias ni el de filas: es lo que de verdad
    depende del criterio del propietario, contado con la regla de `domain.tray` —una por conjunto no
    oficial, una por incidencia oficial—. Va en la respuesta y no se calcula en la pantalla porque
    es la cifra que decide si la bandeja sirve, y una cifra que se calcula en dos sitios acaba
    diciendo dos cosas.

    `rest` son las filas de **la hoja**; `filas`, `total_pendiente`, `propuestas` y
    `entradas_de_decision` son de la bandeja **entera** y no cambian al pasar de hoja: paginar no
    puede mover la cifra del trabajo que queda. La sección de oficiales va entera en todas las
    hojas: son ocho como mucho y sus incidencias no se deciden en bloque.
    """

    official_section: list[TraySetSchema] = Field(default_factory=list)
    rest: list[TraySetSchema] = Field(
        default_factory=list, description="Las filas de la hoja que se está mirando."
    )
    filas: int = Field(ge=0, description="Cuántas filas tiene la bandeja entera.")
    rest_total: int = Field(
        default=0, ge=0, description="Filas de la sección de bancos, sumando todas las hojas."
    )
    total_pendiente: int = Field(ge=0, description="Incidencias que esperan criterio.")
    propuestas: int = Field(
        ge=0, description="Incidencias ya propuestas, que se aprueban en bloque."
    )
    entradas_de_decision: int = Field(
        ge=0, description="La medida de éxito: lo que de verdad depende del propietario."
    )
    page: int = Field(default=1, ge=1, description="La hoja que va en `rest`, empezando por 1.")
    pages: int = Field(default=1, ge=1, description="Cuántas hojas tiene la lista de bancos.")
    page_size: int = Field(default=50, ge=1, description="Cuántas filas caben en una hoja.")


class TrayBulkRequestSchema(BaseModel):
    """Una acción en bloque sobre un conjunto: qué se hace, dónde y quién lo hace.

    La nota es potestativa —una acción en bloque tiene su propio texto por defecto— y, cuando viene,
    es **una línea**, como la del despacho de una en una: es la misma regla y se normaliza igual.
    """

    model_config = ConfigDict(extra="forbid")

    action: TrayActionName
    set_id: str = Field(min_length=1, max_length=36)
    note: str | None = Field(default=None, max_length=MAX_REASON_CHARS)
    actor: str | None = Field(default=None, min_length=1, max_length=64)

    @field_validator("note")
    @classmethod
    def _una_linea(cls, valor: str | None) -> str | None:
        return None if valor is None else " ".join(valor.split())


class TrayBulkResultSchema(BaseModel):
    """Qué hizo la acción en bloque: cuántas incidencias cerró y cuántas claves escribió.

    Los dos números van separados porque no tienen por qué coincidir: aceptar las derivadas escribe
    una clave por propuesta —salvo las que ya estuvieran escritas— y cerrar un conjunto entero no
    escribe ninguna.
    """

    action: TrayActionName
    set_id: str
    incidents: int = Field(ge=0)
    keys_written: int = Field(ge=0)
