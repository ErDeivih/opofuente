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

export interface StudentNotes {
  code: string;
  state: NotesState;
  generated_at: string | null;
  sections: StudentNoteSection[];
}

export interface StudentReport {
  section_key: string;
  reason: string;
  status: 'open' | 'reviewed' | 'dismissed';
  created_at: string;
}

/** Inicio: el test a medias, los fallos vencidos, el progreso por bloque y lo último hecho. */
export function getStudentOverview(): Promise<StudentOverview> {
  return apiFetch<StudentOverview>('/api/v1/student/overview');
}

/** El temario: bloques y temas en orden numérico, con lo disponible y el acierto. */
export function getStudentSyllabus(): Promise<StudentSyllabus> {
  return apiFetch<StudentSyllabus>('/api/v1/student/syllabus');
}

/** Un tema por su código: título, epígrafes, recuentos y progreso. */
export function getStudentTopic(code: string): Promise<StudentTopic> {
  return apiFetch<StudentTopic>(`/api/v1/student/topics/${encodeURIComponent(code)}`);
}

/** Los apuntes del tema, en orden de lectura, con su estado. Un borrador también se lee. */
export function getStudentNotes(code: string): Promise<StudentNotes> {
  return apiFetch<StudentNotes>(`/api/v1/student/topics/${encodeURIComponent(code)}/notes`);
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
