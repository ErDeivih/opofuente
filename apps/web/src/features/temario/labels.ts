import type { Adjustment } from '../../api/temario';

/**
 * Etiquetas cortas y formato de fecha del temario (DOCTRINA-CALIDAD §8: solo lo que el alumno
 * necesita para decidir o actuar; nada de cómo está calculado).
 */

const DATE_FORMAT = new Intl.DateTimeFormat('es-ES', {
  day: 'numeric',
  month: 'long',
  year: 'numeric',
});

/** Fecha legible; si el valor no es una fecha, se enseña tal cual en vez de «Invalid Date». */
export function formatDate(value: string): string {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : DATE_FORMAT.format(date);
}

const ROLE_LABEL: Record<string, string> = {
  primary: 'Temario que se estudia',
  official: 'Programa oficial',
  complementary: 'Temario complementario',
};

export function roleLabel(role: string): string {
  return ROLE_LABEL[role] ?? role;
}

const ADJUSTMENT_LABEL: Record<string, string> = {
  omitted: 'Omitido',
  weighted: 'Ponderado en esta convocatoria',
  renumbered: 'Renumerado',
  renamed: 'Renombrado',
};

export function adjustmentLabel(kind: string): string {
  return ADJUSTMENT_LABEL[kind] ?? kind;
}

/** El detalle que cambia respecto al temario común, si el ajuste lo trae. */
export function adjustmentDetail(adjustment: Adjustment): string | null {
  if (adjustment.kind === 'renamed') {
    return adjustment.title_override ?? null;
  }
  if (adjustment.kind === 'renumbered') {
    return adjustment.official_code_override ?? null;
  }
  return null;
}

/** Ruta de la ficha conservando la convocatoria desde la que se está mirando. */
export function temarioHref(nodeId: string, convocationId: string | null): string {
  return convocationId === null
    ? `/temario/${encodeURIComponent(nodeId)}`
    : `/temario/${encodeURIComponent(nodeId)}?convocatoria=${encodeURIComponent(convocationId)}`;
}

const QUESTION_TYPE_LABEL: Record<string, string> = {
  single_choice: 'Una respuesta',
  multi_mark_error: 'Marcar los errores',
  true_false: 'Verdadero o falso',
  free_text_reference: 'Respuesta abierta',
};

export function questionTypeLabel(questionType: string): string {
  return QUESTION_TYPE_LABEL[questionType] ?? 'Pregunta';
}

const MATERIAL_TYPE_LABEL: Record<string, string> = {
  document_version: 'Documento',
  section: 'Sección',
  evidence: 'Cita',
};

export function materialTypeLabel(subjectType: string): string {
  return MATERIAL_TYPE_LABEL[subjectType] ?? 'Material';
}
