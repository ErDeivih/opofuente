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
import type { PendingActions, StudyReadiness } from '../../src/api/readiness';
import type {
  CurriculumDetail as TemarioDetail,
  CurriculumNode,
  CurriculumNodeDetail as TemarioNodeDetail,
  CurriculumSummary,
  NodeMaterialPage,
  NodeQuestionPage,
  Progress,
} from '../../src/api/temario';

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
    destination: 'disabled',
    destination_reason: 'el modelo de lenguaje no está configurado: no se envía nada',
  },
  embeddings: {
    provider: 'disabled',
    model: null,
    base_url_configured: false,
    destination: 'disabled',
    destination_reason: 'sin proveedor de embeddings configurado',
  },
  ocr: { tesseract_configured: false, tesseract_available: false },
  limits: {
    max_file_bytes: 536_870_912,
    max_batch_entries: 50_000,
    max_url_bytes: 67_108_864,
    max_url_redirects: 5,
    max_paste_bytes: 4_194_304,
    max_zip_entries: 2_000,
    max_zip_uncompressed_bytes: 1_073_741_824,
    max_zip_ratio: 200,
    max_zip_depth: 1,
    max_pdf_pages: 2_000,
    max_representation_chars: 2_000_000,
    worker_poll_seconds: 1,
    job_lease_seconds: 60,
  },
  editable: false,
};

export const TAI_ID = 'opp-tai';
export const GC_ID = 'opp-gc';
export const TAI_CONVOCATION_ID = 'conv-tai';
export const GC_CONVOCATION_ID = 'conv-gc';

/**
 * El resumen de preparación de S12.6, como lo sirve el servidor.
 *
 * Las frases van con sus cifras y **las compone el servidor**: la pantalla las enseña tal cual, así
 * que estas respuestas son el contrato de lo que se lee en Inicio.
 */
export const studyReadinessFixture: StudyReadiness = {
  opposition_id: TAI_ID,
  opposition_name: 'Cuerpo de Técnicos Auxiliares de Informática de la Administración del Estado',
  convocation_code: 'tai-age-2025',
  ready: false,
  steps: [
    {
      key: 'material',
      title: 'Material por papel',
      status: 'ready',
      detail: '12 documento(s) aceptado(s): Temario o programa (5), Apuntes personales (7)',
      count: 12,
      action_href: '/biblioteca',
      action_label: 'Ver la biblioteca',
    },
    {
      key: 'preguntas',
      title: 'Preguntas por tema',
      status: 'incomplete',
      detail: '70 pregunta(s) en 1 conjunto(s); 62 catalogada(s) por tema. Quedan 8 sin tema',
      count: 70,
      action_href: '/preguntas',
      action_label: 'Ver el banco',
    },
    {
      key: 'claves',
      title: 'Claves activas',
      status: 'ready',
      detail: '1 de 1 conjunto(s) con clave activa',
      count: 1,
      action_href: '/preguntas',
      action_label: 'Ver las plantillas',
    },
  ],
  missing: ['70 pregunta(s) en 1 conjunto(s); 62 catalogada(s) por tema. Quedan 8 sin tema'],
};

/** El mismo resumen con los tres pasos completos: es lo que se ve cuando ya se puede estudiar. */
export const studyReadinessReadyFixture: StudyReadiness = {
  ...studyReadinessFixture,
  ready: true,
  steps: studyReadinessFixture.steps.map((paso) =>
    paso.key === 'preguntas' ? { ...paso, status: 'ready' as const } : paso,
  ),
  missing: [],
};

export const pendingActionsFixture: PendingActions = {
  actions: [
    {
      key: 'clasificaciones',
      title: 'Clasificaciones esperando tu decisión',
      detail: '38 propuesta(s) sin decidir: hasta que se decidan, ese material no está en ningún tema',
      count: 38,
      href: '/revision',
      label: 'Revisar propuestas',
    },
    {
      key: 'versiones',
      title: 'Material sin aceptar',
      detail: '2 versión(es) de documento sin aceptar',
      count: 2,
      href: '/biblioteca',
      label: 'Ver la biblioteca',
    },
  ],
  total: 40,
};

