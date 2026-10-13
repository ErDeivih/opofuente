import type { components } from '@opofuente/contracts';

import { apiFetch } from './client';

/**
 * La ficha de pregunta, para el panel (F20, §4.2 del objetivo).
 *
 * Es lo que hay detrás de la dirección que la bandeja del motor y el banco ya usaban
 * (`/admin/preguntas?pregunta=<id>`) y que no tenía pantalla donde arreglar nada. La ficha enseña la
 * pregunta con su respuesta correcta y **de dónde sale**, lo que contestan los apuntes, lo que ha
 * señalado el sistema y qué se puede hacer.
 *
 * Dos cosas que **no** se declaran aquí:
 *
 * - el **porqué** de cada reparación y de cada negativa: lo manda el servidor (`repair.detalle`,
 *   `repair.por_que_no`, `protection.reason`), porque lo decide el dominio y copiarlo en el cliente
 *   sería tener dos versiones del mismo párrafo;
 * - el **vocabulario del estado** de una plantilla (`active`, `draft`…) y el de la fiabilidad
 *   (`fiable`, `dudosa`, `no_fiable`): se traducen a palabras de interfaz abajo, pero el valor que se
 *   compara es el del contrato.
 */
export type QuestionFile = components['schemas']['QuestionFileSchema'];
export type QuestionFileKey = components['schemas']['QuestionFileKeySchema'];
export type QuestionFileKeyVersion = components['schemas']['QuestionFileKeyVersionSchema'];
export type QuestionFileVersion = components['schemas']['QuestionFileVersionSchema'];
export type QuestionFileNotes = components['schemas']['QuestionFileNotesSchema'];
export type QuestionFileIncident = components['schemas']['QuestionFileIncidentSchema'];
export type QuestionFileProtectedSet = components['schemas']['QuestionFileProtectedSetSchema'];
export type QuestionFileRepair = components['schemas']['QuestionFileRepairSchema'];
export type QuestionFileOption = components['schemas']['QuestionFileOptionSchema'];
export type MarkCorrectResult = components['schemas']['MarkCorrectResultSchema'];
export type RepairResult = components['schemas']['RepairResultSchema'];

/** La letra de una opción, tal como la admite el contrato: de la `a` a la `h`. */
export type OptionLetter = NonNullable<
  components['schemas']['MarkCorrectOptionSchema']['correct_option_keys']
>[number];

/**
 * El estado de la plantilla, en palabras de interfaz.
 *
 * `active` es la que corrige los tests y `draft` la que está en revisión: la diferencia importa
 * mucho para saber si marcar la respuesta correcta va a cambiar lo que se corrige.
 */
export const KEY_STATUS_LABELS: Record<QuestionFileKey['status'], string> = {
  active: 'en uso',
  draft: 'sin aprobar',
  superseded: 'sustituida',
  rejected: 'rechazada',
};

/** Qué significa cada estado, para no tener que deducirlo. */
export const KEY_STATUS_HELP: Record<QuestionFileKey['status'], string> = {
  active: 'Es la que corrige los test y los simulacros de este banco.',
  draft: 'Todavía no corrige nada: hace falta aprobarla en el banco de preguntas.',
  superseded: 'Una plantilla posterior la sustituyó; se conserva para poder leer qué decía.',
  rejected: 'Se descartó y no se usa.',
};

/**
 * La fiabilidad de la respuesta correcta de todo un banco (§1 de los ajustes).
 *
 * Es el veredicto de la puerta de datos, no un cálculo de esta pantalla: si la columna todavía no
 * existe en la base, el servidor manda `null` y lo dice en `reliability_source`, y aquí se enseña
 * eso en vez de inventarse un veredicto.
 */
export const RELIABILITY_LABELS: Record<string, string> = {
  fiable: 'fiable',
  dudosa: 'en duda',
  no_fiable: 'no fiable',
};

export const RELIABILITY_HELP: Record<string, string> = {
  fiable: 'Los apuntes y las respuestas correctas de este banco coinciden.',
  dudosa:
    'Entre el 15 % y el 30 % de las respuestas de este banco no cuadran con los apuntes: sus preguntas entran en los test con un aviso.',
  no_fiable:
    'Más del 30 % de las respuestas de este banco no cuadran con los apuntes, así que sus preguntas no entran en los test hasta que se arreglen.',
};

