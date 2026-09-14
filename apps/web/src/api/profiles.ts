import type { components } from '@opofuente/contracts';

import { apiFetch } from './client';

export type Opposition = components['schemas']['OppositionSchema'];
export type OppositionDetail = components['schemas']['OppositionDetailSchema'];
export type ConvocationReference = components['schemas']['ConvocationReferenceSchema'];
export type ConvocationDetail = components['schemas']['ConvocationDetailSchema'];
export type Curriculum = components['schemas']['CurriculumSchema'];
export type CurriculumNode = components['schemas']['CurriculumNodeSchema'];
export type CurriculumNodeDetail = components['schemas']['CurriculumNodeDetailSchema'];
export type ExamPart = components['schemas']['ExamPartSchema'];
export type ExamRule = components['schemas']['ExamRuleSchema'];

export function fetchOppositions(): Promise<Opposition[]> {
  return apiFetch<Opposition[]>('/api/v1/oppositions');
}

export function fetchOpposition(oppositionId: string): Promise<OppositionDetail> {
  return apiFetch<OppositionDetail>(`/api/v1/oppositions/${oppositionId}`);
}

export function fetchConvocation(convocationId: string): Promise<ConvocationDetail> {
  return apiFetch<ConvocationDetail>(`/api/v1/convocations/${convocationId}`);
}

export function fetchCurriculum(convocationId: string): Promise<Curriculum> {
  return apiFetch<Curriculum>(`/api/v1/convocations/${convocationId}/curriculum`);
}

export function fetchCurriculumNode(nodeId: string): Promise<CurriculumNodeDetail> {
  return apiFetch<CurriculumNodeDetail>(`/api/v1/curriculum-nodes/${nodeId}`);
}

/** Cambia la oposición activa. Es la única escritura de S01. */
export function activateOpposition(oppositionId: string): Promise<Opposition> {
  return apiFetch<Opposition>(`/api/v1/oppositions/${oppositionId}/activate`, { method: 'POST' });
}
