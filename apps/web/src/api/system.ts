import type { components } from '@opofuente/contracts';

import { apiFetch, isApiError } from './client';

export type CapabilitiesResponse = components['schemas']['CapabilitiesSchema'];
export type Capability = components['schemas']['CapabilitySchema'];
export type CapabilityStatus = components['schemas']['CapabilityStatus'];
export type CheckResult = components['schemas']['CheckSchema'];
export type Degradation = components['schemas']['DegradationSchema'];
/** Problema RFC 9457 del 503 de /health/ready, con `checks`. Tipo tomado del contrato. */
export type ReadinessProblem = components['schemas']['ReadinessProblem'];
export type ReadinessResponse = components['schemas']['ReadinessSchema'];
export type SettingsResponse = components['schemas']['SettingsSchema'];

/** Vista normalizada de /health/ready: un 503 con `checks` también es información útil. */
export interface ReadinessView {
  status: 'ready' | 'degraded';
  checks: CheckResult[];
}

export async function fetchReadiness(): Promise<ReadinessView> {
  try {
    const readiness = await apiFetch<ReadinessResponse>('/api/v1/health/ready');
    return { status: readiness.status, checks: readiness.checks };
  } catch (error) {
    // El contrato documenta que el 503 de /health/ready es un ReadinessProblem con `checks`
    // (apps/api/tests/contract comprueba el esquema y el cuerpo servido).
    if (isApiError<ReadinessProblem>(error, 503) && error.problem !== null) {
      // Si un servidor incumpliera el contrato, se muestra el resto del estado en lugar de
      // romper la pantalla al recorrer una lista inexistente.
      return { status: 'degraded', checks: error.problem.checks ?? [] };
    }
    throw error;
  }
}

export function fetchCapabilities(): Promise<CapabilitiesResponse> {
  return apiFetch<CapabilitiesResponse>('/api/v1/capabilities');
}

export function fetchSettings(): Promise<SettingsResponse> {
  return apiFetch<SettingsResponse>('/api/v1/settings');
}
