import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it } from 'vitest';

import type { ConceptGroup, LearningErrorDetail, ReviewQueue } from '../../src/api/reviews';
import { AppRoutes } from '../../src/app/routes';
import {
  capabilitiesFixture,
  oppositionsFixture,
  readinessReady,
  renderWithProviders,
  settingsFixture,
  stubApi,
  type StubbedRoute,
} from './testUtils';

/**
 * Pantalla Errores (S10) desde el comportamiento real: qué dice la cola de cada elemento, qué pasa al
 * declarar un repaso, qué enseña la ficha de un error y qué advierte una exportación.
 *
 * Las respuestas imitan el contrato real, incluidos los avisos de la exportación y el hecho de que la
 * cola **no** trae la solución.
 */

const COLA: ReviewQueue = {
  items: [
    {
      review: {
        id: 'rev-1',
        question_version_id: 'q-1',
        opposition_id: 'opp-tai',
        learning_error_id: null,
        due_at: '2026-09-18T09:00:00Z',
        interval_days: 0,
        repetitions: 0,
        lapses: 2,
        last_reviewed_at: null,
        last_reason: 'un fallo entra en la cola de hoy mismo',
        created_at: '2026-09-17T09:00:00Z',
        updated_at: '2026-09-17T09:00:00Z',
      },
      question_version_id: 'q-1',
      question_set_id: 'set-1',
      stable_key: 'q001',
      stem: 'El plazo del procedimiento es de diez dias habiles:',
      part_code: 'primera_parte',
      is_reserve: false,
      origin_type: 'private',
      overdue_days: 0,
      explanation: 'un fallo entra en la cola de hoy mismo',
      options: [
        { stable_key: 'a', text: 'Verdadero' },
        { stable_key: 'b', text: 'Falso' },
      ],
      session_id: 'ses-1',
    },
  ],
  stats: { active: 1, due: 1, next_due_at: '2026-09-18T09:00:00Z', lapses: 2 },
  concepts: [],
  notes: [],
};

const CONCEPTOS: ConceptGroup = {
  total_errors: 1,
  open_errors: 1,
  groups: [
    {
      key: 'label:plazos',
      label: 'plazos',
      node_id: null,
      open_count: 1,
      resolved_count: 0,
      occurrences: 2,
      last_seen_at: '2026-09-17T09:00:00Z',
      errors: [
        {
          id: 'err-1',
          attempt_id: 'att-1',
          question_version_id: 'q-1',
          stable_key: 'q001',
          stem: 'El plazo del procedimiento es de diez dias habiles:',
          session_id: 'ses-1',
          part_code: 'primera_parte',
          curriculum_node_id: null,
          node_title: null,
          concept_label: 'plazos',
          cause: 'confusion',
          user_note: 'Lo confundí con el cómputo',
          status: 'open',
          occurrences: 2,
          first_seen_at: '2026-09-16T09:00:00Z',
          last_seen_at: '2026-09-17T09:00:00Z',
          resolved_at: null,
        },
      ],
    },
  ],
};

const DETALLE: LearningErrorDetail = {
  error: CONCEPTOS.groups[0]!.errors[0]!,
  chosen_option_keys: ['b'],
  confidence: 'high',
  answered_at: '2026-09-17T09:00:00Z',
  review: COLA.items[0]!.review,
  events: [
    {
      id: 'ev-2',
      kind: 'reviewed',
      outcome: 'correct',
      confidence: 'high',
      cause: null,
      note: null,
      previous_due_at: '2026-09-17T09:00:00Z',
      due_at: '2026-09-21T09:00:00Z',
      previous_interval_days: 0,
      interval_days: 4,
      repetitions: 1,
      reason: 'acertada después de un fallo: cuatro días',
      occurred_at: '2026-09-17T10:00:00Z',
    },
    {
      id: 'ev-1',
      kind: 'created',
      outcome: 'wrong',
      confidence: 'high',
      cause: null,
      note: null,
      previous_due_at: null,
      due_at: '2026-09-17T09:00:00Z',
      previous_interval_days: null,
      interval_days: 0,
      repetitions: 0,
      reason: 'un fallo entra en la cola de hoy mismo',
      occurred_at: '2026-09-17T09:00:00Z',
    },
  ],
};

