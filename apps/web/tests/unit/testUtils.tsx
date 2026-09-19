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
import type {
  ConvocationDetail,
  Curriculum,
  CurriculumNodeDetail,
  Opposition,
} from '../../src/api/profiles';

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

/** Sustituye `fetch` por respuestas fijas que imitan el contrato real de la API.
 *
 * Cuando varias claves encajan con la URL gana la **más específica** (la más larga): así una ruta
 * general (`/ingestion-batches/x`) no se come a otra más concreta (`…/x/retry`), y el orden en el
 * que se declaran las respuestas deja de importar.
 */
export function stubApi(routes: Record<string, StubbedRoute>) {
  // El tipo de la función incluye `init` para que las pruebas puedan comprobar el método HTTP
  // (por ejemplo, que activar una oposición es un POST), aunque la simulación no lo use.
  const fetchMock = vi.fn<(input: RequestInfo | URL, init?: RequestInit) => Promise<Response>>(
    (input) => {
      const url =
        typeof input === 'string' ? input : input instanceof URL ? input.href : input.url;
      const match = Object.keys(routes)
        .filter((path) => url.includes(path))
        .sort((left, right) => right.length - left.length)[0];
      if (match === undefined) {
        return Promise.resolve(
          new Response(JSON.stringify({ code: 'not_found' }), {
            status: 404,
            headers: { 'content-type': 'application/problem+json' },
          }),
        );
      }
      const route = routes[match] as StubbedRoute;
      return Promise.resolve(
        new Response(JSON.stringify(route.body), {
          status: route.status ?? 200,
          headers: { 'content-type': route.contentType ?? 'application/json' },
        }),
      );
    },
  );
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
      id: 'ocr',
      label: 'OCR (Tesseract)',
      status: 'disabled',
      detail:
        'Sin ruta configurada. Las imágenes y los PDF escaneados quedan pendientes sin bloquear la aplicación.',
      // Sin `planned_slice`: el OCR no llega con un slice ya cerrado, y la API ya no lo promete.
    },
    {
      id: 'llm',
      label: 'Modelo de lenguaje',
      status: 'disabled',
      detail:
        'Sin proveedor: las respuestas se componen del propio corpus (extractivas) y citan cada afirmación. Un modelo de lenguaje llegaría con la deuda DEBT-014.',
    },
    {
      id: 'embeddings',
      label: 'Embeddings',
      status: 'disabled',
      detail:
        'Sin proveedor de embeddings decidido: la búsqueda es literal (FTS5) y cada respuesta lo declara como degradación (DEBT-014).',
    },
    {
      id: 'fts5',
      label: 'Búsqueda literal (FTS5)',
      status: 'enabled',
      detail:
        'Índice léxico comprobado: tabla externa sobre evidence_spans, ordenada por bm25, con los disparadores que la mantienen al día; se rehace cuando haga falta sin salir de SQLite.',
    },
    {
      id: 'artifact_store',
      label: 'Almacén de originales por SHA-256',
      status: 'enabled',
      detail: 'Copia inmutable por contenido. Los originales no se mueven ni se borran.',
    },
    {
      id: 'worker',
      label: 'Cola de trabajos local',
      status: 'enabled',
      detail: 'Cola persistida en SQLite con lease, trabajada por este proceso.',
    },
    {
      id: 'vector_index',
      label: 'Índice vectorial local',
      status: 'unavailable',
      detail:
        'Sin proveedor de embeddings no hay vectores que indexar: la búsqueda del corpus es literal (FTS5) sobre el texto extraído (DEBT-014).',
    },
  ],
  degradations: [
    {
      code: 'ocr.disabled',
      message:
        'OCR (Tesseract): no configurado. Sin ruta configurada. Las imágenes y los PDF escaneados quedan pendientes sin bloquear la aplicación.',
    },
    {
      code: 'llm.disabled',
      message:
        'Modelo de lenguaje: no configurado. Sin proveedor: las respuestas se componen del propio corpus (extractivas) y citan cada afirmación. Un modelo de lenguaje llegaría con la deuda DEBT-014.',
    },
    {
      code: 'embeddings.disabled',
      message:
        'Embeddings: no configurado. Sin proveedor de embeddings decidido: la búsqueda es literal (FTS5) y cada respuesta lo declara como degradación (DEBT-014).',
    },
    {
      code: 'vector_index.unavailable',
      message:
        'Índice vectorial local: no disponible. Sin proveedor de embeddings no hay vectores que indexar: la búsqueda del corpus es literal (FTS5) sobre el texto extraído (DEBT-014).',
    },
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

export const TAI_ID = 'opp-tai';
export const GC_ID = 'opp-gc';
export const TAI_CONVOCATION_ID = 'conv-tai';
export const GC_CONVOCATION_ID = 'conv-gc';

export const oppositionsFixture: Opposition[] = [
  {
    id: TAI_ID,
    code: 'tai-age',
    name: 'Cuerpo de Técnicos Auxiliares de Informática de la Administración del Estado',
    description: 'Programa de cuatro bloques y treinta y tres temas.',
    active: true,
    active_convocation: {
      id: TAI_CONVOCATION_ID,
      code: 'tai-age-2025',
      published_at: '2025-12-22',
      status: 'active',
    },
  },
  {
    id: GC_ID,
    code: 'gc-cabos-guardias',
    name: 'Escala de Cabos y Guardias de la Guardia Civil',
    description: 'Programa de veinticinco temas.',
    active: false,
    active_convocation: {
      id: GC_CONVOCATION_ID,
      code: 'gc-cabos-guardias-2026',
      published_at: '2026-05-08',
      status: 'active',
    },
  },
];

export const convocationFixture: ConvocationDetail = {
  id: TAI_CONVOCATION_ID,
  code: 'tai-age-2025',
  title:
    'Resolución de 18 de diciembre de 2025, de la Secretaría de Estado de Función Pública, por la que se convocan procesos selectivos (código 1188)',
  official_url: 'https://www.boe.es/diario_boe/txt.php?id=BOE-A-2025-26262',
  published_at: '2025-12-22',
  exam_date: null,
  status: 'active',
  source_reference: 'BOE-A-2025-26262 · ANEXO V',
  opposition_id: TAI_ID,
  opposition_code: 'tai-age',
  opposition_name: 'Cuerpo de Técnicos Auxiliares de Informática',
  parts: [
    {
      code: 'ejercicio_unico',
      name: 'Ejercicio único',
      kind: 'group',
      format: null,
      position: 1,
      parent_code: null,
      ordinary_items: null,
      reserve_items: null,
      options_per_question: null,
      score_min: 0,
      score_max: 100,
      pass_score: null,
      wrong_penalty_fraction: null,
      fail_if_errors_gte: null,
      time_minutes: 120,
      structure_note: 'Dos partes conjuntas, obligatorias y eliminatorias.',
      notes: null,
      evidence_quote: 'El proceso de selección estará formado por un ejercicio único',
    },
    {
      code: 'primera_parte',
      name: 'Primera parte: cuestionario de conocimientos',
      kind: 'test',
      format: 'single_choice',
      position: 1,
      parent_code: 'ejercicio_unico',
      ordinary_items: 80,
      reserve_items: 5,
      options_per_question: null,
      score_min: 0,
      score_max: 50,
      pass_score: 25,
      wrong_penalty_fraction: 0.3333333333,
      fail_if_errors_gte: null,
      time_minutes: null,
      structure_note: 'Máximo de 80 preguntas.',
      notes: null,
      evidence_quote: 'Primera parte: consistirá en contestar por escrito un cuestionario',
    },
  ],
  rules: [
    {
      code: 'blank_answer_penalty',
      kind: 'integer',
      value_text: '0',
      description: 'Las respuestas en blanco no penalizan.',
      evidence_quote: 'Las respuestas en blanco no penalizan.',
    },
  ],
};

export const curriculumFixture: Curriculum = {
  convocation_id: TAI_CONVOCATION_ID,
  convocation_code: 'tai-age-2025',
  opposition_code: 'tai-age',
  counts: { block: 4, topic: 33, epigraph: 0 },
  nodes: [
    {
      id: 'node-i',
      node_type: 'block',
      official_code: 'I',
      title: 'Organización del Estado y Administración electrónica',
      description: null,
      position: 1,
      path: 'I',
      depth: 0,
      children: [
        {
          id: 'node-i-1',
          node_type: 'topic',
          official_code: '1',
          title: 'La Constitución Española de 1978',
          description: null,
          position: 1,
          path: 'I.1',
          depth: 1,
          children: [],
        },
        {
          id: 'node-i-2',
          node_type: 'topic',
          official_code: '2',
          title: 'Las Cortes Generales',
          description: null,
          position: 2,
          path: 'I.2',
          depth: 1,
          children: [],
        },
      ],
    },
  ],
};

export const nodeDetailFixture: CurriculumNodeDetail = {
  node: curriculumFixture.nodes[0]!.children[0]!,
  convocation_id: TAI_CONVOCATION_ID,
  convocation_code: 'tai-age-2025',
  convocation_title: convocationFixture.title,
  official_url: convocationFixture.official_url,
  published_at: '2025-12-22',
  opposition_code: 'tai-age',
  opposition_name: convocationFixture.opposition_name,
  source_reference: 'BOE-A-2025-26262 · ANEXO V',
  ancestors: [curriculumFixture.nodes[0]!],
  coverage: null,
};
