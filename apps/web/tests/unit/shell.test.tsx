import { screen, waitFor, within } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { NAV_ITEMS } from '../../src/app/navigation';
import { AppShell } from '../../src/app/AppShell';
import { AppRoutes } from '../../src/app/routes';
import { NotFoundPage } from '../../src/pages/NotFoundPage';
import { HomePage } from '../../src/pages/HomePage';
import {
  capabilitiesFixture,
  oppositionsFixture,
  readinessReady,
  renderWithProviders,
  settingsFixture,
  stubApi,
  type StubbedRoute,
} from './testUtils';

function stubSystemApi(extra: Record<string, StubbedRoute> = {}) {
  return stubApi({
    '/api/v1/health/ready': { body: readinessReady },
    '/api/v1/capabilities': { body: capabilitiesFixture },
    '/api/v1/settings': { body: settingsFixture },
    '/api/v1/oppositions': { body: oppositionsFixture },
    ...extra,
  });
}

function stubAdjustesApi(extra: Record<string, StubbedRoute> = {}) {
  // Ajustes consulta cinco rutas propias: sin ellas las secciones quedan cargando y la pantalla no
  // llega a declararse construida.
  return stubSystemApi({
    '/api/v1/backups': { body: { backups: [] } },
    '/api/v1/housekeeping': {
      body: {
        usage: [],
        candidates: [],
        retention_days: 30,
        total_bytes: 0,
        reclaimable_bytes: 0,
      },
    },
    '/api/v1/search/index': { body: { healthy: true, detail: 'completo', missing_entries: 0 } },
    '/api/v1/diagnostics': {
      body: {
        generated_at: '2026-09-19T12:00:00+00:00',
        version: '0.0.0-test',
        schema_revision: '0020_changes_and_derivatives',
        python_version: '3.12.0',
        platform: 'Windows 11 (python 64 bits)',
        host: '127.0.0.1',
        port: 8765,
        log_level: 'INFO',
        data_dir_display: '…/datos',
        database_file_display: '…/datos/opofuente.sqlite3',
        disk_total_bytes: 1,
        disk_free_bytes: 1,
        counts: {},
        capabilities: capabilitiesFixture.capabilities,
        degradations: [],
        checks: readinessReady.checks,
        limits: settingsFixture.limits,
        log_tail: [],
        note: 'Diagnóstico sanitizado',
      },
    },
    ...extra,
  });
}

describe('navegación', () => {
  it('contiene las secciones del MVP en orden', () => {
    expect(NAV_ITEMS.map((item) => item.label)).toEqual([
      'Inicio',
      'Bandeja',
      'Programa',
      'Biblioteca',
      'Preguntas',
      'Estudiar',
      'Errores',
      'Cambios',
      'Ajustes',
    ]);
  });

  it('las secciones construidas están implementadas y las demás declaran su slice', () => {
    const implementadas = NAV_ITEMS.filter((item) => item.slice === null).map((item) => item.label);
    expect(implementadas).toEqual([
      'Inicio',
      'Bandeja',
      'Programa',
      'Biblioteca',
      'Preguntas',
      'Estudiar',
      'Errores',
      'Cambios',
      'Ajustes',
    ]);
    // Ninguna sección queda pendiente: el MVP está completo (S00–S12).
    expect(NAV_ITEMS.filter((item) => item.slice !== null)).toEqual([]);
  });
});

