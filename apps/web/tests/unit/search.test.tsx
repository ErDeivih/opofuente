import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it } from 'vitest';

import type { EvidenceSpan, RagQuery, SearchResult } from '../../src/api/search';
import { AppShell } from '../../src/app/AppShell';
import { AppRoutes } from '../../src/app/routes';
import { SearchPage } from '../../src/pages/SearchPage';
import {
  capabilitiesFixture,
  oppositionsFixture,
  readinessReady,
  renderWithProviders,
  settingsFixture,
  stubApi,
  type StubbedRoute,
} from './testUtils';

/**
 * Buscar y preguntar (S09) desde el comportamiento real: qué se manda, qué se enseña de cada
 * fragmento, qué pasa cuando el corpus no sostiene la respuesta y qué se puede comprobar.
 *
 * Las respuestas imitan el contrato real, incluida la respuesta `insufficient` (que es un resultado,
 * no un error) y los fragmentos que se recuperaron sin usarse.
 */

const FRAGMENTO: EvidenceSpan = {
  id: 'span-1',
  document_id: 'doc-1',
  document_version_id: 'ver-1',
  document_title: 'Constitución Española',
  document_type: 'official_consolidated',
  authority_tier: 'official_consolidated',
  version_status: 'accepted',
  section_id: 'sec-1',
  section_title: 'Título preliminar',
  citation_label: 'Constitución Española, art. 1.1',
  page: 1,
  page_start: 1,
  page_end: 1,
  ordinal: 1,
  text: 'España se constituye en un Estado social y democrático de Derecho.',
};

const FRAGMENTO_OBSOLETO: EvidenceSpan = {
  ...FRAGMENTO,
  id: 'span-2',
  document_title: 'Temario derogado',
  version_status: 'outdated',
  citation_label: 'Temario derogado, tema 1',
  text: 'Texto de la versión anterior.',
};

const BUSQUEDA: SearchResult = {
  hits: [
    { span: FRAGMENTO, rank: 1, score: -1.5, strategy: 'lexical', matched_terms: ['estado'] },
  ],
  total: 1,
  strategy: 'lexical',
  strategies: ['lexical'],
  corpus_revision: 'rev-3-12',
  version_mode: 'current',
  degradations: [
    'sin proveedor de embeddings configurado: la búsqueda es solo léxica (FTS5). El índice vectorial local llega cuando se decida el modelo (DEBT-014).',
  ],
  excluded: ['Temario derogado v1: la versión no está publicada (borrador).'],
};

const RESPUESTA_INSUFICIENTE: RagQuery = {
  id: 'rag-1',
  question: '¿Cuántos diputados tiene el Congreso?',
  strategy: 'lexical',
  version_mode: 'current',
  corpus_revision: 'rev-3-12',
  provider: 'extractive',
  model: null,
  prompt_template_version: 'extractive-v1-brief',
  created_at: '2026-09-17T12:00:00Z',
  answer: {
    id: 'ans-1',
    query_id: 'rag-1',
    status: 'insufficient',
    short_answer: 'No hay evidencia en el corpus para responder a esa pregunta.',
    explanation: 'Se ha buscado sobre el material publicado y vigente y no se ha recuperado nada.',
    claims: [],
    uncertainties: ['no se ha recuperado nada del corpus sobre: diputados, congreso'],
    suggested_followups: ['Comprobar si el temario está importado.'],
    provider: 'extractive',
    model: null,
    prompt_template_version: 'extractive-v1-brief',
    created_at: '2026-09-17T12:00:00Z',
  },
};

