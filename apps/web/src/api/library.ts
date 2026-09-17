import type { components } from '@opofuente/contracts';

import { apiFetch } from './client';

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

export type VersionStatus = Version['status'];
export type RightsReview = Rights['review_status'];
export type OwnerScope = DocumentSummary['owner_scope'];
export type MappingStatus = Mapping['status'];

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
  return apiFetch<DocumentPage>(`/api/v1/documents?${params.toString()}`);
}

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
 * Asignaciones de programa de un sujeto.
 *
 * Las de un documento se leen por **versión** (`subject_type=document_version`), que es lo que el
 * servidor sabe relacionar con un nodo del programa.
 */
export function fetchMappings(subjectType: string, subjectId: string): Promise<Mapping[]> {
  const params = new URLSearchParams({ subject_type: subjectType, subject_id: subjectId });
  return apiFetch<Mapping[]>(`/api/v1/mappings?${params.toString()}`);
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
