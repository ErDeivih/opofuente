"""Rutas de la biblioteca (08_API-CONTRACT §7).

Promocionar, versionar, citar y organizar. Dos reglas que se aplican aquí y no en el cliente:

- una promoción que **no** se puede aplicar responde **409** con el motivo (nunca un «ok» sin
efecto);
- las respuestas dicen **si los derechos están restringidos** y **si la versión activa es
candidata**,
  para que nadie tenga que suponerlo.

Dos rutas **no están en el contrato §7** y se declaran aquí en lugar de esconderse: la de
**colecciones** (la spec pide colecciones en el slice pero no fija la ruta) y la de
**evidencia**, que es
lo que hace abrible una cita.

La ruta de **mapeos** de §7 sí está (`POST /document-versions/{id}/mappings`): es la que permite que
una misma fuente se guarde una vez y se asigne a dos oposiciones sin duplicar el fichero.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query

from opofuente.api.deps import LibraryServiceDep
from opofuente.api.error_responses import INGESTION_WRITE_ERRORS, RESOURCE_ERRORS
from opofuente.api.library_schemas import (
    CollectionItemRequestSchema,
    CollectionSchema,
    CreateCollectionRequestSchema,
    DocumentDetailSchema,
    DocumentMappingSchema,
    DocumentPageSchema,
    DocumentSchema,
    EvidenceSchema,
    MappingRequestSchema,
    MarkSupersedesRequestSchema,
    PromoteRequestSchema,
    PromotionOutcomeSchema,
    RightsSchema,
    SectionSchema,
    VersionSchema,
)
from opofuente.application.library_models import (
    CollectionView,
    DocumentDetail,
    DocumentPage,
    DocumentView,
    EvidenceView,
    PromotionOutcome,
    RightsView,
    SectionView,
    VersionView,
)
from opofuente.domain.errors import ClassificationConflictError, NotFoundError

router = APIRouter(tags=["biblioteca"])


def _rights(view: RightsView | None) -> RightsSchema | None:
    if view is None:
        return None
    return RightsSchema(
        code=view.code,
        review_status=view.review_status,  # type: ignore[arg-type]
        license_name=view.license_name,
        license_url=view.license_url,
        attribution=view.attribution,
        commercial_reuse=view.commercial_reuse,
        sharing=view.sharing,
        notes=view.notes,
        is_restricted=view.is_restricted,
    )


def _version(view: VersionView) -> VersionSchema:
    return VersionSchema(
        id=view.id,
        logical_document_id=view.logical_document_id,
        version_label=view.version_label,
        status=view.status,  # type: ignore[arg-type]
        is_accepted=view.is_accepted,
        artifact_id=view.artifact_id,
        representation_id=view.representation_id,
        published_at=view.published_at,
        valid_from=view.valid_from,
        valid_to=view.valid_to,
        retrieved_at=view.retrieved_at,
        language=view.language,
        supersedes_id=view.supersedes_id,
        rights=_rights(view.rights),
        official_url=view.official_url,
        content_hash=view.content_hash,
        approved_at=view.approved_at,
        approved_by=view.approved_by,
        section_count=view.section_count,
        evidence_count=view.evidence_count,
    )


def _document(view: DocumentView) -> DocumentSchema:
    return DocumentSchema(
        id=view.id,
        canonical_title=view.canonical_title,
        document_type=view.document_type,
        owner_scope=view.owner_scope,  # type: ignore[arg-type]
        is_public=view.is_public,
        authority_tier=view.authority_tier,
        canonical_identifier=view.canonical_identifier,
        active_version=_version(view.active_version) if view.active_version else None,
        version_count=view.version_count,
        mapping_count=view.mapping_count,
        created_at=view.created_at,
    )


def _detail(view: DocumentDetail) -> DocumentDetailSchema:
    return DocumentDetailSchema(
        document=_document(view.document),
        versions=[_version(version) for version in view.versions],
    )


def _page(view: DocumentPage) -> DocumentPageSchema:
    return DocumentPageSchema(
        documents=[_document(documento) for documento in view.documents],
        total=view.total,
        limit=view.limit,
        offset=view.offset,
    )


def _section(view: SectionView) -> SectionSchema:
    return SectionSchema(
        id=view.id,
        document_version_id=view.document_version_id,
        section_type=view.section_type,
        title=view.title,
        label=view.label,
        position=view.position,
        ordinal=view.ordinal,
        parent_id=view.parent_id,
        page_start=view.page_start,
        page_end=view.page_end,
        char_start=view.char_start,
        char_end=view.char_end,
    )


def _evidence(view: EvidenceView) -> EvidenceSchema:
    return EvidenceSchema(
        id=view.id,
        document_version_id=view.document_version_id,
        text=view.text,
        normalized_text=view.normalized_text,
        ordinal=view.ordinal,
        section_id=view.section_id,
        page=view.page,
        citation_label=view.citation_label,
        quality=view.quality,
        index_status=view.index_status,  # type: ignore[arg-type]
        char_start=view.char_start,
        char_end=view.char_end,
    )


def _collection(view: CollectionView) -> CollectionSchema:
    return CollectionSchema(
        id=view.id,
        name=view.name,
        description=view.description,
        item_count=view.item_count,
        items=list(view.items),
        created_at=view.created_at,
    )


def _outcome(result: PromotionOutcome) -> PromotionOutcomeSchema:
    if not result.applied:
        raise ClassificationConflictError(result.reason or "La operación no se pudo aplicar")
    return PromotionOutcomeSchema(
        document_id=result.document_id,
        version_id=result.version_id,
        created_document=result.created_document,
        created_version=result.created_version,
        applied=result.applied,
        reason=result.reason,
    )


@router.get(
    "/documents",
    response_model=DocumentPageSchema,
    responses=RESOURCE_ERRORS,
    summary="Biblioteca: documentos con su versión activa",
)
def list_documents(
    service: LibraryServiceDep,
    document_type: Annotated[str | None, Query()] = None,
    owner_scope: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> DocumentPageSchema:
    return _page(
        service.documents(
            document_type=document_type, owner_scope=owner_scope, limit=limit, offset=offset
        )
    )


@router.post(
    "/documents",
    response_model=PromotionOutcomeSchema,
    responses=INGESTION_WRITE_ERRORS,
    summary="Promociona un artefacto a documento (o le añade una versión)",
)
def promote_document(
    request: PromoteRequestSchema, service: LibraryServiceDep
) -> PromotionOutcomeSchema:
    return _outcome(
        service.promote(
            request.artifact_id,
            document_id=request.document_id,
            title=request.title,
            document_type=request.document_type,
            authority_tier=request.authority_tier,
            version_label=request.version_label,
            rights_code=request.rights_code,
            official_url=request.official_url,
        )
    )


@router.get(
    "/documents/{document_id}",
    response_model=DocumentDetailSchema,
    responses=RESOURCE_ERRORS,
    summary="Un documento con sus versiones",
)
def get_document(document_id: str, service: LibraryServiceDep) -> DocumentDetailSchema:
    detalle = service.document(document_id)
    if detalle is None:
        raise NotFoundError("documento", document_id)
    return _detail(detalle)


@router.get(
    "/documents/{document_id}/versions",
    response_model=list[VersionSchema],
    responses=RESOURCE_ERRORS,
    summary="Versiones del documento (la antigua no desaparece)",
)
def list_versions(document_id: str, service: LibraryServiceDep) -> list[VersionSchema]:
    detalle = service.document(document_id)
    if detalle is None:
        raise NotFoundError("documento", document_id)
    return [_version(version) for version in detalle.versions]


@router.post(
    "/documents/{document_id}/versions/{version_id}/accept",
    response_model=PromotionOutcomeSchema,
    responses=INGESTION_WRITE_ERRORS,
    summary="Acepta una versión (promoción crítica, confirmada y auditada)",
)
def accept_version(
    document_id: str, version_id: str, service: LibraryServiceDep
) -> PromotionOutcomeSchema:
    if service.version(document_id, version_id) is None:
        raise NotFoundError("versión", version_id)
    return _outcome(service.accept_version(version_id))


@router.post(
    "/documents/{document_id}/versions/{version_id}/mark-supersedes",
    response_model=PromotionOutcomeSchema,
    responses=INGESTION_WRITE_ERRORS,
    summary="Confirma que una versión sustituye a otra (la antigua se conserva)",
)
def mark_supersedes(
    document_id: str,
    version_id: str,
    request: MarkSupersedesRequestSchema,
    service: LibraryServiceDep,
) -> PromotionOutcomeSchema:
    if service.version(document_id, version_id) is None:
        raise NotFoundError("versión", version_id)
    return _outcome(service.mark_supersedes(version_id, superseded_id=request.superseded_id))


@router.get(
    "/document-versions/{version_id}/sections",
    response_model=list[SectionSchema],
    responses=RESOURCE_ERRORS,
    summary="Estructura de la versión (de aquí sale la cita)",
)
def list_sections(version_id: str, service: LibraryServiceDep) -> list[SectionSchema]:
    return [_section(seccion) for seccion in service.sections(version_id)]


@router.get(
    "/document-versions/{version_id}/evidence",
    response_model=list[EvidenceSchema],
    responses=RESOURCE_ERRORS,
    summary="Evidencia citable de la versión (ruta añadida: la spec pide citas abribles)",
)
def list_evidence(version_id: str, service: LibraryServiceDep) -> list[EvidenceSchema]:
    return [_evidence(evidencia) for evidencia in service.evidence(version_id)]


@router.get(
    "/evidence/{evidence_id}",
    response_model=EvidenceSchema,
    responses=RESOURCE_ERRORS,
    summary="Una evidencia concreta, con su sección y su página",
)
def get_evidence(evidence_id: str, service: LibraryServiceDep) -> EvidenceSchema:
    evidencia = service.citation(evidence_id)
    if evidencia is None:
        raise NotFoundError("evidencia citable", evidence_id)
    return _evidence(evidencia)


@router.get(
    "/collections",
    response_model=list[CollectionSchema],
    responses=RESOURCE_ERRORS,
    summary="Colecciones (ruta añadida: la spec pide colecciones sin fijar la ruta)",
)
def list_collections(service: LibraryServiceDep) -> list[CollectionSchema]:
    return [_collection(coleccion) for coleccion in service.collections()]


@router.post(
    "/collections",
    response_model=CollectionSchema,
    responses=INGESTION_WRITE_ERRORS,
    summary="Crea una colección",
)
def create_collection(
    request: CreateCollectionRequestSchema, service: LibraryServiceDep
) -> CollectionSchema:
    return _collection(service.create_collection(request.name, description=request.description))


@router.post(
    "/collections/{collection_id}/items",
    response_model=CollectionSchema,
    responses=INGESTION_WRITE_ERRORS,
    summary="Añade un sujeto a una colección (sin duplicarlo)",
)
def add_collection_item(
    collection_id: str, request: CollectionItemRequestSchema, service: LibraryServiceDep
) -> CollectionSchema:
    coleccion = service.add_to_collection(
        collection_id, subject_type=request.subject_type, subject_id=request.subject_id
    )
    if coleccion is None:
        raise NotFoundError("colección", collection_id)
    return _collection(coleccion)


@router.post(
    "/document-versions/{version_id}/mappings",
    response_model=DocumentMappingSchema,
    status_code=201,
    responses=INGESTION_WRITE_ERRORS,
    summary="Asigna una versión de documento a un nodo del programa",
)
def add_mapping(
    version_id: str, request: MappingRequestSchema, service: LibraryServiceDep
) -> DocumentMappingSchema:
    """Contrato §7: una fuente compartida se guarda una vez y se asigna a varias oposiciones.

    El mapeo apunta a la **versión**, no al artefacto: así una versión retirada deja de contar como
    cobertura sin tocar el material que ya se había asignado con ella.
    """
    mapeo_id = service.add_mapping(
        version_id,
        curriculum_node_id=request.curriculum_node_id,
        coverage_type=request.coverage_type,
    )
    if mapeo_id is None:
        raise NotFoundError("versión de documento", version_id)
    return DocumentMappingSchema(
        id=mapeo_id,
        document_version_id=version_id,
        curriculum_node_id=request.curriculum_node_id,
        coverage_type=request.coverage_type,
        status="accepted",
    )