function stubErrores(overrides: Record<string, StubbedRoute> = {}) {
  return stubApi({
    '/api/v1/health/ready': { body: readinessReady },
    '/api/v1/capabilities': { body: capabilitiesFixture },
    '/api/v1/settings': { body: settingsFixture },
    '/api/v1/oppositions': { body: oppositionsFixture },
    '/api/v1/reviews/due?opposition_id=opp-tai': { body: COLA },
    '/api/v1/learning-errors?opposition_id=opp-tai': { body: CONCEPTOS },
    '/api/v1/learning-errors/err-1': { body: DETALLE },
    '/api/v1/reviews/rev-1/complete': { body: { ...COLA.items[0]!.review, interval_days: 4 } },
    '/api/v1/reviews/rev-1/snooze': { body: COLA.items[0]!.review },
    '/api/v1/learning-errors/err-1/resolution': {
      body: { ...CONCEPTOS.groups[0]!.errors[0]!, status: 'resolved' },
    },
    '/api/v1/exports/anki-csv': {
      body: {
        filename: 'banco-20260918-120000.csv',
        format: 'anki_csv',
        path: 'F:\\datos\\exports\\banco-20260918-120000.csv',
        bytes: 2048,
        item_count: 12,
        documents: ['Temario oficial (ver-1)'],
        warnings: [
          '3 de 12 pregunta(s) citan material con derechos restringidos o sin determinar: al exportar sale de la aplicación, así que revísalo antes de compartirlo.',
        ],
        provenance: { opofuente: '0.0.0-test' },
        content: 'pregunta;opciones\n"El plazo...";"A) Verdadero"\n',
      },
    },
    ...overrides,
  });
}

function renderErrores() {
  // El marco lo pone la ruta (F1 del rediseño): `/errores` es una dirección antigua que lleva al
  // panel, y el panel trae su propio marco.
  return renderWithProviders(<AppRoutes />, { route: '/errores' });
}

describe('errores: la cola de hoy', () => {
  it('dice qué toca, desde cuándo y por qué, y no enseña la solución', async () => {
    stubErrores();
    renderErrores();

    expect(await screen.findByRole('heading', { level: 1, name: 'Errores' })).toBeInTheDocument();
    expect(await screen.findByText(/1 de 1 vencidos · 2 fallo\(s\) acumulado\(s\)/)).toBeInTheDocument();
    expect(
      screen.getByText('El plazo del procedimiento es de diez dias habiles:'),
    ).toBeInTheDocument();
    expect(screen.getByText('toca hoy')).toBeInTheDocument();
    expect(screen.getByText(/primer repaso · 2 fallo\(s\)/)).toBeInTheDocument();
    expect(screen.getByText('un fallo entra en la cola de hoy mismo')).toBeInTheDocument();
    // La cola deja repasar, pero no dice cuál es la correcta.
    expect(screen.getByText('Verdadero')).toBeInTheDocument();
    expect(screen.queryByText(/respuesta correcta:/i)).toBeNull();
  });

  it('declara un repaso hecho fuera y avisa de que el desenlace es declarado', async () => {
    const fetchMock = stubErrores();
    renderErrores();

    await screen.findByText('El plazo del procedimiento es de diez dias habiles:');
    await userEvent.click(screen.getByRole('button', { name: /Declarar que acerté el repaso/ }));

    await waitFor(() => {
      const llamada = fetchMock.mock.calls.find(
        (call) => typeof call[0] === 'string' && call[0].includes('/complete'),
      );
      expect(llamada).toBeDefined();
      expect(cuerpoJsonDe(llamada)).toMatchObject({
        outcome: 'correct',
        confidence: 'high',
      });
    });
    expect(
      screen.getByText(/el desenlace lo dices tú, no lo mide la aplicación/),
    ).toBeInTheDocument();
  });

  it('aplaza un repaso sin contarlo como repasado', async () => {
    const fetchMock = stubErrores();
    renderErrores();

    await screen.findByText('El plazo del procedimiento es de diez dias habiles:');
    await userEvent.click(screen.getByRole('button', { name: /Aplazar el repaso de / }));

    await waitFor(() => {
      const llamada = fetchMock.mock.calls.find(
        (call) => typeof call[0] === 'string' && call[0].includes('/snooze'),
      );
      expect(cuerpoJsonDe(llamada)).toEqual({ days: 3 });
    });
  });

  it('repasar de verdad se hace en una sesión compuesta con lo vencido', async () => {
    const fetchMock = stubErrores({
      '/api/v1/study-sessions': {
        status: 201,
        body: {
          id: 'ses-repaso',
          mode: 'error_review',
          status: 'draft',
          feedback: 'immediate',
          opposition_id: 'opp-tai',
          convocation_version_id: 'conv-tai',
          question_set_id: null,
          answer_key_version_id: null,
          key_label: 'repaso',
          configuration: {
            mode: 'error_review',
            feedback: 'immediate',
            time_limit_minutes: null,
            shuffle: false,
            sources: [],
          },
          time_limit_minutes: null,
          total_questions: 1,
          answered_questions: 0,
          started_at: null,
          finished_at: null,
          created_at: '2026-09-18T09:00:00Z',
          result: null,
        },
      },
    });
    renderErrores();

    await screen.findByText('El plazo del procedimiento es de diez dias habiles:');
    await userEvent.click(screen.getByRole('button', { name: /Repasar en una sesión/ }));

    await waitFor(() => {
      const llamada = fetchMock.mock.calls.find(
        (call) =>
          typeof call[0] === 'string' &&
          call[0].endsWith('/api/v1/study-sessions') &&
          call[1]?.method === 'POST',
      );
      expect(llamada).toBeDefined();
      expect(cuerpoJsonDe(llamada)).toMatchObject({
        mode: 'error_review',
        sources: [],
      });
    });
  });
});

