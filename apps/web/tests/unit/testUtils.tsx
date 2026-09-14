import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render } from '@testing-library/react';
import type { ReactElement } from 'react';
import { MemoryRouter } from 'react-router-dom';
import { vi } from 'vitest';

import type {
  CapabilitiesResponse,
  ReadinessResponse,
  SettingsResponse,
} from '../../src/api/system';

export function createTestQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0, staleTime: 0 } },
  });
}

export function renderWithProviders(ui: ReactElement, options: { route?: string } = {}) {
  return render(
    <QueryClientProvider client={createTestQueryClient()}>
      <MemoryRouter initialEntries={[options.route ?? '/']}>{ui}</MemoryRouter>
    </QueryClientProvider>,
  );
}

export interface StubbedRoute {
  status?: number;
  body: unknown;
  contentType?: string;
}

/** Sustituye `fetch` por respuestas fijas que imitan el contrato real de la API. */
export function stubApi(routes: Record<string, StubbedRoute>) {
  const fetchMock = vi.fn((input: RequestInfo | URL) => {
    const url =
      typeof input === 'string' ? input : input instanceof URL ? input.href : input.url;
    const match = Object.entries(routes).find(([path]) => url.includes(path));
    if (match === undefined) {
      return Promise.resolve(
        new Response(JSON.stringify({ code: 'not_found' }), {
          status: 404,
          headers: { 'content-type': 'application/problem+json' },
        }),
      );
    }
    const route = match[1];
    return Promise.resolve(
      new Response(JSON.stringify(route.body), {
        status: route.status ?? 200,
        headers: { 'content-type': route.contentType ?? 'application/json' },
      }),
    );
  });
  vi.stubGlobal('fetch', fetchMock);
  return fetchMock;
}

export const readinessReady: ReadinessResponse = {
  status: 'ready',
  checks: [
    {
      name: 'database',
      status: 'ok',
      detail: 'sqlite ok (revisión 0001_app_metadata, foreign_keys=ON, journal_mode=wal)',
    },
    { name: 'data_dir', status: 'ok', detail: 'directorio de datos escribible' },
  ],
};

export const readinessDegraded = {
  type: 'about:blank',
  title: 'Service Unavailable',
  status: 503,
  detail: 'La aplicación no está lista.',
  instance: '/api/v1/health/ready',
  code: 'not_ready',
  correlation_id: 'corr-de-prueba',
  checks: [
    {
      name: 'database',
      status: 'failed',
      detail: 'sqlite inaccesible o esquema sin migrar (OperationalError)',
    },
    { name: 'data_dir', status: 'ok', detail: 'directorio de datos escribible' },
  ],
};

export const capabilitiesFixture: CapabilitiesResponse = {
  version: '0.0.0-test',
  capabilities: [
    {
      id: 'artifact_store',
      label: 'Almacén de originales por SHA-256',
      status: 'planned',
      detail: 'La copia inmutable y el inventario se implementan en S02.',
      planned_slice: 'S02',
    },
    {
      id: 'worker',
      label: 'Cola de trabajos local',
      status: 'planned',
      detail: 'Worker persistido en SQLite con lease.',
      planned_slice: 'S02',
    },
    {
      id: 'ocr',
      label: 'OCR (Tesseract)',
      status: 'disabled',
      detail: 'Sin ruta configurada.',
      planned_slice: 'S03',
    },
    {
      id: 'llm',
      label: 'Modelo de lenguaje',
      status: 'disabled',
      detail: 'Ninguna función básica depende de IA.',
      planned_slice: 'S09',
    },
  ],
  degradations: [
    {
      code: 'worker.planned',
      message: 'Cola de trabajos local: todavía no implementado (previsto en S02).',
    },
    { code: 'llm.disabled', message: 'Modelo de lenguaje: no configurado.' },
  ],
};

export const settingsFixture: SettingsResponse = {
  version: '0.0.0-test',
  host: '127.0.0.1',
  port: 8765,
  log_level: 'INFO',
  data_dir: 'F:\\datos-de-prueba',
  database_file: 'F:\\datos-de-prueba\\opofuente.sqlite3',
  disk_total_bytes: 500_000_000_000,
  disk_free_bytes: 123_456_789_012,
  cors_origins: ['http://127.0.0.1:5173'],
  llm: {
    provider: 'disabled',
    model: null,
    base_url_configured: false,
    api_key_configured: false,
    sends_data_off_device: false,
  },
  embeddings: { provider: 'disabled', model: null },
  ocr: { tesseract_configured: false, tesseract_available: false },
  editable: false,
};
