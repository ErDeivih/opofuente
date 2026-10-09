import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it } from 'vitest';

import type {
  Batch,
  BatchDetail,
  EntryPage,
  IssuePage,
  Representation,
} from '../../src/api/ingestion';
import { AppShell } from '../../src/app/AppShell';
import { PromotePanel } from '../../src/features/ingestion/PromotePanel';
import { TrayPage } from '../../src/pages/TrayPage';
import { renderWithProviders, stubApi, type StubbedRoute } from './testUtils';

/**
 * El paso que faltaba entre la bandeja y la biblioteca.
 *
 * Se prueba desde la pantalla real y contra la petición que sale del navegador, porque lo que hay
 * que garantizar aquí no es «se ve un botón» sino tres cosas concretas:
 *
 * 1. que **pasa a la biblioteca** los artefactos elegidos —antes no había forma de hacerlo desde la
 *    interfaz— y con el identificador del artefacto, no con un nombre inventado;
 * 2. que **no acepta nada**: promocionar deja versiones candidatas, y aceptarlas es otro acto que no
 *    ocurre en esta pantalla (ADR-009). De ahí la comprobación de que **no** se llama a `/accept`;
 * 3. que cuando el servidor no puede o dice que ya estaba, **la pantalla lo cuenta** en vez de dar la
 *    operación por buena.
 */

const lote: Batch = {
  id: 'batch-1',
  kind: 'import',
  mode: 'copy',
  status: 'succeeded',
  source_path_display: '…/OpoFuente/TAI',
  counters: { total: 3, copied: 3, pending: 0 },
  created_at: '2026-09-28T10:00:00Z',
  formats: { '.pdf': 2, '.jpg': 1 },
  issue_counts: {},
  total_items: 3,
};

const detalle: BatchDetail = {
  batch: lote,
  entries: [],
  issues: [],
  report: {
    batch_id: lote.id,
    kind: 'import',
    status: 'succeeded',
    counters: lote.counters,
    issue_counts: {},
    balanced: true,
    artifacts_total: 3,
    generated_at: '2026-09-28T10:01:00Z',
  },
};

const entradasVacias: EntryPage = { entries: [], total: 0, limit: 200, offset: 0 };
const incidenciasVacias: IssuePage = { issues: [], total: 0, limit: 200, offset: 0 };

/** Dos artefactos con texto y uno sin él: el escaneo que hoy no se puede leer. */
const CON_TEXTO_1: Representation = {
  id: 'rep-1',
  artifact_id: 'art-1',
  kind: 'native_text',
  status: 'ready',
  quality: 'good',
  extractor: 'pypdf',
  char_count: 12_000,
  page_count: 30,
  language: 'es',
  ocr_candidate: false,
  warnings: [],
  has_text: true,
  created_at: '2026-09-28T10:01:00Z',
  sources: [{ location: 'pack/APUNTES de BASE/tema 4.pdf', origin_type: 'file', depth: 0 }],
};

const CON_TEXTO_2: Representation = {
  ...CON_TEXTO_1,
  id: 'rep-2',
  artifact_id: 'art-2',
  char_count: 4_500,
  // El mismo contenido desde dos entradas distintas: un ZIP y su contenido copiado a mano.
  sources: [
    { location: 'pack/RECURSOS/tema 5.docx', origin_type: 'file', depth: 0 },
    { location: 'escritorio/BLOQUE 2/tema 5.docx', origin_type: 'file', depth: 1 },
  ],
};

const SIN_TEXTO: Representation = {
  ...CON_TEXTO_1,
  id: 'rep-3',
  artifact_id: 'art-3',
  kind: 'image_metadata',
  quality: 'ocr_unreviewed',
  char_count: 7,
  page_count: 1,
  ocr_candidate: true,
  has_text: false,
  sources: [{ location: 'escritorio/TEST/Azul - Respuestas.pdf', origin_type: 'file', depth: 0 }],
};

const SALIDA_CREADA = {
  document_id: 'doc-1',
  version_id: 'ver-1',
  created_document: true,
  created_version: true,
  applied: true,
  reason: null,
  questions_imported: 0,
  question_set_id: null,
  questions_note: null,
  questions_catalogued: 0,
};

const SALIDA_YA_ESTABA = {
  ...SALIDA_CREADA,
  created_document: false,
  created_version: false,
};

function stubBandeja(overrides: Record<string, StubbedRoute> = {}) {
  return stubApi({
    '/api/v1/ingestion-batches/files': { body: lote },
    '/api/v1/ingestion-batches/paste': { body: lote },
    '/api/v1/ingestion-batches/url': { body: lote },
    '/api/v1/ingestion-batches/batch-1/items': { body: entradasVacias },
    '/api/v1/ingestion-batches/batch-1/issues': { body: incidenciasVacias },
    '/api/v1/ingestion-batches/batch-1/representations': {
      body: [CON_TEXTO_1, CON_TEXTO_2, SIN_TEXTO],
    },
    '/api/v1/ingestion-batches/batch-1': { body: detalle },
    '/api/v1/ingestion-batches': { body: [lote] },
    'POST /api/v1/documents': { body: SALIDA_CREADA },
    ...overrides,
  });
}