describe('shell de la aplicación', () => {
  it('Ajustes ya está construida: su ruta no anuncia un slice pendiente', async () => {
    stubAdjustesApi();
    renderWithProviders(
      <AppShell>
        <AppRoutes />
      </AppShell>,
      { route: '/ajustes' },
    );

    expect(await screen.findByRole('heading', { level: 1, name: 'Ajustes' })).toBeInTheDocument();
    expect(screen.queryByText(/slice S12/)).toBeNull();
    expect(screen.queryByText('pendiente')).toBeNull();
  });

  it('Cambios ya está construida: su ruta no anuncia un slice pendiente', async () => {
    stubSystemApi({
      '/api/v1/change-sets?limit=100': { body: [] },
      '/api/v1/derived-artifacts?needs_review=true': { body: [] },
    });
    renderWithProviders(
      <AppShell>
        <AppRoutes />
      </AppShell>,
      { route: '/cambios' },
    );

    expect(await screen.findByRole('heading', { level: 1, name: 'Cambios' })).toBeInTheDocument();
    expect(screen.queryByText(/slice S11/)).toBeNull();
    expect(screen.queryByText('pendiente')).toBeNull();
  });

  it('Errores ya está construida: su ruta no anuncia un slice pendiente', async () => {
    stubSystemApi({
      '/api/v1/reviews/due?opposition_id=opp-tai': {
        body: {
          items: [],
          stats: { active: 0, due: 0, next_due_at: null, lapses: 0 },
          concepts: [],
          notes: ['No hay nada vencido.'],
        },
      },
      '/api/v1/learning-errors?opposition_id=opp-tai': {
        body: { groups: [], total_errors: 0, open_errors: 0 },
      },
    });
    renderWithProviders(
      <AppShell>
        <AppRoutes />
      </AppShell>,
      { route: '/errores' },
    );

    expect(await screen.findByRole('heading', { level: 1, name: 'Errores' })).toBeInTheDocument();
    expect(screen.queryByText(/slice S10/)).toBeNull();
    expect(screen.queryByText('pendiente')).toBeNull();
  });

  it('Estudiar ya está construida: su ruta no anuncia un slice pendiente', async () => {
    stubSystemApi({
      '/api/v1/study-sessions?limit=50&offset=0&opposition_id=opp-tai': {
        body: { sessions: [], total: 0, limit: 50, offset: 0 },
      },
      '/api/v1/question-sets?limit=100&offset=0&opposition_id=opp-tai': {
        body: { sets: [], total: 0, limit: 100, offset: 0 },
      },
    });
    renderWithProviders(
      <AppShell>
        <AppRoutes />
      </AppShell>,
      { route: '/estudiar' },
    );

    expect(await screen.findByRole('heading', { level: 1, name: 'Estudiar' })).toBeInTheDocument();
    expect(screen.queryByText(/slice S07/)).toBeNull();
    expect(screen.queryByText('pendiente')).toBeNull();
  });

  it('la Biblioteca ya está construida: su ruta no anuncia un slice pendiente', async () => {
    stubSystemApi({
      '/api/v1/documents?limit=50&offset=0': {
        body: { documents: [], total: 0, limit: 50, offset: 0 },
      },
    });
    renderWithProviders(
      <AppShell>
        <AppRoutes />
      </AppShell>,
      { route: '/biblioteca' },
    );

    expect(
      await screen.findByRole('heading', { level: 1, name: 'Biblioteca' }),
    ).toBeInTheDocument();
    expect(screen.queryByText(/slice S05/)).toBeNull();
    expect(screen.queryByText('pendiente')).toBeNull();
  });

  it('muestra el estado real del sistema en Inicio', async () => {
    stubSystemApi();
    renderWithProviders(
      <AppShell>
        <HomePage />
      </AppShell>,
      { route: '/' },
    );

    await waitFor(() => {
      expect(screen.getByText('listo para trabajar')).toBeInTheDocument();
    });
    expect(screen.getByText(/sqlite ok/)).toBeInTheDocument();
    expect(screen.getByText('directorio de datos escribible')).toBeInTheDocument();
    expect(screen.getByText(settingsFixture.data_dir)).toBeInTheDocument();
  });

  it('declara las degradaciones en lugar de esconderlas', async () => {
    stubSystemApi();
    renderWithProviders(
      <AppShell>
        <HomePage />
      </AppShell>,
      { route: '/' },
    );

    expect(
      await screen.findByText(
        /Índice vectorial local: no disponible\. Sin proveedor de embeddings no hay vectores/,
      ),
    ).toBeInTheDocument();
    // La tabla de capacidades declara el estado real: nada se muestra como operativo por error.
    const tabla = screen.getByRole('table', { name: 'Capacidades de esta instalación' });
    expect(within(tabla).getAllByText('operativo', { selector: '.badge__text' })).toHaveLength(3);
    expect(within(tabla).getAllByText('no disponible', { selector: '.badge__text' })).toHaveLength(1);
    expect(within(tabla).getAllByText('desactivado', { selector: '.badge__text' })).toHaveLength(3);
    // El indicador de cabecera resume el estado del worker.
    expect(screen.getByLabelText('Estado de capacidades clave')).toBeInTheDocument();
  });

  it('el enlace de salto al contenido existe y apunta al main', () => {
    stubSystemApi();
    renderWithProviders(
      <AppShell>
        <HomePage />
      </AppShell>,
      { route: '/' },
    );

    const skipLink = screen.getByRole('link', { name: 'Saltar al contenido' });
    expect(skipLink).toHaveAttribute('href', '#contenido');
    expect(document.getElementById('contenido')).not.toBeNull();
  });

  it('una ruta desconocida muestra un aviso claro', () => {
    renderWithProviders(<NotFoundPage />, { route: '/no-existe' });
    expect(screen.getByRole('heading', { level: 1, name: 'Página no encontrada' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Volver a Inicio' })).toBeInTheDocument();
  });
});
