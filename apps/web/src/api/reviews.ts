import type { components } from '@opofuente/contracts';

import { apiFetch } from './client';

/**
 * Errores, repaso y exportación (S10), leídos del contrato generado (§10 y §11).
 *
 * Nada de lo que se ve en la pantalla lo decide el cliente: la fecha del próximo repaso, el motivo de
 * estar en la cola, el intervalo nuevo y los avisos de la exportación vienen del servidor. Aquí solo
 * se declara a quién se llama y qué se devuelve.
 */
export type ReviewItem = components['schemas']['ReviewItemSchema'];
export type ReviewEvent = components['schemas']['ReviewEventSchema'];
export type DueItem = components['schemas']['DueItemSchema'];
export type ReviewQueue = components['schemas']['ReviewQueueSchema'];
export type ReviewStats = components['schemas']['ReviewStatsSchema'];
export type LearningError = components['schemas']['ErrorSchema'];
export type LearningErrorDetail = components['schemas']['ErrorDetailSchema'];
export type ConceptGroup = components['schemas']['ConceptGroupSchema'];
export type Concept = components['schemas']['ConceptSchema'];
export type MasteryProgram = components['schemas']['MasteryProgramSchema'];
export type NodeMastery = components['schemas']['NodeMasterySchema'];
export type ExportResult = components['schemas']['ExportSchema'];
export type ExportRequest = components['schemas']['ExportRequestSchema'];

export type ErrorCause = LearningError['cause'];
export type ReviewOutcome = ReviewEvent['outcome'];
export type MasteryLevel = NodeMastery['level'];

/** Causas del fallo, con lo que significa cada una (06_QUESTIONS §8). */
export const ERROR_CAUSES: readonly ErrorCause[] = [
  'knowledge',
  'confusion',
  'reading',
  'time',
  'calculation',
  'ambiguous',
  'other',
];

export const CAUSE_LABEL: Record<ErrorCause, string> = {
  knowledge: 'no lo sabía',
  confusion: 'lo confundí con otra cosa',
  reading: 'leí mal el enunciado',
  time: 'me faltó tiempo',
  calculation: 'me equivoqué al calcular',
  ambiguous: 'la pregunta es ambigua',
  other: 'otra cosa',
};

export const MASTERY_LABEL: Record<MasteryLevel, string> = {
  no_data: 'sin datos',
  insufficient_evidence: 'evidencia insuficiente',
  low: 'bajo',
  medium: 'medio',
  high: 'alto',
};

export function fetchReviewQueue(oppositionId: string | null): Promise<ReviewQueue> {
  const query = oppositionId === null ? '' : `?opposition_id=${encodeURIComponent(oppositionId)}`;
  return apiFetch<ReviewQueue>(`/api/v1/reviews/due${query}`);
}

export function fetchLearningErrors(oppositionId: string | null): Promise<ConceptGroup> {
  const query = oppositionId === null ? '' : `?opposition_id=${encodeURIComponent(oppositionId)}`;
  return apiFetch<ConceptGroup>(`/api/v1/learning-errors${query}`);
}

export function fetchLearningError(errorId: string): Promise<LearningErrorDetail> {
  return apiFetch<LearningErrorDetail>(`/api/v1/learning-errors/${encodeURIComponent(errorId)}`);
}

export function fetchReviewHistory(reviewId: string): Promise<ReviewEvent[]> {
  return apiFetch<ReviewEvent[]>(`/api/v1/reviews/${encodeURIComponent(reviewId)}/history`);
}

export function fetchMastery(oppositionId: string | null): Promise<MasteryProgram> {
  const query = oppositionId === null ? '' : `?opposition_id=${encodeURIComponent(oppositionId)}`;
  return apiFetch<MasteryProgram>(`/api/v1/reviews/mastery${query}`);
}

export function classifyError(
  attemptId: string,
  input: {
    cause: ErrorCause;
    concept_label: string | null;
    curriculum_node_id: string | null;
    note: string | null;
  },
): Promise<LearningError> {
  return apiFetch<LearningError>(
    `/api/v1/attempts/${encodeURIComponent(attemptId)}/error-classification`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(input),
    },
  );
}

export function completeReview(
  reviewId: string,
  input: {
    outcome: 'correct' | 'wrong';
    confidence: 'low' | 'medium' | 'high' | null;
    cause: ErrorCause | null;
    note: string | null;
  },
): Promise<ReviewItem> {
  return apiFetch<ReviewItem>(`/api/v1/reviews/${encodeURIComponent(reviewId)}/complete`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  });
}

export function snoozeReview(reviewId: string, days: number): Promise<ReviewItem> {
  return apiFetch<ReviewItem>(`/api/v1/reviews/${encodeURIComponent(reviewId)}/snooze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ days }),
  });
}

export function resolveError(
  errorId: string,
  input: { resolved: boolean; note: string | null },
): Promise<LearningError> {
  return apiFetch<LearningError>(
    `/api/v1/learning-errors/${encodeURIComponent(errorId)}/resolution`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(input),
    },
  );
}

export function exportBank(
  format: 'anki-csv' | 'markdown',
  input: ExportRequest,
): Promise<ExportResult> {
  return apiFetch<ExportResult>(`/api/v1/exports/${format}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  });
}

/** Cuánto queda por repasar, en una frase (la misma cifra que enseña la cola). */
export function queueSummary(queue: ReviewQueue): string {
  const { due, active } = queue.stats;
  if (active === 0) {
    return 'sin repasos: se crean al fallar una pregunta';
  }
  if (due === 0) {
    return `${String(active)} en cola, ninguno vencido`;
  }
  return `${String(due)} de ${String(active)} vencidos`;
}