export const pendingActionsEmptyFixture: PendingActions = { actions: [], total: 0 };

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
  curriculum: {
    code: 'informatica-c1',
    name: 'Temario común de informática C1',
    kind: 'common',
    version_code: 'informatica-c1-v1',
    version_title: 'Temario común de informática C1',
  },
  convocation: {
    id: TAI_CONVOCATION_ID,
    code: 'tai-age-2025',
    title: convocationFixture.title,
    official_url: convocationFixture.official_url,
    published_at: '2025-12-22',
    opposition_code: 'tai-age',
    opposition_name: convocationFixture.opposition_name,
    source_reference: 'BOE-A-2025-26262 · ANEXO V',
  },
  appears_in: [],
  particularities: [],
  studied_at: null,
  ancestors: [curriculumFixture.nodes[0]!],
  coverage: null,
};

/* ------------------------------------------- B-005: temario común y ficha de tema */

export const TEMARIO_CODE = 'informatica-c1';
export const TEMARIO_VERSION_CODE = 'informatica-c1-v1';

const TEMARIO_BLOCK_TITLES = [
  'Organización del Estado y Administración electrónica',
  'Tecnología básica',
  'Desarrollo de aplicaciones',
  'Sistemas y comunicaciones',
  'Seguridad y protección de datos',
] as const;

const TEMARIO_BLOCK_PATHS = ['I', 'II', 'III', 'IV', 'V'] as const;

/* Los ocho títulos del bloque I existen; el resto son sintéticos y solo rellenan el árbol. */
const TEMARIO_FIRST_TOPICS = [
  'La Constitución Española de 1978',
  'Las Cortes Generales',
  'El Gobierno y la Administración',
  'La Unión Europea',
  'El régimen local',
  'La Administración electrónica',
  'Protección de datos personales',
  'Transparencia y buen gobierno',
];

/**
 * El árbol del temario común: 5 bloques y 40 temas, en orden oficial.
 *
 * Es el mismo recuento que sirve el servidor (`counts: {block: 5, topic: 40}`); si la pantalla
 * pintara solo algunos, la prueba de «5 bloques y 40 temas» fallaría.
 */
export function buildTemarioNodes(): CurriculumNode[] {
  let numeroDeTema = 0;
  return TEMARIO_BLOCK_TITLES.map((title, blockIndex) => {
    const path = TEMARIO_BLOCK_PATHS[blockIndex]!;
    const children = Array.from({ length: 8 }, (_unused, topicIndex) => {
      numeroDeTema += 1;
      const codigo = topicIndex + 1;
      return {
        id: `tema-${String(numeroDeTema)}`,
        node_type: 'topic' as const,
        official_code: String(codigo),
        title:
          blockIndex === 0
            ? (TEMARIO_FIRST_TOPICS[topicIndex] ?? `Tema ${String(numeroDeTema)}`)
            : `Tema ${String(numeroDeTema)} del bloque ${path}`,
        description: null,
        position: codigo,
        path: `${path}.${String(codigo)}`,
        depth: 1,
        children: [],
        studied_at: null,
      };
    });
    return {
      id: `bloque-${path}`,
      node_type: 'block' as const,
      official_code: path,
      title,
      description: null,
      position: blockIndex + 1,
      path,
      depth: 0,
      children,
      studied_at: null,
    };
  });
}

const TEMARIO_VERSIONS = [
  {
    code: TEMARIO_VERSION_CODE,
    version_no: 1,
    title: 'Temario común de informática C1',
    status: 'active',
  },
];

export const temarioSummaryFixture: CurriculumSummary = {
  code: TEMARIO_CODE,
  name: 'Temario común de informática C1',
  kind: 'common',
  group_code: 'C1',
  family: 'informatica',
  versions: TEMARIO_VERSIONS,
  active_version: TEMARIO_VERSIONS[0]!,
};

export const temarioDetailFixture: TemarioDetail = {
  code: TEMARIO_CODE,
  name: 'Temario común de informática C1',
  kind: 'common',
  group_code: 'C1',
  family: 'informatica',
  versions: TEMARIO_VERSIONS,
  active_version: TEMARIO_VERSIONS[0]!,
  counts: { block: 5, topic: 40, epigraph: 0 },
  nodes: buildTemarioNodes(),
  progress: null,
};

