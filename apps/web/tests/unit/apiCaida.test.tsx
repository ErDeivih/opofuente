import { QueryClientProvider } from '@tanstack/react-query';
import { render, screen, waitFor, within } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { createQueryClient } from '../../src/app/queryClient';
import { resetApiAvailability } from '../../src/app/apiAvailability';
import { AppShell } from '../../src/app/AppShell';
import { StudentHomePage } from '../../src/pages/student/StudentHomePage';

/**
 * Qué se ve cuando la API no está (5 de octubre de 2026).
 *
 * Antes, con la API parada, cada tarjeta de cada pantalla decía «Failed to fetch» en inglés con su
 * botón de reintentar: ocho avisos iguales y ninguno decía qué hacer. Ahora el fallo de red se
 * reconoce como tal (no es un problema de la API con su cuerpo RFC 9457) y la aplicación enseña
 * **un solo** aviso, con cómo arrancarla.
 */
describe('la API caída', () => {
  beforeEach(() => {
    resetApiAvailability();
    vi.stubGlobal(
      'fetch',
      vi.fn(() => Promise.reject(new TypeError('Failed to fetch'))),
    );
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('enseña un aviso único que dice cómo arrancar la aplicación', async () => {
    // El aviso lo dispara la primera consulta que falla, así que la prueba monta una pantalla que lee
    // de la API: Inicio del alumno, que desde F13 lee `/student/overview`.
    render(
      <QueryClientProvider client={createQueryClient()}>
        <MemoryRouter>
          <AppShell>
            <StudentHomePage />
          </AppShell>
        </MemoryRouter>
      </QueryClientProvider>,
    );

    await waitFor(
      () => {
        expect(screen.getByTestId('aviso-api-caida')).toBeInTheDocument();
      },
      { timeout: 5_000 },
    );
    expect(screen.getAllByTestId('aviso-api-caida')).toHaveLength(1);
    const aviso = screen.getByTestId('aviso-api-caida');
    expect(within(aviso).getByText(/La aplicación no responde/i)).toBeInTheDocument();
    expect(within(aviso).getByText(/scripts\\api\.ps1/)).toBeInTheDocument();
    // El aviso trae **su** botón de reintentar (la pantalla, además, conserva el suyo).
    expect(within(aviso).getByRole('button', { name: 'Reintentar' })).toBeInTheDocument();
    // El contenido de la pantalla sigue ahí, con lo suyo: el aviso informa, no sustituye a la app.
    expect(await screen.findByText('No se pudo cargar tu Inicio')).toBeInTheDocument();
  });

  it('con la API levantada no hay ningún aviso', () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(() =>
        Promise.resolve(
          new Response(JSON.stringify({ opposition_id: 'x', ready: true }), {
            status: 200,
            headers: { 'content-type': 'application/json' },
          }),
        ),
      ),
    );
    render(
      <QueryClientProvider client={createQueryClient()}>
        <MemoryRouter>
          <AppShell>
            <p>Contenido de la pantalla</p>
          </AppShell>
        </MemoryRouter>
      </QueryClientProvider>,
    );

    expect(screen.queryByTestId('aviso-api-caida')).not.toBeInTheDocument();
  });
});
