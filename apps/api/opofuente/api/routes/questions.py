"""Rutas del banco de preguntas (08_API-CONTRACT §9).

Dos reglas que se aplican aquí y no en el cliente:

- **el banco enseña la clave** (es lo que se está revisando) y las sesiones no: por eso estas rutas
  piden las preguntas con clave, y el valor por defecto del servicio no la lleva;
- **una corrección local lleva motivo** y crea versión nueva: el texto importado no se reescribe.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query

from opofuente.api.deps import AutoStudyServiceDep, QuestionServiceDep
from opofuente.api.error_responses import INGESTION_WRITE_ERRORS, RESOURCE_ERRORS
from opofuente.api.question_schemas import (
    AnswerKeySchema,
    CorrectionOutcomeSchema,
    CreateQuestionSetSchema,
    CsvMappingSchema,
    DuplicateGroupSchema,
    ExplanationSchema,
    ImportQuestionsFromDocumentSchema,
    IssueReportRequestSchema,
    IssueReportSchema,
    KeyEntrySchema,
    LocalCorrectionSchema,
    MarkKeySupersedesRequestSchema,
    OptionSchema,
    ParseIssueSchema,
    ParseQuestionSetSchema,
    PatchQuestionSchema,
    QuestionEvidenceSchema,
    QuestionImportReportSchema,
    QuestionPageSchema,
    QuestionSchema,
    QuestionSetPageSchema,
    QuestionSetSchema,
    RejectedRowSchema,
    SetExplanationRequestSchema,
)
from opofuente.application.question_models import (
    AnswerKeyView,
    CsvColumnMapping,
    ExplanationView,
    IssueReportView,
    OptionView,
    QuestionEvidenceView,
    QuestionImportReport,
    QuestionPage,
    QuestionSetPage,
    QuestionSetView,
    QuestionView,
)
from opofuente.domain.errors import ClassificationConflictError, NotFoundError
from opofuente.domain.questions import Origin, QuestionDuplicateGroup

router = APIRouter(tags=["preguntas"])

#: Cuántas cosas se devuelven de una vez si la petición no dice otra cosa.
DEFAULT_LIMIT = 50


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
