import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it } from 'vitest';

import type {
  DocumentDetail,
  DocumentPage,
  DocumentSummary,
  Evidence,
  Mapping,
  Section,
  Version,
  VersionDiff,
} from '../../src/api/library';
import type { Curriculum, Opposition } from '../../src/api/profiles';
import { AppShell } from '../../src/app/AppShell';
import { AssignmentsTab } from '../../src/features/library/AssignmentsTab';
import { VersionsTab } from '../../src/features/library/VersionsTab';
import { LibraryPage } from '../../src/pages/LibraryPage';
import { renderWithProviders, stubApi, type StubbedRoute } from './testUtils';

/**
 * Pantalla de Biblioteca (S05) desde el comportamiento real: qué se ve en el listado, qué se pide
 * al servidor al filtrar, qué enseña cada parte de la ficha, qué se copia al citar y qué se dice
 * cuando el servidor rechaza una operación. Las respuestas imitan el contrato real, incluido el 409
 * con su motivo.
 */

const CANDIDATA: Version = {
  id: 'ver-1',
  logical_document_id: 'doc-1',
  version_label: 'convocatoria 2025',
  status: 'candidate',
  is_accepted: false,
  artifact_id: 'art-1',
  representation_id: 'rep-1',
  published_at: '2025-12-22',
  valid_from: null,
  valid_to: null,
  retrieved_at: '2026-01-05T09:00:00Z',
  language: 'es',
  supersedes_id: null,
  rights: {
    code: 'unknown',
    review_status: 'unknown',
    license_name: null,
    license_url: null,
    attribution: null,
    commercial_reuse: false,
    sharing: false,
    notes: null,
    is_restricted: true,
  },
  official_url: 'https://www.boe.es/diario_boe/txt.php?id=BOE-A-2025-26262',
  content_hash: 'b'.repeat(64),
  approved_at: null,
  approved_by: null,
  section_count: 2,
  evidence_count: 2,
};

const ACEPTADA: Version = {
  ...CANDIDATA,
  status: 'accepted',
  is_accepted: true,
  approved_at: '2026-02-10T10:00:00Z',
  approved_by: 'local',
};

const REUTILIZABLE: Version = {
  ...CANDIDATA,
  id: 'ver-2',
  logical_document_id: 'doc-2',
  version_label: 'edición propia',
  status: 'accepted',
  is_accepted: true,
  official_url: null,
  rights: {
    code: 'reuse_with_conditions',
    review_status: 'reviewed',
    license_name: 'CC BY 4.0',
    license_url: 'https://creativecommons.org/licenses/by/4.0/',
    attribution: 'Autoría de prueba',
    commercial_reuse: true,
    sharing: true,
    notes: 'Se puede citar con atribución.',
    is_restricted: false,
  },
};

const DOC_CANDIDATO: DocumentSummary = {
  id: 'doc-1',
  canonical_title: 'Convocatoria TAI 2025',
  document_type: 'convocation',
  owner_scope: 'private_user',
  is_public: false,
  authority_tier: null,
  canonical_identifier: 'BOE-A-2025-26262',
  active_version: CANDIDATA,
  version_count: 2,
  mapping_count: 0,
  created_at: '2026-01-05T09:00:00Z',
};

const DOC_ACEPTADO: DocumentSummary = {
  id: 'doc-2',
  canonical_title: 'Apuntes propios del tema 1',
  document_type: 'personal_notes',
  owner_scope: 'private_user',
  is_public: false,
  authority_tier: null,
  canonical_identifier: null,
  active_version: REUTILIZABLE,
  version_count: 1,
  mapping_count: 2,
  created_at: '2026-01-06T09:00:00Z',
};

const DOC_SIN_VERSION: DocumentSummary = {
  id: 'doc-3',
  canonical_title: 'Material sin promocionar',
  document_type: 'unknown',
  owner_scope: 'generated',
  is_public: false,
  authority_tier: null,
  canonical_identifier: null,
  active_version: null,
  version_count: 0,
  mapping_count: 0,
  created_at: '2026-01-07T09:00:00Z',
};

const PAGINA: DocumentPage = {
  documents: [DOC_CANDIDATO, DOC_ACEPTADO, DOC_SIN_VERSION],
  total: 3,
  limit: 50,
  offset: 0,
};

const SECCIONES: Section[] = [
  {
    id: 'sec-1',
    document_version_id: CANDIDATA.id,
    section_type: 'page',
    title: 'Convocatoria y bases',
    label: null,
    position: 1,
    ordinal: 1,
    parent_id: null,
    page_start: 1,
    page_end: 1,
    char_start: 0,
    char_end: 120,
  },
  {
    id: 'sec-2',
    document_version_id: CANDIDATA.id,
    section_type: 'page',
    title: 'Ejercicio único',
    label: null,
    position: 2,
    ordinal: 2,
    parent_id: 'sec-1',
    page_start: 2,
    page_end: 3,
    char_start: 121,
    char_end: 260,
  },
];

const EVIDENCIA: Evidence[] = [
  {
    id: 'ev-1',
    document_version_id: CANDIDATA.id,
    text: 'El proceso de selección estará formado por un ejercicio único.',
    normalized_text: 'El proceso de selección estará formado por un ejercicio único.',
    ordinal: 1,
    section_id: 'sec-1',
    page: 1,
    citation_label: 'Convocatoria y bases, pág. 1',
    quality: 'good',
    index_status: 'indexed',
    char_start: 0,
    char_end: 61,
  },
  {
    id: 'ev-2',
    document_version_id: CANDIDATA.id,
    text: 'Primera parte: cuestionario de conocimientos.',
    normalized_text: 'Primera parte: cuestionario de conocimientos.',
    ordinal: 2,
    section_id: 'sec-2',
    page: 2,
    citation_label: 'Ejercicio único, pág. 2',
    quality: 'usable_with_warnings',
    index_status: 'pending',
    char_start: 121,
    char_end: 165,
  },
];

/** Versión sin URL oficial y con evidencia sin etiqueta de cita: se cita por su página. */
const SECCIONES_DOS: Section[] = [
  {
    id: 'sec-1b',
    document_version_id: REUTILIZABLE.id,
    section_type: 'page',
    title: 'Tema 1',
    label: null,
    position: 1,
    ordinal: 1,
    parent_id: null,
    page_start: 1,
    page_end: 1,
    char_start: 0,
    char_end: 90,
  },
];

