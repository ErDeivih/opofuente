import { describe, expect, it } from 'vitest';

import { ApiError, apiBaseUrl, apiFetch } from '../../src/api/client';
import { fetchReadiness } from '../../src/api/system';
import { readinessDegraded, readinessReady, stubApi } from './testUtils';

describe('cliente de la API', () => {
  it('usa la URL local por defecto', () => {
    expect(apiBaseUrl()).toBe('http://127.0.0.1:8765');
  });

  it('devuelve el cuerpo JSON cuando la respuesta es correcta', async () => {
    const fetchMock = stubApi({ '/api/v1/capabilities': { body: { version: '0.0.0', capabilities: [], degradations: [] } } });
    const result = await apiFetch<{ version: string }>('/api/v1/capabilities');
    expect(result.version).toBe('0.0.0');
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it('convierte un error RFC 9457 en ApiError con código', async () => {
    stubApi({
      '/api/v1/capabilities': {
        status: 422,
        contentType: 'application/problem+json',
        body: {
          type: 'about:blank',
          title: 'Unprocessable Entity',
          status: 422,
          detail: 'La petición no cumple el contrato.',
          instance: '/api/v1/capabilities',
          code: 'validation_error',
          correlation_id: 'corr-1',
        },
      },
    });

    await expect(apiFetch('/api/v1/capabilities')).rejects.toBeInstanceOf(ApiError);
    await expect(apiFetch('/api/v1/capabilities')).rejects.toMatchObject({
      status: 422,
      code: 'validation_error',
    });
  });

  it('interpreta el 503 de readiness como estado degradado con sus comprobaciones', async () => {
    stubApi({
      '/api/v1/health/ready': {
        status: 503,
        contentType: 'application/problem+json',
        body: readinessDegraded,
      },
    });

    const view = await fetchReadiness();
    expect(view.status).toBe('degraded');
    expect(view.checks).toHaveLength(2);
    expect(view.checks[0]?.name).toBe('database');
  });

  it('devuelve estado listo cuando la API responde 200', async () => {
    stubApi({ '/api/v1/health/ready': { body: readinessReady } });
    const view = await fetchReadiness();
    expect(view.status).toBe('ready');
  });

  it('no rompe la pantalla si un 503 no cumpliera el contrato y omitiera checks', async () => {
    stubApi({
      '/api/v1/health/ready': {
        status: 503,
        contentType: 'application/problem+json',
        // Un servidor que incumpliera `ReadinessProblem`: `checks` es obligatorio en el contrato.
        body: {
          type: 'about:blank',
          title: 'Service Unavailable',
          status: 503,
          detail: 'La aplicación no está lista.',
          instance: '/api/v1/health/ready',
          code: 'not_ready',
          correlation_id: 'corr-sin-checks',
        },
      },
    });

    const view = await fetchReadiness();
    expect(view.status).toBe('degraded');
    expect(view.checks).toEqual([]);
  });
});
