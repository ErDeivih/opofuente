/**
 * La pantalla del simulacro (F14): montarlo sabiendo qué va a caer.
 *
 * Lo que se comprueba:
 *
 * 1. el perfil del examen **tal como lo publica la convocatoria** —80 preguntas con 5 de reserva y un
 *    supuesto de 20 con 5, y los 120 minutos—, sin una cifra escrita a mano en la pantalla;
 * 2. la variante corta con lo que es de la aplicación (40 preguntas, 48 minutos) y **sin** reservas,
 *    porque prometer reservas que no van a caer sería mentir;
 * 3. el aviso de que no es un examen oficial y de que la nota es una **estimación**, que es el mismo
 *    texto que usa el motor al montarlo;
 * 4. que se puede elegir el bloque del supuesto (III o IV) viendo sus temas, y que lo elegido es lo
 *    que se manda al montar el simulacro.
 */

import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it } from 'vitest';

import { MockExamPage } from '../../src/pages/student/MockExamPage';
import { mockPlanFixture } from './studentFixtures';
import { renderWithProviders, stubApi } from './testUtils';

function montar() {
  const fetchMock = stubApi({
    '/api/v1/student/mock-exams': { body: mockPlanFixture },
    'POST /api/v1/student/mock-exams': {
      body: { ...mockPlanFixture, id: 'ses-simulacro' },
      status: 201,
    },
  });
  renderWithProviders(<MockExamPage />, { route: '/simulacros' });
  return fetchMock;
}

/** La URL de una llamada simulada, sin depender de su forma (`string`, `URL` o `Request`). */
function urlDe(url: RequestInfo | URL): string {
  if (typeof url === 'string') {
    return url;
  }
  return url instanceof URL ? url.href : url.url;
}

/** El cuerpo de la última llamada **de escritura** a una ruta, ya leído.
 *
 * Se filtra por método: la misma dirección responde al `GET` que trae el plan y al `POST` que monta
 * el simulacro, y quedarse con la primera llamada que aparezca cogería la lectura (que no lleva
 * cuerpo) en lugar de la escritura.
 */
function cuerpoDe(fetchMock: ReturnType<typeof stubApi>, trozo: string): Record<string, unknown> {
  const llamada = fetchMock.mock.calls.find(
    ([url, init]) => urlDe(url).includes(trozo) && init?.method === 'POST',
  );
  const cuerpo = llamada?.[1]?.body;
  if (typeof cuerpo !== 'string') {
    throw new Error('la llamada no llevaba cuerpo de texto');
  }
  return JSON.parse(cuerpo) as Record<string, unknown>;
}

describe('la pantalla del simulacro', () => {
  it('enseña lo que publica el perfil del examen: 80 más 5 y 20 más 5, en 120 minutos', async () => {
    montar();

    const partes = await screen.findByRole('list', { name: /partes del simulacro/i });
    const filas = within(partes).getAllByRole('listitem');
    expect(filas).toHaveLength(2);
    expect(within(filas[0]!).getByText(/80 preguntas/)).toBeInTheDocument();
    expect(within(filas[0]!).getByText(/5 de reserva/)).toBeInTheDocument();
    expect(within(filas[0]!).getByText(/120 minutos/)).toBeInTheDocument();
    expect(within(filas[0]!).getByText(/mínimo 25/)).toBeInTheDocument();
    expect(within(filas[0]!).getByText(/descuenta 1\/3/)).toBeInTheDocument();
    expect(within(filas[1]!).getByText(/20 preguntas/)).toBeInTheDocument();
  });

  it('no enseña ningún párrafo explicativo por defecto: la regla de la zona del alumno', async () => {
    montar();

    await screen.findByRole('radiogroup', { name: /supuesto práctico/i });
    // El párrafo gris que abría la pantalla («el mismo número de preguntas, el mismo tiempo y la
    // misma penalización que el día del examen») ya no está: ruega por defecto, no explica.
    expect(
      screen.queryByText(/el mismo número de preguntas, el mismo tiempo/i),
    ).not.toBeInTheDocument();
  });

  it('avisa de que no es un examen oficial y de que la nota es una estimación', async () => {
    montar();

    expect(await screen.findByText(/no es un examen oficial/i)).toBeInTheDocument();
    expect(screen.getAllByText(/estimación/i).length).toBeGreaterThan(0);
  });

  it('deja elegir el supuesto sin desplegarle los nueve temas debajo', async () => {
    montar();

    const bloques = await screen.findByRole('radiogroup', { name: /supuesto práctico/i });
    expect(within(bloques).getByRole('radio', { name: /bloque III/i })).toBeInTheDocument();
    expect(within(bloques).getByRole('radio', { name: /bloque IV/i })).toBeInTheDocument();
    expect(within(bloques).getByRole('radio', { name: /bloque IV/i })).toBeChecked();

    // La lista de temas del bloque sobraba: lo que hay que decidir aquí es III o IV, y lo que cae en
    // cada bloque se lee en el temario. La elegida sigue viajando al montar (la prueba de abajo).
    expect(screen.queryByRole('list', { name: /temas del bloque/i })).not.toBeInTheDocument();
  });

  it('el resumen de la variante cuenta las de reserva aparte: «100 preguntas (+10 de reserva)»', async () => {
    montar();

    // Sumarlas daba «110 preguntas» y son 100 las que se contestan más 10 de reserva.
    expect(await screen.findByText(/100 preguntas \(\+10 de reserva\)/)).toBeInTheDocument();
    expect(screen.getAllByText(/· 120 min/).length).toBeGreaterThan(0);
    expect(screen.queryByText(/110 preguntas/)).not.toBeInTheDocument();
  });

  it('monta el simulacro completo con el bloque elegido', async () => {
    const usuario = userEvent.setup();
    const fetchMock = montar();

    await usuario.click(await screen.findByRole('radio', { name: /bloque IV/i }));
    await usuario.click(screen.getByRole('button', { name: /empezar el simulacro/i }));

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/student/mock-exams'),
        expect.objectContaining({ method: 'POST' }),
      );
    });
    expect(cuerpoDe(fetchMock, '/student/mock-exams')).toEqual({
      variant: 'full',
      case_block: 'IV',
    });
  });

  it('monta la variante corta sin supuesto y con su propio tiempo', async () => {
    const usuario = userEvent.setup();
    const fetchMock = montar();

    await usuario.click(await screen.findByRole('radio', { name: /simulacro corto/i }));
    // El bloque del supuesto desaparece: la variante corta no lleva ninguno.
    expect(
      screen.queryByRole('radiogroup', { name: /supuesto práctico/i }),
    ).not.toBeInTheDocument();
    expect(screen.getAllByText(/48 minutos/).length).toBeGreaterThan(0);

    await usuario.click(screen.getByRole('button', { name: /empezar el simulacro/i }));

    await waitFor(() => {
      expect(cuerpoDe(fetchMock, '/student/mock-exams')).toMatchObject({ variant: 'short' });
    });
  });
});