const EVIDENCIA_DOS: Evidence[] = [
  {
    id: 'ev-1b',
    document_version_id: REUTILIZABLE.id,
    text: 'Apuntes propios del tema 1.',
    normalized_text: 'Apuntes propios del tema 1.',
    ordinal: 1,
    section_id: 'sec-1b',
    page: 1,
    citation_label: null,
    quality: 'good',
    index_status: 'indexed',
    char_start: 0,
    char_end: 27,
  },
];

const MAPEOS: Mapping[] = [
  {
    id: 'map-1',
    node_id: 'node-i-1',
    node_path: 'I.1',
    node_title: 'La Constitución Española de 1978',
    node_depth: 1,
    depth: 1,
    coverage_type: 'partial',
    confidence: 0.7,
    status: 'accepted',
    subject_type: 'document_version',
    subject_id: CANDIDATA.id,
    subject_label: 'Convocatoria TAI 2025',
    source_proposal_id: 'p-tema',
    approved_at: '2026-02-01T10:00:00Z',
  },
];

const DETALLE: DocumentDetail = {
  document: DOC_CANDIDATO,
  versions: [
    CANDIDATA,
    { ...CANDIDATA, id: 'ver-0', version_label: 'borrador', status: 'rejected' },
  ],
};

const DETALLE_DOS: DocumentDetail = { document: DOC_ACEPTADO, versions: [REUTILIZABLE] };

/** Comparación servida por el servidor para las dos versiones del documento candidato. */
const DIFF: VersionDiff = {
  document_id: 'doc-1',
  from_version_id: 'ver-1',
  to_version_id: 'ver-0',
  sections: [
    {
      label: 'Convocatoria y bases',
      kind: 'changed',
      left: 'El plazo es de diez días.',
      right: 'El plazo es de veinte días.',
      left_truncated: false,
      right_truncated: false,
    },
    {
      label: 'Anexo I',
      kind: 'added',
      left: null,
      right: 'Anexo nuevo del temario.',
      left_truncated: false,
      right_truncated: false,
    },
  ],
  added: 1,
  removed: 0,
  changed: 1,
  unchanged: 0,
  has_changes: true,
};

const OPOSICIONES: Opposition[] = [
  {
    id: 'op-1',
    code: 'tai-age',
    name: 'Técnico Auxiliar de Informática',
    description: null,
    active: true,
    active_convocation: {
      id: 'conv-1',
      code: 'tai-age-2025',
      published_at: '2025-12-22',
      status: 'active',
    },
  },
  {
    id: 'op-2',
    code: 'gc-cabos-guardias',
    name: 'Guardia Civil (cabos y guardias)',
    description: null,
    active: false,
    active_convocation: null,
  },
];

const CURRICULO: Curriculum = {
  convocation_id: 'conv-1',
  convocation_code: 'tai-age-2025',
  opposition_code: 'tai-age',
  counts: { block: 1, topic: 1 },
  nodes: [
    {
      id: 'node-bloque',
      node_type: 'block',
      official_code: 'I',
      title: 'Organización del Estado',
      description: null,
      position: 1,
      path: 'I',
      depth: 0,
      children: [
        {
          id: 'node-tema',
          node_type: 'topic',
          official_code: 'I.1',
          title: 'La Constitución Española de 1978',
          description: null,
          position: 1,
          path: 'I.1',
          depth: 1,
          children: [],
        },
      ],
    },
  ],
};

const PROMOCION = {
  document_id: 'doc-1',
  version_id: 'ver-1',
  created_document: false,
  created_version: false,
  applied: true,
  reason: null,
};

/** Colecciones de la biblioteca (DEBT-017): una con miembros y otra vacía. */
const COLECCIONES = [
  {
    id: 'col-1',
    name: 'Oposición 2026',
    description: 'Material del año',
    item_count: 2,
    items: ['ver-1', 'ver-2'],
    created_at: '2026-09-19T12:00:00+00:00',
  },
  {
    id: 'col-2',
    name: 'Repaso',
    description: null,
    item_count: 0,
    items: [],
    created_at: '2026-09-19T12:05:00+00:00',
  },
];

function stubLibraryApi(overrides: Record<string, StubbedRoute> = {}) {  return stubApi({
    '/api/v1/documents?limit=50&offset=0&document_type=convocation&owner_scope=generated': {
      body: { ...PAGINA, documents: [], total: 0 },
    },
    '/api/v1/documents?limit=50&offset=0&document_type=convocation': {
      body: { ...PAGINA, documents: [DOC_CANDIDATO], total: 1 },
    },
    '/api/v1/documents?limit=50&offset=0&owner_scope=generated': {
      body: { ...PAGINA, documents: [DOC_SIN_VERSION], total: 1 },
    },
    '/api/v1/documents?limit=50&offset=0': { body: PAGINA },
    // Colecciones (DEBT-017): la lista de documentos lleva además `collection_id` cuando se filtra.
    '/api/v1/documents?limit=50&offset=0&collection_id=col-1': {
      body: { ...PAGINA, documents: [DOC_CANDIDATO], total: 1 },
    },
    '/api/v1/collections': { body: COLECCIONES },
    '/api/v1/documents/doc-1/versions/ver-1/accept': { body: PROMOCION },
    '/api/v1/documents/doc-1/versions/ver-1/mark-supersedes': { body: PROMOCION },
    // La comparación se pide por ruta, sin parámetros en la clave: el `stubApi` empareja por
    // fragmento de URL y así da igual el orden de `from_version_id` y `to_version_id`.
    '/api/v1/documents/doc-1/diff': { body: DIFF },
    '/api/v1/documents/doc-1/versions': { body: DETALLE.versions },
    '/api/v1/documents/doc-1': { body: DETALLE },
    '/api/v1/documents/doc-2/versions': { body: DETALLE_DOS.versions },
    '/api/v1/documents/doc-2': { body: DETALLE_DOS },
    '/api/v1/document-versions/ver-1/sections': { body: SECCIONES },
    '/api/v1/document-versions/ver-1/evidence': { body: EVIDENCIA },
    '/api/v1/document-versions/ver-2/sections': { body: SECCIONES_DOS },
    '/api/v1/document-versions/ver-2/evidence': { body: EVIDENCIA_DOS },
    // Asignaciones: la ruta del contrato §7 es la de la **versión**, no la de mapeos por sujeto.
    '/api/v1/document-versions/ver-1/mappings': { body: MAPEOS },
    '/api/v1/document-versions/ver-2/mappings': { body: [] },
    // El programa del que salen los nodos a los que se asigna.
    '/api/v1/oppositions': { body: OPOSICIONES },
    '/api/v1/convocations/conv-1/curriculum': { body: CURRICULO },
    ...overrides,
  });
}

