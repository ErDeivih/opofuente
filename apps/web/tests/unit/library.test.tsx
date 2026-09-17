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
} from '../../src/api/library';
import { AppShell } from '../../src/app/AppShell';
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

const PROMOCION = {
  document_id: 'doc-1',
  version_id: 'ver-1',
  created_document: false,
  created_version: false,
  applied: true,
  reason: null,
};

function stubLibraryApi(overrides: Record<string, StubbedRoute> = {}) {
  return stubApi({
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
    '/api/v1/documents/doc-1/versions/ver-1/accept': { body: PROMOCION },
    '/api/v1/documents/doc-1/versions/ver-1/mark-supersedes': { body: PROMOCION },
    '/api/v1/documents/doc-1/versions': { body: DETALLE.versions },
    '/api/v1/documents/doc-1': { body: DETALLE },
    '/api/v1/documents/doc-2/versions': { body: DETALLE_DOS.versions },
    '/api/v1/documents/doc-2': { body: DETALLE_DOS },
    '/api/v1/document-versions/ver-1/sections': { body: SECCIONES },
    '/api/v1/document-versions/ver-1/evidence': { body: EVIDENCIA },
    '/api/v1/document-versions/ver-2/sections': { body: SECCIONES_DOS },
    '/api/v1/document-versions/ver-2/evidence': { body: EVIDENCIA_DOS },
    '/api/v1/mappings?subject_type=document_version&subject_id=ver-1': { body: MAPEOS },
    '/api/v1/mappings?subject_type=document_version&subject_id=ver-2': { body: [] },
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

  it('las asignaciones vacías se explican, sin inventar mapeos', async () => {
    stubLibraryApi({
      '/api/v1/mappings?subject_type=document_version&subject_id=ver-1': { body: [] },
    });
    renderLibrary();
    const tabs = await abrirFicha('Convocatoria TAI 2025');

    await userEvent.click(within(tabs).getByRole('tab', { name: 'Asignaciones' }));
    expect(
      await screen.findByText(/no está asignada a ningún nodo del programa/),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/esta pantalla todavía no\s+ofrece ese alta/),
    ).toBeInTheDocument();
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

  it('deja la comparación de versiones preparada y dice que la API no la expone', async () => {
    stubLibraryApi();
    renderLibrary();
    const tabs = await abrirFicha('Convocatoria TAI 2025');
    await userEvent.click(within(tabs).getByRole('tab', { name: 'Versiones y diff' }));

    expect(
      screen.getByRole('heading', { name: 'Comparar dos versiones (diff)' }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/todavía no la expone la API: no hay ruta que devuelva qué cambió/),
    ).toBeInTheDocument();
    // Las versiones reales están listadas con su estado, sin diff inventado.
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
