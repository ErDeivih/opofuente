import { screen, within } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { AppShell } from '../../src/app/AppShell';
import { HomePage } from '../../src/pages/HomePage';
import {
  capabilitiesFixture,
  oppositionsFixture,
  pendingActionsEmptyFixture,
  pendingActionsFixture,
  readinessReady,
  renderWithProviders,
  settingsFixture,
  stubApi,
  studyReadinessFixture,
  studyReadinessReadyFixture,
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

/** El resumen de preparación como lo sirve el servidor: frases incluidas, sin que la pantalla sume. */
const PREPARACION_INCOMPLETA = studyReadinessFixture;

const PREPARACION_LISTA = studyReadinessReadyFixture;

const PENDIENTES = pendingActionsFixture;

const SIN_PENDIENTES = pendingActionsEmptyFixture;

function stubInicio(overrides: Record<string, StubbedRoute> = {}) {
  return stubApi({
    '/api/v1/health/ready': { body: readinessReady },
    '/api/v1/capabilities': { body: capabilitiesFixture },
    '/api/v1/settings': { body: settingsFixture },
    '/api/v1/oppositions': { body: oppositionsFixture },
    // La clave es más larga que `/api/v1/oppositions`, así que gana para esta ruta: sin ella, la
    // preparación recibiría el listado de oposiciones y la pantalla tendría que adivinar.
    '/api/v1/oppositions/opp-tai/readiness': { body: PREPARACION_INCOMPLETA },
    '/api/v1/pending-actions': { body: PENDIENTES },
    // Actividad reciente (07_UI-UX §3.4): sin lotes ni sesiones, la tarjeta lo dice.
    '/api/v1/ingestion-batches?limit=25': { body: [] },
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

describe('inicio: qué falta para poder estudiar (S12.6)', () => {
  it('enseña los pasos del servidor tal cual, con lo que falta y por dónde se resuelve', async () => {
    // Las frases y las cifras las compone el servidor: la pantalla no suma nada por su cuenta.
    stubInicio();
    renderInicio();

    expect(await screen.findByRole('heading', { name: '¿Listo para estudiar?' })).toBeInTheDocument();
    expect(await screen.findByText('falta una cosa')).toBeInTheDocument();
    expect(screen.getByText('Material por papel: listo')).toBeInTheDocument();
    expect(screen.getByText('Preguntas por tema: a medias')).toBeInTheDocument();
    expect(
      screen.getByText(/70 pregunta\(s\) en 1 conjunto\(s\); 62 catalogada\(s\) por tema/),
    ).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Ver el banco' })).toBeInTheDocument();
  });

  it('cuando los tres pasos están completos, lo dice sin pedir nada', async () => {
    stubInicio({ '/api/v1/oppositions/opp-tai/readiness': { body: PREPARACION_LISTA } });
    renderInicio();

    expect(await screen.findByText('listo para estudiar')).toBeInTheDocument();
    expect(screen.queryByText(/faltan/)).not.toBeInTheDocument();
  });

  it('las acciones necesarias son las del servidor, con su cifra y su enlace', async () => {
    // Esta tarjeta enseñaba un texto fijo —«No hay material importado»— sin leer nada.
    stubInicio();
    renderInicio();

    expect(await screen.findByText(/38 propuesta\(s\) sin decidir/)).toBeInTheDocument();
    expect(screen.getByText('38 pendiente(s)')).toBeInTheDocument();
    const acciones = screen.getByRole('region', { name: 'Acciones necesarias' });
    expect(within(acciones).getByRole('link', { name: 'Revisar propuestas' })).toHaveAttribute(
      'href',
      '/revision',
    );
    // El enlace de la biblioteca aparece también en el paso de material: se busca dentro de la acción.
    expect(within(acciones).getByRole('link', { name: 'Ver la biblioteca' })).toBeInTheDocument();
    // Y ya no aparece el texto fijo que decía que la pantalla no resumía esos avisos.
    expect(screen.queryByText(/todavía no resume esos avisos/)).not.toBeInTheDocument();
  });

  it('sin nada pendiente lo dice, en lugar de dejar la tarjeta vacía', async () => {
    stubInicio({ '/api/v1/pending-actions': { body: SIN_PENDIENTES } });
    renderInicio();

    expect(
      await screen.findByText(/Nada esperando tu decisión: no hay incidencias/),
    ).toBeInTheDocument();
  });
});

describe('inicio: cómo va el programa y qué ha pasado (07_UI-UX §3.3 y §3.4)', () => {
  it('dice el dominio estimado por tema, con los temas que tienen datos suficientes', async () => {
    stubInicio({
      '/api/v1/reviews/mastery?opposition_id=opp-tai': {
        body: {
          opposition_id: 'opp-tai',
          nodes_total: 33,
          nodes_with_estimate: 4,
          nodes: [],
          note: 'Sin intentos no hay dominio; con pocos, evidencia insuficiente.',
        },
      },
    });
    renderInicio();

    expect(await screen.findByText(/4 de 33 temas con datos suficientes/)).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /verlo tema a tema/ })).toHaveAttribute(
      'href',
      '/programa',
    );
  });

  it('la actividad reciente son los últimos lotes y las últimas sesiones de verdad', async () => {
    stubInicio({
      '/api/v1/ingestion-batches?limit=25': {
        body: [
          {
            id: 'lote-1',
            kind: 'file',
            status: 'succeeded',
            source_path_display: '…/Apuntes TAI',
            total_items: 12,
            counters: {},
            created_at: '2026-09-22T09:00:00Z',
            finished_at: '2026-09-22T09:01:00Z',
            issue_counts: {},
          },
        ],
      },
    });
    renderInicio();

    // El lote se lee con palabras, no con el valor del enum.
    expect(await screen.findByText(/carpeta elegida/)).toBeInTheDocument();
    expect(screen.getByText(/terminado/)).toBeInTheDocument();
    expect(screen.getByText(/12 entrada\(s\)/)).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Ver en la bandeja' })).toBeInTheDocument();
  });

  it('sin actividad lo dice, en lugar de enseñar una tabla vacía', async () => {
    stubInicio();
    renderInicio();

    expect(
      await screen.findByText(/Todavía no hay actividad: ni lotes en la bandeja ni sesiones/),
    ).toBeInTheDocument();
  });
});