function renderLibrary(route = '/biblioteca') {
  return renderWithProviders(
    <AppShell>
      <LibraryPage />
    </AppShell>,
    { route },
  );
}

function peticion(fetchMock: ReturnType<typeof stubLibraryApi>, fragmento: string) {
  return fetchMock.mock.calls.find(
    (call) => typeof call[0] === 'string' && call[0].includes(fragmento),
  );
}

function cuerpoJson(llamada: ReturnType<typeof peticion>): unknown {
  const body = llamada?.[1]?.body;
  if (typeof body !== 'string') {
    throw new Error('la petición no llevaba un cuerpo JSON');
  }
  return JSON.parse(body) as unknown;
}

function tablaDeDocumentos() {
  return screen.getByRole('table', { name: /documentos en la biblioteca/ });
}

function filaDe(titulo: string) {
  return within(tablaDeDocumentos()).getByRole('row', { name: new RegExp(titulo) });
}

async function abrirFicha(titulo: string) {
  await userEvent.click(await screen.findByRole('button', { name: `Abrir la ficha: ${titulo}` }));
  return waitFor(() => screen.getByRole('tablist', { name: 'Partes de la ficha' }));
}

describe('biblioteca: listado y filtros', () => {
  it('lista los documentos con su versión activa, su estado y los avisos', async () => {
    stubLibraryApi();
    renderLibrary();

    const fila = within(await waitFor(() => tablaDeDocumentos())).getByRole('row', {
      name: /Convocatoria TAI 2025/,
    });
    expect(within(fila).getByText('candidata, sin aceptar')).toBeInTheDocument();
    expect(within(fila).getByText('propuesta de cambio, sin aceptar')).toBeInTheDocument();
    expect(within(fila).getByText('derechos restringidos')).toBeInTheDocument();
    expect(within(fila).getByText(/no es la versión buena todavía/)).toBeInTheDocument();
    // El ámbito y la autoridad salen del servidor: lo que no consta se dice, no se inventa.
    expect(within(fila).getByText('privado tuyo')).toBeInTheDocument();
    expect(within(fila).getByText('sin autoridad declarada')).toBeInTheDocument();

    // Un documento sin versión activa no se disfraza: se declara tal cual.
    const sinVersion = within(tablaDeDocumentos()).getByRole('row', {
      name: /Material sin promocionar/,
    });
    expect(within(sinVersion).getByText('sin versión activa')).toBeInTheDocument();
  });

  it('filtra en el servidor por tipo documental y por ámbito', async () => {
    const fetchMock = stubLibraryApi();
    renderLibrary();

    await waitFor(() => tablaDeDocumentos());
    await userEvent.selectOptions(screen.getByLabelText('Tipo documental'), 'convocation');

    await waitFor(() => {
      expect(
        peticion(fetchMock, '/api/v1/documents?limit=50&offset=0&document_type=convocation'),
      ).toBeDefined();
    });
    await waitFor(() => {
      expect(tablaDeDocumentos()).toHaveAccessibleName(/1 documentos/);
    });
    expect(within(tablaDeDocumentos()).queryByText('Apuntes propios del tema 1')).toBeNull();

    await userEvent.selectOptions(screen.getByLabelText('Ámbito'), 'generated');
    await waitFor(() => {
      expect(
        peticion(fetchMock, 'document_type=convocation&owner_scope=generated'),
      ).toBeDefined();
    });
  });

  it('filtra por derechos sobre lo cargado y lo dice en la pantalla', async () => {
    stubLibraryApi();
    renderLibrary();

    await waitFor(() => tablaDeDocumentos());
    await userEvent.selectOptions(screen.getByLabelText('Derechos'), 'restringidos');

    // La API todavía no filtra por derechos: se dice que el recuento es de esta pantalla.
    expect(screen.getByText(/todavía no filtra por derechos/)).toBeInTheDocument();
    expect(within(tablaDeDocumentos()).getByText('Convocatoria TAI 2025')).toBeInTheDocument();
    expect(within(tablaDeDocumentos()).queryByText('Apuntes propios del tema 1')).toBeNull();

    await userEvent.selectOptions(screen.getByLabelText('Derechos'), 'reutilizables');
    expect(within(tablaDeDocumentos()).getByText('Apuntes propios del tema 1')).toBeInTheDocument();
    expect(within(tablaDeDocumentos()).queryByText('Convocatoria TAI 2025')).toBeNull();

    await userEvent.click(screen.getByRole('button', { name: 'Limpiar filtros' }));
    await waitFor(() => {
      expect(within(tablaDeDocumentos()).getByText('Convocatoria TAI 2025')).toBeInTheDocument();
      expect(
        within(tablaDeDocumentos()).getByText('Material sin promocionar'),
      ).toBeInTheDocument();
    });
  });
});

describe('biblioteca: avisos de la ficha', () => {
  it('dice que la versión activa es una propuesta de cambio, sin aceptar', async () => {
    stubLibraryApi();
    renderLibrary();
    await abrirFicha('Convocatoria TAI 2025');

    const aviso = await screen.findByRole('region', {
      name: /La versión activa es una propuesta de cambio, sin aceptar/,
    });
    expect(within(aviso).getByText('candidata, sin aceptar')).toBeInTheDocument();
    expect(within(aviso).getByText(/no porque sea la versión buena/)).toBeInTheDocument();
  });

  it('dice que los derechos están restringidos y que no se puede compartir', async () => {
    stubLibraryApi();
    renderLibrary();
    await abrirFicha('Convocatoria TAI 2025');

    const aviso = await screen.findByRole('region', {
      name: /Derechos restringidos: no se puede compartir/,
    });
    expect(within(aviso).getByText('restringidos')).toBeInTheDocument();
    expect(
      within(aviso).getByText(/no se puede compartir ni publicar el documento/),
    ).toBeInTheDocument();
  });

  it('no avisa de candidata ni de derechos cuando la versión está aceptada', async () => {
    stubLibraryApi();
    renderLibrary();
    await abrirFicha('Apuntes propios del tema 1');

    await screen.findByRole('tablist', { name: 'Partes de la ficha' });
    expect(
      screen.queryByRole('region', {
        name: /La versión activa es una propuesta de cambio, sin aceptar/,
      }),
    ).toBeNull();
    expect(
      screen.queryByRole('region', { name: /Derechos restringidos: no se puede compartir/ }),
    ).toBeNull();
  });
});

