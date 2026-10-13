"""Lo que la ficha de pregunta enseña y lo que devuelve al escribir (F20, §4.2 del objetivo).

Una pantalla que sirve para **decidir** una clave tiene que enseñar, además de la pregunta, las tres
cosas que permiten decidirla: de dónde sale la respuesta correcta que hay hoy, qué dicen los apuntes
y
qué ha señalado el motor. Eso son tres tablas distintas (`answer_key_versions` con su
`source_document_version_id`, `question_note_anchors` y `notes_incidents`) y por eso la ficha es una
vista compuesta y no la pregunta con dos campos más.

Lo que **no** se copia aquí dentro: el texto del porqué de cada categoría de incidencia ni el de
cada
reparación. Viajan desde el dominio (`TITULO_DE_REGLA`, `TEXTO_DE_CATEGORIA`) para que haya una sola
versión del párrafo; una copia en la pantalla es la que se queda vieja.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime


@dataclass(frozen=True, slots=True)
class OptionView:
    """Una opción, con su letra y su texto.

    `letra` es la clave estable de la opción (`a`, `b`…) y es **la que se guarda** como respuesta
    correcta: la posición se puede reordenar (el modelo B de un examen tiene las mismas opciones en
    otro orden) y la letra no.
    """

    stable_key: str
    position: int
    text: str
    label: str | None = None


@dataclass(frozen=True, slots=True)
class KeyProvenanceView:
    """La respuesta correcta que manda hoy y **de dónde sale**.

    No es solo la letra: un «C» sin decir de qué plantilla viene, de qué material salió y en qué
    estado está la versión de ese material no se puede juzgar. Es la mitad del trabajo de esta
    pantalla.
    """

    answer_key_version_id: str
    version_no: int
    status: str
    outcome: str
    correct_option_keys: tuple[str, ...]
    approved_at: datetime | None = None
    published_at: date | None = None
    #: El material del que salió la clave, cuando consta: es lo que hay que abrir para comprobarla.
    source_document_id: str | None = None
    source_document_title: str | None = None
    source_document_type: str | None = None
    source_version_label: str | None = None
    #: El estado de **esa** versión del material. Una versión `superseded` es material que ya se
    #: sustituyó, y eso cambia por completo lo que se puede concluir de la clave.
    source_version_status: str | None = None
    notes: str | None = None


@dataclass(frozen=True, slots=True)
class NotesContrastView:
    """Lo que contestan los apuntes de esta pregunta, con la frase que lo demuestra.

        Es la comprobación del motor (`question_note_anchors`) tal cual: la letra que dieron los
    apuntes,
        las letras que esperaba la clave, el desenlace y la frase verificada. `topic_code` y
        `anchor`
    son
        lo que permite abrir el párrafo exacto en lugar de la pantalla del tema.
    """

    answer_letter: str | None
    expected_letters: tuple[str, ...]
    result: str | None
    phrase: str | None
    anchor: str
    section_title: str | None
    topic_code: str
    topic_title: str
    key_status: str
    checked_at: datetime | None = None
    #: `True` cuando la letra de los apuntes **está** en la clave: entonces no hay nada que discutir
    #: y
    #: la pantalla lo dice, que es la corrección del falso positivo del §2.
    coincides: bool = False


@dataclass(frozen=True, slots=True)
class IncidentBriefView:
    """Una incidencia que cuelga de esta pregunta, con su categoría y su estado.

    Va resumida a propósito —la bandeja completa tiene su pantalla— pero con lo que hace falta para
    decidir aquí: qué categoría es, qué motivo, en qué estado y la frase cuando la hay.
    """

    id: str
    category: str
    reason: str
    status: str
    coverage: str
    detail: str
    phrase: str | None
    topic_code: str
    topic_title: str
    resolution_note: str | None = None
    reviewed_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class ExclusionView:
    """Por qué esta pregunta está **fuera del temario**, cuando lo está.

        Es la marca de `question_curriculum_exclusions`: una pregunta `enunciado_roto` no entra en
        ningún test, así que saber que la ficha que se está mirando es una de esas —y por qué— es
        parte
    de
        lo que hay que ver antes de tocar nada.
    """

    reason: str
    note: str | None
    actor: str
    created_at: datetime


@dataclass(frozen=True, slots=True)
class QuestionVersionBriefView:
    """Una versión de la pregunta, para el historial.

    El historial es lo que hace que marcar la correcta no pierda nada: la versión anterior sigue
    aquí, con su fecha y su motivo. Se enseña del más nuevo al más viejo.
    """

    id: str
    version_no: int
    status: str
    stem: str
    note: str | None
    created_at: datetime | None
    option_count: int
    #: Las letras que esa versión tenía como respuesta correcta en su plantilla, si se puede saber.
    correct_option_keys: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class AnswerKeyVersionBriefView:
    """Una plantilla del conjunto, con **lo que decía de esta pregunta**.

    Es el otro historial: el de la clave. Cambiar la respuesta correcta crea una plantilla nueva y
    deja la anterior `superseded`, y las dos se ven aquí con la letra que cada una daba a **esta**
    pregunta. Sin esta lista, «no se pisa la anterior» sería una promesa y no un hecho que se pueda
    comprobar en la pantalla.
    """

    id: str
    version_no: int
    status: str
    approved_at: datetime | None
    created_at: datetime | None
    source_document_title: str | None
    correct_option_keys: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ProtectedSetView:
    """Un conjunto cuya clave no se toca, y por qué.

        La pantalla enseña **la lista**, no solo el veredicto: con diez conjuntos protegidos en la
        base,
        «esta clave es oficial» sin decir cuáles son obliga a adivinar cuál estorba. `reason` es el
    texto
        del dominio (`protege_cambiar_la_clave`), el mismo que se lee al intentarlo.
    """

    id: str
    title: str
    set_type: str
    source_document_title: str | None
    reason: str


@dataclass(frozen=True, slots=True)
class ProtectionView:
    """Si **esta** pregunta se puede tocar, y la lista de las que no."""

    protected: bool
    reason: str | None
    sets: tuple[ProtectedSetView, ...] = ()


@dataclass(frozen=True, slots=True)
class RepairOptionView:
    """La reparación que una regla puede hacerle a esta pregunta, si hay alguna.

        `reglas` son las claves del vocabulario del dominio y `titulos` su nombre en la pantalla;
        viajan
        las dos porque la primera es el dato que se escribe en la auditoría y la segunda es lo que
        se
    lee.
    """

    reglas: tuple[str, ...]
    titulos: tuple[str, ...]
    detalle: str
    stem: str | None
    opciones: tuple[str, ...] | None
    #: Por qué **no** se puede reparar, cuando la pregunta está señalada y no hay regla que valga.
    por_que_no: str | None = None


@dataclass(frozen=True, slots=True)
class QuestionFileView:
    """La ficha entera: la pregunta, su clave y de dónde sale, los apuntes, y qué se puede hacer."""

    question_version_id: str
    question_set_id: str
    set_title: str
    set_type: str
    set_distribution: str
    stable_key: str
    version_no: int
    position: int
    question_type: str
    status: str
    origin_type: str
    is_reserve: bool
    reserve_order: int | None
    created_at: datetime | None
    note: str | None
    stem: str
    options: tuple[OptionView, ...]
    #: La clave que manda hoy. `None` cuando la pregunta no tiene ninguna: se dice, no se inventa.
    key: KeyProvenanceView | None
    #: La fiabilidad de la clave del conjunto (`fiable`/`dudosa`/`no_fiable`). `None` cuando la
    #: columna del §1 todavía no existe en esta base: **no se recalcula aquí**, porque sería una
    #: segunda verdad sobre lo mismo.
    key_reliability: str | None
    reliability_source: str
    #: Lo que contestaron los apuntes: una fila por tema en el que la pregunta está comprobada. Es
    #: una
    #: tupla y no un solo contraste porque una pregunta puede estar en dos temas, y contestarla en
    #: uno
    #: y no en el otro es una información distinta de no contestarla en ninguno.
    notes: tuple[NotesContrastView, ...]
    incidents: tuple[IncidentBriefView, ...]
    exclusion: ExclusionView | None
    protection: ProtectionView
    #: La reparación ofrecida, o el porqué de que no haya ninguna. Nunca es nulo: la ausencia de
    #: reparación **es** la respuesta a «¿se puede arreglar esto?», y con `None` la pantalla tendría
    #: que adivinar la diferencia entre «no hay nada que arreglar» y «no se ha mirado».
    repair: RepairOptionView
    versions: tuple[QuestionVersionBriefView, ...]
    keys: tuple[AnswerKeyVersionBriefView, ...]
    #: La versión que sustituye a esta, cuando la ficha se abrió por una incidencia que apunta a una
    #: versión ya corregida. `None` si esta es la vigente.
    superseded_by: str | None = None
    limitations: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class AnswerKeyMarkOutcome:
    """Lo que devuelve marcar la correcta: la ficha al día y qué plantilla se escribió.

        `key_version_id` es la plantilla **nueva** y `superseded_key_version_id` la que se retiró:
        las
    dos
        viajan porque el hecho que hay que poder comprobar es justo ese, que la anterior no se ha
    pisado.
    """

    file: QuestionFileView
    key_version_id: str
    superseded_key_version_id: str | None
    previous_option_keys: tuple[str, ...]
    correct_option_keys: tuple[str, ...]
    moved_versions: bool
    actor: str


@dataclass(frozen=True, slots=True)
class RepairOutcome:
    """Lo que devuelve reparar: la ficha al día y qué se ha hecho con la pregunta.

        `moved_topics`, `moved_anchors` y `moved_exclusion` dicen cuántas cosas **viajaron** a la
    versión
        nueva. Viajan para que reparar un enunciado no saque la pregunta de su tema: si estos
        números
        salieran en cero sin querer, la pregunta habría dejado de contar en el temario y en la
        cobertura
    de
        los apuntes, y eso es un cambio mucho mayor que quitarle una referencia al enunciado.
    """

    file: QuestionFileView
    new_question_version_id: str
    superseded_question_version_id: str
    reglas: tuple[str, ...]
    key_version_id: str | None
    moved_topics: int
    moved_anchors: int
    moved_exclusion: bool
    actor: str
    #: Cuántas incidencias de la bandeja se han despachado como resueltas por esta reparación.
    dispatched_incidents: int = 0


__all__ = [
    "AnswerKeyMarkOutcome",
    "AnswerKeyVersionBriefView",
    "ExclusionView",
    "IncidentBriefView",
    "KeyProvenanceView",
    "NotesContrastView",
    "OptionView",
    "ProtectedSetView",
    "ProtectionView",
    "QuestionFileView",
    "QuestionVersionBriefView",
    "RepairOptionView",
    "RepairOutcome",
]
