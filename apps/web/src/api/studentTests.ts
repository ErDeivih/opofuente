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
  /** La clave de esta pregunta está en revisión (§1): su conjunto discrepa de los apuntes entre el
   * 15 % y el 30 %. Entra en el test, pero el alumno lo ve antes de fiarse de la corrección. */
  in_review: boolean;
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
  questions_in_review: number;
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

/**
 * El desenlace de una pregunta del resultado. `void` no es un fallo del alumno: es una pregunta que
 * la plantilla no corrige (anulada, sin entrada o en conflicto) y la pantalla lo dice así.
 */
export type StudentResultOutcome = 'correct' | 'wrong' | 'blank' | 'void';

/** Un tema por su código legible: la respuesta a «¿de qué era esto?». */
export interface StudentTopicRef {
  code: string;
  title: string;
}

/** Una pregunta corregida, con lo que se marcó, la correcta y su tema. */
export interface StudentResultQuestion {
  position: number;
  is_reserve: boolean;
  part_code: string | null;
  part_name: string | null;
  stem: string;
  options: StudentOption[];
  chosen: string[];
  correct: string[];
  outcome: StudentResultOutcome;
  elapsed_ms: number | null;
  topics: StudentTopicRef[];
  /** La clave de esta pregunta está en revisión (§1). En el resultado importa más que en el test:
   * un fallo puede ser de la clave y no del alumno. */
  in_review: boolean;
}

/** Cómo fue el test en un tema: es el desglose que dice qué hay que repasar. */
export interface StudentResultTopic {
  code: string;
  title: string;
  correct: number;
  wrong: number;
  blank: number;
  graded: number;
  accuracy: number | null;
}

export interface StudentResult {
  session: StudentSession;
  parts: StudentPartScore[];
  total: StudentPartScore;
  official_available: boolean;
  official_note: string | null;
}

/** El resultado entero de un test terminado: la nota por parte, el tiempo y cada pregunta. */
export interface StudentSessionResult extends StudentResult {
  duration_seconds: number | null;
  questions: StudentResultQuestion[];
  topics: StudentResultTopic[];
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

/** El simulacro: variante completa o corta, y el bloque del supuesto en la completa. */
export interface NewMockExam {
  variant: 'full' | 'short';
  case_block: 'III' | 'IV';
}

/** Monta el simulacro con el perfil del examen y el bloque elegido para el supuesto. */
export function createStudentMockExam(body: NewMockExam): Promise<StudentSession> {
  return apiFetch<StudentSession>('/api/v1/student/mock-exams', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
}

/**
 * Monta el examen oficial que ocupa esa posición de la lista.
 *
 * Se pide por su **sitio en la lista** —el primero, el segundo—, igual que una respuesta se pide por
 * su fila: así esta capa sigue sin enseñar de dónde salen las preguntas de un test.
 */
export function createStudentOfficialExam(position: number): Promise<StudentSession> {
  return apiFetch<StudentSession>(`/api/v1/student/official-exams/${String(position)}/sessions`, {
    method: 'POST',
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

/**
 * El resultado entero de un test terminado: partes, tiempo y pregunta a pregunta.
 *
 * Es una lectura y no lo que devuelve «Terminar»: así la pantalla de resultado se puede abrir y
 * recargar sin volver a cerrar nada, y el resultado es el que se guardó al cerrar el test.
 */
export function getStudentResult(sessionId: string): Promise<StudentSessionResult> {
  return apiFetch<StudentSessionResult>(`/api/v1/student/sessions/${sessionId}/result`);
}
