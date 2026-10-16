import { apiFetch } from './client';
import type { StudentSession } from './studentTests';

/**
 * La lectura de la zona del alumno (`/api/v1/student/*`): el temario, el progreso, los apuntes de un
 * tema y el aviso «esto está mal» (F13).
 *
 * Es el hermano de `studentTests.ts` —el test en curso— y comparte su regla: **el tema viaja por su
 * código legible** (`IV.7`, `IV.10`) y por aquí no sale ningún identificador interno. Lo que sí
 * viaja, desde F13, es el `anchor` de cada apartado de los apuntes: es la dirección del párrafo
 * dentro de la página y con ella el índice lleva a su sitio.
 */

/** Cómo están los apuntes de un tema: publicados, en borrador o sin escribir. */
export type NotesState = 'published' | 'draft' | 'none';

export interface StudentOppositionRef {
  code: string;
  name: string;
}

export interface StudentTopicProgress {
  code: string;
  number: number | null;
  title: string;
  available_questions: number;
  answered: number;
  correct: number;
  accuracy: number | null;
  due_reviews: number;
  notes_state: NotesState;
}

export interface StudentBlockProgress {
  code: string;
  title: string;
  position: number;
  available_questions: number;
  answered: number;
  correct: number;
  accuracy: number | null;
  due_reviews: number;
  topics: StudentTopicProgress[];
}

export interface StudentOverview {
  opposition: StudentOppositionRef;
  in_progress: StudentSession | null;
  due_reviews: number;
  blocks: StudentBlockProgress[];
  recent_tests: StudentSession[];
}

export interface StudentSyllabus {
  opposition: StudentOppositionRef;
  blocks: StudentBlockProgress[];
}

export interface StudentEpigraph {
  code: string;
  title: string;
}

export interface StudentTopic {
  code: string;
  number: number | null;
  title: string;
  description: string | null;
  block_code: string;
  block_title: string;
  epigraphs: StudentEpigraph[];
  progress: StudentTopicProgress | null;
}

export interface StudentNoteSection {
  /** Su sitio en el índice (1..N). */
  number: number;
  key: string;
  title: string;
  epigraph_code: string;
  /** La dirección del apartado dentro de la página: el índice y el aviso apuntan aquí. */
  anchor: string;
  body_markdown: string;
  /** Cuántas preguntas **de este tema** se contestan con este apartado. */
  questions_covered: number;
}

/**
 * Un apartado **del índice**, sin su texto.
 *
 * Es lo que permite que el índice viaje entero aunque la página sirva un solo capítulo: con esto se
 * puede enseñar la lista completa de apartados y saber a qué capítulo pertenece un anclaje que no es
 * del capítulo abierto.
 */
export interface StudentNoteChapterSection {
  number: number;
  key: string;
  title: string;
  anchor: string;
  questions_covered: number;
}

/** Un capítulo de los apuntes: un **epígrafe oficial** del tema, con sus apartados. */
export interface StudentNoteChapter {
  /** El código del epígrafe (`IV.7.2`): es lo que lleva `?capitulo=` en la dirección. */
  code: string;
  title: string;
  /** Su lugar en el tema (1..N), para «anterior» y «siguiente». */
  position: number;
  sections: StudentNoteChapterSection[];
}

export interface StudentNotes {
  code: string;
  state: NotesState;
  generated_at: string | null;
  /** El texto del capítulo abierto. */
  sections: StudentNoteSection[];
  /** El capítulo que viaja en `sections`; `null` si el tema no tiene apuntes. */
  chapter: string | null;
  /** El índice completo: todos los capítulos con sus apartados, sin sus textos. */
  chapters: StudentNoteChapter[];
}

export interface StudentReport {
  section_key: string;
  reason: string;
  status: 'open' | 'reviewed' | 'dismissed';
  created_at: string;
}

/** El progreso: bloques, los cinco temas más flojos, el historial y cuántos tests hay hechos. */
export interface StudentProgress {
  opposition: StudentOppositionRef;
  blocks: StudentBlockProgress[];
  weakest_topics: StudentTopicProgress[];
  history: StudentSession[];
  /** Tests **terminados** de esta persona: no los que caben en el historial. */
  tests_finished: number;
}

/** Una parte del simulacro, con lo que publica el perfil del examen y nada más. */
export interface StudentMockExamPart {
  code: string;
  name: string;
  ordinary_items: number | null;
  reserve_items: number | null;
  score_max: number | null;
  pass_score: number | null;
  penalty: string | null;
  time_minutes: number | null;
}

/** Una variante del simulacro: qué cae, cuánto dura y qué es lo que **no** es. */
export interface StudentMockExamVariant {
  variant: 'full' | 'short';
  title: string;
  time_limit_minutes: number | null;
  parts: StudentMockExamPart[];
  note: string | null;
}

export interface StudentMockCaseTopic {
  code: string;
  title: string;
  available_questions: number;
}

export interface StudentMockCaseBlock {
  code: string;
  title: string;
  topics: StudentMockCaseTopic[];
}

/** El simulacro antes de montarlo: sus dos variantes y los bloques del supuesto. */
export interface StudentMockExamPlan {
  opposition: StudentOppositionRef;
  full: StudentMockExamVariant;
  short: StudentMockExamVariant;
  case_blocks: StudentMockCaseBlock[];
}

