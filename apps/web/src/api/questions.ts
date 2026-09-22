import type { components } from '@opofuente/contracts';

import { apiFetch } from './client';

/**
 * Tipos del banco de preguntas (S06), leídos del contrato generado.
 *
 * La pantalla no declara ninguno de estos datos por su cuenta: el estado de la clave, si una pregunta
 * está en conflicto y qué filas rechazó una importación vienen del servidor tal cual
 * (`08_API-CONTRACT §9`).
 */
export type QuestionSet = components['schemas']['QuestionSetSchema'];
export type QuestionSetPage = components['schemas']['QuestionSetPageSchema'];
export type Question = components['schemas']['QuestionSchema'];
export type QuestionPage = components['schemas']['QuestionPageSchema'];
export type QuestionOption = components['schemas']['OptionSchema'];
export type QuestionImportReport = components['schemas']['QuestionImportReportSchema'];
export type RejectedRow = components['schemas']['RejectedRowSchema'];
export type ParseIssue = components['schemas']['ParseIssueSchema'];
export type DuplicateGroup = components['schemas']['DuplicateGroupSchema'];
export type AnswerKey = components['schemas']['AnswerKeySchema'];
export type OutdatedSessions = components['schemas']['OutdatedSessionsSchema'];
export type BulkRecalculation = components['schemas']['BulkRecalculationSchema'];
export type SessionRecalculation = components['schemas']['SessionRecalculationSchema'];
export type KeyEntry = components['schemas']['KeyEntrySchema'];
export type QuestionEvidence = components['schemas']['QuestionEvidenceSchema'];
export type IssueReport = components['schemas']['IssueReportSchema'];
export type CorrectionOutcome = components['schemas']['CorrectionOutcomeSchema'];
export type CsvMapping = components['schemas']['CsvMappingSchema'];
export type CreateQuestionSet = components['schemas']['CreateQuestionSetSchema'];
export type PatchQuestion = components['schemas']['PatchQuestionSchema'];

export type QuestionStatus = Question['status'];
export type QuestionOrigin = Question['origin_type'];
export type QuestionKind = Question['question_type'];
export type KeyOutcome = KeyEntry['outcome'];
export type KeyStatus = AnswerKey['status'];
export type IssueKind = IssueReport['kind'];
/**
 * Las formas de llenar un conjunto. `document` no manda texto: manda la **versión** de un documento
 * de la biblioteca, y el servidor lee de ahí las preguntas y la cita de cada una (DEBT-010).
 */
export type ImportKind = 'questions' | 'csv' | 'json' | 'answer_key' | 'document';

/** Cuántas cosas se piden de una vez: el tope por defecto del servidor. */
export const PAGE_LIMIT = 100;

/** Estados de pregunta que la API admite como filtro, con su nombre para la pantalla. */
export const QUESTION_STATUSES: readonly QuestionStatus[] = [
  'incomplete',
  'complete',
  'verified',
  'conflicting',
  'annulled',
  'superseded',
];

/** Orígenes: los tres badges obligatorios de la spec (07_UI-UX §7). */
export const QUESTION_ORIGINS: readonly QuestionOrigin[] = ['official', 'private', 'generated'];

/** Tipos de pregunta que la API admite al editar. */
export const QUESTION_KINDS: readonly QuestionKind[] = [
  'single_choice',
  'multi_mark_error',
  'true_false',
  'free_text_reference',
];

/** Tipos de conjunto, tal y como los nombra el servidor. */
export const SET_TYPES: readonly QuestionSet['set_type'][] = [
  'official_exam',
  'private_bank',
  'practice',
  'generated_batch',
];

/** Motivos que admite el servidor al reportar una incidencia. */
export const ISSUE_KINDS: readonly IssueKind[] = [
  'ambiguous',
  'wrong_key',
  'typo',
  'outdated',
  'other',
];

/** Mapeo de columnas del CSV con los nombres que propone la spec. */
export const DEFAULT_CSV_MAPPING: CsvMapping = {
  stem: 'stem',
  options: ['option_a', 'option_b', 'option_c', 'option_d'],
  correct: 'correct',
  explanation: 'explanation',
  topic: 'topic',
  source: 'source',
  tags: 'tags',
  position: null,
  reserve: null,
};

