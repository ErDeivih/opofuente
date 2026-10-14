/**
 * La pantalla de progreso (F14).
 *
 * Lo que se comprueba:
 *
 * 1. **el porcentaje escrito**, por bloque y por tema: una barra sin número obliga a adivinar, y eso
 *    ya se decidió en F13;
 * 2. los aciertos y cuántos tests se han hecho —el número de verdad, no los que caben en el
 *    historial—;
 * 3. **qué falta**: el tema sin empezar se dice con palabras («Sin empezar»), no con un 0 % que
 *    parecería un suspenso;
 * 4. y la evolución: los tests terminados, del más nuevo al más viejo, con su nota.
 */

import { screen, within } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { ProgressPage } from '../../src/pages/student/ProgressPage';
import { progressFixture } from './studentFixtures';
import { renderWithProviders, stubApi } from './testUtils';

function montar() {
  stubApi({ '/api/v1/student/progress': { body: progressFixture } });
  return renderWithProviders(<ProgressPage />, { route: '/progreso' });
}

describe('la pantalla de progreso', () => {
  it('enseña cuántos tests hay hechos y el porcentaje por bloque, escrito', async () => {
    montar();

    expect(await screen.findByText(/14 tests hechos/)).toBeInTheDocument();

    const bloques = screen.getByRole('list', { name: /progreso por bloque/i });
    const filas = within(bloques).getAllByRole('listitem');
    expect(filas).toHaveLength(2);
    expect(within(filas[0]!).getByText('64 %')).toBeInTheDocument();
    expect(within(filas[1]!).getByText('75 %')).toBeInTheDocument();
  });

  it('desglosa por tema con su porcentaje, sus aciertos y qué falta', async () => {
    montar();

    const temas = await screen.findByRole('list', { name: /progreso por tema/i });
    const filas = within(temas).getAllByRole('listitem');
    // I.1, I.6, IV.1, IV.7 y IV.10: los cinco temas del temario de prueba.
    expect(filas).toHaveLength(5);
    expect(within(filas[0]!).getByText('I.1')).toBeInTheDocument();
    expect(within(filas[0]!).getByText(/16 de 25/)).toBeInTheDocument();
    expect(within(filas[2]!).getByText('75 %')).toBeInTheDocument();
    // I.6 y IV.10 no se han empezado: se dice, no se pinta un cero.
    expect(within(filas[1]!).getByText(/sin empezar/i)).toBeInTheDocument();
    expect(within(filas[4]!).getByText(/sin empezar/i)).toBeInTheDocument();
  });

  it('enseña la evolución: los tests terminados, con su nota', async () => {
    montar();

    const historial = await screen.findByRole('list', { name: /evolución/i });
    const filas = within(historial).getAllByRole('listitem');
    expect(filas).toHaveLength(1);
    const unica = filas[0]!;
    expect(within(unica).getByText(/Test de IV\.1/)).toBeInTheDocument();
    expect(within(unica).getByText(/14 aciertos/)).toBeInTheDocument();
    expect(within(unica).getByRole('link', { name: /ver el resultado/i })).toHaveAttribute(
      'href',
      '/resultado/ses-2',
    );
  });

  it('destaca los temas más flojos, que es lo que hay que repasar', async () => {
    montar();

    const flojos = await screen.findByRole('list', { name: /temas más flojos/i });
    expect(within(flojos).getByText('IV.1')).toBeInTheDocument();
  });
});
