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
  /**
   * La hora del servidor en el momento de la respuesta, del **mismo reloj** que `started_at`.
   *
   * Es lo que permite poner el reloj del test en hora sin fiarse del reloj del navegador: la
   * diferencia entre las dos horas es el tiempo que lleva corriendo el test, medida con un solo reloj.
   */
  server_now: string;
  finished_at: string | null;
  created_at: string;
  result: StudentScore | null;
  practical_case_origin: string | null;
  /**
   * **El enunciado del supuesto**, cuando la sesión lleva uno de verdad (remate, punto 4).
   * Sus preguntas dicen «con los datos del caso, conteste»: sin el caso delante no se pueden
   * contestar, así que viaja con la sesión y no se busca después.
   */
  practical_case_statement: string | null;
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
  /** **La parte del examen** (`primera_parte`, `segunda_parte`): la hoja separa con ella y el
   *  enunciado del supuesto se enseña solo en la segunda. */
  part_code: string | null;
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
  /** Y la clave de esta pregunta es derivada (§1 del encargo F29): los apuntes, con su cita
   * verificada, y el modelo preguntado sin apuntes dicen la misma letra. Se enseña como «clave
   * revisada automáticamente». */
  derived_key: boolean;
}

export interface StudentSheetRow {
  position: number;
  /** **La parte**, para separar «Primera parte» y «Segunda parte · Supuesto» en la hoja.
   *  Opcional porque las filas que se construyen en el cliente no siempre la traen. */
  part_code?: string | null;
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
  /** Cuántas preguntas del test se corrigen con su clave derivada y llevan la marca «clave revisada
   * automáticamente» (§1 del encargo F29). */
  questions_derived: number;
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

/**
 * El apartado de los apuntes que contesta una pregunta concreta.
 *
 * Va con el **tema**, con el **capítulo** y con el **anclaje**
 * (`/temario/IV.7?capitulo=IV.7.2#apartado-udp`), no con el tema solo: «Ver en apuntes» tiene que
 * dejar al alumno en el párrafo que le explica su fallo, y la portada del tema no lo explica. El
 * servidor lo resuelve de la comprobación del motor (`question_note_anchors`), que es donde está la
 * frase que se verificó contra el texto.
 *
 * El **capítulo** (`epigraph_code`) hace falta desde que los apuntes se leen por epígrafes
 * oficiales: el párrafo puede estar en un capítulo que no es el primero, y abrir el primero dejaría
 * al alumno arriba, con el apartado fuera de la página. Es el fallo que se midió en el recorrido
 * (`scrollY = 0` con el apartado a 10.288 px).
 */
export interface StudentNoteAnchor {
  topic_code: string;
  anchor: string;
  /** El epígrafe oficial que contiene ese apartado. Vacío si el apartado no lo declara. */
  epigraph_code: string;
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
  /** `null` cuando los apuntes no contestan a esta pregunta: entonces no se ofrece la salida. */
  note_anchor: StudentNoteAnchor | null;
  /** La clave de esta pregunta está en revisión (§1). En el resultado importa más que en el test:
   * un fallo puede ser de la clave y no del alumno. */
  in_review: boolean;
  /** Y la clave de esta pregunta es derivada (§1 del encargo F29). En el resultado dice de dónde
   * sale la letra con la que se corrigió: no es la plantilla del conjunto. */
  derived_key: boolean;
  /** La explicación de la pregunta, ya corregida (M1 de la fase 3). */
  explanation?: string | null;
  /** La frase LITERAL de los apuntes que la sostiene, para enseñarla tal cual. */
  explanation_citation?: string | null;
  /** El apartado al que se ancla, si la pantalla quiere llevar al párrafo. */
  explanation_anchor_id?: string | null;
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

/**
 * El test en curso: la pregunta que toca y la hoja de respuestas entera.
 *
 * Con `position` se pide **una fila concreta** de la hoja, que es lo que hace usable la hoja de
 * respuestas: sin esto, una pregunta ya contestada no se puede volver a abrir (§3.2 del encargo F36,
 * defecto 5 del recorrido). Sin `position` la que toca es la primera sin contestar, que es el avance
 * automático de siempre.
 */
export function getStudentRun(sessionId: string, position?: number): Promise<StudentRun> {
  const consulta = position === undefined ? '' : `?position=${String(position)}`;
  return apiFetch<StudentRun>(`/api/v1/student/sessions/${sessionId}${consulta}`);
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

/** Cómo cerrar un test a medias: lo que hay que decirle a quien pulsa «Abandonar». */
export type StudentAbandonAction = 'deleted' | 'abandoned';

/**
 * Qué queda de un test abandonado.
 *
 * `deleted` no es un fallo: es que no se había contestado nada y no hay historial que conservar.
 * `abandoned` es el caso normal: lo contestado se guarda para repasar y el test **no cuenta** como
 * hecho ni entra en las notas.
 */
export interface StudentAbandon {
  session_id: string;
  action: StudentAbandonAction;
  detail: string;
}

/**
 * Abandona el test en curso y devuelve qué ha quedado de él.
 *
 * Es reintentable a propósito: abandonar dos veces devuelve el mismo parte en vez de fallar, y una
 * sesión ya terminada no se toca. Lo contestado se conserva (`abandoned`) salvo que no hubiera nada
 * contestado, y entonces la sesión se descarta.
 */
export function abandonStudentRun(sessionId: string): Promise<StudentAbandon> {
  return apiFetch<StudentAbandon>(`/api/v1/student/sessions/${sessionId}/abandon`, {
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