/** Un examen oficial importado, por su sitio en la lista. */
export interface StudentOfficialExam {
  position: number;
  title: string;
  held_at: string | null;
  questions: number;
  ready: boolean;
  /** De dónde sale el examen (D10): `age`, `otra_administracion` o `desconocida`. */
  origin_scope: 'age' | 'otra_administracion' | 'desconocida';
}

export interface StudentOfficialExams {
  exams: StudentOfficialExam[];
}

/** Una pregunta fallada: qué decía, de qué era, cuándo y cuántas veces. */
export interface StudentMistake {
  stem: string;
  topics: { code: string; title: string }[];
  last_failed_at: string;
  times_failed: number;
  due: boolean;
}

export interface StudentMistakeTopic {
  code: string;
  title: string;
  failed: number;
  due: number;
}

export interface StudentMistakes {
  total: number;
  due_total: number;
  questions: StudentMistake[];
  topics: StudentMistakeTopic[];
}

/** Un tamaño de test ofrecido, con lo que duraría con el reloj del test puesto. */
export interface StudentTestCount {
  questions: number;
  minutes: number;
}

/** Lo que la pantalla de Tests puede ofrecer antes de montar nada (F22). */
export interface StudentTestPlan {
  counts: StudentTestCount[];
  /** La regla del reloj, escrita una vez por el servidor: la pantalla la pinta tal cual. */
  timed_note: string;
  /** El tiempo que lleva el test **sin** el reloj del test. `null`: la convocatoria no lo publica. */
  convocation_minutes: number | null;
}

/** Inicio: el test a medias, los fallos vencidos, el progreso por bloque y lo último hecho. */
export function getStudentOverview(): Promise<StudentOverview> {
  return apiFetch<StudentOverview>('/api/v1/student/overview');
}

/** El temario: bloques y temas en orden numérico, con lo disponible y el acierto. */
export function getStudentSyllabus(): Promise<StudentSyllabus> {
  return apiFetch<StudentSyllabus>('/api/v1/student/syllabus');
}

/** El progreso: acierto por bloque y por tema, los cinco más flojos y el historial de tests. */
export function getStudentProgress(): Promise<StudentProgress> {
  return apiFetch<StudentProgress>('/api/v1/student/progress');
}

/**
 * Qué va a caer en el simulacro, leído del perfil del examen.
 *
 * Es lo que permite elegir sabiendo qué se elige: las partes con sus preguntas y sus reservas, el
 * tiempo, la penalización y los temas de cada bloque del supuesto. Nada de esto se escribe a mano en
 * la pantalla; si el perfil no publica un dato, llega `null` y se dice que no está.
 */
export function getStudentMockExamPlan(): Promise<StudentMockExamPlan> {
  return apiFetch<StudentMockExamPlan>('/api/v1/student/mock-exams');
}

/**
 * Los exámenes oficiales importados. Una lista vacía es un estado, no un error: quiere decir que
 * todavía no se ha importado ninguno, y la pantalla lo dice con esas palabras.
 */
export function getStudentOfficialExams(): Promise<StudentOfficialExams> {
  return apiFetch<StudentOfficialExams>('/api/v1/student/official-exams');
}

/** Las preguntas que fallaste la última vez, con su tema, su fecha y cuántas veces. */
export function getStudentMistakes(): Promise<StudentMistakes> {
  return apiFetch<StudentMistakes>('/api/v1/student/mistakes');
}

/**
 * El plan de un test: qué tamaños se ofrecen y cuánto dura cada uno con el reloj puesto (F22).
 *
 * Se lee antes de montar nada y **no se recalcula en la pantalla**: la regla del reloj es del
 * servidor, y es el mismo que después se lo pone a la sesión. `convocation_minutes` es el tiempo que
 * lleva un test cuando **no** se le pone el reloj del test: no es cero, es el de la convocatoria.
 */
export function getStudentTestPlan(): Promise<StudentTestPlan> {
  return apiFetch<StudentTestPlan>('/api/v1/student/tests/plan');
}

/** Un tema por su código: título, epígrafes, recuentos y progreso. */
export function getStudentTopic(code: string): Promise<StudentTopic> {
  return apiFetch<StudentTopic>(`/api/v1/student/topics/${encodeURIComponent(code)}`);
}

/**
 * Los apuntes de un tema, **un capítulo cada vez**, con el índice completo y su estado.
 *
 * `capitulo` es el código del epígrafe oficial (`IV.7.2`). Sin él, el servidor sirve el primero. Un
 * capítulo que ya no existe **también** sirve el primero: la respuesta dice en `chapter` cuál se
 * sirvió y la pantalla corrige la dirección, en vez de dejar al alumno en un error.
 *
 * Un borrador también se lee.
 */
export function getStudentNotes(code: string, capitulo?: string): Promise<StudentNotes> {
  const ruta = `/api/v1/student/topics/${encodeURIComponent(code)}/notes`;
  const consulta = capitulo === undefined ? '' : `?capitulo=${encodeURIComponent(capitulo)}`;
  return apiFetch<StudentNotes>(`${ruta}${consulta}`);
}

/**
 * Avisa de que un apartado está mal («esto está mal», decisión D2).
 *
 * Se manda la **clave** del apartado y el motivo en una línea: el anclaje lo pone el servidor a
 * partir del apartado que existe hoy, así que la pantalla no puede apuntar a un párrafo que no es.
 */
export function reportNotesMistake(
  code: string,
  body: { section_key: string; reason: string },
): Promise<StudentReport> {
  return apiFetch<StudentReport>(`/api/v1/student/topics/${encodeURIComponent(code)}/reports`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
}
