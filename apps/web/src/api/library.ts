import type { components } from '@opofuente/contracts';

import { apiBaseUrl, apiFetch } from './client';

/**
 * Tipos de la biblioteca (S05), leídos del contrato generado.
 *
 * La pantalla no declara ninguno de estos datos por su cuenta: el estado de la versión activa, si
 * los derechos están restringidos y los recuentos vienen del servidor tal cual
 * (`08_API-CONTRACT §7`).
 */
export type DocumentSummary = components['schemas']['DocumentSchema'];
export type DocumentDetail = components['schemas']['DocumentDetailSchema'];
export type DocumentPage = components['schemas']['DocumentPageSchema'];
export type Version = components['schemas']['VersionSchema'];
export type Rights = components['schemas']['RightsSchema'];
export type Section = components['schemas']['SectionSchema'];
export type Evidence = components['schemas']['EvidenceSchema'];
export type PromotionOutcome = components['schemas']['PromotionOutcomeSchema'];
export type Mapping = components['schemas']['MappingSchema'];
export type VersionDiff = components['schemas']['VersionDiffSchema'];
export type SectionDiff = components['schemas']['SectionDiffSchema'];

export type VersionStatus = Version['status'];
export type RightsReview = Rights['review_status'];
export type OwnerScope = DocumentSummary['owner_scope'];
export type MappingStatus = Mapping['status'];
export type CoverageType = Mapping['coverage_type'];

/** Tipos de cobertura que admite el servidor al asignar una versión a un nodo del programa. */
export const COVERAGE_TYPES: readonly CoverageType[] = ['mention', 'partial', 'complete'];

/**
 * Cuántos documentos se piden de una vez.
 *
 * Es el tope por defecto del servidor: la biblioteca es personal y el listado se lee entero para
 * poder filtrar sin dar la impresión de que hay documentos que no están.
 */
export const DOCUMENT_PAGE_LIMIT = 50;

/** Estados desde los que el servidor admite aceptar una versión (los demás responden 409). */
export const ACCEPTABLE_VERSION_STATUSES: ReadonlySet<string> = new Set(['candidate', 'outdated']);

/**
 * Estados en los que una versión **sustituye** a otra sin destruirla: la antigua se conserva.
 */
export const SUPERSEDING_VERSION_STATUSES: ReadonlySet<string> = new Set([
  'candidate',
  'accepted',
  'outdated',
]);

export interface DocumentQuery {
  /** Tipo documental del vocabulario del servidor, o `null` para no filtrar. */
  documentType: string | null;
  /** Ámbito del documento (`public`, `private_user`, `generated`), o `null`. */
  ownerScope: string | null;
  /**
   * Colección por la que filtrar, o `null`.
   *
   * El filtro lo aplica **el servidor** (`GET /documents?collection_id=…`), porque un miembro de una
   * colección puede ser una versión, un artefacto, una representación, una sección o una evidencia, y
   * resolver eso en el navegador obligaría a traerse la biblioteca entera.
   */
  collectionId?: string | null;
}

export function fetchDocuments(query: DocumentQuery): Promise<DocumentPage> {
  const params = new URLSearchParams({
    limit: String(DOCUMENT_PAGE_LIMIT),
    offset: '0',
  });
  if (query.documentType !== null) {
    params.set('document_type', query.documentType);
  }
  if (query.ownerScope !== null) {
    params.set('owner_scope', query.ownerScope);
  }
  if (query.collectionId !== null && query.collectionId !== undefined) {
    params.set('collection_id', query.collectionId);
  }
  return apiFetch<DocumentPage>(`/api/v1/documents?${params.toString()}`);
}

export type Collection = components['schemas']['CollectionSchema'];

export function fetchCollections(): Promise<Collection[]> {
  return apiFetch<Collection[]>('/api/v1/collections');
}

export function createCollection(input: {
  name: string;
  description: string | null;
}): Promise<Collection> {
  return apiFetch<Collection>('/api/v1/collections', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  });
}

