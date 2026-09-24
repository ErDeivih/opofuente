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
  ConvocationReference,
  Curriculum,
  CurriculumNodeDetail,
  Opposition,
} from '../../src/api/profiles';
import type { Dossier, DossierVersion } from '../../src/api/dossier';
import type { PendingActions, StudyReadiness } from '../../src/api/readiness';
import type { MasteryProgram } from '../../src/api/reviews';

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
 *
 * Una clave puede empezar por el método (`"POST /api/v1/…"`) cuando la **misma** ruta responde cosas
 * distintas según el verbo —archivar el dossier y listar sus versiones comparten ruta—: sin eso, la
 * simulación no podría distinguirlas y la prueba estaría comprobando la respuesta equivocada.
 */
export function stubApi(routes: Record<string, StubbedRoute>) {
  // El tipo de la función incluye `init` para que las pruebas puedan comprobar el método HTTP
  // (por ejemplo, que activar una oposición es un POST), aunque la simulación no lo use.
  const fetchMock = vi.fn<(input: RequestInfo | URL, init?: RequestInit) => Promise<Response>>(
    (input, init) => {
      const url =
        typeof input === 'string' ? input : input instanceof URL ? input.href : input.url;
      const metodo = (init?.method ?? 'GET').toUpperCase();
      const candidatas = Object.entries(routes)
        .map(([clave, ruta]) => {
          const [posibleMetodo, ...resto] = clave.split(' ');
          const tieneMetodo = resto.length > 0;
          const camino = tieneMetodo ? resto.join(' ') : clave;
          return { camino, ruta, metodo: tieneMetodo ? posibleMetodo?.toUpperCase() : null };
        })
        .filter(
          (candidata) =>
            url.includes(candidata.camino) &&
            (candidata.metodo === null || candidata.metodo === metodo),
        );
      // Gana la coincidencia más larga; a igualdad de camino, la que declara el método.
      candidatas.sort(
        (izquierda, derecha) =>
          derecha.camino.length - izquierda.camino.length ||
          (derecha.metodo === null ? 0 : 1) - (izquierda.metodo === null ? 0 : 1),
      );
      const elegida = candidatas[0];
      if (elegida === undefined) {
        return Promise.resolve(
          new Response(JSON.stringify({ code: 'not_found' }), {
            status: 404,
            headers: { 'content-type': 'application/problem+json' },
          }),
        );
      }
      const route = elegida.ruta;
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
export const CELADOR_ID = 'opp-celador';
export const CELADOR_ESTABILIZACION_ID = 'conv-celador-estabilizacion';
export const CELADOR_2022_ID = 'conv-celador-2022';

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

/** El estado de estudio por nodo del programa (S10 y DEBT-027 §5). */
export const masteryFixture: MasteryProgram = {
  opposition_id: TAI_ID,
  convocation_id: TAI_CONVOCATION_ID,
  nodes: [
    {
      curriculum_node_id: 'node-i',
      level: 'medium',
      attempts: 12,
      correct: 8,
      recent_attempts: 5,
      accuracy: 0.6666666666666666,
      explanation: '5 de los últimos 10 intentos correctos: dominio medio (provisional).',
      has_estimate: true,
      study_state: {
        questions_total: 12,
        questions_by_status: [
          { status: 'annulled', count: 1 },
          { status: 'complete', count: 10 },
          { status: 'conflicting', count: 1 },
        ],
        questions_by_origin: [
          { status: 'official', count: 4 },
          { status: 'private', count: 8 },
        ],
        reviews_due: 2,
        next_review_at: null,
      },
    },
    {
      curriculum_node_id: 'node-i-1',
      level: 'no_data',
      attempts: 0,
      correct: 0,
      recent_attempts: 0,
      accuracy: null,
      explanation: 'Ningún intento en este tema: no hay nada que estimar.',
      has_estimate: false,
      study_state: {
        questions_total: 3,
        questions_by_status: [{ status: 'verified', count: 3 }],
        questions_by_origin: [{ status: 'official', count: 3 }],
        reviews_due: 0,
        next_review_at: '2026-09-25T08:00:00Z',
      },
    },
  ],
  nodes_total: 2,
  nodes_with_estimate: 1,
  nodes_insufficient: 0,
  nodes_without_data: 1,
  note: 'El dominio se estima por tema con los intentos de las preguntas asignadas a ese tema.',
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

/* ------------------------------------------------------------------ S12.2: dos convocatorias */

/**
 * TAI y Guardia Civil publican una sola convocatoria cada una: con esas listas el selector de
 * convocatoria no se pinta, que es lo que esperan las pruebas de la pantalla de Programa.
 *
 * Se declaran a propósito: `/api/v1/oppositions/{id}/convocations` contiene
 * `/api/v1/oppositions`, así que sin una respuesta propia el simulador serviría la lista de
 * oposiciones en su lugar.
 */
export const taiConvocationsFixture: ConvocationReference[] = [
  {
    id: TAI_CONVOCATION_ID,
    code: 'tai-age-2025',
    title: 'Resolución de 18 de diciembre de 2025, por la que se convocan procesos selectivos',
    official_url: 'https://www.boe.es/diario_boe/txt.php?id=BOE-A-2025-26262',
    published_at: '2025-12-22',
    exam_date: null,
    status: 'active',
  },
];

export const gcConvocationsFixture: ConvocationReference[] = [
  {
    id: GC_CONVOCATION_ID,
    code: 'gc-cabos-guardias-2026',
    title: 'Resolución de 8 de mayo de 2026, por la que se convoca el proceso selectivo',
    official_url: 'https://www.boe.es/diario_boe/txt.php?id=BOE-A-2026-9982',
    published_at: '2026-05-08',
    exam_date: null,
    status: 'active',
  },
];

/**
 * Celador (SACYL) con dos convocatorias publicadas: la ordinaria de acceso libre de 2022, que es la
 * vigente y ya se examinó, y la del proceso de estabilización, publicada y disponible pero sin fecha
 * de ejercicio (el proceso sigue pendiente).
 */
export const celadorOppositionsFixture: Opposition[] = [
  {
    id: CELADOR_ID,
    code: 'celador-sacyl',
    name: 'Celador/a del Servicio de Salud de Castilla y León',
    description: 'Esta oposición tiene más de una convocatoria publicada.',
    active: true,
    active_convocation: {
      id: CELADOR_2022_ID,
      code: 'celador-sacyl-2022',
      published_at: '2022-12-22',
      status: 'active',
    },
  },
];

export const celadorConvocationsFixture: ConvocationReference[] = [
  {
    id: CELADOR_ESTABILIZACION_ID,
    code: 'celador-sacyl-estabilizacion-2022',
    title:
      'ORDEN SAN/1917/2022, de 23 de diciembre, por la que se convoca proceso excepcional de estabilización de empleo temporal',
    official_url: 'https://bocyl.jcyl.es/html/2022/12/28/html/BOCYL-D-28122022-8.do',
    published_at: '2022-12-28',
    exam_date: null,
    status: 'available',
  },
  {
    id: CELADOR_2022_ID,
    code: 'celador-sacyl-2022',
    title:
      'ORDEN SAN/1828/2022, de 12 de diciembre, por la que se convoca proceso selectivo para el acceso a la condición de personal estatutario fijo',
    official_url: 'https://bocyl.jcyl.es/html/2022/12/22/html/BOCYL-D-22122022-7.do',
    published_at: '2022-12-22',
    exam_date: '2023-11-12',
    status: 'active',
  },
];

/** La convocatoria vigente de Celador: la ordinaria de acceso libre de 2022. */
export const celadorConvocationFixture: ConvocationDetail = {
  id: CELADOR_2022_ID,
  code: 'celador-sacyl-2022',
  title: celadorConvocationsFixture[1]!.title,
  official_url: celadorConvocationsFixture[1]!.official_url,
  published_at: '2022-12-22',
  exam_date: '2023-11-12',
  status: 'active',
  source_reference: 'BOCYL-D-22122022-7 · ANEXO I (descripción del proceso) y ANEXO II (programa)',
  opposition_id: CELADOR_ID,
  opposition_code: 'celador-sacyl',
  opposition_name: 'Celador/a del Servicio de Salud de Castilla y León',
  parts: [
    {
      code: 'ejercicio_unico',
      name: 'Ejercicio único de la fase de oposición',
      kind: 'test',
      format: 'single_choice',
      position: 1,
      parent_code: null,
      ordinary_items: 70,
      reserve_items: 7,
      options_per_question: 4,
      score_min: 0,
      score_max: 150,
      pass_score: null,
      wrong_penalty_fraction: 0.25,
      fail_if_errors_gte: null,
      time_minutes: 90,
      structure_note: 'Un único ejercicio obligatorio y eliminatorio.',
      notes: null,
      evidence_quote:
        'El ejercicio consistirá, para todos los turnos, en contestar un cuestionario que estará formado por 70 preguntas relacionadas con el programa más el 10% de preguntas de reserva para posibles anulaciones.',
    },
  ],
  rules: [
    {
      code: 'published_exam_date',
      kind: 'text',
      value_text: '2023-11-12',
      description: 'Fecha del ejercicio, fijada por la resolución publicada en el BOCYL.',
      evidence_quote: 'para la realización del ejercicio de la fase de oposición el día 12 de noviembre',
    },
  ],
};

/** La convocatoria del proceso de estabilización: disponible y todavía sin ejercicio. */
export const celadorEstabilizacionConvocationFixture: ConvocationDetail = {
  id: CELADOR_ESTABILIZACION_ID,
  code: 'celador-sacyl-estabilizacion-2022',
  title: celadorConvocationsFixture[0]!.title,
  official_url: celadorConvocationsFixture[0]!.official_url,
  published_at: '2022-12-28',
  exam_date: null,
  exam_date_note:
    'El plazo de solicitudes cerró en enero de 2023 y el proceso sigue sin ejercicio: la fecha la fijará la resolución de admitidos (base 8.3).',
  status: 'available',
  source_reference: 'BOCYL-D-28122022-8 · ANEXO I y ANEXO V (sección CELADOR)',
  opposition_id: CELADOR_ID,
  opposition_code: 'celador-sacyl',
  opposition_name: 'Celador/a del Servicio de Salud de Castilla y León',
  parts: [
    {
      code: 'ejercicio_unico',
      name: 'Ejercicio único de la fase de oposición del concurso-oposición',
      kind: 'test',
      format: 'single_choice',
      position: 1,
      parent_code: null,
      ordinary_items: 40,
      reserve_items: 4,
      options_per_question: 3,
      score_min: 0,
      score_max: 150,
      pass_score: null,
      wrong_penalty_fraction: 0.1111111111111111,
      fail_if_errors_gte: null,
      time_minutes: 60,
      structure_note: '44 preguntas incluidas las de reserva, en 60 minutos.',
      notes: null,
      evidence_quote:
        'El ejercicio consistirá, para todos los turnos, en contestar un cuestionario que estará formado por un número de preguntas relacionadas con el temario más el 10% de preguntas de reserva para posibles anulaciones.',
    },
  ],
  rules: [
    {
      code: 'wrong_answer_penalty',
      kind: 'text',
      value_text: '1/9 del valor de una respuesta correcta',
      description: 'Cada contestación errónea descuenta una novena parte.',
      evidence_quote:
        'Las contestaciones erróneas se penalizarán con una novena parte (1/9) del valor de las respuestas correctas.',
    },
  ],
};

/** Programa de Celador en el acceso libre de 2022: dieciséis temas sin bloques. */
export const celador2022CurriculumFixture: Curriculum = {
  convocation_id: CELADOR_2022_ID,
  convocation_code: 'celador-sacyl-2022',
  opposition_code: 'celador-sacyl',
  counts: { block: 0, topic: 16, epigraph: 0 },
  nodes: Array.from({ length: 16 }, (_valor, indice) => ({
    id: `node-2022-tema-${indice + 1}`,
    node_type: 'topic' as const,
    official_code: String(indice + 1),
    title: `Tema ${indice + 1} del programa de 2022`,
    description: null,
    position: indice + 1,
    path: String(indice + 1),
    depth: 0,
    children: [],
  })),
};

/** Programa de Celador en la estabilización: dos partes y catorce temas. */export const celadorCurriculumFixture: Curriculum = {
  convocation_id: CELADOR_ESTABILIZACION_ID,
  convocation_code: 'celador-sacyl-estabilizacion-2022',
  opposition_code: 'celador-sacyl',
  counts: { block: 2, topic: 14, epigraph: 0 },
  nodes: [
    {
      id: 'node-parte-general',
      node_type: 'block',
      official_code: 'PARTE GENERAL',
      title: 'Parte general',
      description: null,
      position: 1,
      path: '1',
      depth: 0,
      children: [1, 2, 3, 4, 5].map((numero) => ({
        id: `node-tema-${numero}`,
        node_type: 'topic' as const,
        official_code: `Tema ${numero}`,
        title: `Tema ${numero} de la parte general`,
        description: null,
        position: numero,
        path: `1.${numero}`,
        depth: 1,
        children: [],
      })),
    },
    {
      id: 'node-parte-especifica',
      node_type: 'block',
      official_code: 'PARTE ESPECÍFICA',
      title: 'Parte específica',
      description: null,
      position: 2,
      path: '2',
      depth: 0,
      children: [6, 7, 8, 9, 10, 11, 12, 13, 14].map((numero, indice) => ({
        id: `node-tema-${numero}`,
        node_type: 'topic' as const,
        official_code: `Tema ${numero}`,
        title: `Tema ${numero} de la parte específica`,
        description: null,
        position: indice + 1,
        path: `2.${indice + 1}`,
        depth: 1,
        children: [],
      })),
    },
  ],
};

/* ------------------------------------------------------------------ S13: el dossier del tema */

/**
 * Un dossier con dos fuentes, un pasaje repetido en otra y dos huecos: lo que dice, lo que no dice y
 * lo que falta. Sirve para comprobar que la pantalla **no** enseña el texto repetido dos veces, que
 * declara el hueco y que una fuente sin confirmar lleva su etiqueta.
 */
export const dossierFixture: Dossier = {
  format_version: 1,
  node_id: 'node-i-1',
  path: 'I.1',
  title: 'La Constitución Española de 1978',
  depth: 1,
  generated_at: '2026-09-24T09:00:00Z',
  content_hash: 'a'.repeat(64),
  version_id: null,
  previous_version_id: null,
  sources_total: 2,
  passages_total: 2,
  accepted_sources: 1,
  provisional_sources: 1,
  provisional: true,
  empty: false,
  sources: [
    {
      document_id: 'doc-apuntes',
      document_title: 'Apuntes de la Constitución',
      document_type: 'personal_notes',
      authority_tier: 'C',
      version_id: 'v-apuntes',
      version_label: 'v1',
      version_status: 'accepted',
      quality: 'good',
      mappings: ['accepted'],
      provisional: false,
      passages_total: 1,
      passages: [
        {
          evidence_id: 'span-1',
          text: 'España se constituye en un Estado social y democrático de Derecho.',
          citation_label: 'Título preliminar, pág. 3',
          page: 3,
          section_title: 'Título preliminar',
          ordinal: 1,
          quality: 'good',
          repeated_in: ['Manual de la oposición, pág. 9'],
        },
      ],
    },
    {
      document_id: 'doc-manual',
      document_title: 'Manual de la oposición',
      document_type: 'private_syllabus',
      authority_tier: null,
      version_id: 'v-manual',
      version_label: null,
      version_status: 'accepted',
      quality: 'usable_with_warnings',
      mappings: ['provisional'],
      provisional: true,
      passages_total: 1,
      passages: [
        {
          evidence_id: 'span-2',
          text: 'La soberanía nacional reside en el pueblo español.',
          citation_label: null,
          page: 12,
          section_title: null,
          ordinal: 4,
          quality: 'usable_with_warnings',
          repeated_in: [],
        },
      ],
    },
  ],
  holes: [
    { code: 'mapeo_provisional', count: 1, reason: null },
    { code: 'repetido_en_otra_fuente', count: 1, reason: null },
  ],
};

/** Un tema sin nada asignado: ni fuentes ni pasajes, con su hueco y sin ceros que parezcan datos. */
export const dossierEmptyFixture: Dossier = {
  ...dossierFixture,
  node_id: 'node-vacio',
  path: 'II.1',
  title: 'Tema sin material',
  content_hash: 'b'.repeat(64),
  sources_total: 0,
  passages_total: 0,
  accepted_sources: 0,
  provisional_sources: 0,
  provisional: false,
  empty: true,
  sources: [],
  holes: [{ code: 'sin_material', count: 0, reason: null }],
};

/** Un tema con material asignado que todavía no tiene texto citable y una versión sin aceptar. */
export const dossierHolesFixture: Dossier = {
  ...dossierEmptyFixture,
  sources_total: 0,
  empty: true,
  holes: [
    { code: 'sin_texto', count: 2, reason: null },
    {
      code: 'no_citable',
      count: 3,
      reason: 'la versión está en estado «candidate»',
    },
  ],
};

export const dossierVersionsFixture: DossierVersion[] = [
  {
    id: 'ver-2',
    content_hash: 'c'.repeat(64),
    built_at: '2026-09-24T09:00:00Z',
    sources_count: 2,
    passages_count: 2,
  },
  {
    id: 'ver-1',
    content_hash: 'd'.repeat(64),
    built_at: '2026-09-20T08:00:00Z',
    sources_count: 1,
    passages_count: 1,
  },
];