/** Abre la bandeja y deja el lote seleccionado, que es lo que hace falta para ver el panel. */
async function abrirLote() {
  renderWithProviders(
    <AppShell>
      <TrayPage />
    </AppShell>,
    { route: '/bandeja' },
  );
  const boton = await screen.findByRole('button', { name: /OpoFuente\/TAI/ });
  await userEvent.click(boton);
  await screen.findByRole('heading', { name: 'Pasar a la biblioteca' });
}

function peticionesA(fetchMock: ReturnType<typeof stubBandeja>, fragmento: string) {
  return fetchMock.mock.calls.filter(
    (call) => typeof call[0] === 'string' && call[0].includes(fragmento),
  );
}

function cuerpoJson(llamada: [RequestInfo | URL, RequestInit?] | undefined): unknown {
  const body = llamada?.[1]?.body;
  if (typeof body !== 'string') {
    throw new Error('la petición no llevaba un cuerpo JSON');
  }
  return JSON.parse(body) as unknown;
}

describe('pasar el material de la bandeja a la biblioteca', () => {
  it('vienen marcados los que tienen texto, y los escaneos sin texto no', async () => {
    stubBandeja();
    await abrirLote();

    const conTexto1 = await screen.findByLabelText(/Pasar a la biblioteca: pack\/APUNTES/);
    expect(conTexto1).toBeChecked();
    expect(screen.getByRole('button', { name: 'Pasar a la biblioteca (2)' })).toBeEnabled();
    // Por defecto no se enseña lo que no tiene texto: es el filtro que deja a la vista lo que se
    // puede leer y citar, y por eso el escaneo no aparece todavía.
    expect(screen.queryByLabelText(/Pasar a la biblioteca: escritorio\/TEST/)).toBeNull();

    // Al pedir ver también los que no tienen texto, aparecen **desmarcados**: un escaneo pendiente de
    // OCR se puede pasar, pero lo decide una persona.
    await userEvent.click(screen.getByLabelText(/Enseñar solo los que tienen texto/));
    const sinTexto = await screen.findByLabelText(/Pasar a la biblioteca: escritorio\/TEST/);
    expect(sinTexto).not.toBeChecked();
    expect(screen.getByText('pendiente de OCR')).toBeInTheDocument();
  });

  it('junta las entradas que traen los mismos bytes y las promociona una sola vez', async () => {
    const fetchMock = stubBandeja();
    await abrirLote();

    // Las dos procedencias del mismo contenido salen en la misma fila, dichas.
    expect(
      await screen.findByText('(y 1 entrada(s) más con el mismo contenido)'),
    ).toBeInTheDocument();

    await userEvent.click(screen.getByRole('button', { name: 'Pasar a la biblioteca (2)' }));

    await waitFor(() => {
      expect(peticionesA(fetchMock, '/api/v1/documents')).toHaveLength(2);
    });
    const enviados = peticionesA(fetchMock, '/api/v1/documents').map((llamada) => ({
      metodo: llamada[1]?.method,
      cuerpo: cuerpoJson(llamada as [RequestInfo | URL, RequestInit?]),
    }));
    expect(enviados).toEqual([
      { metodo: 'POST', cuerpo: { artifact_id: 'art-1', title: null, document_type: 'unknown', authority_tier: null, rights_code: null } },
      { metodo: 'POST', cuerpo: { artifact_id: 'art-2', title: null, document_type: 'unknown', authority_tier: null, rights_code: null } },
    ]);
  });

  it('promocionar no acepta: la pantalla lo dice y no llama a aceptar ninguna versión', async () => {
    const fetchMock = stubBandeja();
    await abrirLote();

    await userEvent.click(screen.getByRole('button', { name: 'Pasar a la biblioteca (2)' }));

    // El texto que ve quien lo hace: candidatas, no aceptadas. La frase va en un párrafo con una
    // parte en negrita, así que se busca por el párrafo entero y no por el texto suelto.
    expect(
      await screen.findByText(
        (_contenido, elemento) =>
          elemento?.tagName === 'P' &&
          (elemento.textContent ?? '').includes('versiones candidatas'),
      ),
    ).toBeInTheDocument();
    expect(await screen.findByText(/2 documento\(s\) nuevo\(s\)/)).toBeInTheDocument();

    // Y la comprobación que importa: aceptar es otro acto, y aquí no ocurre.
    expect(peticionesA(fetchMock, '/accept')).toHaveLength(0);
  });

  it('cuenta aparte lo que ya estaba, porque la promoción es idempotente', async () => {
    stubBandeja({
      'POST /api/v1/documents': { body: SALIDA_YA_ESTABA },
    });
    await abrirLote();

    await userEvent.click(screen.getByRole('button', { name: 'Pasar a la biblioteca (2)' }));

    expect(await screen.findByText(/2 ya estaban en la biblioteca/)).toBeInTheDocument();
    expect(screen.getByText(/0 documento\(s\) nuevo\(s\)/)).toBeInTheDocument();
  });

  it('si el servidor rechaza una promoción, se dice el motivo en vez de dar la operación por hecha', async () => {
    stubBandeja({
      'POST /api/v1/documents': {
        status: 409,
        body: {
          type: 'about:blank',
          title: 'Conflict',
          status: 409,
          detail: 'El artefacto no existe: no hay nada que promocionar',
          code: 'artifact_missing',
        },
        contentType: 'application/problem+json',
      },
    });
    await abrirLote();

    await userEvent.click(screen.getByRole('button', { name: 'Pasar a la biblioteca (2)' }));

    // El motivo del servidor, tal cual, uno por artefacto (aquí fallan los dos), y un recuento que no
    // engaña: cero documentos nuevos.
    expect(
      await screen.findAllByText('El artefacto no existe: no hay nada que promocionar'),
    ).toHaveLength(2);
    expect(screen.getByText(/2 con fallo/)).toBeInTheDocument();
    expect(screen.getByText(/0 documento\(s\) nuevo\(s\)/)).toBeInTheDocument();
  });

  it('el escaneo sin texto se puede pasar a mano, y entonces sí entra', async () => {
    const fetchMock = stubBandeja({ 'POST /api/v1/documents': { body: SALIDA_CREADA } });
    await abrirLote();

    await userEvent.click(await screen.findByLabelText(/Enseñar solo los que tienen texto/));
    await userEvent.click(await screen.findByLabelText(/Pasar a la biblioteca: escritorio\/TEST/));
    await userEvent.click(screen.getByRole('button', { name: 'Pasar a la biblioteca (3)' }));

    await waitFor(() => {
      expect(peticionesA(fetchMock, '/api/v1/documents')).toHaveLength(3);
    });
    const artefactos = peticionesA(fetchMock, '/api/v1/documents').map(
      (llamada) => (cuerpoJson(llamada as [RequestInfo | URL, RequestInit?]) as { artifact_id: string }).artifact_id,
    );
    expect(artefactos).toContain('art-3');
  });

  it('sin nada marcado no se ofrece la operación', async () => {
    stubBandeja();
    await abrirLote();

    await userEvent.click(await screen.findByRole('button', { name: 'Desmarcar todos' }));
    expect(screen.getByRole('button', { name: 'Pasar a la biblioteca (0)' })).toBeDisabled();
  });
});