const RESPUESTA_RESPALDADA: RagQuery = {
  ...RESPUESTA_INSUFICIENTE,
  id: 'rag-2',
  question: '¿En qué se constituye España?',
  answer: {
    id: 'ans-2',
    query_id: 'rag-2',
    status: 'supported',
    short_answer: 'España se constituye en un Estado social y democrático de Derecho.',
    explanation: 'La afirmación es literal del artículo 1.1.',
    claims: [
      { text: 'España es un Estado social y democrático de Derecho.', support: 'direct', evidence: [FRAGMENTO] },
      { text: 'Eso obliga a los poderes públicos a promover la igualdad.', support: 'inferred', evidence: [] },
    ],
    uncertainties: [],
    suggested_followups: [],
    provider: 'extractive',
    model: null,
    prompt_template_version: 'extractive-v1-brief',
    created_at: '2026-09-17T12:00:00Z',
  },
};

function stubBusqueda(overrides: Record<string, StubbedRoute> = {}) {
  return stubApi({
    '/api/v1/health/ready': { body: readinessReady },
    '/api/v1/capabilities': { body: capabilitiesFixture },
    '/api/v1/settings': { body: settingsFixture },
    '/api/v1/oppositions': { body: oppositionsFixture },
    '/api/v1/search': { body: BUSQUEDA },
    '/api/v1/rag/queries': { body: RESPUESTA_INSUFICIENTE, status: 201 },
    '/api/v1/rag/queries/rag-1/retrieval': {
      body: {
        query_id: 'rag-1',
        corpus_revision: 'rev-3-12',
        hits: [
          { span: FRAGMENTO, rank: 1, score: -1.5, strategy: 'lexical', used: false },
          { span: FRAGMENTO_OBSOLETO, rank: 2, score: -3.2, strategy: 'lexical', used: false },
        ],
        used_ids: [],
      },
    },
    ...overrides,
  });
}

function renderBuscar(route = '/buscar?q=estado') {
  return renderWithProviders(
    <AppShell>
      <AppRoutes />
    </AppShell>,
    { route },
  );
}

/** El cuerpo JSON de la primera petición que contenga el fragmento, con el método si se pide. */
function cuerpoJson(
  fetchMock: ReturnType<typeof stubBusqueda>,
  fragmento: string,
  metodo?: string,
): Record<string, unknown> {
  const llamada = fetchMock.mock.calls.find(
    (call) =>
      typeof call[0] === 'string' &&
      call[0].includes(fragmento) &&
      (metodo === undefined || call[1]?.method === metodo),
  );
  const body = llamada?.[1]?.body;
  if (typeof body !== 'string') {
    throw new Error(`la petición a ${fragmento} no llevaba cuerpo JSON`);
  }
  return JSON.parse(body) as Record<string, unknown>;
}

/** Si se ha llamado a alguna URL que contenga el fragmento. */
function seLlamo(fetchMock: ReturnType<typeof stubBusqueda>, fragmento: string): boolean {
  return fetchMock.mock.calls.some(
    (call) => typeof call[0] === 'string' && call[0].includes(fragmento),
  );
}

describe('búsqueda: pantalla', () => {
  it('enseña cada fragmento con su cita, su texto y el enlace para abrirlo', async () => {
    const fetchMock = stubBusqueda();
    renderBuscar();

    expect(await screen.findByRole('heading', { level: 1, name: 'Buscar y preguntar' })).toBeInTheDocument();
    expect(
      await screen.findByText('España se constituye en un Estado social y democrático de Derecho.'),
    ).toBeInTheDocument();
    expect(screen.getByText('Constitución Española, art. 1.1')).toBeInTheDocument();
    expect(screen.getByText(/coincide en: estado/)).toBeInTheDocument();

    const enlace = screen.getByRole('link', { name: /Abrir en la Biblioteca: / });
    expect(enlace).toHaveAttribute('href', '/biblioteca?documento=doc-1');

    // La búsqueda se manda tal cual se pidió, con el modo de versión por defecto.
    expect(cuerpoJson(fetchMock, '/api/v1/search', 'POST')).toMatchObject({
      query: 'estado',
      version_mode: 'current',
    });
  });

  it('declara la degradación y lo que se ha quedado fuera del corpus', async () => {
    stubBusqueda();
    renderBuscar();

    expect(await screen.findByText('Lo que esta búsqueda no puede hacer')).toBeInTheDocument();
    expect(screen.getByText(/sin proveedor de embeddings configurado/)).toBeInTheDocument();
    expect(screen.getByText('Fuera del corpus')).toBeInTheDocument();
    expect(screen.getByText(/la versión no está publicada \(borrador\)/)).toBeInTheDocument();
  });

  it('no busca con el campo vacío y explica que no hay resultados en vez de callarse', async () => {
    stubBusqueda({
      '/api/v1/search': {
        body: { ...BUSQUEDA, hits: [], total: 0, excluded: [], degradations: [] },
      },
    });
    renderBuscar();

    expect(await screen.findByText(/Ningún fragmento publicado responde a esa búsqueda/)).toBeInTheDocument();
  });
});

