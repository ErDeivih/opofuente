import { screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { HomePage } from '../../src/pages/HomePage';
import { revisarPantalla } from '../palabrasProhibidas';
import {
  capabilitiesFixture,
  oppositionsFixture,
  pendingActionsFixture,
  readinessReady,
  renderWithProviders,
  settingsFixture,
  stubApi,
  type StubbedRoute,
} from './testUtils';

/**
 * Inicio del alumno (F1 del rediseño, 6 de octubre de 2026).
 *
 * La pantalla tiene tres tarjetas y una regla: **lo que se enseña es dato real y lo que no hay se
 * dice**. Ni contadores de importaciones, ni lo que espera una decisión de revisión, ni de dónde sale
 * cada pregunta: todo eso se fue con el panel a `/admin` y aquí se comprueba que no vuelve.
 */

/** Una sesión de práctica a medias, con los campos internos que **no** deben verse. */
const SESION_EN_MARCHA = {
  id: 'ses-1',
  mode: 'practice',
  status: 'running',
  feedback: 'immediate',
  opposition_id: 'opp-tai',
  convocation_version_id: 'conv-tai',
  question_set_id: 'set-rojo-general',
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
  total_questions: 50,
  answered_questions: 12,
  started_at: '2026-09-19T09:00:00Z',
  finished_at: null,
  created_at: '2026-09-19T09:00:00Z',
  result: null,
};

const SESION_TERMINADA = { ...SESION_EN_MARCHA, id: 'ses-0', status: 'finished' };

function stubInicio(overrides: Record<string, StubbedRoute> = {}) {
  return stubApi({
    '/api/v1/health/ready': { body: readinessReady },
    '/api/v1/capabilities': { body: capabilitiesFixture },
    '/api/v1/settings': { body: settingsFixture },
    '/api/v1/oppositions': { body: oppositionsFixture },
    '/api/v1/pending-actions': { body: pendingActionsFixture },
    '/api/v1/study-sessions': {
      body: { sessions: [], total: 0, limit: 50, offset: 0 },
    },
    '/api/v1/reviews/due': {
      body: {
        items: [],
        stats: { active: 0, due: 0, next_due_at: null, lapses: 0 },
        concepts: [],
        notes: [],
      },
    },
    '/api/v1/reviews/mastery': {
      body: {
        opposition_id: 'opp-tai',
        nodes_total: 33,
        nodes_with_estimate: 0,
        nodes: [],
        note: 'Sin intentos no hay nada que estimar.',
      },
    },
    ...overrides,
  });
}

function renderInicio() {
  return renderWithProviders(<HomePage />, { route: '/' });
}

/** La interfaz de la pantalla: todo menos lo que va dentro de un contenedor de contenido. */
function interfazDeLaPantalla() {
  const copia = document.body.cloneNode(true) as HTMLElement;
  for (const nodo of Array.from(copia.querySelectorAll('[data-contenido]'))) {
    nodo.remove();
  }
  return { interfaz: copia.textContent ?? '', todo: document.body.textContent ?? '' };
}

describe('inicio: continuar donde lo dejaste', () => {
  it('con un test a medias enseña por dónde va y el botón para seguirlo', async () => {
    stubInicio({
      '/api/v1/study-sessions': {
        body: { sessions: [SESION_EN_MARCHA], total: 1, limit: 50, offset: 0 },
      },
    });
    renderInicio();

    expect(await screen.findByText('12 de 50')).toBeInTheDocument();
    expect(screen.getByText('práctica')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Continuar el test' })).toHaveAttribute(
      'href',
      '/tests',
    );
  });

  it('sin test a medias lo dice, y ofrece empezar uno', async () => {
    stubInicio();
    renderInicio();

    expect(await screen.findByText('Aún no has hecho ningún test.')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Empezar un test' })).toHaveAttribute('href', '/tests');
  });

  it('con tests hechos pero ninguno a medias, tampoco se inventa una sesión', async () => {
    stubInicio({
      '/api/v1/study-sessions': {
        body: { sessions: [SESION_TERMINADA], total: 1, limit: 50, offset: 0 },
      },
    });
    renderInicio();

    expect(await screen.findByText('No tienes ningún test a medias.')).toBeInTheDocument();
  });

  it('si la API no responde lo dice, en lugar de enseñar un hueco vacío', async () => {
    stubInicio({ '/api/v1/study-sessions': { status: 503, body: { code: 'unavailable' } } });
    renderInicio();

    expect(
      await screen.findByText('No se pudieron cargar tus tests: la aplicación no responde.'),
    ).toBeInTheDocument();
  });
});

describe('inicio: repasar fallos', () => {
  it('con repaso vencido pone la cifra delante y la salida a los fallos', async () => {
    stubInicio({
      '/api/v1/reviews/due': {
        body: {
          items: [],
          stats: { active: 5, due: 2, next_due_at: '2026-09-19T09:00:00Z', lapses: 3 },
          concepts: [],
          notes: [],
        },
      },
    });
    renderInicio();

    const cifra = (await screen.findByText('Preguntas para repasar hoy')).closest('.ui-stat');
    expect(cifra).toHaveTextContent('2');
    expect(screen.getByRole('link', { name: 'Repasar mis fallos' })).toHaveAttribute(
      'href',
      '/fallos',
    );
  });

  it('sin nada vencido lo dice', async () => {
    stubInicio();
    renderInicio();

    expect(
      await screen.findByText('No tienes fallos pendientes de repaso.'),
    ).toBeInTheDocument();
    expect(screen.queryByRole('link', { name: 'Repasar mis fallos' })).toBeNull();
  });
});

describe('inicio: tu progreso', () => {
  it('dice cuántos temas tienen datos suficientes', async () => {
    stubInicio({
      '/api/v1/reviews/mastery': {
        body: {
          opposition_id: 'opp-tai',
          nodes_total: 33,
          nodes_with_estimate: 4,
          nodes: [],
          note: 'El dominio se estima por tema con los intentos.',
        },
      },
    });
    renderInicio();

    expect(await screen.findByText('4 de 33')).toBeInTheDocument();
    const barra = screen.getByRole('progressbar', { name: 'Temas ya practicados' });
    expect(barra).toHaveAttribute('aria-valuenow', '12');
    expect(screen.getByRole('link', { name: 'Ver mi progreso' })).toHaveAttribute(
      'href',
      '/progreso',
    );
  });

  it('sin programa no hay progreso que enseñar, y lo dice', async () => {
    stubInicio({
      '/api/v1/reviews/mastery': {
        body: {
          opposition_id: 'opp-tai',
          nodes_total: 0,
          nodes_with_estimate: 0,
          nodes: [],
          note: 'Sin temas no hay nada que estimar.',
        },
      },
    });
    renderInicio();

    expect(
      await screen.findByText('Todavía no hay progreso que enseñar: aparece al hacer tu primer test.'),
    ).toBeInTheDocument();
  });
});

describe('inicio: la cocina se queda en el panel', () => {
  it('no enseña lenguaje interno ni datos del panel, ni con una sesión a medias', async () => {
    stubInicio({
      '/api/v1/study-sessions': {
        body: { sessions: [SESION_EN_MARCHA], total: 1, limit: 50, offset: 0 },
      },
    });
    renderInicio();

    expect(await screen.findByText('12 de 50')).toBeInTheDocument();

    const { interfaz, todo } = interfazDeLaPantalla();
    expect(revisarPantalla(interfaz, todo)).toEqual([]);
    // Los datos del material de origen no se pintan aunque vengan en la respuesta.
    expect(todo).not.toContain('plantilla v1');
    expect(todo).not.toContain('set-rojo-general');
  });

  it('no hay contadores de importaciones ni acciones pendientes de revisión', async () => {
    stubInicio();
    renderInicio();

    expect(await screen.findByText('Aún no has hecho ningún test.')).toBeInTheDocument();
    expect(screen.queryByRole('region', { name: 'Acciones necesarias' })).toBeNull();
    expect(screen.queryByRole('heading', { name: '¿Listo para estudiar?' })).toBeNull();
    expect(screen.queryByRole('heading', { name: 'Siguiente tarea' })).toBeNull();
    expect(document.querySelectorAll('.nav__count')).toHaveLength(0);
  });
});
