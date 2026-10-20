"""Contrato de la zona del alumno (F2).

Estos esquemas son la garantía del contrato de la fase, y conviene leerlos por lo que **no**
tienen: ni evidencia, ni cita, ni conjunto de origen (`question_set_id`), ni clave
(`answer_key_version_id`, `correct_option_keys`), ni versión de documento, ni ruta de fichero, ni
identificador de nodo del programa. La regla del plan —«se consigue con esquemas propios que no
tienen esos campos, no filtrando al final»— se cumple aquí: aunque alguien devolviera por error una
vista con todo eso, no habría dónde ponerlo, porque FastAPI valida la respuesta contra este modelo
y descarta lo que no está declarado.

Dos cosas que sí viajan y son deliberadas:

- **el código legible del tema** (`IV.10`), que es la dirección del alumno; ningún UUID a la vista;
- **el identificador de la sesión**, que es lo que la pantalla necesita para pedir el siguiente
  test. Es lo único que se parece a un identificador interno, y no se puede evitar: es la dirección
  del propio test. Lo que no viaja es de dónde salieron sus preguntas.
- **la procedencia de un examen oficial** (`origin_scope`, D10), y esto es una excepción deliberada
  a la regla de arriba: en la **lista de exámenes** el alumno tiene que saber **qué está
  practicando** —un examen del INAP no es un examen de otra administración—, así que el vocabulario
  cerrado viaja. No viaja el identificador del conjunto (`question_set_id`): la lista sigue
  direccionando cada examen por su sitio, como una fila de la hoja de respuestas.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from opofuente.api.question_schemas import OriginScopeName
from opofuente.api.study_schemas import SessionModeName, SessionStatusName
from opofuente.domain.notes_reports import MAX_REASON_CHARS, normalise_reason

#: Cómo se corrige un test: al momento o al final. Es el vocabulario del dominio, no uno nuevo.
StudentFeedbackName = Literal["immediate", "at_end"]

#: Con qué se eligen las preguntas de un test.
StudentFilterName = Literal["all", "unseen", "failed", "flagged"]

#: Qué se puede marcar de una pregunta al contestarla: la confianza, que es la marca de «dudosa».
StudentConfidenceName = Literal["low", "medium", "high"]

#: El desenlace de una pregunta ya corregida.
StudentOutcomeName = Literal["correct", "wrong", "blank"]

#: Las variantes del simulacro y el bloque de su supuesto.
StudentMockVariantName = Literal["full", "short"]
StudentCaseBlockName = Literal["III", "IV"]

#: Cómo están los apuntes de un tema, tal como se le cuenta al alumno.
StudentNotesStateName = Literal["published", "draft", "none"]

#: En qué punto está un aviso del alumno sobre los apuntes.
StudentReportStatusName = Literal["open", "reviewed", "dismissed"]

#: Qué se hizo al abandonar un test: se descartó (no había nada contestado) o se conservó lo
#: contestado sin contarlo como test hecho.
StudentAbandonActionName = Literal["deleted", "abandoned"]


class StudentOppositionSchema(BaseModel):
    """La oposición que sirve la zona del alumno."""

    code: str
    name: str


class StudentScoreSchema(BaseModel):
    """Cómo fue un test: aciertos, fallos, blancos y la puntuación directa con su penalización.

    La puntuación viaja como fracción exacta en texto (`128/3`) **y** como decimal redondeado: el
    decimal es para leerlo, el exacto es el que vale (DEBT-006). `passed` es `None` cuando la
    convocatoria no publica el umbral, en lugar de inventar un aprobado.
    """

    correct: int = Field(ge=0)
    wrong: int = Field(ge=0)
    blank: int = Field(ge=0)
    points: str
    points_decimal: str
    maximum: float | None = None
    passed: bool | None = None


class StudentSessionSchema(BaseModel):
    """Un test del alumno: lo que se pinta en «Continuar», en el historial y al terminar.

    `title` lo compone la capa del alumno a partir de lo que se eligió; **nunca** es el título del
    conjunto de origen.
    """

    id: str
    mode: SessionModeName
    status: SessionStatusName
    title: str
    total_questions: int = Field(ge=0)
    answered_questions: int = Field(ge=0)
    time_limit_minutes: int | None = None
    started_at: datetime | None = None
    #: La hora del servidor en el momento de la respuesta, del **mismo reloj** que `started_at`. La
    #: pantalla del test la usa para contar el tiempo que queda sin fiarse del reloj del navegador;
    #: sin ella, el reloj se calla en vez de enseñar una cuenta que no se sostiene.
    server_now: datetime
    finished_at: datetime | None = None
    created_at: datetime
    result: StudentScoreSchema | None = None
    #: De dónde salió el supuesto práctico cuando no era material de supuesto: se dice (`bloque`).
    practical_case_origin: str | None = None


class StudentTopicProgressSchema(BaseModel):
    """Un tema con lo que tiene y lo que se ha hecho en él.

    `accuracy` es `None` cuando no hay nada corregido todavía: un tema sin tocar no está
    suspendido. `notes_state` es lo que permite pintar en el temario si sus apuntes están
    publicados, en borrador o sin escribir.
    """

    code: str
    number: int | None = None
    title: str
    available_questions: int = Field(ge=0)
    answered: int = Field(ge=0)
    correct: int = Field(ge=0)
    accuracy: float | None = Field(default=None, ge=0, le=1)
    due_reviews: int = Field(default=0, ge=0)
    notes_state: StudentNotesStateName = "none"


class StudentBlockProgressSchema(BaseModel):
    """Un bloque del programa con sus temas y el agregado del bloque."""

    code: str
    title: str
    position: int
    available_questions: int = Field(ge=0)
    answered: int = Field(ge=0)
    correct: int = Field(ge=0)
    accuracy: float | None = Field(default=None, ge=0, le=1)
    due_reviews: int = Field(default=0, ge=0)
    topics: list[StudentTopicProgressSchema]


class StudentOverviewSchema(BaseModel):
    """Inicio: el test a medias, los fallos vencidos, el progreso por bloque y lo último hecho."""

    opposition: StudentOppositionSchema
    in_progress: StudentSessionSchema | None = None
    due_reviews: int = Field(ge=0)
    blocks: list[StudentBlockProgressSchema]
    recent_tests: list[StudentSessionSchema]


class StudentSyllabusSchema(BaseModel):
    """El temario: bloques y temas **en orden numérico** (IV.1 antes de IV.10)."""

    opposition: StudentOppositionSchema
    blocks: list[StudentBlockProgressSchema]


class StudentEpigraphSchema(BaseModel):
    """Un epígrafe del tema: solo su código y su título."""

    code: str
    title: str


class StudentTopicSchema(BaseModel):
    """Un tema por su código legible, con sus epígrafes y su progreso."""

    code: str
    number: int | None = None
    title: str
    description: str | None = None
    block_code: str
    block_title: str
    epigraphs: list[StudentEpigraphSchema]
    progress: StudentTopicProgressSchema | None = None


class StudentProgressSchema(BaseModel):
    """El progreso: acierto por bloque y por tema, los cinco más flojos e historial.

    `tests_finished` es el número de tests **terminados** de esta persona, no los que caben en el
    historial: la cifra se lee al lado de una lista de veinte y tiene que ser la de verdad.
    """

    opposition: StudentOppositionSchema
    blocks: list[StudentBlockProgressSchema]
    weakest_topics: list[StudentTopicProgressSchema]
    history: list[StudentSessionSchema]
    tests_finished: int = Field(ge=0)


# --- el test en curso: la hoja de respuestas y su corrección -------------------------------------
#
# Aquí se ve otra vez la regla de la fase, y con más motivo que en ningún sitio: la pregunta viaja
# por su **posición en la hoja** (la fila 12), no por su identificador, y una respuesta correcta se
# llama `correct` y no `correct_option_keys` —el nombre que tiene dentro de la casa— porque estas
# respuestas son las que más fácil se cuelan por una pantalla. Los nombres de esta capa son los de
# la hoja de respuestas: posición, opciones, lo marcado.


class StudentOptionSchema(BaseModel):
    """Una opción: su letra (`a`) y su texto."""

    key: str
    text: str


class StudentCorrectionSchema(BaseModel):
    """La corrección de una pregunta respondida, cuando se puede enseñar."""

    outcome: StudentOutcomeName
    correct: list[str] = Field(default_factory=list, description="Letras de la plantilla.")
    reason: str | None = None
    #: La explicación que se enseña DESPUÉS de corregir (M1 de la fase 3).
    explanation: str | None = None
    #: La frase LITERAL de los apuntes que la sostiene, para enseñarla tal cual.
    explanation_citation: str | None = None
    #: El apartado al que se ancla: la pantalla lleva al párrafo con este id.
    explanation_anchor_id: str | None = None


class StudentQuestionSchema(BaseModel):
    """La pregunta que se está contestando, por su posición en la hoja."""

    position: int = Field(ge=1)
    is_reserve: bool
    stem: str
    question_type: str
    options: list[StudentOptionSchema]
    answered: bool
    chosen: list[str] = Field(default_factory=list)
    confidence: StudentConfidenceName | None = None
    correction: StudentCorrectionSchema | None = None
    #: La clave de esta pregunta está en revisión (§1): el conjunto discrepa de los apuntes entre el
    #: 15 % y el 30 %. Entra en el test, pero el alumno lo ve antes de fiarse de la corrección.
    in_review: bool = Field(
        default=False,
        description="La clave de esta pregunta está en revisión: su conjunto discrepa de los "
        "apuntes entre el 15 % y el 30 % de las preguntas medidas.",
    )
    #: Y la clave de esta pregunta es **derivada** (§1 del encargo F29): los apuntes, con su cita
    #: verificada, y el modelo preguntado sin apuntes dicen la misma letra. La interfaz la enseña
    #: como «clave revisada automáticamente», que es distinto de «en revisión».
    derived_key: bool = Field(
        default=False,
        description="La clave de esta pregunta es derivada: los apuntes (con su cita verificada) y "
        "el modelo preguntado sin apuntes dicen la misma letra. Se enseña como «clave revisada "
        "automáticamente».",
    )


class StudentSheetRowSchema(BaseModel):
    """Una fila de la hoja de respuestas: qué se marcó en esa posición y cómo quedó."""

    position: int = Field(ge=1)
    answered: bool
    chosen: list[str] = Field(default_factory=list)
    confidence: StudentConfidenceName | None = None
    outcome: StudentOutcomeName | None = None
    correct: list[str] = Field(default_factory=list)


class StudentAbandonSchema(BaseModel):
    """Qué queda de un test abandonado, en las palabras que se le enseñan al alumno.

    Va aparte de `StudentSessionSchema` a propósito: lo que el alumno necesita saber al salirse de
    un examen a medias no es el estado interno, es si lo contestado se conserva y si eso cuenta.
    """

    session_id: str
    action: StudentAbandonActionName
    detail: str


class StudentRunSchema(BaseModel):
    """El test en curso: la sesión, la pregunta que toca y la hoja de respuestas entera."""

    session: StudentSessionSchema
    total: int = Field(ge=0)
    answered: int = Field(ge=0)
    pending: int = Field(ge=0)
    finished: bool
    position: int | None = Field(default=None, ge=1)
    question: StudentQuestionSchema | None = None
    sheet: list[StudentSheetRowSchema]
    questions_in_review: int = Field(
        default=0,
        ge=0,
        description="Cuántas preguntas del test llevan la marca «clave en revisión».",
    )
    questions_derived: int = Field(
        default=0,
        ge=0,
        description="Cuántas preguntas del test llevan la marca «clave revisada automáticamente»: "
        "su clave es derivada y no sale de la plantilla del conjunto.",
    )


class StudentPartScoreSchema(BaseModel):
    """La nota de una parte, con la forma con la que se calculó.

    `kind` dice cómo se corrigió (`estimated` cuando la puntuación es la directa escalada a la banda
    de la parte) y `verdict_note` lo explica en palabras: una estimación no es la calificación
    oficial, y `passed` se queda en `None` para no declarar un aprobado que nadie ha calculado.
    """

    part_code: str | None = None
    part_name: str | None = None
    kind: str
    correct: int = Field(ge=0)
    wrong: int = Field(ge=0)
    blank: int = Field(ge=0)
    score: str
    score_decimal: str
    score_max: float | None = None
    pass_score: float | None = None
    passed: bool | None = None
    verdict_note: str | None = None


class StudentResultSchema(BaseModel):
    """El resultado de un test: la sesión terminada, la nota por parte y el total."""

    session: StudentSessionSchema
    parts: list[StudentPartScoreSchema]
    total: StudentPartScoreSchema
    official_available: bool
    official_note: str | None = None


class StudentTestRequestSchema(BaseModel):
    """Lo que manda la pantalla para montar un test: sus temas, cuántas y con qué filtro."""

    nodes: list[str] = Field(min_length=1, description="Códigos de tema, como `IV.10`.")
    count: int = Field(ge=1, le=200)
    filter: StudentFilterName = "all"
    feedback: StudentFeedbackName = "immediate"
    timed: bool = False


class StudentMockExamRequestSchema(BaseModel):
    """Lo que manda la pantalla para montar un simulacro: variante y bloque del supuesto."""

    variant: StudentMockVariantName = "full"
    case_block: StudentCaseBlockName = "III"


class StudentTestCountSchema(BaseModel):
    """Un tamaño de test ofrecido, con lo que duraría con el reloj puesto."""

    questions: int = Field(ge=1)
    minutes: int = Field(ge=1)


class StudentTestPlanSchema(BaseModel):
    """Lo que la pantalla de Tests puede ofrecer antes de montar un test (F22).

    Ni un tamaño ni un minuto se calculan en la pantalla: los sirve el servidor, que es el mismo que
    después pone el reloj. `timed_note` es la frase que acompaña al interruptor del reloj, y también
    viene de aquí por la misma razón que la nota del simulacro: la regla se escribe una vez.
    `convocation_minutes` es el tiempo del test cuando **no** se le pone el reloj del test; `null`
    significa que la convocatoria no lo publica, no que no haya ninguno.
    """

    counts: list[StudentTestCountSchema]
    timed_note: str
    convocation_minutes: int | None = Field(default=None, ge=1)


class StudentAnswerRequestSchema(BaseModel):
    """La respuesta a una pregunta, **por su fila en la hoja de respuestas**."""

    position: int = Field(ge=1)
    chosen: list[str] = Field(default_factory=list)
    elapsed_ms: int = Field(default=0, ge=0)
    confidence: StudentConfidenceName | None = None


# --- los apuntes del tema: leerlos y avisar de un error (F13) -------------------------------------


class StudentNoteSectionSchema(BaseModel):
    """Un apartado de los apuntes, con su sitio en el índice y su dirección en la página.

    `anchor` es lo que convierte el índice en navegable: el enlace del índice lleva al párrafo y el
    aviso del alumno apunta a él. `questions_covered` es el dato que acompaña al párrafo («N
    preguntas de este tema se contestan aquí»), y es un recuento real de las comprobaciones del
    tema, no una afirmación sobre exámenes.
    """

    number: int = Field(ge=1)
    key: str
    title: str
    epigraph_code: str
    anchor: str = Field(min_length=1)
    body_markdown: str
    questions_covered: int = Field(ge=0)


class StudentNoteChapterSectionSchema(BaseModel):
    """Un apartado **del índice**: sin su texto, para que viaje el índice entero.

    Es la mitad barata del contrato: con esto la pantalla puede enseñar todos los apartados de todos
    los capítulos y resolver a qué capítulo pertenece un anclaje, sin que un tema de 314.000 px
    viaje de una vez.
    """

    number: int = Field(ge=1)
    key: str
    title: str
    anchor: str = Field(min_length=1)
    questions_covered: int = Field(ge=0)


class StudentNoteChapterSchema(BaseModel):
    """Un capítulo de los apuntes: un **epígrafe oficial** del tema, con sus apartados.

    `code` es el código del epígrafe (`IV.7.2`), que es lo que lleva el parámetro `capitulo` de la
    petición y lo que viaja en el enlace «Ver en apuntes». `position` es su lugar en el tema (1..N),
    para poder ofrecer «anterior» y «siguiente» sin ordenar nada en la pantalla.
    """

    code: str = Field(min_length=1)
    title: str
    position: int = Field(ge=1)
    sections: list[StudentNoteChapterSectionSchema]


class StudentNotesSchema(BaseModel):
    """Los apuntes de un tema: cómo están, **un capítulo** para leer y el índice completo.

    Un tema en `draft` se sirve **igual** que uno en `published`: la marca distingue uno de otro y
    el alumno puede leer los dos. Un tema en `none` no trae apartados, y eso no es un error.

    `sections` trae el texto del capítulo servido y `chapters` el índice de todos los capítulos, con
    sus apartados pero sin sus textos. `chapter` dice cuál de ellos viaja en `sections`, y puede no
    ser el pedido: un `capitulo` que ya no existe sirve el primero, y la pantalla lo dice
    corrigiendo la dirección en vez de dejar al alumno en un error.
    """

    code: str
    state: StudentNotesStateName
    generated_at: datetime | None = None
    sections: list[StudentNoteSectionSchema]
    chapter: str | None = None
    chapters: list[StudentNoteChapterSchema]


class StudentReportRequestSchema(BaseModel):
    """Lo que manda la pantalla cuando el alumno marca «esto está mal» en un apartado.

    El motivo es **una línea** y es obligatorio: se recorta, no puede quedar vacío y tiene su tope
    (`MAX_REASON_CHARS`). El apartado se manda por su clave, no por su anclaje: el anclaje lo pone
    el servidor a partir del apartado que existe hoy.
    """

    section_key: str = Field(min_length=1, max_length=200)
    reason: str = Field(min_length=1)

    @field_validator("reason")
    @classmethod
    def _motivo_en_una_linea(cls, valor: str) -> str:
        """El motivo, tal como se guarda. Un texto que no vale sale como 422 con su campo.

        La regla vive en el dominio (`normalise_reason`) y aquí solo se traduce a la validación del
        contrato: así la pantalla recibe `field_errors` con el motivo del rechazo en lugar de un
        500 por un texto que nadie puede arreglar.
        """
        try:
            return normalise_reason(valor)
        except ValueError as error:
            raise ValueError(str(error)) from error


class StudentReportSchema(BaseModel):
    """El aviso ya guardado: dónde, qué se escribió y cuándo."""

    section_key: str
    reason: str = Field(
        description=f"El motivo, en una línea (máximo {MAX_REASON_CHARS} caracteres)."
    )
    status: StudentReportStatusName
    created_at: datetime


# --- el resultado de un test, pregunta a pregunta (F14) ------------------------------------------
#
# La misma regla de siempre, y aquí se ve por qué importa: la pregunta viaja por su **posición**, su
# opción correcta se llama `correct` —no `correct_option_keys`, que es el nombre de dentro— y de
# dónde salió la pregunta **no aparece**. Lo que sí aparece, y es la razón de ser de esta pantalla,
# es el **tema** de cada pregunta y el desglose por tema: con eso se sabe qué repasar.

#: El desenlace que esta capa pronuncia. `void` no es un fallo del alumno: es una pregunta que la
#: plantilla no corrige (anulada, sin entrada o en conflicto), y se dice así en lugar de contarla.
StudentResultOutcomeName = Literal["correct", "wrong", "blank", "void"]


class StudentTopicRefSchema(BaseModel):
    """Un tema por su código legible: la respuesta a «¿de qué era esto?»."""

    code: str
    title: str


class StudentNoteAnchorSchema(BaseModel):
    """El apartado de los apuntes que contesta una pregunta, con su tema, su capítulo y su anclaje.

    Es lo que permite que «Ver en apuntes» del resultado deje al alumno **en el párrafo** que
    explica su fallo (`/temario/IV.7?capitulo=IV.7.2#apartado-udp`) en vez de en la portada del
    tema, que no explica nada. El **capítulo** viaja con el anclaje porque los apuntes se leen por
    epígrafes oficiales: sin él, la página abriría el primer capítulo de IV.7 y el párrafo no
    estaría en ella.
    """

    topic_code: str = Field(
        description="El tema al que pertenece el apartado, por su código legible."
    )
    anchor: str = Field(description="El anclaje del apartado dentro de los apuntes del tema.")
    epigraph_code: str = Field(
        default="",
        description="El epígrafe oficial (capítulo) que contiene ese apartado, para abrir la "
        "página por él. Vacío si el apartado no dice a qué epígrafe pertenece.",
    )


class StudentResultQuestionSchema(BaseModel):
    """Una pregunta corregida: sus opciones, lo que se marcó, la correcta y de qué era."""

    position: int = Field(ge=1)
    is_reserve: bool
    part_code: str | None = None
    part_name: str | None = None
    stem: str
    options: list[StudentOptionSchema]
    chosen: list[str] = Field(default_factory=list)
    correct: list[str] = Field(default_factory=list)
    outcome: StudentResultOutcomeName
    elapsed_ms: int | None = Field(default=None, ge=0)
    topics: list[StudentTopicRefSchema] = Field(default_factory=list)
    #: La clave de esta pregunta está en revisión (§1). En el resultado importa más que en el test:
    #: un fallo puede ser de la clave y no del alumno.
    in_review: bool = Field(
        default=False,
        description="La clave de esta pregunta está en revisión: un fallo puede ser de la clave y "
        "no del alumno.",
    )
    derived_key: bool = Field(
        default=False,
        description="La clave de esta pregunta es derivada (los apuntes, con su cita verificada, y "
        "el modelo sin apuntes dicen la misma letra): se enseña como «clave revisada "
        "automáticamente».",
    )
    note_anchor: StudentNoteAnchorSchema | None = Field(
        default=None,
        description="El apartado de los apuntes que contesta esta pregunta. Con él, una fallada "
        "ofrece «Ver en apuntes» al párrafo exacto; sin él no se ofrece la salida, en vez de "
        "mandar al alumno a la portada del tema.",
    )


class StudentResultTopicSchema(BaseModel):
    """Cómo fue el test en un tema: aciertos, fallos, blancos y el porcentaje que sale de ellos."""

    code: str
    title: str
    correct: int = Field(ge=0)
    wrong: int = Field(ge=0)
    blank: int = Field(ge=0)
    graded: int = Field(ge=0)
    accuracy: float | None = Field(default=None, ge=0, le=1)


class StudentSessionResultSchema(BaseModel):
    """El resultado de un test terminado, con el tiempo empleado y las preguntas una a una."""

    session: StudentSessionSchema
    parts: list[StudentPartScoreSchema]
    total: StudentPartScoreSchema
    official_available: bool
    official_note: str | None = None
    duration_seconds: int | None = Field(default=None, ge=0)
    questions: list[StudentResultQuestionSchema]
    topics: list[StudentResultTopicSchema]


# --- el simulacro antes de montarlo (F14) --------------------------------------------------------


class StudentMockExamPartSchema(BaseModel):
    """Una parte del simulacro, con lo que publica el perfil del examen y nada más."""

    code: str
    name: str
    ordinary_items: int | None = Field(default=None, ge=0)
    reserve_items: int | None = Field(default=None, ge=0)
    score_max: float | None = None
    pass_score: float | None = None
    penalty: str | None = None
    time_minutes: int | None = Field(default=None, ge=0)


class StudentMockExamVariantSchema(BaseModel):
    """Una variante del simulacro: qué cae, cuánto dura y qué es lo que **no** es."""

    variant: StudentMockVariantName
    title: str
    time_limit_minutes: int | None = Field(default=None, ge=0)
    parts: list[StudentMockExamPartSchema]
    note: str | None = None


class StudentMockCaseTopicSchema(BaseModel):
    """Un tema del bloque del supuesto, con sus preguntas disponibles hoy."""

    code: str
    title: str
    available_questions: int = Field(ge=0)


class StudentMockCaseBlockSchema(BaseModel):
    """Un bloque del que se puede elegir el supuesto (III o IV)."""

    code: str
    title: str
    topics: list[StudentMockCaseTopicSchema]


class StudentMockExamPlanSchema(BaseModel):
    """El simulacro antes de montarlo: las dos variantes y los bloques del supuesto."""

    opposition: StudentOppositionSchema
    full: StudentMockExamVariantSchema
    short: StudentMockExamVariantSchema
    case_blocks: list[StudentMockCaseBlockSchema]


# --- los exámenes oficiales importados (F14) -----------------------------------------------------


class StudentOfficialExamSchema(BaseModel):
    """Un examen oficial, por su sitio en la lista: título, fecha, tamaño y si se puede hacer."""

    position: int = Field(ge=1)
    title: str
    held_at: date | None = None
    #: El año que declara el documento de origen cuando no declara el día (ver
    #: `StudentOfficialExamView.held_year`). La pantalla lo enseña en lugar de «sin fecha»: es lo
    #: único que el origen dice, y no se inventa el día y el mes.
    held_year: int | None = Field(default=None, ge=1900, le=2100)
    questions: int = Field(ge=0)
    ready: bool
    #: Si no se puede hacer, por qué: `faltan_respuestas` o `faltan_preguntas`. Vocabulario cerrado
    #: y traducido en la pantalla (F39): son dos motivos distintos y decir «faltan sus respuestas»
    #: cuando lo que falta son preguntas sería mentir con una frase concreta.
    blocked_reason: Literal["faltan_respuestas", "faltan_preguntas"] | None = None
    #: De dónde sale el examen (D10): `age`, `otra_administracion` o `desconocida`. La pantalla lo
    #: enseña para que el alumno sepa **qué está practicando**.
    origin_scope: OriginScopeName = "desconocida"


class StudentOfficialExamsSchema(BaseModel):
    """Los exámenes oficiales importados. Una lista vacía es un estado, no un error."""

    exams: list[StudentOfficialExamSchema]


# --- los fallos (F14) ----------------------------------------------------------------------------


class StudentMistakeSchema(BaseModel):
    """Una pregunta fallada: qué decía, de qué era, cuándo y cuántas veces."""

    stem: str
    topics: list[StudentTopicRefSchema] = Field(default_factory=list)
    last_failed_at: datetime
    times_failed: int = Field(ge=0)
    due: bool


class StudentMistakeTopicSchema(BaseModel):
    """Los fallos de un tema: es con lo que se pide un test solo de esos fallos."""

    code: str
    title: str
    failed: int = Field(ge=0)
    due: int = Field(ge=0)


class StudentMistakesSchema(BaseModel):
    """Los fallos: los totales, los que se enseñan y su reparto por tema."""

    total: int = Field(ge=0)
    due_total: int = Field(ge=0)
    #: De los fallos, cuántos se pueden corregir y por tanto repasar (F39): es lo que decide si la
    #: pantalla ofrece el test de fallos o dice por qué no hay ninguno que montar.
    servable_total: int = Field(default=0, ge=0)
    questions: list[StudentMistakeSchema]
    topics: list[StudentMistakeTopicSchema]