describe('preguntar: respuesta con citas', () => {
  it('manda el estilo elegido y enseña la falta de evidencia como resultado, no como error', async () => {
    const fetchMock = stubBusqueda();
    renderBuscar('/buscar');

    await userEvent.type(screen.getByLabelText('Qué buscas'), 'diputados tiene el Congreso');
    await userEvent.click(screen.getByRole('button', { name: 'Preguntar al corpus' }));

    expect(await screen.findByText('evidencia insuficiente')).toBeInTheDocument();
    expect(
      screen.getByText('No hay evidencia en el corpus para responder a esa pregunta.'),
    ).toBeInTheDocument();
    expect(screen.getByText('Lo que no se ha podido sostener')).toBeInTheDocument();
    expect(screen.getByText(/no se ha recuperado nada del corpus sobre: diputados, congreso/)).toBeInTheDocument();
    // La respuesta viene con su procedencia: quién la redactó y con qué revisión del corpus.
    const respuesta = screen.getByRole('region', { name: 'Respuesta' });
    expect(within(respuesta).getByText('extractive')).toBeInTheDocument();
    expect(within(respuesta).getByText('rev-3-12')).toBeInTheDocument();

    expect(cuerpoJson(fetchMock, '/api/v1/rag/queries', 'POST')).toMatchObject({
      query: 'diputados tiene el Congreso',
      style: 'brief',
      version_mode: 'current',
      allow_private_sources: true,
    });
    // Sin evidencia no hay afirmaciones: la pantalla no inventa ninguna.
    expect(screen.queryByText('Afirmaciones y de dónde salen')).toBeNull();
  });

  it('cada afirmación lleva su cita y avisa cuando una no cita nada', async () => {
    stubBusqueda({ '/api/v1/rag/queries': { body: RESPUESTA_RESPALDADA, status: 201 } });
    renderBuscar('/buscar?q=España');

    await userEvent.click(screen.getByRole('button', { name: 'Preguntar al corpus' }));

    expect(await screen.findByText('respaldada por el corpus')).toBeInTheDocument();
    expect(screen.getByText('Afirmaciones y de dónde salen')).toBeInTheDocument();
    expect(screen.getByText('literal del corpus')).toBeInTheDocument();
    expect(screen.getByText('inferida')).toBeInTheDocument();
    // La afirmación inferida no tiene cita: se dice, no se rellena con la de al lado.
    expect(screen.getByText('Esta afirmación no cita ningún fragmento: no se puede comprobar.')).toBeInTheDocument();
  });

  it('la recuperación completa se puede abrir y distingue lo usado de lo descartado', async () => {
    const fetchMock = stubBusqueda();
    renderBuscar('/buscar');

    await userEvent.type(screen.getByLabelText('Qué buscas'), 'diputados');
    await userEvent.click(screen.getByRole('button', { name: 'Preguntar al corpus' }));
    await screen.findByText('evidencia insuficiente');

    // Mientras no se pide, la recuperación no se trae: no se hace trabajo por si acaso.
    expect(seLlamo(fetchMock, '/retrieval')).toBe(false);

    await userEvent.click(screen.getByText('Ver todo lo que se recuperó, se usara o no'));

    await waitFor(() => {
      expect(screen.getByText(/2 fragmentos recuperados/)).toBeInTheDocument();
    });
    expect(screen.getByText(/0 usados en la respuesta/)).toBeInTheDocument();
    const lista = screen.getByText(/2 fragmentos recuperados/).closest('details');
    expect(lista).not.toBeNull();
    expect(screen.getByText('Texto de la versión anterior.')).toBeInTheDocument();
  });

  it('un 409 del servidor se enseña como rechazo, no como respuesta', async () => {
    stubBusqueda({
      '/api/v1/rag/queries': {
        status: 409,
        body: {
          type: 'about:blank',
          title: 'Conflict',
          status: 409,
          detail: 'La consulta ya está registrada con otra recuperación.',
          code: 'conflict',
          correlation_id: 'corr-1',
        },
        contentType: 'application/problem+json',
      },
    });
    renderBuscar('/buscar?q=estado');

    await userEvent.click(screen.getByRole('button', { name: 'Preguntar al corpus' }));

    expect(await screen.findByText('El servidor rechazó la consulta')).toBeInTheDocument();
    expect(screen.queryByRole('heading', { name: 'Respuesta' })).toBeNull();
  });
});

