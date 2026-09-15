import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it } from 'vitest';

import type {
  Batch,
  BatchDetail,
  EntryPage,
  Inventory,
  IssuePage,
  Job,
} from '../../src/api/ingestion';
import { AppShell } from '../../src/app/AppShell';
import { TrayPage } from '../../src/pages/TrayPage';
import { renderWithProviders, stubApi, type StubbedRoute } from './testUtils';

const ORIGEN = 'F:\\material-para-probar';

const inventario: Batch = {
  id: 'batch-inventario',
  kind: 'inventory',
  mode: 'read_only',
  status: 'succeeded',
  source_path_display: '…\\material-para-probar',
  counters: {
    inventoried: 3,
    total_bytes: 6144,
    directories: 2,
    omitted_hidden: 1,
    linked_outside_root: 1,
  },
  created_at: '2026-07-01T09:00:00Z',
  started_at: '2026-07-01T09:00:00Z',
  finished_at: '2026-07-01T09:00:02Z',
  formats: { '.pdf': 2, '.txt': 1 },
  issue_counts: { linked_outside_root: 1 },
  total_items: 3,
};

const inventoryResponse: Inventory = {
  batch: inventario,
  sample: [
    {
      id: 'item-1',
      relative_path: 'tema-01.pdf',
      original_name: 'tema-01.pdf',
      size_bytes: 4096,
      media_type: 'application/pdf',
      status: 'inventoried',
      detail: null,
      artifact_sha256: null,
    },
    {
      id: 'item-2',
      relative_path: 'tema-02.txt',
      original_name: 'tema-02.txt',
      size_bytes: 2048,
      media_type: 'text/plain',
      status: 'inventoried',
      detail: null,
      artifact_sha256: null,
    },
  ],
  issues: [
    {
      code: 'linked_outside_root',
      severity: 'warning',
      safe_message: 'Enlace que apunta fuera de la carpeta: no se sigue.',
      relative_path: 'acceso-directo.lnk',
      details: {},
    },
    {
      code: 'omitted_hidden',
      severity: 'info',
      safe_message: 'Fichero oculto: no se copia.',
      relative_path: '.oculto.txt',
      details: {},
    },
  ],
  copied_anything: false,
  note: 'OpoFuente ha leído la carpeta sin modificarla. No se ha copiado ni movido nada todavía.',
};

const loteImportado: Batch = {
  id: 'batch-importacion',
  kind: 'import',
  mode: 'copy',
  status: 'running',
  source_path_display: '…\\material-para-probar',
  counters: { total: 3, copied: 2, copied_bytes: 8192, pending: 1 },
  created_at: '2026-07-01T09:10:00Z',
  started_at: '2026-07-01T09:10:01Z',
  job_id: 'job-import',
  inventory_batch_id: inventario.id,
  manifest_hash: 'a'.repeat(64),
  formats: { '.pdf': 2, '.txt': 1 },
  issue_counts: {},
  total_items: 3,
};

const detalleDelLote: BatchDetail = {
  batch: loteImportado,
  entries: [],
  issues: [],
  report: {
    batch_id: loteImportado.id,
    kind: 'import',
    status: 'running',
    counters: loteImportado.counters,
    issue_counts: {},
    balanced: true,
    artifacts_total: 2,
    generated_at: '2026-07-01T09:10:05Z',
  },
};

const trabajoEnCurso: Job = {
  id: 'job-import',
  job_type: 'ingest_batch',
  status: 'running',
  progress: 0.5,
  attempts: 1,
  max_attempts: 3,
  created_at: '2026-07-01T09:10:00Z',
  updated_at: '2026-07-01T09:10:05Z',
  step: 'copiando tema-01.pdf',
  error_code: null,
  error_message: null,
  started_at: '2026-07-01T09:10:01Z',
  finished_at: null,
  cancel_requested: false,
};

const entradasDelLote: EntryPage = {
  entries: [
    {
      id: 'item-1',
      relative_path: 'tema-01.pdf',
      original_name: 'tema-01.pdf',
      size_bytes: 4096,
      media_type: 'application/pdf',
      status: 'hashed',
      detail: null,
      artifact_sha256: 'b'.repeat(64),
    },
    {
      id: 'item-2',
      relative_path: 'tema-02.txt',
      original_name: 'tema-02.txt',
      size_bytes: 2048,
      media_type: 'text/plain',
      status: 'copied',
      detail: null,
      artifact_sha256: null,
    },
  ],
  total: 2,
  limit: 200,
  offset: 0,
};

