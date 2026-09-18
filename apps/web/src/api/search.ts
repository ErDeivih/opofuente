import type { components } from '@opofuente/contracts';

import { apiFetch } from './client';

/**
 * Búsqueda y RAG (S09), leídos del contrato generado (§8).
 *
 * Nada de lo que se ve aquí lo decide la pantalla: el estado de la respuesta, la estrategia usada, lo
 * que se quedó fuera del corpus y las citas vienen del servidor. La pantalla solo enseña lo que le
 * llega **con su procedencia**.
 */
export type SearchResult = components['schemas']['SearchResultSchema'];
export type SearchHit = components['schemas']['SearchHitSchema'];
export type SearchRequest = components['schemas']['SearchRequestSchema'];
export type AskRequest = components['schemas']['AskRequestSchema'];
export type EvidenceSpan = components['schemas']['EvidenceSpanSchema'];
export type RagQuery = components['schemas']['RagQuerySchema'];
export type RagAnswer = components['schemas']['AnswerSchema'];
export type RagClaim = components['schemas']['ClaimSchema'];
export type Retrieval = components['schemas']['RetrievalSchema'];

export type AnswerStatus = RagAnswer['status'];
export type AnswerStyle = AskRequest['style'];
export type VersionMode = SearchRequest['version_mode'];
export type Strategy = SearchResult['strategy'];

/** Estilos de respuesta que el contrato declara, con lo que hace cada uno. */
export const ANSWER_STYLES: readonly AnswerStyle[] = ['brief', 'teach', 'compare'];

/** Modos de versión: vigente por defecto; el histórico se pide a propósito. */
export const VERSION_MODES: readonly VersionMode[] = ['current', 'explicit_historical'];

export function searchCorpus(input: SearchRequest): Promise<SearchResult> {
  return apiFetch<SearchResult>('/api/v1/search', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  });
}

export function askCorpus(input: AskRequest): Promise<RagQuery> {
  return apiFetch<RagQuery>('/api/v1/rag/queries', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  });
}

export function fetchRagQuery(queryId: string): Promise<RagQuery> {
  return apiFetch<RagQuery>(`/api/v1/rag/queries/${encodeURIComponent(queryId)}`);
}

export function fetchRetrieval(queryId: string): Promise<Retrieval> {
  return apiFetch<Retrieval>(`/api/v1/rag/queries/${encodeURIComponent(queryId)}/retrieval`);
}

export function fetchEvidenceSpan(spanId: string): Promise<EvidenceSpan> {
  return apiFetch<EvidenceSpan>(`/api/v1/evidence-spans/${encodeURIComponent(spanId)}`);
}

/** La cita de un fragmento: etiqueta, página y título, nunca «ver documento». */
export function citationText(span: EvidenceSpan): string {
  if (span.citation_label !== null && span.citation_label !== undefined) {
    return span.citation_label;
  }
  if (span.page !== null && span.page !== undefined) {
    return `${span.document_title}, pág. ${String(span.page)}`;
  }
  return span.document_title;
}

/** Enlace a la ficha del documento en la Biblioteca (el original se abre ahí). */
export function documentHref(span: EvidenceSpan): string {
  return `/biblioteca?documento=${encodeURIComponent(span.document_id)}`;
}
