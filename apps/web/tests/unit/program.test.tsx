import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it } from 'vitest';

import { AppShell } from '../../src/app/AppShell';
import { ProgramPage } from '../../src/pages/ProgramPage';
import {
  GC_ID,
  TAI_CONVOCATION_ID,
  convocationFixture,
  curriculumFixture,
  nodeDetailFixture,
  oppositionsFixture,
  renderWithProviders,
  stubApi,
} from './testUtils';

function stubProgramApi() {
  return stubApi({
    [`/api/v1/oppositions/${GC_ID}/activate`]: { body: { ...oppositionsFixture[1], active: true } },
    '/api/v1/oppositions': { body: oppositionsFixture },
    '/api/v1/curriculum-nodes/node-i-1': { body: nodeDetailFixture },
    [`/api/v1/convocations/${TAI_CONVOCATION_ID}/curriculum`]: { body: curriculumFixture },
    [`/api/v1/convocations/${TAI_CONVOCATION_ID}`]: { body: convocationFixture },
  });
}

describe('pantalla Programa', () => {
  it('muestra el árbol oficial con el recuento de bloques y temas', async () => {
    stubProgramApi();
    renderWithProviders(
      <AppShell>
        <ProgramPage />
      </AppShell>,
      { route: '/programa' },
    );

    expect(await screen.findByRole('heading', { level: 1, name: 'Programa' })).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.getByText('4')).toBeInTheDocument();
    });
    expect(screen.getByText('33')).toBeInTheDocument();
    expect(screen.getByRole('list', { name: 'Programa oficial' })).toBeInTheDocument();
    expect(
      screen.getByText('Organización del Estado y Administración electrónica'),
    ).toBeInTheDocument();
    expect(screen.getByText('La Constitución Española de 1978')).toBeInTheDocument();
  });

  it('muestra el enlace oficial y la fecha de publicación', async () => {
    stubProgramApi();
    renderWithProviders(
      <AppShell>
        <ProgramPage />
      </AppShell>,
      { route: '/programa' },
    );

    const link = await screen.findByRole('link', { name: /BOE-A-2025-26262/ });
    expect(link).toHaveAttribute(
      'href',
      'https://www.boe.es/diario_boe/txt.php?id=BOE-A-2025-26262',
    );
    expect(screen.getByText('2025-12-22')).toBeInTheDocument();
  });

  it('declara que el examen no publica la fecha de celebración', async () => {
    stubProgramApi();
    renderWithProviders(
      <AppShell>
        <ProgramPage />
      </AppShell>,
      { route: '/programa' },
    );

    expect(await screen.findByText('No consta en la convocatoria')).toBeInTheDocument();
  });

  it('abre el detalle de un nodo con su procedencia y sin inventar cobertura', async () => {
    stubProgramApi();
    renderWithProviders(
      <AppShell>
        <ProgramPage />
      </AppShell>,
      { route: '/programa' },
    );

    await userEvent.click(await screen.findByRole('button', { name: /La Constitución Española/ }));

    expect(await screen.findByText('I.1')).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Nodo seleccionado' })).toBeInTheDocument();
    // La cobertura **no** se inventa aquí: esta pantalla dice dónde se calcula y no enseña un cero que
    // parecería un dato. (Antes decía que no se calculaba todavía, y se calcula desde S04.)
    expect(screen.getByText(/Se calcula en Revisión, sobre las fuentes asignadas/)).toBeInTheDocument();
  });

  it('la parte de examen se muestra con sus cifras y su cita', async () => {
    stubProgramApi();
    renderWithProviders(
      <AppShell>
        <ProgramPage />
      </AppShell>,
      { route: '/programa' },
    );

    expect(await screen.findByRole('heading', { name: 'Reglas del examen' })).toBeInTheDocument();
    expect(screen.getByText('120 min')).toBeInTheDocument();
    expect(screen.getByText('80 (+5 de reserva)')).toBeInTheDocument();
    expect(screen.getByText('0–50, mínimo 25')).toBeInTheDocument();
    // Cada regla lleva su código y su cita literal.
    expect(screen.getByText('blank_answer_penalty')).toBeInTheDocument();
    expect(screen.getAllByText('Las respuestas en blanco no penalizan.')).toHaveLength(2);
  });

  it('muestra un ejercicio único que no cuelga de ninguna agrupación', async () => {
    // Celador publica un solo ejercicio, sin agrupar: si la pantalla solo pintara pruebas dentro de
    // un grupo, la parte no aparecería por ninguna parte y el examen quedaría sin cifras.
    stubApi({
      [`/api/v1/oppositions/${GC_ID}/activate`]: { body: { ...oppositionsFixture[1], active: true } },
      '/api/v1/oppositions': { body: oppositionsFixture },
      [`/api/v1/convocations/${TAI_CONVOCATION_ID}/curriculum`]: { body: curriculumFixture },
      [`/api/v1/convocations/${TAI_CONVOCATION_ID}`]: {
        body: {
          ...convocationFixture,
          parts: [
            {
              code: 'ejercicio_unico',
              name: 'Ejercicio único de la fase de oposición',
              kind: 'test',
              format: 'single_choice',
              position: 1,
              parent_code: null,
              ordinary_items: 70,
              reserve_items: 7,
              options_per_question: 4,
              score_min: 0,
              score_max: 150,
              pass_score: null,
              wrong_penalty_fraction: 0.25,
              fail_if_errors_gte: null,
              time_minutes: 90,
              structure_note: 'Un único ejercicio obligatorio y eliminatorio.',
              notes: null,
              evidence_quote: 'El ejercicio consistirá, para todos los turnos',
            },
          ],
        },
      },
    });
    renderWithProviders(
      <AppShell>
        <ProgramPage />
      </AppShell>,
      { route: '/programa' },
    );

    expect(
      await screen.findByRole('heading', { name: /Ejercicio único de la fase de oposición/ }),
    ).toBeInTheDocument();
    expect(screen.getByText('90 min')).toBeInTheDocument();
    expect(screen.getByText('70 (+7 de reserva)')).toBeInTheDocument();
    // Sin mínimo fijo no se inventa uno: el umbral relativo lo cuenta su regla.
    expect(screen.getByText('0–150, mínimo no consta')).toBeInTheDocument();
  });

  it('cambia de oposición activa a través de la API', async () => {
    const fetchMock = stubProgramApi();
    renderWithProviders(
      <AppShell>
        <ProgramPage />
      </AppShell>,
      { route: '/programa' },
    );

    const selector = await screen.findByLabelText('Oposición');
    await userEvent.selectOptions(selector, GC_ID);

    await waitFor(() => {
      const called = fetchMock.mock.calls.some(
        (call) =>
          typeof call[0] === 'string' &&
          call[0].includes(`/oppositions/${GC_ID}/activate`) &&
          call[1]?.method === 'POST',
      );
      expect(called).toBe(true);
    });
  });
});
