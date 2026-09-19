import { fireEvent, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it } from 'vitest';

import type { Batch, BatchDetail, EntryPage, IssuePage } from '../../src/api/ingestion';
import { AppShell } from '../../src/app/AppShell';
import { TrayPage } from '../../src/pages/TrayPage';
import { renderWithProviders, stubApi, type StubbedRoute } from './testUtils';

/**
 * Las tres entradas directas de S03 (04_INGESTION §2), probadas desde la pantalla real: lo que se
 * comprueba es la petición que sale del navegador, no la forma interna del componente.
 */

const loteCreado: Batch = {
  id: 'batch-nuevo',
  kind: 'import',
  mode: 'copy',
  status: 'queued',
  source_path_display: 'texto pegado',
  counters: { total: 1, copied: 0, pending: 1 },
  created_at: '2026-07-01T10:00:00Z',
  formats: { '.txt': 1 },
  issue_counts: {},
  total_items: 1,
};

const detalleCreado: BatchDetail = {
  batch: loteCreado,
  entries: [],
  issues: [],
  report: {
    batch_id: loteCreado.id,
    kind: 'import',
    status: 'queued',
    counters: loteCreado.counters,
    issue_counts: {},
    balanced: true,
    artifacts_total: 1,
    generated_at: '2026-07-01T10:00:01Z',
  },
};

const entradasVacias: EntryPage = { entries: [], total: 0, limit: 200, offset: 0 };
const incidenciasVacias: IssuePage = { issues: [], total: 0, limit: 200, offset: 0 };

function stubIntakeApi(overrides: Record<string, StubbedRoute> = {}) {
  return stubApi({
    '/api/v1/ingestion-batches/files': { body: loteCreado },
    '/api/v1/ingestion-batches/paste': { body: loteCreado },
    '/api/v1/ingestion-batches/url': { body: loteCreado },
    '/api/v1/ingestion-batches/batch-nuevo/items': { body: entradasVacias },
    '/api/v1/ingestion-batches/batch-nuevo/issues': { body: incidenciasVacias },
    '/api/v1/ingestion-batches/batch-nuevo/representations': { body: [] },
    '/api/v1/ingestion-batches/batch-nuevo': { body: detalleCreado },
    '/api/v1/ingestion-batches': { body: [loteCreado] },
    ...overrides,
  });
}

function renderTray() {
  return renderWithProviders(
    <AppShell>
      <TrayPage />
    </AppShell>,
    { route: '/bandeja' },
  );
}

function cuerpoEnviado(fetchMock: ReturnType<typeof stubIntakeApi>, fragmento: string) {
  return fetchMock.mock.calls.find(
    (call) => typeof call[0] === 'string' && call[0].includes(fragmento),
  );
}

/** Cuerpo JSON de una petición, comprobando antes que es texto: nada de `String(objeto)`. */
function cuerpoJson(llamada: ReturnType<typeof cuerpoEnviado>): unknown {
  const body = llamada?.[1]?.body;
  if (typeof body !== 'string') {
    throw new Error('la petición no llevaba un cuerpo JSON');
  }
  return JSON.parse(body) as unknown;
}

