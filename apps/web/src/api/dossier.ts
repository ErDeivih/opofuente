import type { components } from '@opofuente/contracts';

import { apiFetch } from './client';

export type Dossier = components['schemas']['DossierSchema'];
export type DossierSource = components['schemas']['DossierSourceSchema'];
export type DossierPassage = components['schemas']['DossierPassageSchema'];
export type DossierHole = components['schemas']['DossierHoleSchema'];
export type DossierVersion = components['schemas']['DossierVersionSchema'];
export type DossierArchive = components['schemas']['DossierArchiveSchema'];
export type DossierNotes = components['schemas']['DossierNotesSchema'];
export type DossierNoteSection = components['schemas']['DossierNoteSectionSchema'];

/** El tema: lo que el corpus dice de él, citado, con sus huecos y con qué se construyó (S13). */
export function fetchDossier(nodeId: string): Promise<Dossier> {
  return apiFetch<Dossier>(`/api/v1/curriculum-nodes/${encodeURIComponent(nodeId)}/dossier`);
}

/** Archiva la lectura actual como versión del dossier. Repetir la misma lectura no crea otra. */
export function archiveDossier(nodeId: string): Promise<DossierArchive> {
  return apiFetch<DossierArchive>(
    `/api/v1/curriculum-nodes/${encodeURIComponent(nodeId)}/dossier/versions`,
    { method: 'POST' },
  );
}

export function fetchDossierVersions(nodeId: string): Promise<DossierVersion[]> {
  return apiFetch<DossierVersion[]>(
    `/api/v1/curriculum-nodes/${encodeURIComponent(nodeId)}/dossier/versions`,
  );
}

export function fetchDossierVersion(nodeId: string, versionId: string): Promise<Dossier> {
  return apiFetch<Dossier>(
    `/api/v1/curriculum-nodes/${encodeURIComponent(nodeId)}/dossier/versions/${encodeURIComponent(versionId)}`,
  );
}

/**
 * La etiqueta de cita de un pasaje: la que guardó la extracción y, si no consta, página y documento.
 *
 * Se prefiere la guardada porque es la que el lector del documento usa para llevar al sitio correcto.
 */
export function passageCitation(pasaje: DossierPassage, documentTitle: string): string {
  if (pasaje.citation_label !== null && pasaje.citation_label !== undefined) {
    return pasaje.citation_label;
  }
  if (pasaje.page !== null && pasaje.page !== undefined) {
    return `${documentTitle}, pág. ${String(pasaje.page)}`;
  }
  return documentTitle;
}

/** Enlace a la ficha del documento en la Biblioteca, que es donde se abre el original. */
export function sourceHref(documentId: string): string {
  return `/biblioteca?documento=${encodeURIComponent(documentId)}`;
}

/**
 * La frase de un hueco. Los códigos son del servidor y se traducen aquí, como los avisos de
 * extracción: el hueco se explica, no se enseña como un identificador.
 */
const HOLE_TEXT: Record<DossierHole['code'], string> = {
  sin_material: 'Ningún material de tu biblioteca está asignado a este tema todavía.',
  sin_texto: 'Hay material asignado a este tema, pero todavía no tiene texto que citar.',
  no_citable: 'Hay texto asignado a este tema, pero no sostiene una cita (lo dice el motivo).',
  sin_version_aceptada:
    'Todo lo que llega a este tema está en versiones sin aceptar: se lee, pero no como material confirmado.',
  mapeo_provisional:
    'Parte de estas fuentes se asignaron a este tema sin confirmar: revísalas en Revisión.',
  repetido_en_otra_fuente: 'El mismo texto aparece en más de una fuente: se cita una vez y se dice dónde más está.',
};

export function holeText(hueco: DossierHole): string {
  const base = HOLE_TEXT[hueco.code];
  if (hueco.count > 1) {
    return `${base} (${String(hueco.count)} casos)`;
  }
  return base;
}

/** El estado de la versión de un documento, en palabras (el vocabulario es del servidor). */
const VERSION_STATUS_TEXT: Record<string, string> = {
  candidate: 'sin aceptar',
  accepted: 'aceptada',
  outdated: 'desactualizada',
  superseded: 'sustituida',
  withdrawn: 'retirada',
  rejected: 'rechazada',
};

export function versionStatusText(status: string): string {
  return VERSION_STATUS_TEXT[status] ?? status;
}

/** Cómo sostiene el material a este tema: un mapeo confirmado o uno todavía sin confirmar. */
export function mappingText(mappings: string[], provisional: boolean): string {
  if (mappings.length === 0) {
    return 'sin mapeo declarado';
  }
  return provisional ? 'asignación sin confirmar' : 'asignación confirmada';
}

/**
 * La cabecera de los apuntes redactados: cuántos apartados, cuántas preguntas cubren y con qué se
 * escribieron. Se enseña **lo que se comprobó**, no una promesa: el número de preguntas que los
 * apuntes contestan sale de la comprobación mecánica del servidor.
 */
export function notesSummary(notes: DossierNotes): string {
  const partes = [
    `${String(notes.sections_total)} ${notes.sections_total === 1 ? 'apartado' : 'apartados'}`,
    `${String(notes.covered)} de ${String(notes.questions_total)} preguntas cubiertas`,
  ];
  if (notes.conflicts > 0) {
    partes.push(`${String(notes.conflicts)} en conflicto con la clave`);
  }
  if (notes.doubtful > 0) {
    partes.push(`${String(notes.doubtful)} para revisar`);
  }
  if (notes.model !== null && notes.model !== undefined) {
    partes.push(`escritos con ${notes.model}`);
  }
  return partes.join(' · ');
}

/** Lo que se dice de un apartado que el propietario tiene que mirar. */
export function sectionReviewText(section: DossierNoteSection): string | null {
  if (section.needs_review_reason !== null && section.needs_review_reason !== undefined) {
    return section.needs_review_reason;
  }
  return null;
}