export function fetchQuestionSets(oppositionId: string | null): Promise<QuestionSetPage> {
  const params = new URLSearchParams({ limit: String(PAGE_LIMIT), offset: '0' });
  if (oppositionId !== null) {
    params.set('opposition_id', oppositionId);
  }
  return apiFetch<QuestionSetPage>(`/api/v1/question-sets?${params.toString()}`);
}

export function createQuestionSet(input: CreateQuestionSet): Promise<QuestionSet> {
  return apiFetch<QuestionSet>('/api/v1/question-sets', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  });
}

export function fetchQuestionSet(setId: string): Promise<QuestionSet> {
  return apiFetch<QuestionSet>(`/api/v1/question-sets/${encodeURIComponent(setId)}`);
}

export function fetchSetQuestions(
  setId: string,
  filtros: { status: string; originType: string; onlyReserves: boolean; offset?: number },
): Promise<QuestionPage> {
  const params = new URLSearchParams({
    limit: String(PAGE_LIMIT),
    offset: String(filtros.offset ?? 0),
  });
  if (filtros.status !== '') {
    params.set('status', filtros.status);
  }
  if (filtros.originType !== '') {
    params.set('origin_type', filtros.originType);
  }
  if (filtros.onlyReserves) {
    params.set('only_reserves', 'true');
  }
  return apiFetch<QuestionPage>(
    `/api/v1/question-sets/${encodeURIComponent(setId)}/questions?${params.toString()}`,
  );
}

/**
 * Importa a un conjunto: texto, CSV con mapeo o plantilla suelta.
 *
 * El informe que devuelve dice lo que entró y **lo que no**, con la causa de cada fila rechazada: es lo
 * que permite arreglar el fichero y volver a importar solo eso.
 */
export function parseIntoSet(
  setId: string,
  input: { kind: ImportKind; text: string; mapping?: CsvMapping | null },
): Promise<QuestionImportReport> {
  const body: Record<string, unknown> = { kind: input.kind, text: input.text };
  if (input.mapping !== undefined && input.mapping !== null) {
    body.mapping = input.mapping;
  }
  return apiFetch<QuestionImportReport>(
    `/api/v1/question-sets/${encodeURIComponent(setId)}/parse`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    },
  );
}

export function fetchQuestion(questionId: string): Promise<Question> {
  return apiFetch<Question>(`/api/v1/questions/${encodeURIComponent(questionId)}`);
}

/**
 * Cuántas preguntas están en conflicto, en todo el banco (07_UI-UX §2: el contador de la navegación).
 *
 * Se pide **una sola** página con `limit=1` y se lee su total: el número lo cuenta el servidor, no la
 * pantalla contando filas, y traer el banco entero para contar conflictos sería pagar el corpus para
 * pintar un número.
 */
export function fetchConflictingQuestions(): Promise<QuestionPage> {
  return apiFetch<QuestionPage>('/api/v1/questions?status=conflicting&limit=1');
}