/**
 * Añade un sujeto a una colección. El servidor no duplica: añadir dos veces el mismo sujeto deja la
 * colección con un solo miembro.
 */
export function addToCollection(
  collectionId: string,
  input: { subjectType: SubjectType; subjectId: string },
): Promise<Collection> {
  return apiFetch<Collection>(
    `/api/v1/collections/${encodeURIComponent(collectionId)}/items`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ subject_type: input.subjectType, subject_id: input.subjectId }),
    },
  );
}

/**
 * Quita un sujeto de una colección **sin borrar el sujeto** (ruta añadida al contrato).
 *
 * Es idempotente y no pide confirmación: el documento, la versión o la cita siguen donde estaban, y
 * lo único que cambia es en qué colecciones aparecen.
 */
export function removeFromCollection(
  collectionId: string,
  subjectId: string,
  subjectType: SubjectType = 'document_version',
): Promise<Collection> {
  return apiFetch<Collection>(
    `/api/v1/collections/${encodeURIComponent(collectionId)}/items`,
    {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ subject_type: subjectType, subject_id: subjectId }),
    },
  );
}

/** Tipos de sujeto que una colección admite, tal como los declara el contrato. */
export type SubjectType =
  | 'artifact'
  | 'representation'
  | 'document_version'
  | 'section'
  | 'evidence';

/** Cómo se llama cada tipo de sujeto en la pantalla. */
export const SUBJECT_TYPE_LABEL: Record<SubjectType, string> = {
  artifact: 'fichero',
  representation: 'representación (texto extraído)',
  document_version: 'versión de documento',
  section: 'sección',
  evidence: 'cita de evidencia',
};

export function fetchDocument(documentId: string): Promise<DocumentDetail> {
  return apiFetch<DocumentDetail>(`/api/v1/documents/${encodeURIComponent(documentId)}`);
}

/** Versiones del documento, en el orden del servidor. La antigua no desaparece. */
export function fetchVersions(documentId: string): Promise<Version[]> {
  return apiFetch<Version[]>(`/api/v1/documents/${encodeURIComponent(documentId)}/versions`);
}

/** Estructura de una versión: de aquí sale la sección (y su página) que se cita. */
export function fetchSections(versionId: string): Promise<Section[]> {
  return apiFetch<Section[]>(
    `/api/v1/document-versions/${encodeURIComponent(versionId)}/sections`,
  );
}

/** Evidencia citable de una versión: el fragmento concreto que se puede citar y abrir. */
export function fetchEvidence(versionId: string): Promise<Evidence[]> {
  return apiFetch<Evidence[]>(
    `/api/v1/document-versions/${encodeURIComponent(versionId)}/evidence`,
  );
}

/**
 * Asignaciones de programa de un sujeto, en general (clasificación).
 *
 * Para las asignaciones de un **documento** la ruta del contrato §7 es la de su versión
 * (`fetchVersionMappings`): es la que relaciona el material con un nodo del programa.
 */
export function fetchMappings(subjectType: string, subjectId: string): Promise<Mapping[]> {
  const params = new URLSearchParams({ subject_type: subjectType, subject_id: subjectId });
  return apiFetch<Mapping[]>(`/api/v1/mappings?${params.toString()}`);
}

/** Asignaciones de una versión concreta (contrato §7: `GET /document-versions/{id}/mappings`). */
export function fetchVersionMappings(versionId: string): Promise<Mapping[]> {
  return apiFetch<Mapping[]>(
    `/api/v1/document-versions/${encodeURIComponent(versionId)}/mappings`,
  );
}

/**
 * Asigna una versión a un nodo del programa.
 *
 * El mapeo apunta a la **versión**, no al fichero: la misma fuente se guarda una vez y se asigna a
 * varias oposiciones. Nace aceptado y auditado, porque lo pide una persona y no el motor.
 */
