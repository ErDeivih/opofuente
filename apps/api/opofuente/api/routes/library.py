"""Rutas de la biblioteca (08_API-CONTRACT §7).

Promocionar, versionar, citar y organizar. Dos reglas que se aplican aquí y no en el cliente:

- una promoción que **no** se puede aplicar responde **409** con el motivo (nunca un «ok» sin
efecto);
- las respuestas dicen **si los derechos están restringidos** y **si la versión activa es
candidata**,
  para que nadie tenga que suponerlo.

Cuatro rutas **no están en el contrato §7** y se declaran aquí en lugar de esconderse: la de
**colecciones** (la spec pide colecciones en el slice pero no fija la ruta), las dos de
**evidencia**, que es lo que hace abrible una cita, y la de **diff**, que la spec pide («confirmar
diff») y el contrato no sitúa. El resto de §7 está servido, incluida la ruta de **mapeos**
(`POST /document-versions/{id}/mappings`), que es la que permite que una misma fuente se guarde una
vez y se asigne a dos oposiciones sin duplicar el fichero.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query
from fastapi.responses import FileResponse

from opofuente.api.classification_schemas import MappingSchema, mapping_schema
from opofuente.api.deps import ArtifactStoreDep, LibraryServiceDep
from opofuente.api.error_responses import INGESTION_WRITE_ERRORS, RESOURCE_ERRORS
from opofuente.api.library_schemas import (
    CollectionItemRequestSchema,
    CollectionSchema,
    CreateCollectionRequestSchema,
    DocumentDetailSchema,
    DocumentPageSchema,
    DocumentSchema,
    EvidenceSchema,
    MappingRequestSchema,
    MarkSupersedesRequestSchema,
    PatchDocumentRequestSchema,
    PromoteRequestSchema,
    PromotionOutcomeSchema,
    RightsSchema,
    SectionDiffSchema,
    SectionSchema,
    VersionContentSchema,
    VersionDetailSchema,
    VersionDiffSchema,
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
    SectionDiff,
    SectionView,
    VersionDetail,
    VersionDiff,
    VersionText,
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


#: Tope de texto por lado en una comparación: un diff se lee, no se vuelca entero. Cuando se recorta
#: se dice (`*_truncated`), porque un texto cortado sin avisar se lee como si fuera todo el texto.
DIFF_TEXT_LIMIT = 4_000

#: Tipos que se pueden ver **en el navegador**. El resto se descarga: no se abre a ciegas lo que no
#: se sabe interpretar (contrato §7).
SAFE_INLINE_TYPES = frozenset(
    {
        "application/pdf",
        "image/png",
        "image/jpeg",
        "image/webp",
        "image/gif",
        "text/plain",
    }
)


def _recorte(texto: str | None) -> tuple[str | None, bool]:
    if texto is None or len(texto) <= DIFF_TEXT_LIMIT:
        return texto, False
    return texto[:DIFF_TEXT_LIMIT], True


def _diff_section(view: SectionDiff) -> SectionDiffSchema:
    izquierda, recortada_izquierda = _recorte(view.left)
    derecha, recortada_derecha = _recorte(view.right)
    return SectionDiffSchema(
        label=view.label,
        kind=view.kind,  # type: ignore[arg-type]
        left=izquierda,
        right=derecha,
        left_truncated=recortada_izquierda,
        right_truncated=recortada_derecha,
    )


def _diff(view: VersionDiff) -> VersionDiffSchema:
    return VersionDiffSchema(
        document_id=view.document_id,
        from_version_id=view.from_version_id,
        to_version_id=view.to_version_id,
        sections=[_diff_section(seccion) for seccion in view.sections],
        added=view.added,
        removed=view.removed,
        changed=view.changed,
        unchanged=view.unchanged,
        has_changes=view.has_changes,
    )


def _version_detail(view: VersionDetail) -> VersionDetailSchema:
    return VersionDetailSchema(
        document_id=view.document_id,
        document_title=view.document_title,
        document_type=view.document_type,
        owner_scope=view.owner_scope,  # type: ignore[arg-type]
        version=_version(view.version),
        mapping_count=view.mapping_count,
    )


def _version_content(view: VersionText) -> VersionContentSchema:
    return VersionContentSchema(
        document_version_id=view.document_version_id,
        representation_id=view.representation_id,
        text=view.text,
        offset=view.offset,
        limit=view.limit,
        total_chars=view.total_chars,
        truncated=view.truncated,
        quality=view.quality,
        warnings=list(view.warnings),
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
    collection_id: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> DocumentPageSchema:
    """Documentos de la biblioteca con su versión activa.

    `collection_id` filtra por colección (07_UI-UX §6), y el filtro se aplica en el servidor: la
    pantalla no se trae la biblioteca entera para descartarla después.
    """
    return _page(
        service.documents(
            document_type=document_type,
            owner_scope=owner_scope,
            collection_id=collection_id,
            limit=limit,
            offset=offset,
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


@router.delete(
    "/collections/{collection_id}/items",
    response_model=CollectionSchema,
    responses=INGESTION_WRITE_ERRORS,
    summary="Quita un sujeto de una colección (ruta añadida: no existe en el contrato)",
)
def remove_collection_item(
    collection_id: str, request: CollectionItemRequestSchema, service: LibraryServiceDep
) -> CollectionSchema:
    """Saca un sujeto de la colección **sin borrar nada del sujeto**.

    Ruta **añadida** al contrato: §7 no la lista, y sin ella una colección solo se podía llenar. No
    pide confirmación porque no retira material —el documento, la versión o la cita siguen donde
    estaban— y es idempotente: quitar lo que no estaba devuelve la colección como está.
    """
    coleccion = service.remove_from_collection(
        collection_id, subject_type=request.subject_type, subject_id=request.subject_id
    )
    if coleccion is None:
        raise NotFoundError("colección", collection_id)
    return _collection(coleccion)


@router.post(
    "/document-versions/{version_id}/mappings",
    response_model=MappingSchema,
    status_code=201,
    responses=INGESTION_WRITE_ERRORS,
    summary="Asigna una versión de documento a un nodo del programa",
)
def add_mapping(
    version_id: str, request: MappingRequestSchema, service: LibraryServiceDep
) -> MappingSchema:
    """Contrato §7: una fuente compartida se guarda una vez y se asigna a varias oposiciones.

    El mapeo apunta a la **versión**, no al artefacto: así una versión retirada deja de contar como
    cobertura sin tocar el material que ya se había asignado con ella. Se devuelve el mapeo tal y
    como queda (con su nodo), no solo su identificador: quien lo pide quiere verlo.
    """
    mapeo_id = service.add_mapping(
        version_id,
        curriculum_node_id=request.curriculum_node_id,
        coverage_type=request.coverage_type,
    )
    if mapeo_id is None:
        raise NotFoundError("versión de documento", version_id)
    mapeo = next(
        (candidato for candidato in service.mappings_of(version_id) if candidato.id == mapeo_id),
        None,
    )
    if mapeo is None:
        raise NotFoundError("mapeo", mapeo_id)
    return mapping_schema(mapeo)


@router.patch(
    "/documents/{document_id}",
    response_model=DocumentSchema,
    responses=INGESTION_WRITE_ERRORS,
    summary="Edita los metadatos de un documento",
)
def patch_document(
    document_id: str, request: PatchDocumentRequestSchema, service: LibraryServiceDep
) -> DocumentSchema:
    """Contrato §7. Lo que no se puede aplicar responde **409 con el motivo**, nunca a medias.

    Marcar un documento como público es una decisión con consecuencias: exige que los derechos de su
    versión activa consten revisados y permitan reutilizar el material.
    """
    if service.document(document_id) is None:
        raise NotFoundError("documento", document_id)
    resultado = service.update_document(document_id, changes=request.model_dump(exclude_unset=True))
    if resultado.document is None:
        raise ClassificationConflictError(
            resultado.reason or "El cambio de metadatos no se pudo aplicar"
        )
    return _document(resultado.document)


@router.get(
    "/document-versions/{version_id}",
    response_model=VersionDetailSchema,
    responses=RESOURCE_ERRORS,
    summary="Una versión con su documento",
)
def get_version(version_id: str, service: LibraryServiceDep) -> VersionDetailSchema:
    """Contrato §7: una versión sola, sin pedir la ficha entera del documento."""
    vista = service.version_detail(version_id)
    if vista is None:
        raise NotFoundError("versión de documento", version_id)
    return _version_detail(vista)


@router.get(
    "/document-versions/{version_id}/content",
    response_model=VersionContentSchema,
    responses=RESOURCE_ERRORS,
    summary="Texto extraído de la versión, por trozos",
)
def get_version_content(
    version_id: str,
    service: LibraryServiceDep,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=200_000)] = 20_000,
) -> VersionContentSchema:
    """Contrato §7. Si la extracción no dejó texto, se dice con su calidad: no se inventa nada."""
    trozo = service.version_text(version_id, offset=offset, limit=limit)
    if trozo is None:
        raise NotFoundError("versión de documento", version_id)
    return _version_content(trozo)


@router.get(
    "/document-versions/{version_id}/original",
    response_class=FileResponse,
    responses=RESOURCE_ERRORS,
    summary="El fichero original de una versión",
)
def get_version_original(
    version_id: str, service: LibraryServiceDep, artifacts: ArtifactStoreDep
) -> FileResponse:
    """Contrato §7: el original tal y como entró.

    `inline` solo para los tipos que se pueden ver con seguridad; el resto se descarga. El fichero
    se sirve desde el almacén (nunca desde una ruta de fuera) y un material en cuarentena **no se
    sirve**: está retenido a propósito y eso se dice con un 409, no con un 404 que parecería un
    fallo.
    """
    archivo = service.version_artifact(version_id)
    if archivo is None:
        raise NotFoundError("versión de documento", version_id)
    if archivo.is_quarantined:
        raise ClassificationConflictError(
            "El original está en cuarentena y no se sirve hasta que se revise"
        )
    ruta = artifacts.path_for_key(archivo.storage_key)
    if not ruta.is_file():
        raise NotFoundError("fichero original", version_id)
    return FileResponse(
        path=ruta,
        media_type=archivo.media_type,
        filename=archivo.original_name or version_id,
        content_disposition_type=(
            "inline" if archivo.media_type in SAFE_INLINE_TYPES else "attachment"
        ),
    )


@router.get(
    "/document-versions/{version_id}/mappings",
    response_model=list[MappingSchema],
    responses=RESOURCE_ERRORS,
    summary="Asignaciones de programa de una versión",
)
def list_version_mappings(version_id: str, service: LibraryServiceDep) -> list[MappingSchema]:
    """Contrato §7. Mismo formato de mapeo que sirve la clasificación: un mapeo es un mapeo."""
    if service.version_detail(version_id) is None:
        raise NotFoundError("versión de documento", version_id)
    return [mapping_schema(mapeo) for mapeo in service.mappings_of(version_id)]


@router.get(
    "/documents/{document_id}/diff",
    response_model=VersionDiffSchema,
    responses=RESOURCE_ERRORS,
    summary="Compara dos versiones del mismo documento",
)
def get_document_diff(
    document_id: str,
    service: LibraryServiceDep,
    from_version_id: Annotated[str, Query(min_length=1)],
    to_version_id: Annotated[str, Query(min_length=1)],
) -> VersionDiffSchema:
    """**Ruta no listada en el contrato §7**: se declara aquí en lugar de esconderse.

    El diff existe desde el primer día en el dominio y la spec lo pide («confirmar diff»), pero el
    contrato no fija su ruta. Compara el texto real de las secciones del mismo documento y **no
    fusiona nada**: informa y deja decidir.
    """
    comparacion = service.diff(
        document_id, from_version_id=from_version_id, to_version_id=to_version_id
    )
    if comparacion is None:
        raise NotFoundError("versión del documento", f"{from_version_id} / {to_version_id}")
    return _diff(comparacion)
