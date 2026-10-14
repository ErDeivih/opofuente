/**
 * La pantalla de resultado (F14): qué has fallado y **por qué tema**.
 *
 * Lo que se comprueba es lo que el encargo pide de esta pantalla y lo que una captura no demuestra:
 *
 * 1. la nota, con el aviso de que es una **estimación** (el texto del dominio, tal cual) y el
 *    desglose **por parte**: un simulacro tiene primera parte y supuesto, y cada una con su banda;
 * 2. el **desglose por tema** con su porcentaje escrito, que es para lo que sirve un resultado;
 * 3. pregunta a pregunta: tu respuesta, la correcta y la clave; el tiempo empleado; y una pregunta
 *    que la plantilla no corrige (`void`) contada aparte, no como fallo;
 * 4. las dos salidas: **repetir el test** —con los temas de este, no con otros— y **volver al tema**;
 * 5. y que de un test sin terminar no se enseña medio resultado: se dice que hay que terminarlo.
 */

import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Route, Routes } from 'react-router-dom';
import { describe, expect, it } from 'vitest';

import type { StudentSessionResult } from '../../src/api/studentTests';
import { ResultPage } from '../../src/pages/student/ResultPage';
import { sessionResultFixture } from './studentFixtures';
import { renderWithProviders, stubApi } from './testUtils';

function montar(resultado: StudentSessionResult = sessionResultFixture, status = 200) {
  const fetchMock = stubApi({
    '/api/v1/student/sessions/ses-9/result': { body: resultado, status },
    'POST /api/v1/student/tests': { body: { ...resultado.session, id: 'ses-10' }, status: 201 },
  });
  renderWithProviders(
    <Routes>
      <Route path="/resultado/:id" element={<ResultPage />} />
    </Routes>,
    { route: '/resultado/ses-9' },
  );
  return fetchMock;
}

describe('la pantalla de resultado', () => {
  it('enseña la nota con el aviso de que es una estimación y el desglose por parte', async () => {
    montar();

    expect(await screen.findByRole('heading', { name: /resultado/i })).toBeInTheDocument();
    // El aviso vive en el dominio y se enseña tal cual: es lo que impide leer la cifra como oficial.
    // Se espera a que llegue el resultado (el título está también mientras carga).
    expect(await screen.findByText(/no es la calificación oficial/i)).toBeInTheDocument();

    const partes = screen.getByRole('list', { name: /nota por parte/i });
    const filas = within(partes).getAllByRole('listitem');
    expect(filas).toHaveLength(1);
    expect(
      within(filas[0]!).getByText('Primera parte: cuestionario de conocimientos'),
    ).toBeInTheDocument();
    // La banda y el mínimo de la parte; el mínimo no sale en ningún otro sitio de la fila.
    expect(within(filas[0]!).getByText(/mínimo 25/)).toBeInTheDocument();
  });

  it('enseña el tiempo empleado', async () => {
    montar();

    expect(await screen.findByText(/12 min 30 s/)).toBeInTheDocument();
  });

  it('desglosa el resultado por tema con el porcentaje escrito', async () => {
    montar();

    const temas = await screen.findByRole('list', { name: /por tema/i });
    const filas = within(temas).getAllByRole('listitem');
    expect(filas).toHaveLength(2);
    // IV.7: dos fallos de dos → 0 %; IV.1: uno de dos → 50 %.
    expect(within(filas[0]!).getByText('IV.7')).toBeInTheDocument();
    expect(within(filas[0]!).getByText('0 %')).toBeInTheDocument();
    expect(within(filas[1]!).getByText('50 %')).toBeInTheDocument();
    // Y cada tema lleva su salida para repasarlo.
    expect(within(filas[1]!).getByRole('link', { name: /repasar iv\.1/i })).toHaveAttribute(
      'href',
      '/temario/IV.1',
    );
  });

  it('pinta cada pregunta con tu respuesta, la correcta y su tema', async () => {
    montar();

    const lista = await screen.findByRole('list', { name: /pregunta a pregunta/i });
    // Solo las preguntas: dentro de cada una hay otra lista (sus opciones), y sus filas también son
    // `listitem`. Se toman las hijas directas de la lista de preguntas.
    const preguntas = Array.from(lista.querySelectorAll<HTMLElement>(':scope > li'));
    expect(preguntas).toHaveLength(4);

    const primera = preguntas[0]!;
    expect(within(primera).getByText('¿Cuántas capas tiene el modelo OSI?')).toBeInTheDocument();
    expect(within(primera).getByText('Tu respuesta')).toBeInTheDocument();
    expect(within(primera).getByText('Correcta')).toBeInTheDocument();
    expect(within(primera).getByText('IV.7')).toBeInTheDocument();
    expect(within(primera).getByText(/2 s/)).toBeInTheDocument();

    // La acertada lo dice, y la que la plantilla no corrige se cuenta aparte: no es un fallo.
    expect(within(preguntas[1]!).getByText(/acertada/i)).toBeInTheDocument();
    expect(within(preguntas[3]!).getByText(/no se corrige/i)).toBeInTheDocument();
  });

  it('repite el test con los temas de este resultado, no con otros', async () => {
    const usuario = userEvent.setup();
    const fetchMock = montar();

    await usuario.click(await screen.findByRole('button', { name: /repetir este test/i }));

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/student/tests'),
        expect.objectContaining({ method: 'POST' }),
      );
    });
    const llamada = fetchMock.mock.calls.find(([url]) => {
      const direccion = typeof url === 'string' ? url : url instanceof URL ? url.href : url.url;
      return direccion.includes('/student/tests');
    });
    const cuerpo = llamada?.[1]?.body;
    if (typeof cuerpo !== 'string') {
      throw new Error('la llamada no llevaba cuerpo de texto');
    }
    const peticion = JSON.parse(cuerpo) as { nodes: string[]; count: number };
    expect(new Set(peticion.nodes)).toEqual(new Set(['IV.7', 'IV.1']));
    expect(peticion.count).toBe(4);
  });

  it('de un test sin terminar dice que hay que terminarlo, en vez de enseñar medio resultado', async () => {
    montar(
      {
        ...sessionResultFixture,
        session: { ...sessionResultFixture.session, status: 'running', finished_at: null },
      },
      409,
    );

    expect(
      await screen.findByText(/no está terminado|hay que terminar/i),
    ).toBeInTheDocument();
  });
});