describe('errores: los conceptos', () => {
  it('agrupa los fallos y enseña la ficha con su historial y sus dos fechas', async () => {
    stubErrores();
    renderErrores();

    await userEvent.click(await screen.findByRole('tab', { name: 'Conceptos' }));
    const panel = screen.getByRole('tabpanel');
    expect(within(panel).getByText('plazos')).toBeInTheDocument();
    expect(within(panel).getByText(/2 fallo\(s\) · 1 pregunta\(s\)/)).toBeInTheDocument();

    await userEvent.click(within(panel).getByRole('button', { name: /: abrir el error$/ }));

    expect(await screen.findByRole('heading', { name: 'Error declarado' })).toBeInTheDocument();
    expect(screen.getByText('lo confundí con otra cosa')).toBeInTheDocument();
    // El historial del repaso: de qué intervalo a qué intervalo y por qué.
    expect(screen.getByText(/acertada después de un fallo: cuatro días/)).toBeInTheDocument();
    expect(screen.getByText(/un fallo entra en la cola de hoy mismo/)).toBeInTheDocument();
    expect(screen.getByText(/0 → 4 día\(s\)/)).toBeInTheDocument();
    expect(screen.queryByText(/el desenlace lo dices tú/)).toBeNull();
    expect(screen.getByText(/La causa y la nota las declaras tú/)).toBeInTheDocument();
  });

  it('resolver un error dice que el repaso sigue', async () => {
    const fetchMock = stubErrores();
    renderErrores();

    await userEvent.click(await screen.findByRole('tab', { name: 'Conceptos' }));
    await userEvent.click(screen.getByRole('button', { name: /: abrir el error$/ }));
    await screen.findByRole('heading', { name: 'Error declarado' });

    await userEvent.click(screen.getByRole('button', { name: 'Marcar resuelto' }));

    await waitFor(() => {
      const llamada = fetchMock.mock.calls.find(
        (call) => typeof call[0] === 'string' && call[0].includes('/resolution'),
      );
      expect(cuerpoJsonDe(llamada)).toMatchObject({ resolved: true });
    });
    expect(
      screen.getByText(/Resolver un error no detiene su repaso/),
    ).toBeInTheDocument();
  });
});

describe('errores: exportar', () => {
  it('exporta y enseña los avisos del servidor antes de la descarga', async () => {
    const fetchMock = stubErrores();
    renderErrores();

    await screen.findByText('El plazo del procedimiento es de diez dias habiles:');
    await userEvent.click(screen.getByRole('button', { name: 'Anki CSV: exportar el banco para Anki' }));

    expect(await screen.findByText('Última exportación')).toBeInTheDocument();
    expect(screen.getByText('banco-20260918-120000.csv')).toBeInTheDocument();
    expect(screen.getByText('12')).toBeInTheDocument();
    expect(screen.getByText('Antes de usarlo fuera de aquí')).toBeInTheDocument();
    expect(
      screen.getByText(/citan material con derechos restringidos o sin determinar/),
    ).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Descargar el fichero exportado' })).toBeInTheDocument();

    await waitFor(() => {
      const llamada = fetchMock.mock.calls.find(
        (call) => typeof call[0] === 'string' && call[0].includes('/exports/anki-csv'),
      );
      expect(cuerpoJsonDe(llamada)).toMatchObject({
        opposition_id: 'opp-tai',
        include_restricted: true,
      });
    });
  });

  it('el material restringido se puede dejar fuera antes de exportar', async () => {
    const fetchMock = stubErrores();
    renderErrores();

    await screen.findByText('El plazo del procedimiento es de diez dias habiles:');
    await userEvent.click(screen.getByLabelText(/Incluir material con derechos restringidos/));
    await userEvent.click(screen.getByRole('button', { name: 'Exportar el banco en Markdown' }));

    await waitFor(() => {
      const llamada = fetchMock.mock.calls.find(
        (call) => typeof call[0] === 'string' && call[0].includes('/exports/markdown'),
      );
      expect(cuerpoJsonDe(llamada)).toMatchObject({ include_restricted: false });
    });
  });
});

/** El cuerpo JSON de una llamada simulada, con el tipo comprobado antes de leerlo. */
function cuerpoJsonDe(llamada: readonly unknown[] | undefined): unknown {
  const init = llamada?.[1];
  const body = typeof init === 'object' && init !== null && 'body' in init ? init.body : undefined;
  if (typeof body !== 'string') {
    throw new Error('la petición no llevaba cuerpo JSON');
  }
  return JSON.parse(body) as unknown;
}