describe('biblioteca: las cinco partes de la ficha', () => {
  it('el lector enseña el texto por secciones con su página y su evidencia', async () => {
    stubLibraryApi();
    renderLibrary();
    const tabs = await abrirFicha('Convocatoria TAI 2025');

    expect(within(tabs).getAllByRole('tab')).toHaveLength(5);
    expect(within(tabs).getByRole('tab', { name: 'Lector' })).toHaveAttribute(
      'aria-selected',
      'true',
    );
    expect(
      screen.getByText(/Se lee el texto extraído de la versión «convocatoria 2025»/),
    ).toBeInTheDocument();
    // La primera sección se lee sin tener que elegirla, con su página y su evidencia al lado.
    const parrafo = await screen.findByText(
      'El proceso de selección estará formado por un ejercicio único.',
    );
    expect(parrafo).toHaveClass('reader');
    expect(screen.getByText(/página 1 del original/)).toBeInTheDocument();
    expect(screen.getAllByText(/Convocatoria y bases, pág\. 1/).length).toBeGreaterThan(0);
    expect(screen.getByText(/calidad good/)).toBeInTheDocument();
    // El original que se copió se puede abrir: es la ruta §7 que sirve el fichero, no una ruta del
    // disco, así que el enlace apunta a la API de la versión.
    expect(
      screen.getByRole('link', { name: 'abrir el fichero original que se copió' }),
    ).toHaveAttribute('href', expect.stringContaining('/api/v1/document-versions/ver-1/original'));
  });

  it('la estructura enseña el árbol de secciones con su página', async () => {
    stubLibraryApi();
    renderLibrary();
    const tabs = await abrirFicha('Convocatoria TAI 2025');

    await userEvent.click(within(tabs).getByRole('tab', { name: 'Estructura' }));
    const panel = screen.getByRole('tabpanel');
    expect(await within(panel).findByText('Convocatoria y bases')).toBeInTheDocument();
    expect(within(panel).getByText('Ejercicio único')).toBeInTheDocument();
    expect(within(panel).getByText(/páginas 2-3/)).toBeInTheDocument();
  });

  it('las asignaciones son los mapeos de programa de la versión', async () => {
    stubLibraryApi();
    renderLibrary();
    const tabs = await abrirFicha('Convocatoria TAI 2025');

    await userEvent.click(within(tabs).getByRole('tab', { name: 'Asignaciones' }));
    const tabla = await screen.findByRole('table', {
      name: /asignaciones de programa de la versión/,
    });
    const fila = within(tabla).getByRole('row', { name: /I\.1 La Constitución Española/ });
    expect(within(fila).getByText('cobertura parcial')).toBeInTheDocument();
    expect(within(fila).getByText('aceptada')).toBeInTheDocument();
    expect(within(fila).getByText('70 %')).toBeInTheDocument();
  });

  it('las asignaciones vacías se explican, y se pueden dar de alta desde aquí', async () => {
    stubLibraryApi({
      '/api/v1/document-versions/ver-1/mappings': { body: [] },
    });
    renderLibrary();
    const tabs = await abrirFicha('Convocatoria TAI 2025');

    await userEvent.click(within(tabs).getByRole('tab', { name: 'Asignaciones' }));
    expect(
      await screen.findByText(/no está asignada a ningún nodo del programa/),
    ).toBeInTheDocument();
    expect(screen.getByText(/Se le puede dar una asignación\s+aquí debajo/)).toBeInTheDocument();
    expect(screen.getByLabelText('Nodo del programa')).toBeInTheDocument();
  });

  it('los metadatos enseñan procedencia, autoridad, ámbito y derechos con sus avisos', async () => {
    stubLibraryApi();
    renderLibrary();
    const tabs = await abrirFicha('Convocatoria TAI 2025');

    await userEvent.click(within(tabs).getByRole('tab', { name: 'Metadatos' }));
    const panel = screen.getByRole('tabpanel');
    expect(within(panel).getAllByText('no consta').length).toBeGreaterThan(0);
    expect(within(panel).getByText('sin autoridad declarada')).toBeInTheDocument();
    expect(within(panel).getByText('privado tuyo')).toBeInTheDocument();
    // El estado de revisión de los derechos viene del servidor, no se deduce del código.
    expect(within(panel).getByText('sin revisar')).toBeInTheDocument();
    expect(within(panel).getByText('unknown')).toBeInTheDocument();
    expect(within(panel).getByText('art-1')).toBeInTheDocument();
    expect(within(panel).getByText(/la interfaz no concede/)).toBeInTheDocument();
    expect(
      within(panel).getByText(/Sin revisión explícita, un documento se trata como desconocido/),
    ).toBeInTheDocument();
  });

  it('sin registro de derechos se dice que no constan y se tratan como restringidos', async () => {
    const sinDerechos: Version = { ...CANDIDATA, rights: null };
    stubLibraryApi({
      '/api/v1/documents?limit=50&offset=0': {
        body: { ...PAGINA, documents: [{ ...DOC_CANDIDATO, active_version: sinDerechos }] },
      },
      '/api/v1/documents/doc-1': {
        body: {
          document: { ...DOC_CANDIDATO, active_version: sinDerechos },
          versions: [sinDerechos],
        },
      },
      '/api/v1/documents/doc-1/versions': { body: [sinDerechos] },
    });
    renderLibrary();
    const tabs = await abrirFicha('Convocatoria TAI 2025');

    const aviso = await screen.findByRole('region', {
      name: /Derechos restringidos: no se puede compartir/,
    });
    expect(
      within(aviso).getByText(/no trae ningún registro de derechos/),
    ).toBeInTheDocument();

    await userEvent.click(within(tabs).getByRole('tab', { name: 'Metadatos' }));
    expect(
      await screen.findByText(/no consta ninguna revisión de derechos/),
    ).toBeInTheDocument();
  });
});

