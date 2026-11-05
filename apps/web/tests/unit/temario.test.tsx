import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Route, Routes } from 'react-router-dom';
import { describe, expect, it } from 'vitest';

import { TemarioNodePage } from '../../src/pages/TemarioNodePage';
import { TemarioPage } from '../../src/pages/TemarioPage';
import {
  TEMARIO_CODE,
  TAI_CONVOCATION_ID,
  temarioDetailFixture,
  temarioNodeFixture,
  temarioProgressFixture,
  temarioSummaryFixture,
  renderWithProviders,
  stubApi,
  type StubbedRoute,
} from './testUtils';

/** Respuestas del temario común: la lista, el árbol y el avance que su pantalla enseña. */
function stubTemarioApi(extra: Record<string, StubbedRoute> = {}) {
  return stubApi({
    [`/api/v1/curricula/${TEMARIO_CODE}/progress`]: { body: temarioProgressFixture },
    [`/api/v1/curricula/${TEMARIO_CODE}`]: { body: temarioDetailFixture },
    '/api/v1/curricula': { body: [temarioSummaryFixture] },
    ...extra,
  });
}

function stubFichaApi(extra: Record<string, StubbedRoute> = {}) {
  return stubApi({
    [`/api/v1/curricula/${TEMARIO_CODE}`]: { body: temarioDetailFixture },
    '/api/v1/curriculum-nodes/tema-1/studied': {
      body: { node_id: 'tema-1', studied_at: '2026-11-05T09:00:00Z' },
    },
    '/api/v1/curriculum-nodes/tema-1': { body: temarioNodeFixture },
    ...extra,
  });
}

function renderFicha(route: string) {
  return renderWithProviders(
    <Routes>
      <Route path="/temario/:nodeId" element={<TemarioNodePage />} />
    </Routes>,
    { route },
  );
}

