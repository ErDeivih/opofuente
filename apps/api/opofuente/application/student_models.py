"""Modelos de lectura de la zona del alumno (F2).

Estos modelos son la mitad de la regla del contrato de esta fase: **lo que no está aquí no puede
salir por la API**. Deliberadamente **no** tienen campo para la evidencia, el conjunto de origen, la
clave, la versión del documento, la ruta de un fichero ni el título de un banco. No es que se
filtren al final: es que no hay dónde ponerlos (REDISENO-ALUMNO §3.11, F2 §4).

Dos convenciones que se repiten y conviene leer una vez:

1. **El tema viaja por su código legible** (`IV.10`), no por su identificador. Ninguna respuesta de
   esta capa enseña un UUID de nodo del programa.
2. **`accuracy` es `None` cuando no hay nada respondido**, no `0.0`. Un tema sin tocar no está
   «suspendido»: está sin empezar, y confundir las dos cosas es mentir con un número.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from opofuente.domain.topic_notes import NotesState


@dataclass(frozen=True, slots=True)
class StudentOppositionView:
    """La oposición que sirve la zona del alumno, tal como se enseña: código y nombre."""

    code: str
    name: str


@dataclass(frozen=True, slots=True)
class StudentScoreView:
    """Cómo fue un test: aciertos, fallos, blancos y la puntuación directa con su penalización.

    `points` es la fracción exacta en texto (`128/3`, `42`) porque un tercio no es un decimal
    (DEBT-006) y `points_decimal` es la misma cifra redondeada, solo para leerla.
    """

    correct: int
    wrong: int
    blank: int
    points: str
    points_decimal: str
    maximum: float | None = None
    passed: bool | None = None


@dataclass(frozen=True, slots=True)
class StudentSessionView:
    """Un test del alumno: lo que se pinta en «Continuar», en el historial y al terminar.

    `title` lo compone esta capa a partir de lo que el alumno eligió, **nunca** del título del
    conjunto de origen: el nombre del banco del propietario no se le enseña a nadie (§3.10).
    """

    id: str
    mode: str
    status: str
    title: str
    total_questions: int
    answered_questions: int
    time_limit_minutes: int | None
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime
    result: StudentScoreView | None = None
    #: De dónde salieron las preguntas del supuesto práctico cuando no eran material de supuesto:
    #: se dice (`"bloque"`), no se calla. `None` cuando no hay supuesto o cuando lo es de verdad.
    practical_case_origin: str | None = None

    @property
    def finished(self) -> bool:
        return self.status == "finished"


@dataclass(frozen=True, slots=True)
class StudentTopicProgressView:
    """Un tema con lo que el alumno tiene y lo que ha hecho en él.

    `notes_state` es lo único que no es progreso y está aquí a propósito: el temario y el inicio
    pintan cada tema con su estado de apuntes, y separarlo en un diccionario aparte obligaría a
    cruzar dos listas por código en la pantalla para acabar diciendo lo mismo.
    """

    code: str
    number: int | None
    title: str
    available_questions: int
    answered: int
    correct: int
    accuracy: float | None
    due_reviews: int = 0
    notes_state: str = NotesState.NONE.value

    @property
    def started(self) -> bool:
        return self.answered > 0


@dataclass(frozen=True, slots=True)
class StudentBlockProgressView:
    """Un bloque del programa con sus temas y el agregado del bloque.

    El agregado **no** es la media de los temas: es el total del bloque (aciertos entre corregidas).
    Promediar medias daría a un tema con dos preguntas el mismo peso que a uno con cincuenta.
    """

    code: str
    title: str
    position: int
    available_questions: int
    answered: int
    correct: int
    accuracy: float | None
    due_reviews: int = 0
    topics: tuple[StudentTopicProgressView, ...] = ()


@dataclass(frozen=True, slots=True)
class StudentOverviewView:
    """Lo que se pinta al entrar: el test a medias, los fallos vencidos y el progreso por bloque."""

    opposition: StudentOppositionView
    in_progress: StudentSessionView | None
    due_reviews: int
    blocks: tuple[StudentBlockProgressView, ...]
    recent_tests: tuple[StudentSessionView, ...] = ()


@dataclass(frozen=True, slots=True)
class StudentEpigraphView:
    """Un epígrafe del tema: solo código y título (el programa de TAI no publica epígrafes)."""

    code: str
    title: str


@dataclass(frozen=True, slots=True)
class StudentTopicView:
    """Un tema por su código legible: título, epígrafes, recuentos y progreso."""

    code: str
    number: int | None
    title: str
    description: str | None
    block_code: str
    block_title: str
    epigraphs: tuple[StudentEpigraphView, ...] = ()
    progress: StudentTopicProgressView | None = None


@dataclass(frozen=True, slots=True)
class StudentTestRequest:
    """Lo que pide el alumno cuando monta un test: sus temas, cuántas y con qué filtro.

    Los temas viajan por su **código legible** (`IV.10`, `III.1`) porque es lo que el alumno ve; la
    traducción a nodos del programa la hace esta capa, no la pantalla.
    """

    nodes: tuple[str, ...]
    count: int
    filter: str = "all"
    feedback: str = "immediate"
    timed: bool = False
    owner_id: str = "local"


@dataclass(frozen=True, slots=True)
class StudentMockExamRequest:
    """Lo que pide el alumno cuando monta un simulacro: variante y bloque del supuesto.

    `case_block` solo se usa en el simulacro completo: hay que elegir III o IV, y de los dos
    supuestos se monta **el elegido**, no los dos.
    """

    variant: str = "full"
    case_block: str = "III"
    owner_id: str = "local"


@dataclass(frozen=True, slots=True)
class StudentAnswerRequest:
    """La respuesta a una pregunta del test, **por su posición en la hoja**.

    La posición es lo que el alumno tiene delante (la fila 12 de la hoja), y evita que un
    identificador de pregunta salga por esta capa.
    """

    position: int
    chosen_option_keys: tuple[str, ...]
    elapsed_ms: int = 0
    confidence: str | None = None


@dataclass(frozen=True, slots=True)
class StudentProgressView:
    """El progreso: acierto por bloque y por tema, los cinco más flojos e historial.

    «Los más flojos» solo mira temas **empezados**: un tema sin responder no es un punto débil, es
    un tema sin empezar, y colarlo en la lista empujaría fuera al que de verdad hay que repasar.
    """

    opposition: StudentOppositionView
    blocks: tuple[StudentBlockProgressView, ...]
    weakest_topics: tuple[StudentTopicProgressView, ...] = ()
    history: tuple[StudentSessionView, ...] = ()


# --- el test en curso y su resultado (la pantalla con la hoja de respuestas) ----------------------


@dataclass(frozen=True, slots=True)
class StudentOptionView:
    """Una opción de una pregunta: su letra (`a`) y su texto. Nada más."""

    key: str
    text: str


@dataclass(frozen=True, slots=True)
class StudentCorrectionView:
    """La corrección de una pregunta respondida, **cuando se puede enseñar**.

    `outcome` es `correct`, `wrong` o `blank`; `correct_option_keys` las letras de la plantilla. No
    hay campo para la explicación ni para la evidencia: la zona del alumno no las tiene.
    """

    outcome: str
    correct_option_keys: tuple[str, ...] = ()
    reason: str | None = None


@dataclass(frozen=True, slots=True)
class StudentQuestionView:
    """La pregunta que se está contestando.

    Viaja **por su posición** y no por su identificador: la dirección de una pregunta en un test es
    el número de su fila en la hoja de respuestas, y esa es la que el alumno ve. Contestar se pide
    por posición, así que ningún UUID de pregunta sale de esta capa (F2 §4).
    """

    position: int
    is_reserve: bool
    stem: str
    question_type: str
    options: tuple[StudentOptionView, ...]
    answered: bool
    chosen_option_keys: tuple[str, ...] = ()
    confidence: str | None = None
    correction: StudentCorrectionView | None = None


@dataclass(frozen=True, slots=True)
class StudentSheetRowView:
    """Una fila de la hoja de respuestas: qué se marcó en esa posición y cómo quedó."""

    position: int
    answered: bool
    chosen_option_keys: tuple[str, ...] = ()
    confidence: str | None = None
    outcome: str | None = None
    correct_option_keys: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class StudentRunView:
    """El test en curso: la sesión, la pregunta que toca y la hoja de respuestas entera."""

    session: StudentSessionView
    total: int
    answered: int
    pending: int
    finished: bool
    position: int | None = None
    question: StudentQuestionView | None = None
    sheet: tuple[StudentSheetRowView, ...] = ()


@dataclass(frozen=True, slots=True)
class StudentPartScoreView:
    """La nota de una parte del test, con la forma con la que se calculó.

    `kind` es `estimated`, `direct`, `scaled` o `pass_fail`, y `score_max`/`pass_score` son de la
    banda publicada de la parte. `passed` es `None` cuando la convocatoria no publica el umbral o
    cuando la cifra es una estimación: la calificación oficial no se declara.
    """

    part_code: str | None
    part_name: str | None
    kind: str
    correct: int
    wrong: int
    blank: int
    score: str
    score_decimal: str
    score_max: float | None = None
    pass_score: float | None = None
    passed: bool | None = None
    verdict_note: str | None = None


@dataclass(frozen=True, slots=True)
class StudentResultView:
    """El resultado de un test: la sesión, la nota por parte y el total."""

    session: StudentSessionView
    parts: tuple[StudentPartScoreView, ...]
    total: StudentPartScoreView
    official_available: bool
    official_note: str | None = None


# --- los apuntes del tema: la pantalla de lectura (F13) ------------------------------------------


@dataclass(frozen=True, slots=True)
class StudentNoteSectionView:
    """Un apartado de los apuntes, tal como se lee en la pantalla del alumno.

    `number` es su lugar en el índice (1..N) y `anchor` su dirección estable dentro de la página:
    con ella el índice lleva al párrafo y el aviso «esto está mal» apunta a un sitio concreto.

    `questions_covered` es lo único que se dice de las preguntas: **cuántas** de este tema se
    contestan con este apartado. No viaja ningún identificador de pregunta —el contrato de esta capa
    no tiene sitio para él— y la cifra es real: sale de las anclas comprobadas del tema. Es la nota
    al margen que el diseño pide junto al párrafo, con un dato en vez de una frase inventada sobre
    exámenes.
    """

    key: str
    number: int
    title: str
    epigraph_code: str
    anchor: str
    body_markdown: str
    questions_covered: int = 0


@dataclass(frozen=True, slots=True)
class StudentNotesView:
    """Los apuntes de un tema: cómo están y sus apartados en orden de lectura.

    `state` es `published`, `draft` o `none` (`domain.topic_notes.NotesState`). Un tema en borrador
    **se sirve igual** que uno publicado: la decisión D2/D12 es que se pueda leer y que se diga que
    está en revisión, no que se esconda. Un tema sin apuntes no es un error: es una lista vacía con
    su estado, y la pantalla lo dice.
    """

    code: str
    state: str
    generated_at: datetime | None = None
    sections: tuple[StudentNoteSectionView, ...] = ()


@dataclass(frozen=True, slots=True)
class StudentReportView:
    """Lo que se guarda cuando el alumno marca un apartado como «esto está mal» (D2).

    Devuelve lo que escribió y dónde, sin identificadores internos: el alumno acaba de pulsar el
    botón y lo que necesita saber es que ha quedado guardado en ese apartado.
    """

    section_key: str
    reason: str
    status: str
    created_at: datetime
