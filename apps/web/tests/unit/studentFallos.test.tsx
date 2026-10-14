/**
 * La pantalla de fallos (F14): tus preguntas falladas, y de aquí sale un test.
 *
 * Lo que se comprueba:
 *
 * 1. los totales —cuántos fallos y cuántos tocan hoy— y que el reparto por tema sume lo que hay;
 * 2. cada fallo con su tema, su fecha y **cuántas veces** se ha fallado, que es lo que dice si la
 *    pregunta se resiste;
 * 3. que se puede montar un test **solo con los fallos**: con todos (los temas que aparecen) y con los
 *    de un tema concreto, siempre con el filtro de falladas, que es lo que hace que el motor vuelva a
 *    elegir sobre los intentos de verdad;
 * 4. y que sin fallos no se ofrece un test de nada.
 */

import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it } from 'vitest';

import type { StudentMistakes } from '../../src/api/studentStudy';
import { MistakesPage } from '../../src/pages/student/MistakesPage';
import { mistakesFixture } from './studentFixtures';
import { renderWithProviders, stubApi } from './testUtils';

function montar(fallos: StudentMistakes = mistakesFixture) {
  const fetchMock = stubApi({
    '/api/v1/student/mistakes': { body: fallos },
    'POST /api/v1/student/tests': { body: { id: 'ses-fallos' }, status: 201 },
  });
  renderWithProviders(<MistakesPage />, { route: '/fallos' });
  return fetchMock;
}

/** La URL de una llamada simulada, sin depender de su forma (`string`, `URL` o `Request`). */
function urlDe(url: RequestInfo | URL): string {
  if (typeof url === 'string') {
    return url;
  }
  return url instanceof URL ? url.href : url.url;
}

function cuerpoDe(fetchMock: ReturnType<typeof stubApi>): Record<string, unknown> {
  const llamada = fetchMock.mock.calls.find(([url]) => urlDe(url).includes('/student/tests'));
  const cuerpo = llamada?.[1]?.body;
  if (typeof cuerpo !== 'string') {
    throw new Error('la llamada no llevaba cuerpo de texto');
  }
  return JSON.parse(cuerpo) as Record<string, unknown>;
}

describe('la pantalla de fallos', () => {
  it('enseña los totales y el reparto por tema', async () => {
    montar();

    expect(await screen.findByText(/2 preguntas falladas/)).toBeInTheDocument();
    expect(screen.getByText(/1 para repasar hoy/)).toBeInTheDocument();

    const temas = screen.getByRole('list', { name: /fallos por tema/i });
    const filas = within(temas).getAllByRole('listitem');
    expect(filas).toHaveLength(2);
    expect(within(filas[0]!).getByText('IV.7')).toBeInTheDocument();
    expect(within(filas[0]!).getByText(/1 fallo/)).toBeInTheDocument();
  });

  it('cada fallo lleva su tema, su fecha y cuántas veces se ha fallado', async () => {
    montar();

    const lista = await screen.findByRole('list', { name: /preguntas falladas/i });
    const filas = within(lista).getAllByRole('listitem');
    expect(filas).toHaveLength(2);

    const primera = filas[0]!;
    expect(within(primera).getByText('¿Cuántas capas tiene el modelo OSI?')).toBeInTheDocument();
    expect(within(primera).getByText('IV.7')).toBeInTheDocument();
    expect(within(primera).getByText(/la has fallado 3 veces/i)).toBeInTheDocument();
    expect(within(primera).getByText(/11 oct 2026/)).toBeInTheDocument();
    expect(within(primera).getByText(/toca repasar/i)).toBeInTheDocument();

    // Y cada tema tiene su salida para repasarlo.
    expect(within(primera).getByRole('link', { name: /repasar iv\.7/i })).toHaveAttribute(
      'href',
      '/temario/IV.7',
    );
  });

  it('monta un test solo con los fallos, con los temas que aparecen', async () => {
    const usuario = userEvent.setup();
    const fetchMock = montar();

    await usuario.click(
      await screen.findByRole('button', { name: /test con mis fallos/i }),
    );

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/student/tests'),
        expect.objectContaining({ method: 'POST' }),
      );
    });
    const cuerpo = cuerpoDe(fetchMock);
    expect(cuerpo.filter).toBe('failed');
    expect(new Set(cuerpo.nodes as string[])).toEqual(new Set(['IV.7', 'IV.1']));
    expect(cuerpo.count).toBe(2);
  });

  it('monta un test solo con los fallos de un tema', async () => {
    const usuario = userEvent.setup();
    const fetchMock = montar();

    const temas = await screen.findByRole('list', { name: /fallos por tema/i });
    await usuario.click(
      within(within(temas).getAllByRole('listitem')[0]!).getByRole('button', {
        name: /solo los de iv\.7/i,
      }),
    );

    await waitFor(() => {
      expect(cuerpoDe(fetchMock)).toMatchObject({ nodes: ['IV.7'], filter: 'failed' });
    });
  });

  it('sin fallos lo dice y no ofrece un test de nada', async () => {
    montar({ total: 0, due_total: 0, questions: [], topics: [] });

    expect(await screen.findByText(/no tienes ninguna pregunta fallada/i)).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /test con mis fallos/i })).not.toBeInTheDocument();
  });
});