describe('pantalla Temario', () => {
  it('muestra el árbol con 5 bloques y los 40 temas en orden oficial', async () => {
    stubTemarioApi();
    renderWithProviders(<TemarioPage />, { route: '/temario' });

    expect(await screen.findByRole('heading', { level: 1, name: 'Temario' })).toBeInTheDocument();
    // Los cinco bloques, con su título, se pueden desplegar y plegar.
    const bloques = [
      'Organización del Estado y Administración electrónica',
      'Tecnología básica',
      'Desarrollo de aplicaciones',
      'Sistemas y comunicaciones',
      'Seguridad y protección de datos',
    ];
    for (const titulo of bloques) {
      const bloque = await screen.findByRole('button', { name: new RegExp(titulo) });
      expect(bloque).toHaveAttribute('aria-expanded', 'true');
    }
    // Los temas son enlaces a su ficha: 40, ni uno menos.
    await screen.findByText('La Constitución Española de 1978');
    const enlacesTema = screen
      .getAllByRole('link')
      .filter((enlace) => enlace.getAttribute('href')?.startsWith('/temario/tema-'));
    expect(enlacesTema).toHaveLength(40);
  });

  it('busca perdonando las tildes: «constitucion» encuentra «Constitución»', async () => {
    stubTemarioApi();
    renderWithProviders(<TemarioPage />, { route: '/temario' });

    await screen.findByText('La Constitución Española de 1978');
    const buscador = screen.getByLabelText('Buscar un tema');
    await userEvent.type(buscador, 'constitucion');

    expect(
      await screen.findByRole('link', { name: /La Constitución Española de 1978/ }),
    ).toBeInTheDocument();
    expect(screen.queryByText('Las Cortes Generales')).not.toBeInTheDocument();
    expect(screen.getByRole('status')).toHaveTextContent('1 tema');
  });

  it('avisa cuando la búsqueda no encuentra ningún tema', async () => {
    stubTemarioApi();
    renderWithProviders(<TemarioPage />, { route: '/temario' });

    await screen.findByText('La Constitución Española de 1978');
    await userEvent.type(screen.getByLabelText('Buscar un tema'), 'zzzz');

    expect(await screen.findByText('Sin resultados')).toBeInTheDocument();
    expect(screen.getByRole('status')).toHaveTextContent('Ningún tema coincide con la búsqueda');
  });

  it('enseña el avance total, el de cada bloque y qué queda por estudiar', async () => {
    stubTemarioApi();
    renderWithProviders(<TemarioPage />, { route: '/temario' });

    const barra = await screen.findByRole('progressbar', { name: 'Avance total' });
    expect(barra).toHaveAttribute('aria-valuenow', '30');
    expect(screen.getByText(/12 de 40 temas estudiados/)).toBeInTheDocument();
    expect(screen.getByRole('progressbar', { name: 'Avance del bloque I' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Qué queda' })).toBeInTheDocument();
    // Lo que más falta va primero: los dos bloques sin ningún tema marcado.
    const pendientes = screen.getAllByText(/sin estudiar/);
    expect(pendientes.length).toBeGreaterThan(0);
    expect(pendientes[0]).toHaveTextContent('8 de 8 sin estudiar');
  });

  it('enseña un estado vacío cuando todavía no hay temario común', async () => {
    stubApi({ '/api/v1/curricula': { body: [] } });
    renderWithProviders(<TemarioPage />, { route: '/temario' });

    expect(await screen.findByText('Todavía no hay temario común')).toBeInTheDocument();
  });

  it('enseña un estado de error con reintento si la lista no carga', async () => {
    stubApi({
      '/api/v1/curricula': {
        status: 500,
        body: { code: 'internal_error', detail: 'fallo interno' },
        contentType: 'application/problem+json',
      },
    });
    renderWithProviders(<TemarioPage />, { route: '/temario' });

    expect(await screen.findByText('No se pudo cargar el temario')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Reintentar' })).toBeInTheDocument();
  });
});

describe('ficha de tema', () => {
  it('muestra el título, la ruta y en qué convocatorias aparece', async () => {
    stubFichaApi();
    renderFicha('/temario/tema-1');

    expect(
      await screen.findByRole('heading', { level: 1, name: 'La Constitución Española de 1978' }),
    ).toBeInTheDocument();
    expect(screen.getByText('I.1')).toBeInTheDocument();
    expect(
      screen.getByRole('heading', { name: 'En qué convocatorias aparece' }),
    ).toBeInTheDocument();
    expect(screen.getByText(/ANEXO V, apartado 3/)).toBeInTheDocument();
    expect(screen.getByText('Temario que se estudia')).toBeInTheDocument();
    expect(screen.getByText('Temario complementario')).toBeInTheDocument();
    // Una convocatoria de un listado sin bases verificadas se distingue de las confirmadas.
    expect(screen.getByText('Por confirmar')).toBeInTheDocument();
    // Navegación anterior/siguiente dentro del temario: el siguiente tema del bloque I.
    expect(
      await screen.findByRole('link', { name: /Las Cortes Generales/ }),
    ).toBeInTheDocument();
  });

  it('muestra las particularidades de la convocatoria desde la que se llega', async () => {
    stubFichaApi({
      [`/api/v1/curriculum-nodes/tema-1?convocation_id=${TAI_CONVOCATION_ID}`]: {
        body: {
          ...temarioNodeFixture,
          particularities: [
            {
              kind: 'renamed',
              title_override: 'La Constitución y su reforma',
              evidence_quote: 'ANEXO V, apartado 4',
            },
          ],
        },
      },
    });
    renderFicha(`/temario/tema-1?convocatoria=${TAI_CONVOCATION_ID}`);

    expect(await screen.findByRole('heading', { name: 'En esta convocatoria' })).toBeInTheDocument();
    expect(screen.getByText('Renombrado')).toBeInTheDocument();
    expect(screen.getByText('La Constitución y su reforma')).toBeInTheDocument();
    expect(screen.getByText(/ANEXO V, apartado 4/)).toBeInTheDocument();
  });

  it('marca el tema como estudiado y permite retirar la marca', async () => {
    const fetchMock = stubFichaApi();
    renderFicha('/temario/tema-1');

    await userEvent.click(
      await screen.findByRole('button', { name: 'Marcar como estudiado' }),
    );
    expect(await screen.findByText(/Estudiado el/)).toBeInTheDocument();
    await waitFor(() => {
      expect(
        fetchMock.mock.calls.some(
          (call) =>
            typeof call[0] === 'string' &&
            call[0].includes('/curriculum-nodes/tema-1/studied') &&
            call[1]?.method === 'POST',
        ),
      ).toBe(true);
    });

    await userEvent.click(screen.getByRole('button', { name: 'Retirar la marca' }));
    expect(
      await screen.findByRole('button', { name: 'Marcar como estudiado' }),
    ).toBeInTheDocument();
    await waitFor(() => {
      expect(
        fetchMock.mock.calls.some(
          (call) =>
            typeof call[0] === 'string' &&
            call[0].includes('/curriculum-nodes/tema-1/studied') &&
            call[1]?.method === 'DELETE',
        ),
      ).toBe(true);
    });
  });

  it('dice que el tema aún no tiene apuntes en vez de inventar un texto', async () => {
    stubFichaApi();
    renderFicha('/temario/tema-1');

    expect(await screen.findByText('Este tema aún no tiene apuntes')).toBeInTheDocument();
  });
});
