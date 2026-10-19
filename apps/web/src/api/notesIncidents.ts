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
export type TrayPage = components['schemas']['TraySchema'];
export type TraySet = components['schemas']['TraySetSchema'];
export type TrayBulkRequest = components['schemas']['TrayBulkRequestSchema'];
export type TrayBulkResult = components['schemas']['TrayBulkResultSchema'];

/** Las tres acciones en bloque del §2.1 del cierre del objetivo. */
export type TrayAction = TrayBulkRequest['action'];

/** El vocabulario del estado, tal y como lo publica el servidor. */
export type IncidentStatus = NotesIncident['status'];

/** El vocabulario de la categoría: quién tiene que arreglarla. */
export type IncidentCategory = NotesIncident['category'];

/** El vocabulario del motivo: qué pasó exactamente. */
export type IncidentReason = NotesIncident['reason'];

/**
 * Cuántas incidencias se leen de una vez al desplegar un banco.
 *
 * Cincuenta y no doscientas: cada incidencia viaja con el enunciado entero de su pregunta, su
 * motivo y su apartado, y doscientas llenan la pantalla de texto donde el trabajo real queda cuesta
 * abajo. Lo que no cabe se pide con «ver más» (`AVISOS_POR_TANDA` en la fila del banco).
 */
export const INCIDENTS_LIMIT = 50;

/**
 * La categoría en palabras, en el orden del §2 del documento de ajustes.
 *
 * El orden **es el de comprobación**, y por eso no es el alfabético ni el de tamaño: primero lo que
 * está roto por su forma —una pregunta mal importada no se juzga por su clave—, después lo que no se
 * puede juzgar porque su clave está en cuarentena, y solo entonces lo que hay que mirar en la clave,
 * en los apuntes o en la norma. Es el orden en el que hay que trabajar la bandeja.
 *
 * Estos seis nombres **son los de la categoría del dominio**, tal como el §2 los fija
 * (`pregunta_mal_importada`, `clave_no_fiable`, `clave_sospechosa`, `norma_cambiada`,
 * `hueco_sin_material`, `pregunta_ambigua`). Por eso la pantalla los pinta dentro de un contenedor
 * `data-contenido`, igual que f16 hizo con los títulos del programa oficial: son el **nombre de lo
 * que el motor registró**, no una frase nuestra. Las frases de la interfaz —las de esta pantalla y
 * las de sus botones— no usan el vocabulario de dentro.
 */
export const INCIDENT_CATEGORY_LABELS: Record<IncidentCategory, string> = {
  pregunta_mal_importada: 'Pregunta mal importada',
  clave_no_fiable: 'Clave no fiable',
  clave_sospechosa: 'Clave sospechosa',
  norma_cambiada: 'Norma cambiada',
  hueco_sin_material: 'Hueco sin material',
  pregunta_ambigua: 'Pregunta ambigua',
};

/** Las seis categorías, en el orden de comprobación del §2: es el orden de los filtros. */
export const INCIDENT_CATEGORIES: readonly IncidentCategory[] = [
  'pregunta_mal_importada',
  'clave_no_fiable',
  'clave_sospechosa',
  'norma_cambiada',
  'hueco_sin_material',
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
  propuesta_lista: 'Propuesta lista',
  no_son_preguntas: 'No son preguntas',
};

/** Lo que se lee bajo el estado, para saber qué significa cada uno sin abrir nada. */
export const INCIDENT_STATUS_HELP: Record<IncidentStatus, string> = {
  open: 'Nadie la ha mirado todavía.',
  in_progress: 'La tienes en la mano.',
  reviewed: 'Has hecho lo que pedía su categoría.',
  dismissed: 'Has decidido que el motor se equivoca.',
  propuesta_lista: 'La resolvió una regla: hay clave derivada y solo falta aprobarla en bloque.',
  no_son_preguntas: 'Una regla mecánica la sacó de la bandeja: no hay nada que decidir.',
};

/** El orden de los filtros: el del trabajo, no el alfabético. */
export const INCIDENT_STATUSES: readonly IncidentStatus[] = [
  'open',
  'in_progress',
  'propuesta_lista',
  'no_son_preguntas',
  'reviewed',
  'dismissed',
];

