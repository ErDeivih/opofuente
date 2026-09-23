import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it } from 'vitest';

import { AppShell } from '../../src/app/AppShell';
import { ProgramPage } from '../../src/pages/ProgramPage';
import {
  CELADOR_2022_ID,
  CELADOR_ESTABILIZACION_ID,
  CELADOR_ID,
  GC_ID,
  TAI_CONVOCATION_ID,
  TAI_ID,
  celadorConvocationFixture,
  celadorConvocationsFixture,
  celadorCurriculumFixture,
  celador2022CurriculumFixture,
  celadorEstabilizacionConvocationFixture,
  celadorOppositionsFixture,
  convocationFixture,
  curriculumFixture,
  gcConvocationsFixture,
  masteryFixture,
  nodeDetailFixture,
  oppositionsFixture,
  renderWithProviders,
  stubApi,
  taiConvocationsFixture,
  type StubbedRoute,
} from './testUtils';

function stubProgramApi() {
  return stubApi({
    [`/api/v1/oppositions/${GC_ID}/activate`]: { body: { ...oppositionsFixture[1], active: true } },
    '/api/v1/oppositions': { body: oppositionsFixture },
    [`/api/v1/oppositions/${TAI_ID}/convocations`]: { body: taiConvocationsFixture },
    [`/api/v1/oppositions/${GC_ID}/convocations`]: { body: gcConvocationsFixture },
    [`/api/v1/reviews/mastery?opposition_id=${TAI_ID}`]: { body: masteryFixture },
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

  it('muestra las preguntas y el próximo repaso de cada tema (07_UI-UX §5)', async () => {
    stubProgramApi();
    renderWithProviders(
      <AppShell>
        <ProgramPage />
      </AppShell>,
      { route: '/programa' },
    );

    // El bloque tiene 12 preguntas, dos de ellas dudosas, y dos repasos vencidos.
    expect(await screen.findByText('preguntas: 12')).toBeInTheDocument();
    expect(screen.getByText('en conflicto: 1')).toBeInTheDocument();
    expect(screen.getByText('anulada: 1')).toBeInTheDocument();
    expect(screen.getByText('repaso vencido: 2')).toBeInTheDocument();
    // El tema sin repaso programado lo dice, y el que tiene fecha la enseña.
    expect(screen.getByText('repaso: 2026-09-25')).toBeInTheDocument();
    expect(screen.getByText(/1 de 2 con dominio estimado/)).toBeInTheDocument();
  });

  it('el descuadre del nodo no se enseña como cero: dice que no hay preguntas asignadas', async () => {
    stubProgramApi();
    stubApi({
      '/api/v1/oppositions': { body: oppositionsFixture },
      [`/api/v1/oppositions/${TAI_ID}/convocations`]: { body: taiConvocationsFixture },
      [`/api/v1/reviews/mastery?opposition_id=${TAI_ID}`]: {
        body: {
          ...masteryFixture,
          nodes: [
            {
              ...masteryFixture.nodes[1]!,
              study_state: {
                questions_total: 0,
                questions_by_status: [],
                questions_by_origin: [],
                reviews_due: 0,
                next_review_at: null,
              },
            },
          ],
        },
      },
      '/api/v1/curriculum-nodes/node-i-1': { body: nodeDetailFixture },
      [`/api/v1/convocations/${TAI_CONVOCATION_ID}/curriculum`]: { body: curriculumFixture },
      [`/api/v1/convocations/${TAI_CONVOCATION_ID}`]: { body: convocationFixture },
    });
    renderWithProviders(
      <AppShell>
        <ProgramPage />
      </AppShell>,
      { route: '/programa' },
    );

    expect(await screen.findByText('sin preguntas asignadas')).toBeInTheDocument();
    expect(screen.getByText('sin repaso programado')).toBeInTheDocument();
  });

  it('el nodo seleccionado desglosa sus preguntas por origen y por estado', async () => {
    stubProgramApi();
    stubApi({
      '/api/v1/oppositions': { body: oppositionsFixture },
      [`/api/v1/oppositions/${TAI_ID}/convocations`]: { body: taiConvocationsFixture },
      [`/api/v1/reviews/mastery?opposition_id=${TAI_ID}`]: { body: masteryFixture },
      // El bloque también tiene ficha: la tarjeta del nodo seleccionado la pide.
      '/api/v1/curriculum-nodes/node-i': {
        body: { ...nodeDetailFixture, node: curriculumFixture.nodes[0]!, ancestors: [] },
      },
      [`/api/v1/convocations/${TAI_CONVOCATION_ID}/curriculum`]: { body: curriculumFixture },
      [`/api/v1/convocations/${TAI_CONVOCATION_ID}`]: { body: convocationFixture },
    });
    renderWithProviders(
      <AppShell>
        <ProgramPage />
      </AppShell>,
      { route: '/programa' },
    );

    const bloque = await screen.findByRole('button', { name: /Organización del Estado/ });
    await userEvent.click(bloque);

    // El desglose completo vive en la ficha del nodo, que es donde hay sitio para leerlo.
    expect(
      await screen.findByText(/12 en total · 4 OFICIAL, 8 PRIVADA · 1 anulada, 10 completa/),
    ).toBeInTheDocument();
    expect(screen.getByText(/2 repaso\(s\) vencido\(s\): tocan ahora/)).toBeInTheDocument();
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
      [`/api/v1/oppositions/${TAI_ID}/convocations`]: { body: taiConvocationsFixture },
      [`/api/v1/oppositions/${GC_ID}/convocations`]: { body: gcConvocationsFixture },
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

/** Celador tiene dos convocatorias publicadas: la ordinaria (vigente) y la de estabilización. */
function stubCeladorProgramApi(extra: Record<string, StubbedRoute> = {}) {
  return stubApi({
    '/api/v1/oppositions': { body: celadorOppositionsFixture },
    [`/api/v1/oppositions/${CELADOR_ID}/convocations`]: { body: celadorConvocationsFixture },
    [`/api/v1/convocations/${CELADOR_2022_ID}/curriculum`]: {
      body: celador2022CurriculumFixture,
    },
    [`/api/v1/convocations/${CELADOR_2022_ID}`]: { body: celadorConvocationFixture },
    [`/api/v1/convocations/${CELADOR_ESTABILIZACION_ID}/curriculum`]: {
      body: celadorCurriculumFixture,
    },
    [`/api/v1/convocations/${CELADOR_ESTABILIZACION_ID}`]: {
      body: celadorEstabilizacionConvocationFixture,
    },
    ...extra,
  });
}

describe('selector de convocatoria', () => {
  it('no se pinta cuando la oposición tiene una sola convocatoria', async () => {
    stubApi({
      '/api/v1/oppositions': { body: oppositionsFixture },
      [`/api/v1/oppositions/${CELADOR_ID}/convocations`]: {
        body: [celadorConvocationsFixture[0]],
      },
      [`/api/v1/oppositions/${CELADOR_ID}/activate`]: {
        body: { ...oppositionsFixture[0], active: true },
      },
      [`/api/v1/convocations/${TAI_CONVOCATION_ID}/curriculum`]: { body: curriculumFixture },
      [`/api/v1/convocations/${TAI_CONVOCATION_ID}`]: { body: convocationFixture },
    });
    renderWithProviders(
      <AppShell>
        <ProgramPage />
      </AppShell>,
      { route: '/programa' },
    );

    expect(await screen.findByRole('heading', { level: 1, name: 'Programa' })).toBeInTheDocument();
    // Un desplegable de una sola opción es ruido: con una convocatoria no se pinta.
    expect(screen.queryByLabelText('Convocatoria')).not.toBeInTheDocument();
  });

  it('ofrece las dos convocatorias y marca cuál es la vigente', async () => {
    stubCeladorProgramApi();
    renderWithProviders(
      <AppShell>
        <ProgramPage />
      </AppShell>,
      { route: '/programa' },
    );

    const selector = await screen.findByLabelText('Convocatoria');
    const opciones = within(selector).getAllByRole('option');
    expect(opciones).toHaveLength(2);
    // La de estabilización está publicada y pendiente de ejercicio; la ordinaria es la vigente.
    expect(opciones[0]).toHaveTextContent(
      'ORDEN SAN/1917/2022 · 2022-12-28 · sin fecha de ejercicio',
    );
    expect(opciones[1]).toHaveTextContent('ORDEN SAN/1828/2022 · 2022-12-22 · vigente');
    expect(selector).toHaveValue(CELADOR_2022_ID);
  });

  it('muestra el programa y el ejercicio de la convocatoria vigente', async () => {
    stubCeladorProgramApi();
    renderWithProviders(
      <AppShell>
        <ProgramPage />
      </AppShell>,
      { route: '/programa' },
    );

    // La vigente es la ordinaria: dieciséis temas sin bloques y 70 preguntas en 90 minutos.
    expect(
      await screen.findByRole('heading', { name: /Ejercicio único de la fase de oposición/ }),
    ).toBeInTheDocument();
    expect(screen.getByText('90 min')).toBeInTheDocument();
    expect(screen.getByText('70 (+7 de reserva)')).toBeInTheDocument();
    expect(screen.getByText('Tema 1 del programa de 2022')).toBeInTheDocument();
  });

  it('explica por qué una convocatoria no tiene fecha de ejercicio', async () => {
    // Estado real tras elegir la de estabilización: no hay fecha y la procedencia dice por qué.
    stubCeladorProgramApi({
      '/api/v1/oppositions': {
        body: [
          {
            ...celadorOppositionsFixture[0],
            active_convocation: {
              id: CELADOR_ESTABILIZACION_ID,
              code: 'celador-sacyl-estabilizacion-2022',
              published_at: '2022-12-28',
              status: 'active',
            },
          },
        ],
      },
      [`/api/v1/oppositions/${CELADOR_ID}/convocations`]: {
        body: [
          { ...celadorConvocationsFixture[0], status: 'active' },
          { ...celadorConvocationsFixture[1], status: 'available' },
        ],
      },
    });
    renderWithProviders(
      <AppShell>
        <ProgramPage />
      </AppShell>,
      { route: '/programa' },
    );

    expect(await screen.findByText('No consta en la convocatoria')).toBeInTheDocument();
    expect(
      screen.getByText(/El plazo de solicitudes cerró en enero de 2023 y el proceso sigue sin ejercicio/),
    ).toBeInTheDocument();
  });

  it('cambia de convocatoria a través de la API', async () => {
    const fetchMock = stubCeladorProgramApi();
    renderWithProviders(
      <AppShell>
        <ProgramPage />
      </AppShell>,
      { route: '/programa' },
    );

    await userEvent.selectOptions(
      await screen.findByLabelText('Convocatoria'),
      CELADOR_ESTABILIZACION_ID,
    );

    await waitFor(() => {
      const called = fetchMock.mock.calls.some(
        (call) =>
          typeof call[0] === 'string' &&
          call[0].includes(`/convocations/${CELADOR_ESTABILIZACION_ID}/activate`) &&
          call[1]?.method === 'POST',
      );
      expect(called).toBe(true);
    });
  });

  it('enseña el motivo cuando la convocatoria no se puede activar', async () => {
    // 409 del servidor: la convocatoria existe pero no se puede usar (sin programa, en borrador o
    // archivada). El motivo que da la API es la explicación, no un «error» genérico.
    stubCeladorProgramApi({
      [`/api/v1/convocations/${CELADOR_ESTABILIZACION_ID}/activate`]: {
        status: 409,
        body: {
          type: 'about:blank',
          title: 'Conflict',
          status: 409,
          detail: 'la convocatoria no tiene programa sembrado: no hay temario con el que trabajar',
          instance: `/api/v1/convocations/${CELADOR_ESTABILIZACION_ID}/activate`,
          code: 'invalid_state',
          correlation_id: 'corr-de-prueba',
        },
        contentType: 'application/problem+json',
      },
    });
    renderWithProviders(
      <AppShell>
        <ProgramPage />
      </AppShell>,
      { route: '/programa' },
    );

    await userEvent.selectOptions(
      await screen.findByLabelText('Convocatoria'),
      CELADOR_ESTABILIZACION_ID,
    );

    expect(
      await screen.findByText(
        'la convocatoria no tiene programa sembrado: no hay temario con el que trabajar',
      ),
    ).toBeInTheDocument();
  });
});
