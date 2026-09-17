import type {
  IssueKind,
  KeyOutcome,
  KeyStatus,
  QuestionKind,
  QuestionOrigin,
  QuestionSet,
  QuestionStatus,
} from '../../api/questions';
import type { StatusTone } from '../../components/StatusBadge';

/**
 * Vocabulario del banco de preguntas en español (07_UI-UX §7).
 *
 * Los badges de origen son **obligatorios** en la spec (OFICIAL, PRIVADA, GENERADA) y no se suavizan:
 * saber de dónde sale una pregunta es lo primero que hay que poder ver.
 */

export const ORIGIN_LABEL: Record<QuestionOrigin, string> = {
  official: 'OFICIAL',
  private: 'PRIVADA',
  generated: 'GENERADA',
};

export const ORIGIN_TONE: Record<QuestionOrigin, StatusTone> = {
  official: 'ok',
  private: 'info',
  generated: 'warning',
};

export const QUESTION_STATUS_LABEL: Record<QuestionStatus, string> = {
  incomplete: 'incompleta',
  complete: 'completa',
  verified: 'verificada',
  conflicting: 'en conflicto',
  annulled: 'anulada',
  superseded: 'sustituida',
};

export const QUESTION_STATUS_TONE: Record<QuestionStatus, StatusTone> = {
  incomplete: 'warning',
  complete: 'info',
  verified: 'ok',
  conflicting: 'blocked',
  annulled: 'info',
  superseded: 'info',
};

export const KIND_LABEL: Record<QuestionKind, string> = {
  single_choice: 'una respuesta',
  multi_mark_error: 'marcar errores',
  true_false: 'verdadero o falso',
  free_text_reference: 'referencia libre',
};

export const KEY_STATUS_LABEL: Record<KeyStatus, string> = {
  draft: 'borrador, sin activar',
  active: 'activa',
  superseded: 'sustituida',
  rejected: 'rechazada',
};

export const KEY_STATUS_TONE: Record<KeyStatus, StatusTone> = {
  draft: 'warning',
  active: 'ok',
  superseded: 'info',
  rejected: 'blocked',
};

export const KEY_OUTCOME_LABEL: Record<KeyOutcome, string> = {
  keyed: 'con clave',
  annulled: 'anulada',
  unanswered: 'sin responder',
  conflicting: 'en conflicto',
};

export const KEY_OUTCOME_TONE: Record<KeyOutcome, StatusTone> = {
  keyed: 'ok',
  annulled: 'info',
  unanswered: 'warning',
  conflicting: 'blocked',
};

export const SET_TYPE_LABEL: Record<QuestionSet['set_type'], string> = {
  official_exam: 'examen oficial',
  private_bank: 'banco privado',
  practice: 'práctica',
  generated_batch: 'lote generado',
};

export const SET_STATUS_LABEL: Record<QuestionSet['status'], string> = {
  draft: 'borrador',
  confirmed: 'confirmado',
  archived: 'archivado',
};

export const ISSUE_KIND_LABEL: Record<IssueKind, string> = {
  ambiguous: 'ambigua',
  wrong_key: 'clave equivocada',
  typo: 'errata',
  outdated: 'desactualizada',
  other: 'otra cosa',
};

export function originLabel(origin: string): string {
  return ORIGIN_LABEL[origin as QuestionOrigin] ?? origin;
}

export function originTone(origin: string): StatusTone {
  return ORIGIN_TONE[origin as QuestionOrigin] ?? 'info';
}

export function questionStatusLabel(status: string): string {
  return QUESTION_STATUS_LABEL[status as QuestionStatus] ?? status;
}

export function questionStatusTone(status: string): StatusTone {
  return QUESTION_STATUS_TONE[status as QuestionStatus] ?? 'info';
}

export function kindLabel(kind: string): string {
  return KIND_LABEL[kind as QuestionKind] ?? kind;
}

export function keyStatusLabel(status: string): string {
  return KEY_STATUS_LABEL[status as KeyStatus] ?? status;
}

export function keyStatusTone(status: string): StatusTone {
  return KEY_STATUS_TONE[status as KeyStatus] ?? 'info';
}

export function keyOutcomeLabel(outcome: string | null | undefined): string {
  if (outcome === null || outcome === undefined) {
    return 'sin clave';
  }
  return KEY_OUTCOME_LABEL[outcome as KeyOutcome] ?? outcome;
}

export function keyOutcomeTone(outcome: string | null | undefined): StatusTone {
  if (outcome === null || outcome === undefined) {
    return 'warning';
  }
  return KEY_OUTCOME_TONE[outcome as KeyOutcome] ?? 'info';
}

export function setTypeLabel(setType: string): string {
  return SET_TYPE_LABEL[setType as QuestionSet['set_type']] ?? setType;
}

export function setStatusLabel(status: string): string {
  return SET_STATUS_LABEL[status as QuestionSet['status']] ?? status;
}

export function issueKindLabel(kind: string): string {
  return ISSUE_KIND_LABEL[kind as IssueKind] ?? kind;
}

/** Enunciado recortado para la tabla: el completo se lee en la ficha. */
export function shortStem(stem: string, limite = 90): string {
  return stem.length <= limite ? stem : `${stem.slice(0, limite).trimEnd()}…`;
}