/**
 * En qué campo de la respuesta está la cifra de cada estado.
 *
 * El `open` de la incidencia se cuenta en el campo `pending`, que es el nombre que ese número tiene
 * en el contrato: el estado se llama `open` y lo que espera al propietario se llama «pendiente».
 * Traducirlo aquí, en un solo sitio, evita que cada pantalla invente su propia correspondencia.
 *
 * Los dos estados que añade la resolución automática (`propuesta_lista` y `no_son_preguntas`) **no
 * tienen contador propio** en la lista: su cifra se cuenta donde se decide, que es en la bandeja por
 * conjunto —las propuestas de un conjunto y lo que ya no espera—. Poner aquí un cero fijo sería
 * enseñar un número que nadie ha medido.
 */
export const INCIDENT_COUNT_FIELD: Partial<
  Record<IncidentStatus, 'pending' | 'in_progress' | 'reviewed' | 'dismissed'>
> = {
  open: 'pending',
  in_progress: 'in_progress',
  reviewed: 'reviewed',
  dismissed: 'dismissed',
};

/**
 * Lo que anotó la corrida, **sin la frase que ya se está leyendo encima**.
 *
 * El motor escribe en `detail` la explicación de la categoría y, detrás, lo que pasó en esa
 * pregunta concreta («pregunta: … clave: c (draft) · los apuntes dicen: a · vueltas: 1»). La
 * explicación de la categoría viaja además en `category_help`, y la ficha de una incidencia enseña
 * las dos: el resultado era la misma frase tres veces —en el título, en el cuerpo y otra vez al
 * empezar el detalle—, que es lo que el propietario vio en la bandeja.
 *
 * No son tres cosas distintas, es **una frase guardada dos veces**: la escribe el motor al dejar la
 * incidencia y la API la manda otra vez como texto de la categoría. Se quita aquí, al pintar, y no
 * en la base: lo guardado es el rastro de la corrida y no se reescribe para que una pantalla se lea
 * mejor.
 */
export function detailSinLaFraseDeLaCategoria(
  detail: string,
  categoryHelp: string,
): string {
  const anotado = detail.trim();
  const frase = categoryHelp.trim();
  if (frase === '' || !anotado.startsWith(frase)) {
    return anotado;
  }
  return anotado.slice(frase.length).trim();
}

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
  set_id?: string | null;
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
  if (input.set_id !== null && input.set_id !== undefined && input.set_id !== '') {
    params.set('set', input.set_id);
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

/**
 * La bandeja **agrupada por conjunto** (F31, §2 del cierre del objetivo).
 *
 * Una fila por conjunto, con lo que espera dentro y las acciones que admite, más **la cifra** que
 * mide si la bandeja sirve: las entradas que de verdad dependen del criterio del propietario. La
 * cifra la calcula el servidor —`entradas_de_decision`— y la pantalla no la recompone: contarla en
 * dos sitios acaba diciendo dos cosas.
 */
export function fetchNotesTray(page = 1): Promise<TrayPage> {
  const consulta = page > 1 ? `?pagina=${String(page)}` : '';
  return apiFetch<TrayPage>(`/api/v1/notes-incidents/tray${consulta}`);
}

/** Qué hace cada acción en bloque, dicho por el servidor: aquí no se reescribe. */
export function fetchTrayActions(): Promise<Record<string, string>> {
  return apiFetch<Record<string, string>>('/api/v1/notes-incidents/tray/actions');
}

/**
 * Aplica una acción en bloque a un conjunto entero.
 *
 * Es **una** llamada por conjunto y no una por incidencia: la decisión es del conjunto —«sus claves
 * derivadas», «fuera», «no son preguntas»— y mandar doscientas peticiones sería contar doscientas
 * decisiones donde hubo una. El servidor rechaza los conjuntos oficiales con un 409 y su motivo.
 */
export function dispatchTrayBulk(input: {
  action: TrayAction;
  set_id: string;
  note?: string | null;
}): Promise<TrayBulkResult> {
  const cuerpo: TrayBulkRequest = { action: input.action, set_id: input.set_id };
  if (input.note !== null && input.note !== undefined && input.note.trim() !== '') {
    cuerpo.note = input.note;
  }
  return apiFetch<TrayBulkResult>('/api/v1/notes-incidents/tray/bulk', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(cuerpo),
  });
}