const incidenciasDelLote: IssuePage = {
  issues: [
    {
      code: 'source_changed',
      severity: 'warning',
      safe_message: 'El fichero cambió entre el inventario y la copia: se copió lo que había.',
      relative_path: 'tema-02.txt',
      details: {},
    },
  ],
  total: 1,
  limit: 200,
  offset: 0,
};

function stubTrayApi(overrides: Record<string, StubbedRoute> = {}) {
  return stubApi({
    '/api/v1/ingestion-batches/batch-importacion/items': { body: entradasDelLote },
    '/api/v1/ingestion-batches/batch-importacion/issues': { body: incidenciasDelLote },
    '/api/v1/ingestion-batches/batch-importacion': { body: detalleDelLote },
    '/api/v1/ingestion-batches': { body: [loteImportado] },
    '/api/v1/jobs/job-import': { body: trabajoEnCurso },
    '/api/v1/inventories/batch-inventario/confirm-import': { body: loteImportado },
    '/api/v1/inventories': { body: inventoryResponse },
    ...overrides,
  });
}

async function inventariar() {
  await userEvent.type(screen.getByLabelText(/Carpeta a inventariar/), ORIGEN);
  await userEvent.click(screen.getByRole('button', { name: 'Inventariar (solo lectura)' }));
}