describe('biblioteca: versiones', () => {
  it('acepta una versión con confirmación y el listado refleja el estado aceptado', async () => {
    const pagina: DocumentPage = {
      documents: [DOC_CANDIDATO, DOC_ACEPTADO, DOC_SIN_VERSION],
      total: 3,
      limit: 50,
      offset: 0,
    };
    const fetchMock = stubLibraryApi({
      '/api/v1/documents?limit=50&offset=0': { body: pagina },
    });
    renderLibrary();
    const tabs = await abrirFicha('Convocatoria TAI 2025');
    await userEvent.click(within(tabs).getByRole('tab', { name: 'Versiones y diff' }));

    await userEvent.click(
      await screen.findByRole('button', { name: 'Aceptar la versión: convocatoria 2025' }),
    );
    // La aceptación es crítica: pide confirmación antes de enviarla.
    expect(screen.getByText(/¿Confirmas que «convocatoria 2025»/)).toBeInTheDocument();
    // El servidor pasará a devolver la versión ya aceptada: es lo único que la interfaz puede
    // enseñar después, y se comprueba que lo vuelve a pedir en lugar de suponerlo.
    pagina.documents = [
      { ...DOC_CANDIDATO, active_version: ACEPTADA },
      DOC_ACEPTADO,
      DOC_SIN_VERSION,
    ];
    await userEvent.click(
      screen.getByRole('button', {
        name: 'Confirmar la aceptación de la versión: convocatoria 2025',
      }),
    );

    await waitFor(() => {
      expect(peticion(fetchMock, '/documents/doc-1/versions/ver-1/accept')).toBeDefined();
    });
    expect(peticion(fetchMock, '/documents/doc-1/versions/ver-1/accept')?.[1]?.method).toBe('POST');

    await waitFor(() => {
      expect(within(filaDe('Convocatoria TAI 2025')).getByText('aceptada')).toBeInTheDocument();
    });
    expect(
      within(filaDe('Convocatoria TAI 2025')).queryByText('propuesta de cambio, sin aceptar'),
    ).toBeNull();
  });

  it('cuenta lo que la aplicación hizo sola al aceptar: las preguntas importadas', async () => {
    // S12.5: aceptar una versión de un banco de preguntas las importa sin que nadie lo pida. Lo que
    // se comprueba aquí es que el usuario **se entera**: si no, tendría que ir al banco a ver si
    // pasó algo.
    const fetchMock = stubLibraryApi({
      '/api/v1/documents/doc-1/versions/ver-1/accept': {
        body: {
          ...PROMOCION,
          questions_imported: 43,
          question_set_id: 'set-1',
          questions_note: 'importadas 43 preguntas de este documento',
          questions_catalogued: 43,
        },
      },
    });
    renderLibrary();
    const tabs = await abrirFicha('Convocatoria TAI 2025');
    await userEvent.click(within(tabs).getByRole('tab', { name: 'Versiones y diff' }));
    await userEvent.click(
      await screen.findByRole('button', { name: 'Aceptar la versión: convocatoria 2025' }),
    );
    await userEvent.click(
      screen.getByRole('button', {
        name: 'Confirmar la aceptación de la versión: convocatoria 2025',
      }),
    );

    const aviso = await screen.findByRole('region', {
      name: /Lo que la aplicación hizo al aceptar/,
    });
    expect(within(aviso).getByText(/Se importaron 43 preguntas/)).toBeInTheDocument();
    expect(within(aviso).getByText(/Ya se pueden estudiar/)).toBeInTheDocument();
    // Y se dice que quedaron catalogadas por tema: sin eso, el diagnóstico por temas no las vería.
    expect(within(aviso).getByText(/43 quedaron catalogadas por bloque y tema/)).toBeInTheDocument();
    expect(peticion(fetchMock, '/documents/doc-1/versions/ver-1/accept')).toBeDefined();
  });

  it('dice por qué NO importó nada, en lugar de callarse', async () => {
    // «No hizo nada» con su motivo también es información: si esperabas que importara, quieres
    // saber por qué no lo ha hecho.
    stubLibraryApi({
      '/api/v1/documents/doc-1/versions/ver-1/accept': {
        body: {
          ...PROMOCION,
          questions_imported: 0,
          question_set_id: null,
          questions_note: 'el material está clasificado como «curriculum»',
        },
      },
    });
    renderLibrary();
    const tabs = await abrirFicha('Convocatoria TAI 2025');
    await userEvent.click(within(tabs).getByRole('tab', { name: 'Versiones y diff' }));
    await userEvent.click(
      await screen.findByRole('button', { name: 'Aceptar la versión: convocatoria 2025' }),
    );
    await userEvent.click(
      screen.getByRole('button', {
        name: 'Confirmar la aceptación de la versión: convocatoria 2025',
      }),
    );

    const aviso = await screen.findByRole('region', {
      name: /Lo que la aplicación hizo al aceptar/,
    });
    expect(
      within(aviso).getByText(/No se importaron preguntas: el material está clasificado/),
    ).toBeInTheDocument();
  });

  it('marca que una versión sustituye a otra, con confirmación y envío explícito', async () => {
    const fetchMock = stubLibraryApi();
    renderLibrary();
    const tabs = await abrirFicha('Convocatoria TAI 2025');
    await userEvent.click(within(tabs).getByRole('tab', { name: 'Versiones y diff' }));

    await userEvent.click(
      await screen.findByRole('button', {
        name: 'Marcar qué versión sustituye: convocatoria 2025',
      }),
    );
    await userEvent.selectOptions(
      screen.getByLabelText(/¿A qué versión sustituye «convocatoria 2025»\?/),
      'ver-0',
    );
    await userEvent.click(
      screen.getByRole('button', {
        name: 'Confirmar que convocatoria 2025 sustituye a la versión elegida',
      }),
    );

    await waitFor(() => {
      expect(peticion(fetchMock, '/documents/doc-1/versions/ver-1/mark-supersedes')).toBeDefined();
    });
    const llamada = peticion(fetchMock, '/documents/doc-1/versions/ver-1/mark-supersedes');
    expect(llamada?.[1]?.method).toBe('POST');
    expect(cuerpoJson(llamada)).toEqual({ superseded_id: 'ver-0' });
  });

  it('cuenta el 409 como operación no aplicada, con el motivo del servidor', async () => {
    stubLibraryApi({
      '/api/v1/documents/doc-1/versions/ver-1/mark-supersedes': {
        status: 409,
        contentType: 'application/problem+json',
        body: {
          type: 'about:blank',
          title: 'Conflict',
          status: 409,
          detail: 'La versión indicada no sustituye a ninguna versión viva del documento',
          code: 'classification_conflict',
          correlation_id: 'corr-de-prueba',
          instance: '/api/v1/documents/doc-1/versions/ver-1/mark-supersedes',
        },
      },
    });
    renderLibrary();
    const tabs = await abrirFicha('Convocatoria TAI 2025');
    await userEvent.click(within(tabs).getByRole('tab', { name: 'Versiones y diff' }));

    await userEvent.click(
      await screen.findByRole('button', {
        name: 'Marcar qué versión sustituye: convocatoria 2025',
      }),
    );
    await userEvent.selectOptions(
      screen.getByLabelText(/¿A qué versión sustituye «convocatoria 2025»\?/),
      'ver-0',
    );
    await userEvent.click(
      screen.getByRole('button', {
        name: 'Confirmar que convocatoria 2025 sustituye a la versión elegida',
      }),
    );

    expect(await screen.findByText('El servidor la rechazó')).toBeInTheDocument();
    expect(
      screen.getByText(/no sustituye a ninguna versión viva del documento/),
    ).toBeInTheDocument();
    expect(screen.getByText(/Un conflicto no cambia nada/)).toBeInTheDocument();
  });

  it('compara las versiones con lo que devuelve el servidor, sin inventar nada', async () => {
    stubLibraryApi();
    renderLibrary();
    const tabs = await abrirFicha('Convocatoria TAI 2025');
    await userEvent.click(within(tabs).getByRole('tab', { name: 'Versiones y diff' }));

    expect(
      screen.getByRole('heading', { name: 'Comparar dos versiones (diff)' }),
    ).toBeInTheDocument();
    // La comparación es la del servidor: se ve el resumen y la sección que cambió.
    expect(await screen.findByText(/con el texto cambiado: 1/)).toBeInTheDocument();
    expect(screen.getByText('El plazo es de veinte días.')).toBeInTheDocument();
    // Las versiones reales están listadas con su estado.
    expect(screen.getByText('rechazada')).toBeInTheDocument();
    expect(screen.getAllByText('candidata, sin aceptar').length).toBeGreaterThan(0);
  });
});