describe('el panel solo, sin la pantalla', () => {
  it('con una lista vacía lo dice en vez de enseñar una tabla sin filas', async () => {
    stubApi({
      '/api/v1/ingestion-batches/batch-vacio': {
        body: { ...detalle, batch: { ...lote, id: 'batch-vacio' } },
      },
      '/api/v1/ingestion-batches/batch-vacio/representations': { body: [] },
    });
    renderWithProviders(
      <AppShell>
        <PromotePanel batchId="batch-vacio" />
      </AppShell>,
      { route: '/bandeja' },
    );

    expect(
      await screen.findByText(/Este lote no tiene artefactos con representación/),
    ).toBeInTheDocument();
    expect(screen.queryByRole('table')).toBeNull();
  });

  it('en un lote grande no marca nada por defecto, y explica por qué', async () => {
    // Treinta artefactos con texto: el material real del propietario tiene 1.090, y marcar todo por
    // defecto convertiría un clic en mil versiones candidatas que habría que aceptar una a una.
    const muchos: Representation[] = Array.from({ length: 30 }, (_valor, indice) => ({
      ...CON_TEXTO_1,
      id: `rep-masivo-${indice}`,
      artifact_id: `art-masivo-${indice}`,
      sources: [{ location: `pack/masivo/fichero-${indice}.pdf`, origin_type: 'file', depth: 0 }],
    }));
    stubApi({
      '/api/v1/ingestion-batches/batch-grande': {
        body: { ...detalle, batch: { ...lote, id: 'batch-grande' } },
      },
      '/api/v1/ingestion-batches/batch-grande/representations': { body: muchos },
    });
    renderWithProviders(
      <AppShell>
        <PromotePanel batchId="batch-grande" />
      </AppShell>,
      { route: '/bandeja' },
    );

    expect(await screen.findByText(/no hay nada marcado/)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Pasar a la biblioteca (0)' })).toBeDisabled();
    expect(screen.getByText(/30 artefactos/)).toBeInTheDocument();

    // Y se puede marcar en bloque, que es la decisión que la pantalla no toma sola.
    await userEvent.click(screen.getByRole('button', { name: 'Marcar los visibles (30)' }));
    expect(screen.getByRole('button', { name: 'Pasar a la biblioteca (30)' })).toBeEnabled();
  });
});

/** Comprobación de que el panel no promete nada que no haga: el texto del encabezado es honesto. */
describe('lo que el panel promete', () => {
  it('avisa de que las versiones nacen candidatas antes de pulsar nada', async () => {
    stubBandeja();
    await abrirLote();

    const seccion = screen.getByRole('heading', { name: 'Pasar a la biblioteca' }).closest('section');
    expect(
      within(seccion as HTMLElement).getByText(/todavía no\s+cuenta para estudiar/i),
    ).toBeInTheDocument();
  });
});
