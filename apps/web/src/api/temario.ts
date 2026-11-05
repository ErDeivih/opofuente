import type { components } from '@opofuente/contracts';

import { apiFetch } from './client';

/**
 * Cliente del temario común (B-004/B-005).
 *
 * El alumno ve el temario: aquí no se piden registros de auditoría ni datos de administración, solo
 * el árbol, el avance y la ficha del tema con las convocatorias en las que aparece.
 */
export type CurriculumSummary = components['schemas']['CurriculumSummarySchema'];
export type CurriculumDetail = components['schemas']['CurriculumDetailSchema'];
export type CurriculumVersion = components['schemas']['CurriculumVersionSchema'];
export type CurriculumNode = components['schemas']['CurriculumNodeSchema'];
export type Progress = components['schemas']['ProgressSchema'];
export type CurriculumNodeDetail = components['schemas']['CurriculumNodeDetailSchema'];
export type Appearance = components['schemas']['AppearanceSchema'];
export type Adjustment = components['schemas']['AdjustmentSchema'];
export type StudyMark = components['schemas']['StudyMarkSchema'];

export type CurriculumKind = 'common' | 'published';

/** Temarios disponibles; por defecto, todos. */
export function fetchCurricula(kind?: CurriculumKind): Promise<CurriculumSummary[]> {
  const query = kind === undefined ? '' : `?kind=${encodeURIComponent(kind)}`;
  return apiFetch<CurriculumSummary[]>(`/api/v1/curricula${query}`);
}

/** Un temario con sus versiones y su árbol. */
export function fetchCurriculumDetail(code: string): Promise<CurriculumDetail> {
  return apiFetch<CurriculumDetail>(`/api/v1/curricula/${encodeURIComponent(code)}`);
}

/** Avance por bloque y total sobre el temario común. */
export function fetchCurriculumProgress(code: string): Promise<Progress> {
  return apiFetch<Progress>(`/api/v1/curricula/${encodeURIComponent(code)}/progress`);
}

/**
 * Ficha de un nodo del temario.
 *
 * Con `convocationId` el servidor añade las particularidades de esa convocatoria (omitido,
 * renombrado, renumerado) sin copiar el temario; sin él devuelve la ficha del temario común.
 */
export function fetchCurriculumNodeDetail(
  nodeId: string,
  convocationId: string | null,
): Promise<CurriculumNodeDetail> {
  const query =
    convocationId === null ? '' : `?convocation_id=${encodeURIComponent(convocationId)}`;
  return apiFetch<CurriculumNodeDetail>(
    `/api/v1/curriculum-nodes/${encodeURIComponent(nodeId)}${query}`,
  );
}

/** Marca un tema como estudiado. Devuelve la fecha que queda guardada. */
export function markNodeStudied(nodeId: string): Promise<StudyMark> {
  return apiFetch<StudyMark>(`/api/v1/curriculum-nodes/${encodeURIComponent(nodeId)}/studied`, {
    method: 'POST',
  });
}

/** Retira la marca de estudiado. El servidor responde 204 sin cuerpo. */
export function unmarkNodeStudied(nodeId: string): Promise<void> {
  return apiFetch<void>(`/api/v1/curriculum-nodes/${encodeURIComponent(nodeId)}/studied`, {
    method: 'DELETE',
  });
}