describe('búsqueda global de la cabecera', () => {
  it('lleva a la sección de búsqueda con el término en la dirección', async () => {
    const fetchMock = stubBusqueda();
    renderWithProviders(
      <AppShell>
        <AppRoutes />
      </AppShell>,
      { route: '/' },
    );

    await userEvent.type(await screen.findByLabelText('Buscar en el corpus'), 'artículo 1{enter}');

    expect(await screen.findByRole('heading', { level: 1, name: 'Buscar y preguntar' })).toBeInTheDocument();
    expect(cuerpoJson(fetchMock, '/api/v1/search', 'POST')).toMatchObject({ query: 'artículo 1' });
    // El término sigue en la caja de la cabecera: lo que se busca es lo que está en la dirección.
    expect(screen.getByLabelText('Buscar en el corpus')).toHaveValue('artículo 1');
  });

  it('no navega con el campo vacío', async () => {
    stubBusqueda();
    renderWithProviders(
      <AppShell>
        <AppRoutes />
      </AppShell>,
      { route: '/' },
    );

    await userEvent.type(await screen.findByLabelText('Buscar en el corpus'), '   {enter}');
    expect(screen.queryByRole('heading', { level: 1, name: 'Buscar y preguntar' })).toBeNull();
    expect(screen.getByRole('heading', { level: 1, name: 'Inicio' })).toBeInTheDocument();
  });

  it('con el modo histórico pedido se dice en la pantalla y se manda al servidor', async () => {
    const fetchMock = stubBusqueda({
      '/api/v1/search': { body: { ...BUSQUEDA, version_mode: 'explicit_historical' } },
    });
    renderBuscar('/buscar');

    await userEvent.type(screen.getByLabelText('Qué buscas'), 'temario');
    await userEvent.selectOptions(screen.getByLabelText('Versiones'), 'explicit_historical');
    await userEvent.click(screen.getByRole('button', { name: 'Buscar' }));

    expect(await screen.findByText(/con el histórico incluido/)).toBeInTheDocument();
    expect(cuerpoJson(fetchMock, '/api/v1/search', 'POST')).toMatchObject({
      query: 'temario',
      version_mode: 'explicit_historical',
    });
  });
});

describe('página de búsqueda sola', () => {
  it('sin término en la dirección no pide nada al servidor', () => {
    const fetchMock = stubBusqueda();
    renderWithProviders(<SearchPage />, { route: '/buscar' });

    expect(seLlamo(fetchMock, '/api/v1/search')).toBe(false);
    const boton = screen.getByRole('button', { name: 'Buscar' });
    expect(boton).toBeDisabled();
  });
});