export function assignVersionToNode(
  versionId: string,
  input: { curriculumNodeId: string; coverageType: CoverageType },
): Promise<Mapping> {
  return apiFetch<Mapping>(
    `/api/v1/document-versions/${encodeURIComponent(versionId)}/mappings`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        curriculum_node_id: input.curriculumNodeId,
        coverage_type: input.coverageType,
      }),
    },
  );
}

/**
 * Retira una asignación de programa.
 *
 * El servidor responde 204 sin cuerpo y deja la retirada auditada; el material no se borra.
 */
export function removeMapping(mappingId: string): Promise<void> {
  return apiFetch<void>(`/api/v1/curriculum-mappings/${encodeURIComponent(mappingId)}`, {
    method: 'DELETE',
  });
}

/**
 * Dirección del **fichero original** de una versión (contrato §7: `GET /document-versions/{id}/original`).
 *
 * Se sirve desde la API, no desde una ruta del disco: el servidor decide el `Content-Disposition`
 * (`inline` solo para tipos seguros) y responde 409 si el material está en cuarentena.
 */
export function versionOriginalUrl(versionId: string): string {
  return `${apiBaseUrl()}/api/v1/document-versions/${encodeURIComponent(versionId)}/original`;
}

/**
 * Compara dos versiones del **mismo** documento, sección a sección.
 *
 * Lo hace el servidor: aquí no se comparan dos textos leídos por separado, porque eso no sería un
 * diff. El texto de cada lado viene recortado si es largo, y `*_truncated` dice cuándo.
 */
export function fetchVersionDiff(
  documentId: string,
  fromVersionId: string,
  toVersionId: string,
): Promise<VersionDiff> {
  const params = new URLSearchParams({
    from_version_id: fromVersionId,
    to_version_id: toVersionId,
  });
  return apiFetch<VersionDiff>(
    `/api/v1/documents/${encodeURIComponent(documentId)}/diff?${params.toString()}`,
  );
}

/**
 * Acepta una versión: promoción crítica, confirmada por una persona y auditada en el servidor.
 *
 * Si el servidor no la puede aplicar responde 409 con `classification_conflict` y su motivo, y
 * **nada cambia**: la interfaz muestra ese motivo en lugar de dar la operación por hecha.
 */
export function acceptVersion(documentId: string, versionId: string): Promise<PromotionOutcome> {
  const ruta = `/api/v1/documents/${encodeURIComponent(documentId)}/versions`;
  return apiFetch<PromotionOutcome>(
    `${ruta}/${encodeURIComponent(versionId)}/accept`,
    { method: 'POST' },
  );
}

/** Confirma que una versión sustituye a otra. La sustituida se conserva y sigue siendo citable. */
export function markSupersedes(
  documentId: string,
  versionId: string,
  supersededId: string,
): Promise<PromotionOutcome> {
  const ruta = `/api/v1/documents/${encodeURIComponent(documentId)}/versions`;
  return apiFetch<PromotionOutcome>(
    `${ruta}/${encodeURIComponent(versionId)}/mark-supersedes`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ superseded_id: supersededId }),
    },
  );
}

/**
 * ¿Los derechos de esta versión impiden compartirla?
 *
 * Lo decide el servidor con `is_restricted`, y se respeta tal cual. Solo hay un caso que la versión
 * no puede contestar porque no trae registro de derechos: sin declaración **no consta** licencia, y
 * lo desconocido se trata como restringido (09_SECURITY §8, `domain/documents.py`). La interfaz no
 * deduce permisos: cuando no hay dato, avisa de que no lo hay.
 */
export function isRestricted(version: Version): boolean {
  return version.rights === null || version.rights === undefined || version.rights.is_restricted;
}

/** ¿La versión activa es una propuesta de cambio todavía sin aceptar? */
export function isCandidate(version: Version): boolean {
  return !version.is_accepted || version.status === 'candidate';
}

/** Nombre legible de la versión: su etiqueta, o su identificador para poder referirse a ella. */
export function versionName(version: Version): string {
  return version.version_label ?? version.id;
}
