"""Rutas del banco de preguntas (08_API-CONTRACT §9).

Dos reglas que se aplican aquí y no en el cliente:

- **el banco enseña la clave** (es lo que se está revisando) y las sesiones no: por eso estas rutas
  piden las preguntas con clave, y el valor por defecto del servicio no la lleva;
- **una corrección local lleva motivo** y crea versión nueva: el texto importado no se reescribe.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Header, Query

from opofuente.api.deps import AutoStudyServiceDep, QuestionServiceDep
from opofuente.api.error_responses import (
    CONFLICT_WRITE_ERRORS,
    INGESTION_WRITE_ERRORS,
    RESOURCE_ERRORS,
    WRITE_ERRORS,
)
from opofuente.api.question_schemas import (
    AnswerKeySchema,
    AssignTopicRequestSchema,
    BulkTopicAssignmentReportSchema,
    BulkTopicAssignmentResultSchema,
    BulkTopicAssignmentSchema,
    BulkTopicAssignmentsSchema,
    ConflictingTopicSchema,
    CorrectionOutcomeSchema,
    CreateQuestionSetSchema,
    CsvMappingSchema,
    DuplicateGroupSchema,
    ExplanationSchema,
    ImportQuestionsFromDocumentSchema,
    IssueReportRequestSchema,
    IssueReportSchema,
    KeyEntrySchema,
    KeySourceLinkSchema,
    LinkKeySourceRequestSchema,
    LocalCorrectionSchema,
    MarkKeySupersedesRequestSchema,
    OptionSchema,
    ParseIssueSchema,
    ParseQuestionSetSchema,
    PatchQuestionSchema,
    PatchQuestionSetSchema,
    ProgrammeNodeRefSchema,
    QuestionEvidenceSchema,
    QuestionExclusionPageSchema,
    QuestionExclusionSchema,
    QuestionImportReportSchema,
    QuestionPageSchema,
    QuestionSchema,
    QuestionSetPageSchema,
    QuestionSetSchema,
    QuestionTopicAssignmentSchema,
    QuestionTopicConflictPageSchema,
    QuestionTopicConflictSchema,
    QuestionTopicProposalPageSchema,
    QuestionTopicProposalSchema,
    QuestionTopicProposalsSchema,
    QuestionTopicSchema,
    RejectedRowSchema,
    SetExplanationRequestSchema,
)
from opofuente.application.question_models import (
    AnswerKeyView,
    CsvColumnMapping,
    ExplanationView,
    IssueReportView,
    OptionView,
    ProgrammeNodeRef,
    QuestionEvidenceView,
    QuestionExclusionOutcome,
    QuestionExclusionView,
    QuestionImportReport,
    QuestionPage,
    QuestionSetPage,
    QuestionSetView,
    QuestionTopicConflictView,
    QuestionTopicProposalsView,
    QuestionTopicView,
    QuestionView,
    TopicAssignment,
    TopicAssignmentBatch,
    TopicAssignmentRequest,
    TopicAssignmentRow,
    TopicProposalView,
)
from opofuente.domain.errors import ClassificationConflictError, NotFoundError
from opofuente.domain.questions import Origin, QuestionDuplicateGroup
from opofuente.domain.topic_classification import OutOfSyllabus

router = APIRouter(tags=["preguntas"])

#: Cuántas cosas se devuelven de una vez si la petición no dice otra cosa.
DEFAULT_LIMIT = 50

#: Cabecera con la que una herramienta se identifica sin tocar el cuerpo. La usa la clasificación
#: automática, que asigna miles de temas seguidos: pasar el actor en cada cuerpo sería repetirlo.
TOPIC_ACTOR_HEADER = "X-OpoFuente-Actor"

#: Quién hace el cambio si nadie lo dice: una persona en esta máquina.
DEFAULT_ACTOR = "local"


def _topic_actor(*, declared: str | None, header: str | None) -> str:
    """Quién ha pedido el cambio, para que la auditoría lo diga.

    Manda lo declarado en el cuerpo (viaja en el propio contrato y es lo más explícito); si no, la
    cabecera `X-OpoFuente-Actor`; si no, `local`. Un actor en blanco se ignora: en la auditoría es
    mejor «local» que un hueco.
    """
    elegido = (declared or header or "").strip()
    return elegido or DEFAULT_ACTOR


def _set(view: QuestionSetView) -> QuestionSetSchema:
    return QuestionSetSchema(
        id=view.id,
        title=view.title,
        set_type=view.set_type,  # type: ignore[arg-type]
        status=view.status,  # type: ignore[arg-type]
        opposition_id=view.opposition_id,
        convocation_version_id=view.convocation_version_id,
        model_code=view.model_code,
        held_at=view.held_at,
        source_document_version_id=view.source_document_version_id,
        created_at=view.created_at,
        question_count=view.question_count,
        reserve_count=view.reserve_count,
        incomplete_count=view.incomplete_count,
        key_count=view.key_count,
        active_key_id=view.active_key_id,
        is_official=view.is_official,
        distribution=view.distribution,  # type: ignore[arg-type]
    )


def _page(view: QuestionSetPage) -> QuestionSetPageSchema:
    return QuestionSetPageSchema(
        sets=[_set(conjunto) for conjunto in view.sets],
        total=view.total,
        limit=view.limit,
        offset=view.offset,
    )


def _option(view: OptionView) -> OptionSchema:
    return OptionSchema(
        id=view.id,
        stable_key=view.stable_key,
        label=view.label,
        text=view.text,
        position=view.position,
    )


def _question(view: QuestionView) -> QuestionSchema:
    return QuestionSchema(
        id=view.id,
        question_set_id=view.question_set_id,
        stable_key=view.stable_key,
        version_no=view.version_no,
        stem=view.stem,
        question_type=view.question_type,  # type: ignore[arg-type]
        position=view.position,
        status=view.status,  # type: ignore[arg-type]
        origin_type=view.origin_type,  # type: ignore[arg-type]
        is_reserve=view.is_reserve,
        reserve_order=view.reserve_order,
        source_section_id=view.source_section_id,
        supersedes_id=view.supersedes_id,
        created_at=view.created_at,
        note=view.note,
        options=[_option(opcion) for opcion in view.options],
        correct_option_keys=list(view.correct_option_keys),
        key_outcome=view.key_outcome,  # type: ignore[arg-type]
        explanation_count=view.explanation_count,
    )


def _questions(view: QuestionPage) -> QuestionPageSchema:
    return QuestionPageSchema(
        questions=[_question(pregunta) for pregunta in view.questions],
        total=view.total,
        limit=view.limit,
        offset=view.offset,
    )


def _key(view: AnswerKeyView) -> AnswerKeySchema:
    return AnswerKeySchema(
        id=view.id,
        question_set_id=view.question_set_id,
        version_no=view.version_no,
        status=view.status,  # type: ignore[arg-type]
        source_document_version_id=view.source_document_version_id,
        supersedes_id=view.supersedes_id,
        published_at=view.published_at,
        approved_at=view.approved_at,
        created_at=view.created_at,
        entries=[
            KeyEntrySchema(
                question_version_id=entrada.question_version_id,
                outcome=entrada.outcome,  # type: ignore[arg-type]
                correct_option_keys=list(entrada.correct_option_keys),
                notes=entrada.notes,
            )
            for entrada in view.entries
        ],
    )


def _group(grupo: QuestionDuplicateGroup) -> DuplicateGroupSchema:
    return DuplicateGroupSchema(
        kind=grupo.kind,  # type: ignore[arg-type]
        members=list(grupo.members),
        conflicting_keys=grupo.conflicting_keys,
        keys_seen=list(grupo.keys_seen),
        can_merge=grupo.can_merge,
    )


def _report(
    informe: QuestionImportReport, *, key_id: str | None = None, catalogadas: int = 0
) -> QuestionImportReportSchema:
    return QuestionImportReportSchema(
        set_id=informe.set_id,
        created=informe.created,
        existing=informe.existing,
        incomplete=informe.incomplete,
        with_key=informe.with_key,
        key_entries=informe.key_entries,
        keys_in_conflict=informe.keys_in_conflict,
        mapped_to_topics=catalogadas,
        topics_from_column=informe.topics_from_column,
        rejected=[
            RejectedRowSchema(row_number=fila.row_number, cause=fila.cause, detail=fila.detail)
            for fila in informe.rejected
        ],
        issues=[
            ParseIssueSchema(line=aviso.line, code=aviso.code, detail=aviso.detail)
            for aviso in informe.issues
        ],
        duplicates=[_group(grupo) for grupo in informe.duplicates],
        missing_columns=list(informe.missing_columns),
        ignored_columns=list(informe.ignored_columns),
        unmatched_positions=[],
        model_code_detected=informe.model_code_detected,
        key_id=key_id,
        parts_detected=list(informe.parts_detected),
        evidence_links=informe.evidence_links,
        option_explanations=informe.option_explanations,
    )


def _issue(view: IssueReportView) -> IssueReportSchema:
    return IssueReportSchema(
        id=view.id,
        question_version_id=view.question_version_id,
        kind=view.kind,  # type: ignore[arg-type]
        detail=view.detail,
        status=view.status,  # type: ignore[arg-type]
        created_at=view.created_at,
    )


def _explanation(view: ExplanationView) -> ExplanationSchema:
    return ExplanationSchema(
        id=view.id,
        question_version_id=view.question_version_id,
        option_stable_key=view.option_stable_key,
        text=view.text,
        origin=view.origin,  # type: ignore[arg-type]
        status=view.status,  # type: ignore[arg-type]
        model_name=view.model_name,
        created_at=view.created_at,
    )


def _evidence(view: QuestionEvidenceView) -> QuestionEvidenceSchema:
    return QuestionEvidenceSchema(
        span_id=view.span_id,
        role=view.role,  # type: ignore[arg-type]
        claim=view.claim,
        status=view.status,  # type: ignore[arg-type]
        text=view.text,
        page=view.page,
        citation_label=view.citation_label,
        document_version_id=view.document_version_id,
        section_id=view.section_id,
    )


def _topic(vista: QuestionTopicView) -> QuestionTopicSchema:
    return QuestionTopicSchema(
        mapping_id=vista.mapping_id,
        question_version_id=vista.question_version_id,
        curriculum_node_id=vista.curriculum_node_id,
        official_code=vista.official_code,
        title=vista.title,
        status=vista.status,  # type: ignore[arg-type]
        confidence=vista.confidence,
        created_at=vista.created_at,
    )


def _assignment(vista: QuestionTopicView, *, created: bool) -> QuestionTopicAssignmentSchema:
    return QuestionTopicAssignmentSchema(**_topic(vista).model_dump(), created=created)


def _topic_assignment(asignacion: TopicAssignment) -> QuestionTopicAssignmentSchema:
    """Lo que devuelve asignar: el tema y, si se pidió, el epígrafe que se escribió con él."""
    return QuestionTopicAssignmentSchema(
        **_topic(asignacion.topic.view).model_dump(),
        created=asignacion.topic.created,
        promoted=asignacion.topic.promoted,
        epigraph=(
            None
            if asignacion.epigraph is None
            else _assignment(asignacion.epigraph.view, created=asignacion.epigraph.created)
        ),
        retired=asignacion.retired,
    )


def _exclusion(vista: QuestionExclusionView) -> QuestionExclusionSchema:
    return QuestionExclusionSchema(
        question_version_id=vista.question_version_id,
        reason=vista.reason,  # type: ignore[arg-type]
        actor=vista.actor,
        note=vista.note,
        created_at=vista.created_at,
        stem=vista.stem,
    )


def _exclusion_outcome(marca: QuestionExclusionOutcome) -> QuestionExclusionSchema:
    return _exclusion(marca.view)


def _bulk_request(peticion: BulkTopicAssignmentSchema) -> TopicAssignmentRequest:
    """La fila del contrato traducida a lo que entiende el servicio. El servicio decide el resto.

    `status` nulo es «no toques lo que ya haya» y `promote` solo se enciende cuando la fila **dice**
    qué tiene que quedar: es la diferencia entre una clasificación por lotes que se reintenta (no
    cambia nada de lo que ya está) y el propietario confirmando en la pantalla de revisión (la
    propuesta pasa a decisión, con su evento).
    """
    return TopicAssignmentRequest(
        question_version_id=peticion.question_version_id,
        curriculum_node_id=peticion.curriculum_node_id,
        epigraph_node_id=peticion.epigraph_node_id,
        exclusion_reason=(
            None if peticion.exclusion_reason is None else OutOfSyllabus(peticion.exclusion_reason)
        ),
        confidence=peticion.confidence,
        reason=peticion.reason,
        status=peticion.status or "accepted",
        promote=peticion.status is not None,
        retire_others=peticion.retire_others,
    )


def _bulk_row(fila: TopicAssignmentRow) -> BulkTopicAssignmentResultSchema:
    return BulkTopicAssignmentResultSchema(
        question_version_id=fila.question_version_id,
        outcome=fila.outcome,  # type: ignore[arg-type]
        assignment=(None if fila.assignment is None else _topic_assignment(fila.assignment)),
        exclusion=(None if fila.exclusion is None else _exclusion_outcome(fila.exclusion)),
        detail=fila.detail,
    )


def _bulk_report(lote: TopicAssignmentBatch) -> BulkTopicAssignmentReportSchema:
    return BulkTopicAssignmentReportSchema(
        results=[_bulk_row(fila) for fila in lote.rows],
        created=lote.created,
        existing=lote.existing,
        promoted=lote.promoted,
        excluded=lote.excluded,
        already_excluded=lote.already_excluded,
        errors=lote.errors,
    )


def _node_ref(nodo: ProgrammeNodeRef) -> ProgrammeNodeRefSchema:
    return ProgrammeNodeRefSchema(
        node_id=nodo.node_id,
        official_code=nodo.official_code,
        path=nodo.path,
        title=nodo.title,
    )


def _proposal(propuesta: TopicProposalView) -> QuestionTopicProposalSchema:
    return QuestionTopicProposalSchema(
        mapping_id=propuesta.mapping_id,
        topic=_node_ref(propuesta.topic),
        epigraphs=[_node_ref(epigrafe) for epigrafe in propuesta.epigraphs],
        confidence=propuesta.confidence,
        reason=propuesta.reason,
        created_at=propuesta.created_at,
    )


def _proposal_card(tarjeta: QuestionTopicProposalsView) -> QuestionTopicProposalsSchema:
    return QuestionTopicProposalsSchema(
        question_version_id=tarjeta.question_version_id,
        question_set_id=tarjeta.question_set_id,
        set_title=tarjeta.set_title,
        stem=tarjeta.stem,
        options=[_option(opcion) for opcion in tarjeta.options],
        accepted=None if tarjeta.accepted is None else _node_ref(tarjeta.accepted),
        proposals=[_proposal(propuesta) for propuesta in tarjeta.proposals],
    )


def _conflict(conflicto: QuestionTopicConflictView) -> QuestionTopicConflictSchema:
    return QuestionTopicConflictSchema(
        question_version_id=conflicto.question_version_id,
        question_set_id=conflicto.question_set_id,
        set_title=conflicto.set_title,
        stem=conflicto.stem,
        options=[_option(opcion) for opcion in conflicto.options],
        topics=[
            ConflictingTopicSchema(
                mapping_id=tema.mapping_id,
                topic=_node_ref(tema.topic),
                confidence=tema.confidence,
                actor=tema.actor,
                created_at=tema.created_at,
            )
            for tema in conflicto.topics
        ],
    )


@router.get(
    "/question-sets",
    response_model=QuestionSetPageSchema,
    responses=RESOURCE_ERRORS,
    summary="Conjuntos de preguntas con sus recuentos",
)
def list_question_sets(
    service: QuestionServiceDep,
    opposition_id: Annotated[str | None, Query()] = None,
    set_type: Annotated[str | None, Query()] = None,
    include_archived: Annotated[bool, Query()] = False,
    limit: Annotated[int, Query(ge=1, le=200)] = DEFAULT_LIMIT,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> QuestionSetPageSchema:
    return _page(
        service.sets(
            opposition_id=opposition_id,
            set_type=set_type,
            include_archived=include_archived,
            limit=limit,
            offset=offset,
        )
    )


@router.post(
    "/question-sets",
    response_model=QuestionSetSchema,
    status_code=201,
    responses=INGESTION_WRITE_ERRORS,
    summary="Crea un conjunto de preguntas",
)
def create_question_set(
    request: CreateQuestionSetSchema, service: QuestionServiceDep
) -> QuestionSetSchema:
    return _set(
        service.create_set(
            request.title,
            opposition_id=request.opposition_id,
            set_type=request.set_type,
            convocation_version_id=request.convocation_version_id,
            model_code=request.model_code,
            held_at=request.held_at,
            source_document_version_id=request.source_document_version_id,
        )
    )


@router.get(
    "/question-sets/{set_id}",
    response_model=QuestionSetSchema,
    responses=RESOURCE_ERRORS,
    summary="Un conjunto con sus recuentos",
)
def get_question_set(set_id: str, service: QuestionServiceDep) -> QuestionSetSchema:
    vista = service.set_detail(set_id)
    if vista is None:
        raise NotFoundError("conjunto de preguntas", set_id)
    return _set(vista)


@router.patch(
    "/question-sets/{set_id}",
    response_model=QuestionSetSchema,
    responses=WRITE_ERRORS,
    summary="Cambia quién puede ver un conjunto (personal o public)",
)
def update_question_set(
    set_id: str,
    request: PatchQuestionSetSchema,
    service: QuestionServiceDep,
    actor_header: Annotated[str | None, Header(alias=TOPIC_ACTOR_HEADER)] = None,
) -> QuestionSetSchema:
    """`personal` es material del propietario; `public`, publicable.

    Un conjunto **nace** `personal` y solo se hace `public` a propósito, uno a uno: el material que
    el propietario ha reunido no se hace visible por descuido. El actor viaja a la auditoría.
    """
    actor = _topic_actor(declared=None, header=actor_header)
    if not service.set_distribution(set_id, request.distribution, actor=actor):
        raise NotFoundError("conjunto de preguntas", set_id)
    vista = service.set_detail(set_id)
    if vista is None:  # pragma: no cover - se acaba de cambiar y leer
        raise NotFoundError("conjunto de preguntas", set_id)
    return _set(vista)


@router.get(
    "/question-sets/{set_id}/questions",
    response_model=QuestionPageSchema,
    responses=RESOURCE_ERRORS,
    summary="Preguntas de un conjunto (banco: con su clave)",
)
def list_set_questions(
    set_id: str,
    service: QuestionServiceDep,
    status: Annotated[str | None, Query()] = None,
    origin_type: Annotated[str | None, Query()] = None,
    only_reserves: Annotated[bool, Query()] = False,
    limit: Annotated[int, Query(ge=1, le=200)] = DEFAULT_LIMIT,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> QuestionPageSchema:
    if service.set_detail(set_id) is None:
        raise NotFoundError("conjunto de preguntas", set_id)
    return _questions(
        service.questions(
            set_id=set_id,
            status=status,
            origin_type=origin_type,
            only_reserves=only_reserves,
            limit=limit,
            offset=offset,
            include_key=True,
        )
    )


@router.post(
    "/question-sets/{set_id}/parse",
    response_model=QuestionImportReportSchema,
    responses=INGESTION_WRITE_ERRORS,
    summary="Importa preguntas, un CSV, un JSON o una plantilla a un conjunto",
)
def parse_into_set(
    set_id: str, request: ParseQuestionSetSchema, service: QuestionServiceDep
) -> QuestionImportReportSchema:
    """Las cuatro formas de llenar un conjunto: texto, CSV con mapeo, JSON y plantilla suelta.

    Lo que no se entiende se informa (fila a fila, con su causa) y el resto entra: una fila mala no
    aborta el lote.
    """
    if service.set_detail(set_id) is None:
        raise NotFoundError("conjunto de preguntas", set_id)
    if request.kind == "csv":
        return _report(
            service.import_from_csv(
                set_id,
                request.text,
                mapping=_mapping(request.mapping),
                origin_type=Origin.PRIVATE,
            )
        )
    if request.kind == "json":
        return _report(service.import_from_json(set_id, request.text, origin_type=Origin.PRIVATE))
    if request.kind == "answer_key":
        informe = service.import_key_from_text(
            set_id,
            request.text,
            source_document_version_id=request.source_document_version_id,
        )
        if not informe.applied:
            raise ClassificationConflictError(
                "la plantilla no coincide con ninguna pregunta del conjunto"
            )
        return QuestionImportReportSchema(
            set_id=set_id,
            key_entries=informe.entries,
            key_id=informe.key_id,
            # Una importación de plantilla no mete ni rechaza preguntas: se dice con listas vacías.
            rejected=[],
            duplicates=[],
            missing_columns=[],
            ignored_columns=[],
            unmatched_positions=list(informe.unmatched),
            issues=[
                ParseIssueSchema(line=aviso.line, code=aviso.code, detail=aviso.detail)
                for aviso in informe.issues
            ],
        )
    return _report(service.import_from_text(set_id, request.text, origin_type=Origin.PRIVATE))


@router.post(
    "/question-sets/{set_id}/import-document",
    response_model=QuestionImportReportSchema,
    responses=INGESTION_WRITE_ERRORS,
    summary="Importa las preguntas de una versión de documento (ruta añadida: DEBT-010)",
)
def import_from_document(
    set_id: str,
    request: ImportQuestionsFromDocumentSchema,
    service: QuestionServiceDep,
    auto: AutoStudyServiceDep,
) -> QuestionImportReportSchema:
    """Las preguntas de un documento de la biblioteca, con la cita de dónde salió cada una.

    Ruta **añadida** al contrato §9 y registrada en ADR-013. Es la mitad que faltaba del importador
    (04_INGESTION §10: «parser desde texto/**documento**»): hasta ahora solo entraba texto suelto,
    así que una pregunta nacida de un documento no podía enseñar su cita ni abrir el original.

    Después de importar se **cataloga**: cada pregunta hereda el programa del documento del que sale
    (S12.6), igual que cuando la importación la hace la aplicación sola al aceptar una versión. Sin
    ese paso, las preguntas importadas a mano se quedarían fuera del diagnóstico por temas.

    Lo que **no** hace: inventar la cita. Si la versión no tiene fragmentos extraídos no hay de
    dónde citar, y el informe lo dice con una incidencia en lugar de crear una evidencia vacía.
    """
    if service.set_detail(set_id) is None:
        raise NotFoundError("conjunto de preguntas", set_id)
    informe = service.import_from_document(
        set_id, request.document_version_id, origin_type=Origin.PRIVATE
    )
    catalogadas = auto.catalogue_questions(set_id=set_id, version_id=request.document_version_id)
    return _report(informe, catalogadas=catalogadas)


@router.get(
    "/questions",
    response_model=QuestionPageSchema,
    responses=RESOURCE_ERRORS,
    summary="Preguntas del banco, con filtros",
)
def list_questions(
    service: QuestionServiceDep,
    set_id: Annotated[str | None, Query()] = None,
    status: Annotated[str | None, Query()] = None,
    origin_type: Annotated[str | None, Query()] = None,
    only_reserves: Annotated[bool, Query()] = False,
    limit: Annotated[int, Query(ge=1, le=200)] = DEFAULT_LIMIT,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> QuestionPageSchema:
    """El banco enseña la clave: aquí se revisa, no se examina a nadie."""
    return _questions(
        service.questions(
            set_id=set_id,
            status=status,
            origin_type=origin_type,
            only_reserves=only_reserves,
            limit=limit,
            offset=offset,
            include_key=True,
        )
    )


@router.get(
    "/questions/{question_id}",
    response_model=QuestionSchema,
    responses=RESOURCE_ERRORS,
    summary="Una pregunta con sus opciones y su clave",
)
def get_question(question_id: str, service: QuestionServiceDep) -> QuestionSchema:
    vista = service.question(question_id, include_key=True)
    if vista is None:
        raise NotFoundError("pregunta", question_id)
    return _question(vista)


@router.patch(
    "/questions/{question_id}",
    response_model=QuestionSchema,
    responses=INGESTION_WRITE_ERRORS,
    summary="Cambia la composición de una pregunta",
)
def patch_question(
    question_id: str, request: PatchQuestionSchema, service: QuestionServiceDep
) -> QuestionSchema:
    """Tipo, posición y reserva. El **texto** de una oficial se corrige con corrección local."""
    if service.question(question_id) is None:
        raise NotFoundError("pregunta", question_id)
    vista = service.update_question(
        question_id,
        stem=request.stem,
        question_type=request.question_type,
        position=request.position,
        is_reserve=request.is_reserve,
        reserve_order=request.reserve_order,
    )
    if vista is None:
        raise NotFoundError("pregunta", question_id)
    return _question(vista)


@router.post(
    "/questions/{question_id}/local-corrections",
    response_model=CorrectionOutcomeSchema,
    status_code=201,
    responses=INGESTION_WRITE_ERRORS,
    summary="Corrige una transcripción con su motivo, sin tocar el original",
)
def correct_question(
    question_id: str, request: LocalCorrectionSchema, service: QuestionServiceDep
) -> CorrectionOutcomeSchema:
    corregida, clave = service.correct_question(
        question_id, note=request.note, stem=request.stem, options=request.options
    )
    if corregida is None:
        raise NotFoundError("pregunta", question_id)
    return CorrectionOutcomeSchema(question=_question(corregida), key_id=clave)


@router.get(
    "/questions/{question_id}/evidence",
    response_model=list[QuestionEvidenceSchema],
    responses=RESOURCE_ERRORS,
    summary="Evidencia que sostiene una pregunta",
)
def list_question_evidence(
    question_id: str, service: QuestionServiceDep
) -> list[QuestionEvidenceSchema]:
    if service.question(question_id) is None:
        raise NotFoundError("pregunta", question_id)
    return [_evidence(evidencia) for evidencia in service.evidence(question_id)]


@router.post(
    "/questions/{question_id}/report-issue",
    response_model=IssueReportSchema,
    status_code=201,
    responses=INGESTION_WRITE_ERRORS,
    summary="Reporta que una pregunta es ambigua, está mal keyada o tiene una errata",
)
def report_question_issue(
    question_id: str, request: IssueReportRequestSchema, service: QuestionServiceDep
) -> IssueReportSchema:
    informe = service.report_issue(question_id, kind=request.kind, detail=request.detail)
    if informe is None:
        raise NotFoundError("pregunta", question_id)
    return _issue(informe)


@router.get(
    "/questions/{question_id}/explanations",
    response_model=list[ExplanationSchema],
    responses=RESOURCE_ERRORS,
    summary="Explicaciones de la pregunta y de cada una de sus opciones (ruta añadida: S12.7)",
)
def list_question_explanations(
    question_id: str, service: QuestionServiceDep
) -> list[ExplanationSchema]:
    """La explicación de la pregunta entera y la de cada opción, con su clave de opción.

    Se sirven **todas juntas**: quien lee quiere entender la pregunta, y separarlas obligaría a la
    interfaz a juntarlas otra vez (07_UI-UX §7).
    """
    return [_explanation(item) for item in service.explanations(question_id)]


@router.post(
    "/questions/{question_id}/explanations",
    response_model=ExplanationSchema,
    status_code=201,
    responses={**INGESTION_WRITE_ERRORS, **RESOURCE_ERRORS},
    summary="Escribe la explicación de la pregunta o de una de sus opciones (ruta añadida: S12.7)",
)
def set_question_explanation(
    question_id: str, request: SetExplanationRequestSchema, service: QuestionServiceDep
) -> ExplanationSchema:
    """Escribe o **sustituye** la explicación de ese hueco: la identidad es (pregunta, opción).

    Una opción que la pregunta no tiene es un 409 con el motivo, no una explicación huérfana: la
    explicación de una opción que no está no explica nada.
    """
    guardada = service.set_explanation(
        question_id,
        text=request.text,
        option_stable_key=request.option_stable_key,
    )
    if guardada is None:
        raise NotFoundError("pregunta", question_id)
    return _explanation(guardada)


@router.get(
    "/questions/{question_version_id}/topics",
    response_model=list[QuestionTopicSchema],
    responses=RESOURCE_ERRORS,
    summary="Temas asignados a una pregunta, con el estado de cada mapeo",
)
def list_question_topics(
    question_version_id: str, service: QuestionServiceDep
) -> list[QuestionTopicSchema]:
    """Los temas de la pregunta, cada uno con el estado de su mapeo.

    Se sirven todos los mapeos, no solo los aceptados: quien administra tiene que ver también lo que
    propuso un motor y nadie ha confirmado. El estado va en cada uno para que la diferencia se lea
    sin adivinar.
    """
    return [_topic(tema) for tema in service.topics(question_version_id)]


@router.post(
    "/questions/{question_version_id}/topics",
    response_model=QuestionTopicAssignmentSchema,
    responses=CONFLICT_WRITE_ERRORS,
    summary="Asigna un tema a una pregunta y lo deja auditado (idempotente)",
)
def assign_question_topic(
    question_version_id: str,
    request: AssignTopicRequestSchema,
    service: QuestionServiceDep,
    actor: Annotated[str | None, Header(alias=TOPIC_ACTOR_HEADER, max_length=64)] = None,
) -> QuestionTopicAssignmentSchema:
    """Asigna la pregunta al tema indicado y deja el evento de auditoría (`question.mapped`).

    Es **idempotente** por `(tema, pregunta)`: repetirla devuelve el mapeo que ya estaba con
    `created=false` y **no** escribe un segundo evento. Es lo que necesita la clasificación de un
    banco entero, que se reintenta.

    Quién lo hace se dice con `actor` en el cuerpo o con la cabecera `X-OpoFuente-Actor` (por
    defecto `local`): la clasificación automática se identifica («llm:deepseek-flash») y así la
    auditoría distingue a la persona del proceso.

    El destino tiene que ser un **tema**: un bloque responde 409 con el motivo, porque una pregunta
    colgada de él quedaría fuera del diagnóstico por temas creyendo estar dentro. El **epígrafe**
    del tema se puede asignar a la vez (`epigraph_node_id`) y se escribe **además** del tema: el
    epígrafe dice dónde encaja la pregunta y el tema mantiene los recuentos que ya existen.
    """
    vista = service.assign_topic(
        question_version_id,
        node_id=request.curriculum_node_id,
        epigraph_node_id=request.epigraph_node_id,
        actor=_topic_actor(declared=request.actor, header=actor),
        confidence=request.confidence,
        reason=request.reason,
    )
    return _topic_assignment(vista)


@router.post(
    "/questions/topics/bulk",
    response_model=BulkTopicAssignmentReportSchema,
    responses=CONFLICT_WRITE_ERRORS,
    summary="Asigna temas por lotes: misma ruta auditada, idempotente y fila a fila",
)
def assign_question_topics_bulk(
    request: BulkTopicAssignmentsSchema,
    service: QuestionServiceDep,
    actor: Annotated[str | None, Header(alias=TOPIC_ACTOR_HEADER, max_length=64)] = None,
) -> BulkTopicAssignmentReportSchema:
    """La versión por lotes de `POST /questions/{id}/topics`, para no hacer 17.000 peticiones.

    No es un segundo camino de escritura: cada fila entra por el mismo método del servicio, así
    que deja **el mismo mapeo y el mismo evento de auditoría** que la ruta individual. Lo que añade
    es el sobre: un actor para todo el lote y, por fila, o un tema (con su epígrafe) o un fuera de
    temario.

    Es **idempotente**: repetir un lote no duplica mapeos ni eventos, y cada fila dice si la creó
    esta llamada (`created`) o si ya estaba (`existing`). Una fila mala **no** tumba el lote: se
    devuelve con `outcome="error"` y su motivo, y las demás se aplican. Abortar 200 asignaciones
    porque una pregunta se retiró entre medias obligaría a repetir las 199 buenas.

    El actor viaja en el cuerpo (`actor`) o en la cabecera `X-OpoFuente-Actor`. La clasificación
    automática se identifica (`llm:deepseek-flash`) y así la auditoría distingue a la persona del
    proceso.
    """
    lote = service.apply_topic_batch(
        [_bulk_request(peticion) for peticion in request.assignments],
        actor=_topic_actor(declared=request.actor, header=actor),
    )
    return _bulk_report(lote)


@router.get(
    "/question-exclusions",
    response_model=QuestionExclusionPageSchema,
    responses=RESOURCE_ERRORS,
    summary="Las preguntas fuera de temario, con su motivo (la cola que revisa el propietario)",
)
def list_question_exclusions(
    service: QuestionServiceDep,
    reason: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = DEFAULT_LIMIT,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> QuestionExclusionPageSchema:
    """Las marcas de fuera de temario, de la más nueva a la más antigua.

    Es donde se **consulta** lo que no es materia del programa: la pregunta, el motivo por el que
    se declaró y quién lo decidió. Va como recurso propio (`/question-exclusions`) y no dentro de la
    pregunta a propósito: una marca no es un tema, y meterla en el mismo sitio invitaría a leerla
    como si lo fuera. La revisión de una marca se hace asignando un tema (que la levanta) o
    dejándola.
    """
    marcas, total = service.exclusions(reason=reason, limit=limit, offset=offset)
    return QuestionExclusionPageSchema(
        exclusions=[_exclusion(marca) for marca in marcas],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/question-topic-proposals",
    response_model=QuestionTopicProposalPageSchema,
    responses=RESOURCE_ERRORS,
    summary="Las propuestas de tema sin confirmar, con la pregunta (la cola de revisión del panel)",
)
def list_question_topic_proposals(
    service: QuestionServiceDep,
    limit: Annotated[int, Query(ge=1, le=200)] = DEFAULT_LIMIT,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> QuestionTopicProposalPageSchema:
    """Lo que el clasificador propuso con dudas (`provisional`) y nadie ha decidido todavía.

    Es la lectura de la cola que despacha el propietario con el teclado, y por eso trae la pregunta
    **entera** —enunciado y opciones— junto al tema y los epígrafes propuestos, la confianza y el
    motivo del modelo: sin el texto delante, una propuesta no se puede juzgar, y sin la confianza no
    se sabe cuánto dudó quien la hizo.

    Va como recurso propio y no dentro de `GET /questions/{id}/topics` porque una propuesta no es
    «los temas de una pregunta»: es **una cola**, se pagina como tal, y su total lo cuenta el
    servidor. Van de la más dudosa a la menos, y el motivo sale de la auditoría, que es donde vive.

    Se despacha con `POST /questions/topics/bulk`: una fila por propuesta con su `status`
    (`accepted`) la confirma, otra con otro tema la corrige, y `exclusion_reason` la deja fuera de
    temario. No hay una ruta de escritura propia para esto a propósito: la propuesta se decide por
    el mismo camino auditado por el que se asignan los temas.
    """
    propuestas, total = service.topic_proposals(limit=limit, offset=offset)
    return QuestionTopicProposalPageSchema(
        questions=[_proposal_card(tarjeta) for tarjeta in propuestas],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/question-topic-conflicts",
    response_model=QuestionTopicConflictPageSchema,
    responses=RESOURCE_ERRORS,
    summary="Las preguntas que cuentan en dos temas aceptados, con quién decidió cada uno",
)
def list_question_topic_conflicts(
    service: QuestionServiceDep,
    limit: Annotated[int, Query(ge=1, le=200)] = DEFAULT_LIMIT,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> QuestionTopicConflictPageSchema:
    """Las preguntas que cuentan en **dos o más temas decididos** a la vez.

    No es una curiosidad: una pregunta en dos temas suma en los dos en todos los recuentos del
    alumno y en la cobertura, así que mientras exista, esas cifras mienten. Vienen de antes de esta
    tanda —la catalogación heredada del documento, las migraciones— y de dos corridas del
    clasificador que se pisaron; por eso cada tema viaja con **quién lo decidió**, que es lo que
    permite juzgar cuál se queda.

    Se resuelve con la misma ruta por lotes que la cola: una fila con el tema elegido, `status`
    `accepted` y `retire_others` deja la pregunta con ese tema y retira los demás. La aplicación no
    elige: si nadie decide, no se toca nada.
    """
    conflictos, total = service.topic_conflicts(limit=limit, offset=offset)
    return QuestionTopicConflictPageSchema(
        questions=[_conflict(conflicto) for conflicto in conflictos],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.delete(
    "/questions/{question_version_id}/topics/{curriculum_node_id}",
    status_code=204,
    responses=WRITE_ERRORS,
    summary="Quita el tema de una pregunta y lo deja auditado",
)
def unassign_question_topic(
    question_version_id: str,
    curriculum_node_id: str,
    service: QuestionServiceDep,
    actor: Annotated[str | None, Header(alias=TOPIC_ACTOR_HEADER, max_length=64)] = None,
) -> None:
    """Retira el mapeo y deja su evento (`question.unmapped`) con el antes.

    Quitar algo que no estaba es un 404: no es una retirada sin efecto, es que no había nada que
    retirar, y decirlo evita creer que se ha deshecho una asignación que sigue puesta en otro sitio.
    """
    if not service.unassign_topic(
        question_version_id,
        node_id=curriculum_node_id,
        actor=_topic_actor(declared=None, header=actor),
    ):
        raise NotFoundError("mapeo de tema", f"{question_version_id}/{curriculum_node_id}")


@router.get(
    "/question-sets/{set_id}/answer-keys",
    response_model=list[AnswerKeySchema],
    responses=RESOURCE_ERRORS,
    summary="Plantillas de un conjunto, con sus desenlaces",
)
def list_answer_keys(set_id: str, service: QuestionServiceDep) -> list[AnswerKeySchema]:
    if service.set_detail(set_id) is None:
        raise NotFoundError("conjunto de preguntas", set_id)
    return [_key(clave) for clave in service.keys(set_id)]


@router.post(
    "/question-sets/{set_id}/answer-keys/{key_id}/activate",
    response_model=AnswerKeySchema,
    responses=INGESTION_WRITE_ERRORS,
    summary="Activa una plantilla (activar es aprobar)",
)
def activate_answer_key(set_id: str, key_id: str, service: QuestionServiceDep) -> AnswerKeySchema:
    """Activar una plantilla **es** aprobarla: lo decide una persona y queda en la auditoría.

    Si el conjunto es oficial y la plantilla no tiene enlazada la plantilla oficial, responde 409
    con el motivo: una aprobación no convierte en oficial un documento que no lo es.
    """
    clave = service.keys(set_id)
    if not any(candidata.id == key_id for candidata in clave):
        raise NotFoundError("plantilla", key_id)
    aplicada, motivo = service.activate_key(key_id)
    if not aplicada:
        raise ClassificationConflictError(motivo or "la plantilla no se pudo activar")
    activada = next(candidata for candidata in service.keys(set_id) if candidata.id == key_id)
    return _key(activada)


@router.post(
    "/question-sets/{set_id}/answer-keys/{key_id}/source",
    response_model=KeySourceLinkSchema,
    responses=INGESTION_WRITE_ERRORS,
    summary="Enlaza (o desenlaza) la plantilla oficial de una clave que ya existe",
)
def link_answer_key_source(
    set_id: str,
    key_id: str,
    request: LinkKeySourceRequestSchema,
    service: QuestionServiceDep,
) -> KeySourceLinkSchema:
    """Antes, el enlace solo se hacía al aceptar la versión de la plantilla: un examen importado
    después se quedaba con su clave oficial sin poder activarse. Enlazar exige que la plantilla
    diga lo mismo que la clave, pregunta a pregunta; si no, 409 con lo que no coincide.
    """
    if not any(candidata.id == key_id for candidata in service.keys(set_id)):
        raise NotFoundError("plantilla", key_id)
    resultado = service.link_key_source(
        key_id, source_document_version_id=request.source_document_version_id
    )
    if not resultado.applied:
        raise ClassificationConflictError(resultado.reason or "la plantilla no se pudo enlazar")
    clave = service.key(key_id)
    if clave is None:
        raise NotFoundError("plantilla", key_id)
    return KeySourceLinkSchema(
        key=_key(clave),
        lines=resultado.lines,
        agreeing=resultado.agreeing,
        disagreeing=resultado.disagreeing,
        without_entry=resultado.without_entry,
        ambiguous=resultado.ambiguous,
        key_entries=resultado.key_entries,
    )


@router.post(
    "/answer-keys/{key_id}/mark-supersedes",
    response_model=AnswerKeySchema,
    responses=INGESTION_WRITE_ERRORS,
    summary="Confirma que una plantilla sustituye a otra",
)
def mark_answer_key_supersedes(
    key_id: str, request: MarkKeySupersedesRequestSchema, service: QuestionServiceDep
) -> AnswerKeySchema:
    aplicada, motivo = service.mark_key_supersedes(key_id, superseded_id=request.superseded_id)
    if not aplicada:
        raise ClassificationConflictError(motivo or "la sustitución no se pudo aplicar")
    clave = service.key(key_id)
    if clave is None:
        raise NotFoundError("plantilla", key_id)
    return _key(clave)


def _mapping(mapeo: CsvMappingSchema | None) -> CsvColumnMapping:
    if mapeo is None:
        return CsvColumnMapping()
    return CsvColumnMapping(
        stem=mapeo.stem,
        options=tuple(mapeo.options),
        correct=mapeo.correct,
        explanation=mapeo.explanation,
        topic=mapeo.topic,
        source=mapeo.source,
        tags=mapeo.tags,
        position=mapeo.position,
        reserve=mapeo.reserve,
    )
