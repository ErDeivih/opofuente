import type { components } from '@opofuente/contracts';

import { ApiError, apiFetch } from './client';

export type CapabilitiesResponse = components['schemas']['CapabilitiesSchema'];
export type Capability = components['schemas']['CapabilitySchema'];
export type CapabilityStatus = components['schemas']['CapabilityStatus'];
export type CheckResult = components['schemas']['CheckSchema'];
export type Degradation = components['schemas']['DegradationSchema'];
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
    if (error instanceof ApiError && error.status === 503 && error.problem !== null) {
      const checks = (error.problem as { checks?: CheckResult[] }).checks;
      return { status: 'degraded', checks: checks ?? [] };
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
