"""Modelos de lectura del banco de preguntas (S06): conjuntos, preguntas, opciones y claves.

La clave de una pregunta **no** viaja por defecto: `QuestionView.correct_option_keys` viene vacía
salvo que se pida explícitamente. El contrato §9 lo exige para las sesiones no corregidas («no
devolver claves ni explicaciones en el payload de pregunta de una sesión no corregida»), y la forma
más segura de cumplirlo es que el valor por defecto sea no llevarla: quien la necesite —el banco, el
editor— lo pide a propósito.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime

from opofuente.domain.questions import ParseIssue, QuestionDuplicateGroup


@dataclass(frozen=True, slots=True)
class OptionView:
    id: str
    stable_key: str
    text: str
    position: int
    label: str | None = None


@dataclass(frozen=True, slots=True)
class QuestionView:
    """Una pregunta con sus opciones y, si se ha pedido, su clave."""

    id: str
    question_set_id: str
    stable_key: str
    version_no: int
    stem: str
    question_type: str
    position: int
    status: str
    origin_type: str
    is_reserve: bool = False
    reserve_order: int | None = None
    source_section_id: str | None = None
    supersedes_id: str | None = None
    created_at: datetime | None = None
    #: Motivo de la corrección local, cuando esta versión es una corrección.
    note: str | None = None
    options: tuple[OptionView, ...] = ()
    correct_option_keys: tuple[str, ...] = ()
    key_outcome: str | None = None
    explanation_count: int = 0

    @property
    def has_key(self) -> bool:
        return self.key_outcome is not None

    @property
    def option_count(self) -> int:
        return len(self.options)


@dataclass(frozen=True, slots=True)
class ExplanationView:
    """Explicación de una pregunta entera o de una de sus opciones (S12.7).

    `option_stable_key` nulo significa «la pregunta entera»; con valor, es la explicación de esa
    opción («por qué la b no vale»). El vocabulario está cerrado en la base: `origin` vale
    `official`, `private` o `generated`, y el estado es de borrador hasta que alguien la revisa.
    """

    id: str
    question_version_id: str
    option_stable_key: str | None
    text: str
    origin: str
    status: str
    model_name: str | None = None
    created_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class QuestionSetView:
    """Un conjunto con sus recuentos: es lo que se ve en el listado del banco."""

    id: str
    title: str
    set_type: str
    status: str
    opposition_id: str
    convocation_version_id: str | None = None
    model_code: str | None = None
    held_at: date | None = None
    source_document_version_id: str | None = None
    created_at: datetime | None = None
    question_count: int = 0
    reserve_count: int = 0
    incomplete_count: int = 0
    key_count: int = 0
    active_key_id: str | None = None

    @property
    def is_official(self) -> bool:
        return self.set_type == "official_exam"


@dataclass(frozen=True, slots=True)
class QuestionPage:
    questions: tuple[QuestionView, ...]
    total: int
    limit: int
    offset: int


@dataclass(frozen=True, slots=True)
class QuestionSetPage:
    sets: tuple[QuestionSetView, ...]
    total: int
    limit: int
    offset: int


@dataclass(frozen=True, slots=True)
class KeyEntryView:
    question_version_id: str
    outcome: str
    correct_option_keys: tuple[str, ...] = ()
    notes: str | None = None


@dataclass(frozen=True, slots=True)
class AnswerKeyView:
    id: str
    question_set_id: str
    version_no: int
    status: str
    source_document_version_id: str | None = None
    supersedes_id: str | None = None
    published_at: date | None = None
    approved_at: datetime | None = None
    created_at: datetime | None = None
    entries: tuple[KeyEntryView, ...] = ()

    @property
    def is_active(self) -> bool:
        return self.status == "active"

    @property
    def entry_count(self) -> int:
        return len(self.entries)


@dataclass(frozen=True, slots=True)
class SaveQuestionsOutcome:
    """Qué pasó al guardar un lote de preguntas: ni una se pierde en silencio."""

    created: int = 0
    existing: int = 0
    incomplete: int = 0
    question_ids: tuple[str, ...] = field(default_factory=tuple)

    @property
    def total(self) -> int:
        return self.created + self.existing


@dataclass(frozen=True, slots=True)
class CsvColumnMapping:
    """Qué columna del CSV es cada cosa (04_INGESTION §10: «el importador permite mapear columnas»).

    Los nombres por defecto son los que propone la spec (`stem`, `option_a`.., `correct`,
    `explanation`, `topic`, `source`, `tags`), pero el asistente acepta los que traiga el fichero:
    una hoja real casi nunca se llama así.
    """

    stem: str = "stem"
    options: tuple[str, ...] = ("option_a", "option_b", "option_c", "option_d")
    correct: str | None = "correct"
    explanation: str | None = "explanation"
    topic: str | None = "topic"
    source: str | None = "source"
    tags: str | None = "tags"
    position: str | None = None
    reserve: str | None = None

    @property
    def columns(self) -> tuple[str, ...]:
        """Columnas que el mapeo usa: es lo que tiene que traer la cabecera."""
        nombres = [self.stem, *self.options]
        for opcional in (self.correct, self.explanation, self.topic, self.source, self.tags):
            if opcional is not None and opcional not in nombres:
                nombres.append(opcional)
        for extra in (self.position, self.reserve):
            if extra is not None and extra not in nombres:
                nombres.append(extra)
        return tuple(nombres)


@dataclass(frozen=True, slots=True)
class RejectedRow:
    """Una fila que no se pudo importar, con su causa: se exporta tal cual, no se tira."""

    row_number: int
    cause: str
    detail: str


@dataclass(frozen=True, slots=True)
class QuestionImportReport:
    """Resultado de una importación: lo que entró, lo que ya estaba y lo que no pudo entrar."""

    set_id: str
    created: int = 0
    existing: int = 0
    incomplete: int = 0
    with_key: int = 0
    key_entries: int = 0
    duplicates: tuple[QuestionDuplicateGroup, ...] = ()
    issues: tuple[ParseIssue, ...] = ()
    rejected: tuple[RejectedRow, ...] = ()
    ignored_columns: tuple[str, ...] = ()
    missing_columns: tuple[str, ...] = ()
    conflicts: tuple[str, ...] = ()
    model_code_detected: str | None = None
    #: Rótulos de parte que el parser ha visto en el material («2», «IV»…). Se **declaran** aquí y
    #: no se guardan por pregunta: el modelo no tiene dónde, y emparejarlos con `exam_parts` sería
    #: adivinar (ADR-014). Lo que no se hace es perderlos en silencio (DEBT-010, criterio 3).
    parts_detected: tuple[str, ...] = ()
    #: Citas creadas al importar desde un documento: es el enlace que antes no existía (DEBT-010).
    evidence_links: int = 0
    #: Explicaciones **por opción** guardadas al importar (S12.7). Se cuentan para que el informe
    #: diga que el material las traía: sin esta cifra, un fichero con «por qué la b no vale» en cada
    #: fila parecería no haber traído nada.
    option_explanations: int = 0
    #: Preguntas a las que la columna de tema (`topic`) dejó asignado un nodo del programa. Sin esta
    #: cifra el informe no decía cuántos temas había aplicado y había que contarlos en la base
    #: (§4.8 del traspaso de octubre de 2026).
    topics_from_column: int = 0

    @property
    def imported(self) -> int:
        return self.created + self.existing

    @property
    def rows_rejected(self) -> int:
        return len(self.rejected)

    @property
    def keys_in_conflict(self) -> int:
        """Preguntas que ya estaban con otra clave: se informan y **no** se fusionan."""
        return len(self.conflicts)


@dataclass(frozen=True, slots=True)
class QuestionEvidenceView:
    """Qué evidencia sostiene una parte de la pregunta, con el texto de la cita."""

    span_id: str
    role: str
    status: str
    text: str
    document_version_id: str
    claim: str | None = None
    page: int | None = None
    citation_label: str | None = None
    section_id: str | None = None


@dataclass(frozen=True, slots=True)
class IssueReportView:
    """Lo que reportó quien estudia sobre una pregunta."""

    id: str
    question_version_id: str
    kind: str
    detail: str
    status: str
    created_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class KeySourceLink:
    """Resultado de enlazar la plantilla oficial con una clave: si se hizo y lo que se comparó."""

    applied: bool
    reason: str | None
    lines: int = 0
    agreeing: int = 0
    disagreeing: int = 0
    without_entry: int = 0
    ambiguous: int = 0
    key_entries: int = 0


@dataclass(frozen=True, slots=True)
class QuestionTopicView:
    """Un tema del programa asignado a una pregunta, con el estado de su mapeo.

    `status` no es adorno: `accepted` es un tema que alguien ha decidido (una persona o la
    catalogación que hereda el programa del documento) y `provisional` es lo que propuso un motor y
    nadie ha confirmado. El panel tiene que poder distinguirlos, y el diagnóstico por temas solo
    cuenta lo aceptado.
    """

    mapping_id: str
    question_version_id: str
    curriculum_node_id: str
    official_code: str
    title: str
    status: str
    confidence: float = 1.0
    created_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class KeyImportReport:
    """Resultado de alinear una plantilla suelta con las preguntas del conjunto."""

    key_id: str | None
    version_no: int | None
    entries: int = 0
    unmatched: tuple[int, ...] = ()
    issues: tuple[ParseIssue, ...] = ()

    @property
    def applied(self) -> bool:
        return self.key_id is not None


__all__ = [
    "AnswerKeyView",
    "CsvColumnMapping",
    "IssueReportView",
    "KeyEntryView",
    "KeyImportReport",
    "KeySourceLink",
    "OptionView",
    "QuestionEvidenceView",
    "QuestionImportReport",
    "QuestionPage",
    "QuestionSetPage",
    "QuestionSetView",
    "QuestionTopicView",
    "QuestionView",
    "RejectedRow",
    "SaveQuestionsOutcome",
]
