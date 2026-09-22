import type { components } from '@opofuente/contracts';

import { apiFetch } from './client';

/**
 * ¿Está esto listo para estudiar, y qué falta? (S12.6), leído del contrato generado.
 *
 * Nada de lo que se ve lo compone la pantalla: el estado de cada paso, sus cifras y las frases que
 * explican qué falta vienen del servidor, que es el único que ve el corpus entero. Aquí solo se
 * declara a quién se llama y qué se devuelve.
 */

export type StudyReadiness = components['schemas']['StudyReadinessSchema'];
export type StudyReadinessStep = components['schemas']['StudyReadinessStepSchema'];
export type PendingActions = components['schemas']['PendingActionsSchema'];
export type PendingAction = components['schemas']['PendingActionSchema'];

export type StepStatus = StudyReadinessStep['status'];

/** Cómo se dice cada estado de un paso. `incomplete` no es un error: es «a medias». */
export const STEP_STATUS_LABEL: Record<StepStatus, string> = {
  ready: 'listo',
  incomplete: 'a medias',
  empty: 'todavía nada',
};

/** Color del aviso por estado (los nombres son los del sistema de avisos de la interfaz). */
export const STEP_STATUS_TONE: Record<StepStatus, 'ok' | 'warning' | 'info'> = {
  ready: 'ok',
  incomplete: 'warning',
  empty: 'info',
};

export function fetchStudyReadiness(oppositionId: string): Promise<StudyReadiness> {
  return apiFetch<StudyReadiness>(`/api/v1/oppositions/${oppositionId}/readiness`);
}

export function fetchPendingActions(): Promise<PendingActions> {
  return apiFetch<PendingActions>('/api/v1/pending-actions');
}