describe('biblioteca: copiar cita', () => {
  it('copia título, versión y sección o página, y lo avisa', async () => {
    const user = userEvent.setup();
    stubLibraryApi();
    renderLibrary();
    await abrirFicha('Convocatoria TAI 2025');

    await user.click(
      await screen.findByRole('button', {
        name: /^Copiar la cita: Convocatoria TAI 2025, Convocatoria y bases, pág\. 1$/,
      }),
    );

    const copiado = await navigator.clipboard.readText();
    expect(copiado).toContain('Título: «Convocatoria TAI 2025»');
    expect(copiado).toContain('Versión: convocatoria 2025');
    expect(copiado).toContain('Lugar: Convocatoria y bases, pág. 1');
    expect(copiado).toContain('https://www.boe.es/diario_boe/txt.php?id=BOE-A-2025-26262');
    expect(
      await screen.findByText(/copiado: título, versión, Convocatoria y bases, pág\. 1 y URL/),
    ).toBeInTheDocument();
  });

  it('cita por página cuando no consta la etiqueta, y dice que la URL no consta', async () => {
    const user = userEvent.setup();
    stubLibraryApi();
    renderLibrary();
    await abrirFicha('Apuntes propios del tema 1');

    await user.click(
      await screen.findByRole('button', {
        name: 'Copiar la cita: Apuntes propios del tema 1, página 1',
      }),
    );

    const copiado = await navigator.clipboard.readText();
    expect(copiado).toContain('Título: «Apuntes propios del tema 1»');
    expect(copiado).toContain('Versión: edición propia');
    expect(copiado).toContain('Lugar: página 1');
    expect(copiado).toContain('URL: no consta');
  });
});

/** Las dos pestañas que trabajan con datos del servidor, con sus respuestas tal cual llegan. */
const VERSIONES: Version[] = [
  CANDIDATA,
  { ...CANDIDATA, id: 'ver-0', version_label: 'borrador', status: 'rejected', is_accepted: false },
];

const DIFF_SIN_SECCIONES: VersionDiff = {
  document_id: 'doc-1',
  from_version_id: 'ver-1',
  to_version_id: 'ver-0',
  sections: [],
  added: 0,
  removed: 0,
  changed: 0,
  unchanged: 0,
  has_changes: false,
};

function nada(): void {
  // Manejador vacío para las pruebas que no comprueban esa acción.
}

describe('biblioteca: comparación de versiones', () => {
  function renderVersiones(
    props: Partial<Parameters<typeof VersionsTab>[0]> = {},
  ): ReturnType<typeof renderWithProviders> {
    return renderWithProviders(
      <VersionsTab
        documentId="doc-1"
        versions={VERSIONES}
        busy={false}
        conflict={null}
        error={null}
        isPending={false}
        isError={false}
        onRetry={nada}
        onAccept={nada}
        onSupersede={nada}
        fromVersionId="ver-1"
        toVersionId="ver-0"
        onSelectFrom={nada}
        onSelectTo={nada}
        diff={DIFF}
        diffIsPending={false}
        diffIsError={false}
        onRetryDiff={nada}
        {...props}
      />,
    );
  }

  it('enseña la comparación que sirve el servidor, sección a sección', () => {
    renderVersiones();

    expect(screen.getByText(/con el texto cambiado: 1/)).toBeInTheDocument();
    expect(screen.getByText(/Nuevas: 1/)).toBeInTheDocument();
    expect(screen.getByText('texto cambiado')).toBeInTheDocument();
    expect(screen.getByText('sección nueva')).toBeInTheDocument();
    expect(screen.getByText('El plazo es de veinte días.')).toBeInTheDocument();
    expect(screen.getByText('El plazo es de diez días.')).toBeInTheDocument();
    // Lo que no estaba en una de las dos versiones se dice con palabras, no con un hueco.
    expect(screen.getAllByText(/no estaba|no está/).length).toBeGreaterThan(0);
  });

  it('avisa de que hay texto recortado cuando el servidor lo marca así', () => {
    renderVersiones({
      diff: {
        ...DIFF,
        sections: [
          {
            label: 'Convocatoria y bases',
            kind: 'changed',
            left: 'viejo',
            right: 'nuevo',
            left_truncated: true,
            right_truncated: false,
          },
        ],
      },
    });

    expect(screen.getByText(/recortan al mostrarlos/)).toBeInTheDocument();
    expect(screen.getByText(/viejo … recortado/)).toBeInTheDocument();
  });

  it('explica por qué una comparación sin secciones está vacía, sin decir que no hay cambios', () => {
    renderVersiones({ diff: DIFF_SIN_SECCIONES });

    expect(screen.getByText(/no tienen ninguna\s+con la que comparar/)).toBeInTheDocument();
    expect(screen.getByText(/DEBT-009/)).toBeInTheDocument();
    expect(screen.queryByRole('table', { name: /Comparación de/ })).not.toBeInTheDocument();
  });

  it('con una sola versión dice que hacen falta dos, en lugar de comparar consigo misma', () => {
    renderVersiones({ versions: [CANDIDATA] });

    expect(screen.getByText(/Comparar necesita al menos dos versiones/)).toBeInTheDocument();
    expect(screen.queryByRole('table', { name: /Comparación de/ })).not.toBeInTheDocument();
  });

  it('si el servidor no devuelve la comparación, lo dice y ofrece reintentar', () => {
    renderVersiones({ diff: null, diffIsError: true });

    expect(screen.getByText('No se pudo comparar las versiones')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Reintentar/ })).toBeInTheDocument();
  });
});

