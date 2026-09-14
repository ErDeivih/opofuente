import { screen, waitFor, within } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { NAV_ITEMS } from '../../src/app/navigation';
import { AppShell } from '../../src/app/AppShell';
import { AppRoutes } from '../../src/app/routes';
import { NotFoundPage } from '../../src/pages/NotFoundPage';
import { HomePage } from '../../src/pages/HomePage';
import {
  capabilitiesFixture,
  readinessReady,
  renderWithProviders,
  settingsFixture,
  stubApi,
} from './testUtils';

function stubSystemApi() {
  return stubApi({
    '/api/v1/health/ready': { body: readinessReady },
    '/api/v1/capabilities': { body: capabilitiesFixture },
    '/api/v1/settings': { body: settingsFixture },
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

  it('solo Inicio está implementada en S00', () => {
    const implementadas = NAV_ITEMS.filter((item) => item.slice === null).map((item) => item.label);
    expect(implementadas).toEqual(['Inicio']);
  });

  it('las secciones no implementadas declaran su slice', () => {
    const slices = new Map(NAV_ITEMS.map((item) => [item.label, item.slice]));
    expect(slices.get('Bandeja')).toBe('S02');
    expect(slices.get('Programa')).toBe('S01');
    expect(slices.get('Biblioteca')).toBe('S05');
    expect(slices.get('Estudiar')).toBe('S07');
  });
});

describe('shell de la aplicación', () => {
  it('anuncia la sección pendiente en lugar de mostrar una pantalla vacía', async () => {
    stubSystemApi();
    renderWithProviders(
      <AppShell>
        <AppRoutes />
      </AppShell>,
      { route: '/biblioteca' },
    );

    expect(await screen.findByRole('heading', { level: 1, name: 'Biblioteca' })).toBeInTheDocument();
    expect(screen.getByText(/slice S05/)).toBeInTheDocument();
    expect(screen.getByText('pendiente')).toBeInTheDocument();
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
      await screen.findByText('Cola de trabajos local: todavía no implementado (previsto en S02).'),
    ).toBeInTheDocument();
    // La tabla de capacidades declara el estado real: nada se muestra como operativo por error.
    const tabla = screen.getByRole('table', { name: 'Capacidades de esta instalación' });
    expect(within(tabla).getAllByText('pendiente', { selector: '.badge__text' })).toHaveLength(2);
    expect(within(tabla).getAllByText('desactivado', { selector: '.badge__text' })).toHaveLength(2);
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
