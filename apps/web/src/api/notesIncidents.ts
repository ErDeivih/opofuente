import type { components } from '@opofuente/contracts';

import { apiFetch } from './client';

/**
 * La bandeja del motor, para el panel (F18, §4.1 del objetivo).
 *
 * Lo que **no** se declara aquí: la categoría y el motivo se traducen a palabras en la pantalla
 * (`IncidentRow`/`IncidentsPage`), pero el **porqué** de cada incidencia no se escribe aquí: el
 * servidor manda `category_help`, que es el texto del dominio (`TEXTO_DE_CATEGORIA`). Copiarlo en el
 * cliente sería tener dos versiones del mismo párrafo, y la que se queda vieja es siempre la que
 * nadie lee.
 *
 * Y se **escribe** por una sola ruta (`PATCH /notes-incidents/{id}`), la que deja el estado, la nota
 * y su evento de auditoría en la misma transacción: no hay un segundo camino para despachar una
 * incidencia desde la interfaz.
 */
export type IncidentPage = components['schemas']['NotesIncidentListSchema'];
export type NotesIncident = components['schemas']['NotesIncidentSchema'];
export type IncidentUpdate = components['schemas']['NotesIncidentUpdateSchema'];

/** El vocabulario del estado, tal y como lo publica el servidor. */
export type IncidentStatus = NotesIncident['status'];

/** El vocabulario de la categoría: quién tiene que arreglarla. */
export type IncidentCategory = NotesIncident['category'];

/** El vocabulario del motivo: qué pasó exactamente. */
export type IncidentReason = NotesIncident['reason'];

/** Cuántas incidencias se leen de una vez. */
export const INCIDENTS_LIMIT = 200;

/**
 * La categoría en palabras, en el orden en que se trabaja.
 *
 * El orden no es alfabético: primero lo que hay que **escribir** en los apuntes, luego lo que hay que
 * **mirar** en una respuesta correcta, después la norma y por último la pregunta que no se pudo
 * situar. Es el orden del vocabulario del §2.1.4 del objetivo.
 *
 * Estos cuatro nombres **son los de la categoría del dominio**, tal como el objetivo los fija
 * (`hueco_sin_material`, `clave_sospechosa`, `pregunta_ambigua`, `norma_cambiada`). Por eso la
 * pantalla los pinta dentro de un contenedor `data-contenido`, igual que f16 hizo con los títulos del
 * programa oficial: son el **nombre de lo que el motor registró**, no una frase nuestra. Las frases
 * de la interfaz —las de esta pantalla y las de sus botones— no usan el vocabulario de dentro.
 */
export const INCIDENT_CATEGORY_LABELS: Record<IncidentCategory, string> = {
  hueco_sin_material: 'Hueco sin material',
  clave_sospechosa: 'Clave sospechosa',
  norma_cambiada: 'Norma cambiada',
  pregunta_ambigua: 'Pregunta ambigua',
};

/** Las cuatro categorías, en el orden en que se enseñan los filtros y las cifras. */
export const INCIDENT_CATEGORIES: readonly IncidentCategory[] = [
  'hueco_sin_material',
  'clave_sospechosa',
  'norma_cambiada',
  'pregunta_ambigua',
];

/**
 * El motivo en pocas palabras, para la ficha de cada incidencia.
 *
 * Es la etiqueta corta del `reason` del servidor, y está escrita **con las palabras de la interfaz**
 * («respuesta correcta», no «clave»): la aplicación reserva el vocabulario de dentro para lo que
 * enseña el motor tal cual. El párrafo que explica **qué significa** cada motivo lo manda él en
 * `category_help`, y ahí sí habla su lengua —es su texto, y viaja como contenido—.
 */
export const INCIDENT_REASON_LABELS: Record<IncidentReason, string> = {
  sin_frase_en_los_apuntes: 'La pregunta no tiene frase en los apuntes',
  letra_no_coincide: 'Los apuntes contestan con otra letra que la respuesta correcta',
  clave_contradice_la_norma: 'La respuesta correcta contradice la norma o el material',
  clave_sin_definir: 'La pregunta no tiene respuesta correcta con la que comprobarla',
  sin_materia_en_el_indice: 'La pregunta no cabe en ninguna materia del tema',
};

/**
 * El estado en palabras, y en el orden en que se despachan.
 *
 * Los cuatro salen del dominio (`domain/notes_incidents.py`) y son **los mismos** que los de la
 * bandeja de avisos del alumno: la aplicación ya tenía un vocabulario para decir «esto espera, lo
 * tengo en la mano, lo he resuelto, o el aviso se equivoca», y esta bandeja lo usa en vez de
 * estrenar otro.
 */
export const INCIDENT_STATUS_LABELS: Record<IncidentStatus, string> = {
  open: 'Pendiente',
  in_progress: 'En curso',
  reviewed: 'Resuelta',
  dismissed: 'Descartada',
};

/** Lo que se lee bajo el estado, para saber qué significa cada uno sin abrir nada. */
export const INCIDENT_STATUS_HELP: Record<IncidentStatus, string> = {
  open: 'Nadie la ha mirado todavía.',
  in_progress: 'La tienes en la mano.',
  reviewed: 'Has hecho lo que pedía su categoría.',
  dismissed: 'Has decidido que el motor se equivoca.',
};

