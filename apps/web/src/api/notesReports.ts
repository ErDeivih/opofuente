import type { components } from '@opofuente/contracts';

import { apiFetch } from './client';

/**
 * La bandeja de avisos del alumno, para el panel (F13 y F16, decisiones D2 y del bloque C).
 *
 * Todo lo que se lee y se escribe aquí viene del contrato generado: la pantalla no declara ni un
 * campo por su cuenta. Y se **escribe** por una sola ruta (`PATCH /notes-reports/{id}`), que es la
 * que deja el estado, la nota y su evento de auditoría en la misma transacción: no hay un segundo
 * camino para despachar un aviso desde la interfaz.
 */
export type NoteReportPage = components['schemas']['NoteReportListSchema'];
export type NoteReport = components['schemas']['NoteReportSchema'];
export type NoteReportUpdate = components['schemas']['NoteReportUpdateSchema'];

/** El vocabulario del estado, tal y como lo publica el servidor. */
export type NoteReportStatus = NoteReport['status'];

/** Cuántos avisos se leen de una vez. */
export const NOTE_REPORTS_LIMIT = 200;

/**
 * El estado de un aviso en palabras, y en el orden en que se despachan.
 *
 * Los cuatro salen del dominio (`domain/notes_reports.py`), no de la pantalla. `in_progress` es el
 * que se añadió en F16: sin él, un aviso está pendiente o está cerrado, y no había forma de decir
 * «lo he visto y estoy en ello» sin cerrarlo.
 */
export const NOTE_REPORT_STATUS_LABELS: Record<NoteReportStatus, string> = {
  open: 'Pendiente',
  in_progress: 'En curso',
  reviewed: 'Resuelto',
  dismissed: 'Descartado',
};

/** Lo que se lee bajo el estado, para saber qué significa cada uno sin abrir nada. */
export const NOTE_REPORT_STATUS_HELP: Record<NoteReportStatus, string> = {
  open: 'Nadie lo ha mirado todavía.',
  in_progress: 'Lo tienes en la mano.',
  reviewed: 'Lo has arreglado.',
  dismissed: 'Decidiste que no era un error.',
};

/** El orden de los filtros: el del trabajo, no el alfabético. */
export const NOTE_REPORT_STATUSES: readonly NoteReportStatus[] = [
  'open',
  'in_progress',
  'reviewed',
  'dismissed',
];

/**
 * En qué campo de la respuesta está la cifra de cada estado.
 *
 * El `open` del aviso se cuenta en el campo `pending`, que es el nombre que ese número tiene en el
 * contrato desde F13 (y el que el menú ya usa): el estado se llama `open` y lo que espera el
 * propietario se llama «pendiente». Traducirlo aquí, en un solo sitio, evita que cada pantalla
 * invente su propia correspondencia.
 */
export const NOTE_REPORT_COUNT_FIELD: Record<
  NoteReportStatus,
  'pending' | 'in_progress' | 'reviewed' | 'dismissed'
> = {
  open: 'pending',
  in_progress: 'in_progress',
  reviewed: 'reviewed',
  dismissed: 'dismissed',
};

/**
 * La dirección del apartado exacto del que habla el aviso.
 *
 * Es la misma que usa el índice de los apuntes (`#apartado-<ancla>`), así que un aviso lleva al
 * punto del texto y no a la pantalla del tema. Cuando el apartado ya no existe, el aviso lo dice y
 * **no** hay enlace: mandar a un ancla que no está dejaría al propietario buscando a mano, que es
 * justo lo que esta bandeja viene a evitar.
 */
export function notesSectionHref(aviso: NoteReport): string | null {
  if (aviso.section_title === null || aviso.section_title === undefined) {
    return null;
  }
  return `/temario/${aviso.topic_code}#apartado-${aviso.anchor}`;
}

/** Los avisos de la bandeja, con los filtros que el propietario puede pedir. */
export function fetchNoteReports(input: {
  status?: NoteReportStatus | null;
  topic?: string | null;
  q?: string | null;
  limit?: number;
}): Promise<NoteReportPage> {
  const params = new URLSearchParams({
    limit: String(input.limit ?? NOTE_REPORTS_LIMIT),
  });
  if (input.status !== null && input.status !== undefined) {
    params.set('status', input.status);
  }
  if (input.topic !== null && input.topic !== undefined && input.topic !== '') {
    params.set('topic', input.topic);
  }
  if (input.q !== null && input.q !== undefined && input.q.trim() !== '') {
    params.set('q', input.q.trim());
  }
  return apiFetch<NoteReportPage>(`/api/v1/notes-reports?${params.toString()}`);
}

/**
 * Despacha un aviso: el estado y, si se escribe, la nota de lo que se ha hecho.
 *
 * Una sola llamada por aviso y no un lote: a diferencia de la cola de clasificación, aquí cada
 * aviso es un texto que hay que leer y una decisión que hay que pensar —como mucho unas decenas por
 * sesión—, y guardar de uno en uno deja el estado escrito en el momento en que se decide.
 */
export function updateNoteReport(
  id: string,
  input: { status: NoteReportStatus; note?: string | null },
): Promise<NoteReport> {
  const cuerpo: NoteReportUpdate = { status: input.status };
  if (input.note !== null && input.note !== undefined && input.note.trim() !== '') {
    cuerpo.note = input.note;
  }
  return apiFetch<NoteReport>(`/api/v1/notes-reports/${encodeURIComponent(id)}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(cuerpo),
  });
}
