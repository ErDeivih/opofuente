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
  temarioMaterialPageFixture,
  temarioNodeFixture,
  temarioProgressFixture,
  temarioQuestionPageFixture,
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
    '/api/v1/curriculum-nodes/tema-1/questions': { body: temarioQuestionPageFixture },
    '/api/v1/curriculum-nodes/tema-1/materials': { body: temarioMaterialPageFixture },
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
    // Cada convocatoria confirmada enlaza a sus bases oficiales.
    expect(screen.getByRole('link', { name: 'Bases oficiales' })).toHaveAttribute(
      'href',
      'https://www.boe.es/diario_boe/txt.php?id=BOE-A-2025-26262',
    );
    expect(screen.getByText('Temario que se estudia')).toBeInTheDocument();
    expect(screen.getByText('Temario complementario')).toBeInTheDocument();
    // Una convocatoria de un listado sin bases verificadas se distingue de las confirmadas.
    expect(screen.getByText('Por confirmar')).toBeInTheDocument();
    // Navegación anterior/siguiente dentro del temario: el siguiente tema del bloque I.
    expect(
      await screen.findByRole('link', { name: /Las Cortes Generales/ }),
    ).toBeInTheDocument();
  });

  it('enseña las preguntas del tema, sin la clave y con su tipo', async () => {
    stubFichaApi();
    renderFicha('/temario/tema-1');

    expect(await screen.findByRole('heading', { name: 'Preguntas' })).toBeInTheDocument();
    expect(await screen.findByText(/2 preguntas/)).toBeInTheDocument();
    expect(
      screen.getByText('¿Cuál es la norma suprema del ordenamiento jurídico?'),
    ).toBeInTheDocument();
    // Cada pregunta lleva al banco con su conjunto y su pregunta ya abiertos.
    expect(screen.getAllByRole('link', { name: 'Ver en el banco' })[0]).toHaveAttribute(
      'href',
      '/preguntas?conjunto=set-1&pregunta=preg-1',
    );
    expect(screen.getByText('Una respuesta')).toBeInTheDocument();
    expect(screen.getByText('Reserva')).toBeInTheDocument();
  });

  it('enseña el material de la biblioteca que apunta al tema', async () => {
    stubFichaApi();
    renderFicha('/temario/tema-1');

    expect(await screen.findByText('Material del tema')).toBeInTheDocument();
    expect(screen.getAllByText('Apuntes de Constitución')).toHaveLength(1);
    // El material abre la biblioteca en el documento del que sale.
    expect(screen.getByRole('link', { name: 'Apuntes de Constitución' })).toHaveAttribute(
      'href',
      '/biblioteca?documento=doc-1',
    );
    expect(screen.getByText(/pág\. 3/)).toBeInTheDocument();
    expect(
      screen.getByText('La Constitución es la norma suprema del ordenamiento jurídico.'),
    ).toBeInTheDocument();
  });

  it('agrupa las convocatorias por confirmar para no llenar la ficha de ruido', async () => {
    stubFichaApi();
    renderFicha('/temario/tema-1');

    const resumen = await screen.findByText('1 convocatoria por confirmar');
    expect(resumen.closest('details')).not.toHaveAttribute('open');
    expect(
      screen.getByText('Vienen de un listado de convocatorias; faltan sus bases oficiales.'),
    ).toBeInTheDocument();
    // Las confirmadas sí llevan su enlace; la de un listado sin bases, no.
    expect(screen.getAllByRole('link', { name: 'Ver particularidades' })).toHaveLength(1);

    await userEvent.click(resumen);
    expect(resumen.closest('details')).toHaveAttribute('open');
  });

  it('dice que no hay preguntas cuando el tema no tiene ninguna', async () => {
    stubFichaApi({
      '/api/v1/curriculum-nodes/tema-1/questions': {
        body: { ...temarioQuestionPageFixture, total: 0, questions: [] },
      },
    });
    renderFicha('/temario/tema-1');

    expect(await screen.findByText('Este tema aún no tiene preguntas')).toBeInTheDocument();
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
