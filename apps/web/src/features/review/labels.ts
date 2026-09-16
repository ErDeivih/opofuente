import type {
  ProposalAxis,
  ProposalBand,
  ProposalStatus,
  SubjectType,
} from '../../api/classification';
import type { StatusTone } from '../../components/StatusBadge';

/**
 * Vocabulario de la cola de revisión en español (07_UI-UX §12).
 *
 * El servidor habla en códigos (`topic`, `high`, `auto_applied_provisional`); la pantalla los traduce
 * para leerlos. La traducción es solo de presentación: qué banda tiene una propuesta y si es crítica
 * lo decide el servidor y viaja en la propia propuesta (`band`, `is_critical`), nunca se recalcula
 * aquí.
 */
export const AXIS_LABEL: Record<ProposalAxis, string> = {
  document_type: 'Tipo de documento',
  opposition: 'Oposición',
  topic: 'Tema del programa',
  authority: 'Autoridad',
  rights: 'Derechos',
};

export const BAND_LABEL: Record<ProposalBand, string> = {
  high: 'alta',
  medium: 'media',
  low: 'baja',
};

/** La banda no depende solo del color: va escrita y con su glifo (07_UI-UX §1). */
export const BAND_TONE: Record<ProposalBand, StatusTone> = {
  high: 'ok',
  medium: 'warning',
  low: 'info',
};

export const STATUS_LABEL: Record<ProposalStatus, string> = {
  pending: 'pendiente de tu decisión',
  accepted: 'aceptada',
  rejected: 'rechazada',
  superseded: 'sustituida',
  auto_applied_provisional: 'aplicada provisionalmente',
};

export const STATUS_TONE: Record<ProposalStatus, StatusTone> = {
  pending: 'warning',
  accepted: 'ok',
  rejected: 'info',
  superseded: 'info',
  auto_applied_provisional: 'warning',
};

export const SUBJECT_TYPE_LABEL: Record<SubjectType, string> = {
  artifact: 'material',
  representation: 'texto extraído',
};

export const SUBJECT_LABEL_FALLBACK = 'material sin nombre';

/** Etiqueta del tipo de sujeto cuando el código llega como texto libre (grupos de revisión). */
export function subjectTypeLabel(type: string): string {
  return SUBJECT_TYPE_LABEL[type as SubjectType] ?? type;
}

/** Etiqueta de un eje.
 *
 * El eje llega como texto libre en los grupos de revisión (`axis: string`) y como unión cerrada en
 * las propuestas. Aquí se traduce cuando se conoce y se deja el código cuando no, en lugar de
 * inventar un nombre para un eje que el servidor no ha declarado.
 */
export function axisLabel(axis: string): string {
  return AXIS_LABEL[axis as ProposalAxis] ?? axis;
}

/** Etiqueta del estado que devuelve una decisión (`status: string` en el contrato). */
export function statusLabel(status: string): string {
  return STATUS_LABEL[status as ProposalStatus] ?? status;
}

/** Confianza en porcentaje. La confianza viene del servidor; aquí solo se da formato. */
export function percent(value: number): string {
  return `${Math.round(value * 100)} %`;
}

/** Recuento con su concordancia: «1 propuesta», «3 propuestas». El número se lee, no se abrevia. */
export function countLabel(count: number, singular: string, plural: string): string {
  return `${count} ${count === 1 ? singular : plural}`;
}

/** Etiqueta del sujeto de una propuesta: su nombre si consta, y si no, la ausencia de nombre. */
export function subjectLabel(proposal: { subject_label?: string | null }): string {
  return proposal.subject_label ?? SUBJECT_LABEL_FALLBACK;
}

/** Valor legible de una propuesta: el que da el servidor, o el código cuando no hay etiqueta. */
export function valueLabel(proposal: { value_label?: string | null; proposed_value: string }): string {
  return proposal.value_label ?? proposal.proposed_value;
}