/** Cómo se llama cada estado de una versión de la pregunta. */
export const QUESTION_STATUS_LABELS: Record<QuestionFileVersion['status'], string> = {
  incomplete: 'incompleta',
  complete: 'completa',
  verified: 'comprobada',
  conflicting: 'en conflicto',
  annulled: 'anulada',
  superseded: 'sustituida',
};

/** Cómo se llama cada motivo de fuera de temario. */
export const EXCLUSION_LABELS: Record<string, string> = {
  otra_administracion: 'es de otra administración',
  enunciado_roto: 'el enunciado está roto',
};

/**
 * El enlace al punto exacto de los apuntes del que habla una comprobación.
 *
 * Es el mismo ancla que usan los apuntes (`#apartado-<ancla>`), así que lleva al párrafo y no a la
 * pantalla del tema. Cuando no hay apartado no hay enlace: mandar a un ancla que no está dejaría al
 * propietario buscando a mano.
 */
export function notesHref(contraste: QuestionFileNotes): string | null {
  if (contraste.anchor === '' || contraste.section_title === null) {
    return null;
  }
  return `/temario/${contraste.topic_code}#apartado-${contraste.anchor}`;
}

/** El enlace al material del que salió la respuesta correcta, cuando consta. */
export function materialHref(file: QuestionFile): string | null {
  const documento = file.key?.source_document_id;
  if (documento === null || documento === undefined) {
    return null;
  }
  return `/admin/biblioteca?documento=${encodeURIComponent(documento)}`;
}

/** Las letras que la pregunta tiene, en el orden de sus opciones. */
export function optionLetters(file: QuestionFile): OptionLetter[] {
  return file.options
    .map((opcion) => opcion.stable_key)
    .filter((clave): clave is OptionLetter => /^[a-h]$/.test(clave));
}

/** Las letras marcadas como respuesta correcta hoy. */
export function markedLetters(file: QuestionFile): string[] {
  return file.key?.correct_option_keys ?? [];
}

/** La ficha de una pregunta, por su identificador. */
export function fetchQuestionFile(questionVersionId: string): Promise<QuestionFile> {
  return apiFetch<QuestionFile>(
    `/api/v1/question-files/${encodeURIComponent(questionVersionId)}`,
  );
}

/**
 * Marca la respuesta correcta: una escritura auditada, con la anterior al historial.
 *
 * La nota es opcional —el histórico ya guarda el antes y el después— y quien escribe lo firma con su
 * nombre, que viaja en el cuerpo.
 */
export function markCorrectOption(
  questionVersionId: string,
  input: { correctOptionKeys: string[]; note?: string | null; actor?: string | undefined },
): Promise<MarkCorrectResult> {
  const cuerpo: components['schemas']['MarkCorrectOptionSchema'] = {
    correct_option_keys: input.correctOptionKeys as OptionLetter[],
  };
  if (input.note !== null && input.note !== undefined && input.note.trim() !== '') {
    cuerpo.note = input.note.trim();
  }
  if (input.actor !== undefined && input.actor.trim() !== '') {
    cuerpo.actor = input.actor.trim();
  }
  return apiFetch<MarkCorrectResult>(
    `/api/v1/question-files/${encodeURIComponent(questionVersionId)}/answer-key`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(cuerpo),
    },
  );
}

/**
 * Repara lo que una regla mecánica pueda reparar, escribiendo una versión nueva.
 *
 * No se manda texto: lo que se escribe lo decide el servidor con las reglas del §2 sobre lo que ya
 * hay. La nota sí es obligatoria, porque una versión nueva sin motivo es un cambio que nadie puede
 * explicar después.
 */
export function repairQuestion(
  questionVersionId: string,
  input: { note: string; reglas?: string[] | null; actor?: string | undefined },
): Promise<RepairResult> {
  const cuerpo: components['schemas']['RepairQuestionSchema'] = { note: input.note };
  if (input.reglas !== null && input.reglas !== undefined && input.reglas.length > 0) {
    cuerpo.reglas = input.reglas;
  }
  if (input.actor !== undefined && input.actor.trim() !== '') {
    cuerpo.actor = input.actor.trim();
  }
  return apiFetch<RepairResult>(
    `/api/v1/question-files/${encodeURIComponent(questionVersionId)}/repairs`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(cuerpo),
    },
  );
}