describe('biblioteca: asignaciones de programa', () => {
  function renderAsignaciones(
    props: Partial<Parameters<typeof AssignmentsTab>[0]> = {},
  ): ReturnType<typeof renderWithProviders> {
    return renderWithProviders(
      <AssignmentsTab
        version={CANDIDATA}
        versionCount={2}
        mappings={[]}
        isPending={false}
        isError={false}
        onRetry={nada}
        oppositions={OPOSICIONES}
        convocationId="conv-1"
        onConvocationChange={nada}
        curriculum={CURRICULO}
        curriculumIsPending={false}
        onAssign={nada}
        onRemove={nada}
        busy={false}
        actionError={null}
        {...props}
      />,
    );
  }

  it('explica que no hay asignaciones y ofrece darlas de alta aquí mismo', () => {
    renderAsignaciones();

    expect(
      screen.getByText(/no está asignada a ningún nodo del programa/),
    ).toBeInTheDocument();
    expect(screen.getByText(/Se le puede dar una asignación\s+aquí debajo/)).toBeInTheDocument();
    expect(screen.getByLabelText('Nodo del programa')).toBeInTheDocument();
  });

  it('da de alta la asignación con el nodo y la cobertura elegidos', async () => {
    const asignadas: { nodeId: string; cobertura: string }[] = [];
    renderAsignaciones({
      onAssign: (nodeId, coverage) => {
        asignadas.push({ nodeId, cobertura: coverage });
      },
    });

    // El árbol del programa llega aplanado, con sus dos niveles: bloque y tema.
    const selector = screen.getByLabelText('Nodo del programa');
    expect(within(selector).getByRole('option', { name: /I · Organización del Estado/ })).toBeInTheDocument();
    expect(within(selector).getByRole('option', { name: /— I\.1 · La Constitución/ })).toBeInTheDocument();

    await userEvent.selectOptions(selector, 'node-tema');
    await userEvent.selectOptions(screen.getByLabelText('Cobertura'), 'complete');
    await userEvent.click(
      screen.getByRole('button', { name: 'Asignar a la versión: el nodo elegido' }),
    );

    expect(asignadas).toEqual([{ nodeId: 'node-tema', cobertura: 'complete' }]);
  });

  it('no deja asignar mientras no se elige nodo', () => {
    renderAsignaciones();

    expect(
      screen.getByRole('button', { name: 'Asignar a la versión: el nodo elegido' }),
    ).toBeDisabled();
  });

  it('quita una asignación solo después de confirmarlo, y no por accidente', async () => {
    const quitadas: string[] = [];
    renderAsignaciones({
      mappings: MAPEOS,
      onRemove: (mappingId) => {
        quitadas.push(mappingId);
      },
    });

    await userEvent.click(screen.getByRole('button', { name: 'Quitar la asignación: I.1' }));
    expect(quitadas).toEqual([]);
    expect(screen.getByText(/¿Quitar la asignación de/)).toBeInTheDocument();

    await userEvent.click(
      screen.getByRole('button', { name: 'Confirmar quitar la asignación: I.1' }),
    );
    expect(quitadas).toEqual(['map-1']);
  });

  it('muestra el motivo del servidor cuando rechaza la operación', () => {
    renderAsignaciones({
      actionError: 'El nodo indicado no existe en el programa de esta convocatoria.',
    });

    expect(screen.getByText('El servidor no aplicó la operación')).toBeInTheDocument();
    expect(
      screen.getByText('El nodo indicado no existe en el programa de esta convocatoria.'),
    ).toBeInTheDocument();
  });

  it('sin convocatoria activa dice de dónde sale el programa en lugar de ofrecer una lista vacía', () => {
    renderAsignaciones({ oppositions: [], convocationId: null, curriculum: null });

    expect(screen.getByText(/No hay ninguna convocatoria activa/)).toBeInTheDocument();
    expect(screen.queryByLabelText('Nodo del programa')).not.toBeInTheDocument();
  });
});