/** Temas marcados por bloque: 4 + 2 + 6 = 12 de 40 (30 %), como en el avance real. */
const TEMARIO_STUDIED_BY_BLOCK = [4, 2, 6, 0, 0] as const;

export const temarioProgressFixture: Progress = {
  curriculum_code: TEMARIO_CODE,
  version_code: TEMARIO_VERSION_CODE,
  blocks: temarioDetailFixture.nodes.map((block, index) => {
    const estudiados = TEMARIO_STUDIED_BY_BLOCK[index] ?? 0;
    const total = block.children.length;
    return {
      block_id: block.id,
      path: block.path,
      title: block.title,
      position: block.position,
      topics_total: total,
      topics_studied: estudiados,
      topics_with_activity: 0,
      percent: total === 0 ? 0 : Math.round((estudiados * 1000) / total) / 10,
    };
  }),
  topics_total: 40,
  topics_studied: 12,
  topics_with_activity: 0,
  percent: 30,
};

export const temarioNodeFixture: TemarioNodeDetail = {
  node: temarioDetailFixture.nodes[0]!.children[0]!,
  curriculum: {
    code: TEMARIO_CODE,
    name: 'Temario común de informática C1',
    kind: 'common',
    version_code: TEMARIO_VERSION_CODE,
    version_title: 'Temario común de informática C1',
  },
  convocation: null,
  appears_in: [
    {
      convocation_id: TAI_CONVOCATION_ID,
      convocation_code: 'tai-age-2025',
      convocation_title: convocationFixture.title,
      convocation_status: 'active',
      official_url: 'https://www.boe.es/diario_boe/txt.php?id=BOE-A-2025-26262',
      role: 'primary',
      source_reference: 'ANEXO V, apartado 3',
      omitted: false,
      adjustments: [],
    },
    {
      convocation_id: 'conv-diputacion',
      convocation_code: 'diputacion-2026',
      convocation_title: 'Convocatoria de Técnico de Informática de la Diputación',
      convocation_status: 'draft',
      official_url: 'https://oposicionesinformatica.com/1-plaza-diputacion/',
      role: 'complementary',
      source_reference: null,
      omitted: false,
      adjustments: [],
    },
  ],
  particularities: [],
  studied_at: null,
  ancestors: [temarioDetailFixture.nodes[0]!],
  coverage: null,
};

/* ------------------------------------------- B-007: preguntas y material del tema */

export const temarioQuestionPageFixture: NodeQuestionPage = {
  node_id: 'tema-1',
  total: 2,
  limit: 100,
  offset: 0,
  questions: [
    {
      id: 'preg-1',
      question_set_id: 'set-1',
      set_title: 'Banco TAI',
      stable_key: 'q-1',
      stem: '¿Cuál es la norma suprema del ordenamiento jurídico?',
      question_type: 'single_choice',
      origin_type: 'official',
      position: 1,
      is_reserve: false,
    },
    {
      id: 'preg-2',
      question_set_id: 'set-1',
      set_title: 'Banco TAI',
      stable_key: 'q-2',
      stem: 'La Constitución Española de 1978 entró en vigor el 29 de diciembre.',
      question_type: 'true_false',
      origin_type: 'official',
      position: 2,
      is_reserve: true,
    },
  ],
};

export const temarioMaterialPageFixture: NodeMaterialPage = {
  node_id: 'tema-1',
  total: 2,
  materials: [
    {
      subject_type: 'document_version',
      subject_id: 'doc-ver-1',
      document_id: 'doc-1',
      document_version_id: 'doc-ver-1',
      title: 'Apuntes de Constitución',
      section_title: null,
      page: null,
      citation_label: null,
      excerpt: null,
      coverage_type: 'complete',
    },
    {
      subject_type: 'evidence',
      subject_id: 'span-1',
      document_id: 'doc-1',
      document_version_id: 'doc-ver-1',
      title: 'Apuntes de Constitución',
      section_title: null,
      page: 3,
      citation_label: 'pág. 3',
      excerpt: 'La Constitución es la norma suprema del ordenamiento jurídico.',
      coverage_type: 'complete',
    },
  ],
};