export function patchQuestion(questionId: string, cambios: PatchQuestion): Promise<Question> {
  return apiFetch<Question>(`/api/v1/questions/${encodeURIComponent(questionId)}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(cambios),
  });
}

/**
 * Corrige una transcripción **con motivo**: crea versión nueva y no toca el original importado.
 *
 * El motivo no es opcional: mandar una corrección sin él es un 422 del servidor, así que la pantalla
 * tampoco deja intentarlo.
 */
export function correctQuestion(
  questionId: string,
  input: { note: string; stem?: string | null; options?: string[] | null },
): Promise<CorrectionOutcome> {
  const body: Record<string, unknown> = { note: input.note };
  if (input.stem !== undefined && input.stem !== null && input.stem !== '') {
    body.stem = input.stem;
  }
  if (input.options !== undefined && input.options !== null && input.options.length > 0) {
    body.options = input.options;
  }
  return apiFetch<CorrectionOutcome>(
    `/api/v1/questions/${encodeURIComponent(questionId)}/local-corrections`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    },
  );
}

/** Evidencia que sostiene la pregunta, con el texto de su cita. Vacío significa que no hay ninguna. */
export function fetchQuestionEvidence(questionId: string): Promise<QuestionEvidence[]> {
  return apiFetch<QuestionEvidence[]>(
    `/api/v1/questions/${encodeURIComponent(questionId)}/evidence`,
  );
}

export function reportQuestionIssue(
  questionId: string,
  input: { kind: IssueKind; detail: string },
): Promise<IssueReport> {
  return apiFetch<IssueReport>(
    `/api/v1/questions/${encodeURIComponent(questionId)}/report-issue`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(input),
    },
  );
}

export function fetchAnswerKeys(setId: string): Promise<AnswerKey[]> {
  return apiFetch<AnswerKey[]>(
    `/api/v1/question-sets/${encodeURIComponent(setId)}/answer-keys`,
  );
}

/** Activa una plantilla: **activar es aprobar** (ADR-009), y el servidor lo deja auditado. */
export function activateAnswerKey(setId: string, keyId: string): Promise<AnswerKey> {
  const ruta = `/api/v1/question-sets/${encodeURIComponent(setId)}/answer-keys`;
  return apiFetch<AnswerKey>(`${ruta}/${encodeURIComponent(keyId)}/activate`, { method: 'POST' });
}

export function markKeySupersedes(keyId: string, supersededId: string): Promise<AnswerKey> {
  return apiFetch<AnswerKey>(
    `/api/v1/answer-keys/${encodeURIComponent(keyId)}/mark-supersedes`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ superseded_id: supersededId }),
    },
  );
}

/**
 * Cuántas sesiones terminadas del conjunto **no** están corregidas con la plantilla activa (DEBT-013).
 *
 * Es la cuenta que se hace al activar una plantilla corregida: sin ella, activar una clave nueva no
 * cambiaba ninguna nota y no se notaba en ninguna parte.
 */
export function fetchOutdatedSessions(setId: string): Promise<OutdatedSessions> {
  return apiFetch<OutdatedSessions>(
    `/api/v1/question-sets/${encodeURIComponent(setId)}/outdated-sessions`,
  );
}

/** Recalcula **en bloque** las sesiones terminadas del conjunto y devuelve qué cambió en cada una. */
export function recalculateSetSessions(setId: string): Promise<BulkRecalculation> {
  return apiFetch<BulkRecalculation>(
    `/api/v1/question-sets/${encodeURIComponent(setId)}/recalculate-sessions`,
    { method: 'POST' },
  );
}

/**
 * Importa las preguntas de una **versión de documento** y crea la cita de cada una (DEBT-010).
 *
 * Es la única forma de importar que deja la pregunta con su origen: el servidor lee la versión por
 * sus fragmentos, así que la ficha puede enseñar la cita y abrir el original en su página.
 */
export function importQuestionsFromDocument(
  setId: string,
  documentVersionId: string,
): Promise<QuestionImportReport> {
  return apiFetch<QuestionImportReport>(
    `/api/v1/question-sets/${encodeURIComponent(setId)}/import-document`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ document_version_id: documentVersionId }),
    },
  );
}

/**
 * Las filas rechazadas, en CSV, para poder arreglarlas y volver a importarlas.
 *
 * Se construye con lo que devolvió el informe: no hay ruta de exportación porque no hace falta una, y
 * el fichero lleva la cabecera con la causa, que es lo que hay que corregir.
 */
export function rejectedRowsCsv(rechazadas: readonly RejectedRow[]): string {
  const lineas = ['fila,causa,detalle'];
  for (const fila of rechazadas) {
    lineas.push(
      [String(fila.row_number), fila.cause, `"${fila.detail.replaceAll('"', '""')}"`].join(','),
    );
  }
  return `${lineas.join('\n')}\n`;
}

/** ¿Esta pregunta tiene un conflicto de claves que hay que mirar? */
export function isConflicting(question: Question): boolean {
  return question.status === 'conflicting' || question.key_outcome === 'conflicting';
}
