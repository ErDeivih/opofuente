/**
 * La pantalla de exámenes oficiales (F14).
 *
 * Es la pantalla más fácil de mentir de toda la zona del alumno: si no hay exámenes importados, lo
 * cómodo es rellenarla con cualquier cosa que se le parezca. Lo que se comprueba aquí es justo lo
 * contrario:
 *
 * 1. **sin exámenes, lo dice con esas palabras** («todavía no hay exámenes oficiales importados») y
 *    explica por qué, sin enseñar una lista vacía sin explicación ni inventar datos;
 * 2. con exámenes, cada uno con su fecha y su tamaño, y el que no se puede correr todavía lo dice con
 *    su motivo en vez de ofrecer un botón que falle;
 * 3. y hacer uno **pide el examen por su sitio en la lista**, no por un identificador.
 */

import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it } from 'vitest';

import type { StudentOfficialExams } from '../../src/api/studentStudy';
import { OfficialExamsPage } from '../../src/pages/student/OfficialExamsPage';
import { officialExamsFixture, officialExamsVacioFixture } from './studentFixtures';
import { renderWithProviders, stubApi } from './testUtils';

function montar(examenes: StudentOfficialExams) {
  const fetchMock = stubApi({
    '/api/v1/student/official-exams': { body: examenes },
    'POST /api/v1/student/official-exams/1/sessions': {
      body: { id: 'ses-examen' },
      status: 201,
    },
  });
  renderWithProviders(<OfficialExamsPage />, { route: '/examenes' });
  return fetchMock;
}

describe('la pantalla de exámenes oficiales', () => {
  it('sin exámenes importados lo dice con esas palabras y explica qué pasa', async () => {
    montar(officialExamsVacioFixture);

    expect(
      await screen.findByText(/todavía no hay exámenes oficiales importados/i),
    ).toBeInTheDocument();
    // Y no deja la pantalla como si estuviera cargando: no hay ninguna lista de exámenes.
    expect(screen.queryByRole('list', { name: /exámenes/i })).not.toBeInTheDocument();
  });

  it('con exámenes, cada uno con su fecha, su tamaño y su botón', async () => {
    montar(officialExamsFixture);

    const lista = await screen.findByRole('list', { name: /exámenes oficiales/i });
    const filas = within(lista).getAllByRole('listitem');
    expect(filas).toHaveLength(4);
    expect(within(filas[0]!).getByText(/TAI ingreso libre 2025/)).toBeInTheDocument();
    expect(within(filas[0]!).getByText(/22 nov 2025/)).toBeInTheDocument();
    expect(within(filas[0]!).getByText(/85 preguntas/)).toBeInTheDocument();
    expect(
      within(filas[0]!).getByRole('button', { name: /hacer este examen/i }),
    ).toBeInTheDocument();
  });

  it('sin día pero con año, la fecha es el año que declara el documento (§3.7)', async () => {
    montar(officialExamsFixture);

    const lista = await screen.findByRole('list', { name: /exámenes oficiales/i });
    const tercera = within(lista).getAllByRole('listitem')[2]!;
    // Ni «sin fecha publicada» ni un 1 de enero inventado: el año, que es lo que el cuestionario
    // del INAP rotula en su cabecera.
    expect(within(tercera).getByText(/ejercicio de 2019/i)).toBeInTheDocument();
    expect(within(tercera).queryByText(/sin fecha publicada/i)).toBeNull();
    expect(within(tercera).getByText(/85 preguntas/)).toBeInTheDocument();
  });

  it('sin año en el origen, se dice que no hay fecha y por qué', async () => {
    montar(officialExamsFixture);

    const lista = await screen.findByRole('list', { name: /exámenes oficiales/i });
    const cuarta = within(lista).getAllByRole('listitem')[3]!;
    expect(within(cuarta).getByText(/sin fecha publicada/i)).toBeInTheDocument();
    expect(within(cuarta).getByText(/el documento de origen no la declara/i)).toBeInTheDocument();
  });

  it('faltan preguntas y faltan respuestas no se dicen con la misma frase', async () => {
    montar(officialExamsFixture);

    const lista = await screen.findByRole('list', { name: /exámenes oficiales/i });
    const filas = within(lista).getAllByRole('listitem');
    expect(within(filas[1]!).getByText(/faltan sus respuestas/i)).toBeInTheDocument();
    expect(within(filas[3]!).getByText(/menos preguntas de las que pide/i)).toBeInTheDocument();
  });

  it('un examen que todavía no se puede corregir lo dice y no ofrece el botón', async () => {
    montar(officialExamsFixture);

    const lista = await screen.findByRole('list', { name: /exámenes oficiales/i });
    const segunda = within(lista).getAllByRole('listitem')[1]!;
    expect(within(segunda).queryByRole('button', { name: /hacer este examen/i })).toBeNull();
    expect(within(segunda).getByText(/todavía no se puede hacer/i)).toBeInTheDocument();
  });

  it('monta el examen que se pide, por su sitio en la lista', async () => {
    const usuario = userEvent.setup();
    const fetchMock = montar(officialExamsFixture);

    const lista = await screen.findByRole('list', { name: /exámenes oficiales/i });
    await usuario.click(
      within(within(lista).getAllByRole('listitem')[0]!).getByRole('button', {
        name: /hacer este examen/i,
      }),
    );

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/student/official-exams/1/sessions'),
        expect.objectContaining({ method: 'POST' }),
      );
    });
  });
});
