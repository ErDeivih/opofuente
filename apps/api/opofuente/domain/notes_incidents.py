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
"""

from __future__ import annotations

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


__all__ = [
    "CLOSED_STATUSES",
    "IncidentCoverage",
    "IncidentFilter",
    "IncidentStatus",
    "NotesIncident",
    "normalise_note",
    "reviewed_at_for",
]
