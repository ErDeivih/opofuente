import type { components } from '@opofuente/contracts';

import { apiFetch } from './client';

/**
 * Sesiones de estudio (S07), leídas del contrato generado (§10).
 *
 * Nada de lo que se ve aquí se calcula en el cliente: la puntuación, los desenlaces y qué preguntas
 * cuentan los decide el servidor. La pantalla solo enseña lo que le llega, incluida la frase que dice
 * que la calificación oficial no está disponible.
 */
export type StudySession = components['schemas']['SessionSchema'];
export type SessionPage = components['schemas']['SessionPageSchema'];
export type SessionQuestion = components['schemas']['SessionQuestionSchema'];
export type SessionQuestionCorrection = components['schemas']['CorrectionSchema'];
export type CurrentQuestion = components['schemas']['CurrentQuestionSchema'];
export type AnswerOutcome = components['schemas']['AnswerOutcomeSchema'];
export type SessionResult = components['schemas']['SessionResultSchema'];
export type PartScore = components['schemas']['PartScoreSchema'];
export type Score = components['schemas']['ScoreSchema'];
export type Attempt = components['schemas']['AttemptSchema'];
export type SessionReview = components['schemas']['ReviewSchema'];
export type SessionSource = components['schemas']['SessionSourceSchema'];
export type CreateSession = components['schemas']['CreateSessionSchema'];
export type AnswerRequest = components['schemas']['AnswerRequestSchema'];
export type NavigateRequest = components['schemas']['NavigateRequestSchema'];

export type SessionMode = StudySession['mode'];
export type SessionStatus = StudySession['status'];
export type FeedbackName = StudySession['feedback'];
export type AttemptOutcome = SessionQuestionCorrection['outcome'];
export type Confidence = NonNullable<AnswerRequest['confidence']>;

/** Modos que el contrato declara: son los que el servidor implementa de verdad. */
export const SESSION_MODES: readonly SessionMode[] = ['practice', 'official_exam'];

/** Cuándo se puede ver la corrección. La pantalla no decide esto: lo dice el servidor. */
export const FEEDBACKS: readonly FeedbackName[] = ['immediate', 'at_end'];

/** Confianza declarada al responder (opcional). */
export const CONFIDENCES: readonly Confidence[] = ['low', 'medium', 'high'];

/** Cuántas sesiones se piden de una vez. */
export const PAGE_LIMIT = 50;

export function fetchSessions(oppositionId: string | null): Promise<SessionPage> {
  const params = new URLSearchParams({ limit: String(PAGE_LIMIT), offset: '0' });
  if (oppositionId !== null) {
    params.set('opposition_id', oppositionId);
  }
  return apiFetch<SessionPage>(`/api/v1/study-sessions?${params.toString()}`);
}

export function createSession(input: CreateSession): Promise<StudySession> {
  return apiFetch<StudySession>('/api/v1/study-sessions', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  });
}

export function fetchSession(sessionId: string): Promise<StudySession> {
  return apiFetch<StudySession>(`/api/v1/study-sessions/${encodeURIComponent(sessionId)}`);
}

export function startSession(sessionId: string): Promise<StudySession> {
  return apiFetch<StudySession>(
    `/api/v1/study-sessions/${encodeURIComponent(sessionId)}/start`,
    { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({}) },
  );
}

export function fetchCurrentQuestion(sessionId: string): Promise<CurrentQuestion> {
  return apiFetch<CurrentQuestion>(
    `/api/v1/study-sessions/${encodeURIComponent(sessionId)}/current-question`,
  );
}

export function navigateSession(
  sessionId: string,
  input: NavigateRequest,
): Promise<CurrentQuestion> {
  return apiFetch<CurrentQuestion>(
    `/api/v1/study-sessions/${encodeURIComponent(sessionId)}/navigate`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(input),
    },
  );
}

export function answerQuestion(
  sessionId: string,
  input: AnswerRequest,
): Promise<AnswerOutcome> {
  return apiFetch<AnswerOutcome>(
    `/api/v1/study-sessions/${encodeURIComponent(sessionId)}/answers`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(input),
    },
  );
}

export function finishSession(sessionId: string): Promise<SessionResult> {
  return apiFetch<SessionResult>(
    `/api/v1/study-sessions/${encodeURIComponent(sessionId)}/finish`,
    { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({}) },
  );
}

export function fetchSessionResult(sessionId: string): Promise<SessionResult> {
  return apiFetch<SessionResult>(
    `/api/v1/study-sessions/${encodeURIComponent(sessionId)}/result`,
  );
}

export function fetchSessionReview(sessionId: string): Promise<SessionReview> {
  return apiFetch<SessionReview>(
    `/api/v1/study-sessions/${encodeURIComponent(sessionId)}/review`,
  );
}

/** La puntuación, con su fracción exacta delante: el decimal es para leerlo (ADR-010). */
export function formatScore(score: Score): string {
  return score.denominator === 1 ? score.fraction : `${score.decimal} (${score.fraction})`;
}

/** ¿Se puede corregir lo que se acaba de responder? Lo decide el modo, no la pantalla. */
export function showsCorrectionNow(session: StudySession): boolean {
  return session.feedback === 'immediate';
}

/** Enunciado recortado para listados. */
export function shortStem(stem: string, limite = 90): string {
  return stem.length <= limite ? stem : `${stem.slice(0, limite).trimEnd()}…`;
}
