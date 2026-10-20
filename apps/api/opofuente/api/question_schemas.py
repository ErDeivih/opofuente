"""DTO del banco de preguntas (08_API-CONTRACT §9).

Dos cosas que se ven en los esquemas y son decisiones, no formato:

1. **La clave no viaja salvo que se pida.** `QuestionSchema.correct_option_keys` viene vacía en las
   respuestas que no la piden a propósito, y el contrato lo exige para las sesiones no corregidas.
2. **Una corrección local lleva motivo obligatorio.** `LocalCorrectionSchema.note` no tiene valor
   por defecto: si alguien cambia una transcripción oficial, tiene que decir por qué.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

#: De qué administración sale el material de un conjunto (D10, `0037`). El vocabulario vive en el
#: dominio (`OriginScope`) y aquí se declara una vez para el contrato: `age` (Administración General
#: del Estado), `otra_administracion` (queda fuera de un simulacro) y `desconocida` (por defecto).
OriginScopeName = Literal["age", "otra_administracion", "desconocida"]


class QuestionSetSchema(BaseModel):
    id: str
    title: str
    set_type: Literal["official_exam", "private_bank", "practice", "generated_batch"]
    status: Literal["draft", "confirmed", "archived"]
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
    is_official: bool = False
    #: `personal` (material del propietario) o `public` (publicable). Nunca nulo: el conjunto
    #: siempre dice quién puede verlo, y por defecto lo dice «solo su dueño».
    distribution: Literal["personal", "public"] = "personal"
    #: De qué administración sale el material (D10). Nunca nulo: un conjunto sin procedencia
    #: declarada dice `desconocida`, que es la respuesta honesta y la que no excluye de nada.
    origin_scope: OriginScopeName = "desconocida"


class QuestionSetPageSchema(BaseModel):
    sets: list[QuestionSetSchema]
    total: int
    limit: int
    offset: int


class CreateQuestionSetSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=300)
    opposition_id: str = Field(min_length=1)
    set_type: Literal["official_exam", "private_bank", "practice", "generated_batch"]
    convocation_version_id: str | None = None
    model_code: str | None = Field(default=None, max_length=8)
    held_at: date | None = None
    source_document_version_id: str | None = None
    #: La procedencia se declara al crear el conjunto cuando se sabe —el importador del INAP sabe
    #: que sus exámenes son de la AGE—. Si no se dice, `desconocida`.
    origin_scope: OriginScopeName = "desconocida"


class PatchQuestionSetSchema(BaseModel):
    """Lo que se puede cambiar de un conjunto sin tocar su contenido.

    La **visibilidad** (un conjunto nace `personal` y se hace `public` a propósito, uno a uno) y la
    **procedencia** (`origin_scope`, que es lo que deja el material de otra administración fuera de
    un simulacro). Nada más se cambia por aquí — el título y el tipo son la identidad del conjunto,
    y reescribirlos rompería la trazabilidad de las preguntas que cuelgan de él.

    Los dos campos son opcionales pero **al menos uno** tiene que venir: un `PATCH` que no cambia
    nada es un error de quien llama, no una operación correcta.
    """

    model_config = ConfigDict(extra="forbid")

    distribution: Literal["personal", "public"] | None = None
    origin_scope: OriginScopeName | None = None

    @model_validator(mode="after")
    def _algo_que_cambiar(self) -> PatchQuestionSetSchema:
        if self.distribution is None and self.origin_scope is None:
            raise ValueError(
                "el cambio no dice nada: `distribution` u `origin_scope`, uno al menos"
            )
        return self


class OptionSchema(BaseModel):
    id: str
    stable_key: str
    label: str | None = None
    text: str
    position: int


class QuestionSchema(BaseModel):
    id: str
    question_set_id: str
    stable_key: str
    version_no: int
    stem: str
    question_type: Literal["single_choice", "multi_mark_error", "true_false", "free_text_reference"]
    position: int
    status: Literal["incomplete", "complete", "verified", "conflicting", "annulled", "superseded"]
    origin_type: Literal["official", "private", "generated"]
    is_reserve: bool = False
    reserve_order: int | None = None
    source_section_id: str | None = None
    supersedes_id: str | None = None
    created_at: datetime | None = None
    #: Motivo de la corrección local: quien lee la pregunta tiene que ver por qué cambió.
    note: str | None = None
    #: Las listas son **obligatorias** aunque puedan estar vacías: el servidor siempre las calcula,
    #: y declararlas opcionales obligaría a cada cliente a defenderse de un caso que no ocurre.
    options: list[OptionSchema]
    correct_option_keys: list[str]
    key_outcome: Literal["keyed", "annulled", "unanswered", "conflicting"] | None = None
    explanation_count: int = 0


class QuestionPageSchema(BaseModel):
    questions: list[QuestionSchema]
    total: int
    limit: int
    offset: int


class PatchQuestionSchema(BaseModel):
    """Cambia lo que se puede cambiar sin tocar el texto importado: una corrección es otra cosa."""

    model_config = ConfigDict(extra="forbid")

    stem: str | None = Field(default=None, min_length=1)
    question_type: (
        Literal["single_choice", "multi_mark_error", "true_false", "free_text_reference"] | None
    ) = None
    position: int | None = Field(default=None, ge=1)
    is_reserve: bool | None = None
    reserve_order: int | None = Field(default=None, ge=1)


class LocalCorrectionSchema(BaseModel):
    """Corrección local de una transcripción: **con motivo** y sin tocar el original importado."""

    model_config = ConfigDict(extra="forbid")

    note: str = Field(min_length=3, max_length=1000)
    stem: str | None = Field(default=None, min_length=1)
    options: list[str] | None = None


class CsvMappingSchema(BaseModel):
    stem: str = "stem"
    options: list[str] = Field(
        default_factory=lambda: ["option_a", "option_b", "option_c", "option_d"]
    )
    correct: str | None = "correct"
    explanation: str | None = "explanation"
    topic: str | None = "topic"
    source: str | None = "source"
    tags: str | None = "tags"
    position: str | None = None
    reserve: str | None = None


class ParseQuestionSetSchema(BaseModel):
    """Lo que se pide al importar: preguntas de un texto, un CSV, un JSON o una plantilla suelta."""

    model_config = ConfigDict(extra="forbid")

    kind: Literal["questions", "answer_key", "csv", "json"] = "questions"
    text: str = Field(min_length=1)
    mapping: CsvMappingSchema | None = None
    source_document_version_id: str | None = None


class RejectedRowSchema(BaseModel):
    row_number: int
    cause: str
    detail: str


class ParseIssueSchema(BaseModel):
    line: int
    code: str
    detail: str


class DuplicateGroupSchema(BaseModel):
    kind: Literal["same_question", "reordered_options", "similar"]
    members: list[str]
    conflicting_keys: bool = False
    keys_seen: list[str]
    can_merge: bool = False


class QuestionImportReportSchema(BaseModel):
    """Lo que ha pasado al importar: ni una fila se pierde, ni un conflicto se esconde.

    Se llama `QuestionImportReport` y no `ImportReport` porque la ingestión ya tiene su propio
    `ImportReportSchema` (el cuadre del lote): dos modelos con el mismo nombre obligan a FastAPI a
    inventar nombres cualificados en el OpenAPI y rompen los tipos derivados del contrato.
    """

    set_id: str
    created: int = 0
    existing: int = 0
    incomplete: int = 0
    with_key: int = 0
    key_entries: int = 0
    keys_in_conflict: int = 0
    #: Preguntas que quedaron **catalogadas por bloque y tema** al heredar el programa del documento
    #: del que salen (S12.6). Sin ese mapeo, el diagnóstico por temas no las vería.
    mapped_to_topics: int = 0
    #: Preguntas con tema asignado desde la columna `topic` del CSV (o el campo del JSON).
    #: `mapped_to_topics` es otra cosa: lo que catalogó la aplicación sola.
    topics_from_column: int = 0
    #: Listas obligatorias: «sin filas rechazadas» se dice con una lista vacía, no con un ausente.
    rejected: list[RejectedRowSchema]
    issues: list[ParseIssueSchema]
    duplicates: list[DuplicateGroupSchema]
    missing_columns: list[str]
    ignored_columns: list[str]
    unmatched_positions: list[int]
    model_code_detected: str | None = None
    key_id: str | None = None
    #: Rótulos de parte vistos en el material. Se declaran y **no** se guardan por pregunta
    #: (ADR-014): lo que no se hace es perderlos en silencio (DEBT-010, criterio 3).
    parts_detected: list[str] = Field(default_factory=list)
    #: Citas creadas al importar desde un documento: el enlace pregunta↔fragmento (DEBT-010).
    evidence_links: int = 0
    #: Explicaciones **por opción** guardadas al importar (S12.7): el material las traía y se dice.
    option_explanations: int = 0


class ImportQuestionsFromDocumentSchema(BaseModel):
    """Importar las preguntas de una **versión de documento** (DEBT-010)."""

    model_config = ConfigDict(extra="forbid")

    document_version_id: str = Field(min_length=1)


class KeyEntrySchema(BaseModel):
    question_version_id: str
    outcome: Literal["keyed", "annulled", "unanswered", "conflicting"]
    correct_option_keys: list[str] = Field(default_factory=list)
    notes: str | None = None


class AnswerKeySchema(BaseModel):
    id: str
    question_set_id: str
    version_no: int
    status: Literal["draft", "active", "superseded", "rejected"]
    source_document_version_id: str | None = None
    supersedes_id: str | None = None
    published_at: date | None = None
    approved_at: datetime | None = None
    created_at: datetime | None = None
    entries: list[KeyEntrySchema]


class MarkKeySupersedesRequestSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    superseded_id: str = Field(min_length=1)


class LinkKeySourceRequestSchema(BaseModel):
    """La versión de documento que es la plantilla oficial de la clave (`null` desenlaza)."""

    model_config = ConfigDict(extra="forbid")

    source_document_version_id: str | None = Field(default=None, min_length=1)


class KeySourceLinkSchema(BaseModel):
    """Lo que se comparó al enlazar: la plantilla, pregunta a pregunta, contra la clave."""

    key: AnswerKeySchema
    lines: int
    agreeing: int
    disagreeing: int
    without_entry: int
    ambiguous: int
    key_entries: int


class IssueReportRequestSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: Literal["ambiguous", "wrong_key", "typo", "outdated", "other"]
    detail: str = Field(min_length=3, max_length=2000)


class IssueReportSchema(BaseModel):
    id: str
    question_version_id: str
    kind: Literal["ambiguous", "wrong_key", "typo", "outdated", "other"]
    detail: str
    status: Literal["open", "reviewed", "dismissed"]
    created_at: datetime | None = None


class ExplanationSchema(BaseModel):
    """Explicación de una pregunta entera o de una de sus opciones (07_UI-UX §7, S12.7).

    `option_stable_key` nulo es «la pregunta entera»; con valor, es la explicación de esa opción
    («por qué la b no vale»). El origen y el estado no son adorno: una explicación generada por un
    modelo queda en borrador y se dice con qué modelo se escribió.
    """

    id: str
    question_version_id: str
    option_stable_key: str | None = None
    text: str
    origin: Literal["official", "private", "generated"]
    status: Literal["draft", "reviewed", "rejected"]
    model_name: str | None = None
    created_at: datetime | None = None
    #: La frase LITERAL de los apuntes que sostiene la explicación, para enseñarla tal cual.
    citation: str | None = None
    #: El apartado al que se ancla: la pantalla lleva al párrafo con este id.
    note_anchor_id: str | None = None


class ExplanationTrayItemSchema(BaseModel):
    """Una fila de la bandeja de revisión: la explicación **y la pregunta a la que pertenece**.

    No es `ExplanationSchema` con dos campos más: **aquí la pregunta es el contexto y tiene que
    venir dentro**, porque el propietario aprueba una explicación **sabiendo de qué pregunta es**.
    Servirla suelta obligaría a abrir otra pantalla por cada fila, que es lo que la bandeja existe
    para evitar.

    `options` no viene: quien revisa abre la ficha de la pregunta, y **la bandeja no repite la
    pregunta entera** — su trabajo es decidir si la explicación sirve, no volver a leer el examen.
    """

    explanation: ExplanationSchema
    #: La versión de la pregunta: el id con el que se abre su ficha si hace falta.
    question_version_id: str
    stem: str


class SetExplanationRequestSchema(BaseModel):
    """Escribir (o sustituir) la explicación de una pregunta o de una de sus opciones."""

    model_config = ConfigDict(extra="forbid")

    text: str = Field(min_length=1, max_length=4000)
    option_stable_key: str | None = Field(default=None, max_length=16)


class QuestionEvidenceSchema(BaseModel):
    span_id: str
    role: Literal["stem", "correct", "distractor", "explanation"]
    claim: str | None = None
    status: Literal["proposed", "accepted", "rejected"]
    text: str
    page: int | None = None
    citation_label: str | None = None
    document_version_id: str
    section_id: str | None = None


class CorrectionOutcomeSchema(BaseModel):
    """La versión corregida y, si la tenía, la plantilla nueva que apunta a ella."""

    question: QuestionSchema
    key_id: str | None = None


class QuestionTopicSchema(BaseModel):
    """Un tema del programa asignado a una pregunta, con el estado de su mapeo.

    `status` viaja a propósito: `accepted` es un tema decidido y `provisional` es lo que propuso un
    motor sin que nadie lo haya confirmado. El panel tiene que poder distinguirlos, y el diagnóstico
    por temas solo cuenta lo aceptado.
    """

    mapping_id: str
    question_version_id: str
    curriculum_node_id: str
    official_code: str
    title: str
    status: Literal["provisional", "accepted", "rejected"]
    confidence: float = 1.0
    created_at: datetime | None = None


class QuestionTopicAssignmentSchema(QuestionTopicSchema):
    """El mapeo y si **esta** llamada lo creó.

    `created` es lo que hace utilizable una ruta idempotente: reintentar la clasificación de un lote
    entero no puede confundir «lo asigné yo ahora» con «ya estaba asignado».

    `promoted` es la tercera cosa que puede pasar, y la que necesita la cola de revisión: el mapeo
    ya estaba, pero como **propuesta**, y esta llamada la ha confirmado. No es «creado» —la fila
    existía— ni «ya estaba» —algo se ha escrito y queda auditado—.

    `epigraph` viaja cuando se pidió asignar también un epígrafe: se asigna con su tema, y decir
    solo el tema escondería la mitad de lo que se ha escrito.

    `retired` son las propuestas **de esa pregunta** que se han retirado en la misma operación: una
    pregunta no puede quedarse con dos temas propuestos cuando uno se acepta, y quien decide tiene
    que ver que las demás ya no están.
    """

    created: bool
    promoted: bool = False
    epigraph: QuestionTopicAssignmentSchema | None = None
    retired: int = 0


class AssignTopicRequestSchema(BaseModel):
    """Asignar un tema a una pregunta.

    `actor` distingue quién lo hace y no es adorno: la clasificación automática de miles de
    preguntas tiene que quedar identificada en la auditoría, y `local` es la persona que está.
    `reason` es el motivo y va a la auditoría, que es donde se lee por qué se clasificó así.
    """

    model_config = ConfigDict(extra="forbid")

    curriculum_node_id: str = Field(min_length=1, max_length=36)
    #: Epígrafe del tema, si se sabe. Se escribe **además** del tema, nunca en su lugar.
    epigraph_node_id: str | None = Field(default=None, min_length=1, max_length=36)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    actor: str | None = Field(default=None, min_length=1, max_length=64)
    reason: str | None = Field(default=None, max_length=500)


#: Los motivos por los que una pregunta no es materia del programa vigente. Es el vocabulario de
#: `domain.topic_classification.OutOfSyllabus` y se declara aquí para que el contrato lo publique.
ExclusionReasonName = Literal["otra_administracion", "enunciado_roto"]


class QuestionExclusionSchema(BaseModel):
    """Una pregunta declarada fuera del temario, con su motivo.

    No lleva código de tema ni nodo: **no es un mapeo**, y por eso no se puede confundir con uno.
    Sí lleva el enunciado, que es lo que permite juzgar si la marca estaba bien puesta; al escribir
    la marca va nulo, porque ahí no hay nada que revisar.
    """

    question_version_id: str
    reason: ExclusionReasonName
    actor: str
    note: str | None = None
    created_at: datetime | None = None
    stem: str | None = None


class QuestionExclusionPageSchema(BaseModel):
    """La cola de fuera de temario: las marcas de una página y cuántas hay en total.

    `totals_by_reason` cuenta **cada** motivo en la base, sin mirar el filtro de la petición: es lo
    que permite que la sección «No son preguntas» del panel (F16, decisión D6) diga cuántos
    enunciados rotos hay sin leerlos para contarlos. Un motivo sin ninguna marca no aparece.
    """

    exclusions: list[QuestionExclusionSchema]
    total: int
    limit: int
    offset: int
    totals_by_reason: dict[str, int] = Field(default_factory=dict)


class ProgrammeNodeRefSchema(BaseModel):
    """Un nodo del programa dentro de una propuesta: sus dos códigos y su título.

    `official_code` es el número que publica la convocatoria («1») y `path` la posición legible del
    árbol («I.1»), que es la que el propietario reconoce en la pantalla.
    """

    node_id: str
    official_code: str
    path: str
    title: str


class QuestionTopicProposalSchema(BaseModel):
    """Un tema candidato para una pregunta, sin confirmar, con sus epígrafes propuestos.

    No lleva la pregunta dentro: la pregunta es la tarjeta (`QuestionTopicProposalsSchema`) y esto
    es una de las respuestas que la máquina le dio.
    """

    mapping_id: str
    topic: ProgrammeNodeRefSchema
    #: Puede haber más de uno: el mismo tema puede traer varios epígrafes propuestos.
    epigraphs: list[ProgrammeNodeRefSchema]
    confidence: float
    reason: str | None = None
    created_at: datetime | None = None


class QuestionTopicProposalsSchema(BaseModel):
    """Una pregunta de la cola con **todas** sus propuestas juntas: una tarjeta, no una por mapeo.

    Es la unidad con la que se despacha: el propietario decide sobre la pregunta —«esta pregunta es
    del tema X»—, así que el mismo enunciado no puede salir dos veces. `accepted` va aparte de
    `proposals`: si la pregunta ya tiene tema decidido, ese manda y lo que queda son propuestas que
    se retiran.
    """

    question_version_id: str
    question_set_id: str
    set_title: str
    stem: str
    options: list[OptionSchema]
    accepted: ProgrammeNodeRefSchema | None = None
    proposals: list[QuestionTopicProposalSchema]


class QuestionTopicProposalPageSchema(BaseModel):
    """La cola de propuestas, contada en **preguntas** (tarjetas): las de una página y el total."""

    questions: list[QuestionTopicProposalsSchema]
    total: int
    limit: int
    offset: int


class ConflictingTopicSchema(BaseModel):
    """Un tema ya decidido de una pregunta que tiene más de uno, con quién lo decidió.

    `actor` viaja porque cambia cómo se mira: uno heredado de una migración (`local`) y uno
    propuesto por el modelo (`llm:…`) no se juzgan igual. Nulo es «no consta en la auditoría», que
    también hay que poder decir en lugar de inventarse un autor.
    """

    mapping_id: str
    topic: ProgrammeNodeRefSchema
    confidence: float
    actor: str | None = None
    created_at: datetime | None = None


class QuestionTopicConflictSchema(BaseModel):
    """Una pregunta que cuenta en **dos temas aceptados** a la vez, con los dos delante.

    Es la otra cara de la cola: allí se revisa lo que nadie ha decidido y aquí lo que quedó decidido
    dos veces. Una pregunta en dos temas cuenta en los dos agregados, así que hay que poder dejarla
    con uno —eligiendo cuál— sin que la aplicación decida por su cuenta.
    """

    question_version_id: str
    question_set_id: str
    set_title: str
    stem: str
    options: list[OptionSchema]
    topics: list[ConflictingTopicSchema]


class QuestionTopicConflictPageSchema(BaseModel):
    """Las preguntas en dos temas de una página, y cuántas hay en total."""

    questions: list[QuestionTopicConflictSchema]
    total: int
    limit: int
    offset: int


class BulkTopicAssignmentSchema(BaseModel):
    """Una fila del lote: o un tema (con su epígrafe, si se sabe) o un fuera de temario.

    Las dos formas son excluyentes y se comprueba: una fila que dijera las dos cosas dejaría la
    pregunta clasificada y sin clasificar a la vez, y una que no dijera ninguna no pide nada.

    `status` es opcional **a propósito**, y su ausencia significa algo: una fila sin `status` no
    toca lo que ya existe (crear si falta, y nada más), que es lo que necesita una clasificación por
    lotes que se reintenta. Una fila **con** `status` dice qué tiene que quedar: si la pregunta ya
    tenía una propuesta (`provisional`) a ese tema, se confirma —o se vuelve a proponer— y eso queda
    auditado. Es lo que hace el propietario al despachar la cola desde la pantalla de revisión, y
    por eso la confirmación viaja en el lote: no una petición por pregunta.
    """

    model_config = ConfigDict(extra="forbid")

    question_version_id: str = Field(min_length=1, max_length=36)
    curriculum_node_id: str | None = Field(default=None, min_length=1, max_length=36)
    epigraph_node_id: str | None = Field(default=None, min_length=1, max_length=36)
    exclusion_reason: ExclusionReasonName | None = None
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    reason: str | None = Field(default=None, max_length=500)
    #: `provisional` guarda una propuesta (la cola), `accepted` la decide. Nulo: no cambia nada
    #: de lo que ya haya; solo escribe si el mapeo no existía.
    status: Literal["provisional", "accepted"] | None = None
    #: Al decidir una fila, retirar las demás propuestas de esa pregunta. Es lo que impide que una
    #: pregunta con dos propuestas —de dos corridas que se pisaron— acabe con dos temas aceptados.
    #: Lo pide la pantalla de revisión; el clasificador no, y no le hace falta: solo escribe
    #: preguntas que no tienen ninguna propuesta.
    retire_others: bool = False


class BulkTopicAssignmentsSchema(BaseModel):
    """Un lote de asignaciones con **un** actor.

    El actor va en el sobre y no en cada fila: un lote lo firma quien lo manda, y repetirlo 200
    veces solo sirve para que alguna fila diga otra cosa que las demás por error.
    """

    model_config = ConfigDict(extra="forbid")

    actor: str | None = Field(default=None, min_length=1, max_length=64)
    assignments: list[BulkTopicAssignmentSchema] = Field(min_length=1, max_length=200)


class BulkTopicAssignmentResultSchema(BaseModel):
    """Qué ha pasado con **una** fila del lote.

    `outcome` es el vocabulario que hace utilizable el reintento: `created` (esta llamada lo creó),
    `existing` (ya estaba tal cual), `promoted` (ya estaba como **propuesta** y esta llamada la ha
    confirmado), `excluded` (marcada fuera de temario ahora), `already_excluded` (ya lo estaba) y
    `error` (la fila no se pudo aplicar, con el motivo en `detail`). Una fila mala **no** tumba el
    lote: se dice cuál y por qué.

    `promoted` y `created` son distintos a propósito: la cola de revisión se despacha confirmando
    propuestas, y un informe que contara las confirmaciones como «ya estaban» dejaría al propietario
    sin saber si su decisión se aplicó.
    """

    question_version_id: str
    outcome: Literal["created", "existing", "promoted", "excluded", "already_excluded", "error"]
    assignment: QuestionTopicAssignmentSchema | None = None
    exclusion: QuestionExclusionSchema | None = None
    detail: str | None = None


class BulkTopicAssignmentReportSchema(BaseModel):
    """El lote entero: cada fila con su desenlace y los totales por desenlace."""

    results: list[BulkTopicAssignmentResultSchema]
    created: int = 0
    existing: int = 0
    promoted: int = 0
    excluded: int = 0
    already_excluded: int = 0
    errors: int = 0
