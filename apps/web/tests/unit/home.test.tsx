import { screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { AppShell } from '../../src/app/AppShell';
import { HomePage } from '../../src/pages/HomePage';
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
 * Inicio (07_UI-UX §3): la tarea recomendada.
 *
 * §3 pide que la primera tarjeta diga qué hacer: **el repaso vencido manda**, y si no hay nada
 * vencido se continúa la sesión que quedó a medias. Lo que la pantalla no hace es recomendar algo que
 * no toca: sin repasos y sin sesión, lo dice.
 */

const SESION_EN_MARCHA = {
  id: 'ses-1',
  mode: 'practice',
  status: 'running',
  feedback: 'immediate',
  opposition_id: 'opp-tai',
  convocation_version_id: 'conv-tai',
  question_set_id: 'set-1',
  answer_key_version_id: 'key-1',
  key_label: 'Primera parte: plantilla v1',
  configuration: {
    mode: 'practice',
    feedback: 'immediate',
    time_limit_minutes: null,
    shuffle: false,
    sources: [],
  },
  time_limit_minutes: null,
  total_questions: 3,
  answered_questions: 1,
  started_at: '2026-09-19T09:00:00Z',
  finished_at: null,
  created_at: '2026-09-19T09:00:00Z',
  result: null,
};

function stubInicio(overrides: Record<string, StubbedRoute> = {}) {
  return stubApi({
    '/api/v1/health/ready': { body: readinessReady },
    '/api/v1/capabilities': { body: capabilitiesFixture },
    '/api/v1/settings': { body: settingsFixture },
    '/api/v1/oppositions': { body: oppositionsFixture },
    '/api/v1/study-sessions?limit=50&offset=0&opposition_id=opp-tai': {
      body: { sessions: [], total: 0, limit: 50, offset: 0 },
    },
    '/api/v1/reviews/due?opposition_id=opp-tai': {
      body: {
        items: [],
        stats: { active: 0, due: 0, next_due_at: null, lapses: 0 },
        concepts: [],
        notes: [],
      },
    },
    ...overrides,
  });
}

function renderInicio() {
  return renderWithProviders(
    <AppShell>
      <HomePage />
    </AppShell>,
    { route: '/' },
  );
}

describe('inicio: la siguiente tarea', () => {
  it('si hay repaso vencido, manda el repaso', async () => {
    stubInicio({
      '/api/v1/reviews/due?opposition_id=opp-tai': {
        body: {
          items: [],
          stats: { active: 5, due: 2, next_due_at: '2026-09-19T09:00:00Z', lapses: 3 },
          concepts: [],
          notes: [],
        },
      },
    });
    renderInicio();

    expect(await screen.findByRole('heading', { name: 'Siguiente tarea' })).toBeInTheDocument();
    expect(await screen.findByText(/2 pregunta\(s\) vencida\(s\) de repaso/)).toBeInTheDocument();
    expect(screen.getByText('2 de 5 vencidos')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Ir al repaso de errores' })).toBeInTheDocument();
    // Y dice cómo se repasa: en una sesión, sin enseñar la solución antes del intento.
    expect(screen.getByText(/no se enseña antes de contestar/)).toBeInTheDocument();
  });

  it('sin nada vencido, se continúa la sesión a medias', async () => {
    stubInicio({
      '/api/v1/study-sessions?limit=50&offset=0&opposition_id=opp-tai': {
        body: { sessions: [SESION_EN_MARCHA], total: 1, limit: 50, offset: 0 },
      },
    });
    renderInicio();

    expect(await screen.findByText('Tienes una sesión sin terminar')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Continuar la sesión' })).toBeInTheDocument();
  });

  it('sin repasos y sin sesión, lo dice en lugar de recomendar algo que no toca', async () => {
    stubInicio();
    renderInicio();

    expect(
      await screen.findByText(/Nada vencido y ninguna sesión a medias/),
    ).toBeInTheDocument();
    expect(screen.getByText(/Lo siguiente es practicar/)).toBeInTheDocument();
  });
});
