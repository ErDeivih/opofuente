import type { components } from '@opofuente/contracts';

import { formatearPorcentaje } from '../lib/numeros';
import { apiFetch } from './client';

/**
 * La revisión de los apuntes, para el panel (F24, §4.3 del objetivo).
 *
 * Lo que **no** se declara aquí: las frases del motivo. El servidor manda cada razón ya escrita y con
 * su cifra (`reasons[].text` y `reasons[].figure`), así que la pantalla las pinta tal cual. Copiarlas
 * en el cliente sería tener dos versiones del mismo párrafo, y la que se queda vieja es siempre la que
 * nadie lee. Lo mismo con el listón: viaja en `coverage_threshold` y no se escribe aquí.
 *
 * Y se **escribe** por una sola ruta (`POST /notes-review/{codigo}/decision`), la que deja la decisión
 * y su evento de auditoría en la misma transacción: no hay un segundo camino para aprobar o rechazar
 * unos apuntes desde la interfaz.
 */
export type NotesReviewPage = components['schemas']['NotesReviewListSchema'];
export type NotesReviewTopic = components['schemas']['NotesReviewTopicSchema'];
export type NotesReviewFile = components['schemas']['NotesReviewFileSchema'];
export type NotesReviewSection = components['schemas']['NotesReviewSectionSchema'];
export type NotesReviewCounters = components['schemas']['NotesReviewCountersSchema'];
export type NotesReviewReason = components['schemas']['NotesReviewReasonSchema'];
export type NotesReviewResult = components['schemas']['NotesReviewDecisionResultSchema'];

/** La decisión sobre un tema: son dos, aprobar y rechazar (el vocabulario lo fija el servidor). */
export type ReviewDecisionName = 'approved' | 'rejected';

/** El estado de los apuntes de un tema: el mismo vocabulario que la zona del alumno. */
export type NotesStateName = NotesReviewTopic['state'];

/**
 * El estado en palabras, para la tabla del panel.
 *
 * `published` es «tiene versión archivada» y `draft` es «tiene texto y nadie lo ha archivado»; el
 * tercero es un tema del que todavía no se ha escrito nada. Son las mismas tres palabras que usa la
 * zona del alumno (`NotesStateChip`), porque son el mismo estado del mismo tema.
 */
export const NOTES_STATE_LABELS: Record<NotesStateName, string> = {
  published: 'Publicado',
  draft: 'En borrador',
  none: 'Sin apuntes',
};

export const NOTES_STATE_HELP: Record<NotesStateName, string> = {
  published: 'Ya pasó las dos puertas y su texto quedó archivado.',
  draft: 'Tiene apartados escritos y su texto no está archivado: se lee, pero no está publicado.',
  none: 'Todavía no hay apartados escritos de este tema.',
};

/**
 * La clase de la marca de cada estado: **las mismas** que usa la zona del alumno.
 *
 * Publicado va con la marca neutra, en borrador con la de borrador y sin apuntes con la de vacío: son
 * los tres colores que la suite ya tiene verificados (contraste y axe incluidos), y estrenar un cuarto
 * para decir lo mismo sería tener dos formas de pintar el mismo estado. Están aquí, al lado de las
 * palabras, para que las dos pantallas que enseñan el estado usen la misma pareja palabra/color.
 */
export const NOTES_STATE_CLASS: Record<NotesStateName, string> = {
  published: '',
  draft: 'marca--borrador',
  none: 'marca--vacia',
};

/** La decisión en palabras, y en el orden en el que se lee. */
export const REVIEW_DECISION_LABELS: Record<'approved' | 'rejected', string> = {
  approved: 'Aprobado',
  rejected: 'Rechazado',
};

/**
 * De qué puerta habla cada bloqueo, cuando un tema aprobado no se ha podido publicar.
 *
 * El servidor dice **qué** puerta (`blocked_by`) y la cifra va en el motivo; aquí solo se pone en
 * palabras lo que significa, sin repetir ningún número.
 */
export const REVIEW_BLOCK_LABELS: Record<'cobertura' | 'forma', string> = {
  cobertura: 'La cobertura no llega al listón del §2.3',
  forma: 'La forma del texto no pasa las comprobaciones',
};

/** El listón del §2.3, en porcentaje, para enseñarlo junto a la cifra medida. */
export function thresholdPercent(threshold: number): string {
  return `${String(Math.round(threshold * 100))} %`;
}

/**
 * El porcentaje de una cobertura medida, o nada si no hay denominador.
 *
 * Se calcula **del par de números que manda el servidor** y no de un porcentaje ya redondeado: así la
 * pantalla puede enseñar «489 de 542» y su porcentaje, y las dos cifras dicen lo mismo.
 */
export function coveragePercent(coverage: [number, number] | null | undefined): string | null {
  if (coverage === null || coverage === undefined) {
    return null;
  }
  const [cubiertas, total] = coverage;
  if (total <= 0) {
    return null;
  }
  // Aquí la décima **hace falta**: el listón es el 90 % y una cobertura de 89,7 % no es lo mismo que
  // una de 90,2 %. Se pide con el formateador común (§2.2), no con un `toFixed` que se acuerde o no de
  // la coma según el día.
  return formatearPorcentaje(cubiertas / total, { decimales: 1 });
}

/** La tabla de la revisión: los temas con su estado, sus cifras y el motivo de los borradores. */
export function fetchNotesReview(): Promise<NotesReviewPage> {
  return apiFetch<NotesReviewPage>('/api/v1/notes-review');
}

/** Los contadores del menú, sin medir nada: cuántos borradores esperan una decisión. */
export function fetchNotesReviewSummary(): Promise<NotesReviewCounters> {
  return apiFetch<NotesReviewCounters>('/api/v1/notes-review/summary');
}

/** La ficha de un tema: sus apartados tal como se leerán en la zona del alumno. */
export function fetchNotesReviewFile(code: string): Promise<NotesReviewFile> {
  return apiFetch<NotesReviewFile>(`/api/v1/notes-review/${encodeURIComponent(code)}`);
}

/**
 * Aprueba o rechaza los apuntes de un tema.
 *
 * Una sola llamada: la decisión, su nota y su evento de auditoría entran juntos. El motivo del rechazo
 * lo exige el servidor (422 con su campo) y la pantalla no deja mandarlo vacío, pero la regla no vive
 * aquí.
 */
export function decideNotesReview(
  code: string,
  input: { decision: 'approved' | 'rejected'; note?: string | null },
): Promise<NotesReviewResult> {
  const cuerpo: { decision: 'approved' | 'rejected'; note?: string } = {
    decision: input.decision,
  };
  if (input.note !== null && input.note !== undefined && input.note.trim() !== '') {
    cuerpo.note = input.note;
  }
  return apiFetch<NotesReviewResult>(
    `/api/v1/notes-review/${encodeURIComponent(code)}/decision`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(cuerpo),
    },
  );
}

/**
 * Los apartados de un tema, **los peores primero** cuando se piden así.
 *
 * «Peor» es lo que queda sin resolver en ese apartado (en conflicto con la respuesta correcta, dudoso
 * o sin frase), que es la cifra que el servidor manda en `worst`. El orden de lectura —el de verdad,
 * el que tiene el alumno— es el de `position`, y es el que se usa cuando no se piden los peores.
 */
export function orderSections(
  sections: readonly NotesReviewSection[],
  worstFirst: boolean,
): NotesReviewSection[] {
  const copia = [...sections];
  if (!worstFirst) {
    return copia.sort((uno, otro) => uno.position - otro.position);
  }
  return copia.sort((uno, otro) => otro.worst - uno.worst || uno.position - otro.position);
}
