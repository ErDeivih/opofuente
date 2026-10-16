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
from datetime import date, datetime

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
class StudentTestCountView:
    """Un tamaño de test ofrecido en la pantalla, con lo que dura si se le pone reloj.

    `minutes` sale de la **misma** regla con la que el servidor pone el reloj al montar la sesión
    (`StudentService._minutos_de_test`). La pantalla no la recalcula: si lo hiciera, habría dos
    verdades sobre cuánto dura un test, y la que se enseña antes de empezar podría dejar de ser la
    que se aplica después.
    """

    questions: int
    minutes: int


@dataclass(frozen=True, slots=True)
class StudentTestPlanView:
    """Lo que la pantalla de Tests puede ofrecer **antes** de montar nada (F22).

    Los tamaños y la nota del reloj son de la **aplicación**, no de la convocatoria —como los 40
    minutos de la variante corta del simulacro—, y por eso los sirve el servidor: son números que
    la interfaz enseña y que tienen que salir del mismo sitio del que sale el reloj de verdad.

    `convocation_minutes` es el tiempo que **sí** lleva un test cuando no se le pone el reloj del
    test: el de la parte del perfil con la que se corrige ese material. Es `None` si la convocatoria
    no lo publica, y la pantalla lo dice en lugar de suponer que no hay ninguno: medido en la base,
    un test sin reloj hereda los 120 minutos del ejercicio, no cero.
    """

    counts: tuple[StudentTestCountView, ...]
    timed_note: str
    convocation_minutes: int | None = None


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

    `tests_finished` cuenta los tests **terminados** de esta persona en esta oposición, no los que
    caben en el historial: es la cifra que se lee junto al historial y tiene que ser la de verdad.
    """

    opposition: StudentOppositionView
    blocks: tuple[StudentBlockProgressView, ...]
    weakest_topics: tuple[StudentTopicProgressView, ...] = ()
    history: tuple[StudentSessionView, ...] = ()
    tests_finished: int = 0


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
    #: La clave de esta pregunta está **en revisión** (§1): su conjunto discrepa de los apuntes
    #: entre el 15 % y el 30 %, así que entra en el test pero el alumno lo ve. El texto de la
    #: marca vive en `domain.key_reliability.MARCA_EN_REVISION` y no se repite aquí: dos
    #: literales distintos acabarían diciendo cosas distintas en la pantalla y en el contrato.
    in_review: bool = False
    #: La clave de **esta** pregunta es **derivada** (§1 del encargo F29): los apuntes, con su cita
    #: verificada, y el modelo preguntado sin apuntes dicen la misma letra. El alumno la ve con la
    #: marca `domain.key_reliability.MARCA_DERIVADA` («clave revisada automáticamente»), que es
    #: distinta de «en revisión» y por eso es otro campo: una avisa de una duda y la otra dice de
    #: dónde sale la letra.
    derived_key: bool = False


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
    #: Cuántas preguntas del test llevan la marca «clave en revisión». El test entero lo puede decir
    #: de un vistazo sin que el alumno tenga que ir pregunta a pregunta.
    questions_in_review: int = 0
    #: Y cuántas se corrigen con su **clave derivada** y llevan la marca «clave revisada
    #: automáticamente». Es otra cuenta porque es otra cosa: una dice cuántas están en duda y esta,
    #: cuántas letras se han reconstruido con dos fuentes independientes.
    questions_derived: int = 0


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


# --- el resultado de un test, pregunta a pregunta (F14) ------------------------------------------


@dataclass(frozen=True, slots=True)
class StudentTopicRefView:
    """Un tema, por su código legible: es la respuesta a «¿de qué era esto?».

    Existe para las pantallas que dicen **por qué tema** se ha fallado. No lleva el identificador
    del
    nodo: el código (`IV.7`) es la dirección del alumno en toda la zona.
    """

    code: str
    title: str


@dataclass(frozen=True, slots=True)
class StudentNoteAnchorView:
    """El apartado de los apuntes que **contesta** una pregunta, con su tema y su anclaje.

    Existe para que «Ver en apuntes» del resultado lleve al párrafo que explica el fallo
    (`/temario/IV.7#udp`) y no a la portada del tema, que no explica nada. Sale de la
    comprobación del motor (`question_note_anchors`), que es donde está la letra que los apuntes
    dieron con su cita.

    Una pregunta puede estar en dos temas (D7) y el apartado pertenece a **uno**: viaja con su
    código de tema para que el enlace no dependa de cuál de los dos se enseñe primero.
    """

    topic_code: str
    anchor: str


@dataclass(frozen=True, slots=True)
class StudentResultQuestionView:
    """Una pregunta ya corregida, con las tres cosas que el alumno necesita ver juntas.

    Sus opciones, lo que marcó, cuál era la correcta y —esto es lo que convierte la lista en algo
    útil— **de qué tema era**, para poder ir a repasarlo. `outcome` es `correct`, `wrong` o `blank`.

    `topics` es una tupla porque una pregunta puede estar catalogada en dos temas (D7): enseñar uno
    sería elegir por el alumno cuál de los dos repasa.
    """

    position: int
    is_reserve: bool
    part_code: str | None
    part_name: str | None
    stem: str
    options: tuple[StudentOptionView, ...]
    chosen_option_keys: tuple[str, ...] = ()
    correct_option_keys: tuple[str, ...] = ()
    outcome: str = "blank"
    elapsed_ms: int | None = None
    topics: tuple[StudentTopicRefView, ...] = ()
    #: La clave de esta pregunta está **en revisión** (§1). En el resultado importa más que en
    #: el test: si la clave no es de fiar, un fallo puede ser de la clave y no del alumno, y eso
    #: hay que poder verlo justo cuando se mira qué se ha fallado.
    in_review: bool = False
    #: Y la clave de esta pregunta es **derivada** (§1 del encargo F29). En el resultado importa
    #: por lo mismo que la otra: dice de dónde sale la letra con la que se corrigió, y con la marca
    #: «clave revisada automáticamente» el alumno sabe que la letra no es la de la plantilla.
    derived_key: bool = False
    #: El apartado de los apuntes que contesta esta pregunta, o `None` si los apuntes no la
    #: contestan. Con él, una fallada ofrece «Ver en apuntes» **al párrafo**, que es lo que el
    #: alumno necesita para entender el fallo; sin él no se ofrece la salida, en vez de mandarlo a
    #: la portada del tema.
    note_anchor: StudentNoteAnchorView | None = None


@dataclass(frozen=True, slots=True)
class StudentResultTopicView:
    """Cómo fue el test **en un tema**: es el desglose que dice qué hay que repasar.

    `graded` es el denominador del acierto (aciertos, fallos y blancos) y `accuracy` es `None`
    cuando no hay nada corregido en ese tema: un tema sin preguntas en el test no está suspendido.
    """

    code: str
    title: str
    correct: int
    wrong: int
    blank: int

    @property
    def graded(self) -> int:
        return self.correct + self.wrong + self.blank

    @property
    def accuracy(self) -> float | None:
        return None if self.graded == 0 else self.correct / self.graded


@dataclass(frozen=True, slots=True)
class StudentSessionResultView:
    """El resultado de un test terminado, listo para leerse entero.

    Es el hermano de `StudentResultView` (lo que devuelve terminar) con lo que la pantalla de
    resultado necesita además: **el tiempo empleado** y las preguntas una a una con su tema. La
    puntuación no se recalcula aquí: son las mismas partes y el mismo total que se guardaron al
    cerrar la sesión.
    """

    session: StudentSessionView
    parts: tuple[StudentPartScoreView, ...]
    total: StudentPartScoreView
    official_available: bool
    official_note: str | None = None
    duration_seconds: int | None = None
    questions: tuple[StudentResultQuestionView, ...] = ()
    topics: tuple[StudentResultTopicView, ...] = ()


# --- el simulacro: qué va a caer antes de empezarlo (F14) ----------------------------------------


@dataclass(frozen=True, slots=True)
class StudentMockExamPartView:
    """Una parte del simulacro, tal como la publica el perfil del examen.

    Todos los números salen de la convocatoria: cuántas preguntas ordinarias, cuántas de reserva, la
    banda de puntuación, el mínimo y la penalización. Lo que el perfil no publica va en `None`, que
    es distinto de cero.
    """

    code: str
    name: str
    ordinary_items: int | None
    reserve_items: int | None
    score_max: float | None
    pass_score: float | None
    penalty: str | None
    time_minutes: int | None


@dataclass(frozen=True, slots=True)
class StudentMockExamVariantView:
    """Una variante del simulacro con lo que se sabe de ella **antes** de empezar.

    `note` es la frase que dice lo que el simulacro es y lo que no: tiene el perfil del examen, no
    es
    un examen oficial y su nota por parte es una estimación. Viaja con la variante porque es lo que
    hay que leer antes de pulsar «empezar», no después.
    """

    variant: str
    title: str
    time_limit_minutes: int | None
    parts: tuple[StudentMockExamPartView, ...]
    note: str | None = None


@dataclass(frozen=True, slots=True)
class StudentMockCaseTopicView:
    """Un tema del bloque del supuesto, con las preguntas que hoy tiene disponibles."""

    code: str
    title: str
    available_questions: int


@dataclass(frozen=True, slots=True)
class StudentMockCaseBlockView:
    """Un bloque del que se puede elegir el supuesto (III o IV), con sus temas.

    Los dos supuestos son **excluyentes**: se elige uno. Enseñar los dos bloques con sus temas es lo
    que permite elegir sabiendo qué va a caer.
    """

    code: str
    title: str
    topics: tuple[StudentMockCaseTopicView, ...]


@dataclass(frozen=True, slots=True)
class StudentMockExamPlanView:
    """El simulacro antes de montarlo: las dos variantes y los bloques del supuesto."""

    opposition: StudentOppositionView
    full: StudentMockExamVariantView
    short: StudentMockExamVariantView
    case_blocks: tuple[StudentMockCaseBlockView, ...] = ()


# --- los exámenes oficiales importados (F14) -----------------------------------------------------


@dataclass(frozen=True, slots=True)
class StudentOfficialExamView:
    """Un examen oficial importado, tal como se ofrece: su sitio en la lista, su fecha y su tamaño.

    `position` es la **dirección del alumno** dentro de la lista (el primero, el segundo), igual que
    la fila de la hoja de respuestas es la dirección de una pregunta: así la pantalla puede pedir
    «hazme este» sin que viaje de dónde salieron sus preguntas.
    """

    position: int
    title: str
    held_at: date | None
    questions: int
    ready: bool
    #: De dónde sale el examen (D10): `age`, `otra_administracion` o `desconocida`. Va en la vista
    #: porque **la pantalla lo tiene que decir**: el alumno tiene que saber qué está practicando.
    origin_scope: str = "desconocida"


@dataclass(frozen=True, slots=True)
class StudentOfficialExamsView:
    """Los exámenes oficiales importados de esta oposición.

    Una lista vacía **no es un error**: es que todavía no se ha importado ninguno, y la pantalla lo
    dice con esas palabras en vez de quedarse en blanco.
    """

    exams: tuple[StudentOfficialExamView, ...] = ()


# --- los fallos (F14) ----------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class StudentMistakeView:
    """Una pregunta fallada: su enunciado, de qué era, cuándo y cuántas veces.

    `times_failed` cuenta los fallos de verdad (evaluaciones con desenlace `wrong` de los intentos
    de
    esta persona), no los intentos. `due` es si ya toca repasarla.
    """

    stem: str
    topics: tuple[StudentTopicRefView, ...]
    last_failed_at: datetime
    times_failed: int
    due: bool


@dataclass(frozen=True, slots=True)
class StudentMistakeTopicView:
    """Los fallos de un tema, que es con lo que se monta un test solo de fallos."""

    code: str
    title: str
    failed: int
    due: int


@dataclass(frozen=True, slots=True)
class StudentMistakesView:
    """Los fallos: la página que se lee, los totales y su reparto por tema.

    `total` y `due_total` cuentan **todos** los fallos, no los que caben en la página; `topics` es
    el
    reparto que permite decir «monta un test solo con los fallos de este tema».
    """

    total: int
    due_total: int
    questions: tuple[StudentMistakeView, ...] = ()
    topics: tuple[StudentMistakeTopicView, ...] = ()
