"""La bandeja del propietario **agrupada por conjunto**, con acciones en bloque (F31).

El problema que resuelve este módulo se midió, no se supuso: la bandeja del motor tiene **868
incidencias abiertas** repartidas en 150 conjuntos, y seiscientas filas de una en una no las revisa
nadie. Lo que hace falta no es una lista más corta, es **la fila correcta**: casi todo lo que hay
dentro de un conjunto es el mismo defecto del conjunto —su clave está mal extraída— y se decide una
vez, no tantas veces como preguntas tenga.

De ahí las tres piezas de vocabulario de este módulo:

1. **la sección** (`TraySection`): lo **oficial** va aparte y arriba, porque una clave oficial la
   decide el propietario y nadie más. Es el mismo criterio que
   `domain.question_file.protege_cambiar_la_clave`, y **no** una segunda lista de conjuntos
   oficiales: dos verdades sobre qué es oficial es como acabas tocando una plantilla publicada;
2. **la acción en bloque** (`TrayAction`): lo que se puede hacer con un conjunto entero de una vez;
3. **la entrada de decisión**: qué cuenta como «una cosa que el propietario tiene que atender», que
   es la cifra de la medida de éxito (§2.4 del cierre del objetivo).

La regla de la cifra, escrita aquí para que se pueda probar sin base de datos:

- una incidencia **propuesta** (`propuesta_lista`) **no** cuenta: el propietario la aprueba en
  bloque, y una aprobación en bloque es una fila, no cuarenta;
- lo **resuelto** por regla (falso positivo que sale, pregunta mal importada que se va a «No son
  preguntas») **no** cuenta: nadie tiene que mirarlo;
- de lo que queda, **un conjunto no oficial cuenta una vez**: sus acciones en bloque lo cierran
  entero, y por eso no se cuentan sus incidencias una a una;
- **una incidencia oficial cuenta una vez cada una**: un examen oficial no se despacha en bloque,
  porque su clave no se toca. Ahí no hay atajo que valga.

Todo lo de este módulo es **puro**: no sabe de SQL, ni de ficheros, ni de modelos.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum

from opofuente.domain.errors import InvalidStateError
from opofuente.domain.notes_incidents import IncidentStatus
from opofuente.domain.plural import forma
from opofuente.domain.question_file import protege_cambiar_la_clave
from opofuente.domain.topic_notes import CategoriaIncidencia


class TrayRefusalError(InvalidStateError):
    """La acción en bloque no se puede aplicar, y el motivo se le enseña al propietario.

    Es un error **de dominio** y no un 400 de la ruta porque quien decide qué es oficial no es el
    contrato HTTP: lo decide `protege_cambiar_la_clave`. Hereda de `InvalidStateError` para que la
    aplicación conteste **409 con el texto** —el mismo camino que ya usa «esa decisión no se puede
    aplicar»— en vez de un 500 que obligaría a la pantalla a inventarse el porqué. El texto es el
    mismo que el propietario leería al intentar cambiar la clave desde la ficha de la pregunta.
    """


class TraySection(StrEnum):
    """Dónde se enseña un conjunto en la bandeja.

    `OFICIAL` **no** es «un conjunto importante»: es un conjunto cuya clave no se puede cambiar
    (`protege_cambiar_la_clave`). Va aparte y arriba porque sus incidencias son las que más pesan y
    las únicas que no admiten un botón de «hazlo todo».
    """

    OFICIAL = "oficial"
    RESTO = "resto"


class TrayAction(StrEnum):
    """Lo que se puede hacer con un conjunto entero, de una vez.

    Son **tres** y no cuatro porque son tres trabajos distintos, los del §2.1 del cierre del
    objetivo:

    - **`ACEPTAR_DERIVADAS`**: la clave derivada —la letra que dicen los apuntes con cita y una
      respuesta independiente del modelo, coincidiendo— pasa a la clave del conjunto y sus
      incidencias quedan resueltas. Es lo que devuelve las preguntas al estudio;
    - **`DEJAR_FUERA`**: el conjunto queda fuera de tests, simulacros y repasos
      (`question_sets.key_reliability = 'no_fiable'`), que es lo que ya existe para eso;
    - **`NO_SON_PREGUNTAS`**: lo que hay en el conjunto no son preguntas contestables: sale del
      temario con su motivo y se queda en la base.
    """

    ACEPTAR_DERIVADAS = "aceptar_derivadas"
    DEJAR_FUERA = "dejar_fuera"
    NO_SON_PREGUNTAS = "no_son_preguntas"


#: Las tres acciones, en el orden en que se ofrecen: primero lo que devuelve preguntas al estudio.
ACCIONES: tuple[TrayAction, ...] = (
    TrayAction.ACEPTAR_DERIVADAS,
    TrayAction.DEJAR_FUERA,
    TrayAction.NO_SON_PREGUNTAS,
)

#: Qué hace cada acción, dicho para poder decidirla sin abrir nada. Es el texto que lee el
#: propietario en la pantalla, y se calcula en el servidor para que no haya dos versiones.
#:
#: El vocabulario es **el suyo**: «banco» y «respuesta correcta», no «conjunto», «bandeja» ni
#: «clave». Esas tres son palabras de dentro y la interfaz las tiene vetadas (la puerta 18 las busca
#: fuera del contenido): decirlas aquí sería colar por el texto del servidor lo que la pantalla no
#: puede decir. Y «banco» y no «examen» porque la fila es un conjunto de preguntas y **casi todos
#: son bancos privados**: los exámenes oficiales van en su propia sección y no llevan estos botones.
TEXTO_DE_ACCION: dict[TrayAction, str] = {
    TrayAction.ACEPTAR_DERIVADAS: (
        "acepta todas las respuestas derivadas de este banco: la letra que coinciden los apuntes "
        "y una respuesta independiente del modelo pasa a ser la respuesta correcta, y sus avisos "
        "quedan resueltos"
    ),
    TrayAction.DEJAR_FUERA: (
        "deja este banco fuera de tests, simulacros y repasos: su respuesta correcta no se usa "
        "para nada hasta que se arregle, y sus avisos quedan resueltos"
    ),
    TrayAction.NO_SON_PREGUNTAS: (
        "lo que hay en este banco no son preguntas contestables: sale del temario con su motivo y "
        "se queda en la base, fuera de tests, simulacros y comprobaciones"
    ),
}

#: Los estados en los que una incidencia **ya no espera** una decisión, sea porque la tomó el
#: propietario o porque la tomó una regla. `propuesta_lista` no está aquí: espera una aprobación, y
#: por eso tampoco cuenta como entrada de decisión.
ESTADOS_ESPERANDO: frozenset[IncidentStatus] = frozenset(
    {IncidentStatus.OPEN, IncidentStatus.IN_PROGRESS}
)


def rechazo_de_accion(
    action: TrayAction, *, set_type: str, tiene_plantilla_enlazada: bool
) -> str | None:
    """Por qué **no** se puede aplicar esta acción en bloque a este conjunto, o `None` si sí.

    El criterio de «oficial» es **uno solo** y no se reescribe aquí: lo dice
    `protege_cambiar_la_clave`, que es lo que lee la ruta de la clave cuando alguien intenta
    cambiarla. Con dos listas de conjuntos oficiales, la que se queda vieja es siempre la que
    protege la clave.

    `ACEPTAR_DERIVADAS` **escribe la clave**, así que se rechaza exactamente por lo que la protege.
    Las otras dos no la escriben, pero un examen oficial tampoco se saca del temario ni se deja
    fuera de los tests en bloque: su incidencia la decide el propietario, una a una. Por eso el
    motivo viaja con la aclaración de por qué tampoco esas.
    """
    protegida = protege_cambiar_la_clave(
        set_type=set_type, tiene_plantilla_enlazada=tiene_plantilla_enlazada
    )
    if action is TrayAction.ACEPTAR_DERIVADAS:
        return protegida
    if protegida is None:
        return None
    return (
        f"{protegida}; y por eso este conjunto no se decide en bloque: sus incidencias las mira el "
        "propietario una a una"
    )


def acciones_permitidas(*, set_type: str, tiene_plantilla_enlazada: bool) -> tuple[TrayAction, ...]:
    """Las acciones que este conjunto admite en bloque. Un conjunto oficial no admite ninguna."""
    return tuple(
        action
        for action in ACCIONES
        if rechazo_de_accion(
            action, set_type=set_type, tiene_plantilla_enlazada=tiene_plantilla_enlazada
        )
        is None
    )


@dataclass(frozen=True, slots=True)
class TraySet:
    """Un conjunto con lo que espera, que es la **fila** de la bandeja.

    `pendientes` cuenta por categoría lo que está en `open` o `in_progress`; `propuestas` cuenta lo
    que ya está en `propuesta_lista` —resuelto por regla, esperando la aprobación en bloque—. Las
    dos cosas van separadas porque significan cosas distintas: una espera criterio y la otra no.
    """

    set_id: str
    title: str
    set_type: str
    origin_scope: str
    key_reliability: str
    tiene_plantilla_enlazada: bool
    pendientes: Mapping[str, int] = field(default_factory=dict)
    propuestas: int = 0

    @property
    def es_oficial(self) -> bool:
        """¿Su clave está protegida? Lo decide el dominio de la clave, no este módulo."""
        return (
            protege_cambiar_la_clave(
                set_type=self.set_type, tiene_plantilla_enlazada=self.tiene_plantilla_enlazada
            )
            is not None
        )

    @property
    def seccion(self) -> TraySection:
        return TraySection.OFICIAL if self.es_oficial else TraySection.RESTO

    @property
    def acciones(self) -> tuple[TrayAction, ...]:
        """Las acciones en bloque que admite, con el mismo criterio que la ruta que las aplica."""
        return acciones_permitidas(
            set_type=self.set_type, tiene_plantilla_enlazada=self.tiene_plantilla_enlazada
        )

    @property
    def total_pendiente(self) -> int:
        """Cuántas incidencias esperan criterio en este conjunto."""
        return sum(self.pendientes.values())

    @property
    def entradas_de_decision(self) -> int:
        """Cuántas cosas hay que atender aquí: **una** si es un conjunto, una por incidencia si es
        oficial."""
        if self.total_pendiente == 0:
            return 0
        return self.total_pendiente if self.es_oficial else 1

    def resumen(self) -> str:
        """«50 claves sospechosas», que es el título de la fila del §2.1 del cierre del objetivo.

        **Con el número en su forma**: «1 clave sospechosa», no «1 claves sospechosas». Lo compone
        el servidor y no la pantalla justo por esto: un plural escrito a mano se rompe en cuanto el
        cuanto el número es uno, y el propietario lo lee en cada fila.
        """
        if self.total_pendiente == 0:
            return "sin nada pendiente"
        partes = [
            f"{cuantas} {_etiqueta(categoria, cuantas)}"
            for categoria, cuantas in sorted(
                self.pendientes.items(), key=lambda par: (-par[1], par[0])
            )
            if cuantas
        ]
        return " · ".join(partes)


def _etiqueta(categoria: str, cuantas: int) -> str:
    """El nombre de la categoría, en singular si hay una y en plural si hay más.

    Una categoría que el vocabulario no conozca sale **tal cual** —es lo que ya hacía— y no se
    inventa un plural: la fila enseña el nombre del dominio antes que una palabra mal formada.

    La elección de la forma la hace `con_numero`, que es el **único** sitio del servidor donde se
    decide un singular o un plural: el resumen de esta fila y las frases de la revisión de apuntes
    tienen que decir «1 pregunta» y «3 preguntas» de la misma manera.
    """
    formas = ETIQUETA_DE_CATEGORIA.get(categoria)
    if formas is None:
        return categoria
    singular, plural = formas
    return forma(cuantas, singular, plural)


#: El nombre de cada categoría en la fila del banco, en **sus dos formas** (singular, plural).
#:
#: Están las dos escritas y no se deriva una de la otra con una regla: en español el plural no es
#: añadir una «s» —«norma» → «normas» sí, pero «pregunta que no se puede juzgar» → «preguntas que no
#: se pueden juzgar»— y una regla a medias escribiría «1 claves» o «2 claves sospechosa».
ETIQUETA_DE_CATEGORIA: dict[str, tuple[str, str]] = {
    CategoriaIncidencia.HUECO_SIN_MATERIAL.value: ("hueco sin material", "huecos sin material"),
    CategoriaIncidencia.CLAVE_SOSPECHOSA.value: ("clave sospechosa", "claves sospechosas"),
    CategoriaIncidencia.PREGUNTA_AMBIGUA.value: (
        "pregunta que no se puede juzgar",
        "preguntas que no se pueden juzgar",
    ),
    CategoriaIncidencia.NORMA_CAMBIADA.value: (
        "norma que hay que comprobar",
        "normas que hay que comprobar",
    ),
    CategoriaIncidencia.PREGUNTA_MAL_IMPORTADA.value: (
        "pregunta mal importada",
        "preguntas mal importadas",
    ),
    CategoriaIncidencia.CLAVE_NO_FIABLE.value: ("clave no fiable", "claves no fiables"),
}


@dataclass(frozen=True, slots=True)
class TrayView:
    """La bandeja entera, en dos secciones, con la cifra que decide si sirve o no.

    `entradas_de_decision` es la medida de éxito del §2.4: lo que de verdad depende del criterio del
    propietario. **No** es el número de incidencias —eso es `total_pendiente`— ni el número de filas
    —eso es `filas`—: es lo que hay que atender, contado con la regla de `TraySet`.
    """

    oficial: tuple[TraySet, ...] = ()
    resto: tuple[TraySet, ...] = ()

    @property
    def filas(self) -> int:
        return len(self.oficial) + len(self.resto)

    @property
    def entradas_de_decision(self) -> int:
        return sum(fila.entradas_de_decision for fila in self.oficial) + sum(
            fila.entradas_de_decision for fila in self.resto
        )

    @property
    def total_pendiente(self) -> int:
        return sum(fila.total_pendiente for fila in (*self.oficial, *self.resto))

    @property
    def propuestas(self) -> int:
        return sum(fila.propuestas for fila in (*self.oficial, *self.resto))


def agrupar(filas: Sequence[TraySet]) -> TrayView:
    """Parte las filas en las dos secciones y las ordena: lo oficial arriba, lo demás por volumen.

    Dentro de cada sección manda cuánto espera (de más a menos): la bandeja se trabaja de arriba
    abajo, y un conjunto con 69 incidencias antes que uno con 1 es lo que hace que la primera hora
    sirva para algo. El desempate es el título, para que dos corridas seguidas enseñen el mismo
    orden.
    """
    orden = sorted(filas, key=lambda fila: (-fila.total_pendiente, fila.title, fila.set_id))
    return TrayView(
        oficial=tuple(fila for fila in orden if fila.seccion is TraySection.OFICIAL),
        resto=tuple(fila for fila in orden if fila.seccion is TraySection.RESTO),
    )


#: Cuántas filas viajan por hoja de la bandeja. Cincuenta es lo que se despacha en una sesión de
#: trabajo sin que la pantalla tenga que pintar ciento cincuenta y siete tarjetas con sus acciones.
FILAS_POR_PAGINA = 50


@dataclass(frozen=True, slots=True)
class TrayPage:
    """Una **hoja** de la bandeja: las filas de esa hoja y los totales de la bandeja entera.

    Los totales (`filas`, `total_pendiente`, `propuestas`, `entradas_de_decision`) son de la
    bandeja completa y **no cambian al pasar de hoja**: paginar no puede cambiar la cifra que mide
    el trabajo que queda. Lo que cambia es qué filas se enseñan.

    La sección de oficiales **no se pagina**: son ocho como mucho y su clave no se decide en bloque,
    así que partirlas por hojas solo estorbaría.
    """

    pagina: Sequence[TraySet]
    oficial: tuple[TraySet, ...]
    resto_total: int
    filas: int
    total_pendiente: int
    propuestas: int
    entradas_de_decision: int
    page: int = 1
    page_size: int = FILAS_POR_PAGINA

    @property
    def pages(self) -> int:
        """Cuántas hojas tiene la lista de bancos. Siempre al menos una, aunque esté vacía."""
        return max(1, -(-self.resto_total // self.page_size))


def paginar(vista: TrayView, *, page: int = 1, page_size: int = FILAS_POR_PAGINA) -> TrayPage:
    """Corta la bandeja en hojas y deja los totales de la bandeja entera intactos.

    Se pagina **solo la sección de bancos**: la de exámenes oficiales va entera y arriba, porque sus
    incidencias no se despachan en bloque y verlas todas es barato. Una hoja fuera de rango se
    corrige a la última en vez de devolver un error: el enlace de una bandeja se guarda y, si entre
    dos visitas se despachan bancos, la hoja que existía puede dejar de existir.
    """
    tamano = max(1, page_size)
    total_resto = len(vista.resto)
    hojas = max(1, -(-total_resto // tamano))
    elegida = min(max(1, page), hojas)
    desde = (elegida - 1) * tamano
    return TrayPage(
        pagina=vista.resto[desde : desde + tamano],
        oficial=vista.oficial,
        resto_total=total_resto,
        filas=vista.filas,
        total_pendiente=vista.total_pendiente,
        propuestas=vista.propuestas,
        entradas_de_decision=vista.entradas_de_decision,
        page=elegida,
        page_size=tamano,
    )


__all__ = [
    "ACCIONES",
    "ESTADOS_ESPERANDO",
    "ETIQUETA_DE_CATEGORIA",
    "FILAS_POR_PAGINA",
    "TEXTO_DE_ACCION",
    "TrayAction",
    "TrayPage",
    "TrayRefusalError",
    "TraySection",
    "TraySet",
    "TrayView",
    "acciones_permitidas",
    "agrupar",
    "paginar",
    "rechazo_de_accion",
]
