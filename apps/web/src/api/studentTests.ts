import { apiFetch } from './client';

/**
 * El test del alumno: montarlo, correrlo y cerrarlo (`/api/v1/student/*`).
 *
 * Estas rutas son de la **capa del alumno**, no del panel: su contrato no tiene evidencia, ni
 * conjunto, ni clave, ni identificadores de pregunta. Por eso la pregunta viaja por su **posición
 * en la hoja de respuestas** (la fila 12) y la respuesta se pide por esa posición: es lo que el
 * alumno tiene delante.
 */

export type StudentFeedback = 'immediate' | 'at_end';
export type StudentFilter = 'all' | 'unseen' | 'failed' | 'flagged';
export type StudentConfidence = 'low' | 'medium' | 'high';
export type StudentOutcome = 'correct' | 'wrong' | 'blank';

export type StudentSessionMode =
  | 'practice'
  | 'error_review'
  | 'official_exam'
  | 'mock_exam'
  | 'diagnostic';

export type StudentStatus = 'draft' | 'running' | 'finished' | 'abandoned';

export interface StudentScore {
  correct: number;
  wrong: number;
  blank: number;
  points: string;
  points_decimal: string;
  maximum: number | null;
  passed: boolean | null;
}

export interface StudentSession {
  id: string;
  mode: StudentSessionMode;
  status: StudentStatus;
  title: string;
  total_questions: number;
  answered_questions: number;
  time_limit_minutes: number | null;
  started_at: string | null;
  finished_at: string | null;
  created_at: string;
  result: StudentScore | null;
  practical_case_origin: string | null;
}

export interface StudentOption {
  key: string;
  text: string;
}

export interface StudentCorrection {
  outcome: StudentOutcome;
  correct: string[];
  reason: string | null;
}

export interface StudentQuestion {
  position: number;
  is_reserve: boolean;
  stem: string;
  question_type: string;
  options: StudentOption[];
  answered: boolean;
  chosen: string[];
  confidence: StudentConfidence | null;
  correction: StudentCorrection | null;
}

export interface StudentSheetRow {
  position: number;
  answered: boolean;
  chosen: string[];
  confidence: StudentConfidence | null;
  outcome: StudentOutcome | null;
  correct: string[];
}

export interface StudentRun {
  session: StudentSession;
  total: number;
  answered: number;
  pending: number;
  finished: boolean;
  position: number | null;
  question: StudentQuestion | null;
  sheet: StudentSheetRow[];
}

export interface StudentPartScore {
  part_code: string | null;
  part_name: string | null;
  kind: string;
  correct: number;
  wrong: number;
  blank: number;
  score: string;
  score_decimal: string;
  score_max: number | null;
  pass_score: number | null;
  passed: boolean | null;
  verdict_note: string | null;
}

export interface StudentResult {
  session: StudentSession;
  parts: StudentPartScore[];
  total: StudentPartScore;
  official_available: boolean;
  official_note: string | null;
}

export interface NewTest {
  nodes: string[];
  count: number;
  filter?: StudentFilter;
  feedback?: StudentFeedback;
  timed?: boolean;
}

/** Monta un test de los temas elegidos. Si no hay tantas preguntas como se piden, entran las que hay. */
export function createStudentTest(body: NewTest): Promise<StudentSession> {
  return apiFetch<StudentSession>('/api/v1/student/tests', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
}

/** El test en curso: la pregunta que toca y la hoja de respuestas entera. */
export function getStudentRun(sessionId: string): Promise<StudentRun> {
  return apiFetch<StudentRun>(`/api/v1/student/sessions/${sessionId}`);
}

/** Arranca el test. Arrancar uno que ya corre no cambia nada. */
export function startStudentRun(sessionId: string): Promise<StudentRun> {
  return apiFetch<StudentRun>(`/api/v1/student/sessions/${sessionId}/start`, { method: 'POST' });
}

/** Contesta la pregunta de una fila de la hoja y devuelve el test como queda. */
export function answerStudentQuestion(
  sessionId: string,
  body: {
    position: number;
    chosen: string[];
    elapsed_ms: number;
    confidence?: StudentConfidence | null;
  },
): Promise<StudentRun> {
  return apiFetch<StudentRun>(`/api/v1/student/sessions/${sessionId}/answers`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
}

/** Cierra el test y devuelve el resultado con la nota de cada parte. */
export function finishStudentRun(sessionId: string): Promise<StudentResult> {
  return apiFetch<StudentResult>(`/api/v1/student/sessions/${sessionId}/finish`, {
    method: 'POST',
  });
}