describe('biblioteca: colecciones (DEBT-017)', () => {
  /**
   * La tarjeta de colecciones, ya **cargada** (una `section` no tiene rol propio, así que se localiza
   * por su encabezado). Se espera a que el cargador desaparezca: quedarse en «Cargando…» hacía que las
   * cuatro pruebas de colecciones fallaran por mirar antes de tiempo.
   */
  async function panelColecciones(): Promise<HTMLElement> {
    const titulo = await screen.findByRole('heading', { name: 'Colecciones' });
    const seccion = titulo.closest('section') as HTMLElement;
    await waitFor(() => {
      expect(within(seccion).queryByText(/Cargando las colecciones/)).not.toBeInTheDocument();
    });
    return seccion;
  }

  /** La tarjeta de colecciones del documento abierto, ya cargada (ver `panelColecciones`). */
  async function panelDocumentoAbierto(): Promise<HTMLElement> {
    const titulo = await screen.findByRole('heading', {
      name: 'Colecciones del documento abierto',
    });
    const seccion = titulo.closest('section') as HTMLElement;
    // Puede quedarse en «crea una arriba» (sin colecciones) o enseñar el selector; lo que no puede
    // es quedarse cargando.
    await waitFor(() => {
      expect(within(seccion).queryByText(/Cargando/)).not.toBeInTheDocument();
    });
    return seccion;
  }

  /**
   * El botón que **filtra** por una colección. Desde que una colección despliega sus miembros, dos
   * botones llevan su nombre en el texto accesible; se distinguen por lo que son: el filtro es un
   * interruptor (`aria-pressed`) y el desplegable, una divulgación (`aria-expanded`).
   */
  function filtroDe(panel: HTMLElement, nombre: string): HTMLElement {
    const candidatos = within(panel).getAllByRole('button', { name: new RegExp(nombre) });
    const filtro = candidatos.find((boton) => boton.getAttribute('aria-pressed') !== null);
    if (filtro === undefined) {
      throw new Error(`ningún botón de filtro menciona «${nombre}»`);
    }
    return filtro;
  }

  it('enseña las colecciones con sus miembros y deja crear una nueva', async () => {
    const fetchMock = stubLibraryApi({ '/api/v1/collections': { body: COLECCIONES } });
    renderLibrary();

    const panel = await panelColecciones();
    const oposicion = filtroDe(panel, 'Oposición 2026');
    expect(oposicion).toHaveTextContent('Oposición 2026');
    expect(oposicion).toHaveTextContent('2 miembros');
    const repaso = filtroDe(panel, 'Repaso');
    expect(repaso).toHaveTextContent('Repaso');
    expect(repaso).toHaveTextContent('0 miembros');

    const campo = within(panel).getByLabelText('Nombre de la colección');
    await userEvent.type(campo, 'Temario 2026');
    expect(campo).toHaveValue('Temario 2026');
    const crear = within(panel).getByRole('button', { name: 'Crear la colección' });
    expect(crear).toBeEnabled();
    await userEvent.click(crear);

    // La lectura del listado también va a `/collections`, así que se busca la **escritura**: la que
    // lleva método POST. Buscar «la última» no vale: después de crear, la pantalla vuelve a leer.
    const envio = fetchMock.mock.calls.find(
      (call) =>
        typeof call[0] === 'string' &&
        call[0].endsWith('/api/v1/collections') &&
        call[1]?.method === 'POST',
    );
    expect(cuerpoJson(envio)).toEqual({ name: 'Temario 2026', description: null });
  });

  it('filtra la lista por colección y lo dice, sin descartar nada en el navegador', async () => {
    const fetchMock = stubLibraryApi({ '/api/v1/collections': { body: COLECCIONES } });
    renderLibrary();

    const panel = await panelColecciones();
    await userEvent.click(filtroDe(panel, 'Oposición 2026'));

    // La petición lleva el filtro: el servidor es quien decide qué documentos son de la colección.
    await waitFor(() => {
      expect(peticion(fetchMock, 'collection_id=col-1')).toBeDefined();
    });
    expect(
      await screen.findByText(/filtrados por la colección elegida, en el servidor/),
    ).toBeInTheDocument();

    // Y volver a pulsar la misma colección quita el filtro.
    await userEvent.click(filtroDe(panel, 'Oposición 2026'));
    await waitFor(() => {
      expect(screen.queryByText(/filtrados por la colección elegida/)).not.toBeInTheDocument();
    });
  });

  it('añade la versión activa del documento abierto a una colección', async () => {
    const fetchMock = stubLibraryApi({ '/api/v1/collections': { body: COLECCIONES } });
    renderLibrary('/biblioteca?documento=doc-1');

    const seccion = await panelDocumentoAbierto();
    await userEvent.selectOptions(within(seccion).getByLabelText('Añadir a una colección'), 'col-2');
    await userEvent.click(within(seccion).getByRole('button', { name: 'Añadir a la colección' }));

    await waitFor(() => {
      expect(peticion(fetchMock, '/api/v1/collections/col-2/items')).toBeDefined();
    });
    // Se añade la **versión activa** del documento, no «el documento» a secas.
    expect(cuerpoJson(peticion(fetchMock, '/api/v1/collections/col-2/items'))).toEqual({
      subject_type: 'document_version',
      subject_id: DETALLE.document.active_version?.id,
    });
  });

  it('quita un miembro de una colección sin borrar el documento', async () => {
    const fetchMock = stubLibraryApi({ '/api/v1/collections': { body: COLECCIONES } });
    renderLibrary();

    const panel = await panelColecciones();
    await userEvent.click(
      within(panel).getByRole('button', { name: 'Ver los miembros de «Oposición 2026»' }),
    );
    await userEvent.click(
      within(panel).getByRole('button', {
        name: 'Quitar el miembro ver-1 de «Oposición 2026»',
      }),
    );

    await waitFor(() => {
      expect(peticion(fetchMock, '/api/v1/collections/col-1/items')).toBeDefined();
    });
    const envio = fetchMock.mock.calls.find(
      (call) =>
        typeof call[0] === 'string' &&
        call[0].endsWith('/api/v1/collections/col-1/items') &&
        call[1]?.method === 'DELETE',
    );
    // Se quita el miembro concreto, y la operación es un DELETE del sujeto: no borra material.
    expect(cuerpoJson(envio)).toEqual({ subject_type: 'document_version', subject_id: 'ver-1' });

    // Y se dice **donde se hizo**: la tarjeta de colecciones, que es la que está a la vista. El aviso
    // guardaba antes un estado que solo se pintaba dentro de la ficha de un documento abierto, así
    // que quitar un miembro con la ficha cerrada no avisaba de nada.
    const aviso = await within(panel).findByRole('status');
    expect(aviso).toHaveTextContent(/El documento no se ha borrado/);
  });

  it('sin colecciones no ofrece un selector vacío: dice cómo crear una', async () => {
    stubLibraryApi({ '/api/v1/collections': { body: [] } });
    renderLibrary('/biblioteca?documento=doc-1');

    const panel = await panelColecciones();
    expect(within(panel).getByText(/Todavía no hay colecciones/)).toBeInTheDocument();

    const seccion = await panelDocumentoAbierto();
    expect(within(seccion).getByText(/crea una arriba/)).toBeInTheDocument();
    expect(within(seccion).queryByLabelText('Añadir a una colección')).not.toBeInTheDocument();
  });
});