describe('pantalla Bandeja', () => {
  it('inventaría una carpeta con una petición de solo lectura y sin copiar nada', async () => {
    const fetchMock = stubTrayApi();
    renderWithProviders(
      <AppShell>
        <TrayPage />
      </AppShell>,
      { route: '/bandeja' },
    );

    await inventariar();

    expect(await screen.findByRole('heading', { name: 'Vista previa del inventario' })).toBeInTheDocument();
    const llamada = fetchMock.mock.calls.find(
      (call) => typeof call[0] === 'string' && call[0].endsWith('/inventories'),
    );
    expect(llamada?.[1]?.method).toBe('POST');
    const cuerpo = llamada?.[1]?.body;
    const enviado: unknown = JSON.parse(typeof cuerpo === 'string' ? cuerpo : 'null');
    expect(enviado).toEqual({ source_path: ORIGEN });
    // La pantalla dice explícitamente que no se ha copiado nada todavía.
    expect(screen.getByText(/No se ha copiado ni movido nada todavía/)).toBeInTheDocument();
  });

  it('resume la vista previa: recuento, tamaño, formatos y muestra', async () => {
    stubTrayApi();
    renderWithProviders(
      <AppShell>
        <TrayPage />
      </AppShell>,
      { route: '/bandeja' },
    );

    await inventariar();

    const previa = await screen.findByRole('region', { name: 'Vista previa del inventario' });
    expect(within(previa).getByText('3')).toBeInTheDocument();
    expect(within(previa).getByText('6.0 KB')).toBeInTheDocument();
    expect(within(previa).getByText('.pdf ×2, .txt ×1')).toBeInTheDocument();
    expect(within(previa).getByText('tema-01.pdf')).toBeInTheDocument();
    // La ruta mostrada es la abreviada, nunca la ruta absoluta del equipo.
    expect(within(previa).getByText('…\\material-para-probar')).toBeInTheDocument();
    expect(screen.queryByText(ORIGEN)).not.toBeInTheDocument();
  });

  it('declara lo que se omite y por qué, en lugar de callarlo', async () => {
    stubTrayApi();
    renderWithProviders(
      <AppShell>
        <TrayPage />
      </AppShell>,
      { route: '/bandeja' },
    );

    await inventariar();

    const previa = await screen.findByRole('region', { name: 'Vista previa del inventario' });
    expect(within(previa).getByText('linked_outside_root')).toBeInTheDocument();
    expect(within(previa).getByText('omitted_hidden')).toBeInTheDocument();
    expect(within(previa).getByText('.oculto.txt')).toBeInTheDocument();
  });

  it('no importa hasta que el usuario confirma, y entonces muestra el progreso y el informe', async () => {
    const fetchMock = stubTrayApi();
    renderWithProviders(
      <AppShell>
        <TrayPage />
      </AppShell>,
      { route: '/bandeja' },
    );

    await inventariar();
    await screen.findByRole('heading', { name: 'Vista previa del inventario' });

    // Antes de confirmar no existe ninguna petición de copia.
    expect(
      fetchMock.mock.calls.some(
        (call) => typeof call[0] === 'string' && call[0].includes('confirm-import'),
      ),
    ).toBe(false);

    await userEvent.click(screen.getByRole('button', { name: 'Importar una copia' }));

    expect(await screen.findByRole('heading', { name: 'Importación' })).toBeInTheDocument();
    const confirmacion = fetchMock.mock.calls.find(
      (call) => typeof call[0] === 'string' && call[0].includes('confirm-import'),
    );
    expect(confirmacion?.[1]?.method).toBe('POST');
    // Progreso real del trabajo, no una barra decorativa.
    expect(await screen.findByText(/50 % · copiando tema-01\.pdf/)).toBeInTheDocument();
    expect(screen.getByText('2 de 3')).toBeInTheDocument();
    expect(screen.getByText('El trabajo se ejecuta en el servidor local: cerrar esta pestaña no lo cancela.')).toBeInTheDocument();
  });

  it('lista las entradas y las incidencias del lote', async () => {
    stubTrayApi();
    renderWithProviders(
      <AppShell>
        <TrayPage />
      </AppShell>,
      { route: '/bandeja' },
    );

    await inventariar();
    await screen.findByRole('heading', { name: 'Vista previa del inventario' });
    await userEvent.click(screen.getByRole('button', { name: 'Importar una copia' }));

    const tabla = await screen.findByRole('table', { name: /entradas/ });
    expect(within(tabla).getByText('tema-02.txt')).toBeInTheDocument();
    expect(within(tabla).getByText('hashed')).toBeInTheDocument();

    const incidencias = await screen.findByRole('region', { name: 'Incidencias del lote' });
    expect(within(incidencias).getByText('source_changed')).toBeInTheDocument();
  });

  it('ofrece cancelar mientras el lote trabaja', async () => {
    const fetchMock = stubTrayApi({
      '/api/v1/ingestion-batches/batch-importacion/cancel': {
        body: { ...loteImportado, status: 'cancel_requested' },
      },
    });
    renderWithProviders(
      <AppShell>
        <TrayPage />
      </AppShell>,
      { route: '/bandeja' },
    );

    await inventariar();
    await screen.findByRole('heading', { name: 'Vista previa del inventario' });
    await userEvent.click(screen.getByRole('button', { name: 'Importar una copia' }));

    const importacion = await screen.findByRole('region', { name: 'Importación' });
    await userEvent.click(within(importacion).getByRole('button', { name: 'Cancelar' }));

    await waitFor(() => {
      expect(
        fetchMock.mock.calls.some(
          (call) =>
            typeof call[0] === 'string' &&
            call[0].includes('batch-importacion/cancel') &&
            call[1]?.method === 'POST',
        ),
      ).toBe(true);
    });
  });

  it('declara las formas de entrada que todavía no existen en lugar de mostrar botones falsos', async () => {
    stubTrayApi();
    renderWithProviders(
      <AppShell>
        <TrayPage />
      </AppShell>,
      { route: '/bandeja' },
    );

    expect(
      await screen.findByText(/soltar archivos y pegar texto o URL \(slice S03\)/),
    ).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /soltar|pegar/i })).not.toBeInTheDocument();
  });

  it('muestra las entradas pendientes del informe', async () => {
    stubTrayApi();
    renderWithProviders(
      <AppShell>
        <TrayPage />
      </AppShell>,
      { route: '/bandeja' },
    );

    await inventariar();
    await screen.findByRole('heading', { name: 'Vista previa del inventario' });
    await userEvent.click(screen.getByRole('button', { name: 'Importar una copia' }));

    const importacion = await screen.findByRole('region', { name: 'Importación' });
    // `Pendientes` es el valor del término de la lista de datos que va justo después.
    const pendientes = within(importacion).getByText('Pendientes').nextElementSibling;
    expect(pendientes).toHaveTextContent('1');
  });

  it('solo ofrece reintentar lo que está parado y a medias', async () => {
    stubTrayApi({
      '/api/v1/ingestion-batches/batch-importacion': {
        body: { ...detalleDelLote, batch: { ...loteImportado, status: 'cancelled' } },
      },
    });
    renderWithProviders(
      <AppShell>
        <TrayPage />
      </AppShell>,
      { route: '/bandeja' },
    );

    await inventariar();
    await screen.findByRole('heading', { name: 'Vista previa del inventario' });
    await userEvent.click(screen.getByRole('button', { name: 'Importar una copia' }));

    const importacion = await screen.findByRole('region', { name: 'Importación' });
    await waitFor(() => {
      expect(within(importacion).getByRole('button', { name: 'Reintentar' })).toBeInTheDocument();
    });
    // Un lote en marcha no se reintenta: la API responde 409 y el botón no se muestra.
    expect(within(importacion).queryByRole('button', { name: 'Cancelar' })).not.toBeInTheDocument();
  });

  it('no ofrece reintentar un lote terminado', async () => {
    stubTrayApi({
      '/api/v1/ingestion-batches/batch-importacion': {
        body: { ...detalleDelLote, batch: { ...loteImportado, status: 'succeeded' } },
      },
    });
    renderWithProviders(
      <AppShell>
        <TrayPage />
      </AppShell>,
      { route: '/bandeja' },
    );

    await inventariar();
    await screen.findByRole('heading', { name: 'Vista previa del inventario' });
    await userEvent.click(screen.getByRole('button', { name: 'Importar una copia' }));

    const importacion = await screen.findByRole('region', { name: 'Importación' });
    await waitFor(() => {
      expect(within(importacion).getByText('succeeded')).toBeInTheDocument();
    });
    expect(within(importacion).queryByRole('button', { name: 'Reintentar' })).not.toBeInTheDocument();
  });

  it('explica el 409 si el lote cambia de estado mientras se mira', async () => {
    // El lote se ve cancelado (y por tanto reintentable), pero cuando llega la petición ya no lo
    // está: la API responde 409 y la pantalla lo cuenta en lugar de fingir que se reintentó.
    stubTrayApi({
      '/api/v1/ingestion-batches/batch-importacion': {
        body: { ...detalleDelLote, batch: { ...loteImportado, status: 'cancelled' } },
      },
      '/api/v1/ingestion-batches/batch-importacion/retry': {
        status: 409,
        contentType: 'application/problem+json',
        body: {
          type: 'about:blank',
          title: 'Conflict',
          status: 409,
          detail: 'el lote está en estado «running»: solo se puede reintentar si está failed o cancelled',
          code: 'invalid_state',
          correlation_id: 'corr-de-prueba',
        },
      },
    });
    renderWithProviders(
      <AppShell>
        <TrayPage />
      </AppShell>,
      { route: '/bandeja' },
    );

    await inventariar();
    await screen.findByRole('heading', { name: 'Vista previa del inventario' });
    await userEvent.click(screen.getByRole('button', { name: 'Importar una copia' }));

    const importacion = await screen.findByRole('region', { name: 'Importación' });
    await userEvent.click(within(importacion).getByRole('button', { name: 'Reintentar' }));

    expect(await screen.findByText('No se pudo cambiar el estado del lote')).toBeInTheDocument();
    expect(screen.getByText(/solo se puede reintentar si está failed o cancelled/)).toBeInTheDocument();
  });

  it('avisa de que un fichero que cambió necesita un inventario nuevo', async () => {
    stubTrayApi({
      '/api/v1/ingestion-batches/batch-importacion': {
        body: {
          ...detalleDelLote,
          batch: {
            ...loteImportado,
            status: 'succeeded',
            counters: { total: 3, copied: 2, source_changed: 1, pending: 0 },
          },
        },
      },
    });
    renderWithProviders(
      <AppShell>
        <TrayPage />
      </AppShell>,
      { route: '/bandeja' },
    );

    await inventariar();
    await screen.findByRole('heading', { name: 'Vista previa del inventario' });
    await userEvent.click(screen.getByRole('button', { name: 'Importar una copia' }));

    expect(
      await screen.findByText(/cambiaron desde el inventario: no se copian ni se reintentan/),
    ).toBeInTheDocument();
  });

  it('explica el error de la API sin inventar un resultado correcto', async () => {
    stubTrayApi({
      '/api/v1/inventories': {
        status: 400,
        body: {
          type: 'about:blank',
          title: 'Bad Request',
          status: 400,
          detail: 'La carpeta no existe o no es accesible.',
          code: 'invalid_source',
          correlation_id: 'corr-de-prueba',
        },
      },
    });
    renderWithProviders(
      <AppShell>
        <TrayPage />
      </AppShell>,
      { route: '/bandeja' },
    );

    await inventariar();

    expect(await screen.findByText('No se pudo inventariar esa carpeta')).toBeInTheDocument();
    expect(screen.queryByRole('heading', { name: 'Vista previa del inventario' })).not.toBeInTheDocument();
  });
});