describe('entradas directas de la Bandeja', () => {
  it('guarda el texto pegado como material propio, con su título', async () => {
    const fetchMock = stubIntakeApi();
    renderTray();

    const boton = await screen.findByRole('button', { name: 'Guardar el texto' });
    // Sin texto no hay nada que guardar: el botón no se ofrece en falso.
    expect(boton).toBeDisabled();

    // `paste` en lugar de `type`: escribir carácter a carácter en un textarea controlado que vuelve a
    // renderizar por cada pulsación es lento y, con el tiempo justo, se cuela un espacio entre letras
    // («Suelto.» llegaba como « S uelto.»). Pegar es lo que hace de verdad una persona aquí.
    await userEvent.click(screen.getByLabelText('Texto'));
    await userEvent.paste('Tema 1. La Constitución Española.');
    await userEvent.type(screen.getByLabelText(/Título/), '  Notas del tema 1  ');
    await userEvent.click(boton);

    await waitFor(() => {
      expect(cuerpoEnviado(fetchMock, '/ingestion-batches/paste')).toBeDefined();
    });
    const llamada = cuerpoEnviado(fetchMock, '/ingestion-batches/paste');
    expect(llamada?.[1]?.method).toBe('POST');
    expect(cuerpoJson(llamada)).toEqual({
      text: 'Tema 1. La Constitución Española.',
      title: 'Notas del tema 1',
    });
    // El lote creado se sigue en la propia pantalla, sin recargar nada a mano.
    expect(await screen.findByRole('heading', { name: 'Importación' })).toBeInTheDocument();
  });

  it('pega texto sin título sin inventarse uno', async () => {
    const fetchMock = stubIntakeApi();
    renderTray();

    await userEvent.click(await screen.findByLabelText('Texto'));
    await userEvent.paste('Suelto.');
    await userEvent.click(screen.getByRole('button', { name: 'Guardar el texto' }));

    await waitFor(() => {
      expect(cuerpoEnviado(fetchMock, '/ingestion-batches/paste')).toBeDefined();
    });
    const llamada = cuerpoEnviado(fetchMock, '/ingestion-batches/paste');
    // Sin título el campo no viaja: el servidor decide el nombre, no el navegador.
    expect(cuerpoJson(llamada)).toEqual({ text: 'Suelto.' });
  });

  it('copia los ficheros elegidos como formulario, sin fijar el tipo de contenido', async () => {
    const fetchMock = stubIntakeApi();
    renderTray();

    const fichero = new File(['Tema 1'], 'tema-01.txt', { type: 'text/plain' });
    await userEvent.upload(await screen.findByLabelText(/Suelta aquí o elige ficheros/), fichero);

    await waitFor(() => {
      expect(cuerpoEnviado(fetchMock, '/ingestion-batches/files')).toBeDefined();
    });
    const llamada = cuerpoEnviado(fetchMock, '/ingestion-batches/files');
    expect(llamada?.[1]?.method).toBe('POST');
    const enviado = llamada?.[1]?.body;
    expect(enviado).toBeInstanceOf(FormData);
    const partes = (enviado as FormData).getAll('files');
    expect(partes).toHaveLength(1);
    expect((partes[0] as File).name).toBe('tema-01.txt');
    // El navegador pone el separador del multipart; fijarlo a mano lo rompería.
    expect(llamada?.[1]?.headers).not.toHaveProperty('Content-Type');
  });

  it('acepta ficheros soltados sobre la zona de arrastre', async () => {
    const fetchMock = stubIntakeApi();
    renderTray();

    const zona = (await screen.findByLabelText(/Suelta aquí o elige ficheros/)).closest(
      '.intake__drop',
    );
    expect(zona).not.toBeNull();
    fireEvent.drop(zona as Element, {
      dataTransfer: { files: [new File(['x'], 'soltado.txt', { type: 'text/plain' })] },
    });

    await waitFor(() => {
      expect(cuerpoEnviado(fetchMock, '/ingestion-batches/files')).toBeDefined();
    });
    const enviado = cuerpoEnviado(fetchMock, '/ingestion-batches/files')?.[1]?.body;
    const partes = (enviado as FormData).getAll('files');
    expect((partes[0] as File).name).toBe('soltado.txt');
  });

  it('trae una URL pública por el servidor, que es quien comprueba la red', async () => {
    const fetchMock = stubIntakeApi();
    renderTray();

    const direccion = 'https://www.boe.es/diario_boe/txt.php?id=BOE-A-2025-26262';
    await userEvent.type(await screen.findByLabelText('Dirección'), direccion);
    await userEvent.click(screen.getByRole('button', { name: 'Descargar y copiar' }));

    await waitFor(() => {
      expect(cuerpoEnviado(fetchMock, '/ingestion-batches/url')).toBeDefined();
    });
    const llamada = cuerpoEnviado(fetchMock, '/ingestion-batches/url');
    expect(llamada?.[1]?.method).toBe('POST');
    expect(cuerpoJson(llamada)).toEqual({ url: direccion });
  });

  it('cuenta el motivo real cuando el servidor rechaza la dirección, sin fingir la copia', async () => {
    stubIntakeApi({
      '/api/v1/ingestion-batches/url': {
        status: 400,
        contentType: 'application/problem+json',
        body: {
          type: 'about:blank',
          title: 'Bad Request',
          status: 400,
          detail: 'La dirección apunta a una red interna (loopback): no se descarga.',
          code: 'url_rejected',
          correlation_id: 'corr-de-prueba',
        },
      },
    });
    renderTray();

    await userEvent.type(await screen.findByLabelText('Dirección'), 'http://127.0.0.1:8765/x');
    await userEvent.click(screen.getByRole('button', { name: 'Descargar y copiar' }));

    expect(await screen.findByText('No se pudo descargar')).toBeInTheDocument();
    expect(screen.getByText(/red interna \(loopback\)/)).toBeInTheDocument();
    expect(screen.queryByRole('heading', { name: 'Importación' })).not.toBeInTheDocument();
  });
});