/** El orden de los filtros: el del trabajo, no el alfabético. */
export const INCIDENT_STATUSES: readonly IncidentStatus[] = [
  'open',
  'in_progress',
  'reviewed',
  'dismissed',
];

/**
 * En qué campo de la respuesta está la cifra de cada estado.
 *
 * El `open` de la incidencia se cuenta en el campo `pending`, que es el nombre que ese número tiene
 * en el contrato: el estado se llama `open` y lo que espera al propietario se llama «pendiente».
 * Traducirlo aquí, en un solo sitio, evita que cada pantalla invente su propia correspondencia.
 */
export const INCIDENT_COUNT_FIELD: Record<
  IncidentStatus,
  'pending' | 'in_progress' | 'reviewed' | 'dismissed'
> = {
  open: 'pending',
  in_progress: 'in_progress',
  reviewed: 'reviewed',
  dismissed: 'dismissed',
};

/**
 * La dirección del apartado de los apuntes del que habla la incidencia.
 *
 * Es la misma que usa el índice de los apuntes (`#apartado-<ancla>`), así que una incidencia lleva al
 * punto del texto y no a la pantalla del tema. Cuando la pregunta **no se pudo situar en ninguna
 * materia** no hay ancla y no hay enlace: mandar a un ancla que no está dejaría al propietario
 * buscando a mano, que es justo lo que esta bandeja viene a evitar.
 */
export function incidentSectionHref(incidencia: NotesIncident): string | null {
  if (incidencia.anchor === '' || incidencia.section_title === null) {
    return null;
  }
  return `/temario/${incidencia.topic_code}#apartado-${incidencia.anchor}`;
}

/**
 * La dirección de la pregunta que la provoca, en el banco.
 *
 * Se abre en la pantalla de preguntas, que ya sabe enseñar la ficha de una pregunta por su
 * identificador (`?pregunta=…`), igual que la biblioteca abre un documento (`?documento=…`). Sin ese
 * enlace, la clave sospechosa habría que buscarla a mano en 17.000 preguntas.
 */
export function incidentQuestionHref(incidencia: NotesIncident): string {
  return `/admin/preguntas?pregunta=${encodeURIComponent(incidencia.question_version_id)}`;
}

/**
 * La dirección del material del que salió la pregunta, cuando consta.
 *
 * Es la **otra mitad** de una «norma cambiada»: la clave viene de este material y los apuntes dicen
 * otra cosa, así que hay que poder mirar el material sin buscarlo. Cuando la incidencia no dice de
 * dónde viene (o no consta), no hay enlace y la pantalla no lo inventa.
 */
export function incidentSourceHref(incidencia: NotesIncident): string | null {
  if (incidencia.source_document_id === null || incidencia.source_document_id === undefined) {
    return null;
  }
  return `/admin/biblioteca?documento=${encodeURIComponent(incidencia.source_document_id)}`;
}

/** El estado de la versión del material, en palabras (el vocabulario es del servidor). */
const VERSION_STATUS_TEXT: Record<string, string> = {
  candidate: 'sin aceptar',
  accepted: 'aceptada',
  outdated: 'desactualizada',
  superseded: 'sustituida',
  withdrawn: 'retirada',
  rejected: 'rechazada',
};

export function incidentVersionText(status: string | null | undefined): string | null {
  if (status === null || status === undefined) {
    return null;
  }
  return VERSION_STATUS_TEXT[status] ?? status;
}

/** Las incidencias de la bandeja, con los filtros que el propietario puede pedir. */
export function fetchNotesIncidents(input: {
  category?: IncidentCategory | null;
  status?: IncidentStatus | null;
  topic?: string | null;
  q?: string | null;
  limit?: number;
}): Promise<IncidentPage> {
  const params = new URLSearchParams({
    limit: String(input.limit ?? INCIDENTS_LIMIT),
  });
  if (input.category !== null && input.category !== undefined) {
    params.set('category', input.category);
  }
  if (input.status !== null && input.status !== undefined) {
    params.set('status', input.status);
  }
  if (input.topic !== null && input.topic !== undefined && input.topic !== '') {
    params.set('topic', input.topic);
  }
  if (input.q !== null && input.q !== undefined && input.q.trim() !== '') {
    params.set('q', input.q.trim());
  }
  return apiFetch<IncidentPage>(`/api/v1/notes-incidents?${params.toString()}`);
}

/**
 * Despacha una incidencia: el estado y, si se escribe, la nota de lo que se ha decidido.
 *
 * Una sola llamada por incidencia y no un lote: cada una es una pregunta que hay que leer y un
 * criterio que hay que aplicar, así que guardar de una en una deja la decisión escrita en el momento
 * en que se toma.
 */
export function updateNotesIncident(
  id: string,
  input: { status: IncidentStatus; note?: string | null },
): Promise<NotesIncident> {
  const cuerpo: IncidentUpdate = { status: input.status };
  if (input.note !== null && input.note !== undefined && input.note.trim() !== '') {
    cuerpo.note = input.note;
  }
  return apiFetch<NotesIncident>(`/api/v1/notes-incidents/${encodeURIComponent(id)}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(cuerpo),
  });
}
